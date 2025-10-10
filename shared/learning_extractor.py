"""Learning pattern extraction from agent sessions.

Per Leap 3 Milestone 4.2: Extract reusable patterns from completed sessions
and store them in VectorStore for future agent learning (Article IV).
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ExtractedPattern:
    """A learned pattern extracted from session data."""

    pattern_type: str  # "code_pattern", "architecture", "testing", "error_handling"
    description: str
    context: str
    example: str
    success_rate: float  # 0.0-1.0
    evidence_count: int
    tags: list[str]
    confidence: float  # 0.0-1.0


class LearningExtractor:
    """Extract reusable patterns from agent session data.

    Analyzes completed sessions to identify:
    - Successful code patterns (Result<T,E>, Pydantic models)
    - Architectural decisions (ADRs, system design)
    - Testing strategies (AAA pattern, TDD)
    - Error handling approaches
    - Performance optimizations

    Per Article IV: MANDATORY VectorStore integration for continuous learning.
    """

    def __init__(self, vector_store: Any):
        """Initialize learning extractor.

        Args:
            vector_store: VectorStore for pattern storage (Article IV required)
        """
        if vector_store is None:
            raise ValueError("Article IV violation: VectorStore required for learning")

        self.vector_store = vector_store

    def extract_from_session(
        self,
        session_id: str,
        session_data: dict[str, Any],
        min_confidence: float = 0.6
    ) -> list[ExtractedPattern]:
        """Extract patterns from completed session.

        Args:
            session_id: Session identifier
            session_data: Session metadata and memories
            min_confidence: Minimum confidence threshold (default 0.6)

        Returns:
            List of extracted patterns meeting confidence threshold
        """
        patterns: list[ExtractedPattern] = []

        # Extract code patterns
        code_patterns = self._extract_code_patterns(session_data)
        patterns.extend([p for p in code_patterns if p.confidence >= min_confidence])

        # Extract architectural patterns
        arch_patterns = self._extract_architectural_patterns(session_data)
        patterns.extend([p for p in arch_patterns if p.confidence >= min_confidence])

        # Extract testing patterns
        test_patterns = self._extract_testing_patterns(session_data)
        patterns.extend([p for p in test_patterns if p.confidence >= min_confidence])

        # Extract error handling patterns
        error_patterns = self._extract_error_handling_patterns(session_data)
        patterns.extend([p for p in error_patterns if p.confidence >= min_confidence])

        return patterns

    def _extract_code_patterns(self, session_data: dict[str, Any]) -> list[ExtractedPattern]:
        """Extract code quality patterns."""
        patterns = []

        # Pattern: Result<T, E> usage
        result_pattern_count = self._count_pattern(
            session_data,
            r"Result\[.*,.*\]|from shared\.type_definitions\.result import"
        )

        if result_pattern_count > 0:
            patterns.append(ExtractedPattern(
                pattern_type="code_pattern",
                description="Result<T,E> pattern for error handling",
                context="Functional error handling without exceptions",
                example="def process() -> Result[Data, Error]: ...",
                success_rate=0.95,
                evidence_count=result_pattern_count,
                tags=["error_handling", "result_pattern", "functional"],
                confidence=min(0.9, result_pattern_count * 0.3)
            ))

        # Pattern: Pydantic models
        pydantic_count = self._count_pattern(
            session_data,
            r"from pydantic import BaseModel|class \w+\(BaseModel\)"
        )

        if pydantic_count > 0:
            patterns.append(ExtractedPattern(
                pattern_type="code_pattern",
                description="Pydantic models for strict typing",
                context="Type-safe data models with validation",
                example="class User(BaseModel): name: str",
                success_rate=0.98,
                evidence_count=pydantic_count,
                tags=["typing", "pydantic", "validation"],
                confidence=min(0.9, pydantic_count * 0.3)
            ))

        return patterns

    def _extract_architectural_patterns(self, session_data: dict[str, Any]) -> list[ExtractedPattern]:
        """Extract architectural decision patterns."""
        patterns = []

        # Pattern: ADR creation
        adr_count = self._count_pattern(
            session_data,
            r"ADR-\d+|docs/adr/|Architectural Decision Record"
        )

        if adr_count > 0:
            patterns.append(ExtractedPattern(
                pattern_type="architecture",
                description="ADR-driven architectural decisions",
                context="Document significant architecture choices",
                example="ADR-024: Adaptive Model Router for cost optimization",
                success_rate=1.0,
                evidence_count=adr_count,
                tags=["adr", "architecture", "documentation"],
                confidence=min(0.95, adr_count * 0.5)
            ))

        return patterns

    def _extract_testing_patterns(self, session_data: dict[str, Any]) -> list[ExtractedPattern]:
        """Extract testing strategy patterns."""
        patterns = []

        # Pattern: AAA pattern (Arrange-Act-Assert)
        aaa_count = self._count_pattern(
            session_data,
            r"# Arrange|# Act|# Assert"
        )

        if aaa_count >= 3:  # At least one full AAA test
            patterns.append(ExtractedPattern(
                pattern_type="testing",
                description="AAA (Arrange-Act-Assert) test pattern",
                context="Clear test structure for readability",
                example="# Arrange\nuser = User()\n# Act\nresult = user.login()\n# Assert\nassert result.is_ok()",
                success_rate=0.92,
                evidence_count=aaa_count // 3,
                tags=["testing", "aaa_pattern", "structure"],
                confidence=min(0.85, (aaa_count // 3) * 0.4)
            ))

        # Pattern: TDD (tests written first)
        tdd_indicators = self._count_pattern(
            session_data,
            r"test_.*\.py.*created before|TDD|test-driven"
        )

        if tdd_indicators > 0:
            patterns.append(ExtractedPattern(
                pattern_type="testing",
                description="TDD (Test-Driven Development)",
                context="Write tests before implementation",
                example="1. Write failing test\n2. Implement minimum code\n3. Refactor",
                success_rate=0.88,
                evidence_count=tdd_indicators,
                tags=["testing", "tdd", "methodology"],
                confidence=min(0.8, tdd_indicators * 0.4)
            ))

        return patterns

    def _extract_error_handling_patterns(self, session_data: dict[str, Any]) -> list[ExtractedPattern]:
        """Extract error handling patterns."""
        patterns = []

        # Pattern: Graceful degradation
        degradation_count = self._count_pattern(
            session_data,
            r"fallback|graceful.*degrad|error.*recovery"
        )

        if degradation_count > 0:
            patterns.append(ExtractedPattern(
                pattern_type="error_handling",
                description="Graceful degradation with fallbacks",
                context="Provide fallback behavior when primary fails",
                example="if primary.is_err():\n    return fallback_strategy()",
                success_rate=0.85,
                evidence_count=degradation_count,
                tags=["error_handling", "resilience", "fallback"],
                confidence=min(0.8, degradation_count * 0.3)
            ))

        return patterns

    def _count_pattern(self, session_data: dict[str, Any], pattern: str) -> int:
        """Count occurrences of regex pattern in session data."""
        count = 0

        # Search in session memories
        memories = session_data.get("memory_snapshots", [])
        for memory in memories:
            content_str = str(memory.get("content", ""))
            matches = re.findall(pattern, content_str, re.IGNORECASE)
            count += len(matches)

        # Search in metadata
        metadata_str = str(session_data.get("metadata", {}))
        matches = re.findall(pattern, metadata_str, re.IGNORECASE)
        count += len(matches)

        return count

    def store_patterns(
        self,
        patterns: list[ExtractedPattern],
        session_id: str
    ) -> int:
        """Store extracted patterns to VectorStore (Article IV).

        Args:
            patterns: List of patterns to store
            session_id: Source session identifier

        Returns:
            Number of patterns stored
        """
        stored_count = 0

        for pattern in patterns:
            key = f"learned_pattern_{pattern.pattern_type}_{session_id}_{stored_count}"

            content = {
                "pattern_type": pattern.pattern_type,
                "description": pattern.description,
                "context": pattern.context,
                "example": pattern.example,
                "success_rate": pattern.success_rate,
                "evidence_count": pattern.evidence_count,
                "confidence": pattern.confidence,
                "source_session": session_id,
                "extracted_at": datetime.now().isoformat()
            }

            try:
                self.vector_store.add_memory(
                    key,
                    content,
                    tags=pattern.tags + ["learned_pattern", f"session:{session_id}"],
                    namespace="learning_patterns"
                )
                stored_count += 1

            except Exception as e:
                print(f"Warning: Failed to store pattern {key}: {e}")

        return stored_count

    def query_similar_patterns(
        self,
        pattern_type: str,
        query: str,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """Query VectorStore for similar learned patterns.

        Args:
            pattern_type: Type of pattern to search for
            query: Search query
            limit: Maximum results

        Returns:
            List of matching patterns
        """
        try:
            results = self.vector_store.search(
                query=f"{pattern_type} {query}",
                namespace="learning_patterns",
                limit=limit
            )

            # Filter by pattern type
            filtered = [
                r for r in results
                if r.get("content", {}).get("pattern_type") == pattern_type
            ]

            return filtered

        except Exception:
            return []

    def generate_learning_report(
        self,
        session_id: str,
        patterns: list[ExtractedPattern]
    ) -> dict[str, Any]:
        """Generate learning report for session.

        Args:
            session_id: Session identifier
            patterns: Extracted patterns

        Returns:
            Learning report dict
        """
        # Group by pattern type
        by_type: dict[str, list[ExtractedPattern]] = {}
        for pattern in patterns:
            if pattern.pattern_type not in by_type:
                by_type[pattern.pattern_type] = []
            by_type[pattern.pattern_type].append(pattern)

        # Calculate aggregate metrics
        total_confidence = sum(p.confidence for p in patterns)
        avg_confidence = total_confidence / len(patterns) if patterns else 0.0

        total_evidence = sum(p.evidence_count for p in patterns)

        return {
            "session_id": session_id,
            "patterns_extracted": len(patterns),
            "pattern_types": list(by_type.keys()),
            "patterns_by_type": {
                ptype: len(plist) for ptype, plist in by_type.items()
            },
            "average_confidence": avg_confidence,
            "total_evidence": total_evidence,
            "top_patterns": sorted(
                patterns,
                key=lambda p: p.confidence,
                reverse=True
            )[:5],
            "timestamp": datetime.now().isoformat()
        }


def extract_and_store_session_learnings(
    session_id: str,
    session_data: dict[str, Any],
    vector_store: Any,
    min_confidence: float = 0.6
) -> dict[str, Any]:
    """Convenience function to extract and store learnings from session.

    Args:
        session_id: Session identifier
        session_data: Session metadata and memories
        vector_store: VectorStore instance
        min_confidence: Minimum confidence threshold

    Returns:
        Learning report
    """
    extractor = LearningExtractor(vector_store)

    # Extract patterns
    patterns = extractor.extract_from_session(
        session_id,
        session_data,
        min_confidence=min_confidence
    )

    # Store to VectorStore
    stored_count = extractor.store_patterns(patterns, session_id)

    # Generate report
    report = extractor.generate_learning_report(session_id, patterns)
    report["patterns_stored"] = stored_count

    return report
