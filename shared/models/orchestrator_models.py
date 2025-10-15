"""
Orchestrator models for graceful fallback handling and retry policies.

These models provide constitutional-compliant fallback strategies when
infrastructure components (VectorStore, local models, etc.) are unavailable.

Also includes PrimeA execution result models for typed PR metadata, task graph
tracking, and execution results.

Constitutional validation models for orchestrator workflow gates (PHASE1-002):
- RetryConfig: Article I retry protocol configuration (2x, 3x, 10x timeouts)
- TestGateResult: Article II 100% test pass enforcement
- BypassAttempt: Article III bypass detection and audit logging
- LearningQuery: Article IV VectorStore integration tracking
- SpecTrace: Article V spec traceability validation

Backlog auto-selection models for /primeA orchestrator (PHASE1-001):
- TaskStatus: Task lifecycle states (Ready, Blocked, Locked)
- BacklogTask: Prioritized work item with agent locking (priority 1-5)
- BacklogQueue: Task queue container with file persistence and priority sorting

Constitutional Compliance:
- Article I: Retry policies with exponential backoff, complete execution tracking
- Article II: Test verification always required (no bypass), test_pass_rate tracking, strict typing (NO Dict[Any, Any])
- Article III: Budget guard always active (no constitutional bypass), automated state enforcement
- Article IV: Learning continues where possible (fallback to session memory), backlog tracking
- Article V: Spec-driven development (mission, report_path traceability)
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FallbackStrategy(str, Enum):
    """
    Enumeration of available fallback strategies.

    Each strategy represents a graceful degradation path when
    primary infrastructure components are unavailable.
    """

    SESSION_ONLY = "session_only"  # VectorStore unavailable, use session memory
    CLOUD_ROUTING = "cloud_routing"  # Local model unavailable, route to cloud
    RETRY_SUCCESS = "retry_success"  # Retry succeeded after transient failure
    AUTO_FIX_SUCCESS = "auto_fix_success"  # Auto-fix applied (e.g., ruff)
    MANUAL_INTERVENTION = "manual_intervention"  # Requires user action
    USER_INTERVENTION = "user_intervention"  # Alias for MANUAL_INTERVENTION
    READ_ONLY = "read_only"  # VectorStore read-only mode
    SKIP_LEARNING = "skip_learning"  # Skip VectorStore queries for performance


class FallbackResult(BaseModel):
    """
    Result of applying a fallback strategy.

    Tracks whether fallback succeeded, provides user-facing messages,
    and enforces constitutional compliance (no bypasses permitted).
    """

    model_config = ConfigDict(extra="forbid")

    strategy: FallbackStrategy = Field(..., description="Fallback strategy that was applied")
    success: bool = Field(..., description="True if fallback succeeded")
    warning_message: str = Field(
        ..., description="User-facing warning message describing the fallback"
    )
    suggested_fix: str | None = Field(
        None, description="Optional suggestion for resolving the underlying issue"
    )
    execution_continues: bool = Field(True, description="True if execution can continue safely")
    retry_count: int = Field(0, ge=0, description="Number of retries performed")
    latency_ms: float | None = Field(
        None, ge=0.0, description="Fallback execution latency in milliseconds"
    )
    permanent_failure: bool = Field(
        False, description="True if error is not retryable (e.g., 401, 403)"
    )
    constitutional_bypass: bool = Field(
        False,
        description="Always False - constitutional compliance CANNOT be bypassed (Article III)",
    )
    test_verification_required: bool = Field(
        True,
        description="Always True - tests MUST be verified before merge (Article II)",
    )
    budget_guard_active: bool = Field(
        True,
        description="Always True - budget guard MUST remain active (Article III)",
    )
    compliance_notes: str = Field(
        "",
        description="Human-readable notes on constitutional compliance status",
    )
    next_steps: str = Field(
        "",
        description="Optional user-facing next steps for manual intervention",
    )


class RetryPolicy(BaseModel):
    """
    Configurable retry policy with exponential backoff.

    Implements Article I requirement for retries with increasing timeouts
    (2x, 3x, up to 10x base delay).

    Constitutional Compliance:
    - Article I: Complete context before action (retry on transient failures)
    - Permanent failures (401, 403) abort immediately (no wasteful retries)
    """

    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(5, ge=1, le=10, description="Maximum retry attempts")
    base_delay_seconds: float = Field(
        2.0, gt=0.0, description="Base delay in seconds before first retry"
    )
    backoff_multiplier: float = Field(2.0, ge=1.0, description="Multiplier for exponential backoff")
    abort_on_errors: list[str] = Field(
        default_factory=lambda: ["401", "403"],
        description="HTTP status codes or error types that abort immediately (permanent failures)",
    )

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number using exponential backoff.

        Args:
            attempt: Zero-indexed attempt number (0 = first retry)

        Returns:
            Delay in seconds before the next retry

        Example:
            policy = RetryPolicy(base_delay_seconds=2.0, backoff_multiplier=2.0)
            policy.get_delay(0)  # Returns 2.0 (2s)
            policy.get_delay(1)  # Returns 4.0 (4s)
            policy.get_delay(2)  # Returns 8.0 (8s)

        Constitutional Compliance:
            Implements Article I retry protocol (2x, 3x, ..., 10x timeout)
        """
        return self.base_delay_seconds * (self.backoff_multiplier**attempt)


class FallbackError(Exception):
    """
    Exception raised when all fallback strategies are exhausted.

    This exception indicates a non-recoverable failure where:
    1. Primary infrastructure is unavailable
    2. All fallback strategies failed
    3. Retry limit exceeded (if applicable)
    4. Manual intervention required

    Attributes:
        error_type: Classification of error (RETRY_EXHAUSTED, PERMANENT_FAILURE, etc.)
        message: Human-readable error description
        retry_count: Number of retries attempted before failure
        suggested_fix: Optional guidance for resolving the issue
        permanent_failure: True if error is permanent (e.g., 401, 403)
    """

    def __init__(
        self,
        error_type: str,
        message: str,
        retry_count: int = 0,
        suggested_fix: str | None = None,
    ):
        """
        Initialize FallbackError with detailed failure context.

        Args:
            error_type: Error classification (e.g., "RETRY_EXHAUSTED", "PERMANENT_FAILURE")
            message: Human-readable error message
            retry_count: Number of retry attempts performed
            suggested_fix: Optional suggestion for resolving the error
        """
        self.error_type = error_type
        self.message = message
        self.retry_count = retry_count
        self.suggested_fix = suggested_fix
        # Permanent failure if explicitly marked OR if retries exhausted
        self.permanent_failure = error_type in ("PERMANENT_FAILURE", "RETRY_EXHAUSTED")
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message with all context."""
        parts = [f"[{self.error_type}] {self.message}"]
        if self.retry_count > 0:
            parts.append(f"(after {self.retry_count} retries)")
        if self.suggested_fix:
            parts.append(f"Suggested fix: {self.suggested_fix}")
        return " ".join(parts)


# ============================================================================
# CONSTITUTIONAL VALIDATION MODELS (PHASE1-002)
# ============================================================================


class RetryConfig(BaseModel):
    """
    Configuration for Article I retry protocol with exponential backoff.

    Defines timeout multipliers for retry attempts:
    - First retry: 2x initial timeout (e.g., 120s → 240s)
    - Second retry: 3x initial timeout (e.g., 120s → 360s)
    - Final retry: 10x initial timeout (e.g., 120s → 1200s)

    Article I: "At EVERY timeout: halt and analyze, retry with extended timeouts (2x, 3x, up to 10x)"

    Example:
        >>> config = RetryConfig(max_retries=3, initial_timeout=120.0)
        >>> config.timeout_multipliers
        [2.0, 3.0, 10.0]

    Constitutional Compliance:
        - Article I: Complete context before action (retry on timeout)
    """

    model_config = ConfigDict(extra="forbid")

    max_retries: int = Field(3, ge=1, description="Maximum retry attempts")
    initial_timeout: float = Field(120.0, gt=0, description="Initial timeout in seconds")
    timeout_multipliers: list[float] = Field(
        default=[2.0, 3.0, 10.0], description="Timeout multipliers for retries"
    )


class TestGateResult(BaseModel):
    """
    Result from Article II test gate validation (100% pass rate enforcement).

    Tracks test execution results and enforces constitutional requirement
    that ALL tests must pass before PR creation.

    Article II: "Main branch MUST maintain 100% test success - no exceptions"

    Fields:
        pass_rate: Test pass percentage (0.0 to 1.0, MUST be 1.0 for PR)
        total_tests: Total number of tests executed
        passed_tests: Number of tests that passed
        failed_tests: List of failed test names (empty if pass_rate = 1.0)
        simulation_detected: True if mocked/simulated work detected in production code

    Example:
        >>> result = TestGateResult(
        ...     pass_rate=1.0,
        ...     total_tests=100,
        ...     passed_tests=100,
        ...     failed_tests=[]
        ... )
        >>> result.pass_rate == 1.0  # Required for PR creation
        True

    Constitutional Compliance:
        - Article II: 100% verification and stability (no merge without green tests)
    """

    model_config = ConfigDict(extra="forbid")

    pass_rate: float = Field(..., ge=0.0, le=1.0)
    total_tests: int = Field(..., ge=0)
    passed_tests: int = Field(..., ge=0)
    failed_tests: list[str] = Field(default_factory=list)
    simulation_detected: bool = Field(False, description="True if mocked tests detected")


class BypassAttempt(BaseModel):
    """
    Record of Article III bypass attempt for audit trail.

    Logs all attempts to circumvent quality gates, including:
    - --force flags
    - Environment variable overrides (SKIP_TESTS=true, etc.)
    - Manual override function calls
    - Emergency bypass mechanisms

    All bypass attempts are REJECTED and logged for security audit.

    Article III: "No manual override capabilities - quality gates are absolute barriers"

    Fields:
        flag: The flag/mechanism that triggered bypass attempt (e.g., "--force")
        source: Where bypass came from (cli, env_var, config)
        timestamp: When bypass was attempted
        rejected: Whether bypass was rejected (always True)
        article: Constitutional article violated (default: "Article III")

    Example:
        >>> attempt = BypassAttempt(
        ...     flag="--force",
        ...     source="cli",
        ...     timestamp=datetime.now(),
        ...     rejected=True
        ... )
        >>> attempt.article
        'Article III'

    Constitutional Compliance:
        - Article III: Automated merge enforcement (no manual overrides)
    """

    model_config = ConfigDict(extra="forbid")

    flag: str = Field(..., description="Flag that triggered bypass attempt (--force, etc)")
    source: str = Field(..., description="Source of bypass (cli, env_var, config)")
    timestamp: datetime
    rejected: bool = Field(True, description="Whether bypass was rejected")
    article: str = Field("Article III", description="Constitutional article violated")


class LearningQuery(BaseModel):
    """
    VectorStore query result for Article IV learning integration.

    Stores results from VectorStore pattern queries before task execution,
    ensuring agents apply accumulated institutional knowledge.

    Article IV: "Agents MUST query learnings before decisions"

    Fields:
        tags: Tags used for VectorStore search (e.g., ["pattern", "auth", "success"])
        min_confidence: Minimum confidence threshold (default: 0.6)
        results: List of matching patterns with confidence scores
        execution_time_ms: Time taken for VectorStore query (optional)

    Example:
        >>> query = LearningQuery(
        ...     tags=["pattern", "jwt_auth"],
        ...     min_confidence=0.6,
        ...     results=[
        ...         {"pattern": "TDD workflow", "confidence": 0.85},
        ...         {"pattern": "Result pattern", "confidence": 0.88}
        ...     ],
        ...     execution_time_ms=45.2
        ... )
        >>> len([r for r in query.results if r["confidence"] >= query.min_confidence])
        2

    Constitutional Compliance:
        - Article IV: Continuous learning (VectorStore query before action)
    """

    model_config = ConfigDict(extra="forbid")

    tags: list[str] = Field(..., min_length=1)
    min_confidence: float = Field(0.6, ge=0.0, le=1.0)
    results: list[dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float | None = None


class SpecTrace(BaseModel):
    """
    Spec traceability validation for Article V spec-driven development.

    Validates that task graph tasks trace back to formal specification
    acceptance criteria, ensuring no implementation without approved spec.

    Article V: "All implementation traces to specification"

    Fields:
        spec_id: Specification ID (format: SPEC-XXX, e.g., SPEC-030)
        acceptance_criteria: List of acceptance criteria from spec
        matched: Whether task criteria match spec criteria
        coverage: Percentage of spec criteria covered by task graph (0.0 to 1.0)

    Example:
        >>> trace = SpecTrace(
        ...     spec_id="SPEC-030",
        ...     acceptance_criteria=["CONST-001", "CONST-002", "CONST-003"],
        ...     matched=True,
        ...     coverage=1.0
        ... )
        >>> trace.spec_id
        'SPEC-030'
        >>> trace.coverage == 1.0  # 100% spec coverage
        True

    Constitutional Compliance:
        - Article V: Spec-driven development (traceability to acceptance criteria)
    """

    model_config = ConfigDict(extra="forbid")

    spec_id: str = Field(..., pattern=r"SPEC-\d{3}", description="Spec ID format: SPEC-XXX")
    acceptance_criteria: list[str] = Field(..., min_length=1)
    matched: bool
    coverage: float = Field(..., ge=0.0, le=1.0, description="Percentage of criteria covered")


# ============================================================================
# PRIMEA EXECUTION RESULT MODELS (PHASE1-005)
# ============================================================================


class PRMetadata(BaseModel):
    """
    Metadata for GitHub Pull Request creation.

    Enforces git best practices:
    - Title ≤72 chars (git commit summary line standard)
    - Body with detailed description
    - Branch naming for traceability

    Constitutional Compliance:
    - Article V: Spec-driven (PR metadata traces to mission intent)
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ...,
        min_length=1,
        max_length=72,
        description="PR title (summary line, git best practice: ≤72 chars)",
    )
    body: str = Field(..., min_length=1, description="Full PR description with sections")
    branch: str = Field(..., description="Feature branch name")
    base_branch: str = Field("main", description="Base branch for PR")
    mermaid_graph: str | None = Field(
        None, description="Mermaid diagram of task graph for PR visualization"
    )


class TaskGraphExecution(BaseModel):
    """
    Task graph execution tracking with timing metrics.

    Tracks:
    - Total tasks vs completed/failed tasks
    - Execution timing (start → end)
    - Calculated execution time in seconds

    Constitutional Compliance:
    - Article I: Complete context tracking (all tasks accounted for)
    - Article II: Failed task tracking (verification enforcement)
    """

    model_config = ConfigDict(extra="forbid")

    graph_id: str = Field(..., description="Unique identifier for task graph")
    total_tasks: int = Field(..., ge=0, description="Total number of tasks in graph")
    completed_tasks: int = Field(..., ge=0, description="Number of successfully completed tasks")
    failed_tasks: int = Field(0, ge=0, description="Number of failed tasks")
    start_time: datetime = Field(..., description="Execution start timestamp")
    end_time: datetime | None = Field(None, description="Execution end timestamp")

    @property
    def execution_time_seconds(self) -> float | None:
        """
        Calculate execution time if end_time is set.

        Returns:
            Execution duration in seconds, or None if execution incomplete

        Constitutional Compliance:
            Article I: Complete execution tracking (precise timing)
        """
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class PrimeAResult(BaseModel):
    """
    Complete execution result for PrimeA orchestrator workflow.

    Aggregates:
    - Mission summary and status
    - Task completion metrics
    - Test pass rate (Article II enforcement)
    - Execution timing and performance
    - PR metadata if created
    - Constitutional compliance validation
    - Backlog selection tracking (auto-select mode)

    Constitutional Requirements:
    - test_pass_rate: Enforces Article II (100% verification)
    - constitutional_compliant: Validates all 5 articles before merge
    - selected_from_backlog: Tracks Article IV learning integration
    - mission: Article V spec traceability
    """

    model_config = ConfigDict(extra="forbid")

    mission: str = Field(..., description="Mission title from task graph")
    status: str = Field(..., description="Execution status: complete, failed, partial")
    pr_url: str | None = Field(None, description="GitHub PR URL if created")
    tasks_completed: int = Field(..., ge=0, description="Number of successfully completed tasks")
    tasks_total: int = Field(..., ge=0, description="Total number of tasks in graph")
    test_pass_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Test pass rate (1.0 = 100%, Article II requirement)",
    )
    execution_time_seconds: float = Field(
        ..., ge=0.0, description="Total execution time in seconds"
    )
    visualization: str | None = Field(None, description="Mermaid graph visualization for PR/docs")
    report_path: str | None = Field(None, description="Path to execution report file")
    selected_from_backlog: bool = Field(
        False,
        description="True if task auto-selected from backlog (Article IV learning)",
    )
    backlog_priority: int | None = Field(
        None, ge=1, le=5, description="Priority level from backlog (1=highest, 5=lowest)"
    )
    constitutional_compliant: bool = Field(
        True,
        description="All 5 constitutional articles validated before merge",
    )

    @property
    def completion_rate(self) -> float:
        """
        Calculate task completion rate.

        Returns:
            Completion percentage as decimal (0.0 to 1.0)

        Constitutional Compliance:
            Article II: 100% completion required for merge (completion_rate == 1.0)
        """
        if self.tasks_total == 0:
            return 0.0
        return self.tasks_completed / self.tasks_total


# ============================================================================
# BACKLOG AUTO-SELECTION MODELS (PHASE1-001)
# ============================================================================


class TaskStatus(str, Enum):
    """
    Task lifecycle states for backlog management.

    State Transitions:
    - READY → LOCKED (when agent claims task)
    - LOCKED → READY (on failure/timeout)
    - BLOCKED → READY (when blocker resolved)

    Article III: Automated state enforcement (no manual overrides)
    """

    READY = "ready"
    BLOCKED = "blocked"
    LOCKED = "locked"


class BacklogTask(BaseModel):
    """
    Single task in the agency backlog queue.

    Represents a prioritized work item with:
    - Priority: 1 (highest) to 5 (lowest)
    - Status: Ready/Blocked/Locked lifecycle
    - Description: Human-readable task summary
    - Locking: Agent ID and timestamp for duplicate prevention

    Example:
        ```python
        task = BacklogTask(
            priority=1,
            status=TaskStatus.READY,
            description="Implement JWT authentication middleware"
        )

        # Lock task to agent
        task.locked_by = "agent_coder_001"
        task.locked_at = datetime.now()
        task.status = TaskStatus.LOCKED
        ```

    Constitutional Compliance:
    - Article II: Strict typing (no any types)
    - Article III: Field validation enforced (priority 1-5)
    """

    priority: int = Field(
        ..., ge=1, le=5, description="Task priority (1=highest, 5=lowest)"
    )
    status: TaskStatus = Field(..., description="Current task status in lifecycle")
    description: str = Field(
        ..., min_length=1, description="Human-readable task description from markdown"
    )
    locked_by: str | None = Field(
        None, description="Agent ID that locked this task (prevents duplicate work)"
    )
    locked_at: datetime | None = Field(
        None, description="Timestamp when task was locked (for timeout detection)"
    )

    model_config = ConfigDict(
        frozen=False,  # Allow updates for locking/unlocking
        validate_assignment=True,  # Validate on field updates (enforce priority 1-5)
    )


class BacklogQueue(BaseModel):
    """
    Container for backlog task queue with file persistence.

    Manages task list with:
    - Priority-based sorting (highest priority first)
    - Status filtering (Ready tasks only)
    - File synchronization (markdown persistence)
    - Modification tracking (detect external changes)

    Example:
        ```python
        queue = BacklogQueue(
            tasks=[
                BacklogTask(priority=1, status=TaskStatus.READY, description="Task A"),
                BacklogTask(priority=2, status=TaskStatus.BLOCKED, description="Task B"),
                BacklogTask(priority=3, status=TaskStatus.READY, description="Task C"),
            ],
            file_path="~/.agency/memories/agency_backlog/test_suite_gaps.md"
        )

        # Get next available task
        ready_tasks = queue.get_ready_tasks()  # [Task A, Task C] (sorted by priority)
        next_task = ready_tasks[0]  # Task A (priority 1)
        ```

    Constitutional Compliance:
    - Article I: Complete context (last_modified tracks external changes)
    - Article IV: Learning integration (backlog patterns stored in VectorStore)
    """

    tasks: list[BacklogTask] = Field(
        default_factory=list, description="All tasks in backlog (any status)"
    )
    file_path: str = Field(..., description="Absolute path to backlog markdown file")
    last_modified: datetime | None = Field(
        None, description="File modification timestamp (detect external edits)"
    )

    def get_ready_tasks(self) -> list[BacklogTask]:
        """
        Return Ready tasks sorted by priority (ascending).

        Filters out Blocked and Locked tasks, returning only tasks
        available for immediate execution.

        Returns:
            List of Ready tasks, sorted by priority (1=highest first)

        Example:
            ```python
            queue = BacklogQueue(tasks=[
                BacklogTask(priority=3, status=TaskStatus.READY, description="C"),
                BacklogTask(priority=1, status=TaskStatus.READY, description="A"),
                BacklogTask(priority=2, status=TaskStatus.BLOCKED, description="B"),
            ])

            ready = queue.get_ready_tasks()
            # Returns: [Task A (priority=1), Task C (priority=3)]
            # Task B excluded (Blocked status)
            ```

        Constitutional Compliance:
        - Article III: Status enforcement (only Ready tasks returned)
        - Article II: Deterministic ordering (priority sort)
        """
        ready_tasks = [task for task in self.tasks if task.status == TaskStatus.READY]

        # Sort by priority ascending (1=highest priority)
        return sorted(ready_tasks, key=lambda task: task.priority)


# ============================================================================
# GIT VALIDATION MODELS (PHASE1-003)
# ============================================================================


class BranchInfo(BaseModel):
    """
    Git branch information with pattern matching metadata.

    Tracks branch name, protection status, and matched pattern for validation.
    Used during Phase 0 git validation before orchestrator execution.

    Attributes:
        name: Branch name (e.g., "feat/test", "main", "fix/bug-123")
        protected: True if branch is protected (main, master, develop)
        pattern: Matched pattern (e.g., "feat/*", "fix/*", "docs/*")

    Constitutional Compliance:
        - Article III: Protected branches (main, master, develop) cannot be modified
        - No bypass mechanism exists (protected flag is enforced)

    Example:
        >>> branch = BranchInfo(name="feat/test", protected=False, pattern="feat/*")
        >>> assert branch.is_safe_for_execution() == True

        >>> protected = BranchInfo(name="main", protected=True)
        >>> assert protected.is_safe_for_execution() == False
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Git branch name")
    protected: bool = Field(
        default=False, description="True if branch is protected (main, master, develop)"
    )
    pattern: str | None = Field(
        None, description="Matched pattern (feat/*, fix/*, docs/*, refactor/*, test/*)"
    )

    def is_safe_for_execution(self) -> bool:
        """
        Check if branch is safe for autonomous execution.

        Returns:
            True if branch is NOT protected (safe for execution)
            False if branch is protected (execution blocked by Article III)

        Constitutional Note:
            Protected branches ALWAYS return False - no bypass mechanism exists.
        """
        return not self.protected


class GitValidationResult(BaseModel):
    """
    Result of git branch validation with constitutional metadata.

    Provides validation outcome, branch details, pattern matching results,
    and error messages with recovery hints.

    Attributes:
        is_safe: True if branch is safe for execution (not protected)
        branch_name: Current git branch name
        pattern_match: Pattern that matched (e.g., "feat/*") or None
        error_message: Error details if validation failed (None if safe)
        article: Constitutional article for protection (default: "Article III")

    Constitutional Compliance:
        - Article III: Automated Merge Enforcement (no manual bypass)
        - Protected branches (main, master, develop) always fail validation
        - Error messages include actionable recovery hints

    Example:
        >>> # Safe branch
        >>> result = GitValidationResult(
        ...     is_safe=True,
        ...     branch_name="feat/test",
        ...     pattern_match="feat/*",
        ...     article="Article III"
        ... )
        >>> assert result.is_safe == True

        >>> # Protected branch
        >>> result = GitValidationResult(
        ...     is_safe=False,
        ...     branch_name="main",
        ...     error_message="Cannot execute on protected branch 'main'",
        ...     article="Article III"
        ... )
        >>> assert result.is_safe == False
    """

    model_config = ConfigDict(extra="forbid")

    is_safe: bool = Field(..., description="True if branch is safe for execution")
    branch_name: str = Field(..., min_length=1, description="Current git branch name")
    pattern_match: str | None = Field(None, description="Pattern that matched (e.g., 'feat/*')")
    error_message: str | None = Field(
        None, description="Error details if validation failed (None if safe)"
    )
    article: str = Field(
        default="Article III",
        description="Constitutional article for protection (Article III: Automated Merge Enforcement)",
    )

    def raise_if_unsafe(self) -> None:
        """
        Raise GitValidationError if validation failed.

        Raises:
            GitValidationError: If is_safe is False

        Usage:
            >>> result = validate_branch_safety(repo_path)
            >>> result.unwrap().raise_if_unsafe()  # Raises if unsafe
        """
        if not self.is_safe:
            raise GitValidationError(
                message=self.error_message or f"Branch '{self.branch_name}' is not safe",
                branch_name=self.branch_name,
                recovery_hint="Checkout a feature branch: git checkout -b feat/<feature-name>",
            )


# ============================================================================
# TYPE-SAFE RESPONSE MODELS (Leap 8 - Article II Strict Typing)
# ============================================================================


class TestFailure(BaseModel):
    """
    Individual test failure details for constitutional validation.

    Captures all information needed to diagnose and fix test failures:
    - Test name and location (file:line)
    - Error message and stack trace
    - Recommended fix (if available)

    Constitutional Compliance:
        - Article II: 100% verification (no dict[str, Any] for test results)

    Example:
        >>> failure = TestFailure(
        ...     test="test_auth_token_valid",
        ...     file="tests/test_auth.py",
        ...     line=42,
        ...     error="AssertionError: Expected 200, got 401",
        ...     recommended_fix="Check token expiry logic"
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    test: str = Field(..., min_length=1, description="Test function name")
    file: str | None = Field(None, description="Test file path")
    line: int | None = Field(None, ge=1, description="Line number where test failed")
    error: str = Field("", description="Error message or stack trace")
    recommended_fix: str | None = Field(None, description="Suggested fix for failure")


class TestResultsInput(BaseModel):
    """
    Test execution results input for Article II validation.

    Enhanced version of TestGateResult with detailed failure information
    for constitutional test gate enforcement.

    Fields:
        pass_rate: Percentage of tests passed (0.0 to 1.0)
        test_count: Total number of tests executed
        tests_passed: Number of tests that passed
        tests_failed: Number of tests that failed
        failures: List of detailed failure information

    Constitutional Compliance:
        - Article II: 100% verification (pass_rate must be 1.0 for merge)

    Example:
        >>> results = TestResultsInput(
        ...     pass_rate=1.0,
        ...     test_count=100,
        ...     tests_passed=100,
        ...     tests_failed=0,
        ...     failures=[]
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    pass_rate: float = Field(..., ge=0.0, le=1.0)
    test_count: int = Field(..., ge=0)
    tests_passed: int = Field(..., ge=0)
    tests_failed: int = Field(..., ge=0)
    failures: list[TestFailure] = Field(default_factory=list)


class PatternContent(BaseModel):
    """
    Flexible pattern content for VectorStore storage (Article IV).

    Allows any fields to accommodate different pattern types while
    enforcing type safety for common fields.

    Common Fields (all optional):
        code: Implementation code snippet
        tests_passed: Whether tests passed for this pattern
        confidence: Confidence score (0.0 to 1.0)
        description: Human-readable description
        tags: Categorization tags

    Constitutional Compliance:
        - Article II: Strict typing (no dict[str, Any])
        - Article IV: Pattern storage after successful operations

    Example:
        >>> pattern = PatternContent(
        ...     code="def authenticate(token): ...",
        ...     tests_passed=True,
        ...     confidence=0.92,
        ...     description="JWT auth with RS256 signing",
        ...     tags=["auth", "jwt", "security"]
        ... )
    """

    model_config = ConfigDict(extra="allow")  # Allow additional fields per pattern type

    # Common optional fields
    code: str | None = None
    tests_passed: bool | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    description: str | None = None
    tags: list[str] | None = None


class ExecutionContextInput(BaseModel):
    """
    Execution context for Article III bypass detection.

    Provides CLI flags and environment variables for
    constitutional bypass detection and audit logging.

    Fields:
        flags: CLI flags passed to orchestrator (e.g., ["--force", "--no-verify"])

    Constitutional Compliance:
        - Article III: Automated enforcement (no manual bypass)

    Example:
        >>> context = ExecutionContextInput(
        ...     flags=["--force", "--no-verify"]
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    flags: list[str] = Field(default_factory=list)


class HealthCheckResponse(BaseModel):
    """
    Health check response for local model availability testing.

    Used by fallback handlers to determine if local models (Ollama)
    are available for P3 task execution.

    Fields:
        status: Health status ("healthy", "unhealthy", "timeout")
        error: Error message if unhealthy (None if healthy)

    Constitutional Compliance:
        - Article II: Strict typing (no dict[str, Any])

    Example:
        >>> response = HealthCheckResponse(
        ...     status="healthy"
        ... )
        >>> response = HealthCheckResponse(
        ...     status="unhealthy",
        ...     error="Connection refused"
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., pattern="^(healthy|unhealthy|timeout)$")
    error: str | None = None


class GitHubAPIResponse(BaseModel):
    """
    GitHub API response for PR/issue operations.

    Used by fallback handlers and retry logic for GitHub
    API interactions (rate limiting, transient failures).

    Fields:
        status: Response status ("success", "error")
        pr_url: Pull request URL if created (None on error)
        error: Error message if status is error (None on success)

    Constitutional Compliance:
        - Article II: Strict typing (no dict[str, Any])

    Example:
        >>> response = GitHubAPIResponse(
        ...     status="success",
        ...     pr_url="https://github.com/org/repo/pull/123"
        ... )
        >>> response = GitHubAPIResponse(
        ...     status="error",
        ...     error="HTTP 429: Rate limit exceeded"
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., pattern="^(success|error)$")
    pr_url: str | None = None
    error: str | None = None


class GitValidationError(Exception):
    """
    Exception raised when git validation fails.

    Raised for:
    - Protected branch execution attempt (main, master, develop)
    - Detached HEAD state
    - Invalid branch name pattern
    - Git repository errors (missing repo, locked index, timeout)

    Attributes:
        message: Human-readable error message
        branch_name: Branch that caused the error (None if not applicable)
        recovery_hint: Actionable guidance for user (e.g., "git checkout -b feat/fix")

    Constitutional Compliance:
        - Article III: No bypass mechanism exists (no --force flag)
        - Error messages reference Article III for protected branches
        - Recovery hints guide user to safe workflows

    Example:
        >>> try:
        ...     validate_branch_safety(repo_path="./my-repo")
        ... except GitValidationError as e:
        ...     print(f"Error: {e.message}")
        ...     print(f"Branch: {e.branch_name}")
        ...     print(f"Hint: {e.recovery_hint}")
    """

    def __init__(
        self,
        message: str,
        branch_name: str | None = None,
        recovery_hint: str | None = None,
    ) -> None:
        """
        Initialize GitValidationError with message and recovery guidance.

        Args:
            message: Human-readable error message (required)
            branch_name: Branch that caused the error (optional)
            recovery_hint: Actionable guidance for recovery (optional)

        Example:
            >>> error = GitValidationError(
            ...     message="Cannot execute on protected branch 'main' (Article III)",
            ...     branch_name="main",
            ...     recovery_hint="Checkout feature branch: git checkout -b feat/fix"
            ... )
            >>> raise error
        """
        self.message = message
        self.branch_name = branch_name
        self.recovery_hint = recovery_hint
        super().__init__(message)

    def __str__(self) -> str:
        """
        Format error message with recovery hint.

        Returns:
            Formatted error string with message and optional recovery hint

        Example:
            >>> error = GitValidationError(
            ...     "Protected branch",
            ...     branch_name="main",
            ...     recovery_hint="git checkout -b feat/fix"
            ... )
            >>> str(error)
            'Protected branch (Hint: git checkout -b feat/fix)'
        """
        if self.recovery_hint:
            return f"{self.message} (Hint: {self.recovery_hint})"
        return self.message

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Returns:
            String representation with all attributes

        Example:
            >>> error = GitValidationError("Error", branch_name="main")
            >>> repr(error)
            "GitValidationError(message='Error', branch_name='main', recovery_hint=None)"
        """
        return (
            f"GitValidationError(message={self.message!r}, "
            f"branch_name={self.branch_name!r}, "
            f"recovery_hint={self.recovery_hint!r})"
        )


# ============================================================================
# TIERED SPEC REVIEW MODELS (Leap 7 - Two-Stage Workflow Enhancement)
# ============================================================================


class ConstitutionalStatus(str, Enum):
    """
    Constitutional compliance status for specifications.

    Used in Tier 1 summaries to indicate whether the specification
    meets all 5 constitutional articles (I-V).
    """

    COMPLIANT = "compliant"  # All articles satisfied (✅)
    NEEDS_REVIEW = "needs_review"  # Missing required sections (⚠️)
    NON_COMPLIANT = "non_compliant"  # Violations detected (🔴)


class RiskLevel(str, Enum):
    """
    Risk assessment for feature implementation.

    Used in Tier 1 summaries to communicate implementation risk
    and guide user approval decisions.
    """

    LOW = "low"  # Well-understood problem, low complexity (🟢)
    MEDIUM = "medium"  # Some complexity, moderate risk (🟡)
    HIGH = "high"  # Novel problem, high complexity, critical system (🔴)


class ArchitecturalDecision(BaseModel):
    """
    Single architectural decision with rationale and trade-offs.

    Represents one key decision in Tier 2 (e.g., "RSA-256 vs HMAC-SHA256").
    Includes choice made, reasoning, and acknowledged trade-offs.

    Fields:
        title: Decision title (e.g., "RSA-256 vs HMAC-SHA256")
        choice: Selected option (e.g., "RSA-256")
        rationale: Why this choice was made (1-2 sentences)
        tradeoffs: Acknowledged trade-offs (1-2 sentences)

    Constitutional Compliance:
        - Article II: Strict typing (no dict[str, Any])
        - Article V: Spec-driven (traceable decision rationale)

    Example:
        >>> decision = ArchitecturalDecision(
        ...     title="Token Storage",
        ...     choice="HTTP-only cookies",
        ...     rationale="XSS protection, automatic transmission",
        ...     tradeoffs="CSRF risk (mitigated with CSRF tokens)"
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=5, max_length=100, description="Decision title")
    choice: str = Field(..., min_length=2, max_length=100, description="Selected option")
    rationale: str = Field(
        ..., min_length=10, max_length=500, description="Reasoning (1-2 sentences)"
    )
    tradeoffs: str = Field(
        ..., min_length=10, max_length=500, description="Trade-offs (1-2 sentences)"
    )


class Tier1Summary(BaseModel):
    """
    Tier 1: Executive Summary (<25 lines, 30-second read).

    Provides the minimum information needed for rapid approval:
    - Mission statement (what are we building?)
    - Approach (how are we building it?)
    - Test summary (how is it verified?)
    - Deliverables (what files will be created?)
    - Constitutional status (does it comply with Articles I-V?)
    - Effort estimate (how long will it take?)
    - Risk level (how risky is this change?)

    Constitutional Compliance:
        - Article I: Complete context (all required fields present)
        - Article II: Test summary required (100% verification)
        - Article V: Mission statement traces to specification

    Example:
        >>> tier1 = Tier1Summary(
        ...     mission="Implement JWT authentication with RSA-256 signing",
        ...     approach="Use PyJWT library with RSA key pair generation",
        ...     test_summary="47 NECESSARY tests (Normal, Edge, Security)",
        ...     deliverables=["auth_middleware.py", "jwt_utils.py", "tests/"],
        ...     constitutional_status=ConstitutionalStatus.COMPLIANT,
        ...     effort_estimate="6-8 hours",
        ...     risk_level=RiskLevel.MEDIUM,
        ...     line_count=20
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    mission: str = Field(
        ..., min_length=10, max_length=500, description="Mission statement (1-2 sentences)"
    )
    approach: str = Field(
        ..., min_length=10, max_length=500, description="Technical approach (1-2 sentences)"
    )
    test_summary: str = Field(
        ..., min_length=10, max_length=300, description="Test coverage summary"
    )
    deliverables: list[str] = Field(
        ..., min_length=1, description="List of files to be created/modified"
    )
    constitutional_status: ConstitutionalStatus = Field(
        ..., description="Articles I-V compliance status"
    )
    effort_estimate: str = Field(
        ..., min_length=3, max_length=50, description="Time estimate (e.g., '4-6 hours')"
    )
    risk_level: RiskLevel = Field(..., description="Implementation risk level")
    line_count: int = Field(..., ge=1, le=25, description="Tier 1 line count (must be ≤25)")


class Tier2Summary(BaseModel):
    """
    Tier 2: Key Decisions (<50 lines, 2-minute read).

    Provides deeper context on architectural choices:
    - 4-6 architectural decisions with rationale/trade-offs
    - Security implications
    - Dependencies (libraries, services)
    - Performance considerations (optional)

    Constitutional Compliance:
        - Article I: Complete context (all decisions documented)
        - Article V: Decision rationale traces to spec

    Example:
        >>> tier2 = Tier2Summary(
        ...     decisions=[
        ...         ArchitecturalDecision(
        ...             title="RSA-256 vs HMAC-SHA256",
        ...             choice="RSA-256",
        ...             rationale="Public key verification without exposing private key",
        ...             tradeoffs="Slower signing vs better security model"
        ...         )
        ...     ],
        ...     security_implications="Private key must be stored in HSM",
        ...     dependencies="PyJWT 2.8+, cryptography 41.0+",
        ...     line_count=35
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    decisions: list[ArchitecturalDecision] = Field(
        ..., min_length=1, max_length=6, description="4-6 key architectural decisions"
    )
    security_implications: str = Field(..., min_length=10, description="Security considerations")
    dependencies: str = Field(..., min_length=5, description="Required libraries/services")
    performance_notes: str | None = Field(None, description="Optional performance considerations")
    line_count: int = Field(..., ge=1, le=50, description="Tier 2 line count (must be ≤50)")


class Tier3Reference(BaseModel):
    """
    Tier 3: Full Specification Reference.

    Points to the complete specification file with metadata:
    - File path (absolute or relative)
    - Line count (total lines in spec)
    - Section count (number of ## sections)

    Constitutional Compliance:
        - Article I: Complete context (full spec always available)
        - Article V: Spec traceability (file path stored)

    Example:
        >>> tier3 = Tier3Reference(
        ...     file_path=Path("/tmp/spec_jwt_auth.md"),
        ...     line_count=250,
        ...     section_count=8
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    file_path: Path = Field(..., description="Path to full specification file")
    line_count: int = Field(..., ge=1, description="Total lines in specification")
    section_count: int = Field(..., ge=1, description="Number of sections (## headings)")


class TieredSpec(BaseModel):
    """
    Complete tiered specification (Tier 1 + Tier 2 + Tier 3).

    Combines all three tiers for progressive disclosure UI:
    - Tier 1: Show immediately (30-second read)
    - Tier 2: Show if user requests more detail (2-minute read)
    - Tier 3: Show if user wants full spec (interactive view)

    Constitutional Compliance:
        - Article I: Complete context (all tiers present)
        - Article II: Test summary in Tier 1 (verification required)
        - Article V: Spec file in Tier 3 (traceability)

    Example:
        >>> tiered_spec = TieredSpec(
        ...     tier1=tier1_summary,
        ...     tier2=tier2_summary,
        ...     tier3=tier3_reference
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    tier1: Tier1Summary = Field(..., description="Executive summary (<25 lines)")
    tier2: Tier2Summary = Field(..., description="Key decisions (<50 lines)")
    tier3: Tier3Reference = Field(..., description="Full spec reference")


class UserAction(str, Enum):
    """
    User action at checkpoint (keyboard shortcuts).

    Used by CheckpointUI to track which action user selected:
    - APPROVE: Proceed with implementation (press 'A')
    - REVISE: Request specification changes (press 'R')
    - VIEW: View full spec (press 'V', then re-prompt)
    - QUIT: Cancel orchestration (press 'Q')
    """

    APPROVE = "approve"
    REVISE = "revise"
    VIEW = "view"
    QUIT = "quit"


class CheckpointResult(BaseModel):
    """
    Result of checkpoint interaction.

    Tracks user's decision and which tier they viewed before deciding:
    - action: What user chose (APPROVE/REVISE/VIEW/QUIT)
    - tier_viewed: Which tier was last displayed (1/2/3)
    - timestamp: When decision was made

    Constitutional Compliance:
        - Article I: Complete context (tier_viewed tracked)
        - Article V: Decision trace (timestamp stored)

    Example:
        >>> result = CheckpointResult(
        ...     action=UserAction.APPROVE,
        ...     tier_viewed=1,  # Approved after reading Tier 1 only
        ...     timestamp=datetime.now(UTC)
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    action: UserAction = Field(..., description="User action (APPROVE/REVISE/VIEW/QUIT)")
    tier_viewed: int = Field(
        ..., ge=1, le=3, description="Last tier viewed before decision (1/2/3)"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="Decision timestamp"
    )


class TierGenerationError(BaseModel):
    """
    Error during tier generation with recovery hints.

    Used when spec_tier_generator fails to parse specification:
    - reason: Human-readable error message
    - file_path: Spec file that caused error
    - recovery_hint: Suggested fix

    Example:
        >>> error = TierGenerationError(
        ...     reason="Specification file is empty",
        ...     file_path=Path("/tmp/empty_spec.md"),
        ...     recovery_hint="Add Executive Summary section to spec"
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(..., min_length=10, description="Error reason")
    file_path: Path | None = Field(None, description="Spec file that caused error")
    recovery_hint: str | None = Field(None, description="Suggested fix")


__all__ = [
    "FallbackStrategy",
    "FallbackResult",
    "RetryPolicy",
    "FallbackError",
    "RetryConfig",
    "TestGateResult",
    "BypassAttempt",
    "LearningQuery",
    "SpecTrace",
    "PRMetadata",
    "TaskGraphExecution",
    "PrimeAResult",
    "TaskStatus",
    "BacklogTask",
    "BacklogQueue",
    "BranchInfo",
    "GitValidationResult",
    "GitValidationError",
    "TestFailure",
    "TestResultsInput",
    "PatternContent",
    "ExecutionContextInput",
    "HealthCheckResponse",
    "GitHubAPIResponse",
    # Tiered Spec Review Models (Leap 7)
    "ConstitutionalStatus",
    "RiskLevel",
    "ArchitecturalDecision",
    "Tier1Summary",
    "Tier2Summary",
    "Tier3Reference",
    "TieredSpec",
    "UserAction",
    "CheckpointResult",
    "TierGenerationError",
]
