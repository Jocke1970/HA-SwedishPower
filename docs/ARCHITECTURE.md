# Proposed architecture (not yet implemented)

## Scope

A **Sweden-only**, read-only Home Assistant integration and a separately maintained Lovelace frontend. The integration presents third-party reported grid data; it does not control the power system, meter electricity at the user's premises or guarantee instantaneous accuracy.

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

One adapter failing should not erase data from other independent adapters.

## Planned repository layout

```text
custom_components/swedish_power/  # HA integration: to be implemented
  manifest.json
  __init__.py
  config_flow.py
  coordinator.py
  sensor.py
  sources/
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

This is a **proposed** layout, not a claim that these code files currently exist. The backend and frontend may later be split into different repositories if packaging warrants it.

## Proposed normalized data contract

Every numeric record should carry, wherever source-provided:

- `value_mw` (number or unknown), `unit` and measurement `kind`: actual / planned / estimated / unknown;
- `source_id`, `source_record_id` (if any), `measured_at` (timestamp from source), and `fetched_at` (HA retrieval time);
- `scope`: `SE` or an explicit Swedish bidding-zone/flow pair, not inferred by display position;
- `quality`: valid / stale / partial / invalid / unavailable, with diagnostics when source metadata is insufficient.

Source-specific records can add `production_type`, `from_area`, `to_area`, `gross_or_net`, `reference_capacity_mw`, or outage notice metadata. The field mapping remains **provisional until raw payloads are tested**.

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

- External **sv** and **en** translation files for the frontend. Backend translation support should follow Home Assistant's native conventions.
- UI defaults to Home Assistant theme and exposes a visual editor when ready.
- **dev → beta → main**: new work on dev; only promote when tests and manual review pass. User installs beta for evaluation, never dev.
