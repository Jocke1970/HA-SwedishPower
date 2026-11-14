"""Pure data model and strict parsers for Statnett Sweden data.

No Home Assistant imports: unit-testable without a running HA instance.
For v1, raw signed flows are retained ONLY as diagnostics; the sign
convention has not yet been verified and must not drive direction arrows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
import re
from typing import Any

from .const import MAX_CLOCK_SKEW, MAX_DATA_AGE, METRIC_FIELDS, SE_AREAS


@dataclass(frozen=True)
class PowerReading:
    """One source-labelled reported electrical power value."""

    value_mw: float | None
    measured_at: datetime | None
    timestamp_basis: str
    quality: str
    period_start_label: str | None = None
    period_end_label: str | None = None


@dataclass(frozen=True)
class ProductionSnapshot:
    """Country-level Swedish readings and original snapshot timestamp."""

    readings: dict[str, PowerReading]
    snapshot_at: datetime | None
    fetched_at: datetime

    @property
    def checks(self) -> dict[str, float]:
        """Return diagnostic residuals without silently adjusting the readings."""
        result: dict[str, float] = {}
        p = self.readings["production"].value_mw
        c = self.readings["consumption"].value_mw
        x = self.readings["net_exchange"].value_mw
        if None not in (p, c, x):
            result["consumption_minus_production_minus_exchange_mw"] = round(c - p - x, 3)
        parts = [self.readings[key].value_mw for key in ("hydro", "wind", "nuclear", "thermal", "other")]
        if p is not None and all(value is not None for value in parts):
            result["generation_parts_minus_total_mw"] = round(sum(parts) - p, 3)
        return result


@dataclass(frozen=True)
class RawFlow:
    """An area-pair flow; fields deliberately do not imply direction."""

    in_area_raw: str
    out_area_raw: str
    signed_value_mw_raw: float | None
    measured_at: datetime | None
    quality: str
    area_type: str


def parse_mw(value: Any) -> float | None:
    """Reject invalid/missing values without converting them to 0."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (float, int)):
        result = float(value)
    elif isinstance(value, str):
        cleaned = re.sub(r"[\s\u00a0\u202f]", "", value).replace("\u2212", "-")
        if not cleaned or cleaned in ("-", "–", "—"):
            return None
        try:
            result = float(cleaned)
        except ValueError:
            return None
    else:
        return None
    return result if isfinite(result) else None


def parse_timestamp(value: Any) -> datetime | None:
    """Accept offset-aware ISO timestamps or Unix milliseconds."""
    try:
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, (int, float)):
            if not isfinite(float(value)):
                return None
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        if not isinstance(value, str):
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def quality_of(
    value: float | None,
    at: datetime | None,
    now: datetime,
    max_age: timedelta = MAX_DATA_AGE,
) -> str:
    """Categorize each record using its source timestamp."""
    if value is None:
        return "missing"
    if at is None:
        return "unknown_timestamp"
    age = now - at
    if age < -MAX_CLOCK_SKEW:
        return "future_timestamp"
    if age > max_age:
        return "stale"
    return "valid"


def parse_production(
    payload: Any,
    *,
    now: datetime | None = None,
    max_age: timedelta = MAX_DATA_AGE,
) -> ProductionSnapshot:
    """Parse official direct JSON and only the 'SE' country rows.

    Rows without measuredAt are not silently assigned the current HA time.
    Aggregate rows may use the source *snapshot* timestamp, with provenance.
    """
    if not isinstance(payload, dict):
        raise ValueError("Statnett production response must be a JSON object")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")

    snapshot_at = parse_timestamp(payload.get("MeasuredAt"))
    readings: dict[str, PowerReading] = {}
    for key, source_field in METRIC_FIELDS.items():
        rows = payload.get(source_field)
        if not isinstance(rows, list):
            raise ValueError(f"Invalid or missing source category: {source_field}")
        matches = [row for row in rows if isinstance(row, dict) and row.get("countryCode") == "SE"]
        if len(matches) > 1:
            raise ValueError(f"Duplicate Swedish rows in {source_field}")
        row = matches[0] if matches else {}
        value = parse_mw(row.get("value"))
        measured_at = parse_timestamp(row.get("measuredAt"))
        basis = "row" if measured_at else "missing"
        # Both these source aggregate rows had null measuredAt in direct testing.
        if measured_at is None and key in ("production", "net_exchange") and snapshot_at:
            measured_at = snapshot_at
            basis = "snapshot"
        readings[key] = PowerReading(
            value_mw=value,
            measured_at=measured_at,
            timestamp_basis=basis,
            quality=quality_of(value, measured_at, now, max_age),
            period_start_label=row.get("periodStart") or None,
            period_end_label=row.get("periodEnd") or None,
        )

    return ProductionSnapshot(readings=readings, snapshot_at=snapshot_at, fetched_at=now)


def parse_flows(
    payload: Any,
    *,
    now: datetime | None = None,
    max_age: timedelta = MAX_DATA_AGE,
) -> tuple[RawFlow, ...]:
    """Select Swedish flows only, preserving raw signs and endpoints."""
    if not isinstance(payload, list):
        raise ValueError("Statnett physical flow response must be a JSON array")
    now = now or datetime.now(timezone.utc)
    result: list[RawFlow] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        a, b = row.get("InAreaElspotId"), row.get("OutAreaElspotId")
        if a not in SE_AREAS and b not in SE_AREAS:
            continue
        if not isinstance(a, str) or not isinstance(b, str):
            continue
        val = parse_mw(row.get("Value"))
        when = parse_timestamp(row.get("MeasureDate"))
        result.append(
            RawFlow(
                in_area_raw=a,
                out_area_raw=b,
                signed_value_mw_raw=val,
                measured_at=when,
                quality=quality_of(val, when, now, max_age),
                area_type="internal" if a in SE_AREAS and b in SE_AREAS else "cross_border",
            )
        )
    return tuple(result)
