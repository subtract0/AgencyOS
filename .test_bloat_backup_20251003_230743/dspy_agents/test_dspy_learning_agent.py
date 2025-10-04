"""
Comprehensive test suite for DSPyLearningAgent

Tests the DSPy-powered Learning Agent implementation for pattern extraction,
knowledge consolidation, and learning capabilities.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Import the DSPyLearningAgent and related classes
from dspy_agents.modules.learning_agent import (
    ConsolidatedLearning,
    DSPyLearningAgent,
    ExtractedPattern,
    LearningContext,
    LearningResult,
    create_dspy_learning_agent,
)


class TestDSPyLearningAgent:
    """Test suite for DSPyLearningAgent."""

    @pytest.fixture
    def agent(self):
        """Create a DSPyLearningAgent instance for testing."""
        return DSPyLearningAgent(
            model="gpt-4o-mini", reasoning_effort="high", enable_learning=True, min_confidence=0.7
        )

    @pytest.fixture
    def sample_session_data(self):
        """Create sample session data for testing."""
        return {
            "session_id": "test_session_001",
            "timestamp": datetime.now().isoformat(),
            "tool_calls": [
                {"tool": "Read", "status": "success"},
                {"tool": "Write", "status": "success"},
                {"tool": "Test", "status": "success"},
            ],
            "errors": [
                {"type": "FileNotFoundError", "resolved": True},
            ],
            "agent_interactions": [
                {"from": "planner", "to": "coder", "message": "implement feature"},
                {"from": "coder", "to": "tester", "message": "test implementation"},
            ],
            "task_completions": [
                {"task": "implement feature X", "success": True, "duration": 120},
            ],
        }

    @pytest.fixture
    def sample_patterns(self):
        """Create sample patterns for testing."""
        return [
            ExtractedPattern(
                pattern_type="tool_usage",
                description="Frequent use of Read->Write->Test sequence",
                confidence=0.85,
                occurrences=5,
                context={"tools": ["Read", "Write", "Test"]},
                keywords=["tool_sequence", "read_write_test"],
            ),
            ExtractedPattern(
                pattern_type="error_resolution",
                description="FileNotFoundError successfully resolved",
                confidence=0.75,
                occurrences=3,
                context={"error_type": "FileNotFoundError"},
                keywords=["error_handling", "file_errors"],
            ),
        ]

    @pytest.fixture
    def sample_learnings(self):
        """Create sample consolidated learnings for testing."""
        return [
            ConsolidatedLearning(
                title="Effective Tool Sequence Pattern",
                summary="Read->Write->Test sequence shows high success rate",
                patterns=[],
                actionable_insights=[
                    "Continue using this sequence for file modifications",
                    "Consider creating a composite tool for this pattern",
                ],
                confidence=0.85,
                tags=["tool_usage", "best_practice"],
            )
        ]

    def test_agent_initialization(self):
        """Test that the agent initializes correctly."""
        agent = DSPyLearningAgent(
            model="gpt-4o-mini",
            reasoning_effort="medium",
            enable_learning=False,
            min_confidence=0.8,
        )

        assert agent.model == "gpt-4o-mini"
        assert agent.reasoning_effort == "medium"
        assert agent.enable_learning is False
        assert agent.min_confidence == 0.8
        assert agent.knowledge_base == {}
        assert agent.pattern_history == []

    def test_factory_function(self):
        """Test the factory function creates agents correctly."""
        agent = create_dspy_learning_agent(
            model="gpt-5", reasoning_effort="low", enable_learning=True, min_confidence=0.6
        )

        assert isinstance(agent, DSPyLearningAgent)
        assert agent.model == "gpt-5"
        assert agent.reasoning_effort == "low"
        assert agent.enable_learning is True
        assert agent.min_confidence == 0.6

    @patch("dspy_agents.modules.learning_agent.DSPY_AVAILABLE", False)
    def test_fallback_mode(self, agent):
        """Test fallback behavior when DSPy is not available."""
        result = agent.forward(session_data={"tool_calls": [1, 2, 3], "errors": [1]})

        assert result.success is False
        assert "DSPy not available" in result.message
        assert result.patterns_extracted > 0  # Basic patterns extracted

    def test_analyze_session(self, agent, sample_session_data, tmp_path):
        """Test analyzing a session from file."""
        # Create a temporary session file
        session_file = tmp_path / "test_session.json"
        with open(session_file, "w") as f:
            json.dump(sample_session_data, f)

        with patch.object(agent, "forward") as mock_forward:
            mock_forward.return_value = LearningResult(
                success=True,
                patterns_extracted=5,
                learnings_consolidated=2,
                knowledge_stored=True,
                message="Analysis complete",
            )

            result = agent.analyze_session(str(session_file))

            assert result["success"] is True
            assert result["patterns"] == 5
            assert result["learnings"] == 2
            mock_forward.assert_called_once()

    def test_extract_insights(self, agent, sample_patterns):
        """Test extracting insights from patterns."""
        # Add more patterns to meet minimum occurrences
        patterns = sample_patterns * 2  # Duplicate to have 4 patterns

        insights = agent.extract_insights(patterns, min_occurrences=2)

        assert len(insights) == 2  # One for each pattern type
        assert insights[0]["type"] in ["tool_usage", "error_resolution"]
        assert insights[0]["frequency"] == 2
        assert "patterns" in insights[0]

    def test_consolidate_learning(self, agent):
        """Test consolidating insights into learnings."""
        insights = [
            {
                "type": "tool_usage",
                "frequency": 3,
                "avg_confidence": 0.82,
                "description": "Recurring tool pattern",
                "patterns": [],
            }
        ]

        learnings = agent.consolidate_learning(insights)

        assert len(learnings) == 1
        assert (
            learnings[0].title == "Tool Usage Pattern"
        )  # Note: underscores are replaced with spaces
        assert learnings[0].confidence == 0.82
        assert "tool_usage" in learnings[0].tags

    def test_consolidate_learning_with_existing(self, agent, sample_learnings):
        """Test consolidating with existing learnings."""
        insights = [
            {
                "type": "tool_usage",
                "frequency": 2,
                "avg_confidence": 0.78,
                "description": "Similar tool pattern",
                "patterns": [],
            }
        ]

        # Test that it can build on existing learnings
        learnings = agent.consolidate_learning(insights, sample_learnings)

        # Should create new learning since _is_related_learning checks for exact tag match
        # and the insight type "tool_usage" matches the tag in sample_learnings
        # The implementation creates a new learning when not related
        assert len(learnings) == 1

    def test_store_knowledge(self, agent, sample_learnings):
        """Test storing learnings in knowledge base."""
        result = agent.store_knowledge(sample_learnings)

        assert result is True
        assert "tool_usage" in agent.knowledge_base
        assert len(agent.knowledge_base["tool_usage"]) == 1
        assert agent.knowledge_base["tool_usage"][0].title == sample_learnings[0].title

    def test_query_knowledge(self, agent, sample_learnings):
        """Test querying the knowledge base."""
        # Store some learnings first
        agent.store_knowledge(sample_learnings)

        # Query by keyword
        results = agent.query_knowledge("tool")
        assert len(results) == 1
        assert results[0].title == sample_learnings[0].title

        # Query by category
        results = agent.query_knowledge("", category="tool_usage")
        assert len(results) == 1

        # Query with confidence threshold
        results = agent.query_knowledge("tool", min_confidence=0.9)
        assert len(results) == 0  # Sample has 0.85 confidence

    def test_learning_context_validation(self, agent):
        """Test LearningContext validation."""
        context = LearningContext(
            session_id="test_001",
            logs_directory="custom/logs",
            memory_store="database",
            pattern_types=["custom_pattern"],
            confidence_threshold=0.9,
        )

        assert context.session_id == "test_001"
        assert context.logs_directory == "custom/logs"
        assert context.memory_store == "database"
        assert context.pattern_types == ["custom_pattern"]
        assert context.confidence_threshold == 0.9

    @patch("dspy_agents.modules.learning_agent.DSPY_AVAILABLE", True)
    def test_forward_with_dspy(self, agent, sample_session_data):
        """Test forward method with DSPy available."""
        # Mock DSPy modules
        with (
            patch.object(agent, "pattern_extractor") as mock_extractor,
            patch.object(agent, "consolidator") as mock_consolidator,
            patch.object(agent, "storage") as mock_storage,
        ):
            # Configure mock returns
            mock_extractor.return_value = MagicMock(
                patterns=[{"pattern_type": "tool_usage", "confidence": 0.8}],
                confidence_scores={"tool_usage": 0.8},
            )

            mock_consolidator.return_value = MagicMock(
                consolidated_learnings=[
                    {
                        "title": "Test Learning",
                        "summary": "Test summary",
                        "patterns": [],
                        "actionable_insights": ["Test insight"],
                        "confidence": 0.85,
                        "tags": ["test"],
                    }
                ]
            )

            mock_storage.return_value = MagicMock(
                storage_confirmation=True, storage_ids=["id1", "id2"]
            )

            result = agent.forward(session_data=sample_session_data, pattern_types=["tool_usage"])

            assert result.success is True
            assert result.patterns_extracted == 1
            assert result.learnings_consolidated == 1
            assert result.knowledge_stored is True
            assert "storage_ids" in result.details

    def test_get_learning_summary(self, agent, sample_learnings):
        """Test getting a summary of the knowledge base."""
        agent.store_knowledge(sample_learnings)

        summary = agent.get_learning_summary()

        assert summary["total_categories"] == 1
        assert summary["total_learnings"] == 1
        assert "tool_usage" in summary["categories"]
        assert summary["avg_confidence"] == 0.85

    def test_reset_knowledge(self, agent, sample_learnings):
        """Test resetting the knowledge base."""
        agent.store_knowledge(sample_learnings)
        assert len(agent.knowledge_base) > 0

        agent.reset_knowledge()

        assert len(agent.knowledge_base) == 0
        assert len(agent.pattern_history) == 0

    def test_load_session_data(self, agent, sample_session_data, tmp_path):
        """Test loading session data from file."""
        # Create test context
        context = LearningContext(session_id="test_session", logs_directory=str(tmp_path))

        # Create session file
        session_file = tmp_path / "test_session.json"
        with open(session_file, "w") as f:
            json.dump(sample_session_data, f)

        # Load data
        data = agent._load_session_data(context)

        assert data["session_id"] == sample_session_data["session_id"]
        assert data["tool_calls"] == sample_session_data["tool_calls"]

    def test_load_missing_session_data(self, agent, tmp_path):
        """Test loading when session file doesn't exist."""
        context = LearningContext(session_id="missing_session", logs_directory=str(tmp_path))

        data = agent._load_session_data(context)

        assert data["session_id"] == "missing_session"
        assert "timestamp" in data
        assert data["events"] == []

    def test_is_related_learning(self, agent, sample_learnings):
        """Test checking if insight relates to existing learning."""
        insight = {"type": "tool_usage"}
        learning = sample_learnings[0]

        is_related = agent._is_related_learning(insight, learning)
        assert is_related is True

        insight = {"type": "different_type"}
        is_related = agent._is_related_learning(insight, learning)
        assert is_related is False

    def test_process_patterns_error_handling(self, agent):
        """Test error handling in pattern processing."""
        # Test with invalid extraction result
        invalid_result = "not_an_object"
        patterns = agent._process_patterns(invalid_result)
        assert patterns == []

        # Test with object missing attributes
        mock_result = MagicMock()
        del mock_result.patterns
        patterns = agent._process_patterns(mock_result)
        assert patterns == []

    def test_knowledge_base_size_limit(self, agent):
        """Test that knowledge base has size limits."""
        # Create many learnings
        for i in range(150):
            learning = ConsolidatedLearning(
                title=f"Learning {i}",
                summary=f"Summary {i}",
                patterns=[],
                actionable_insights=[],
                confidence=0.8,
                tags=["test_category"],
            )
            agent._update_knowledge_base(
                [learning.model_dump()], LearningContext(session_id="test")
            )

        # Check that size is limited
        assert len(agent.knowledge_base["test_category"]) <= 100

    def test_pattern_extraction_types(self, agent):
        """Test different pattern type extraction."""
        session_data = {
            "tool_calls": [1, 2, 3],
            "errors": [1, 2],
            "workflows": [1],
            "optimizations": [1, 2, 3, 4],
        }

        # Test fallback extraction with different pattern types
        result = agent._fallback_execution(
            LearningContext(session_id="test", pattern_types=["tool_usage", "error_resolution"]),
            session_data,
        )

        assert result.patterns_extracted >= 2
        assert "tool_usage" in str(result.details)
        assert "error_resolution" in str(result.details)

    def test_confidence_filtering(self, agent):
        """Test that patterns are filtered by confidence."""
        # Create patterns with varying confidence
        patterns = [
            ExtractedPattern(
                pattern_type="high_conf",
                description="High confidence pattern",
                confidence=0.9,
                occurrences=5,
            ),
            ExtractedPattern(
                pattern_type="low_conf",
                description="Low confidence pattern",
                confidence=0.5,
                occurrences=5,
            ),
        ]

        # Store as learnings with different confidence
        agent.store_knowledge(
            [
                ConsolidatedLearning(
                    title="High Conf",
                    summary="High",
                    patterns=[patterns[0]],
                    actionable_insights=[],
                    confidence=0.9,
                    tags=["test"],
                ),
                ConsolidatedLearning(
                    title="Low Conf",
                    summary="Low",
                    patterns=[patterns[1]],
                    actionable_insights=[],
                    confidence=0.5,
                    tags=["test"],
                ),
            ]
        )

        # Query with high confidence threshold
        results = agent.query_knowledge("", min_confidence=0.8)
        assert len(results) == 1
        assert results[0].title == "High Conf"


class TestLearningIntegration:
    """Integration tests for DSPyLearningAgent."""

    @pytest.fixture
    def agent_with_knowledge(self):
        """Create an agent with pre-loaded knowledge."""
        agent = DSPyLearningAgent(enable_learning=True)

        # Add some knowledge
        learnings = [
            ConsolidatedLearning(
                title="TDD Pattern",
                summary="Test-driven development improves quality",
                patterns=[],
                actionable_insights=["Write tests first"],
                confidence=0.9,
                tags=["testing", "best_practice"],
            ),
            ConsolidatedLearning(
                title="Error Handling",
                summary="Proper error handling prevents crashes",
                patterns=[],
                actionable_insights=["Use try-except blocks"],
                confidence=0.85,
                tags=["error_handling", "reliability"],
            ),
        ]

        agent.store_knowledge(learnings)
        return agent

    def test_knowledge_persistence(self, agent_with_knowledge):
        """Test that knowledge persists across operations."""
        initial_summary = agent_with_knowledge.get_learning_summary()
        assert initial_summary["total_learnings"] == 2

        # Perform operations
        agent_with_knowledge.query_knowledge("test")

        # Check knowledge still exists
        final_summary = agent_with_knowledge.get_learning_summary()
        assert final_summary["total_learnings"] == 2

    def test_cross_category_query(self, agent_with_knowledge):
        """Test querying across multiple categories."""
        results = agent_with_knowledge.query_knowledge("pattern")
        assert len(results) == 1  # Only TDD Pattern matches

        results = agent_with_knowledge.query_knowledge("error")
        assert len(results) == 1  # Only Error Handling matches

        results = agent_with_knowledge.query_knowledge("nonexistent_query")
        assert len(results) == 0  # Query with no matches returns nothing

    def test_end_to_end_learning_flow(self, tmp_path):
        """Test complete learning flow from session to stored knowledge."""
        # Patch DSPY_AVAILABLE to ensure we can test properly
        with patch("dspy_agents.modules.learning_agent.DSPY_AVAILABLE", True):
            agent = DSPyLearningAgent(enable_learning=True)

            # Create session data
            session_data = {
                "session_id": "e2e_test",
                "tool_calls": ["Read", "Write", "Test"] * 3,
                "errors": ["TypeError"] * 2,
            }

            # Create session file
            logs_dir = tmp_path / "logs"
            logs_dir.mkdir()
            session_file = logs_dir / "e2e_test.json"
            with open(session_file, "w") as f:
                json.dump(session_data, f)

            # Mock DSPy components for consistent testing
            with (
                patch.object(agent, "pattern_extractor") as mock_extractor,
                patch.object(agent, "consolidator") as mock_consolidator,
                patch.object(agent, "storage") as mock_storage,
            ):
                mock_extractor.return_value = MagicMock(
                    patterns=[{"pattern_type": "test", "confidence": 0.8}],
                    confidence_scores={"test": 0.8},
                )

                mock_consolidator.return_value = MagicMock(
                    consolidated_learnings=[
                        {
                            "title": "E2E Learning",
                            "summary": "End-to-end test",
                            "patterns": [],
                            "actionable_insights": ["Test insight"],
                            "confidence": 0.85,
                            "tags": ["e2e"],
                        }
                    ]
                )

                mock_storage.return_value = MagicMock(
                    storage_confirmation=True, storage_ids=["e2e_001"]
                )

                # Execute learning
                result = agent.forward(
                    session_id="e2e_test", context={"logs_directory": str(logs_dir)}
                )

                assert result.success is True
                assert result.patterns_extracted > 0
                assert result.learnings_consolidated > 0

                # Verify knowledge was stored
                summary = agent.get_learning_summary()
                assert summary["total_learnings"] > 0


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
