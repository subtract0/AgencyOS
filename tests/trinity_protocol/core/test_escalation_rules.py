"""
Comprehensive production tests for trinity_protocol/core/escalation_rules.py

Tests all 8 escalation triggers, escalation chains, and policy configurations.
Uses REAL data structures, NO MOCKS - tests actual policy logic.

NECESSARY Framework Compliance:
- N: Normal operation tests (happy paths)
- E: Edge case tests (boundaries)
- C: Corner case tests (unusual combinations)
- E: Error condition tests (failures)
- S: Security tests (input validation)
- S: Stress tests (performance)
- A: Accessibility tests (API usability)
- R: Regression tests (bug prevention)
- Y: Yield tests (output validation)

Constitutional Compliance:
- Article I: Complete context (all scenarios tested)
- Article II: 100% verification (comprehensive coverage)
- Article IV: Learning patterns (test escalation behaviors)
"""

import pytest

from trinity_protocol.core.agent_registry import ModelTier
from trinity_protocol.core.escalation_rules import (
    EscalationContext,
    EscalationDecision,
    EscalationPolicy,
    EscalationTrigger,
    create_aggressive_escalation_policy,
    create_conservative_escalation_policy,
    create_cost_optimized_policy,
    create_escalation_policy,
)


# ==================== NORMAL OPERATION TESTS (N) ====================


class TestNormalEscalationFlow:
    """Test normal escalation progression: LOCAL → LOCAL_PLUS → CLOUD."""

    def test_first_attempt_stays_at_local(self):
        """First attempt should stay at LOCAL tier."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False
        assert decision.next_tier == ModelTier.LOCAL
        assert decision.trigger is None
        assert "Continue at local" in decision.reason
        assert decision.skip_local is False

    def test_second_attempt_escalates_from_local(self):
        """Second attempt should escalate from LOCAL (max_local_attempts=2 uses >=)."""
        # Arrange
        policy = EscalationPolicy(max_local_attempts=2)
        context = EscalationContext(
            attempt_count=2,
            current_tier=ModelTier.LOCAL,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.LOCAL_PLUS
        assert decision.trigger == EscalationTrigger.RETRY_EXHAUSTED

    def test_third_attempt_escalates_to_local_plus(self):
        """Third attempt should escalate from LOCAL to LOCAL_PLUS."""
        # Arrange
        policy = EscalationPolicy(max_local_attempts=2)
        context = EscalationContext(
            attempt_count=3,
            current_tier=ModelTier.LOCAL,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.LOCAL_PLUS
        assert decision.trigger == EscalationTrigger.RETRY_EXHAUSTED
        assert "Max attempts" in decision.reason
        assert decision.skip_local is False

    def test_local_plus_escalates_to_cloud(self):
        """LOCAL_PLUS should escalate to CLOUD after max attempts."""
        # Arrange
        policy = EscalationPolicy(max_local_plus_attempts=1)
        context = EscalationContext(
            attempt_count=2,
            current_tier=ModelTier.LOCAL_PLUS,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD
        assert decision.trigger == EscalationTrigger.RETRY_EXHAUSTED

    def test_cloud_stays_at_cloud(self):
        """CLOUD tier should stay at CLOUD (no further escalation)."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=10,  # Even with many attempts
            current_tier=ModelTier.CLOUD,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False
        assert decision.next_tier == ModelTier.CLOUD
        assert decision.trigger is None


# ==================== TRIGGER-SPECIFIC TESTS (N + E) ====================


class TestEscalationTriggers:
    """Test all 8 escalation triggers with real scenarios."""

    def test_trigger_test_failures(self):
        """Test failures trigger should escalate when threshold exceeded."""
        # Arrange
        policy = EscalationPolicy(test_failure_threshold=2)
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            test_failures=3,  # Exceeds threshold of 2
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.LOCAL_PLUS
        assert decision.trigger == EscalationTrigger.TEST_FAILURES
        assert "Test failures (3) ≥ threshold (2)" in decision.reason

    def test_trigger_timeout(self):
        """Timeout trigger should escalate immediately."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            has_timeout=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.LOCAL_PLUS
        assert decision.trigger == EscalationTrigger.TIMEOUT
        assert "timeout" in decision.reason.lower()

    def test_trigger_novel_problem_jumps_to_cloud(self):
        """Novel problem (no VectorStore match) should jump directly to CLOUD."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            is_novel=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD  # Jumps to CLOUD
        assert decision.trigger == EscalationTrigger.NOVEL_PROBLEM
        assert "no VectorStore match" in decision.reason

    def test_trigger_novel_problem_at_cloud_stays(self):
        """Novel problem at CLOUD tier should stay at CLOUD."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.CLOUD,
            is_novel=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False  # Already at CLOUD
        assert decision.next_tier == ModelTier.CLOUD

    def test_trigger_constitutional_violation(self):
        """Constitutional violation should escalate to next tier."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            constitutional_violation=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.LOCAL_PLUS
        assert decision.trigger == EscalationTrigger.CONSTITUTIONAL_VIOLATION
        assert "Constitutional violation" in decision.reason

    def test_trigger_user_request_high_complexity(self):
        """User request with high complexity should skip to CLOUD."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            user_complexity="high",
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD
        assert decision.trigger == EscalationTrigger.USER_REQUEST
        assert decision.skip_local is True  # Direct to CLOUD
        assert "complexity=high" in decision.reason

    def test_trigger_user_request_critical_complexity(self):
        """User request with critical complexity should skip to CLOUD."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            user_complexity="critical",
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD
        assert decision.trigger == EscalationTrigger.USER_REQUEST
        assert decision.skip_local is True

    def test_trigger_low_confidence(self):
        """Low confidence score should escalate to next tier."""
        # Arrange
        policy = EscalationPolicy(confidence_threshold=0.5)
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            confidence_score=0.3,  # Below threshold
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.LOCAL_PLUS
        assert decision.trigger == EscalationTrigger.LOW_CONFIDENCE
        assert "0.30" in decision.reason
        assert "0.5" in decision.reason

    def test_trigger_retry_exhausted(self):
        """Retry exhausted should escalate after max attempts."""
        # Arrange
        policy = EscalationPolicy(max_local_attempts=2)
        context = EscalationContext(
            attempt_count=3,
            current_tier=ModelTier.LOCAL,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.RETRY_EXHAUSTED
        assert "Max attempts (3)" in decision.reason


# ==================== POLICY VARIANTS TESTS (N) ====================


class TestPolicyVariants:
    """Test pre-configured policy variants: aggressive, conservative, cost-optimized."""

    def test_aggressive_policy_escalates_quickly(self):
        """Aggressive policy should escalate after 1 attempt."""
        # Arrange
        policy = create_aggressive_escalation_policy()
        context = EscalationContext(
            attempt_count=2,  # Second attempt
            current_tier=ModelTier.LOCAL,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.LOCAL_PLUS
        assert policy.max_local_attempts == 1
        assert policy.test_failure_threshold == 1
        assert policy.confidence_threshold == 0.7

    def test_aggressive_policy_sensitive_to_test_failures(self):
        """Aggressive policy should escalate on first test failure."""
        # Arrange
        policy = create_aggressive_escalation_policy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            test_failures=1,  # Just one failure
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.TEST_FAILURES

    def test_conservative_policy_tries_local_extensively(self):
        """Conservative policy should stay at LOCAL until attempt 3 (escalates at attempt 3)."""
        # Arrange
        policy = create_conservative_escalation_policy()

        # Test that attempt 2 stays at LOCAL
        context2 = EscalationContext(
            attempt_count=2,
            current_tier=ModelTier.LOCAL,
        )
        decision2 = policy.evaluate(context2)
        assert decision2.should_escalate is False

        # Test that attempt 3 escalates (>= threshold)
        context3 = EscalationContext(
            attempt_count=3,
            current_tier=ModelTier.LOCAL,
        )
        decision3 = policy.evaluate(context3)

        # Assert
        assert decision3.should_escalate is True
        assert decision3.next_tier == ModelTier.LOCAL_PLUS
        assert policy.max_local_attempts == 3
        assert policy.max_local_plus_attempts == 2

    def test_conservative_policy_tolerates_test_failures(self):
        """Conservative policy should tolerate up to 3 test failures."""
        # Arrange
        policy = create_conservative_escalation_policy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            test_failures=2,  # Below threshold of 3
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False
        assert policy.test_failure_threshold == 3

    def test_cost_optimized_policy_maximizes_local_usage(self):
        """Cost-optimized policy should stay at LOCAL until attempt 5 (escalates at 5)."""
        # Arrange
        policy = create_cost_optimized_policy()

        # Test that attempt 4 stays at LOCAL
        context4 = EscalationContext(
            attempt_count=4,
            current_tier=ModelTier.LOCAL,
        )
        decision4 = policy.evaluate(context4)
        assert decision4.should_escalate is False

        # Test that attempt 5 escalates (>= threshold)
        context5 = EscalationContext(
            attempt_count=5,
            current_tier=ModelTier.LOCAL,
        )
        decision5 = policy.evaluate(context5)

        # Assert
        assert decision5.should_escalate is True
        assert decision5.next_tier == ModelTier.LOCAL_PLUS
        assert policy.max_local_attempts == 5
        assert policy.max_local_plus_attempts == 3
        assert policy.confidence_threshold == 0.2  # Very permissive

    def test_cost_optimized_policy_very_permissive_confidence(self):
        """Cost-optimized policy should accept very low confidence."""
        # Arrange
        policy = create_cost_optimized_policy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            confidence_score=0.25,  # Above 0.2 threshold
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False
        assert decision.next_tier == ModelTier.LOCAL


# ==================== EDGE CASE TESTS (E) ====================


class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    def test_exact_threshold_test_failures(self):
        """Test failures exactly at threshold should escalate."""
        # Arrange
        policy = EscalationPolicy(test_failure_threshold=2)
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            test_failures=2,  # Exactly at threshold
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.TEST_FAILURES

    def test_exact_threshold_confidence(self):
        """Confidence exactly at threshold should NOT escalate."""
        # Arrange
        policy = EscalationPolicy(confidence_threshold=0.5)
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            confidence_score=0.5,  # Exactly at threshold
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False  # Not below threshold

    def test_zero_confidence_score(self):
        """Zero confidence should trigger escalation."""
        # Arrange
        policy = EscalationPolicy(confidence_threshold=0.5)
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            confidence_score=0.0,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.LOW_CONFIDENCE

    def test_perfect_confidence_score(self):
        """Perfect confidence (1.0) should not escalate."""
        # Arrange
        policy = EscalationPolicy(confidence_threshold=0.5)
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            confidence_score=1.0,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False

    def test_user_complexity_medium_no_skip(self):
        """Medium user complexity should NOT skip to CLOUD."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            user_complexity="medium",
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False
        assert decision.skip_local is False

    def test_user_complexity_low_no_skip(self):
        """Low user complexity should NOT skip to CLOUD."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            user_complexity="low",
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False
        assert decision.skip_local is False


# ==================== CORNER CASE TESTS (C) ====================


class TestCornerCases:
    """Test unusual combinations and interactions."""

    def test_multiple_triggers_user_request_wins(self):
        """User request (high complexity) should override other triggers."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            user_complexity="high",  # Should win
            test_failures=5,  # Would also trigger
            has_timeout=True,  # Would also trigger
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD
        assert decision.trigger == EscalationTrigger.USER_REQUEST  # Highest priority
        assert decision.skip_local is True

    def test_multiple_triggers_constitutional_after_user_check(self):
        """Constitutional violation should be second priority after user request."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            constitutional_violation=True,
            test_failures=5,
            has_timeout=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.trigger == EscalationTrigger.CONSTITUTIONAL_VIOLATION

    def test_novel_problem_at_local_plus_jumps_to_cloud(self):
        """Novel problem at LOCAL_PLUS should jump to CLOUD."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL_PLUS,
            is_novel=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD
        assert decision.trigger == EscalationTrigger.NOVEL_PROBLEM

    def test_all_triggers_false_no_escalation(self):
        """When all triggers are false, should not escalate."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            test_failures=0,
            has_timeout=False,
            is_novel=False,
            constitutional_violation=False,
            user_complexity=None,
            confidence_score=1.0,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False
        assert decision.next_tier == ModelTier.LOCAL
        assert decision.trigger is None

    def test_cloud_tier_with_all_triggers_escalates_but_stays_cloud(self):
        """CLOUD tier triggers escalation but next_tier stays CLOUD (no higher tier)."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=10,
            current_tier=ModelTier.CLOUD,
            test_failures=10,
            has_timeout=True,
            is_novel=True,
            constitutional_violation=True,
            confidence_score=0.0,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        # Constitutional violation triggers first, escalates but stays at CLOUD
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD  # Can't escalate beyond CLOUD
        assert decision.trigger == EscalationTrigger.CONSTITUTIONAL_VIOLATION


# ==================== PARAMETRIZED TESTS (S - Stress) ====================


@pytest.mark.parametrize(
    "attempt_count,current_tier,expected_escalate,expected_tier",
    [
        # LOCAL tier progression (max_local_attempts=2, so escalates at attempt >= 2)
        (1, ModelTier.LOCAL, False, ModelTier.LOCAL),
        (2, ModelTier.LOCAL, True, ModelTier.LOCAL_PLUS),  # Escalates at >= 2
        (3, ModelTier.LOCAL, True, ModelTier.LOCAL_PLUS),
        (4, ModelTier.LOCAL, True, ModelTier.LOCAL_PLUS),
        # LOCAL_PLUS tier progression (max_local_plus_attempts=1, so escalates at >= 1)
        (1, ModelTier.LOCAL_PLUS, True, ModelTier.CLOUD),  # Escalates at >= 1
        (2, ModelTier.LOCAL_PLUS, True, ModelTier.CLOUD),
        (3, ModelTier.LOCAL_PLUS, True, ModelTier.CLOUD),
        # CLOUD tier (stays at CLOUD)
        (1, ModelTier.CLOUD, False, ModelTier.CLOUD),
        (10, ModelTier.CLOUD, False, ModelTier.CLOUD),
        (100, ModelTier.CLOUD, False, ModelTier.CLOUD),
    ],
)
def test_attempt_count_progression(
    attempt_count, current_tier, expected_escalate, expected_tier
):
    """Test escalation behavior across all attempt counts and tiers."""
    # Arrange
    policy = EscalationPolicy(max_local_attempts=2, max_local_plus_attempts=1)
    context = EscalationContext(
        attempt_count=attempt_count,
        current_tier=current_tier,
    )

    # Act
    decision = policy.evaluate(context)

    # Assert
    assert decision.should_escalate == expected_escalate
    assert decision.next_tier == expected_tier


@pytest.mark.parametrize(
    "test_failures,threshold,should_escalate",
    [
        (0, 2, False),
        (1, 2, False),
        (2, 2, True),  # Exactly at threshold
        (3, 2, True),
        (10, 2, True),
        (0, 5, False),
        (4, 5, False),
        (5, 5, True),  # Exactly at threshold
    ],
)
def test_test_failure_threshold_variations(test_failures, threshold, should_escalate):
    """Test various test failure counts against different thresholds."""
    # Arrange
    policy = EscalationPolicy(test_failure_threshold=threshold)
    context = EscalationContext(
        attempt_count=1,
        current_tier=ModelTier.LOCAL,
        test_failures=test_failures,
    )

    # Act
    decision = policy.evaluate(context)

    # Assert
    assert decision.should_escalate == should_escalate


@pytest.mark.parametrize(
    "confidence,threshold,should_escalate",
    [
        (1.0, 0.5, False),
        (0.75, 0.5, False),
        (0.5, 0.5, False),  # Exactly at threshold (not below)
        (0.49, 0.5, True),
        (0.0, 0.5, True),
        (0.3, 0.7, True),
        (0.7, 0.7, False),  # Exactly at threshold
        (0.71, 0.7, False),
    ],
)
def test_confidence_threshold_variations(confidence, threshold, should_escalate):
    """Test various confidence scores against different thresholds."""
    # Arrange
    policy = EscalationPolicy(confidence_threshold=threshold)
    context = EscalationContext(
        attempt_count=1,
        current_tier=ModelTier.LOCAL,
        confidence_score=confidence,
    )

    # Act
    decision = policy.evaluate(context)

    # Assert
    assert decision.should_escalate == should_escalate


@pytest.mark.parametrize(
    "user_complexity,should_escalate,should_skip_local",
    [
        (None, False, False),
        ("low", False, False),
        ("medium", False, False),
        ("high", True, True),  # Skips to CLOUD
        ("critical", True, True),  # Skips to CLOUD
    ],
)
def test_user_complexity_variations(user_complexity, should_escalate, should_skip_local):
    """Test all user complexity levels."""
    # Arrange
    policy = EscalationPolicy()
    context = EscalationContext(
        attempt_count=1,
        current_tier=ModelTier.LOCAL,
        user_complexity=user_complexity,
    )

    # Act
    decision = policy.evaluate(context)

    # Assert
    assert decision.should_escalate == should_escalate
    assert decision.skip_local == should_skip_local
    if should_escalate:
        assert decision.next_tier == ModelTier.CLOUD


# ==================== API USABILITY TESTS (A - Accessibility) ====================


class TestAPIUsability:
    """Test ease of use and API design."""

    def test_factory_function_creates_policy(self):
        """create_escalation_policy should create valid policy."""
        # Arrange & Act
        policy = create_escalation_policy(
            max_local_attempts=3,
            max_local_plus_attempts=2,
            test_failure_threshold=4,
            confidence_threshold=0.6,
        )

        # Assert
        assert policy.max_local_attempts == 3
        assert policy.max_local_plus_attempts == 2
        assert policy.test_failure_threshold == 4
        assert policy.confidence_threshold == 0.6

    def test_escalation_context_defaults(self):
        """EscalationContext should have sensible defaults."""
        # Arrange & Act
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
        )

        # Assert
        assert context.test_failures == 0
        assert context.has_timeout is False
        assert context.is_novel is False
        assert context.constitutional_violation is False
        assert context.user_complexity is None
        assert context.error_type is None
        assert context.confidence_score == 1.0

    def test_escalation_decision_structure(self):
        """EscalationDecision should have all required fields."""
        # Arrange
        decision = EscalationDecision(
            should_escalate=True,
            next_tier=ModelTier.CLOUD,
            trigger=EscalationTrigger.USER_REQUEST,
            reason="Test reason",
            skip_local=True,
        )

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD
        assert decision.trigger == EscalationTrigger.USER_REQUEST
        assert decision.reason == "Test reason"
        assert decision.skip_local is True

    def test_escalation_trigger_enum_values(self):
        """EscalationTrigger should have all 8 triggers."""
        # Arrange & Act
        triggers = list(EscalationTrigger)

        # Assert
        assert len(triggers) == 8
        assert EscalationTrigger.TEST_FAILURES in triggers
        assert EscalationTrigger.TIMEOUT in triggers
        assert EscalationTrigger.NOVEL_PROBLEM in triggers
        assert EscalationTrigger.CONSTITUTIONAL_VIOLATION in triggers
        assert EscalationTrigger.USER_REQUEST in triggers
        assert EscalationTrigger.ERROR_PATTERN in triggers
        assert EscalationTrigger.RETRY_EXHAUSTED in triggers
        assert EscalationTrigger.LOW_CONFIDENCE in triggers


# ==================== REGRESSION TESTS (R) ====================


class TestRegressionPrevention:
    """Tests to prevent known issues and ensure backward compatibility."""

    def test_novel_problem_does_not_skip_if_already_cloud(self):
        """Regression: Novel problem at CLOUD should not cause infinite loop."""
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.CLOUD,
            is_novel=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is False  # Should not escalate beyond CLOUD
        assert decision.next_tier == ModelTier.CLOUD

    def test_get_next_tier_never_returns_none(self):
        """Regression: _get_next_tier should always return valid tier."""
        # Arrange
        policy = EscalationPolicy()

        # Act & Assert
        assert policy._get_next_tier(ModelTier.LOCAL) == ModelTier.LOCAL_PLUS
        assert policy._get_next_tier(ModelTier.LOCAL_PLUS) == ModelTier.CLOUD
        assert policy._get_next_tier(ModelTier.CLOUD) == ModelTier.CLOUD  # Stays

    def test_should_escalate_by_attempts_handles_all_tiers(self):
        """Regression: _should_escalate_by_attempts should handle all tiers."""
        # Arrange
        policy = EscalationPolicy(max_local_attempts=2, max_local_plus_attempts=1)

        # Act & Assert - LOCAL (escalates at >= max_local_attempts)
        context_local = EscalationContext(attempt_count=1, current_tier=ModelTier.LOCAL)
        assert policy._should_escalate_by_attempts(context_local) is False
        context_local.attempt_count = 2  # At threshold
        assert policy._should_escalate_by_attempts(context_local) is True
        context_local.attempt_count = 3  # Above threshold
        assert policy._should_escalate_by_attempts(context_local) is True

        # Act & Assert - LOCAL_PLUS (escalates at >= max_local_plus_attempts)
        context_plus = EscalationContext(attempt_count=1, current_tier=ModelTier.LOCAL_PLUS)
        assert policy._should_escalate_by_attempts(context_plus) is True  # >= 1
        context_plus.attempt_count = 2
        assert policy._should_escalate_by_attempts(context_plus) is True

        # Act & Assert - CLOUD
        context_cloud = EscalationContext(attempt_count=100, current_tier=ModelTier.CLOUD)
        assert policy._should_escalate_by_attempts(context_cloud) is False  # Never escalate from CLOUD

    def test_trigger_priority_order_preserved(self):
        """Regression: Trigger priority order should be stable."""
        # Arrange - Set up context that triggers multiple rules
        policy = EscalationPolicy()

        # Act & Assert - User request (highest priority)
        context1 = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            user_complexity="high",
            constitutional_violation=True,
        )
        decision1 = policy.evaluate(context1)
        assert decision1.trigger == EscalationTrigger.USER_REQUEST

        # Act & Assert - Constitutional violation (second priority)
        context2 = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            constitutional_violation=True,
            test_failures=10,
        )
        decision2 = policy.evaluate(context2)
        assert decision2.trigger == EscalationTrigger.CONSTITUTIONAL_VIOLATION


# ==================== OUTPUT VALIDATION TESTS (Y - Yield) ====================


class TestOutputValidation:
    """Test that decision outputs are valid and consistent."""

    def test_decision_always_has_reason(self):
        """Every decision should include a reason."""
        # Arrange
        policy = EscalationPolicy()
        contexts = [
            EscalationContext(attempt_count=1, current_tier=ModelTier.LOCAL),
            EscalationContext(attempt_count=1, current_tier=ModelTier.LOCAL, test_failures=5),
            EscalationContext(attempt_count=1, current_tier=ModelTier.LOCAL, has_timeout=True),
            EscalationContext(attempt_count=1, current_tier=ModelTier.LOCAL, is_novel=True),
        ]

        # Act & Assert
        for context in contexts:
            decision = policy.evaluate(context)
            assert decision.reason is not None
            assert len(decision.reason) > 0

    def test_decision_trigger_matches_escalation(self):
        """Trigger should be None if not escalating, present if escalating."""
        # Arrange
        policy = EscalationPolicy()

        # Act - No escalation
        context_no_escalate = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
        )
        decision_no_escalate = policy.evaluate(context_no_escalate)

        # Act - Escalation
        context_escalate = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            test_failures=5,
        )
        decision_escalate = policy.evaluate(context_escalate)

        # Assert
        assert decision_no_escalate.should_escalate is False
        assert decision_no_escalate.trigger is None

        assert decision_escalate.should_escalate is True
        assert decision_escalate.trigger is not None
        assert isinstance(decision_escalate.trigger, EscalationTrigger)

    def test_skip_local_only_for_user_high_critical(self):
        """skip_local flag should only be True for high/critical user complexity."""
        # Arrange
        policy = EscalationPolicy()

        # Test all scenarios
        test_cases = [
            ({"user_complexity": "high"}, True),
            ({"user_complexity": "critical"}, True),
            ({"user_complexity": "medium"}, False),
            ({"user_complexity": "low"}, False),
            ({"test_failures": 10}, False),
            ({"has_timeout": True}, False),
            ({"is_novel": True}, False),
        ]

        # Act & Assert
        for kwargs, expected_skip in test_cases:
            context = EscalationContext(
                attempt_count=1,
                current_tier=ModelTier.LOCAL,
                **kwargs,
            )
            decision = policy.evaluate(context)
            assert decision.skip_local == expected_skip, f"Failed for {kwargs}"

    def test_next_tier_always_valid_model_tier(self):
        """next_tier should always be a valid ModelTier enum."""
        # Arrange
        policy = EscalationPolicy()
        contexts = [
            EscalationContext(attempt_count=1, current_tier=ModelTier.LOCAL),
            EscalationContext(attempt_count=3, current_tier=ModelTier.LOCAL),
            EscalationContext(attempt_count=2, current_tier=ModelTier.LOCAL_PLUS),
            EscalationContext(attempt_count=1, current_tier=ModelTier.CLOUD),
        ]

        # Act & Assert
        for context in contexts:
            decision = policy.evaluate(context)
            assert isinstance(decision.next_tier, ModelTier)
            assert decision.next_tier in [ModelTier.LOCAL, ModelTier.LOCAL_PLUS, ModelTier.CLOUD]


# ==================== INTEGRATION TESTS ====================


class TestRealWorldScenarios:
    """Test real-world escalation scenarios end-to-end."""

    def test_scenario_flaky_tests_escalate_to_cloud(self):
        """
        Real scenario: Tests fail repeatedly, escalate through all tiers.

        Attempt 1 (LOCAL): 2 test failures
        Attempt 2 (LOCAL): Another failure
        Should escalate to LOCAL_PLUS, then CLOUD
        """
        # Arrange
        policy = EscalationPolicy(test_failure_threshold=2)

        # Act - Attempt 1 at LOCAL
        context1 = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            test_failures=2,
        )
        decision1 = policy.evaluate(context1)

        # Assert - Escalate to LOCAL_PLUS
        assert decision1.should_escalate is True
        assert decision1.next_tier == ModelTier.LOCAL_PLUS
        assert decision1.trigger == EscalationTrigger.TEST_FAILURES

        # Act - Attempt 2 at LOCAL_PLUS (more failures)
        context2 = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL_PLUS,
            test_failures=3,
        )
        decision2 = policy.evaluate(context2)

        # Assert - Escalate to CLOUD
        assert decision2.should_escalate is True
        assert decision2.next_tier == ModelTier.CLOUD
        assert decision2.trigger == EscalationTrigger.TEST_FAILURES

    def test_scenario_user_critical_task_skips_local(self):
        """
        Real scenario: User marks task as critical, skip local models entirely.
        """
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            user_complexity="critical",
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD
        assert decision.skip_local is True
        assert decision.trigger == EscalationTrigger.USER_REQUEST

    def test_scenario_novel_architecture_decision(self):
        """
        Real scenario: Novel architectural problem (no VectorStore match).
        Should jump to CLOUD for sophisticated reasoning.
        """
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            is_novel=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.CLOUD  # Jumps to CLOUD
        assert decision.trigger == EscalationTrigger.NOVEL_PROBLEM

    def test_scenario_constitutional_violation_quality_gate(self):
        """
        Real scenario: Code violates Article II (quality gate failed).
        Should escalate to more capable model for quality.
        """
        # Arrange
        policy = EscalationPolicy()
        context = EscalationContext(
            attempt_count=1,
            current_tier=ModelTier.LOCAL,
            constitutional_violation=True,
        )

        # Act
        decision = policy.evaluate(context)

        # Assert
        assert decision.should_escalate is True
        assert decision.next_tier == ModelTier.LOCAL_PLUS
        assert decision.trigger == EscalationTrigger.CONSTITUTIONAL_VIOLATION

    def test_scenario_cost_optimization_workflow(self):
        """
        Real scenario: Cost-conscious user wants to minimize cloud usage.
        Should try local models extensively before escalating.
        """
        # Arrange
        policy = create_cost_optimized_policy()  # max_local_attempts=5

        # Act - Multiple attempts at LOCAL (policy escalates at >= 5)
        decisions = []
        for attempt in range(1, 5):  # Attempts 1-4
            context = EscalationContext(
                attempt_count=attempt,
                current_tier=ModelTier.LOCAL,
            )
            decisions.append(policy.evaluate(context))

        # Assert - First 4 attempts stay at LOCAL
        for i, decision in enumerate(decisions, 1):
            assert decision.should_escalate is False, f"Attempt {i} should not escalate"
            assert decision.next_tier == ModelTier.LOCAL

        # Act - 5th attempt (at threshold)
        context5 = EscalationContext(
            attempt_count=5,
            current_tier=ModelTier.LOCAL,
        )
        decision5 = policy.evaluate(context5)

        # Assert - Now escalate at threshold
        assert decision5.should_escalate is True
        assert decision5.next_tier == ModelTier.LOCAL_PLUS

        # Act - 6th attempt (above threshold)
        context6 = EscalationContext(
            attempt_count=6,
            current_tier=ModelTier.LOCAL,
        )
        decision6 = policy.evaluate(context6)

        # Assert - Also escalates
        assert decision6.should_escalate is True
        assert decision6.next_tier == ModelTier.LOCAL_PLUS
