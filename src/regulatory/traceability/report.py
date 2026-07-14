"""Generate regulatory coverage evidence and enforce the release gate."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    source_id: str
    topic: str
    applicability: str
    implementation_status: str
    code: str
    test: str
    evidence: str


def load_requirements(path: Path) -> tuple[Requirement, ...]:
    with path.open(encoding="utf-8", newline="") as source:
        return tuple(
            Requirement(**{field: row[field] for field in Requirement.__annotations__})
            for row in csv.DictReader(source)
        )


def release_blockers(requirements: tuple[Requirement, ...]) -> tuple[Requirement, ...]:
    return tuple(
        item
        for item in requirements
        if item.applicability != "not_applicable"
        and (
            item.implementation_status != "implemented"
            or not item.code
            or not item.test
            or not item.evidence
            or any(not Path(test.strip()).exists() for test in item.test.split(";"))
        )
    )


def render_report(requirements: tuple[Requirement, ...]) -> str:
    statuses = Counter(item.implementation_status for item in requirements)
    applicability = Counter(item.applicability for item in requirements)
    blockers = release_blockers(requirements)
    lines = [
        "# Regulatory coverage report",
        "",
        f"- Requirements: {len(requirements)}",
        f"- Implemented: {statuses['implemented']}",
        f"- Partial: {statuses['partial']}",
        f"- Planned: {statuses['planned']}",
        f"- Not applicable: {applicability['not_applicable']}",
        f"- Release blockers: {len(blockers)}",
        "",
        "## Release blockers",
        "",
    ]
    lines.extend(
        f"- `{item.requirement_id}` — {item.topic}: {item.implementation_status}"
        for item in blockers
    )
    if not blockers:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Requirement status",
            "",
            "| ID | Source | Topic | Applicability | Status |",
            "|---|---|---|---|---|",
        ]
    )
    lines.extend(
        f"| `{item.requirement_id}` | `{item.source_id}` | {item.topic} | "
        f"{item.applicability} | {item.implementation_status} |"
        for item in requirements
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matrix", type=Path, default=Path("docs/regulatory/TRACEABILITY_MATRIX.csv")
    )
    parser.add_argument("--output", type=Path, default=Path("build/regulatory-coverage.md"))
    parser.add_argument("--enforce", action="store_true")
    args = parser.parse_args(argv)
    requirements = load_requirements(args.matrix)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(requirements), encoding="utf-8")
    blockers = release_blockers(requirements)
    print(f"regulatory report: {args.output} ({len(blockers)} blocker(s))")
    return 1 if args.enforce and blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
