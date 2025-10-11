"""
Budget Guard for Orchestrator - Production Cost Governance

Prevents runaway costs by validating estimated task graph costs against
daily and per-mission budget limits. Part of Leap 6: Bulletproof Orchestrator.

Constitutional Compliance:
- Article I: Complete context via accurate cost estimation
- Article II: 100% verification through strict budget enforcement
- ADR-008: Strict typing with Pydantic models (no Dict[Any, Any])
- ADR-010: Result pattern for error handling

Example:
    from tools.orchestrator.budget_guard import BudgetGuard, BudgetLimits

    limits = BudgetLimits(daily_usd=10.0, per_mission_usd=2.0)
    guard = BudgetGuard()

    result = guard.check_budget(graph, limits, force=False)
    if result.is_err():
        print(f"Budget exceeded: {result.unwrap_err()}")
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class BudgetLimits(BaseModel):
    """Budget limits for cost governance (ADR-008: Strict typing)."""

    model_config = {"extra": "forbid"}

    daily_usd: float = Field(..., gt=0.0, description="Maximum USD spend per day (24-hour window)")
    per_mission_usd: float = Field(
        ..., gt=0.0, description="Maximum USD spend per single mission/graph execution"
    )

    @field_validator("daily_usd", "per_mission_usd")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        """Ensure budget limits are positive."""
        if v <= 0:
            raise ValueError("Budget limits must be positive")
        return v


class BudgetExceeded(BaseModel):
    """Budget exceeded error with detailed cost breakdown (ADR-008)."""

    model_config = {"extra": "forbid"}

    message: str = Field(..., description="Human-readable error message")
    estimated_cost_usd: float = Field(..., ge=0.0, description="Estimated mission cost in USD")
    daily_limit_usd: float = Field(..., gt=0.0, description="Daily budget limit")
    per_mission_limit_usd: float = Field(..., gt=0.0, description="Per-mission budget limit")
    daily_spent_usd: float = Field(
        ..., ge=0.0, description="Total spent today (24-hour rolling window)"
    )
    would_exceed_daily: bool = Field(..., description="Whether execution would exceed daily limit")
    would_exceed_per_mission: bool = Field(
        ..., description="Whether execution would exceed per-mission limit"
    )
    force_override_available: bool = Field(
        default=True, description="Whether --force flag can override this error"
    )

    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"{self.message} | "
            f"Estimated: ${self.estimated_cost_usd:.4f} | "
            f"Daily: ${self.daily_spent_usd:.4f}/${self.daily_limit_usd:.2f} | "
            f"Per-mission limit: ${self.per_mission_limit_usd:.2f}"
        )


class CostEstimate(BaseModel):
    """Cost estimation breakdown (ADR-008: Strict typing)."""

    model_config = {"extra": "forbid"}

    total_usd: float = Field(..., ge=0.0, description="Total estimated cost in USD")
    total_tokens: int = Field(..., ge=0, description="Total estimated tokens")
    tasks_count: int = Field(..., ge=0, description="Number of tasks in graph")
    cost_per_1k_tokens: float = Field(
        default=0.0025, ge=0.0, description="Cost per 1K tokens (USD)"
    )
    breakdown: dict[str, float] = Field(default_factory=dict, description="Per-task cost breakdown")


class AuditEntry(BaseModel):
    """Audit log entry for budget overrides (ADR-008)."""

    model_config = {"extra": "forbid"}

    timestamp: str = Field(..., description="ISO 8601 timestamp")
    action: str = Field(..., description="Action taken (e.g., 'budget_override')")
    estimated_cost_usd: float = Field(..., ge=0.0, description="Estimated cost")
    daily_limit_usd: float = Field(..., gt=0.0, description="Daily limit at time of override")
    per_mission_limit_usd: float = Field(
        ..., gt=0.0, description="Per-mission limit at time of override"
    )
    daily_spent_usd: float = Field(..., ge=0.0, description="Daily spend at time of override")
    reason: str = Field(..., description="Reason for override (e.g., '--force flag used')")
    user: str = Field(default="system", description="User who triggered override")


class BudgetGuard:
    """
    Budget guard for orchestrator cost governance.

    Validates task graph estimated costs against daily and per-mission limits.
    Supports --force flag override with comprehensive audit logging.

    Constitutional Compliance:
    - ADR-008: Strict typing (Pydantic models, no Dict[Any, Any])
    - ADR-010: Result pattern for error handling
    """

    def __init__(self, audit_log_path: str | None = None):
        """
        Initialize budget guard.

        Args:
            audit_log_path: Path to audit log file (default: logs/budget/audit.jsonl)
        """
        self.audit_log_path = audit_log_path or os.path.join(
            os.getcwd(), "logs", "budget", "audit.jsonl"
        )
        self._ensure_audit_log_dir()

    def _ensure_audit_log_dir(self) -> None:
        """Ensure audit log directory exists."""
        Path(self.audit_log_path).parent.mkdir(parents=True, exist_ok=True)

    def estimate_cost(
        self, total_tokens: int, tasks_count: int, cost_per_1k: float = 0.0025
    ) -> CostEstimate:
        """
        Estimate total cost based on token count.

        Args:
            total_tokens: Total tokens across all tasks
            tasks_count: Number of tasks in graph
            cost_per_1k: Cost per 1K tokens in USD (default: gpt-4o standard)

        Returns:
            CostEstimate with breakdown
        """
        total_usd = (total_tokens / 1000.0) * cost_per_1k

        return CostEstimate(
            total_usd=total_usd,
            total_tokens=total_tokens,
            tasks_count=tasks_count,
            cost_per_1k_tokens=cost_per_1k,
            breakdown={"total": total_usd},
        )

    def get_daily_spend(self) -> float:
        """
        Calculate total spend in last 24 hours from audit log.

        Returns:
            Total USD spent in last 24 hours
        """
        if not os.path.exists(self.audit_log_path):
            return 0.0

        now = datetime.now(UTC)
        daily_spend = 0.0

        try:
            with open(self.audit_log_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry_data = json.loads(line)
                    entry = AuditEntry(**entry_data)

                    # Parse timestamp and check if within 24 hours
                    entry_time = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                    hours_ago = (now - entry_time).total_seconds() / 3600

                    if hours_ago <= 24:
                        daily_spend += entry.estimated_cost_usd
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to read audit log for daily spend: {e}")
            return 0.0

        return daily_spend

    def check_budget(
        self,
        estimated_cost: CostEstimate,
        limits: BudgetLimits,
        force: bool = False,
    ) -> Result[None, BudgetExceeded]:
        """
        Check if estimated cost is within budget limits.

        Args:
            estimated_cost: Cost estimate for task graph
            limits: Budget limits to enforce
            force: Whether to override budget limits (requires audit log)

        Returns:
            Ok(None) if within budget or force=True
            Err(BudgetExceeded) if limits exceeded and force=False

        Constitutional Compliance:
        - ADR-010: Result pattern for explicit error handling
        - Article II: 100% verification (strict budget enforcement)
        """
        daily_spent = self.get_daily_spend()
        would_exceed_daily = (daily_spent + estimated_cost.total_usd) > limits.daily_usd
        would_exceed_per_mission = estimated_cost.total_usd > limits.per_mission_usd

        # Build error if any limit exceeded
        if would_exceed_daily or would_exceed_per_mission:
            error_parts = []
            if would_exceed_per_mission:
                error_parts.append(
                    f"per-mission limit (${estimated_cost.total_usd:.4f} > "
                    f"${limits.per_mission_usd:.2f})"
                )
            if would_exceed_daily:
                projected = daily_spent + estimated_cost.total_usd
                error_parts.append(f"daily limit (${projected:.4f} > ${limits.daily_usd:.2f})")

            error_msg = f"Budget exceeded: {' and '.join(error_parts)}"

            budget_error = BudgetExceeded(
                message=error_msg,
                estimated_cost_usd=estimated_cost.total_usd,
                daily_limit_usd=limits.daily_usd,
                per_mission_limit_usd=limits.per_mission_usd,
                daily_spent_usd=daily_spent,
                would_exceed_daily=would_exceed_daily,
                would_exceed_per_mission=would_exceed_per_mission,
                force_override_available=True,
            )

            # If force=True, log override and allow
            if force:
                self._log_override(budget_error, limits)
                logger.warning(
                    f"BUDGET OVERRIDE: {error_msg} | --force flag used | "
                    f"Logged to {self.audit_log_path}"
                )
                return Ok(None)

            # Otherwise, block execution
            logger.error(str(budget_error))
            return Err(budget_error)

        # Within budget - log normal execution
        self._log_execution(estimated_cost, limits, daily_spent)
        return Ok(None)

    def _log_override(self, error: BudgetExceeded, limits: BudgetLimits) -> None:
        """Log budget override to audit trail."""
        entry = AuditEntry(
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            action="budget_override",
            estimated_cost_usd=error.estimated_cost_usd,
            daily_limit_usd=limits.daily_usd,
            per_mission_limit_usd=limits.per_mission_usd,
            daily_spent_usd=error.daily_spent_usd,
            reason="--force flag used",
            user=os.getenv("USER", "system"),
        )
        self._append_audit_entry(entry)

    def _log_execution(
        self, estimate: CostEstimate, limits: BudgetLimits, daily_spent: float
    ) -> None:
        """Log normal execution to audit trail."""
        entry = AuditEntry(
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            action="budget_check_passed",
            estimated_cost_usd=estimate.total_usd,
            daily_limit_usd=limits.daily_usd,
            per_mission_limit_usd=limits.per_mission_usd,
            daily_spent_usd=daily_spent,
            reason="within budget limits",
            user=os.getenv("USER", "system"),
        )
        self._append_audit_entry(entry)

    def _append_audit_entry(self, entry: AuditEntry) -> None:
        """Append audit entry to JSONL log file."""
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.model_dump(), ensure_ascii=False) + "\n")
        except OSError as e:
            logger.error(f"Failed to write audit log: {e}")
