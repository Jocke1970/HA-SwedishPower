"""No-Home-Assistant parser tests for the five Vattenfall reactors."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
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

from swedish_power.vattenfall import parse_vattenfall_html

FIXTURES = ROOT / "tests" / "fixtures"
NOW = datetime(2026, 11, 14, 22, 11, tzinfo=timezone.utc)


def fixture(plant):
    return (FIXTURES / f"vattenfall_{plant}_excerpt.html").read_text(encoding="utf-8")


def transform(html, fn):
    start = html.index('{"powerPlant"')
    end = html.index('</script>', start)
    obj = json.loads(html[start:end])
    fn(obj)
    return html[:start] + json.dumps(obj) + "\n" + html[end:]


class VattenfallTests(unittest.TestCase):
    def test_real_observed_forsmark_shape_and_decimal_preservation(self):
        snapshot = parse_vattenfall_html(fixture("forsmark"), "forsmark", now=NOW)
        self.assertEqual(list(snapshot.reactors), ["F1", "F2", "F3"])
        self.assertEqual(snapshot.reactors["F1"].power_mw, 0.032)
        self.assertEqual(snapshot.reactors["F2"].power_mw, 1129.125)
        self.assertEqual(snapshot.reactors["F3"].power_mw, 0)
        self.assertEqual(snapshot.reactors["F3"].quality, "valid")
        self.assertEqual(snapshot.measured_at.isoformat(), "2026-11-14T22:00:00.206000+00:00")

    def test_real_observed_ringhals_shape(self):
        snap = parse_vattenfall_html(fixture("ringhals"), "ringhals", now=NOW)
        self.assertEqual(list(snap.reactors), ["R3", "R4"])
        self.assertEqual([r.quality for r in snap.reactors.values()], ["valid", "valid"])

    def test_missing_null_nan_and_unknown_unit_do_not_become_zero(self):
        def mutate(p):
            p["blockProductionDataList"][0]["production"] = None
            p["blockProductionDataList"][1]["production"] = "NaN"
            p["blockProductionDataList"][2]["unit"] = "kW"
        snap = parse_vattenfall_html(transform(fixture("forsmark"), mutate), "forsmark", now=NOW)
        self.assertIsNone(snap.reactors["F1"].power_mw)
        self.assertEqual(snap.reactors["F1"].quality, "missing")
        self.assertIsNone(snap.reactors["F2"].power_mw)
        self.assertEqual(snap.reactors["F3"].quality, "unexpected_unit")

    def test_missing_block_is_missing_not_zero(self):
        def mutate(p):
            p["blockProductionDataList"] = p["blockProductionDataList"][:1]
        snap = parse_vattenfall_html(transform(fixture("forsmark"), mutate), "forsmark", now=NOW)
        self.assertIsNone(snap.reactors["F2"].power_mw)
        self.assertEqual(snap.reactors["F2"].quality, "missing")

    def test_stale_source_timestamp_even_if_fetched_recently(self):
        late = NOW + timedelta(hours=2)
        snap = parse_vattenfall_html(fixture("forsmark"), "forsmark", now=late)
        self.assertEqual(snap.reactors["F2"].quality, "stale")

    def test_missing_or_future_timestamp_is_not_valid(self):
        def missing(p):
            p["timestamp"] = None
        snap = parse_vattenfall_html(transform(fixture("ringhals"), missing), "ringhals", now=NOW)
        self.assertEqual(snap.reactors["R3"].quality, "unknown_timestamp")
        def future(p):
            p["timestamp"] = "2026-11-15T00:00:00+00:00"
        snap = parse_vattenfall_html(transform(fixture("ringhals"), future), "ringhals", now=NOW)
        self.assertEqual(snap.reactors["R3"].quality, "future_timestamp")

    def test_duplicate_id_and_bad_schema_raise(self):
        def dup(p):
            p["blockProductionDataList"].append(dict(p["blockProductionDataList"][0]))
        with self.assertRaises(ValueError):
            parse_vattenfall_html(transform(fixture("forsmark"), dup), "forsmark", now=NOW)
        def bad(p):
            p["blockProductionDataList"] = "error"
        with self.assertRaises(ValueError):
            parse_vattenfall_html(transform(fixture("forsmark"), bad), "forsmark", now=NOW)

    def test_only_labeled_embedded_json_is_accepted(self):
        with self.assertRaises(ValueError):
            parse_vattenfall_html("<script>window.data={}</script>", "ringhals", now=NOW)
        with self.assertRaises(ValueError):
            parse_vattenfall_html(fixture("ringhals"), "oskarshamn", now=NOW)


if __name__ == "__main__":
    unittest.main()
