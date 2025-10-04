"""
Test suite for Constitutional Compliance Validator.

Following TDD principles: write tests first, then implementation.
Tests all 5 constitutional articles and decorator functionality.
"""

from unittest.mock import Mock, patch

import pytest

from shared.agent_context import AgentContext, create_agent_context


# Test fixtures
@pytest.fixture
def mock_agent_context():
    """Create a mock agent context for testing."""
    return create_agent_context()


@pytest.fixture
def mock_create_agent_func():
    """Create a mock agent creation function."""

    def create_mock_agent(
        model: str = "gpt-5", reasoning_effort: str = "medium", agent_context: AgentContext = None
    ):
        return Mock(name="MockAgent", model=model)

    return create_mock_agent


class TestConstitutionalComplianceDecorator:
    """Test suite for @constitutional_compliance decorator."""

    def test_decorator_exists(self):
        """Test that the decorator can be imported."""
        from shared.constitutional_validator import constitutional_compliance

        assert callable(constitutional_compliance)

    def test_decorator_preserves_function_metadata(self, mock_create_agent_func):
        """Test that decorator preserves original function's metadata."""
        from shared.constitutional_validator import constitutional_compliance

        decorated_func = constitutional_compliance(mock_create_agent_func)

        assert decorated_func.__name__ == mock_create_agent_func.__name__
        assert callable(decorated_func)

    def test_decorator_calls_validation_functions(self, mock_create_agent_func, mock_agent_context):
        """Test that decorator invokes all 5 article validation functions."""
        from shared.constitutional_validator import constitutional_compliance

        with (
            patch("shared.constitutional_validator.validate_article_i") as mock_i,
            patch("shared.constitutional_validator.validate_article_ii") as mock_ii,
            patch("shared.constitutional_validator.validate_article_iii") as mock_iii,
            patch("shared.constitutional_validator.validate_article_iv") as mock_iv,
            patch("shared.constitutional_validator.validate_article_v") as mock_v,
        ):
            decorated_func = constitutional_compliance(mock_create_agent_func)
            result = decorated_func(agent_context=mock_agent_context)

            # All validation functions should be called
            mock_i.assert_called_once()
            mock_ii.assert_called_once()
            mock_iii.assert_called_once()
            mock_iv.assert_called_once()
            mock_v.assert_called_once()

            # Original function should be called
            assert result is not None

    def test_decorator_blocks_on_article_i_violation(self, mock_create_agent_func):
        """Test that Article I violation prevents agent creation."""
        from shared.constitutional_validator import (
            ConstitutionalViolation,
            constitutional_compliance,
        )

        with patch(
            "shared.constitutional_validator.validate_article_i",
            side_effect=ConstitutionalViolation("Article I: Incomplete context"),
        ):
            decorated_func = constitutional_compliance(mock_create_agent_func)

            with pytest.raises(ConstitutionalViolation, match="Article I"):
                decorated_func()

    def test_decorator_blocks_on_article_ii_violation(self, mock_create_agent_func):
        """Test that Article II violation prevents agent creation."""
        from shared.constitutional_validator import (
            ConstitutionalViolation,
            constitutional_compliance,
        )

        with (
            patch("shared.constitutional_validator.validate_article_i"),
            patch(
                "shared.constitutional_validator.validate_article_ii",
                side_effect=ConstitutionalViolation("Article II: Quality standards not met"),
            ),
        ):
            decorated_func = constitutional_compliance(mock_create_agent_func)

            with pytest.raises(ConstitutionalViolation, match="Article II"):
                decorated_func()

    def test_decorator_passes_arguments_through(self, mock_create_agent_func):
        """Test that decorator passes all arguments to wrapped function."""
        from shared.constitutional_validator import constitutional_compliance

        with (
            patch("shared.constitutional_validator.validate_article_i"),
            patch("shared.constitutional_validator.validate_article_ii"),
            patch("shared.constitutional_validator.validate_article_iii"),
            patch("shared.constitutional_validator.validate_article_iv"),
            patch("shared.constitutional_validator.validate_article_v"),
        ):
            decorated_func = constitutional_compliance(mock_create_agent_func)
            result = decorated_func(model="gpt-5-mini", reasoning_effort="high")

            assert result.model == "gpt-5-mini"


class TestArticleIValidation:
    """Test Article I: Complete Context Before Action."""

    def test_validate_article_i_exists(self):
        """Test that Article I validation function exists."""
        from shared.constitutional_validator import validate_article_i

        assert callable(validate_article_i)

    def test_validate_article_i_checks_agent_context(self):
        """Test that Article I validates agent context is provided."""
        from shared.constitutional_validator import validate_article_i

        # Should not raise with valid context
        context = create_agent_context()
        validate_article_i(agent_context=context)

    def test_validate_article_i_checks_session_id(self):
        """Test that Article I validates session ID exists."""
        from shared.constitutional_validator import validate_article_i

        context = create_agent_context()
        assert context.session_id is not None
        validate_article_i(agent_context=context)

    def test_validate_article_i_checks_memory_availability(self):
        """Test that Article I validates memory system is available."""
        from shared.constitutional_validator import validate_article_i

        context = create_agent_context()
        assert context.memory is not None
        validate_article_i(agent_context=context)


class TestArticleIIValidation:
    """Test Article II: 100% Verification and Stability."""

    def test_validate_article_ii_exists(self):
        """Test that Article II validation function exists."""
        from shared.constitutional_validator import validate_article_ii

        assert callable(validate_article_ii)

    def test_validate_article_ii_checks_test_availability(self):
        """Test that Article II validates test infrastructure exists."""
        from shared.constitutional_validator import validate_article_ii

        # Should check for run_tests.py or pytest availability
        validate_article_ii()

    def test_validate_article_ii_does_not_run_tests(self):
        """Test that Article II validation does NOT execute tests (performance)."""
        # Validation should be fast and not run full test suite
        import time

        from shared.constitutional_validator import validate_article_ii

        start = time.time()
        validate_article_ii()
        duration = time.time() - start

        # Should complete in under 1 second
        assert duration < 1.0


class TestArticleIIIValidation:
    """Test Article III: Automated Merge Enforcement."""

    def test_validate_article_iii_exists(self):
        """Test that Article III validation function exists."""
        from shared.constitutional_validator import validate_article_iii

        assert callable(validate_article_iii)

    def test_validate_article_iii_checks_git_hooks(self):
        """Test that Article III validates git hooks are configured."""
        from shared.constitutional_validator import validate_article_iii

        # Should verify pre-commit hooks exist
        validate_article_iii()

    def test_validate_article_iii_checks_no_bypass_flags(self):
        """Test that Article III ensures no bypass mechanisms are enabled."""
        from shared.constitutional_validator import validate_article_iii

        # Should check that FORCE_BYPASS or similar flags are not set
        with patch.dict("os.environ", {"FORCE_BYPASS": "true"}):
            from shared.constitutional_validator import ConstitutionalViolation

            with pytest.raises(ConstitutionalViolation, match="Article III"):
                validate_article_iii()


class TestArticleIVValidation:
    """Test Article IV: Continuous Learning and Improvement."""

    def test_validate_article_iv_exists(self):
        """Test that Article IV validation function exists."""
        from shared.constitutional_validator import validate_article_iv

        assert callable(validate_article_iv)

    def test_validate_article_iv_checks_learning_integration(self):
        """Test that Article IV validates learning system is available."""
        from shared.constitutional_validator import validate_article_iv

        context = create_agent_context()
        validate_article_iv(agent_context=context)

    def test_validate_article_iv_checks_vector_store(self):
        """Test that Article IV validates VectorStore access."""
        from shared.constitutional_validator import validate_article_iv

        context = create_agent_context()
        # Context should have memory system which includes vector store
        assert context.memory is not None
        validate_article_iv(agent_context=context)

    def test_validate_article_iv_rejects_disabled_learning(self):
        """Test that Article IV rejects DISABLE_LEARNING flag."""
        from shared.constitutional_validator import ConstitutionalViolation, validate_article_iv

        with patch.dict("os.environ", {"DISABLE_LEARNING": "true"}):
            with pytest.raises(ConstitutionalViolation, match="Article IV.*DISABLE_LEARNING"):
                validate_article_iv()

    def test_validate_article_iv_requires_enhanced_memory_enabled(self):
        """Test that Article IV requires USE_ENHANCED_MEMORY to be true."""
        from shared.constitutional_validator import ConstitutionalViolation, validate_article_iv

        # Test with explicit false
        with patch.dict("os.environ", {"USE_ENHANCED_MEMORY": "false"}):
            with pytest.raises(ConstitutionalViolation, match="Article IV.*USE_ENHANCED_MEMORY"):
                validate_article_iv()

    def test_validate_article_iv_passes_with_enhanced_memory_true(self):
        """Test that Article IV passes when USE_ENHANCED_MEMORY is true."""
        from shared.constitutional_validator import validate_article_iv

        with patch.dict("os.environ", {"USE_ENHANCED_MEMORY": "true"}):
            # Should not raise
            validate_article_iv()


class TestArticleVValidation:
    """Test Article V: Spec-Driven Development."""

    def test_validate_article_v_exists(self):
        """Test that Article V validation function exists."""
        from shared.constitutional_validator import validate_article_v

        assert callable(validate_article_v)

    def test_validate_article_v_checks_specs_directory(self):
        """Test that Article V validates specs/ directory exists."""
        from shared.constitutional_validator import validate_article_v

        # Should verify specs/ directory is present
        validate_article_v()

    def test_validate_article_v_checks_plans_directory(self):
        """Test that Article V validates plans/ directory exists."""
        from shared.constitutional_validator import validate_article_v

        # Should verify plans/ directory is present
        validate_article_v()

    def test_validate_article_v_checks_constitution(self):
        """Test that Article V validates constitution.md exists."""
        from shared.constitutional_validator import validate_article_v

        # Should verify constitution.md is accessible
        validate_article_v()


class TestConstitutionalViolationException:
    """Test ConstitutionalViolation exception class."""

    def test_constitutional_violation_exists(self):
        """Test that ConstitutionalViolation exception exists."""
        from shared.constitutional_validator import ConstitutionalViolation

        assert issubclass(ConstitutionalViolation, Exception)

    def test_constitutional_violation_has_message(self):
        """Test that ConstitutionalViolation carries error message."""
        from shared.constitutional_validator import ConstitutionalViolation

        error = ConstitutionalViolation("Article II violated")
        assert str(error) == "Article II violated"

    def test_constitutional_violation_can_be_raised(self):
        """Test that ConstitutionalViolation can be raised and caught."""
        from shared.constitutional_validator import ConstitutionalViolation

        with pytest.raises(ConstitutionalViolation):
            raise ConstitutionalViolation("Test violation")


class TestValidationHelpers:
    """Test helper functions for validation."""

    def test_check_file_exists_helper(self):
        """Test helper function to check file existence."""
        from shared.constitutional_validator import _check_file_exists

        # Should return True for existing file
        assert _check_file_exists("constitution.md")

        # Should return False for non-existing file
        assert not _check_file_exists("nonexistent_file.md")

    def test_check_directory_exists_helper(self):
        """Test helper function to check directory existence."""
        from shared.constitutional_validator import _check_directory_exists

        # Should return True for existing directory
        assert _check_directory_exists("specs")

        # Should return False for non-existing directory
        assert not _check_directory_exists("nonexistent_dir")

    def test_get_env_flag_helper(self):
        """Test helper function to check environment flags."""
        from shared.constitutional_validator import _get_env_flag

        with patch.dict("os.environ", {"TEST_FLAG": "true"}):
            assert _get_env_flag("TEST_FLAG") is True

        with patch.dict("os.environ", {"TEST_FLAG": "false"}):
            assert _get_env_flag("TEST_FLAG") is False


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_successful_agent_creation_with_decorator(self, mock_agent_context):
        """Test successful agent creation when all validations pass."""
        from shared.constitutional_validator import constitutional_compliance

        @constitutional_compliance
        def create_test_agent(model: str = "gpt-5", agent_context: AgentContext = None):
            return Mock(name="TestAgent", model=model)

        # Should succeed without errors
        agent = create_test_agent(agent_context=mock_agent_context)
        assert agent is not None

    def test_failed_agent_creation_logs_violation(self, mock_agent_context):
        """Test that violations are logged for debugging."""
        from shared.constitutional_validator import (
            ConstitutionalViolation,
            constitutional_compliance,
        )

        with (
            patch(
                "shared.constitutional_validator.validate_article_ii",
                side_effect=ConstitutionalViolation("Article II: Tests failing"),
            ),
            patch("shared.constitutional_validator._log_violation") as mock_log,
        ):

            @constitutional_compliance
            def create_test_agent(agent_context: AgentContext = None):
                return Mock()

            with pytest.raises(ConstitutionalViolation):
                create_test_agent(agent_context=mock_agent_context)

            # Violation should be logged
            mock_log.assert_called_once()

    def test_decorator_performance_overhead(self, mock_create_agent_func, mock_agent_context):
        """Test that decorator adds minimal performance overhead."""
        import time

        from shared.constitutional_validator import constitutional_compliance

        decorated_func = constitutional_compliance(mock_create_agent_func)

        # Measure execution time
        start = time.time()
        decorated_func(agent_context=mock_agent_context)
        duration = time.time() - start

        # Validation should complete quickly (under 2 seconds)
        assert duration < 2.0


class TestBackwardCompatibility:
    """Test backward compatibility with existing agent creation functions."""

    def test_decorator_works_with_optional_agent_context(self):
        """Test decorator works when agent_context is None (creates default)."""
        from shared.constitutional_validator import constitutional_compliance

        @constitutional_compliance
        def create_test_agent(model: str = "gpt-5", agent_context: AgentContext = None):
            if agent_context is None:
                agent_context = create_agent_context()
            return Mock(name="TestAgent", agent_context=agent_context)

        # Should work with None
        agent = create_test_agent(agent_context=None)
        assert agent is not None

    def test_decorator_works_with_cost_tracker(self):
        """Test decorator works with cost_tracker parameter."""
        from shared.constitutional_validator import constitutional_compliance

        @constitutional_compliance
        def create_test_agent(
            model: str = "gpt-5", agent_context: AgentContext = None, cost_tracker=None
        ):
            return Mock(name="TestAgent", cost_tracker=cost_tracker)

        mock_tracker = Mock()
        agent = create_test_agent(cost_tracker=mock_tracker)
        assert agent.cost_tracker == mock_tracker

    def test_decorator_preserves_return_type(self, mock_create_agent_func):
        """Test that decorator preserves original function's return type."""
        from shared.constitutional_validator import constitutional_compliance

        decorated_func = constitutional_compliance(mock_create_agent_func)
        result = decorated_func()

        # Return type should be preserved
        assert isinstance(result, Mock)
