"""Isolated OKG Oskarshamn 3 source adapter; not enabled in HA yet.

Source discovered in OKG's public production-meter JavaScript, 2026-11-14:
https://okg.se/.netlify/functions/getReactorOutput
JSON observed with fields value, valueDate (naive local time), timestamp (UTC).
The official OKG site labels its O3 gauge as MW. Source reuse terms pending.

Do not silently convert valueDate to UTC or use fetch time as measured time.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo

from .const import REQUEST_TIMEOUT_SECONDS
from .model import parse_mw, parse_timestamp, quality_of

OKG_URL = "https://okg.se/.netlify/functions/getReactorOutput"
OKG_LOCAL_ZONE = ZoneInfo("Europe/Stockholm")


@dataclass(frozen=True)
class OkgO3Reading:
    """Measured output with explicitly documented local-time interpretation."""

    value_mw: float | None
    quality: str
    measured_at: datetime | None
    api_timestamp: datetime | None
    fetched_at: datetime
    timestamp_basis: str = "valueDate_local_Europe/Stockholm"
    source_unit_basis: str = "MW displayed by OKG website"


def _parse_value_date_local(value: Any, api_at: datetime | None) -> datetime | None:
    """Resolve naive OKG local wall clock using the API's UTC time for DST.

    The probe observed valueDate='2026-11-14T23:17:00' and
    timestamp='2026-11-14T22:17:39Z', i.e. Stockholm time.
    If the API and local times diverge too far, reject rather than mislabel.
    """
    if not isinstance(value, str):
        return None
    try:
        local = datetime.fromisoformat(value)
    except ValueError:
        return None
    if local.tzinfo is not None:
        return local.astimezone(timezone.utc)
    if api_at is None:
        # Cannot disambiguate the repeated autumn 02:00 hour with no UTC anchor.
        return None
    candidates: set[datetime] = set()
    for fold in (0, 1):
        aware = local.replace(tzinfo=OKG_LOCAL_ZONE, fold=fold)
        utc = aware.astimezone(timezone.utc)
        # Reject impossible local clock times during DST spring transition.
        if utc.astimezone(OKG_LOCAL_ZONE).replace(tzinfo=None) == local:
            candidates.add(utc)
    if not candidates:
        return None
    nearest = min(candidates, key=lambda utc: abs((api_at - utc).total_seconds()))
    # An OKG API timestamp may lag the source by minutes, but not by hours.
    if abs((api_at - nearest).total_seconds()) > 15 * 60:
        return None
    return nearest


def parse_okg_o3(payload: Any, *, now: datetime | None = None) -> OkgO3Reading:
    """Handle source-reported zeros, missing values and independent timestamps."""
    if not isinstance(payload, dict):
        raise ValueError("OKG O3 data must be a JSON object")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    api_at = parse_timestamp(payload.get("timestamp"))
    value = parse_mw(payload.get("value"))
    measured_at = _parse_value_date_local(payload.get("valueDate"), api_at)
    quality = quality_of(value, measured_at, now)
    return OkgO3Reading(
        value_mw=value,
        quality=quality,
        measured_at=measured_at,
        api_timestamp=api_at,
        fetched_at=now,
    )


async def async_fetch_okg_o3(session: Any) -> OkgO3Reading:
    """Fetch one JSON payload; OKG serves JSON under text/plain MIME type."""
    async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
        async with session.get(
            OKG_URL, headers={"Accept": "application/json", "User-Agent": "HA-SwedishPower-Research/0.1"}
        ) as response:
            response.raise_for_status()
            if response.content_type not in ("text/plain", "application/json"):
                raise ValueError("Unexpected OKG response content type")
            document = await response.text()
    if len(document) > 10_000:
        raise ValueError("Unexpectedly large OKG source response")
    try:
        payload = json.loads(document)
    except (ValueError, TypeError) as exc:
        raise ValueError("Malformed OKG O3 JSON") from exc
    return parse_okg_o3(payload)
