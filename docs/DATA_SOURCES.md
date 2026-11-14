# Data sources and verification register

> **Research register, not a list of production-verified endpoints.** Access methods, field semantics, freshness and reuse conditions must be checked before implementation. Updated: 2026-11-14.

| Candidate | Intended Sweden-only data | Initial status | Required verification |
| --- | --- | --- | --- |
| [Statnett Driftsdata REST overview](https://driftsdata.statnett.no/restapi/) | Swedish national generation mix, consumption, net exchange, physical SE1–SE4 flows | **Direct JSON access verified on 2026-11-14 via GitHub Actions; semantics require further checks** | Endpoint status, schema, timestamps, attribution, permission, cadence, region coverage |
| [Statnett production/consumption candidate](https://driftsdata.statnett.no/restapi/ProductionConsumption/GetLatestDetailedOverview) | Detailed production and consumption | **HTTP 200 / JSON verified** | Individual timestamp semantics, actual/planned definitions, unit semantics and reuse terms |
| [Statnett physical flows candidate](https://driftsdata.statnett.no/restapi/PhysicalFlowMap/GetFlow) | Area-to-area MW flows | **HTTP 200 / JSON verified; 14 Sweden-related pairs parsed** | Direction/sign conventions, stale flow handling and reuse terms |
| [Svenska kraftnät Kontrollrummet](https://www.svk.se/om-kraftsystemet/kontrollrummet/) | Reference presentation and cross-checking | **Reference page; not assumed a public API** | Source attribution, definitions, publication delays |
| [Vattenfall Forsmark/Ringhals](https://karnkraft.vattenfall.se/) | F1–F3, R3–R4 power | **Direct HTML + embedded JSON verified, 5 reactor IDs and MW unit** | Source rights, production cadence, capacity definition, anomaly behavior |
| [OKG production meter](https://okg.se/) | O3 power | **HTTP 200, JSON response verified via OKG's own JS endpoint** | Naive local `valueDate`, source rights, DST and freshness |
| [Nord Pool UMM API](https://ummapi.nordpoolgroup.com/messages) | Reactor notice periods and reported capacity | **Direct HTTP 200 JSON verified; 48 Swedish periods across 6 reactors on a 100-message sample** | Full paging, cancellation/revision handling, permissions and semantics |
| [Nordisk Kärnkraft](https://www.nordiskkarnkraft.se/sv/se) | Third-party aggregated reactor cross-check | **Reference only** | Terms and provenance; do not build an undisclosed scraping dependency |
| ENTSO-E Transparency | Optional fallback/validation of generation by type | **Future/optional** | Access token, measured versus delayed data, mapping, licensing |
| Existing HA Nord Pool entities | Optional SE1–SE4 electricity prices | **Later UI enrichment** | Entity availability and user configuration |

## Validation protocol

For every candidate endpoint:
1. Fetch an actual response, record HTTP status, content-type, authentication need and date.
2. Store a **sanitized** response fixture without secrets or personal data.
3. Verify geographic key (`SE`, `SE1`–`SE4`), unit (MW/MWh), period boundaries and timezone.
4. Compare reported measurement time with fetching time; check age and missing/null values.
5. Validate aggregation and sign conventions against a known reference at the same period.
6. Review permissions, acceptable polling and attribution before using the endpoint.
7. Document behavior on 429/rate limiting, 5xx, malformed payload and source silence.

Do **not** claim SE1–SE4 production-by-type exists until validated. Do **not** infer individual reactor operational status or cause solely from MW output.

See [Nuclear data discovery](NUCLEAR_DATA_DISCOVERY.md) for the exact schemas, observed values, source timestamps and research-only parser limitations.

## Initial MVP priority

1. Statnett Swedish production/consumption response and fields.
2. Statnett Swedish area-to-area physical flows.
3. Independent official individual-reactor output sources.
4. Structured UMM notices and status reconciliation.

**Out of first release:** monitoring neighboring countries' national generation, high-frequency live refresh, and other Nordic dashboards.

## Verified direct HTTP baseline — 2026-11-14

Two GitHub Actions runs confirmed `HTTP 200` and `application/json; charset=utf-8` directly from the two Statnett endpoints, **without an API key or a third-party proxy**. The second run also passed all **six offline tests** and parsed the live Swedish values using the project Python probe:

- [Direct HTTP run](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43605396288)
- [Parser and offline tests run](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43605579911)
- [Detailed validation report](ISSUE_001_STATNETT_VALIDATION.md)

The parser identified **14 flow pairs involving SE1–SE4**: **3 internal pairs** and **11 cross-border pairs**. Direction/sign has **not yet been established**. Production, consumption and exchange returned national `SE` fields; direct per-bidding-zone production-by-type remains **unverified**. Current snapshot `MeasuredAt` is available even though some aggregate row `measuredAt` fields are null.
