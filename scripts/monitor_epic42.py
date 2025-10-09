#!/usr/bin/env python3
"""
Monitor Epic 4.2 Autonomous Execution

Real-time monitoring of autonomous agents working on Epic 4.2 tasks.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, "/Users/am/Code/Agency")
from meta_learning.task_queue import TaskQueue


def format_task_status(task):
    """Format task status with icons."""
    icons = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}
    icon = icons.get(task.status, "❓")

    agent = task.assigned_to or "unassigned"
    machine = task.machine or "N/A"

    return f"{icon} {task.task_id:<40} {task.status:<12} {agent:<15} {machine}"


def main():
    """Monitor Epic 4.2 tasks."""
    print("=" * 120)
    print(" 🎯 EPIC 4.2: Proposal Generator - Real-Time Monitoring")
    print("=" * 120)
    print()

    try:
        while True:
            q = TaskQueue()
            tasks = q._read_queue()

            # Filter Epic 4.2 tasks
            epic42_tasks = [t for t in tasks if "epic4.2" in t.task_id]

            # Sort by status priority
            status_order = {"in_progress": 0, "failed": 1, "pending": 2, "completed": 3}
            epic42_tasks.sort(key=lambda t: (status_order.get(t.status, 99), t.task_id))

            # Count by status
            counts = {}
            for task in epic42_tasks:
                counts[task.status] = counts.get(task.status, 0) + 1

            # Clear screen
            print("\033[2J\033[H", end="")

            # Print header
            print("=" * 120)
            print(" 🎯 EPIC 4.2: Proposal Generator - Real-Time Monitoring")
            print("=" * 120)
            print()
            print(
                f"📊 Status: Pending={counts.get('pending', 0)} | In Progress={counts.get('in_progress', 0)} | "
                + f"Completed={counts.get('completed', 0)} | Failed={counts.get('failed', 0)}"
            )
            print()
            print(f"{'Status':<3} {'Task ID':<40} {'Status':<12} {'Agent':<15} {'Machine'}")
            print("-" * 120)

            # Print tasks
            for task in epic42_tasks:
                print(format_task_status(task))

            print()
            print("=" * 120)
            print("🔄 Refreshing every 5 seconds... (Ctrl+C to exit)")

            # Wait before refresh
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
