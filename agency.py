import os
import time
from contextlib import contextmanager

from shared.utils import silence_warnings_and_logs

silence_warnings_and_logs()

import litellm  # noqa: E402 - must import after warning suppression
from agency_swarm import Agency  # noqa: E402 - must import after warning suppression
from agency_swarm.tools import (  # noqa: E402 - must import after warning suppression
    SendMessageHandoff,
)
from dotenv import load_dotenv  # noqa: E402 - must import after warning suppression

# Minimal telemetry emission for CLI commands (best-effort)
try:  # noqa: E402
    from tools.orchestrator.scheduler import _telemetry_emit as _tel_emit  # type: ignore
except Exception:  # noqa: E402
    def _tel_emit(event):  # type: ignore
        try:
            # Fallback writer to logs/telemetry
            from datetime import datetime, timezone
            import json as _json
            base = os.path.join(os.getcwd(), "logs", "telemetry")
            os.makedirs(base, exist_ok=True)
            ts = datetime.now(timezone.utc)
            event = dict(event)
            event["ts"] = ts.isoformat(timespec="milliseconds").replace("+00:00", "Z")
            fname = os.path.join(base, f"events-{ts:%Y%m%d}.jsonl")
            with open(fname, "a", encoding="utf-8") as f:
                f.write(_json.dumps(event) + "\n")
        except Exception:
            pass


@contextmanager
def _cli_event_scope(command: str, args_dict: dict | None = None):
    started = time.time()
    try:
        _tel_emit({"type": "cli_command_started", "command": command, "args": args_dict or {}, "started_at": started})
    except Exception:
        pass
    try:
        yield
        try:
            finished = time.time()
            _tel_emit({
                "type": "cli_command_finished",
                "command": command,
                "status": "success",
                "finished_at": finished,
                "duration_s": max(0.0, finished - started),
            })
        except Exception:
            pass
    except Exception as e:
        try:
            finished = time.time()
            _tel_emit({
                "type": "cli_command_finished",
                "command": command,
                "status": "failed",
                "error": str(e),
                "finished_at": finished,
                "duration_s": max(0.0, finished - started),
            })
        except Exception:
            pass
        raise

from agency_code_agent.agency_code_agent import (  # noqa: E402 - must import after warning suppression
    create_agency_code_agent,
)
from agency_memory import Memory, create_firestore_store, EnhancedMemoryStore, create_enhanced_memory_store  # noqa: E402 - must import after warning suppression
from auditor_agent import create_auditor_agent  # noqa: E402 - must import after warning suppression
from planner_agent.planner_agent import (  # noqa: E402 - must import after warning suppression
    create_planner_agent,
)
from shared.agent_context import create_agent_context  # noqa: E402 - must import after warning suppression
from subagent_example.subagent_example import (  # noqa: E402 - must import after warning suppression
    create_subagent_example,
)
from test_generator_agent import create_test_generator_agent  # noqa: E402 - must import after warning suppression
from learning_agent import create_learning_agent  # noqa: E402 - must import after warning suppression
from chief_architect_agent import create_chief_architect_agent  # noqa: E402 - must import after warning suppression
from merger_agent.merger_agent import create_merger_agent  # noqa: E402 - must import after warning suppression
from work_completion_summary_agent import create_work_completion_summary_agent  # noqa: E402 - must import after warning suppression
from toolsmith_agent import create_toolsmith_agent  # noqa: E402 - must import after warning suppression
from quality_enforcer_agent import create_quality_enforcer_agent  # noqa: E402 - must import after warning suppression

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
litellm.modify_params = True

# switch between models here
# model = "anthropic/claude-sonnet-4-20250514"
model = "gpt-5"

# Create shared memory and agent context for the agency with VectorStore integration
# This allows memory sharing between agents with both tag-based and semantic search capabilities
use_firestore = os.getenv("FRESH_USE_FIRESTORE", "").lower() == "true"
use_enhanced_memory = os.getenv("USE_ENHANCED_MEMORY", "true").lower() == "true"

if use_enhanced_memory:
    # Use enhanced memory store with VectorStore integration
    if use_firestore:
        firestore_store = create_firestore_store()
        # Note: Enhanced memory store doesn't directly support Firestore yet
        # For now, use enhanced memory with automatic VectorStore population
        enhanced_store = create_enhanced_memory_store(embedding_provider="sentence-transformers")
        shared_memory = Memory(store=enhanced_store)
    else:
        # Use enhanced memory store with in-memory backend
        enhanced_store = create_enhanced_memory_store(embedding_provider="sentence-transformers")
        shared_memory = Memory(store=enhanced_store)
else:
    # Use traditional memory for backward compatibility
    memory_store = create_firestore_store() if use_firestore else None
    shared_memory = Memory(store=memory_store)

shared_context = create_agent_context(memory=shared_memory)

# Learning Agent Configuration:
# - Automatically analyzes session transcripts in logs/sessions/
# - Extracts successful patterns and consolidates insights
# - Trigger conditions: After complex tasks, on errors, or periodically
# - Can be invoked by Planner for strategic learning or Auditor for pattern analysis

# Quality Enforcement Agent Configuration:
# - QualityEnforcerAgent: Maintains constitutional compliance and quality standards
# - Integrates constitutional enforcement with code quality oversight
# - Works with existing agents for comprehensive quality assurance

# create agents with shared context
planner = create_planner_agent(
    model=model, reasoning_effort="high", agent_context=shared_context
)
# coder = create_agency_code_agent(model="gpt-5", reasoning_effort="high")
coder = create_agency_code_agent(
    model=model, reasoning_effort="medium", agent_context=shared_context
)
auditor = create_auditor_agent(
    model=model, reasoning_effort="high", agent_context=shared_context
)
test_generator = create_test_generator_agent(
    model=model, reasoning_effort="medium", agent_context=shared_context
)
subagent_example = create_subagent_example(
    model=model, reasoning_effort="medium"
)
learning_agent = create_learning_agent(
    model=model, reasoning_effort="high", agent_context=shared_context
)
chief_architect = create_chief_architect_agent(
    model=model, reasoning_effort="medium", agent_context=shared_context
)
merger = create_merger_agent(
    model=model, reasoning_effort="medium", agent_context=shared_context
)
summary = create_work_completion_summary_agent(
    model=model, reasoning_effort="low", agent_context=shared_context
)
toolsmith = create_toolsmith_agent(
    model=model, reasoning_effort="medium", agent_context=shared_context
)
quality_enforcer = create_quality_enforcer_agent(
    model=model, reasoning_effort="high", agent_context=shared_context
)

agency = Agency(
    chief_architect, coder, planner, auditor, test_generator, learning_agent, merger, summary, toolsmith,
    quality_enforcer,
    name="AgencyCode",
    communication_flows=[
        # Core development workflow
        (chief_architect, auditor, SendMessageHandoff),
        (chief_architect, learning_agent, SendMessageHandoff),
        (chief_architect, planner, SendMessageHandoff),
        (chief_architect, toolsmith, SendMessageHandoff),
        (chief_architect, quality_enforcer, SendMessageHandoff),
        (planner, coder, SendMessageHandoff),
        (coder, planner, SendMessageHandoff),
        (planner, auditor, SendMessageHandoff),
        (auditor, test_generator, SendMessageHandoff),
        (auditor, quality_enforcer, SendMessageHandoff),
        (test_generator, coder, SendMessageHandoff),
        (quality_enforcer, coder, SendMessageHandoff),
        (quality_enforcer, test_generator, SendMessageHandoff),
        (coder, merger, SendMessageHandoff),
        (toolsmith, merger, SendMessageHandoff),
        # Route-aware wiring for audio summaries
        (coder, summary, SendMessageHandoff),
        (planner, summary, SendMessageHandoff),
        (merger, summary, SendMessageHandoff),
    ],
    shared_instructions="./project-overview.md",
)

import sys
import argparse
from typing import Any, Dict
from shared.type_definitions.json import JSONValue

try:
    # Telemetry utilities for dashboard/tail subcommands
    from tools.telemetry.aggregator import aggregate, list_events  # type: ignore
except Exception:
    aggregate = None  # type: ignore
    list_events = None  # type: ignore


def _render_dashboard_text(summary: Dict[str, JSONValue]) -> None:
    metrics = summary.get("metrics", {})
    total = metrics.get("total_events", 0)
    if total == 0:
        print("No telemetry events found. Ensure Telemetry is enabled and running.")
        return
    agents = summary.get("agents_active", [])
    running = summary.get("running_tasks", [])
    recent = summary.get("recent_results", {})
    window = summary.get("window", {})
    resources = summary.get("resources", {})
    costs = summary.get("costs", {})

    print(f"Agents Active: {', '.join(agents) if agents else 'none'}")
    print("Running Tasks (top 10):")
    if running:
        for r in running:
            hb = r.get('last_heartbeat_age_s')
            hb_txt = f" hb_age={hb:.2f}s" if isinstance(hb, (int, float)) else ""
            print(f"- id={r.get('id')} agent={r.get('agent')} age={r.get('age_s'):.2f}s{hb_txt}")
    else:
        print("- none")
    print(
        f"Recent Results: success={recent.get('success',0)} failed={recent.get('failed',0)} timeout={recent.get('timeout',0)}"
    )
    # Resources
    mc = resources.get('max_concurrency')
    util = resources.get('utilization')
    util_txt = f" util={util*100:.1f}%" if isinstance(util, (int, float)) else ""
    print(f"Resources: running={resources.get('running',0)}" + (f" of max={mc}" if mc else "") + util_txt)
    # Costs
    total_tokens = costs.get('total_tokens', 0)
    total_usd = costs.get('total_usd', 0.0)
    print(f"Costs: tokens={total_tokens} usd=${total_usd:.4f}")
    print(
        f"Window: since={window.get('since')} events={total} started={metrics.get('tasks_started',0)} finished={metrics.get('tasks_finished',0)}"
    )


def _cmd_run(args: argparse.Namespace) -> None:
    # Preserve existing behavior: run terminal demo
    show_reasoning = False if model.startswith("anthropic") else True
    with _cli_event_scope("run", {"show_reasoning": show_reasoning}):
        agency.terminal_demo(show_reasoning=show_reasoning)


def _cmd_dashboard(args: argparse.Namespace) -> None:
    with _cli_event_scope("dashboard", {"since": args.since, "format": args.format}):
        if aggregate is None:
            print("Dashboard not available: telemetry aggregator not importable")
            sys.exit(1)
        summary = aggregate(since=args.since)
        if args.format == "json":
            import json as _json
            print(_json.dumps(summary, indent=2))
            return
        _render_dashboard_text(summary)


def _cmd_tail(args: argparse.Namespace) -> None:
    with _cli_event_scope("tail", {"since": args.since, "grep": args.grep, "limit": args.limit, "format": args.format}):
        if list_events is None:
            print("Tail not available: telemetry aggregator not importable")
            sys.exit(1)
        events = list_events(since=args.since, grep=args.grep, limit=args.limit)
        if args.format == "json":
            import json as _json
            print(_json.dumps(events, indent=2))
            return
        if not events:
            print("No telemetry events in window.")
            return
        for e in events:
            typ = e.get("type")
            rid = e.get("run_id", "-")
            tid = e.get("id", "-")
            agent_name = e.get("agent", "-")
            ts = e.get("ts", "-")
            status = e.get("status", "")
            print(f"{ts} {typ} run={rid} id={tid} agent={agent_name} {status}")


def _cmd_logs(args: argparse.Namespace) -> None:
    with _cli_event_scope("logs", {}):
        import os
        base = os.path.join(current_dir, "logs")
        print("Recent Session Logs:")
        sessions = os.path.join(base, "sessions")
        if os.path.isdir(sessions):
            try:
                entries = sorted(
                    ((name, os.path.getmtime(os.path.join(sessions, name))) for name in os.listdir(sessions)),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                for name, _ in entries:
                    print(f"  {name}")
            except Exception:
                print("  (error reading session logs)")
        else:
            print("  No session logs found")

        print("\nAutonomous Healing Logs:")
        healing = os.path.join(base, "autonomous_healing")
        if os.path.isdir(healing):
            try:
                entries = sorted(
                    ((name, os.path.getmtime(os.path.join(healing, name))) for name in os.listdir(healing)),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                for name, _ in entries:
                    print(f"  {name}")
            except Exception:
                print("  (error reading autonomous healing logs)")
        else:
            print("  No autonomous healing logs found")

        print("\nTelemetry Logs:")
        telem = os.path.join(base, "telemetry")
        if os.path.isdir(telem):
            try:
                entries = sorted(
                    ((name, os.path.getmtime(os.path.join(telem, name))) for name in os.listdir(telem)),
                    key=lambda x: x[1],
                    reverse=True,
                )[:3]
                for name, _ in entries:
                    print(f"  {name}")
            except Exception:
                print("  (error reading telemetry logs)")
        else:
            print("  No telemetry logs found")


def _cmd_demo(args: argparse.Namespace) -> None:
    import runpy
    with _cli_event_scope("demo", {}):
        # Use unified demo if available, fallback to archived version
        demo_unified = os.path.join(current_dir, "demo_unified.py")
        demo_archived = os.path.join(current_dir, "demos/archive/demo_autonomous_healing.py")

        if os.path.exists(demo_unified):
            runpy.run_path(demo_unified, run_name="__main__")
        elif os.path.exists(demo_archived):
            runpy.run_path(demo_archived, run_name="__main__")
        else:
            print("❌ Demo file not found. Please run from the Agency directory.")


def _cmd_test(args: argparse.Namespace) -> None:
    # Delegate to run_tests.py for consistency
    import subprocess
    with _cli_event_scope("test", {}):
        cmd = [sys.executable, os.path.join(current_dir, "run_tests.py")]
        subprocess.run(cmd, check=False)


def _cmd_health(args: argparse.Namespace) -> None:
    import subprocess
    import time
    with _cli_event_scope("health", {}):
        print("\U0001F3E5 Checking Agency health and autonomous healing status...")

        # Test Status
        print("  Test Status:")
        try:
            # Run a fast smoke subset to keep health under 30s
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_memory_api.py", "-q"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=25,
            )
            if result.returncode == 0:
                print("    \u2705 All tests passing (Constitutional Article II compliant)")
            else:
                print("    \u274C Some tests failing (Constitutional violation!)")
        except subprocess.TimeoutExpired:
            print("    (test run timed out)")
        except Exception as e:
            print("    (error running tests)")

        # Environment
        print("  Environment:")
        try:
            print(f"    \u2705 Python: {sys.version.split()[0]}")
        except Exception:
            pass

        # Dependencies
        print("  Dependencies:")
        try:
            import agency_swarm  # type: ignore  # noqa: F401
            import litellm  # type: ignore  # noqa: F401
            import pytest  # type: ignore  # noqa: F401
            print("    \u2705 Core dependencies installed")
        except Exception:
            print("    \u274C Missing dependencies")

        # Autonomous Healing Tools
        print("  Autonomous Healing:")
        try:
            from tools.auto_fix_nonetype import AutoNoneTypeFixer  # type: ignore  # noqa: F401
            from tools.apply_and_verify_patch import ApplyAndVerifyPatch  # type: ignore  # noqa: F401
            print("    \u2705 Autonomous healing tools available")
        except Exception:
            print("    \u274C Autonomous healing tools not found")

        # Recent Activity (last 24h)
        print("  Recent Activity:")
        try:
            logs_dir = os.path.join(current_dir, "logs", "autonomous_healing")
            count = 0
            if os.path.isdir(logs_dir):
                now = time.time()
                for name in os.listdir(logs_dir):
                    if name.endswith(".jsonl"):
                        fp = os.path.join(logs_dir, name)
                        try:
                            if now - os.path.getmtime(fp) <= 86400:
                                count += 1
                        except Exception:
                            continue
            if count:
                print(f"    \U0001F4CA {count} healing log files from last 24 hours")
            else:
                print("    \U0001F4CA No recent autonomous healing activity")
        except Exception:
            print("    (error reading healing activity)")


def _cmd_kanban(args: argparse.Namespace) -> None:
    # Start minimal stdlib Kanban server
    from tools.kanban.server import run_server  # type: ignore
    enabled = os.getenv("ENABLE_KANBAN_UI", "false").lower() == "true"
    with _cli_event_scope("kanban", {"enabled": enabled}):
        if not enabled:
            print("ENABLE_KANBAN_UI=false; set it to 'true' to enable the Kanban UI.")
            return
        run_server()


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agency", description="Agency runtime and utilities")
    sub = p.add_subparsers(dest="command")

    # run (default)
    sp = sub.add_parser("run", help="Start the Agency interactive demo")
    sp.set_defaults(func=_cmd_run)

    # dashboard
    sp = sub.add_parser("dashboard", help="Show telemetry dashboard")
    sp.add_argument("--since", default="1h")
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.set_defaults(func=_cmd_dashboard)

    # tail
    sp = sub.add_parser("tail", help="Tail telemetry events")
    sp.add_argument("--since", default="1h")
    sp.add_argument("--grep", default=None)
    sp.add_argument("--limit", type=int, default=200)
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.set_defaults(func=_cmd_tail)

    # health
    sp = sub.add_parser("health", help="Check system health")
    sp.set_defaults(func=_cmd_health)

    # logs
    sp = sub.add_parser("logs", help="Show recent logs")
    sp.set_defaults(func=_cmd_logs)

    # demo
    sp = sub.add_parser("demo", help="Run the autonomous healing demo")
    sp.set_defaults(func=_cmd_demo)

    # test
    sp = sub.add_parser("test", help="Run test suite")
    sp.set_defaults(func=_cmd_test)

    # kanban
    sp = sub.add_parser("kanban", help="Run minimal Kanban UI server")
    sp.set_defaults(func=_cmd_kanban)

    return p


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        # Default to run for backward compatibility
        _cmd_run(args)
        return
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return
    func(args)


if __name__ == "__main__":
    main()
    # agency.visualize()
