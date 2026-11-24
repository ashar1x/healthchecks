#!/usr/bin/env python3
"""Compute requirements coverage from test names/markers and the traceability CSV.

Run from the repository root:
    python tools/traceability/coverage.py
    python tools/traceability/coverage.py --pytest-report evidence/raw/pytest-report.json

No third-party dependencies. The raw result is written unchanged to
evidence/raw/requirements-coverage.json. Exit code 0 = matrix internally valid;
2 = a CSV ID does not resolve (fix the matrix, do not commit).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCOPE_DOC = ROOT / "docs" / "01-scope-and-test-basis.md"
RISK_DOC = ROOT / "docs" / "05-risk-register.md"
TRACE_CSV = ROOT / "docs" / "07-traceability.csv"
TEST_DIR = ROOT / "tests" / "team"
OUT = ROOT / "evidence" / "raw" / "requirements-coverage.json"

FR_RE = re.compile(r"\bFR-\d{2}\b")
BR_RE = re.compile(r"\bBR-\d{2}\b")
RISK_RE = re.compile(r"\bRISK-\d{2}\b")
TEST_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)\s*\(")
# Python test names cannot contain "-", so accept FR10 / FR_10 as well as FR-10.
FR_TAG_RE = re.compile(r"(?<![A-Za-z0-9])FR[-_]?(\d{2})(?!\d)")
BR_TAG_RE = re.compile(r"(?<![A-Za-z0-9])BR[-_]?(\d{2})(?!\d)")


def ids_in(text: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(text))


def discover_tests() -> list[dict]:
    """One record per test function; IDs come from its name and decorators only."""
    found: list[dict] = []
    if not TEST_DIR.exists():
        return found
    paths = sorted(TEST_DIR.rglob("test_*.py"))
    for path in paths:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        for i, line in enumerate(lines):
            match = TEST_DEF_RE.match(line)
            if not match:
                continue
            j = i - 1
            while j >= 0 and lines[j].lstrip().startswith("@"):
                j -= 1
            context = "\n".join(lines[j + 1 : i + 1])
            found.append(
                {
                    "name": match.group(1),
                    "file": path.relative_to(ROOT).as_posix(),
                    "fr_ids": sorted({f"FR-{n}" for n in FR_TAG_RE.findall(context)}),
                    "br_ids": sorted({f"BR-{n}" for n in BR_TAG_RE.findall(context)}),
                }
            )
    return found


def passed_test_names(report_path: Path | None) -> set[str] | None:
    if not report_path:
        return None
    data = json.loads(report_path.read_text(encoding="utf-8"))
    tests = data.get("report", {}).get("tests", data.get("tests", []))
    return {
        str(t.get("nodeid", "")).split("::")[-1].split("[")[0]
        for t in tests
        if t.get("outcome") == "passed"
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pytest-report",
        type=Path,
        default=None,
        help="pytest --json-report output; only outcome=passed tests count",
    )
    args = parser.parse_args()

    scope = SCOPE_DOC.read_text(encoding="utf-8")
    risks = RISK_DOC.read_text(encoding="utf-8")
    known_fr = ids_in(scope, FR_RE)
    known_br = ids_in(scope, BR_RE)
    known_risk = ids_in(risks, RISK_RE)

    with TRACE_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    dangling: list[str] = []
    csv_fr: set[str] = set()
    for row in rows:
        rid = row["requirement_id"].strip()
        csv_fr.add(rid)
        for field, pattern, known in (
            ("requirement_id", FR_RE, known_fr),
            ("rule_ids", BR_RE, known_br),
            ("risk_ids", RISK_RE, known_risk),
        ):
            for value in ids_in(row[field], pattern):
                if value not in known:
                    dangling.append(f"{rid}:{field}={value}")
    for missing in sorted(known_fr - csv_fr):
        dangling.append(f"no CSV row for {missing}")

    tests = discover_tests()
    planned = {fr for test in tests for fr in test["fr_ids"]}
    passed_names = passed_test_names(args.pytest_report)
    executed = None
    if passed_names is not None:
        executed = {
            fr
            for test in tests
            if test["name"] in passed_names
            for fr in test["fr_ids"]
        }

    def percent(n: int | None) -> float | None:
        return None if n is None else round(100.0 * n / len(known_fr), 1)

    result = {
        "source_of_requirements": SCOPE_DOC.relative_to(ROOT).as_posix(),
        "source_of_matrix": TRACE_CSV.relative_to(ROOT).as_posix(),
        "requirements_total": len(known_fr),
        "traceability_rows": len(rows),
        "rows_with_test_ids": sum(bool(r["test_ids"].strip()) for r in rows),
        "test_functions_found": len(tests),
        "requirements_with_planned_test": len(planned & known_fr),
        "planned_coverage_pct": percent(len(planned & known_fr)),
        "pytest_report": args.pytest_report.as_posix() if args.pytest_report else None,
        "requirements_with_passing_test": len(executed & known_fr) if executed is not None else None,
        "executed_coverage_pct": percent(len(executed & known_fr)) if executed is not None else None,
        "missing_or_invalid_ids": sorted(dangling),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if dangling:
        print("FAIL: unresolved traceability IDs: " + ", ".join(sorted(dangling)))
        return 2
    print(f"OK: {len(known_fr)} FR, {len(known_br)} BR, {len(known_risk)} RISK IDs resolve")
    print(
        f"Planned FR coverage: {result['requirements_with_planned_test']}/{len(known_fr)} "
        f"({result['planned_coverage_pct']}%)"
    )
    if executed is None:
        print("Executed FR coverage: not available - run pytest with --json-report first")
    else:
        print(
            f"Executed FR coverage: {result['requirements_with_passing_test']}/{len(known_fr)} "
            f"({result['executed_coverage_pct']}%)"
        )
    print(f"Raw result: {OUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
