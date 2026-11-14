"""Strict synthetic schema tests for UMM notice normalization (no live API)."""

from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "swedish_power"
if "swedish_power" not in sys.modules:
    stub = ModuleType("swedish_power")
    stub.__path__ = [str(COMPONENT)]
    sys.modules["swedish_power"] = stub
from swedish_power.umm import reactor_id_for_unit, parse_umm_nuclear_sweden

NOW = datetime(2026, 11, 14, 13, 0, tzinfo=timezone.utc)
PAYLOAD = json.loads((ROOT / "tests" / "fixtures" / "nordpool_umm_nuclear_synthetic.json").read_text())


class UmmTests(unittest.TestCase):
    def test_swedish_unit_alias_matching_without_guessing(self):
        for name, expected in [
            ("Forsmark Block3", "F3"), ("Forsmark block 1", "F1"),
            ("Ringhals block4", "R4"), ("Oskarshamn Block 3", "O3"),
            ("F2", "F2"), ("R 3", "R3"),
        ]:
            self.assertEqual(reactor_id_for_unit(name), expected)
        for bad in ("Ringhals Block 2", "Oskarshamn 2", "Olkiluoto Block 3", "", "Forsmark 5", None):
            self.assertIsNone(reactor_id_for_unit(bad))

    def test_filters_fi_and_outdated(self):
        records = parse_umm_nuclear_sweden(PAYLOAD, now=NOW)
        self.assertEqual([p.reactor_id for p in records], ["F3", "O3"])

    def test_distinguishes_notice_schedule_from_operational_status(self):
        records = parse_umm_nuclear_sweden(PAYLOAD, now=NOW)
        self.assertEqual(records[0].period_position, "inside_reported_window")
        self.assertEqual(records[1].period_position, "upcoming_window")
        self.assertEqual(records[0].unavailable_capacity_mw, 1172)
        self.assertEqual(records[0].event_status_raw, 1)

    def test_outdated_available_only_when_explicit(self):
        records = parse_umm_nuclear_sweden(PAYLOAD, now=NOW, include_outdated=True)
        self.assertEqual({p.reactor_id for p in records}, {"F3", "R3", "O3"})

    def test_invalid_stop_is_unknown_not_an_open_ended_outage(self):
        raw = json.loads(json.dumps(PAYLOAD))
        raw["items"][0]["productionUnits"][0]["timePeriods"][0]["eventStop"] = "bad-time"
        self.assertEqual(parse_umm_nuclear_sweden(raw, now=NOW)[0].period_position, "unknown_time")

    def test_zero_and_missing_capacity_differ(self):
        raw = json.loads(json.dumps(PAYLOAD))
        p = raw["items"][0]["productionUnits"][0]["timePeriods"][0]
        p["unavailableCapacity"] = None
        p["availableCapacity"] = 0
        notice = parse_umm_nuclear_sweden(raw, now=NOW)[0]
        self.assertIsNone(notice.unavailable_capacity_mw)
        self.assertEqual(notice.available_capacity_mw, 0)

    def test_invalid_payload_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_umm_nuclear_sweden({"items": "bad"}, now=NOW)

    def test_ended_window(self):
        raw = json.loads(json.dumps(PAYLOAD))
        raw["items"][0]["productionUnits"][0]["timePeriods"][0]["eventStop"] = "2026-11-14T12:00:00Z"
        self.assertEqual(parse_umm_nuclear_sweden(raw, now=NOW)[0].period_position, "ended_window")


if __name__ == "__main__":
    unittest.main()
