"""Independent parser checks for official OKG O3 read-only output."""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest

ROOT=Path(__file__).resolve().parents[1]
COMPONENT=ROOT/"custom_components"/"swedish_power"
if "swedish_power" not in sys.modules:
    stub=ModuleType("swedish_power")
    stub.__path__=[str(COMPONENT)]
    sys.modules["swedish_power"]=stub
from swedish_power.okg import parse_okg_o3

SOURCE=json.loads((ROOT/"tests"/"fixtures"/"okg_o3_excerpt.json").read_text())
NOW=datetime(2026,11,14,22,18,tzinfo=timezone.utc)


class OkgTests(unittest.TestCase):
    def test_live_observed_source_timezone(self):
        x=parse_okg_o3(SOURCE,now=NOW)
        self.assertEqual(x.value_mw,1432)
        self.assertEqual(x.measured_at.isoformat(),"2026-11-14T22:17:00+00:00")
        self.assertEqual(x.quality,"valid")
        self.assertEqual(x.timestamp_basis,"valueDate_local_Europe/Stockholm")

    def test_real_zero_is_valid(self):
        x=parse_okg_o3({**SOURCE,"value":0},now=NOW)
        self.assertEqual(x.value_mw,0)
        self.assertEqual(x.quality,"valid")

    def test_null_is_missing(self):
        x=parse_okg_o3({**SOURCE,"value":None},now=NOW)
        self.assertIsNone(x.value_mw)
        self.assertEqual(x.quality,"missing")

    def test_bad_value_date_not_replaced_with_fetch_time(self):
        x=parse_okg_o3({**SOURCE,"valueDate":"broken"},now=NOW)
        self.assertIsNone(x.measured_at)
        self.assertEqual(x.quality,"unknown_timestamp")

    def test_missing_api_timestamp_makes_naive_value_date_unverified(self):
        x=parse_okg_o3({**SOURCE,"timestamp":None},now=NOW)
        self.assertIsNone(x.measured_at)
        self.assertEqual(x.quality,"unknown_timestamp")

    def test_stale_source(self):
        x=parse_okg_o3(SOURCE,now=NOW+timedelta(hours=3))
        self.assertEqual(x.quality,"stale")

    def test_autumn_dst_ambiguous_hour_uses_api_utc_time(self):
        # Sweden local 02:20 occurs twice on 2026-10-25.
        src={ "value":900, "valueDate":"2026-10-25T02:20:00",
              "timestamp":"2026-10-25T01:20:29Z"}
        x=parse_okg_o3(src,now=datetime(2026,10,25,1,21,tzinfo=timezone.utc))
        self.assertEqual(x.measured_at,datetime(2026,10,25,1,20,tzinfo=timezone.utc))
        self.assertEqual(x.quality,"valid")

    def test_spring_gap_is_unknown(self):
        src={"value":100,"valueDate":"2026-03-29T02:30:00","timestamp":"2026-03-29T01:30:00Z"}
        x=parse_okg_o3(src,now=datetime(2026,3,29,1,31,tzinfo=timezone.utc))
        self.assertEqual(x.quality,"unknown_timestamp")

    def test_inconsistent_utc_and_stockholm_clock_is_not_current(self):
        x=parse_okg_o3({**SOURCE,"timestamp":"2026-11-14T19:17:39Z"},now=NOW)
        self.assertEqual(x.quality,"unknown_timestamp")

    def test_invalid_root(self):
        with self.assertRaises(ValueError):
            parse_okg_o3([],now=NOW)


if __name__=="__main__":
    unittest.main()
