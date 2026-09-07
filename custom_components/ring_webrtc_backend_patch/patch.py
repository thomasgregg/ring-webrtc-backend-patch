"""Narrow runtime patch for the ring-doorbell WebRTC self-await defect."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any

RING_DISTRIBUTION = "ring-doorbell"
SUPPORTED_VERSIONS = frozenset({"0.9.14"})

_PATCH_MARKER = "__ring_webrtc_backend_patch__"
_ORIGINAL_CLOSE = "__ring_webrtc_backend_patch_original_close__"


@dataclass(frozen=True, slots=True)
class PatchStatus:
    """Describe whether and why the compatibility patch is active."""

    library_version: str
    applied: bool
    reason: str


def installed_ring_version() -> str:
    """Return the installed ring-doorbell distribution version."""

    try:
        return version(RING_DISTRIBUTION)
    except PackageNotFoundError:
        return "not-installed"


def _has_expected_signature(method: Any) -> bool:
    """Check the private method shape before modifying it."""

    parameters = list(inspect.signature(method).parameters.values())
    return (
        len(parameters) == 2
        and parameters[0].name == "self"
        and parameters[1].name == "closed_by_self"
        and parameters[1].kind is inspect.Parameter.KEYWORD_ONLY
    )


def apply_patch_to_class(stream_class: type[Any], library_version: str) -> PatchStatus:
    """Apply the guarded close wrapper to a compatible stream class."""

    current_close = stream_class._close
    if getattr(current_close, _PATCH_MARKER, False):
        return PatchStatus(library_version, True, "already_applied")

    if library_version not in SUPPORTED_VERSIONS:
        return PatchStatus(library_version, False, "unsupported_version")

    if not _has_expected_signature(current_close):
        return PatchStatus(library_version, False, "unexpected_method_signature")

    original_close = current_close

    async def guarded_close(self: Any, *, closed_by_self: bool) -> None:
        """Avoid awaiting the reader task when it is the current task."""

        read_task = self.read_task
        if read_task is asyncio.current_task():
            # The original method will otherwise await this task. Clearing the
            # reference has the same effect as the proposed upstream guard; the
            # reader finishes naturally after the close handler returns.
            self.read_task = None

        await original_close(self, closed_by_self=closed_by_self)

    setattr(guarded_close, _PATCH_MARKER, True)
    setattr(stream_class, _ORIGINAL_CLOSE, original_close)
    stream_class._close = guarded_close
    return PatchStatus(library_version, True, "applied")


def remove_patch_from_class(stream_class: type[Any]) -> bool:
    """Restore the exact method that was present before patching."""

    current_close = stream_class._close
    original_close = getattr(stream_class, _ORIGINAL_CLOSE, None)
    if not getattr(current_close, _PATCH_MARKER, False) or original_close is None:
        return False

    stream_class._close = original_close
    delattr(stream_class, _ORIGINAL_CLOSE)
    return True


def apply_ring_patch() -> PatchStatus:
    """Apply the patch to the installed Ring WebRTC stream class."""

    from ring_doorbell.webrtcstream import RingWebRtcStream

    ring_version = installed_ring_version()
    return apply_patch_to_class(RingWebRtcStream, ring_version)


def remove_ring_patch() -> bool:
    """Remove this integration's patch from the Ring WebRTC stream class."""

    from ring_doorbell.webrtcstream import RingWebRtcStream

    return remove_patch_from_class(RingWebRtcStream)
