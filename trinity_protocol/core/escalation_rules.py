"""
Escalation Rules Engine - Determines when to escalate from local to cloud models.

Implements intelligent escalation logic:
- LOCAL → LOCAL_PLUS → CLOUD progression
- Rule-based escalation triggers
- Cost-aware decision making

Constitutional Compliance:
- Article I: Complete context before escalation
- Article II: Quality gates trigger escalation
- Article IV: Learn from escalation patterns
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from trinity_protocol.core.agent_registry import ModelTier

logger = logging.getLogger(__name__)


class EscalationTrigger(Enum):
    """Reasons for escalating to higher model tier."""

    TEST_FAILURES = "test_failures"  # Tests failed N times
    TIMEOUT = "timeout"  # Operation timed out
    NOVEL_PROBLEM = "novel_problem"  # No VectorStore match found
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"  # Quality gate failed
    USER_REQUEST = "user_request"  # User explicitly requested complex/high-quality
    ERROR_PATTERN = "error_pattern"  # Known difficult error pattern
    RETRY_EXHAUSTED = "retry_exhausted"  # Max retries reached at current tier
    LOW_CONFIDENCE = "low_confidence"  # Agent confidence below threshold


@dataclass
class EscalationContext:
    """Context for escalation decision."""

    attempt_count: int  # How many attempts at current tier
    current_tier: ModelTier  # Current model tier
    test_failures: int = 0  # Number of test failures
    has_timeout: bool = False  # Whether timeout occurred
    is_novel: bool = False  # Whether problem is novel (no VectorStore match)
    constitutional_violation: bool = False  # Whether quality gate failed
    user_complexity: Literal["low", "medium", "high", "critical"] | None = None
    error_type: str | None = None  # Type of error encountered
    confidence_score: float = 1.0  # Agent's confidence (0-1)


@dataclass
class EscalationDecision:
    """Result of escalation evaluation."""

    should_escalate: bool
    next_tier: ModelTier
    trigger: EscalationTrigger | None
    reason: str
    skip_local: bool = False  # If true, go directly to CLOUD


class EscalationPolicy:
    """
    Policy engine for determining when to escalate models.

    Default policy:
    - Attempt 1-2: LOCAL
    - Attempt 3: LOCAL_PLUS
    - Attempt 4+: CLOUD
    - Override: User complexity=high/critical → skip to CLOUD
    """

    def __init__(
        self,
        max_local_attempts: int = 2,
        max_local_plus_attempts: int = 1,
        test_failure_threshold: int = 2,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize escalation policy.

        Args:
            max_local_attempts: Max attempts at LOCAL tier before escalating
            max_local_plus_attempts: Max attempts at LOCAL_PLUS before escalating
            test_failure_threshold: Number of test failures to trigger escalation
            confidence_threshold: Min confidence score (0-1) to continue at current tier
        """
        self.max_local_attempts = max_local_attempts
        self.max_local_plus_attempts = max_local_plus_attempts
        self.test_failure_threshold = test_failure_threshold
        self.confidence_threshold = confidence_threshold

        logger.info(
            f"EscalationPolicy initialized: "
            f"max_local={max_local_attempts}, "
            f"max_local_plus={max_local_plus_attempts}, "
            f"test_threshold={test_failure_threshold}, "
            f"confidence_threshold={confidence_threshold}"
        )

    def evaluate(self, context: EscalationContext) -> EscalationDecision:
        """
        Evaluate whether to escalate based on context.

        Args:
            context: Current execution context

        Returns:
            EscalationDecision with next tier and reasoning
        """
        # Rule 1: User requested high complexity → skip to CLOUD
        if context.user_complexity in ["high", "critical"]:
            return EscalationDecision(
                should_escalate=True,
                next_tier=ModelTier.CLOUD,
                trigger=EscalationTrigger.USER_REQUEST,
                reason=f"User complexity={context.user_complexity} → direct CLOUD",
                skip_local=True,
            )

        # Rule 2: Constitutional violation → escalate immediately
        if context.constitutional_violation:
            next_tier = self._get_next_tier(context.current_tier)
            return EscalationDecision(
                should_escalate=True,
                next_tier=next_tier,
                trigger=EscalationTrigger.CONSTITUTIONAL_VIOLATION,
                reason="Constitutional violation detected → escalating for quality",
            )

        # Rule 3: Test failures exceed threshold → escalate
        if context.test_failures >= self.test_failure_threshold:
            next_tier = self._get_next_tier(context.current_tier)
            return EscalationDecision(
                should_escalate=True,
                next_tier=next_tier,
                trigger=EscalationTrigger.TEST_FAILURES,
                reason=f"Test failures ({context.test_failures}) ≥ threshold ({self.test_failure_threshold})",
            )

        # Rule 4: Novel problem with no VectorStore match → escalate to CLOUD
        if context.is_novel and context.current_tier != ModelTier.CLOUD:
            return EscalationDecision(
                should_escalate=True,
                next_tier=ModelTier.CLOUD,
                trigger=EscalationTrigger.NOVEL_PROBLEM,
                reason="Novel problem (no VectorStore match) → CLOUD for reasoning",
            )

        # Rule 5: Low confidence score → escalate
        if context.confidence_score < self.confidence_threshold:
            next_tier = self._get_next_tier(context.current_tier)
            return EscalationDecision(
                should_escalate=True,
                next_tier=next_tier,
                trigger=EscalationTrigger.LOW_CONFIDENCE,
                reason=f"Low confidence ({context.confidence_score:.2f}) < threshold ({self.confidence_threshold})",
            )

        # Rule 6: Timeout → escalate
        if context.has_timeout:
            next_tier = self._get_next_tier(context.current_tier)
            return EscalationDecision(
                should_escalate=True,
                next_tier=next_tier,
                trigger=EscalationTrigger.TIMEOUT,
                reason="Operation timeout → escalating to more capable model",
            )

        # Rule 7: Max attempts at current tier → escalate
        if self._should_escalate_by_attempts(context):
            next_tier = self._get_next_tier(context.current_tier)
            return EscalationDecision(
                should_escalate=True,
                next_tier=next_tier,
                trigger=EscalationTrigger.RETRY_EXHAUSTED,
                reason=f"Max attempts ({context.attempt_count}) at {context.current_tier.value} → escalating",
            )

        # No escalation needed
        return EscalationDecision(
            should_escalate=False,
            next_tier=context.current_tier,
            trigger=None,
            reason=f"Continue at {context.current_tier.value} (attempt {context.attempt_count})",
        )

    def _should_escalate_by_attempts(self, context: EscalationContext) -> bool:
        """Check if should escalate based on attempt count at current tier."""
        if context.current_tier == ModelTier.LOCAL:
            return context.attempt_count >= self.max_local_attempts
        elif context.current_tier == ModelTier.LOCAL_PLUS:
            return context.attempt_count >= self.max_local_plus_attempts
        else:  # CLOUD
            return False  # Already at max tier

    def _get_next_tier(self, current_tier: ModelTier) -> ModelTier:
        """Get next tier in escalation chain."""
        escalation_chain = {
            ModelTier.LOCAL: ModelTier.LOCAL_PLUS,
            ModelTier.LOCAL_PLUS: ModelTier.CLOUD,
            ModelTier.CLOUD: ModelTier.CLOUD,  # Stay at CLOUD
        }
        return escalation_chain[current_tier]


# Convenience factory
def create_escalation_policy(
    max_local_attempts: int = 2,
    max_local_plus_attempts: int = 1,
    test_failure_threshold: int = 2,
    confidence_threshold: float = 0.5,
) -> EscalationPolicy:
    """
    Create an EscalationPolicy with custom thresholds.

    Args:
        max_local_attempts: Max attempts at LOCAL tier
        max_local_plus_attempts: Max attempts at LOCAL_PLUS tier
        test_failure_threshold: Test failures before escalation
        confidence_threshold: Min confidence to stay at current tier

    Returns:
        Configured EscalationPolicy
    """
    return EscalationPolicy(
        max_local_attempts=max_local_attempts,
        max_local_plus_attempts=max_local_plus_attempts,
        test_failure_threshold=test_failure_threshold,
        confidence_threshold=confidence_threshold,
    )


# Pre-configured policies for common scenarios
def create_aggressive_escalation_policy() -> EscalationPolicy:
    """Policy that escalates quickly (for critical tasks)."""
    return EscalationPolicy(
        max_local_attempts=1,
        max_local_plus_attempts=1,
        test_failure_threshold=1,
        confidence_threshold=0.7,
    )


def create_conservative_escalation_policy() -> EscalationPolicy:
    """Policy that tries local models extensively before escalating."""
    return EscalationPolicy(
        max_local_attempts=3,
        max_local_plus_attempts=2,
        test_failure_threshold=3,
        confidence_threshold=0.3,
    )


def create_cost_optimized_policy() -> EscalationPolicy:
    """Policy optimized for minimal cloud usage (maximize local attempts)."""
    return EscalationPolicy(
        max_local_attempts=5,
        max_local_plus_attempts=3,
        test_failure_threshold=5,
        confidence_threshold=0.2,  # Very permissive
    )
