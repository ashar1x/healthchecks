"""Build a Pareto chart from the exported GitHub Issues list.

Input: evidence/raw/issues.json (one JSON object per line, from `gh api`).
Output: evidence/raw/pareto.json and evidence/raw/pareto.svg.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISSUES = ROOT / "evidence" / "raw" / "issues.json"
OUT_JSON = ROOT / "evidence" / "raw" / "pareto.json"
OUT_SVG = ROOT / "evidence" / "raw" / "pareto.svg"


@dataclass(frozen=True, slots=True)
class Slice:
    category: str
    count: int
    percent: float
    cumulative: float


def read_issues() -> list[dict]:
    issues = [json.loads(line) for line in ISSUES.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [issue for issue in issues if "pull_request" not in issue]


def build_slices(issues: list[dict]) -> list[Slice]:
    counts: dict[str, int] = {}
    for issue in issues:
        labels = [label.removeprefix("category:") for label in issue.get("labels", []) if label.startswith("category:")]
        category = labels[0] if labels else "uncategorised"
        counts[category] = counts.get(category, 0) + 1
    total = sum(counts.values())
    slices: list[Slice] = []
    running = 0
    for category, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        running += count
        slices.append(Slice(category, count, round(100 * count / total, 1), round(100 * running / total, 1)))
    return slices


def render_svg(slices: list[Slice]) -> str:
    width, height, left, top, row = 680, 300, 150, 40, 42
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">', '<rect width="100%" height="100%" fill="white"/>', '<text x="20" y="25" font-size="16">Defects by category (Pareto)</text>']
    for index, item in enumerate(slices):
        y = top + index * row
        bar = item.count * 90
        parts.append(f'<text x="20" y="{y + 15}" font-size="12">{item.category}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar}" height="22" fill="#4472c4"/>')
        parts.append(f'<text x="{left + bar + 8}" y="{y + 16}" font-size="12">{item.count} ({item.percent}%, cum {item.cumulative}%)</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    slices = build_slices(read_issues())
    OUT_JSON.write_text(json.dumps({"source": "evidence/raw/issues.json", "slices": [asdict(s) for s in slices]}, indent=2) + "\n", encoding="utf-8")
    OUT_SVG.write_text(render_svg(slices) + "\n", encoding="utf-8")
    for item in slices:
        print(f"{item.category}: {item.count} ({item.percent}%, cumulative {item.cumulative}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
