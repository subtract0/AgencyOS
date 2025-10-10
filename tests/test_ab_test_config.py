"""
Tests for ABTestConfig model.

Constitutional compliance:
- Article II: TDD - tests written FIRST before implementation
- Law #2: Strict typing with Pydantic models
- Law #8: Functions <50 lines each

Reference: specs/spec-007-phase3-ml-inference.md
Author: CodeAgent
Date: 2025-10-10
"""

import pytest
from pydantic import ValidationError

from shared.models.ab_test_config import ABTestConfig


class TestABTestConfigModel:
    """Test ABTestConfig Pydantic model."""

    def test_creates_config_with_default_values(self):
        """Test creating ABTestConfig with default values."""
        # Act
        config = ABTestConfig()

        # Assert
        assert config.enabled is True
        assert config.ml_percentage == 50
        assert config.random_seed == 42

    def test_creates_config_with_custom_values(self):
        """Test creating ABTestConfig with custom values."""
        # Act
        config = ABTestConfig(
            enabled=False,
            ml_percentage=75,
            random_seed=123,
        )

        # Assert
        assert config.enabled is False
        assert config.ml_percentage == 75
        assert config.random_seed == 123

    def test_rejects_negative_ml_percentage(self):
        """Test validation rejects negative ml_percentage."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ABTestConfig(ml_percentage=-10)

        # Assert error message
        assert "ml_percentage" in str(exc_info.value)

    def test_rejects_ml_percentage_above_100(self):
        """Test validation rejects ml_percentage > 100."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ABTestConfig(ml_percentage=150)

        # Assert error message
        assert "ml_percentage" in str(exc_info.value)

    def test_accepts_ml_percentage_boundary_values(self):
        """Test accepts boundary values (0 and 100)."""
        # Act
        config_0 = ABTestConfig(ml_percentage=0)
        config_100 = ABTestConfig(ml_percentage=100)

        # Assert
        assert config_0.ml_percentage == 0
        assert config_100.ml_percentage == 100

    def test_should_use_ml_returns_false_when_disabled(self):
        """Test should_use_ml() returns False when disabled."""
        # Arrange
        config = ABTestConfig(enabled=False, ml_percentage=100)

        # Act & Assert
        assert config.should_use_ml("task-123") is False
        assert config.should_use_ml("task-456") is False
        assert config.should_use_ml("task-789") is False

    def test_should_use_ml_is_deterministic(self):
        """Test should_use_ml() returns same result for same task_id."""
        # Arrange
        config = ABTestConfig(enabled=True, ml_percentage=50)

        # Act - call multiple times with same task_id
        result1 = config.should_use_ml("task-123")
        result2 = config.should_use_ml("task-123")
        result3 = config.should_use_ml("task-123")

        # Assert
        assert result1 == result2 == result3

    def test_should_use_ml_respects_percentage_0(self):
        """Test should_use_ml() returns False for all tasks when ml_percentage=0."""
        # Arrange
        config = ABTestConfig(enabled=True, ml_percentage=0)

        # Act & Assert - test multiple task IDs
        for i in range(100):
            assert config.should_use_ml(f"task-{i}") is False

    def test_should_use_ml_respects_percentage_100(self):
        """Test should_use_ml() returns True for all tasks when ml_percentage=100."""
        # Arrange
        config = ABTestConfig(enabled=True, ml_percentage=100)

        # Act & Assert - test multiple task IDs
        for i in range(100):
            assert config.should_use_ml(f"task-{i}") is True

    def test_should_use_ml_distribution_matches_percentage(self):
        """Test should_use_ml() distribution roughly matches ml_percentage."""
        # Arrange
        config = ABTestConfig(enabled=True, ml_percentage=50)

        # Act - test 1000 task IDs
        ml_count = sum(1 for i in range(1000) if config.should_use_ml(f"task-{i}"))

        # Assert - should be roughly 50% (allow 5% variance)
        expected = 500
        assert expected - 50 <= ml_count <= expected + 50

    def test_should_use_ml_distribution_25_percent(self):
        """Test should_use_ml() distribution for 25% ml_percentage."""
        # Arrange
        config = ABTestConfig(enabled=True, ml_percentage=25)

        # Act
        ml_count = sum(1 for i in range(1000) if config.should_use_ml(f"task-{i}"))

        # Assert - should be roughly 25% (allow 5% variance)
        expected = 250
        assert expected - 50 <= ml_count <= expected + 50

    def test_should_use_ml_distribution_75_percent(self):
        """Test should_use_ml() distribution for 75% ml_percentage."""
        # Arrange
        config = ABTestConfig(enabled=True, ml_percentage=75)

        # Act
        ml_count = sum(1 for i in range(1000) if config.should_use_ml(f"task-{i}"))

        # Assert - should be roughly 75% (allow 5% variance)
        expected = 750
        assert expected - 50 <= ml_count <= expected + 50

    def test_different_seeds_produce_different_distributions(self):
        """Test different random seeds produce different routing."""
        # Arrange
        config1 = ABTestConfig(enabled=True, ml_percentage=50, random_seed=42)
        config2 = ABTestConfig(enabled=True, ml_percentage=50, random_seed=99)

        # Act - test same task IDs with different seeds
        results1 = [config1.should_use_ml(f"task-{i}") for i in range(100)]
        results2 = [config2.should_use_ml(f"task-{i}") for i in range(100)]

        # Assert - results should differ for some tasks
        differences = sum(1 for r1, r2 in zip(results1, results2) if r1 != r2)
        assert differences > 10  # At least 10% different

    def test_same_seed_produces_same_routing(self):
        """Test same seed produces identical routing."""
        # Arrange
        config1 = ABTestConfig(enabled=True, ml_percentage=50, random_seed=42)
        config2 = ABTestConfig(enabled=True, ml_percentage=50, random_seed=42)

        # Act
        results1 = [config1.should_use_ml(f"task-{i}") for i in range(100)]
        results2 = [config2.should_use_ml(f"task-{i}") for i in range(100)]

        # Assert - all results should match
        assert results1 == results2

    def test_to_dict_exports_all_fields(self):
        """Test to_dict() exports all fields correctly."""
        # Arrange
        config = ABTestConfig(
            enabled=False,
            ml_percentage=60,
            random_seed=999,
        )

        # Act
        data = config.to_dict()

        # Assert
        assert data["enabled"] is False
        assert data["ml_percentage"] == 60
        assert data["random_seed"] == 999

    def test_from_dict_deserializes_correctly(self):
        """Test from_dict() deserializes data correctly."""
        # Arrange
        data = {
            "enabled": True,
            "ml_percentage": 80,
            "random_seed": 555,
        }

        # Act
        config = ABTestConfig.from_dict(data)

        # Assert
        assert config.enabled is True
        assert config.ml_percentage == 80
        assert config.random_seed == 555

    def test_from_dict_uses_defaults_for_missing_fields(self):
        """Test from_dict() uses defaults for missing optional fields."""
        # Arrange
        data = {}  # Empty dict, all fields optional

        # Act
        config = ABTestConfig.from_dict(data)

        # Assert
        assert config.enabled is True
        assert config.ml_percentage == 50
        assert config.random_seed == 42

    def test_hash_based_routing_handles_special_characters(self):
        """Test should_use_ml() handles task IDs with special characters."""
        # Arrange
        config = ABTestConfig(enabled=True, ml_percentage=50)

        # Act & Assert - should not raise exceptions
        assert isinstance(config.should_use_ml("task-123-abc"), bool)
        assert isinstance(config.should_use_ml("task_with_underscores"), bool)
        assert isinstance(config.should_use_ml("task.with.dots"), bool)
        assert isinstance(config.should_use_ml("task/with/slashes"), bool)

    def test_hash_based_routing_handles_unicode(self):
        """Test should_use_ml() handles Unicode task IDs."""
        # Arrange
        config = ABTestConfig(enabled=True, ml_percentage=50)

        # Act & Assert
        assert isinstance(config.should_use_ml("task-测试-123"), bool)
        assert isinstance(config.should_use_ml("task-🚀-456"), bool)
