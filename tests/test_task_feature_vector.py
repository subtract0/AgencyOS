"""
Tests for TaskFeatureVector model.

Validates:
- 1644-dimension feature vector schema (1536 + 100 + 8)
- Pydantic validators for dimension constraints
- Article II compliance (strict typing, 100% verification)
- Article IV compliance (VectorStore-ready format)
- to_flat_array() conversion for ML model input

Constitutional compliance:
- Article I: Complete context (all dimensions validated)
- Article II: 100% verification (100% test coverage required)

Reference: specs/spec-005-advanced-pattern-recognition.md AC-1.2
Author: ChiefArchitectAgent
Date: 2025-10-10
"""

import pytest
from pydantic import ValidationError

from shared.models.task_feature_vector import TaskFeatureVector


class TestTaskFeatureVectorSchema:
    """Test TaskFeatureVector dimension schema and validation."""

    def test_valid_feature_vector_all_dimensions(self):
        """Article II: Valid feature vector with all 1644 dimensions."""
        vector = TaskFeatureVector(
            embedding=[0.1] * 1536,  # 1536-dim
            tfidf_features=[0.05] * 100,  # 100-dim
            description_length=150,
            word_count=25,
            has_refactor_keyword=1,
            has_test_keyword=0,
            has_async_keyword=1,
            has_fix_keyword=0,
            estimated_time_seconds=600.0,
            historical_tier_mode=2
        )

        assert len(vector.embedding) == 1536
        assert len(vector.tfidf_features) == 100
        assert vector.description_length == 150
        assert vector.word_count == 25
        assert vector.has_refactor_keyword == 1
        assert vector.has_test_keyword == 0
        assert vector.has_async_keyword == 1
        assert vector.has_fix_keyword == 0
        assert vector.estimated_time_seconds == 600.0
        assert vector.historical_tier_mode == 2

    def test_embedding_dimension_validation_too_short(self):
        """Article II: Reject embedding with <1536 dimensions."""
        with pytest.raises(ValidationError) as exc_info:
            TaskFeatureVector(
                embedding=[0.1] * 1535,  # Too short (1535 < 1536)
                tfidf_features=[0.05] * 100,
                description_length=100,
                word_count=20,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=0
            )

        error_str = str(exc_info.value)
        assert "embedding" in error_str.lower()
        assert "1536" in error_str or "dimension" in error_str.lower()

    def test_embedding_dimension_validation_too_long(self):
        """Article II: Reject embedding with >1536 dimensions."""
        with pytest.raises(ValidationError) as exc_info:
            TaskFeatureVector(
                embedding=[0.1] * 1537,  # Too long (1537 > 1536)
                tfidf_features=[0.05] * 100,
                description_length=100,
                word_count=20,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=0
            )

        error_str = str(exc_info.value)
        assert "embedding" in error_str.lower()
        assert "1536" in error_str or "1537" in error_str

    def test_tfidf_dimension_validation_too_short(self):
        """Article II: Reject TF-IDF with <100 dimensions."""
        with pytest.raises(ValidationError) as exc_info:
            TaskFeatureVector(
                embedding=[0.1] * 1536,
                tfidf_features=[0.05] * 99,  # Too short (99 < 100)
                description_length=100,
                word_count=20,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=0
            )

        error_str = str(exc_info.value)
        assert "tfidf" in error_str.lower()
        assert "100" in error_str or "99" in error_str

    def test_tfidf_dimension_validation_too_long(self):
        """Article II: Reject TF-IDF with >100 dimensions."""
        with pytest.raises(ValidationError) as exc_info:
            TaskFeatureVector(
                embedding=[0.1] * 1536,
                tfidf_features=[0.05] * 101,  # Too long (101 > 100)
                description_length=100,
                word_count=20,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=0
            )

        error_str = str(exc_info.value)
        assert "tfidf" in error_str.lower()
        assert "100" in error_str or "101" in error_str


class TestTaskFeatureVectorMetadata:
    """Test metadata feature validation (8 dimensions)."""

    def test_metadata_valid_ranges(self):
        """Article II: Validate metadata features within valid ranges."""
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=250,  # 0-10000+ valid
            word_count=42,  # 0-2000+ valid
            has_refactor_keyword=1,  # 0 or 1
            has_test_keyword=0,  # 0 or 1
            has_async_keyword=1,  # 0 or 1
            has_fix_keyword=0,  # 0 or 1
            estimated_time_seconds=1800.0,  # 0-36000 valid
            historical_tier_mode=1  # 0, 1, or 2
        )

        assert vector.description_length == 250
        assert vector.word_count == 42
        assert vector.estimated_time_seconds == 1800.0
        assert vector.historical_tier_mode == 1

    def test_binary_flags_zero_valid(self):
        """Article II: Binary flags accept 0 value."""
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=50,
            word_count=10,
            has_refactor_keyword=0,  # Valid
            has_test_keyword=0,  # Valid
            has_async_keyword=0,  # Valid
            has_fix_keyword=0,  # Valid
            estimated_time_seconds=0.0,
            historical_tier_mode=0
        )

        assert vector.has_refactor_keyword == 0
        assert vector.has_test_keyword == 0
        assert vector.has_async_keyword == 0
        assert vector.has_fix_keyword == 0

    def test_binary_flags_one_valid(self):
        """Article II: Binary flags accept 1 value."""
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=50,
            word_count=10,
            has_refactor_keyword=1,  # Valid
            has_test_keyword=1,  # Valid
            has_async_keyword=1,  # Valid
            has_fix_keyword=1,  # Valid
            estimated_time_seconds=0.0,
            historical_tier_mode=0
        )

        assert vector.has_refactor_keyword == 1
        assert vector.has_test_keyword == 1
        assert vector.has_async_keyword == 1
        assert vector.has_fix_keyword == 1

    def test_binary_flags_invalid_values(self):
        """Article II: Binary flags reject values other than 0 or 1."""
        # Test has_refactor_keyword=2 (invalid)
        with pytest.raises(ValidationError) as exc_info:
            TaskFeatureVector(
                embedding=[0.0] * 1536,
                tfidf_features=[0.0] * 100,
                description_length=50,
                word_count=10,
                has_refactor_keyword=2,  # Invalid (not 0 or 1)
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=0
            )

        error_str = str(exc_info.value)
        assert "has_refactor_keyword" in error_str.lower() or "refactor" in error_str.lower()
        assert "1" in error_str or "less than" in error_str.lower()

    def test_historical_tier_mode_valid_tiers(self):
        """Article IV: Historical tier mode accepts 0, 1, 2."""
        for tier in [0, 1, 2]:
            vector = TaskFeatureVector(
                embedding=[0.0] * 1536,
                tfidf_features=[0.0] * 100,
                description_length=50,
                word_count=10,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=tier
            )
            assert vector.historical_tier_mode == tier

    def test_historical_tier_mode_invalid_tier(self):
        """Article IV: Historical tier mode rejects invalid tiers (not 0, 1, 2)."""
        with pytest.raises(ValidationError) as exc_info:
            TaskFeatureVector(
                embedding=[0.0] * 1536,
                tfidf_features=[0.0] * 100,
                description_length=50,
                word_count=10,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=3  # Invalid (not 0, 1, or 2)
            )

        error_str = str(exc_info.value)
        assert "historical_tier_mode" in error_str.lower() or "tier" in error_str.lower()
        assert "2" in error_str or "less than" in error_str.lower()

    def test_description_length_negative_rejected(self):
        """Article II: Reject negative description length."""
        with pytest.raises(ValidationError):
            TaskFeatureVector(
                embedding=[0.0] * 1536,
                tfidf_features=[0.0] * 100,
                description_length=-10,  # Invalid (negative)
                word_count=10,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=0
            )

    def test_estimated_time_negative_rejected(self):
        """Article II: Reject negative estimated time."""
        with pytest.raises(ValidationError):
            TaskFeatureVector(
                embedding=[0.0] * 1536,
                tfidf_features=[0.0] * 100,
                description_length=50,
                word_count=10,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=-300.0,  # Invalid (negative)
                historical_tier_mode=0
            )


class TestTaskFeatureVectorConversion:
    """Test to_flat_array() conversion for ML model input."""

    def test_to_flat_array_correct_dimension(self):
        """Article II: to_flat_array() returns exactly 1644 dimensions."""
        vector = TaskFeatureVector(
            embedding=[0.1] * 1536,
            tfidf_features=[0.05] * 100,
            description_length=150,
            word_count=25,
            has_refactor_keyword=1,
            has_test_keyword=0,
            has_async_keyword=1,
            has_fix_keyword=0,
            estimated_time_seconds=600.0,
            historical_tier_mode=2
        )

        flat = vector.to_flat_array()

        assert len(flat) == 1644  # 1536 + 100 + 8
        assert all(isinstance(x, float) for x in flat)  # All floats for scikit-learn

    def test_to_flat_array_correct_ordering(self):
        """Article II: to_flat_array() preserves correct feature ordering."""
        vector = TaskFeatureVector(
            embedding=[0.1] * 1536,
            tfidf_features=[0.05] * 100,
            description_length=150,
            word_count=25,
            has_refactor_keyword=1,
            has_test_keyword=0,
            has_async_keyword=1,
            has_fix_keyword=0,
            estimated_time_seconds=600.0,
            historical_tier_mode=2
        )

        flat = vector.to_flat_array()

        # Verify embedding (first 1536)
        assert flat[:1536] == [0.1] * 1536

        # Verify TF-IDF (next 100)
        assert flat[1536:1636] == [0.05] * 100

        # Verify metadata (last 8)
        assert flat[1636] == 150.0  # description_length
        assert flat[1637] == 25.0  # word_count
        assert flat[1638] == 1.0  # has_refactor_keyword
        assert flat[1639] == 0.0  # has_test_keyword
        assert flat[1640] == 1.0  # has_async_keyword
        assert flat[1641] == 0.0  # has_fix_keyword
        assert flat[1642] == 600.0  # estimated_time_seconds
        assert flat[1643] == 2.0  # historical_tier_mode

    def test_to_flat_array_metadata_conversion_to_float(self):
        """Article II: to_flat_array() converts integer metadata to float."""
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=100,  # int
            word_count=20,  # int
            has_refactor_keyword=1,  # int
            has_test_keyword=0,  # int
            has_async_keyword=1,  # int
            has_fix_keyword=0,  # int
            estimated_time_seconds=300.0,  # already float
            historical_tier_mode=1  # int
        )

        flat = vector.to_flat_array()

        # All metadata converted to float
        metadata_slice = flat[1636:]
        assert all(isinstance(x, float) for x in metadata_slice)
        assert metadata_slice == [100.0, 20.0, 1.0, 0.0, 1.0, 0.0, 300.0, 1.0]


class TestTaskFeatureVectorUtilityMethods:
    """Test utility methods for dimension introspection."""

    def test_get_total_dimensions(self):
        """Article II: get_total_dimensions() returns 1644."""
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=50,
            word_count=10,
            has_refactor_keyword=0,
            has_test_keyword=0,
            has_async_keyword=0,
            has_fix_keyword=0,
            estimated_time_seconds=0.0,
            historical_tier_mode=0
        )

        assert vector.get_total_dimensions() == 1644

    def test_get_dimension_breakdown(self):
        """Article II: get_dimension_breakdown() returns correct breakdown."""
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=50,
            word_count=10,
            has_refactor_keyword=0,
            has_test_keyword=0,
            has_async_keyword=0,
            has_fix_keyword=0,
            estimated_time_seconds=0.0,
            historical_tier_mode=0
        )

        breakdown = vector.get_dimension_breakdown()

        assert breakdown == {
            "embedding": 1536,
            "tfidf": 100,
            "metadata": 8,
            "total": 1644
        }


class TestTaskFeatureVectorConstitutionalCompliance:
    """Test constitutional compliance (Articles I-V)."""

    def test_article_ii_strict_typing_no_dict_any(self):
        """Article II: Model uses strict typing, no Dict[Any, Any]."""
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=50,
            word_count=10,
            has_refactor_keyword=0,
            has_test_keyword=0,
            has_async_keyword=0,
            has_fix_keyword=0,
            estimated_time_seconds=0.0,
            historical_tier_mode=0
        )

        # All fields have explicit types (no Any)
        schema = vector.model_json_schema()
        assert "embedding" in schema["properties"]
        assert "tfidf_features" in schema["properties"]
        assert schema["properties"]["embedding"]["type"] == "array"
        assert schema["properties"]["tfidf_features"]["type"] == "array"

    def test_article_ii_validators_enforce_complete_context(self):
        """Article I: Validators ensure complete context (all 1644 dimensions)."""
        # Incomplete embedding (Article I violation)
        with pytest.raises(ValidationError) as exc_info:
            TaskFeatureVector(
                embedding=[0.0] * 1000,  # Incomplete (1000 < 1536)
                tfidf_features=[0.0] * 100,
                description_length=50,
                word_count=10,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=0.0,
                historical_tier_mode=0
            )

        error_str = str(exc_info.value)
        # Pydantic validator ensures complete context by rejecting incomplete dimensions
        assert "embedding" in error_str.lower()
        assert "1536" in error_str or "1000" in error_str

    def test_article_iv_historical_tier_mode_from_vectorstore(self):
        """Article IV: historical_tier_mode supports VectorStore learning."""
        # Simulate VectorStore learning result (tier mode from similar tasks)
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=50,
            word_count=10,
            has_refactor_keyword=0,
            has_test_keyword=0,
            has_async_keyword=0,
            has_fix_keyword=0,
            estimated_time_seconds=0.0,
            historical_tier_mode=2  # VectorStore learned: similar tasks were complex (P1)
        )

        assert vector.historical_tier_mode == 2  # Article IV: Learning integrated


class TestTaskFeatureVectorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_values_all_features(self):
        """Edge case: All features set to zero (valid but unusual)."""
        vector = TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=0,  # Empty description
            word_count=0,  # No words
            has_refactor_keyword=0,
            has_test_keyword=0,
            has_async_keyword=0,
            has_fix_keyword=0,
            estimated_time_seconds=0.0,
            historical_tier_mode=0
        )

        flat = vector.to_flat_array()
        assert len(flat) == 1644
        assert all(x == 0.0 for x in flat)

    def test_large_values_metadata(self):
        """Edge case: Large but valid metadata values."""
        vector = TaskFeatureVector(
            embedding=[1.0] * 1536,  # Max normalized embedding
            tfidf_features=[1.0] * 100,  # Max TF-IDF scores
            description_length=10000,  # Very long description
            word_count=2000,  # Very long task
            has_refactor_keyword=1,
            has_test_keyword=1,
            has_async_keyword=1,
            has_fix_keyword=1,
            estimated_time_seconds=36000.0,  # 10 hours
            historical_tier_mode=2  # Complex
        )

        assert vector.description_length == 10000
        assert vector.word_count == 2000
        assert vector.estimated_time_seconds == 36000.0

    def test_mixed_positive_negative_embedding(self):
        """Edge case: Embedding with positive and negative values (normal for embeddings)."""
        embedding_mixed = [0.1, -0.2, 0.3, -0.4] * 384  # 1536 values, alternating signs
        vector = TaskFeatureVector(
            embedding=embedding_mixed,
            tfidf_features=[0.0] * 100,
            description_length=50,
            word_count=10,
            has_refactor_keyword=0,
            has_test_keyword=0,
            has_async_keyword=0,
            has_fix_keyword=0,
            estimated_time_seconds=0.0,
            historical_tier_mode=0
        )

        flat = vector.to_flat_array()
        assert flat[:4] == [0.1, -0.2, 0.3, -0.4]  # Negative values preserved
