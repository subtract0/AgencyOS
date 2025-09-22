import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List

from agency_swarm.tools import BaseTool
from pydantic import Field


class ContextMessageHandoff(BaseTool):
    """
    Enhanced handoff tool that packages a mission prompt and structured context
    for a recipient agent. Optionally persists the payload under logs/handoffs/.
    """

    target_agent: str = Field(..., description="Target agent label (e.g., PlannerAgent)")
    prompt: str = Field(..., description="Mission prompt or instruction for the recipient")
    payload: Any = Field(
        None, alias="context", description="Structured context (dict) or raw string to accompany the prompt"
    )
    tags: Optional[List[str]] = Field(
        default=None, description="Optional tags for the handoff payload"
    )
    persist: bool = Field(
        default=False, description="When true, persist the payload to logs/handoffs/"
    )

    def run(self) -> str:
        target = (self.target_agent or "").strip()
        prompt = (self.prompt or "").strip()

        if not target:
            return "Error: target_agent is required"
        if not prompt:
            return "Error: prompt is required"

        payload = {
            "target_agent": target,
            "prompt": prompt,
            "context": self._safe_context(self.payload),
            "tags": self.tags or [],
            "created_at": datetime.utcnow().isoformat(),
        }

        saved_path: Optional[str] = None
        if self.persist:
            try:
                base = Path(os.getcwd()) / "logs" / "handoffs"
                base.mkdir(parents=True, exist_ok=True)
                filename = (
                    f"handoff_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}_{self._sanitize(target)}.json"
                )
                path = base / filename
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                saved_path = str(path)
            except Exception as e:
                return f"Error: failed to persist handoff context: {e}"

        prompt_snippet = prompt[:80] + ("…" if len(prompt) > 80 else "")
        context_keys = (
            ",".join(list(payload["context"].keys())[:5]) if isinstance(payload["context"], dict) else "raw"
        )

        if saved_path:
            return (
                "Prepared handoff to "
                + target
                + f" | prompt='{prompt_snippet}' | context saved: path={saved_path} (keys={context_keys})"
            )
        else:
            return (
                "Prepared handoff to "
                + target
                + f" | prompt='{prompt_snippet}' | context not persisted (keys={context_keys})"
            )

    def _sanitize(self, s: str) -> str:
        return "".join(c for c in s if c.isalnum() or c in ("-", "_"))[:64]

    def _safe_context(self, ctx: Any) -> Any:
        # Only allow dict or str; otherwise, coerce to str summary
        if isinstance(ctx, dict):
            return ctx
        if isinstance(ctx, str):
            # Avoid huge summaries in memory/returns
            return ctx if len(ctx) <= 2000 else (ctx[:1999] + "…")
        return {"summary": str(ctx)[:500]}


# Alias for Agency Swarm loader conventions
context_message_handoff = ContextMessageHandoff
