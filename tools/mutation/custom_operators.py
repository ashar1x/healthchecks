#!/usr/bin/env python3
"""Two custom mutation operators derived from the project's business rules.

The SQE brief requires at least two custom operators (Phase 8 / mutation and CI
quality gate).  mutmut's built-in operators are generic; these operators encode
the two rules that drive the selected workflows:

  * BR-01 (boundary): timeout / grace must be in 60..31536000 seconds.
    ``BoundaryValueOperator`` shifts each limit by +/-1 (four mutants per
    field), the exact off-by-one values that 3-point BVA must catch.

  * BR-02 / BR-03 (compound condition / state transition): ``get_status`` and
    ``ping`` decide state from compound Boolean conditions.
    ``BooleanNegationOperator`` negates a condition, flips a comparison, swaps
    and/or, or flips a state equality, one change at a time.

Each mutant is applied to the real source file, the relevant team tests are
run, and the file is restored in a ``finally`` block.  A mutant is "killed" if
the selected tests fail (non-zero pytest exit code) and "survived" otherwise.
Evidence is written to evidence/mutation/custom-operators.json.

Usage (from the repository root, inside the venv)::

    python tools/mutation/custom_operators.py            # run all mutants
    python tools/mutation/custom_operators.py --dry-run  # list them only

NOTE: do not run this while ``mutmut run`` is in progress; both tools rewrite
source files in place.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMS = ROOT / "hc" / "front" / "forms.py"
MODELS = ROOT / "hc" / "api" / "models.py"
OUTPUT = ROOT / "evidence" / "mutation" / "custom-operators.json"

BVA_TESTS = ("tests/team/unit/test_validation_bva.py",)
STATE_TESTS = (
    "tests/team/unit/test_get_status_mcc.py",
    "tests/team/unit/test_get_status_edges.py",
    "tests/team/unit/test_ping_state_machine.py",
)


@dataclass(frozen=True)
class Mutant:
    id: str
    operator: str
    rule: str
    file: str
    description: str
    start: int
    end: int
    replacement: str
    tests: tuple[str, ...]


def _mutant(
    mid: str,
    operator: str,
    rule: str,
    path: Path,
    source: str,
    old: str,
    new: str,
    description: str,
    tests: tuple[str, ...],
    occurrence: int = 0,
) -> Mutant:
    if source.count(old) <= occurrence:
        raise RuntimeError(
            f"{mid}: expected at least {occurrence + 1} occurrence(s) of {old!r}, "
            f"found {source.count(old)}"
        )
    start = -1
    for _ in range(occurrence + 1):
        start = source.index(old, start + 1)
    return Mutant(
        id=mid,
        operator=operator,
        rule=rule,
        file=str(path.relative_to(ROOT)),
        description=description,
        start=start,
        end=start + len(old),
        replacement=new,
        tests=tests,
    )


def boundary_value_mutants() -> list[Mutant]:
    """BR-01: shift the min/max limits of AddCheckForm's timeout and grace."""
    source = FORMS.read_text(encoding="utf-8")
    mutants: list[Mutant] = []
    for field in ("timeout", "grace"):
        old = f"    {field} = forms.IntegerField(min_value=60, max_value=31536000)"
        variants = (
            ("min_value=61, max_value=31536000", "exclude valid minimum (60 -> 61)"),
            ("min_value=59, max_value=31536000", "include invalid below-minimum (60 -> 59)"),
            ("min_value=60, max_value=31535999", "exclude valid maximum (31536000 -> 31535999)"),
            ("min_value=60, max_value=31536001", "include invalid above-maximum (31536000 -> 31536001)"),
        )
        for n, (args, description) in enumerate(variants, start=1):
            new = f"    {field} = forms.IntegerField({args})"
            mutants.append(
                _mutant(
                    f"BOUNDARY-{len(mutants) + 1}",
                    "BoundaryValueOperator",
                    "BR-01",
                    FORMS,
                    source,
                    old,
                    new,
                    f"{field}: {description}",
                    BVA_TESTS,
                )
            )
    return mutants


def boolean_negation_mutants() -> list[Mutant]:
    """BR-02/BR-03: negate one decision in get_status/get_grace_start/ping."""
    source = MODELS.read_text(encoding="utf-8")
    specs: list[tuple[str, str, str]] = [
        (
            "running state inverted in get_status",
            '        if self.last_start:\n            if frozen_now >= self.last_start + self.grace:',
            '        if not self.last_start:\n            if frozen_now >= self.last_start + self.grace:',
        ),
        ("grace comparison >= changed to >", "if frozen_now >= self.last_start + self.grace:", "if frozen_now > self.last_start + self.grace:"),
        ("status set membership negated", 'if self.status in ("new", "paused", "down"):', 'if self.status not in ("new", "paused", "down"):'),
        ("grace_start None test negated", "if grace_start is None:", "if grace_start is not None:"),
        ("grace_end boundary >= changed to >", "if frozen_now >= grace_end:", "if frozen_now > grace_end:"),
        ("grace_start boundary >= changed to >", "if frozen_now >= grace_start:", "if frozen_now > grace_start:"),
        ("min() changed to max() in get_grace_start", "result = min(result, self.last_start)", "result = max(result, self.last_start)"),
        ("compound and changed to or in get_grace_start", 'if with_started and self.last_start and self.status != "down":', 'if with_started or self.last_start and self.status != "down":'),
        ("cron condition and changed to or", 'if self.kind == "simple" and self.status == "up":', 'if self.kind == "simple" or self.status == "up":'),
        ("paused-state condition and changed to or in ping", 'if self.status == "paused" and self.manual_resume:', 'if self.status == "paused" or self.manual_resume:'),
        ("fail/success outcome swapped in ping", 'new_status = "down" if action == "fail" else "up"', 'new_status = "up" if action == "fail" else "down"'),
        ("state-change guard negated in ping", "if self.status != new_status:", "if self.status == new_status:"),
    ]
    mutants: list[Mutant] = []
    for n, (description, old, new) in enumerate(specs, start=1):
        if source.count(old) != 1:
            raise RuntimeError(f"BOOL-{n}: expected one occurrence of {old!r}, found {source.count(old)}")
        mutants.append(
            _mutant(
                f"BOOL-{n}",
                "BooleanNegationOperator",
                "BR-02/BR-03",
                MODELS,
                source,
                old,
                new,
                description,
                STATE_TESTS,
            )
        )
    return mutants


def run_mutant(mutant: Mutant, python: str, env: dict[str, str]) -> dict:
    """Apply one mutation, run its tests, restore the file, return evidence."""
    path = ROOT / mutant.file
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(
            original[: mutant.start] + mutant.replacement + original[mutant.end :],
            encoding="utf-8",
        )
        completed = subprocess.run(
            [python, "-m", "pytest", "-x", "-q", "--no-header", *mutant.tests],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        exit_code = completed.returncode
        stderr_tail = completed.stdout.strip().splitlines()[-1:] or [completed.stderr.strip()[-200:]]
    finally:
        path.write_text(original, encoding="utf-8")
    if path.read_text(encoding="utf-8") != original:
        raise RuntimeError(f"{mutant.id}: source file was not restored")
    return {
        **asdict(mutant),
        "status": "killed" if exit_code != 0 else "survived",
        "pytest_exit_code": exit_code,
        "pytest_summary": stderr_tail[0][:300] if stderr_tail else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="list mutants without running tests")
    args = parser.parse_args()

    mutants = boundary_value_mutants() + boolean_negation_mutants()
    if args.dry_run:
        for m in mutants:
            print(f"{m.id:12} {m.rule:10} {m.operator:24} {m.description}")
        print(f"Total custom mutants: {len(mutants)}")
        return 0

    env = os.environ.copy()
    env.setdefault("SECRET_KEY", "dummy-key")
    results = [run_mutant(m, sys.executable, env) for m in mutants]

    killed = sum(r["status"] == "killed" for r in results)
    survived = len(results) - killed
    evidence = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "pytest": "see venv requirements",
        "operators": [
            {
                "name": "BoundaryValueOperator",
                "rule": "BR-01",
                "target": "hc/front/forms.py AddCheckForm.timeout / .grace",
                "mutation": "min_value 60 -> 59/61; max_value 31536000 -> 31535999/31536001",
            },
            {
                "name": "BooleanNegationOperator",
                "rule": "BR-02/BR-03",
                "target": "hc/api/models.py get_status/get_grace_start/ping",
                "mutation": "negate condition; flip >=/==; swap and/or; min->max",
            },
        ],
        "summary": {
            "total": len(results),
            "killed": killed,
            "survived": survived,
            "score": round(100 * killed / len(results), 1),
        },
        "mutants": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    for r in results:
        print(f"{r['id']:12} {r['rule']:10} {r['status']:9} {r['description']}")
    print(f"Custom operators: {killed}/{len(results)} killed = {evidence['summary']['score']}%")
    print(f"Evidence: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
