"""Conservative pure-parser for Nord Pool UMM Swedish nuclear production notices.

Discovery verified a public HTTP 200 response from:
https://ummapi.nordpoolgroup.com/messages?messageTypes=1&fuelTypes=14

NOT YET connected to Home Assistant entities. Notice period membership does not
prove a reactor fault, current output, or definitive operating status.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any

from .model import parse_mw, parse_timestamp

UMM_ENDPOINT = "https://ummapi.nordpoolgroup.com/messages"
SWEDISH_ZONES = frozenset({"SE1", "SE2", "SE3", "SE4"})
SWEDISH_REACTORS = frozenset({"F1", "F2", "F3", "R3", "R4", "O3"})
UMM_PRODUCTION_TYPE = 1
UMM_NUCLEAR_FUEL_TYPE = 14


def reactor_id_for_unit(name: Any) -> str | None:
    """Match known Swedish operating units only; no fuzzy cross-country guesses."""
    if not isinstance(name, str):
        return None
    cleaned = re.sub(r"[_\-\s]+", " ", name).strip().casefold()
    short = re.fullmatch(r"([fro])\s*([1-4])", cleaned)
    if short:
        candidate = short.group(1).upper() + short.group(2)
        return candidate if candidate in SWEDISH_REACTORS else None
    long = re.fullmatch(
        r"(forsmark|ringhals|oskarshamn)\s*(?:(?:block|unit|reaktor|reactor)\s*)?([1-4])",
        cleaned,
    )
    if not long:
        return None
    prefix = {"forsmark": "F", "ringhals": "R", "oskarshamn": "O"}[long.group(1)]
    result = prefix + long.group(2)
    return result if result in SWEDISH_REACTORS else None


@dataclass(frozen=True)
class UMMNoticePeriod:
    """A source-reported notice period, NOT a verified outage classification."""

    reactor_id: str
    raw_unit_name: str
    zone: str
    message_id: str
    message_version: str | None
    published_at: datetime | None
    event_start: datetime | None
    event_end: datetime | None
    available_capacity_mw: float | None
    unavailable_capacity_mw: float | None
    installed_capacity_mw: float | None
    event_status_raw: str | int | None
    unavailability_type_raw: str | int | None
    unavailability_reason_raw: str | int | None
    reason_code_raw: str | int | None
    period_position: str


def _position(start: datetime | None, end: datetime | None, now: datetime) -> str:
    """Describe a schedule window, never infer actual operating status."""
    if start is None:
        return "unknown_time"
    if end is not None and end <= start:
        return "invalid_window"
    if now < start:
        return "upcoming_window"
    if end is not None and now >= end:
        return "ended_window"
    return "inside_reported_window"


def parse_umm_nuclear_sweden(
    payload: Any,
    *,
    now: datetime | None = None,
    include_outdated: bool = False,
) -> tuple[UMMNoticePeriod, ...]:
    """Select Swedish current-unit nuclear production notices without aggregation.

    No deduping or 'total unavailable' calculation is done here: versions,
    cancellations and overlapping periods require explicit reconciliation.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("Nord Pool UMM must contain an items array")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must have a UTC offset")
    records: list[UMMNoticePeriod] = []
    for message in payload["items"]:
        if not isinstance(message, dict):
            continue
        if message.get("messageType") != UMM_PRODUCTION_TYPE:
            continue
        if not include_outdated and message.get("isOutdated") is True:
            continue
        mid = message.get("messageId")
        if not isinstance(mid, (str, int)) or isinstance(mid, bool):
            continue
        for unit in message.get("productionUnits") or []:
            if not isinstance(unit, dict):
                continue
            if unit.get("fuelType") != UMM_NUCLEAR_FUEL_TYPE:
                continue
            zone = unit.get("areaName")
            if zone not in SWEDISH_ZONES:
                continue
            name = unit.get("name")
            reactor_id = reactor_id_for_unit(name)
            if reactor_id is None:
                continue
            for period in unit.get("timePeriods") or []:
                if not isinstance(period, dict):
                    continue
                start = parse_timestamp(period.get("eventStart"))
                end = parse_timestamp(period.get("eventStop"))
                # If a stop exists but cannot be parsed, report unknown,
                # not an indefinitely active event.
                if period.get("eventStop") is not None and end is None:
                    position = "unknown_time"
                else:
                    position = _position(start, end, now)
                records.append(UMMNoticePeriod(
                    reactor_id=reactor_id,
                    raw_unit_name=name,
                    zone=zone,
                    message_id=str(mid),
                    message_version=str(message["version"]) if message.get("version") is not None else None,
                    published_at=parse_timestamp(message.get("publicationDate")),
                    event_start=start,
                    event_end=end,
                    available_capacity_mw=parse_mw(period.get("availableCapacity")),
                    unavailable_capacity_mw=parse_mw(period.get("unavailableCapacity")),
                    installed_capacity_mw=parse_mw(unit.get("installedCapacity")),
                    event_status_raw=message.get("eventStatus"),
                    unavailability_type_raw=message.get("unavailabilityType"),
                    unavailability_reason_raw=message.get("unavailabilityReason"),
                    reason_code_raw=message.get("reasonCode"),
                    period_position=position,
                ))
    return tuple(records)
