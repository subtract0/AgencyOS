"""
Comprehensive unit tests for the Pattern Extraction Logic.

Tests follow the NECESSARY pattern:
- N: No Missing Behaviors - All code paths covered
- E: Edge Cases - Boundary conditions tested
- C: Comprehensive - Multiple test vectors per function
- E: Error Conditions - Exception handling verified
- S: State Validation - Object state changes confirmed
- S: Side Effects - External impacts tested
- A: Async Operations - Concurrent code coverage (N/A for this module)
- R: Regression Prevention - Historical bugs covered
- Y: Yielding Confidence - Overall quality assurance

Constitutional Compliance:
- Article I: Complete context gathering for all test scenarios
- Article II: 100% test verification with comprehensive coverage
- Article III: Automated test execution and validation
- Article IV: Integration with learning systems
- Article V: Spec-driven test implementation following SPEC-LEARNING-001
"""

import os
import sys
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from learning_loop.pattern_extraction import (
    Trigger, ErrorTrigger, TaskTrigger, Condition, Action, PatternMetadata,
    EnhancedPattern, Operation, FailureReason, TestFailureAnalysis, ExecutionError,
    AntiPattern, PatternExtractor, FailureLearner
)
from core.patterns import Pattern as ExistingPattern


class TestTrigger:
    """Test the base Trigger class and its serialization."""

    def test_trigger_creation(self):
        """Test basic trigger creation with required fields."""
        metadata = {"source": "test", "priority": 5}

        trigger = Trigger(
            type="test_trigger",
            metadata=metadata
        )

        assert trigger.type == "test_trigger"
        assert trigger.metadata == metadata

    def test_trigger_to_dict(self):
        """Test trigger serialization to dictionary."""
        trigger = Trigger(
            type="error",
            metadata={"error_type": "NoneType", "severity": "high"}
        )

        result = trigger.to_dict()

        assert result["type"] == "error"
        assert result["metadata"]["error_type"] == "NoneType"
        assert result["metadata"]["severity"] == "high"

    def test_trigger_from_dict(self):
        """Test trigger deserialization from dictionary."""
        data = {
            "type": "task",
            "metadata": {"keywords": ["fix", "error"], "complexity": "medium"}
        }

        trigger = Trigger.from_dict(data)

        assert trigger.type == "task"
        assert trigger.metadata["keywords"] == ["fix", "error"]
        assert trigger.metadata["complexity"] == "medium"

    def test_trigger_round_trip_serialization(self):
        """Test that trigger serialization is reversible."""
        original = Trigger(
            type="complex_trigger",
            metadata={"nested": {"data": [1, 2, 3]}, "simple": "value"}
        )

        serialized = original.to_dict()
        restored = Trigger.from_dict(serialized)

        assert restored.type == original.type
        assert restored.metadata == original.metadata


class TestErrorTrigger:
    """Test ErrorTrigger class with error-specific metadata."""

    def test_error_trigger_creation(self):
        """Test ErrorTrigger creation with all fields."""
        error_trigger = ErrorTrigger(
            error_type="NoneType",
            error_pattern=r"AttributeError.*'NoneType'.*has no attribute.*"
        )

        assert error_trigger.type == "error"
        assert error_trigger.error_type == "NoneType"
        assert error_trigger.error_pattern == r"AttributeError.*'NoneType'.*has no attribute.*"
        assert error_trigger.metadata["error_type"] == "NoneType"
        assert error_trigger.metadata["error_pattern"] == error_trigger.error_pattern

    def test_error_trigger_post_init_metadata_population(self):
        """Test that ErrorTrigger auto-populates metadata in __post_init__."""
        error_trigger = ErrorTrigger(
            error_type="ImportError",
            error_pattern=r"ImportError|ModuleNotFoundError"
        )

        # Verify metadata is populated
        assert error_trigger.metadata["error_type"] == "ImportError"
        assert error_trigger.metadata["error_pattern"] == r"ImportError|ModuleNotFoundError"

    def test_error_trigger_existing_metadata_preserved(self):
        """Test that metadata is properly populated during construction."""
        error_trigger = ErrorTrigger(
            error_type="SyntaxError",
            error_pattern=r"SyntaxError.*line\s+\d+"
        )

        # Auto-populated metadata should be present
        assert error_trigger.metadata["error_type"] == "SyntaxError"
        assert error_trigger.metadata["error_pattern"] == r"SyntaxError.*line\s+\d+"
        assert error_trigger.type == "error"


class TestTaskTrigger:
    """Test TaskTrigger class with task-specific metadata."""

    def test_task_trigger_creation(self):
        """Test TaskTrigger creation with keywords."""
        task_trigger = TaskTrigger(
            keywords=["fix", "import", "error"]
        )

        assert task_trigger.type == "task"
        assert task_trigger.keywords == ["fix", "import", "error"]
        assert task_trigger.metadata["keywords"] == ["fix", "import", "error"]

    def test_task_trigger_empty_keywords(self):
        """Test TaskTrigger with empty keywords list."""
        task_trigger = TaskTrigger(keywords=[])

        assert task_trigger.keywords == []
        assert task_trigger.metadata["keywords"] == []

    def test_task_trigger_complex_keywords(self):
        """Test TaskTrigger with complex keyword patterns."""
        complex_keywords = ["refactor_method", "add_null_check", "update_imports"]
        task_trigger = TaskTrigger(keywords=complex_keywords)

        assert task_trigger.keywords == complex_keywords
        assert task_trigger.metadata["keywords"] == complex_keywords


class TestCondition:
    """Test Condition class and evaluation logic."""

    def test_condition_creation(self):
        """Test Condition creation with all fields."""
        condition = Condition(
            type="file_exists",
            target="/path/to/file.py",
            value=True,
            operator="equals"
        )

        assert condition.type == "file_exists"
        assert condition.target == "/path/to/file.py"
        assert condition.value is True
        assert condition.operator == "equals"

    def test_condition_default_operator(self):
        """Test Condition with default operator."""
        condition = Condition(
            type="test_passes",
            target="test_module",
            value=True
        )

        assert condition.operator == "equals"

    @patch('pathlib.Path.exists')
    def test_evaluate_file_exists_true(self, mock_exists):
        """Test evaluating file_exists condition when file exists."""
        mock_exists.return_value = True

        condition = Condition(
            type="file_exists",
            target="/test/file.py",
            value=True
        )

        result = condition.evaluate({})

        assert result is True
        mock_exists.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_evaluate_file_exists_false(self, mock_exists):
        """Test evaluating file_exists condition when file doesn't exist."""
        mock_exists.return_value = False

        condition = Condition(
            type="file_exists",
            target="/nonexistent/file.py",
            value=True
        )

        result = condition.evaluate({})

        assert result is False

    def test_evaluate_test_passes_true(self):
        """Test evaluating test_passes condition when tests pass."""
        condition = Condition(
            type="test_passes",
            target="test_results",
            value=True
        )

        context = {"tests_passing": True}
        result = condition.evaluate(context)

        assert result is True

    def test_evaluate_test_passes_false(self):
        """Test evaluating test_passes condition when tests fail."""
        condition = Condition(
            type="test_passes",
            target="test_results",
            value=True
        )

        context = {"tests_passing": False}
        result = condition.evaluate(context)

        assert result is False

    def test_evaluate_error_absent_true(self):
        """Test evaluating error_absent condition when error is not present."""
        condition = Condition(
            type="error_absent",
            target="ImportError",
            value="ImportError"
        )

        context = {"errors": ["SyntaxError", "NameError"]}
        result = condition.evaluate(context)

        assert result is True

    def test_evaluate_error_absent_false(self):
        """Test evaluating error_absent condition when error is present."""
        condition = Condition(
            type="error_absent",
            target="ImportError",
            value="ImportError"
        )

        context = {"errors": ["ImportError", "SyntaxError"]}
        result = condition.evaluate(context)

        assert result is False

    def test_evaluate_generic_equals_true(self):
        """Test evaluating generic condition with equals operator (true)."""
        condition = Condition(
            type="generic",
            target="status",
            value="success",
            operator="equals"
        )

        context = {"status": "success"}
        result = condition.evaluate(context)

        assert result is True

    def test_evaluate_generic_equals_false(self):
        """Test evaluating generic condition with equals operator (false)."""
        condition = Condition(
            type="generic",
            target="status",
            value="success",
            operator="equals"
        )

        context = {"status": "failed"}
        result = condition.evaluate(context)

        assert result is False

    def test_evaluate_generic_contains_true(self):
        """Test evaluating generic condition with contains operator (true)."""
        condition = Condition(
            type="generic",
            target="message",
            value="error",
            operator="contains"
        )

        context = {"message": "This is an error message"}
        result = condition.evaluate(context)

        assert result is True

    def test_evaluate_generic_contains_false(self):
        """Test evaluating generic condition with contains operator (false)."""
        condition = Condition(
            type="generic",
            target="message",
            value="success",
            operator="contains"
        )

        context = {"message": "This is an error message"}
        result = condition.evaluate(context)

        assert result is False

    def test_evaluate_generic_matches_true(self):
        """Test evaluating generic condition with matches operator (true)."""
        condition = Condition(
            type="generic",
            target="log",
            value=r"ERROR.*line\s+\d+",
            operator="matches"
        )

        context = {"log": "ERROR: Syntax error at line 42"}
        result = condition.evaluate(context)

        assert result is True

    def test_evaluate_generic_matches_false(self):
        """Test evaluating generic condition with matches operator (false)."""
        condition = Condition(
            type="generic",
            target="log",
            value=r"SUCCESS.*\d+",
            operator="matches"
        )

        context = {"log": "ERROR: Something went wrong"}
        result = condition.evaluate(context)

        assert result is False

    def test_evaluate_unknown_operator(self):
        """Test evaluating condition with unknown operator returns False."""
        condition = Condition(
            type="generic",
            target="value",
            value="test",
            operator="unknown_operator"
        )

        context = {"value": "test"}
        result = condition.evaluate(context)

        assert result is False


class TestAction:
    """Test Action class and serialization."""

    def test_action_creation(self):
        """Test Action creation with all fields."""
        action = Action(
            tool="Edit",
            parameters={"file_path": "/test.py", "old_string": "old", "new_string": "new"},
            output_pattern=r"✓|SUCCESS",
            timeout_seconds=30
        )

        assert action.tool == "Edit"
        assert action.parameters["file_path"] == "/test.py"
        assert action.output_pattern == r"✓|SUCCESS"
        assert action.timeout_seconds == 30

    def test_action_minimal_creation(self):
        """Test Action creation with minimal required fields."""
        action = Action(
            tool="Read",
            parameters={"file_path": "/test.py"}
        )

        assert action.tool == "Read"
        assert action.parameters == {"file_path": "/test.py"}
        assert action.output_pattern is None
        assert action.timeout_seconds is None

    def test_action_to_dict(self):
        """Test Action serialization to dictionary."""
        action = Action(
            tool="Bash",
            parameters={"command": "pytest"},
            output_pattern=r"\d+ passed",
            timeout_seconds=60
        )

        result = action.to_dict()

        assert result["tool"] == "Bash"
        assert result["parameters"]["command"] == "pytest"
        assert result["output_pattern"] == r"\d+ passed"
        assert result["timeout_seconds"] == 60

    def test_action_from_dict(self):
        """Test Action deserialization from dictionary."""
        data = {
            "tool": "MultiEdit",
            "parameters": {"file_path": "/test.py", "edits": []},
            "output_pattern": "SUCCESS",
            "timeout_seconds": 120
        }

        action = Action.from_dict(data)

        assert action.tool == "MultiEdit"
        assert action.parameters["file_path"] == "/test.py"
        assert action.output_pattern == "SUCCESS"
        assert action.timeout_seconds == 120

    def test_action_from_dict_minimal(self):
        """Test Action deserialization with minimal data."""
        data = {
            "tool": "Grep",
            "parameters": {"pattern": "test"}
        }

        action = Action.from_dict(data)

        assert action.tool == "Grep"
        assert action.parameters == {"pattern": "test"}
        assert action.output_pattern is None
        assert action.timeout_seconds is None

    def test_action_round_trip_serialization(self):
        """Test that Action serialization is reversible."""
        original = Action(
            tool="ComplexTool",
            parameters={"nested": {"data": [1, 2, 3]}, "simple": "value"},
            output_pattern=r"COMPLEX.*PATTERN",
            timeout_seconds=300
        )

        serialized = original.to_dict()
        restored = Action.from_dict(serialized)

        assert restored.tool == original.tool
        assert restored.parameters == original.parameters
        assert restored.output_pattern == original.output_pattern
        assert restored.timeout_seconds == original.timeout_seconds


class TestPatternMetadata:
    """Test PatternMetadata class and serialization."""

    def test_pattern_metadata_creation(self):
        """Test PatternMetadata creation with all fields."""
        created_at = datetime.now()
        last_used = created_at + timedelta(hours=1)

        metadata = PatternMetadata(
            confidence=0.85,
            usage_count=5,
            success_count=4,
            failure_count=1,
            last_used=last_used,
            created_at=created_at,
            source="learned",
            tags=["error_fix", "import", "auto_learned"]
        )

        assert metadata.confidence == 0.85
        assert metadata.usage_count == 5
        assert metadata.success_count == 4
        assert metadata.failure_count == 1
        assert metadata.last_used == last_used
        assert metadata.created_at == created_at
        assert metadata.source == "learned"
        assert metadata.tags == ["error_fix", "import", "auto_learned"]

    def test_pattern_metadata_to_dict(self):
        """Test PatternMetadata serialization to dictionary."""
        created_at = datetime.now()
        last_used = created_at + timedelta(hours=2)

        metadata = PatternMetadata(
            confidence=0.75,
            usage_count=3,
            success_count=2,
            failure_count=1,
            last_used=last_used,
            created_at=created_at,
            source="manual",
            tags=["test", "validation"]
        )

        result = metadata.to_dict()

        assert result["confidence"] == 0.75
        assert result["usage_count"] == 3
        assert result["success_count"] == 2
        assert result["failure_count"] == 1
        assert result["last_used"] == last_used.isoformat()
        assert result["created_at"] == created_at.isoformat()
        assert result["source"] == "manual"
        assert result["tags"] == ["test", "validation"]

    def test_pattern_metadata_from_dict(self):
        """Test PatternMetadata deserialization from dictionary."""
        created_at = datetime.now()
        last_used = created_at + timedelta(minutes=30)

        data = {
            "confidence": 0.9,
            "usage_count": 10,
            "success_count": 9,
            "failure_count": 1,
            "last_used": last_used.isoformat(),
            "created_at": created_at.isoformat(),
            "source": "imported",
            "tags": ["high_confidence", "tested"]
        }

        metadata = PatternMetadata.from_dict(data)

        assert metadata.confidence == 0.9
        assert metadata.usage_count == 10
        assert metadata.success_count == 9
        assert metadata.failure_count == 1
        assert metadata.last_used == last_used
        assert metadata.created_at == created_at
        assert metadata.source == "imported"
        assert metadata.tags == ["high_confidence", "tested"]

    def test_pattern_metadata_round_trip_serialization(self):
        """Test that PatternMetadata serialization is reversible."""
        original = PatternMetadata(
            confidence=0.65,
            usage_count=7,
            success_count=5,
            failure_count=2,
            last_used=datetime.now(),
            created_at=datetime.now() - timedelta(days=1),
            source="learned",
            tags=["complex", "multi_step", "error_handling"]
        )

        serialized = original.to_dict()
        restored = PatternMetadata.from_dict(serialized)

        assert restored.confidence == original.confidence
        assert restored.usage_count == original.usage_count
        assert restored.success_count == original.success_count
        assert restored.failure_count == original.failure_count
        assert restored.last_used == original.last_used
        assert restored.created_at == original.created_at
        assert restored.source == original.source
        assert restored.tags == original.tags


class TestEnhancedPattern:
    """Test EnhancedPattern class and conversions."""

    def create_test_pattern(self) -> EnhancedPattern:
        """Create a test pattern for use in multiple tests."""
        trigger = ErrorTrigger(
            error_type="NoneType",
            error_pattern=r"AttributeError.*'NoneType'"
        )

        preconditions = [
            Condition(type="file_exists", target="/test.py", value=True)
        ]

        actions = [
            Action(tool="Read", parameters={"file_path": "/test.py"}),
            Action(tool="Edit", parameters={"old_string": "old", "new_string": "new"})
        ]

        postconditions = [
            Condition(type="test_passes", target="test_results", value=True)
        ]

        metadata = PatternMetadata(
            confidence=0.8,
            usage_count=3,
            success_count=2,
            failure_count=1,
            last_used=datetime.now(),
            created_at=datetime.now() - timedelta(hours=1),
            source="learned",
            tags=["error_fix", "nonetype"]
        )

        return EnhancedPattern(
            id="test_pattern_001",
            trigger=trigger,
            preconditions=preconditions,
            actions=actions,
            postconditions=postconditions,
            metadata=metadata
        )

    def test_enhanced_pattern_creation(self):
        """Test EnhancedPattern creation with all components."""
        pattern = self.create_test_pattern()

        assert pattern.id == "test_pattern_001"
        assert isinstance(pattern.trigger, ErrorTrigger)
        assert len(pattern.preconditions) == 1
        assert len(pattern.actions) == 2
        assert len(pattern.postconditions) == 1
        assert isinstance(pattern.metadata, PatternMetadata)

    def test_to_existing_pattern_conversion(self):
        """Test conversion to existing UnifiedPatternStore format."""
        enhanced_pattern = self.create_test_pattern()
        existing_pattern = enhanced_pattern.to_existing_pattern()

        assert isinstance(existing_pattern, ExistingPattern)
        assert existing_pattern.id == "test_pattern_001"
        assert existing_pattern.pattern_type == "error"
        assert existing_pattern.success_rate == 0.8
        assert existing_pattern.usage_count == 3
        assert "error_fix" in existing_pattern.tags

        # Check context structure
        context = existing_pattern.context
        assert "trigger" in context
        assert "preconditions" in context
        assert "postconditions" in context

        # Check solution contains serialized actions
        actions = json.loads(existing_pattern.solution)
        assert len(actions) == 2
        assert actions[0]["tool"] == "Read"

    def test_from_existing_pattern_conversion(self):
        """Test conversion from existing UnifiedPatternStore format."""
        # Create an existing pattern
        existing = ExistingPattern(
            id="existing_001",
            pattern_type="error",
            context={
                "trigger": {
                    "type": "error",
                    "metadata": {
                        "error_type": "ImportError",
                        "error_pattern": r"ImportError.*"
                    }
                },
                "preconditions": [
                    {"type": "file_exists", "target": "/src.py", "value": True, "operator": "equals"}
                ],
                "postconditions": [
                    {"type": "test_passes", "target": "tests", "value": True, "operator": "equals"}
                ]
            },
            solution=json.dumps([
                {"tool": "Edit", "parameters": {"file_path": "/src.py"}, "output_pattern": None, "timeout_seconds": None}
            ]),
            success_rate=0.9,
            usage_count=5,
            created_at="2023-01-01T12:00:00",
            last_used="2023-01-01T13:00:00",
            tags=["import_fix", "learned"]
        )

        enhanced = EnhancedPattern.from_existing_pattern(existing)

        assert enhanced.id == "existing_001"
        assert isinstance(enhanced.trigger, ErrorTrigger)
        assert enhanced.trigger.error_type == "ImportError"
        assert len(enhanced.preconditions) == 1
        assert len(enhanced.actions) == 1
        assert len(enhanced.postconditions) == 1
        assert enhanced.metadata.confidence == 0.9

    def test_conversion_round_trip(self):
        """Test that pattern conversion is reversible."""
        original = self.create_test_pattern()

        # Convert to existing format and back
        existing = original.to_existing_pattern()
        restored = EnhancedPattern.from_existing_pattern(existing)

        assert restored.id == original.id
        assert restored.trigger.type == original.trigger.type
        assert len(restored.actions) == len(original.actions)
        assert restored.metadata.confidence == original.metadata.confidence

    def test_from_existing_pattern_legacy_solution(self):
        """Test handling of legacy patterns with non-JSON solution."""
        legacy_pattern = ExistingPattern(
            id="legacy_001",
            pattern_type="task",
            context={
                "trigger": {
                    "type": "task",
                    "metadata": {"keywords": ["fix", "bug"]}
                },
                "preconditions": [],
                "postconditions": []
            },
            solution="Legacy solution text, not JSON",
            success_rate=0.7,
            usage_count=2,
            created_at="2023-01-01T10:00:00",
            last_used="2023-01-01T11:00:00",
            tags=["legacy"]
        )

        enhanced = EnhancedPattern.from_existing_pattern(legacy_pattern)

        assert enhanced.id == "legacy_001"
        assert len(enhanced.actions) == 0  # Should handle gracefully


class TestOperation:
    """Test Operation class and properties."""

    def test_operation_creation(self):
        """Test Operation creation with all fields."""
        timestamp = datetime.now()
        tool_calls = [
            {"tool": "Read", "parameters": {"file_path": "/test.py"}},
            {"tool": "Edit", "parameters": {"old_string": "old", "new_string": "new"}}
        ]

        operation = Operation(
            id="op_001",
            task_description="Fix import error in test file",
            initial_error={"type": "ImportError", "message": "Module not found"},
            tool_calls=tool_calls,
            final_state={"success": True, "tests_passing": True},
            success=True,
            duration_seconds=12.5,
            timestamp=timestamp
        )

        assert operation.id == "op_001"
        assert operation.task_description == "Fix import error in test file"
        assert operation.initial_error["type"] == "ImportError"
        assert len(operation.tool_calls) == 2
        assert operation.success is True
        assert operation.duration_seconds == 12.5

    def test_operation_caused_regression_true(self):
        """Test caused_regression property when regressions exist."""
        operation = Operation(
            id="op_002",
            task_description=None,
            initial_error=None,
            tool_calls=[],
            final_state={"test_results": {"regressions": 2}},
            success=False,
            duration_seconds=5.0,
            timestamp=datetime.now()
        )

        assert operation.caused_regression is True

    def test_operation_caused_regression_false(self):
        """Test caused_regression property when no regressions."""
        operation = Operation(
            id="op_003",
            task_description=None,
            initial_error=None,
            tool_calls=[],
            final_state={"test_results": {"regressions": 0}},
            success=True,
            duration_seconds=3.0,
            timestamp=datetime.now()
        )

        assert operation.caused_regression is False

    def test_operation_caused_regression_no_test_results(self):
        """Test caused_regression property when test_results not present."""
        operation = Operation(
            id="op_004",
            task_description=None,
            initial_error=None,
            tool_calls=[],
            final_state={"other_data": "value"},
            success=True,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        assert operation.caused_regression is False


class TestFailureReasonClass:
    """Test FailureReason classes."""

    def test_test_failure_creation(self):
        """Test TestFailureAnalysis creation and auto-population."""
        test_failure = TestFailureAnalysis(
            failed_tests=["test_func1", "test_func2", "test_func3"],
            root_cause="Assertion errors in business logic"
        )

        assert test_failure.type == "test_failure"
        assert test_failure.failed_tests == ["test_func1", "test_func2", "test_func3"]
        assert test_failure.root_cause == "Assertion errors in business logic"
        assert "test_func1, test_func2, test_func3" in test_failure.description
        assert test_failure.details["failed_tests"] == ["test_func1", "test_func2", "test_func3"]

    def test_test_failure_long_list_truncation(self):
        """Test TestFailureAnalysis description truncates long lists."""
        failed_tests = [f"test_func{i}" for i in range(10)]
        test_failure = TestFailureAnalysis(
            failed_tests=failed_tests,
            root_cause="Multiple assertion failures"
        )

        # Should only show first 3 tests in description
        assert "test_func0, test_func1, test_func2" in test_failure.description
        assert "test_func9" not in test_failure.description

    def test_execution_error_creation(self):
        """Test ExecutionError creation and auto-population."""
        exec_error = ExecutionError(
            error_type="PermissionError",
            error_message="Access denied to file /protected.txt"
        )

        assert exec_error.type == "execution_error"
        assert exec_error.error_type == "PermissionError"
        assert exec_error.error_message == "Access denied to file /protected.txt"
        assert "PermissionError: Access denied" in exec_error.description
        assert exec_error.details["error_type"] == "PermissionError"


class TestPatternExtractor:
    """Test PatternExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_pattern_store = Mock()
        self.extractor = PatternExtractor(pattern_store=self.mock_pattern_store)

    def create_success_operation(self) -> Operation:
        """Create a successful operation for testing."""
        return Operation(
            id="success_op_001",
            task_description="Fix NoneType error in validation function",
            initial_error={
                "type": "AttributeError",
                "message": "AttributeError: 'NoneType' object has no attribute 'validate'"
            },
            tool_calls=[
                {
                    "tool": "Read",
                    "parameters": {"file_path": "/src/validator.py"},
                    "output": "File content read successfully"
                },
                {
                    "tool": "Edit",
                    "parameters": {
                        "old_string": "result.validate()",
                        "new_string": "if result: result.validate()"
                    },
                    "output": "✓ Edit completed successfully"
                },
                {
                    "tool": "Bash",
                    "parameters": {"command": "pytest tests/test_validator.py"},
                    "output": "5 passed, 0 failed"
                }
            ],
            final_state={"tests_passing": True, "error_resolved": True},
            success=True,
            duration_seconds=15.2,
            timestamp=datetime.now()
        )

    def test_extractor_initialization_default_store(self):
        """Test PatternExtractor initialization with default store."""
        extractor = PatternExtractor()

        assert extractor.pattern_store is not None
        assert hasattr(extractor, 'telemetry')

    def test_extractor_initialization_custom_store(self):
        """Test PatternExtractor initialization with custom store."""
        custom_store = Mock()
        extractor = PatternExtractor(pattern_store=custom_store)

        assert extractor.pattern_store == custom_store

    @patch('learning_loop.pattern_extraction.emit')
    def test_extract_from_success(self, mock_emit):
        """Test successful pattern extraction from operation."""
        operation = self.create_success_operation()

        pattern = self.extractor.extract_from_success(operation)

        assert isinstance(pattern, EnhancedPattern)
        assert pattern.id.startswith("success_success_op_001")
        assert isinstance(pattern.trigger, ErrorTrigger)
        assert pattern.trigger.error_type == "AttributeError"
        assert len(pattern.actions) == 3
        assert pattern.metadata.confidence == 0.5  # Initial confidence per spec

        # Verify pattern was stored
        self.mock_pattern_store.add.assert_called_once()

        # Verify telemetry emission
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args[0]
        assert call_args[0] == "pattern_extracted"

    def test_extract_from_success_failure_operation(self):
        """Test that extracting from failed operation raises error."""
        failed_operation = Operation(
            id="failed_op",
            task_description="Failed task",
            initial_error=None,
            tool_calls=[],
            final_state={},
            success=False,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        with pytest.raises(ValueError, match="Cannot extract success pattern from failed operation"):
            self.extractor.extract_from_success(failed_operation)

    def test_identify_trigger_error_trigger(self):
        """Test trigger identification for error-based operations."""
        operation = self.create_success_operation()

        trigger = self.extractor._identify_trigger(operation)

        assert isinstance(trigger, ErrorTrigger)
        assert trigger.error_type == "AttributeError"
        assert "AttributeError.*'NoneType'" in trigger.error_pattern

    def test_identify_trigger_import_error(self):
        """Test trigger identification for ImportError."""
        operation = Operation(
            id="import_op",
            task_description=None,
            initial_error={
                "type": "ImportError",
                "message": "ImportError: No module named 'missing_module'"
            },
            tool_calls=[],
            final_state={},
            success=True,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        trigger = self.extractor._identify_trigger(operation)

        assert isinstance(trigger, ErrorTrigger)
        assert trigger.error_type == "ImportError"
        assert "ImportError|ModuleNotFoundError" in trigger.error_pattern

    def test_identify_trigger_task_description(self):
        """Test trigger identification for task-based operations."""
        operation = Operation(
            id="task_op",
            task_description="Add null check to prevent NoneType errors in user validation",
            initial_error=None,
            tool_calls=[],
            final_state={},
            success=True,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        trigger = self.extractor._identify_trigger(operation)

        assert isinstance(trigger, TaskTrigger)
        expected_keywords = {"add", "null", "error", "none"}
        actual_keywords = set(trigger.keywords)
        assert expected_keywords.intersection(actual_keywords)

    def test_identify_trigger_default(self):
        """Test trigger identification with no error or task description."""
        operation = Operation(
            id="default_op",
            task_description=None,
            initial_error=None,
            tool_calls=[],
            final_state={},
            success=True,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        trigger = self.extractor._identify_trigger(operation)

        assert isinstance(trigger, TaskTrigger)
        assert trigger.keywords == ["general"]

    def test_extract_keywords_comprehensive(self):
        """Test keyword extraction from various task descriptions."""
        test_cases = [
            ("Fix import error in module", ["fix", "error", "import"]),
            ("Add null check to prevent crashes", ["add", "null", "crash"]),
            ("Refactor function to handle exceptions", ["refactor", "function", "exception"]),
            ("Create new test for validation", ["create", "test"]),
            ("Random task description", ["general"])
        ]

        for description, expected_keywords in test_cases:
            keywords = self.extractor._extract_keywords(description)
            for expected in expected_keywords:
                if expected != "general":
                    assert expected in keywords
                else:
                    # "general" should only appear if no other keywords found
                    assert keywords == ["general"]

    def test_extract_preconditions(self):
        """Test precondition extraction from operation."""
        operation = self.create_success_operation()

        preconditions = self.extractor._extract_preconditions(operation)

        # Should have error presence condition and file existence condition
        assert len(preconditions) >= 2

        error_conditions = [pc for pc in preconditions if pc.type == "error_present"]
        assert len(error_conditions) == 1
        assert error_conditions[0].value == "AttributeError"

        file_conditions = [pc for pc in preconditions if pc.type == "file_exists"]
        assert len(file_conditions) == 1
        assert file_conditions[0].target == "/src/validator.py"

    def test_extract_action_sequence(self):
        """Test action sequence extraction and generalization."""
        operation = self.create_success_operation()

        actions = self.extractor._extract_action_sequence(operation)

        assert len(actions) == 3

        # Check Read action
        read_action = actions[0]
        assert read_action.tool == "Read"
        assert read_action.parameters["file_path"] == "{python_file}"

        # Check Edit action
        edit_action = actions[1]
        assert edit_action.tool == "Edit"
        assert "{code_change}" in edit_action.parameters["old_string"]
        assert edit_action.output_pattern is not None

        # Check Bash action
        bash_action = actions[2]
        assert bash_action.tool == "Bash"

    def test_generalize_parameters(self):
        """Test parameter generalization for reusability."""
        test_cases = [
            ({"file_path": "/tests/test_module.py"}, {"file_path": "{test_file}"}),
            ({"file_path": "/src/module.py"}, {"file_path": "{python_file}"}),
            ({"file_path": "/config.json"}, {"file_path": "{file}"}),
            ({"old_string": "import missing_module"}, {"old_string": "{import_statement}"}),
            ({"new_string": "def new_function():"}, {"new_string": "{function_definition}"}),
            ({"pattern": "error.*"}, {"pattern": "{pattern: error.*}"}),
            ({"other_param": "value"}, {"other_param": "value"})
        ]

        for input_params, expected_output in test_cases:
            result = self.extractor._generalize_parameters(input_params)
            for key, expected_value in expected_output.items():
                assert key in result
                assert result[key] == expected_value

    def test_extract_output_pattern(self):
        """Test output pattern extraction for validation."""
        test_cases = [
            ("✓ Operation completed successfully", r"✓|✅|\bSUCCESS\b|\bPASS\b|\bOK\b"),
            ("5 passed, 0 failed", r"\d+ passed"),
            ("All tests passed", r"All tests passed"),
            ("File written successfully", r"File written successfully"),
            ("No recognizable outcome here", None),
            ("", None)
        ]

        for output, expected_pattern in test_cases:
            result = self.extractor._extract_output_pattern(output)
            if expected_pattern:
                assert result == expected_pattern
            else:
                assert result is None

    def test_extract_postconditions(self):
        """Test postcondition extraction from operation."""
        operation = self.create_success_operation()

        postconditions = self.extractor._extract_postconditions(operation)

        # Should have operation success, test passes, and error absence conditions
        assert len(postconditions) == 3

        success_conditions = [pc for pc in postconditions if pc.type == "operation_success"]
        assert len(success_conditions) == 1

        test_conditions = [pc for pc in postconditions if pc.type == "test_passes"]
        assert len(test_conditions) == 1

        error_conditions = [pc for pc in postconditions if pc.type == "error_absent"]
        assert len(error_conditions) == 1

    def test_generate_tags(self):
        """Test tag generation for pattern categorization."""
        operation = self.create_success_operation()
        trigger = ErrorTrigger(error_type="NoneType", error_pattern="test")

        tags = self.extractor._generate_tags(operation, trigger)

        # Should include base tags
        assert "auto_learned" in tags
        assert "pattern_extraction" in tags

        # Should include trigger-based tags
        assert "error" in tags
        assert "error_nonetype" in tags

        # Should include tool-based tags
        assert "uses_read" in tags
        assert "uses_edit" in tags
        assert "uses_bash" in tags

        # Should include complexity tag
        assert "moderate" in tags  # 3 tool calls


class TestFailureLearner:
    """Test FailureLearner class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_pattern_store = Mock()
        self.learner = FailureLearner(pattern_store=self.mock_pattern_store)

    def create_failed_operation(self) -> Operation:
        """Create a failed operation for testing."""
        return Operation(
            id="failed_op_001",
            task_description="Attempt to fix validation without null check",
            initial_error={
                "type": "AttributeError",
                "message": "AttributeError: 'NoneType' object has no attribute 'validate'"
            },
            tool_calls=[
                {
                    "tool": "Read",
                    "parameters": {"file_path": "/src/validator.py"}
                },
                {
                    "tool": "Edit",
                    "parameters": {
                        "old_string": "result.validate()",
                        "new_string": "result.validate_all()"  # Wrong fix
                    }
                }
            ],
            final_state={
                "error": {"type": "AttributeError", "message": "validate_all not found"},
                "test_results": {"passed": False, "failures": ["test_validate_user"]}
            },
            success=False,
            duration_seconds=8.1,
            timestamp=datetime.now()
        )

    def test_learner_initialization_default_store(self):
        """Test FailureLearner initialization with default store."""
        learner = FailureLearner()

        assert learner.pattern_store is not None
        assert hasattr(learner, 'telemetry')

    def test_learner_initialization_custom_store(self):
        """Test FailureLearner initialization with custom store."""
        custom_store = Mock()
        learner = FailureLearner(pattern_store=custom_store)

        assert learner.pattern_store == custom_store

    @patch('learning_loop.pattern_extraction.emit')
    def test_learn_from_failure(self, mock_emit):
        """Test anti-pattern learning from failed operation."""
        operation = self.create_failed_operation()

        antipattern = self.learner.learn_from_failure(operation)

        assert isinstance(antipattern, AntiPattern)
        assert antipattern.id.startswith("failure_failed_op_001")
        assert isinstance(antipattern.trigger, ErrorTrigger)
        assert len(antipattern.failed_approach) == 2
        assert antipattern.severity == "medium"  # No regression

        # Verify anti-pattern was stored
        self.mock_pattern_store.add.assert_called_once()

        # Verify telemetry emission
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args[0]
        assert call_args[0] == "antipattern_learned"

    def test_learn_from_failure_success_operation(self):
        """Test that learning from successful operation raises error."""
        success_operation = Operation(
            id="success_op",
            task_description="Successful task",
            initial_error=None,
            tool_calls=[],
            final_state={},
            success=True,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        with pytest.raises(ValueError, match="Cannot extract failure pattern from successful operation"):
            self.learner.learn_from_failure(success_operation)

    def test_analyze_failure_test_failure(self):
        """Test failure analysis for test failures."""
        operation = Operation(
            id="test_fail_op",
            task_description=None,
            initial_error=None,
            tool_calls=[],
            final_state={
                "test_results": {
                    "passed": False,
                    "failures": ["test_func1", "test_func2"]
                }
            },
            success=False,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        failure_reason = self.learner._analyze_failure(operation)

        assert isinstance(failure_reason, TestFailureAnalysis)
        assert failure_reason.failed_tests == ["test_func1", "test_func2"]

    def test_analyze_failure_execution_error(self):
        """Test failure analysis for execution errors."""
        operation = Operation(
            id="exec_fail_op",
            task_description=None,
            initial_error=None,
            tool_calls=[],
            final_state={
                "error": {
                    "type": "PermissionError",
                    "message": "Access denied"
                }
            },
            success=False,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        failure_reason = self.learner._analyze_failure(operation)

        assert isinstance(failure_reason, ExecutionError)
        assert failure_reason.error_type == "PermissionError"
        assert failure_reason.error_message == "Access denied"

    def test_analyze_failure_unknown(self):
        """Test failure analysis for unknown failures."""
        operation = Operation(
            id="unknown_fail_op",
            task_description=None,
            initial_error=None,
            tool_calls=[],
            final_state={"some_data": "value"},
            success=False,
            duration_seconds=1.0,
            timestamp=datetime.now()
        )

        failure_reason = self.learner._analyze_failure(operation)

        assert failure_reason.type == "unknown_failure"
        assert "unknown reasons" in failure_reason.description

    def test_analyze_test_failures(self):
        """Test test failure root cause analysis."""
        test_cases = [
            ({"failures": ["AssertionError: expected True"]}, "Assertion failures"),
            ({"failures": ["ImportError: module not found"]}, "Import errors"),
            ({"failures": ["SyntaxError: invalid syntax"]}, "Syntax errors"),
            ({"failures": ["AttributeError: NoneType has no attribute"]}, "NoneType errors"),
            ({"failures": ["TimeoutError: operation timed out"]}, "Timeout errors"),
            ({"failures": ["Error1", "Error2", "Error3"]}, "Multiple test failures: 3 tests failed"),
            ({}, "Unknown test failure")
        ]

        for test_results, expected_root_cause in test_cases:
            root_cause = self.learner._analyze_test_failures(test_results)
            assert expected_root_cause.lower() in root_cause.lower()

    def test_suggest_alternatives(self):
        """Test alternative approach suggestions."""
        operation = self.create_failed_operation()

        alternatives = self.learner._suggest_alternatives(operation)

        assert isinstance(alternatives, list)
        assert len(alternatives) > 0

        # Should suggest null checks for AttributeError
        null_check_suggestions = [alt for alt in alternatives if "null check" in alt.lower()]
        assert len(null_check_suggestions) > 0

    def test_generate_failure_tags(self):
        """Test failure tag generation."""
        operation = self.create_failed_operation()
        failure_reason = ExecutionError(error_type="TestError", error_message="Test failed")

        tags = self.learner._generate_failure_tags(operation, failure_reason)

        assert "anti_pattern" in tags
        assert "failure_learning" in tags
        assert "execution_error" in tags
        assert "failed_with_read" in tags
        assert "failed_with_edit" in tags


class TestIntegration:
    """Integration tests for pattern extraction components."""

    @patch('learning_loop.pattern_extraction.get_pattern_store')
    def test_end_to_end_success_pattern_extraction(self, mock_get_store):
        """Test complete success pattern extraction workflow."""
        mock_store = Mock()
        mock_get_store.return_value = mock_store

        # Create successful operation
        operation = Operation(
            id="integration_success",
            task_description="Fix import error by adding missing import",
            initial_error={
                "type": "ImportError",
                "message": "ImportError: cannot import name 'utils' from 'mymodule'"
            },
            tool_calls=[
                {
                    "tool": "Read",
                    "parameters": {"file_path": "/src/mymodule.py"},
                    "output": "File read successfully"
                },
                {
                    "tool": "Edit",
                    "parameters": {
                        "old_string": "# imports",
                        "new_string": "# imports\nfrom . import utils"
                    },
                    "output": "✓ Edit completed"
                },
                {
                    "tool": "Bash",
                    "parameters": {"command": "python -m pytest tests/"},
                    "output": "3 passed, 0 failed"
                }
            ],
            final_state={"tests_passing": True, "import_resolved": True},
            success=True,
            duration_seconds=22.7,
            timestamp=datetime.now()
        )

        extractor = PatternExtractor()
        pattern = extractor.extract_from_success(operation)

        # Verify complete pattern structure
        assert isinstance(pattern, EnhancedPattern)
        assert isinstance(pattern.trigger, ErrorTrigger)
        assert pattern.trigger.error_type == "ImportError"
        assert len(pattern.preconditions) >= 1
        assert len(pattern.actions) == 3
        assert len(pattern.postconditions) >= 1

        # Verify pattern was stored in correct format
        mock_store.add.assert_called_once()
        stored_pattern = mock_store.add.call_args[0][0]
        assert isinstance(stored_pattern, ExistingPattern)
        assert stored_pattern.pattern_type == "error"

    @patch('learning_loop.pattern_extraction.get_pattern_store')
    def test_end_to_end_failure_pattern_learning(self, mock_get_store):
        """Test complete failure pattern learning workflow."""
        mock_store = Mock()
        mock_get_store.return_value = mock_store

        # Create failed operation
        operation = Operation(
            id="integration_failure",
            task_description="Attempted to fix validation error incorrectly",
            initial_error={
                "type": "AttributeError",
                "message": "AttributeError: 'NoneType' object has no attribute 'is_valid'"
            },
            tool_calls=[
                {
                    "tool": "Edit",
                    "parameters": {
                        "old_string": "user.is_valid()",
                        "new_string": "user.validate()"  # Wrong method
                    }
                }
            ],
            final_state={
                "error": {"type": "AttributeError", "message": "validate method not found"},
                "test_results": {"passed": False, "failures": ["test_user_validation"]}
            },
            success=False,
            duration_seconds=3.2,
            timestamp=datetime.now()
        )

        learner = FailureLearner()
        antipattern = learner.learn_from_failure(operation)

        # Verify complete anti-pattern structure
        assert isinstance(antipattern, AntiPattern)
        assert isinstance(antipattern.trigger, ErrorTrigger)
        assert len(antipattern.failed_approach) == 1
        assert len(antipattern.alternative_approaches) > 0

        # Verify anti-pattern was stored
        mock_store.add.assert_called_once()
        stored_antipattern = mock_store.add.call_args[0][0]
        assert stored_antipattern.pattern_type == "anti_pattern"
        assert stored_antipattern.success_rate == 0.0

    def test_pattern_conversion_compatibility(self):
        """Test that enhanced patterns are compatible with existing store."""
        # Create enhanced pattern
        trigger = ErrorTrigger(error_type="TestError", error_pattern="test.*")
        enhanced = EnhancedPattern(
            id="compat_test",
            trigger=trigger,
            preconditions=[],
            actions=[Action(tool="Test", parameters={})],
            postconditions=[],
            metadata=PatternMetadata(
                confidence=0.8,
                usage_count=1,
                success_count=1,
                failure_count=0,
                last_used=datetime.now(),
                created_at=datetime.now(),
                source="test",
                tags=["test"]
            )
        )

        # Convert to existing format
        existing = enhanced.to_existing_pattern()

        # Convert back to enhanced format
        restored = EnhancedPattern.from_existing_pattern(existing)

        # Verify compatibility
        assert restored.id == enhanced.id
        assert restored.trigger.type == enhanced.trigger.type
        assert len(restored.actions) == len(enhanced.actions)
        assert restored.metadata.confidence == enhanced.metadata.confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])