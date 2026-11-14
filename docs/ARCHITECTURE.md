# Architecture — backend MVP on dev, frontend planned

## Scope

The **Sweden-only read-only backend MVP is implemented in `dev`**; the separate Lovelace frontend, reactor adapters and directional flow sensors are still planned. This integration presents third-party reported grid data; it does not control the power system, meter electricity at the user's premises or guarantee instantaneous accuracy.

```text
Statnett (candidate backbone) ─┐
Vattenfall / OKG (reactors) ────┼─> source adapters ─> normalized data + validation
UMM (outages, if permitted) ────┘                          |
                                                         v
                                  HA DataUpdateCoordinator (15 min default)
                                                         |
                                                  HA sensors + attributes
                                                         |
                                          HA-SwedishPower-Card (read-only)
```

**Currently implemented:** the Statnett national-production adapter and optional raw-flow fetching. Vattenfall, OKG, UMM and the card are not yet implemented. An optional flow-fetch failure does not discard valid national production data.

## Repository layout (implemented components marked)

```text
custom_components/swedish_power/  # Implemented in dev
  manifest.json
  __init__.py
  config_flow.py
  coordinator.py
  sensor.py
  model.py
  const.py
  diagnostics.py
  strings.json
  translations/
    sv.json
    en.json
  sources/                     # Future reactor adapters
www/                             # Lovelace JS frontend, to be implemented
  swedish-power-card.js
  translations/
    sv.json
    en.json
tests/                           # payload fixtures and tests
docs/
  ARCHITECTURE.md
  DATA_SOURCES.md
ROADMAP.md
README.md
LICENSE
```

The backend files above, excluding the future `sources/` adapters, are in `dev`. The `www/` Lovelace card is **not yet present**. Backend and frontend may be split into different repositories later if packaging warrants it.

## Proposed normalized data contract

Every numeric record should carry, wherever source-provided:

- `value_mw` (number or unknown), `unit` and measurement `kind`: actual / planned / estimated / unknown;
- `source_id`, `source_record_id` (if any), `measured_at` (timestamp from source), and `fetched_at` (HA retrieval time);
- `scope`: `SE` or an explicit Swedish bidding-zone/flow pair, not inferred by display position;
- `quality`: valid / stale / partial / invalid / unavailable, with diagnostics when source metadata is insufficient.

Source-specific records can add `production_type`, `from_area`, `to_area`, `gross_or_net`, `reference_capacity_mw`, or outage notice metadata. National Swedish field names and direct JSON access have been verified by GitHub Actions. Semantic interpretation (especially flow direction and exchange sign) remains provisional.

## Update and failure semantics

- Default polling: **15 minutes (900 s)** for v1; source publishing cadence can differ.
- Use asynchronous HTTP, one request per required endpoint when possible, shared session, timeout, bounded retry/backoff and no unrestricted refresh loops.
- Compare source timestamps with a **source-specific, configurable** freshness threshold. Never treat the latest HA poll timestamp as the measurement timestamp.
- Missing / invalid / stale payload is **not** 0 MW. Show source health and last successful reading separately; mark active state unavailable when necessary.
- Keep historical measurements in HA Recorder as appropriate. Avoid overwhelming entity attributes with full external JSON payloads.
- Log sufficient diagnostics for debugging without leaking credentials/tokens.
- Keep consumption, net exchange and generation accounting distinct. Never silently force totals to balance if source definitions/times differ.

## Nuclear status model

Report MW and validated reference capacity separately. A green percentage bar is not itself proof of normal operation; the meaning of 100% depends on gross/net capacity and source definitions.

Operational status is evidence-based:
- `normal`: trusted status, not just MW > 90% capacity;
- `reduced`: confirmed reduced output when cause or threshold is understood;
- `planned_outage`: corroborating planned outage notice;
- `unplanned_outage`: corroborating unplanned outage notice;
- `unknown`: no reliable status evidence.

Show UMM notices, last update and expected return only when genuinely supplied, with clear source attribution. Do not conflate planned outages with faults or unused capacity with lost generation.

## Localization and release workflow

- The **backend** already has external `sv` and `en` translation files and a `strings.json`; the frontend translations remain planned.
- UI defaults to Home Assistant theme and exposes a visual editor when ready.
- **dev → beta → main**: new work on dev; only promote when tests and manual review pass. User installs beta for evaluation, never dev.
