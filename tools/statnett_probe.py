"""One-shot, read-only Statnett probe for HA-SwedishPower issue #1.

Stdlib only. This is NOT a Home Assistant integration or periodic poller.
The normalized output describes source fields; directional flow signs remain raw.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

PRODUCTION_URL = "https://driftsdata.statnett.no/restapi/ProductionConsumption/GetLatestDetailedOverview"
FLOWS_URL = "https://driftsdata.statnett.no/restapi/PhysicalFlowMap/GetFlow"
CATEGORIES = {
    "production": "ProductionData",
    "consumption": "ConsumptionData",
    "net_exchange": "NetExchangeData",
    "hydro": "HydroData",
    "wind": "WindData",
    "nuclear": "NuclearData",
    "thermal": "ThermalData",
    "other": "NotSpecifiedData",
}
SE_AREAS = {"SE1", "SE2", "SE3", "SE4"}


def mw(value):
    """Parse display MW, preserving absent/placeholder data as None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (float, int)):
        return float(value)
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"[\s\u00a0\u202f]", "", value).replace("\u2212", "-")
    if cleaned in ("", "-", "–", "—"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def utc_time(value):
    """Parse source UTC ISO timestamp or Unix milliseconds, if valid."""
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (float, int)) and not isinstance(value, bool):
            return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat()
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def unwrap(payload):
    if isinstance(payload, dict) and isinstance(payload.get("data"), (list, dict)):
        return payload["data"]
    return payload


def sweden_production(payload, now=None, max_age_minutes=90):
    data = unwrap(payload)
    if not isinstance(data, dict):
        raise ValueError("Expected production JSON object")
    now = now or datetime.now(timezone.utc)
    result = {"source": "statnett_candidate", "scope": "SE", "unit": "MW", "values": {},
              "snapshot_reported_at": utc_time(data.get("MeasuredAt")), "checks": {}}
    for key, field in CATEGORIES.items():
        rows = data.get(field, [])
        matches = [r for r in rows if isinstance(r, dict) and r.get("countryCode") == "SE"] if isinstance(rows, list) else []
        if len(matches) > 1:
            raise ValueError(f"Duplicate SE rows in {field}")
        item = matches[0] if matches else {}
        value = mw(item.get("value"))
        at = utc_time(item.get("measuredAt"))
        quality = "missing" if value is None else "unknown_timestamp" if at is None else "valid"
        if at and value is not None:
            age = (now - datetime.fromisoformat(at)).total_seconds() / 60
            if age > max_age_minutes:
                quality = "stale"
            if age < -10:
                quality = "future_timestamp"
        result["values"][key] = {"value_mw": value, "measured_at": at,
                                 "period_start_label": item.get("periodStart") or None,
                                 "period_end_label": item.get("periodEnd") or None,
                                 "quality": quality}
    p = result["values"]["production"]["value_mw"]
    c = result["values"]["consumption"]["value_mw"]
    n = result["values"]["net_exchange"]["value_mw"]
    if None not in (p, c, n):
        result["checks"]["net_exchange_consumption_minus_production_mw"] = round(c - p - n, 3)
    parts = [result["values"][k]["value_mw"] for k in ("hydro", "wind", "nuclear", "thermal", "other")]
    if p is not None and all(v is not None for v in parts):
        result["checks"]["generation_parts_minus_total_mw"] = round(sum(parts) - p, 3)
    return result


def sweden_flows(payload, now=None, max_age_minutes=90):
    rows = unwrap(payload)
    if not isinstance(rows, list):
        raise ValueError("Expected flow JSON array")
    now = now or datetime.now(timezone.utc)
    results = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        a, b = row.get("InAreaElspotId"), row.get("OutAreaElspotId")
        if a not in SE_AREAS and b not in SE_AREAS:
            continue
        value = mw(row.get("Value"))
        at = utc_time(row.get("MeasureDate"))
        quality = "missing" if value is None else "unknown_timestamp" if at is None else "valid"
        if at and value is not None:
            age = (now - datetime.fromisoformat(at)).total_seconds() / 60
            if age > max_age_minutes:
                quality = "stale"
            if age < -10:
                quality = "future_timestamp"
        results.append({"in_area_raw": a, "out_area_raw": b, "value_mw_signed_raw": value,
                        "measured_at": at, "quality": quality,
                        "area_type": "internal" if a in SE_AREAS and b in SE_AREAS else "cross_border"})
    return {"scope": "Swedish flow pairs", "sign_convention": "UNVERIFIED — no arrows",
            "flows": results}


def fetch_json(url):
    # This is a one-shot discovery command, not automatic HA polling.
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "HA-SwedishPower-source-probe/0.1"})
    with urlopen(request, timeout=12) as response:
        body = response.read(2_000_000)
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type.lower():
            raise ValueError(f"Unexpected Content-Type {content_type!r}; HTTP {response.status}")
        return json.loads(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production-file", type=Path, help="Offline production fixture; skips live production fetch")
    parser.add_argument("--flows-file", type=Path, help="Offline flow fixture; skips live flows fetch")
    parser.add_argument("--max-age-minutes", type=int, default=90, help="Provisional display freshness threshold")
    args = parser.parse_args()
    try:
        p = json.loads(args.production_file.read_text(encoding="utf-8")) if args.production_file else fetch_json(PRODUCTION_URL)
        f = json.loads(args.flows_file.read_text(encoding="utf-8")) if args.flows_file else fetch_json(FLOWS_URL)
        result = {"production": sweden_production(p, max_age_minutes=args.max_age_minutes),
                  "flows": sweden_flows(f, max_age_minutes=args.max_age_minutes)}
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Probe failed (no data accepted): {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
