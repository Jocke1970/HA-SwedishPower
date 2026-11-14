# HA-SwedishPower ⚡🇸🇪

A developing **Sweden-first Home Assistant integration and planned Lovelace card** for exploring the Swedish electricity system.

> **Project status:** `2026.11.0b1` is in HA field testing, and `2026.11.0b2` is the six-reactor data-collection beta candidate. **Install only a published beta release, never `dev`.** Stable `main` and the Lovelace card are pending.

## Vision

A Sweden-focused control room with:

- Total electricity generation and consumption in MW, plus production mix by source;
- Sweden's import/export and electricity flows involving **SE1–SE4**;
- Individual output and evidence-based status for Sweden's six operating nuclear reactors: **Forsmark 1–3, Ringhals 3–4, Oskarshamn 3**;
- Transparent measurement timestamps, source attribution and data-quality indicators;
- A separately implemented, theme-friendly Lovelace card with expandable details.

**Default update cadence:** every **15 minutes**. The source measurement may be older than the most recent poll; this must be visible. Higher-frequency realtime monitoring is not part of v1.

## Sources under evaluation

**Statnett Driftsdata** direct endpoints for Sweden's country-level production/consumption and raw area flows returned HTTP 200/JSON in GitHub Actions. The new backend parser also passed a live contract check. Flow direction, access/reuse terms and deployment behavior still need verification. Vattenfall and OKG operator output is verified and implemented in the b2 candidate; UMM notice interpretation remains research-only.

See [Data sources and verification](docs/DATA_SOURCES.md).

## Beta installation and upgrades (manual until main is installable)

**Known Home Assistant 2026.11 Marketplace limitation:** `Add from link` checks the repository's default branch (`main`) before adding a custom integration. We intentionally keep the unfield-tested beta code off `main`, so Marketplace currently reports **"missing content ... in version main"**. The beta release itself exists and has passed automated tests. We will not move an untested release into `main` just to bypass discovery.

Install from the **published** Git beta release, not a branch head. For the existing b1 integration, upgrade in place using the [2026.11.0b2 published tag](https://github.com/Jocke1970/HA-SwedishPower/releases/tag/2026.11.0b2) when available: back up and replace **only** `/config/custom_components/swedish_power/`, then restart HA. **Keep the configured Swedish Power entry**: b2 preserves eight Statnett entity IDs and adds six reactor MW sensors, for **14 total**. See [b2 test plan](docs/BETA_TEST_PLAN_2026.11.0b2.md).

**Manual installation is not managed by Marketplace**, so future beta updates also need manual file replacement and a restart. Never install code directly from the `dev` branch. See the [complete beta test plan](docs/BETA_TEST_PLAN.md) and [beta field-test issue](https://github.com/Jocke1970/HA-SwedishPower/issues/6).

## Project documentation

- [Roadmap and milestones](ROADMAP.md)
- [Backend MVP, limitations and planned beta test](docs/BACKEND_MVP.md)
- [Live Statnett verification log](docs/ISSUE_001_STATNETT_VALIDATION.md)
- [Proposed architecture and safety rules](docs/ARCHITECTURE.md)
- [Data-source validation register](docs/DATA_SOURCES.md)

## Reactor data and source research

Vattenfall F1–F3 / R3–R4 and OKG O3 output were verified directly from official sites. A limited public Nord Pool UMM response was successfully normalized for all six Swedish reactors. The b2 candidate on `dev` adds six reactor output sensors, with quality and source-time attributes. UMM remains a research-only parser and **is not used to infer operational status**. See [source schema and caveats](docs/NUCLEAR_DATA_DISCOVERY.md). The installed b1 remains unchanged until upgraded by the user.

## Development approach

1. `dev` — implementation and discovery;
2. `beta` — supervised Home Assistant testing;
3. `main` — validated stable releases and documentation.

The b1 backend has eight national MW sensors. The b2 candidate adds six independently refreshed 15-minute reactor MW sensors. Direct Statnett JSON parsing, offline unit tests and real HA 2026.11 lifecycle tests with mocked HTTP are green. Supervised beta field testing and source policy checks remain before stable release.

## Development verification

- [Backend offline checks — 15 tests passed](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43617129635)
- [Home Assistant 2026.11 — 10 integration tests passed](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43617129627)
- [Marketplace/HACS validation and hassfest — passed (repo About metadata tracked in Issue #5)](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43618520445)
- [Backend live Statnett parser check — passed](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43609117170)

The flow endpoint's raw records are available only for diagnostics until direction/sign semantics are verified. Reactor output sensors are implemented in the b2 candidate; no confirmed outage/status entities or Lovelace card exist.

## Scope boundaries

- **In scope:** Sweden, SE1–SE4, six Swedish reactors, border flows that affect Sweden.
- **Out of scope for v1:** full Nordic country dashboards, second-by-second data, and speculative reactor status.
- Missing values are **unknown/unavailable**, never silently rewritten as zero.

## Licence

[MIT License](LICENSE) © 2026 Joachim Eriksson. External data and third-party code retain their own rights and terms.
