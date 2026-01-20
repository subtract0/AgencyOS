"""AI Classifier for Second Brain thoughts.

Uses local vcoder-120b ($0) or falls back to OpenAI.
Treats prompts as APIs - structured JSON input/output.
"""

import json
import os
from typing import Optional
import httpx

from .types import Category, ClassificationResult


# Configuration
LOCAL_API_BASE = os.getenv("LOCAL_API_BASE", "http://localhost:1234/v1")
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "vcoder-120b-1.0-hi-mlx")
USE_LOCAL = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"
CONFIDENCE_THRESHOLD = float(os.getenv("SB_CONFIDENCE_THRESHOLD", "0.6"))


CLASSIFICATION_PROMPT = """You are a Second Brain classifier. Your job is to route thoughts into the right bucket.

CATEGORIES (choose exactly ONE):
- people: About a specific person, relationship, follow-up needed with someone
- projects: Active work, tasks, goals, things you're building or shipping
- ideas: Insights, concepts, observations, things to remember but not act on now
- admin: Errands, bills, appointments, logistics, household, paperwork

RULES:
1. Extract the most specific, actionable information
2. For projects: ALWAYS extract a concrete "next_action" (verb + object + deadline if mentioned)
3. For people: Extract who, context, and any follow-ups
4. Return ONLY valid JSON, no markdown, no explanation
5. Be confident in your classification - if truly ambiguous, use confidence < 0.6

INPUT: {thought}

OUTPUT JSON SCHEMA:
{{
  "category": "people" | "projects" | "ideas" | "admin",
  "confidence": 0.0-1.0,
  "reasoning": "one sentence why this category",
  "extracted": {{
    // For people:
    "name": "string",
    "context": "string",
    "follow_ups": ["string"],

    // For projects:
    "name": "string",
    "status": "active" | "waiting" | "blocked" | "someday",
    "next_action": "specific verb + object",
    "notes": "string",

    // For ideas:
    "title": "string",
    "oneliner": "core insight in one sentence",
    "notes": "string",

    // For admin:
    "name": "string",
    "due_date": "YYYY-MM-DD or null",
    "notes": "string"
  }},
  "tags": ["relevant", "tags"]
}}

Return ONLY the JSON:"""


def classify_thought(raw_text: str) -> ClassificationResult:
    """Classify a raw thought into a category with extracted fields.

    Uses local LLM by default ($0 cost).
    Returns ClassificationResult with category, confidence, and extracted data.
    """
    prompt = CLASSIFICATION_PROMPT.format(thought=raw_text)

    try:
        if USE_LOCAL:
            result = _call_local_llm(prompt)
        else:
            result = _call_openai(prompt)

        return _parse_result(result, raw_text)

    except Exception as e:
        # Safe default: unknown category with low confidence
        return ClassificationResult(
            category=Category.UNKNOWN,
            confidence=0.0,
            extracted_data={"raw_text": raw_text, "error": str(e)},
            reasoning=f"Classification failed: {e}"
        )


def _call_local_llm(prompt: str) -> str:
    """Call local vcoder-120b via OpenAI-compatible API."""
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{LOCAL_API_BASE}/chat/completions",
            json={
                "model": LOCAL_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # Low for deterministic classification
                "max_tokens": 500,
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def _call_openai(prompt: str) -> str:
    """Fallback to OpenAI API."""
    import openai

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
    )
    return response.choices[0].message.content or ""


def _parse_result(raw_response: str, original_text: str) -> ClassificationResult:
    """Parse LLM response into ClassificationResult."""
    # Clean up response (remove markdown if present)
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)

        category_str = data.get("category", "unknown").lower()
        category = Category(category_str) if category_str in [c.value for c in Category] else Category.UNKNOWN

        return ClassificationResult(
            category=category,
            confidence=float(data.get("confidence", 0.5)),
            extracted_data=data.get("extracted", {}),
            reasoning=data.get("reasoning", "")
        )

    except (json.JSONDecodeError, ValueError) as e:
        return ClassificationResult(
            category=Category.UNKNOWN,
            confidence=0.0,
            extracted_data={"raw_text": original_text, "parse_error": str(e)},
            reasoning=f"Failed to parse LLM response: {e}"
        )


def needs_review(result: ClassificationResult) -> bool:
    """Check if classification needs human review (bouncer pattern)."""
    return result.confidence < CONFIDENCE_THRESHOLD or result.category == Category.UNKNOWN
