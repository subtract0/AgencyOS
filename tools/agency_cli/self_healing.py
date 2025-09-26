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
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from shared.type_definitions.json import JSONValue

# Add project root to path when running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Mock classes for missing modules
class TriggerType:
    def __init__(self, value: str):
        self.value = value

class TriggerSeverity:
    def __init__(self, value: str):
        self.value = value

class ActionType:
    def __init__(self, value: str):
        self.value = value

class ActionPriority:
    def __init__(self, value: str):
        self.value = value

# Mock functions for missing imports - these will return empty results
def run_self_healing_check() -> JSONValue:
    """Mock function for missing self-healing check."""
    return {
        "success": False,
        "error": "Self-healing modules not available",
        "triggers_evaluated": 0,
        "triggers_fired": 0,
        "actions_executed": 0,
        "trigger_results": [],
        "action_results": []
    }

def get_self_healing_status(telemetry_dir: Optional[str] = None) -> JSONValue:
    """Mock function for missing self-healing status."""
    return {
        "running": False,
        "start_time": None,
        "uptime_seconds": 0,
        "monitoring_interval": 60,
        "cycles_completed": 0,
        "total_triggers_fired": 0,
        "total_actions_executed": 0,
        "trigger_framework_status": {
            "active_conditions": []
        }
    }

def get_self_healing_health() -> JSONValue:
    """Mock function for missing self-healing health."""
    return {
        "status": "unavailable",
        "telemetry_healthy": False,
        "triggers_enabled": 0,
        "actions_available": 0,
        "issues": ["Self-healing modules not available"],
        "last_check": None
    }

class MockFramework:
    def get_trigger_status(self) -> JSONValue:
        return {
            "triggers": {},
            "active_conditions": [],
            "constitutional_violations": []
        }

    def enable_trigger(self, name: str) -> bool:
        return False

    def disable_trigger(self, name: str) -> bool:
        return False

    def clear_active_conditions(self) -> None:
        pass

class MockRegistry:
    def get_action_status(self) -> JSONValue:
        return {
            "actions": {},
            "active_executions": 0,
            "total_executions": 0,
            "total_successes": 0
        }

    def get_execution_history(self, limit: int = 20) -> List[JSONValue]:
        return []

def create_default_trigger_framework() -> MockFramework:
    return MockFramework()

def create_default_action_registry() -> MockRegistry:
    return MockRegistry()


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


def cmd_status(args: argparse.Namespace) -> None:
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


def cmd_triggers(args: argparse.Namespace) -> None:
    """Show trigger configurations and status."""
    try:
        framework = create_default_trigger_framework()
        trigger_status = framework.get_trigger_status()

        if args.format == "json":
            print(json.dumps(trigger_status, indent=2))
            return

        triggers = trigger_status.get('triggers', {})
        active_conditions = trigger_status.get('active_conditions', [])
        if not isinstance(active_conditions, list):
            active_conditions = []

        print("Self-Healing Triggers Configuration")
        print("=" * 50)

        if not triggers:
            print("No triggers configured.")
            return

        # Group triggers by type
        by_type: Dict[str, List[Tuple[str, JSONValue]]] = {}
        for name, config in triggers.items():
            if isinstance(config, dict):
                trigger_type = config.get('type')
                if isinstance(trigger_type, str):
                    if trigger_type not in by_type:
                        by_type[trigger_type] = []
                    by_type[trigger_type].append((name, config))

        # Mock trigger types for iteration
        mock_trigger_types = [TriggerType("error"), TriggerType("performance"), TriggerType("health")]
        for trigger_type in mock_trigger_types:
            type_triggers = by_type.get(trigger_type.value, [])
            if not type_triggers:
                continue

            print(f"\n{trigger_type.value.upper()} TRIGGERS:")
            print("-" * 30)

            for name, config in type_triggers:
                enabled = config.get('enabled', False)
                status_icon = "✓" if enabled else "✗"
                active_icon = "🔥" if name in active_conditions else "  "

                print(f"{active_icon} {status_icon} {name}")
                print(f"    Threshold: {config.get('threshold', 'N/A')}")
                print(f"    Target Agent: {config.get('target_agent', 'N/A')}")
                print(f"    Fired: {config.get('trigger_count', 0)} times")

                last_triggered = config.get('last_triggered')
                last_triggered_str = last_triggered if isinstance(last_triggered, str) else None
                print(f"    Last Triggered: {format_timestamp(last_triggered_str)}")

                cooldown_remaining = config.get('cooldown_remaining', 0)
                if isinstance(cooldown_remaining, (int, float)) and cooldown_remaining > 0:
                    print(f"    Cooldown: {format_duration(cooldown_remaining)}")

        if active_conditions:
            conditions_str = ', '.join(str(c) for c in active_conditions)
            print(f"\nACTIVE CONDITIONS: {conditions_str}")

        constitutional_violations = trigger_status.get('constitutional_violations', [])
        if isinstance(constitutional_violations, list) and constitutional_violations:
            print(f"\nCONSTITUTIONAL VIOLATIONS: {len(constitutional_violations)}")
            for violation in constitutional_violations[-5:]:  # Show last 5
                print(f"  - {violation}")

    except Exception as e:
        print(f"Error getting trigger status: {e}")
        sys.exit(1)


def cmd_actions(args: argparse.Namespace) -> None:
    """Show action registry configurations and status."""
    try:
        registry = create_default_action_registry()
        action_status = registry.get_action_status()

        if args.format == "json":
            print(json.dumps(action_status, indent=2))
            return

        actions = action_status.get('actions', {})

        print("Self-Healing Actions Registry")
        print("=" * 40)

        if not actions:
            print("No actions registered.")
            return

        # Group actions by type
        by_type: Dict[str, List[Tuple[str, JSONValue]]] = {}
        for name, config in actions.items():
            if isinstance(config, dict):
                action_type = config.get('type')
                if isinstance(action_type, str):
                    if action_type not in by_type:
                        by_type[action_type] = []
                    by_type[action_type].append((name, config))

        # Mock action types for iteration
        mock_action_types = [ActionType("fix"), ActionType("restart"), ActionType("alert")]
        for action_type in mock_action_types:
            type_actions = by_type.get(action_type.value, [])
            if not type_actions:
                continue

            print(f"\n{action_type.value.upper()} ACTIONS:")
            print("-" * 30)

            for name, config in type_actions:
                auto_execute = config.get('auto_execute', False)
                auto_icon = "🤖" if auto_execute else "👤"

                priority = config.get('priority', 'low')
                priority_str = priority if isinstance(priority, str) else 'low'
                priority_icon = {
                    'emergency': '🚨',
                    'critical': '🔴',
                    'high': '🟡',
                    'medium': '🔵',
                    'low': '⚪'
                }.get(priority_str, '⚪')

                print(f"{auto_icon} {priority_icon} {name}")
                print(f"    Target Agent: {config.get('target_agent', 'N/A')}")
                print(f"    Priority: {priority_str}")

                trigger_types = config.get('trigger_types', [])
                if isinstance(trigger_types, list):
                    trigger_types_str = ', '.join(str(t) for t in trigger_types)
                else:
                    trigger_types_str = 'N/A'
                print(f"    Trigger Types: {trigger_types_str}")
                execution_count = config.get('execution_count', 0)
                success_rate = config.get('success_rate', 0.0)
                if isinstance(success_rate, (int, float)):
                    print(f"    Executions: {execution_count} (success rate: {success_rate:.1%})")
                else:
                    print(f"    Executions: {execution_count} (success rate: N/A)")

                last_executed = config.get('last_executed')
                last_executed_str = last_executed if isinstance(last_executed, str) else None
                print(f"    Last Executed: {format_timestamp(last_executed_str)}")
                print(f"    Max Concurrent: {config.get('max_concurrent', 1)}")

        print(f"\nSUMMARY:")
        print(f"Active Executions: {action_status.get('active_executions', 0)}")
        total_executions = action_status.get('total_executions', 0)
        total_successes = action_status.get('total_successes', 0)
        print(f"Total Executions: {total_executions}")
        print(f"Total Successes: {total_successes}")
        if isinstance(total_executions, (int, float)) and total_executions > 0:
            if isinstance(total_successes, (int, float)):
                overall_success_rate = total_successes / total_executions
                print(f"Overall Success Rate: {overall_success_rate:.1%}")
            else:
                print(f"Overall Success Rate: N/A")

    except Exception as e:
        print(f"Error getting action status: {e}")
        sys.exit(1)


def cmd_check(args: argparse.Namespace) -> None:
    """Run a manual self-healing check."""
    try:
        print("Running self-healing check...")
        result = run_self_healing_check()

        if args.format == "json":
            print(json.dumps(result, indent=2))
            return

        success = result.get('success', False)
        if success:
            print("✓ Self-healing check completed successfully")
            print(f"Triggers Evaluated: {result.get('triggers_evaluated', 0)}")
            triggers_fired = result.get('triggers_fired', 0)
            actions_executed = result.get('actions_executed', 0)
            print(f"Triggers Fired: {triggers_fired}")
            print(f"Actions Executed: {actions_executed}")

            if triggers_fired > 0:
                print("\nTRIGGERED CONDITIONS:")
                trigger_results = result.get('trigger_results', [])
                if isinstance(trigger_results, list):
                    for trigger in trigger_results:
                        if isinstance(trigger, dict) and trigger.get('triggered'):
                            name = trigger.get('name', 'Unknown')
                            severity = trigger.get('severity', 'Unknown')
                            message = trigger.get('message', 'No message')
                            print(f"  🔥 {name} ({severity}) - {message}")

            if actions_executed > 0:
                print("\nEXECUTED ACTIONS:")
                action_results = result.get('action_results', [])
                if isinstance(action_results, list):
                    for action in action_results:
                        if isinstance(action, dict):
                            success = action.get('success', False)
                            status_icon = "✓" if success else "✗"
                            name = action.get('name', 'Unknown')
                            message = action.get('message', 'No message')
                            print(f"  {status_icon} {name} - {message}")

                            handoff_id = action.get('handoff_id')
                            if handoff_id:
                                print(f"    Handoff ID: {handoff_id}")

            if triggers_fired == 0:
                print("No issues detected - system operating normally")

        else:
            error = result.get('error', 'Unknown error')
            print(f"✗ Self-healing check failed: {error}")
            sys.exit(1)

    except Exception as e:
        print(f"Error running self-healing check: {e}")
        sys.exit(1)


def cmd_history(args: argparse.Namespace) -> None:
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
            if isinstance(entry, dict):
                success = entry.get('success', False)
                status_icon = "✓" if success else "✗"

                timestamp_val = entry.get('timestamp')
                timestamp_str = timestamp_val if isinstance(timestamp_val, str) else None
                timestamp = format_timestamp(timestamp_str)

                print(f"{status_icon} {timestamp}")
                print(f"  Action: {entry.get('action_name', 'Unknown')} ({entry.get('action_type', 'Unknown')})")
                print(f"  Trigger: {entry.get('trigger_name', 'Unknown')}")
                print(f"  Target: {entry.get('target_agent', 'Unknown')}")

                execution_time = entry.get('execution_time', 0)
                if isinstance(execution_time, (int, float)):
                    print(f"  Duration: {execution_time:.2f}s")
                else:
                    print(f"  Duration: N/A")

                handoff_id = entry.get('handoff_id')
                if handoff_id:
                    print(f"  Handoff: {handoff_id}")

                error = entry.get('error')
                if error:
                    print(f"  Error: {error}")

                print()

    except Exception as e:
        print(f"Error getting execution history: {e}")
        sys.exit(1)


def cmd_enable_trigger(args: argparse.Namespace) -> None:
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


def cmd_disable_trigger(args: argparse.Namespace) -> None:
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


def cmd_clear_conditions(args: argparse.Namespace) -> None:
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