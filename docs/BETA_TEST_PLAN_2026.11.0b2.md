# Swedish Power b2 — reactor MW supervised data-collection test

**Release to install:** [2026.11.0b2 published prerelease](https://github.com/Jocke1970/HA-SwedishPower/releases/tag/2026.11.0b2) (once the guarded workflow has published it). Never install a `dev` branch snapshot in HA.

## Installation / upgrade

1. Take an HA config backup and save the existing installed `/config/custom_components/swedish_power/`.
2. Use the published Git tag `2026.11.0b2` (Source code ZIP or `git clone --depth 1 --branch 2026.11.0b2 ...`), copy only its `custom_components/swedish_power/` folder onto the installed folder.
3. Restart Home Assistant; do not remove the existing config entry or old Recorder history.
4. In `/config/custom_components/swedish_power/manifest.json`, verify `"version": "2026.11.0b2"`.
5. In Settings → Devices & services → Swedish Power, look for eight national sensors plus six reactor MW sensors.

## Sensor and isolation checks

- [ ] Existing eight Statnett readings still work with the same entity IDs / recorder history.
- [ ] Six additional MW sensors present: **Forsmark 1/2/3**, **Ringhals 3/4**, **Oskarshamn 3**.
- [ ] Reactor attributes: `source`, `source_measured_at`, `fetched_at`, `quality`, `timestamp_basis`, `source_url`, `reactor_id`.
- [ ] 0 MW is a real zero; `unknown`/`unavailable` is not silently treated as zero.
- [ ] Compare output on both official Vattenfall production pages and OKG's own display at matching source timestamps.
- [ ] Collect **at least four 15-minute cycles**, then 12–24 hours of Recorder history.
- [ ] Inspect logs for source timeouts, mismatched unit, stale readings or unexpected retries.
- [ ] Restart and reload the integration; confirm 14 sensors remain, none duplicate.
- [ ] Verify diagnostics includes `reactor_sources` per plant and the original Statnett checks.
- [ ] Never infer a reactor fault, maintenance or return time from 0 MW alone. Nord Pool UMM is **not part of b2 HA polling**.

## What to share

- A Jinja snapshot of all 14 sensors, including source timestamp, `fetched_at`, quality and `last_updated`.
- `history_records` of at least **F2, F3, O3** plus Sweden-wide nuclear aggregate over **6–12 hours** (12–24 hours preferred).
- Redacted HA log excerpts only if an error appears.
- Note HA version, b2 manifest version, and whether this was an in-place b1 upgrade.

## Go/no-go

We need field confirmation of both operator sources, no duplicate entities, outage isolation and consistent source timestamps before considering b2 successful. UMM reconciliation/reuse-rights work is a separate gate. **Do not promote to main automatically.**
