"""Config flow for Ring WebRTC Backend Patch."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries

from .const import DOMAIN, INTEGRATION_NAME


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the Ring WebRTC Backend Patch integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the single confirmation step."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title=INTEGRATION_NAME, data={})

        return self.async_show_form(step_id="user")

