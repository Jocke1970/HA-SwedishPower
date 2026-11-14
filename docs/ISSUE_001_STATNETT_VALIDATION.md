# Issue #1 — Statnett direct access and Sweden-only data validation

**Date:** 2026-11-14  
**Status:** **Direct JSON access VERIFIED; field semantics and production readiness still under validation.**

## Direct origin verification — PASSED

A one-shot test ran on an Ubuntu GitHub Actions runner from the project's `dev` branch at **2026-11-14 14:32 UTC**. The test made direct unauthenticated HTTPS requests to `driftsdata.statnett.no`, without NordAPI or any intermediary data provider.

**Evidence:** [GitHub Actions run #1, successful](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43605396288) — full HTTP response summary and data field structure are available in the step logs. Reproducible script: [`.github/workflows/statnett-direct-probe.yml`](../.github/workflows/statnett-direct-probe.yml).

| Direct URL suffix | HTTP | Content-Type | Body size | Actual root |
| --- | --- | --- | --- | --- |
| `/restapi/ProductionConsumption/GetLatestDetailedOverview` | **200** | `application/json; charset=utf-8` | 21,644 bytes | JSON **object** |
| `/restapi/PhysicalFlowMap/GetFlow` | **200** | `application/json; charset=utf-8` | 3,266 bytes | JSON **array**, 34 rows |

No API key or authentication header was supplied. The source returned JSON. Earlier web-browsing errors claiming unsupported `application/xml` and the local container's DNS failures were **limitations of those testing environments**, not reliable evidence of the API's actual JSON content.

### Production: actual Swedish sample

The direct JSON object contains: `MeasuredAt`, `Headers`, `ProductionData`, `NuclearData`, `HydroData`, `ThermalData`, `WindData`, `NotSpecifiedData`, `ConsumptionData`, `NetExchangeData`. Each listed category contains nine rows; rows have `countryCode` such as `SE`, a string `value`, `measuredAt`, `periodStart`, `periodEnd`, and translation/description fields.

| Source field for `countryCode=SE` | Observed reported value |
| --- | ---: |
| `ProductionData` | **20,734 MW** |
| `ConsumptionData` | **21,165 MW** |
| `NetExchangeData` | **431 MW** |
| `NuclearData` | **2,503 MW** |
| `HydroData` | **10,035 MW** |
| `WindData` | **6,805 MW** |
| `ThermalData` | **2 MW** |
| `NotSpecifiedData` | **1,389 MW** |

These values are a **point-in-time example, not a continually updated reading**. The individual source rows for the last six categories and consumption had `measuredAt = 2026-11-14T13:30:00+00:00`, with displayed period **14:30–14:45 CET**. `ProductionData` and `NetExchangeData` each had `measuredAt: null` and empty period labels. The response also includes an overall `MeasuredAt` field; source-level and aggregate times must be treated distinctly.

**Arithmetic check:** 10,035 + 6,805 + 2,503 + 1,389 + 2 = **20,734 MW**. Consumption − production = **431 MW**, matching the reported `NetExchangeData` for this sample. Sign conventions must be verified across more periods before labelling import/export for all conditions.

### Physical flows

The direct endpoint returned a JSON array with **34 records**, each including `OutAreaElspotId`, `InAreaElspotId`, `Value` and `MeasureDate` (Unix milliseconds). Example rows in this response included:
- `OutAreaElspotId=DE`, `InAreaElspotId=SE4`, `Value=346.0`, `MeasureDate=1794666709000`.
- `OutAreaElspotId=DK1`, `InAreaElspotId=SE3`, `Value=626.4779`, same timestamp.

**Important:** no direction or net export interpretation is implied by the labels or sign until independently cross-checked. Values are raw MW. We must filter pairs involving SE1–SE4 and avoid assuming generation by type exists for each bidding zone.

## Reproducible integration checks

The repo contains a one-shot Python source probe:
- `tools/statnett_probe.py`: direct GET, JSON parsing, Swedish extraction, time parsing and freshness markers.
- `tests/test_statnett_probe.py` and `tests/fixtures/`: **illustrative** offline samples and unit tests.
- `.github/workflows/statnett-direct-probe.yml`: direct HTTP check, and a follow-up parser validation step.

```bash
python -m unittest discover -s tests -v
python tools/statnett_probe.py
```

The offline example fixtures originate from a prior **third-party** display and should not be misrepresented as raw direct API captures. Direct metadata above is transcribed from the new GitHub Actions run.

## Remaining work before marking Issue #1 done

- [x] Verify independent direct HTTPS access, HTTP status, JSON content-type and response structure for both endpoints.
- [x] Confirm that direct production data has `countryCode=SE` rows and raw flows contain Swedish area codes.
- [x] Confirm Swedish national generation, consumption and mix are numerically parseable and consistent in this sample.
- [ ] Repeat measurements across periods, including exports, to establish net-exchange sign semantics.
- [ ] Validate area-flow direction/sign and compare timestamps with a trusted Statnett/SvK visualization.
- [ ] Test 15-minute polling behavior, temporary errors, rate-limits and freshness policy.
- [ ] Confirm reuse/attribution terms before publishing a reusable integration.
- [ ] Preserve raw-source timestamp semantics and validated format in parser fixtures and HA mapping.

**Decision:** Direct JSON access is verified and suitable for the next engineering checks. **Issue #1 stays open** until flow semantics and source policy are established; no stable HA release yet.
