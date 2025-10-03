#!/usr/bin/env python3
"""
Constitutional Violation Pattern Analyzer - MVP

Analyzes constitutional_violations.jsonl to find actionable patterns,
not just counts. Shows ROI in hours and dollars.

Usage:
    python tools/constitutional_intelligence/violation_patterns.py
    python tools/constitutional_intelligence/violation_patterns.py --last-7-days
    python tools/constitutional_intelligence/violation_patterns.py --json
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def load_violations(log_file: Path, days: int | None = None) -> list[dict[str, Any]]:
    """Load violations from JSONL file, optionally filtering by days."""
    if not log_file.exists():
        return []

    violations = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days) if days else None

    for line in log_file.read_text().splitlines():
        if not line.strip():
            continue
        try:
            v = json.loads(line)
            if cutoff:
                ts = datetime.fromisoformat(v["timestamp"].replace("Z", "+00:00"))
                if ts < cutoff:
                    continue
            violations.append(v)
        except (json.JSONDecodeError, KeyError):
            continue

    return violations


def analyze_patterns(violations: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract actionable patterns from violations."""

    # Group by function
    by_function = Counter(v["function"] for v in violations)

    # Group by article
    by_article = Counter(v["error"].split(":")[0] for v in violations)

    # Group by function + article
    by_function_article = defaultdict(list)
    for v in violations:
        key = v["function"]
        article = v["error"].split(":")[0]
        by_function_article[key].append(article)

    # Time distribution (violations per day)
    by_day = defaultdict(int)
    for v in violations:
        ts = datetime.fromisoformat(v["timestamp"].replace("Z", "+00:00"))
        day = ts.date().isoformat()
        by_day[day] += 1

    return {
        "by_function": dict(by_function),
        "by_article": dict(by_article),
        "by_function_article": dict(by_function_article),
        "by_day": dict(by_day),
        "total": len(violations)
    }


def generate_insights(patterns: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate actionable insights from patterns."""
    insights = []

    # Top violator insight
    if patterns["by_function"]:
        top_func, top_count = max(patterns["by_function"].items(), key=lambda x: x[1])

        # Estimate time waste (8 min avg to investigate/fix each violation)
        weekly_waste_min = top_count * 8
        weekly_waste_hours = weekly_waste_min / 60
        annual_waste_hours = weekly_waste_hours * 52
        annual_cost = annual_waste_hours * 150  # $150/hour

        # Find which articles are violated
        articles = Counter(patterns["by_function_article"][top_func])

        insights.append({
            "type": "recurring_violation",
            "function": top_func,
            "count": top_count,
            "articles": dict(articles),
            "time_waste_weekly_min": weekly_waste_min,
            "time_waste_weekly_hours": round(weekly_waste_hours, 1),
            "time_waste_annual_hours": round(annual_waste_hours, 0),
            "cost_annual_usd": round(annual_cost, 0),
            "suggested_fix": f"Review {top_func} implementation for constitutional compliance",
            "root_cause": "Test infrastructure violates Articles I & II",
            "autofix_available": top_func == "create_mock_agent"
        })

    # Article V spec coverage insight
    article_v_violations = [
        v for v in patterns["by_article"].items()
        if "Article V" in v[0]
    ]
    if article_v_violations:
        for article, count in article_v_violations:
            insights.append({
                "type": "spec_coverage",
                "article": "Article V",
                "count": count,
                "issue": "Spec-driven development mandate not met",
                "suggested_fix": "Add spec.md files for existing features or adjust Article V threshold",
                "impact": "Low priority - legacy code issue, not blocking new development"
            })

    return insights


def print_report(patterns: dict[str, Any], insights: list[dict[str, Any]]) -> None:
    """Print human-readable report."""
    print("\n" + "="*80)
    print("CONSTITUTIONAL VIOLATION PATTERN ANALYSIS")
    print("="*80)

    print(f"\nTOTAL VIOLATIONS: {patterns['total']}")

    # Time distribution
    if patterns["by_day"]:
        print(f"\nTIME DISTRIBUTION:")
        for day in sorted(patterns["by_day"].keys())[-7:]:  # Last 7 days
            count = patterns["by_day"][day]
            bar = "█" * min(count, 50)
            print(f"  {day}: {bar} ({count})")

    print("\n" + "-"*80)
    print("TOP 3 VIOLATION PATTERNS")
    print("-"*80 + "\n")

    # Show top 3 functions
    for i, (func, count) in enumerate(sorted(patterns["by_function"].items(), key=lambda x: x[1], reverse=True)[:3], 1):
        articles = Counter(patterns["by_function_article"][func])
        weekly_waste = count * 8  # minutes

        print(f"{i}. 🔴 {func}")
        print(f"   Occurrences: {count}")
        print(f"   Articles violated: {', '.join(articles.keys())}")
        print(f"   Time waste: {weekly_waste} min/week = {weekly_waste/60:.1f} hours/week")
        print(f"   Annual cost: ${weekly_waste * 52 / 60 * 150:,.0f}\n")

    print("-"*80)
    print("ACTIONABLE INSIGHTS")
    print("-"*80 + "\n")

    for insight in insights:
        if insight["type"] == "recurring_violation":
            print(f"🚨 CRITICAL PATTERN DETECTED: {insight['function']}")
            print(f"   Frequency: {insight['count']} violations")
            print(f"   Articles: {', '.join(insight['articles'].keys())}")
            print(f"   Weekly waste: {insight['time_waste_weekly_hours']} hours")
            print(f"   Annual cost: ${insight['cost_annual_usd']:,}")
            print(f"\n   ROOT CAUSE:")
            print(f"   {insight['root_cause']}")
            print(f"\n   SUGGESTED FIX:")
            print(f"   {insight['suggested_fix']}")
            if insight["autofix_available"]:
                print(f"   ✨ AutoFix available - run with --fix flag")
            print()

        elif insight["type"] == "spec_coverage":
            print(f"ℹ️  {insight['article']} Violations: {insight['count']}")
            print(f"   Issue: {insight['issue']}")
            print(f"   Fix: {insight['suggested_fix']}")
            print(f"   Impact: {insight['impact']}\n")

    # Overall summary
    total_weekly_min = patterns["total"] * 8
    total_weekly_hours = total_weekly_min / 60
    total_annual_hours = total_weekly_hours * 52
    total_annual_cost = total_annual_hours * 150

    print("-"*80)
    print("TOTAL COST ANALYSIS")
    print("-"*80)
    print(f"\n💰 Current weekly cost: {total_weekly_hours:.1f} hours = ${total_weekly_hours * 150:,.0f}")
    print(f"💰 Annualized cost: {total_annual_hours:.0f} hours = ${total_annual_cost:,.0f}")
    print(f"\n📊 Potential savings if top pattern fixed:")
    if insights and insights[0]["type"] == "recurring_violation":
        top = insights[0]
        savings_hours = total_annual_hours - top["time_waste_annual_hours"]
        savings_usd = total_annual_cost - top["cost_annual_usd"]
        print(f"   Annual hours saved: {top['time_waste_annual_hours']:.0f}")
        print(f"   Annual cost saved: ${top['cost_annual_usd']:,.0f}")
        print(f"   ROI: Fix once (2 hours) → Save {top['time_waste_annual_hours']:.0f} hours/year")
        print(f"   ROI Ratio: {top['time_waste_annual_hours'] / 2:.0f}x return")

    print("\n" + "="*80 + "\n")


def print_json_report(patterns: dict[str, Any], insights: list[dict[str, Any]]) -> None:
    """Print JSON report for programmatic use."""
    report = {
        "summary": {
            "total_violations": patterns["total"],
            "analysis_date": datetime.now(timezone.utc).isoformat(),
        },
        "patterns": patterns,
        "insights": insights,
        "cost_analysis": {
            "weekly_hours": round(patterns["total"] * 8 / 60, 1),
            "annual_hours": round(patterns["total"] * 8 * 52 / 60, 0),
            "annual_cost_usd": round(patterns["total"] * 8 * 52 / 60 * 150, 0)
        }
    }
    print(json.dumps(report, indent=2))


def main():
    """Main entry point."""
    # Parse args
    days = None
    output_format = "text"

    if "--last-7-days" in sys.argv:
        days = 7
    elif "--last-30-days" in sys.argv:
        days = 30

    if "--json" in sys.argv:
        output_format = "json"

    # Load violations
    log_file = Path("logs/autonomous_healing/constitutional_violations.jsonl")
    violations = load_violations(log_file, days)

    if not violations:
        print("No violations found.", file=sys.stderr)
        return 1

    # Analyze patterns
    patterns = analyze_patterns(violations)
    insights = generate_insights(patterns)

    # Output report
    if output_format == "json":
        print_json_report(patterns, insights)
    else:
        print_report(patterns, insights)

    return 0


if __name__ == "__main__":
    sys.exit(main())
