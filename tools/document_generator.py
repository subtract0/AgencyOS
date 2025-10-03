"""
Document Generator Tool for Trinity Life Assistant Phase 3.

PURPOSE:
Generate documents (book chapters, outlines, drafts) based on specs and research.
LLM-powered generation with version tracking and template support.

CONSTITUTIONAL REQUIREMENTS:
- Result<T,E> pattern for all operations
- Pydantic models (zero Dict[Any, Any])
- All functions under 50 lines
- Complete type annotations
- Comprehensive docstrings

INTEGRATION:
- Used by ProjectExecutor for background document creation
- Integrates with BudgetEnforcer for cost tracking
- Supports iterative revision based on user feedback
"""

from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

from agency_swarm.tools import BaseTool
from pydantic import BaseModel, Field, field_validator
from shared.type_definitions import Result, Ok, Err


# === Data Models ===

class DocumentType(str, Enum, JSONValue):
    """Types of documents that can be generated."""
    CHAPTER = "chapter"
    OUTLINE = "outline"
    SUMMARY = "summary"
    DRAFT = "draft"
    BOOK = "book"


class ChapterRequest(BaseModel):
    """Request for chapter generation."""
    chapter_number: int = Field(..., description="Chapter number (1-indexed)")
    title: str = Field(..., description="Chapter title")
    context: str = Field(..., description="Book context and background")
    requirements: List[str] = Field(..., description="Requirements (word count, style, etc)")
    style: str = Field(..., description="Writing style (e.g., 'Professional, conversational')")

    @field_validator('chapter_number')
    @classmethod
    def validate_chapter_number(cls, v):
        """Validate chapter number is positive."""
        if v <= 0:
            raise ValueError("Chapter number must be positive")
        return v


class OutlineRequest(BaseModel):
    """Request for outline generation."""
    document_type: DocumentType = Field(..., description="Type of document")
    title: str = Field(..., description="Document title")
    context: str = Field(..., description="Context and target audience")
    num_sections: int = Field(..., description="Number of sections to generate")
    requirements: List[str] = Field(..., description="Specific requirements")

    @field_validator('num_sections')
    @classmethod
    def validate_num_sections(cls, v):
        """Validate number of sections is positive."""
        if v <= 0:
            raise ValueError("Number of sections must be positive")
        return v


class Chapter(BaseModel):
    """Generated chapter."""
    chapter_number: int = Field(..., description="Chapter number")
    title: str = Field(..., description="Chapter title")
    content: str = Field(..., description="Chapter content")
    word_count: int = Field(..., description="Word count")
    metadata: JSONValue = Field(default_factory=dict, description="Additional metadata")


class Outline(BaseModel):
    """Generated outline."""
    title: str = Field(..., description="Outline title")
    document_type: DocumentType = Field(..., description="Document type")
    sections: List[JSONValue] = Field(..., description="Outline sections")
    metadata: JSONValue = Field(default_factory=dict, description="Additional metadata")


class GeneratedDocument(BaseModel):
    """Generic generated document."""
    document_type: DocumentType = Field(..., description="Document type")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    version: int = Field(default=1, description="Document version")
    metadata: JSONValue = Field(default_factory=dict, description="Additional metadata")


class GenerationError(BaseModel):
    """Error during document generation."""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


# === Core Document Generator ===

class DocumentGenerator:
    """
    Generate documents using LLM with template support.

    Supports: chapters, outlines, summaries, drafts.
    Includes version tracking and iterative revision.
    """

    def __init__(self, llm_client) -> None:
        """
        Initialize document generator.

        Args:
            llm_client: LLM client for generation (GPT-5)
        """
        self.llm = llm_client

    def generate_chapter(
        self, request: ChapterRequest
    ) -> Result[Chapter, GenerationError]:
        """
        Generate a book chapter from request.

        Args:
            request: Chapter generation request

        Returns:
            Result containing Chapter or GenerationError
        """
        try:
            # Validate request
            if request.chapter_number <= 0:
                return Err(GenerationError(
                    error_type="ValidationError",
                    message="Chapter number must be positive"
                ))

            # Build prompt from template
            prompt = self._build_chapter_prompt(request)

            # Generate via LLM
            chapter = self.llm.generate(prompt)

            # Validate response
            if not chapter:
                return Err(GenerationError(
                    error_type="GenerationError",
                    message="LLM returned empty response"
                ))

            return Ok(chapter)

        except TimeoutError as e:
            return Err(GenerationError(
                error_type="TimeoutError",
                message=f"Generation timeout: {str(e)}"
            ))
        except Exception as e:
            return Err(GenerationError(
                error_type="UnexpectedError",
                message=str(e)
            ))

    def generate_outline(
        self, request: OutlineRequest
    ) -> Result[Outline, GenerationError]:
        """
        Generate document outline from request.

        Args:
            request: Outline generation request

        Returns:
            Result containing Outline or GenerationError
        """
        try:
            # Build prompt from template
            prompt = self._build_outline_prompt(request)

            # Generate via LLM
            outline = self.llm.generate(prompt)

            if not outline:
                return Err(GenerationError(
                    error_type="GenerationError",
                    message="LLM returned empty response"
                ))

            return Ok(outline)

        except Exception as e:
            return Err(GenerationError(
                error_type="UnexpectedError",
                message=str(e)
            ))

    def revise_document(
        self, document: GeneratedDocument, feedback: str
    ) -> Result[GeneratedDocument, GenerationError]:
        """
        Revise document based on feedback.

        Args:
            document: Original document
            feedback: User feedback for revision

        Returns:
            Result containing revised document or error
        """
        try:
            # Build revision prompt
            prompt = f"""
            Revise the following document based on feedback.

            Original Document:
            Title: {document.title}
            Content:
            {document.content}

            User Feedback:
            {feedback}

            Generate revised version incorporating feedback.
            """

            # Generate revision
            revised = self.llm.generate(prompt)

            if not revised:
                return Err(GenerationError(
                    error_type="GenerationError",
                    message="LLM returned empty response"
                ))

            # Increment version
            revised.version = document.version + 1

            return Ok(revised)

        except Exception as e:
            return Err(GenerationError(
                error_type="UnexpectedError",
                message=str(e)
            ))

    def _build_chapter_prompt(self, request: ChapterRequest) -> str:
        """
        Build chapter generation prompt.

        Args:
            request: Chapter request

        Returns:
            Formatted prompt string
        """
        return f"""
        Generate Chapter {request.chapter_number}: {request.title}

        Context:
        {request.context}

        Requirements:
        {chr(10).join(f"- {req}" for req in request.requirements)}

        Style:
        {request.style}

        Generate complete chapter content.
        """

    def _build_outline_prompt(self, request: OutlineRequest) -> str:
        """
        Build outline generation prompt.

        Args:
            request: Outline request

        Returns:
            Formatted prompt string
        """
        return f"""
        Generate outline for: {request.title}

        Document Type: {request.document_type.value}

        Context:
        {request.context}

        Generate {request.num_sections} sections with:
        - Section number
        - Section title
        - Section summary

        Requirements:
        {chr(10).join(f"- {req}" for req in request.requirements)}
        """


# === Agency Swarm Tool Wrappers ===

class GenerateChapter(BaseTool):  # type: ignore[misc]
    """
    Generate a book chapter using LLM.

    Usage:
    - Requires chapter number, title, context, requirements, style
    - Returns generated chapter with word count
    - Integrates with budget enforcer
    """

    chapter_number: int = Field(..., description="Chapter number (1-indexed)")
    title: str = Field(..., description="Chapter title")
    book_context: str = Field(..., description="Book context and background")
    requirements: List[str] = Field(..., description="Requirements list")
    style: str = Field(..., description="Writing style")

    def run(self):
        """Execute chapter generation."""
        # Create request
        request = ChapterRequest(
            chapter_number=self.chapter_number,
            title=self.title,
            context=self.book_context,
            requirements=self.requirements,
            style=self.style
        )

        # Generate (placeholder - requires real LLM integration)
        generator = DocumentGenerator(llm_client=None)
        result = generator.generate_chapter(request)

        if result.is_ok():
            chapter = result.unwrap()
            return f"Chapter {chapter.chapter_number} generated: {chapter.word_count} words"
        else:
            error = result.unwrap_err()
            return f"Error: {error.message}"


class GenerateOutline(BaseTool):  # type: ignore[misc]
    """
    Generate document outline using LLM.

    Usage:
    - Requires document type, title, context, num_sections
    - Returns structured outline
    """

    document_type: str = Field(..., description="Document type (book, chapter, etc)")
    title: str = Field(..., description="Document title")
    doc_context: str = Field(..., description="Context and target audience")
    num_sections: int = Field(..., description="Number of sections")
    requirements: List[str] = Field(..., description="Requirements list")

    def run(self):
        """Execute outline generation."""
        # Create request
        request = OutlineRequest(
            document_type=DocumentType(self.document_type),
            title=self.title,
            context=self.doc_context,
            num_sections=self.num_sections,
            requirements=self.requirements
        )

        # Generate (placeholder)
        generator = DocumentGenerator(llm_client=None)
        result = generator.generate_outline(request)

        if result.is_ok():
            outline = result.unwrap()
            return f"Outline generated: {len(outline.sections)} sections"
        else:
            error = result.unwrap_err()
            return f"Error: {error.message}"


class ReviseDocument(BaseTool):  # type: ignore[misc]
    """
    Revise document based on feedback.

    Usage:
    - Requires original document and feedback
    - Returns revised version with incremented version number
    """

    document_json: str = Field(..., description="Original document as JSON")
    feedback: str = Field(..., description="User feedback for revision")

    def run(self):
        """Execute document revision."""
        import json

        # Parse document
        try:
            doc_data = json.loads(self.document_json)
            document = GeneratedDocument(**doc_data)
        except Exception as e:
            return f"Error parsing document: {str(e)}"

        # Revise (placeholder)
        generator = DocumentGenerator(llm_client=None)
        result = generator.revise_document(document, self.feedback)

        if result.is_ok():
            revised = result.unwrap()
            return f"Document revised (v{revised.version})"
        else:
            error = result.unwrap_err()
            return f"Error: {error.message}"


# Aliases for Agency Swarm
generate_chapter = GenerateChapter
generate_outline = GenerateOutline
revise_document = ReviseDocument
