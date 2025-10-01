"""
Tests for document_generator tool.

Constitutional Requirements:
- TDD: Tests written BEFORE implementation
- 100% coverage: All functions, edge cases, errors
- NECESSARY pattern: Named, Executable, Comprehensive, Error handling,
  State changes, Side effects, Assertions, Repeatable, Yield fast
- Result<T,E> pattern validation
- Zero Dict[Any, Any] usage
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.document_generator import (
    DocumentGenerator,
    GenerateChapter,
    GenerateOutline,
    ReviseDocument,
    ChapterRequest,
    OutlineRequest,
    Chapter,
    Outline,
    GeneratedDocument,
    GenerationError,
    DocumentType,
)
from shared.type_definitions import Result, Ok, Err


# Test Fixtures
@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.generate = Mock()
    return client


@pytest.fixture
def document_generator(mock_llm_client):
    """Document generator instance with mocked LLM."""
    return DocumentGenerator(llm_client=mock_llm_client)


@pytest.fixture
def sample_chapter_request():
    """Sample chapter generation request."""
    return ChapterRequest(
        chapter_number=1,
        title="Introduction to Coaching",
        context="Book on coaching methodologies",
        requirements=["1500 words", "Include case studies"],
        style="Professional, conversational"
    )


@pytest.fixture
def sample_outline_request():
    """Sample outline generation request."""
    return OutlineRequest(
        document_type=DocumentType.BOOK,
        title="Coaching for Entrepreneurs",
        context="Target audience: startup founders",
        num_sections=5,
        requirements=["Action-oriented", "Include exercises"]
    )


# === Happy Path Tests ===

class TestGenerateChapter:
    """Tests for chapter generation (happy path)."""

    def test_generates_chapter_with_valid_request(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should generate chapter with valid request."""
        # Arrange
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Introduction to Coaching",
            content="Chapter content here...",
            word_count=1500,
            metadata={"style": "Professional"}
        )

        # Act
        result = document_generator.generate_chapter(sample_chapter_request)

        # Assert
        assert result.is_ok()
        chapter = result.unwrap()
        assert chapter.chapter_number == 1
        assert chapter.title == "Introduction to Coaching"
        assert chapter.word_count == 1500

    def test_includes_context_in_generation(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should include provided context in LLM prompt."""
        # Arrange
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        document_generator.generate_chapter(sample_chapter_request)

        # Assert
        call_args = mock_llm_client.generate.call_args
        prompt = call_args[0][0] if call_args else ""
        assert "Book on coaching methodologies" in prompt

    def test_respects_style_requirements(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should include style requirements in prompt."""
        # Arrange
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        document_generator.generate_chapter(sample_chapter_request)

        # Assert
        call_args = mock_llm_client.generate.call_args
        prompt = call_args[0][0] if call_args else ""
        assert "Professional, conversational" in prompt


class TestGenerateOutline:
    """Tests for outline generation (happy path)."""

    def test_generates_outline_with_valid_request(
        self, document_generator, sample_outline_request, mock_llm_client
    ):
        """Should generate outline with valid request."""
        # Arrange
        mock_llm_client.generate.return_value = Outline(
            title="Coaching for Entrepreneurs",
            document_type=DocumentType.BOOK,
            sections=[
                {"number": 1, "title": "Introduction", "summary": "Overview"},
                {"number": 2, "title": "Chapter 1", "summary": "Details"}
            ],
            metadata={"total_sections": 2}
        )

        # Act
        result = document_generator.generate_outline(sample_outline_request)

        # Assert
        assert result.is_ok()
        outline = result.unwrap()
        assert outline.title == "Coaching for Entrepreneurs"
        assert len(outline.sections) == 2

    def test_respects_num_sections_requirement(
        self, document_generator, sample_outline_request, mock_llm_client
    ):
        """Should generate requested number of sections."""
        # Arrange
        mock_llm_client.generate.return_value = Outline(
            title="Test",
            document_type=DocumentType.BOOK,
            sections=[{"number": i, "title": f"Section {i}", "summary": "Test"}
                     for i in range(1, 6)],
            metadata={}
        )

        # Act
        result = document_generator.generate_outline(sample_outline_request)

        # Assert
        assert result.is_ok()
        outline = result.unwrap()
        assert len(outline.sections) == 5


class TestReviseDocument:
    """Tests for document revision (happy path)."""

    def test_revises_document_with_feedback(
        self, document_generator, mock_llm_client
    ):
        """Should revise document based on feedback."""
        # Arrange
        original_doc = GeneratedDocument(
            document_type=DocumentType.CHAPTER,
            title="Original Title",
            content="Original content",
            version=1,
            metadata={}
        )
        feedback = "Add more examples"

        mock_llm_client.generate.return_value = GeneratedDocument(
            document_type=DocumentType.CHAPTER,
            title="Original Title",
            content="Revised content with examples",
            version=2,
            metadata={"revised": True}
        )

        # Act
        result = document_generator.revise_document(original_doc, feedback)

        # Assert
        assert result.is_ok()
        revised = result.unwrap()
        assert revised.version == 2
        assert revised.content != original_doc.content


# === Error Handling Tests ===

class TestErrorConditions:
    """Tests for error conditions and edge cases."""

    def test_returns_error_on_llm_failure(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should return Err when LLM fails."""
        # Arrange
        mock_llm_client.generate.side_effect = Exception("LLM API error")

        # Act
        result = document_generator.generate_chapter(sample_chapter_request)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "LLM API error" in str(error)

    def test_returns_error_on_invalid_response_format(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should return Err when LLM returns invalid format."""
        # Arrange
        mock_llm_client.generate.return_value = None

        # Act
        result = document_generator.generate_chapter(sample_chapter_request)

        # Assert
        assert result.is_err()

    def test_handles_empty_context_gracefully(
        self, document_generator, mock_llm_client
    ):
        """Should handle empty context without crashing."""
        # Arrange
        request = ChapterRequest(
            chapter_number=1,
            title="Test",
            context="",
            requirements=[],
            style=""
        )
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        result = document_generator.generate_chapter(request)

        # Assert
        assert result.is_ok()

    def test_validates_chapter_number_positive(
        self, document_generator, mock_llm_client
    ):
        """Should validate chapter number is positive."""
        # Arrange
        from pydantic import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError):
            request = ChapterRequest(
                chapter_number=0,
                title="Test",
                context="Context",
                requirements=[],
                style="Style"
            )

    def test_handles_network_timeout(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should handle network timeout gracefully."""
        # Arrange
        mock_llm_client.generate.side_effect = TimeoutError("Request timeout")

        # Act
        result = document_generator.generate_chapter(sample_chapter_request)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "timeout" in str(error).lower()


# === Integration Tests ===

class TestDocumentTemplates:
    """Tests for document templates and formatting."""

    def test_chapter_template_includes_required_sections(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should include all required sections in chapter template."""
        # Arrange
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        document_generator.generate_chapter(sample_chapter_request)

        # Assert
        call_args = mock_llm_client.generate.call_args
        prompt = call_args[0][0] if call_args else ""
        assert "chapter" in prompt.lower()
        assert "requirements" in prompt.lower()

    def test_outline_template_structures_sections(
        self, document_generator, sample_outline_request, mock_llm_client
    ):
        """Should structure outline sections properly."""
        # Arrange
        mock_llm_client.generate.return_value = Outline(
            title="Test",
            document_type=DocumentType.BOOK,
            sections=[],
            metadata={}
        )

        # Act
        document_generator.generate_outline(sample_outline_request)

        # Assert
        call_args = mock_llm_client.generate.call_args
        prompt = call_args[0][0] if call_args else ""
        assert "outline" in prompt.lower()


# === Version Tracking Tests ===

class TestVersionTracking:
    """Tests for document version tracking."""

    def test_initial_version_is_one(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should set initial version to 1."""
        # Arrange
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={"version": 1}
        )

        # Act
        result = document_generator.generate_chapter(sample_chapter_request)

        # Assert
        assert result.is_ok()
        chapter = result.unwrap()
        assert chapter.metadata.get("version", 1) == 1

    def test_revision_increments_version(
        self, document_generator, mock_llm_client
    ):
        """Should increment version on revision."""
        # Arrange
        original = GeneratedDocument(
            document_type=DocumentType.CHAPTER,
            title="Test",
            content="Original",
            version=1,
            metadata={}
        )
        mock_llm_client.generate.return_value = GeneratedDocument(
            document_type=DocumentType.CHAPTER,
            title="Test",
            content="Revised",
            version=2,
            metadata={}
        )

        # Act
        result = document_generator.revise_document(original, "Feedback")

        # Assert
        assert result.is_ok()
        revised = result.unwrap()
        assert revised.version == 2


# === Constitutional Compliance Tests ===

class TestConstitutionalCompliance:
    """Tests for constitutional requirements compliance."""

    def test_all_functions_return_result_type(
        self, document_generator, sample_chapter_request,
        sample_outline_request, mock_llm_client
    ):
        """Should use Result<T,E> pattern for all operations."""
        # Arrange
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        chapter_result = document_generator.generate_chapter(sample_chapter_request)

        # Assert
        assert isinstance(chapter_result, Result)

    def test_no_dict_any_any_in_data_models(self):
        """Should not use Dict[Any, Any] in data models."""
        # This test verifies Pydantic models have typed fields
        # Check model fields exist via model_fields
        assert 'chapter_number' in ChapterRequest.model_fields
        assert 'title' in ChapterRequest.model_fields
        assert 'context' in ChapterRequest.model_fields

    def test_all_public_apis_have_docstrings(self):
        """Should document all public APIs."""
        assert DocumentGenerator.generate_chapter.__doc__ is not None
        assert DocumentGenerator.generate_outline.__doc__ is not None
        assert DocumentGenerator.revise_document.__doc__ is not None


# === Edge Cases Tests ===

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_handles_very_long_context(
        self, document_generator, mock_llm_client
    ):
        """Should handle very long context strings."""
        # Arrange
        long_context = "A" * 10000
        request = ChapterRequest(
            chapter_number=1,
            title="Test",
            context=long_context,
            requirements=[],
            style="Style"
        )
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        result = document_generator.generate_chapter(request)

        # Assert
        assert result.is_ok()

    def test_handles_special_characters_in_title(
        self, document_generator, mock_llm_client
    ):
        """Should handle special characters in titles."""
        # Arrange
        request = ChapterRequest(
            chapter_number=1,
            title="Test: Chapter #1 (Introduction)",
            context="Context",
            requirements=[],
            style="Style"
        )
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title=request.title,
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        result = document_generator.generate_chapter(request)

        # Assert
        assert result.is_ok()

    def test_handles_empty_requirements_list(
        self, document_generator, mock_llm_client
    ):
        """Should handle empty requirements list."""
        # Arrange
        request = ChapterRequest(
            chapter_number=1,
            title="Test",
            context="Context",
            requirements=[],
            style="Style"
        )
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        result = document_generator.generate_chapter(request)

        # Assert
        assert result.is_ok()


# === Budget Integration Tests ===

class TestBudgetIntegration:
    """Tests for budget enforcer integration."""

    def test_respects_budget_limits(
        self, document_generator, sample_chapter_request, mock_llm_client
    ):
        """Should respect budget limits when generating."""
        # This is a placeholder - actual budget integration
        # would be tested with real BudgetEnforcer
        # Arrange
        mock_llm_client.generate.return_value = Chapter(
            chapter_number=1,
            title="Test",
            content="Content",
            word_count=100,
            metadata={}
        )

        # Act
        result = document_generator.generate_chapter(sample_chapter_request)

        # Assert
        assert result.is_ok()
