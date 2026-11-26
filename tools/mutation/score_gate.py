#!/usr/bin/env python3
"""Mutation score / CI gate for the Phase 8 business-rule module.

mutmut mutates every covered line of the two measured files, including
serialisation helpers that the unit suite deliberately does not assert
(``Check.to_dict``, ``channels_str``, ``isostring``).  Those helpers are listed
as out of measurement scope in docs/08-unit-testing.md §1 and §5.  This gate
therefore reports two numbers:

  * full-file score  - every mutant in hc/api/models.py + decorators.py;
  * business-rule score - only the functions named as the Phase 5/8
    measurement target (get_status, get_grace_start, going_down_after, ping,
    pause/resume data rules, prune, create_flip and the API role decorators).

The CI gate threshold (80%) is applied to the business-rule score.  A mutant
with exit code 5 ("no tests") counts as survived: an undetected change is an
undetected change whether or not a test was associated with it.

Usage::

    python tools/mutation/score_gate.py            # gate (exit 1 below 80%)
    python tools/mutation/score_gate.py --no-gate  # report only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
META_DIR = ROOT / "mutants" / "hc" / "api"
OUTPUT = ROOT / "evidence" / "mutation" / "mutmut-summary.json"

# docs/08-unit-testing.md §1 - the measured business logic.
MEASURED_FUNCTIONS = frozenset(
    {
        "get_status",
        "get_grace_start",
        "going_down_after",
        "cached_status",
        "clamped_last_duration",
        "ping",
        "prune",
        "create_flip",
        "last_duration",
        "status_url",
        "authorize",
        "authorize_read",
        "cors",
    }
)

KILLED_CODES = {1, 3}  # pytest test failure / internal error = mutant killed
NO_TESTS_CODE = 5


def function_of(mutant_name: str) -> str:
    stem = mutant_name.rsplit("__mutmut_", 1)[0]
    if "ǁ" in stem:
        return stem.split("ǁ")[-1]
    return stem[2:] if stem.startswith("x_") else stem


def collect() -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {"full": {}, "business_rules": {}}
    for meta_file in sorted(META_DIR.glob("*.meta")):
        data = json.loads(meta_file.read_text()).get("exit_code_by_key", {})
        for name, code in data.items():
            if code is None:
                continue
            if code in KILLED_CODES:
                verdict = "killed"
            elif code == NO_TESTS_CODE:
                verdict = "no_tests"
            elif code == 0:
                verdict = "survived"
            else:
                verdict = "other"
            result["full"][verdict] = result["full"].get(verdict, 0) + 1
            if function_of(name) in MEASURED_FUNCTIONS:
                result["business_rules"][verdict] = result["business_rules"].get(verdict, 0) + 1
    return result


def score(stats: dict[str, int]) -> float:
    killed = stats.get("killed", 0)
    undetected = stats.get("survived", 0) + stats.get("no_tests", 0) + stats.get("other", 0)
    total = killed + undetected
    return round(100 * killed / total, 1) if total else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-gate", action="store_true", help="report only, never fail")
    parser.add_argument("--threshold", type=float, default=80.0)
    args = parser.parse_args()

    stats = collect()
    full_score = score(stats["full"])
    br_score = score(stats["business_rules"])

    print(f"Full-file mutation score:  {full_score}%  (mutants: {stats['full']})")
    print(f"Business-rule score:       {br_score}%  (mutants: {stats['business_rules']})")
    print(f"Gate threshold:            {args.threshold}% (applied to business-rule score)")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "full_file": {"stats": stats["full"], "score": full_score},
                "business_rules": {"stats": stats["business_rules"], "score": br_score},
                "measured_functions": sorted(MEASURED_FUNCTIONS),
                "threshold": args.threshold,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Evidence: {OUTPUT.relative_to(ROOT)}")

    if not args.no_gate and (sum(stats["business_rules"].values()) == 0 or br_score < args.threshold):
        print("::error::Business-rule mutation score below threshold")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
