"""
Migration utilities for converting legacy pattern formats to CodingPattern.

Provides conversion functions to migrate from:
- core.patterns.Pattern (legacy UnifiedPatternStore)
- shared.models.patterns.HealingPattern (self-healing system)

to the unified CodingPattern format.
"""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from shared.type_definitions.json import JSONValue
import json
import logging

from .coding_pattern import (
    CodingPattern,
    ProblemContext,
    SolutionApproach,
    EffectivenessMetric,
    PatternMetadata
)

logger = logging.getLogger(__name__)


def pattern_to_coding_pattern(legacy_pattern: Any) -> CodingPattern:
    """
    Convert legacy Pattern from core.patterns to CodingPattern.

    Args:
        legacy_pattern: Pattern instance from core.patterns

    Returns:
        CodingPattern: Converted pattern in new format
    """
    try:
        # Extract context information
        context_data = legacy_pattern.context if hasattr(legacy_pattern, 'context') else {}

        # Build ProblemContext
        context = ProblemContext(
            description=context_data.get("error_type", "Legacy pattern migration"),
            domain=legacy_pattern.pattern_type if hasattr(legacy_pattern, 'pattern_type') else "general",
            constraints=[],
            symptoms=[str(context_data.get("original", ""))[:200]] if "original" in context_data else [],
            scale=None,
            urgency="medium"
        )

        # Build SolutionApproach
        solution = SolutionApproach(
            approach=context_data.get("transformation", "legacy_migration"),
            implementation=legacy_pattern.solution if hasattr(legacy_pattern, 'solution') else "",
            tools=[],
            reasoning="Migrated from legacy Pattern format",
            code_examples=[legacy_pattern.solution[:500]] if hasattr(legacy_pattern, 'solution') else [],
            dependencies=[],
            alternatives=[]
        )

        # Build EffectivenessMetric
        outcome = EffectivenessMetric(
            success_rate=legacy_pattern.success_rate if hasattr(legacy_pattern, 'success_rate') else 0.5,
            performance_impact=None,
            maintainability_impact=None,
            user_impact=None,
            technical_debt=None,
            adoption_rate=legacy_pattern.usage_count if hasattr(legacy_pattern, 'usage_count') else 0,
            longevity=None,
            confidence=0.7  # Default confidence for migrated patterns
        )

        # Build PatternMetadata
        metadata = PatternMetadata(
            pattern_id=legacy_pattern.id if hasattr(legacy_pattern, 'id') else PatternMetadata.generate_id(context, solution),
            discovered_timestamp=legacy_pattern.created_at if hasattr(legacy_pattern, 'created_at') else datetime.now().isoformat(),
            source="legacy:core.patterns",
            discoverer="migration_utility",
            last_applied=legacy_pattern.last_used if hasattr(legacy_pattern, 'last_used') else None,
            application_count=legacy_pattern.usage_count if hasattr(legacy_pattern, 'usage_count') else 0,
            validation_status="validated" if hasattr(legacy_pattern, 'success_rate') and legacy_pattern.success_rate > 0.7 else "unvalidated",
            tags=legacy_pattern.tags if hasattr(legacy_pattern, 'tags') else [],
            related_patterns=[]
        )

        logger.info(f"Migrated legacy Pattern {metadata.pattern_id} to CodingPattern")

        return CodingPattern(
            context=context,
            solution=solution,
            outcome=outcome,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Failed to migrate Pattern: {e}")
        raise


def healing_pattern_to_coding_pattern(healing_pattern: Any) -> CodingPattern:
    """
    Convert HealingPattern from shared.models.patterns to CodingPattern.

    Args:
        healing_pattern: HealingPattern instance

    Returns:
        CodingPattern: Converted pattern in new format
    """
    try:
        # Build ProblemContext from healing pattern
        context = ProblemContext(
            description=healing_pattern.description if hasattr(healing_pattern, 'description') else "Self-healing pattern",
            domain=healing_pattern.pattern_type.value if hasattr(healing_pattern, 'pattern_type') else "self_healing",
            constraints=[],
            symptoms=[healing_pattern.trigger] if hasattr(healing_pattern, 'trigger') and healing_pattern.trigger else [],
            scale=f"{healing_pattern.occurrences} occurrences" if hasattr(healing_pattern, 'occurrences') else None,
            urgency="high" if hasattr(healing_pattern, 'success_rate') and healing_pattern.success_rate > 0.9 else "medium"
        )

        # Build SolutionApproach
        solution = SolutionApproach(
            approach=healing_pattern.action if hasattr(healing_pattern, 'action') and healing_pattern.action else "Automated healing action",
            implementation=healing_pattern.sequence if hasattr(healing_pattern, 'sequence') and healing_pattern.sequence else "",
            tools=["self_healing_system"],
            reasoning=f"Pattern extracted from self-healing with {healing_pattern.confidence:.1%} confidence" if hasattr(healing_pattern, 'confidence') else "Self-healing pattern",
            code_examples=[],
            dependencies=[],
            alternatives=[]
        )

        # Build EffectivenessMetric
        outcome = EffectivenessMetric(
            success_rate=healing_pattern.success_rate if hasattr(healing_pattern, 'success_rate') else 0.0,
            performance_impact=None,
            maintainability_impact="Automated healing reduces manual intervention",
            user_impact=None,
            technical_debt=None,
            adoption_rate=healing_pattern.occurrences if hasattr(healing_pattern, 'occurrences') else 0,
            longevity=healing_pattern.time_period if hasattr(healing_pattern, 'time_period') else None,
            confidence=healing_pattern.overall_confidence if hasattr(healing_pattern, 'overall_confidence') else healing_pattern.confidence if hasattr(healing_pattern, 'confidence') else 0.5
        )

        # Build PatternMetadata
        metadata = PatternMetadata(
            pattern_id=healing_pattern.pattern_id if hasattr(healing_pattern, 'pattern_id') else PatternMetadata.generate_id(context, solution),
            discovered_timestamp=datetime.now().isoformat(),
            source="self_healing:pattern_extractor",
            discoverer="self_healing_pattern_extractor",
            last_applied=None,
            application_count=healing_pattern.occurrences if hasattr(healing_pattern, 'occurrences') else 0,
            validation_status=healing_pattern.validation_status.value if hasattr(healing_pattern, 'validation_status') else "unvalidated",
            tags=["self_healing", healing_pattern.pattern_type.value] if hasattr(healing_pattern, 'pattern_type') else ["self_healing"],
            related_patterns=[]
        )

        # Add evidence as tags if available
        if hasattr(healing_pattern, 'evidence') and healing_pattern.evidence:
            for i, evidence in enumerate(healing_pattern.evidence[:3]):  # Limit to first 3
                if isinstance(evidence, dict) and 'type' in evidence:
                    metadata.tags.append(f"evidence_{evidence['type']}")

        logger.info(f"Migrated HealingPattern {metadata.pattern_id} to CodingPattern")

        return CodingPattern(
            context=context,
            solution=solution,
            outcome=outcome,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Failed to migrate HealingPattern: {e}")
        raise


def dict_to_coding_pattern(data: Dict[str, JSONValue]) -> CodingPattern:
    """
    Convert a dictionary representation to CodingPattern.

    Handles both legacy formats and attempts smart conversion.

    Args:
        data: Dictionary with pattern data

    Returns:
        CodingPattern: Converted pattern
    """
    # Check if it's already in CodingPattern format
    if all(key in data for key in ['context', 'solution', 'outcome', 'metadata']):
        return CodingPattern.from_dict(data)

    # Try to detect format and convert
    if 'pattern_type' in data and 'trigger' in data:
        # Looks like HealingPattern format
        from shared.models.patterns import HealingPattern
        healing = HealingPattern(**data)
        return healing_pattern_to_coding_pattern(healing)

    if 'pattern_type' in data and 'context' in data and 'solution' in data:
        # Looks like legacy Pattern format
        from dataclasses import dataclass
        @dataclass
        class LegacyPattern:
            id: str
            pattern_type: str
            context: dict
            solution: str
            success_rate: float
            usage_count: int
            created_at: str
            last_used: str
            tags: List[str]

        legacy = LegacyPattern(
            id=data.get('id', ''),
            pattern_type=data.get('pattern_type', ''),
            context=data.get('context', {}),
            solution=data.get('solution', ''),
            success_rate=data.get('success_rate', 0.0),
            usage_count=data.get('usage_count', 0),
            created_at=data.get('created_at', ''),
            last_used=data.get('last_used', ''),
            tags=data.get('tags', [])
        )
        return pattern_to_coding_pattern(legacy)

    # Fallback: Create minimal CodingPattern
    logger.warning("Creating minimal CodingPattern from unrecognized format")
    context = ProblemContext(
        description=str(data.get('description', 'Unknown pattern')),
        domain=str(data.get('domain', 'general')),
        constraints=[],
        symptoms=[]
    )

    solution = SolutionApproach(
        approach=str(data.get('approach', 'Unknown approach')),
        implementation=str(data.get('implementation', '')),
        tools=[],
        reasoning="Migrated from unknown format"
    )

    outcome = EffectivenessMetric(
        success_rate=float(data.get('success_rate', 0.5)),
        confidence=0.3  # Low confidence for unknown format
    )

    metadata = PatternMetadata(
        pattern_id=str(data.get('id', PatternMetadata.generate_id(context, solution))),
        discovered_timestamp=datetime.now().isoformat(),
        source="migration:unknown",
        discoverer="migration_utility"
    )

    return CodingPattern(context, solution, outcome, metadata)


def migrate_pattern_store() -> None:
    """
    Migrate all patterns from UnifiedPatternStore to PatternStore.

    This function:
    1. Loads all patterns from UnifiedPatternStore
    2. Converts them to CodingPattern format
    3. Stores them in the new PatternStore
    """
    try:
        from core.patterns import get_pattern_store
        from .pattern_store import PatternStore

        legacy_store = get_pattern_store()
        new_store = PatternStore()

        migrated_count = 0
        failed_count = 0

        for pattern_id, pattern in legacy_store.patterns.items():
            try:
                coding_pattern = pattern_to_coding_pattern(pattern)
                new_store.store_pattern(coding_pattern)
                migrated_count += 1
                logger.info(f"Migrated pattern {pattern_id}")
            except Exception as e:
                logger.error(f"Failed to migrate pattern {pattern_id}: {e}")
                failed_count += 1

        logger.info(f"Migration complete: {migrated_count} patterns migrated, {failed_count} failed")

    except Exception as e:
        logger.error(f"Pattern store migration failed: {e}")
        raise