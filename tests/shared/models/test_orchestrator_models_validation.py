"""
Test suite for orchestrator_models.py Pydantic validation and type safety.

Tests all 5 model groups from PHASE1:
1. Backlog auto-selection models (PHASE1-001)
2. Constitutional validation models (PHASE1-002)
3. Git validation models (PHASE1-003)
4. Fallback/retry models (base infrastructure)
5. PrimeA execution result models (PHASE1-005)

Constitutional Compliance:
- Article I: Complete validation coverage (all models tested)
- Article II: 100% test pass requirement (strict assertions)
- Article VI: TDD mandate (tests validate model behavior)

NECESSARY Pattern Coverage:
- Normal: Valid model instantiation
- Edge: Boundary conditions (priority=1, priority=5)
- Corner: Invalid combinations (empty description + valid priority)
- Error: Validation errors (priority=0, priority=6, empty strings)
- Security: Input validation (min_length, ge, le constraints)
- Stress: Large data (1000 tasks in BacklogQueue)
- Accessibility: Public API (model_dump, model_validate)
- Regression: Field validation on assignment (validate_assignment=True)
- Yield: Output validation (computed properties, methods)
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from shared.models.orchestrator_models import (
    BacklogQueue,
    BacklogTask,
    # Git validation models (PHASE1-003)
    BranchInfo,
    BypassAttempt,
    FallbackError,
    FallbackResult,
    # Fallback/retry models
    FallbackStrategy,
    GitValidationError,
    GitValidationResult,
    LearningQuery,
    PrimeAResult,
    # PrimeA result models (PHASE1-005)
    PRMetadata,
    # Constitutional validation models (PHASE1-002)
    RetryConfig,
    RetryPolicy,
    SpecTrace,
    TaskGraphExecution,
    # Backlog models (PHASE1-001)
    TaskStatus,
    TestGateResult,
)

# ============================================================================
# BACKLOG AUTO-SELECTION MODELS (PHASE1-001)
# ============================================================================


class TestTaskStatus:
    """Test TaskStatus enum values."""

    def test_task_status_values(self):
        """Normal: All status values are accessible."""
        assert TaskStatus.READY == "ready"
        assert TaskStatus.BLOCKED == "blocked"
        assert TaskStatus.LOCKED == "locked"

    def test_task_status_enum_membership(self):
        """Normal: Status values are valid enum members."""
        assert "ready" in [status.value for status in TaskStatus]
        assert "blocked" in [status.value for status in TaskStatus]
        assert "locked" in [status.value for status in TaskStatus]


class TestBacklogTask:
    """Test BacklogTask model validation."""

    def test_create_backlog_task_valid(self):
        """Normal: Create task with valid data."""
        task = BacklogTask(
            priority=1,
            status=TaskStatus.READY,
            description="Implement JWT authentication middleware",
        )

        assert task.priority == 1
        assert task.status == TaskStatus.READY
        assert task.description == "Implement JWT authentication middleware"
        assert task.locked_by is None
        assert task.locked_at is None

    def test_priority_validation_edge_cases(self):
        """Edge: Priority boundary conditions (1 and 5)."""
        # Minimum priority
        task_min = BacklogTask(priority=1, status=TaskStatus.READY, description="Task")
        assert task_min.priority == 1

        # Maximum priority
        task_max = BacklogTask(priority=5, status=TaskStatus.READY, description="Task")
        assert task_max.priority == 5

    def test_priority_validation_error_below_min(self):
        """Error: Priority below minimum (priority=0)."""
        with pytest.raises(ValidationError) as exc_info:
            BacklogTask(priority=0, status=TaskStatus.READY, description="Invalid")

        errors = exc_info.value.errors()
        assert any("greater than or equal to 1" in str(err) for err in errors)

    def test_priority_validation_error_above_max(self):
        """Error: Priority above maximum (priority=6)."""
        with pytest.raises(ValidationError) as exc_info:
            BacklogTask(priority=6, status=TaskStatus.READY, description="Invalid")

        errors = exc_info.value.errors()
        assert any("less than or equal to 5" in str(err) for err in errors)

    def test_description_validation_error_empty(self):
        """Error: Empty description raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            BacklogTask(priority=1, status=TaskStatus.READY, description="")

        errors = exc_info.value.errors()
        assert any("min_length" in str(err) or "at least 1" in str(err) for err in errors)

    def test_task_locking(self):
        """Normal: Lock task to agent with timestamp."""
        task = BacklogTask(priority=1, status=TaskStatus.READY, description="Task")

        # Lock task
        task.locked_by = "agent_coder_001"
        task.locked_at = datetime.now()
        task.status = TaskStatus.LOCKED

        assert task.locked_by == "agent_coder_001"
        assert task.locked_at is not None
        assert task.status == TaskStatus.LOCKED

    def test_validate_assignment_priority_update(self):
        """Regression: validate_assignment=True enforces constraints on updates."""
        task = BacklogTask(priority=1, status=TaskStatus.READY, description="Task")

        # Valid update
        task.priority = 3
        assert task.priority == 3

        # Invalid update (priority=0)
        with pytest.raises(ValidationError):
            task.priority = 0

    def test_model_dump_json_serialization(self):
        """Accessibility: model_dump() for JSON serialization."""
        task = BacklogTask(priority=1, status=TaskStatus.READY, description="Task")

        data = task.model_dump()
        assert data["priority"] == 1
        assert data["status"] == "ready"
        assert data["description"] == "Task"
        assert data["locked_by"] is None


class TestBacklogQueue:
    """Test BacklogQueue model validation and methods."""

    def test_create_backlog_queue_valid(self):
        """Normal: Create queue with tasks."""
        queue = BacklogQueue(
            tasks=[
                BacklogTask(priority=1, status=TaskStatus.READY, description="Task A"),
                BacklogTask(priority=2, status=TaskStatus.BLOCKED, description="Task B"),
            ],
            file_path="~/.agency/memories/agency_backlog/test_suite_gaps.md",
        )

        assert len(queue.tasks) == 2
        assert queue.file_path == "~/.agency/memories/agency_backlog/test_suite_gaps.md"
        assert queue.last_modified is None

    def test_get_ready_tasks_filters_status(self):
        """Yield: get_ready_tasks() filters by status."""
        queue = BacklogQueue(
            tasks=[
                BacklogTask(priority=3, status=TaskStatus.READY, description="C"),
                BacklogTask(priority=1, status=TaskStatus.READY, description="A"),
                BacklogTask(priority=2, status=TaskStatus.BLOCKED, description="B"),
                BacklogTask(priority=4, status=TaskStatus.LOCKED, description="D"),
            ],
            file_path="test.md",
        )

        ready_tasks = queue.get_ready_tasks()

        # Only READY tasks returned
        assert len(ready_tasks) == 2
        assert all(task.status == TaskStatus.READY for task in ready_tasks)

        # Excluded BLOCKED and LOCKED
        descriptions = [task.description for task in ready_tasks]
        assert "B" not in descriptions
        assert "D" not in descriptions

    def test_get_ready_tasks_priority_sorting(self):
        """Yield: get_ready_tasks() sorts by priority ascending."""
        queue = BacklogQueue(
            tasks=[
                BacklogTask(priority=5, status=TaskStatus.READY, description="E"),
                BacklogTask(priority=2, status=TaskStatus.READY, description="B"),
                BacklogTask(priority=1, status=TaskStatus.READY, description="A"),
                BacklogTask(priority=3, status=TaskStatus.READY, description="C"),
            ],
            file_path="test.md",
        )

        ready_tasks = queue.get_ready_tasks()

        # Priority sorted ascending (1 first, 5 last)
        assert ready_tasks[0].priority == 1
        assert ready_tasks[1].priority == 2
        assert ready_tasks[2].priority == 3
        assert ready_tasks[3].priority == 5

    def test_get_ready_tasks_empty_queue(self):
        """Edge: Empty queue returns empty list."""
        queue = BacklogQueue(tasks=[], file_path="test.md")

        ready_tasks = queue.get_ready_tasks()

        assert ready_tasks == []

    def test_get_ready_tasks_all_blocked(self):
        """Corner: All tasks blocked returns empty list."""
        queue = BacklogQueue(
            tasks=[
                BacklogTask(priority=1, status=TaskStatus.BLOCKED, description="A"),
                BacklogTask(priority=2, status=TaskStatus.LOCKED, description="B"),
            ],
            file_path="test.md",
        )

        ready_tasks = queue.get_ready_tasks()

        assert ready_tasks == []

    def test_large_queue_stress(self):
        """Stress: Queue with 1000 tasks."""
        tasks = [
            BacklogTask(priority=(i % 5) + 1, status=TaskStatus.READY, description=f"Task {i}")
            for i in range(1000)
        ]

        queue = BacklogQueue(tasks=tasks, file_path="large.md")
        ready_tasks = queue.get_ready_tasks()

        assert len(ready_tasks) == 1000
        assert ready_tasks[0].priority == 1  # Sorted by priority


# ============================================================================
# CONSTITUTIONAL VALIDATION MODELS (PHASE1-002)
# ============================================================================


class TestRetryConfig:
    """Test RetryConfig model validation."""

    def test_create_retry_config_valid(self):
        """Normal: Create config with default values."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.initial_timeout == 120.0
        assert config.timeout_multipliers == [2.0, 3.0, 10.0]

    def test_create_retry_config_custom(self):
        """Normal: Create config with custom values."""
        config = RetryConfig(
            max_retries=5, initial_timeout=60.0, timeout_multipliers=[2.0, 4.0, 8.0, 16.0, 32.0]
        )

        assert config.max_retries == 5
        assert config.initial_timeout == 60.0
        assert len(config.timeout_multipliers) == 5

    def test_max_retries_validation_edge_cases(self):
        """Edge: Max retries boundary conditions (1 and 10)."""
        config_min = RetryConfig(max_retries=1)
        assert config_min.max_retries == 1

        config_max = RetryConfig(max_retries=10)
        assert config_max.max_retries == 10

    def test_max_retries_validation_error_below_min(self):
        """Error: Max retries below minimum (max_retries=0)."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(max_retries=0)

        errors = exc_info.value.errors()
        assert any("greater than or equal to 1" in str(err) for err in errors)

    def test_max_retries_accepts_large_values(self):
        """Edge: Max retries can be set to large values (no upper bound in RetryConfig)."""
        # RetryConfig does NOT have upper bound constraint (unlike RetryPolicy)
        config = RetryConfig(max_retries=100)
        assert config.max_retries == 100

    def test_initial_timeout_validation_error_zero(self):
        """Error: Initial timeout zero (initial_timeout=0.0)."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(initial_timeout=0.0)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)


class TestTestGateResult:
    """Test TestGateResult model validation."""

    def test_create_test_gate_result_valid_100_percent(self):
        """Normal: Create result with 100% pass rate."""
        result = TestGateResult(pass_rate=1.0, total_tests=100, passed_tests=100, failed_tests=[])

        assert result.pass_rate == 1.0
        assert result.total_tests == 100
        assert result.passed_tests == 100
        assert result.failed_tests == []
        assert result.simulation_detected is False

    def test_create_test_gate_result_with_failures(self):
        """Normal: Create result with failures."""
        result = TestGateResult(
            pass_rate=0.95,
            total_tests=100,
            passed_tests=95,
            failed_tests=["test_auth_invalid_token", "test_auth_expired_token"],
        )

        assert result.pass_rate == 0.95
        assert len(result.failed_tests) == 2

    def test_pass_rate_validation_edge_cases(self):
        """Edge: Pass rate boundary conditions (0.0 and 1.0)."""
        result_zero = TestGateResult(pass_rate=0.0, total_tests=10, passed_tests=0)
        assert result_zero.pass_rate == 0.0

        result_one = TestGateResult(pass_rate=1.0, total_tests=10, passed_tests=10)
        assert result_one.pass_rate == 1.0

    def test_pass_rate_validation_error_below_min(self):
        """Error: Pass rate below minimum (pass_rate=-0.1)."""
        with pytest.raises(ValidationError) as exc_info:
            TestGateResult(pass_rate=-0.1, total_tests=10, passed_tests=0)

        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in str(err) for err in errors)

    def test_pass_rate_validation_error_above_max(self):
        """Error: Pass rate above maximum (pass_rate=1.1)."""
        with pytest.raises(ValidationError) as exc_info:
            TestGateResult(pass_rate=1.1, total_tests=10, passed_tests=11)

        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(err) for err in errors)

    def test_total_tests_validation_error_negative(self):
        """Error: Negative total tests."""
        with pytest.raises(ValidationError) as exc_info:
            TestGateResult(pass_rate=1.0, total_tests=-1, passed_tests=0)

        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in str(err) for err in errors)


class TestBypassAttempt:
    """Test BypassAttempt model validation."""

    def test_create_bypass_attempt_valid(self):
        """Normal: Create bypass attempt with valid data."""
        attempt = BypassAttempt(
            flag="--force", source="cli", timestamp=datetime.now(), rejected=True
        )

        assert attempt.flag == "--force"
        assert attempt.source == "cli"
        assert attempt.rejected is True
        assert attempt.article == "Article III"

    def test_bypass_attempt_default_rejected_true(self):
        """Normal: Default rejected=True."""
        attempt = BypassAttempt(flag="--force", source="cli", timestamp=datetime.now())

        assert attempt.rejected is True

    def test_bypass_attempt_custom_article(self):
        """Normal: Custom article override."""
        attempt = BypassAttempt(
            flag="SKIP_TESTS", source="env_var", timestamp=datetime.now(), article="Article II"
        )

        assert attempt.article == "Article II"


class TestLearningQuery:
    """Test LearningQuery model validation."""

    def test_create_learning_query_valid(self):
        """Normal: Create learning query with results."""
        query = LearningQuery(
            tags=["pattern", "jwt_auth"],
            min_confidence=0.6,
            results=[
                {"pattern": "TDD workflow", "confidence": 0.85},
                {"pattern": "Result pattern", "confidence": 0.88},
            ],
            execution_time_ms=45.2,
        )

        assert query.tags == ["pattern", "jwt_auth"]
        assert query.min_confidence == 0.6
        assert len(query.results) == 2
        assert query.execution_time_ms == 45.2

    def test_tags_validation_error_empty(self):
        """Error: Empty tags list raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            LearningQuery(tags=[], min_confidence=0.6)

        errors = exc_info.value.errors()
        assert any("min_length" in str(err) or "at least 1" in str(err) for err in errors)

    def test_min_confidence_validation_edge_cases(self):
        """Edge: Min confidence boundary conditions (0.0 and 1.0)."""
        query_zero = LearningQuery(tags=["pattern"], min_confidence=0.0)
        assert query_zero.min_confidence == 0.0

        query_one = LearningQuery(tags=["pattern"], min_confidence=1.0)
        assert query_one.min_confidence == 1.0

    def test_min_confidence_validation_error_above_max(self):
        """Error: Min confidence above maximum (min_confidence=1.1)."""
        with pytest.raises(ValidationError) as exc_info:
            LearningQuery(tags=["pattern"], min_confidence=1.1)

        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(err) for err in errors)


class TestSpecTrace:
    """Test SpecTrace model validation."""

    def test_create_spec_trace_valid(self):
        """Normal: Create spec trace with valid data."""
        trace = SpecTrace(
            spec_id="SPEC-030",
            acceptance_criteria=["CONST-001", "CONST-002", "CONST-003"],
            matched=True,
            coverage=1.0,
        )

        assert trace.spec_id == "SPEC-030"
        assert len(trace.acceptance_criteria) == 3
        assert trace.matched is True
        assert trace.coverage == 1.0

    def test_spec_id_validation_pattern(self):
        """Normal: Spec ID pattern validation (SPEC-XXX)."""
        # Valid patterns
        SpecTrace(spec_id="SPEC-001", acceptance_criteria=["AC1"], matched=True, coverage=1.0)
        SpecTrace(spec_id="SPEC-999", acceptance_criteria=["AC1"], matched=True, coverage=1.0)

    def test_spec_id_validation_error_invalid_pattern(self):
        """Error: Invalid spec ID pattern."""
        with pytest.raises(ValidationError) as exc_info:
            SpecTrace(
                spec_id="INVALID-001", acceptance_criteria=["AC1"], matched=True, coverage=1.0
            )

        errors = exc_info.value.errors()
        assert any("pattern" in str(err) or "match" in str(err) for err in errors)

    def test_acceptance_criteria_validation_error_empty(self):
        """Error: Empty acceptance criteria raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SpecTrace(spec_id="SPEC-030", acceptance_criteria=[], matched=True, coverage=1.0)

        errors = exc_info.value.errors()
        assert any("min_length" in str(err) or "at least 1" in str(err) for err in errors)

    def test_coverage_validation_edge_cases(self):
        """Edge: Coverage boundary conditions (0.0 and 1.0)."""
        trace_zero = SpecTrace(
            spec_id="SPEC-030", acceptance_criteria=["AC1"], matched=False, coverage=0.0
        )
        assert trace_zero.coverage == 0.0

        trace_one = SpecTrace(
            spec_id="SPEC-030", acceptance_criteria=["AC1"], matched=True, coverage=1.0
        )
        assert trace_one.coverage == 1.0


# ============================================================================
# GIT VALIDATION MODELS (PHASE1-003)
# ============================================================================


class TestBranchInfo:
    """Test BranchInfo model validation."""

    def test_create_branch_info_feature_branch(self):
        """Normal: Create feature branch info."""
        branch = BranchInfo(name="feat/test", protected=False, pattern="feat/*")

        assert branch.name == "feat/test"
        assert branch.protected is False
        assert branch.pattern == "feat/*"

    def test_create_branch_info_protected_branch(self):
        """Normal: Create protected branch info."""
        branch = BranchInfo(name="main", protected=True)

        assert branch.name == "main"
        assert branch.protected is True
        assert branch.pattern is None

    def test_is_safe_for_execution_feature_branch(self):
        """Yield: is_safe_for_execution() returns True for feature branch."""
        branch = BranchInfo(name="feat/test", protected=False)

        assert branch.is_safe_for_execution() is True

    def test_is_safe_for_execution_protected_branch(self):
        """Yield: is_safe_for_execution() returns False for protected branch."""
        branch = BranchInfo(name="main", protected=True)

        assert branch.is_safe_for_execution() is False

    def test_name_validation_error_empty(self):
        """Error: Empty branch name raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            BranchInfo(name="")

        errors = exc_info.value.errors()
        assert any("min_length" in str(err) or "at least 1" in str(err) for err in errors)


class TestGitValidationResult:
    """Test GitValidationResult model validation."""

    def test_create_git_validation_result_safe(self):
        """Normal: Create safe validation result."""
        result = GitValidationResult(
            is_safe=True, branch_name="feat/test", pattern_match="feat/*", article="Article III"
        )

        assert result.is_safe is True
        assert result.branch_name == "feat/test"
        assert result.pattern_match == "feat/*"
        assert result.error_message is None

    def test_create_git_validation_result_unsafe(self):
        """Normal: Create unsafe validation result."""
        result = GitValidationResult(
            is_safe=False,
            branch_name="main",
            error_message="Cannot execute on protected branch 'main'",
        )

        assert result.is_safe is False
        assert result.error_message == "Cannot execute on protected branch 'main'"

    def test_raise_if_unsafe_safe_branch(self):
        """Yield: raise_if_unsafe() does not raise for safe branch."""
        result = GitValidationResult(is_safe=True, branch_name="feat/test")

        # Should not raise
        result.raise_if_unsafe()

    def test_raise_if_unsafe_protected_branch(self):
        """Error: raise_if_unsafe() raises GitValidationError for protected branch."""
        result = GitValidationResult(
            is_safe=False, branch_name="main", error_message="Protected branch"
        )

        with pytest.raises(GitValidationError) as exc_info:
            result.raise_if_unsafe()

        # Error message includes recovery hint, verify branch name in repr or attributes
        error = exc_info.value
        assert error.branch_name == "main"
        assert error.message == "Protected branch"


class TestGitValidationError:
    """Test GitValidationError exception."""

    def test_create_git_validation_error(self):
        """Normal: Create error with message and branch name."""
        error = GitValidationError(
            message="Cannot execute on protected branch 'main'",
            branch_name="main",
            recovery_hint="Checkout feature branch: git checkout -b feat/fix",
        )

        assert error.message == "Cannot execute on protected branch 'main'"
        assert error.branch_name == "main"
        assert error.recovery_hint == "Checkout feature branch: git checkout -b feat/fix"

    def test_git_validation_error_str_with_hint(self):
        """Yield: __str__ includes recovery hint."""
        error = GitValidationError(
            message="Protected branch", branch_name="main", recovery_hint="git checkout -b feat/fix"
        )

        error_str = str(error)

        assert "Protected branch" in error_str
        assert "git checkout -b feat/fix" in error_str

    def test_git_validation_error_str_without_hint(self):
        """Yield: __str__ excludes hint if not provided."""
        error = GitValidationError(message="Protected branch", branch_name="main")

        error_str = str(error)

        assert error_str == "Protected branch"

    def test_git_validation_error_repr(self):
        """Yield: __repr__ includes all attributes."""
        error = GitValidationError(message="Error", branch_name="main")

        repr_str = repr(error)

        assert "GitValidationError" in repr_str
        assert "message='Error'" in repr_str
        assert "branch_name='main'" in repr_str


# ============================================================================
# FALLBACK/RETRY MODELS (BASE INFRASTRUCTURE)
# ============================================================================


class TestFallbackStrategy:
    """Test FallbackStrategy enum values."""

    def test_fallback_strategy_values(self):
        """Normal: All strategy values are accessible."""
        assert FallbackStrategy.SESSION_ONLY == "session_only"
        assert FallbackStrategy.CLOUD_ROUTING == "cloud_routing"
        assert FallbackStrategy.RETRY_SUCCESS == "retry_success"
        assert FallbackStrategy.AUTO_FIX_SUCCESS == "auto_fix_success"
        assert FallbackStrategy.MANUAL_INTERVENTION == "manual_intervention"
        assert FallbackStrategy.READ_ONLY == "read_only"
        assert FallbackStrategy.SKIP_LEARNING == "skip_learning"


class TestFallbackResult:
    """Test FallbackResult model validation."""

    def test_create_fallback_result_success(self):
        """Normal: Create successful fallback result."""
        result = FallbackResult(
            strategy=FallbackStrategy.RETRY_SUCCESS,
            success=True,
            warning_message="Retry succeeded after transient failure",
            suggested_fix=None,
            execution_continues=True,
            retry_count=2,
            latency_ms=150.5,
        )

        assert result.strategy == FallbackStrategy.RETRY_SUCCESS
        assert result.success is True
        assert result.retry_count == 2
        assert result.latency_ms == 150.5

    def test_create_fallback_result_failure(self):
        """Normal: Create failed fallback result."""
        result = FallbackResult(
            strategy=FallbackStrategy.MANUAL_INTERVENTION,
            success=False,
            warning_message="VectorStore unavailable - manual intervention required",
            suggested_fix="Check Firestore connection or restart VectorStore service",
            execution_continues=False,
            permanent_failure=True,
        )

        assert result.success is False
        assert result.execution_continues is False
        assert result.permanent_failure is True

    def test_constitutional_compliance_fields_defaults(self):
        """Security: Constitutional compliance fields have correct defaults."""
        result = FallbackResult(
            strategy=FallbackStrategy.SESSION_ONLY,
            success=True,
            warning_message="VectorStore unavailable - using session memory",
        )

        # Article III: No constitutional bypass
        assert result.constitutional_bypass is False

        # Article II: Tests always verified
        assert result.test_verification_required is True

        # Article III: Budget guard always active
        assert result.budget_guard_active is True


class TestRetryPolicy:
    """Test RetryPolicy model validation."""

    def test_create_retry_policy_default(self):
        """Normal: Create retry policy with defaults."""
        policy = RetryPolicy()

        assert policy.max_attempts == 5
        assert policy.base_delay_seconds == 2.0
        assert policy.backoff_multiplier == 2.0
        assert policy.abort_on_errors == ["401", "403"]

    def test_get_delay_exponential_backoff(self):
        """Yield: get_delay() calculates exponential backoff correctly."""
        policy = RetryPolicy(base_delay_seconds=2.0, backoff_multiplier=2.0)

        assert policy.get_delay(0) == 2.0  # 2.0 * 2^0
        assert policy.get_delay(1) == 4.0  # 2.0 * 2^1
        assert policy.get_delay(2) == 8.0  # 2.0 * 2^2
        assert policy.get_delay(3) == 16.0  # 2.0 * 2^3

    def test_max_attempts_validation_edge_cases(self):
        """Edge: Max attempts boundary conditions (1 and 10)."""
        policy_min = RetryPolicy(max_attempts=1)
        assert policy_min.max_attempts == 1

        policy_max = RetryPolicy(max_attempts=10)
        assert policy_max.max_attempts == 10

    def test_base_delay_validation_error_zero(self):
        """Error: Base delay zero raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            RetryPolicy(base_delay_seconds=0.0)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(err) for err in errors)


class TestFallbackError:
    """Test FallbackError exception."""

    def test_create_fallback_error(self):
        """Normal: Create fallback error with context."""
        error = FallbackError(
            error_type="RETRY_EXHAUSTED",
            message="All retries failed after 5 attempts",
            retry_count=5,
            suggested_fix="Check VectorStore connection",
        )

        assert error.error_type == "RETRY_EXHAUSTED"
        assert error.message == "All retries failed after 5 attempts"
        assert error.retry_count == 5
        assert error.suggested_fix == "Check VectorStore connection"

    def test_fallback_error_str_with_all_context(self):
        """Yield: __str__ includes all context."""
        error = FallbackError(
            error_type="RETRY_EXHAUSTED",
            message="Failed",
            retry_count=3,
            suggested_fix="Fix it",
        )

        error_str = str(error)

        assert "[RETRY_EXHAUSTED]" in error_str
        assert "Failed" in error_str
        assert "(after 3 retries)" in error_str
        assert "Suggested fix: Fix it" in error_str


# ============================================================================
# PRIMEA EXECUTION RESULT MODELS (PHASE1-005)
# ============================================================================


class TestPRMetadata:
    """Test PRMetadata model validation."""

    def test_create_pr_metadata_valid(self):
        """Normal: Create PR metadata with valid data."""
        metadata = PRMetadata(
            title="feat: Add JWT authentication middleware",
            body="## Summary\n\nImplemented JWT auth...",
            branch="feat/jwt-auth",
            base_branch="main",
        )

        assert metadata.title == "feat: Add JWT authentication middleware"
        assert "Summary" in metadata.body
        assert metadata.branch == "feat/jwt-auth"
        assert metadata.base_branch == "main"

    def test_title_validation_max_length_edge_case(self):
        """Edge: Title at maximum length (72 chars)."""
        title_72 = "a" * 72
        metadata = PRMetadata(title=title_72, body="Body", branch="feat/test")

        assert len(metadata.title) == 72

    def test_title_validation_error_exceeds_max_length(self):
        """Error: Title exceeds maximum length (>72 chars)."""
        title_73 = "a" * 73

        with pytest.raises(ValidationError) as exc_info:
            PRMetadata(title=title_73, body="Body", branch="feat/test")

        errors = exc_info.value.errors()
        assert any("max_length" in str(err) or "at most 72" in str(err) for err in errors)

    def test_title_validation_error_empty(self):
        """Error: Empty title raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PRMetadata(title="", body="Body", branch="feat/test")

        errors = exc_info.value.errors()
        assert any("min_length" in str(err) or "at least 1" in str(err) for err in errors)

    def test_body_validation_error_empty(self):
        """Error: Empty body raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PRMetadata(title="Title", body="", branch="feat/test")

        errors = exc_info.value.errors()
        assert any("min_length" in str(err) or "at least 1" in str(err) for err in errors)


class TestTaskGraphExecution:
    """Test TaskGraphExecution model validation."""

    def test_create_task_graph_execution_in_progress(self):
        """Normal: Create execution in progress (no end_time)."""
        execution = TaskGraphExecution(
            graph_id="graph_001",
            total_tasks=10,
            completed_tasks=5,
            failed_tasks=0,
            start_time=datetime.now(),
        )

        assert execution.graph_id == "graph_001"
        assert execution.total_tasks == 10
        assert execution.completed_tasks == 5
        assert execution.end_time is None

    def test_execution_time_seconds_completed(self):
        """Yield: execution_time_seconds calculates duration."""
        start = datetime.now()
        end = start + timedelta(seconds=120)

        execution = TaskGraphExecution(
            graph_id="graph_001",
            total_tasks=10,
            completed_tasks=10,
            start_time=start,
            end_time=end,
        )

        assert execution.execution_time_seconds == 120.0

    def test_execution_time_seconds_in_progress(self):
        """Yield: execution_time_seconds returns None if in progress."""
        execution = TaskGraphExecution(
            graph_id="graph_001",
            total_tasks=10,
            completed_tasks=5,
            start_time=datetime.now(),
        )

        assert execution.execution_time_seconds is None

    def test_failed_tasks_validation_error_negative(self):
        """Error: Negative failed tasks raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            TaskGraphExecution(
                graph_id="graph_001",
                total_tasks=10,
                completed_tasks=5,
                failed_tasks=-1,
                start_time=datetime.now(),
            )

        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in str(err) for err in errors)


class TestPrimeAResult:
    """Test PrimeAResult model validation."""

    def test_create_primea_result_success(self):
        """Normal: Create successful PrimeA result."""
        result = PrimeAResult(
            mission="Implement JWT authentication",
            status="complete",
            pr_url="https://github.com/org/repo/pull/42",
            tasks_completed=10,
            tasks_total=10,
            test_pass_rate=1.0,
            execution_time_seconds=120.5,
            constitutional_compliant=True,
        )

        assert result.mission == "Implement JWT authentication"
        assert result.status == "complete"
        assert result.pr_url is not None
        assert result.test_pass_rate == 1.0
        assert result.constitutional_compliant is True

    def test_create_primea_result_from_backlog(self):
        """Normal: Create result auto-selected from backlog."""
        result = PrimeAResult(
            mission="Fix test suite gaps",
            status="complete",
            tasks_completed=5,
            tasks_total=5,
            test_pass_rate=1.0,
            execution_time_seconds=60.0,
            selected_from_backlog=True,
            backlog_priority=1,
        )

        assert result.selected_from_backlog is True
        assert result.backlog_priority == 1

    def test_completion_rate_property_100_percent(self):
        """Yield: completion_rate property calculates 100%."""
        result = PrimeAResult(
            mission="Task",
            status="complete",
            tasks_completed=10,
            tasks_total=10,
            test_pass_rate=1.0,
            execution_time_seconds=120.0,
        )

        assert result.completion_rate == 1.0

    def test_completion_rate_property_partial(self):
        """Yield: completion_rate property calculates partial completion."""
        result = PrimeAResult(
            mission="Task",
            status="partial",
            tasks_completed=7,
            tasks_total=10,
            test_pass_rate=1.0,
            execution_time_seconds=120.0,
        )

        assert result.completion_rate == 0.7

    def test_completion_rate_property_zero_tasks(self):
        """Edge: completion_rate property returns 0.0 for zero tasks."""
        result = PrimeAResult(
            mission="Task",
            status="failed",
            tasks_completed=0,
            tasks_total=0,
            test_pass_rate=0.0,
            execution_time_seconds=0.0,
        )

        assert result.completion_rate == 0.0

    def test_test_pass_rate_validation_error_above_max(self):
        """Error: Test pass rate above maximum (>1.0)."""
        with pytest.raises(ValidationError) as exc_info:
            PrimeAResult(
                mission="Task",
                status="complete",
                tasks_completed=10,
                tasks_total=10,
                test_pass_rate=1.1,
                execution_time_seconds=120.0,
            )

        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(err) for err in errors)

    def test_backlog_priority_validation_edge_cases(self):
        """Edge: Backlog priority boundary conditions (1 and 5)."""
        result_min = PrimeAResult(
            mission="Task",
            status="complete",
            tasks_completed=5,
            tasks_total=5,
            test_pass_rate=1.0,
            execution_time_seconds=60.0,
            backlog_priority=1,
        )
        assert result_min.backlog_priority == 1

        result_max = PrimeAResult(
            mission="Task",
            status="complete",
            tasks_completed=5,
            tasks_total=5,
            test_pass_rate=1.0,
            execution_time_seconds=60.0,
            backlog_priority=5,
        )
        assert result_max.backlog_priority == 5

    def test_backlog_priority_validation_error_below_min(self):
        """Error: Backlog priority below minimum (priority=0)."""
        with pytest.raises(ValidationError) as exc_info:
            PrimeAResult(
                mission="Task",
                status="complete",
                tasks_completed=5,
                tasks_total=5,
                test_pass_rate=1.0,
                execution_time_seconds=60.0,
                backlog_priority=0,
            )

        errors = exc_info.value.errors()
        assert any("greater than or equal to 1" in str(err) for err in errors)


# ============================================================================
# IMPORT PATH VERIFICATION
# ============================================================================


class TestImportPaths:
    """Test that all models are importable from shared.models."""

    def test_all_models_importable(self):
        """Accessibility: All models importable from shared.models."""
        from shared.models import (
            BacklogQueue,
            BacklogTask,
            BranchInfo,
            BypassAttempt,
            FallbackError,
            FallbackResult,
            FallbackStrategy,
            GitValidationError,
            GitValidationResult,
            LearningQuery,
            PrimeAResult,
            PRMetadata,
            RetryConfig,
            RetryPolicy,
            SpecTrace,
            TaskGraphExecution,
            TaskStatus,
            TestGateResult,
        )

        # All imports succeeded (no ImportError)
        assert True

    def test_enum_values_accessible(self):
        """Accessibility: Enum values accessible via shared.models."""
        from shared.models import FallbackStrategy, TaskStatus

        assert TaskStatus.READY == "ready"
        assert FallbackStrategy.SESSION_ONLY == "session_only"

    def test_exception_classes_accessible(self):
        """Accessibility: Exception classes accessible via shared.models."""
        from shared.models import FallbackError, GitValidationError

        # Can instantiate exceptions
        error1 = FallbackError("RETRY_EXHAUSTED", "Failed")
        error2 = GitValidationError("Protected branch", branch_name="main")

        assert isinstance(error1, Exception)
        assert isinstance(error2, Exception)


# ============================================================================
# ANTI-PATTERNS (ZERO ANY TYPES)
# ============================================================================


class TestZeroAnyTypes:
    """Test that zero 'Any' types exist in orchestrator_models.py."""

    def test_no_dict_any_any_in_models(self):
        """Security: No Dict[Any, Any] in model type annotations."""
        import inspect

        from shared.models import orchestrator_models

        # Get all classes from module
        classes = [
            obj
            for name, obj in inspect.getmembers(orchestrator_models)
            if inspect.isclass(obj) and obj.__module__ == orchestrator_models.__name__
        ]

        # Check each class for Dict[Any, Any] in annotations
        for cls in classes:
            annotations = getattr(cls, "__annotations__", {})
            for field_name, field_type in annotations.items():
                field_type_str = str(field_type)
                assert "Dict[Any, Any]" not in field_type_str, (
                    f"Class {cls.__name__} field {field_name} has Dict[Any, Any]"
                )

    def test_no_bare_any_in_models(self):
        """Security: No bare 'Any' in model type annotations."""
        import inspect

        from shared.models import orchestrator_models

        classes = [
            obj
            for name, obj in inspect.getmembers(orchestrator_models)
            if inspect.isclass(obj) and obj.__module__ == orchestrator_models.__name__
        ]

        for cls in classes:
            annotations = getattr(cls, "__annotations__", {})
            for field_name, field_type in annotations.items():
                field_type_str = str(field_type)
                # Allow "Any" in contexts like list[dict[str, Any]] but not bare Any
                if field_type_str == "typing.Any" or field_type_str == "Any":
                    pytest.fail(f"Class {cls.__name__} field {field_name} has bare Any type")
