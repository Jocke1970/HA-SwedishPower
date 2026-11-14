"""Real Home Assistant lifecycle tests (pytest-homeassistant 2026.11).

These tests execute Home Assistant integration setup, config flow,
sensor registration and coordinator updates with mocked Statnett HTTP.
No real Statnett requests or private user data are needed.
"""

from __future__ import annotations

from copy import deepcopy
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.swedish_power.const import (
    DOMAIN,
    FLOWS_PATH,
    PRODUCTION_PATH,
    UPDATE_INTERVAL,
)
from custom_components.swedish_power.coordinator import SwedishPowerCoordinator
from custom_components.swedish_power.reactor_coordinator import ReactorSourceCoordinator
from custom_components.swedish_power.vattenfall import parse_vattenfall_html
from custom_components.swedish_power.okg import parse_okg_o3

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _payloads() -> tuple[dict, list]:
    """Use offline examples with fresh, current timestamps for lifecycle checks."""
    production = json.loads(
        (FIXTURES / "statnett_se_production_excerpt.json").read_text(encoding="utf-8")
    )["data"]
    flows = json.loads(
        (FIXTURES / "statnett_se_flows_excerpt.json").read_text(encoding="utf-8")
    )["data"]
    now = datetime.now(timezone.utc)
    production["MeasuredAt"] = now.isoformat()
    for source_key, rows in production.items():
        if source_key.endswith("Data") and isinstance(rows, list):
            for row in rows:
                row["measuredAt"] = now.isoformat()
    for row in flows:
        row["MeasureDate"] = int(now.timestamp() * 1000)
    return production, flows


@pytest.fixture
def source_payloads():
    """Provide isolated fixture payloads."""
    return _payloads()


@pytest.fixture
def mocked_statnett(source_payloads):
    """Intercept network at coordinator boundary; assert all route requests."""
    production, flows = source_payloads
    requested = []

    async def fake_get(self, path):
        requested.append(path)
        if path == PRODUCTION_PATH:
            return deepcopy(production)
        if path == FLOWS_PATH:
            return deepcopy(flows)
        raise AssertionError(f"Unexpected Statnett URL path: {path}")

    async def fake_reactor_update(self):
        now = datetime.now(timezone.utc)
        if self.plant == "oskarshamn":
            return parse_okg_o3({
                "value": 1432,
                "valueDate": now.astimezone(ZoneInfo("Europe/Stockholm")).strftime("%Y-%m-%dT%H:%M:%S"),
                "timestamp": now.isoformat(),
            }, now=now)
        html = (FIXTURES / f"vattenfall_{self.plant}_excerpt.html").read_text()
        html = html.replace("2026-11-14T22:00:00.206Z", now.isoformat())
        return parse_vattenfall_html(html, self.plant, now=now)

    with patch.object(SwedishPowerCoordinator, "_async_get_json", fake_get), patch.object(
        ReactorSourceCoordinator, "_async_update_data", fake_reactor_update
    ):
        yield requested, production, flows


async def _setup_entry(hass):
    """Set up a config entry and validate it loads."""
    entry = MockConfigEntry(
        domain=DOMAIN, title="Sweden", data={}, unique_id="sweden"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _sensor_states(hass, entry):
    registry = er.async_get(hass)
    records = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(records) == 14, [(r.entity_id, r.unique_id) for r in records]
    return {
        r.unique_id: hass.states.get(r.entity_id)
        for r in records if "_reactor_" not in r.unique_id
    }


def _reactor_states(hass, entry):
    registry = er.async_get(hass)
    records = er.async_entries_for_config_entry(registry, entry.entry_id)
    return {
        r.unique_id: hass.states.get(r.entity_id)
        for r in records if "_reactor_" in r.unique_id
    }


async def test_config_flow_creates_one_sweden_instance(hass, mocked_statnett):
    """Test real HA config flow and duplicate prevention."""
    initial = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert initial["type"] == FlowResultType.FORM
    assert initial["step_id"] == "user"
    created = await hass.config_entries.flow.async_configure(initial["flow_id"], {})
    assert created["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert created["title"] == "Sweden"

    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert second["type"] == FlowResultType.FORM
    duplicate = await hass.config_entries.flow.async_configure(second["flow_id"], {})
    assert duplicate["type"] == FlowResultType.ABORT
    assert duplicate["reason"] == "already_configured"


async def test_eight_entities_and_900_second_coordinator(hass, mocked_statnett):
    """Validate entity registry, source metadata and polling configuration."""
    requests, _, _ = mocked_statnett
    entry = await _setup_entry(hass)
    coordinator = entry.runtime_data.statnett
    assert coordinator.update_interval == UPDATE_INTERVAL
    assert coordinator.last_update_success
    assert requests.count(PRODUCTION_PATH) == 1
    assert requests.count(FLOWS_PATH) == 1

    states = _sensor_states(hass, entry)
    assert set(states) == {
        f"swedish_power_se_{key}" for key in (
            "production", "consumption", "net_exchange", "hydro", "wind",
            "nuclear", "thermal", "other"
        )
    }
    production_state = states["swedish_power_se_production"]
    assert production_state is not None
    assert float(production_state.state) == 20323
    assert production_state.attributes["unit_of_measurement"] == "MW"
    assert production_state.attributes["source"] == "Statnett Driftsdata"
    assert production_state.attributes["timestamp_basis"] == "row"
    assert len(coordinator.data.raw_flows) == 4
    reactors = _reactor_states(hass, entry)
    assert set(reactors) == {
        f"swedish_power_se_reactor_{name}_mw"
        for name in ("f1", "f2", "f3", "r3", "r4", "o3")
    }
    assert float(reactors["swedish_power_se_reactor_f1_mw"].state) == 0.032
    assert float(reactors["swedish_power_se_reactor_o3_mw"].state) == 1432
    assert reactors["swedish_power_se_reactor_f2_mw"].attributes["source"] == "Vattenfall"
    assert reactors["swedish_power_se_reactor_o3_mw"].attributes["source"] == "OKG"


async def test_reload_and_unload(hass, mocked_statnett):
    """Validate HA entry lifecycle and reloading without duplicate sensors."""
    entry = await _setup_entry(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    _sensor_states(hass, entry)


async def test_network_failure_marks_data_unavailable(hass, mocked_statnett):
    """A production API exception must not leave stale MW marked available."""
    entry = await _setup_entry(hass)
    coordinator = entry.runtime_data.statnett
    assert coordinator.last_update_success

    async def failing(_path):
        raise TimeoutError("test network loss")

    with patch.object(coordinator, "_async_get_json", failing):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert coordinator.last_update_success is False
    states = _sensor_states(hass, entry)
    assert all(state is not None and state.state == "unavailable" for state in states.values())


async def test_optional_flow_failure_keeps_national_sensors(hass, mocked_statnett):
    """Flow API failure must not discard valid production observations."""
    entry = await _setup_entry(hass)
    coordinator = entry.runtime_data.statnett
    original_get = coordinator._async_get_json

    async def flaky(path):
        if path == FLOWS_PATH:
            raise TimeoutError("test optional flow failure")
        return await original_get(path)

    with patch.object(coordinator, "_async_get_json", flaky):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert coordinator.last_update_success is True
    assert coordinator.data.flow_error == "TimeoutError"
    assert len(coordinator.data.raw_flows) == 0
    assert float(_sensor_states(hass, entry)["swedish_power_se_production"].state) == 20323


async def test_source_staleness_marks_mw_unavailable(hass, mocked_statnett):
    """A successful poll with old source data must not refresh timestamps."""
    _, production, _ = mocked_statnett
    entry = await _setup_entry(hass)
    production["MeasuredAt"] = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
    for name, rows in production.items():
        if name.endswith("Data") and isinstance(rows, list):
            for row in rows:
                row["measuredAt"] = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
    coordinator = entry.runtime_data.statnett
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    states = _sensor_states(hass, entry)
    assert all(state is not None and state.state == "unavailable" for state in states.values())


async def test_failed_poll_recovers_on_next_success(hass, mocked_statnett):
    """After a transient Statnett timeout, the same sensors recover."""
    entry = await _setup_entry(hass)
    coordinator = entry.runtime_data.statnett
    original = coordinator._async_get_json

    async def timeout(_path):
        raise TimeoutError("temporary outage")

    with patch.object(coordinator, "_async_get_json", timeout):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert not coordinator.last_update_success
    assert _sensor_states(hass, entry)["swedish_power_se_production"].state == "unavailable"

    with patch.object(coordinator, "_async_get_json", original):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert coordinator.last_update_success
    assert float(_sensor_states(hass, entry)["swedish_power_se_production"].state) == 20323


async def test_malformed_production_response_fails_safely(hass, mocked_statnett):
    """A malformed successful HTTP response must not be displayed as data."""
    entry = await _setup_entry(hass)
    coordinator = entry.runtime_data.statnett
    original = coordinator._async_get_json

    async def malformed(path):
        if path == PRODUCTION_PATH:
            return {"ProductionData": "not-an-array"}
        return await original(path)

    with patch.object(coordinator, "_async_get_json", malformed):
        await coordinator.async_refresh()
        await hass.async_block_till_done()
    assert not coordinator.last_update_success
    assert all(
        state.state == "unavailable" for state in _sensor_states(hass, entry).values()
    )


async def test_diagnostics_do_not_include_raw_payload(hass, mocked_statnett):
    """Export compact source status without exposing full API responses."""
    from custom_components.swedish_power.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    entry = await _setup_entry(hass)
    info = await async_get_config_entry_diagnostics(hass, entry)
    assert info["scope"] == "SE"
    assert info["poll_interval_seconds"] == 900
    assert info["sweden_flow_count"] == 4
    assert len(info["readings"]) == 8
    assert info["readings"]["production"]["quality"] == "valid"
    assert "ProductionData" not in json.dumps(info)
    assert set(info["reactor_sources"]) == {"forsmark", "ringhals", "oskarshamn"}
    assert info["reactor_sources"]["oskarshamn"]["readings"]["O3"]["value_mw"] == 1432


async def test_first_refresh_failure_results_in_retry_state(hass, mocked_statnett):
    """A startup source outage should request retry, never mark setup successful."""
    from homeassistant.config_entries import ConfigEntryState

    async def no_network(self, path):
        raise TimeoutError("first refresh offline")

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Sweden",
        data={},
        unique_id="sweden",
    )
    entry.add_to_hass(hass)
    with patch.object(SwedishPowerCoordinator, "_async_get_json", no_network):
        result = await hass.config_entries.async_setup(entry.entry_id)
    assert not result
    assert entry.state == ConfigEntryState.SETUP_RETRY


async def test_okg_outage_is_isolated_and_recovers(hass, mocked_statnett):
    """One source outage cannot make Statnett or the other reactors unavailable."""
    entry = await _setup_entry(hass)
    source = entry.runtime_data.reactors["oskarshamn"]
    original = source._async_update_data

    async def failing():
        raise TimeoutError("mock O3 source outage")

    with patch.object(source, "_async_update_data", failing):
        await source.async_refresh()
        await hass.async_block_till_done()
    states = _reactor_states(hass, entry)
    assert states["swedish_power_se_reactor_o3_mw"].state == "unavailable"
    assert float(states["swedish_power_se_reactor_f2_mw"].state) == 1129.125
    assert float(_sensor_states(hass, entry)["swedish_power_se_production"].state) == 20323

    with patch.object(source, "_async_update_data", original):
        await source.async_refresh()
        await hass.async_block_till_done()
    assert float(_reactor_states(hass, entry)["swedish_power_se_reactor_o3_mw"].state) == 1432


async def test_forsmark_failure_is_independent_from_ringhals(hass, mocked_statnett):
    """When Forsmark is missing, Ringhals and O3 keep their own measurements."""
    entry = await _setup_entry(hass)
    source = entry.runtime_data.reactors["forsmark"]

    async def failing():
        raise TimeoutError("mock Forsmark source outage")

    with patch.object(source, "_async_update_data", failing):
        await source.async_refresh()
        await hass.async_block_till_done()

    states = _reactor_states(hass, entry)
    for name in ("f1", "f2", "f3"):
        assert states[f"swedish_power_se_reactor_{name}_mw"].state == "unavailable"
    assert states["swedish_power_se_reactor_r3_mw"].state in ("0", "0.0")
    assert float(states["swedish_power_se_reactor_o3_mw"].state) == 1432


async def test_null_reactor_mw_is_not_a_valid_zero(hass, mocked_statnett):
    """A missing F1 value becomes unavailable; another valid zero stays zero."""
    from dataclasses import replace
    entry = await _setup_entry(hass)
    source = entry.runtime_data.reactors["forsmark"]
    old = source.data
    new = replace(old, reactors={
        **old.reactors,
        "F1": replace(old.reactors["F1"], power_mw=None, quality="missing"),
    })
    source.async_set_updated_data(new)
    await hass.async_block_till_done()
    states = _reactor_states(hass, entry)
    assert states["swedish_power_se_reactor_f1_mw"].state == "unavailable"
    assert states["swedish_power_se_reactor_f3_mw"].state in ("0", "0.0")


async def test_reactors_do_not_duplicate_after_reload(hass, mocked_statnett):
    entry = await _setup_entry(hass)
    original_ids = set(_reactor_states(hass, entry))
    assert len(original_ids) == 6
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert set(_reactor_states(hass, entry)) == original_ids
