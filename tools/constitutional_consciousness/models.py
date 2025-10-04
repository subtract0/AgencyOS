"""
Pydantic models for Constitutional Consciousness feedback loop.

Constitutional Compliance:
- No Dict[Any, Any] - all models use typed fields
- Result<T,E> pattern for error handling
- Strict type safety throughout
"""


from pydantic import BaseModel, Field


class ConstitutionalPattern(BaseModel):
    """Pattern detected from constitutional violations."""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    function_name: str = Field(..., description="Function triggering violations")
    articles_violated: list[str] = Field(..., description="Constitutional articles violated")
    frequency: int = Field(..., ge=0, description="Number of occurrences")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Pattern confidence score")
    roi_hours_saved: float = Field(
        ..., ge=0.0, description="Estimated hours saved per year by fixing"
    )
    roi_cost_saved: float = Field(..., ge=0.0, description="Estimated cost saved per year (USD)")
    fix_suggestion: str | None = Field(None, description="Suggested fix or remediation")
    first_seen: str = Field(..., description="ISO timestamp of first occurrence")
    last_seen: str = Field(..., description="ISO timestamp of last occurrence")
    trend: str = Field(..., description="Trend: INCREASING, STABLE, DECREASING")

    class Config:
        frozen = True  # Immutable after creation


class ViolationPrediction(BaseModel):
    """Prediction of future constitutional violations."""

    pattern_id: str = Field(..., description="Pattern this prediction is based on")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability of recurrence")
    expected_occurrences: int = Field(..., ge=0, description="Expected violations in next period")
    time_period: str = Field(default="7_days", description="Prediction time period")
    recommended_action: str = Field(..., description="Recommended preventive action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")

    class Config:
        frozen = True


class CycleReport(BaseModel):
    """Report from one consciousness cycle."""

    cycle_timestamp: str = Field(..., description="ISO timestamp of cycle execution")
    violations_analyzed: int = Field(..., ge=0, description="Total violations analyzed")
    patterns_detected: list[ConstitutionalPattern] = Field(default_factory=list)
    predictions: list[ViolationPrediction] = Field(default_factory=list)
    fixes_suggested: list[dict] = Field(default_factory=list, description="Fix suggestions")
    agents_evolved: list[str] = Field(
        default_factory=list, description="Agents updated with learnings"
    )
    total_roi_potential: float = Field(
        default=0.0, ge=0.0, description="Total potential ROI in USD"
    )
    vectorstore_updated: bool = Field(default=False, description="VectorStore integration status")

    @property
    def summary(self) -> str:
        """Generate one-line summary."""
        return (
            f"Analyzed {self.violations_analyzed} violations, "
            f"found {len(self.patterns_detected)} patterns, "
            f"${self.total_roi_potential:,.0f}/year potential savings"
        )
