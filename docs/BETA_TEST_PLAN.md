# HA-SwedishPower — supervised beta 2026.11.0b1

**Branch policy:** `dev → beta → main`. Test only the `beta` prerelease; **do not install `dev`**. `main` must remain unchanged until beta is accepted.

## Prerequisites

- Home Assistant **2026.11.0 or later**. The automated integration tests used Core 2026.11.0 and Python 3.14.
- Back up your Home Assistant configuration before installing any new custom integration.
- Ability to reach `driftsdata.statnett.no` through HTTPS.
- No API key is required for the two Statnett endpoints tested.
- The repository is public on GitHub; `hacs.json` is required for the 2026.11 Marketplace.
- The **GitHub prerelease must exist** before attempting Marketplace installation. A branch or tag alone is not a published release.

## Installation using Marketplace (Home Assistant 2026.11+)

1. Open **Settings → Marketplace**, then use **Add from link**.
2. Enter `https://github.com/Jocke1970/HA-SwedishPower`. A GitHub device sign-in may be requested for custom repositories.
3. Enable the repository's **Pre-release** entity under **Settings → Devices & services → Marketplace** and switch it on. The entity may be disabled by default and need enabling first.
4. On the repository page in Marketplace, install prerelease **2026.11.0b1**. Verify that the selected release is `2026.11.0b1`, **not `dev` or `main`**.
5. Restart Home Assistant after installation if prompted.
6. Open **Settings → Devices & services → Add integration**, find **Swedish Power**, and confirm **Sweden**.

If the repository is not installable or the release is not selectable, do not manually substitute `main` or `dev`. Collect the error message and link it to a new issue.

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
