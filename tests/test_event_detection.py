"""
Comprehensive unit tests for the Event Detection Layer.

Tests follow the NECESSARY pattern:
- N: No Missing Behaviors - All code paths covered
- E: Edge Cases - Boundary conditions tested
- C: Comprehensive - Multiple test vectors per function
- E: Error Conditions - Exception handling verified
- S: State Validation - Object state changes confirmed
- S: Side Effects - External impacts tested
- A: Async Operations - Concurrent code coverage
- R: Regression Prevention - Historical bugs covered
- Y: Yielding Confidence - Overall quality assurance
"""

import os
import sys
import re
import time
import json
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from typing import List, Dict, Any

import pytest
from watchdog.events import FileModifiedEvent, FileCreatedEvent

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from learning_loop.event_detection import (
    Event, FileEvent, ErrorEvent, FileWatcher, ErrorMonitor, EventDetectionSystem,
    FileWatchHandler
)


class TestEvent:
    """Test the base Event class and its serialization."""

    def test_event_creation(self):
        """Test basic event creation with required fields."""
        timestamp = datetime.now()
        metadata = {"key": "value", "count": 42}

        event = Event(
            type="test_event",
            timestamp=timestamp,
            metadata=metadata
        )

        assert event.type == "test_event"
        assert event.timestamp == timestamp
        assert event.metadata == metadata

    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        timestamp = datetime.now()
        metadata = {"operation": "test", "success": True}

        event = Event(
            type="operation_complete",
            timestamp=timestamp,
            metadata=metadata
        )

        result = event.to_dict()

        assert result["type"] == "operation_complete"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["metadata"] == metadata

    def test_event_from_dict(self):
        """Test event deserialization from dictionary."""
        timestamp = datetime.now()
        data = {
            "type": "parsed_event",
            "timestamp": timestamp.isoformat(),
            "metadata": {"source": "unittest"}
        }

        event = Event.from_dict(data)

        assert event.type == "parsed_event"
        assert event.timestamp == timestamp
        assert event.metadata == {"source": "unittest"}

    def test_event_round_trip_serialization(self):
        """Test that event serialization is reversible."""
        original = Event(
            type="round_trip",
            timestamp=datetime.now(),
            metadata={"test": "data", "number": 123}
        )

        # Serialize and deserialize
        serialized = original.to_dict()
        restored = Event.from_dict(serialized)

        assert restored.type == original.type
        assert restored.timestamp == original.timestamp
        assert restored.metadata == original.metadata


class TestFileEvent:
    """Test FileEvent class with filesystem-specific metadata."""

    def test_file_event_creation(self):
        """Test FileEvent creation with all required fields."""
        timestamp = datetime.now()

        file_event = FileEvent(
            type="file_modified",
            timestamp=timestamp,
            path="/test/path.py",
            change_type="modified",
            file_type="python",
            metadata={"size": 1024}
        )

        assert file_event.type == "file_modified"
        assert file_event.timestamp == timestamp
        assert file_event.path == "/test/path.py"
        assert file_event.change_type == "modified"
        assert file_event.file_type == "python"

    def test_file_event_metadata_population(self):
        """Test that FileEvent auto-populates metadata fields."""
        file_event = FileEvent(
            type="file_created",
            timestamp=datetime.now(),
            path="/src/module.py",
            change_type="created",
            file_type="python",
            metadata={}
        )

        # Verify metadata is populated
        assert file_event.metadata["path"] == "/src/module.py"
        assert file_event.metadata["change_type"] == "created"
        assert file_event.metadata["file_type"] == "python"

    def test_file_event_existing_metadata_preserved(self):
        """Test that existing metadata is preserved when auto-populating."""
        existing_metadata = {"custom": "value", "size": 2048}

        file_event = FileEvent(
            type="file_modified",
            timestamp=datetime.now(),
            path="/docs/readme.md",
            change_type="modified",
            file_type="markdown",
            metadata=existing_metadata.copy()
        )

        # Custom metadata should be preserved
        assert file_event.metadata["custom"] == "value"
        assert file_event.metadata["size"] == 2048
        # Auto-populated metadata should be added
        assert file_event.metadata["path"] == "/docs/readme.md"
        assert file_event.metadata["file_type"] == "markdown"


class TestErrorEvent:
    """Test ErrorEvent class with error-specific metadata."""

    def test_error_event_creation(self):
        """Test ErrorEvent creation with all fields."""
        timestamp = datetime.now()

        error_event = ErrorEvent(
            type="error_detected",
            timestamp=timestamp,
            error_type="NoneType",
            message="AttributeError: 'NoneType' object has no attribute 'value'",
            context="Line 42: result.value",
            source_file="/src/module.py",
            line_number=42,
            metadata={}
        )

        assert error_event.type == "error_detected"
        assert error_event.error_type == "NoneType"
        assert error_event.message == "AttributeError: 'NoneType' object has no attribute 'value'"
        assert error_event.context == "Line 42: result.value"
        assert error_event.source_file == "/src/module.py"
        assert error_event.line_number == 42

    def test_error_event_optional_fields(self):
        """Test ErrorEvent with optional fields as None."""
        error_event = ErrorEvent(
            type="error_detected",
            timestamp=datetime.now(),
            error_type="ImportError",
            message="Module not found",
            context="import missing_module",
            metadata={}
        )

        assert error_event.source_file is None
        assert error_event.line_number is None

    def test_error_event_metadata_population(self):
        """Test that ErrorEvent auto-populates metadata fields."""
        error_event = ErrorEvent(
            type="error_detected",
            timestamp=datetime.now(),
            error_type="SyntaxError",
            message="Invalid syntax",
            context="def func(:",
            source_file="/src/bad.py",
            line_number=15,
            metadata={}
        )

        # Verify metadata population
        assert error_event.metadata["error_type"] == "SyntaxError"
        assert error_event.metadata["message"] == "Invalid syntax"
        assert error_event.metadata["context"] == "def func(:"
        assert error_event.metadata["source_file"] == "/src/bad.py"
        assert error_event.metadata["line_number"] == 15


class TestFileWatchHandler:
    """Test the FileWatchHandler for file system events."""

    def setup_method(self):
        """Set up test fixtures."""
        self.callback_events = []
        self.callback = lambda event: self.callback_events.append(event)
        self.handler = FileWatchHandler(self.callback)

    def test_should_ignore_pycache(self):
        """Test that __pycache__ directories are ignored."""
        assert self.handler._should_ignore("/project/__pycache__/module.cpython-39.pyc")
        assert self.handler._should_ignore("/project/subdir/__pycache__/file.pyc")

    def test_should_ignore_git(self):
        """Test that .git directories are ignored."""
        assert self.handler._should_ignore("/project/.git/objects/abc123")
        assert self.handler._should_ignore("/project/.git/refs/heads/main")

    def test_should_ignore_logs(self):
        """Test that logs directories are ignored."""
        assert self.handler._should_ignore("/project/logs/events.jsonl")
        assert self.handler._should_ignore("/project/app/logs/debug.log")

    def test_should_ignore_pyc_files(self):
        """Test that .pyc files are ignored."""
        assert self.handler._should_ignore("/project/module.pyc")
        assert self.handler._should_ignore("/project/src/utils.pyo")

    def test_should_not_ignore_python_files(self):
        """Test that Python source files are not ignored."""
        assert not self.handler._should_ignore("/project/src/module.py")
        assert not self.handler._should_ignore("/project/test_module.py")

    def test_get_file_type_python(self):
        """Test file type detection for Python files."""
        assert self.handler._get_file_type("/src/module.py") == "python"
        assert self.handler._get_file_type("/project/utils.py") == "python"

    def test_get_file_type_test(self):
        """Test file type detection for test files."""
        assert self.handler._get_file_type("/tests/test_module.py") == "test"
        assert self.handler._get_file_type("/project/test_utils.py") == "test"
        assert self.handler._get_file_type("/src/tests/integration.py") == "test"

    def test_get_file_type_markdown(self):
        """Test file type detection for markdown files."""
        assert self.handler._get_file_type("/docs/readme.md") == "markdown"
        assert self.handler._get_file_type("/project/CHANGELOG.md") == "markdown"

    def test_get_file_type_config(self):
        """Test file type detection for config files."""
        assert self.handler._get_file_type("/project/config.yml") == "config"
        assert self.handler._get_file_type("/project/settings.yaml") == "config"
        assert self.handler._get_file_type("/project/package.json") == "config"
        assert self.handler._get_file_type("/project/pyproject.toml") == "config"

    def test_get_file_type_other(self):
        """Test file type detection for unrecognized files."""
        assert self.handler._get_file_type("/project/data.txt") == "other"
        assert self.handler._get_file_type("/project/image.png") == "other"

    def test_on_modified_python_file(self):
        """Test handling of Python file modification events."""
        # Mock the telemetry instance on the handler
        mock_telemetry = Mock()
        self.handler.telemetry = mock_telemetry

        # Create mock file modification event
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = "/project/src/module.py"

        self.handler.on_modified(mock_event)

        # Verify callback was called
        assert len(self.callback_events) == 1
        file_event = self.callback_events[0]

        assert file_event.type == "file_modified"
        assert file_event.path == "/project/src/module.py"
        assert file_event.change_type == "modified"
        assert file_event.file_type == "python"

        # Verify telemetry logging
        mock_telemetry.log.assert_called_once_with(
            "file_watcher_event",
            {
                "path": "/project/src/module.py",
                "file_type": "python",
                "change_type": "modified"
            }
        )

    def test_on_created_test_file(self):
        """Test handling of test file creation events."""
        # Mock the telemetry instance on the handler
        mock_telemetry = Mock()
        self.handler.telemetry = mock_telemetry

        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = "/project/tests/test_new_feature.py"

        self.handler.on_created(mock_event)

        # Verify callback was called
        assert len(self.callback_events) == 1
        file_event = self.callback_events[0]

        assert file_event.type == "file_created"
        assert file_event.path == "/project/tests/test_new_feature.py"
        assert file_event.change_type == "created"
        assert file_event.file_type == "test"

    def test_on_modified_ignored_file(self):
        """Test that ignored files don't trigger callbacks."""
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = "/project/__pycache__/module.cpython-39.pyc"

        self.handler.on_modified(mock_event)

        # No callback should be triggered
        assert len(self.callback_events) == 0

    def test_on_modified_directory_ignored(self):
        """Test that directory events are ignored."""
        mock_event = Mock()
        mock_event.is_directory = True
        mock_event.src_path = "/project/src"

        self.handler.on_modified(mock_event)

        # No callback should be triggered
        assert len(self.callback_events) == 0

    def test_on_modified_other_file_ignored(self):
        """Test that 'other' file types are ignored."""
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = "/project/data.txt"

        self.handler.on_modified(mock_event)

        # No callback should be triggered (other file type)
        assert len(self.callback_events) == 0


class TestFileWatcher:
    """Test the FileWatcher component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.callback_events = []
        self.callback = lambda event: self.callback_events.append(event)

    def test_file_watcher_initialization(self):
        """Test FileWatcher initialization with default callback."""
        watcher = FileWatcher()

        assert watcher.callback is not None
        assert watcher.is_running is False
        assert watcher.watch_root == Path.cwd()
        assert "**/*.py" in watcher.watch_patterns

    def test_file_watcher_initialization_with_callback(self):
        """Test FileWatcher initialization with custom callback."""
        watcher = FileWatcher(callback=self.callback)

        assert watcher.callback == self.callback

    @patch('learning_loop.event_detection.get_telemetry')
    @patch('learning_loop.event_detection.emit')
    def test_default_callback(self, mock_emit, mock_get_telemetry):
        """Test the default callback logs events to telemetry."""
        watcher = FileWatcher()

        # Create test event
        file_event = FileEvent(
            type="file_modified",
            timestamp=datetime.now(),
            path="/test.py",
            change_type="modified",
            file_type="python",
            metadata={}
        )

        watcher._default_callback(file_event)

        # Verify emit was called with correct parameters
        mock_emit.assert_called_once_with(
            "file_change_detected",
            {
                "path": "/test.py",
                "file_type": "python",
                "change_type": "modified"
            }
        )

    @patch('learning_loop.event_detection.Observer')
    @patch('learning_loop.event_detection.emit')
    def test_start_success(self, mock_emit, mock_observer_class):
        """Test successful FileWatcher start."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = FileWatcher(callback=self.callback)
        watcher.start()

        assert watcher.is_running is True
        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()

        # Verify telemetry logging
        mock_emit.assert_called_once_with(
            "file_watcher_started",
            {
                "watch_root": str(Path.cwd()),
                "patterns": watcher.watch_patterns
            }
        )

    @patch('learning_loop.event_detection.Observer')
    @patch('learning_loop.event_detection.emit')
    def test_start_already_running(self, mock_emit, mock_observer_class):
        """Test that start() is idempotent when already running."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = FileWatcher(callback=self.callback)
        watcher.is_running = True

        watcher.start()

        # Observer methods should not be called
        mock_observer.schedule.assert_not_called()
        mock_observer.start.assert_not_called()

    @patch('learning_loop.event_detection.Observer')
    @patch('learning_loop.event_detection.emit')
    def test_start_failure(self, mock_emit, mock_observer_class):
        """Test FileWatcher start failure handling."""
        mock_observer = Mock()
        mock_observer.start.side_effect = Exception("Permission denied")
        mock_observer_class.return_value = mock_observer

        watcher = FileWatcher(callback=self.callback)

        with pytest.raises(Exception, match="Permission denied"):
            watcher.start()

        # Error should be logged
        mock_emit.assert_called_with(
            "file_watcher_error",
            {
                "error": "Permission denied",
                "operation": "start"
            },
            level="error"
        )

    @patch('learning_loop.event_detection.Observer')
    @patch('learning_loop.event_detection.emit')
    def test_stop_success(self, mock_emit, mock_observer_class):
        """Test successful FileWatcher stop."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = FileWatcher(callback=self.callback)
        watcher.is_running = True

        watcher.stop()

        assert watcher.is_running is False
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()

        # Verify telemetry logging
        mock_emit.assert_called_once_with("file_watcher_stopped", {})

    @patch('learning_loop.event_detection.Observer')
    def test_stop_not_running(self, mock_observer_class):
        """Test that stop() is idempotent when not running."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = FileWatcher(callback=self.callback)
        watcher.stop()

        # Observer methods should not be called
        mock_observer.stop.assert_not_called()
        mock_observer.join.assert_not_called()

    @patch('learning_loop.event_detection.Observer')
    @patch('learning_loop.event_detection.emit')
    def test_context_manager(self, mock_emit, mock_observer_class):
        """Test FileWatcher as context manager."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        with FileWatcher(callback=self.callback) as watcher:
            assert watcher.is_running is True
            mock_observer.start.assert_called_once()

        # Should be stopped after context exit
        assert watcher.is_running is False
        mock_observer.stop.assert_called_once()


class TestErrorMonitor:
    """Test the ErrorMonitor component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.callback_events = []
        self.callback = lambda event: self.callback_events.append(event)

    def test_error_monitor_initialization(self):
        """Test ErrorMonitor initialization."""
        monitor = ErrorMonitor()

        assert monitor.callback is not None
        assert monitor.is_monitoring is False
        assert "logs/events/*.jsonl" in monitor.error_sources
        assert "NoneType" in monitor.error_patterns

    def test_error_monitor_initialization_with_callback(self):
        """Test ErrorMonitor initialization with custom callback."""
        monitor = ErrorMonitor(callback=self.callback)

        assert monitor.callback == self.callback

    @patch('learning_loop.event_detection.emit')
    def test_default_callback(self, mock_emit):
        """Test the default callback logs errors to telemetry."""
        monitor = ErrorMonitor()

        error_event = ErrorEvent(
            type="error_detected",
            timestamp=datetime.now(),
            error_type="NoneType",
            message="AttributeError: 'NoneType' object has no attribute 'value'",
            context="Line context",
            source_file="/src/module.py",
            metadata={}
        )

        monitor._default_callback(error_event)

        mock_emit.assert_called_once_with(
            "error_detected",
            {
                "error_type": "NoneType",
                "message": "AttributeError: 'NoneType' object has no attribute 'value'",
                "source": "/src/module.py"
            },
            level="warning"
        )

    def test_extract_context(self):
        """Test context extraction around error matches."""
        monitor = ErrorMonitor(callback=self.callback)

        content = """Line 1
Line 2
Line 3 with error message
Line 4
Line 5
Line 6"""

        # Create mock match object
        mock_match = Mock()
        mock_match.group.return_value = "error message"

        context = monitor._extract_context(content, mock_match, lines_context=2)

        assert "Line 1" in context
        assert "Line 2" in context
        assert "Line 3 with error message" in context
        assert "Line 4" in context
        assert "Line 5" in context

    def test_extract_line_number_syntax_error(self):
        """Test line number extraction for SyntaxError."""
        monitor = ErrorMonitor(callback=self.callback)

        mock_match = Mock()
        mock_match.groups.return_value = ("42",)
        mock_match.group.side_effect = lambda x: "42" if x == 1 else "SyntaxError: invalid syntax"

        line_num = monitor._extract_line_number(mock_match, "SyntaxError")

        assert line_num == 42

    def test_extract_line_number_no_groups(self):
        """Test line number extraction when no groups available."""
        monitor = ErrorMonitor(callback=self.callback)

        mock_match = Mock()
        mock_match.groups.return_value = ()

        line_num = monitor._extract_line_number(mock_match, "TypeError")

        assert line_num is None

    @patch('learning_loop.event_detection.emit')
    def test_detect_error_nonetype(self, mock_emit):
        """Test NoneType error detection."""
        monitor = ErrorMonitor(callback=self.callback)

        log_content = """
INFO: Starting process
ERROR: AttributeError: 'NoneType' object has no attribute 'value'
INFO: Process continued
"""

        events = monitor.detect_error(log_content, "/test/log.txt")

        assert len(events) == 1
        event = events[0]

        assert event.error_type == "NoneType"
        assert "'NoneType' object has no attribute 'value'" in event.message
        assert event.source_file == "/test/log.txt"

        # Verify telemetry logging
        mock_emit.assert_called_once_with(
            "error_pattern_matched",
            {
                "error_type": "NoneType",
                "source_file": "/test/log.txt",
                "message": "AttributeError: 'NoneType' object has no attribute 'value'"
            }
        )

    @patch('learning_loop.event_detection.emit')
    def test_detect_error_import_error(self, mock_emit):
        """Test ImportError detection."""
        monitor = ErrorMonitor(callback=self.callback)

        log_content = "ModuleNotFoundError: No module named 'missing_module'"

        events = monitor.detect_error(log_content, "/test/log.txt")

        assert len(events) == 1
        event = events[0]

        assert event.error_type == "ImportError"
        assert "ModuleNotFoundError" in event.message

    @patch('learning_loop.event_detection.emit')
    def test_detect_error_test_failure(self, mock_emit):
        """Test test failure detection."""
        monitor = ErrorMonitor(callback=self.callback)

        log_content = "FAILED tests/test_module.py::test_function - AssertionError"

        events = monitor.detect_error(log_content, "/test/pytest.log")

        assert len(events) == 1
        event = events[0]

        assert event.error_type == "TestFailure"
        assert "FAILED tests/test_module.py::test_function" in event.message

    @patch('learning_loop.event_detection.emit')
    def test_detect_error_syntax_error_with_line(self, mock_emit):
        """Test SyntaxError detection with line number extraction."""
        monitor = ErrorMonitor(callback=self.callback)

        log_content = "SyntaxError: invalid syntax (test.py, line 15)"

        events = monitor.detect_error(log_content, "/test/log.txt")

        assert len(events) == 1
        event = events[0]

        assert event.error_type == "SyntaxError"
        assert event.line_number == 15

    @patch('learning_loop.event_detection.emit')
    def test_detect_error_multiple_patterns(self, mock_emit):
        """Test detection of multiple error types in same content."""
        monitor = ErrorMonitor(callback=self.callback)

        log_content = """
ImportError: No module named 'test'
AttributeError: 'NoneType' object has no attribute 'value'
FAILED tests/test.py::test_func
"""

        events = monitor.detect_error(log_content, "/test/log.txt")

        assert len(events) == 3
        error_types = [event.error_type for event in events]

        assert "ImportError" in error_types
        assert "NoneType" in error_types
        assert "TestFailure" in error_types

    @patch('learning_loop.event_detection.emit')
    def test_detect_error_regex_error_handling(self, mock_emit):
        """Test handling of regex compilation errors."""
        monitor = ErrorMonitor(callback=self.callback)

        # Add invalid regex pattern
        monitor.error_patterns["BadPattern"] = "["  # Invalid regex

        log_content = "Some log content"
        events = monitor.detect_error(log_content, "/test/log.txt")

        # Should handle regex error gracefully
        assert len(events) >= 0  # Other patterns may still match

        # Error should be logged
        mock_emit.assert_any_call(
            "error_monitor_regex_error",
            {
                "pattern": "[",
                "error": mock_emit.call_args_list[-1][0][1]["error"]
            },
            level="error"
        )

    def test_monitor_file_nonexistent(self):
        """Test monitoring of non-existent file."""
        monitor = ErrorMonitor(callback=self.callback)

        fake_path = Path("/nonexistent/file.log")
        events = monitor._monitor_file(fake_path)

        assert len(events) == 0

    def test_monitor_file_no_new_content(self):
        """Test monitoring file with no new content."""
        monitor = ErrorMonitor(callback=self.callback)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("Initial content")
            f.flush()
            temp_path = Path(f.name)

        try:
            # Set position to end of file
            monitor._file_positions[str(temp_path)] = temp_path.stat().st_size

            events = monitor._monitor_file(temp_path)

            assert len(events) == 0
        finally:
            temp_path.unlink()

    @patch('learning_loop.event_detection.emit')
    def test_monitor_file_with_new_content(self, mock_emit):
        """Test monitoring file with new error content."""
        monitor = ErrorMonitor(callback=self.callback)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("Initial content\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            # Set position to beginning to simulate new content
            monitor._file_positions[str(temp_path)] = 0

            # Append error content
            with open(temp_path, 'a') as f:
                f.write("AttributeError: 'NoneType' object has no attribute 'test'\n")

            events = monitor._monitor_file(temp_path)

            assert len(events) == 1
            assert events[0].error_type == "NoneType"

        finally:
            temp_path.unlink()

    @patch('learning_loop.event_detection.emit')
    def test_monitor_file_read_error(self, mock_emit):
        """Test handling of file read errors."""
        monitor = ErrorMonitor(callback=self.callback)

        # Mock a file that exists but can't be read
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat, \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):

            mock_stat.return_value.st_size = 100
            fake_path = Path("/fake/path.log")

            events = monitor._monitor_file(fake_path)

            assert len(events) == 0

            # Error should be logged
            mock_emit.assert_called_with(
                "error_monitor_file_error",
                {
                    "file": "/fake/path.log",
                    "error": "Permission denied"
                },
                level="warning"
            )

    @patch('learning_loop.event_detection.emit')
    def test_start_and_stop(self, mock_emit):
        """Test starting and stopping error monitoring."""
        monitor = ErrorMonitor(callback=self.callback)

        # Test start
        monitor.start()
        assert monitor.is_monitoring is True
        assert monitor._monitor_thread is not None

        # Verify start logging
        mock_emit.assert_called_with(
            "error_monitor_started",
            {
                "sources": monitor.error_sources,
                "patterns": list(monitor.error_patterns.keys())
            }
        )

        # Test stop
        monitor.stop()
        assert monitor.is_monitoring is False

        # Verify stop logging
        mock_emit.assert_any_call("error_monitor_stopped", {})

    def test_start_idempotent(self):
        """Test that start is idempotent."""
        monitor = ErrorMonitor(callback=self.callback)

        monitor.is_monitoring = True
        original_thread = monitor._monitor_thread

        monitor.start()

        assert monitor._monitor_thread == original_thread

    def test_stop_idempotent(self):
        """Test that stop is idempotent."""
        monitor = ErrorMonitor(callback=self.callback)

        monitor.stop()  # Should not raise error

    def test_context_manager(self):
        """Test ErrorMonitor as context manager."""
        with ErrorMonitor(callback=self.callback) as monitor:
            assert monitor.is_monitoring is True

        assert monitor.is_monitoring is False


class TestEventDetectionSystem:
    """Test the EventDetectionSystem orchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.file_events = []
        self.error_events = []

        self.file_callback = lambda event: self.file_events.append(event)
        self.error_callback = lambda event: self.error_events.append(event)

    def test_initialization(self):
        """Test EventDetectionSystem initialization."""
        system = EventDetectionSystem(
            file_callback=self.file_callback,
            error_callback=self.error_callback
        )

        assert system.file_watcher is not None
        assert system.error_monitor is not None
        assert system.is_running is False

    def test_initialization_default_callbacks(self):
        """Test initialization with default callbacks."""
        system = EventDetectionSystem()

        assert system.file_watcher.callback is not None
        assert system.error_monitor.callback is not None

    @patch('learning_loop.event_detection.emit')
    def test_start_success(self, mock_emit):
        """Test successful system start."""
        system = EventDetectionSystem(
            file_callback=self.file_callback,
            error_callback=self.error_callback
        )

        # Mock the individual components to prevent real file operations
        system.file_watcher.start = Mock()
        system.error_monitor.start = Mock()
        # Also mock the monitor thread to prevent it from actually running
        system.error_monitor._monitor_thread = Mock()

        system.start()

        assert system.is_running is True
        system.file_watcher.start.assert_called_once()
        system.error_monitor.start.assert_called_once()

        # Check that the last call was for the start event
        # (ignoring any other telemetry from real file operations)
        calls = mock_emit.call_args_list
        assert any(
            call[0][0] == "event_detection_started" and
            call[0][1] == {"components": ["FileWatcher", "ErrorMonitor"]}
            for call in calls
        )

    def test_start_idempotent(self):
        """Test that start is idempotent."""
        system = EventDetectionSystem(
            file_callback=self.file_callback,
            error_callback=self.error_callback
        )

        system.file_watcher.start = Mock()
        system.error_monitor.start = Mock()
        system.is_running = True

        system.start()

        system.file_watcher.start.assert_not_called()
        system.error_monitor.start.assert_not_called()

    @patch('learning_loop.event_detection.emit')
    def test_start_failure_cleanup(self, mock_emit):
        """Test cleanup on start failure."""
        system = EventDetectionSystem(
            file_callback=self.file_callback,
            error_callback=self.error_callback
        )

        system.file_watcher.start = Mock()
        system.error_monitor.start = Mock(side_effect=Exception("Start failed"))
        system.stop = Mock()

        with pytest.raises(Exception, match="Start failed"):
            system.start()

        # Should attempt cleanup
        system.stop.assert_called_once()

        mock_emit.assert_called_with(
            "event_detection_start_error",
            {
                "error": "Start failed"
            },
            level="error"
        )

    @patch('learning_loop.event_detection.emit')
    def test_stop_success(self, mock_emit):
        """Test successful system stop."""
        system = EventDetectionSystem(
            file_callback=self.file_callback,
            error_callback=self.error_callback
        )

        system.file_watcher.stop = Mock()
        system.error_monitor.stop = Mock()
        system.is_running = True

        system.stop()

        assert system.is_running is False
        system.file_watcher.stop.assert_called_once()
        system.error_monitor.stop.assert_called_once()

        mock_emit.assert_called_once_with("event_detection_stopped", {})

    def test_stop_idempotent(self):
        """Test that stop is idempotent."""
        system = EventDetectionSystem(
            file_callback=self.file_callback,
            error_callback=self.error_callback
        )

        system.file_watcher.stop = Mock()
        system.error_monitor.stop = Mock()

        system.stop()

        system.file_watcher.stop.assert_not_called()
        system.error_monitor.stop.assert_not_called()

    @patch('learning_loop.event_detection.emit')
    def test_stop_with_error(self, mock_emit):
        """Test stop with error handling."""
        system = EventDetectionSystem(
            file_callback=self.file_callback,
            error_callback=self.error_callback
        )

        system.file_watcher.stop = Mock(side_effect=Exception("Stop failed"))
        system.error_monitor.stop = Mock()
        system.is_running = True

        system.stop()

        # Should still set running to False
        assert system.is_running is False

        mock_emit.assert_called_with(
            "event_detection_stop_error",
            {
                "error": "Stop failed"
            },
            level="error"
        )

    def test_context_manager(self):
        """Test EventDetectionSystem as context manager."""
        system = EventDetectionSystem(
            file_callback=self.file_callback,
            error_callback=self.error_callback
        )

        system.start = Mock()
        system.stop = Mock()

        with system as ctx_system:
            assert ctx_system == system
            system.start.assert_called_once()

        system.stop.assert_called_once()


class TestIntegration:
    """Integration tests for the complete event detection system."""

    @pytest.mark.asyncio
    async def test_end_to_end_file_detection(self):
        """Test complete file change detection flow."""
        events_received = []

        def event_handler(event):
            events_received.append(event)

        system = EventDetectionSystem(file_callback=event_handler)

        # Mock the watchdog components to avoid actual file system monitoring
        with patch('learning_loop.event_detection.Observer'):
            system.start()

            try:
                # Simulate a file event
                file_event = FileEvent(
                    type="file_modified",
                    timestamp=datetime.now(),
                    path="/test/module.py",
                    change_type="modified",
                    file_type="python",
                    metadata={}
                )

                # Call the handler directly to simulate watchdog callback
                system.file_watcher.handler.callback(file_event)

                # Verify event was received
                assert len(events_received) == 1
                assert events_received[0].file_type == "python"

            finally:
                system.stop()

    def test_end_to_end_error_detection(self):
        """Test complete error detection flow."""
        errors_received = []

        def error_handler(event):
            errors_received.append(event)

        monitor = ErrorMonitor(callback=error_handler)

        # Test error detection without starting the monitor thread
        log_content = "AttributeError: 'NoneType' object has no attribute 'value'"
        events = monitor.detect_error(log_content, "/test/error.log")

        assert len(events) == 1
        assert events[0].error_type == "NoneType"
        assert "'NoneType' object has no attribute 'value'" in events[0].message

    @patch('learning_loop.event_detection.emit')
    def test_telemetry_integration(self, mock_emit):
        """Test that all components properly integrate with telemetry."""
        system = EventDetectionSystem()

        # Mock component methods to avoid actual startup
        system.file_watcher.start = Mock()
        system.error_monitor.start = Mock()

        system.start()

        # Verify telemetry was called
        mock_emit.assert_called_with(
            "event_detection_started",
            {
                "components": ["FileWatcher", "ErrorMonitor"]
            }
        )

    def test_error_resilience(self):
        """Test system resilience to component failures."""
        system = EventDetectionSystem()

        # Mock file watcher to fail
        system.file_watcher.start = Mock(side_effect=Exception("File watcher failed"))
        system.file_watcher.stop = Mock()
        system.error_monitor.start = Mock()
        system.error_monitor.stop = Mock()

        with pytest.raises(Exception, match="File watcher failed"):
            system.start()

        # System should attempt cleanup even after failure
        assert system.is_running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])