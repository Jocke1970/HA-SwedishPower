"""Swedish Power: Sweden-only Statnett monitoring for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SwedishPowerCoordinator

PLATFORMS = (Platform.SENSOR,)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one Sweden-wide API instance and forward sensor entities."""
    coordinator = SwedishPowerCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop polling and unload entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
