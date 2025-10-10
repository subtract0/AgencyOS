"""
Task feature vector model for ML-based task routing.

Provides 1644-dimension feature representation for task complexity classification:
- 1536-dim semantic embedding (OpenAI text-embedding-3-small)
- 100-dim TF-IDF features (keyword importance scores)
- 8-dim metadata features (length, keyword flags, historical data)

Constitutional compliance:
- Article I: Complete context (all 1644 dimensions validated)
- Article II: 100% verification (strict typing, Pydantic validators)
- Article IV: VectorStore integration (feature vectors stored for ML training)
- Article V: Spec-driven (follows spec-005-advanced-pattern-recognition.md)

Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.3
Author: ChiefArchitectAgent
Date: 2025-10-10
"""

from typing import ClassVar

from pydantic import BaseModel, Field, field_validator


class TaskFeatureVector(BaseModel):
    """
    1644-dimension feature vector for ML classification.

    Composition:
    - embedding: 1536-dim semantic representation from text-embedding-3-small
    - tfidf_features: 100-dim keyword importance scores
    - description_length: Character count (metadata 1/8)
    - word_count: Word count (metadata 2/8)
    - has_refactor_keyword: Binary flag for 'refactor' (metadata 3/8)
    - has_test_keyword: Binary flag for 'test' (metadata 4/8)
    - has_async_keyword: Binary flag for 'async' (metadata 5/8)
    - has_fix_keyword: Binary flag for 'fix' (metadata 6/8)
    - estimated_time_seconds: User-provided time estimate (metadata 7/8)
    - historical_tier_mode: Most common tier for similar tasks (metadata 8/8)

    Total dimensions: 1536 + 100 + 8 = 1644

    Constitutional Alignment:
    - Article I: All 1644 dimensions validated before classification
    - Article II: Strict typing, no Dict[Any, Any] (Result pattern philosophy)
    - Article IV: Feature vectors stored in VectorStore for ML training

    Example:
        >>> vector = TaskFeatureVector(
        ...     embedding=[0.023, -0.045, ...],  # 1536 floats
        ...     tfidf_features=[0.12, 0.0, 0.08, ...],  # 100 floats
        ...     description_length=120,
        ...     word_count=20,
        ...     has_refactor_keyword=1,
        ...     has_test_keyword=0,
        ...     has_async_keyword=1,
        ...     has_fix_keyword=0,
        ...     estimated_time_seconds=300.0,
        ...     historical_tier_mode=2  # complex
        ... )
    """

    # Dimension constants
    EMBEDDING_DIM: ClassVar[int] = 1536
    TFIDF_DIM: ClassVar[int] = 100
    METADATA_DIM: ClassVar[int] = 8
    TOTAL_DIM: ClassVar[int] = 1644  # 1536 + 100 + 8

    # Semantic Features (1536-dim)
    embedding: list[float] = Field(
        ...,
        description=(
            "Task description embedding from OpenAI text-embedding-3-small. "
            "Captures semantic meaning of task description for similarity matching. "
            "Must be exactly 1536 dimensions (Article II: strict validation)."
        ),
    )

    # TF-IDF Features (100-dim)
    tfidf_features: list[float] = Field(
        ...,
        description=(
            "TF-IDF scores for top 100 keywords from historical tasks. "
            "Keywords include: 'refactor', 'async', 'test', 'fix', 'optimize', etc. "
            "Each score ranges from 0.0 (keyword absent) to 1.0 (high importance). "
            "Must be exactly 100 dimensions for ML model compatibility."
        ),
    )

    # Metadata Features (8-dim)
    description_length: int = Field(
        ...,
        ge=0,
        description=(
            "Character count of task description (metadata feature 1/8). "
            "Used to distinguish simple (short) vs complex (long) tasks. "
            "Range: 0-10000+ characters."
        ),
    )

    word_count: int = Field(
        ...,
        ge=0,
        description=(
            "Word count of task description (metadata feature 2/8). "
            "Calculated by splitting on whitespace. "
            "Range: 0-2000+ words."
        ),
    )

    has_refactor_keyword: int = Field(
        ...,
        ge=0,
        le=1,
        description=(
            "Binary flag: 'refactor' keyword present in description (metadata 3/8). "
            "1 = contains 'refactor', 0 = does not contain. "
            "Refactor tasks typically P2 (moderate) or P3 (simple)."
        ),
    )

    has_test_keyword: int = Field(
        ...,
        ge=0,
        le=1,
        description=(
            "Binary flag: 'test' keyword present in description (metadata 4/8). "
            "1 = contains 'test', 0 = does not contain. "
            "Test-related tasks typically P3 (simple) unless integration tests."
        ),
    )

    has_async_keyword: int = Field(
        ...,
        ge=0,
        le=1,
        description=(
            "Binary flag: 'async' keyword present in description (metadata 5/8). "
            "1 = contains 'async', 0 = does not contain. "
            "Async tasks typically P2 (moderate) due to concurrency complexity."
        ),
    )

    has_fix_keyword: int = Field(
        ...,
        ge=0,
        le=1,
        description=(
            "Binary flag: 'fix' keyword present in description (metadata 6/8). "
            "1 = contains 'fix', 0 = does not contain. "
            "Fix tasks range from P3 (typo fix) to P2 (bug fix)."
        ),
    )

    estimated_time_seconds: float = Field(
        ...,
        ge=0.0,
        description=(
            "User-provided time estimate in seconds (metadata 7/8). "
            "0.0 if no estimate provided. Longer estimates correlate with P1/P2 complexity. "
            "Range: 0-36000 (0-10 hours)."
        ),
    )

    historical_tier_mode: int = Field(
        ...,
        ge=0,
        le=2,
        description=(
            "Most common tier for similar tasks from VectorStore (metadata 8/8). "
            "0 = simple (P3), 1 = moderate (P2), 2 = complex (P1). "
            "Computed from historical classifications (Article IV learning). "
            "Default to 0 if no historical data available."
        ),
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "embedding": [0.023, -0.045, 0.012, 0.089, -0.034] + [0.0] * 1531,  # 1536 floats
                "tfidf_features": [0.12, 0.0, 0.08, 0.05, 0.0, 0.03] + [0.0] * 94,  # 100 floats
                "description_length": 120,
                "word_count": 20,
                "has_refactor_keyword": 1,
                "has_test_keyword": 0,
                "has_async_keyword": 1,
                "has_fix_keyword": 0,
                "estimated_time_seconds": 300.0,
                "historical_tier_mode": 2,
            },
            "description": (
                "TaskFeatureVector: 1644-dimension ML feature representation. "
                "Used by scikit-learn RandomForest classifier for task complexity prediction. "
                "Constitutional compliance: Article II (strict typing), Article IV (VectorStore learning)."
            ),
        }

    @field_validator("embedding")
    @classmethod
    def validate_embedding_dimension(cls, v: list[float]) -> list[float]:
        """
        Validate embedding dimension is exactly 1536.

        Article II compliance: 100% verification before classification.

        Args:
            v: Embedding vector to validate

        Returns:
            Validated embedding vector

        Raises:
            ValueError: If dimension mismatch detected
        """
        if len(v) != cls.EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: expected {cls.EMBEDDING_DIM}, got {len(v)}. "
                f"Article II violation: Incomplete context for ML classification."
            )
        return v

    @field_validator("tfidf_features")
    @classmethod
    def validate_tfidf_dimension(cls, v: list[float]) -> list[float]:
        """
        Validate TF-IDF dimension is exactly 100.

        Article II compliance: 100% verification before classification.

        Args:
            v: TF-IDF feature vector to validate

        Returns:
            Validated TF-IDF vector

        Raises:
            ValueError: If dimension mismatch detected
        """
        if len(v) != cls.TFIDF_DIM:
            raise ValueError(
                f"TF-IDF dimension mismatch: expected {cls.TFIDF_DIM}, got {len(v)}. "
                f"Article II violation: Incomplete feature extraction."
            )
        return v

    @field_validator(
        "has_refactor_keyword", "has_test_keyword", "has_async_keyword", "has_fix_keyword"
    )
    @classmethod
    def validate_binary_flags(cls, v: int) -> int:
        """
        Validate binary flags are 0 or 1.

        Article II compliance: Strict typing for ML model input.

        Args:
            v: Binary flag value to validate

        Returns:
            Validated binary flag (0 or 1)

        Raises:
            ValueError: If value is not 0 or 1
        """
        if v not in (0, 1):
            raise ValueError(
                f"Binary flag must be 0 or 1, got {v}. Article II violation: Invalid feature value."
            )
        return v

    @field_validator("historical_tier_mode")
    @classmethod
    def validate_tier_mode(cls, v: int) -> int:
        """
        Validate historical tier mode is 0, 1, or 2.

        Article IV compliance: VectorStore learning encodes tiers as integers.
        0 = simple (P3), 1 = moderate (P2), 2 = complex (P1)

        Args:
            v: Historical tier mode to validate

        Returns:
            Validated tier mode (0, 1, or 2)

        Raises:
            ValueError: If value is not 0, 1, or 2
        """
        if v not in (0, 1, 2):
            raise ValueError(
                f"Historical tier mode must be 0 (simple), 1 (moderate), or 2 (complex), got {v}. "
                f"Article IV violation: Invalid VectorStore learning tier."
            )
        return v

    def to_flat_array(self) -> list[float]:
        """
        Convert TaskFeatureVector to flat 1644-dimension array for ML model input.

        Used by scikit-learn RandomForest classifier during inference.

        Returns:
            Flattened feature array (1644 dimensions)

        Example:
            >>> vector = TaskFeatureVector(...)
            >>> X = vector.to_flat_array()
            >>> len(X)
            1644
            >>> model.predict([X])  # scikit-learn input format
        """
        return (
            self.embedding  # 1536 dimensions
            + self.tfidf_features  # 100 dimensions
            + [
                float(self.description_length),  # metadata 1/8
                float(self.word_count),  # metadata 2/8
                float(self.has_refactor_keyword),  # metadata 3/8
                float(self.has_test_keyword),  # metadata 4/8
                float(self.has_async_keyword),  # metadata 5/8
                float(self.has_fix_keyword),  # metadata 6/8
                float(self.estimated_time_seconds),  # metadata 7/8
                float(self.historical_tier_mode),  # metadata 8/8
            ]
        )

    def get_total_dimensions(self) -> int:
        """
        Get total dimension count for validation.

        Returns:
            Total dimensions (1644)

        Example:
            >>> vector = TaskFeatureVector(...)
            >>> vector.get_total_dimensions()
            1644
        """
        return self.TOTAL_DIM

    def get_dimension_breakdown(self) -> dict[str, int]:
        """
        Get dimension breakdown for debugging.

        Returns:
            Dictionary with dimension counts per feature type

        Example:
            >>> vector = TaskFeatureVector(...)
            >>> vector.get_dimension_breakdown()
            {'embedding': 1536, 'tfidf': 100, 'metadata': 8, 'total': 1644}
        """
        return {
            "embedding": self.EMBEDDING_DIM,
            "tfidf": self.TFIDF_DIM,
            "metadata": self.METADATA_DIM,
            "total": self.TOTAL_DIM,
        }
