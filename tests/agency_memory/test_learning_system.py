"""
Tests for Continuous Learning System (agency_memory/learning.py).

Constitutional Compliance:
- Article I: Complete test coverage (all pattern types tested)
- Article II: 100% test pass rate (TDD)
- Article IV: Validates continuous learning functionality

Test Coverage:
- LearningPattern creation and serialization
- LearningSystem pattern extraction (tool, error, interaction)
- Confidence scoring (evidence-based, consistency, recency)
- Auto-extraction triggers
- Pattern statistics generation
"""

import tempfile
from pathlib import Path

import pytest

from agency_memory.learning import LearningPattern, LearningSystem
from agency_memory.vector_store import VectorStore


@pytest.fixture
def isolated_vector_store():
    """Create isolated VectorStore with temporary storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use temporary directory to avoid state pollution
        vector_store = VectorStore(storage_path=tmpdir)
        yield vector_store


class TestLearningPattern:
    """Test LearningPattern class."""

    def test_learning_pattern_creation(self, isolated_vector_store):
        """Test creating a LearningPattern instance."""
        evidence = [
            {"key": "tool_1", "content": "success", "tags": ["tool", "Read"]},
            {"key": "tool_2", "content": "success", "tags": ["tool", "Read"]},
            {"key": "tool_3", "content": "success", "tags": ["tool", "Read"]},
        ]

        pattern = LearningPattern(
            pattern_type="tool",
            description="Successful Read tool usage pattern",
            evidence=evidence,
            confidence=0.85,
            tags=["tool", "Read", "success", "pattern"],
        )

        assert pattern.pattern_type == "tool"
        assert pattern.description == "Successful Read tool usage pattern"
        assert pattern.confidence == 0.85
        assert pattern.evidence_count == 3
        assert "tool" in pattern.tags
        assert "pattern" in pattern.tags

    def test_learning_pattern_to_dict(self, isolated_vector_store):
        """Test converting LearningPattern to dictionary."""
        evidence = [{"key": "test", "content": "data"}]

        pattern = LearningPattern(
            pattern_type="error",
            description="Error resolution pattern",
            evidence=evidence,
            confidence=0.7,
            tags=["error", "fixed"],
        )

        pattern_dict = pattern.to_dict()

        assert pattern_dict["pattern_type"] == "error"
        assert pattern_dict["description"] == "Error resolution pattern"
        assert pattern_dict["evidence_count"] == 1
        assert pattern_dict["confidence"] == 0.7
        assert "timestamp" in pattern_dict

    def test_learning_pattern_repr(self, isolated_vector_store):
        """Test LearningPattern string representation."""
        pattern = LearningPattern(
            pattern_type="interaction",
            description="Agent coordination",
            evidence=[{}, {}, {}],
            confidence=0.9,
            tags=["agent"],
        )

        repr_str = repr(pattern)
        assert "LearningPattern" in repr_str
        assert "interaction" in repr_str
        assert "0.90" in repr_str
        assert "evidence=3" in repr_str


class TestLearningSystemToolPatterns:
    """Test LearningSystem tool pattern extraction."""

    def test_extract_tool_patterns_success(self, isolated_vector_store):
        """Test successful tool pattern extraction."""
        vector_store = isolated_vector_store

        # Store tool usage memories (5 Read successes)
        for i in range(5):
            vector_store.store(
                key=f"tool_read_{i}",
                content={"tool": "Read", "status": "success"},
                tags=["tool", "Read", "success"],
                confidence=0.9,
            )

        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)
        result = learning.extract_patterns()

        assert result.is_ok()
        patterns = result.unwrap()

        # Should extract 1 Read tool pattern
        assert len(patterns) >= 1
        tool_patterns = [p for p in patterns if p.pattern_type == "tool"]
        assert len(tool_patterns) >= 1

        read_pattern = tool_patterns[0]
        assert "Read" in read_pattern.description
        assert read_pattern.confidence == 1.0  # 5 examples / 5 = 1.0
        assert read_pattern.evidence_count == 5

    def test_extract_tool_patterns_insufficient_evidence(self, isolated_vector_store):
        """Test tool pattern extraction with insufficient evidence."""
        vector_store = isolated_vector_store

        # Store only 2 tool memories (need 3 for pattern)
        for i in range(2):
            vector_store.store(
                key=f"tool_write_{i}",
                content={"tool": "Write", "status": "success"},
                tags=["tool", "Write", "success"],
                confidence=0.9,
            )

        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)
        result = learning.extract_patterns()

        assert result.is_ok()
        patterns = result.unwrap()

        # Should not extract tool patterns (insufficient evidence)
        tool_patterns = [p for p in patterns if p.pattern_type == "tool"]
        assert len(tool_patterns) == 0

    def test_extract_multiple_tool_patterns(self, isolated_vector_store):
        """Test extracting patterns for multiple tools."""
        vector_store = isolated_vector_store

        # Store Read successes (3)
        for i in range(3):
            vector_store.store(
                key=f"tool_read_{i}",
                content={"tool": "Read"},
                tags=["tool", "Read", "success"],
                confidence=0.9,
            )

        # Store Edit successes (4)
        for i in range(4):
            vector_store.store(
                key=f"tool_edit_{i}",
                content={"tool": "Edit"},
                tags=["tool", "Edit", "success"],
                confidence=0.9,
            )

        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)
        result = learning.extract_patterns()

        assert result.is_ok()
        patterns = result.unwrap()

        tool_patterns = [p for p in patterns if p.pattern_type == "tool"]
        assert len(tool_patterns) == 2

        # Check confidence scores
        for pattern in tool_patterns:
            if "Read" in pattern.description:
                assert pattern.confidence == 0.6  # 3 / 5
                assert pattern.evidence_count == 3
            elif "Edit" in pattern.description:
                assert pattern.confidence == 0.8  # 4 / 5
                assert pattern.evidence_count == 4


class TestLearningSystemErrorPatterns:
    """Test LearningSystem error pattern extraction."""

    def test_extract_error_patterns_success(self, isolated_vector_store):
        """Test successful error pattern extraction."""
        vector_store = isolated_vector_store

        # Store error resolution memories (3 NoneType errors)
        for i in range(3):
            vector_store.store(
                key=f"error_nonetype_{i}",
                content={"error_type": "NoneType", "resolution": "added null check"},
                tags=["error", "fixed", "NoneType"],
                confidence=0.9,
            )

        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)
        result = learning.extract_patterns()

        assert result.is_ok()
        patterns = result.unwrap()

        error_patterns = [p for p in patterns if p.pattern_type == "error"]
        assert len(error_patterns) >= 1

        # Check NoneType pattern
        nonetype_pattern = [p for p in error_patterns if "NoneType" in p.description][0]
        assert nonetype_pattern.confidence == 1.0  # 3 / 3
        assert nonetype_pattern.evidence_count == 3
        assert "error" in nonetype_pattern.tags
        assert "fixed" in nonetype_pattern.tags

    def test_extract_generic_error_pattern(self, isolated_vector_store):
        """Test generic error pattern extraction (5+ examples)."""
        vector_store = isolated_vector_store

        # Store 6 various error resolutions
        for i in range(6):
            vector_store.store(
                key=f"error_various_{i}",
                content={"error_type": f"error_type_{i}", "fixed": True},
                tags=["error", "fixed"],
                confidence=0.9,
            )

        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)
        result = learning.extract_patterns()

        assert result.is_ok()
        patterns = result.unwrap()

        error_patterns = [p for p in patterns if p.pattern_type == "error"]
        assert len(error_patterns) >= 1

        # Should include generic error pattern
        generic_patterns = [p for p in error_patterns if "Generic" in p.description]
        assert len(generic_patterns) >= 1

        generic_pattern = generic_patterns[0]
        assert generic_pattern.confidence == 0.6  # 6 / 10
        assert generic_pattern.evidence_count == 6  # Uses all available (max 10)


class TestLearningSystemInteractionPatterns:
    """Test LearningSystem interaction pattern extraction."""

    def test_extract_interaction_patterns_success(self, isolated_vector_store):
        """Test successful interaction pattern extraction."""
        vector_store = isolated_vector_store

        # Store agent interaction memories (3 Planner → Coder handoffs)
        for i in range(3):
            vector_store.store(
                key=f"handoff_{i}",
                content={
                    "source_agent": "Planner",
                    "target_agent": "Coder",
                    "status": "success",
                },
                tags=["agent", "handoff", "Planner", "Coder"],
                confidence=0.9,
            )

        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)
        result = learning.extract_patterns()

        assert result.is_ok()
        patterns = result.unwrap()

        interaction_patterns = [p for p in patterns if p.pattern_type == "interaction"]
        assert len(interaction_patterns) >= 1

        planner_coder_pattern = interaction_patterns[0]
        assert "Planner → Coder" in planner_coder_pattern.description
        assert planner_coder_pattern.confidence == 0.6  # 3 / 5
        assert planner_coder_pattern.evidence_count == 3

    def test_extract_generic_interaction_pattern(self, isolated_vector_store):
        """Test generic interaction pattern extraction (5+ handoffs)."""
        vector_store = isolated_vector_store

        # Store 6 various handoffs
        for i in range(6):
            vector_store.store(
                key=f"handoff_{i}",
                content={
                    "source_agent": f"Agent{i}",
                    "target_agent": f"Agent{i+1}",
                    "status": "success",
                },
                tags=["agent", "handoff"],
                confidence=0.9,
            )

        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)
        result = learning.extract_patterns()

        assert result.is_ok()
        patterns = result.unwrap()

        interaction_patterns = [p for p in patterns if p.pattern_type == "interaction"]

        # Should include generic interaction pattern
        generic_patterns = [p for p in interaction_patterns if "Generic" in p.description]
        assert len(generic_patterns) >= 1


class TestLearningSystemAutoExtraction:
    """Test LearningSystem auto-extraction triggers."""

    def test_should_trigger_extraction_threshold(self, isolated_vector_store):
        """Test auto-extraction triggers at threshold."""
        vector_store = isolated_vector_store
        learning = LearningSystem(
            vector_store=vector_store, auto_extraction_trigger=10  # Trigger every 10
        )

        # Initially should not trigger
        assert not learning.should_trigger_extraction()

        # Store 10 memories
        for i in range(10):
            vector_store.store(
                key=f"mem_{i}",
                content={"data": i},
                tags=["test"],
                confidence=0.9,
            )

        # Should trigger after 10 memories
        assert learning.should_trigger_extraction()

        # Should not trigger again until +10 more
        assert not learning.should_trigger_extraction()

    def test_enable_auto_extraction(self, isolated_vector_store):
        """Test enabling auto-extraction (logs initialization)."""
        vector_store = isolated_vector_store
        learning = LearningSystem(vector_store=vector_store)

        # Should not raise exception
        learning.enable_auto_extraction()


class TestLearningSystemConfidenceCalculation:
    """Test LearningSystem confidence calculation."""

    def test_calculate_confidence_base(self, isolated_vector_store):
        """Test base confidence calculation (evidence only)."""
        vector_store = isolated_vector_store
        learning = LearningSystem(vector_store=vector_store)

        # 3 occurrences = confidence 1.0
        confidence = learning.calculate_pattern_confidence(evidence_count=3)
        assert confidence == 1.0

        # 1 occurrence = confidence 0.33
        confidence = learning.calculate_pattern_confidence(evidence_count=1)
        assert abs(confidence - 0.333) < 0.01

        # 6 occurrences = confidence 1.0 (capped)
        confidence = learning.calculate_pattern_confidence(evidence_count=6)
        assert confidence == 1.0

    def test_calculate_confidence_with_consistency(self, isolated_vector_store):
        """Test confidence calculation with consistency weighting."""
        vector_store = isolated_vector_store
        learning = LearningSystem(vector_store=vector_store)

        # 3 occurrences, 100% consistency
        confidence = learning.calculate_pattern_confidence(
            evidence_count=3, consistency_score=1.0
        )
        assert confidence == 1.0

        # 3 occurrences, 50% consistency
        confidence = learning.calculate_pattern_confidence(
            evidence_count=3, consistency_score=0.5
        )
        assert confidence == 0.5

    def test_calculate_confidence_with_recency(self, isolated_vector_store):
        """Test confidence calculation with recency factor."""
        vector_store = isolated_vector_store
        learning = LearningSystem(vector_store=vector_store)

        # Recent pattern (0 days old)
        confidence = learning.calculate_pattern_confidence(
            evidence_count=3, recency_days=0
        )
        assert confidence == 1.0

        # 30 days old (mid-decay: recency_factor = 1.0 - 30/90 = 0.67)
        confidence = learning.calculate_pattern_confidence(
            evidence_count=3, recency_days=30
        )
        assert 0.5 < confidence < 1.0  # Should be ~0.67

        # 90 days old (max decay to 0.5)
        confidence = learning.calculate_pattern_confidence(
            evidence_count=3, recency_days=90
        )
        assert confidence == 0.5  # 3/3 * 1.0 * 0.5 = 0.5


class TestLearningSystemStatistics:
    """Test LearningSystem statistics generation."""

    def test_get_pattern_statistics_empty(self, isolated_vector_store):
        """Test statistics with no patterns."""
        vector_store = isolated_vector_store
        learning = LearningSystem(vector_store=vector_store)

        stats = learning.get_pattern_statistics()

        assert stats["total_patterns"] == 0
        assert stats["by_type"] == {}
        assert stats["avg_confidence"] == 0.0
        assert stats["high_confidence_count"] == 0

    def test_get_pattern_statistics_with_patterns(self, isolated_vector_store):
        """Test statistics with extracted patterns."""
        vector_store = isolated_vector_store

        # Store various patterns
        # Tool patterns (2)
        for i in range(2):
            vector_store.store(
                key=f"pattern_tool_{i}",
                content={"type": "tool"},
                tags=["pattern", "tool"],
                confidence=0.9,
            )

        # Error patterns (3)
        for i in range(3):
            vector_store.store(
                key=f"pattern_error_{i}",
                content={"type": "error"},
                tags=["pattern", "error"],
                confidence=0.95,
            )

        # Interaction patterns (1)
        vector_store.store(
            key="pattern_interaction_0",
            content={"type": "interaction"},
            tags=["pattern", "interaction"],
            confidence=0.7,
        )

        learning = LearningSystem(vector_store=vector_store)
        stats = learning.get_pattern_statistics()

        assert stats["total_patterns"] == 6
        assert stats["by_type"]["tool"] == 2
        assert stats["by_type"]["error"] == 3
        assert stats["by_type"]["interaction"] == 1
        assert stats["avg_confidence"] > 0.8  # Average of 0.9, 0.95, 0.7
        assert stats["high_confidence_count"] == 5  # 2 + 3 patterns ≥0.9


class TestLearningSystemIntegration:
    """Integration tests for LearningSystem."""

    def test_full_pattern_extraction_workflow(self, isolated_vector_store):
        """Test complete pattern extraction workflow (tool, error, interaction)."""
        vector_store = isolated_vector_store

        # Store diverse memories
        # 5 Read tool successes
        for i in range(5):
            vector_store.store(
                key=f"tool_read_{i}",
                content={"tool": "Read"},
                tags=["tool", "Read", "success"],
                confidence=0.9,
            )

        # 3 NoneType error resolutions
        for i in range(3):
            vector_store.store(
                key=f"error_nonetype_{i}",
                content={"error_type": "NoneType"},
                tags=["error", "fixed"],
                confidence=0.9,
            )

        # 4 Planner → Coder handoffs
        for i in range(4):
            vector_store.store(
                key=f"handoff_{i}",
                content={"source_agent": "Planner", "target_agent": "Coder"},
                tags=["agent", "handoff"],
                confidence=0.9,
            )

        # Extract patterns
        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)
        result = learning.extract_patterns()

        assert result.is_ok()
        patterns = result.unwrap()

        # Should extract at least 3 patterns (1 tool, 1 error, 1 interaction)
        assert len(patterns) >= 3

        tool_patterns = [p for p in patterns if p.pattern_type == "tool"]
        error_patterns = [p for p in patterns if p.pattern_type == "error"]
        interaction_patterns = [p for p in patterns if p.pattern_type == "interaction"]

        assert len(tool_patterns) >= 1
        assert len(error_patterns) >= 1
        assert len(interaction_patterns) >= 1

    def test_pattern_extraction_performance(self, isolated_vector_store):
        """Test pattern extraction performance (<5 seconds for 10 patterns)."""
        import time

        vector_store = isolated_vector_store

        # Store enough memories to extract 10+ patterns
        # 5 tools × 3 memories each = 15 tool patterns
        for tool in ["Read", "Write", "Edit", "Bash", "Glob"]:
            for i in range(3):
                vector_store.store(
                    key=f"tool_{tool}_{i}",
                    content={"tool": tool},
                    tags=["tool", tool, "success"],
                    confidence=0.9,
                )

        # Extract patterns and measure time
        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)

        start_time = time.perf_counter()
        result = learning.extract_patterns()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert result.is_ok()
        patterns = result.unwrap()

        # Should extract 5 tool patterns (one per tool, 3 examples each = confidence 0.6)
        assert len(patterns) >= 3  # At least 3 patterns extracted

        # Performance target: <5000ms for 10 patterns
        assert elapsed_ms < 5000
