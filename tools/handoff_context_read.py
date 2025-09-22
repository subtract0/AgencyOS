import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from agency_swarm.tools import BaseTool
from pydantic import Field


class HandoffContextRead(BaseTool):
    """
    Read the most recent persisted ContextMessageHandoff payload(s) for a target agent
    from logs/handoffs/. Useful for consumers to retrieve mission context.
    """

    target_agent: str = Field(..., description="Target agent label used when persisting handoff")
    limit: int = Field(1, description="Number of recent records to return")
    since: Optional[str] = Field(
        None,
        description="Optional ISO timestamp filter: only records created after this time are returned",
    )

    def run(self) -> str:
        target = (self.target_agent or "").strip()
        if not target:
            return "Exit code: 1\nError: target_agent is required"

        base = Path(os.getcwd()) / "logs" / "handoffs"
        if not base.exists():
            return "Exit code: 0\nNo handoffs directory found; no records yet"

        try:
            since_dt = datetime.fromisoformat(self.since) if self.since else None
        except Exception:
            return "Exit code: 1\nError: since must be ISO 8601 timestamp"

        sanitized = self._sanitize(target)
        files: List[Path] = sorted(
            [p for p in base.glob(f"handoff_*_{sanitized}.json") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not files:
            return f"Exit code: 0\nNo handoff records found for target: {target}"

        results = []
        for p in files:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                created_at = data.get("created_at")
                if since_dt and created_at:
                    try:
                        created_dt = datetime.fromisoformat(created_at)
                        if created_dt <= since_dt:
                            continue
                    except Exception:
                        # Skip records with invalid timestamps
                        pass
                results.append({"path": str(p), "data": data})
                if len(results) >= max(1, self.limit):
                    break
            except Exception as e:
                # Skip corrupted files but report at end
                results.append({"path": str(p), "error": str(e)})
                if len(results) >= max(1, self.limit):
                    break

        # Return compact JSON lines for easy parsing
        lines = []
        for r in results:
            try:
                lines.append(json.dumps(r))
            except Exception:
                lines.append(json.dumps({"path": r.get("path"), "error": "serialization_failed"}))
        return "Exit code: 0\n" + "\n".join(lines)

    def _sanitize(self, s: str) -> str:
        return "".join(c for c in s if c.isalnum() or c in ("-", "_"))[:64]


handoff_context_read = HandoffContextRead
