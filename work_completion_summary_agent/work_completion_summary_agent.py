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
            bundle_text = ""
            if self.bundle_path and os.path.exists(self.bundle_path):
                try:
                    with open(self.bundle_path, "r", encoding="utf-8") as f:
                        # Limit read to avoid token blowup
                        bundle_text = f.read(120000)
                except Exception as e:
                    bundle_text = f"(failed to read bundle at {self.bundle_path}: {e})"

            sys_prompt = (
                "You are generating a concise, listener-friendly audio summary for TTS. Include what was done, why it matters, and 1–3 next steps."
            )
            user_payload = {
                "task": "Regenerate audio summary at high quality",
                "draft_summary": self.draft,
                "bundle_excerpt": bundle_text[:60000] if bundle_text else "",
                "extra_guidance": self.guidance or "",
            }
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ]

            # Call GPT-5 with high reasoning; litellm will pass through extra fields
            resp = litellm.completion(
                model="gpt-5",
                messages=messages,
                extra_body={"reasoning": {"effort": "high"}},
            )
            # Extract content robustly across response shapes
            content = None
            try:
                # litellm often returns an object with .choices
                choices = getattr(resp, "choices", None) or resp.get("choices")  # type: ignore
                if choices and len(choices) > 0:
                    first = choices[0]
                    msg = getattr(first, "message", None) or first.get("message")  # type: ignore
                    if msg:
                        content = getattr(msg, "content", None) or msg.get("content")  # type: ignore
            except Exception:
                pass

            if not content:
                content = str(resp)
            return content
        except Exception as e:
            return f"Escalation failed: {e}"


def create_work_completion_summary_agent(
    model: str = "gpt-5-nano", reasoning_effort: str = "low", agent_context: AgentContext | None = None
) -> Agent:
    """Factory to create the WorkCompletionSummaryAgent.

    Proactively triggered when work is completed to provide concise audio summaries and suggest next steps.
    If they say 'tts' or 'tts summary' or 'audio summary' use this agent. When you prompt this agent, describe
    exactly what you want them to communicate to the user. Remember, this agent has no context about any
    questions or previous conversations between you and the user.
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
        },
        ["agency", "summary", "creation"],
    )

    return Agent(
        name="WorkCompletionSummaryAgent",
        description=(
            "Proactively triggered when work is completed to provide concise audio summaries and suggest next steps. "
            "If they say 'tts' or 'tts summary' or 'audio summary' use this agent. When you prompt this agent, describe "
            "exactly what you want them to communicate to the user. Remember, this agent has no context about any "
            "questions or previous conversations between you and the user."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        model_settings=create_model_settings(model, reasoning_effort),
        tools=[RegenerateWithGpt5],
    )
