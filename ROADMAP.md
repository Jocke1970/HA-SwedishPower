# Roadmap — HA-SwedishPower

> Status: **Backend MVP on dev; 10 HA integration tests and 15 parser tests passed; on-device beta pending** · Scope: **Sweden first** · Last reviewed: **2026-11-14**

Checked milestones below identify features implemented in `dev`. There is **no production-ready release or Lovelace card yet**.

## Guiding decisions

- **Geography:** Sweden only in v1. Country-level electricity data and the Swedish bidding zones **SE1–SE4** are the focus. Flows to neighboring countries are relevant only as Sweden's imports/exports.
- **Update cadence:** poll at **15-minute intervals** by default. A successful poll does **not** imply measurements are only 15 minutes old.
- **Separation:** Home Assistant backend owns fetching, normalization, validation, caching and sensor entities. The Lovelace card renders sensor data; it does not scrape sources.
- **Source discipline:** use Statnett as a candidate backbone, subject to verifying endpoints, schemas, conditions and data freshness. Add primary reactor sources and outage notices independently.
- **Data integrity:** unknown/unavailable is not 0 MW. Every measurement should have source and measurement timestamp; flag stale or estimated data. Do not confuse unused capacity with a verified outage.
- **Release policy:** develop on `dev`, validate on `beta`, and publish tested releases to `main`. No requirement to install `dev`.

## Phase 0 — Data-source discovery and contract (P0, in progress)

- [x] Confirm direct Statnett API endpoints respond HTTP 200/JSON, with Sweden rows and timestamps (GitHub Actions).
- [ ] Document permitted use/rate limits and verify source semantics across periods.
- [x] Confirm Swedish national production types, consumption and net exchange fields via direct JSON.
- [ ] Verify actual versus scheduled versus estimated values with primary-source documentation.
- [ ] Verify which flow pairs exist for **SE1–SE4**, including direction/sign convention and publication delays.
- [ ] Inspect Vattenfall, OKG and UMM sources for **F1, F2, F3, R3, R4, O3**; confirm permitted, reliable machine access and gross/net reference capacities.
- [ ] Record source attribution, reuse terms and sensible failure/backoff strategy.
- [ ] Save sanitized sample responses as fixtures and define normalized field names.

**Exit criteria:** at least one verified, reproducible Swedish production/consumption data fetch, a documented schema, and an explicit list of unresolved fields. Do not start a production scraper on assumptions.

## Phase 1 — Home Assistant backend MVP (P1, HA 2026.11 automated tests passed; on-device beta pending)

- [x] Create `custom_components/swedish_power/` with UI config flow, `DataUpdateCoordinator`, diagnostics and eight sensor entities.
- [x] Implement source reads with default **900-second** refresh, 15-second timeouts and coordinator-managed retries.
- [ ] Decide whether a rate-limited manual refresh is desirable; not exposed by this first implementation.
- [x] Map eight country-level source fields to MW sensor descriptions; live parser verified.
- [x] Preserve row/snapshot timestamps, handle missing/stale/future values and optional flow failure in code.
- [x] Test HA 2026.11 config flow, sensors, reload/unload, error/recovery, diagnostics and stale source behavior with mocked HTTP.
- [ ] Confirm Recorder history and long-term statistics through supervised physical beta testing.
- [x] Add nine backend data-model tests (15 total repository tests passed) and a live JSON contract check.
- [x] Add 10 real HA integration tests, including first-refresh retry, coordinator failure/recovery and malformed data.

**Exit criteria:** supervised beta testing of functioning entities in the user's HA; no fabricated values, and no false 0 MW on fetch failure. Automation tests pass, but in-device field validation remains.

## Phase 2 — Swedish bidding-zone flows (P1/P2)

- [ ] Normalize SE1–SE4 flows and Sweden's cross-border connections from verified pairs.
- [ ] Test direction conventions against published reference information and prevent double-counting.
- [ ] Model separate zone-to-zone MW sensors and data ages, where endpoints support them.
- [ ] Identify gaps in zone-level generation/consumption; don't present national values as per-zone measurements.

**Exit criteria:** a correct, timestamped Swedish flow model with explicit gaps and tests.

## Phase 3 — Nuclear detail (P1/P2, source adapters implemented on dev; not deployed)

- [x] Implement research-only parsers/fetchers in `dev` for Vattenfall Forsmark **1–3**, Ringhals **3–4** and OKG Oskarshamn **3**, preserving actual measurement times and missing data.
- [ ] Wire adapters into isolated HA source coordinators, verify network-failure behavior, and expose six stable-ID reactor MW sensors after integration tests.
- [ ] Track each unit's reported power, measurement time, validated net/gross reference capacity and data quality.
- [x] Verify Nord Pool UMM endpoint/schema and implement conservative Sweden-specific notice parser in `dev` (48 periods for six reactors matched in a live first-page test).
- [ ] Complete UMM pagination, revisions/cancellations and permitted-use verification before attaching notices as operational statuses.
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

See [BACKEND_MVP.md](docs/BACKEND_MVP.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md) and [DATA_SOURCES.md](docs/DATA_SOURCES.md) for the proposed technical design and validation checklist.
