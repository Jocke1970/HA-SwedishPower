"""Offline tests for the research probe; no network/HA required."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from statnett_probe import mw, sweden_flows, sweden_production, utc_time  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
NOW = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)


class ProbeTests(unittest.TestCase):
    def production(self):
        return json.loads((FIX / "statnett_se_production_excerpt.json").read_text(encoding="utf-8"))

    def flows(self):
        return json.loads((FIX / "statnett_se_flows_excerpt.json").read_text(encoding="utf-8"))

    def test_production_and_net_exchange(self):
        result = sweden_production(self.production(), now=NOW)
        values = result["values"]
        self.assertEqual(values["production"]["value_mw"], 20323)
        self.assertEqual(values["consumption"]["value_mw"], 20753)
        self.assertEqual(result["checks"]["net_exchange_consumption_minus_production_mw"], 0)
        self.assertEqual(result["checks"]["generation_parts_minus_total_mw"], 1)
        self.assertEqual(values["production"]["quality"], "unknown_timestamp")
        self.assertEqual(values["hydro"]["quality"], "stale")

    def test_mw_placeholders_not_zero(self):
        for token in (None, "", "-", "–", "—", "oops", True):
            self.assertIsNone(mw(token))
        self.assertEqual(mw("0"), 0)
        self.assertEqual(mw("−220"), -220)
        self.assertEqual(mw("10\u202f109"), 10109)

    def test_missing_and_duplicates(self):
        data = self.production()
        data["data"]["NuclearData"][0]["value"] = "-"
        self.assertIsNone(sweden_production(data, now=NOW)["values"]["nuclear"]["value_mw"])
        data["data"]["WindData"].append({"countryCode": "SE", "value": "3"})
        with self.assertRaises(ValueError):
            sweden_production(data, now=NOW)

    def test_flow_extraction_keeps_raw_signed_values(self):
        result = sweden_flows(self.flows(), now=NOW)
        self.assertEqual(len(result["flows"]), 4)
        self.assertEqual(sum(f["area_type"] == "internal" for f in result["flows"]), 3)
        self.assertEqual(result["flows"][3]["value_mw_signed_raw"], -766.0917)
        self.assertIn("UNVERIFIED", result["sign_convention"])

    def test_timestamp_parsing(self):
        self.assertEqual(utc_time(1794664249000), "2026-11-14T13:50:49+00:00")
        self.assertEqual(utc_time("2026-11-14T12:30:00.0000000+00:00"), "2026-11-14T12:30:00+00:00")
        self.assertIsNone(utc_time("2026-11-14 13:30"))

    def test_future_timestamp(self):
        now = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(sweden_production(self.production(), now=now)["values"]["hydro"]["quality"], "future_timestamp")


if __name__ == "__main__":
    unittest.main()
