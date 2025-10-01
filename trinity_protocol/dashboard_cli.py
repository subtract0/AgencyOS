#!/usr/bin/env python3
"""
Unified CLI for Trinity Protocol Cost Monitoring.

Provides easy access to all dashboard features:
- Terminal dashboard (live curses interface)
- Web dashboard (browser-based)
- Cost alerts (continuous monitoring)
- Data export (CSV/JSON)
- Snapshots (one-time reports)

Usage:
    # Terminal dashboard
    python trinity_protocol/dashboard_cli.py terminal --live

    # Web dashboard
    python trinity_protocol/dashboard_cli.py web --port 8080

    # Cost alerts
    python trinity_protocol/dashboard_cli.py alerts --continuous

    # Export data
    python trinity_protocol/dashboard_cli.py export --csv costs.csv

    # Quick snapshot
    python trinity_protocol/dashboard_cli.py snapshot
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.cost_tracker import CostTracker
from trinity_protocol.cost_dashboard import CostDashboard
from trinity_protocol.cost_alerts import CostAlertSystem, AlertConfig, run_continuous_monitoring


def cmd_terminal(args):
    """Run terminal dashboard."""
    tracker = CostTracker(db_path=args.db, budget_usd=args.budget)
    dashboard = CostDashboard(
        cost_tracker=tracker,
        refresh_interval=args.interval,
        budget_warning_pct=args.warning_pct
    )

    if args.live:
        print("Starting live terminal dashboard...")
        print("Controls: [Q]uit | [E]xport | [R]efresh")
        print()
        dashboard.run_terminal_dashboard()
    else:
        dashboard.print_snapshot()


def cmd_web(args):
    """Run web dashboard."""
    try:
        from trinity_protocol.cost_dashboard_web import CostDashboardWeb
    except ImportError:
        print("ERROR: Flask not installed. Install with: pip install flask")
        return 1

    tracker = CostTracker(db_path=args.db, budget_usd=args.budget)
    dashboard = CostDashboardWeb(
        cost_tracker=tracker,
        refresh_interval=args.interval
    )

    dashboard.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


def cmd_alerts(args):
    """Run cost alerts."""
    tracker = CostTracker(db_path=args.db, budget_usd=args.budget)

    config = AlertConfig(
        budget_threshold_pct=args.thresholds,
        hourly_rate_max=args.hourly_max,
        daily_budget_max=args.daily_max,
        alert_cooldown_minutes=args.cooldown,
        log_to_file=args.log_file is not None,
        log_file_path=args.log_file or "trinity_alerts.log",
        # Email config
        email_enabled=args.email_enabled,
        email_smtp_host=args.email_smtp_host,
        email_smtp_port=args.email_smtp_port,
        email_from=args.email_from,
        email_to=args.email_to.split(',') if args.email_to else None,
        email_password=args.email_password,
        # Slack config
        slack_enabled=args.slack_enabled,
        slack_webhook_url=args.slack_webhook
    )

    if args.continuous:
        run_continuous_monitoring(tracker, config, args.check_interval)
    else:
        # Single check
        alert_system = CostAlertSystem(tracker, config)
        alerts = alert_system.check_all()

        if alerts:
            print(f"\n⚠️  {len(alerts)} alert(s) triggered:")
            for alert in alerts:
                print(f"\n[{alert.level.value.upper()}] {alert.title}")
                print(f"  {alert.message}")
        else:
            print("✅ No alerts triggered. All costs within limits.")


def cmd_export(args):
    """Export cost data."""
    tracker = CostTracker(db_path=args.db)
    dashboard = CostDashboard(cost_tracker=tracker)

    if args.csv:
        dashboard._export_csv(args.csv)
        print(f"✅ Exported to CSV: {args.csv}")

    if args.json:
        dashboard._export_json(args.json)
        print(f"✅ Exported to JSON: {args.json}")

    if not args.csv and not args.json:
        # Default: export both with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"trinity_costs_{timestamp}.csv"
        json_path = f"trinity_costs_{timestamp}.json"

        dashboard._export_csv(csv_path)
        dashboard._export_json(json_path)

        print(f"✅ Exported cost data:")
        print(f"  CSV:  {csv_path}")
        print(f"  JSON: {json_path}")


def cmd_snapshot(args):
    """Print cost snapshot."""
    tracker = CostTracker(db_path=args.db, budget_usd=args.budget)
    dashboard = CostDashboard(
        cost_tracker=tracker,
        budget_warning_pct=args.warning_pct
    )
    dashboard.print_snapshot()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Trinity Protocol Cost Monitoring CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Live terminal dashboard
  %(prog)s terminal --live

  # Web dashboard on custom port
  %(prog)s web --port 8080

  # Continuous cost alerts
  %(prog)s alerts --continuous --hourly-max 1.0

  # Export data
  %(prog)s export --csv costs.csv --json costs.json

  # Quick snapshot
  %(prog)s snapshot --budget 10.0
"""
    )

    # Global arguments
    parser.add_argument(
        '--db',
        type=str,
        default='trinity_costs.db',
        help='Path to cost database (default: trinity_costs.db)'
    )

    parser.add_argument(
        '--budget',
        type=float,
        help='Budget limit in USD (optional)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Terminal dashboard
    terminal_parser = subparsers.add_parser('terminal', help='Run terminal dashboard')
    terminal_parser.add_argument(
        '--live',
        action='store_true',
        help='Run live dashboard with auto-refresh'
    )
    terminal_parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Refresh interval in seconds (default: 5)'
    )
    terminal_parser.add_argument(
        '--warning-pct',
        type=float,
        default=80.0,
        help='Budget warning percentage (default: 80)'
    )
    terminal_parser.set_defaults(func=cmd_terminal)

    # Web dashboard
    web_parser = subparsers.add_parser('web', help='Run web dashboard')
    web_parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    web_parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port to listen on (default: 8080)'
    )
    web_parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Refresh interval in seconds (default: 5)'
    )
    web_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    web_parser.set_defaults(func=cmd_web)

    # Cost alerts
    alerts_parser = subparsers.add_parser('alerts', help='Run cost alerts')
    alerts_parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous monitoring'
    )
    alerts_parser.add_argument(
        '--check-interval',
        type=int,
        default=300,
        help='Check interval for continuous mode (seconds, default: 300)'
    )
    alerts_parser.add_argument(
        '--thresholds',
        type=float,
        nargs='+',
        default=[80, 90, 100],
        help='Budget threshold percentages (default: 80 90 100)'
    )
    alerts_parser.add_argument(
        '--hourly-max',
        type=float,
        help='Maximum hourly spending rate (USD/hour)'
    )
    alerts_parser.add_argument(
        '--daily-max',
        type=float,
        help='Maximum daily spending (USD/day)'
    )
    alerts_parser.add_argument(
        '--cooldown',
        type=int,
        default=60,
        help='Alert cooldown minutes (default: 60)'
    )
    alerts_parser.add_argument(
        '--log-file',
        type=str,
        help='Log file path (default: trinity_alerts.log)'
    )

    # Email alerts
    alerts_parser.add_argument(
        '--email-enabled',
        action='store_true',
        help='Enable email alerts'
    )
    alerts_parser.add_argument(
        '--email-smtp-host',
        type=str,
        help='SMTP server host'
    )
    alerts_parser.add_argument(
        '--email-smtp-port',
        type=int,
        default=587,
        help='SMTP server port (default: 587)'
    )
    alerts_parser.add_argument(
        '--email-from',
        type=str,
        help='From email address'
    )
    alerts_parser.add_argument(
        '--email-to',
        type=str,
        help='To email addresses (comma-separated)'
    )
    alerts_parser.add_argument(
        '--email-password',
        type=str,
        help='Email password'
    )

    # Slack alerts
    alerts_parser.add_argument(
        '--slack-enabled',
        action='store_true',
        help='Enable Slack alerts'
    )
    alerts_parser.add_argument(
        '--slack-webhook',
        type=str,
        help='Slack webhook URL'
    )

    alerts_parser.set_defaults(func=cmd_alerts)

    # Export
    export_parser = subparsers.add_parser('export', help='Export cost data')
    export_parser.add_argument(
        '--csv',
        type=str,
        help='Export to CSV file'
    )
    export_parser.add_argument(
        '--json',
        type=str,
        help='Export to JSON file'
    )
    export_parser.set_defaults(func=cmd_export)

    # Snapshot
    snapshot_parser = subparsers.add_parser('snapshot', help='Print cost snapshot')
    snapshot_parser.add_argument(
        '--warning-pct',
        type=float,
        default=80.0,
        help='Budget warning percentage (default: 80)'
    )
    snapshot_parser.set_defaults(func=cmd_snapshot)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run command
    return args.func(args) or 0


if __name__ == '__main__':
    sys.exit(main())
