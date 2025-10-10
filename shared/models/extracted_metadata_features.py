"""
ExtractedMetadataFeatures Pydantic model for feature extractor metadata output.

Constitutional compliance:
- Article II: Strict typing (Law #2) - replaces dict[str, Any]
- Article IV: Structured feature data for ML pipeline

Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.3
Author: QualityEnforcer
Date: 2025-10-10
"""

from pydantic import BaseModel, Field


class ExtractedMetadataFeatures(BaseModel):
    """
    8-dimensional metadata features extracted from task description.

    Output from FeatureExtractor._extract_metadata(), used to build
    TaskFeatureVector (1644-dim = 1536 embedding + 100 TF-IDF + 8 metadata).

    Fields (8 dimensions):
        description_length: Character count of task description
        word_count: Word count of task description
        has_refactor_keyword: Binary flag (1 if "refactor" in description)
        has_test_keyword: Binary flag (1 if "test" in description)
        has_async_keyword: Binary flag (1 if "async" in description)
        has_fix_keyword: Binary flag (1 if "fix" in description)
        estimated_time_seconds: User-provided time estimate
        historical_tier_mode: Most common historical tier

    Constitutional Compliance:
        Article II: Strict typing (replaces dict[str, Any])
        Article IV: Structured ML feature data

    Example:
        >>> features = ExtractedMetadataFeatures(
        ...     description_length=45,
        ...     word_count=8,
        ...     has_refactor_keyword=1,
        ...     has_test_keyword=0,
        ...     has_async_keyword=0,
        ...     has_fix_keyword=0,
        ...     estimated_time_seconds=1800.0,
        ...     historical_tier_mode=2
        ... )
    """

    description_length: int = Field(
        ...,
        ge=0,
        description="Character count of task description",
    )

    word_count: int = Field(
        ...,
        ge=0,
        description="Word count of task description",
    )

    has_refactor_keyword: int = Field(
        ...,
        ge=0,
        le=1,
        description="Binary flag: 1 if 'refactor' in description, else 0",
    )

    has_test_keyword: int = Field(
        ...,
        ge=0,
        le=1,
        description="Binary flag: 1 if 'test' in description, else 0",
    )

    has_async_keyword: int = Field(
        ...,
        ge=0,
        le=1,
        description="Binary flag: 1 if 'async' in description, else 0",
    )

    has_fix_keyword: int = Field(
        ...,
        ge=0,
        le=1,
        description="Binary flag: 1 if 'fix' in description, else 0",
    )

    estimated_time_seconds: float = Field(
        ...,
        ge=0.0,
        description="User-estimated task duration in seconds",
    )

    historical_tier_mode: int = Field(
        ...,
        ge=0,
        le=3,
        description="Most common historical tier (0=unknown, 1-3=tier)",
    )
