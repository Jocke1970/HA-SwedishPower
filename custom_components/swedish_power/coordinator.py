"""Read-only 15-minute Statnett data coordinator for Sweden."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Any

from aiohttp import ClientError, ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    FLOWS_PATH,
    PRODUCTION_PATH,
    REQUEST_TIMEOUT_SECONDS,
    SOURCE_URL,
    UPDATE_INTERVAL,
)
from .model import ProductionSnapshot, RawFlow, parse_flows, parse_production

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SwedishPowerData:
    """Current national readings, plus optional raw flow diagnostics."""

    production: ProductionSnapshot
    raw_flows: tuple[RawFlow, ...]
    flow_error: str | None = None


class SwedishPowerCoordinator(DataUpdateCoordinator[SwedishPowerData]):
    """Fetch and normalize only Statnett's Sweden-relevant information."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self._session: ClientSession = async_get_clientsession(hass)

    async def _async_get_json(self, path: str) -> Any:
        """Fetch a single JSON object/array with bounded timeout."""
        url = f"{SOURCE_URL}{path}"
        async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
            async with self._session.get(
                url,
                headers={"Accept": "application/json"},
            ) as response:
                response.raise_for_status()
                if "json" not in response.content_type.lower():
                    raise ValueError("Statnett response is not JSON")
                return await response.json()

    async def _async_update_data(self) -> SwedishPowerData:
        """Refresh country metrics; optional flow failure does not lose MW data."""
        production_result, flows_result = await asyncio.gather(
            self._async_get_json(PRODUCTION_PATH),
            self._async_get_json(FLOWS_PATH),
            return_exceptions=True,
        )
        if isinstance(production_result, BaseException):
            if isinstance(production_result, asyncio.CancelledError):
                raise production_result
            raise UpdateFailed(
                f"Statnett production request failed: {type(production_result).__name__}"
            ) from production_result

        now = datetime.now(timezone.utc)
        try:
            production = parse_production(production_result, now=now)
        except (ValueError, TypeError) as err:
            raise UpdateFailed("Unexpected Statnett production response") from err

        flows: tuple[RawFlow, ...] = ()
        flow_error: str | None = None
        if isinstance(flows_result, BaseException):
            if isinstance(flows_result, asyncio.CancelledError):
                raise flows_result
            flow_error = type(flows_result).__name__
        else:
            try:
                flows = parse_flows(flows_result, now=now)
            except (ValueError, TypeError) as err:
                flow_error = type(err).__name__
        if flow_error:
            _LOGGER.warning("Optional Statnett flow update unavailable (%s)", flow_error)

        return SwedishPowerData(
            production=production,
            raw_flows=flows,
            flow_error=flow_error,
        )
