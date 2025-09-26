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
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from shared.types.json import JSONValue
from shared.models.telemetry import (
    TelemetryEvent, TelemetryMetrics, AgentMetrics,
    SystemHealth, EventType, EventSeverity
)


# ------------------------
# Helpers (also used by enhanced_aggregator)
# ------------------------

def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _telemetry_dir(telemetry_dir: Optional[str] = None) -> Path:
    if telemetry_dir:
        return Path(telemetry_dir)
    return _project_root() / "logs" / "telemetry"


def _iso_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        # Support 'Z' suffix (UTC)
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
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


def _load_events(since_dt: datetime, telemetry_dir: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, JSONValue]]:
    base = _telemetry_dir(telemetry_dir)
    events: List[Dict[str, JSONValue]] = []

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
                        dt = dt.replace(tzinfo=timezone.utc)
                    if dt < since_dt:
                        continue
                    ev["_dt"] = dt
                    events.append(ev)
        except Exception:
            # Skip file if unreadable
            continue

    # Sort by timestamp ascending
    events.sort(key=lambda e: e.get("_dt", _iso_now()))

    if limit is not None and len(events) > limit:
        events = events[-limit:]
    return events


# ------------------------
# Public API
# ------------------------

def list_events(since: str = "1h", grep: Optional[str] = None, limit: int = 200, telemetry_dir: Optional[str] = None) -> List[Dict[str, JSONValue]]:
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
        filtered: List[Dict[str, JSONValue]] = []
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


def aggregate(since: str = "1h", telemetry_dir: Optional[str] = None) -> TelemetryMetrics:
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

    # Metrics and counters
    total_events = len(events)
    tasks_started = 0
    tasks_finished = 0
    recent_results = {"success": 0, "failed": 0, "timeout": 0}
    agents_active: List[str] = []

    # Running tasks tracking
    now = _iso_now()
    tasks: Dict[str, Dict[str, JSONValue]] = {}

    # Resource snapshot (take latest orchestrator_started)
    max_concurrency: Optional[int] = None
    latest_orchestrator_ts: Optional[datetime] = None

    # Cost counters (if usage present in events)
    total_tokens = 0
    total_usd = 0.0

    for ev in events:
        typ = ev.get("type")
        agent = ev.get("agent")
        if agent and agent not in agents_active:
            agents_active.append(agent)

        if typ == "orchestrator_started":
            ts = ev.get("ts")
            dt = _parse_iso(ts) if isinstance(ts, str) else None
            if dt and (latest_orchestrator_ts is None or dt > latest_orchestrator_ts):
                latest_orchestrator_ts = dt
                max_concurrency = int(ev.get("max_concurrency", max_concurrency or 0)) or None

        elif typ == "task_started":
            tasks_started += 1
            tid = str(ev.get("id")) if ev.get("id") is not None else None
            if tid:
                started_at = ev.get("started_at")
                dt = None
                if isinstance(started_at, (int, float)):
                    try:
                        dt = datetime.fromtimestamp(float(started_at), tz=timezone.utc)
                    except Exception:
                        dt = None
                if dt is None:
                    ts = ev.get("ts")
                    dt = _parse_iso(ts) if isinstance(ts, str) else now
                tasks[tid] = {
                    "id": tid,
                    "agent": agent or "-",
                    "started_dt": dt or now,
                    "last_hb_dt": None,
                    "finished": False,
                }

        elif typ == "heartbeat":
            tid = str(ev.get("id")) if ev.get("id") is not None else None
            if tid and tid in tasks:
                ts = ev.get("ts")
                hb_dt = _parse_iso(ts) if isinstance(ts, str) else None
                tasks[tid]["last_hb_dt"] = hb_dt or now

        elif typ == "task_finished":
            tasks_finished += 1
            status = str(ev.get("status", "")).lower()
            if status in recent_results:
                recent_results[status] += 1
            tid = str(ev.get("id")) if ev.get("id") is not None else None
            if tid and tid in tasks:
                tasks[tid]["finished"] = True

            # Cost accounting if present
            usage = ev.get("usage")
            if isinstance(usage, dict):
                tokens = usage.get("total_tokens")
                try:
                    if tokens is not None:
                        total_tokens += int(tokens)
                except Exception:
                    pass
                # If cost provided, accumulate
                cost = usage.get("total_usd") or ev.get("cost_usd")
                try:
                    if cost is not None:
                        total_usd += float(cost)
                except Exception:
                    pass

    # Derive running tasks (not finished)
    running_tasks: List[Dict[str, JSONValue]] = []
    for t in tasks.values():
        if t.get("finished"):
            continue
        started_dt: datetime = t.get("started_dt", now)
        last_hb_dt: Optional[datetime] = t.get("last_hb_dt")
        age_s = max(0.0, (now - started_dt).total_seconds())
        hb_age_s = (now - last_hb_dt).total_seconds() if isinstance(last_hb_dt, datetime) else None
        running_tasks.append({
            "id": t.get("id", "-"),
            "agent": t.get("agent", "-"),
            "age_s": age_s,
            "last_heartbeat_age_s": hb_age_s,
        })

    # Sort and cap running tasks
    running_tasks.sort(key=lambda r: r.get("age_s", 0.0), reverse=True)
    running_tasks = running_tasks[:10]

    # Resources
    running_count = len(running_tasks)
    util = None
    try:
        if max_concurrency and max_concurrency > 0:
            util = min(1.0, running_count / float(max_concurrency))
    except Exception:
        util = None

    # Build system health
    system_health = SystemHealth(
        status="healthy" if recent_results.get("failed", 0) < recent_results.get("success", 0) else "degraded",
        total_events=total_events,
        error_count=recent_results.get("failed", 0),
        active_agents=agents_active,
        uptime_seconds=(now - since_dt).total_seconds()
    )

    # Build agent metrics
    agent_metrics_dict: Dict[str, AgentMetrics] = {}
    for agent in agents_active:
        agent_metrics_dict[agent] = AgentMetrics(
            agent_id=agent,
            total_invocations=0,  # Would need event tracking
            successful_invocations=0,
            failed_invocations=0
        )

    # Build telemetry metrics
    telemetry_metrics = TelemetryMetrics(
        period_start=since_dt,
        period_end=now,
        total_events=total_events,
        events_by_type={"tasks_started": tasks_started, "tasks_finished": tasks_finished},
        agent_metrics=agent_metrics_dict,
        system_health=system_health
    )

    # For backward compatibility, attach additional data
    # Convert to dict and add extra fields
    summary = telemetry_metrics.model_dump()
    summary.update({
        "agents_active": agents_active,
        "running_tasks": running_tasks,
        "recent_results": recent_results,
        "resources": {
            "max_concurrency": max_concurrency,
            "running": running_count,
            "utilization": util,
        },
        "costs": {
            "total_tokens": total_tokens,
            "total_usd": total_usd,
        },
        "window": {
            "since": since,
            "events": total_events,
            "tasks_started": tasks_started,
            "tasks_finished": tasks_finished,
        },
        "metrics": {
            "total_events": total_events,
            "tasks_started": tasks_started,
            "tasks_finished": tasks_finished,
        }
    })

    # Return as dict for backward compatibility
    # TODO: Update callers to use TelemetryMetrics directly
    return summary
