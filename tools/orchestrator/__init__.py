"""
Orchestrator System - Advanced Agent Task Coordination

This module provides sophisticated orchestration capabilities extracted from
the enterprise infrastructure branch. Key features:

- Parallel task execution with concurrency control
- Exponential backoff retry policies with jitter
- Real-time heartbeat monitoring
- Comprehensive telemetry integration
- Graceful error handling and recovery
- Cost accounting and resource utilization tracking
- Two-stage TDD orchestration (Intent-to-Spec, Spec-to-Execution)

Usage:
    from tools.orchestrator.scheduler import run_parallel, OrchestrationPolicy, TaskSpec
    from tools.orchestrator.intent_parser import IntentParser, InputMode, Intent

    # Orchestration scheduling
    policy = OrchestrationPolicy(
        max_concurrency=4,
        retry=RetryPolicy(max_attempts=3, backoff="exp")
    )
    result = await run_parallel(context, task_specs, policy)

    # Intent parsing (Leap 7)
    parser = IntentParser(context)
    result = parser.parse(None, InputMode.AUTO_SELECT)
"""

from .completion_validator import (
    CompletionValidator,
    ConstitutionalChecks,
)
from .completion_validator import (
    ValidationError as CompletionValidationError,
)
from .completion_validator import (
    ValidationResults as CompletionValidationResults,
)
from .intent_parser import InputMode, Intent, IntentParser
from .retry_policy import (
    IdempotencyKey,
    RetryExhausted,
    RetryMetrics,
    retry_with_policy,
    retry_with_policy_sync,
)
from .retry_policy import (
    RetryPolicy as EnhancedRetryPolicy,
)
from .scheduler import (
    BackoffType,
    CancellationType,
    FairnessType,
    OrchestrationPolicy,
    OrchestrationResult,
    RetryPolicy,
    TaskResult,
    TaskSpec,
    run_parallel,
)
from .spec_generator import Spec, SpecGenerator, SpecIntent
from .test_verification_gate import (
    TestVerificationGate,
    VerificationError,
    VerificationResults,
    verify_tests,
)

__all__ = [
    # Orchestration scheduling
    "run_parallel",
    "OrchestrationPolicy",
    "OrchestrationResult",
    "RetryPolicy",
    "TaskSpec",
    "TaskResult",
    "BackoffType",
    "FairnessType",
    "CancellationType",
    # Enhanced retry policy (Leap 6)
    "EnhancedRetryPolicy",
    "IdempotencyKey",
    "RetryExhausted",
    "RetryMetrics",
    "retry_with_policy",
    "retry_with_policy_sync",
    # Intent parsing (Leap 7)
    "IntentParser",
    "InputMode",
    "Intent",
    # Spec generation (Leap 7)
    "SpecGenerator",
    "SpecIntent",
    "Spec",
    # Test verification gate (Leap 7)
    "TestVerificationGate",
    "VerificationError",
    "VerificationResults",
    "verify_tests",
    # Completion validator (Leap 7)
    "CompletionValidator",
    "CompletionValidationError",
    "CompletionValidationResults",
    "ConstitutionalChecks",
]
