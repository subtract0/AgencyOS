"""
Gemini 2.5 Flash Helper for Agency OS
Provides cost-effective codebase analysis and planning.
"""
import os
from pathlib import Path

import google.generativeai as genai


def get_gemini_api_key() -> str:
    """Get Gemini API key from environment."""
    # Try both possible env var names
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

    if not api_key:
        # Try loading from .env file
        env_file = Path(__file__).parent.parent / '.env'
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith('GOOGLE_API_KEY=') or line.startswith('GEMINI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break

    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment or .env file")

    return api_key


def plan_implementation(
    feature_description: str,
    context: str | None = None,
    model: str = 'gemini-2.5-flash'
) -> str:
    """
    Use Gemini for implementation planning (saves Anthropic credits).

    Args:
        feature_description: What needs to be implemented
        context: Additional context (codebase structure, constraints, etc.)
        model: Gemini model to use

    Returns:
        Implementation plan from Gemini
    """
    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)

    prompt = f"""
You are a senior software architect planning an implementation for Agency OS.

FEATURE TO IMPLEMENT:
{feature_description}

CONTEXT:
{context or "No additional context provided"}

Create a detailed implementation plan with:
1. High-level architecture
2. File structure (what files to create/modify)
3. Key functions/classes needed
4. Testing strategy
5. Integration points with existing code
6. Risk assessment

Format as markdown with clear sections.
"""

    gemini = genai.GenerativeModel(model)
    response = gemini.generate_content(prompt)

    return response.text
