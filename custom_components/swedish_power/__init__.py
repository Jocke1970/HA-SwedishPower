"""Swedish Power: country-wide Statnett and independent Swedish reactor data."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SwedishPowerCoordinator
from .reactor_coordinator import PLANTS, ReactorSourceCoordinator

PLATFORMS = (Platform.SENSOR,)


@dataclass(frozen=True)
class SwedishPowerRuntime:
    """Keep Statnett and the three independent reactor feeds separate."""

    statnett: SwedishPowerCoordinator
    reactors: dict[str, ReactorSourceCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Statnett first; optional reactor failures never block integration."""
    statnett = SwedishPowerCoordinator(hass, entry)
    await statnett.async_config_entry_first_refresh()

    reactors = {
        plant: ReactorSourceCoordinator(hass, entry, plant)
        for plant in PLANTS
    }
    entry.runtime_data = SwedishPowerRuntime(statnett=statnett, reactors=reactors)

    # Each source has its own update loop, quality and failure state.
    # async_refresh records UpdateFailed as failure; it does not abort setup.
    await asyncio.gather(*(source.async_refresh() for source in reactors.values()))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading entities drops coordinator listeners and scheduled callbacks."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
