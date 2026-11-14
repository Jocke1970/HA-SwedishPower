"""Offline tests for the Sweden-only integration parser (no HA runtime)."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest

# Import the dependency-free parser without importing Home Assistant __init__.
COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "swedish_power"
package = ModuleType("swedish_power")
package.__path__ = [str(COMPONENT)]
sys.modules.setdefault("swedish_power", package)

from swedish_power.model import (  # noqa: E402
    parse_flows,
    parse_mw,
    parse_production,
    parse_timestamp,
)

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 14, 13, 35, tzinfo=timezone.utc)


class BackendModelTests(unittest.TestCase):
    def production(self):
        # Third-party-derived EXAMPLE, not a directly captured original JSON.
        return json.loads((FIXTURES / "statnett_se_production_excerpt.json").read_text())["data"]

    def flows(self):
        return json.loads((FIXTURES / "statnett_se_flows_excerpt.json").read_text())["data"]

    def test_sweden_production_is_eight_metrics(self):
        snapshot = parse_production(self.production(), now=NOW)
        self.assertEqual(len(snapshot.readings), 8)
        self.assertEqual(snapshot.readings["production"].value_mw, 20323)
        self.assertEqual(snapshot.readings["nuclear"].value_mw, 2503)
        self.assertEqual(snapshot.readings["hydro"].value_mw, 10109)
        self.assertEqual(snapshot.readings["wind"].value_mw, 6201)
        self.assertEqual(snapshot.checks["consumption_minus_production_minus_exchange_mw"], 0)
        self.assertEqual(snapshot.checks["generation_parts_minus_total_mw"], 1)

    def test_snapshot_timestamp_fallback_is_not_hass_now(self):
        snapshot = parse_production(self.production(), now=NOW)
        prod = snapshot.readings["production"]
        self.assertEqual(prod.timestamp_basis, "snapshot")
        self.assertEqual(prod.measured_at, parse_timestamp(1794660300000))
        self.assertEqual(prod.quality, "valid")

    def test_missing_snapshot_timestamp_makes_aggregate_unavailable(self):
        payload = self.production()
        payload["MeasuredAt"] = None
        snapshot = parse_production(payload, now=NOW)
        prod = snapshot.readings["production"]
        self.assertEqual(prod.quality, "unknown_timestamp")
        self.assertIsNone(prod.measured_at)

    def test_older_source_data_is_stale_even_after_new_fetch(self):
        payload = self.production()
        payload["MeasuredAt"] = "2026-11-14T11:00:00+00:00"
        payload["NuclearData"][0]["measuredAt"] = "2026-11-14T10:00:00+00:00"
        snapshot = parse_production(payload, now=NOW, max_age=timedelta(minutes=90))
        self.assertEqual(snapshot.readings["production"].quality, "stale")
        self.assertEqual(snapshot.readings["nuclear"].quality, "stale")

    def test_invalid_value_is_missing_not_zero(self):
        payload = self.production()
        payload["NuclearData"][0]["value"] = "–"
        snapshot = parse_production(payload, now=NOW)
        self.assertEqual(snapshot.readings["nuclear"].quality, "missing")
        self.assertIsNone(snapshot.readings["nuclear"].value_mw)
        self.assertNotIn("generation_parts_minus_total_mw", snapshot.checks)
        for invalid in ("–", "-", "NaN", "inf", "", None, True):
            self.assertIsNone(parse_mw(invalid))
        self.assertEqual(parse_mw("0"), 0)
        self.assertEqual(parse_mw("−220"), -220)

    def test_duplicate_se_rows_and_invalid_schema_fail(self):
        payload = self.production()
        payload["WindData"].append({"countryCode": "SE", "value": "500"})
        with self.assertRaises(ValueError):
            parse_production(payload, now=NOW)
        with self.assertRaises(ValueError):
            parse_production([], now=NOW)
        payload = self.production()
        payload["HydroData"] = {}
        with self.assertRaises(ValueError):
            parse_production(payload, now=NOW)

    def test_future_and_naive_timestamps(self):
        self.assertIsNone(parse_timestamp("2026-11-14T12:30:00"))
        self.assertIsNone(parse_timestamp(True))
        payload = self.production()
        payload["MeasuredAt"] = "2026-11-14T15:30:00+00:00"
        self.assertEqual(parse_production(payload, now=NOW).readings["production"].quality, "future_timestamp")

    def test_flows_preserve_raw_sign_and_filter_sweden(self):
        rows = parse_flows(self.flows(), now=NOW)
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(r.area_type == "internal" for r in rows), 3)
        self.assertEqual(sum(r.area_type == "cross_border" for r in rows), 1)
        self.assertEqual(rows[-1].signed_value_mw_raw, -766.0917)
        self.assertEqual(rows[0].in_area_raw, "SE2")

    def test_missing_country_row_stays_missing(self):
        payload = self.production()
        payload["HydroData"] = [{"countryCode": "NO", "value": "20000"}]
        self.assertEqual(parse_production(payload, now=NOW).readings["hydro"].quality, "missing")


if __name__ == "__main__":
    unittest.main()
