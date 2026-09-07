# Ring WebRTC Backend Patch

[![Latest release](https://img.shields.io/github/v/release/thomasgregg/ring-webrtc-backend-patch?display_name=tag&sort=semver)](https://github.com/thomasgregg/ring-webrtc-backend-patch/releases/latest)
[![Validate](https://github.com/thomasgregg/ring-webrtc-backend-patch/actions/workflows/validate.yml/badge.svg)](https://github.com/thomasgregg/ring-webrtc-backend-patch/actions/workflows/validate.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<p align="center">
  <img src="https://raw.githubusercontent.com/thomasgregg/ring-webrtc-backend-patch/main/custom_components/ring_webrtc_backend_patch/brand/icon@2x.png" alt="Ring WebRTC Backend Patch stream recovery icon" width="112">
</p>

## Reliable Ring View reconnects after rotation and stream restarts

Ring WebRTC Backend Patch is an optional companion integration for [Ring View](https://github.com/thomasgregg/ring-view). It works around a specific stream-cleanup defect in `ring-doorbell==0.9.14` that can leave the next Ring Live session unable to connect after the previous session closes.

The problem is often exposed when the Home Assistant Companion App rebuilds the Ring View viewer during an iPhone orientation change. Rotation does not break the video directly: that rebuild closes the current WebRTC session, then Ring View reconnects and reveals the backend shutdown bug. Closing and reopening Live, a Web View reload, or another reconnect can expose the same problem.

## What problem does it solve?

When Ring's signalling server closes a stream from inside its websocket reader task, the library can follow this sequence:

1. The reader task starts closing the WebRTC stream.
2. `RingWebRtcStream._close()` tries to await that same reader task.
3. Python raises `RuntimeError: Task cannot await on itself`.
4. Cleanup stops part-way through, so the replacement Live or talkback session can fail or take longer to recover.

The patch adds one narrow guard: when shutdown is already running inside the reader task, it clears that task reference before calling the original shutdown implementation. Normal shutdown from another task is unchanged.

## How it relates to Ring View

[Ring View](https://github.com/thomasgregg/ring-view) is the Home Assistant dashboard card. It combines Ring's latest recording, Live view, sound, and optional push-to-talk in one viewer. Ring View also manages the visible orientation-change and reconnect experience.

This integration is the backend safeguard. It does not add a card or replace Ring View; it prevents the Ring library's incomplete stream cleanup from interfering with the next connection Ring View requests.

| Component | Responsibility |
| --- | --- |
| Home Assistant's built-in Ring integration | Ring authentication, devices, camera entities, and WebRTC sessions |
| Ring View | Dashboard viewer, recording/Live switching, talkback controls, and reconnect experience |
| Ring WebRTC Backend Patch | Temporary guard for the affected backend stream-cleanup path |

Ring View works without this patch. Install it only when the described backend defect affects repeated Live sessions or when testing the known iPhone rotation recovery case.

## Get started

You need Home Assistant **2026.7 or newer** with the built-in [Ring integration](https://www.home-assistant.io/integrations/ring/) already configured.

[![Open Ring WebRTC Backend Patch in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=thomasgregg&repository=ring-webrtc-backend-patch&category=integration)

1. Open the repository in HACS using the button above and download **Ring WebRTC Backend Patch**.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **Ring WebRTC Backend Patch** and confirm installation.

The patch is applied when the integration loads and remains active across Ring integration reloads.

## Safety and scope

- Runs alongside Home Assistant's built-in Ring integration.
- Applies only to the verified vulnerable version, `ring-doorbell==0.9.14`.
- Checks the private method signature before making any change.
- Leaves normal external stream shutdown behavior intact.
- Is safe to load more than once and restores the original method when unloaded.
- Contains and transmits no Ring credentials or device data.
- Does not change orientation handling, media negotiation, autoplay policy, or network behavior.

If the installed Ring library version or method signature is not recognized, the integration fails closed and does not patch it. Not every Live-view problem is caused by this defect; Ring outages, network problems, camera session limits, competing clients, and iOS autoplay restrictions remain possible.

## Verify the fix

1. Start Ring Live view in Ring View with two-way audio enabled.
2. Rotate the iPhone while the Home Assistant Companion App viewer is open, or close and reopen Live.
3. Confirm the replacement Live stream connects and talkback still works.
4. Confirm no new `Task cannot await on itself` traceback appears in the Home Assistant logs.

For the patch's own status, download diagnostics from this integration. Diagnostics report the installed Ring library version, whether the patch was applied, and the reason. They include no credentials or device data.

## Removal

1. Remove **Ring WebRTC Backend Patch** from **Settings → Devices & services**.
2. Remove it from HACS.
3. Restart Home Assistant.

The original built-in Ring behavior is then restored.

## Temporary by design

This integration is an interim workaround while the fix moves through the upstream Ring library and into Home Assistant:

- [python-ring-doorbell issue #554](https://github.com/python-ring-doorbell/python-ring-doorbell/issues/554)
- [python-ring-doorbell pull request #534](https://github.com/python-ring-doorbell/python-ring-doorbell/pull/534)

Once Home Assistant ships a corrected Ring library version, remove this integration and verify normal Live and reconnect behavior without it. A merged upstream change alone does not update an existing Home Assistant installation.

## License

[MIT](LICENSE)
