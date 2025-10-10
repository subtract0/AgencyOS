"""Adaptive model router with cost tracking and learning.

Per ADR-024 and Leap 3 Milestone 3: Route tasks to optimal models based on complexity.
Constitutional Article IV compliance: VectorStore integration mandatory.
"""

import os
import time
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from shared.task_complexity import (
    ClassificationResult,
    RoutingDecision,
    TaskComplexity,
    TaskComplexityClassifier,
)
from shared.type_definitions.result import Err, Ok, Result

# Model pricing (as of 2025-10, per 1M tokens)
MODEL_PRICING = {
    "gpt-5": {"input": 4.00, "output": 16.00},
    "gpt-4o": {"input": 1.50, "output": 6.00},
    "gpt-4o-mini": {"input": 0.10, "output": 0.40},
    "ollama/qwen3-coder:30b": {"input": 0.00, "output": 0.00},
    "ollama": {"input": 0.00, "output": 0.00},  # Generic local
}


class CostMetric(BaseModel):
    """Cost metric for a single routing decision."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_description: str
    complexity: str  # P1/P2/P3
    model_used: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    routing_latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class CostSummary(BaseModel):
    """Aggregated cost metrics for reporting."""

    model_config = ConfigDict(extra="forbid")

    period_start: datetime
    period_end: datetime

    # Task counts by complexity
    p1_tasks: int = 0
    p2_tasks: int = 0
    p3_tasks: int = 0
    total_tasks: int = 0

    # Cost breakdown
    p1_cost_usd: float = 0.0
    p2_cost_usd: float = 0.0
    p3_cost_usd: float = 0.0
    total_cost_usd: float = 0.0

    # Comparison metrics
    baseline_cost_usd: float  # All gpt-5 cost
    cost_savings_usd: float = 0.0
    cost_reduction_percent: float = 0.0

    # Accuracy metrics
    correct_classifications: int = 0
    misclassifications: int = 0
    classification_accuracy: float = Field(ge=0.0, le=1.0, default=0.0)

    # Performance metrics
    avg_routing_latency_ms: float = 0.0
    p99_routing_latency_ms: float = 0.0

    def calculate_savings(self) -> None:
        """Calculate cost savings vs baseline."""
        self.cost_savings_usd = self.baseline_cost_usd - self.total_cost_usd
        if self.baseline_cost_usd > 0:
            self.cost_reduction_percent = (self.cost_savings_usd / self.baseline_cost_usd) * 100


class ModelRouter:
    """Route tasks to optimal models based on complexity classification.

    Per ADR-024:
    - P1 → gpt-5 ($4/1M)
    - P2 → gpt-4o ($1.50/1M)
    - P3 → local ollama/qwen3:30b ($0) or gpt-4o-mini fallback ($0.10/1M)

    Environment overrides:
    - {AGENT}_MODEL: Per-agent override
    - FORCE_MODEL: Global override (testing/debugging)
    """

    def __init__(
        self,
        classifier: TaskComplexityClassifier | None = None,
        cost_tracker: "CostTracker | None" = None,
    ):
        """Initialize model router.

        Args:
            classifier: TaskComplexityClassifier instance
            cost_tracker: CostTracker for telemetry
        """
        self.classifier = classifier or TaskComplexityClassifier()
        self.cost_tracker = cost_tracker

    def route(
        self,
        task_description: str,
        task_type: str = "general",
        agent_key: str = "coder",
        session_id: str | None = None,
        estimated_tokens: int = 500,
    ) -> Result[RoutingDecision, str]:
        """Route task to optimal model.

        Args:
            task_description: Task description text
            task_type: Task type (e.g., "code_modification", "architecture")
            agent_key: Agent identifier (e.g., "coder", "planner")
            session_id: Session identifier for tracking
            estimated_tokens: Estimated token count for cost calculation

        Returns:
            Result containing RoutingDecision or error
        """
        start_time = time.perf_counter()

        # Check environment overrides first (Article III)
        override_model = self._check_overrides(agent_key)
        if override_model:
            # Skip classification if override
            decision = RoutingDecision(
                task_id=str(uuid.uuid4()),
                task_description=task_description,
                task_type=task_type,
                complexity=TaskComplexity.P2_MODERATE,  # Default for overrides
                classification_method="override",
                classification_confidence=1.0,
                selected_model=override_model,
                fallback_used=False,
                environment_override=True,
                routing_latency_ms=(time.perf_counter() - start_time) * 1000,
                classification_latency_ms=0.0,
                estimated_cost_usd=self._estimate_cost(override_model, estimated_tokens),
                estimated_tokens=estimated_tokens,
                agent_key=agent_key,
                session_id=session_id or "default",
            )

            if self.cost_tracker:
                self.cost_tracker.track_decision(decision)

            return Ok(decision)

        # Classify task complexity
        classification_start = time.perf_counter()
        classification_result = self.classifier.classify(task_description, task_type)
        classification_latency_ms = (time.perf_counter() - classification_start) * 1000

        if classification_result.is_err():
            return Err(f"Classification failed: {classification_result.unwrap_err()}")

        result: ClassificationResult = classification_result.unwrap()

        # Select model based on complexity
        selected_model, fallback_used = self._select_model(result.complexity)

        # Calculate cost estimate
        estimated_cost = self._estimate_cost(selected_model, estimated_tokens)

        # Create routing decision
        routing_latency_ms = (time.perf_counter() - start_time) * 1000

        decision = RoutingDecision(
            task_id=str(uuid.uuid4()),
            task_description=task_description,
            task_type=task_type,
            complexity=result.complexity,
            classification_method=result.method,
            classification_confidence=result.confidence,
            selected_model=selected_model,
            fallback_used=fallback_used,
            environment_override=False,
            routing_latency_ms=routing_latency_ms,
            classification_latency_ms=classification_latency_ms,
            vectorstore_query_latency_ms=result.details.get("query_latency_ms"),
            estimated_cost_usd=estimated_cost,
            estimated_tokens=estimated_tokens,
            agent_key=agent_key,
            session_id=session_id or "default",
        )

        # Track decision
        if self.cost_tracker:
            self.cost_tracker.track_decision(decision)

        return Ok(decision)

    def _check_overrides(self, agent_key: str) -> str | None:
        """Check for environment variable overrides.

        Priority:
        1. FORCE_MODEL (global override for testing)
        2. {AGENT}_MODEL (per-agent override)
        """
        # Global override
        force_model = os.getenv("FORCE_MODEL")
        if force_model:
            return force_model

        # Agent-specific override
        agent_override = os.getenv(f"{agent_key.upper()}_MODEL")
        if agent_override:
            return agent_override

        return None

    def _select_model(self, complexity: TaskComplexity) -> tuple[str, bool]:
        """Select model based on complexity tier.

        Returns:
            (selected_model, fallback_used)
        """
        fallback_used = False

        if complexity == TaskComplexity.P3_SIMPLE:
            # Check if local model is available
            use_local = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"

            if use_local and self._is_local_model_available():
                return ("ollama/qwen3-coder:30b", False)
            else:
                # Fallback to cloud
                fallback_used = True
                return ("gpt-4o-mini", True)

        # P1/P2 use cloud models
        return (complexity.recommended_model, False)

    def _is_local_model_available(self) -> bool:
        """Check if local Ollama model is available."""
        try:
            import subprocess

            # Quick check: ollama list
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=2)

            # Check if qwen3-coder is in the list
            return "qwen3-coder" in result.stdout or "qwen" in result.stdout

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Ollama not available or timeout
            return False

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for model and token count.

        Args:
            model: Model identifier
            tokens: Estimated token count (input + output)

        Returns:
            Estimated cost in USD
        """
        # Get pricing for model
        pricing = MODEL_PRICING.get(model)

        if pricing is None:
            # Unknown model, use gpt-4o pricing as safe default
            pricing = MODEL_PRICING["gpt-4o"]

        # Assume 60/40 split (input/output)
        input_tokens = int(tokens * 0.6)
        output_tokens = int(tokens * 0.4)

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost


class CostTracker:
    """Track routing decisions and aggregate cost metrics.

    Integrates with telemetry system for logging.
    """

    def __init__(self, telemetry: Any | None = None):
        """Initialize cost tracker.

        Args:
            telemetry: Telemetry system for logging events
        """
        self.telemetry = telemetry
        self.decisions: list[RoutingDecision] = []

    def track_decision(self, decision: RoutingDecision) -> None:
        """Track a routing decision.

        Args:
            decision: RoutingDecision to track
        """
        self.decisions.append(decision)

        # Log to telemetry
        if self.telemetry:
            self.telemetry.log_event(decision.to_telemetry_event())

    def record_completion(
        self,
        decision: RoutingDecision,
        success: bool,
        actual_tokens: int,
        duration_ms: float,
        vector_store: Any | None = None,
    ) -> None:
        """Record task completion for learning (Article IV).

        Args:
            decision: Original routing decision
            success: Whether task completed successfully
            actual_tokens: Actual token count used
            duration_ms: Task duration in milliseconds
            vector_store: VectorStore for pattern storage (Article IV)
        """
        # Calculate actual cost
        actual_cost = self._calculate_actual_cost(decision.selected_model, actual_tokens)

        # Store pattern in VectorStore (Article IV requirement)
        if vector_store is not None:
            self._store_routing_pattern(vector_store, decision, success, actual_cost, duration_ms)

    def _calculate_actual_cost(self, model: str, tokens: int) -> float:
        """Calculate actual cost from token usage."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o"])

        # Assume 60/40 split
        input_tokens = int(tokens * 0.6)
        output_tokens = int(tokens * 0.4)

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def _store_routing_pattern(
        self,
        vector_store: Any,
        decision: RoutingDecision,
        success: bool,
        actual_cost: float,
        duration_ms: float,
    ) -> None:
        """Store routing pattern to VectorStore (Article IV).

        Args:
            vector_store: VectorStore instance
            decision: Routing decision
            success: Task success
            actual_cost: Actual cost incurred
            duration_ms: Task duration
        """
        pattern = {
            "task_description": decision.task_description,
            "task_type": decision.task_type,
            "classified_complexity": decision.complexity.value,
            "model_used": decision.selected_model,
            "success": success,
            "cost_usd": actual_cost,
            "duration_ms": duration_ms,
            "confidence": 0.9 if success else 0.5,
            "evidence_count": 1,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            vector_store.add_memory(
                f"routing_{decision.task_id}",
                pattern,
                tags=[
                    "routing_pattern",
                    f"complexity_{decision.complexity.value}",
                    f"model_{decision.selected_model.replace('/', '_')}",
                    "adaptive_router",
                ],
                namespace="task_classification",
            )
        except Exception as e:
            # Don't fail task if VectorStore write fails
            print(f"Warning: Failed to store routing pattern: {e}")

    def generate_summary(self, period_start: datetime, period_end: datetime) -> CostSummary:
        """Generate cost summary for time period.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            CostSummary with aggregated metrics
        """
        # Filter decisions in period
        period_decisions = [d for d in self.decisions if period_start <= d.timestamp <= period_end]

        # Count tasks by complexity
        p1_tasks = sum(1 for d in period_decisions if d.complexity == TaskComplexity.P1_COMPLEX)
        p2_tasks = sum(1 for d in period_decisions if d.complexity == TaskComplexity.P2_MODERATE)
        p3_tasks = sum(1 for d in period_decisions if d.complexity == TaskComplexity.P3_SIMPLE)

        # Sum costs by complexity
        p1_cost = sum(
            d.estimated_cost_usd
            for d in period_decisions
            if d.complexity == TaskComplexity.P1_COMPLEX
        )
        p2_cost = sum(
            d.estimated_cost_usd
            for d in period_decisions
            if d.complexity == TaskComplexity.P2_MODERATE
        )
        p3_cost = sum(
            d.estimated_cost_usd
            for d in period_decisions
            if d.complexity == TaskComplexity.P3_SIMPLE
        )

        total_cost = p1_cost + p2_cost + p3_cost
        total_tasks = len(period_decisions)

        # Calculate baseline (all gpt-5)
        baseline_cost = sum(
            d.estimated_tokens * 0.000004  # $4/1M tokens
            for d in period_decisions
        )

        # Calculate routing latencies
        latencies = [d.routing_latency_ms for d in period_decisions]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0.0

        summary = CostSummary(
            period_start=period_start,
            period_end=period_end,
            p1_tasks=p1_tasks,
            p2_tasks=p2_tasks,
            p3_tasks=p3_tasks,
            total_tasks=total_tasks,
            p1_cost_usd=p1_cost,
            p2_cost_usd=p2_cost,
            p3_cost_usd=p3_cost,
            total_cost_usd=total_cost,
            baseline_cost_usd=baseline_cost,
            avg_routing_latency_ms=avg_latency,
            p99_routing_latency_ms=p99_latency,
        )

        summary.calculate_savings()

        return summary
