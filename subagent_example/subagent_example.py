from agency_swarm import Agent
import os
from tools import Read, Bash, LS, Grep, Edit, Write, TodoWrite
from shared.agent_utils import (
    render_instructions,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import create_code_bundle_attachment_hook, create_composite_hook
from agency_swarm.tools import BaseTool as Tool
from pydantic import Field
import litellm
import json


class RegenerateWithGpt5(Tool):
    """Escalate the current subagent output to GPT-5 (high reasoning)."""

    draft: str = Field(..., description="Initial draft or content to improve")
    bundle_path: str | None = Field(default=None, description="Optional path to bundle context file (if available)")
    guidance: str | None = Field(default=None, description="Optional guidance or constraints")

    def run(self) -> str:
        try:
            bundle_text = ""
            if self.bundle_path:
                try:
                    with open(self.bundle_path, "r", encoding="utf-8") as f:
                        bundle_text = f.read(80000)
                except Exception:
                    pass
            sys_prompt = (
                "You are improving a concise, clear output. Keep it simple, action-oriented, and clean."
            )
            payload = {
                "draft": self.draft,
                "bundle_excerpt": bundle_text[:40000] if bundle_text else "",
                "guidance": self.guidance or "",
            }
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": json.dumps(payload)},
            ]
            resp = litellm.completion(
                model="gpt-5",
                messages=messages,
                extra_body={"reasoning": {"effort": "high"}},
            )
            # Extract content
            content = None
            try:
                choices = getattr(resp, "choices", None) or resp.get("choices")  # type: ignore
                if choices:
                    msg = getattr(choices[0], "message", None) or choices[0].get("message")  # type: ignore
                    if msg:
                        content = getattr(msg, "content", None) or msg.get("content")  # type: ignore
            except Exception:
                pass
            return content or str(resp)
        except Exception as e:
            return f"Escalation failed: {e}"



def create_subagent_example(
    model: str = "gpt-5-mini", reasoning_effort: str = "low"
) -> Agent:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Use gpt-5 specific instructions if applicable
    instr_path = current_dir + ("/instructions-gpt-5.md" if model.lower().startswith("gpt-5") else "/instructions.md")
    instructions = render_instructions(instr_path, model)
    # Hooks: attach bundle so escalation tools can use it when available
    bundle_hook = create_code_bundle_attachment_hook()
    hooks = create_composite_hook([bundle_hook])
    return Agent(
        name="SubagentExample",
        description="A template subagent that can be customized for specific domain tasks.",
        instructions=instructions,
        tools=[
            Read,
            Bash,
            LS,
            Grep,
            Edit,
            Write,
            TodoWrite,
            RegenerateWithGpt5,
        ],
        model=get_model_instance(model),
        model_settings=create_model_settings(model, reasoning_effort, "detailed"),
        hooks=hooks,
    )
