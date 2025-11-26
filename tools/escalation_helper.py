"""
Escalation helper for Night Shift failures.

Attempts to obtain remediation guidance from Gemini 3.0 Pro (Thinking) and
falls back to GPT-5.1 (Thinking) with high reasoning effort when Gemini fails.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from shared.models.backlog import Task


@dataclass
class EscalationResult:
    provider: str
    analysis: str


def escalate_with_llm(task: Task, failure_reason: str, log_excerpt: Optional[str] = None) -> EscalationResult:
    """
    Ask an external reasoning model to analyze a repeatedly failing task.

    Args:
        task: Task metadata
        failure_reason: Latest failure message
        log_excerpt: Optional snippet of recent logs for extra context

    Returns:
        EscalationResult with provider name and analysis text
    """
    prompt = _build_prompt(task, failure_reason, log_excerpt)

    gemini_error: Exception | None = None
    if genai is not None:
        try:
            analysis = _call_gemini(prompt)
            return EscalationResult(provider="gemini-3.0-pro", analysis=analysis)
        except Exception as exc:  # pragma: no cover - network interactions
            gemini_error = exc

    try:
        analysis = _call_openai(prompt)
        return EscalationResult(provider="gpt-5.1", analysis=analysis)
    except Exception as openai_error:  # pragma: no cover - network interactions
        if gemini_error:
            raise RuntimeError(
                f"Escalation failed via Gemini ({gemini_error}) and GPT-5.1 ({openai_error})"
            ) from openai_error
        raise


def _build_prompt(task: Task, failure_reason: str, log_excerpt: Optional[str]) -> str:
    failure_history = task.metadata.get("failure_history", [])
    history_json = json.dumps(failure_history, indent=2) if failure_history else "[]"
    log_text = log_excerpt or "(no additional logs provided)"

    return f"""
Night Shift (an autonomous software engineer) escalated a task after repeated failures.

TASK DETAILS:
- ID: {task.id}
- Title: {task.title}
- Type: {task.task_type.value}
- Priority: {task.priority.value}
- Description: {task.description}

LATEST FAILURE:
{failure_reason}

FAILURE HISTORY (JSON):
{history_json}

RECENT LOG SNIPPET:
{log_text}

Deliver a concise remediation report with sections:
1. Root cause hypothesis
2. Immediate mitigation steps Night Shift can take automatically
3. Follow-up hardening (tests/guards) to prevent recurrence

Use numbered lists where practical. Keep it under 300 words.
"""


def _call_gemini(prompt: str) -> str:
    try:
        from tools import gemini_helper  # Local import to avoid hard dependency at module load
        import google.generativeai as genai
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("google-generativeai is not installed") from exc

    api_key = gemini_helper.get_gemini_api_key()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.0-pro")
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "top_p": 0.8,
            "max_output_tokens": 1024,
        },
    )
    if not response or not response.text:
        raise RuntimeError("Gemini returned empty response")
    return response.text.strip()


def _call_openai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-5.1",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You are a senior reliability engineer (Thinking mode) providing Toyota-style Andon remediation guidance. Use deep reasoning and provide concrete steps.",
            },
            {"role": "user", "content": prompt},
        ],
        extra_body={"reasoning": {"effort": "high"}},
    )
    choice = response.choices[0]
    content = choice.message.content if hasattr(choice, "message") else None
    if not content:
        raise RuntimeError("OpenAI returned empty response")
    return content.strip()
