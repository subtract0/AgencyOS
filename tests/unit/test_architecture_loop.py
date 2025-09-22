"""
Unit tests for RunArchitectureLoop tool.
Tests audit analysis, VectorStore integration, and target selection logic.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
from chief_architect_agent.tools.architecture_loop import RunArchitectureLoop


class TestRunArchitectureLoop:
    """Test RunArchitectureLoop tool functionality."""

    @pytest.fixture
    def tool_instance(self):
        """Create a RunArchitectureLoop instance."""
        return RunArchitectureLoop(
            target_path="/test/path",
            objective="test objective"
        )

    def test_initialization(self):
        """Test tool initialization with default and custom parameters."""
        # Test with defaults
        tool = RunArchitectureLoop()
        assert tool.target_path == os.getcwd()
        assert tool.objective == "auto"

        # Test with custom parameters
        tool = RunArchitectureLoop(
            target_path="/custom/path",
            objective="custom objective"
        )
        assert tool.target_path == "/custom/path"
        assert tool.objective == "custom objective"

    def test_run_basic_flow(self, tool_instance):
        """Test basic run flow with mocked dependencies."""
        with patch('chief_architect_agent.tools.architecture_loop.ASTAnalyzer') as mock_analyzer_class, \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore') as mock_vs_class, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch.object(tool_instance, '_detect_vectorstore_api_mismatches') as mock_detect, \
             patch.object(tool_instance, '_choose_high_impact_target') as mock_choose:

            # Setup mocks
            mock_analyzer = Mock()
            mock_analyzer.analyze_directory.return_value = {
                "total_behaviors": 100,
                "total_test_functions": 80,
                "coverage_ratio": 0.8
            }
            mock_analyzer_class.return_value = mock_analyzer

            mock_vs = Mock()
            mock_vs.get_stats.return_value = {
                "total_memories": 50,
                "total_embeddings": 200
            }
            mock_vs_class.return_value = mock_vs

            mock_detect.return_value = {"issues": []}
            mock_choose.return_value = {
                "title": "Test target",
                "reason": "Test reason"
            }

            # Run the tool
            result = tool_instance.run()

            # Verify calls
            assert mock_analyzer_class.called
            mock_analyzer.analyze_directory.assert_called_with("/test/path")
            assert mock_vs_class.called
            mock_vs.get_stats.assert_called_once()
            assert mock_detect.called
            assert mock_choose.called

            # Verify result structure
            result_data = json.loads(result)
            assert "timestamp" in result_data
            assert "audit" in result_data
            assert result_data["audit"]["total_behaviors"] == 100
            assert result_data["audit"]["total_tests"] == 80
            assert "vector_store_stats" in result_data
            assert "api_mismatches" in result_data
            assert "selected_target" in result_data

    def test_detect_vectorstore_api_mismatches(self, tool_instance):
        """Test VectorStore API mismatch detection."""
        # Test when VectorStore has search method
        with patch('inspect.getmembers') as mock_getmembers, \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore'):

            mock_getmembers.return_value = [
                ('search', Mock()),
                ('store', Mock()),
                ('get_stats', Mock())
            ]

            result = tool_instance._detect_vectorstore_api_mismatches()

            assert "issues" in result
            assert len(result["issues"]) == 0

        # Test when VectorStore missing search method
        with patch('inspect.getmembers') as mock_getmembers, \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore'):

            mock_getmembers.return_value = [
                ('store', Mock()),
                ('get_stats', Mock())
            ]

            result = tool_instance._detect_vectorstore_api_mismatches()

            assert "issues" in result
            assert len(result["issues"]) > 0
            assert any("missing .search API" in issue for issue in result["issues"])

    def test_detect_vectorstore_api_mismatches_error_handling(self, tool_instance):
        """Test error handling in API mismatch detection."""
        with patch('inspect.getmembers') as mock_getmembers:
            mock_getmembers.side_effect = Exception("Import error")

            result = tool_instance._detect_vectorstore_api_mismatches()

            assert "error" in result
            assert "Import error" in result["error"]

    def test_choose_high_impact_target_vectorstore_issues(self, tool_instance):
        """Test target selection when VectorStore issues exist."""
        findings = {
            "api_mismatches": {
                "issues": ["VectorStore missing .search API used by LearningAgent"]
            }
        }

        result = tool_instance._choose_high_impact_target(findings)

        assert result["title"] == "Harmonize VectorStore API with LearningAgent"
        assert "continuous learning pipeline" in result["reason"]

    def test_choose_high_impact_target_no_issues(self, tool_instance):
        """Test target selection with no specific issues."""
        findings = {
            "api_mismatches": {
                "issues": []
            }
        }

        result = tool_instance._choose_high_impact_target(findings)

        assert result["title"] == "Improve test coverage"
        assert result["reason"] == "Default fallback"

    def test_file_output_creation(self, tool_instance):
        """Test that findings are written to log file."""
        with patch('chief_architect_agent.tools.architecture_loop.ASTAnalyzer') as mock_analyzer_class, \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore') as mock_vs_class, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch.object(tool_instance, '_detect_vectorstore_api_mismatches') as mock_detect, \
             patch.object(tool_instance, '_choose_high_impact_target') as mock_choose:

            # Setup minimal mocks
            mock_analyzer = Mock()
            mock_analyzer.analyze_directory.return_value = {
                "total_behaviors": 10,
                "total_test_functions": 5
            }
            mock_analyzer_class.return_value = mock_analyzer

            mock_vs = Mock()
            mock_vs.get_stats.return_value = {}
            mock_vs_class.return_value = mock_vs

            mock_detect.return_value = {"issues": []}
            mock_choose.return_value = {"title": "Test", "reason": "Test"}

            # Run the tool
            tool_instance.run()

            # Verify file operations
            mock_makedirs.assert_called_with("logs", exist_ok=True)
            mock_file.assert_called_with(
                os.path.join("logs", "chief_architect_findings.json"), "w"
            )

    def test_file_output_error_handling(self, tool_instance):
        """Test graceful handling of file write errors."""
        with patch('chief_architect_agent.tools.architecture_loop.ASTAnalyzer') as mock_analyzer_class, \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore') as mock_vs_class, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open') as mock_file_open, \
             patch.object(tool_instance, '_detect_vectorstore_api_mismatches') as mock_detect, \
             patch.object(tool_instance, '_choose_high_impact_target') as mock_choose:

            # Setup mocks
            mock_analyzer = Mock()
            mock_analyzer.analyze_directory.return_value = {
                "total_behaviors": 10,
                "total_test_functions": 5
            }
            mock_analyzer_class.return_value = mock_analyzer

            mock_vs = Mock()
            mock_vs.get_stats.return_value = {}
            mock_vs_class.return_value = mock_vs

            mock_detect.return_value = {"issues": []}
            mock_choose.return_value = {"title": "Test", "reason": "Test"}

            # Simulate file write error
            mock_file_open.side_effect = IOError("Permission denied")

            # Run should not raise exception
            result = tool_instance.run()

            # Should still return valid JSON
            result_data = json.loads(result)
            assert "timestamp" in result_data
            assert "audit" in result_data

    def test_comprehensive_findings_structure(self, tool_instance):
        """Test that all expected fields are in findings output."""
        with patch('chief_architect_agent.tools.architecture_loop.ASTAnalyzer') as mock_analyzer_class, \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore') as mock_vs_class, \
             patch('os.makedirs'), \
             patch('builtins.open', mock_open()), \
             patch.object(tool_instance, '_detect_vectorstore_api_mismatches') as mock_detect, \
             patch.object(tool_instance, '_choose_high_impact_target') as mock_choose:

            # Setup comprehensive mocks
            mock_analyzer = Mock()
            mock_analyzer.analyze_directory.return_value = {
                "total_behaviors": 150,
                "total_test_functions": 120,
                "coverage_ratio": 0.8,
                "source_files": ["file1.py", "file2.py"],
                "test_files": ["test_file1.py", "test_file2.py"]
            }
            mock_analyzer_class.return_value = mock_analyzer

            mock_vs = Mock()
            mock_vs.get_stats.return_value = {
                "total_memories": 100,
                "total_embeddings": 500,
                "dimensions": 768
            }
            mock_vs_class.return_value = mock_vs

            mock_detect.return_value = {
                "issues": ["Issue 1", "Issue 2"],
                "learning_uses_search": True
            }

            mock_choose.return_value = {
                "title": "Critical improvement",
                "reason": "High impact on system"
            }

            # Run the tool
            result = tool_instance.run()
            result_data = json.loads(result)

            # Verify comprehensive structure
            assert "timestamp" in result_data
            assert datetime.fromisoformat(result_data["timestamp"])  # Valid ISO timestamp

            assert "audit" in result_data
            assert result_data["audit"]["total_behaviors"] == 150
            assert result_data["audit"]["total_tests"] == 120

            assert "vector_store_stats" in result_data
            assert result_data["vector_store_stats"]["total_memories"] == 100

            assert "api_mismatches" in result_data
            assert len(result_data["api_mismatches"]["issues"]) == 2

            assert "selected_target" in result_data
            assert result_data["selected_target"]["title"] == "Critical improvement"

    def test_learning_agent_import_check(self, tool_instance):
        """Test checking for LearningAgent StoreKnowledge import."""
        # Test when import exists
        with patch('inspect.getmembers'), \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore'), \
             patch('learning_agent.tools.store_knowledge.StoreKnowledge'):

            result = tool_instance._detect_vectorstore_api_mismatches()
            assert result.get("learning_uses_search") == True

        # Test when import fails - simplified version
        with patch('inspect.getmembers') as mock_getmembers:
            mock_getmembers.side_effect = Exception("Module not found")

            result = tool_instance._detect_vectorstore_api_mismatches()
            # Should handle gracefully and include error
            assert "error" in result

    def test_target_selection_priority(self, tool_instance):
        """Test that target selection follows correct priority."""
        # VectorStore issues should take priority
        findings_with_vs_issues = {
            "api_mismatches": {
                "issues": ["VectorStore problem"]
            },
            "audit": {
                "total_behaviors": 100,
                "total_tests": 10  # Low coverage
            }
        }

        result = tool_instance._choose_high_impact_target(findings_with_vs_issues)
        assert "VectorStore" in result["title"]

        # No VectorStore issues, fallback to coverage
        findings_no_vs_issues = {
            "api_mismatches": {
                "issues": []
            },
            "audit": {
                "total_behaviors": 100,
                "total_tests": 10
            }
        }

        result = tool_instance._choose_high_impact_target(findings_no_vs_issues)
        assert result["title"] == "Improve test coverage"

    def test_objective_parameter_usage(self):
        """Test that objective parameter is properly used."""
        # Test with auto objective
        tool_auto = RunArchitectureLoop(objective="auto")
        assert tool_auto.objective == "auto"

        # Test with custom objective
        tool_custom = RunArchitectureLoop(objective="Fix critical bug in authentication")
        assert tool_custom.objective == "Fix critical bug in authentication"

        # Though the current implementation doesn't use objective in logic,
        # verify it's stored for future use
        with patch('chief_architect_agent.tools.architecture_loop.ASTAnalyzer'), \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore'), \
             patch('os.makedirs'), \
             patch('builtins.open', mock_open()):

            # The objective should be available for future enhancements
            assert hasattr(tool_custom, 'objective')

    def test_concurrent_execution_safety(self):
        """Test that multiple instances can run safely."""
        tool1 = RunArchitectureLoop(target_path="/path1")
        tool2 = RunArchitectureLoop(target_path="/path2")

        with patch('chief_architect_agent.tools.architecture_loop.ASTAnalyzer') as mock_analyzer_class, \
             patch('chief_architect_agent.tools.architecture_loop.VectorStore') as mock_vs_class, \
             patch('os.makedirs'), \
             patch('builtins.open', mock_open()):

            mock_analyzer = Mock()
            mock_analyzer.analyze_directory.return_value = {
                "total_behaviors": 10,
                "total_test_functions": 5
            }
            mock_analyzer_class.return_value = mock_analyzer

            mock_vs = Mock()
            mock_vs.get_stats.return_value = {
                "total_memories": 10,
                "total_embeddings": 20
            }
            mock_vs_class.return_value = mock_vs

            # Both should work independently
            result1 = tool1.run()
            result2 = tool2.run()

            assert json.loads(result1)
            assert json.loads(result2)

            # Verify each used their own path
            calls = mock_analyzer.analyze_directory.call_args_list
            assert any(call[0][0] == "/path1" for call in calls)
            assert any(call[0][0] == "/path2" for call in calls)