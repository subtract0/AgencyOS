"""CLI interface for self-healing trigger management and monitoring.

This module provides command-line tools to:
- View current triggers and their thresholds
- Monitor self-healing system status
- Execute manual trigger checks
- Manage trigger configurations
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Add project root to path when running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.self_healing.orchestrator import (
    SelfHealingOrchestrator,
    run_self_healing_check,
    get_self_healing_status,
    get_self_healing_health
)
from tools.self_healing.trigger_framework import create_default_trigger_framework, TriggerType, TriggerSeverity
from tools.self_healing.action_registry import create_default_action_registry, ActionType, ActionPriority


def format_timestamp(timestamp_str: Optional[str]) -> str:
    """Format timestamp for display."""
    if not timestamp_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return timestamp_str


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def cmd_status(args) -> None:
    """Show self-healing system status."""
    try:
        if args.health:
            status = get_self_healing_health()
            if args.format == "json":
                print(json.dumps(status, indent=2))
                return

            print(f"Self-Healing System Health: {status['status'].upper()}")
            print(f"Telemetry Access: {'✓' if status['telemetry_healthy'] else '✗'}")
            print(f"Triggers Enabled: {status['triggers_enabled']}")
            print(f"Actions Available: {status['actions_available']}")

            if status['issues']:
                print("\nIssues Detected:")
                for issue in status['issues']:
                    print(f"  - {issue}")

            print(f"\nLast Check: {format_timestamp(status['last_check'])}")
            return

        status = get_self_healing_status(args.telemetry_dir)

        if args.format == "json":
            print(json.dumps(status, indent=2))
            return

        # Text format
        print(f"Self-Healing System Status")
        print(f"Running: {'Yes' if status['running'] else 'No'}")
        if status['start_time']:
            print(f"Started: {format_timestamp(status['start_time'])}")
        print(f"Uptime: {format_duration(status['uptime_seconds'])}")
        print(f"Monitoring Interval: {status['monitoring_interval']}s")
        print(f"Cycles Completed: {status['cycles_completed']}")
        print(f"Total Triggers Fired: {status['total_triggers_fired']}")
        print(f"Total Actions Executed: {status['total_actions_executed']}")

        trigger_status = status.get('trigger_framework_status', {})
        active_conditions = trigger_status.get('active_conditions', [])
        if active_conditions:
            print(f"\nActive Conditions: {', '.join(active_conditions)}")

    except Exception as e:
        print(f"Error getting status: {e}")
        sys.exit(1)


def cmd_triggers(args) -> None:
    """Show trigger configurations and status."""
    try:
        framework = create_default_trigger_framework()
        trigger_status = framework.get_trigger_status()

        if args.format == "json":
            print(json.dumps(trigger_status, indent=2))
            return

        triggers = trigger_status['triggers']
        active_conditions = trigger_status['active_conditions']

        print("Self-Healing Triggers Configuration")
        print("=" * 50)

        if not triggers:
            print("No triggers configured.")
            return

        # Group triggers by type
        by_type = {}
        for name, config in triggers.items():
            trigger_type = config['type']
            if trigger_type not in by_type:
                by_type[trigger_type] = []
            by_type[trigger_type].append((name, config))

        for trigger_type in TriggerType:
            type_triggers = by_type.get(trigger_type.value, [])
            if not type_triggers:
                continue

            print(f"\n{trigger_type.value.upper()} TRIGGERS:")
            print("-" * 30)

            for name, config in type_triggers:
                status_icon = "✓" if config['enabled'] else "✗"
                active_icon = "🔥" if name in active_conditions else "  "

                print(f"{active_icon} {status_icon} {name}")
                print(f"    Threshold: {config['threshold']}")
                print(f"    Target Agent: {config['target_agent']}")
                print(f"    Fired: {config['trigger_count']} times")
                print(f"    Last Triggered: {format_timestamp(config['last_triggered'])}")

                if config['cooldown_remaining'] > 0:
                    print(f"    Cooldown: {format_duration(config['cooldown_remaining'])}")

        if active_conditions:
            print(f"\nACTIVE CONDITIONS: {', '.join(active_conditions)}")

        constitutional_violations = trigger_status.get('constitutional_violations', [])
        if constitutional_violations:
            print(f"\nCONSTITUTIONAL VIOLATIONS: {len(constitutional_violations)}")
            for violation in constitutional_violations[-5:]:  # Show last 5
                print(f"  - {violation}")

    except Exception as e:
        print(f"Error getting trigger status: {e}")
        sys.exit(1)


def cmd_actions(args) -> None:
    """Show action registry configurations and status."""
    try:
        registry = create_default_action_registry()
        action_status = registry.get_action_status()

        if args.format == "json":
            print(json.dumps(action_status, indent=2))
            return

        actions = action_status['actions']

        print("Self-Healing Actions Registry")
        print("=" * 40)

        if not actions:
            print("No actions registered.")
            return

        # Group actions by type
        by_type = {}
        for name, config in actions.items():
            action_type = config['type']
            if action_type not in by_type:
                by_type[action_type] = []
            by_type[action_type].append((name, config))

        for action_type in ActionType:
            type_actions = by_type.get(action_type.value, [])
            if not type_actions:
                continue

            print(f"\n{action_type.value.upper()} ACTIONS:")
            print("-" * 30)

            for name, config in type_actions:
                auto_icon = "🤖" if config['auto_execute'] else "👤"
                priority_icon = {
                    'emergency': '🚨',
                    'critical': '🔴',
                    'high': '🟡',
                    'medium': '🔵',
                    'low': '⚪'
                }.get(config['priority'], '⚪')

                print(f"{auto_icon} {priority_icon} {name}")
                print(f"    Target Agent: {config['target_agent']}")
                print(f"    Priority: {config['priority']}")
                print(f"    Trigger Types: {', '.join(config['trigger_types'])}")
                print(f"    Executions: {config['execution_count']} (success rate: {config['success_rate']:.1%})")
                print(f"    Last Executed: {format_timestamp(config['last_executed'])}")
                print(f"    Max Concurrent: {config['max_concurrent']}")

        print(f"\nSUMMARY:")
        print(f"Active Executions: {action_status['active_executions']}")
        print(f"Total Executions: {action_status['total_executions']}")
        print(f"Total Successes: {action_status['total_successes']}")
        if action_status['total_executions'] > 0:
            overall_success_rate = action_status['total_successes'] / action_status['total_executions']
            print(f"Overall Success Rate: {overall_success_rate:.1%}")

    except Exception as e:
        print(f"Error getting action status: {e}")
        sys.exit(1)


def cmd_check(args) -> None:
    """Run a manual self-healing check."""
    try:
        print("Running self-healing check...")
        result = run_self_healing_check()

        if args.format == "json":
            print(json.dumps(result, indent=2))
            return

        if result['success']:
            print("✓ Self-healing check completed successfully")
            print(f"Triggers Evaluated: {result['triggers_evaluated']}")
            print(f"Triggers Fired: {result['triggers_fired']}")
            print(f"Actions Executed: {result['actions_executed']}")

            if result['triggers_fired'] > 0:
                print("\nTRIGGERED CONDITIONS:")
                for trigger in result['trigger_results']:
                    if trigger['triggered']:
                        print(f"  🔥 {trigger['name']} ({trigger['severity']}) - {trigger['message']}")

            if result['actions_executed'] > 0:
                print("\nEXECUTED ACTIONS:")
                for action in result['action_results']:
                    status_icon = "✓" if action['success'] else "✗"
                    print(f"  {status_icon} {action['name']} - {action['message']}")
                    if action['handoff_id']:
                        print(f"    Handoff ID: {action['handoff_id']}")

            if result['triggers_fired'] == 0:
                print("No issues detected - system operating normally")

        else:
            print(f"✗ Self-healing check failed: {result['error']}")
            sys.exit(1)

    except Exception as e:
        print(f"Error running self-healing check: {e}")
        sys.exit(1)


def cmd_history(args) -> None:
    """Show execution history."""
    try:
        registry = create_default_action_registry()
        history = registry.get_execution_history(limit=args.limit)

        if args.format == "json":
            print(json.dumps(history, indent=2))
            return

        if not history:
            print("No execution history available.")
            return

        print(f"Self-Healing Execution History (last {len(history)} entries)")
        print("=" * 60)

        for entry in history:
            status_icon = "✓" if entry['success'] else "✗"
            timestamp = format_timestamp(entry['timestamp'])

            print(f"{status_icon} {timestamp}")
            print(f"  Action: {entry['action_name']} ({entry['action_type']})")
            print(f"  Trigger: {entry['trigger_name']}")
            print(f"  Target: {entry['target_agent']}")
            print(f"  Duration: {entry['execution_time']:.2f}s")

            if entry['handoff_id']:
                print(f"  Handoff: {entry['handoff_id']}")

            if entry['error']:
                print(f"  Error: {entry['error']}")

            print()

    except Exception as e:
        print(f"Error getting execution history: {e}")
        sys.exit(1)


def cmd_enable_trigger(args) -> None:
    """Enable a specific trigger."""
    try:
        framework = create_default_trigger_framework()
        if framework.enable_trigger(args.trigger_name):
            print(f"✓ Enabled trigger: {args.trigger_name}")
        else:
            print(f"✗ Trigger not found: {args.trigger_name}")
            sys.exit(1)
    except Exception as e:
        print(f"Error enabling trigger: {e}")
        sys.exit(1)


def cmd_disable_trigger(args) -> None:
    """Disable a specific trigger."""
    try:
        framework = create_default_trigger_framework()
        if framework.disable_trigger(args.trigger_name):
            print(f"✓ Disabled trigger: {args.trigger_name}")
        else:
            print(f"✗ Trigger not found: {args.trigger_name}")
            sys.exit(1)
    except Exception as e:
        print(f"Error disabling trigger: {e}")
        sys.exit(1)


def cmd_clear_conditions(args) -> None:
    """Clear active conditions."""
    try:
        framework = create_default_trigger_framework()
        framework.clear_active_conditions()
        print("✓ Cleared all active conditions")
    except Exception as e:
        print(f"Error clearing conditions: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="agency self-healing",
        description="Self-healing trigger management and monitoring"
    )

    # Global options
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--telemetry-dir",
        help="Custom telemetry directory path"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument(
        "--health",
        action="store_true",
        help="Show health check instead of full status"
    )
    status_parser.set_defaults(func=cmd_status)

    # Triggers command
    triggers_parser = subparsers.add_parser("triggers", help="Show trigger configurations")
    triggers_parser.set_defaults(func=cmd_triggers)

    # Actions command
    actions_parser = subparsers.add_parser("actions", help="Show action configurations")
    actions_parser.set_defaults(func=cmd_actions)

    # Check command
    check_parser = subparsers.add_parser("check", help="Run manual self-healing check")
    check_parser.set_defaults(func=cmd_check)

    # History command
    history_parser = subparsers.add_parser("history", help="Show execution history")
    history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of entries to show"
    )
    history_parser.set_defaults(func=cmd_history)

    # Enable trigger command
    enable_parser = subparsers.add_parser("enable", help="Enable a trigger")
    enable_parser.add_argument("trigger_name", help="Name of trigger to enable")
    enable_parser.set_defaults(func=cmd_enable_trigger)

    # Disable trigger command
    disable_parser = subparsers.add_parser("disable", help="Disable a trigger")
    disable_parser.add_argument("trigger_name", help="Name of trigger to disable")
    disable_parser.set_defaults(func=cmd_disable_trigger)

    # Clear conditions command
    clear_parser = subparsers.add_parser("clear", help="Clear active conditions")
    clear_parser.set_defaults(func=cmd_clear_conditions)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()