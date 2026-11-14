"""Non-sensitive status diagnostics for Swedish Power."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SwedishPowerCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Provide source status without copying raw external payloads."""
    coordinator: SwedishPowerCoordinator = entry.runtime_data
    data = coordinator.data
    if not data:
        return {"source": "Statnett Driftsdata", "last_update_success": coordinator.last_update_success}
    prod = data.production
    return {
        "scope": "SE",
        "source": "Statnett Driftsdata",
        "poll_interval_seconds": 900,
        "last_update_success": coordinator.last_update_success,
        "fetched_at": prod.fetched_at.isoformat(),
        "source_snapshot_at": prod.snapshot_at.isoformat() if prod.snapshot_at else None,
        "readings": {
            key: {
                "value_mw": reading.value_mw,
                "quality": reading.quality,
                "timestamp_basis": reading.timestamp_basis,
                "measured_at": reading.measured_at.isoformat() if reading.measured_at else None,
            }
            for key, reading in prod.readings.items()
        },
        "checks": prod.checks,
        "sweden_flow_count": len(data.raw_flows),
        "internal_area_flow_count": sum(1 for r in data.raw_flows if r.area_type == "internal"),
        "flow_error": data.flow_error,
        "flow_sign_convention": "UNVERIFIED - raw flow values not exposed as directional sensors",
    }
