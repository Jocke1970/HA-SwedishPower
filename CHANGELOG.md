# Changelog

All notable changes to HA-SwedishPower will be documented here.
Only published GitHub releases are installable versions. Code on `dev` is not a release.

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
