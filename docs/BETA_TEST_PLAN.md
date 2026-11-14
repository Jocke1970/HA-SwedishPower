# HA-SwedishPower — supervised beta 2026.11.0b1

## IMPORTANT: Marketplace cannot add this beta yet (2026-11-14)

**Verified limitation:** In Home Assistant 2026.11, Marketplace's **Add from link** first checks the GitHub repository's default branch (`main`). The default branch currently has no `hacs.json` or `custom_components/swedish_power/`, because the implementation exists only in `dev`/`beta` and was published as a **prerelease**.

The error **"missing content Marketplace can install in version main"** is therefore expected. It is **not a failed Statnett API or backend test**. Enabling prereleases cannot fix initial repository discovery.

**We deliberately preserve `dev → beta → main` and do not promote an unfield-tested integration to `main` to bypass this error.** For b1 use the manual install below. When a beta passes field testing and the complete installable repository reaches `main`, Marketplace can be revisited.

## Manual supervised beta installation — recommended for b1

1. Back up the HA configuration. In the Marketplace **Add from link** dialog click **Cancel**; do not select another integration type.
2. Open the published release: https://github.com/Jocke1970/HA-SwedishPower/releases/tag/2026.11.0b1
3. Under **Assets**, download **Source code (zip)** for the **2026.11.0b1** release — **not** the `dev` or `main` branch.
4. Extract the archive on your computer. Inside it, open `custom_components/swedish_power/`.
5. Using your Home Assistant file-access method (Studio Code Server, Samba share, or SSH), copy the **whole `swedish_power` directory** into your HA configuration's `custom_components/` directory. Resulting paths should be:
   - `/config/custom_components/swedish_power/manifest.json`
   - `/config/custom_components/swedish_power/__init__.py`
   - `/config/custom_components/swedish_power/sensor.py`
   - and all other files/subfolders including `translations/`.
   Create `custom_components` if needed. Do **not** copy the entire GitHub archive into `custom_components`.
6. **Restart Home Assistant** to load the new custom integration.
7. Go to **Settings → Devices & services → Add integration**, search for **Swedish Power**, and confirm Sweden.
8. Inspect the **eight** sensors, source timestamps and diagnostics. Observe at least four scheduled refresh cycles (about an hour).

**Manual installs do not receive Marketplace-managed updates.** For later betas, replace the `swedish_power` folder with the files from that **specific published beta tag**, restart HA, and verify the manifest version. Do not copy `dev` by accident.

If the integration doesn't show after restarting, check **Settings → System → Logs** for a `swedish_power` import/config-flow error; report the sanitized error in beta test Issue #6.

**Branch policy:** `dev → beta → main`. Test only the `beta` prerelease; **do not install `dev`**. `main` must remain unchanged until beta is accepted.

## Prerequisites

- Home Assistant **2026.11.0 or later**. The automated integration tests used Core 2026.11.0 and Python 3.14.
- Back up your Home Assistant configuration before installing any new custom integration.
- Ability to reach `driftsdata.statnett.no` through HTTPS.
- No API key is required for the two Statnett endpoints tested.
- The repository is public on GitHub; `hacs.json` is required for the 2026.11 Marketplace.
- The **GitHub prerelease must exist** before attempting Marketplace installation. A branch or tag alone is not a published release.

## Marketplace setup — postponed until main has installable content

Marketplace installation of this prerelease is **not available while the default branch lacks installable integration files**. Follow the manual beta procedure above instead. Do not install an untested `main` stub.

## Beta smoke checklist

- [ ] The config flow opens and succeeds exactly once.
- [ ] Eight MW sensors are registered under **Swedish Power Sweden**.
- [ ] Positive and zero values are represented correctly; `unknown` is not invented as zero.
- [ ] Inspect sensor attributes: `source_measured_at`, `source_snapshot_at`, `timestamp_basis`, `quality`, `fetched_at`.
- [ ] Observe at least **four scheduled polling cycles** (about one hour) and confirm source timestamps progress; do not require updates at exact quarter-hours.
- [ ] Compare 2–3 values at approximately matching timestamps with Statnett's display or a trusted reference.
- [ ] Confirm Recorder graphs show history over time; do not expect MW sensors to be valid for the *Energy dashboard* energy (kWh) configuration.
- [ ] Reload the integration and check for duplicate entities or errors.
- [ ] Check Diagnostics: eight readings, freshness and flow status. Do not paste secrets.
- [ ] If possible, simulate a safe **source communication outage** through an isolated test environment (not by disabling your actual HA network) and verify `unavailable`/recovery behavior.

## What to record

Home Assistant Core version; beta version; installation method; successful sensor IDs; first observed values and timestamps; any unavailable sources; redacted errors/log lines; observations over one hour.

## Known limitations

- Source-wide data are not local household power readings.
- The net-exchange sensor is **raw signed** and should not yet be styled as import/export.
- SE1–SE4 raw flows are available in backend diagnostics only. Direction/sign checks remain open.
- Reactor output is the **national aggregate**; there are no Forsmark/Ringhals/Oskarshamn unit sensors yet.
- No custom Lovelace card or visual editor in b1.
- `main` remains unchanged for beta testing.

## Go/no-go criteria for stable

All beta smoke checks pass, no critical or data-correctness bugs, source terms/attribution reviewed, stable sensors over multiple intervals, known source-age behavior, version/docs/README cleaned. A stable release requires a separate decision; b1 alone is not permission to promote to `main`.
