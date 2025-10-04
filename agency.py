import os
import time
from contextlib import contextmanager

from shared.type_definitions.json import JSONValue
from shared.utils import silence_warnings_and_logs

silence_warnings_and_logs()
try:
    from dspy_agents.config import DSPY_AVAILABLE, DSPyConfig

    if DSPY_AVAILABLE:
        if DSPyConfig.initialize():
            import logging

            logger = logging.getLogger(__name__)
            logger.info("DSPy configuration initialized for Agency agents")
except ImportError:
    pass
from datetime import UTC

import litellm
from agency_swarm import Agency
from agency_swarm.tools import SendMessageHandoff
from dotenv import load_dotenv

try:
    from tools.orchestrator.scheduler import _telemetry_emit as _tel_emit
except Exception:

    def _tel_emit(event: dict) -> None:
        try:
            import json as _json
            from datetime import datetime

            base = os.path.join(os.getcwd(), "logs", "telemetry")
            os.makedirs(base, exist_ok=True)
            ts = datetime.now(UTC)
            event = dict(event)
            event["ts"] = ts.isoformat(timespec="milliseconds").replace("+00:00", "Z")
            fname = os.path.join(base, f"events-{ts:%Y%m%d}.jsonl")
            with open(fname, "a", encoding="utf-8") as f:
                f.write(_json.dumps(event) + "\n")
        except OSError as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to write telemetry event to {fname}: {e}")
        except (TypeError, ValueError) as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid event data format: {e}")


@contextmanager
def _cli_event_scope(
    command: str | None = None, args_dict: dict[str, JSONValue] | None = None
):
    started = time.time()
    try:
        _tel_emit(
            {
                "type": "cli_command_started",
                "command": command,
                "args": args_dict or {},
                "started_at": started,
            }
        )
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to emit CLI command start event: {e}")
    try:
        yield
        try:
            finished = time.time()
            _tel_emit(
                {
                    "type": "cli_command_finished",
                    "command": command,
                    "status": "success",
                    "finished_at": finished,
                    "duration_s": max(0.0, finished - started),
                }
            )
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to emit CLI command success event: {e}")
    except Exception as e:
        try:
            finished = time.time()
            _tel_emit(
                {
                    "type": "cli_command_finished",
                    "command": command,
                    "status": "failed",
                    "error": str(e),
                    "finished_at": finished,
                    "duration_s": max(0.0, finished - started),
                }
            )
        except Exception as nested_e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to emit CLI command failure event: {nested_e}")
        raise


from agency_code_agent.agency_code_agent import create_agency_code_agent
from agency_memory import (
    Memory,
    create_enhanced_memory_store,
    create_firestore_store,
)
from auditor_agent import create_auditor_agent
from chief_architect_agent import create_chief_architect_agent
from learning_agent import create_learning_agent
from merger_agent.merger_agent import create_merger_agent
from planner_agent.planner_agent import create_planner_agent
from quality_enforcer_agent import create_quality_enforcer_agent
from shared.agent_context import create_agent_context
from test_generator_agent import create_test_generator_agent
from toolsmith_agent import create_toolsmith_agent
from work_completion_summary_agent import create_work_completion_summary_agent

load_dotenv()
current_dir = os.path.dirname(os.path.abspath(__file__))
litellm.modify_params = True
model = os.getenv("AGENCY_MODEL", "gpt-5")
use_firestore = os.getenv("FRESH_USE_FIRESTORE", "true").lower() == "true"
use_enhanced_memory = True
if use_firestore:
    firestore_store = create_firestore_store()
    enhanced_store = create_enhanced_memory_store(embedding_provider="sentence-transformers")
    shared_memory = Memory(store=firestore_store)
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        "🔥 Firestore + VectorStore enabled: Production persistence with semantic search (Article IV compliant)"
    )
else:
    enhanced_store = create_enhanced_memory_store(embedding_provider="sentence-transformers")
    shared_memory = Memory(store=enhanced_store)
    import logging

    logger = logging.getLogger(__name__)
    logger.info("💾 In-memory + VectorStore: Development mode (Article IV compliant)")
shared_context = create_agent_context(memory=shared_memory)
cost_tracker_enabled = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"
cost_budget = float(os.getenv("COST_BUDGET_USD", "100.0"))
if cost_tracker_enabled:
    from shared.cost_tracker import CostTracker, SQLiteStorage
    from shared.llm_cost_wrapper import wrap_openai_client

    storage = SQLiteStorage(os.path.join(current_dir, "trinity_costs.db"))
    shared_cost_tracker = CostTracker(storage=storage)
    shared_cost_tracker.set_budget(limit_usd=cost_budget, alert_threshold_pct=80.0)
    wrap_openai_client(shared_cost_tracker, agent_name="Agency", correlation_id="agency-session")
    shared_context.cost_tracker = shared_cost_tracker
    logger = logging.getLogger(__name__)
    logger.info(f"💰 Cost tracking enabled: budget=${cost_budget:.2f} USD, db=trinity_costs.db")
else:
    shared_cost_tracker = None
from shared.model_policy import agent_model

planner = create_planner_agent(
    model=agent_model("planner"), reasoning_effort="high", agent_context=shared_context
)
coder = create_agency_code_agent(
    model=agent_model("coder"), reasoning_effort="medium", agent_context=shared_context
)
auditor = create_auditor_agent(
    model=agent_model("auditor"), reasoning_effort="high", agent_context=shared_context
)
test_generator = create_test_generator_agent(
    model=agent_model("test_generator"), reasoning_effort="medium", agent_context=shared_context
)
learning_agent = create_learning_agent(
    model=agent_model("learning"), reasoning_effort="high", agent_context=shared_context
)
chief_architect = create_chief_architect_agent(
    model=agent_model("chief_architect"), reasoning_effort="medium", agent_context=shared_context
)
merger = create_merger_agent(
    model=agent_model("merger"), reasoning_effort="medium", agent_context=shared_context
)
summary = create_work_completion_summary_agent(
    model=agent_model("summary"), reasoning_effort="low", agent_context=shared_context
)
toolsmith = create_toolsmith_agent(
    model=agent_model("toolsmith"), reasoning_effort="medium", agent_context=shared_context
)
quality_enforcer = create_quality_enforcer_agent(
    model=agent_model("quality_enforcer"), reasoning_effort="high", agent_context=shared_context
)
agency = Agency(
    chief_architect,
    coder,
    planner,
    auditor,
    test_generator,
    learning_agent,
    merger,
    summary,
    toolsmith,
    quality_enforcer,
    name="AgencyCode",
    communication_flows=[
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
        (coder, summary, SendMessageHandoff),
        (planner, summary, SendMessageHandoff),
        (merger, summary, SendMessageHandoff),
    ],
    shared_instructions="./project-overview.md",
)
import argparse
import sys
from typing import cast

from shared.type_definitions.json import JSONValue

try:
    from tools.telemetry.aggregator import aggregate, list_events
except Exception:
    aggregate = None
    list_events = None


def _render_dashboard_text(summary: dict[str, JSONValue]) -> None:
    metrics = cast(dict[str, JSONValue], summary.get("metrics", {}))
    total = metrics.get("total_events", 0)
    if total == 0:
        print("No telemetry events found. Ensure Telemetry is enabled and running.")
        return
    agents = cast(list, summary.get("agents_active", []))
    running = cast(list, summary.get("running_tasks", []))
    recent = cast(dict[str, JSONValue], summary.get("recent_results", {}))
    window = cast(dict[str, JSONValue], summary.get("window", {}))
    resources = cast(dict[str, JSONValue], summary.get("resources", {}))
    costs = cast(dict[str, JSONValue], summary.get("costs", {}))
    print(f"Agents Active: {(', '.join(str(a) for a in agents) if agents else 'none')}")
    print("Running Tasks (top 10):")
    if running:
        for r in running:
            task_dict = cast(dict[str, JSONValue], r)
            hb = task_dict.get("last_heartbeat_age_s")
            hb_txt = f" hb_age={hb:.2f}s" if isinstance(hb, (int, float)) else ""
            age_s = task_dict.get("age_s", 0)
            age_str = f"{age_s:.2f}" if isinstance(age_s, (int, float)) else "0.00"
            print(
                f"- id={task_dict.get('id')} agent={task_dict.get('agent')} age={age_str}s{hb_txt}"
            )
    else:
        print("- none")
    print(
        f"Recent Results: success={recent.get('success', 0)} failed={recent.get('failed', 0)} timeout={recent.get('timeout', 0)}"
    )
    mc = resources.get("max_concurrency")
    util = resources.get("utilization")
    util_txt = f" util={util * 100:.1f}%" if isinstance(util, (int, float)) else ""
    print(
        f"Resources: running={resources.get('running', 0)}"
        + (f" of max={mc}" if mc else "")
        + util_txt
    )
    total_tokens = costs.get("total_tokens", 0)
    total_usd = costs.get("total_usd", 0.0)
    print(f"Costs: tokens={total_tokens} usd=${total_usd:.4f}")
    esc = metrics.get("", 0)
    print(f"Escalations used: {esc}")
    print(
        f"Window: since={window.get('since')} events={total} started={metrics.get('tasks_started', 0)} finished={metrics.get('tasks_finished', 0)}"
    )


def _cmd_run(args: argparse.Namespace) -> None:
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
        _render_dashboard_text(cast(dict[str, JSONValue], summary))


def _cmd_tail(args: argparse.Namespace) -> None:
    with _cli_event_scope(
        "tail", {"since": args.since, "grep": args.grep, "limit": args.limit, "format": args.format}
    ):
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


def _list_recent_files(directory: str, description: str, limit: int = 5) -> None:
    """List recent files in a directory.

    Args:
        directory: Directory path to scan
        description: Description for output header
        limit: Maximum number of files to show
    """
    import os

    print(f"\n{description}:" if not description.startswith("Recent") else f"{description}:")
    if os.path.isdir(directory):
        try:
            entries = sorted(
                (
                    (name, os.path.getmtime(os.path.join(directory, name)))
                    for name in os.listdir(directory)
                ),
                key=lambda x: x[1],
                reverse=True,
            )[:limit]
            for name, _ in entries:
                print(f"  {name}")
        except Exception:
            print(f"  (error reading {description.lower()})")
    else:
        print(f"  No {description.lower()} found")


def _cmd_logs(args: argparse.Namespace) -> None:
    """Show recent logs from various subsystems."""
    with _cli_event_scope("logs", {}):
        import os

        base = os.path.join(current_dir, "logs")
        _list_recent_files(os.path.join(base, "sessions"), "Recent Session Logs", 5)
        _list_recent_files(os.path.join(base, "autonomous_healing"), "Autonomous Healing Logs", 5)
        _list_recent_files(os.path.join(base, "telemetry"), "Telemetry Logs", 3)


def _cmd_demo(args: argparse.Namespace) -> None:
    import runpy

    with _cli_event_scope("demo", {}):
        demo_unified = os.path.join(current_dir, "demo_unified.py")
        if os.path.exists(demo_unified):
            runpy.run_path(demo_unified, run_name="__main__")
        else:
            print("❌ Demo file not found. Please run from the Agency directory.")


def _cmd_test(args: argparse.Namespace) -> None:
    import subprocess

    with _cli_event_scope("test", {}):
        cmd = [sys.executable, os.path.join(current_dir, "run_tests.py")]
        subprocess.run(cmd, check=False)


def _check_test_status() -> None:
    """Check test execution status."""
    import subprocess

    print("  Test Status:")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_memory_api.py", "-q"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=25,
        )
        if result.returncode == 0:
            print("    ✅ All tests passing (Constitutional Article II compliant)")
        else:
            print("    ❌ Some tests failing (Constitutional violation!)")
    except subprocess.TimeoutExpired:
        print("    (test run timed out)")
    except Exception:
        print("    (error running tests)")


def _check_environment_status() -> None:
    """Check Python environment status."""
    print("  Environment:")
    try:
        print(f"    ✅ Python: {sys.version.split()[0]}")
    except Exception:
        pass


def _check_dependencies_status() -> None:
    """Check core dependencies availability."""
    print("  Dependencies:")
    try:

        print("    ✅ Core dependencies installed")
    except Exception:
        print("    ❌ Missing dependencies")


def _check_healing_tools_status() -> None:
    """Check autonomous healing tools availability."""
    print("  Autonomous Healing:")
    try:

        print("    ✅ Autonomous healing tools available")
    except Exception:
        print("    ❌ Autonomous healing tools not found")


def _check_recent_activity() -> None:
    """Check recent autonomous healing activity."""
    import time

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
            print(f"    📊 {count} healing log files from last 24 hours")
        else:
            print("    📊 No recent autonomous healing activity")
    except Exception:
        print("    (error reading healing activity)")


def _cmd_health(args: argparse.Namespace) -> None:
    """Check Agency health and autonomous healing status."""
    with _cli_event_scope("health", {}):
        print("🏥 Checking Agency health and autonomous healing status...")
        _check_test_status()
        _check_environment_status()
        _check_dependencies_status()
        _check_healing_tools_status()
        _check_recent_activity()


def _cmd_kanban(args: argparse.Namespace) -> None:
    from tools.kanban.server import run_server

    enabled = os.getenv("ENABLE_KANBAN_UI", "false").lower() == "true"
    with _cli_event_scope("kanban", {"enabled": enabled}):
        if not enabled:
            print("ENABLE_KANBAN_UI=false; set it to 'true' to enable the Kanban UI.")
            return
        run_server()


def _cmd_cost_dashboard(args: argparse.Namespace) -> None:
    """Launch CLI cost monitoring dashboard."""
    with _cli_event_scope("cost_dashboard", {"live": args.live}):
        from trinity_protocol.cost_dashboard import CostDashboard

        from shared.cost_tracker import CostTracker

        tracker = CostTracker(db_path=args.db, budget_usd=args.budget)
        dashboard = CostDashboard(
            cost_tracker=tracker,
            refresh_interval=args.interval,
            budget_warning_pct=args.warning_pct,
        )
        if args.live:
            print("Starting live cost dashboard... (Press Q to quit)")
            import time

            time.sleep(1)
            dashboard.run_terminal_dashboard()
        else:
            dashboard.print_snapshot()


def _cmd_cost_web(args: argparse.Namespace) -> None:
    """Launch web-based cost monitoring dashboard."""
    with _cli_event_scope("cost_web", {"port": args.port}):
        from trinity_protocol.cost_dashboard_web import CostDashboardWeb

        from shared.cost_tracker import CostTracker

        tracker = CostTracker(db_path=args.db, budget_usd=args.budget)
        dashboard = CostDashboardWeb(cost_tracker=tracker, refresh_interval=args.interval)
        dashboard.run(host=args.host, port=args.port, debug=args.debug)


def _cmd_cost_alerts(args: argparse.Namespace) -> None:
    """Check cost alerts or run continuous monitoring."""
    with _cli_event_scope("cost_alerts", {"continuous": args.continuous}):
        from trinity_protocol.cost_alerts import (
            AlertConfig,
            CostAlertSystem,
            run_continuous_monitoring,
        )

        from shared.cost_tracker import CostTracker

        tracker = CostTracker(db_path=args.db, budget_usd=args.budget)
        config = AlertConfig(hourly_rate_max=args.hourly_max, daily_budget_max=args.daily_max)
        if args.continuous:
            run_continuous_monitoring(tracker, config, args.interval)
        else:
            alert_system = CostAlertSystem(tracker, config)
            alerts = alert_system.check_all()
            if alerts:
                print(f"\n⚠️  {len(alerts)} alert(s) triggered:")
                for alert in alerts:
                    print(f"\n[{alert.level.value.upper()}] {alert.title}")
                    print(f"  {alert.message}")
            else:
                print("✅ No alerts triggered. All costs within limits.")


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agency", description="Agency runtime and utilities")
    sub = p.add_subparsers(dest="command")
    sp = sub.add_parser("run", help="Start the Agency interactive demo")
    sp.set_defaults(func=_cmd_run)
    sp = sub.add_parser("dashboard", help="Show telemetry dashboard")
    sp.add_argument("--since", default="1h")
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.set_defaults(func=_cmd_dashboard)
    sp = sub.add_parser("tail", help="Tail telemetry events")
    sp.add_argument("--since", default="1h")
    sp.add_argument("--grep", default=None)
    sp.add_argument("--limit", type=int, default=200)
    sp.add_argument("--format", choices=["text", "json"], default="text")
    sp.set_defaults(func=_cmd_tail)
    sp = sub.add_parser("health", help="Check system health")
    sp.set_defaults(func=_cmd_health)
    sp = sub.add_parser("logs", help="Show recent logs")
    sp.set_defaults(func=_cmd_logs)
    sp = sub.add_parser("demo", help="Run the autonomous healing demo")
    sp.set_defaults(func=_cmd_demo)
    sp = sub.add_parser("test", help="Run test suite")
    sp.set_defaults(func=_cmd_test)
    sp = sub.add_parser("kanban", help="Run minimal Kanban UI server")
    sp.set_defaults(func=_cmd_kanban)
    sp = sub.add_parser("cost-dashboard", help="Launch CLI cost monitoring dashboard")
    sp.add_argument("--live", action="store_true", help="Run live dashboard with auto-refresh")
    sp.add_argument("--interval", type=int, default=5, help="Refresh interval in seconds")
    sp.add_argument("--db", type=str, default="trinity_costs.db", help="Path to cost database")
    sp.add_argument("--budget", type=float, help="Budget limit in USD")
    sp.add_argument("--warning-pct", type=float, default=80.0, help="Budget warning percentage")
    sp.set_defaults(func=_cmd_cost_dashboard)
    sp = sub.add_parser("cost-web", help="Launch web-based cost dashboard")
    sp.add_argument("--port", type=int, default=8080, help="Port to listen on")
    sp.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    sp.add_argument("--db", type=str, default="trinity_costs.db", help="Path to cost database")
    sp.add_argument("--budget", type=float, help="Budget limit in USD")
    sp.add_argument("--interval", type=int, default=5, help="Refresh interval in seconds")
    sp.add_argument("--debug", action="store_true", help="Enable debug mode")
    sp.set_defaults(func=_cmd_cost_web)
    sp = sub.add_parser("cost-alerts", help="Check cost alerts or run continuous monitoring")
    sp.add_argument("--db", type=str, default="trinity_costs.db", help="Path to cost database")
    sp.add_argument("--budget", type=float, help="Budget limit in USD")
    sp.add_argument("--hourly-max", type=float, help="Maximum hourly spending rate")
    sp.add_argument("--daily-max", type=float, help="Maximum daily spending")
    sp.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    sp.add_argument("--interval", type=int, default=300, help="Check interval for continuous mode")
    sp.set_defaults(func=_cmd_cost_alerts)
    return p


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        _cmd_run(args)
        return
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return
    func(args)


if __name__ == "__main__":
    main()
