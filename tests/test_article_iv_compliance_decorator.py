# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Tests for Article IV Compliance Decorator

Validates that @with_article_iv_compliance enforces:
1. VectorStore query BEFORE action
2. Pattern storage AFTER successful action
3. Proper handling of Result<T,E> pattern
4. Dynamic tag generation
5. Error resilience (degraded mode)

Constitutional Requirements:
    - Article IV (ADR-004): Mandatory VectorStore integration
    - Query search_memories() before action
    - Store successful patterns after completion
"""

import pytest
from unittest.mock import Mock, patch

from shared.agent_context import create_agent_context
from shared.article_iv_compliance import with_article_iv_compliance
from shared.type_definitions.result import Result, Ok, Err


class MockAgent:
    """Mock agent for testing decorator."""

    def __init__(self, context):
        self.context = context

    @with_article_iv_compliance(query_tags=["test", "pattern"])
    def simple_method(self, **kwargs):
        """Simple method with static tags."""
        return "success"

    @with_article_iv_compliance(query_tags=["test", "result_pattern"])
    def result_method(self, **kwargs) -> Result[str, str]:
        """Method returning Result<T,E>."""
        return Ok("success")

    @with_article_iv_compliance(query_tags=lambda self, task_type, **kw: ["test", task_type])
    def dynamic_tags_method(self, task_type: str, **kwargs):
        """Method with dynamic tag generation."""
        return {"success": True, "task_type": task_type}

    @with_article_iv_compliance(query_tags=["test", "error"], store_on_success=True)
    def error_method(self, **kwargs) -> Result[str, str]:
        """Method that returns error."""
        return Err("failure")

    @with_article_iv_compliance(query_tags=["test"], store_on_success=False)
    def no_store_method(self, **kwargs):
        """Method with storage disabled."""
        return "success"


class TestArticleIVComplianceDecorator:
    """Test suite for Article IV compliance decorator."""

    def test_decorator_queries_vectorstore_before_action(self):
        """Decorator should query VectorStore patterns BEFORE executing method."""
        context = create_agent_context()
        agent = MockAgent(context)

        # Store a pattern to query
        context.store_memory(
            key="test_pattern_1", content={"data": "pattern"}, tags=["test", "pattern"]
        )

        # Mock search_memories to track calls
        with patch.object(context, "search_memories", wraps=context.search_memories) as mock_search:
            result = agent.simple_method()

            # Verify search was called BEFORE method execution
            assert mock_search.called
            call_args = mock_search.call_args
            assert call_args[1]["tags"] == ["test", "pattern"]
            assert call_args[1]["min_confidence"] == 0.6
            assert result == "success"

    def test_decorator_stores_success_pattern_after_action(self):
        """Decorator should store success pattern AFTER executing method."""
        context = create_agent_context()
        agent = MockAgent(context)

        # Execute method
        result = agent.simple_method()

        # Verify pattern was stored
        stored_patterns = context.search_memories(tags=["success", "simple_method"])
        assert len(stored_patterns) > 0
        assert result == "success"

        # Verify stored content
        pattern = stored_patterns[0]
        assert pattern["content"]["function"] == "simple_method"
        assert pattern["content"]["success"] is True

    def test_decorator_handles_result_pattern_success(self):
        """Decorator should detect Result<T,E> success and store pattern."""
        context = create_agent_context()
        agent = MockAgent(context)

        # Execute method returning Ok(...)
        result = agent.result_method()

        # Verify Result success
        assert result.is_ok()
        assert result.unwrap() == "success"

        # Verify pattern was stored
        stored_patterns = context.search_memories(tags=["success", "result_method"])
        assert len(stored_patterns) > 0

        pattern = stored_patterns[0]
        assert pattern["content"]["function"] == "result_method"
        assert pattern["content"]["success"] is True

    def test_decorator_skips_storage_for_result_pattern_errors(self):
        """Decorator should NOT store pattern when Result is Err(...)."""
        # Create fresh context to avoid pollution from other tests
        context = create_agent_context(use_persistent_memory=False)
        agent = MockAgent(context)

        # Execute method returning Err(...)
        result = agent.error_method()

        # Verify Result error
        assert result.is_err()
        assert result.unwrap_err() == "failure"

        # Verify pattern was NOT stored (check session memory only)
        stored_patterns = context.search_memories(
            tags=["success", "error_method"], include_session=True
        )

        # Filter to only patterns from this specific call
        recent_patterns = [
            p
            for p in stored_patterns
            if p.get("content", {}).get("function") == "error_method"
        ]
        assert len(recent_patterns) == 0, "Error result should not be stored"

    def test_decorator_supports_dynamic_tag_generation(self):
        """Decorator should support callable for dynamic tag generation."""
        context = create_agent_context()
        agent = MockAgent(context)

        # Execute method with dynamic tags
        result = agent.dynamic_tags_method(task_type="refactor")

        # Verify success
        assert result["success"] is True
        assert result["task_type"] == "refactor"

        # Verify pattern was stored with dynamic tags
        stored_patterns = context.search_memories(tags=["test", "refactor"])
        assert len(stored_patterns) > 0

        pattern = stored_patterns[0]
        assert "refactor" in pattern["tags"]

    def test_decorator_respects_store_on_success_false(self):
        """Decorator should NOT store pattern when store_on_success=False."""
        # Create fresh context to avoid pollution from other tests
        context = create_agent_context(use_persistent_memory=False)
        agent = MockAgent(context)

        # Execute method with storage disabled
        result = agent.no_store_method()

        # Verify success
        assert result == "success"

        # Verify pattern was NOT stored (check session memory only)
        stored_patterns = context.search_memories(
            tags=["success", "no_store_method"], include_session=True
        )

        # Filter to only patterns from this specific call
        recent_patterns = [
            p
            for p in stored_patterns
            if p.get("content", {}).get("function") == "no_store_method"
        ]
        assert (
            len(recent_patterns) == 0
        ), "Pattern should not be stored when store_on_success=False"

    def test_decorator_handles_missing_context_gracefully(self):
        """Decorator should degrade gracefully when AgentContext is missing."""

        class NoContextAgent:
            # No context attribute

            @with_article_iv_compliance(query_tags=["test"])
            def method(self, **kwargs):
                return "success"

        agent = NoContextAgent()

        # Should not raise, just skip compliance
        result = agent.method()
        assert result == "success"

    def test_decorator_handles_vectorstore_query_failure(self):
        """Decorator should handle VectorStore query failures gracefully."""
        context = create_agent_context()
        agent = MockAgent(context)

        # Mock search_memories to raise exception
        with patch.object(context, "search_memories", side_effect=Exception("VectorStore error")):
            # Should not raise, just continue without patterns
            result = agent.simple_method()
            assert result == "success"

    def test_decorator_handles_vectorstore_storage_failure(self):
        """Decorator should handle VectorStore storage failures gracefully."""
        context = create_agent_context()
        agent = MockAgent(context)

        # Mock store_memory to raise exception
        with patch.object(context, "store_memory", side_effect=Exception("Storage error")):
            # Should not raise, just continue without storing
            result = agent.simple_method()
            assert result == "success"

    def test_decorator_injects_patterns_into_kwargs(self):
        """Decorator should inject VectorStore patterns into kwargs."""
        context = create_agent_context()

        # Store patterns
        context.store_memory(
            key="pattern_1", content={"solution": "use_cache"}, tags=["test", "pattern"]
        )
        context.store_memory(
            key="pattern_2", content={"solution": "validate_input"}, tags=["test", "pattern"]
        )

        class PatternAgent:
            def __init__(self, context):
                self.context = context

            @with_article_iv_compliance(query_tags=["test", "pattern"])
            def method(self, _vectorstore_patterns=None):
                return _vectorstore_patterns

        agent = PatternAgent(context)
        patterns = agent.method()

        # Verify patterns were injected
        assert patterns is not None
        assert len(patterns) >= 2

    def test_decorator_preserves_function_metadata(self):
        """Decorator should preserve original function name and docstring."""
        context = create_agent_context()
        agent = MockAgent(context)

        # Verify metadata preserved
        assert agent.simple_method.__name__ == "simple_method"
        assert agent.simple_method.__doc__ == "Simple method with static tags."

    def test_decorator_supports_dict_success_indicator(self):
        """Decorator should detect success from dict with 'success' key."""
        context = create_agent_context()
        agent = MockAgent(context)

        # Execute method returning success dict
        result = agent.dynamic_tags_method(task_type="test")

        # Verify pattern stored
        stored_patterns = context.search_memories(tags=["success", "dynamic_tags_method"])
        assert len(stored_patterns) > 0

    def test_decorator_respects_min_confidence_parameter(self):
        """Decorator should respect min_confidence parameter for queries."""
        context = create_agent_context()

        # Store patterns with different confidence levels
        context.store_memory(
            key="high_conf",
            content={"solution": "high"},
            tags=["test", "confidence"],
            confidence=0.9,
        )
        context.store_memory(
            key="low_conf",
            content={"solution": "low"},
            tags=["test", "confidence"],
            confidence=0.3,
        )

        class ConfidenceAgent:
            def __init__(self, context):
                self.context = context

            @with_article_iv_compliance(query_tags=["test", "confidence"], min_confidence=0.6)
            def method(self, _vectorstore_patterns=None):
                return _vectorstore_patterns

        agent = ConfidenceAgent(context)
        patterns = agent.method()

        # Should only get high-confidence pattern
        assert patterns is not None
        assert len(patterns) >= 1
        # All returned patterns should have confidence >= 0.6
        for pattern in patterns:
            assert pattern.get("confidence", 1.0) >= 0.6

    def test_decorator_handles_none_query_tags(self):
        """Decorator should handle None query_tags gracefully."""
        context = create_agent_context()

        class NoneTagsAgent:
            def __init__(self, context):
                self.context = context

            @with_article_iv_compliance(query_tags=None)
            def method(self, **kwargs):
                return "success"

        agent = NoneTagsAgent(context)
        result = agent.method()

        # Should execute successfully without querying
        assert result == "success"

    def test_decorator_handles_invalid_query_tags_callable(self):
        """Decorator should handle exceptions in query_tags callable."""
        context = create_agent_context()

        def bad_tags_callable(*args, **kwargs):
            raise ValueError("Tags generation failed")

        class BadCallableAgent:
            def __init__(self, context):
                self.context = context

            @with_article_iv_compliance(query_tags=bad_tags_callable)
            def method(self, **kwargs):
                return "success"

        agent = BadCallableAgent(context)
        result = agent.method()

        # Should execute successfully with empty tags
        assert result == "success"

    def test_decorator_with_custom_storage_confidence(self):
        """Decorator should use custom storage_confidence parameter."""
        context = create_agent_context(use_persistent_memory=False)

        class CustomConfidenceAgent:
            def __init__(self, context):
                self.context = context

            @with_article_iv_compliance(query_tags=["test"], storage_confidence=0.95)
            def method(self, **kwargs):
                return "success"

        # Mock store_memory to verify confidence parameter
        with patch.object(context, "store_memory", wraps=context.store_memory) as mock_store:
            agent = CustomConfidenceAgent(context)
            agent.method()

            # Verify store_memory was called with correct confidence
            assert mock_store.called
            call_args = mock_store.call_args
            assert call_args[1]["confidence"] == 0.95, "Custom confidence should be 0.95"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
