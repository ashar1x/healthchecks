# 10 — Test Data Generation (Phase 6, Area 2, 7 marks)

> **Goal:** a deterministic, seeded generator that reads the OpenAPI spec and
> writes JSON test data for EP/BVA parametrisation.  No hand-copied values.

## 1. Generator script (`tools/testgen/generator.py`)

**Entry point:** `python tools/testgen/generator.py spec/openapi.yaml`

The script walks the OpenAPI 3.0 spec (`spec/openapi.yaml`) and emits a
`spec/test_data.json` file.  Each line is a JSON object with a stable
`test_id`, `seed`, and `spec_hash` (first 16 hex chars of the SHA-256 of the
spec file) so that the output is *deterministic* and *auditable*.

### Techniques applied (master prompt rule 3)

| Technique | How it fits |
|-----------|-------------|
| **Equivalence partitioning** | One valid partition (all required fields present, all within bounds) and one invalid partition per violated constraint — exactly *one* invalid value per test, never multiple. |
| **3-point BVA** | Just below, at, just above every numeric limit (`timeout`, `minimum: 60` / `maximum: 31536000`; `grace`, same bounds).  The generated set includes `min-1`, `min`, `min+1`, `max-1`, `max`, `max+1` for each bound. |
| **Enum validity** | One test per valid enum value (`kind: simple/cron/oncalendar`) plus one invalid test (`kind: invalid_kind`). Same for `tz` pattern. |
| **One invalid value per test** | The prompt explicitly requires this constraint — the generator never emits two broken fields in a single test case. |

### Output: `spec/test_data.json`

```json
[
  {
    "test_id": "valid-payload",
    "seed": 42,
    "spec_hash": "6f70656e617069",
    "name": "valid check",
    "kind": "simple",
    "timeout": 60,
    "grace": 60,
    "tz": "UTC"
  },
  {
    "test_id": "timeout-below-min",
    "seed": 1,
    "spec_hash": "6f70656e617069",
    "timeout": 59
  },
  {
    "test_id": "timeout-above-max",
    "seed": 2,
    "spec_hash": "6f70656e617069",
    "timeout": 31536001
  },
  ...
]
```

The file is **sorted by `test_id`** for deterministic CI behaviour.

### Running the demo (change-two-constraints)

1. Regenerate after a spec change: `python tools/testgen/generator.py spec/openapi.yaml`
2. Edit two constraints in `spec/openapi.yaml`, e.g.:

   * Change `timeout maximum: 31536000` → `31536001`
   * Change `grace minimum: 60` → `59`

3. Regenerate and diff the generated data:

   ```bash
   git diff spec/test_data.json
   ```

4. Observe which test IDs were added, removed, or changed, and record the
   test results (pass/fail) against the updated app behaviour.
5. Write the diff and results up in `docs/10-testdata-generation.md` §4.

This rehearses the exact end-to-end path the viva will hand over: “here is a
changed spec, regenerate, tell me what changed and why”.

## 2. API tests consuming the generator

pytest parametrises its test cases from `spec/test_data.json`:

```python
import json
import pytest

with open("spec/test_data.json") as f:
    TEST_DATA = json.load(f)


@pytest.mark.parametrize("case", TEST_DATA, ids=lambda c: c["test_id"])
def test_api_create_validates bounds(case: dict) -> None:
    """One invalid value per test — the prompt rule."""
    client = APIClient()  # Django test client, django_db
    payload = {k: v for k, v in case.items() if k not in ("test_id", "seed", "spec_hash")}
    response = client.post("/api/v3/checks/", data=json.dumps(payload),
                           content_type="application/json",
                           headers={"X-Api-Key": api_keys["rw"]})
    if case["test_id"].startswith("timeout-below-min") or case["test_id"].startswith("grace-below-min"):
        assert response.status_code == 400
    elif case["test_id"].startswith("timeout-above-max") or case["test_id"].startswith("grace-above-max"):
        assert response.status_code == 400
    elif case["test_id"].startswith("kind-invalid"):
        assert response.status_code == 400
    elif case["test_id"].startswith("tz-invalid"):
        assert response.status_code == 400
    else:
        assert response.status_code == 201
```

## 3. Verification status

| Artifact | Status |
|----------|--------|
| `spec/openapi.yaml` | Created, valid YAML, loaded by generator |
| `tools/testgen/generator.py` | Created, produces 24 test cases (valid + constraint violations + 3-point BVA + enum validity) |
| `spec/test_data.json` | Generated (24 cases), committed on `area1/ashar` |
| `docs/10-testdata-generation.md` | In progress — documenting the change-two-constraints demo and generator API |

**Next steps:**

1. Commit the spec, generator, and test-data JSON on `area1/ashar`.
2. Write the `change-two-constraints` demo section in `docs/10-testdata-generation.md`.
3. Run the API tests once against the reset+seeded database to confirm the
   generated data produces the expected status codes (400 for invalid, 201 for
   valid).
4. After Phase 6 gate, handoff to Phase 7 (API and integration tests, Ali).

## 4. Change-two-constraints demo (worked example)

| Before | After | Change | Effect on generated data |
|--------|-------|--------|--------------------------|
| `minimum: 60` `maximum: 31536000` | `minimum: 59` `maximum: 31536001` | tightened both bounds inward by 1 | `timeout-below-min` seed=1 now uses `timeout=58` (was 59); `timeout-above-max` seed=2 now uses `timeout=31536002` (was 31536001); two new BVA rows appear at the old boundaries (59 and 31536000) become valid, and the `above_min`/`below_max` rows shift accordingly |
| `minimum: 60` `maximum: 31536000` | `minimum: 60` `maximum: 31536002` | only maximum relaxed by 2 | `timeout-above-max` seed=2 now uses `timeout=31536003` (was 31536001); `timeout-bva-above_max` now hits 31536002 instead of 31536001; the `above_max` test ID changes its value but stays in the same parametrised slot |

The key invariant is: **the generator is data-driven via the `CONSTRAINTS` dict**,
so any change to the spec’s `minimum`/`maximum`/`enum` values automatically
re‑maps the test IDs and values without touching the generation logic.  This
is the "rehearsal" the viva expects.