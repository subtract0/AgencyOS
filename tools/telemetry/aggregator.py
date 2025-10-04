"""Minimal telemetry aggregator to power `agency.py dashboard` and `tail`.

- Reads JSONL events from logs/telemetry/events-*.jsonl
- Provides list_events() for raw event tailing
- Provides aggregate() for a summary used by the text dashboard

Safe by default:
- Works even if telemetry dir or files are missing
- Ignores malformed lines
- Returns conservative defaults for unknown metrics
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from shared.models.telemetry import (
    AgentMetrics,
    CostInfo,
    DashboardSummary,
    MetricsInfo,
    ResourceInfo,
    SystemHealth,
    TaskInfo,
    TelemetryMetrics,
    WindowInfo,
)
from shared.type_definitions.json import JSONValue

# ------------------------
# Helpers (also used by enhanced_aggregator)
# ------------------------


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _telemetry_dir(telemetry_dir: str | None = None) -> Path:
    if telemetry_dir:
        return Path(telemetry_dir)
    return _project_root() / "logs" / "telemetry"


def _iso_now() -> datetime:
    return datetime.now(UTC)


def _parse_iso(ts: str) -> datetime | None:
    try:
        # Support 'Z' suffix (UTC)
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError) as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to parse ISO timestamp '{ts}': {e}")
        return None
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error parsing timestamp '{ts}': {e}")
        return None


def _parse_since(since: str) -> datetime:
    """Parse since window like '15m', '1h', '24h', '7d'. Defaults to 1h on errors."""
    now = _iso_now()
    try:
        s = since.strip().lower()
        if s.endswith("m"):
            mins = int(s[:-1])
            return now - timedelta(minutes=mins)
        if s.endswith("h"):
            hrs = int(s[:-1])
            return now - timedelta(hours=hrs)
        if s.endswith("d"):
            days = int(s[:-1])
            return now - timedelta(days=days)
        # bare number -> hours
        hrs = int(s)
        return now - timedelta(hours=hrs)
    except Exception:
        return now - timedelta(hours=1)


# ------------------------
# Event ingestion
# ------------------------


def _iter_event_files(base_dir: Path) -> Iterable[Path]:
    if not base_dir.exists():
        return []
    # Prefer recent files by modification time
    files = sorted(base_dir.glob("events-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=False)
    return files


def _load_events(
    since_dt: datetime, telemetry_dir: str | None = None, limit: int | None = None
) -> list[dict[str, JSONValue]]:
    base = _telemetry_dir(telemetry_dir)
    events: list[dict[str, JSONValue]] = []

    for fp in _iter_event_files(base):
        try:
            with fp.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    ts = ev.get("ts")
                    if not isinstance(ts, str):
                        continue
                    dt = _parse_iso(ts)
                    if dt is None:
                        continue
                    if dt.tzinfo is None:
                        # Assume UTC if missing tz
                        dt = dt.replace(tzinfo=UTC)
                    if dt < since_dt:
                        continue
                    ev["_dt"] = dt
                    events.append(ev)
        except Exception:
            # Skip file if unreadable
            continue

    # Sort by timestamp ascending
    def get_dt(e: dict[str, JSONValue]) -> datetime:
        dt_val = e.get("_dt", _iso_now())
        return dt_val if isinstance(dt_val, datetime) else _iso_now()

    events.sort(key=get_dt)

    if limit is not None and len(events) > limit:
        events = events[-limit:]
    return events


# ------------------------
# Public API
# ------------------------


def list_events(
    since: str = "1h",
    grep: str | None = None,
    limit: int = 200,
    telemetry_dir: str | None = None,
) -> list[dict[str, JSONValue]]:
    """Return recent events within window.

    Args:
        since: Time window (e.g., '15m', '1h', '24h', '7d')
        grep: Optional substring filter (case-insensitive) against the JSON line
        limit: Max number of events to return (tail)
        telemetry_dir: Optional override directory for telemetry
    """
    since_dt = _parse_since(since)
    events = _load_events(since_dt, telemetry_dir=telemetry_dir, limit=None)

    if grep:
        g = grep.lower()
        filtered: list[dict[str, JSONValue]] = []
        for ev in events:
            try:
                s = json.dumps(ev, default=str).lower()
                if g in s:
                    filtered.append(ev)
            except Exception:
                continue
        events = filtered

    if limit is not None and len(events) > limit:
        events = events[-limit:]

    # Remove helper field before returning
    for ev in events:
        ev.pop("_dt", None)
    return events


@dataclass
class _EventProcessingContext:
    """Context object to hold state during event processing."""

    total_events: int
    tasks_started: int = 0
    tasks_finished: int = 0
    recent_results: dict[str, int] = None
    agents_active: list[str] = None
    escalations_used: int = 0
    tasks: dict[str, dict[str, JSONValue]] = None
    max_concurrency: int | None = None
    latest_orchestrator_ts: datetime | None = None
    total_tokens: int = 0
    total_usd: float = 0.0

    def __post_init__(self):
        if self.recent_results is None:
            self.recent_results = {"success": 0, "failed": 0, "timeout": 0}
        if self.agents_active is None:
            self.agents_active = []
        if self.tasks is None:
            self.tasks = {}


def _process_orchestrator_event(ev: dict[str, JSONValue], ctx: _EventProcessingContext) -> None:
    """Process orchestrator_started event to track max concurrency."""
    ts = ev.get("ts")
    dt = _parse_iso(ts) if isinstance(ts, str) else None
    if dt and (ctx.latest_orchestrator_ts is None or dt > ctx.latest_orchestrator_ts):
        ctx.latest_orchestrator_ts = dt
        mc_val = ev.get("max_concurrency", ctx.max_concurrency or 0)
        ctx.max_concurrency = (
            int(mc_val) if isinstance(mc_val, (int, float)) else ctx.max_concurrency
        )


def _process_task_started_event(
    ev: dict[str, JSONValue], ctx: _EventProcessingContext, now: datetime
) -> None:
    """Process task_started event to track running tasks."""
    ctx.tasks_started += 1
    tid = str(ev.get("id")) if ev.get("id") is not None else None
    if not tid:
        return

    agent = ev.get("agent")
    started_at = ev.get("started_at")
    dt = None
    if isinstance(started_at, (int, float)):
        try:
            dt = datetime.fromtimestamp(float(started_at), tz=UTC)
        except Exception:
            dt = None
    if dt is None:
        ts = ev.get("ts")
        dt = _parse_iso(ts) if isinstance(ts, str) else now

    ctx.tasks[tid] = {
        "id": tid,
        "agent": agent or "-",
        "started_dt": dt or now,
        "last_hb_dt": None,
        "finished": False,
    }


def _process_heartbeat_event(
    ev: dict[str, JSONValue], ctx: _EventProcessingContext, now: datetime
) -> None:
    """Process heartbeat event to update task heartbeat timestamps."""
    tid = str(ev.get("id")) if ev.get("id") is not None else None
    if tid and tid in ctx.tasks:
        ts = ev.get("ts")
        hb_dt = _parse_iso(ts) if isinstance(ts, str) else None
        ctx.tasks[tid]["last_hb_dt"] = hb_dt or now


def _process_task_finished_event(ev: dict[str, JSONValue], ctx: _EventProcessingContext) -> None:
    """Process task_finished event and accumulate costs."""
    ctx.tasks_finished += 1
    status = str(ev.get("status", "")).lower()
    if status in ctx.recent_results:
        ctx.recent_results[status] += 1

    tid = str(ev.get("id")) if ev.get("id") is not None else None
    if tid and tid in ctx.tasks:
        ctx.tasks[tid]["finished"] = True

    # Cost accounting if present
    usage = ev.get("usage")
    if isinstance(usage, dict):
        tokens = usage.get("total_tokens")
        try:
            if tokens is not None and isinstance(tokens, (int, float)):
                ctx.total_tokens += int(tokens)
        except (ValueError, OverflowError) as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid token count in usage data: {tokens}, error: {e}")
        # If cost provided, accumulate
        cost = usage.get("total_usd") or ev.get("cost_usd")
        try:
            if cost is not None and isinstance(cost, (int, float)):
                ctx.total_usd += float(cost)
        except (ValueError, OverflowError) as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid cost value in usage data: {cost}, error: {e}")


def _process_events(events: list[dict[str, JSONValue]]) -> _EventProcessingContext:
    """Process all events and return aggregated context."""
    ctx = _EventProcessingContext(total_events=len(events))
    now = _iso_now()

    for ev in events:
        typ = ev.get("type")
        agent = ev.get("agent")
        if agent and isinstance(agent, str) and agent not in ctx.agents_active:
            ctx.agents_active.append(agent)

        if typ == "orchestrator_started":
            _process_orchestrator_event(ev, ctx)
        elif typ == "task_started":
            _process_task_started_event(ev, ctx, now)
        elif typ == "heartbeat":
            _process_heartbeat_event(ev, ctx, now)
        elif typ == "escalation_used":
            ctx.escalations_used += 1
        elif typ == "task_finished":
            _process_task_finished_event(ev, ctx)

    return ctx


def _build_running_tasks(tasks: dict[str, dict[str, JSONValue]], now: datetime) -> list[TaskInfo]:
    """Build list of running tasks with age and heartbeat information."""
    running_tasks: list[TaskInfo] = []

    for t in tasks.values():
        if t.get("finished"):
            continue

        started_dt_val = t.get("started_dt", now)
        started_dt: datetime = started_dt_val if isinstance(started_dt_val, datetime) else now
        last_hb_dt_val = t.get("last_hb_dt")
        last_hb_dt: datetime | None = (
            last_hb_dt_val if isinstance(last_hb_dt_val, datetime) else None
        )

        age_s = max(0.0, (now - started_dt).total_seconds())
        hb_age_s = (now - last_hb_dt).total_seconds() if isinstance(last_hb_dt, datetime) else None

        running_tasks.append(
            TaskInfo(
                id=str(t.get("id", "-")),
                agent=str(t.get("agent", "-")),
                age_s=age_s,
                last_heartbeat_age_s=hb_age_s,
            )
        )

    # Sort by age (oldest first) and cap at 10
    running_tasks.sort(key=lambda r: r.age_s, reverse=True)
    return running_tasks[:10]


def _calculate_resource_utilization(
    running_count: int, max_concurrency: int | None
) -> float | None:
    """Calculate resource utilization percentage."""
    try:
        if max_concurrency and max_concurrency > 0:
            return min(1.0, running_count / float(max_concurrency))
    except Exception:
        pass
    return None


def _build_system_health(
    ctx: _EventProcessingContext, since_dt: datetime, now: datetime
) -> SystemHealth:
    """Build SystemHealth object from processing context."""
    status = (
        "healthy"
        if ctx.recent_results.get("failed", 0) < ctx.recent_results.get("success", 0)
        else "degraded"
    )
    return SystemHealth(
        status=status,
        total_events=ctx.total_events,
        error_count=ctx.recent_results.get("failed", 0),
        active_agents=ctx.agents_active,
        uptime_seconds=(now - since_dt).total_seconds(),
    )


def _build_agent_metrics(agents_active: list[str]) -> dict[str, AgentMetrics]:
    """Build agent metrics dictionary for active agents."""
    agent_metrics_dict: dict[str, AgentMetrics] = {}
    for agent in agents_active:
        agent_metrics_dict[agent] = AgentMetrics(
            agent_id=agent,
            total_invocations=0,  # Would need event tracking
            successful_invocations=0,
            failed_invocations=0,
        )
    return agent_metrics_dict


def _build_dashboard_summary(
    telemetry_metrics: TelemetryMetrics,
    ctx: _EventProcessingContext,
    running_tasks: list[TaskInfo],
    since: str,
) -> DashboardSummary:
    """Build dashboard summary with proper Pydantic models."""
    running_count = len(running_tasks)
    util = _calculate_resource_utilization(running_count, ctx.max_concurrency)

    return DashboardSummary(
        # TelemetryMetrics fields
        period_start=telemetry_metrics.period_start,
        period_end=telemetry_metrics.period_end,
        total_events=telemetry_metrics.total_events,
        events_by_type=telemetry_metrics.events_by_type,
        events_by_severity=telemetry_metrics.events_by_severity,
        agent_metrics=telemetry_metrics.agent_metrics,
        system_health=telemetry_metrics.system_health,
        top_errors=telemetry_metrics.top_errors,
        slowest_operations=telemetry_metrics.slowest_operations,
        # Dashboard-specific fields
        agents_active=ctx.agents_active,
        running_tasks=running_tasks,
        recent_results=ctx.recent_results,
        resources=ResourceInfo(
            max_concurrency=ctx.max_concurrency,
            running=running_count,
            utilization=util,
        ),
        costs=CostInfo(
            total_tokens=ctx.total_tokens,
            total_usd=ctx.total_usd,
        ),
        window=WindowInfo(
            since=since,
            events=ctx.total_events,
            tasks_started=ctx.tasks_started,
            tasks_finished=ctx.tasks_finished,
        ),
        metrics=MetricsInfo(
            total_events=ctx.total_events,
            tasks_started=ctx.tasks_started,
            tasks_finished=ctx.tasks_finished,
            escalations_used=ctx.escalations_used,
        ),
    )


def aggregate(since: str = "1h", telemetry_dir: str | None = None) -> DashboardSummary:
    """Aggregate telemetry for dashboard.

    Returns a summary dict with keys consumed by agency._render_dashboard_text:
    - metrics.total_events
    - agents_active (list)
    - running_tasks (list of {id, agent, age_s, last_heartbeat_age_s})
    - recent_results ({success, failed, timeout})
    - resources ({max_concurrency, running, utilization})
    - costs ({total_tokens, total_usd})
    - window ({since, events, tasks_started, tasks_finished})
    """
    since_dt = _parse_since(since)
    events = _load_events(since_dt, telemetry_dir=telemetry_dir, limit=None)
    now = _iso_now()

    # Process all events to extract metrics
    ctx = _process_events(events)

    # Build running tasks list
    running_tasks = _build_running_tasks(ctx.tasks, now)

    # Build system health and agent metrics
    system_health = _build_system_health(ctx, since_dt, now)
    agent_metrics_dict = _build_agent_metrics(ctx.agents_active)

    # Build telemetry metrics
    telemetry_metrics = TelemetryMetrics(
        period_start=since_dt,
        period_end=now,
        total_events=ctx.total_events,
        events_by_type={"tasks_started": ctx.tasks_started, "tasks_finished": ctx.tasks_finished},
        agent_metrics=agent_metrics_dict,
        system_health=system_health,
    )

    # Build dashboard summary
    return _build_dashboard_summary(telemetry_metrics, ctx, running_tasks, since)
