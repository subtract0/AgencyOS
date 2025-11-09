"""
TDD Tests for Reddit Pain Point Pattern Configuration Loader

Constitutional Compliance:
- Article II (TDD): Tests written BEFORE implementation
- Article II (Types): Pydantic models, no Dict[Any, Any]
- Article II (Result): Result<T,E> pattern for error handling

NECESSARY Pattern Coverage:
- N: Normal operation (valid YAML loads)
- E: Edge cases (empty arrays, boundary values)
- C: Corner cases (malformed data structures)
- E: Error conditions (missing files, invalid YAML)
- S: Security (path traversal, injection)
- S: Stability (corrupt YAML, network failures)
- A: Accessibility (API usability)
- R: Regression (schema changes)
- Y: Yield (output validation)

Created: 2025-11-09
Status: RED PHASE (tests should FAIL - no implementation yet)
"""

import os
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import BaseModel, ValidationError

from shared.config_loader import (
    ConfigError,
    ConfigInvalidError,
    ConfigNotFoundError,
    ConfigSchemaError,
    ConfigSecurityError,
    IntegrationConfig,
    MemoryToolConfig,
    OvernightWorkerConfig,
    PatternCategory,
    QualityFilters,
    RedditPatternConfig,
    RedditPatternConfigLoader,
    TopicConfig,
    VectorStoreConfig,
)
from shared.type_definitions.result import Err, Ok, Result


# =============================================================================
# FIXTURES (Test Data Setup)
# =============================================================================


@pytest.fixture
def valid_config_path() -> str:
    """Path to actual valid configuration file."""
    return "/Users/am/Code/AgencyOS/config/knowledge_ingest/reddit_pain_point_patterns.yaml"


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Temporary directory for test configurations."""
    config_dir = tmp_path / "config" / "knowledge_ingest"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def valid_config_data() -> dict[str, Any]:
    """Valid configuration data structure."""
    return {
        "patterns": {
            "experience_markers": {
                "description": "First-person experiences",
                "keywords": ["I think", "I feel", "I was"],
                "usage": "Filter for posts",
                "weight": 1.0,
            },
            "pain_signals": {
                "description": "Pain indicators",
                "keywords": ["struggles", "problems", "issues"],
                "usage": "Primary extraction",
                "weight": 1.5,
            },
        },
        "reddit_search_template": '"{topic}" site:reddit.com',
        "topics": {
            "acim": {
                "subreddits": ["r/ACIM", "r/spirituality"],
                "additional_keywords": ["forgiveness", "miracle"],
                "extraction_focus": ["practice_difficulties"],
            },
            "co_parenting": {
                "subreddits": ["r/coparenting", "r/Parenting"],
                "additional_keywords": ["custody", "visitation"],
                "extraction_focus": ["communication_issues"],
            },
            "conscious_uncoupling": {
                "subreddits": ["r/Divorce", "r/BreakUps"],
                "additional_keywords": ["ending relationship", "peaceful divorce"],
                "extraction_focus": ["emotional_processing"],
            },
            "open_relationships": {
                "subreddits": ["r/polyamory", "r/nonmonogamy"],
                "additional_keywords": ["ethical non-monogamy", "jealousy"],
                "extraction_focus": ["jealousy_management"],
            },
            "love_and_forgiveness": {
                "subreddits": ["r/selfimprovement", "r/DecidingToBeBetter"],
                "additional_keywords": ["letting go", "healing from hurt"],
                "extraction_focus": ["self_forgiveness"],
            },
        },
        "integration": {
            "vectorstore": {
                "enabled": True,
                "tags_format": ["topic:{topic}", "source:reddit"],
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            },
            "memory_tool": {
                "enabled": True,
                "path": "~/.agency/memories/coaching/{topic}/",
                "format": "markdown",
            },
            "overnight_worker": {
                "enabled": True,
                "schedule": "nightly",
                "max_posts_per_topic": 20,
                "rate_limit_seconds": 2,
            },
        },
        "quality_filters": {
            "min_upvotes": 5,
            "min_comment_length": 100,
            "exclude_patterns": ["[deleted]", "spam"],
            "sentiment_threshold": -0.3,
            "authenticity_score_min": 0.6,
        },
    }


@pytest.fixture
def malformed_yaml_content() -> str:
    """Invalid YAML content for error testing."""
    return """
patterns:
  experience_markers:
    description: "Test"
    keywords: [unclosed array
    weight: 1.0
"""


@pytest.fixture
def empty_patterns_config() -> dict[str, Any]:
    """Configuration with empty pattern arrays (edge case)."""
    return {
        "patterns": {
            "experience_markers": {
                "description": "Empty patterns",
                "keywords": [],  # EMPTY - should fail validation
                "usage": "Test empty",
                "weight": 1.0,
            },
        },
        "reddit_search_template": "test",
        "topics": {},
        "integration": {
            "vectorstore": {"enabled": False, "tags_format": [], "embedding_model": "test"},
            "memory_tool": {"enabled": False, "path": "test", "format": "markdown"},
            "overnight_worker": {
                "enabled": False,
                "schedule": "never",
                "max_posts_per_topic": 0,
                "rate_limit_seconds": 0,
            },
        },
        "quality_filters": {
            "min_upvotes": 0,
            "min_comment_length": 0,
            "exclude_patterns": [],
            "sentiment_threshold": 0.0,
            "authenticity_score_min": 0.0,
        },
    }


# =============================================================================
# NECESSARY PATTERN: NORMAL OPERATION TESTS
# =============================================================================


def test_load_valid_config_file_success(valid_config_path: str) -> None:
    """
    N-NORMAL: Load valid configuration file successfully.

    AAA Pattern:
        Arrange: Valid config file exists
        Act: Load configuration
        Assert: Returns Ok(RedditPatternConfig)

    Expected: FAIL (NotImplementedError - no implementation yet)
    """
    # Arrange: Config file exists at valid_config_path

    # Act
    result = RedditPatternConfigLoader.load_config(valid_config_path)

    # Assert
    assert result.is_ok(), f"Expected Ok, got Err: {result.error if result.is_err() else None}"
    config = result.unwrap()
    assert isinstance(config, RedditPatternConfig)
    assert len(config.patterns) == 3  # experience_markers, pain_signals, emotional_depth
    assert len(config.topics) == 5  # acim, open_relationships, etc.


def test_pydantic_model_validates_all_topics(valid_config_data: dict[str, Any]) -> None:
    """
    N-NORMAL: Pydantic models validate all 5 topic configurations.

    Expected: FAIL (model validation not yet complete)
    """
    # Arrange
    loader = RedditPatternConfigLoader()

    # Act
    result = loader.load_config(valid_config_data)

    # Assert
    assert result.is_ok()
    config = result.unwrap()
    assert "acim" in config.topics
    assert "co_parenting" in config.topics
    assert "conscious_uncoupling" in config.topics
    assert "open_relationships" in config.topics
    assert "love_and_forgiveness" in config.topics


def test_pattern_categories_have_required_fields(valid_config_data: dict[str, Any]) -> None:
    """
    N-NORMAL: All pattern categories have required fields (description, keywords, usage, weight).

    Expected: FAIL (validation not implemented)
    """
    # Arrange
    loader = RedditPatternConfigLoader()

    # Act
    result = loader.validate_patterns(valid_config_data["patterns"])

    # Assert
    assert result.is_ok()
    patterns = result.unwrap()
    for category_name, category in patterns.items():
        assert category.description, f"{category_name} missing description"
        assert len(category.keywords) > 0, f"{category_name} has empty keywords"
        assert category.usage, f"{category_name} missing usage"
        assert category.weight > 0, f"{category_name} has invalid weight"


# =============================================================================
# NECESSARY PATTERN: EDGE CASE TESTS
# =============================================================================


def test_empty_keyword_array_raises_validation_error(
    empty_patterns_config: dict[str, Any]
) -> None:
    """
    E-EDGE: Empty keyword arrays should fail validation.

    Expected: FAIL (validation not yet enforced)
    """
    # Arrange
    loader = RedditPatternConfigLoader()

    # Act
    result = loader.validate_patterns(empty_patterns_config["patterns"])

    # Assert
    assert result.is_err(), "Empty keyword array should fail validation"
    assert isinstance(result.unwrap_err(), ConfigSchemaError)
    assert "keywords" in str(result.unwrap_err()).lower()


def test_zero_weight_pattern_fails_validation(temp_config_dir: Path) -> None:
    """
    E-EDGE: Pattern with weight=0 should fail validation.

    Expected: FAIL (boundary validation not implemented)
    """
    # Arrange
    config_data = {
        "patterns": {
            "test_pattern": {
                "description": "Test",
                "keywords": ["test"],
                "usage": "test",
                "weight": 0.0,  # INVALID - weight must be > 0
            }
        }
    }
    config_path = temp_config_dir / "zero_weight.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    # Act
    result = RedditPatternConfigLoader.load_config(str(config_path))

    # Assert
    assert result.is_err()
    assert "weight" in str(result.unwrap_err()).lower()


def test_negative_sentiment_threshold_allowed(valid_config_data: dict[str, Any]) -> None:
    """
    E-EDGE: Negative sentiment threshold is valid (pain points are negative).

    Expected: FAIL (edge case not handled)
    """
    # Arrange
    loader = RedditPatternConfigLoader()

    # Act
    result = loader.load_config(valid_config_data)

    # Assert
    assert result.is_ok()
    config = result.unwrap()
    assert config.quality_filters.sentiment_threshold == -0.3


# =============================================================================
# NECESSARY PATTERN: CORNER CASE TESTS
# =============================================================================


def test_duplicate_topic_keys_handled_gracefully(temp_config_dir: Path) -> None:
    """
    C-CORNER: Duplicate topic keys in YAML handled gracefully.

    YAML allows duplicate keys (last wins) - ensure this is documented.

    Expected: FAIL (corner case not tested)
    """
    # Arrange
    yaml_content = """
patterns:
  test_pattern:
    description: "Test"
    keywords: ["test"]
    usage: "test"
    weight: 1.0
reddit_search_template: "test"
topics:
  acim:
    subreddits: ["r/ACIM"]
    additional_keywords: ["first"]
    extraction_focus: ["first"]
  acim:  # DUPLICATE KEY
    subreddits: ["r/spirituality"]
    additional_keywords: ["second"]
    extraction_focus: ["second"]
integration:
  vectorstore:
    enabled: false
    tags_format: []
    embedding_model: "test"
  memory_tool:
    enabled: false
    path: "test"
    format: "markdown"
  overnight_worker:
    enabled: false
    schedule: "never"
    max_posts_per_topic: 0
    rate_limit_seconds: 0
quality_filters:
  min_upvotes: 0
  min_comment_length: 0
  exclude_patterns: []
  sentiment_threshold: 0.0
  authenticity_score_min: 0.0
"""
    config_path = temp_config_dir / "duplicate_keys.yaml"
    config_path.write_text(yaml_content)

    # Act
    result = RedditPatternConfigLoader.load_config(str(config_path))

    # Assert - YAML parser takes last value by default
    assert result.is_ok()
    config = result.unwrap()
    assert config.topics["acim"].additional_keywords == ["second"]


def test_missing_optional_integration_sections(temp_config_dir: Path) -> None:
    """
    C-CORNER: Missing optional integration sections use defaults.

    Expected: FAIL (default handling not implemented)
    """
    # Arrange
    minimal_config = {
        "patterns": {
            "test": {
                "description": "Test",
                "keywords": ["test"],
                "usage": "test",
                "weight": 1.0,
            }
        },
        "reddit_search_template": "test",
        "topics": {},
        # Missing integration and quality_filters sections
    }
    config_path = temp_config_dir / "minimal.yaml"
    with open(config_path, "w") as f:
        yaml.dump(minimal_config, f)

    # Act
    result = RedditPatternConfigLoader.load_config(str(config_path))

    # Assert
    assert result.is_err()  # Should fail if required sections missing
    assert isinstance(result.unwrap_err(), ConfigSchemaError)


# =============================================================================
# NECESSARY PATTERN: ERROR CONDITION TESTS
# =============================================================================


def test_missing_config_file_returns_error(temp_config_dir: Path) -> None:
    """
    E-ERROR: Missing configuration file returns ConfigNotFoundError.

    Expected: FAIL (error handling not implemented)
    """
    # Arrange
    nonexistent_path = str(temp_config_dir / "does_not_exist.yaml")

    # Act
    result = RedditPatternConfigLoader.load_config(nonexistent_path)

    # Assert
    assert result.is_err()
    assert isinstance(result.unwrap_err(), ConfigNotFoundError)
    assert "does_not_exist.yaml" in str(result.unwrap_err())


def test_malformed_yaml_returns_error(
    temp_config_dir: Path, malformed_yaml_content: str
) -> None:
    """
    E-ERROR: Malformed YAML returns ConfigInvalidError.

    Expected: FAIL (YAML error handling not implemented)
    """
    # Arrange
    config_path = temp_config_dir / "malformed.yaml"
    config_path.write_text(malformed_yaml_content)

    # Act
    result = RedditPatternConfigLoader.load_config(str(config_path))

    # Assert
    assert result.is_err()
    assert isinstance(result.unwrap_err(), ConfigInvalidError)


def test_invalid_pydantic_schema_returns_error(temp_config_dir: Path) -> None:
    """
    E-ERROR: Configuration with invalid schema returns ConfigSchemaError.

    Expected: FAIL (schema validation not implemented)
    """
    # Arrange - complete config with just keywords field invalid
    invalid_config = {
        "patterns": {
            "test": {
                "description": "Test",
                "keywords": "NOT_A_LIST",  # INVALID - should be list
                "usage": "test",
                "weight": 1.0,
            }
        },
        "reddit_search_template": "test",
        "topics": {},
        "integration": {
            "vectorstore": {"enabled": False, "tags_format": [], "embedding_model": "test"},
            "memory_tool": {"enabled": False, "path": "test", "format": "markdown"},
            "overnight_worker": {
                "enabled": False,
                "schedule": "never",
                "max_posts_per_topic": 0,
                "rate_limit_seconds": 0,
            },
        },
        "quality_filters": {
            "min_upvotes": 0,
            "min_comment_length": 0,
            "exclude_patterns": [],
            "sentiment_threshold": 0.0,
            "authenticity_score_min": 0.0,
        },
    }
    config_path = temp_config_dir / "invalid_schema.yaml"
    with open(config_path, "w") as f:
        yaml.dump(invalid_config, f)

    # Act
    result = RedditPatternConfigLoader.load_config(str(config_path))

    # Assert
    assert result.is_err()
    assert isinstance(result.unwrap_err(), ConfigSchemaError)
    assert "keywords" in str(result.unwrap_err()).lower()


# =============================================================================
# NECESSARY PATTERN: SECURITY TESTS
# =============================================================================


def test_path_traversal_attempt_blocked(temp_config_dir: Path) -> None:
    """
    S-SECURITY: Path traversal attempts (../) are blocked.

    Expected: FAIL (security validation not implemented)
    """
    # Arrange
    malicious_path = "../../etc/passwd"

    # Act
    result = RedditPatternConfigLoader.sanitize_path(malicious_path)

    # Assert
    assert result.is_err()
    assert isinstance(result.unwrap_err(), ConfigSecurityError)
    assert "traversal" in str(result.unwrap_err()).lower() or "security" in str(result.unwrap_err()).lower()


def test_absolute_path_outside_allowed_directories_blocked(temp_config_dir: Path) -> None:
    """
    S-SECURITY: Absolute paths outside allowed directories are blocked.

    Expected: FAIL (path validation not implemented)
    """
    # Arrange
    malicious_path = "/etc/passwd"

    # Act
    result = RedditPatternConfigLoader.sanitize_path(malicious_path)

    # Assert
    assert result.is_err()
    assert isinstance(result.unwrap_err(), ConfigSecurityError)


# =============================================================================
# NECESSARY PATTERN: STABILITY TESTS
# =============================================================================


def test_corrupt_yaml_handled_gracefully(temp_config_dir: Path) -> None:
    """
    S-STABILITY: Corrupt YAML file handled gracefully without crashes.

    Expected: FAIL (error handling not complete)
    """
    # Arrange
    corrupt_content = b"\x00\xFF\xFE\x00INVALID_BYTES"
    config_path = temp_config_dir / "corrupt.yaml"
    config_path.write_bytes(corrupt_content)

    # Act
    result = RedditPatternConfigLoader.load_config(str(config_path))

    # Assert
    assert result.is_err()
    assert isinstance(result.unwrap_err(), (ConfigInvalidError, ConfigError))


def test_large_config_file_loads_successfully(temp_config_dir: Path) -> None:
    """
    S-STABILITY: Large configuration file (1000+ patterns) loads successfully.

    Expected: FAIL (performance not yet tested)
    """
    # Arrange
    large_config = {
        "patterns": {
            f"pattern_{i}": {
                "description": f"Pattern {i}",
                "keywords": [f"keyword_{j}" for j in range(10)],
                "usage": f"Usage {i}",
                "weight": 1.0 + (i * 0.01),
            }
            for i in range(1000)
        },
        "reddit_search_template": "test",
        "topics": {},
        "integration": {
            "vectorstore": {"enabled": False, "tags_format": [], "embedding_model": "test"},
            "memory_tool": {"enabled": False, "path": "test", "format": "markdown"},
            "overnight_worker": {
                "enabled": False,
                "schedule": "never",
                "max_posts_per_topic": 0,
                "rate_limit_seconds": 0,
            },
        },
        "quality_filters": {
            "min_upvotes": 0,
            "min_comment_length": 0,
            "exclude_patterns": [],
            "sentiment_threshold": 0.0,
            "authenticity_score_min": 0.0,
        },
    }
    config_path = temp_config_dir / "large.yaml"
    with open(config_path, "w") as f:
        yaml.dump(large_config, f)

    # Act
    result = RedditPatternConfigLoader.load_config(str(config_path))

    # Assert
    assert result.is_ok()
    config = result.unwrap()
    assert len(config.patterns) == 1000


# =============================================================================
# NECESSARY PATTERN: ACCESSIBILITY (API USABILITY) TESTS
# =============================================================================


def test_loader_provides_clear_error_messages(temp_config_dir: Path) -> None:
    """
    A-ACCESSIBILITY: Error messages are clear and actionable.

    Expected: FAIL (error message quality not yet validated)
    """
    # Arrange
    invalid_config = {"patterns": {}}  # Missing required fields
    config_path = temp_config_dir / "invalid.yaml"
    with open(config_path, "w") as f:
        yaml.dump(invalid_config, f)

    # Act
    result = RedditPatternConfigLoader.load_config(str(config_path))

    # Assert
    assert result.is_err()
    error_msg = str(result.unwrap_err())
    assert len(error_msg) > 10, "Error message too short"
    assert any(
        keyword in error_msg.lower()
        for keyword in ["missing", "required", "invalid", "schema"]
    ), "Error message not descriptive"


# =============================================================================
# NECESSARY PATTERN: REGRESSION TESTS
# =============================================================================


def test_schema_version_compatibility(valid_config_path: str) -> None:
    """
    R-REGRESSION: Configuration schema is backward compatible.

    Expected: FAIL (versioning not implemented)
    """
    # Arrange: Current production config file

    # Act
    result = RedditPatternConfigLoader.load_config(valid_config_path)

    # Assert
    assert result.is_ok(), "Production config file must always be valid"


# =============================================================================
# NECESSARY PATTERN: YIELD (OUTPUT VALIDATION) TESTS
# =============================================================================


def test_loaded_config_contains_all_expected_fields(valid_config_path: str) -> None:
    """
    Y-YIELD: Loaded configuration contains all expected fields.

    Expected: FAIL (output validation not complete)
    """
    # Arrange
    loader = RedditPatternConfigLoader()

    # Act
    result = loader.load_config(valid_config_path)

    # Assert
    assert result.is_ok()
    config = result.unwrap()

    # Validate patterns section
    assert "experience_markers" in config.patterns
    assert "pain_signals" in config.patterns
    assert "emotional_depth" in config.patterns

    # Validate topics section
    assert "acim" in config.topics
    assert "co_parenting" in config.topics
    assert "conscious_uncoupling" in config.topics
    assert "open_relationships" in config.topics
    assert "love_and_forgiveness" in config.topics

    # Validate integration section
    assert config.integration.vectorstore.enabled is True
    assert config.integration.memory_tool.enabled is True
    assert config.integration.overnight_worker.enabled is True

    # Validate quality filters
    assert config.quality_filters.min_upvotes >= 0
    assert config.quality_filters.min_comment_length >= 0
    assert -1.0 <= config.quality_filters.sentiment_threshold <= 1.0
    assert 0.0 <= config.quality_filters.authenticity_score_min <= 1.0


def test_pattern_keywords_are_lowercased_for_consistency(valid_config_path: str) -> None:
    """
    Y-YIELD: Pattern keywords are normalized (lowercased) for consistency.

    Expected: FAIL (normalization not implemented)
    """
    # Arrange
    loader = RedditPatternConfigLoader()

    # Act
    result = loader.load_config(valid_config_path)

    # Assert
    assert result.is_ok()
    config = result.unwrap()

    for category_name, category in config.patterns.items():
        for keyword in category.keywords:
            # Keywords should be case-insensitive searchable
            assert keyword.lower() == keyword or keyword.isupper(), (
                f"Keyword '{keyword}' in {category_name} should be normalized"
            )
