#!/usr/bin/env python3
"""
Format Trinity audit results as a GitHub PR comment.

Constitutional Compliance:
- Article I: Complete Context (reads full audit state)
- Article II: 100% Verification (validates JSON)
- Article V: Spec-Driven Development (follows format spec)

Usage:
    python scripts/format_pr_comment.py
    python scripts/format_pr_comment.py --input .audit_state.json
"""

import argparse
import json
import sys
from typing import Literal

from pydantic import BaseModel, Field


class AuditState(BaseModel):
    """Audit state from .audit_state.json."""

    start_time: str
    last_scan_time: str
    scanned_files: list[str]
    recommendations_count: int
    next_recommendation_number: int
    status: Literal["running", "stopped", "completed"]
    findings_summary: dict[str, int] = Field(default_factory=dict)


class PriorityGroup(BaseModel):
    """Group of issues by priority."""

    priority: str
    count: int
    total_effort_hours: float
    issues: list[str] = Field(default_factory=list)


EFFORT_BY_CATEGORY = {
    "architecture": 4.0,
    "simplification": 3.0,
    "consolidation": 2.0,
    "pruning": 1.0,
    "linting": 0.5,
}

CATEGORY_TO_PRIORITY = {
    "architecture": "P0",
    "simplification": "P1",
    "consolidation": "P2",
    "pruning": "P3",
    "linting": "P3",
}


def group_by_priority(findings: dict[str, int]) -> list[PriorityGroup]:
    """Group findings by priority with effort estimates."""
    groups: dict[str, PriorityGroup] = {
        p: PriorityGroup(priority=p, count=0, total_effort_hours=0.0) for p in ["P0", "P1", "P2", "P3"]
    }

    for category, count in findings.items():
        if count == 0:
            continue

        priority = CATEGORY_TO_PRIORITY.get(category, "P3")
        effort = EFFORT_BY_CATEGORY.get(category, 1.0) * count

        groups[priority].count += count
        groups[priority].total_effort_hours += effort
        groups[priority].issues.append(f"{count} {category}")

    return [g for g in groups.values() if g.count > 0]


PRIORITY_LABELS = {
    "P0": "Critical Priority (P0)",
    "P1": "High Priority (P1)",
    "P2": "Medium Priority (P2)",
    "P3": "Low Priority (P3)",
}


def format_pr_comment(state: AuditState) -> str:
    """Format audit state as GitHub PR comment markdown."""
    groups = group_by_priority(state.findings_summary)
    lines = [
        "## 🤖 Trinity Code Quality Report\n",
        f"**Found {state.recommendations_count} improvements** for this PR\n",
    ]

    # Priority sections
    for group in groups:
        lines.append(f"### {PRIORITY_LABELS[group.priority]} - {group.count} issues")
        lines.extend(f"- {issue}" for issue in group.issues)

        hours = group.total_effort_hours
        effort = f"~{int(hours * 60)} minutes" if hours < 1 else f"~{hours:.1f} hours"
        lines.append(f"- **Estimated effort**: {effort}\n")

    # Auto-fix guidance
    lines.append("### 🎯 Auto-Fix Available\n")
    groups_map = {g.priority: g for g in groups}

    if p3 := groups_map.get("P3"):
        lines.append(f"- [ ] Fix all P3 (safest, {p3.count} fixes in ~{int(p3.total_effort_hours * 60)} minutes)")
    if p2 := groups_map.get("P2"):
        lines.append(f"- [ ] Fix P2 (medium risk, {p2.count} fixes)")
    if p1 := groups_map.get("P1"):
        lines.append(f"- [ ] Manual review P1 (requires judgment, {p1.count} issues)")

    lines.append("\n💡 **Powered by Trinity AI** - [Learn more](https://github.com/subtract0/Agency)")
    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Format Trinity audit results as GitHub PR comment")
    parser.add_argument(
        "--input",
        default=".output/audit_recommendations/.audit_state.json",
        help="Audit state JSON file (default: .output/audit_recommendations/.audit_state.json)",
    )
    parser.add_argument("--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    try:
        with open(args.input) as f:
            state = AuditState(**json.load(f))

        comment = format_pr_comment(state)

        if args.output:
            with open(args.output, "w") as f:
                f.write(comment)
            print(f"✓ PR comment written to {args.output}")
        else:
            print(comment)

    except FileNotFoundError:
        print(f"✗ Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
