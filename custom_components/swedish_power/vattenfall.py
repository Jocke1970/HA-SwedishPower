"""Source adapter for Vattenfall's official Forsmark and Ringhals production pages.

Pure parsing and async HTTP: no HA-specific imports and no dependency on
third-party scraping packages. The source's observed embedded JSON contract
was independently checked against both plants on 2026-11-14.

This adapter reports *power observations*, never inferred outage status.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import json
from typing import Any

from .const import MAX_DATA_AGE, REQUEST_TIMEOUT_SECONDS
from .model import parse_mw, parse_timestamp, quality_of

VATTENFALL_URLS: dict[str, str] = {
    "forsmark": "https://karnkraft.vattenfall.se/forsmark/produktion/",
    "ringhals": "https://karnkraft.vattenfall.se/ringhals/produktion/",
}
VATTENFALL_REACTORS: dict[str, tuple[str, ...]] = {
    "forsmark": ("F1", "F2", "F3"),
    "ringhals": ("R3", "R4"),
}


class _DataJsonScripts(HTMLParser):
    """Collect JSON from marked script elements, independent of attribute order."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._inside = False
        self._parts: list[str] = []
        self.contents: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script" or self._inside:
            return
        if any(key.lower() == "data-json-data" for key, _ in attrs):
            self._inside = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._inside:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._inside:
            self.contents.append("".join(self._parts).strip())
            self._parts = []
            self._inside = False


@dataclass(frozen=True)
class ReactorPower:
    """One reactor's source-reported output, without inferred operational status."""

    reactor_id: str
    power_mw: float | None
    reported_percent: float | None
    source_unit: str | None
    measured_at: datetime | None
    quality: str


@dataclass(frozen=True)
class VattenfallSnapshot:
    """One source page snapshot, retaining source and fetch times separately."""

    plant: str
    source_url: str
    measured_at: datetime | None
    fetched_at: datetime
    reactors: dict[str, ReactorPower]


def parse_vattenfall_html(
    html: str,
    plant: str,
    *,
    now: datetime | None = None,
    max_age: timedelta = MAX_DATA_AGE,
) -> VattenfallSnapshot:
    """Parse exactly the expected reactors; missing values remain unknown.

    Source JSON keys seen on both pages: `blockProductionDataList`, `timestamp`,
    and per-block `name`, `production`, `percent`, `unit`.
    """
    if plant not in VATTENFALL_URLS:
        raise ValueError(f"Unsupported Vattenfall source plant: {plant}")
    if not isinstance(html, str):
        raise ValueError("Expected HTML document text")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must have a UTC offset")

    parser = _DataJsonScripts()
    parser.feed(html)
    matches: list[dict[str, Any]] = []
    for script in parser.contents:
        try:
            parsed = json.loads(script)
        except (ValueError, TypeError):
            continue
        if isinstance(parsed, dict) and "blockProductionDataList" in parsed:
            matches.append(parsed)
    if len(matches) != 1:
        raise ValueError("Expected exactly one embedded Vattenfall reactor JSON payload")
    payload = matches[0]
    blocks = payload["blockProductionDataList"]
    if not isinstance(blocks, list):
        raise ValueError("Vattenfall blockProductionDataList must be an array")

    source_at = parse_timestamp(payload.get("timestamp"))
    expected_ids = set(VATTENFALL_REACTORS[plant])
    parsed_blocks: dict[str, dict] = {}
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError("Unexpected Vattenfall reactor record type")
        name = block.get("name")
        if name not in expected_ids:
            continue
        if name in parsed_blocks:
            raise ValueError(f"Duplicate Vattenfall reactor ID: {name}")
        parsed_blocks[name] = block

    reactors: dict[str, ReactorPower] = {}
    for name in VATTENFALL_REACTORS[plant]:
        block = parsed_blocks.get(name, {})
        value = parse_mw(block.get("production"))
        reported_percent = parse_mw(block.get("percent"))
        unit = block.get("unit")
        unit = unit.strip() if isinstance(unit, str) else None
        quality = quality_of(value, source_at, now, max_age)
        if value is not None and unit != "MW":
            # Without a verified MW unit, do not expose the number as power.
            quality = "unknown_unit" if not unit else "unexpected_unit"
        reactors[name] = ReactorPower(
            reactor_id=name,
            power_mw=value,
            reported_percent=reported_percent,
            source_unit=unit,
            measured_at=source_at,
            quality=quality,
        )

    return VattenfallSnapshot(
        plant=plant,
        source_url=VATTENFALL_URLS[plant],
        measured_at=source_at,
        fetched_at=now,
        reactors=reactors,
    )


async def async_fetch_vattenfall(session: Any, plant: str) -> VattenfallSnapshot:
    """Fetch at most one official HTML page with a bounded timeout."""
    if plant not in VATTENFALL_URLS:
        raise ValueError(f"Unsupported Vattenfall source plant: {plant}")
    async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
        async with session.get(
            VATTENFALL_URLS[plant],
            headers={
                "Accept": "text/html",
                "User-Agent": "HA-SwedishPower-Research/0.1",
            },
        ) as response:
            response.raise_for_status()
            if response.content_type != "text/html":
                raise ValueError("Unexpected Vattenfall content type")
            document = await response.text()
    if len(document) > 2_000_000:
        raise ValueError("Unexpectedly large Vattenfall HTML document")
    return parse_vattenfall_html(document, plant)
