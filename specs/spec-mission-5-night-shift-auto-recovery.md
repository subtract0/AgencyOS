# Mission 5: Night Shift & Auto-Recovery - Specification

**Date**: 2025-11-15
**Mission**: Metaproductivity 2.0 - Mission 5
**Status**: Draft
**Dependencies**: Missions 0-4 (CMP, Learning Coach, Self-Healing Agent, Backlog Agent)

---

## 1. Goals & Success Criteria

### Primary Goal
Enable 24/7 autonomous operation of AgencyOS by implementing scheduled execution (Night Shift) and automatic failure recovery, allowing the system to continuously fix tests, implement features, and improve itself without human intervention.

### Success Criteria

**SC1: Night Shift Scheduler Operational**
- Scheduled execution of primeX orchestrator at configurable intervals
- Executes highest-priority backlog tasks during off-hours
- Rate limiting prevents system overload (max N tasks per hour)
- Comprehensive logging of all autonomous operations
- Graceful shutdown and resume capabilities

**SC2: Auto-Recovery System Functional**
- Detects failures during autonomous execution (test failures, build errors, etc.)
- Automatic rollback to last known good state on failure
- Retry logic with exponential backoff (max 3 retries)
- Escalation to user (email/notification) when auto-recovery fails
- Health monitoring and self-diagnostics

**SC3: Quality & Testing**
- 100% test coverage for Night Shift scheduler
- 100% test coverage for Auto-Recovery system
- All tests passing (no regressions in prior missions)
- TDD protocol followed (RED → GREEN → REFACTOR)
- Integration tests with all prior missions (M0-M4)

**SC4: Documentation & Safety**
- Comprehensive spec (this document)
- Safety controls: kill switch, rate limits, dry-run mode
- Monitoring dashboard for autonomous operations
- Updated CLAUDE.md with Mission 5 details
- Completion report with verification

---

## 2. Personas

### P1: Developer (Primary)
**Need**: System that fixes tests and implements features while sleeping
**Pain Point**: Manual intervention required for every failure, blocks progress
**Expectation**: Wake up to green builds and completed features from backlog

### P2: DevOps Engineer
**Need**: Autonomous system with robust failure recovery
**Pain Point**: Automated systems that break in unexpected ways require manual cleanup
**Expectation**: System that can detect and recover from failures automatically

### P3: Product Owner
**Need**: Continuous progress on technical debt and feature backlog
**Pain Point**: Development velocity limited by developer availability (8 hours/day)
**Expectation**: 24/7 operation tripling effective development capacity

---

## 3. Functional Requirements

### FR1: Night Shift Scheduler - Basic Execution
**Requirement**: Night Shift must execute primeX orchestrator on a configurable schedule.

**Acceptance Criteria**:
- Schedule format: cron-like syntax (e.g., "0 2 * * *" = 2 AM daily)
- Default schedule: Every 4 hours (0 */4 * * *)
- Configuration file: `~/.agency/config/night_shift.yaml`
- Executes: `primeX.execute(task_intent=None)` to auto-select from backlog
- Logs all operations to `~/.agency/logs/night_shift/YYYY-MM-DD.log`
- Supports dry-run mode (logs intent without execution)

**Test Coverage**:
- `test_schedule_parsing()` - Parse cron syntax
- `test_next_execution_time()` - Calculate next run time
- `test_dry_run_mode()` - Dry run doesn't execute tasks
- `test_logging()` - All operations logged correctly

### FR2: Night Shift Scheduler - Rate Limiting
**Requirement**: Night Shift must prevent system overload with configurable rate limits.

**Acceptance Criteria**:
- Max tasks per execution: configurable (default: 3)
- Min interval between executions: configurable (default: 15 minutes)
- Max concurrent operations: 1 (sequential execution only)
- Graceful degradation if backlog is empty (log and skip)
- Resource monitoring: abort if CPU >90% or memory >90%

**Test Coverage**:
- `test_max_tasks_per_execution()` - Respects task limit
- `test_min_interval_enforcement()` - Enforces minimum interval
- `test_sequential_execution()` - No concurrent operations
- `test_resource_monitoring()` - Aborts on resource exhaustion

### FR3: Night Shift Scheduler - Graceful Shutdown
**Requirement**: Night Shift must support graceful shutdown and resume.

**Acceptance Criteria**:
- Signal handling: SIGTERM, SIGINT (Ctrl+C) → graceful shutdown
- Shutdown process:
  1. Stop accepting new tasks
  2. Wait for current task to complete (max 10 minutes)
  3. Save state to `~/.agency/state/night_shift_state.json`
  4. Clean exit with status code 0
- Resume: On startup, check for interrupted tasks and resume or mark failed
- Kill switch: File-based (`~/.agency/STOP_NIGHT_SHIFT` exists → immediate shutdown)

**Test Coverage**:
- `test_sigterm_graceful_shutdown()` - SIGTERM triggers shutdown
- `test_sigint_graceful_shutdown()` - SIGINT triggers shutdown
- `test_state_persistence()` - State saved on shutdown
- `test_resume_interrupted_task()` - Resumes interrupted tasks
- `test_kill_switch()` - File-based kill switch works

### FR4: Auto-Recovery - Failure Detection
**Requirement**: Auto-Recovery must detect failures during autonomous execution.

**Acceptance Criteria**:
- Failure types detected:
  1. Test failures (pytest exit code != 0)
  2. Build errors (compilation/linting failures)
  3. Git operation failures (merge conflicts, push failures)
  4. Timeout errors (task exceeds max duration)
  5. Resource exhaustion (OOM, disk full)
- Failure metadata captured: error message, stack trace, exit code, timestamp
- All failures logged to `~/.agency/logs/auto_recovery/YYYY-MM-DD.log`
- VectorStore integration: Store failure patterns for learning

**Test Coverage**:
- `test_detect_test_failure()` - Detects pytest failures
- `test_detect_build_error()` - Detects build errors
- `test_detect_git_failure()` - Detects git failures
- `test_detect_timeout()` - Detects timeouts
- `test_detect_resource_exhaustion()` - Detects resource issues

### FR5: Auto-Recovery - Automatic Rollback
**Requirement**: Auto-Recovery must rollback to last known good state on failure.

**Acceptance Criteria**:
- Git-based rollback: `git reset --hard <last_good_commit>`
- Last known good state: Before task execution started
- Rollback triggers:
  1. Test failures after code changes
  2. Build errors
  3. Git push failures
- Snapshot before execution: Create git tag `auto_snapshot_<timestamp>`
- Rollback verification: Run tests after rollback to confirm green state
- VectorStore update: Mark task as failed, store rollback reason

**Test Coverage**:
- `test_rollback_on_test_failure()` - Rollback on test fail
- `test_rollback_on_build_error()` - Rollback on build error
- `test_snapshot_creation()` - Creates snapshot before execution
- `test_rollback_verification()` - Verifies green state after rollback

### FR6: Auto-Recovery - Retry Logic
**Requirement**: Auto-Recovery must retry failed operations with exponential backoff.

**Acceptance Criteria**:
- Retry strategy:
  1. First retry: Immediate (0 seconds delay)
  2. Second retry: 30 seconds delay
  3. Third retry: 120 seconds delay
  4. Max retries: 3
- Retryable failures:
  1. Transient network errors (git push timeout)
  2. Resource contention (file locks)
  3. Flaky tests (if configured)
- Non-retryable failures:
  1. Test failures (logical errors in code)
  2. Merge conflicts
  3. Build errors
- Retry metadata: Logged with attempt number, delay, outcome

**Test Coverage**:
- `test_retry_exponential_backoff()` - Exponential backoff works
- `test_max_retries()` - Respects max retry limit
- `test_retryable_failures()` - Retries transient errors
- `test_non_retryable_failures()` - Doesn't retry logical errors

### FR7: Auto-Recovery - Escalation
**Requirement**: Auto-Recovery must escalate to user when auto-recovery fails.

**Acceptance Criteria**:
- Escalation triggers:
  1. Max retries exhausted
  2. Non-retryable failure detected
  3. Rollback fails
  4. Resource exhaustion persists
- Escalation methods:
  1. Log critical error to `~/.agency/logs/escalations/YYYY-MM-DD.log`
  2. Create file: `~/.agency/escalations/<task_id>.json` with failure details
  3. Optional: Email notification (if configured)
- Escalation metadata: Task details, failure reason, stack trace, recovery attempts
- User response options: Review and retry manually, skip task, adjust backlog priority

**Test Coverage**:
- `test_escalate_on_max_retries()` - Escalates after max retries
- `test_escalate_on_non_retryable()` - Escalates on non-retryable failures
- `test_escalation_file_creation()` - Creates escalation file
- `test_escalation_metadata()` - Captures all required metadata

### FR8: Health Monitoring & Self-Diagnostics
**Requirement**: Night Shift must monitor system health and perform self-diagnostics.

**Acceptance Criteria**:
- Health checks:
  1. Disk space: >10GB free required
  2. Memory: <80% utilization required
  3. CPU: <90% average utilization (5-minute window)
  4. Git repo: Clean working tree, up-to-date with remote
  5. Dependencies: All required packages installed
- Diagnostic reports: Generated before each execution cycle
- Health status: Logged to `~/.agency/logs/health/YYYY-MM-DD.log`
- Abort execution: If health check fails (prevent cascading failures)
- VectorStore integration: Store health patterns for trend analysis

**Test Coverage**:
- `test_disk_space_check()` - Detects low disk space
- `test_memory_check()` - Detects high memory utilization
- `test_cpu_check()` - Detects high CPU utilization
- `test_git_repo_check()` - Detects dirty working tree
- `test_dependency_check()` - Detects missing dependencies

---

## 4. Data Models

### NightShiftConfig (Pydantic Model)
```python
from pydantic import BaseModel, Field
from typing import Optional

class NightShiftConfig(BaseModel):
    """Configuration for Night Shift scheduler."""

    schedule: str = Field(
        default="0 */4 * * *",
        description="Cron-like schedule (default: every 4 hours)"
    )
    max_tasks_per_execution: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max tasks to execute per cycle"
    )
    min_interval_minutes: int = Field(
        default=15,
        ge=5,
        description="Minimum interval between executions"
    )
    max_task_duration_minutes: int = Field(
        default=60,
        ge=10,
        description="Maximum duration per task (timeout)"
    )
    dry_run: bool = Field(
        default=False,
        description="Dry run mode (log intent without execution)"
    )
    enable_notifications: bool = Field(
        default=False,
        description="Enable email/notification escalations"
    )
    notification_email: Optional[str] = Field(
        default=None,
        description="Email for escalation notifications"
    )
```

### AutoRecoveryConfig (Pydantic Model)
```python
class AutoRecoveryConfig(BaseModel):
    """Configuration for Auto-Recovery system."""

    max_retries: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Maximum retry attempts"
    )
    retry_delays_seconds: list[int] = Field(
        default=[0, 30, 120],
        description="Retry delays (exponential backoff)"
    )
    enable_rollback: bool = Field(
        default=True,
        description="Enable automatic rollback on failure"
    )
    enable_escalation: bool = Field(
        default=True,
        description="Enable escalation to user on failure"
    )
    retryable_errors: list[str] = Field(
        default=["network_timeout", "file_lock", "resource_contention"],
        description="Error types that trigger retry"
    )
```

### NightShiftState (Pydantic Model)
```python
from datetime import datetime

class NightShiftState(BaseModel):
    """Persistent state for Night Shift scheduler."""

    last_execution_time: datetime
    current_task_id: Optional[str] = None
    tasks_completed_this_cycle: int = 0
    total_tasks_completed: int = 0
    total_failures: int = 0
    total_escalations: int = 0
    health_status: dict[str, bool] = Field(
        default_factory=dict,
        description="Latest health check results"
    )
```

### RecoveryAttempt (Pydantic Model)
```python
class RecoveryAttempt(BaseModel):
    """Metadata for a single recovery attempt."""

    task_id: str
    attempt_number: int
    failure_type: str
    error_message: str
    stack_trace: str
    recovery_action: str  # "retry", "rollback", "escalate"
    outcome: str  # "success", "failure"
    timestamp: datetime = Field(default_factory=datetime.now)
```

### EscalationRecord (Pydantic Model)
```python
class EscalationRecord(BaseModel):
    """Record of escalation to user."""

    task_id: str
    failure_reason: str
    recovery_attempts: list[RecoveryAttempt]
    stack_trace: str
    timestamp: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
    resolution_notes: Optional[str] = None
```

---

## 5. Test Plan

### Unit Tests (TDD - Write First)

**Test File**: `tests/test_night_shift_scheduler.py`

#### TestNightShiftScheduler
- `test_schedule_parsing()` - Parse cron syntax
- `test_next_execution_time()` - Calculate next run time
- `test_dry_run_mode()` - Dry run doesn't execute tasks
- `test_logging()` - All operations logged correctly
- `test_max_tasks_per_execution()` - Respects task limit
- `test_min_interval_enforcement()` - Enforces minimum interval
- `test_sequential_execution()` - No concurrent operations
- `test_resource_monitoring()` - Aborts on resource exhaustion

#### TestGracefulShutdown
- `test_sigterm_graceful_shutdown()` - SIGTERM triggers shutdown
- `test_sigint_graceful_shutdown()` - SIGINT triggers shutdown
- `test_state_persistence()` - State saved on shutdown
- `test_resume_interrupted_task()` - Resumes interrupted tasks
- `test_kill_switch()` - File-based kill switch works

**Test File**: `tests/test_auto_recovery.py`

#### TestFailureDetection
- `test_detect_test_failure()` - Detects pytest failures
- `test_detect_build_error()` - Detects build errors
- `test_detect_git_failure()` - Detects git failures
- `test_detect_timeout()` - Detects timeouts
- `test_detect_resource_exhaustion()` - Detects resource issues

#### TestAutomaticRollback
- `test_rollback_on_test_failure()` - Rollback on test fail
- `test_rollback_on_build_error()` - Rollback on build error
- `test_snapshot_creation()` - Creates snapshot before execution
- `test_rollback_verification()` - Verifies green state after rollback

#### TestRetryLogic
- `test_retry_exponential_backoff()` - Exponential backoff works
- `test_max_retries()` - Respects max retry limit
- `test_retryable_failures()` - Retries transient errors
- `test_non_retryable_failures()` - Doesn't retry logical errors

#### TestEscalation
- `test_escalate_on_max_retries()` - Escalates after max retries
- `test_escalate_on_non_retryable()` - Escalates on non-retryable failures
- `test_escalation_file_creation()` - Creates escalation file
- `test_escalation_metadata()` - Captures all required metadata

#### TestHealthMonitoring
- `test_disk_space_check()` - Detects low disk space
- `test_memory_check()` - Detects high memory utilization
- `test_cpu_check()` - Detects high CPU utilization
- `test_git_repo_check()` - Detects dirty working tree
- `test_dependency_check()` - Detects missing dependencies

### Integration Tests

**Test File**: `tests/integration/test_night_shift_integration.py`

- `test_night_shift_end_to_end()` - Full Night Shift cycle
- `test_night_shift_with_primex()` - Integration with Mission 4
- `test_auto_recovery_with_self_healing()` - Integration with Mission 3
- `test_multi_task_execution()` - Multiple tasks in sequence
- `test_failure_recovery_workflow()` - Full failure → rollback → escalate flow

---

## 6. Implementation Plan

### Phase 1: Night Shift Scheduler Core (10-12 hours)
1. **Data Models** (`shared/models/night_shift.py`)
   - NightShiftConfig, NightShiftState

2. **Scheduler Implementation** (`tools/night_shift_scheduler.py`)
   - NightShiftScheduler class
   - Schedule parsing (cron syntax)
   - Execution loop
   - Rate limiting

3. **Tests** (`tests/test_night_shift_scheduler.py`)
   - TestNightShiftScheduler (8 tests)
   - Run: `pytest tests/test_night_shift_scheduler.py::TestNightShiftScheduler -v`

### Phase 2: Graceful Shutdown & State Management (6-8 hours)
1. **Signal Handling** (`tools/night_shift_scheduler.py`)
   - SIGTERM/SIGINT handlers
   - Graceful shutdown logic
   - State persistence

2. **Kill Switch** (`tools/night_shift_scheduler.py`)
   - File-based kill switch (`~/.agency/STOP_NIGHT_SHIFT`)

3. **Tests** (`tests/test_night_shift_scheduler.py`)
   - TestGracefulShutdown (5 tests)

### Phase 3: Auto-Recovery Core (10-12 hours)
1. **Data Models** (`shared/models/auto_recovery.py`)
   - AutoRecoveryConfig, RecoveryAttempt, EscalationRecord

2. **Failure Detection** (`tools/auto_recovery.py`)
   - AutoRecovery class
   - Failure type detection
   - Error metadata capture

3. **Tests** (`tests/test_auto_recovery.py`)
   - TestFailureDetection (5 tests)

### Phase 4: Rollback & Retry Logic (8-10 hours)
1. **Rollback System** (`tools/auto_recovery.py`)
   - Git snapshot creation
   - Automatic rollback
   - Verification after rollback

2. **Retry Logic** (`tools/auto_recovery.py`)
   - Exponential backoff
   - Retryable vs non-retryable classification

3. **Tests** (`tests/test_auto_recovery.py`)
   - TestAutomaticRollback (4 tests)
   - TestRetryLogic (4 tests)

### Phase 5: Escalation & Health Monitoring (8-10 hours)
1. **Escalation System** (`tools/auto_recovery.py`)
   - Escalation triggers
   - Escalation file creation
   - Optional email notifications

2. **Health Monitoring** (`tools/health_monitor.py`)
   - Resource checks (disk, memory, CPU)
   - Git repo validation
   - Dependency checks

3. **Tests** (`tests/test_auto_recovery.py`)
   - TestEscalation (4 tests)
   - TestHealthMonitoring (5 tests)

### Phase 6: Integration & Command Interface (6-8 hours)
1. **Command Implementation** (`.claude/commands/night-shift.md`)
   - `/night-shift start` - Start scheduler
   - `/night-shift stop` - Graceful shutdown
   - `/night-shift status` - Show status
   - `/night-shift config` - Show/edit configuration

2. **Integration** (`tools/night_shift_orchestrator.py`)
   - Integrate with primeX (Mission 4)
   - Integrate with AutoRecovery
   - Integrate with HealthMonitor

3. **Tests** (`tests/integration/test_night_shift_integration.py`)
   - Integration tests (5 tests)

### Phase 7: Documentation & Verification (4-6 hours)
1. **Documentation**
   - CLAUDE.md update
   - Usage guide
   - Safety controls documentation
   - Completion report

2. **Full Test Suite**
   - Run all tests (100% pass required)
   - Integration verification
   - Manual testing of shutdown/resume

---

## 7. Dependencies

**Required from Prior Missions**:
- Mission 0: CmpStore (learning integration)
- Mission 2: LearningCoach (pattern extraction)
- Mission 3: SelfHealingAgent (test failure fixing)
- Mission 4: PrimeXOrchestrator, BacklogAgent (task execution)
- Shared: EnhancedMemoryStore (VectorStore), Result pattern

**External Dependencies**:
- `croniter>=2.0` (cron schedule parsing)
- `pydantic>=2.0` (data models)
- `pytest>=8.0` (testing)
- `psutil>=5.0` (resource monitoring)

---

## 8. Success Metrics

| Metric | Target | Verification Method |
|--------|--------|---------------------|
| Test Coverage | 100% | `pytest --cov=tools/night_shift_scheduler --cov=tools/auto_recovery` |
| Test Pass Rate | 100% | `pytest tests/test_night_shift*.py tests/test_auto_recovery.py -v` |
| TDD Compliance | 100% | Tests written before implementation |
| Uptime | >99% | Monitor for 7 days without manual intervention |
| Auto-Recovery Success | >95% | Track successful recoveries vs escalations |
| Documentation | Complete | Spec, usage guide, safety controls docs |

---

## 9. Safety Controls

### Kill Switch
- **File-based**: `~/.agency/STOP_NIGHT_SHIFT` → immediate shutdown
- **Signal-based**: SIGTERM/SIGINT → graceful shutdown
- **Resource-based**: CPU >90% or memory >90% → abort execution

### Rate Limits
- **Max tasks per cycle**: 3 (default)
- **Min interval**: 15 minutes (default)
- **Max concurrent ops**: 1 (sequential only)
- **Max task duration**: 60 minutes (timeout)

### Dry Run Mode
- **Purpose**: Test scheduling and task selection without execution
- **Usage**: Set `dry_run: true` in config
- **Logs**: All intent logged, no actual execution

### Monitoring Dashboard
- **Health status**: Real-time resource monitoring
- **Task history**: Last 100 tasks executed
- **Failure rate**: Track success/failure/escalation rates
- **CMP integration**: Track clade performance over time

---

## 10. Risk Mitigation

**Risk 1: Runaway Autonomous Execution**
- Mitigation: Rate limits, resource monitoring, kill switch
- Fallback: Manual intervention via STOP_NIGHT_SHIFT file

**Risk 2: Cascading Failures**
- Mitigation: Health checks before each execution, abort on failure
- Fallback: Auto-recovery escalates to user after max retries

**Risk 3: State Corruption**
- Mitigation: Atomic state writes, git snapshots before execution
- Fallback: Rollback to last known good state

**Risk 4: Resource Exhaustion**
- Mitigation: Resource monitoring, task duration limits
- Fallback: Abort execution, escalate to user

---

## 11. Open Questions

1. **Notification Method**: Email, Slack, or file-based only? (MVP: File-based, optional email)
2. **Parallel Execution**: Allow multiple tasks in parallel? (MVP: Sequential only, parallel in future)
3. **Task Priority Override**: Allow manual priority boost during Night Shift? (MVP: No, use backlog priority)
4. **Failure Classification**: Use ML to classify retryable vs non-retryable? (MVP: Hardcoded rules, ML in future)

---

**Specification Version**: 1.0
**Last Updated**: 2025-11-15
**Author**: Claude (AgencyOS Mission 5)
**Status**: Ready for Implementation
