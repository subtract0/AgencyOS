from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

from tools.telemetry.aggregator import aggregate

ENV_DIR = "AGENCY_TELEMETRY_DIR"
DEFAULT_TELEMETRY_DIR = os.path.join(os.getcwd(), "logs", "telemetry")


def _telemetry_dir() -> str:
    return os.environ.get(ENV_DIR) or DEFAULT_TELEMETRY_DIR


def _render_text(summary: Dict[str, Any]) -> None:
    metrics = summary.get("metrics", {})
    total = metrics.get("total_events", 0)
    if total == 0:
        print("No telemetry events found. Ensure Telemetry is enabled and running.")
        sys.exit(0)

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


def _parse_refresh(refresh: str) -> float:
    s = (refresh or "0").strip().lower()
    try:
        if s.endswith("ms"):
            return max(0.0, float(s[:-2]) / 1000.0)
        if s.endswith("s"):
            return max(0.0, float(s[:-1]))
        return max(0.0, float(s))
    except Exception:
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(prog="agency dashboard", description="Live agent performance dashboard (MVP)")
    parser.add_argument("--since", default="1h")
    parser.add_argument("--refresh", default="2s")
    parser.add_argument("--watch", action="store_true", help="Continuously refresh at --refresh interval")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    interval = _parse_refresh(args.refresh)

    def once() -> None:
        summary = aggregate(since=args.since, telemetry_dir=_telemetry_dir())
        if args.format == "json":
            print(json.dumps(summary, indent=2))
        else:
            _render_text(summary)

    if args.watch and interval > 0 and args.format == "text":
        try:
            while True:
                # Simple clear screen
                print("\033[2J\033[H", end="")
                once()
                import time as _t
                _t.sleep(interval)
        except KeyboardInterrupt:
            return
    else:
        once()


if __name__ == "__main__":
    main()