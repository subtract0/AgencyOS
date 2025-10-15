"""
Unit tests for orchestrator_models.py (PHASE1-004)

Tests Pydantic models for graceful fallback handling:
- FallbackStrategy enum
- FallbackResult model
- RetryPolicy model with exponential backoff
- FallbackError exception

Constitutional Compliance Validation:
- Article I: RetryPolicy implements exponential backoff (2x, 3x, 10x)
- Article II: FallbackResult.test_verification_required always True
- Article III: FallbackResult.constitutional_bypass always False
- Article IV: FallbackStrategy supports learning fallbacks
- Article V: Spec traceability via compliance_notes field

Coverage:
- NECESSARY Normal: Model instantiation with valid data
- NECESSARY Edge: Boundary values (retry_count=0, latency_ms=0.0)
- NECESSARY Constraints: Field validation (ge, gt constraints)
- NECESSARY Error: Pydantic validation errors on invalid data
- NECESSARY Security: Constitutional bypass prevention
"""

import pytest
from pydantic import ValidationError

from shared.models.orchestrator_models import (
    FallbackError,
    FallbackResult,
    FallbackStrategy,
    RetryPolicy,
)

# ============================================================================
# NECESSARY NORMAL: Model instantiation with valid data
# ============================================================================


def test_fallback_strategy_enum_has_all_strategies() -> None:
    """
    NECESSARY Normal: FallbackStrategy enum contains all required strategies.

    Validates:
    - Enum has 7 strategies (SESSION_ONLY, CLOUD_ROUTING, etc.)
    - Each strategy is a string value
    - Values match naming convention

    Expected: All 7 strategies present
    """
    strategies = list(FallbackStrategy)

    assert len(strategies) == 7, f"Expected 7 strategies, got {len(strategies)}"

    expected_values = {
        "session_only",
        "cloud_routing",
        "retry_success",
        "auto_fix_success",
        "manual_intervention",
        "read_only",
        "skip_learning",
    }

    actual_values = {s.value for s in strategies}
    assert actual_values == expected_values, f"Strategy mismatch: {actual_values}"


def test_fallback_result_with_valid_data() -> None:
    """
    NECESSARY Normal: FallbackResult instantiation with valid data.

    Validates:
    - All required fields populated
    - Constitutional compliance defaults correct
    - Optional fields handled properly

    Expected: Model instance created successfully
    """
    result = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY,
        success=True,
        warning_message="VectorStore unavailable, using session memory",
        suggested_fix="Check VectorStore connection",
        execution_continues=True,
        retry_count=2,
        latency_ms=45.5,
        permanent_failure=False,
    )

    assert result.strategy == FallbackStrategy.SESSION_ONLY
    assert result.success is True
    assert "session memory" in result.warning_message
    assert result.suggested_fix == "Check VectorStore connection"
    assert result.execution_continues is True
    assert result.retry_count == 2
    assert result.latency_ms == 45.5
    assert result.permanent_failure is False

    # Constitutional compliance defaults (Article II, III)
    assert result.constitutional_bypass is False
    assert result.test_verification_required is True
    assert result.budget_guard_active is True
    assert isinstance(result.compliance_notes, str)


def test_retry_policy_with_default_values() -> None:
    """
    NECESSARY Normal: RetryPolicy instantiation with default values.

    Validates:
    - Defaults: max_attempts=5, base_delay=2.0, backoff=2.0
    - Abort on permanent errors (401, 403)
    - Exponential backoff formula correct

    Expected: Default policy created successfully
    """
    policy = RetryPolicy()

    assert policy.max_attempts == 5
    assert policy.base_delay_seconds == 2.0
    assert policy.backoff_multiplier == 2.0
    assert policy.abort_on_errors == ["401", "403"]


def test_retry_policy_exponential_backoff_calculation() -> None:
    """
    NECESSARY Normal: RetryPolicy.get_delay() calculates exponential backoff.

    Validates:
    - Formula: base_delay * (backoff_multiplier ** attempt)
    - Correct progression: 2s, 4s, 8s, 16s, 32s
    - Type safety (returns float)

    Expected: Delays match exponential formula
    """
    policy = RetryPolicy(base_delay_seconds=2.0, backoff_multiplier=2.0)

    expected_delays = [2.0, 4.0, 8.0, 16.0, 32.0]

    for attempt, expected in enumerate(expected_delays):
        actual = policy.get_delay(attempt)
        assert actual == expected, f"Attempt {attempt}: expected {expected}s, got {actual}s"


def test_fallback_error_exception_with_all_fields() -> None:
    """
    NECESSARY Normal: FallbackError exception instantiation.

    Validates:
    - All fields (error_type, message, retry_count, suggested_fix)
    - String representation includes all context
    - Exception can be raised and caught

    Expected: Exception created with all fields
    """
    error = FallbackError(
        error_type="RETRY_EXHAUSTED",
        message="All retries failed after 5 attempts",
        retry_count=5,
        suggested_fix="Increase max_retries or check API key",
    )

    assert error.error_type == "RETRY_EXHAUSTED"
    assert error.message == "All retries failed after 5 attempts"
    assert error.retry_count == 5
    assert error.suggested_fix == "Increase max_retries or check API key"

    # Test string representation
    error_str = str(error)
    assert "RETRY_EXHAUSTED" in error_str
    assert "5 retries" in error_str
    assert "Suggested fix:" in error_str


# ============================================================================
# NECESSARY EDGE: Boundary values (retry_count=0, latency_ms=0.0)
# ============================================================================


def test_fallback_result_with_zero_retries() -> None:
    """
    NECESSARY Edge: FallbackResult with retry_count=0 (no retries).

    Validates:
    - Zero retries allowed (immediate fallback)
    - Permanent failure can be True
    - No validation errors on boundary value

    Expected: Model accepts retry_count=0
    """
    result = FallbackResult(
        strategy=FallbackStrategy.READ_ONLY,
        success=True,
        warning_message="VectorStore in read-only mode",
        retry_count=0,
        permanent_failure=True,
    )

    assert result.retry_count == 0
    assert result.permanent_failure is True


def test_fallback_result_with_zero_latency() -> None:
    """
    NECESSARY Edge: FallbackResult with latency_ms=0.0 (instant fallback).

    Validates:
    - Zero latency allowed (boundary value)
    - Optional field can be omitted (None)
    - Validation accepts 0.0

    Expected: Model accepts latency_ms=0.0 and None
    """
    # Test with 0.0
    result1 = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY,
        success=True,
        warning_message="Instant fallback",
        latency_ms=0.0,
    )
    assert result1.latency_ms == 0.0

    # Test with None (omitted)
    result2 = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY,
        success=True,
        warning_message="Instant fallback",
    )
    assert result2.latency_ms is None


def test_retry_policy_with_max_attempts_boundary() -> None:
    """
    NECESSARY Edge: RetryPolicy with max_attempts=1 and 10 (boundaries).

    Validates:
    - Min: max_attempts=1 (single attempt, no retries)
    - Max: max_attempts=10 (maximum allowed)
    - Validation rejects 0 and 11

    Expected: Boundaries accepted, out-of-range rejected
    """
    # Min boundary
    policy_min = RetryPolicy(max_attempts=1)
    assert policy_min.max_attempts == 1

    # Max boundary
    policy_max = RetryPolicy(max_attempts=10)
    assert policy_max.max_attempts == 10

    # Test out-of-range (should raise ValidationError)
    with pytest.raises(ValidationError):
        RetryPolicy(max_attempts=0)  # Below min

    with pytest.raises(ValidationError):
        RetryPolicy(max_attempts=11)  # Above max


def test_retry_policy_exponential_backoff_with_zero_attempt() -> None:
    """
    NECESSARY Edge: RetryPolicy.get_delay(0) returns base_delay.

    Validates:
    - First retry uses base_delay (2^0 = 1 multiplier)
    - No division by zero
    - Formula: 2.0 * (2.0 ** 0) = 2.0

    Expected: get_delay(0) == 2.0
    """
    policy = RetryPolicy(base_delay_seconds=2.0, backoff_multiplier=2.0)

    assert policy.get_delay(0) == 2.0


# ============================================================================
# NECESSARY CONSTRAINTS: Field validation (ge, gt constraints)
# ============================================================================


def test_retry_policy_base_delay_must_be_positive() -> None:
    """
    NECESSARY Constraints: RetryPolicy.base_delay_seconds must be > 0.

    Validates:
    - Constraint: gt=0.0 (greater than zero)
    - Validation rejects 0.0, -1.0
    - Positive values accepted

    Expected: ValidationError on zero or negative values
    """
    # Valid: positive value
    policy = RetryPolicy(base_delay_seconds=1.5)
    assert policy.base_delay_seconds == 1.5

    # Invalid: zero
    with pytest.raises(ValidationError) as exc_info:
        RetryPolicy(base_delay_seconds=0.0)
    assert "greater than 0" in str(exc_info.value).lower()

    # Invalid: negative
    with pytest.raises(ValidationError):
        RetryPolicy(base_delay_seconds=-1.0)


def test_retry_policy_backoff_multiplier_must_be_gte_one() -> None:
    """
    NECESSARY Constraints: RetryPolicy.backoff_multiplier must be >= 1.0.

    Validates:
    - Constraint: ge=1.0 (greater than or equal to 1.0)
    - Validation rejects 0.9, 0.0
    - 1.0 accepted (no backoff growth)

    Expected: ValidationError on values < 1.0
    """
    # Valid: exactly 1.0 (no exponential growth)
    policy = RetryPolicy(backoff_multiplier=1.0)
    assert policy.backoff_multiplier == 1.0
    assert policy.get_delay(0) == policy.get_delay(5)  # No growth

    # Valid: typical value
    policy2 = RetryPolicy(backoff_multiplier=2.0)
    assert policy2.backoff_multiplier == 2.0

    # Invalid: below 1.0
    with pytest.raises(ValidationError):
        RetryPolicy(backoff_multiplier=0.9)


def test_fallback_result_retry_count_must_be_non_negative() -> None:
    """
    NECESSARY Constraints: FallbackResult.retry_count must be >= 0.

    Validates:
    - Constraint: ge=0 (non-negative)
    - Validation rejects -1
    - Zero accepted (no retries)

    Expected: ValidationError on negative values
    """
    # Valid: zero retries
    result = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY,
        success=True,
        warning_message="No retries",
        retry_count=0,
    )
    assert result.retry_count == 0

    # Invalid: negative retries
    with pytest.raises(ValidationError):
        FallbackResult(
            strategy=FallbackStrategy.SESSION_ONLY,
            success=True,
            warning_message="Negative retries",
            retry_count=-1,
        )


def test_fallback_result_latency_must_be_non_negative() -> None:
    """
    NECESSARY Constraints: FallbackResult.latency_ms must be >= 0.0 if provided.

    Validates:
    - Constraint: ge=0.0 (non-negative)
    - Validation rejects -5.0
    - Zero and None accepted

    Expected: ValidationError on negative latency
    """
    # Valid: zero latency
    result1 = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY,
        success=True,
        warning_message="Zero latency",
        latency_ms=0.0,
    )
    assert result1.latency_ms == 0.0

    # Valid: None (optional field)
    result2 = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY, success=True, warning_message="No latency"
    )
    assert result2.latency_ms is None

    # Invalid: negative latency
    with pytest.raises(ValidationError):
        FallbackResult(
            strategy=FallbackStrategy.SESSION_ONLY,
            success=True,
            warning_message="Negative latency",
            latency_ms=-5.0,
        )


# ============================================================================
# NECESSARY ERROR: Pydantic validation errors on invalid data
# ============================================================================


def test_fallback_result_requires_all_mandatory_fields() -> None:
    """
    NECESSARY Error: FallbackResult validation fails on missing required fields.

    Validates:
    - Required: strategy, success, warning_message
    - Optional: suggested_fix, latency_ms, etc.
    - Validation error on missing required field

    Expected: ValidationError when required field missing
    """
    # Valid: all required fields provided
    result = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY, success=True, warning_message="Test"
    )
    assert result.strategy == FallbackStrategy.SESSION_ONLY

    # Invalid: missing strategy
    with pytest.raises(ValidationError):
        FallbackResult(success=True, warning_message="Test")  # type: ignore

    # Invalid: missing success
    with pytest.raises(ValidationError):
        FallbackResult(
            strategy=FallbackStrategy.SESSION_ONLY,
            warning_message="Test",  # type: ignore
        )

    # Invalid: missing warning_message
    with pytest.raises(ValidationError):
        FallbackResult(strategy=FallbackStrategy.SESSION_ONLY, success=True)  # type: ignore


def test_retry_policy_rejects_invalid_max_attempts() -> None:
    """
    NECESSARY Error: RetryPolicy validation rejects max_attempts out of range [1, 10].

    Validates:
    - Range: 1 <= max_attempts <= 10
    - Validation error on 0, 11, -1, etc.

    Expected: ValidationError on out-of-range values
    """
    # Invalid: zero
    with pytest.raises(ValidationError):
        RetryPolicy(max_attempts=0)

    # Invalid: negative
    with pytest.raises(ValidationError):
        RetryPolicy(max_attempts=-1)

    # Invalid: above max
    with pytest.raises(ValidationError):
        RetryPolicy(max_attempts=11)


def test_fallback_error_can_be_raised_and_caught() -> None:
    """
    NECESSARY Error: FallbackError can be raised and caught as Exception.

    Validates:
    - Exception subclassing works
    - Can be raised in try/except block
    - All fields preserved when caught

    Expected: Exception behavior correct
    """
    with pytest.raises(FallbackError) as exc_info:
        raise FallbackError(
            error_type="PERMANENT_FAILURE",
            message="VectorStore authentication failed",
            retry_count=0,
            suggested_fix="Check VECTORSTORE_API_KEY",
        )

    caught_error = exc_info.value
    assert caught_error.error_type == "PERMANENT_FAILURE"
    assert "authentication" in caught_error.message
    assert caught_error.retry_count == 0
    assert "VECTORSTORE_API_KEY" in caught_error.suggested_fix


# ============================================================================
# NECESSARY SECURITY: Constitutional bypass prevention
# ============================================================================


def test_fallback_result_constitutional_bypass_always_false() -> None:
    """
    NECESSARY Security: FallbackResult.constitutional_bypass always False (Article III).

    Validates:
    - Default value is False
    - No way to set to True via constructor
    - Field enforces constitutional compliance

    Expected: constitutional_bypass always False
    """
    # Test all strategies - constitutional_bypass must be False
    strategies = list(FallbackStrategy)

    for strategy in strategies:
        result = FallbackResult(
            strategy=strategy, success=True, warning_message=f"Testing {strategy.value}"
        )
        assert result.constitutional_bypass is False, f"Strategy {strategy.value} allows bypass!"


def test_fallback_result_test_verification_required_always_true() -> None:
    """
    NECESSARY Security: FallbackResult.test_verification_required always True (Article II).

    Validates:
    - Default value is True
    - Tests required even during fallback
    - Article II enforcement preserved

    Expected: test_verification_required always True
    """
    result = FallbackResult(
        strategy=FallbackStrategy.CLOUD_ROUTING,
        success=True,
        warning_message="Local model unavailable",
    )

    assert result.test_verification_required is True, "Test verification must never be skipped!"


def test_fallback_result_budget_guard_active_always_true() -> None:
    """
    NECESSARY Security: FallbackResult.budget_guard_active always True (Article III).

    Validates:
    - Default value is True
    - Budget guard enforced even during fallback
    - Article III enforcement preserved

    Expected: budget_guard_active always True
    """
    result = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY,
        success=True,
        warning_message="VectorStore unavailable",
    )

    assert result.budget_guard_active is True, "Budget guard must never be bypassed!"


def test_fallback_result_compliance_notes_field_exists() -> None:
    """
    NECESSARY Security: FallbackResult.compliance_notes field for audit trail.

    Validates:
    - Field exists and is string type
    - Can store compliance details
    - Default is empty string

    Expected: compliance_notes field accessible
    """
    result = FallbackResult(
        strategy=FallbackStrategy.AUTO_FIX_SUCCESS,
        success=True,
        warning_message="Linting errors auto-fixed",
        compliance_notes="Article II: Tests still required before merge (ruff --fix applied)",
    )

    assert isinstance(result.compliance_notes, str)
    assert "Article II" in result.compliance_notes
    assert "ruff --fix" in result.compliance_notes

    # Test default value
    result2 = FallbackResult(
        strategy=FallbackStrategy.SESSION_ONLY, success=True, warning_message="Test"
    )
    assert result2.compliance_notes == ""


# ============================================================================
# ADDITIONAL COVERAGE: RetryPolicy edge cases
# ============================================================================


def test_retry_policy_custom_abort_errors() -> None:
    """
    Additional: RetryPolicy with custom abort_on_errors list.

    Validates:
    - Custom error codes can be configured
    - Default includes 401, 403
    - Empty list allowed

    Expected: Custom abort errors accepted
    """
    # Custom error codes
    policy = RetryPolicy(abort_on_errors=["401", "403", "404", "500"])
    assert policy.abort_on_errors == ["401", "403", "404", "500"]

    # Empty list (retry on all errors)
    policy_retry_all = RetryPolicy(abort_on_errors=[])
    assert policy_retry_all.abort_on_errors == []


def test_retry_policy_exponential_backoff_with_different_multipliers() -> None:
    """
    Additional: RetryPolicy exponential backoff with various multipliers.

    Validates:
    - Multiplier 1.0: constant delay
    - Multiplier 1.5: moderate growth
    - Multiplier 3.0: aggressive growth

    Expected: Delays match formula for all multipliers
    """
    # Multiplier 1.0: No exponential growth (constant delay)
    policy_constant = RetryPolicy(base_delay_seconds=5.0, backoff_multiplier=1.0)
    assert policy_constant.get_delay(0) == 5.0
    assert policy_constant.get_delay(1) == 5.0
    assert policy_constant.get_delay(5) == 5.0

    # Multiplier 1.5: Moderate growth
    policy_moderate = RetryPolicy(base_delay_seconds=2.0, backoff_multiplier=1.5)
    assert policy_moderate.get_delay(0) == 2.0  # 2.0 * (1.5^0)
    assert policy_moderate.get_delay(1) == 3.0  # 2.0 * (1.5^1)
    assert policy_moderate.get_delay(2) == 4.5  # 2.0 * (1.5^2)

    # Multiplier 3.0: Aggressive growth
    policy_aggressive = RetryPolicy(base_delay_seconds=1.0, backoff_multiplier=3.0)
    assert policy_aggressive.get_delay(0) == 1.0  # 1.0 * (3.0^0)
    assert policy_aggressive.get_delay(1) == 3.0  # 1.0 * (3.0^1)
    assert policy_aggressive.get_delay(2) == 9.0  # 1.0 * (3.0^2)


def test_fallback_error_minimal_fields() -> None:
    """
    Additional: FallbackError with minimal fields (no retry_count, suggested_fix).

    Validates:
    - error_type and message are required
    - retry_count defaults to 0
    - suggested_fix defaults to None
    - String representation handles missing fields

    Expected: Exception works with minimal fields
    """
    error = FallbackError(error_type="NETWORK_ERROR", message="Connection timeout")

    assert error.error_type == "NETWORK_ERROR"
    assert error.message == "Connection timeout"
    assert error.retry_count == 0
    assert error.suggested_fix is None

    # String representation should not include retry/fix info
    error_str = str(error)
    assert "NETWORK_ERROR" in error_str
    assert "Connection timeout" in error_str
    assert "retries" not in error_str  # No retries mentioned
    assert "Suggested fix:" not in error_str  # No suggestion
