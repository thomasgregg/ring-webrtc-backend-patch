"""Ring WebRTC Backend Patch integration."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from .const import DOMAIN
from .patch import apply_ring_patch, remove_ring_patch

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Apply the compatibility patch when the config entry loads."""

    status = apply_ring_patch()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = asdict(status)

    if status.applied:
        _LOGGER.info(
            "Ring WebRTC backend patch status: %s (ring-doorbell %s)",
            status.reason,
            status.library_version,
        )
    else:
        _LOGGER.warning(
            "Ring WebRTC backend patch was not applied: %s "
            "(ring-doorbell %s)",
            status.reason,
            status.library_version,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove the patch when the config entry unloads."""

    removed = remove_ring_patch()
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not hass.data.get(DOMAIN):
        hass.data.pop(DOMAIN, None)

    _LOGGER.info("Ring WebRTC backend patch removed: %s", removed)
    return True
