#!/usr/bin/env python3
"""
Real-time cost monitoring dashboard for Trinity Protocol.

Features:
- Live cost updates every 5 seconds
- Per-agent breakdown with visual bars
- Hourly/daily spending trends
- Budget alerts with warnings
- Export to CSV/JSON
- Keyboard-driven interface

Usage:
    # Terminal dashboard (live updates)
    python trinity_protocol/cost_dashboard.py --live

    # Single snapshot
    python trinity_protocol/cost_dashboard.py

    # Export to CSV
    python trinity_protocol/cost_dashboard.py --export costs.csv

    # Custom refresh interval
    python trinity_protocol/cost_dashboard.py --live --interval 10
"""

import argparse
import csv
import curses
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.cost_tracker import CostTracker, CostSummary


@dataclass
class SpendingTrend:
    """Spending trend over time period."""

    hourly_rate: float  # USD per hour
    daily_projection: float  # Projected daily spend
    last_hour_cost: float  # Cost in last hour
    last_day_cost: float  # Cost in last 24 hours


class CostDashboard:
    """Real-time cost monitoring dashboard for Trinity Protocol."""

    def __init__(
        self,
        cost_tracker: CostTracker,
        refresh_interval: int = 5,
        budget_warning_pct: float = 80.0
    ):
        """
        Initialize cost dashboard.

        Args:
            cost_tracker: CostTracker instance to monitor
            refresh_interval: Seconds between dashboard updates
            budget_warning_pct: Budget percentage to trigger warnings
        """
        self.tracker = cost_tracker
        self.refresh_interval = refresh_interval
        self.budget_warning_pct = budget_warning_pct
        self.start_time = datetime.now()

    def run_terminal_dashboard(self) -> None:
        """Run curses-based terminal dashboard with live updates."""
        try:
            curses.wrapper(self._render_dashboard)
        except KeyboardInterrupt:
            print("\n\nDashboard stopped by user.")

    def _render_dashboard(self, stdscr) -> None:
        """
        Render interactive dashboard in terminal.

        Args:
            stdscr: Curses window object
        """
        # Configure curses
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)  # Non-blocking input
        stdscr.timeout(self.refresh_interval * 1000)  # Refresh timeout

        # Initialize color pairs if supported
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Success
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)  # Alert
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Info

        export_message = ""

        while True:
            try:
                stdscr.clear()
                height, width = stdscr.getmaxyx()

                # Get current data
                summary = self.tracker.get_summary()
                trend = self._calculate_trends()

                row = 0

                # Header
                self._draw_header(stdscr, row, width)
                row += 4

                # Total costs section
                row = self._draw_totals(stdscr, row, summary, trend, width)
                row += 1

                # Budget section
                if self.tracker.budget_usd:
                    row = self._draw_budget(stdscr, row, summary, width)
                    row += 1

                # Per-agent breakdown
                if summary.by_agent:
                    row = self._draw_agent_breakdown(stdscr, row, summary, width, height)
                    row += 1

                # Recent activity
                if row < height - 8:
                    row = self._draw_recent_activity(stdscr, row, width, height)
                    row += 1

                # Export message
                if export_message and row < height - 3:
                    self._draw_text(stdscr, row, 0, export_message, curses.A_DIM)
                    row += 1

                # Controls
                self._draw_controls(stdscr, height - 2, width)

                stdscr.refresh()

                # Handle input
                key = stdscr.getch()

                if key == ord('q') or key == ord('Q'):
                    break
                elif key == ord('e') or key == ord('E'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv_path = f"trinity_costs_{timestamp}.csv"
                    json_path = f"trinity_costs_{timestamp}.json"

                    self._export_csv(csv_path)
                    self._export_json(json_path)

                    export_message = f"Exported: {csv_path} and {json_path}"
                elif key == ord('r') or key == ord('R'):
                    export_message = "Dashboard refreshed"

                time.sleep(0.1)  # Small delay to prevent CPU spin

            except curses.error:
                # Window too small or other curses error
                stdscr.clear()
                stdscr.addstr(0, 0, "Terminal window too small. Please resize.")
                stdscr.refresh()
                time.sleep(1)

    def _draw_header(self, stdscr, row: int, width: int) -> None:
        """Draw dashboard header."""
        separator = "=" * min(width - 1, 80)
        title = "TRINITY PROTOCOL - REAL-TIME COST DASHBOARD"
        timestamp = f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self._draw_text(stdscr, row, 0, separator)
        self._draw_text(stdscr, row + 1, 0, title, curses.A_BOLD)
        self._draw_text(stdscr, row + 2, 0, timestamp, curses.A_DIM)
        self._draw_text(stdscr, row + 3, 0, separator)

    def _draw_totals(
        self,
        stdscr,
        row: int,
        summary: CostSummary,
        trend: SpendingTrend,
        width: int
    ) -> int:
        """Draw total costs section."""
        self._draw_text(stdscr, row, 0, "SUMMARY", curses.A_BOLD)
        row += 1

        total_tokens = summary.total_input_tokens + summary.total_output_tokens

        # Main metrics
        self._draw_text(stdscr, row, 2, f"Total Spent:        ${summary.total_cost_usd:.4f}")
        row += 1
        self._draw_text(stdscr, row, 2, f"Total Calls:        {summary.total_calls:,}")
        row += 1
        self._draw_text(stdscr, row, 2, f"Total Tokens:       {total_tokens:,}")
        row += 1
        self._draw_text(stdscr, row, 2, f"Success Rate:       {summary.success_rate * 100:.1f}%")
        row += 1

        # Spending trends
        self._draw_text(stdscr, row, 2, f"Hourly Rate:        ${trend.hourly_rate:.4f}/hour")
        row += 1
        self._draw_text(stdscr, row, 2, f"Daily Projection:   ${trend.daily_projection:.2f}/day")
        row += 1

        return row

    def _draw_budget(
        self,
        stdscr,
        row: int,
        summary: CostSummary,
        width: int
    ) -> int:
        """Draw budget section with visual indicator."""
        budget = self.tracker.budget_usd
        spent = summary.total_cost_usd
        remaining = budget - spent
        percent = (spent / budget) * 100 if budget > 0 else 0

        self._draw_text(stdscr, row, 0, "BUDGET", curses.A_BOLD)
        row += 1

        # Budget numbers
        self._draw_text(stdscr, row, 2, f"Budget:             ${budget:.2f}")
        row += 1
        self._draw_text(stdscr, row, 2, f"Spent:              ${spent:.4f} ({percent:.1f}%)")
        row += 1
        self._draw_text(stdscr, row, 2, f"Remaining:          ${remaining:.4f}")
        row += 1

        # Visual progress bar
        bar_width = min(width - 6, 60)
        filled = int((percent / 100) * bar_width)

        # Choose color based on percentage
        if percent >= 90:
            color = curses.color_pair(3)  # Red
        elif percent >= self.budget_warning_pct:
            color = curses.color_pair(2)  # Yellow
        else:
            color = curses.color_pair(1)  # Green

        bar = "█" * filled + "░" * (bar_width - filled)
        self._draw_text(stdscr, row, 2, "[", color)
        self._draw_text(stdscr, row, 3, bar, color)
        self._draw_text(stdscr, row, 3 + bar_width, "]", color)
        row += 1

        # Budget warning
        if percent >= self.budget_warning_pct:
            warning = f"⚠️  WARNING: {percent:.1f}% of budget used!"
            self._draw_text(stdscr, row, 2, warning, curses.color_pair(3) | curses.A_BOLD)
            row += 1

        return row

    def _draw_agent_breakdown(
        self,
        stdscr,
        row: int,
        summary: CostSummary,
        width: int,
        height: int
    ) -> int:
        """Draw per-agent cost breakdown with bars."""
        self._draw_text(stdscr, row, 0, "PER-AGENT COSTS", curses.A_BOLD)
        row += 1

        # Sort agents by cost (descending)
        sorted_agents = sorted(
            summary.by_agent.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Calculate max cost for bar scaling
        max_cost = max(summary.by_agent.values()) if summary.by_agent else 1.0

        # Display top agents (limit to available space)
        max_agents = min(len(sorted_agents), height - row - 6)

        for agent, cost in sorted_agents[:max_agents]:
            # Calculate percentage of total
            pct = (cost / summary.total_cost_usd * 100) if summary.total_cost_usd > 0 else 0

            # Create visual bar
            bar_width = 30
            filled = int((cost / max_cost) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            line = f"  {agent:25s} ${cost:7.4f} ({pct:5.1f}%) {bar}"
            self._draw_text(stdscr, row, 0, line)
            row += 1

        if len(sorted_agents) > max_agents:
            self._draw_text(
                stdscr,
                row,
                2,
                f"... and {len(sorted_agents) - max_agents} more agents",
                curses.A_DIM
            )
            row += 1

        return row

    def _draw_recent_activity(
        self,
        stdscr,
        row: int,
        width: int,
        height: int
    ) -> int:
        """Draw recent API calls."""
        self._draw_text(stdscr, row, 0, "RECENT ACTIVITY", curses.A_BOLD)
        row += 1

        recent_calls = self.tracker.get_recent_calls(limit=5)

        if not recent_calls:
            self._draw_text(stdscr, row, 2, "No recent activity", curses.A_DIM)
            row += 1
            return row

        for call in recent_calls:
            timestamp = datetime.fromisoformat(call.timestamp).strftime("%H:%M:%S")
            status = "✓" if call.success else "✗"

            line = f"  {timestamp} | {call.agent:20s} | ${call.cost_usd:.4f} | {status}"

            color = curses.color_pair(1) if call.success else curses.color_pair(3)
            self._draw_text(stdscr, row, 0, line, color if curses.has_colors() else 0)
            row += 1

        return row

    def _draw_controls(self, stdscr, row: int, width: int) -> None:
        """Draw keyboard controls."""
        controls = "Controls: [Q]uit | [E]xport | [R]efresh"
        self._draw_text(stdscr, row, 0, controls, curses.A_DIM)

    def _draw_text(self, stdscr, row: int, col: int, text: str, attr=0) -> None:
        """Safely draw text to screen."""
        try:
            stdscr.addstr(row, col, text, attr)
        except curses.error:
            pass  # Ignore if outside window bounds

    def _calculate_trends(self) -> SpendingTrend:
        """Calculate spending trends."""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        # Get costs for different time periods
        last_hour_summary = self.tracker.get_summary(since=one_hour_ago)
        last_day_summary = self.tracker.get_summary(since=one_day_ago)

        last_hour_cost = last_hour_summary.total_cost_usd
        last_day_cost = last_day_summary.total_cost_usd

        # Calculate hourly rate
        hourly_rate = last_hour_cost

        # Project daily spending
        daily_projection = hourly_rate * 24

        return SpendingTrend(
            hourly_rate=hourly_rate,
            daily_projection=daily_projection,
            last_hour_cost=last_hour_cost,
            last_day_cost=last_day_cost
        )

    def _export_csv(self, output_path: str) -> None:
        """Export cost data to CSV."""
        summary = self.tracker.get_summary()
        recent_calls = self.tracker.get_recent_calls(limit=1000)

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "timestamp",
                "agent",
                "model",
                "model_tier",
                "input_tokens",
                "output_tokens",
                "cost_usd",
                "duration_seconds",
                "success",
                "task_id",
                "correlation_id"
            ])

            # Data rows
            for call in recent_calls:
                writer.writerow([
                    call.timestamp,
                    call.agent,
                    call.model,
                    call.model_tier.value,
                    call.input_tokens,
                    call.output_tokens,
                    call.cost_usd,
                    call.duration_seconds,
                    call.success,
                    call.task_id or "",
                    call.correlation_id or ""
                ])

    def _export_json(self, output_path: str) -> None:
        """Export cost data to JSON."""
        summary = self.tracker.get_summary()
        recent_calls = self.tracker.get_recent_calls(limit=1000)
        trend = self._calculate_trends()

        data = {
            "exported_at": datetime.now().isoformat(),
            "summary": {
                "total_cost_usd": summary.total_cost_usd,
                "total_calls": summary.total_calls,
                "total_input_tokens": summary.total_input_tokens,
                "total_output_tokens": summary.total_output_tokens,
                "success_rate": summary.success_rate,
                "by_agent": summary.by_agent,
                "by_model": summary.by_model,
                "by_task": summary.by_task
            },
            "trends": {
                "hourly_rate": trend.hourly_rate,
                "daily_projection": trend.daily_projection,
                "last_hour_cost": trend.last_hour_cost,
                "last_day_cost": trend.last_day_cost
            },
            "budget": {
                "limit": self.tracker.budget_usd,
                "spent": summary.total_cost_usd,
                "remaining": (self.tracker.budget_usd or 0) - summary.total_cost_usd,
                "percent_used": (
                    (summary.total_cost_usd / self.tracker.budget_usd * 100)
                    if self.tracker.budget_usd else 0
                )
            },
            "recent_calls": [
                {
                    "timestamp": call.timestamp,
                    "agent": call.agent,
                    "model": call.model,
                    "model_tier": call.model_tier.value,
                    "input_tokens": call.input_tokens,
                    "output_tokens": call.output_tokens,
                    "cost_usd": call.cost_usd,
                    "duration_seconds": call.duration_seconds,
                    "success": call.success,
                    "task_id": call.task_id,
                    "correlation_id": call.correlation_id
                }
                for call in recent_calls
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def print_snapshot(self) -> None:
        """Print a single dashboard snapshot to console."""
        summary = self.tracker.get_summary()
        trend = self._calculate_trends()

        print("\n" + "=" * 70)
        print("TRINITY PROTOCOL - COST SNAPSHOT")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        print(f"\n💰 TOTAL COST: ${summary.total_cost_usd:.4f}")

        if self.tracker.budget_usd:
            remaining = self.tracker.budget_usd - summary.total_cost_usd
            percent = (summary.total_cost_usd / self.tracker.budget_usd) * 100
            print(f"📊 BUDGET: ${summary.total_cost_usd:.4f} / ${self.tracker.budget_usd:.2f} ({percent:.1f}%)")
            print(f"💵 REMAINING: ${remaining:.4f}")

            if percent >= self.budget_warning_pct:
                print(f"\n⚠️  WARNING: {percent:.1f}% of budget used!")

        print(f"\n📞 TOTAL CALLS: {summary.total_calls}")
        print(f"✅ SUCCESS RATE: {summary.success_rate * 100:.1f}%")
        print(f"🔢 TOKENS: {summary.total_input_tokens:,} in + {summary.total_output_tokens:,} out")

        print(f"\n📈 SPENDING TRENDS:")
        print(f"  Hourly Rate:      ${trend.hourly_rate:.4f}/hour")
        print(f"  Daily Projection: ${trend.daily_projection:.2f}/day")
        print(f"  Last Hour Cost:   ${trend.last_hour_cost:.4f}")
        print(f"  Last Day Cost:    ${trend.last_day_cost:.4f}")

        if summary.by_agent:
            print(f"\n📍 BY AGENT:")
            for agent, cost in sorted(summary.by_agent.items(), key=lambda x: -x[1]):
                pct = (cost / summary.total_cost_usd * 100) if summary.total_cost_usd > 0 else 0
                print(f"  {agent:30s} ${cost:7.4f} ({pct:5.1f}%)")

        if summary.by_model:
            print(f"\n🤖 BY MODEL:")
            for model, cost in sorted(summary.by_model.items(), key=lambda x: -x[1]):
                pct = (cost / summary.total_cost_usd * 100) if summary.total_cost_usd > 0 else 0
                print(f"  {model:30s} ${cost:7.4f} ({pct:5.1f}%)")

        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point for cost dashboard CLI."""
    parser = argparse.ArgumentParser(
        description="Trinity Protocol Real-Time Cost Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Live dashboard with default 5-second refresh
  python cost_dashboard.py --live

  # Live dashboard with 10-second refresh
  python cost_dashboard.py --live --interval 10

  # Single snapshot
  python cost_dashboard.py

  # Export to CSV
  python cost_dashboard.py --export costs.csv

  # Custom database and budget
  python cost_dashboard.py --live --db trinity_costs.db --budget 10.0
"""
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live dashboard with auto-refresh"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)"
    )

    parser.add_argument(
        "--db",
        type=str,
        default="trinity_costs.db",
        help="Path to cost database (default: trinity_costs.db)"
    )

    parser.add_argument(
        "--budget",
        type=float,
        help="Budget limit in USD (optional)"
    )

    parser.add_argument(
        "--export",
        type=str,
        metavar="PATH",
        help="Export data to CSV and exit"
    )

    parser.add_argument(
        "--warning-pct",
        type=float,
        default=80.0,
        help="Budget warning percentage (default: 80)"
    )

    args = parser.parse_args()

    # Initialize cost tracker
    tracker = CostTracker(db_path=args.db, budget_usd=args.budget)
    dashboard = CostDashboard(
        cost_tracker=tracker,
        refresh_interval=args.interval,
        budget_warning_pct=args.warning_pct
    )

    # Handle export mode
    if args.export:
        base_path = args.export.replace(".csv", "")
        csv_path = f"{base_path}.csv"
        json_path = f"{base_path}.json"

        dashboard._export_csv(csv_path)
        dashboard._export_json(json_path)

        print(f"✅ Exported cost data:")
        print(f"  CSV:  {csv_path}")
        print(f"  JSON: {json_path}")
        return 0

    # Handle live mode
    if args.live:
        print("Starting live dashboard... (Press Q to quit, E to export)")
        time.sleep(1)
        dashboard.run_terminal_dashboard()
    else:
        # Single snapshot
        dashboard.print_snapshot()

    return 0


if __name__ == "__main__":
    sys.exit(main())
