# Changelog

All notable changes to HA-SwedishPower will be documented here.
Only published GitHub releases are installable versions. Code on `dev` is not a release.

## 2026.11.0b2 — Reactor MW data collection beta (candidate)

### Added
- Six official operator MW sensors: Forsmark F1–F3, Ringhals R3–R4, Oskarshamn O3.
- Independently refreshing Forsmark, Ringhals and Oskarshamn sources, all on a 15-minute schedule. One failed source does not affect Statnett or the other plants.
- Explicit source timestamps, provenance, data quality and conservative null-versus-zero handling.
- Operator-source status and last-record details in diagnostics.
- HA runtime tests for 14 sensor IDs, source failures/recovery, startup with O3 offline, stale values and reload without duplicates.
- Research-only Nord Pool UMM parser retained for future work; **no UMM status entities** in b2.

### Important limitations
- Reactor output is not an independently confirmed operational status. A zero MW reading does not mean an unplanned failure.
- The six reactor measurements must not be added blindly to the Statnett national value: timestamp and gross/net definition differences are still under review.
- Only a published beta Git tag is intended for installation; no Marketplace-managed updates while main remains unchanged.

## 2026.11.0b1 — Initial supervised beta (candidate)

### Added
- Sweden-only read-only Home Assistant integration, with UI configuration and Swedish/English translations.
- Eight Statnett-powered national MW sensors: production, consumption, net exchange (raw sign), hydro, wind, nuclear, thermal, and other generation.
- Default 15-minute polling using Home Assistant's DataUpdateCoordinator.
- Source measurement/snapshot timestamps, data freshness validation, and diagnostics.
- Independent fail-safe handling of the optional physical-flow endpoint.
- GitHub Actions tests: source JSON probe, 15 parser tests, and 10 Home Assistant 2026.11 integration tests with mocked HTTP.
- Marketplace/HACS metadata and reproducible installation/test instructions.

### Important limitations
- No Lovelace card, individual reactor status, or SE1–SE4 directional flow entities in this beta.
- The net-exchange value preserves Statnett's **raw sign**; its import/export interpretation is not yet verified.
- 'Other' is Statnett's unspecified generation; solar generation is not independently broken out.
- Measurements reflect the source's publication times. This is not sub-minute real-time data.
- 90-minute stale-data threshold is provisional. Users should report unexpected `unavailable` values.
- Installation support is tested against Home Assistant 2026.11; other Core versions have not been verified.
