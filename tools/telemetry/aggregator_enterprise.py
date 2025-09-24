from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

# Public type alias for compatibility with prior stub
Event = Dict[str, Any]

# Environment variable to override telemetry directory
ENV_DIR = "AGENCY_TELEMETRY_DIR"
DEFAULT_DIR_NAME = os.path.join(os.getcwd(), "logs", "telemetry")
FILE_PATTERN = re.compile(r"^events-(\d{8})\.jsonl$")


def _iso_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_since(since: str, now: Optional[datetime] = None) -> datetime:
    """Parse a since window like '15m', '1h', '24h' into an absolute UTC datetime."""
    now = now or _iso_now()
    s = (since or "1h").strip().lower()
    if s.endswith("m"):
        try:
            minutes = int(s[:-1])
            return now - timedelta(minutes=minutes)
        except Exception:
            return now - timedelta(hours=1)
    if s.endswith("h"):
        try:
            hours = int(s[:-1])
            return now - timedelta(hours=hours)
        except Exception:
            return now - timedelta(hours=1)
    if s.endswith("d"):
        try:
            days = int(s[:-1])
            return now - timedelta(days=days)
        except Exception:
            return now - timedelta(hours=24)
    # default hours if numeric only
    try:
        hours = int(s)
        return now - timedelta(hours=hours)
    except Exception:
        return now - timedelta(hours=1)


def _telemetry_dir(telemetry_dir: Optional[str] = None) -> str:
    return telemetry_dir or os.environ.get(ENV_DIR) or DEFAULT_DIR_NAME


def _parse_ts(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        # Support 'Z' suffix and offsets
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


@dataclass
class _Start:
    ts: datetime
    agent: str
    attempt: int
    started_at: Optional[float]


def _iter_event_files(dir_path: str) -> Iterable[str]:
    try:
        for name in sorted(os.listdir(dir_path)):
            if FILE_PATTERN.match(name):
                yield os.path.join(dir_path, name)
    except FileNotFoundError:
        return


def _load_events_since(dir_path: str, since_dt: datetime) -> Iterable[Dict[str, Any]]:
    for fp in _iter_event_files(dir_path):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                    except Exception:
                        continue
                    ts = _parse_ts(evt.get("ts", ""))
                    if ts is None:
                        continue
                    if ts >= since_dt:
                        evt["_ts_dt"] = ts
                        yield evt
        except FileNotFoundError:
            continue
        except Exception:
            # Swallow I/O errors per spec
            continue


def _load_pricing() -> Dict[str, Any]:
    try:
        raw = os.environ.get("AGENCY_PRICING_JSON")
        if not raw:
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def _estimate_cost(usage: Dict[str, Any], model: Optional[str], pricing: Dict[str, Any]) -> float:
    try:
        if not usage:
            return 0.0
        prompt = float(usage.get("prompt_tokens") or 0)
        completion = float(usage.get("completion_tokens") or 0)
        total = float(usage.get("total_tokens") or (prompt + completion))
        price = 0.0
        if model and model in pricing:
            entry = pricing[model]
            if isinstance(entry, dict):
                p_prompt = float(entry.get("prompt", entry.get("price_per_1k_tokens", 0.0)) or 0.0)
                p_completion = float(entry.get("completion", entry.get("price_per_1k_tokens", 0.0)) or 0.0)
                if "prompt_tokens" in usage or "completion_tokens" in usage:
                    price = (prompt / 1000.0) * p_prompt + (completion / 1000.0) * p_completion
                else:
                    price = (total / 1000.0) * float(entry.get("price_per_1k_tokens", 0.0))
            else:
                # flat price per 1k tokens
                price = (total / 1000.0) * float(entry)
        return round(price, 6)
    except Exception:
        return 0.0


def aggregate(
    since: str = "1h",
    telemetry_dir: Optional[str] = None,
    now: Optional[datetime] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Aggregate telemetry events into a dashboard-friendly summary.

    Returns a dict with keys: running_tasks, recent_results, agents_active, metrics, window, resources, costs
    """
    now_dt = now or _iso_now()
    since_dt = _parse_since(since, now=now_dt)
    dir_path = _telemetry_dir(telemetry_dir)

    total_events = 0
    tasks_started = 0
    tasks_finished = 0
    recent_results = {"success": 0, "failed": 0, "timeout": 0}
    agents: set[str] = set()

    last_start_by_id: Dict[str, _Start] = {}
    last_finish_ts_by_id: Dict[str, datetime] = {}
    last_hb_ts_by_id: Dict[str, datetime] = {}
    max_concurrency: Optional[int] = None

    # Cost accounting
    pricing = _load_pricing()
    total_tokens = 0
    total_usd = 0.0
    by_agent: Dict[str, Dict[str, Any]] = {}
    by_model: Dict[str, Dict[str, Any]] = {}

    for evt in _load_events_since(dir_path, since_dt):
        # Filter by run_id if specified
        if run_id is not None and evt.get("run_id") != run_id:
            continue

        total_events += 1
        evt_type = evt.get("type")
        agent = evt.get("agent") or "unknown"
        task_id = evt.get("id") or "unknown"
        if agent:
            agents.add(agent)

        if evt_type == "task_started":
            tasks_started += 1
            last_start_by_id[task_id] = _Start(
                ts=evt["_ts_dt"],
                agent=agent,
                attempt=int(evt.get("attempt", 1) or 1),
                started_at=evt.get("started_at"),
            )
        elif evt_type == "task_finished":
            tasks_finished += 1
            status = str(evt.get("status", "")).lower()
            if status in recent_results:
                recent_results[status] += 1
            last_finish_ts_by_id[task_id] = evt["_ts_dt"]

            # Usage / model -> cost
            usage = evt.get("usage")
            model = evt.get("model")
            try:
                p = int((usage or {}).get("prompt_tokens") or 0)
                c = int((usage or {}).get("completion_tokens") or 0)
                t = int((usage or {}).get("total_tokens") or (p + c))
            except Exception:
                p = c = t = 0
            if t:
                total_tokens += t
            usd = _estimate_cost(usage or {}, model, pricing)
            total_usd += usd

            # by agent
            if agent:
                agg = by_agent.setdefault(agent, {"tokens": 0, "usd": 0.0})
                agg["tokens"] += t
                agg["usd"] += usd
            # by model
            if model:
                aggm = by_model.setdefault(model, {"tokens": 0, "usd": 0.0})
                aggm["tokens"] += t
                aggm["usd"] += usd
        elif evt_type == "heartbeat":
            last_hb_ts_by_id[task_id] = evt["_ts_dt"]
        elif evt_type == "orchestrator_started":
            try:
                mc = int(evt.get("max_concurrency")) if evt.get("max_concurrency") is not None else None
            except Exception:
                mc = None
            if mc:
                max_concurrency = mc
        else:
            # ignore other types if any
            pass

    running_all: List[Dict[str, Any]] = []
    for tid, s in last_start_by_id.items():
        fts = last_finish_ts_by_id.get(tid)
        if fts is None or fts < s.ts:
            age_s = max(0.0, (now_dt - s.ts).total_seconds())
            hb_ts = last_hb_ts_by_id.get(tid)
            hb_age = (now_dt - hb_ts).total_seconds() if hb_ts else None
            running_all.append({
                "id": tid,
                "agent": s.agent,
                "attempt": s.attempt,
                "started_ts": s.ts.isoformat().replace("+00:00", "Z"),
                "age_s": age_s,
                "last_heartbeat_age_s": hb_age,
            })

    running_all.sort(key=lambda x: x["age_s"], reverse=True)
    running = running_all[:10]

    # Bottleneck heuristics thresholds
    age_thresh = float(os.environ.get("AGENCY_BOTTLENECK_AGE_S", "60"))
    retry_thresh = int(os.environ.get("AGENCY_BOTTLENECK_RETRIES", "3"))
    error_rate_warn = float(os.environ.get("AGENCY_ERROR_RATE_WARN", "0.2"))

    slow_tasks = [
        {"id": r["id"], "agent": r["agent"], "age_s": r["age_s"]}
        for r in running_all if r["age_s"] >= age_thresh
    ][:10]
    retry_heavy = [
        {"id": tid, "agent": s.agent, "attempt": s.attempt}
        for tid, s in last_start_by_id.items() if s.attempt >= retry_thresh
    ][:10]

    # Resources and Costs
    resources = {
        "running": len(running_all),
        "max_concurrency": max_concurrency,
        "utilization": round(len(running_all) / max_concurrency, 3) if max_concurrency else None,
        "heartbeats": {
            "count": len(last_hb_ts_by_id),
            "stale": len([1 for tid, ts in last_hb_ts_by_id.items() if (now_dt - ts).total_seconds() > float(os.environ.get("AGENCY_HEARTBEAT_INTERVAL_S", "5.0")) * 2]),
        },
    }

    costs = {
        "total_tokens": total_tokens,
        "total_usd": round(total_usd, 6),
        "by_agent": {k: {"tokens": v["tokens"], "usd": round(v["usd"], 6)} for k, v in by_agent.items()},
        "by_model": {k: {"tokens": v["tokens"], "usd": round(v["usd"], 6)} for k, v in by_model.items()},
    }

    # Error rate & spike
    error_rate = (recent_results["failed"] / tasks_finished) if tasks_finished else 0.0
    bottlenecks = {
        "slow_tasks": slow_tasks,
        "retry_heavy": retry_heavy,
        "error_rate": round(error_rate, 3),
        "spike": bool(error_rate >= error_rate_warn),
    }

    summary = {
        "running_tasks": running,
        "recent_results": recent_results,
        "agents_active": sorted(agents),
        "resources": resources,
        "costs": costs,
        "bottlenecks": bottlenecks,
        "metrics": {
            "total_events": total_events,
            "tasks_started": tasks_started,
            "tasks_finished": tasks_finished,
        },
        "window": {
            "since": since,
            "from": since_dt.isoformat().replace("+00:00", "Z"),
            "to": now_dt.isoformat().replace("+00:00", "Z"),
        },
    }

    return summary


def list_events(
    since: str = "1h",
    telemetry_dir: Optional[str] = None,
    now: Optional[datetime] = None,
    run_id: Optional[str] = None,
    grep: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """List raw telemetry events with optional filtering."""
    import re

    now_dt = now or _iso_now()
    since_dt = _parse_since(since, now=now_dt)
    dir_path = _telemetry_dir(telemetry_dir)

    events = []
    grep_pattern = re.compile(grep, re.IGNORECASE) if grep else None

    for evt in _load_events_since(dir_path, since_dt):
        # Filter by run_id if specified
        if run_id is not None and evt.get("run_id") != run_id:
            continue

        # Filter by grep pattern if specified
        if grep_pattern is not None:
            # Remove datetime object before JSON serialization for grep
            evt_for_grep = {k: v for k, v in evt.items() if k != "_ts_dt"}
            event_text = json.dumps(evt_for_grep, ensure_ascii=False)
            if not grep_pattern.search(event_text):
                continue

        # Remove internal _ts_dt field before returning
        evt_clean = {k: v for k, v in evt.items() if k != "_ts_dt"}
        events.append(evt_clean)

        if len(events) >= limit:
            break

    return events


# Backward-compatible stub retained for any callers using aggregate_basic

def aggregate_basic(events: Iterable[Event]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    total = 0
    for ev in events:
        total += 1
        t = ev.get("type", "?")
        counts[t] = counts.get(t, 0) + 1
    return {"total_events": total, "by_type": counts}
