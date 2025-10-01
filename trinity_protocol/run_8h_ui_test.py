#!/usr/bin/env python3
"""
8-Hour UI Development Focused Autonomous Test

Focus: Develop Apple-inspired integrated UI system
Model: Claude Sonnet 4.5 (cost-efficient, high-quality)
Duration: 8 hours
Budget: $5.00

This test runs Trinity Protocol in autonomous mode focused on:
1. Designing integrated UI system (text + visual, Apple-inspired)
2. Implementing UI components with real-time updates
3. Testing cost efficiency with Claude Sonnet 4.5
4. Validating autonomous UI development workflow
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.run_24h_test import run_autonomous_test

async def main():
    """Run 8-hour UI-focused autonomous test."""

    print("=" * 80)
    print("TRINITY PROTOCOL - 8-HOUR UI DEVELOPMENT TEST")
    print("=" * 80)
    print()
    print("Configuration:")
    print("  Duration: 8 hours")
    print("  Budget: $5.00")
    print("  Model: Claude Sonnet 4.5")
    print("  Focus: Apple-inspired integrated UI system")
    print()
    print("Objectives:")
    print("  1. Design integrated UI (text + visual + interactive)")
    print("  2. Implement real-time dashboard with Apple aesthetics")
    print("  3. Test autonomous UI development workflow")
    print("  4. Validate cost efficiency with Sonnet 4.5")
    print()
    print("Starting test...")
    print("=" * 80)
    print()

    # Set model to Claude Sonnet 4.5
    os.environ["AGENCY_MODEL"] = "claude-sonnet-4-20250514"
    os.environ["PLANNER_MODEL"] = "claude-sonnet-4-20250514"
    os.environ["CODER_MODEL"] = "claude-sonnet-4-20250514"

    # Run 8-hour test
    await run_autonomous_test(
        duration_hours=8,
        budget_usd=5.00,
        event_interval_minutes=30,
        cost_snapshot_interval_minutes=60,
        metrics_interval_minutes=5,
        focus_area="ui_development",
        model_override="claude-sonnet-4-20250514"
    )

if __name__ == "__main__":
    asyncio.run(main())
