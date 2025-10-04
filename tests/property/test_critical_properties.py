"""
Property-based tests for CRITICAL Agency functions.

Tests critical systems with thousands of auto-generated inputs:
- RetryController (exponential backoff, circuit breaker)
- Memory consolidation
- Learning system
- CLI event scopes

Each property generates 100-1000 test cases automatically.
"""

import time

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from agency_memory import consolidate_learnings
from shared.retry_controller import (
    CircuitBreaker,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    RetryController,
)
from shared.type_definitions.result import Ok, Result
from tools.property_testing import (
    memory_record_strategy,
    result_strategy,
)

# ============================================================================
# RETRY CONTROLLER PROPERTIES
# ============================================================================


class TestRetryControllerProperties:
    """
    Property-based tests for RetryController.

    Validates retry logic under various failure scenarios.
    """

    @given(
        st.integers(min_value=0, max_value=10),
        st.floats(min_value=0.01, max_value=2.0),
    )
    def test_exponential_backoff_delay_increases(self, attempt: int, initial_delay: float):
        """PROPERTY: Exponential backoff delay increases with attempts."""
        strategy = ExponentialBackoffStrategy(
            initial_delay=initial_delay,
            multiplier=2.0,
            jitter=False,  # Disable jitter for deterministic testing
        )

        if attempt > 0:
            delay_current = strategy.calculate_delay(attempt)
            delay_previous = strategy.calculate_delay(attempt - 1)

            # Delay should increase (or stay same if at max)
            assert delay_current >= delay_previous

    @given(
        st.integers(min_value=0, max_value=100),
        st.floats(min_value=0.1, max_value=10.0),
        st.floats(min_value=1.0, max_value=60.0),
    )
    def test_exponential_backoff_respects_max_delay(
        self, attempt: int, initial_delay: float, max_delay: float
    ):
        """PROPERTY: Exponential backoff never exceeds max_delay."""
        assume(max_delay >= initial_delay)

        strategy = ExponentialBackoffStrategy(
            initial_delay=initial_delay,
            max_delay=max_delay,
            jitter=False,
        )

        delay = strategy.calculate_delay(attempt)
        assert delay <= max_delay

    @given(
        st.floats(min_value=0.1, max_value=5.0),
        st.floats(min_value=0.1, max_value=5.0),
    )
    def test_linear_backoff_increases_linearly(self, initial_delay: float, increment: float):
        """PROPERTY: Linear backoff increases by constant increment."""
        strategy = LinearBackoffStrategy(
            initial_delay=initial_delay,
            increment=increment,
            max_delay=100.0,
        )

        for attempt in range(5):
            expected_delay = min(initial_delay + (increment * attempt), strategy.max_delay)
            actual_delay = strategy.calculate_delay(attempt)

            # Allow small floating point errors
            assert abs(actual_delay - expected_delay) < 0.001

    @settings(deadline=1000)  # Allow more time for retry tests
    @given(st.integers(min_value=0, max_value=10))
    def test_retry_eventually_succeeds_if_function_recovers(self, failure_count: int):
        """PROPERTY: Retry succeeds if function recovers before max attempts."""
        attempt_counter = [0]

        def flaky_function():
            attempt_counter[0] += 1
            if attempt_counter[0] <= failure_count:
                raise ValueError(f"Attempt {attempt_counter[0]} failed")
            return "success"

        strategy = ExponentialBackoffStrategy(
            max_attempts=failure_count + 2,  # Enough to succeed
            initial_delay=0.001,  # Very fast for testing
        )
        controller = RetryController(strategy=strategy)

        result = controller.execute_with_retry(flaky_function)
        assert result == "success"
        assert attempt_counter[0] == failure_count + 1

    @given(st.integers(min_value=2, max_value=5))  # Min 2 to have retries
    def test_retry_exhausts_after_max_attempts(self, max_attempts: int):
        """PROPERTY: Retry fails after exhausting max attempts."""
        attempt_count = [0]

        def always_fails():
            attempt_count[0] += 1
            raise ValueError("Always fails")

        strategy = ExponentialBackoffStrategy(
            max_attempts=max_attempts,
            initial_delay=0.001,
        )
        controller = RetryController(strategy=strategy)

        with pytest.raises(ValueError, match="Always fails"):
            controller.execute_with_retry(always_fails)

        # Should have tried max_attempts times (strategy determines exact behavior)
        # The controller tries at least max_attempts times
        assert attempt_count[0] >= max_attempts

    @given(st.integers(min_value=1, max_value=5))
    def test_circuit_breaker_opens_after_threshold(self, failure_threshold: int):
        """PROPERTY: Circuit breaker opens after failure threshold."""
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=0.1,
        )

        # Record failures up to threshold
        for _ in range(failure_threshold):
            breaker.record_failure()

        # Circuit should be open
        assert breaker.state == "open"
        assert not breaker.allow_request()

    @given(st.integers(min_value=1, max_value=5))
    def test_circuit_breaker_resets_on_success(self, failures_before_success: int):
        """PROPERTY: Circuit breaker resets failure count on success."""
        breaker = CircuitBreaker(failure_threshold=10)

        # Record some failures
        for _ in range(failures_before_success):
            breaker.record_failure()

        # Record success
        breaker.record_success()

        # Circuit should be closed and reset
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
        assert breaker.allow_request()

    @settings(deadline=2000)  # Need time for sleep
    @given(st.floats(min_value=0.01, max_value=0.2))  # Reduce max to speed up tests
    def test_circuit_breaker_half_open_after_timeout(self, recovery_timeout: float):
        """PROPERTY: Circuit breaker transitions to half-open after timeout."""
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=recovery_timeout,
        )

        # Open the circuit
        breaker.record_failure()
        assert breaker.state == "open"

        # Wait for recovery timeout
        time.sleep(recovery_timeout + 0.01)

        # Should allow probe (half-open)
        assert breaker.allow_request()

    @settings(deadline=1000)
    @given(st.integers(min_value=0, max_value=5))
    def test_retry_with_intermittent_failures(self, failures_before_success: int):
        """PROPERTY: Retry handles intermittent failures correctly."""
        attempt_counter = [0]

        def intermittent_function():
            attempt_counter[0] += 1
            if attempt_counter[0] <= failures_before_success:
                raise ValueError("Intermittent failure")
            return "success"

        max_attempts = failures_before_success + 2
        strategy = ExponentialBackoffStrategy(
            max_attempts=max_attempts,
            initial_delay=0.001,
        )
        controller = RetryController(strategy=strategy)

        # Should succeed since max_attempts > failures
        result = controller.execute_with_retry(intermittent_function)
        assert result == "success"
        assert attempt_counter[0] == failures_before_success + 1


# ============================================================================
# MEMORY CONSOLIDATION PROPERTIES
# ============================================================================


class TestMemoryConsolidationProperties:
    """
    Property-based tests for memory consolidation.

    Validates learning extraction and pattern recognition.
    """

    @given(st.lists(memory_record_strategy(), min_size=0, max_size=20))
    def test_consolidation_handles_any_memory_list(self, memories: list):
        """PROPERTY: Consolidation handles any list of memories without crashing."""
        try:
            result = consolidate_learnings(memories)
            # Should return a result (may be empty)
            assert isinstance(result, (list, dict))
        except Exception as e:
            # Only acceptable exceptions are validation errors
            assert "validation" in str(e).lower() or "invalid" in str(e).lower()

    @given(st.lists(memory_record_strategy(), min_size=1, max_size=10))
    def test_consolidation_preserves_memory_count_invariant(self, memories: list):
        """PROPERTY: Consolidation doesn't increase memory count."""
        result = consolidate_learnings(memories)

        # Result should not have more items than input
        if isinstance(result, list):
            assert len(result) <= len(memories)

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10))
    def test_consolidation_with_text_content(self, text_contents: list):
        """PROPERTY: Consolidation handles text-heavy memories."""
        memories = [
            {"key": f"mem_{i}", "content": text, "tags": ["text"]}
            for i, text in enumerate(text_contents)
        ]

        result = consolidate_learnings(memories)
        # Should process without error
        assert result is not None


# ============================================================================
# RESULT CHAINING PROPERTIES
# ============================================================================


class TestResultChainingProperties:
    """
    Property-based tests for Result pattern chaining operations.

    Validates monad laws and composition.
    """

    @given(st.integers())  # Use plain integers, not results
    def test_result_left_identity(self, value: int):
        """PROPERTY: Result satisfies left identity monad law."""

        # return a >>= f === f a
        def f(x):
            return Ok(x * 2)

        result1 = Ok(value).and_then(f)
        result2 = f(value)

        if result1.is_ok() and result2.is_ok():
            assert result1.unwrap() == result2.unwrap()

    @given(result_strategy(st.integers()))
    def test_result_right_identity(self, m: Result):
        """PROPERTY: Result satisfies right identity monad law."""
        # m >>= return === m
        result = m.and_then(lambda x: Ok(x))

        if m.is_ok():
            assert result.unwrap() == m.unwrap()
        else:
            assert result.is_err()

    @given(result_strategy(st.integers()))
    def test_result_associativity(self, m: Result):
        """PROPERTY: Result satisfies associativity monad law."""

        # (m >>= f) >>= g === m >>= (\\x -> f x >>= g)
        def f(x):
            return Ok(x + 1)

        def g(x):
            return Ok(x * 2)

        result1 = m.and_then(f).and_then(g)
        result2 = m.and_then(lambda x: f(x).and_then(g))

        if result1.is_ok() and result2.is_ok():
            assert result1.unwrap() == result2.unwrap()
        elif result1.is_err() and result2.is_err():
            # Both errored (expected for Err inputs)
            pass
        else:
            pytest.fail("Associativity law violated")

    @given(
        result_strategy(st.integers()),
        result_strategy(st.integers()),
    )
    def test_result_map_functor_identity(self, r1: Result, r2: Result):
        """PROPERTY: map preserves identity: r.map(id) === r."""
        identity = lambda x: x
        mapped = r1.map(identity)

        if r1.is_ok():
            assert mapped.unwrap() == r1.unwrap()
        else:
            assert mapped.is_err()

    @given(result_strategy(st.lists(st.integers())))
    def test_result_map_functor_composition(self, r: Result):
        """PROPERTY: map preserves composition: r.map(f).map(g) === r.map(g . f)."""

        def f(x):
            return len(x) if isinstance(x, list) else 0

        def g(x):
            return x * 2

        result1 = r.map(f).map(g)
        result2 = r.map(lambda x: g(f(x)))

        if result1.is_ok() and result2.is_ok():
            assert result1.unwrap() == result2.unwrap()


# ============================================================================
# STATEFUL RETRY TESTING
# ============================================================================


class RetryControllerStateMachine(RuleBasedStateMachine):
    """
    Stateful testing for RetryController.

    Executes random sequences of operations and validates invariants.
    """

    def __init__(self):
        super().__init__()
        self.strategy = ExponentialBackoffStrategy(
            max_attempts=5,
            initial_delay=0.01,
        )
        self.controller = RetryController(strategy=self.strategy)
        self.total_successes = 0
        self.total_failures = 0

    @rule()
    def execute_succeeding_function(self):
        """Execute function that always succeeds."""
        result = self.controller.execute_with_retry(lambda: "success")
        assert result == "success"
        self.total_successes += 1

    @rule(failure_count=st.integers(min_value=1, max_value=3))
    def execute_flaky_function(self, failure_count: int):
        """Execute function that fails N times then succeeds."""
        attempts = [0]

        def flaky():
            attempts[0] += 1
            if attempts[0] <= failure_count:
                raise ValueError("Not yet")
            return "recovered"

        result = self.controller.execute_with_retry(flaky)
        assert result == "recovered"
        self.total_successes += 1

    @rule()
    def execute_failing_function(self):
        """Execute function that always fails."""

        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            self.controller.execute_with_retry(always_fails)

        self.total_failures += 1

    @invariant()
    def statistics_are_consistent(self):
        """Statistics should be consistent with execution history."""
        stats = self.controller.get_statistics()

        # Total executions should match our tracking
        expected_total = self.total_successes + self.total_failures
        assert stats["total_executions"] == expected_total

        # Successful recoveries should not exceed total successes
        assert stats["successful_recoveries"] <= self.total_successes


class TestRetryStateful:
    """Stateful property testing for RetryController."""

    def test_retry_controller_state_machine(self):
        """Run stateful tests on RetryController."""
        from hypothesis.stateful import run_state_machine_as_test

        run_state_machine_as_test(
            RetryControllerStateMachine,
            settings=settings(max_examples=20, stateful_step_count=10, deadline=2000),
        )


# ============================================================================
# PERFORMANCE PROPERTIES
# ============================================================================


class TestPerformanceProperties:
    """
    Property-based tests for performance characteristics.
    """

    @given(st.integers(min_value=1, max_value=10))
    def test_retry_delay_accumulation(self, max_attempts: int):
        """PROPERTY: Total retry delay is bounded."""
        strategy = ExponentialBackoffStrategy(
            initial_delay=0.1,
            max_delay=1.0,
            max_attempts=max_attempts,
            jitter=False,
        )

        total_delay = sum(strategy.calculate_delay(i) for i in range(max_attempts))

        # Total delay should be bounded
        # Geometric series: a(1 - r^n) / (1 - r) where a=0.1, r=2
        max_possible_delay = 1.0 * max_attempts  # Conservative upper bound
        assert total_delay <= max_possible_delay

    @given(st.integers(min_value=1, max_value=100))
    def test_memory_consolidation_performance(self, num_memories: int):
        """PROPERTY: Memory consolidation completes in reasonable time."""
        memories = [
            {"key": f"mem_{i}", "content": f"Content {i}", "tags": ["test"]}
            for i in range(num_memories)
        ]

        start = time.time()
        consolidate_learnings(memories)
        elapsed = time.time() - start

        # Should complete quickly (< 2 seconds for 100 memories)
        assert elapsed < 2.0, f"Consolidation took {elapsed}s for {num_memories} memories"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
