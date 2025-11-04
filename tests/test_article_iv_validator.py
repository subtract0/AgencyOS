"""Tests for Article IV constitutional validator.

Article IV: Continuous Learning and Improvement (ADR-004)
- VectorStore integration is constitutionally mandatory (not optional)
- USE_ENHANCED_MEMORY must be 'true' - no disable flags permitted
- Cross-session pattern persistence required
"""
import os
import pytest
from shared.agent_context import create_agent_context
from agency_memory import Memory, InMemoryStore, EnhancedMemoryStore


def test_validate_article_iv_passes_with_vectorstore():
    """Verify Article IV validator passes with EnhancedMemoryStore."""
    from shared.constitutional_validator import validate_article_iv

    context = create_agent_context()  # Should use EnhancedMemoryStore by default

    result = validate_article_iv(context)

    assert result.is_ok()
    assert result.unwrap() is True


def test_validate_article_iv_fails_with_inmemory():
    """Verify Article IV validator detects InMemoryStore violation."""
    from shared.constitutional_validator import validate_article_iv

    # Explicit InMemoryStore (violates Article IV)
    context = create_agent_context(memory=Memory(store=InMemoryStore()))

    result = validate_article_iv(context)

    assert result.is_err()
    error_msg = result.unwrap_err()
    assert "InMemoryStore" in error_msg
    assert "Article IV" in error_msg


def test_validate_article_iv_checks_env_var():
    """Verify Article IV validator checks USE_ENHANCED_MEMORY env var."""
    from shared.constitutional_validator import validate_article_iv

    # Temporarily set env var to false
    original = os.environ.get("USE_ENHANCED_MEMORY")
    os.environ["USE_ENHANCED_MEMORY"] = "false"

    try:
        context = create_agent_context()
        result = validate_article_iv(context)

        # Should fail even with VectorStore if env var is false
        assert result.is_err()
        assert "USE_ENHANCED_MEMORY" in result.unwrap_err()
    finally:
        if original:
            os.environ["USE_ENHANCED_MEMORY"] = original
        else:
            os.environ.pop("USE_ENHANCED_MEMORY", None)


def test_validate_article_iv_result_pattern():
    """Verify validate_article_iv returns Result type."""
    from shared.constitutional_validator import validate_article_iv
    from shared.type_definitions.result import Result

    context = create_agent_context()
    result = validate_article_iv(context)

    assert isinstance(result, Result)
