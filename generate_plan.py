#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-generativeai",
# ]
# ///

"""Generate implementation plan using Gemini 2.5 Flash."""

import os

import google.generativeai as genai


def get_gemini_api_key() -> str:
    """Get Gemini API key from environment."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Try loading from .env file
        from pathlib import Path

        env_file = Path(__file__).parent / ".env"
        if not env_file.exists():
            env_file = Path(__file__).parent.parent / "Agency" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GOOGLE_API_KEY=") or line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found")
    return api_key


def main():
    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)

    context = """
Agency OS Codebase Context:
- 10 specialized Python agents (Planner, Coder, Auditor, QualityEnforcer, etc.)
- Constitutional enforcement: 5 Articles (I: Complete Context, II: 100% Verification, III: Automated Merge, IV: Learning, V: Spec-Driven)
- Current enforcement: Post-facto via quality_enforcer_agent (LLM-based, expensive)
- Claude Code Hooks: 8 lifecycle points (UserPromptSubmit, PreToolUse, PostToolUse, Stop, etc.)
- Goal: Deterministic constitutional enforcement at prompt/tool/stop levels (non-LLM)

Top 3 Priorities from Analysis:
1. UserPromptSubmit: Block prompts that violate Articles (e.g., "skip tests", "use Dict[Any, Any]")
2. PreToolUse: Block git commits/pushes if tests fail (Article II)
3. Stop: Block session end if tasks incomplete (Definition of Done)

Implementation Requirements:
- Exit code 2 = block action (deterministic, no LLM inference)
- UV single-file scripts with embedded dependencies
- TDD-first (write tests before implementation)
- Result<T,E> pattern for error handling
- Pydantic models for validation
- Integration with existing shared/ infrastructure
"""

    prompt = f"""
You are a senior software architect planning an implementation for Agency OS.

FEATURE TO IMPLEMENT:
Implement top 3 Claude Code Hooks for constitutional enforcement

CONTEXT:
{context}

Create a detailed implementation plan with:
1. High-level architecture
2. File structure (what files to create/modify)
3. Key functions/classes needed
4. Testing strategy
5. Integration points with existing code
6. Risk assessment
7. Estimated effort (hours)

Format as markdown with clear sections.
"""

    gemini = genai.GenerativeModel("gemini-2.5-flash")
    response = gemini.generate_content(prompt)

    print(response.text)


if __name__ == "__main__":
    main()
