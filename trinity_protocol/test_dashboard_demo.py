#!/usr/bin/env python3
"""
Demo script to test cost dashboard with simulated data.

Creates realistic cost tracking data and demonstrates all dashboard features:
- Terminal dashboard
- Web dashboard
- Cost alerts
- Export functionality

Usage:
    # Generate test data and show snapshot
    python trinity_protocol/test_dashboard_demo.py

    # Generate test data and run live terminal dashboard
    python trinity_protocol/test_dashboard_demo.py --terminal

    # Generate test data and run web dashboard
    python trinity_protocol/test_dashboard_demo.py --web

    # Test alerts
    python trinity_protocol/test_dashboard_demo.py --alerts
"""

import argparse
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.cost_tracker import CostTracker, ModelTier
from trinity_protocol.cost_dashboard import CostDashboard
from trinity_protocol.cost_alerts import CostAlertSystem, AlertConfig


def generate_test_data(tracker: CostTracker, num_calls: int = 50) -> None:
    """
    Generate realistic test cost data.

    Args:
        tracker: CostTracker to populate
        num_calls: Number of API calls to simulate
    """
    print(f"\n📊 Generating {num_calls} test API calls...")

    agents = [
        "WITNESS",
        "ARCHITECT",
        "EXECUTOR",
        "AgencyCodeAgent",
        "TestGeneratorAgent",
        "ToolsmithAgent",
        "QualityEnforcerAgent",
        "MergerAgent",
        "WorkCompletionSummaryAgent"
    ]

    models = [
        ("gpt-5", ModelTier.CLOUD_PREMIUM),
        ("gpt-5-mini", ModelTier.CLOUD_MINI),
        ("claude-sonnet-4.5", ModelTier.CLOUD_PREMIUM),
        ("claude-haiku-3.5", ModelTier.CLOUD_MINI),
    ]

    tasks = [
        "task-implement-feature",
        "task-write-tests",
        "task-create-tool",
        "task-quality-check",
        "task-merge-pr",
        "task-summarize"
    ]

    now = datetime.now()

    # Generate calls with temporal distribution
    for i in range(num_calls):
        # Simulate calls over the last 24 hours
        hours_ago = random.uniform(0, 24)
        call_time = now - timedelta(hours=hours_ago)

        agent = random.choice(agents)
        model, tier = random.choice(models)
        task_id = random.choice(tasks)

        # Simulate realistic token counts
        if tier == ModelTier.CLOUD_PREMIUM:
            input_tokens = random.randint(500, 3000)
            output_tokens = random.randint(200, 1500)
        else:
            input_tokens = random.randint(200, 1000)
            output_tokens = random.randint(100, 500)

        duration = random.uniform(1.0, 5.0)
        success = random.random() > 0.05  # 95% success rate

        # Track call (need to temporarily override timestamp)
        call = tracker.track_call(
            agent=agent,
            model=model,
            model_tier=tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=duration,
            success=success,
            task_id=task_id,
            correlation_id=f"corr-{i}"
        )

        # Update timestamp in database to simulate historical data
        if tracker.db_path != ":memory:":
            import sqlite3
            conn = sqlite3.connect(str(tracker.db_path))
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE llm_calls SET timestamp = ? WHERE id = (SELECT MAX(id) FROM llm_calls)",
                (call_time.isoformat(),)
            )
            conn.commit()
            conn.close()

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_calls} calls...")

    summary = tracker.get_summary()
    print(f"\n✅ Generated {summary.total_calls} API calls")
    print(f"   Total cost: ${summary.total_cost_usd:.4f}")
    print(f"   Success rate: {summary.success_rate * 100:.1f}%")
    print(f"   Agents: {len(summary.by_agent)}")
    print()


def demo_terminal_dashboard(tracker: CostTracker) -> None:
    """Demo terminal dashboard."""
    print("\n🖥️  Starting Terminal Dashboard...")
    print("   Press Q to quit, E to export, R to refresh")
    print()
    time.sleep(2)

    dashboard = CostDashboard(cost_tracker=tracker, refresh_interval=5)
    dashboard.run_terminal_dashboard()


def demo_web_dashboard(tracker: CostTracker) -> None:
    """Demo web dashboard."""
    try:
        from trinity_protocol.cost_dashboard_web import CostDashboardWeb
    except ImportError:
        print("\n❌ Flask not installed. Install with: pip install flask")
        return

    print("\n🌐 Starting Web Dashboard...")
    print("   Open http://localhost:8080 in your browser")
    print("   Press Ctrl+C to stop")
    print()

    dashboard = CostDashboardWeb(cost_tracker=tracker, refresh_interval=5)
    dashboard.run(host='0.0.0.0', port=8080, debug=False)


def demo_alerts(tracker: CostTracker) -> None:
    """Demo cost alerts."""
    print("\n🔔 Testing Cost Alert System...")

    # Configure alerts with low thresholds to trigger
    summary = tracker.get_summary()
    budget = summary.total_cost_usd * 1.2  # Set budget slightly above current cost

    config = AlertConfig(
        budget_threshold_pct=[50, 75, 90],  # Lower thresholds for demo
        hourly_rate_max=summary.total_cost_usd * 0.1,  # Will trigger
        daily_budget_max=summary.total_cost_usd * 2.0,  # Will trigger
        alert_cooldown_minutes=0  # No cooldown for demo
    )

    alert_system = CostAlertSystem(tracker, config)

    # Run checks
    alerts = alert_system.check_all()

    if alerts:
        print(f"\n⚠️  {len(alerts)} alert(s) triggered:")
        for alert in alerts:
            print(f"\n  [{alert.level.value.upper()}] {alert.title}")
            print(f"  {alert.message}")
    else:
        print("\n✅ No alerts triggered (all costs within limits)")

    print("\nAlert Summary:")
    for key, count in alert_system.get_alert_summary().items():
        print(f"  {key}: {count} time(s)")


def demo_snapshot(tracker: CostTracker) -> None:
    """Demo snapshot display."""
    print("\n📸 Cost Snapshot:\n")
    dashboard = CostDashboard(cost_tracker=tracker)
    dashboard.print_snapshot()


def demo_export(tracker: CostTracker) -> None:
    """Demo data export."""
    print("\n💾 Exporting Cost Data...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"trinity_costs_demo_{timestamp}.csv"
    json_path = f"trinity_costs_demo_{timestamp}.json"

    dashboard = CostDashboard(cost_tracker=tracker)
    dashboard._export_csv(csv_path)
    dashboard._export_json(json_path)

    print(f"\n✅ Data exported:")
    print(f"   CSV:  {csv_path}")
    print(f"   JSON: {json_path}")

    # Show file sizes
    csv_size = Path(csv_path).stat().st_size
    json_size = Path(json_path).stat().st_size

    print(f"\n📊 File sizes:")
    print(f"   CSV:  {csv_size:,} bytes")
    print(f"   JSON: {json_size:,} bytes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cost Dashboard Demo with Test Data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--calls',
        type=int,
        default=50,
        help='Number of test API calls to generate (default: 50)'
    )

    parser.add_argument(
        '--db',
        type=str,
        default='trinity_costs_demo.db',
        help='Database path (default: trinity_costs_demo.db)'
    )

    parser.add_argument(
        '--budget',
        type=float,
        default=10.0,
        help='Budget limit for demo (default: 10.0)'
    )

    parser.add_argument(
        '--terminal',
        action='store_true',
        help='Run terminal dashboard after generating data'
    )

    parser.add_argument(
        '--web',
        action='store_true',
        help='Run web dashboard after generating data'
    )

    parser.add_argument(
        '--alerts',
        action='store_true',
        help='Test alert system after generating data'
    )

    parser.add_argument(
        '--export',
        action='store_true',
        help='Export data after generating'
    )

    parser.add_argument(
        '--no-generate',
        action='store_true',
        help='Skip data generation (use existing database)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("TRINITY PROTOCOL - COST DASHBOARD DEMO")
    print("=" * 70)

    # Initialize tracker
    tracker = CostTracker(db_path=args.db, budget_usd=args.budget)

    # Generate test data
    if not args.no_generate:
        generate_test_data(tracker, num_calls=args.calls)
    else:
        print(f"\n📂 Using existing database: {args.db}")
        summary = tracker.get_summary()
        print(f"   Existing calls: {summary.total_calls}")
        print(f"   Total cost: ${summary.total_cost_usd:.4f}")
        print()

    # Run selected demo
    if args.terminal:
        demo_terminal_dashboard(tracker)
    elif args.web:
        demo_web_dashboard(tracker)
    elif args.alerts:
        demo_alerts(tracker)
    elif args.export:
        demo_export(tracker)
    else:
        # Default: show snapshot
        demo_snapshot(tracker)

        # Show available commands
        print("\n" + "=" * 70)
        print("TRY THESE COMMANDS:")
        print("=" * 70)
        print(f"\n# Terminal Dashboard (live updates)")
        print(f"python trinity_protocol/test_dashboard_demo.py --no-generate --terminal")
        print(f"\n# Web Dashboard")
        print(f"python trinity_protocol/test_dashboard_demo.py --no-generate --web")
        print(f"\n# Test Alerts")
        print(f"python trinity_protocol/test_dashboard_demo.py --no-generate --alerts")
        print(f"\n# Export Data")
        print(f"python trinity_protocol/test_dashboard_demo.py --no-generate --export")
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
