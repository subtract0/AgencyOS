from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List
from shared.type_definitions.json import JSONValue

from tools.telemetry.aggregator import list_events

ENV_DIR = "AGENCY_TELEMETRY_DIR"
DEFAULT_TELEMETRY_DIR = os.path.join(os.getcwd(), "logs", "telemetry")


def _telemetry_dir() -> str:
    return os.environ.get(ENV_DIR) or DEFAULT_TELEMETRY_DIR


def _render_text(events: List[Dict[str, JSONValue]]) -> None:
    if not events:
        print("No telemetry events in window.")
        return
    for e in events:
        typ = e.get("type")
        rid = e.get("run_id", "-")
        tid = e.get("id", "-")
        agent = e.get("agent", "-")
        ts = e.get("ts", "-")
        status = e.get("status", "")
        print(f"{ts} {typ} run={rid} id={tid} agent={agent} {status}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="agency telemetry tail", description="Tail telemetry events (filtered)")
    parser.add_argument("--since", default="1h")
    parser.add_argument("--run", dest="run_id", default=None)
    parser.add_argument("--grep", dest="grep", default=None)
    parser.add_argument("--limit", dest="limit", type=int, default=200)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--now", dest="now", default=None, help="Reference time for 'since' calculation (ISO format)")
    args = parser.parse_args()

    # Parse --now if provided
    now_dt = None
    if args.now:
        from datetime import datetime
        try:
            if args.now.endswith("Z"):
                args.now = args.now[:-1] + "+00:00"
            now_dt = datetime.fromisoformat(args.now)
        except ValueError:
            print(f"Error: Invalid --now format: {args.now}")
            return

    evs = list_events(since=args.since, telemetry_dir=_telemetry_dir(), run_id=args.run_id, grep=args.grep, limit=args.limit, now=now_dt)

    if args.format == "json":
        print(json.dumps(evs, indent=2))
        return

    _render_text(evs)


if __name__ == "__main__":
    main()