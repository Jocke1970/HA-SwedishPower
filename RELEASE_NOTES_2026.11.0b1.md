# Swedish Power 2026.11.0b1 — first supervised beta ⚡🇸🇪

**Beta only.** Tested against Home Assistant Core 2026.11.0 and direct Statnett JSON. No stable release or frontend card yet.

## Features
- Sweden-only electricity data from Statnett, updated on a **15-minute schedule**.
- Eight national MW sensors: production, consumption, signed net exchange, hydropower, wind power, nuclear power, thermal power, and other generation.
- UI configuration flow (no API key), Swedish/English names and diagnostics.
- Source row/snapshot timestamps and stale-data guards; a missing or old value is not silently displayed as zero.
- Optional Sweden-related raw physical-flow data kept for diagnostics; flow problems do not stop national production sensors.

## Validation
- **15 Python/unit tests**, including strict parsing and source data handling.
- **10 Home Assistant 2026.11 lifecycle tests**: UI setup, eight sensors, reload, failures, recovery, stale data and diagnostics.
- A separate live contract check against Statnett's direct endpoints returned valid JSON and parsed Swedish data.
- Marketplace/HACS packaging and hassfest checks (temporary repository About-metadata exceptions tracked separately).

## Known limitations
- The **sign of net exchange has not yet been independently validated**; the sensor is intentionally labelled "raw sign". Do not use it for import/export actions until checked.
- No individual nuclear reactor data, outage status, directional SE1–SE4 flow sensors or custom Lovelace card in this beta.
- This is **national power in MW**, not household power or cumulative MWh/kWh.
- "Other" is not an independently verified solar-power figure.
- The 90-minute data-age limit is provisional. Monitor the `quality` and `source_measured_at` attributes.
- Release compatibility is limited to Home Assistant **2026.11.0+**; older versions were not tested.

## Supervised testing
Follow [the beta test plan](https://github.com/Jocke1970/HA-SwedishPower/blob/beta/docs/BETA_TEST_PLAN.md) and use the **pre-release** option when installing from Marketplace. Verify the selected release is `2026.11.0b1`, not `dev` or `main`.

After installation, let the integration run for at least **four scheduled update cycles**, check actual source timestamps, and report mismatches or persistent `unavailable` states. Stable promotion to `main` requires a separate test decision.
