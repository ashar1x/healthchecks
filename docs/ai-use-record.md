# AI-use record

One row per member per AI-assisted piece. Required in the final PDF. `docs/prompts/` holds the corresponding prompt text with its date.

| Date | Member | Tool and model | Purpose | Output | What the member checked or changed |
|---|---|---|---|---|---|
| 2026-11-23 | Taimoor Khaliq (24i-3052) | OpenCode agent, model `opencode/big-pickle` | Draft Phase 4 test-management documents on `area2/taimoor` from Ashar's Phase 1–3 work | `docs/03-test-plan.md`, `docs/04-estimation.md`, `docs/05-risk-register.md` + CSV, `docs/06-exit-criteria.md`, `docs/07-traceability.md` + CSV, `tools/traceability/coverage.py` | Reviewed and corrected with Claude Code (next row). Estimates, risk scores and thresholds marked `[CONFIRM]` are **not yet confirmed**; they remain proposals for the Phase 4 team call. |
| 2026-11-23 | Taimoor Khaliq (24i-3052) | Claude Code, model `claude-opus-5-5` | Apply and verify the Phase 4 bundle, correct defects found, commit and open the PR at Taimoor's request | Fixes in `tools/traceability/coverage.py`, `docs/05-risk-register.md`, `docs/03-test-plan.md`; this record; `docs/prompts/2026-11-23-phase4.md` | Both verification commands re-run and passing. Changed: script now counts `test_FR10_BR02_...` names; score 5 labelled Low in the matrix; exit-criteria risk links corrected; weekly-report path made consistent. `[TAIMOOR TO ADD: own review notes after the Phase 4 call]` |

## Notes

- The agent prepared drafts only; Taimoor Khaliq owns, reviews, edits and commits them under his own GitHub identity.
- No output was copied from upstream tests or from generated evidence; all raw results are saved under `evidence/raw/`.
- Add a row for every later AI-assisted piece (spec, generator, API tests, reports).
