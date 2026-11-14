# HA-SwedishPower ⚡🇸🇪

A developing **Sweden-first Home Assistant integration and planned Lovelace card** for exploring the Swedish electricity system.

> **Project status: first supervised beta candidate `2026.11.0b1`.** Backend tests pass, but the release is not yet field-tested in the user's Home Assistant. The Lovelace card is planned. **Install only a published beta release, never `dev`.**

## Vision

A Sweden-focused control room with:

- Total electricity generation and consumption in MW, plus production mix by source;
- Sweden's import/export and electricity flows involving **SE1–SE4**;
- Individual output and evidence-based status for Sweden's six operating nuclear reactors: **Forsmark 1–3, Ringhals 3–4, Oskarshamn 3**;
- Transparent measurement timestamps, source attribution and data-quality indicators;
- A separately implemented, theme-friendly Lovelace card with expandable details.

**Default update cadence:** every **15 minutes**. The source measurement may be older than the most recent poll; this must be visible. Higher-frequency realtime monitoring is not part of v1.

## Sources under evaluation

**Statnett Driftsdata** direct endpoints for Sweden's country-level production/consumption and raw area flows returned HTTP 200/JSON in GitHub Actions. The new backend parser also passed a live contract check. Flow direction, access/reuse terms and deployment behavior still need verification. Vattenfall, OKG and UMM are planned sources for individual reactors.

See [Data sources and verification](docs/DATA_SOURCES.md).

## Beta installation (Home Assistant 2026.11+)

For the published `2026.11.0b1` prerelease (check [Releases](https://github.com/Jocke1970/HA-SwedishPower/releases)), use the built-in **Marketplace** at **Settings → Marketplace → Add from link**, and enter this repository URL. On the repository's Marketplace device under **Settings → Devices & services → Marketplace**, enable its normally disabled **Pre-release** entity and switch it on; then select the beta release. Restart Home Assistant, then add **Swedish Power** under **Settings → Devices & services**.

Read the [supervised beta checklist](docs/BETA_TEST_PLAN.md) first. If the version cannot be selected, do **not** install `dev` or `main` as a replacement. Report the problem or use the published beta source only after verifying its tag. Releasing the prerelease does not constitute a stable release.

**Not included in b1:** SE1–SE4 directional sensors, reactor-by-reactor details, and the Lovelace card.

## Project documentation

- [Roadmap and milestones](ROADMAP.md)
- [Backend MVP, limitations and planned beta test](docs/BACKEND_MVP.md)
- [Live Statnett verification log](docs/ISSUE_001_STATNETT_VALIDATION.md)
- [Proposed architecture and safety rules](docs/ARCHITECTURE.md)
- [Data-source validation register](docs/DATA_SOURCES.md)

## Development approach

1. `dev` — implementation and discovery;
2. `beta` — supervised Home Assistant testing;
3. `main` — validated stable releases and documentation.

The initial backend includes eight country-level MW sensors and 15-minute polling. Direct Statnett JSON parsing, offline unit tests and real HA 2026.11 lifecycle tests with mocked HTTP are green. Supervised beta field testing and source policy checks remain before stable release.

## Development verification

- [Backend offline checks — 15 tests passed](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43617129635)
- [Home Assistant 2026.11 — 10 integration tests passed](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43617129627)
- [Marketplace/HACS validation and hassfest — passed (repo About metadata tracked in Issue #5)](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43618520445)
- [Backend live Statnett parser check — passed](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43609117170)

The flow endpoint's raw records are available only for diagnostics until direction/sign semantics are verified. No standalone reactor entities or custom Lovelace card have been implemented yet.

## Scope boundaries

- **In scope:** Sweden, SE1–SE4, six Swedish reactors, border flows that affect Sweden.
- **Out of scope for v1:** full Nordic country dashboards, second-by-second data, and speculative reactor status.
- Missing values are **unknown/unavailable**, never silently rewritten as zero.

## Licence

[MIT License](LICENSE) © 2026 Joachim Eriksson. External data and third-party code retain their own rights and terms.
