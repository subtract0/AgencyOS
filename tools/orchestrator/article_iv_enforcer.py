"""
Article IV Enforcement Tool for /primeA

Ensures VectorStore learning actually happens (not just claimed in documentation).
Provides mandatory validation gate that blocks execution report generation
if patterns haven't been stored.

Constitutional Compliance:
- Article IV: MANDATORY VectorStore integration (not optional)
- Article III: Automated enforcement (no manual bypass)
- Article II: 100% verification (validate storage happened)

Author: Claude (fixing systemic gap in /primeA protocol)
Date: 2025-11-08
"""

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared.agent_context import AgentContext, create_agent_context
from shared.type_definitions.result import Err, Ok, Result


class ArticleIVViolation(Exception):
    """Raised when Article IV VectorStore requirement is violated."""

    def __init__(
        self,
        reason: str,
        mission: str,
        suggestions: list[str],
    ):
        self.reason = reason
        self.mission = mission
        self.suggestions = suggestions
        super().__init__(f"Article IV violation for mission '{mission}': {reason}")


class ArticleIVEnforcer:
    """
    Enforces Article IV VectorStore learning requirement.

    Validates that patterns are actually stored to VectorStore,
    not just claimed in execution reports.
    """

    def __init__(self, mission_name: str, session_id: str | None = None):
        """
        Initialize enforcer for a specific mission.

        Args:
            mission_name: Name of the mission being executed
            session_id: Optional session ID (auto-generated if not provided)
        """
        self.mission_name = mission_name
        self.session_id = session_id or f"primea_{int(time.time())}"
        self.context = create_agent_context(session_id=self.session_id)
        self.patterns_stored: list[dict[str, Any]] = []
        self.start_time = time.time()

    def store_pattern(
        self,
        pattern_key: str,
        pattern_content: dict[str, Any],
        tags: list[str],
        confidence: float = 1.0,
    ) -> Result[None, str]:
        """
        Store a pattern to VectorStore with validation.

        Args:
            pattern_key: Unique key for pattern
            pattern_content: Pattern data (must include 'type' and 'description')
            tags: Searchable tags (must include 'pattern')
            confidence: Confidence score (0.0-1.0, default 1.0)

        Returns:
            Result[None, str] - Ok(None) on success, Err(message) on failure
        """
        # Validate pattern content
        if "type" not in pattern_content:
            return Err("Pattern content must include 'type' field")
        if "description" not in pattern_content:
            return Err("Pattern content must include 'description' field")

        # Validate tags
        if "pattern" not in tags:
            return Err("Tags must include 'pattern'")

        # Add metadata
        enriched_content = {
            **pattern_content,
            "mission": self.mission_name,
            "confidence": confidence,
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": self.session_id,
        }

        # Store to VectorStore
        self.context.store_memory(
            key=pattern_key,
            content=enriched_content,
            tags=tags,
        )

        # Track internally
        self.patterns_stored.append(
            {
                "key": pattern_key,
                "content": enriched_content,
                "tags": tags,
                "stored_at": time.time(),
            }
        )

        return Ok(None)

    def validate_article_iv_compliance(
        self, min_patterns: int = 1
    ) -> Result[dict[str, Any], ArticleIVViolation]:
        """
        Validate that Article IV VectorStore requirement was met.

        This is a BLOCKING gate - execution cannot proceed without compliance.

        Args:
            min_patterns: Minimum number of patterns required (default 1)

        Returns:
            Result containing validation report or ArticleIVViolation

        Raises:
            ArticleIVViolation if validation fails
        """
        # Check 1: At least min_patterns were stored
        if len(self.patterns_stored) < min_patterns:
            raise ArticleIVViolation(
                reason=f"Insufficient patterns stored ({len(self.patterns_stored)}/{min_patterns})",
                mission=self.mission_name,
                suggestions=[
                    f"Store at least {min_patterns} pattern(s) using enforcer.store_pattern()",
                    "Patterns should capture reusable strategies from execution",
                    "Article IV is MANDATORY - no bypass allowed (Article III)",
                ],
            )

        # Check 2: Verify patterns are actually retrievable from VectorStore
        verification_failures = []
        for pattern in self.patterns_stored:
            # Try to retrieve the pattern we just stored
            results = self.context.search_memories(
                tags=pattern["tags"], include_session=False
            )

            # Check if our pattern is in the results
            found = False
            for result in results:
                if result.get("key") == pattern["key"]:
                    found = True
                    break

            if not found:
                verification_failures.append(pattern["key"])

        if verification_failures:
            raise ArticleIVViolation(
                reason=f"Pattern storage verification failed for {len(verification_failures)} pattern(s)",
                mission=self.mission_name,
                suggestions=[
                    f"Failed to retrieve: {', '.join(verification_failures)}",
                    "VectorStore may not be operational - check configuration",
                    "Ensure USE_ENHANCED_MEMORY=true (constitutional requirement)",
                ],
            )

        # Success - generate validation report
        elapsed_time = time.time() - self.start_time
        validation_report = {
            "article_iv_compliant": True,
            "patterns_stored": len(self.patterns_stored),
            "patterns_verified": len(self.patterns_stored),
            "mission": self.mission_name,
            "session_id": self.session_id,
            "validation_time": elapsed_time,
            "pattern_keys": [p["key"] for p in self.patterns_stored],
            "pattern_types": [p["content"].get("type") for p in self.patterns_stored],
            "average_confidence": sum(
                p["content"].get("confidence", 0.0) for p in self.patterns_stored
            )
            / len(self.patterns_stored),
        }

        return Ok(validation_report)

    def get_stored_patterns_summary(self) -> str:
        """
        Get human-readable summary of stored patterns.

        Returns:
            Formatted string summary
        """
        if not self.patterns_stored:
            return "⚠️ No patterns stored yet (Article IV violation)"

        summary_lines = [
            "✅ Article IV Compliance Summary",
            f"   Mission: {self.mission_name}",
            f"   Patterns Stored: {len(self.patterns_stored)}",
            "",
            "Stored Patterns:",
        ]

        for i, pattern in enumerate(self.patterns_stored, 1):
            content = pattern["content"]
            summary_lines.append(
                f"{i}. {content.get('type', 'unknown')} - {content.get('description', 'no description')[:60]}"
            )
            summary_lines.append(
                f"   Key: {pattern['key']}, Confidence: {content.get('confidence', 0.0):.2f}"
            )

        return "\n".join(summary_lines)


def create_article_iv_enforcer(
    mission_name: str, session_id: str | None = None
) -> ArticleIVEnforcer:
    """
    Create Article IV enforcer for a mission.

    Args:
        mission_name: Name of the mission
        session_id: Optional session ID

    Returns:
        ArticleIVEnforcer instance
    """
    return ArticleIVEnforcer(mission_name=mission_name, session_id=session_id)


# Example usage for /primeA integration:
#
# STEP 6: Reflection & Evolution (MANDATORY Article IV enforcement)
#
# enforcer = create_article_iv_enforcer(mission_name=graph.mission)
#
# # Store patterns discovered during execution
# enforcer.store_pattern(
#     pattern_key=f"pattern_completion_validator_{int(time.time())}",
#     pattern_content={
#         "type": "quality_gate",
#         "description": "Completion validator blocks premature stopping",
#         "code_example": "validator.validate() before STEP 7",
#         "effectiveness": "100% (prevents 90% conclusions)"
#     },
#     tags=["pattern", "quality", "completion", "blocking_gate"],
#     confidence=1.0
# )
#
# # STEP 6.5: Validate Article IV Compliance (BLOCKING GATE)
#
# try:
#     validation_result = enforcer.validate_article_iv_compliance(min_patterns=1)
#
#     if validation_result.is_ok():
#         report = validation_result.unwrap()
#         print(enforcer.get_stored_patterns_summary())
#         print("\n✅ Article IV Validated - Proceeding to STEP 7")
#     else:
#         # This won't happen - exceptions are raised instead
#         pass
#
# except ArticleIVViolation as e:
#     print(f"\n❌ ARTICLE IV VIOLATION: {e.reason}")
#     print(f"   Mission: {e.mission}")
#     print("\n   Suggestions:")
#     for suggestion in e.suggestions:
#         print(f"   - {suggestion}")
#     print("\n⚠️ BLOCKING: Cannot proceed to STEP 7 without Article IV compliance")
#     print("⚠️ Store at least 1 pattern using enforcer.store_pattern()")
#     raise
