# HA-SwedishPower ⚡🇸🇪

A planned **Sweden-first Home Assistant integration and Lovelace card** for exploring the Swedish electricity system.

> **Project status: planning / data-source validation.** No functioning integration or card has been released yet. Do not install this repository as if it were production-ready.

## Vision

A Sweden-focused control room with:

- Total electricity generation and consumption in MW, plus production mix by source;
- Sweden's import/export and electricity flows involving **SE1–SE4**;
- Individual output and evidence-based status for Sweden's six operating nuclear reactors: **Forsmark 1–3, Ringhals 3–4, Oskarshamn 3**;
- Transparent measurement timestamps, source attribution and data-quality indicators;
- A separately implemented, theme-friendly Lovelace card with expandable details.

**Default update cadence:** every **15 minutes**. The source measurement may be older than the most recent poll; this must be visible. Higher-frequency realtime monitoring is not part of v1.

## Sources under evaluation

**Statnett Driftsdata** is the candidate backbone for Swedish grid production and flows. Vattenfall, OKG and outage notices are candidates for unit-level nuclear detail. The project will not assume API endpoints, terms of use, sign conventions, or per-zone data exist until tested.

See [Data sources and verification](docs/DATA_SOURCES.md).

## Project documentation

- [Roadmap and milestones](ROADMAP.md)
- [Proposed architecture and safety rules](docs/ARCHITECTURE.md)
- [Data-source validation register](docs/DATA_SOURCES.md)

## Development approach

1. `dev` — implementation and discovery;
2. `beta` — supervised Home Assistant testing;
3. `main` — validated stable releases and documentation.

The first usable milestone is a tested backend with trustworthy Swedish electricity sensors, **not** a live control-room UI.

## Scope boundaries

- **In scope:** Sweden, SE1–SE4, six Swedish reactors, border flows that affect Sweden.
- **Out of scope for v1:** full Nordic country dashboards, second-by-second data, and speculative reactor status.
- Missing values are **unknown/unavailable**, never silently rewritten as zero.

## Licence

[MIT License](LICENSE) © 2026 Joachim Eriksson. External data and third-party code retain their own rights and terms.
