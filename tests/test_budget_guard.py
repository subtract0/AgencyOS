"""
Comprehensive Tests for Budget Guard

Tests budget governance, cost estimation, audit logging, and --force override.

Constitutional Compliance:
- Article I: Complete context (accurate cost calculation)
- Article II: 100% verification (all tests must pass)
- ADR-008: Strict typing validation
"""

import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tools.orchestrator.budget_guard import (
    AuditEntry,
    BudgetExceeded,
    BudgetGuard,
    BudgetLimits,
    CostEstimate,
)


class TestBudgetLimits:
    """Test BudgetLimits Pydantic model validation (ADR-008)."""

    def test_valid_budget_limits(self) -> None:
        """Test valid budget limits creation."""
        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=2.0)
        assert limits.daily_usd == 10.0
        assert limits.per_mission_usd == 2.0

    def test_zero_budget_raises_error(self) -> None:
        """Test zero budget limits are rejected."""
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            BudgetLimits(daily_usd=0.0, per_mission_usd=2.0)

    def test_negative_budget_raises_error(self) -> None:
        """Test negative budget limits are rejected."""
        with pytest.raises(ValueError):
            BudgetLimits(daily_usd=-5.0, per_mission_usd=2.0)

    def test_extra_fields_forbidden(self) -> None:
        """Test strict typing - extra fields forbidden."""
        with pytest.raises(ValueError):
            BudgetLimits(daily_usd=10.0, per_mission_usd=2.0, extra_field="invalid")


class TestCostEstimate:
    """Test cost estimation logic."""

    def test_estimate_cost_calculation(self) -> None:
        """Test cost calculation: tokens * cost_per_1k."""
        guard = BudgetGuard()
        estimate = guard.estimate_cost(total_tokens=10000, tasks_count=5, cost_per_1k=0.0025)

        assert estimate.total_tokens == 10000
        assert estimate.tasks_count == 5
        assert estimate.cost_per_1k_tokens == 0.0025
        # 10000 tokens / 1000 * 0.0025 = 0.025
        assert estimate.total_usd == 0.025

    def test_estimate_cost_zero_tokens(self) -> None:
        """Test cost estimation with zero tokens."""
        guard = BudgetGuard()
        estimate = guard.estimate_cost(total_tokens=0, tasks_count=1, cost_per_1k=0.0025)

        assert estimate.total_usd == 0.0
        assert estimate.total_tokens == 0

    def test_estimate_cost_high_cost_model(self) -> None:
        """Test cost estimation with expensive model (gpt-5)."""
        guard = BudgetGuard()
        estimate = guard.estimate_cost(
            total_tokens=5000,
            tasks_count=1,
            cost_per_1k=0.004,  # gpt-5 pricing
        )

        # 5000 / 1000 * 0.004 = 0.02
        assert estimate.total_usd == 0.02


class TestBudgetCheck:
    """Test budget validation logic."""

    @pytest.fixture
    def temp_audit_log(self) -> str:
        """Create temporary audit log path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            return f.name

    def test_within_budget_passes(self, temp_audit_log: str) -> None:
        """Test execution passes when within budget."""
        guard = BudgetGuard(audit_log_path=temp_audit_log)
        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=2.0)
        estimate = guard.estimate_cost(total_tokens=1000, tasks_count=1, cost_per_1k=0.0025)

        result = guard.check_budget(estimate, limits, force=False)

        assert result.is_ok()

    def test_exceeds_per_mission_limit(self, temp_audit_log: str) -> None:
        """Test execution blocked when per-mission limit exceeded."""
        guard = BudgetGuard(audit_log_path=temp_audit_log)
        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=0.01)
        estimate = guard.estimate_cost(
            total_tokens=10000, tasks_count=1, cost_per_1k=0.0025
        )  # $0.025

        result = guard.check_budget(estimate, limits, force=False)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.would_exceed_per_mission is True
        assert error.estimated_cost_usd == 0.025
        assert "per-mission limit" in error.message

    def test_exceeds_daily_limit(self, temp_audit_log: str) -> None:
        """Test execution blocked when daily limit exceeded."""
        guard = BudgetGuard(audit_log_path=temp_audit_log)

        # Pre-populate audit log with $9.50 spend today
        past_entry = AuditEntry(
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            action="budget_override",
            estimated_cost_usd=9.5,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=0.0,
            reason="test setup",
        )
        with open(temp_audit_log, "w", encoding="utf-8") as f:
            f.write(json.dumps(past_entry.model_dump()) + "\n")

        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=5.0)
        estimate = guard.estimate_cost(
            total_tokens=2000, tasks_count=1, cost_per_1k=0.0025
        )  # $0.005

        result = guard.check_budget(estimate, limits, force=False)

        # Daily spend: 9.5 + 0.005 = 9.505 > 10.0 (WAIT, this should pass!)
        # Let me recalculate: 9.5 + 0.005 = 9.505 < 10.0
        # Need higher new cost
        estimate_high = guard.estimate_cost(
            total_tokens=400000, tasks_count=1, cost_per_1k=0.0025
        )  # $1.0

        result_high = guard.check_budget(estimate_high, limits, force=False)
        assert result_high.is_err()
        error = result_high.unwrap_err()
        assert error.would_exceed_daily is True
        # Daily spent includes the last check, so it's 9.5 + 0.005 = 9.505
        assert error.daily_spent_usd > 9.5
        assert "daily limit" in error.message

    def test_force_override_allows_execution(self, temp_audit_log: str) -> None:
        """Test --force flag overrides budget limits."""
        guard = BudgetGuard(audit_log_path=temp_audit_log)
        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=0.01)
        estimate = guard.estimate_cost(
            total_tokens=10000, tasks_count=1, cost_per_1k=0.0025
        )  # $0.025 > $0.01

        result = guard.check_budget(estimate, limits, force=True)

        assert result.is_ok()

        # Verify audit log contains override entry
        with open(temp_audit_log, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
            assert len(entries) >= 1
            override_entry = entries[-1]
            assert override_entry["action"] == "budget_override"
            assert override_entry["reason"] == "--force flag used"


class TestDailySpendCalculation:
    """Test daily spend calculation from audit log."""

    @pytest.fixture
    def temp_audit_log(self) -> str:
        """Create temporary audit log path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            return f.name

    def test_empty_audit_log_returns_zero(self, temp_audit_log: str) -> None:
        """Test daily spend is zero when no audit log exists."""
        os.remove(temp_audit_log)  # Ensure it doesn't exist
        guard = BudgetGuard(audit_log_path=temp_audit_log)

        daily_spend = guard.get_daily_spend()

        assert daily_spend == 0.0

    def test_daily_spend_sums_last_24_hours(self, temp_audit_log: str) -> None:
        """Test daily spend sums entries from last 24 hours."""
        guard = BudgetGuard(audit_log_path=temp_audit_log)

        now = datetime.now(UTC)
        entries = [
            AuditEntry(
                timestamp=(now - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
                action="budget_check_passed",
                estimated_cost_usd=2.0,
                daily_limit_usd=10.0,
                per_mission_limit_usd=5.0,
                daily_spent_usd=0.0,
                reason="within budget",
            ),
            AuditEntry(
                timestamp=(now - timedelta(hours=12)).isoformat().replace("+00:00", "Z"),
                action="budget_override",
                estimated_cost_usd=3.5,
                daily_limit_usd=10.0,
                per_mission_limit_usd=5.0,
                daily_spent_usd=2.0,
                reason="--force",
            ),
            AuditEntry(
                timestamp=(now - timedelta(hours=30)).isoformat().replace("+00:00", "Z"),
                action="budget_check_passed",
                estimated_cost_usd=100.0,  # Too old, should be excluded
                daily_limit_usd=10.0,
                per_mission_limit_usd=5.0,
                daily_spent_usd=0.0,
                reason="old entry",
            ),
        ]

        with open(temp_audit_log, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry.model_dump()) + "\n")

        daily_spend = guard.get_daily_spend()

        # Should sum only first two entries: 2.0 + 3.5 = 5.5
        assert daily_spend == 5.5


class TestAuditLogging:
    """Test audit log functionality."""

    @pytest.fixture
    def temp_audit_log(self) -> str:
        """Create temporary audit log path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            return f.name

    def test_audit_log_created_on_first_check(self, temp_audit_log: str) -> None:
        """Test audit log file is created on first check."""
        os.remove(temp_audit_log)
        guard = BudgetGuard(audit_log_path=temp_audit_log)
        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=5.0)
        estimate = guard.estimate_cost(total_tokens=1000, tasks_count=1)

        guard.check_budget(estimate, limits, force=False)

        assert os.path.exists(temp_audit_log)

    def test_audit_log_jsonl_format(self, temp_audit_log: str) -> None:
        """Test audit log uses JSONL format (one JSON per line)."""
        guard = BudgetGuard(audit_log_path=temp_audit_log)
        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=5.0)

        # Execute two budget checks
        estimate1 = guard.estimate_cost(total_tokens=1000, tasks_count=1)
        estimate2 = guard.estimate_cost(total_tokens=2000, tasks_count=2)

        guard.check_budget(estimate1, limits, force=False)
        guard.check_budget(estimate2, limits, force=False)

        # Verify JSONL format
        with open(temp_audit_log, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            assert len(lines) == 2
            for line in lines:
                entry = json.loads(line)  # Should parse as valid JSON
                assert "timestamp" in entry
                assert "action" in entry
                assert "estimated_cost_usd" in entry

    def test_audit_log_contains_user_info(self, temp_audit_log: str) -> None:
        """Test audit log captures user information."""
        os.environ["USER"] = "test_user"
        guard = BudgetGuard(audit_log_path=temp_audit_log)
        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=0.01)
        estimate = guard.estimate_cost(total_tokens=10000, tasks_count=1)

        guard.check_budget(estimate, limits, force=True)

        with open(temp_audit_log, encoding="utf-8") as f:
            entry = json.loads(f.readline())
            assert entry["user"] == "test_user"


class TestBudgetExceededModel:
    """Test BudgetExceeded Pydantic model."""

    def test_budget_exceeded_string_representation(self) -> None:
        """Test BudgetExceeded __str__ method."""
        error = BudgetExceeded(
            message="Budget exceeded: per-mission limit",
            estimated_cost_usd=0.05,
            daily_limit_usd=10.0,
            per_mission_limit_usd=0.02,
            daily_spent_usd=3.5,
            would_exceed_daily=False,
            would_exceed_per_mission=True,
        )

        error_str = str(error)

        assert "Budget exceeded" in error_str
        assert "$0.0500" in error_str
        assert "$3.5000" in error_str  # Format is 4 decimal places
        assert "$10.00" in error_str
        assert "$0.02" in error_str

    def test_budget_exceeded_validation(self) -> None:
        """Test BudgetExceeded model validation."""
        error = BudgetExceeded(
            message="Test",
            estimated_cost_usd=0.05,
            daily_limit_usd=10.0,
            per_mission_limit_usd=0.02,
            daily_spent_usd=3.5,
            would_exceed_daily=False,
            would_exceed_per_mission=True,
        )

        assert error.force_override_available is True


class TestIntegration:
    """Integration tests simulating real usage."""

    @pytest.fixture
    def temp_audit_log(self) -> str:
        """Create temporary audit log path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            return f.name

    def test_full_workflow_within_budget(self, temp_audit_log: str) -> None:
        """Test full workflow: estimate → check → pass."""
        guard = BudgetGuard(audit_log_path=temp_audit_log)
        limits = BudgetLimits(daily_usd=100.0, per_mission_usd=10.0)

        # Simulate 5 missions throughout the day
        for i in range(5):
            estimate = guard.estimate_cost(
                total_tokens=2000 * (i + 1), tasks_count=i + 1, cost_per_1k=0.0025
            )
            result = guard.check_budget(estimate, limits, force=False)
            assert result.is_ok()

        # Verify daily spend is cumulative
        daily_spend = guard.get_daily_spend()
        assert daily_spend > 0

    def test_full_workflow_budget_exceeded_then_override(self, temp_audit_log: str) -> None:
        """Test workflow: exceed budget → blocked → override with --force."""
        guard = BudgetGuard(audit_log_path=temp_audit_log)
        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=5.0)

        # Mission that exceeds per-mission limit
        expensive_estimate = guard.estimate_cost(
            total_tokens=3000000, tasks_count=10, cost_per_1k=0.0025
        )  # $7.5

        # First attempt: should fail
        result_blocked = guard.check_budget(expensive_estimate, limits, force=False)
        assert result_blocked.is_err()

        # Second attempt with --force: should pass
        result_override = guard.check_budget(expensive_estimate, limits, force=True)
        assert result_override.is_ok()

        # Verify override logged
        with open(temp_audit_log, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
            override_entries = [e for e in entries if e["action"] == "budget_override"]
            assert len(override_entries) == 1
            assert override_entries[0]["reason"] == "--force flag used"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
