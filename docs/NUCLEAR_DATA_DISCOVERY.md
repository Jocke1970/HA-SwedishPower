# Swedish nuclear data — source discovery and adapter status

> Research performed 2026-11-14 on the `dev` branch. **No reactor adapter is enabled in the installed `2026.11.0b1` beta.** Neither `beta` nor `main` has been changed.

## Sources verified by direct GET from GitHub Actions

### Vattenfall — five units (F1, F2, F3, R3, R4)

- Official Forsmark page: https://karnkraft.vattenfall.se/forsmark/produktion/
- Official Ringhals page: https://karnkraft.vattenfall.se/ringhals/produktion/
- Each responded **HTTP 200, HTML** with one marked `<script data-json-data>` JSON payload containing:
  - `timestamp` (offset-aware UTC ISO string);
  - `blockProductionDataList` with `name`, `production`, `percent`, `unit`.
- Both use the **same schema**; explicitly verified unit = `MW` for all five.
- Observation at source time `2026-11-14T22:00:00.206Z`: F1 0.032, F2 1129.125, F3 0, R3 0, R4 0 MW. **This is an observation, not a claim about current operations or outage causes.**
- Initial structure verification: [Vattenfall official pages probe](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43646804352).
- Live parser including `unit` validation: [nuclear source discovery](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43647118817).

Our independent `custom_components/swedish_power/vattenfall.py` adapter uses a proper HTML parser (not brittle HTML text scraping), preserves fractional MW, and marks missing, stale, invalid/future timestamps and unexpected units unavailable. It *never* interprets low power as a confirmed failure or maintenance outage.

### OKG — Oskarshamn 3 (O3)

- Official website: https://okg.se/ ; description of the current-output display: https://okg.se/var-verksamhet/kontrollrummet/
- Its public `/main.js` loads O3 data in the `production-meter` element using:
  `https://okg.se/.netlify/functions/getReactorOutput`
- Direct HTTP **200** on 2026-11-14; response contains valid JSON despite `Content-Type: text/plain`.
- Observed sanitized fields:
  - `value: 1432` (MW according to the operator's production display);
  - `valueDate: "2026-11-14T23:17:00"` (**timezone-naive Swedish local wall time**, inferred from direct comparison);
  - `timestamp: "2026-11-14T22:17:39.2611408Z"` (UTC API timestamp).
- Our `custom_components/swedish_power/okg.py` adapter resolves `valueDate` using `Europe/Stockholm`, anchored to the source's UTC timestamp. It tests ambiguous autumn DST and invalid springtime clock values. It does **not** use HA fetch time to fabricate a measurement timestamp.
- Direct discovery: [OKG JavaScript trace](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43647204978), [O3 endpoint probe](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43647253620).

**Assumption to keep explicit:** The endpoint does not identify the unit in its JSON; the MW interpretation is taken from the official visible gauge, not an endpoint `unit` key. Naive `valueDate` is treated as Stockholm local time based on matched timestamps. Verify this across DST periods and source publication gaps before a stable release.

### Nord Pool UMM — production outage and maintenance messages

- Discovered endpoint: `https://ummapi.nordpoolgroup.com/messages`.
- A bounded GET with `messageTypes=1&fuelTypes=14&limit=2&skip=0` returned **HTTP 200**, JSON, keys `items` and `total`; `total=1938` in the observed query.
- Message fields observed: `messageId`, `version`, `isOutdated`, `eventStatus`, `publicationDate`, `productionUnits`, `unavailabilityType`, `unavailabilityReason`, `reasonCode`, `remarks`; unit fields `name`, `areaName`, `fuelType`, `installedCapacity`, `timePeriods`; period fields `eventStart`, `eventStop`, `availableCapacity`, `unavailableCapacity`.
- `custom_components/swedish_power/umm.py` performs **conservative, non-production parsing** for exactly the six operational Swedish IDs F1/F2/F3/R3/R4/O3. It keeps raw event status and capacity claims, normalizes name aliases, filters foreign zones and outdated messages, and assigns only **reported time-window** labels. It does **not** infer actual outages, deduplicate UMM revisions, total unavailable capacity, or live MW.
- Initial HTTP and schema verification: [source discovery](https://github.com/Jocke1970/HA-SwedishPower/actions/runs/43647118817).
- Live first-page Swedish alias matching is a research-only smoke test; a first page does not prove coverage of **historical still-active** messages. Pagination, amendments, cancellations and source reuse rights remain to be verified.

## Code and testing status

- `vattenfall.py`, `okg.py`, `umm.py` and their offline tests are committed on **`dev` only**.
- Fixtures are narrow **transcriptions/illustrations** of observed schemas, not archived full external payloads. The UMM fixture is **synthetic**.
- All-source probe: `tools/nuclear_source_discovery.py`, runnable as a one-shot GitHub Actions job.
- Baseline repository Python tests were 15; new tests cover Vattenfall precision/error handling, OKG timezone/DST, and conservative UMM matching.
- **No sensor entities or scheduled polling of these additional sources are enabled yet.** The existing b1 Statnett integration and HA entities are unaffected.

## Outstanding gates before a reactor-sensor beta

1. Verify operator source reuse terms and acceptable access frequency. Public reachability does not automatically imply unrestricted API rights.
2. Test UMM paging across all relevant notices, cancellation/revision semantics, and filter correctness. Never sum overlapping UMM unavailable MW.
3. Decide whether the actual operator-page `unit` and historical source timestamp behavior support a 90-minute stale threshold for each independent reactor feed.
4. Wire independent, failure-isolated source coordinators into HA; add six stable-ID MW entities and separate **evidence-based** notice/status attributes only after UMM semantics tests.
5. Validate on a real HA Core test runtime and with current operator data; release through **dev → beta → main**. Never install `dev` directly.

## Credits and prior art

The open-source MIT-licensed [MorningBriefing](https://github.com/wh1xdy/MorningBriefing) project pointed us to the general Vattenfall embedded JSON and Nord Pool UMM approach. Our adapters are independently implemented, with additional timestamp, unit and safety checks. Third-party repository licensing and operators' data reuse terms are separate issues.
