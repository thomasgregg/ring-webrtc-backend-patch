# Ring WebRTC Backend Patch

Temporary Home Assistant compatibility integration for the
`ring-doorbell==0.9.14` WebRTC shutdown defect.

When Ring's signalling server closes a stream from inside its websocket reader
task, `RingWebRtcStream._close()` attempts to await that same task. Python raises
`RuntimeError: Task cannot await on itself`, cleanup stops part-way through, and
the next live-view connection can fail.

This integration applies the narrow guard proposed upstream: when shutdown is
already running inside the reader task, it clears that task reference before
calling the original shutdown implementation. All other shutdown behavior is
left to the installed Ring library.

## Scope

- Runs alongside Home Assistant's built-in Ring integration.
- Does not replace Ring authentication, devices, entities, or camera handling.
- Applies only to the verified vulnerable version, `ring-doorbell==0.9.14`.
- Does not contain or transmit Ring credentials.
- Can be removed completely through HACS followed by a Home Assistant restart.

This is an interim workaround while the upstream fix is reviewed and released:

- [python-ring-doorbell issue #554](https://github.com/python-ring-doorbell/python-ring-doorbell/issues/554)
- [python-ring-doorbell pull request #534](https://github.com/python-ring-doorbell/python-ring-doorbell/pull/534)

## Installation with HACS

1. Open HACS and add this repository as a custom repository of type
   **Integration**.
2. Download **Ring WebRTC Backend Patch**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**.
5. Search for **Ring WebRTC Backend Patch** and confirm installation.

The built-in Ring integration must already be configured. The patch is applied
when this integration loads and remains active across Ring integration reloads.

## Verification

Download diagnostics from this integration in Home Assistant. Diagnostics show
the installed Ring library version, whether the patch was applied, and why. No
credentials or device data are included.

For the orientation regression:

1. Start Ring live view with two-way audio enabled.
2. Rotate the iPhone while the Home Assistant Companion App viewer is open.
3. Confirm live view reconnects and talkback still works.
4. Confirm no new `Task cannot await on itself` traceback appears in the Home
   Assistant logs.

Both visible recovery and a clean backend log are required for a successful
test.

## Removal

1. Remove **Ring WebRTC Backend Patch** from **Settings → Devices & services**.
2. Remove it from HACS.
3. Restart Home Assistant.

The original built-in Ring behavior is then restored.

## Development

```bash
python -m pip install -r requirements-test.txt
pytest
ruff check custom_components tests
```

