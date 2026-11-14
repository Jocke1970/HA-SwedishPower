"""Three independent source coordinators for six Swedish reactor MW readings.

Forsmark, Ringhals and Oskarshamn are separately polled every 15 minutes.
One failed plant endpoint cannot invalidate another source or Statnett.
The UMM notice feed is intentionally NOT used to infer reactor operating status.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UPDATE_INTERVAL
from .okg import OkgO3Reading, async_fetch_okg_o3
from .vattenfall import VattenfallSnapshot, async_fetch_vattenfall

_LOGGER = logging.getLogger(__name__)

ReactorSourceData: TypeAlias = VattenfallSnapshot | OkgO3Reading
PLANTS = ("forsmark", "ringhals", "oskarshamn")


class ReactorSourceCoordinator(DataUpdateCoordinator[ReactorSourceData]):
    """Own one source endpoint and its independent success/availability state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, plant: str) -> None:
        if plant not in PLANTS:
            raise ValueError(f"Unknown reactor plant: {plant}")
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"swedish_power_{plant}",
            update_interval=UPDATE_INTERVAL,
        )
        self.plant = plant
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> ReactorSourceData:
        """Treat a failed source as unavailable without touching other sources."""
        try:
            if self.plant == "oskarshamn":
                return await async_fetch_okg_o3(self._session)
            return await async_fetch_vattenfall(self._session, self.plant)
        except Exception as exc:
            # Never include whole remote payloads, URLs with params or raw responses.
            raise UpdateFailed(
                f"{self.plant} reactor power source unavailable ({type(exc).__name__})"
            ) from exc

    @property
    def fetched_at(self) -> datetime | None:
        """Source fetch time of latest successful snapshot (not measured time)."""
        return self.data.fetched_at if self.data is not None else None
