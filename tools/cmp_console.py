#!/usr/bin/env python3
"""
CMP Console - CLI tool for inspecting CMP (Clade Metaproductivity) events and scores.

Provides commands for:
- Listing all clades with scores
- Viewing events for a specific clade
- Inspecting per-agent health metrics
- Exporting raw events for auditing

Usage:
    python tools/cmp_console.py list-clades [--task-type TYPE]
    python tools/cmp_console.py show-clade <clade_id> [--limit N]
    python tools/cmp_console.py agent-health [--task-type TYPE]
    python tools/cmp_console.py show-event <event_id>
    python tools/cmp_console.py export [--output FILE]

Examples:
    # List all clades ranked by score
    python tools/cmp_console.py list-clades

    # List clades for self_heal tasks
    python tools/cmp_console.py list-clades --task-type self_heal

    # Show details for a specific clade
    python tools/cmp_console.py show-clade "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"

    # Export all events to JSON
    python tools/cmp_console.py export --output cmp_export.json
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to PYTHONPATH for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agency_memory.learning import CmpStore, compute_clade_score


def list_clades(task_type: str | None = None) -> None:
    """
    List all clades with their performance scores.

    Args:
        task_type: Optional filter by task type
    """
    store = CmpStore()
    events = store.load_events(task_type=task_type)

    if not events:
        print("No CMP events found.")
        if task_type:
            print(f"(filtered by task_type={task_type})")
        return

    # Get all unique clade IDs
    clade_ids = store.get_all_clade_ids(task_type=task_type)

    if not clade_ids:
        print("No clades found.")
        return

    # Compute scores for all clades
    clade_scores = []
    for clade_id in clade_ids:
        score = compute_clade_score(events, clade_id)
        clade_scores.append(score)

    # Sort by score (highest first)
    clade_scores.sort(key=lambda x: x.score, reverse=True)

    # Print header
    print("\n" + "=" * 100)
    print(f"CLADE PERFORMANCE RANKING" + (f" (task_type={task_type})" if task_type else ""))
    print("=" * 100)
    print(
        f"{'RANK':<5} {'SCORE':<7} {'EVENTS':<7} {'APPROVED':<9} {'REJECTED':<9} {'REVERTS':<8} {'CLADE ID':<40}"
    )
    print("-" * 100)

    # Print clades
    for rank, score in enumerate(clade_scores, 1):
        print(
            f"{rank:<5} {score.score:>6.3f} {score.total_events:>6} "
            f"{score.approvals:>8} {score.rejections:>8} {score.reverts:>7} "
            f"{score.clade_id:<40}"
        )

    print("-" * 100)
    print(f"Total clades: {len(clade_scores)}")
    print(f"Total events: {len(events)}")
    print()


def show_clade(clade_id: str, limit: int = 10) -> None:
    """
    Show detailed information for a specific clade.

    Args:
        clade_id: Clade identifier to inspect
        limit: Maximum number of events to show
    """
    store = CmpStore()
    events = store.load_events()

    # Filter events for this clade
    clade_events = [e for e in events if e.clade_id == clade_id]

    if not clade_events:
        print(f"No events found for clade: {clade_id}")
        return

    # Compute score
    score = compute_clade_score(events, clade_id)

    # Print header
    print("\n" + "=" * 100)
    print(f"CLADE DETAILS: {clade_id}")
    print("=" * 100)

    # Print score summary
    print("\nPERFORMANCE METRICS:")
    print(f"  Score:              {score.score:.3f}")
    print(f"  Total Events:       {score.total_events}")
    print(f"  Approvals:          {score.approvals} ({score.approval_rate*100:.1f}%)")
    print(f"  Rejections:         {score.rejections}")
    print(f"  Reverts:            {score.reverts} ({score.revert_rate*100:.1f}%)")
    print(f"  Avg LOC (rejected): {score.avg_loc_delta_rejected:.1f}")

    # Print recent events
    print(f"\nRECENT EVENTS (showing {min(limit, len(clade_events))} of {len(clade_events)}):")
    print("-" * 100)
    print(f"{'EVENT ID':<30} {'PR':<5} {'SIGNAL':<10} {'REVERTED':<9} {'LOC':<6} {'TEST':<6} {'DATE':<19}")
    print("-" * 100)

    # Sort by closed_at (most recent first)
    clade_events.sort(key=lambda x: x.closed_at, reverse=True)

    for event in clade_events[:limit]:
        closed_dt = datetime.fromtimestamp(event.closed_at).strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"{event.id:<30} #{event.pr_id:<4} {event.reinforcement_signal:<10} "
            f"{'YES' if event.reverted else 'NO':<9} {event.size_loc_delta:<6} "
            f"{event.test_status:<6} {closed_dt:<19}"
        )

    print()


def show_event(event_id: str) -> None:
    """
    Show detailed information for a specific event.

    Args:
        event_id: Event ID to inspect
    """
    store = CmpStore()
    events = store.load_events()

    # Find event
    event = next((e for e in events if e.id == event_id), None)

    if not event:
        print(f"Event not found: {event_id}")
        return

    # Print event details
    print("\n" + "=" * 100)
    print(f"EVENT DETAILS: {event_id}")
    print("=" * 100)
    print()


def agent_health(task_type: str | None = None) -> None:
    """Display aggregate CMP metrics per agent."""

    store = CmpStore()
    events = store.load_events(task_type=task_type)

    if not events:
        print("No CMP events available." + (f" (task_type={task_type})" if task_type else ""))
        return

    # Aggregate stats per agent
    agents: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "total": 0,
        "approvals": 0,
        "rejections": 0,
        "reverts": 0,
        "clades": set(),
    })

    for event in events:
        stats = agents[event.agent_id]
        stats["total"] += 1
        if event.reinforcement_signal == "approved":
            stats["approvals"] += 1
        else:
            stats["rejections"] += 1
        if event.reverted:
            stats["reverts"] += 1
        stats["clades"].add(event.clade_id)

    # Header
    print("\n" + "=" * 80)
    print(f"AGENT HEALTH" + (f" (task_type={task_type})" if task_type else ""))
    print("=" * 80)
    print(
        f"{'AGENT':<30} {'EVENTS':>6} {'APP':>5} {'REJ':>5} {'REVERTS':>7} "
        f"{'APP%':>6} {'CLADES':>7}"
    )
    print("-" * 80)

    for agent_id, stats in sorted(agents.items()):
        total = stats["total"]
        approvals = stats["approvals"]
        rejections = stats["rejections"]
        reverts = stats["reverts"]
        approval_rate = (approvals / total * 100) if total else 0.0
        clade_count = len(stats["clades"])

        print(
            f"{agent_id:<30} {total:>6} {approvals:>5} {rejections:>5} {reverts:>7} "
            f"{approval_rate:>5.1f}% {clade_count:>7}"
        )

    print("-" * 80)
    print(f"Total agents: {len(agents)}")
    print()

    # Convert to dict for pretty printing
    event_dict = event.to_dict()

    # Print key fields
    print(f"ID:                   {event_dict['id']}")
    print(f"PR ID:                #{event_dict['pr_id']}")
    print(f"Branch:               {event_dict['branch_name']}")
    print(f"Agent:                {event_dict['agent_id']}")
    print(f"Clade:                {event_dict['clade_id']}")
    print(f"Task Type:            {event_dict['task_type']}")
    print()

    # Timestamps
    created_dt = datetime.fromtimestamp(event_dict["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
    closed_dt = datetime.fromtimestamp(event_dict["closed_at"]).strftime("%Y-%m-%d %H:%M:%S")
    duration_sec = event_dict["closed_at"] - event_dict["created_at"]
    duration_min = duration_sec // 60

    print(f"Created:              {created_dt}")
    print(f"Closed:               {closed_dt}")
    print(f"Duration:             {duration_min} minutes ({duration_sec} seconds)")
    print()

    # Outcome
    print(f"Reinforcement Signal: {event_dict['reinforcement_signal']}")
    print(f"Reverted:             {'YES' if event_dict['reverted'] else 'NO'}")
    print(f"Test Status:          {event_dict['test_status']}")
    print(f"Test Suites:          {', '.join(event_dict['test_suites']) if event_dict['test_suites'] else 'N/A'}")
    print()

    # Code changes
    print(f"LOC Delta:            {event_dict['size_loc_delta']}")
    print(f"Files Touched:        {len(event_dict['files_touched'])}")
    if event_dict['files_touched']:
        for file_path in event_dict['files_touched'][:10]:  # Show first 10 files
            print(f"  - {file_path}")
        if len(event_dict['files_touched']) > 10:
            print(f"  ... and {len(event_dict['files_touched']) - 10} more")
    print()

    # Optional fields
    if event_dict.get('human_review_time_sec'):
        review_min = event_dict['human_review_time_sec'] // 60
        print(f"Human Review Time:    {review_min} minutes ({event_dict['human_review_time_sec']} seconds)")

    if event_dict.get('extra_metadata'):
        print("\nExtra Metadata:")
        for key, value in event_dict['extra_metadata'].items():
            print(f"  {key}: {value}")

    print()


def export_events(output_file: str | None = None) -> None:
    """
    Export all CMP events to JSON file.

    Args:
        output_file: Output file path (default: cmp_export_{timestamp}.json)
    """
    store = CmpStore()
    events = store.load_events()

    if not events:
        print("No events to export.")
        return

    # Default output file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"cmp_export_{timestamp}.json"

    # Convert events to dicts
    events_data = [event.to_dict() for event in events]

    # Write to file
    output_path = Path(output_file)
    with open(output_path, "w") as f:
        json.dump(events_data, f, indent=2)

    print(f"✅ Exported {len(events)} events to: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CMP Console - Inspect clade metaproductivity events and scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # list-clades command
    list_parser = subparsers.add_parser("list-clades", help="List all clades with scores")
    list_parser.add_argument(
        "--task-type", type=str, help="Filter by task type (e.g., self_heal, backlog)"
    )

    # show-clade command
    show_clade_parser = subparsers.add_parser("show-clade", help="Show details for a specific clade")
    show_clade_parser.add_argument("clade_id", type=str, help="Clade identifier")
    show_clade_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of events to show (default: 10)"
    )

    # show-event command
    show_event_parser = subparsers.add_parser("show-event", help="Show details for a specific event")
    show_event_parser.add_argument("event_id", type=str, help="Event ID")

    # agent-health command
    agent_health_parser = subparsers.add_parser(
        "agent-health", help="Aggregate CMP stats per agent"
    )
    agent_health_parser.add_argument(
        "--task-type", type=str, help="Filter by task type (e.g., self_heal, backlog)"
    )

    # export command
    export_parser = subparsers.add_parser("export", help="Export all events to JSON file")
    export_parser.add_argument(
        "--output", type=str, help="Output file path (default: cmp_export_{timestamp}.json)"
    )

    args = parser.parse_args()

    # Execute command
    if args.command == "list-clades":
        list_clades(task_type=args.task_type)
    elif args.command == "show-clade":
        show_clade(args.clade_id, limit=args.limit)
    elif args.command == "agent-health":
        agent_health(task_type=args.task_type)
    elif args.command == "show-event":
        show_event(args.event_id)
    elif args.command == "export":
        export_events(output_file=args.output)
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
