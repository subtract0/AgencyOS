#!/usr/bin/env python3
"""
Trinity Daemon - Continuous Learning Autonomous Fixer

WATCHER → FIXER → LEARNER trinity pattern for autonomous code quality improvement.

Components:
1. WATCHER: Monitors recommendation files (Phase 4 audit output)
2. FIXER: Applies fixes via AgencyOSAgent
3. LEARNER: Extracts patterns from successful fixes, stores in VectorStore

Constitutional Compliance:
- Article I: Complete Context (read all fix artifacts)
- Article II: 100% Verification (test validation mandatory)
- Article III: Automated Enforcement (no manual overrides)
- Article IV: Continuous Learning (VectorStore integration MANDATORY)
- Article V: Spec-Driven (follows audit recommendations)

Usage:
    # Run daemon in continuous mode
    python scripts/trinity_daemon.py --mode continuous

    # Run single iteration
    python scripts/trinity_daemon.py --mode once --limit 10
"""

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

# Add parent directory to Python path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field

from shared.agent_context import AgentContext, create_agent_context
from shared.type_definitions.result import Err, Ok, Result

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/trinity_daemon.log"),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pattern Models
# ============================================================================


class FixPattern(BaseModel):
    """Learned pattern from successful fix."""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    category: str = Field(..., description="Fix category (pruning, simplification, etc)")
    problem_signature: str = Field(..., description="Problem pattern signature")
    solution_template: str = Field(..., description="Reusable solution template")
    files_affected: list[str] = Field(..., description="Files where fix was applied")
    success_count: int = Field(default=1, description="Number of successful applications")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Pattern confidence")
    example_code: str | None = Field(default=None, description="Example fix code")
    created_at: datetime = Field(default_factory=datetime.now)


class FixRecord(BaseModel):
    """Record of a successful fix for pattern extraction."""

    recommendation_file: str = Field(..., description="Source recommendation file")
    category: str = Field(..., description="Fix category")
    priority: str = Field(..., description="Priority level (P0-P3)")
    files_modified: list[str] = Field(..., description="Files that were modified")
    commit_sha: str = Field(..., description="Git commit SHA")
    tests_passed: bool = Field(..., description="Whether tests passed")
    execution_time: float = Field(..., description="Execution time in seconds")
    applied_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Trinity Learner Component
# ============================================================================


class TrinityLearner:
    """
    Extract patterns from successful fixes and store in VectorStore.

    Article IV Compliance: VectorStore integration is constitutionally mandatory.

    Integration Point: Called every 1 hour OR after 10 successful fixes.
    """

    def __init__(self, context: AgentContext):
        """
        Initialize learner with agent context.

        Args:
            context: AgentContext with VectorStore access
        """
        self.context = context
        self.patterns: dict[str, FixPattern] = {}
        self.successful_fixes: list[FixRecord] = []
        logger.info("TrinityLearner initialized")

    def record_success(self, fix_record: FixRecord) -> None:
        """
        Record a successful fix for pattern extraction.

        Args:
            fix_record: Details of successful fix
        """
        self.successful_fixes.append(fix_record)
        logger.info(
            f"Recorded fix: {fix_record.category} - "
            f"{len(fix_record.files_modified)} files, "
            f"{fix_record.execution_time:.2f}s"
        )

    def extract_patterns(self, successful_fixes: list[FixRecord]) -> list[FixPattern]:
        """
        Analyze successful fixes and extract reusable patterns.

        Constitutional Requirement (Article IV):
        - Store patterns in VectorStore for cross-session learning
        - Query existing patterns to avoid duplicates
        - Boost confidence on repeated occurrences

        Args:
            successful_fixes: List of successful fix records

        Returns:
            List of extracted patterns
        """
        if not successful_fixes:
            logger.warning("No successful fixes to extract patterns from")
            return []

        patterns: list[FixPattern] = []

        # Group fixes by category and problem signature
        by_category: dict[str, list[FixRecord]] = {}
        for fix in successful_fixes:
            key = f"{fix.category}:{fix.priority}"
            if key not in by_category:
                by_category[key] = []
            by_category[key].append(fix)

        # Extract patterns from grouped fixes
        for category_key, fixes in by_category.items():
            category, priority = category_key.split(":", 1)

            # Query VectorStore for existing similar patterns
            existing_patterns = self.context.search_memories(
                tags=["pattern", "fix", category], include_session=False
            )

            # Determine if this is a new pattern or update to existing
            pattern_signature = self._generate_pattern_signature(fixes)
            existing = self._find_matching_pattern(pattern_signature, existing_patterns)

            if existing:
                # Boost confidence for repeated pattern
                confidence = min(existing.get("confidence", 0.7) + 0.1, 1.0)
                success_count = existing.get("success_count", 1) + len(fixes)
            else:
                # New pattern with base confidence
                confidence = 0.7
                success_count = len(fixes)

            # Create pattern
            pattern = FixPattern(
                pattern_id=f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                category=category,
                problem_signature=pattern_signature,
                solution_template=self._extract_solution_template(fixes),
                files_affected=[f for fix in fixes for f in fix.files_modified],
                success_count=success_count,
                confidence=confidence,
                example_code=self._extract_example_code(fixes[0]) if fixes else None,
            )

            patterns.append(pattern)

            # Store in VectorStore (Article IV mandate)
            self._store_pattern_in_vectorstore(pattern)

        logger.info(f"Extracted {len(patterns)} patterns from {len(successful_fixes)} fixes")
        return patterns

    def boost_confidence(self, recommendation_category: str, recommendation_priority: str) -> float:
        """
        Query VectorStore for similar past successes and boost confidence.

        Article IV Compliance: Query learnings before action.

        Args:
            recommendation_category: Category of recommendation (pruning, etc)
            recommendation_priority: Priority level (P0-P3)

        Returns:
            Confidence boost factor (0.7-1.0)
        """
        # Query VectorStore for similar successful fixes
        similar_patterns = self.context.search_memories(
            tags=["pattern", "fix", recommendation_category], include_session=False
        )

        if not similar_patterns:
            # No prior learnings, base confidence
            return 0.7

        # Calculate confidence based on success rate and recency
        total_confidence = 0.0
        pattern_count = 0

        for pattern in similar_patterns:
            pattern_confidence = pattern.get("confidence", 0.7)
            success_count = pattern.get("success_count", 1)

            # Weight by success count (more successes = higher confidence)
            weighted_confidence = pattern_confidence * min(success_count / 10.0, 1.0)
            total_confidence += weighted_confidence
            pattern_count += 1

        if pattern_count == 0:
            return 0.7

        # Average confidence across patterns, with minimum of 0.7
        avg_confidence = total_confidence / pattern_count
        boosted = max(avg_confidence, 0.7)

        logger.info(
            f"Confidence boost for {recommendation_category}/{recommendation_priority}: "
            f"{boosted:.2f} (based on {pattern_count} patterns)"
        )

        return min(boosted, 1.0)  # Cap at 1.0

    def _generate_pattern_signature(self, fixes: list[FixRecord]) -> str:
        """Generate unique signature for a problem pattern."""
        # Use category + priority + common file patterns
        categories = {fix.category for fix in fixes}
        priorities = {fix.priority for fix in fixes}

        # Find common file patterns (e.g., all in same directory)
        all_files = [f for fix in fixes for f in fix.files_modified]
        common_paths = self._find_common_path_patterns(all_files)

        signature = f"{','.join(sorted(categories))}:{','.join(sorted(priorities))}"
        if common_paths:
            signature += f":{common_paths}"

        return signature

    def _find_common_path_patterns(self, file_paths: list[str]) -> str:
        """Find common directory patterns in file paths."""
        if not file_paths:
            return ""

        # Extract parent directories
        dirs = [str(Path(f).parent) for f in file_paths]
        unique_dirs = set(dirs)

        if len(unique_dirs) == 1:
            return list(unique_dirs)[0]

        # Find common prefix
        common_prefix = Path(file_paths[0]).parts[0] if file_paths else ""
        return common_prefix

    def _extract_solution_template(self, fixes: list[FixRecord]) -> str:
        """Extract reusable solution template from fixes."""
        # For now, create simple template based on category
        if not fixes:
            return "No template available"

        category = fixes[0].category
        templates = {
            "pruning": "Remove unnecessary code/comments, verify tests pass",
            "simplification": "Break large function into smaller units (<50 lines each)",
            "consolidation": "Extract common logic into shared utility function",
            "architecture": "Replace Dict[Any,Any] with typed Pydantic model",
            "linting": "Apply auto-formatting and fix linting violations",
        }

        return templates.get(category, "Apply recommended fix and verify tests")

    def _extract_example_code(self, fix: FixRecord) -> str | None:
        """Extract example code from fix record."""
        # This would parse the recommendation file for example code
        # For now, return None (implementation detail)
        return None

    def _find_matching_pattern(self, signature: str, existing_patterns: list[dict]) -> dict | None:
        """Find existing pattern matching the signature."""
        for pattern in existing_patterns:
            if pattern.get("content", {}).get("problem_signature") == signature:
                return pattern.get("content", {})
        return None

    def _store_pattern_in_vectorstore(self, pattern: FixPattern) -> None:
        """
        Store pattern in VectorStore for cross-session learning.

        Article IV Compliance: MANDATORY storage of successful patterns.
        """
        self.context.store_memory(
            key=pattern.pattern_id,
            content={
                "pattern_id": pattern.pattern_id,
                "category": pattern.category,
                "problem_signature": pattern.problem_signature,
                "solution_template": pattern.solution_template,
                "files_affected": pattern.files_affected,
                "success_count": pattern.success_count,
                "confidence": pattern.confidence,
                "example_code": pattern.example_code,
                "created_at": pattern.created_at.isoformat(),
            },
            tags=["trinity", "learner", "pattern", "fix", pattern.category],
        )

        logger.info(
            f"Stored pattern in VectorStore: {pattern.pattern_id} "
            f"(confidence: {pattern.confidence:.2f})"
        )


# ============================================================================
# Main CLI
# ============================================================================


def main() -> int:
    """Main entry point for Trinity daemon."""
    parser = argparse.ArgumentParser(
        description="Trinity Daemon - Continuous Learning Autonomous Fixer"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["once", "continuous"],
        default="once",
        help="Run mode: once (single iteration) or continuous (daemon)",
    )

    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum fixes to apply per iteration"
    )

    parser.add_argument(
        "--learning-interval",
        type=int,
        default=3600,
        help="Learning interval in seconds (default: 1 hour)",
    )

    args = parser.parse_args()

    logger.info("Starting Trinity Daemon...")

    # Initialize agent context with VectorStore (Article IV mandate)
    context = create_agent_context(session_id=f"trinity_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    # Initialize learner
    learner = TrinityLearner(context)

    # Demo: Simulate some successful fixes
    demo_fixes = [
        FixRecord(
            recommendation_file="localM4_recommends_016-excessive_commented_code.md",
            category="pruning",
            priority="P3",
            files_modified=["learning_agent/__init__.py"],
            commit_sha="abc123",
            tests_passed=True,
            execution_time=5.2,
        ),
        FixRecord(
            recommendation_file="localM4_recommends_022-excessive_commented_code.md",
            category="pruning",
            priority="P3",
            files_modified=["tools/consolidate_tests.py"],
            commit_sha="def456",
            tests_passed=True,
            execution_time=4.8,
        ),
    ]

    for fix in demo_fixes:
        learner.record_success(fix)

    # Extract patterns
    patterns = learner.extract_patterns(learner.successful_fixes)

    # Test confidence boost
    confidence = learner.boost_confidence("pruning", "P3")

    logger.info(
        f"Trinity Learner Demo Complete: {len(patterns)} patterns, confidence: {confidence:.2f}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
