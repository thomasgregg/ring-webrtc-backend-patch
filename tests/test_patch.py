"""Regression tests for the Ring WebRTC self-await compatibility patch."""

from __future__ import annotations

import asyncio
from typing import Any

from ring_doorbell.webrtcstream import RingWebRtcStream

from custom_components.ring_webrtc_backend_patch.patch import (
    apply_patch_to_class,
    remove_patch_from_class,
)


def _stream_with_reader(reader_task: asyncio.Task[Any]) -> RingWebRtcStream:
    """Build the minimal real Ring stream state required by _close()."""

    stream = object.__new__(RingWebRtcStream)
    stream.session_id = "test-session"
    stream._on_close_callback = None
    stream.is_alive = True
    stream.ping_task = None
    stream.websocket = None
    stream.read_task = reader_task
    stream._close_task = None
    return stream


def test_unpatched_ring_0_9_14_reproduces_self_await() -> None:
    """Prove the pinned upstream implementation contains the reported defect."""

    remove_patch_from_class(RingWebRtcStream)
    original_close = RingWebRtcStream._close

    async def run() -> None:
        current_task = asyncio.current_task()
        assert current_task is not None
        stream = _stream_with_reader(current_task)

        async def close_callback() -> None:
            await stream.close()

        stream._on_close_callback = close_callback

        try:
            await original_close(stream, closed_by_self=True)
        except RuntimeError as err:
            assert "cannot await on itself" in str(err)
        else:
            raise AssertionError("ring-doorbell 0.9.14 no longer reproduces the defect")

    asyncio.run(run())


def test_patch_allows_server_initiated_close_from_reader_task() -> None:
    """A close received by the reader must finish without awaiting itself."""

    status = apply_patch_to_class(RingWebRtcStream, "0.9.14")
    assert status.applied

    async def run() -> None:
        current_task = asyncio.current_task()
        assert current_task is not None
        stream = _stream_with_reader(current_task)
        callback_count = 0

        async def close_callback() -> None:
            nonlocal callback_count
            callback_count += 1
            await stream.close()

        stream._on_close_callback = close_callback

        await stream._close(closed_by_self=True)

        assert callback_count == 1
        assert stream.read_task is None
        assert stream.session_id is None
        assert not stream.is_alive

    try:
        asyncio.run(run())
    finally:
        assert remove_patch_from_class(RingWebRtcStream)


def test_patch_preserves_normal_external_reader_shutdown() -> None:
    """Client shutdown must still await a different reader task normally."""

    status = apply_patch_to_class(RingWebRtcStream, "0.9.14")
    assert status.applied

    async def run() -> None:
        reader_task = asyncio.create_task(asyncio.sleep(0))
        stream = _stream_with_reader(reader_task)

        await stream._close(closed_by_self=False)

        assert reader_task.done()
        assert stream.read_task is None

    try:
        asyncio.run(run())
    finally:
        assert remove_patch_from_class(RingWebRtcStream)


def test_patch_is_idempotent_and_reversible() -> None:
    """Repeated setup is harmless and unload restores the exact method."""

    remove_patch_from_class(RingWebRtcStream)
    original_close = RingWebRtcStream._close

    first = apply_patch_to_class(RingWebRtcStream, "0.9.14")
    patched_close = RingWebRtcStream._close
    second = apply_patch_to_class(RingWebRtcStream, "0.9.14")

    assert first.reason == "applied"
    assert second.reason == "already_applied"
    assert RingWebRtcStream._close is patched_close
    assert remove_patch_from_class(RingWebRtcStream)
    assert RingWebRtcStream._close is original_close


def test_unknown_library_version_is_not_modified() -> None:
    """Unknown Ring versions must fail closed instead of being monkey-patched."""

    remove_patch_from_class(RingWebRtcStream)
    original_close = RingWebRtcStream._close

    status = apply_patch_to_class(RingWebRtcStream, "9.9.9")

    assert not status.applied
    assert status.reason == "unsupported_version"
    assert RingWebRtcStream._close is original_close
