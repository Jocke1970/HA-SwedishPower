# Backend MVP — Sweden only (development branch)

> **Status:** implementation in `dev`; **not yet a beta release or HA-installed verification**.
>
> Scope: Statnett's **national Sweden** production / consumption / raw-sign net-exchange data. Default refresh **15 minutes**. No frequency stream, individual reactor sensors or directional flow cards in this milestone.

## Installation once a beta is approved

The integration lives in `custom_components/swedish_power/`. For beta testing, copy that complete folder into Home Assistant's `config/custom_components/swedish_power/`, restart Home Assistant, then add **Swedish Power** under **Settings → Devices & services → Add integration**.

**Do not install `dev` in production.** This paragraph is preparation for a future beta, not an instruction to deploy immediately.

No API key is needed for the two Statnett endpoints verified on 2026-11-14.

## First eight sensors

The integration creates eight country-level **MW** sensors, all backed by `countryCode=SE` rows:

| Sensor translation key | Statnett field | Description |
| --- | --- | --- |
| `production` | `ProductionData` | National generation |
| `consumption` | `ConsumptionData` | National consumption |
| `net_exchange` | `NetExchangeData` | Signed net exchange, **direction interpretation pending** |
| `hydro` | `HydroData` | Hydropower |
| `wind` | `WindData` | Wind power |
| `nuclear` | `NuclearData` | Nuclear power, **not per-reactor** |
| `thermal` | `ThermalData` | Thermal power |
| `other` | `NotSpecifiedData` | Unspecified / other production; **not separately verified solar** |

These sensors are **electric power in MW**, not accumulated energy in MWh. The exact generated entity IDs depend on HA entity registry names and translations. Unique IDs are stable: `swedish_power_se_<key>`.

The Statnett physical-flow endpoint is also polled **at most once per scheduled refresh**; current raw-flow records are retained in the coordinator for diagnostics only. Until sign/direction is independently established, **there are no directional SE1–SE4 sensors**.

## Source timestamps and availability

Every sensor includes:
- `source`, `scope`, `source_measured_at`, `source_snapshot_at`, `fetched_at`;
- `timestamp_basis`: `row` or `snapshot`; `period_start_label` / `period_end_label` as supplied;
- `quality`: `valid`, `missing`, `unknown_timestamp`, `stale` or `future_timestamp`;
- `data_kind`: source-reporting caveat (planned/actual composition not confirmed).

For the **national total** and **net-exchange total**, direct Statnett samples had null row-level `measuredAt`. The parser falls back to **Statnett's own `MeasuredAt`** and explicitly labels it `snapshot`. It NEVER uses HA retrieval time as a measurement timestamp.

A present number is reported only when its quality is `valid`; otherwise its entity is `unavailable`, not 0. Explicitly reported numeric 0 remains valid.

**Provisional freshness cutoff: 90 minutes**, independent of the 15-minute poll interval. The source can report older values, so the UI must always surface the actual source time.

## Failure handling

- Network requests use Home Assistant's shared async aiohttp session and a per-request **15-second timeout**.
- The two endpoints are requested once during each update (in parallel), avoiding an unbounded retry loop.
- Production endpoint errors fail the update and mark coordinator entities unavailable; the normal coordinator handles scheduled retry.
- If physical-flow fetching or parsing fails, national power values remain available; the diagnostics report the optional flow failure.
- Missing categories or malformed schema reject the current update instead of creating fabricated readings.
- No API keys, secrets, raw response dumps or arbitrary untrusted text are stored in state attributes.

## Testing

```bash
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests tools
python -m json.tool custom_components/swedish_power/manifest.json >/dev/null
```

An Actions workflow also executes the source probe directly against Statnett to confirm the parser is compatible with current JSON. Those checks **do not replace a Home Assistant runtime test**. Before beta promotion we still need to verify UI setup, entity registration, reload/unload, Recorder history, and behavior on real outages in a safe HA test environment.

## Constraints / next work

1. Independently cross-check Statnett `NetExchangeData` sign and physical flow orientation before adding import/export arrows or the SE-zone flow entities.
2. Confirm data source access/reuse terms and attribution.
3. Verify publication latency and 90-minute stale threshold over multiple 15-minute periods.
4. Separate reactor adapters (Vattenfall, OKG, UMM) belong to the next milestone. A 0 MW national nuclear share is **not** evidence of any unit failure.
5. Beta is released **after** tests; don't advance `dev` changes straight to `main`.
