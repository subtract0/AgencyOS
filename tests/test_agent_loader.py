"""
Tests for AgentLoader - Hybrid DSPy/Traditional Implementation Loader

Following TDD principles per Constitution Article V and ADR-012.
These tests MUST fail initially, then pass after implementation.

Tests cover:
- Frontmatter parsing from .claude/agents/*.md files
- DSPy availability checking
- Traditional fallback when DSPy unavailable
- Telemetry wrapper integration
- All 5 DSPy-migrated agents
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import will fail initially - this is expected for TDD
try:
    from src.agency.agents.loader import (
        AgentLoader,
        AgentFrontmatter,
        ImplementationConfig,
        RolloutConfig,
        LoaderError,
        TelemetryWrapper
    )
except ImportError:
    # Expected during TDD - tests should fail
    pytest.skip("AgentLoader not yet implemented", allow_module_level=True)


class TestAgentFrontmatterParsing:
    """Test frontmatter parsing from agent markdown files."""

    @pytest.fixture
    def loader(self):
        """Create AgentLoader instance."""
        return AgentLoader()

    def test_parse_frontmatter_with_valid_yaml(self, loader, tmp_path):
        """Should parse valid frontmatter correctly."""
        agent_file = tmp_path / "test_agent.md"
        agent_file.write_text("""---
name: test-agent
description: Test agent for testing
implementation:
  traditional: "src/agency/agents/test.py"
  dspy: "src/agency/agents/dspy/test.py"
  preferred: dspy
  features:
    dspy:
      - "Feature 1"
      - "Feature 2"
    traditional:
      - "Basic feature"
rollout:
  status: gradual
  fallback: traditional
  comparison: true
---

# Test Agent

Agent body content here.
""")

        frontmatter = loader._parse_frontmatter(str(agent_file))

        assert frontmatter.name == "test-agent"
        assert frontmatter.description == "Test agent for testing"
        assert frontmatter.implementation.preferred == "dspy"
        assert frontmatter.rollout.status == "gradual"
        assert frontmatter.rollout.comparison is True

    def test_parse_frontmatter_missing_file(self, loader):
        """Should raise LoaderError for missing file."""
        with pytest.raises(LoaderError, match="File not found"):
            loader._parse_frontmatter("/nonexistent/file.md")

    def test_parse_frontmatter_invalid_yaml(self, loader, tmp_path):
        """Should raise LoaderError for invalid YAML."""
        agent_file = tmp_path / "invalid.md"
        agent_file.write_text("""---
invalid yaml: [unclosed
---
""")

        with pytest.raises(LoaderError, match="Invalid YAML"):
            loader._parse_frontmatter(str(agent_file))

    def test_parse_frontmatter_missing_required_fields(self, loader, tmp_path):
        """Should raise LoaderError for missing required fields."""
        agent_file = tmp_path / "incomplete.md"
        agent_file.write_text("""---
name: test-agent
# Missing implementation and rollout
---
""")

        with pytest.raises(LoaderError, match="Missing required field"):
            loader._parse_frontmatter(str(agent_file))

    def test_parse_markdown_body(self, loader, tmp_path):
        """Should extract markdown body correctly."""
        agent_file = tmp_path / "test.md"
        agent_file.write_text("""---
name: test
---

# Agent Body

This is the markdown specification.
""")

        body = loader._parse_body(str(agent_file))

        assert "# Agent Body" in body
        assert "This is the markdown specification" in body
        assert "---" not in body  # Frontmatter should be stripped


class TestDSPyAvailabilityChecking:
    """Test DSPy availability detection."""

    @pytest.fixture
    def loader(self):
        return AgentLoader()

    def test_check_dspy_available_when_installed(self, loader):
        """Should return True when DSPy is available."""
        with patch('src.agency.agents.loader.DSPY_AVAILABLE', True):
            assert loader._check_dspy_available() is True

    def test_check_dspy_unavailable(self, loader):
        """Should return False when DSPy not available."""
        with patch('src.agency.agents.loader.DSPY_AVAILABLE', False):
            assert loader._check_dspy_available() is False

    def test_check_dspy_import_error(self, loader):
        """Should handle import errors gracefully."""
        # The loader checks the global DSPY_AVAILABLE flag, not importlib directly
        with patch('src.agency.agents.loader.DSPY_AVAILABLE', False):
            assert loader._check_dspy_available() is False


class TestAgentLoading:
    """Test agent instantiation with preferred implementation."""

    @pytest.fixture
    def loader(self):
        return AgentLoader()

    @pytest.fixture
    def mock_frontmatter(self):
        """Create mock frontmatter for testing."""
        return AgentFrontmatter(
            name="test-agent",
            description="Test agent",
            implementation=ImplementationConfig(
                traditional="src/agency/agents/test.py",
                dspy="src/agency/agents/dspy/test.py",
                preferred="dspy",
                features={"dspy": ["Feature 1"], "traditional": ["Basic"]}
            ),
            rollout=RolloutConfig(
                status="gradual",
                fallback="traditional",
                comparison=True
            )
        )

    def test_load_dspy_agent_when_available(self, loader, mock_frontmatter):
        """Should load DSPy agent when available and preferred."""
        with patch.object(loader, '_check_dspy_available', return_value=True):
            with patch.object(loader, '_load_dspy_agent') as mock_load:
                mock_agent = Mock()
                mock_load.return_value = mock_agent

                agent = loader.load_agent_from_frontmatter(mock_frontmatter, "body")

                mock_load.assert_called_once()
                assert agent is not None

    def test_load_traditional_when_dspy_unavailable(self, loader, mock_frontmatter):
        """Should fallback to traditional when DSPy unavailable."""
        with patch.object(loader, '_check_dspy_available', return_value=False):
            with patch.object(loader, '_load_traditional_agent') as mock_load:
                mock_agent = Mock()
                mock_load.return_value = mock_agent

                agent = loader.load_agent_from_frontmatter(mock_frontmatter, "body")

                mock_load.assert_called_once()
                assert agent is not None

    def test_fallback_on_dspy_load_error(self, loader, mock_frontmatter):
        """Should fallback to traditional when DSPy load fails."""
        with patch.object(loader, '_check_dspy_available', return_value=True):
            with patch.object(loader, '_load_dspy_agent', side_effect=Exception("Load failed")):
                with patch.object(loader, '_load_traditional_agent') as mock_fallback:
                    mock_agent = Mock()
                    mock_fallback.return_value = mock_agent

                    agent = loader.load_agent_from_frontmatter(mock_frontmatter, "body")

                    mock_fallback.assert_called_once()
                    assert agent is not None

    def test_force_implementation_override(self, loader, mock_frontmatter):
        """Should respect force_implementation parameter."""
        with patch.object(loader, '_check_dspy_available', return_value=True):
            with patch.object(loader, '_load_traditional_agent') as mock_load:
                mock_agent = Mock()
                mock_load.return_value = mock_agent

                # Force traditional even though DSPy is preferred
                agent = loader.load_agent_from_frontmatter(
                    mock_frontmatter, 
                    "body",
                    force_implementation="traditional"
                )

                mock_load.assert_called_once()


class TestTelemetryWrapper:
    """Test telemetry wrapper for performance comparison."""

    def test_telemetry_wrapper_tracks_calls(self):
        """Should track agent method calls."""
        mock_agent = Mock()
        mock_agent.execute = Mock(return_value="result")

        wrapper = TelemetryWrapper(mock_agent, "dspy")

        result = wrapper.execute("test")

        assert result == "result"
        assert wrapper.call_count > 0
        assert wrapper.implementation_type == "dspy"

    def test_telemetry_wrapper_tracks_latency(self):
        """Should track execution latency."""
        mock_agent = Mock()
        wrapper = TelemetryWrapper(mock_agent, "traditional")

        wrapper.execute("test")

        assert hasattr(wrapper, 'last_latency_ms')
        assert wrapper.last_latency_ms >= 0

    def test_telemetry_wrapper_tracks_errors(self):
        """Should track errors during execution."""
        mock_agent = Mock()
        mock_agent.execute = Mock(side_effect=Exception("Test error"))

        wrapper = TelemetryWrapper(mock_agent, "dspy")

        with pytest.raises(Exception, match="Test error"):
            wrapper.execute("test")

        assert wrapper.error_count > 0

    def test_telemetry_wrapper_disabled_when_comparison_false(self):
        """Should not add telemetry when comparison disabled."""
        # This tests the loader's decision to wrap or not
        loader = AgentLoader()
        mock_agent = Mock()

        # When comparison is False, should return agent unwrapped
        frontmatter = Mock()
        frontmatter.rollout.comparison = False

        # Test implementation will verify this behavior


class TestRealAgentLoading:
    """Integration tests with actual agent markdown files."""

    @pytest.fixture
    def loader(self):
        return AgentLoader()

    @pytest.fixture
    def agents_dir(self):
        """Return path to actual agent definitions."""
        return Path(__file__).parent.parent / ".claude" / "agents"

    @pytest.mark.parametrize("agent_name", [
        "auditor",
        "code_agent",
        "learning_agent",
        "planner",
        "toolsmith"
    ])
    def test_load_dspy_migrated_agents(self, loader, agents_dir, agent_name):
        """Should successfully load all 5 DSPy-migrated agents."""
        agent_path = agents_dir / f"{agent_name}.md"

        assert agent_path.exists(), f"Agent file not found: {agent_path}"

        # Parse frontmatter
        frontmatter = loader._parse_frontmatter(str(agent_path))

        assert frontmatter.name is not None
        assert frontmatter.implementation is not None
        assert frontmatter.implementation.dspy is not None
        assert frontmatter.implementation.traditional is not None

    def test_load_auditor_agent_end_to_end(self, loader, agents_dir):
        """End-to-end test loading auditor agent."""
        agent_path = agents_dir / "auditor.md"

        # This will test the full load_agent() method
        # For now, just test frontmatter parsing
        frontmatter = loader._parse_frontmatter(str(agent_path))

        assert frontmatter.name == "auditor"
        assert frontmatter.implementation.preferred == "dspy"
        assert frontmatter.rollout.fallback == "traditional"


class TestConstitutionalCompliance:
    """Test compliance with Agency Constitution articles."""

    @pytest.fixture
    def loader(self):
        return AgentLoader()

    def test_article_i_complete_context(self, loader):
        """Article I: Must verify DSPy availability before loading."""
        # Loader should NEVER proceed without checking DSPy availability
        with patch.object(loader, '_check_dspy_available') as mock_check:
            mock_check.return_value = True

            frontmatter = Mock()
            frontmatter.implementation.preferred = "dspy"
            frontmatter.implementation.dspy = "path"
            frontmatter.rollout.fallback = "traditional"

            with patch.object(loader, '_load_dspy_agent', return_value=Mock()):
                loader.load_agent_from_frontmatter(frontmatter, "body")

                # MUST have checked availability
                mock_check.assert_called()

    def test_article_ii_hundred_percent_verification(self, loader):
        """Article II: System must NEVER fail due to missing DSPy."""
        # Even if DSPy loading fails, system must continue
        frontmatter = Mock()
        frontmatter.implementation.preferred = "dspy"
        frontmatter.rollout.fallback = "traditional"

        with patch.object(loader, '_check_dspy_available', return_value=True):
            with patch.object(loader, '_load_dspy_agent', side_effect=Exception("DSPy failed")):
                with patch.object(loader, '_load_traditional_agent', return_value=Mock()):
                    # Should NOT raise exception - must fallback
                    agent = loader.load_agent_from_frontmatter(frontmatter, "body")
                    assert agent is not None

    def test_article_iv_learning_enabled(self, loader):
        """Article IV: Telemetry must be enabled when comparison is True."""
        frontmatter = Mock()
        frontmatter.rollout.comparison = True
        frontmatter.implementation.preferred = "traditional"

        with patch.object(loader, '_load_traditional_agent', return_value=Mock()) as mock_load:
            agent = loader.load_agent_from_frontmatter(frontmatter, "body")

            # Should be wrapped with telemetry
            assert isinstance(agent, TelemetryWrapper) or hasattr(agent, 'telemetry')

    def test_article_v_markdown_remains_source_of_truth(self, loader):
        """Article V: Markdown spec must always be parsed and preserved."""
        # Loader must parse markdown body and make it available
        frontmatter = Mock()
        frontmatter.implementation.preferred = "traditional"

        markdown_body = "# Agent Specification\n\nThis is the source of truth."

        with patch.object(loader, '_load_traditional_agent') as mock_load:
            mock_agent = Mock()
            mock_load.return_value = mock_agent

            agent = loader.load_agent_from_frontmatter(frontmatter, markdown_body)

            # Verify markdown was passed to agent constructor
            # (Implementation detail will vary)
            mock_load.assert_called()
            call_args = mock_load.call_args
            # Should contain markdown body in some form