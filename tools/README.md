# One-shot Statnett research probe

The script `statnett_probe.py` is an **offline parser + optional direct HTTP probe** for the Sweden-only Statnett source investigation (Issue #1). It is not the Home Assistant integration.

## Run locally, no external dependencies

```bash
python -m unittest discover -s tests -v
python tools/statnett_probe.py --production-file tests/fixtures/statnett_se_production_excerpt.json --flows-file tests/fixtures/statnett_se_flows_excerpt.json
```

This only uses illustrative fixtures obtained from a third-party Statnett-derived response. It proves **parser behavior**, not source authenticity or direct availability.

## Attempt direct source reads

```bash
python tools/statnett_probe.py
```

Uses the two URLs documented at [Statnett's API index](https://driftsdata.statnett.no/restapi/) with a timeout and strict JSON content-type check. When the response is XML, HTML, an error, or unexpected JSON, the probe exits with an error **instead of pretending success**.

The browsing tool used during discovery reported an unsupported `application/xml` response for both direct endpoints, so direct access still requires confirmation from a normal HTTP client.

No polling loop or API key is included. If testing with `curl`, inspect status and content-type before trusting payload content.

See [validation log](../docs/ISSUE_001_STATNETT_VALIDATION.md).
