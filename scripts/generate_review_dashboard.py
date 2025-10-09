#!/usr/bin/env python3
"""
Human Review Dashboard Generator for Autonomous Fix Recommendations

Generates a markdown dashboard for reviewing 488 audit recommendations.

Usage:
    python scripts/generate_review_dashboard.py
    python scripts/generate_review_dashboard.py --category pruning
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.agent_context import create_agent_context


def parse_rec(path: Path) -> dict | None:
    """Parse recommendation file."""
    try:
        c = path.read_text()
        p, cat, e, s = (
            re.search(r"\*\*Priority\*\*:\s*(\w+)", c),
            re.search(r"\*\*Category\*\*:\s*(\w+)", c),
            re.search(r"\*\*Effort\*\*:\s*([\d.]+)", c),
            re.search(r"\*\*Status\*\*:\s*(\w+)", c),
        )
        if not all([p, cat, e, s]):
            return None
        return {
            "id": path.stem,
            "priority": p.group(1),
            "category": cat.group(1),
            "summary": (
                m.group(1).strip()[:50] + "..."
                if (m := re.search(r"## Summary\n(.+?)(?:\n\n|\n##)", c, re.DOTALL))
                else "No summary"
            ),
            "files_count": len(re.findall(r"-\s*`([^`]+?)`", c)),
            "effort": float(e.group(1)),
            "status": s.group(1),
        }
    except Exception:
        return None


def load_state(f: Path) -> dict:
    """Load fixer state."""
    if not f.exists():
        return {"processed": 0, "applied": 0, "failed": 0, "skipped": 0, "results": []}
    try:
        return json.loads(f.read_text())
    except Exception:
        return {"processed": 0, "applied": 0, "failed": 0, "skipped": 0, "results": []}


def calc_stats(recs: list[dict], state: dict) -> dict:
    """Calculate stats."""
    stats = {"total": len(recs), "p0": 0, "p1": 0, "p2": 0, "p3": 0, "by_cat": {}}
    for r in recs:
        stats[f"p{r['priority'][1]}"] += 1
        stats["by_cat"][r["category"]] = stats["by_cat"].get(r["category"], 0) + 1
    total = state.get("applied", 0) + state.get("failed", 0)
    stats["success_rate"] = (state.get("applied", 0) / total * 100) if total > 0 else 0.0
    return stats


def query_conf(ctx, recs: list[dict]) -> dict[str, float]:
    """Query confidence scores."""
    conf = {}
    for r in recs:
        pats = ctx.search_memories(
            tags=["pattern", "fix", r["category"].lower()], include_session=False
        )
        conf[r["id"]] = (
            min(sum(p.get("confidence", 0.7) for p in pats) / len(pats) + 0.1, 1.0)
            if pats
            else {"P3": 0.9, "P2": 0.7, "P1": 0.6, "P0": 0.4}.get(r["priority"], 0.7)
        )
    return conf


def gen_dash(recs: list[dict], stats: dict, state: dict, conf: dict, out: Path) -> None:
    """Generate dashboard."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Autonomous Fix Recommendations - Human Review Dashboard\n",
        f"**Generated**: {now}",
        f"**Total**: {stats['total']}",
        f"**Session**: {state.get('session_id', 'N/A')}\n",
        "---\n",
        "## 1. Summary Statistics\n",
        "### Status Breakdown\n",
        f"- **Pending**: {stats['total'] - state.get('processed', 0)}",
        f"- **Applied**: {state.get('applied', 0)}",
        f"- **Failed**: {state.get('failed', 0)}",
        f"- **Skipped**: {state.get('skipped', 0)}\n",
        "### Priority Breakdown\n",
        f"- **P3** (Low): {stats['p3']}",
        f"- **P2** (Medium): {stats['p2']}",
        f"- **P1** (High): {stats['p1']}",
        f"- **P0** (Critical): {stats['p0']}\n",
        "### Category Breakdown\n",
    ]
    lines.extend([f"- **{cat.title()}**: {cnt}" for cat, cnt in sorted(stats["by_cat"].items())])
    lines.extend(
        [
            "\n### Success Metrics\n",
            f"- **Success Rate**: {stats['success_rate']:.1f}%",
            f"- **Processed**: {state.get('processed', 0)} / {stats['total']}\n",
            "---\n",
            "## 2. Quick Actions\n",
            "```bash",
            "# Approve all P3 (safest)",
            "python scripts/autonomous_recommendation_fixer.py --priority P3 --batch-all\n",
            "# Review P1",
            "python scripts/autonomous_recommendation_fixer.py --priority P1 --dry-run\n",
            "# Process category",
            "python scripts/autonomous_recommendation_fixer.py --category pruning --limit 50",
            "```\n",
            "---\n",
            "## 3. Recommendation Table\n",
            "| ID | Priority | Category | Summary | Files | Effort (h) | Confidence |",
            "|:---|:---------|:---------|:--------|------:|-----------:|:-----------|",
        ]
    )
    sorted_recs = sorted(
        recs,
        key=lambda r: (
            {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(r["priority"], 4),
            -conf.get(r["id"], 0.7),
        ),
    )
    for rec in sorted_recs[:100]:
        c = conf.get(rec["id"], 0.7)
        c_d = f"🟢 {c:.2f}" if c > 0.8 else f"🟡 {c:.2f}" if c > 0.6 else f"🔴 {c:.2f}"
        lines.append(
            f"| {rec['id'][:30]} | {rec['priority']} | {rec['category']} | {rec['summary'][:35]} | {rec['files_count']} | {rec['effort']:.1f} | {c_d} |"
        )
    if len(sorted_recs) > 100:
        lines.append(f"\n*Showing 100 of {len(sorted_recs)} total*")
    lines.extend(
        [
            "\n**Legend**: 🟢 High (>0.8) | 🟡 Medium (0.6-0.8) | 🔴 Low (<0.6)\n",
            "---\n",
            "## 4. Recent Activity\n",
        ]
    )
    results = state.get("results", [])
    if results:
        lines.extend(
            [
                "| Time | Category | Status | Files | Tests | Commit |",
                "|:-----|:---------|:-------|------:|:------|:-------|",
            ]
        )
        for res in results[-20:]:
            rd = res.get("recommendation", {})
            emoji = {"applied": "✅", "failed": "❌", "skipped": "⏭️"}.get(
                res.get("status", "").lower(), "❓"
            )
            commit = res.get("commit_sha", "N/A")[:8] if res.get("commit_sha") else "N/A"
            lines.append(
                f"| {now[11:16]} | {rd.get('category', 'N/A')} | {emoji} {res.get('status', 'N/A')} | {len(res.get('files_modified', []))} | {'✅' if res.get('tests_passed') else '❌'} | {commit} |"
            )
    else:
        lines.append("*No activity*")
    lines.extend(
        [
            "\n---\n",
            "## 5. Quality Metrics\n",
            f"- **Low Risk (P3)**: {stats['p3']} - Auto-apply recommended",
            f"- **Medium Risk (P2)**: {stats['p2']} - Review + auto-apply",
            f"- **High Risk (P1)**: {stats['p1']} - Manual review required\n",
            "---\n",
            f"*Generated at {now}*",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate review dashboard")
    parser.add_argument(
        "--recommendations-dir", type=Path, default=Path(".output/audit_recommendations")
    )
    parser.add_argument("--state-file", type=Path, default=Path(".fixer_state.json"))
    parser.add_argument(
        "--output", type=Path, default=Path(".output/autonomous_fixes/review_dashboard.md")
    )
    parser.add_argument("--category", type=str)
    args = parser.parse_args()

    print(
        f"Generating dashboard...\n  Recommendations: {args.recommendations_dir}\n  Output: {args.output}"
    )
    state = load_state(args.state_file)
    recs = [
        rec
        for f in sorted(args.recommendations_dir.glob("*.md"))
        if (rec := parse_rec(f))
        and (not args.category or rec["category"].lower() == args.category.lower())
    ]
    if not recs:
        print("ERROR: No valid recommendations")
        return 1
    print(f"  Parsed: {len(recs)} recommendations")
    ctx = create_agent_context(session_id="dashboard_gen")
    conf = query_conf(ctx, recs)
    stats = calc_stats(recs, state)
    gen_dash(recs, stats, state, conf, args.output)
    print(
        f"\n✅ Dashboard: {args.output}\n  Total: {stats['total']}, Pending: {stats['total'] - state.get('processed', 0)}, Success: {stats['success_rate']:.1f}%"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
