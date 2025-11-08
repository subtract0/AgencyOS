"""
Tests for Article IV Enforcement Tool.

Validates that VectorStore learning is actually enforced, not just claimed.

Constitutional Compliance:
- Article IV: VectorStore integration MANDATORY
- Article III: Automated enforcement (no bypass)
- Article II: 100% verification (storage validated)
"""

import time
from datetime import UTC, datetime

import pytest

from shared.agent_context import create_agent_context
from tools.orchestrator.article_iv_enforcer import (
    ArticleIVEnforcer,
    ArticleIVViolation,
    create_article_iv_enforcer,
)


class TestArticleIVEnforcerCreation:
    """Test enforcer initialization and basic setup."""

    def test_create_enforcer_with_mission_name(self):
        """Test enforcer creation with mission name."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        assert enforcer.mission_name == "Test Mission"
        assert enforcer.session_id is not None
        assert enforcer.session_id.startswith("primea_")
        assert enforcer.context is not None
        assert enforcer.patterns_stored == []

    def test_create_enforcer_with_custom_session_id(self):
        """Test enforcer creation with custom session ID."""
        custom_session = "test_session_123"
        enforcer = create_article_iv_enforcer(
            mission_name="Test Mission", session_id=custom_session
        )

        assert enforcer.session_id == custom_session


class TestArticleIVPatternStorage:
    """Test pattern storage and validation."""

    def test_store_pattern_success(self):
        """Test successful pattern storage."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        result = enforcer.store_pattern(
            pattern_key="test_pattern_1",
            pattern_content={
                "type": "test_pattern",
                "description": "Test pattern for validation",
            },
            tags=["pattern", "test"],
            confidence=1.0,
        )

        assert result.is_ok()
        assert len(enforcer.patterns_stored) == 1

    def test_store_pattern_missing_type(self):
        """Test pattern storage fails without 'type' field."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        result = enforcer.store_pattern(
            pattern_key="test_pattern_invalid",
            pattern_content={
                "description": "Missing type field",
            },
            tags=["pattern", "test"],
        )

        assert result.is_err()
        assert "must include 'type' field" in result.unwrap_err()

    def test_store_pattern_missing_description(self):
        """Test pattern storage fails without 'description' field."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        result = enforcer.store_pattern(
            pattern_key="test_pattern_invalid",
            pattern_content={
                "type": "test_pattern",
            },
            tags=["pattern", "test"],
        )

        assert result.is_err()
        assert "must include 'description' field" in result.unwrap_err()

    def test_store_pattern_missing_pattern_tag(self):
        """Test pattern storage fails without 'pattern' tag."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        result = enforcer.store_pattern(
            pattern_key="test_pattern_invalid",
            pattern_content={
                "type": "test_pattern",
                "description": "Missing pattern tag",
            },
            tags=["test"],  # Missing 'pattern' tag
        )

        assert result.is_err()
        assert "must include 'pattern'" in result.unwrap_err()

    def test_store_multiple_patterns(self):
        """Test storing multiple patterns."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        for i in range(3):
            result = enforcer.store_pattern(
                pattern_key=f"test_pattern_{i}",
                pattern_content={
                    "type": "test_pattern",
                    "description": f"Test pattern {i}",
                },
                tags=["pattern", "test", f"batch_{i}"],
                confidence=0.8 + (i * 0.1),
            )
            assert result.is_ok()

        assert len(enforcer.patterns_stored) == 3

    def test_stored_pattern_enrichment(self):
        """Test that stored patterns are enriched with metadata."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        enforcer.store_pattern(
            pattern_key="test_pattern",
            pattern_content={
                "type": "test_pattern",
                "description": "Test enrichment",
            },
            tags=["pattern", "test"],
            confidence=0.9,
        )

        stored = enforcer.patterns_stored[0]
        content = stored["content"]

        # Check enrichment
        assert content["mission"] == "Test Mission"
        assert content["confidence"] == 0.9
        assert "timestamp" in content
        assert content["session_id"] == enforcer.session_id


class TestArticleIVComplianceValidation:
    """Test Article IV compliance validation."""

    def test_validate_compliance_success(self):
        """Test validation passes with stored patterns."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        # Store a pattern
        enforcer.store_pattern(
            pattern_key="test_pattern_validation",
            pattern_content={
                "type": "quality_gate",
                "description": "Test validation pattern",
            },
            tags=["pattern", "test", "validation"],
            confidence=1.0,
        )

        # Validate compliance
        result = enforcer.validate_article_iv_compliance(min_patterns=1)

        assert result.is_ok()
        report = result.unwrap()
        assert report["article_iv_compliant"] is True
        assert report["patterns_stored"] == 1
        assert report["patterns_verified"] == 1
        assert report["mission"] == "Test Mission"

    def test_validate_compliance_fails_no_patterns(self):
        """Test validation fails when no patterns stored."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        # Don't store any patterns
        with pytest.raises(ArticleIVViolation) as exc_info:
            enforcer.validate_article_iv_compliance(min_patterns=1)

        violation = exc_info.value
        assert "Insufficient patterns stored" in violation.reason
        assert violation.mission == "Test Mission"
        assert len(violation.suggestions) > 0

    def test_validate_compliance_fails_insufficient_patterns(self):
        """Test validation fails when not enough patterns stored."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        # Store only 1 pattern
        enforcer.store_pattern(
            pattern_key="test_pattern",
            pattern_content={
                "type": "test",
                "description": "Only one pattern",
            },
            tags=["pattern", "test"],
        )

        # Require 3 patterns
        with pytest.raises(ArticleIVViolation) as exc_info:
            enforcer.validate_article_iv_compliance(min_patterns=3)

        violation = exc_info.value
        assert "1/3" in violation.reason

    def test_validate_compliance_multiple_patterns(self):
        """Test validation with multiple patterns."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        # Store 5 patterns
        for i in range(5):
            enforcer.store_pattern(
                pattern_key=f"pattern_{i}",
                pattern_content={
                    "type": f"type_{i}",
                    "description": f"Pattern {i}",
                },
                tags=["pattern", "test"],
                confidence=0.6 + (i * 0.08),
            )

        result = enforcer.validate_article_iv_compliance(min_patterns=3)

        assert result.is_ok()
        report = result.unwrap()
        assert report["patterns_stored"] == 5
        assert report["patterns_verified"] == 5
        # Average confidence: (0.6 + 0.68 + 0.76 + 0.84 + 0.92) / 5 = 0.76
        assert abs(report["average_confidence"] - 0.76) < 0.01


class TestArticleIVPatternRetrieval:
    """Test pattern retrieval and verification."""

    def test_stored_patterns_are_retrievable(self):
        """Test that stored patterns can be retrieved from VectorStore."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        # Store a pattern
        pattern_key = f"test_retrievable_{int(time.time())}"
        enforcer.store_pattern(
            pattern_key=pattern_key,
            pattern_content={
                "type": "retrieval_test",
                "description": "Test pattern retrieval",
            },
            tags=["pattern", "test", "retrieval"],
            confidence=1.0,
        )

        # Retrieve using context
        results = enforcer.context.search_memories(
            tags=["pattern", "retrieval"], include_session=False
        )

        # Verify pattern is in results
        found = False
        for result in results:
            if result.get("key") == pattern_key:
                found = True
                content = result.get("content", {})
                assert content.get("type") == "retrieval_test"
                assert content.get("description") == "Test pattern retrieval"
                break

        assert found, f"Pattern {pattern_key} not found in VectorStore"


class TestArticleIVSummaryGeneration:
    """Test summary generation."""

    def test_summary_no_patterns(self):
        """Test summary when no patterns stored."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        summary = enforcer.get_stored_patterns_summary()

        assert "No patterns stored" in summary
        assert "Article IV violation" in summary

    def test_summary_with_patterns(self):
        """Test summary with stored patterns."""
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        enforcer.store_pattern(
            pattern_key="pattern_1",
            pattern_content={
                "type": "quality_gate",
                "description": "Completion validator blocks premature stopping",
            },
            tags=["pattern", "quality"],
            confidence=1.0,
        )

        enforcer.store_pattern(
            pattern_key="pattern_2",
            pattern_content={
                "type": "cost_optimization",
                "description": "Adaptive model routing saves 96% on costs",
            },
            tags=["pattern", "cost"],
            confidence=0.9,
        )

        summary = enforcer.get_stored_patterns_summary()

        assert "Article IV Compliance Summary" in summary
        assert "Test Mission" in summary
        assert "Patterns Stored: 2" in summary
        assert "quality_gate" in summary
        assert "cost_optimization" in summary
        assert "Confidence: 1.00" in summary
        assert "Confidence: 0.90" in summary


class TestArticleIVIntegration:
    """Integration tests for /primeA workflow."""

    def test_primeA_workflow_simulation(self):
        """Simulate /primeA workflow with Article IV enforcement."""
        # STEP 6.0: Initialize enforcer
        mission_name = "Test /primeA Workflow"
        session_id = f"test_primea_{int(time.time())}"
        enforcer = create_article_iv_enforcer(
            mission_name=mission_name, session_id=session_id
        )

        # STEP 6.1-6.3: Execution would happen here (simulated)
        # ...

        # STEP 6.4: Store execution patterns (MANDATORY)
        enforcer.store_pattern(
            pattern_key=f"pattern_quality_gate_{int(time.time())}",
            pattern_content={
                "type": "quality_gate",
                "description": "Applied all quality gates successfully",
                "gates_used": ["slop_immunity", "budget_guard", "completion_validator"],
            },
            tags=["pattern", "quality", "blocking_gate"],
            confidence=1.0,
        )

        enforcer.store_pattern(
            pattern_key=f"pattern_task_decomposition_{int(time.time())}",
            pattern_content={
                "type": "task_decomposition",
                "description": "Decomposed mission into 12 tasks across 3 phases",
                "parallelism": 4,
            },
            tags=["pattern", "planning", "decomposition"],
            confidence=0.8,
        )

        # STEP 6.5: Validate Article IV compliance (BLOCKING GATE)
        validation_result = enforcer.validate_article_iv_compliance(min_patterns=1)

        assert validation_result.is_ok()
        report = validation_result.unwrap()
        assert report["article_iv_compliant"] is True
        assert report["patterns_stored"] >= 2

        # STEP 7: Can now proceed to execution report
        print(enforcer.get_stored_patterns_summary())

    def test_primeA_workflow_fails_without_patterns(self):
        """Test that /primeA workflow fails if no patterns stored."""
        # STEP 6.0: Initialize enforcer
        enforcer = create_article_iv_enforcer(mission_name="Test Mission")

        # STEP 6.1-6.3: Execution happens
        # ...

        # STEP 6.4: FORGET to store patterns (the bug we're fixing!)
        # (No enforcer.store_pattern() calls)

        # STEP 6.5: Validation should BLOCK
        with pytest.raises(ArticleIVViolation) as exc_info:
            enforcer.validate_article_iv_compliance(min_patterns=1)

        violation = exc_info.value
        assert "Insufficient patterns stored" in violation.reason
        assert "Article IV is MANDATORY" in str(violation.suggestions)
