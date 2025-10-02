"""
Tool execution telemetry for performance monitoring.

Tracks tool execution time, cache hits, success/failure rates, and provides
statistics for performance analysis and learning.

Constitutional Compliance:
- Article IV: Continuous learning (telemetry feeds into learning system)
- Performance targets: <100ms for cached operations, 2-5s for uncached

Usage:
    @instrument_tool("git_status")
    @with_cache(ttl_seconds=5)
    def git_status() -> str:
        return execute_git_status()
"""

import time
from functools import wraps
from typing import Callable, TypeVar, ParamSpec, Any

T = TypeVar('T')
P = ParamSpec('P')

# In-memory telemetry (could be persisted to SQLite/Firestore)
_telemetry_data: list[dict[str, Any]] = []


def instrument_tool(tool_name: str):
    """
    Decorator to measure tool execution time and cache hits.

    Captures:
    - Execution duration (milliseconds)
    - Cache hit/miss status
    - Success/failure status
    - Timestamp
    - Error messages (on failure)

    Args:
        tool_name: Name of tool being instrumented

    Returns:
        Decorator function

    Example:
        @instrument_tool("git_status")
        @with_cache(ttl_seconds=5)
        def git_status() -> str:
            return subprocess.run(["git", "status"]).stdout
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.time()
            cached = kwargs.get('_from_cache', False)

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000

                # Log to telemetry
                _telemetry_data.append({
                    "tool": tool_name,
                    "duration_ms": duration_ms,
                    "cached": cached,
                    "timestamp": time.time(),
                    "success": True
                })

                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                _telemetry_data.append({
                    "tool": tool_name,
                    "duration_ms": duration_ms,
                    "cached": False,
                    "timestamp": time.time(),
                    "success": False,
                    "error": str(e)
                })
                raise
        return wrapper
    return decorator


def get_tool_stats(hours: int = 24) -> dict[str, Any]:
    """
    Get tool execution statistics for last N hours.

    Provides performance metrics:
    - Total calls
    - Cache hit rate
    - Average duration
    - Success rate
    - Per-tool breakdown

    Args:
        hours: Time window in hours (default: 24)

    Returns:
        Dictionary with aggregated statistics
    """
    cutoff = time.time() - (hours * 3600)
    recent = [t for t in _telemetry_data if t['timestamp'] > cutoff]

    if not recent:
        return {"message": "No data"}

    total_calls = len(recent)
    cache_hits = sum(1 for t in recent if t.get('cached'))
    successful_calls = sum(1 for t in recent if t.get('success'))
    avg_duration = sum(t['duration_ms'] for t in recent) / total_calls

    # Per-tool breakdown
    tools_seen = set(t['tool'] for t in recent)
    tool_breakdown = {}

    for tool in tools_seen:
        tool_data = [t for t in recent if t['tool'] == tool]
        tool_total = len(tool_data)
        tool_cached = sum(1 for t in tool_data if t.get('cached'))
        tool_avg_duration = sum(t['duration_ms'] for t in tool_data) / tool_total

        tool_breakdown[tool] = {
            "calls": tool_total,
            "cache_hit_rate": tool_cached / tool_total if tool_total else 0,
            "avg_duration_ms": tool_avg_duration
        }

    return {
        "total_calls": total_calls,
        "cache_hit_rate": cache_hits / total_calls if total_calls else 0,
        "success_rate": successful_calls / total_calls if total_calls else 0,
        "avg_duration_ms": avg_duration,
        "tools": list(tools_seen),
        "tool_breakdown": tool_breakdown
    }


def clear_telemetry():
    """Clear telemetry data (useful for testing)."""
    global _telemetry_data
    _telemetry_data.clear()


def get_recent_errors(limit: int = 10) -> list[dict[str, Any]]:
    """
    Get recent errors from telemetry.

    Args:
        limit: Maximum number of errors to return

    Returns:
        List of error entries, most recent first
    """
    errors = [t for t in _telemetry_data if not t.get('success')]
    errors.sort(key=lambda x: x['timestamp'], reverse=True)
    return errors[:limit]
