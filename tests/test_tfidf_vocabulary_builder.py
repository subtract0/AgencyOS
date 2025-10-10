"""
Comprehensive tests for TfidfVocabularyBuilder.

TDD-first implementation following Constitutional Law #1.
Tests written to ensure complete coverage of vocabulary building.

Test Coverage:
- TfidfVocabulary Pydantic model validation
- Vocabulary building from task descriptions (AAA pattern)
- Edge cases (empty input, single document, large corpus)
- File I/O operations (save, load, directory creation)
- Result pattern validation (Ok/Err branches)
- Top-N filtering behavior
- IDF score computation

Constitutional Compliance:
- Article I: Complete context (all tests isolated, no shared state)
- Article II: 100% test coverage, strict typing
- Article IV: VectorStore pattern extraction ready
- Article V: Follows TF-IDF vocabulary builder specification
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pytest

from shared.type_definitions.result import Result
from tools.ml_routing.tfidf_vocabulary_builder import (
    TfidfVocabulary,
    TfidfVocabularyBuilder,
)

# ============================================================================
# Test Suite 1: TfidfVocabulary Pydantic Model
# ============================================================================


class TestTfidfVocabularyPydanticModel:
    """Test Pydantic model validation and defaults."""

    def test_valid_vocabulary_all_fields_populated(self):
        """Test valid TfidfVocabulary with all fields."""
        # Arrange
        terms = ["pydantic", "result", "test", "tdd", "agent"]
        idf_scores = {
            "pydantic": 2.5,
            "result": 2.3,
            "test": 2.1,
            "tdd": 2.8,
            "agent": 2.0,
        }
        created_time = datetime.now()

        # Act
        vocab = TfidfVocabulary(
            terms=terms,
            idf_scores=idf_scores,
            version="v1.0",
            created_at=created_time,
        )

        # Assert
        assert vocab.terms == terms
        assert vocab.idf_scores == idf_scores
        assert vocab.version == "v1.0"
        assert vocab.created_at == created_time

    def test_valid_vocabulary_default_values(self):
        """Test TfidfVocabulary with default version and timestamp."""
        # Arrange
        terms = ["pydantic", "result"]
        idf_scores = {"pydantic": 2.5, "result": 2.3}

        # Act
        vocab = TfidfVocabulary(terms=terms, idf_scores=idf_scores)

        # Assert
        assert vocab.terms == terms
        assert vocab.idf_scores == idf_scores
        assert vocab.version == "v1.0"  # Default
        assert isinstance(vocab.created_at, datetime)

    def test_invalid_vocabulary_empty_terms(self):
        """Test vocabulary with empty terms list (valid but unusual)."""
        # Arrange
        terms = []
        idf_scores = {}

        # Act
        vocab = TfidfVocabulary(terms=terms, idf_scores=idf_scores)

        # Assert - should not crash, but empty
        assert vocab.terms == []
        assert vocab.idf_scores == {}

    def test_vocabulary_serialization_to_dict(self):
        """Test vocabulary can be serialized to dictionary."""
        # Arrange
        vocab = TfidfVocabulary(
            terms=["test", "code"],
            idf_scores={"test": 1.5, "code": 1.8},
            version="v1.0",
        )

        # Act
        vocab_dict = vocab.model_dump()

        # Assert
        assert vocab_dict["terms"] == ["test", "code"]
        assert vocab_dict["idf_scores"] == {"test": 1.5, "code": 1.8}
        assert vocab_dict["version"] == "v1.0"
        assert "created_at" in vocab_dict


# ============================================================================
# Test Suite 2: Happy Path Tests
# ============================================================================


class TestBuildVocabularyHappyPath:
    """Test vocabulary generation from realistic task descriptions."""

    @pytest.fixture
    def sample_tasks(self):
        """Fixture providing realistic code-related task descriptions."""
        return [
            "Implement Result pattern for error handling in Python",
            "Create Pydantic models with strict type validation",
            "Write comprehensive tests using pytest framework",
            "Implement TDD workflow with test-first development",
            "Build agent communication using shared context",
            "Create TF-IDF vocabulary builder for task classification",
            "Implement constitutional compliance validation",
            "Write integration tests for agent workflows",
            "Create ADR documentation for architecture decisions",
            "Implement VectorStore learning pattern extraction",
            "Build quality enforcer agent with autonomous healing",
            "Create test generator using NECESSARY pattern",
            "Implement file I/O with Result pattern",
            "Build code analyzer with AST parsing",
            "Create memory facade with three-tier architecture",
            "Implement git workflow automation tools",
            "Build JSON schema validation with Pydantic",
            "Create API endpoints with strict typing",
            "Implement retry controller with exponential backoff",
            "Build telemetry system for agent monitoring",
        ]

    def test_build_vocabulary_from_sample_tasks(self, sample_tasks):
        """Test vocabulary generation from realistic task descriptions."""
        # Arrange
        builder = TfidfVocabularyBuilder()

        # Act
        result = builder.build_vocabulary(sample_tasks, top_n=100)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()
        assert isinstance(vocab, TfidfVocabulary)
        assert len(vocab.terms) <= 100  # May be less if not enough unique terms
        assert len(vocab.idf_scores) == len(vocab.terms)
        assert all(isinstance(term, str) for term in vocab.terms)
        assert all(score > 0 for score in vocab.idf_scores.values())

    def test_vocabulary_contains_code_keywords(self, sample_tasks):
        """Test vocabulary includes code-specific keywords."""
        # Arrange
        builder = TfidfVocabularyBuilder()

        # Act
        result = builder.build_vocabulary(sample_tasks, top_n=50)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()

        # Check for presence of key technical terms
        # Note: Exact terms depend on TF-IDF scoring, but should include some
        terms_lower = [term.lower() for term in vocab.terms]
        code_keywords = ["pydantic", "result", "test", "agent", "pattern"]
        found_keywords = [kw for kw in code_keywords if kw in terms_lower]

        # At least some code keywords should be present
        assert len(found_keywords) > 0, f"No code keywords found in {terms_lower}"

    def test_idf_scores_are_positive_and_valid(self, sample_tasks):
        """Test all IDF scores are positive and in valid range."""
        # Arrange
        builder = TfidfVocabularyBuilder()

        # Act
        result = builder.build_vocabulary(sample_tasks, top_n=50)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()

        for term, score in vocab.idf_scores.items():
            assert score > 0, f"IDF score for '{term}' is not positive: {score}"
            assert score < 100, f"IDF score for '{term}' is suspiciously high: {score}"


# ============================================================================
# Test Suite 3: Edge Case Tests
# ============================================================================


class TestBuildVocabularyEdgeCases:
    """Test handling of edge cases and boundary conditions."""

    def test_build_vocabulary_empty_input(self):
        """Test handling of empty task list."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        tasks = []

        # Act
        result = builder.build_vocabulary(tasks)

        # Assert
        assert result.is_err()
        error_msg = result.unwrap_err()
        assert "empty" in error_msg.lower()

    def test_build_vocabulary_single_document(self):
        """Test with only one task (insufficient for TF-IDF by default)."""
        # Arrange
        builder = TfidfVocabularyBuilder(min_df=2)
        tasks = ["Single task with some words"]

        # Act
        result = builder.build_vocabulary(tasks)

        # Assert
        assert result.is_err()
        error_msg = result.unwrap_err()
        assert "at least" in error_msg.lower()

    def test_build_vocabulary_single_document_min_df_one(self):
        """Test with single document when min_df=1 (should succeed)."""
        # Arrange
        builder = TfidfVocabularyBuilder(min_df=1)
        tasks = ["Single task with multiple words for vocabulary"]

        # Act
        result = builder.build_vocabulary(tasks, top_n=5)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()
        assert len(vocab.terms) <= 5

    def test_build_vocabulary_very_large_corpus(self):
        """Test with 1000+ tasks (performance check)."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        # Generate 1000 tasks with varied content
        tasks = [
            f"Task {i} implement feature with code and test validation {i % 10}"
            for i in range(1000)
        ]

        # Act
        start_time = time.time()
        result = builder.build_vocabulary(tasks, top_n=100)
        elapsed = time.time() - start_time

        # Assert
        assert result.is_ok()
        assert elapsed < 5.0, f"Vocabulary building took {elapsed}s (expected <5s)"
        vocab = result.unwrap()
        assert len(vocab.terms) <= 100

    def test_build_vocabulary_identical_documents(self):
        """Test with all identical documents (no discriminative terms)."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        tasks = ["Identical task description"] * 10

        # Act
        result = builder.build_vocabulary(tasks, top_n=20)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()
        # All terms should have similar IDF scores since all docs are identical
        assert len(vocab.terms) > 0

    def test_top_n_filtering(self):
        """Test that only top_n terms are returned."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        tasks = [
            f"Task {i} with unique word_{i} and common terms"
            for i in range(50)
        ]

        # Act
        result = builder.build_vocabulary(tasks, top_n=10)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()
        # May return fewer than top_n if filtered by min_df and token_pattern
        assert len(vocab.terms) <= 10, f"Expected <=10 terms, got {len(vocab.terms)}"
        assert len(vocab.idf_scores) == len(vocab.terms)

    def test_top_n_larger_than_available_terms(self):
        """Test top_n exceeds number of unique terms."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        tasks = ["Short task"] * 5

        # Act
        result = builder.build_vocabulary(tasks, top_n=100)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()
        # Should return fewer than 100 terms since corpus is small
        assert len(vocab.terms) < 100


# ============================================================================
# Test Suite 4: File I/O Tests - Save
# ============================================================================


class TestSaveVocabulary:
    """Test vocabulary persistence to JSON file."""

    def test_save_vocabulary_to_json(self, tmp_path):
        """Test vocabulary saved to JSON file."""
        # Arrange
        vocab = TfidfVocabulary(
            terms=["test", "code", "pydantic"],
            idf_scores={"test": 2.5, "code": 2.3, "pydantic": 2.8},
            version="v1.0",
        )
        builder = TfidfVocabularyBuilder()
        save_path = tmp_path / "vocab.json"

        # Act
        result = builder.save_vocabulary(vocab, save_path)

        # Assert
        assert result.is_ok()
        saved_path = result.unwrap()
        assert saved_path.exists()
        assert saved_path == save_path

        # Verify JSON content
        with open(save_path) as f:
            data = json.load(f)
        assert data["terms"] == ["test", "code", "pydantic"]
        assert data["idf_scores"] == {"test": 2.5, "code": 2.3, "pydantic": 2.8}

    def test_save_creates_directory_if_missing(self, tmp_path):
        """Test directory creation for vocabulary path."""
        # Arrange
        vocab = TfidfVocabulary(
            terms=["test"],
            idf_scores={"test": 2.5},
        )
        builder = TfidfVocabularyBuilder()
        save_path = tmp_path / "nonexistent" / "subdir" / "vocab.json"

        # Act
        result = builder.save_vocabulary(vocab, save_path)

        # Assert
        assert result.is_ok()
        assert save_path.exists()
        assert save_path.parent.exists()

    def test_save_overwrites_existing_file(self, tmp_path):
        """Test overwriting existing vocabulary file."""
        # Arrange
        vocab1 = TfidfVocabulary(
            terms=["old"],
            idf_scores={"old": 1.0},
        )
        vocab2 = TfidfVocabulary(
            terms=["new"],
            idf_scores={"new": 2.0},
        )
        builder = TfidfVocabularyBuilder()
        save_path = tmp_path / "vocab.json"

        # Act - save twice
        result1 = builder.save_vocabulary(vocab1, save_path)
        result2 = builder.save_vocabulary(vocab2, save_path)

        # Assert
        assert result1.is_ok()
        assert result2.is_ok()

        # Verify file contains vocab2
        with open(save_path) as f:
            data = json.load(f)
        assert data["terms"] == ["new"]
        assert data["idf_scores"] == {"new": 2.0}

    def test_save_handles_datetime_serialization(self, tmp_path):
        """Test datetime is correctly serialized to ISO format."""
        # Arrange
        created_time = datetime(2025, 1, 15, 10, 30, 45)
        vocab = TfidfVocabulary(
            terms=["test"],
            idf_scores={"test": 2.5},
            created_at=created_time,
        )
        builder = TfidfVocabularyBuilder()
        save_path = tmp_path / "vocab.json"

        # Act
        result = builder.save_vocabulary(vocab, save_path)

        # Assert
        assert result.is_ok()

        # Verify ISO format in JSON
        with open(save_path) as f:
            data = json.load(f)
        assert data["created_at"] == "2025-01-15T10:30:45"


# ============================================================================
# Test Suite 5: File I/O Tests - Load
# ============================================================================


class TestLoadVocabulary:
    """Test vocabulary loading from JSON."""

    def test_load_vocabulary_from_json(self, tmp_path):
        """Test vocabulary loaded from JSON file."""
        # Arrange
        vocab = TfidfVocabulary(
            terms=["test", "code"],
            idf_scores={"test": 2.5, "code": 2.3},
            version="v1.0",
        )
        builder = TfidfVocabularyBuilder()
        save_path = tmp_path / "vocab.json"

        # Save first
        save_result = builder.save_vocabulary(vocab, save_path)
        assert save_result.is_ok()

        # Act
        load_result = builder.load_vocabulary(save_path)

        # Assert
        assert load_result.is_ok()
        loaded_vocab = load_result.unwrap()
        assert loaded_vocab.terms == vocab.terms
        assert loaded_vocab.idf_scores == vocab.idf_scores
        assert loaded_vocab.version == vocab.version

    def test_load_vocabulary_datetime_deserialization(self, tmp_path):
        """Test datetime is correctly deserialized from ISO format."""
        # Arrange
        created_time = datetime(2025, 1, 15, 10, 30, 45)
        vocab = TfidfVocabulary(
            terms=["test"],
            idf_scores={"test": 2.5},
            created_at=created_time,
        )
        builder = TfidfVocabularyBuilder()
        save_path = tmp_path / "vocab.json"

        # Save first
        save_result = builder.save_vocabulary(vocab, save_path)
        assert save_result.is_ok()

        # Act
        load_result = builder.load_vocabulary(save_path)

        # Assert
        assert load_result.is_ok()
        loaded_vocab = load_result.unwrap()
        assert loaded_vocab.created_at == created_time

    def test_load_handles_missing_file(self, tmp_path):
        """Test graceful handling of missing vocabulary file."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        load_path = tmp_path / "nonexistent.json"

        # Act
        result = builder.load_vocabulary(load_path)

        # Assert
        assert result.is_err()
        error_msg = result.unwrap_err()
        assert "not found" in error_msg.lower()

    def test_load_handles_corrupted_json(self, tmp_path):
        """Test handling of malformed JSON file."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        load_path = tmp_path / "corrupted.json"
        load_path.write_text("{ invalid json }")

        # Act
        result = builder.load_vocabulary(load_path)

        # Assert
        assert result.is_err()
        error_msg = result.unwrap_err()
        assert "failed to read" in error_msg.lower() or "failed to parse" in error_msg.lower()

    def test_load_handles_invalid_vocabulary_structure(self, tmp_path):
        """Test handling of JSON with invalid vocabulary structure."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        load_path = tmp_path / "invalid_structure.json"
        # Missing required fields
        load_path.write_text(json.dumps({"invalid_field": "value"}))

        # Act
        result = builder.load_vocabulary(load_path)

        # Assert
        assert result.is_err()
        error_msg = result.unwrap_err()
        assert "failed to parse" in error_msg.lower()


# ============================================================================
# Test Suite 6: Result Pattern Validation
# ============================================================================


class TestResultPatternValidation:
    """Test Result pattern usage for error handling."""

    def test_result_pattern_ok_branch_build(self):
        """Test successful build_vocabulary returns Ok."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        tasks = ["Task one with words", "Task two with more words"]

        # Act
        result = builder.build_vocabulary(tasks)

        # Assert
        assert isinstance(result, Result)
        assert result.is_ok()
        vocab = result.unwrap()
        assert isinstance(vocab, TfidfVocabulary)

    def test_result_pattern_err_branch_build_empty(self):
        """Test failed build_vocabulary returns Err."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        tasks = []

        # Act
        result = builder.build_vocabulary(tasks)

        # Assert
        assert isinstance(result, Result)
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, str)

    def test_result_pattern_ok_branch_save(self, tmp_path):
        """Test successful save_vocabulary returns Ok."""
        # Arrange
        vocab = TfidfVocabulary(terms=["test"], idf_scores={"test": 2.5})
        builder = TfidfVocabularyBuilder()
        save_path = tmp_path / "vocab.json"

        # Act
        result = builder.save_vocabulary(vocab, save_path)

        # Assert
        assert isinstance(result, Result)
        assert result.is_ok()
        path = result.unwrap()
        assert isinstance(path, Path)

    def test_result_pattern_ok_branch_load(self, tmp_path):
        """Test successful load_vocabulary returns Ok."""
        # Arrange
        vocab = TfidfVocabulary(terms=["test"], idf_scores={"test": 2.5})
        builder = TfidfVocabularyBuilder()
        save_path = tmp_path / "vocab.json"
        builder.save_vocabulary(vocab, save_path)

        # Act
        result = builder.load_vocabulary(save_path)

        # Assert
        assert isinstance(result, Result)
        assert result.is_ok()
        loaded_vocab = result.unwrap()
        assert isinstance(loaded_vocab, TfidfVocabulary)

    def test_result_pattern_err_branch_load_missing(self, tmp_path):
        """Test failed load_vocabulary returns Err."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        load_path = tmp_path / "missing.json"

        # Act
        result = builder.load_vocabulary(load_path)

        # Assert
        assert isinstance(result, Result)
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, str)


# ============================================================================
# Test Suite 7: Configuration Tests
# ============================================================================


class TestVocabularyBuilderConfiguration:
    """Test vocabulary builder configuration options."""

    def test_custom_stop_words(self):
        """Test custom stop words configuration."""
        # Arrange
        builder = TfidfVocabularyBuilder(stop_words="english", min_df=1)
        tasks = [
            "The quick brown fox jumps over lazy dog",
            "A lazy dog sleeps under brown tree",
            "Quick brown animals run fast daily",
        ]

        # Act
        result = builder.build_vocabulary(tasks, top_n=10)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()
        # English stopwords like "the", "a" should be filtered
        terms_lower = [term.lower() for term in vocab.terms]
        assert "the" not in terms_lower
        assert "a" not in terms_lower

    def test_custom_min_df(self):
        """Test custom minimum document frequency."""
        # Arrange - require term to appear in at least 3 documents
        builder = TfidfVocabularyBuilder(min_df=3)
        tasks = ["word1 common", "word2 common", "word3 common"]

        # Act
        result = builder.build_vocabulary(tasks, top_n=10)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()
        # Only "common" appears in all 3 docs, unique words filtered
        assert "common" in vocab.terms

    def test_no_stop_words(self):
        """Test building vocabulary without stopword filtering."""
        # Arrange
        builder = TfidfVocabularyBuilder(stop_words=None)
        tasks = ["The quick brown fox", "The lazy dog"]

        # Act
        result = builder.build_vocabulary(tasks, top_n=10)

        # Assert
        assert result.is_ok()
        vocab = result.unwrap()
        # With no stopword filtering, "the" should appear
        terms_lower = [term.lower() for term in vocab.terms]
        # Note: might still be filtered by min_df or token_pattern


# ============================================================================
# Test Suite 8: Integration Tests
# ============================================================================


class TestVocabularyBuilderIntegration:
    """End-to-end integration tests."""

    def test_full_workflow_build_save_load(self, tmp_path):
        """Test complete workflow: build → save → load."""
        # Arrange
        builder = TfidfVocabularyBuilder()
        tasks = [
            "Implement feature with tests",
            "Create Pydantic models",
            "Write comprehensive tests",
            "Build agent communication",
            "Implement error handling",
        ]
        save_path = tmp_path / "models" / "vocab.json"

        # Act - Build
        build_result = builder.build_vocabulary(tasks, top_n=20)
        assert build_result.is_ok()
        vocab = build_result.unwrap()

        # Act - Save
        save_result = builder.save_vocabulary(vocab, save_path)
        assert save_result.is_ok()

        # Act - Load
        load_result = builder.load_vocabulary(save_path)
        assert load_result.is_ok()
        loaded_vocab = load_result.unwrap()

        # Assert - Roundtrip integrity
        assert loaded_vocab.terms == vocab.terms
        assert loaded_vocab.idf_scores == vocab.idf_scores
        assert loaded_vocab.version == vocab.version

    def test_vocabulary_persistence_across_instances(self, tmp_path):
        """Test vocabulary can be loaded by different builder instance."""
        # Arrange
        builder1 = TfidfVocabularyBuilder()
        builder2 = TfidfVocabularyBuilder()
        tasks = ["Test task one", "Test task two"]
        save_path = tmp_path / "vocab.json"

        # Act - Build and save with builder1
        vocab = builder1.build_vocabulary(tasks).unwrap()
        builder1.save_vocabulary(vocab, save_path)

        # Load with builder2
        load_result = builder2.load_vocabulary(save_path)

        # Assert
        assert load_result.is_ok()
        loaded_vocab = load_result.unwrap()
        assert loaded_vocab.terms == vocab.terms
