"""One-shot, read-only research on reactor source accessibility and schema.

This script deliberately does not save source HTML, raw UMM messages, or secrets.
Use it in GitHub Actions for reproducible endpoint research; not the HA runtime.
"""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from types import ModuleType
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "swedish_power"
stub = ModuleType("swedish_power")
stub.__path__ = [str(COMPONENT)]
sys.modules["swedish_power"] = stub
from swedish_power.vattenfall import VATTENFALL_URLS, parse_vattenfall_html


def fetch(url: str, accept: str = "text/html") -> tuple[int, str, str]:
    request = Request(
        url, headers={"Accept": accept, "User-Agent": "HA-SwedishPower-Research/0.1"}
    )
    try:
        with urlopen(request, timeout=16) as response:
            return response.status, response.headers.get("Content-Type", ""), (
                response.read(1_500_000).decode("utf-8", errors="replace")
            )
    except HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), ""
    except (URLError, TimeoutError, OSError) as exc:
        print("Network issue:", type(exc).__name__)
        return 0, "", ""


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.iframes = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag.lower() == "script" and data.get("src"):
            self.scripts.append(data["src"])
        if tag.lower() == "iframe" and data.get("src"):
            self.iframes.append(data["src"])


def probe_vattenfall() -> bool:
    ok = True
    for plant, url in VATTENFALL_URLS.items():
        status, ct, html = fetch(url)
        print(f"Vattenfall {plant}: HTTP {status}, type={ct}, html={len(html)} chars")
        try:
            assert status == 200
            parsed = parse_vattenfall_html(html, plant)
            print("  source time:", parsed.measured_at)
            for name, item in parsed.reactors.items():
                print(f"  {name}: {item.power_mw} {item.source_unit or '?'}; quality={item.quality}")
            assert all(item.source_unit == "MW" for item in parsed.reactors.values())
            assert all(item.quality == "valid" for item in parsed.reactors.values())
        except (ValueError, AssertionError) as exc:
            print("  CONTRACT FAIL:", type(exc).__name__, str(exc)[:200])
            ok = False
    return ok


def probe_okg():
    for url in (
        "https://okg.se/",
        "https://okg.se/var-verksamhet/kontrollrummet/",
    ):
        status, ct, html = fetch(url)
        print(f"OKG page: HTTP {status}, type={ct}, chars={len(html)}, url={url}")
        if status != 200:
            continue
        parser = References()
        parser.feed(html)
        urls = parser.scripts + parser.iframes
        print("  embedded script/iframe links:", len(urls))
        for u in urls[:40]:
            print("  asset:", u[:250])
        # Bounded context only. Avoid dumping full HTML / private values.
        patterns = (
            r"(?i)(?:oskarshamn\s*3|production|produktion|aktuell\s*effekt|powerplant|widget|\bO3\b)",
            r"(?i)(?:api\.|/api/|\.json|kilowatt|megawatt)",
        )
        shown = set()
        for pattern in patterns:
            for hit in list(re.finditer(pattern, html))[:14]:
                fragment = re.sub(r"\s+", " ", html[max(0, hit.start()-90):hit.end()+140])
                fragment = fragment[:240]
                if fragment not in shown:
                    shown.add(fragment)
                    print("  context:", fragment)
                if len(shown) >= 20:
                    break
            if len(shown) >= 20:
                break


def probe_okg_javascript():
    url = "https://okg.se/main.js"
    status, ct, js = fetch(url, "application/javascript")
    print(f"OKG JS: HTTP {status}, type={ct}, chars={len(js)}")
    if status != 200:
        return
    print("  fetched content cap: 1.5 MB")
    for term in (
        "production-meter", "productionMeter", "ProductionMeter",
        "functionsBaseUrl", "functionsbaseurl", "/api/", "productionData",
        "production", "Production", "Oskarshamn", "getO3", "FetchProduction",
    ):
        matches = list(re.finditer(re.escape(term), js, re.IGNORECASE))
        print(f"  JS term {term}: {len(matches)} hits")
        for m in matches[:3]:
            excerpt = re.sub(r"\\s+", " ", js[max(0,m.start()-160):m.end()+240])
            print("    JS context:", excerpt[:420])


def probe_okg_output():
    url = "https://okg.se/.netlify/functions/getReactorOutput"
    status, ct, raw = fetch(url, "application/json")
    print(f"OKG O3 output: HTTP {status}, type={ct}, bytes={len(raw)}")
    if status != 200:
        print("  Not a confirmed direct HTTP 200 response")
        return
    try:
        payload = json.loads(raw)
    except ValueError:
        print("  Not JSON")
        return
    if isinstance(payload, dict):
        print("  field names:", sorted(payload))
        for key, value in payload.items():
            if key.lower() in {"value", "unit", "timestamp", "updatedat", "measuredat", "time", "valuedate"}:
                print("  field:", key, repr(value)[:160], "type:", type(value).__name__)
    else:
        print("  root type:", type(payload).__name__)


def probe_umm():
    base = "https://ummapi.nordpoolgroup.com/messages"
    query = urlencode({"messageTypes": 1, "fuelTypes": 14, "limit": 2, "skip": 0})
    status, ct, raw = fetch(f"{base}?{query}", "application/json")
    print(f"Nord Pool UMM: HTTP {status}, type={ct}, bytes={len(raw)}")
    if status != 200:
        print("  Public access is NOT verified; do not implement against assumptions.")
        return
    try:
        payload = json.loads(raw)
    except ValueError:
        print("  Response is not valid JSON")
        return
    if not isinstance(payload, dict):
        print("  Unexpected root type:", type(payload).__name__)
        return
    print("  root keys:", sorted(payload))
    print("  total:", payload.get("total"))
    entries = payload.get("items")
    print("  entries:", len(entries) if isinstance(entries, list) else "not a list")
    if isinstance(entries, list):
        for entry in entries[:2]:
            if not isinstance(entry, dict):
                continue
            print("  message keys:", sorted(entry))
            units = entry.get("productionUnits")
            if isinstance(units, list) and units and isinstance(units[0], dict):
                print("  production unit keys:", sorted(units[0]))
                times = units[0].get("timePeriods")
                if isinstance(times, list) and times and isinstance(times[0], dict):
                    print("  period keys:", sorted(times[0]))


if __name__ == "__main__":
    print("=== Vattenfall source contract ===")
    passed = probe_vattenfall()
    print("=== OKG discovery (read-only) ===")
    probe_okg()
    print("=== OKG production-meter JavaScript ===")
    probe_okg_javascript()
    print("=== OKG O3 output direct HTTP ===")
    probe_okg_output()
    print("=== Nord Pool UMM discovery (read-only) ===")
    probe_umm()
    print("VERIFIED VATTENFALL CONTRACT:", "PASS" if passed else "FAIL")
    raise SystemExit(0 if passed else 1)
