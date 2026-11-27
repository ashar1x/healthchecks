"""Fail if a GitHub Actions workflow contains a banned escape hatch.

Patterns are built from parts so this script does not match its own source.
Run from the repository root: python tools/evidence/check_workflows.py
"""
from __future__ import annotations

from pathlib import Path

WORKFLOWS = Path(".github/workflows")
BANNED = [
    "continue-on-" + "error",
    "|" + "| " + "true",
    "--exit-" + "zero",
    "allow_" + "failure",
]


def main() -> int:
    offenders: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(pattern in line for pattern in BANNED):
                offenders.append(f"{path}:{number}: {line.strip()}")
    if offenders:
        print("Banned escape-hatch patterns found:")
        for offender in offenders:
            print(offender)
        return 1
    print("No banned escape-hatch patterns found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
