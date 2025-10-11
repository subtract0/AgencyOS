"""Pydantic model for robust LLM JSON output parsing in Slop Guardian.

Constitutional Compliance:
- Article II: 100% verification (strict validation of LLM responses)
- ADR-008: Strict typing (no Dict[Any, Any])
"""

from pydantic import BaseModel, Field, confloat

# Robust Pydantic model for LLM JSON output
class RawSlopEval(BaseModel):
    """Raw evaluation response from GPT-5 slop rubric.

    Validates that LLM output contains required keys with correct types.
    Prevents runtime errors from malformed JSON responses.
    """

    dimension_scores: dict[str, confloat(ge=0.0, le=5.0)] = Field(
        ..., description="Scores for clarity, measurability, completeness, actionability (0.0-5.0)"
    )
    reasons: list[str] = Field(
        default_factory=list, description="Human-readable reasons for low scores"
    )
    top_fixes: list[str] = Field(
        default_factory=list, description="Actionable fixes to improve quality"
    )

    model_config = {"extra": "forbid"}  # Reject unknown fields
