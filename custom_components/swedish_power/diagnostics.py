"""Non-sensitive status diagnostics for Swedish Power."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .vattenfall import VattenfallSnapshot


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Provide source status without copying raw external payloads."""
    runtime = entry.runtime_data
    coordinator = runtime.statnett
    data = coordinator.data
    if not data:
        return {
            "source": "Statnett Driftsdata",
            "last_update_success": coordinator.last_update_success,
            "reactor_sources": _reactor_sources(runtime),
        }
    prod = data.production
    return {
        "scope": "SE",
        "reactor_sources": _reactor_sources(runtime),
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


def _reactor_sources(runtime) -> dict:
    """No raw payloads, no UMM notices, and no guessed operating status."""
    results = {}
    for plant, coordinator in runtime.reactors.items():
        snapshot = coordinator.data
        records = {}
        if isinstance(snapshot, VattenfallSnapshot):
            records = {
                rid: {
                    "value_mw": reading.power_mw,
                    "quality": reading.quality,
                    "measured_at": reading.measured_at.isoformat() if reading.measured_at else None,
                }
                for rid, reading in snapshot.reactors.items()
            }
        elif snapshot is not None:
            records = {
                "O3": {
                    "value_mw": snapshot.value_mw,
                    "quality": snapshot.quality,
                    "measured_at": snapshot.measured_at.isoformat() if snapshot.measured_at else None,
                }
            }
        results[plant] = {
            "last_update_success": coordinator.last_update_success,
            "fetched_at": coordinator.fetched_at.isoformat() if coordinator.fetched_at else None,
            "readings": records,
            "source": "OKG" if plant == "oskarshamn" else "Vattenfall",
            "status_policy": "MW only; never infer outage/fault from power",
        }
    return results
