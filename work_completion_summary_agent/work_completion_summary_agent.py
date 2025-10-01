import os

from agency_swarm import Agent
from shared.agent_context import AgentContext, create_agent_context
from shared.agent_utils import (
    select_instructions_file,
    create_model_settings,
    get_model_instance,
)
from agency_swarm.tools import BaseTool as Tool
from pydantic import Field
import litellm
import json
import os
from shared.system_hooks import (
    create_message_filter_hook,
    create_memory_integration_hook,
    create_composite_hook,
    create_code_bundle_attachment_hook,
)

current_dir = os.path.dirname(os.path.abspath(__file__))


class RegenerateWithGpt5(Tool):
    """Escalate summary generation to GPT-5 with high reasoning using optional code bundle context.

    Provide your draft summary and optionally a bundle_path (provided via a system note or context)
    to allow GPT-5 to see the prior agent's full context.
    """

    draft: str = Field(..., description="The initial draft summary to improve")
    bundle_path: str | None = Field(default=None, description="Path to the code bundle file with prior context")
    guidance: str | None = Field(default=None, description="Optional extra instructions or constraints")

    def run(self) -> str:
        try:
            bundle_text = self._load_bundle_content()
            messages = self._prepare_gpt5_messages(bundle_text)
            resp = self._call_gpt5_with_reasoning(messages)
            content = self._extract_response_content(resp)
            self._emit_telemetry_event()
            return content
        except Exception as e:
            return f"Escalation failed: {e}"

    def _load_bundle_content(self) -> str:
        """Load and return bundle content if path exists."""
        if not self.bundle_path or not os.path.exists(self.bundle_path):
            return ""

        try:
            with open(self.bundle_path, "r", encoding="utf-8") as f:
                return f.read(120000)  # Limit read to avoid token blowup
        except Exception as e:
            return f"(failed to read bundle at {self.bundle_path}: {e})"

    def _prepare_gpt5_messages(self, bundle_text: str) -> list:
        """Prepare messages for GPT-5 API call."""
        sys_prompt = (
            "You are generating a concise, listener-friendly audio summary for TTS. Include what was done, why it matters, and 1–3 next steps."
        )
        user_payload = {
            "task": "Regenerate audio summary at high quality",
            "draft_summary": self.draft,
            "bundle_excerpt": bundle_text[:60000] if bundle_text else "",
            "extra_guidance": self.guidance or "",
        }
        return [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ]

    def _call_gpt5_with_reasoning(self, messages: list):
        """Call GPT-5 with high reasoning effort."""
        return litellm.completion(
            model="gpt-5",
            messages=messages,
            extra_body={"reasoning": {"effort": "high"}},
        )

    def _extract_response_content(self, resp) -> str:
        """Extract content from GPT-5 response robustly."""
        content = None
        try:
            choices = getattr(resp, "choices", None) or resp.get("choices")  # type: ignore
            if choices and len(choices) > 0:
                first = choices[0]
                msg = getattr(first, "message", None) or first.get("message")  # type: ignore
                if msg:
                    content = getattr(msg, "content", None) or msg.get("content")  # type: ignore
        except Exception:
            pass

        return content if content else str(resp)

    def _emit_telemetry_event(self) -> None:
        """Emit telemetry event for escalation usage."""
        try:
            from tools.orchestrator.scheduler import _telemetry_emit  # type: ignore
            _telemetry_emit({
                "type": "escalation_used",
                "agent": "WorkCompletionSummaryAgent",
                "tool": "RegenerateWithGpt5",
                "bundle_present": bool(self.bundle_path),
            })
        except Exception:
            self._fallback_telemetry_write()

    def _fallback_telemetry_write(self) -> None:
        """Fallback telemetry writing when main telemetry fails."""
        try:
            import json as _json, os as _os
            from datetime import datetime, timezone
            base = os.path.join(os.getcwd(), "logs", "telemetry")
            os.makedirs(base, exist_ok=True)
            ts = datetime.now(timezone.utc)
            fname = os.path.join(base, f"events-{ts:%Y%m%d}.jsonl")
            ev = {
                "ts": ts.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "type": "escalation_used",
                "agent": "WorkCompletionSummaryAgent",
                "tool": "RegenerateWithGpt5",
                "bundle_present": bool(self.bundle_path),
            }
            with open(fname, "a", encoding="utf-8") as f:
                f.write(_json.dumps(ev) + "\n")
        except Exception:
            pass


def create_work_completion_summary_agent(
    model: str = "gpt-5-nano",
    reasoning_effort: str = "low",
    agent_context: AgentContext | None = None,
    cost_tracker = None
) -> Agent:
    """Factory to create the WorkCompletionSummaryAgent.

    Proactively triggered when work is completed to provide concise audio summaries and suggest next steps.
    If they say 'tts' or 'tts summary' or 'audio summary' use this agent. When you prompt this agent, describe
    exactly what you want them to communicate to the user. Remember, this agent has no context about any
    questions or previous conversations between you and the user.

    Args:
        model: Model name to use
        reasoning_effort: Reasoning effort level
        agent_context: Optional AgentContext for memory integration
        cost_tracker: Optional CostTracker for real-time LLM cost tracking
    """
    if agent_context is None:
        agent_context = create_agent_context()

    # Hooks (memory + filter + code bundle for escalation)
    filter_hook = create_message_filter_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    bundle_hook = create_code_bundle_attachment_hook()
    combined_hook = create_composite_hook([filter_hook, memory_hook, bundle_hook])

    # Log creation
    agent_context.store_memory(
        f"agent_created_{agent_context.session_id}",
        {
            "agent_type": "WorkCompletionSummaryAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id,
            "cost_tracker_enabled": cost_tracker is not None
        },
        ["agency", "summary", "creation"],
    )

    # Store cost_tracker in agent context for later use
    if cost_tracker is not None:
        agent_context.cost_tracker = cost_tracker

    # Create agent
    agent = Agent(
        name="WorkCompletionSummaryAgent",
        description=(
            "PROACTIVE task summarization specialist providing concise, actionable completion reports. Uses cost-efficient model "
            "(GPT-5-mini) for intelligent synthesis of multi-agent work sessions. AUTOMATICALLY triggered by MergerAgent after "
            "successful integration or by any agent completing significant work. INTELLIGENTLY analyzes: (1) git diff output for "
            "code changes, (2) test results and coverage reports, (3) cost tracking data for LLM operations, (4) TodoWrite task "
            "completion status, and (5) constitutional compliance verification results. PROACTIVELY generates: technical summaries "
            "for developers, executive summaries for stakeholders, cost reports, and learning insights for VectorStore. Coordinates "
            "with LearningAgent to extract patterns from successful sessions. Creates structured markdown reports with: changes made, "
            "tests added/passing, constitutional articles satisfied, costs incurred, and recommendations for next steps. Optimized "
            "for minimal cost while maintaining high-quality output. When prompting, provide session context and completion criteria."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        model_settings=create_model_settings(model, reasoning_effort),
        tools=[RegenerateWithGpt5],
    )

    # Enable cost tracking if provided
    if cost_tracker is not None:
        from shared.llm_cost_wrapper import wrap_agent_with_cost_tracking
        wrap_agent_with_cost_tracking(agent, cost_tracker)

    return agent
