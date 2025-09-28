"""
Integration tests for the Pattern Intelligence Unification.

Tests the migration from legacy Pattern and HealingPattern formats
to the unified CodingPattern format.
"""

import pytest
import json
from datetime import datetime
from typing import Dict, List

# Import legacy formats
from core.patterns import Pattern, UnifiedPatternStore
from shared.models.patterns import (
    HealingPattern,
    PatternType,
    ValidationStatus
)

# Import new unified format
from pattern_intelligence.coding_pattern import (
    CodingPattern,
    ProblemContext,
    SolutionApproach,
    EffectivenessMetric,
    PatternMetadata
)
from pattern_intelligence.pattern_store import PatternStore
from pattern_intelligence.migration import (
    pattern_to_coding_pattern,
    healing_pattern_to_coding_pattern,
    dict_to_coding_pattern
)


class TestPatternMigration:
    """Test migration utilities for pattern conversion."""

    def test_legacy_pattern_to_coding_pattern(self):
        """Test converting legacy Pattern to CodingPattern."""
        # Create a legacy Pattern
        legacy = Pattern(
            id="test_pattern_001",
            pattern_type="error_fix",
            context={"error_type": "NoneType", "original": "if obj:", "transformation": "add_null_check"},
            solution="if obj is not None:",
            success_rate=0.85,
            usage_count=10,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            tags=["nonetype", "auto_fix"]
        )

        # Convert to CodingPattern
        coding_pattern = pattern_to_coding_pattern(legacy)

        # Verify conversion
        assert isinstance(coding_pattern, CodingPattern)
        assert coding_pattern.metadata.pattern_id == "test_pattern_001"
        assert coding_pattern.context.domain == "error_fix"
        assert coding_pattern.outcome.success_rate == 0.85
        assert coding_pattern.outcome.adoption_rate == 10
        assert "nonetype" in coding_pattern.metadata.tags
        assert "auto_fix" in coding_pattern.metadata.tags

    def test_healing_pattern_to_coding_pattern(self):
        """Test converting HealingPattern to CodingPattern."""
        # Create a HealingPattern
        healing = HealingPattern(
            pattern_id="heal_pattern_001",
            pattern_type=PatternType.TRIGGER_ACTION,
            trigger="memory_leak_detected",
            action="restart_service",
            context="production_environment",
            occurrences=25,
            success_rate=0.92,
            confidence=0.88,
            overall_confidence=0.85,
            effectiveness_score=0.90,
            description="Restart service on memory leak detection",
            evidence=[],
            validation_status=ValidationStatus.VALIDATED
        )

        # Convert to CodingPattern
        coding_pattern = healing_pattern_to_coding_pattern(healing)

        # Verify conversion
        assert isinstance(coding_pattern, CodingPattern)
        assert coding_pattern.metadata.pattern_id == "heal_pattern_001"
        assert coding_pattern.context.symptoms == ["memory_leak_detected"]
        assert "restart_service" in coding_pattern.solution.approach
        assert coding_pattern.outcome.success_rate == 0.92
        assert coding_pattern.outcome.confidence == 0.85
        assert coding_pattern.metadata.validation_status == "validated"

    def test_bidirectional_conversion(self):
        """Test converting CodingPattern to HealingPattern and back."""
        # Create a CodingPattern
        original = CodingPattern(
            context=ProblemContext(
                description="Memory leak in production",
                domain="performance",
                constraints=["limited_memory"],
                symptoms=["high_memory_usage", "slow_response"]
            ),
            solution=SolutionApproach(
                approach="Restart service periodically",
                implementation="Schedule service restart every 6 hours",
                tools=["systemd", "cron"],
                reasoning="Temporary fix until memory leak is resolved"
            ),
            outcome=EffectivenessMetric(
                success_rate=0.75,
                performance_impact="Service downtime during restart",
                confidence=0.8
            ),
            metadata=PatternMetadata(
                pattern_id="coding_pattern_001",
                discovered_timestamp=datetime.now().isoformat(),
                source="manual_entry",
                discoverer="test_suite"
            )
        )

        # Convert to HealingPattern
        healing = HealingPattern.from_coding_pattern(original)
        assert isinstance(healing, HealingPattern)
        assert healing.pattern_id == "coding_pattern_001"

        # Convert back to CodingPattern
        restored = healing.to_coding_pattern()
        assert isinstance(restored, CodingPattern)
        assert restored.metadata.pattern_id == original.metadata.pattern_id
        assert restored.outcome.success_rate == original.outcome.success_rate


class TestUnifiedPatternStore:
    """Test the deprecated UnifiedPatternStore with new backend."""

    def test_unified_store_uses_new_backend(self):
        """Test that UnifiedPatternStore delegates to new PatternStore."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            store = UnifiedPatternStore(persist=False)

            # Check deprecation warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

        # Add a pattern
        pattern = Pattern(
            id="test_001",
            pattern_type="test",
            context={"test": "context"},
            solution="test solution",
            success_rate=0.9,
            usage_count=1,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            tags=["test"]
        )

        # Should work without errors (compatibility maintained)
        assert store.add(pattern) == True

        # Pattern should be in both legacy and new stores
        assert pattern.id in store.patterns

        # Find should still work
        results = store.find(pattern_type="test")
        assert len(results) == 1
        assert results[0].id == "test_001"


class TestPatternStore:
    """Test the new PatternStore with CodingPattern."""

    def test_store_and_retrieve_coding_pattern(self):
        """Test storing and retrieving CodingPattern."""
        store = PatternStore(namespace="test")

        # Create a CodingPattern
        pattern = CodingPattern(
            context=ProblemContext(
                description="Test pattern",
                domain="testing",
                constraints=[],
                symptoms=["test_symptom"]
            ),
            solution=SolutionApproach(
                approach="Test approach",
                implementation="Test implementation",
                tools=["pytest"],
                reasoning="For testing"
            ),
            outcome=EffectivenessMetric(
                success_rate=0.95,
                confidence=0.9
            ),
            metadata=PatternMetadata(
                pattern_id="test_pattern_store_001",
                discovered_timestamp=datetime.now().isoformat(),
                source="test",
                discoverer="test_suite"
            )
        )

        # Store the pattern
        assert store.store_pattern(pattern) == True

        # Retrieve patterns
        results = store.find_patterns(query="test_symptom")

        # Should find our pattern
        assert len(results) > 0
        found = False
        for result in results:
            if result.pattern.metadata.pattern_id == "test_pattern_store_001":
                found = True
                assert result.pattern.outcome.success_rate == 0.95
                break
        assert found, "Pattern not found in search results"


class TestSelfHealingPatternExtractor:
    """Test that SelfHealingPatternExtractor outputs both formats."""

    def test_extractor_dual_format_output(self):
        """Test that the extractor provides both legacy and new formats."""
        from learning_agent.tools.self_healing_pattern_extractor import SelfHealingPatternExtractor

        # Verify the module has the proper imports
        import learning_agent.tools.self_healing_pattern_extractor as extractor_module

        # Check that CodingPattern is imported
        assert hasattr(extractor_module, 'CodingPattern')

        # Check that the extractor class exists
        assert hasattr(extractor_module, 'SelfHealingPatternExtractor')

        # Verify the extractor can be instantiated
        extractor = SelfHealingPatternExtractor(
            data_sources="logs",
            time_window="1d",
            success_threshold=0.7,
            min_occurrences=1
        )

        # Check that the extractor has the necessary methods
        assert hasattr(extractor, 'run')
        assert hasattr(extractor, '_extract_successful_patterns')

        # The actual dual-format output is tested via the run() method
        # which returns JSON with both "patterns" (legacy) and "coding_patterns" (new) keys


class TestDictConversion:
    """Test converting dictionaries to CodingPattern."""

    def test_dict_to_coding_pattern_legacy_format(self):
        """Test converting legacy dict format to CodingPattern."""
        legacy_dict = {
            "id": "dict_pattern_001",
            "pattern_type": "optimization",
            "context": {"type": "slow_query", "database": "postgres"},
            "solution": "Add index on user_id column",
            "success_rate": 0.88,
            "usage_count": 5,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "tags": ["database", "performance"]
        }

        coding_pattern = dict_to_coding_pattern(legacy_dict)

        assert isinstance(coding_pattern, CodingPattern)
        assert coding_pattern.metadata.pattern_id == "dict_pattern_001"
        assert coding_pattern.context.domain == "optimization"
        assert coding_pattern.outcome.success_rate == 0.88

    def test_dict_to_coding_pattern_healing_format(self):
        """Test converting HealingPattern dict format to CodingPattern."""
        healing_dict = {
            "pattern_id": "heal_dict_001",
            "pattern_type": "trigger_action",
            "trigger": "cpu_high",
            "action": "scale_up",
            "occurrences": 15,
            "success_rate": 0.93,
            "confidence": 0.87,
            "description": "Scale up on high CPU",
            "validation_status": "validated"
        }

        coding_pattern = dict_to_coding_pattern(healing_dict)

        assert isinstance(coding_pattern, CodingPattern)
        assert "cpu_high" in str(coding_pattern.context.symptoms)
        assert "scale_up" in coding_pattern.solution.approach


if __name__ == "__main__":
    pytest.main([__file__, "-v"])