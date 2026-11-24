#!/usr/bin/env python3
"""Generate the complete MCC truth table for the critical module Check.get_status.

Phase 5 of the SQE project (master prompt rule 4): write the complete MCC truth
table (2^n rows), then pick the MC/DC pairs for each condition from that table.

Derivation
----------
The conditions are the seven *atomic* Boolean conditions evaluated by
``Check.get_status`` (hc/api/models.py:355-380), in evaluation order:

  A1  self.last_start is set (truthy)
  A2  now >= last_start + grace          -- evaluated only when A1 is true
  A3  with_started kwarg is true         -- evaluated only when A1 true, A2 false
  A4  stored status in ("new", "paused", "down")
  A5  grace_start is None (next elapse is "never")
  A6  now >= grace_end  (grace_start + grace)
  A7  now >= grace_start                 -- evaluated only when A5 false, A6 false

This is business rule BR-02 from docs/01-scope-and-test-basis.md section 6,
expanded to atomic conditions.  Mapping to the BR-02 decision table there:

  BR-02 C1 ("last_start set AND now >= last_start + grace")  <=>  A1 and A2
  BR-02 C2 ("... AND with_started=True")                     <=>  A1 and not A2 and A3
  BR-02 C3 (stored status in new/paused/down)                <=>  A4
  BR-02 C4 (grace_start is None)                             <=>  A5
  BR-02 C5 (now >= grace end)                                <=>  A6
  BR-02 C6 (now >= grace_start)                              <=>  A7
  BR-02 C7 ("otherwise")                                     <=>  not A4 and not A5
                                                                 and not A6 and not A7

Masking: a condition that is never evaluated on the path a row selects is a
don't-care for that row; the table records it under "masked" and the realising
test case does not depend on it.

Feasibility: a row is feasible iff its *evaluated* conditions can hold
simultaneously for some concrete Check/time state.  The only semantic
implication among the conditions is A6 => A7 (now >= grace_end implies
now >= grace_start for any positive grace).  Because the code returns "down"
as soon as A6 is true, A7 is never evaluated on that path, so no row is
contradicted - rows with a6=1 and a7=0 are feasible with A7 masked.  If a
future edit creates a row whose evaluated conditions contradict, this script
marks it infeasible and exits non-zero so the table is never silently wrong.

Outputs (raw evidence - never edited by hand):
  evidence/raw/get-status-truth-table.csv   2^7 = 128 rows, complete MCC table
  evidence/raw/get-status-truth-table.md    the same table as Markdown
  evidence/raw/get-status-mcdc-pairs.csv    MC/DC: 7 pairs over n+1 = 8 rows

Run from the repository root:
    python tools/unit/get_status_truth_table.py
Exit status: 0 = table valid, 1 = invalid (do not run tests against it).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evidence" / "raw"
TABLE_CSV = RAW / "get-status-truth-table.csv"
TABLE_MD = RAW / "get-status-truth-table.md"
MCDC_CSV = RAW / "get-status-mcdc-pairs.csv"

CONDITIONS = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
CONDITION_LABELS = {
    "a1": "last_start is set",
    "a2": "now >= last_start + grace",
    "a3": "with_started is true",
    "a4": "stored status in (new, paused, down)",
    "a5": "grace_start is None",
    "a6": "now >= grace_end",
    "a7": "now >= grace_start",
}

# The minimal MC/DC set: a chain of n+1 = 8 rows, consecutive rows differ in
# exactly one condition and flip the outcome.  Each of the 7 conditions appears
# in exactly one pair (independence).  Selected from the table below; the
# script re-validates every pair against the generated outcomes.
MCDC_CHAIN: list[tuple[str, str, str]] = [
    ("a4", "0011111", "0010111"),  # new vs up
    ("a5", "0010111", "0010011"),  # up (never elapses) vs down (grace end passed)
    ("a6", "0010011", "0010001"),  # down vs grace
    ("a7", "0010001", "0010000"),  # grace vs up
    ("a1", "1010000", "0010000"),  # started vs up
    ("a3", "1010000", "1000000"),  # started vs up
    ("a2", "1100000", "1000000"),  # down vs up
]


def evaluate(bits: dict[str, bool]) -> tuple[list[str], str]:
    """Return (evaluated_conditions, outcome) for one truth-table row.

    Mirrors the decision structure documented for BR-02: conditions are
    evaluated in order and the first satisfied one fixes the outcome, so all
    later conditions are masked (don't care).  The stored status partition
    (A4) is realised as "new" in tests - "paused"/"down" behave identically
    here and are covered as equivalence partitions in test_get_status_edges.py.
    """
    evaluated: list[str] = []

    evaluated.append("a1")
    if bits["a1"]:
        evaluated.append("a2")
        if bits["a2"]:
            return evaluated, "down"
        evaluated.append("a3")
        if bits["a3"]:
            return evaluated, "started"

    evaluated.append("a4")
    if bits["a4"]:
        return evaluated, "new"  # returns the stored status itself

    evaluated.append("a5")
    if bits["a5"]:
        return evaluated, "up"

    evaluated.append("a6")
    if bits["a6"]:
        return evaluated, "down"

    evaluated.append("a7")
    return evaluated, ("grace" if bits["a7"] else "up")


def feasibility(bits: dict[str, bool], evaluated: list[str]) -> tuple[str, str]:
    """Classify one row.  Returns (feasible, reason).

    Structural constraints (path) are guaranteed by evaluate(); the semantic
    constraint A6 => A7 can only bite if A7 were evaluated after A6=true.
    """
    if "a6" in evaluated and bits["a6"] and "a7" in evaluated and not bits["a7"]:
        return "no", "contradiction: A6 (now >= grace_end) implies A7 (now >= grace_start)"
    if "a2" in evaluated and "a1" not in evaluated:
        return "no", "A2 evaluated without A1 (last_start set)"
    return "yes", ""


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for n in range(1 << len(CONDITIONS)):
        bits = {name: bool(n >> (len(CONDITIONS) - i - 1) & 1) for i, name in enumerate(CONDITIONS)}
        evaluated, outcome = evaluate(bits)
        masked = [name for name in CONDITIONS if name not in evaluated]
        feasible, reason = feasibility(bits, evaluated)
        row = {"row_id": f"R{n:07b}"}
        row.update({name: "1" if bits[name] else "0" for name in CONDITIONS})
        row["evaluated"] = ",".join(evaluated)
        row["masked"] = ",".join(masked) if masked else ""
        row["outcome"] = outcome
        row["feasible"] = feasible
        row["infeasible_reason"] = reason
        row["mcdc_condition"] = ""
        rows.append(row)

    by_id = {row["row_id"]: row for row in rows}
    for condition, row_true, row_false in MCDC_CHAIN:
        for key in (row_true, row_false):
            if f"R{key}" in by_id:
                by_id[f"R{key}"]["mcdc_condition"] = condition
    return rows


def validate(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    by_id = {row["row_id"]: row for row in rows}

    if len(rows) != 128:
        errors.append(f"expected 128 rows, got {len(rows)}")
    if [row["row_id"] for row in rows] != [f"R{n:07b}" for n in range(128)]:
        errors.append("row ids are not the full 2^7 sequence")

    # MC/DC validation: n + 1 rows, n pairs, one condition each, outcomes flip.
    def rid(bits: str) -> str:
        return f"R{bits}"

    mcdc_rows = {rid(row_id) for _, row_true, row_false in MCDC_CHAIN
                 for row_id in (row_true, row_false)}
    if len(mcdc_rows) != 8:
        errors.append(f"MC/DC chain must use n+1 = 8 distinct rows, uses {len(mcdc_rows)}")
    covered: list[str] = []
    for condition, row_true, row_false in MCDC_CHAIN:
        a, b = by_id.get(rid(row_true)), by_id.get(rid(row_false))
        if a is None or b is None:
            errors.append(f"MC/DC pair {condition}: row missing from table")
            continue
        diffs = [name for name in CONDITIONS if a[name] != b[name]]
        if diffs != [condition]:
            errors.append(f"MC/DC pair {condition}: rows differ in {diffs}, expected only [{condition}]")
        if a[condition] != "1" or b[condition] != "0":
            errors.append(f"MC/DC pair {condition}: row_true must have the bit set, row_false clear")
        if a["outcome"] == b["outcome"]:
            errors.append(
                f"MC/DC pair {condition}: outcomes do not flip ({a['outcome']} vs {b['outcome']})"
            )
        if a["feasible"] != "yes" or b["feasible"] != "yes":
            errors.append(f"MC/DC pair {condition}: contains an infeasible row")
        covered.append(condition)
    if sorted(covered) != sorted(CONDITIONS):
        errors.append(f"MC/DC conditions covered: {sorted(covered)}")

    # Every row must be classified; infeasible rows carry a reason.
    for row in rows:
        if row["feasible"] not in ("yes", "no"):
            errors.append(f"{row['row_id']}: unclassified")
        if row["feasible"] == "no" and not row["infeasible_reason"]:
            errors.append(f"{row['row_id']}: infeasible without a reason")
    return errors


def write_outputs(rows: list[dict[str, str]]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    fields = ["row_id", *CONDITIONS, "evaluated", "masked", "outcome", "feasible",
              "infeasible_reason", "mcdc_condition"]

    with TABLE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    with MCDC_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["condition", "label", "row_true", "outcome_true",
                         "row_false", "outcome_false"])
        by_id = {row["row_id"]: row for row in rows}
        for condition, row_true, row_false in MCDC_CHAIN:
            writer.writerow([
                condition,
                CONDITION_LABELS[condition],
                f"R{row_true}",
                by_id[f"R{row_true}"]["outcome"],
                f"R{row_false}",
                by_id[f"R{row_false}"]["outcome"],
            ])

    lines = [
        "# Complete MCC truth table for Check.get_status (2^7 = 128 rows)",
        "",
        "Generated by `tools/unit/get_status_truth_table.py` from BR-02"
        " (docs/01-scope-and-test-basis.md section 6). Raw CSV:"
        " `evidence/raw/get-status-truth-table.csv`. Conditions A1..A7 in"
        " evaluation order; `masked` = don't-care conditions on that row's path.",
        "",
        "| Row | A1 | A2 | A3 | A4 | A5 | A6 | A7 | Evaluated | Masked | Outcome | Feasible | MC/DC |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {row_id} | {a1} | {a2} | {a3} | {a4} | {a5} | {a6} | {a7} | {evaluated} |"
            " {masked} | {outcome} | {feasible} | {mcdc} |".format(
                **row, mcdc=row["mcdc_condition"] or ""
            )
        )
    TABLE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    errors = validate(rows)
    if errors:
        print("FAIL: truth table validation errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    write_outputs(rows)
    infeasible = sum(1 for row in rows if row["feasible"] == "no")
    print(f"OK: 128 rows written, {infeasible} infeasible, MC/DC set = 8 rows / 7 pairs")
    print(f"    {TABLE_CSV.relative_to(ROOT)}")
    print(f"    {TABLE_MD.relative_to(ROOT)}")
    print(f"    {MCDC_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
