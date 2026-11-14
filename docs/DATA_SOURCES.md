# Data sources and verification register

> **Research register, not a list of production-verified endpoints.** Access methods, field semantics, freshness and reuse conditions must be checked before implementation. Updated: 2026-11-14.

| Candidate | Intended Sweden-only data | Initial status | Required verification |
| --- | --- | --- | --- |
| [Statnett Driftsdata REST overview](https://driftsdata.statnett.no/restapi/) | Swedish national generation mix, consumption, net exchange, physical SE1–SE4 flows | **Candidate; exact live responses not yet confirmed in this repository** | Endpoint status, schema, timestamps, attribution, permission, cadence, region coverage |
| [Statnett production/consumption candidate](https://driftsdata.statnett.no/restapi/ProductionConsumption/GetLatestDetailedOverview) | Detailed production and consumption | **Test required** | Field meanings, whether values are measured/estimated/planned, units, Swedish coverage |
| [Statnett physical flows candidate](https://driftsdata.statnett.no/restapi/PhysicalFlowMap/GetFlow) | Area-to-area MW flows | **Test required** | Flow direction, sign convention, SE pairs, timestamp and duplicates |
| [Svenska kraftnät Kontrollrummet](https://www.svk.se/om-kraftsystemet/kontrollrummet/) | Reference presentation and cross-checking | **Reference page; not assumed a public API** | Source attribution, definitions, publication delays |
| Vattenfall official power-plant reporting | Forsmark F1–F3, Ringhals R3–R4 unit power | **Access path to validate** | Fetch method, licence/terms, gross/net, measurement time, capacity and availability |
| OKG official reporting | Oskarshamn O3 unit power | **Access path to validate** | Same checks as Vattenfall |
| Nord Pool UMM / relevant outage feed | Planned and unplanned unit notices | **Access path to validate** | Permitted API/data access, mapping notices to reactor, updates, amended return estimates |
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

## Initial MVP priority

1. Statnett Swedish production/consumption response and fields.
2. Statnett Swedish area-to-area physical flows.
3. Independent official individual-reactor output sources.
4. Structured UMM notices and status reconciliation.

**Out of first release:** monitoring neighboring countries' national generation, high-frequency live refresh, and other Nordic dashboards.
