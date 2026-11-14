# Swedish Power 2026.11.0b2 — supervised reactor data collection beta ☢️⚡

**Prerelease only.** Install this exact published release through the supervised manual update procedure. Do not install `dev`, and do not promote to `main` until real Home Assistant observations are reviewed.

## What's added

- Six new read-only, 15-minute MW sensors for **Forsmark 1/2/3**, **Ringhals 3/4**, and **Oskarshamn 3**.
- The **eight Statnett sensors remain unchanged**, with their stable entity unique IDs and their existing data fields.
- Vattenfall and OKG each have their own independently failing feed, grouped by plant: Forsmark, Ringhals and Oskarshamn. One upstream source's timeout does **not** make other sources unavailable.
- Every MW sensor has a source measurement timestamp, fetch timestamp, quality flag, provenance/source URL and operator name in its attributes.
- Source-reported fractional MW is preserved, `0` is different from missing, stale source reports become unavailable. No low-output threshold is used to label a reactor fault.
- Home Assistant diagnostics include per-source refresh state, last fetch and reactor MW values without copying external raw payloads.
- Swedish and English translation files include the six new units.

## Sources

- Vattenfall official Forsmark and Ringhals production pages: embedded source JSON.
- OKG official O3 production display: direct `getReactorOutput` endpoint extracted from its publicly served JavaScript. Local `valueDate` converted using `Europe/Stockholm` and API's UTC timestamp to resolve DST.
- Nord Pool UMM direct access and schema are **research-verified on dev**, but no UMM outage/status entities are enabled in this release pending interpretation, revision/cancellation and reuse-policy checks.

**Caution:** Statnett's Swedish national `nuclear` number and the six operator-reported values may have different timestamps, gross/net definitions and reporting delays. They must not be treated as directly comparable without checking matching periods and definitions.

## Update existing manually installed b1

1. Back up the Home Assistant configuration. Do **not** remove/re-add the existing Swedish Power config entry.
2. Download [Source code ZIP for this published prerelease](https://github.com/Jocke1970/HA-SwedishPower/releases/tag/2026.11.0b2), or fetch the immutable Git tag via Git, never the branch head.
3. Replace **only** `/config/custom_components/swedish_power/` with the directory from the published tag. Preserve a copy of the previous b1 directory in your backup location.
4. Restart Home Assistant. Confirm that its installed `manifest.json` says `2026.11.0b2`.
5. Swedish Power remains the same configured integration; it should register **14** sensors (8 Statnett + 6 reactor MW) and three reactor devices. Leave Recorder enabled.
6. Review readings for at least 4 polling cycles (~1 hour), plus overnight if possible. [Field test plan](docs/BETA_TEST_PLAN_2026.11.0b2.md).

Manual beta upgrades are not managed through Marketplace at this stage. The repository's default `main` branch stays unchanged.

## Not in this beta

- No confirmed reactor fault, maintenance or return-to-service status.
- No UMM polling from Home Assistant; no new UMM status entities.
- No Lovelace custom JS card, and no changes to Statnett raw exchange sign or SE1–SE4 directional flows.
- No stable `main` release.

## Verification

- Source-scheme probes: Vattenfall F1–F3 and R3–R4, OKG O3, and first-page Nord Pool UMM schema all returned HTTP 200.
- Pure parsing and source-quality test suite plus HA 2026.11 runtime lifecycle and failure isolation tests must pass the guarded release workflow **before** b2 is published.
