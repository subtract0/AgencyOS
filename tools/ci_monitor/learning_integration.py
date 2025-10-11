#!/usr/bin/env python3
"""
CI Monitor Learning Integration - VectorStore pattern storage and retrieval.

This module implements Article IV (Continuous Learning) for the CI monitor:
stores successful fix patterns and queries historical learnings to improve
fix generation over time.

Constitutional Compliance:
- Article I: Complete context (store all relevant pattern metadata)
- Article II: 100% verification (all tests pass)
- Article IV: MANDATORY VectorStore integration (constitutional requirement)
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md (AC-5)

Architecture:
- Clean public API for learning operations
- Result<T,E> pattern for error handling
- Pydantic models for type safety
- Graceful degradation when VectorStore unavailable

Version: 1.0.0
Created: 2025-10-11
"""

from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel, Field

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result
from tools.ci_monitor.code_error_parser import ErrorPattern
from tools.ci_monitor.code_fix_generator import GeneratedFix

# ============================================================================
# TYPE DEFINITIONS (Pydantic models for strict typing)
# ============================================================================


class FixLearning(BaseModel):
    """
    Learned fix pattern stored in VectorStore.

    Attributes:
        category: Error category (missing_dependency, lint_error, etc.)
        strategy_type: Fix strategy type (pip_install, ruff_fix, etc.)
        command: Shell command to execute
        confidence: Confidence score 0.0-1.0
        timestamp: When pattern was learned (ISO format)
        evidence_count: Number of successful applications (optional)
    """

    category: str = Field(..., min_length=1)
    strategy_type: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    evidence_count: int = Field(default=1, ge=1)


class LearningQuery(BaseModel):
    """
    Query parameters for retrieving learned patterns.

    Attributes:
        error_category: Error category to search for
        min_confidence: Minimum confidence threshold (default: 0.6 per Article IV)
        include_session: Whether to scope to current session only
    """

    error_category: str = Field(..., min_length=1)
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    include_session: bool = Field(default=False)


class StoreError(BaseModel):
    """
    Error type for pattern storage failures.

    Attributes:
        reason: Error reason description
        context: Optional context about failure
        is_recoverable: Whether error is recoverable
    """

    reason: str = Field(..., min_length=1)
    context: str | None = Field(default=None)
    is_recoverable: bool = Field(default=True)


class QueryError(BaseModel):
    """
    Error type for pattern query failures.

    Attributes:
        reason: Error reason description
        context: Optional context about failure
        is_recoverable: Whether error is recoverable
    """

    reason: str = Field(..., min_length=1)
    context: str | None = Field(default=None)
    is_recoverable: bool = Field(default=True)


class LearningStatistics(BaseModel):
    """
    Statistics about stored learning patterns.

    Attributes:
        total_patterns: Total number of patterns
        categories: Count by category
        avg_confidence: Average confidence score
        high_confidence_count: Number of high confidence patterns (≥0.8)
    """

    total_patterns: int = Field(default=0, ge=0)
    categories: dict[str, int] = Field(default_factory=dict)
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    high_confidence_count: int = Field(default=0, ge=0)


class MemoryContent(TypedDict, total=False):
    """
    Type definition for VectorStore memory content.

    This ensures type safety without Dict[str, Any] violations.
    """

    category: str
    strategy_type: str
    command: str
    confidence: float
    timestamp: str
    evidence_count: int


# ============================================================================
# PUBLIC API (Article IV: VectorStore Integration)
# ============================================================================


def _build_fix_learning(fix: GeneratedFix) -> FixLearning:
    """Build FixLearning model from GeneratedFix (<50 lines)."""
    return FixLearning(
        category=fix.error_category,
        strategy_type=fix.fix_strategy.strategy_type,
        command=fix.fix_strategy.command,
        confidence=fix.fix_strategy.confidence,
        timestamp=datetime.now().isoformat(),
        evidence_count=1,
    )


def store_successful_fix(
    context: AgentContext, error_pattern: ErrorPattern, fix: GeneratedFix, success: bool = True
) -> Result[None, StoreError]:
    """
    Store successful fix pattern to VectorStore (Article IV).

    This function implements the "after_action" phase of Article IV:
    stores successful patterns for future agents to query and reuse.

    Args:
        context: AgentContext for VectorStore access
        error_pattern: Original error pattern that triggered the fix
        fix: GeneratedFix that was successfully applied
        success: Whether fix was successful (only True stored)

    Returns:
        Result[None, StoreError] on success/failure

    Constitutional Compliance:
        - Article I: Complete context (stores all relevant metadata)
        - Article IV: Mandatory VectorStore integration (after_action)
        - Law #5: Result pattern for error handling
        - Law #8: Function <50 lines

    Example:
        >>> context = create_agent_context()
        >>> result = store_successful_fix(context, error, fix, success=True)
        >>> if result.is_ok():
        ...     print("Pattern stored for future learning")
    """
    # Only store successful fixes (avoid learning bad patterns)
    if not success:
        return Ok(None)

    try:
        learning = _build_fix_learning(fix)
        context.store_memory(
            key=f"fix_{fix.error_category}_{datetime.now().isoformat()}",
            content=learning.model_dump(),
            tags=["fix", "pattern", fix.error_category, "success"],
        )
        return Ok(None)
    except Exception as e:
        return Err(
            StoreError(
                reason=f"VectorStore storage failed: {str(e)}",
                context=f"category={fix.error_category}",
                is_recoverable=True,
            )
        )


def _parse_learning_from_memory(
    content: MemoryContent, min_confidence: float
) -> FixLearning | None:
    """Parse FixLearning from memory content (<50 lines)."""
    # Validate confidence threshold
    confidence = content.get("confidence", 0.0)
    if not isinstance(confidence, (int, float)) or confidence < min_confidence:
        return None

    # Validate required fields
    required = ["category", "strategy_type", "command", "confidence"]
    if not all(key in content for key in required):
        return None

    try:
        return FixLearning(
            category=content["category"],
            strategy_type=content["strategy_type"],
            command=content["command"],
            confidence=confidence,
            timestamp=content.get("timestamp", datetime.now().isoformat()),
            evidence_count=content.get("evidence_count", 1),
        )
    except Exception:
        return None


def _extract_patterns(memories: list[MemoryContent], min_confidence: float) -> list[FixLearning]:
    """Extract and validate patterns from memories (<50 lines)."""
    patterns: list[FixLearning] = []
    for memory in memories:
        learning = _parse_learning_from_memory(memory, min_confidence)
        if learning:
            patterns.append(learning)

    # Sort by confidence (highest first)
    patterns.sort(key=lambda p: p.confidence, reverse=True)
    return patterns


def query_fix_patterns(
    context: AgentContext, error_pattern: ErrorPattern, min_confidence: float = 0.6
) -> Result[list[FixLearning], QueryError]:
    """
    Query VectorStore for learned fix patterns (Article IV).

    This function implements the "before_action" phase of Article IV:
    queries historical learnings before generating fixes.

    Args:
        context: AgentContext for VectorStore access
        error_pattern: Error pattern to find fixes for
        min_confidence: Minimum confidence threshold (default: 0.6 per Article IV)

    Returns:
        Result with list of FixLearning patterns or QueryError

    Constitutional Compliance:
        - Article I: Complete context (retrieves all relevant patterns)
        - Article IV: Mandatory VectorStore integration (before_action)
        - Law #5: Result pattern for error handling
        - Law #8: Function <50 lines

    Example:
        >>> context = create_agent_context()
        >>> result = query_fix_patterns(context, error)
        >>> if result.is_ok():
        ...     patterns = result.unwrap()
        ...     if patterns:
        ...         best_fix = patterns[0]  # Highest confidence
    """
    try:
        memories = context.search_memories(
            tags=["fix", "pattern", error_pattern.category, "success"],
            include_session=False,
        )
        patterns = _extract_patterns(memories, min_confidence)
        return Ok(patterns)
    except Exception as e:
        return Err(
            QueryError(
                reason=f"VectorStore query failed: {str(e)}",
                context=f"category={error_pattern.category}",
                is_recoverable=True,
            )
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def _calculate_statistics(patterns: list[MemoryContent]) -> LearningStatistics:
    """Calculate statistics from patterns (<50 lines)."""
    if not patterns:
        return LearningStatistics()

    categories: dict[str, int] = {}
    confidences: list[float] = []

    for pattern in patterns:
        category = pattern.get("category", "unknown")
        categories[category] = categories.get(category, 0) + 1

        confidence = pattern.get("confidence", 0.0)
        if isinstance(confidence, (int, float)):
            confidences.append(confidence)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    high_confidence_count = sum(1 for c in confidences if c >= 0.8)

    return LearningStatistics(
        total_patterns=len(patterns),
        categories=categories,
        avg_confidence=avg_confidence,
        high_confidence_count=high_confidence_count,
    )


def get_learning_statistics(context: AgentContext) -> LearningStatistics:
    """
    Get statistics about stored learning patterns (<50 lines).

    Args:
        context: AgentContext for VectorStore access

    Returns:
        LearningStatistics with pattern statistics

    Example:
        >>> stats = get_learning_statistics(context)
        >>> print(f"Learned {stats.total_patterns} patterns")
    """
    try:
        memories = context.search_memories(
            tags=["fix", "pattern", "success"],
            include_session=False,
        )
        patterns: list[MemoryContent] = [
            m.get("content", {}) for m in memories if isinstance(m.get("content"), dict)
        ]
        return _calculate_statistics(patterns)
    except Exception:
        return _calculate_statistics([])
