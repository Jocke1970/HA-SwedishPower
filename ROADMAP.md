# Roadmap — HA-SwedishPower

> Status: **Planning / discovery** · Scope: **Sweden first** · Last reviewed: **2026-11-14**

This roadmap describes intended work, **not features that are already implemented**. No production-ready integration or Lovelace card exists yet.

## Guiding decisions

- **Geography:** Sweden only in v1. Country-level electricity data and the Swedish bidding zones **SE1–SE4** are the focus. Flows to neighboring countries are relevant only as Sweden's imports/exports.
- **Update cadence:** poll at **15-minute intervals** by default. A successful poll does **not** imply measurements are only 15 minutes old.
- **Separation:** Home Assistant backend owns fetching, normalization, validation, caching and sensor entities. The Lovelace card renders sensor data; it does not scrape sources.
- **Source discipline:** use Statnett as a candidate backbone, subject to verifying endpoints, schemas, conditions and data freshness. Add primary reactor sources and outage notices independently.
- **Data integrity:** unknown/unavailable is not 0 MW. Every measurement should have source and measurement timestamp; flag stale or estimated data. Do not confuse unused capacity with a verified outage.
- **Release policy:** develop on `dev`, validate on `beta`, and publish tested releases to `main`. No requirement to install `dev`.

## Phase 0 — Data-source discovery and contract (P0, next)

- [ ] Test Statnett's current documented endpoints from a Home Assistant-compatible client; record HTTP behavior, schema, units, timestamps, geographic coverage and rate limits.
- [ ] Confirm Swedish national production by type, total consumption and net exchange. Distinguish actual, scheduled, estimated and stale values.
- [ ] Verify which flow pairs exist for **SE1–SE4**, including direction/sign convention and publication delays.
- [ ] Inspect Vattenfall, OKG and UMM sources for **F1, F2, F3, R3, R4, O3**; confirm permitted, reliable machine access and gross/net reference capacities.
- [ ] Record source attribution, reuse terms and sensible failure/backoff strategy.
- [ ] Save sanitized sample responses as fixtures and define normalized field names.

**Exit criteria:** at least one verified, reproducible Swedish production/consumption data fetch, a documented schema, and an explicit list of unresolved fields. Do not start a production scraper on assumptions.

## Phase 1 — Home Assistant backend MVP (P1)

- [ ] Create `custom_components/swedish_power/` with config flow, `DataUpdateCoordinator`, diagnostics and sensor entities.
- [ ] Read the verified Statnett source(s) with default **900-second** refresh, timeouts, backoff, and an optional rate-limited manual refresh.
- [ ] Expose Swedish total production, production types actually supported, total consumption and net exchange with **MW** units.
- [ ] Preserve source measurement timestamps; handle missing/stale data, partial results, clock skew and API failures safely.
- [ ] Add tests for payload parsing, timezone conversion, source disagreement, stale data and failed polling.

**Exit criteria:** supervised beta testing of functioning entities in HA; no fabricated values, and no false 0 MW on fetch failure.

## Phase 2 — Swedish bidding-zone flows (P1/P2)

- [ ] Normalize SE1–SE4 flows and Sweden's cross-border connections from verified pairs.
- [ ] Test direction conventions against published reference information and prevent double-counting.
- [ ] Model separate zone-to-zone MW sensors and data ages, where endpoints support them.
- [ ] Identify gaps in zone-level generation/consumption; don't present national values as per-zone measurements.

**Exit criteria:** a correct, timestamped Swedish flow model with explicit gaps and tests.

## Phase 3 — Nuclear detail (P1/P2)

- [ ] Add independent source adapters for Forsmark **1–3**, Ringhals **3–4**, and Oskarshamn **3**.
- [ ] Track each unit's reported power, measurement time, validated net/gross reference capacity and data quality.
- [ ] Integrate verified outage/maintenance notices (UMM) where access and reuse are permitted.
- [ ] Distinguish **normal**, **reduced**, **planned outage**, **unplanned outage**, and **unknown** only when evidence permits.
- [ ] Provide last notice, cause, estimated return and notice update time when available.
- [ ] Never infer that 0 MW alone means an unplanned trip. Explain possible differences from national nuclear production totals.

**Exit criteria:** six individually traceable reactor sensors; status can fall back to unknown rather than inventing a cause.

## Phase 4 — HA-SwedishPower-Card (P2)

- [ ] Separate Lovelace JS frontend from integration logic, sharing only HA entity state and attributes.
- [ ] Sweden overview: total generation, consumption, production mix, and import/export.
- [ ] Expandable SE1–SE4 electricity-flow section.
- [ ] Six clickable reactor tiles and detailed panel/popup with source, freshness, history and UMM context.
- [ ] Build visual editor and **external** `sv`/`en` translation files from the outset.
- [ ] Respect mobile/desktop layouts, HA themes, accessibility and missing sensor states.

**Exit criteria:** functional, legible beta UI that cannot mislabel stale information as live.

## Phase 5 — Quality, documentation and release (P2)

- [ ] Unit and integration tests; representative fixture and offline/failure scenarios.
- [ ] Document installation, source attribution, configuration, limitations and privacy/security handling.
- [ ] Add changelog, release notes, HACS packaging and screenshots once features exist.
- [ ] Follow **dev → beta → main**. Test on beta before stable release; keep main clean.

## Future ideas — explicitly not v1

- Higher-frequency live updates, frequency-focused views, Nord Pool price comparisons, optional ENTSO-E enrichment, solar split where source coverage supports it, broader Nordic views.
- Any future addition must not compromise reliability of the Sweden-only baseline.

## Open decisions

1. Which **direct** Statnett endpoints and response fields are stable enough for v1?
2. What are realistic freshness thresholds per source, independent of the 15-minute polling interval?
3. Are SE1–SE4 *generation by type* available from a reliable source? If not, do not invent them.
4. What is the permitted and preferred access path for reactor MW and UMM records?
5. Should the Lovelace card remain in this repository under a separate directory or eventually move to its own repository?

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) and [DATA_SOURCES.md](docs/DATA_SOURCES.md) for the proposed technical design and validation checklist.
