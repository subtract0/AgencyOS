#!/usr/bin/env python3
"""
Quick status check for the Pain Point Goldminer.

Usage: python tools/goldminer_status.py
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

STORAGE_PATH = Path("/Volumes/Satechi4TB/pain_points")

def main():
    print("=" * 60)
    print("GOLDMINER STATUS CHECK")
    print("=" * 60)

    # Check if process is running
    result = subprocess.run(
        ["pgrep", "-f", "pain_point_goldminer"],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        pids = result.stdout.strip().split('\n')
        print(f"\n✅ RUNNING - PID(s): {', '.join(pids)}")
    else:
        print("\n❌ NOT RUNNING")
        print("   Start with: cd /Users/am/Code/AgencyOS && nohup python tools/pain_point_goldminer_v4.py --storage /Volumes/Satechi4TB/pain_points > /tmp/goldminer.out 2>&1 &")
        return

    # Check storage
    if not STORAGE_PATH.exists():
        print(f"\n⚠️  Storage path not found: {STORAGE_PATH}")
        return

    # Count raw files
    raw_files = list((STORAGE_PATH / "raw").glob("*.json"))
    print(f"\n📦 RAW DATA FILES: {len(raw_files)}")

    # Count total pain points
    total_points = 0
    latest_file = None
    latest_time = None

    for f in raw_files:
        try:
            with open(f) as fp:
                data = json.load(fp)
                total_points += len(data)

            mtime = f.stat().st_mtime
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_file = f
        except:
            pass

    print(f"📊 TOTAL PAIN POINTS: {total_points}")

    if latest_file:
        age = datetime.now() - datetime.fromtimestamp(latest_time)
        print(f"🕐 LATEST FILE: {latest_file.name} ({age.seconds // 60} min ago)")

    # Check analysis files
    analysis_files = list((STORAGE_PATH / "analysis").glob("*.txt"))
    print(f"\n🔍 ANALYSIS FILES: {len(analysis_files)}")

    # Check daily summaries
    summary_files = list((STORAGE_PATH / "daily_summaries").glob("*.md"))
    print(f"📋 DAILY SUMMARIES: {len(summary_files)}")

    # Latest log entries
    log_files = list(STORAGE_PATH.glob("goldminer_*.log"))
    if log_files:
        latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
        print(f"\n📝 LATEST LOG: {latest_log.name}")
        print("-" * 40)

        with open(latest_log) as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"   {line.rstrip()}")

    print("\n" + "=" * 60)
    print("COMMANDS:")
    print("  View live log: tail -f /Volumes/Satechi4TB/pain_points/goldminer_*.log")
    print("  Stop gracefully: kill -SIGTERM $(pgrep -f pain_point_goldminer)")
    print("=" * 60)


if __name__ == "__main__":
    main()
