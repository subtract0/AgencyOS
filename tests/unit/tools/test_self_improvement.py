"""
Tests for Self-Improvement Engine (Phase 5).

Tests the autonomous enhancement capabilities including:
- Pattern analysis
- Improvement proposals
- Approval workflow
- Application and rollback
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestImprovementType:
    """Tests for ImprovementType enum."""

    def test_all_types_defined(self):
        """Test that all expected types are defined."""
        from tools.self_improvement import ImprovementType

        expected = ["PERFORMANCE", "QUALITY", "CAPABILITY",
                    "CONFIGURATION", "PATTERN", "KNOWLEDGE"]
        for imp_type in expected:
            assert hasattr(ImprovementType, imp_type)


class TestImprovementStatus:
    """Tests for ImprovementStatus enum."""

    def test_all_statuses_defined(self):
        """Test that all expected statuses are defined."""
        from tools.self_improvement import ImprovementStatus

        expected = ["PROPOSED", "ANALYZING", "APPROVED", "REJECTED",
                    "APPLYING", "APPLIED", "ROLLED_BACK", "FAILED"]
        for status in expected:
            assert hasattr(ImprovementStatus, status)


class TestImprovementProposal:
    """Tests for ImprovementProposal dataclass."""

    def test_proposal_creation(self):
        """Test creating an improvement proposal."""
        from tools.self_improvement import (
            ImprovementProposal,
            ImprovementStatus,
            ImprovementType,
        )

        proposal = ImprovementProposal(
            id="imp-001",
            title="Optimize caching",
            description="Add LRU cache to frequently called functions",
            improvement_type=ImprovementType.PERFORMANCE,
            source="pattern_analyzer",
            confidence=0.85,
            estimated_impact=0.6,
        )

        assert proposal.id == "imp-001"
        assert proposal.status == ImprovementStatus.PROPOSED
        assert proposal.confidence == 0.85

    def test_proposal_defaults(self):
        """Test proposal default values."""
        from tools.self_improvement import ImprovementProposal, ImprovementType

        proposal = ImprovementProposal(
            id="test",
            title="Test",
            description="",
            improvement_type=ImprovementType.QUALITY,
            source="test",
            confidence=0.5,
            estimated_impact=0.3,
        )

        assert proposal.evidence == []
        assert proposal.changes == []
        assert proposal.metrics_before is None


class TestLearningOutcome:
    """Tests for LearningOutcome dataclass."""

    def test_outcome_creation(self):
        """Test creating a learning outcome."""
        from datetime import datetime

        from tools.self_improvement import LearningOutcome

        outcome = LearningOutcome(
            pattern_id="pattern-001",
            pattern_type="success",
            success=True,
            confidence=0.8,
            occurrences=5,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )

        assert outcome.pattern_id == "pattern-001"
        assert outcome.success is True
        assert outcome.occurrences == 5


class TestPatternAnalyzer:
    """Tests for PatternAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a pattern analyzer instance."""
        from tools.self_improvement import PatternAnalyzer

        return PatternAnalyzer()

    def test_analyze_success(self, analyzer):
        """Test analyzing a successful task."""
        result = analyzer.analyze_success(
            task_type="code_generation",
            context={"file": "test.py"},
            duration_ms=150.0,
        )

        assert result.is_ok()
        outcome = result.unwrap()
        assert outcome.success is True
        assert outcome.pattern_type == "success"

    def test_analyze_failure(self, analyzer):
        """Test analyzing a failed task."""
        result = analyzer.analyze_failure(
            task_type="code_generation",
            error="Syntax error",
            context={"file": "broken.py"},
        )

        assert result.is_ok()
        outcome = result.unwrap()
        assert outcome.success is False
        assert outcome.pattern_type == "failure"

    def test_reinforcement_increases_confidence(self, analyzer):
        """Test that repeated success increases confidence."""
        # First occurrence
        result1 = analyzer.analyze_success(
            task_type="same_task",
            context={},
            duration_ms=100,
        )
        initial_confidence = result1.unwrap().confidence

        # Same task again
        result2 = analyzer.analyze_success(
            task_type="same_task",
            context={},
            duration_ms=100,
        )
        new_confidence = result2.unwrap().confidence

        assert new_confidence > initial_confidence

    def test_get_high_confidence_patterns(self, analyzer):
        """Test getting high confidence patterns."""
        # Create patterns with varying confidence
        for i in range(5):
            analyzer.analyze_success(
                task_type=f"task_{i}",
                context={},
                duration_ms=100,
            )

        # Reinforce one pattern to high confidence
        for _ in range(10):
            analyzer.analyze_success(
                task_type="task_0",
                context={},
                duration_ms=100,
            )

        high_conf = analyzer.get_high_confidence_patterns(min_confidence=0.8)

        assert len(high_conf) >= 1

    def test_get_stats(self, analyzer):
        """Test getting analyzer stats."""
        analyzer.analyze_success("success_task", {}, 100)
        analyzer.analyze_failure("fail_task", "Error", {})

        stats = analyzer.get_stats()

        assert stats["total_patterns"] == 2
        assert stats["success_patterns"] == 1
        assert stats["failure_patterns"] == 1


class TestSelfImprovement:
    """Tests for SelfImprovement class."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create a self-improvement engine with temp storage."""
        from tools.self_improvement import SelfImprovement

        # Override storage path
        import tools.self_improvement as module

        original_path = module.SelfImprovement.IMPROVEMENT_STORE
        module.SelfImprovement.IMPROVEMENT_STORE = tmp_path / "improvements.json"

        engine = SelfImprovement()
        yield engine

        module.SelfImprovement.IMPROVEMENT_STORE = original_path

    def test_propose_improvement(self, engine):
        """Test proposing an improvement."""
        from tools.self_improvement import ImprovementType

        result = engine.propose_improvement(
            title="Add caching",
            description="Cache frequently accessed data",
            improvement_type=ImprovementType.PERFORMANCE,
            source="manual",
            confidence=0.8,
            estimated_impact=0.5,
        )

        assert result.is_ok()
        proposal = result.unwrap()
        assert proposal.id.startswith("imp-")
        assert proposal.title == "Add caching"

    def test_propose_requires_title(self, engine):
        """Test that proposal requires title."""
        from tools.self_improvement import ImprovementType

        result = engine.propose_improvement(
            title="",
            description="",
            improvement_type=ImprovementType.QUALITY,
            source="test",
            confidence=0.5,
            estimated_impact=0.3,
        )

        assert result.is_err()
        assert "title" in result.unwrap_err().lower()

    def test_propose_validates_confidence(self, engine):
        """Test that proposal validates confidence range."""
        from tools.self_improvement import ImprovementType

        result = engine.propose_improvement(
            title="Test",
            description="",
            improvement_type=ImprovementType.QUALITY,
            source="test",
            confidence=1.5,  # Invalid
            estimated_impact=0.3,
        )

        assert result.is_err()
        assert "confidence" in result.unwrap_err().lower()

    def test_analyze_improvement(self, engine):
        """Test analyzing an improvement."""
        from tools.self_improvement import ImprovementType

        proposal = engine.propose_improvement(
            title="Test improvement",
            description="Test",
            improvement_type=ImprovementType.QUALITY,
            source="test",
            confidence=0.7,
            estimated_impact=0.5,
        ).unwrap()

        result = engine.analyze_improvement(proposal.id)

        assert result.is_ok()
        analysis = result.unwrap()
        assert "risk_level" in analysis
        assert "recommendation" in analysis

    def test_auto_approve_high_confidence(self, engine):
        """Test that high confidence improvements are auto-approved."""
        from tools.self_improvement import ImprovementStatus, ImprovementType

        proposal = engine.propose_improvement(
            title="High confidence improvement",
            description="Very confident about this",
            improvement_type=ImprovementType.PATTERN,
            source="test",
            confidence=0.95,  # Above threshold
            estimated_impact=0.2,  # Low impact = low risk
        ).unwrap()

        engine.analyze_improvement(proposal.id)

        assert engine.get_proposal(proposal.id).status == ImprovementStatus.APPROVED

    def test_approve_improvement(self, engine):
        """Test manually approving an improvement."""
        from tools.self_improvement import ImprovementStatus, ImprovementType

        proposal = engine.propose_improvement(
            title="To approve",
            description="",
            improvement_type=ImprovementType.QUALITY,
            source="test",
            confidence=0.7,
            estimated_impact=0.3,
        ).unwrap()

        result = engine.approve_improvement(proposal.id)

        assert result.is_ok()
        assert engine.get_proposal(proposal.id).status == ImprovementStatus.APPROVED

    def test_reject_improvement(self, engine):
        """Test rejecting an improvement."""
        from tools.self_improvement import ImprovementStatus, ImprovementType

        proposal = engine.propose_improvement(
            title="To reject",
            description="",
            improvement_type=ImprovementType.QUALITY,
            source="test",
            confidence=0.3,
            estimated_impact=0.8,
        ).unwrap()

        result = engine.reject_improvement(proposal.id, "Too risky")

        assert result.is_ok()
        assert engine.get_proposal(proposal.id).status == ImprovementStatus.REJECTED

    def test_apply_improvement(self, engine):
        """Test applying an approved improvement."""
        from tools.self_improvement import ImprovementStatus, ImprovementType

        proposal = engine.propose_improvement(
            title="To apply",
            description="",
            improvement_type=ImprovementType.PATTERN,
            source="test",
            confidence=0.8,
            estimated_impact=0.3,
        ).unwrap()

        engine.approve_improvement(proposal.id)
        result = engine.apply_improvement(proposal.id)

        assert result.is_ok()
        assert engine.get_proposal(proposal.id).status == ImprovementStatus.APPLIED

    def test_apply_unapproved_fails(self, engine):
        """Test that applying unapproved improvement fails."""
        from tools.self_improvement import ImprovementType

        proposal = engine.propose_improvement(
            title="Not approved",
            description="",
            improvement_type=ImprovementType.QUALITY,
            source="test",
            confidence=0.5,
            estimated_impact=0.3,
        ).unwrap()

        result = engine.apply_improvement(proposal.id)

        assert result.is_err()
        assert "not approved" in result.unwrap_err().lower()

    def test_rollback_improvement(self, engine):
        """Test rolling back an applied improvement."""
        from tools.self_improvement import ImprovementStatus, ImprovementType

        proposal = engine.propose_improvement(
            title="To rollback",
            description="",
            improvement_type=ImprovementType.CONFIGURATION,
            source="test",
            confidence=0.8,
            estimated_impact=0.3,
        ).unwrap()

        engine.approve_improvement(proposal.id)
        engine.apply_improvement(proposal.id)
        result = engine.rollback_improvement(proposal.id)

        assert result.is_ok()
        assert engine.get_proposal(proposal.id).status == ImprovementStatus.ROLLED_BACK

    def test_learn_from_outcome_success(self, engine):
        """Test learning from successful outcome."""
        result = engine.learn_from_outcome(
            task_type="code_generation",
            success=True,
            context={"file": "test.py"},
            duration_ms=150,
        )

        assert result.is_ok()
        outcome = result.unwrap()
        assert outcome.success is True

    def test_learn_from_outcome_failure(self, engine):
        """Test learning from failed outcome."""
        result = engine.learn_from_outcome(
            task_type="code_generation",
            success=False,
            context={"file": "broken.py"},
            error="Compilation failed",
        )

        assert result.is_ok()
        outcome = result.unwrap()
        assert outcome.success is False

    def test_suggest_improvements(self, engine):
        """Test suggesting improvements from patterns."""
        # Learn some patterns
        for _ in range(5):
            engine.learn_from_outcome(
                task_type="optimizable_task",
                success=True,
                context={},
                duration_ms=100,
            )

        suggestions = engine.suggest_improvements()

        # May or may not have suggestions depending on confidence
        assert isinstance(suggestions, list)

    def test_get_pending_proposals(self, engine):
        """Test getting pending proposals."""
        from tools.self_improvement import ImprovementType

        for i in range(3):
            engine.propose_improvement(
                title=f"Pending {i}",
                description="",
                improvement_type=ImprovementType.QUALITY,
                source="test",
                confidence=0.6,
                estimated_impact=0.3,
            )

        pending = engine.get_pending_proposals()

        assert len(pending) == 3

    def test_get_stats(self, engine):
        """Test getting engine statistics."""
        from tools.self_improvement import ImprovementType

        engine.propose_improvement(
            title="Test 1",
            description="",
            improvement_type=ImprovementType.QUALITY,
            source="test",
            confidence=0.7,
            estimated_impact=0.3,
        )

        engine.propose_improvement(
            title="Test 2",
            description="",
            improvement_type=ImprovementType.PERFORMANCE,
            source="test",
            confidence=0.7,
            estimated_impact=0.3,
        )

        stats = engine.get_stats()

        assert stats["total_proposals"] == 2
        assert "by_type" in stats
        assert "pattern_stats" in stats


class TestGlobalEngine:
    """Tests for global engine instance."""

    def test_get_engine_returns_instance(self):
        """Test that get_engine returns an engine."""
        from tools.self_improvement import SelfImprovement, get_engine

        engine = get_engine()

        assert isinstance(engine, SelfImprovement)

    def test_get_engine_returns_same_instance(self):
        """Test that get_engine returns the same instance."""
        from tools.self_improvement import get_engine

        engine1 = get_engine()
        engine2 = get_engine()

        assert engine1 is engine2
