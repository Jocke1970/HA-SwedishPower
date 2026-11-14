# Issue #1 — Statnett data validation log

**Date:** 2026-11-14  
**Scope:** Swedish production, consumption, net exchange and SE1–SE4 physical-flow pairs.  
**State:** **Partial: offline parser verified; direct API response not verified.**

## Evidence levels

- **Verified in this repository (local offline test):** Python parsing and normalization of **source-labelled illustrative excerpts**; six unit tests passed.
- **Third-party observed:** [NordAPI production/consumption documentation](https://nordapi.ee/docs/norway/no-statnett-production-consumption) shows fields including `ProductionData`, `ConsumptionData`, `NetExchangeData`, `HydroData`, `WindData`, `NuclearData`, `ThermalData`, `NotSpecifiedData`, `countryCode`, `measuredAt`, `periodStart`, `periodEnd`, `value`. [NordAPI physical flow documentation](https://nordapi.ee/docs/norway/no-statnett-physical-flows) shows `InAreaElspotId`, `OutAreaElspotId`, `MeasureDate`, `Value`. These are not proof that the **direct** endpoint will currently return the same envelope.
- **Statnett official listing:** [REST API index](https://driftsdata.statnett.no/restapi/) links to `ProductionConsumption/GetLatestDetailedOverview` and `PhysicalFlowMap/GetFlow`.
- **Direct API access:** Attempts to open these endpoints with the browsing environment on 2026-11-14 were rejected by its content parser with `Unsupported content-type: application/xml`. The response body, HTTP status, and actual origin-side format could **not** be established. This may be a tooling limitation or an XML error response. **Do not interpret it as confirmed success or a confirmed service outage.**
- **Current workspace command-line test:** Internet/DNS connectivity is unavailable in the execution container, so no direct origin response was captured there.

## What the offline fixture proves (and does not)

The `tests/fixtures/*_excerpt.json` files are small **illustrative transcriptions** from previously viewed third-party Statnett-derived data, not raw verifiable direct responses. They are intended to test parser behavior without asserting data provenance.

| Fixture field | Example | Interpretation |
| --- | --- | --- |
| `ProductionData` / Sweden | 20,323 MW | Numeric country field; total timestamp absent |
| `ConsumptionData` / Sweden | 20,753 MW | Different measurement time/period possible |
| `NetExchangeData` / Sweden | 430 MW | Numeric exchange field; **meaning of sign still unverified** |
| Production mix sum | 20,324 MW | Exceeds production total by 1 MW; do not silently force balance |
| `SE2` and `SE1` flow pair | 2,281.1069 MW (raw) | **Direction and sign convention unverified** |
| `MeasureDate` | Unix milliseconds | Must be converted to timezone-aware UTC |

The probe currently preserves the timestamp and does not interpret signed flow directions. Absent source timestamps are explicitly labelled `unknown_timestamp`. The **90-minute** staleness threshold is a temporary research default, not a final source-specific policy. The requested Home Assistant **poll interval remains 15 minutes**.

## Repeatable tests

```bash
python -m unittest discover -s tests -v
python tools/statnett_probe.py \
  --production-file tests/fixtures/statnett_se_production_excerpt.json \
  --flows-file tests/fixtures/statnett_se_flows_excerpt.json
```

To attempt **direct** reads from a machine with network access:

```bash
python tools/statnett_probe.py
```

This command is **one-shot**, not periodic. If it fails with unexpected `Content-Type`, manually inspect **HTTP status and response type first**, without publishing private data. For example:

```bash
curl -sS -D - -o /tmp/statnett-response \
  -H 'Accept: application/json' \
  'https://driftsdata.statnett.no/restapi/ProductionConsumption/GetLatestDetailedOverview'
file /tmp/statnett-response
```

If the direct response differs from the illustrated normalized shape, update the parser **only after** recording a sanitized real fixture. Do not silently fall back to an unauthorized proxy/scrape.

## Outstanding acceptance blockers

- [ ] Capture **direct** HTTP status, `Content-Type`, source payload schema and timestamped sanitized fixture for both Statnett endpoints.
- [ ] Check whether direct response is JSON or XML (or an error), and whether `data` is a wrapper added by a third party.
- [ ] Verify Sweden fields, units, the semantics of `NetExchangeData`, raw flow-direction conventions and geographic coverage.
- [ ] Cross-check values at matching measurement periods against Statnett/Svenska kraftnät.
- [ ] Check rate limits, permitted automated access and required attribution.
- [ ] Define source-specific freshness limits and error/retry behavior before Home Assistant backend implementation.

**Decision:** keep Issue #1 **open**. Proceed with schema and failure-case tests; do not claim a production-ready data source yet.
