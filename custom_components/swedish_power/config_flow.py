"""UI setup: exactly one Swedish data service entry, no credentials."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
import probatio

from .const import DOMAIN, ENTRY_UNIQUE_ID


class SwedishPowerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure Swedish Power from Home Assistant's Integrations UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Offer a simple confirmation; avoid duplicate country-level entries."""
        if user_input is not None:
            await self.async_set_unique_id(ENTRY_UNIQUE_ID)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Sweden", data={})
        return self.async_show_form(step_id="user", data_schema=probatio.Schema({}))
