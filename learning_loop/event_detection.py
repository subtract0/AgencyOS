"""
Event Detection Layer: Monitors filesystem changes and errors for learning opportunities.

This module implements the core components for detecting events that could trigger
autonomous learning and healing responses, as specified in SPEC-LEARNING-001.
"""

import os
import re
import json
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

# Global registry to prevent background monitor leakage across tests/runs
_ERROR_MONITOR_REGISTRY: "set[ErrorMonitor]"  # forward-declared; assigned below

from core.telemetry import get_telemetry, emit

# Initialize the global registry for error monitors
try:
    _ERROR_MONITOR_REGISTRY = set()
except Exception:
    _ERROR_MONITOR_REGISTRY = set()


@dataclass
class Event:
    """Base event class for all detected events."""
    type: str
    timestamp: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            type=data["type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data["metadata"]
        )


@dataclass
class FileEvent(Event):
    """Event triggered by file system changes."""
    path: str
    change_type: str  # 'modified', 'created', 'deleted'
    file_type: str    # 'python', 'markdown', 'test', 'config'

    def __post_init__(self):
        if not hasattr(self, 'metadata'):
            self.metadata = {}
        self.metadata.update({
            "path": self.path,
            "change_type": self.change_type,
            "file_type": self.file_type
        })


@dataclass
class ErrorEvent(Event):
    """Event triggered by error detection in logs."""
    error_type: str
    message: str
    context: str
    source_file: Optional[str] = None
    line_number: Optional[int] = None

    def __post_init__(self):
        if not hasattr(self, 'metadata'):
            self.metadata = {}
        self.metadata.update({
            "error_type": self.error_type,
            "message": self.message,
            "context": self.context,
            "source_file": self.source_file,
            "line_number": self.line_number
        })


class FileWatchHandler(FileSystemEventHandler):
    """Handles file system events for FileWatcher."""

    def __init__(self, callback: Callable[[FileEvent], None]):
        self.callback = callback
        self.telemetry = get_telemetry()

        # Ignore patterns as specified in the spec
        self.ignore_patterns = {
            "__pycache__",
            ".git",
            "logs",
            ".pyc",
            ".pyo",
            ".DS_Store",
            ".pytest_cache"
        }

    def _should_ignore(self, path: str) -> bool:
        """Check if the file should be ignored based on ignore patterns."""
        path_parts = Path(path).parts
        for pattern in self.ignore_patterns:
            if any(pattern in part for part in path_parts):
                return True
        return False

    def _get_file_type(self, path: str) -> str:
        """Determine file type based on path and extension."""
        path_obj = Path(path)

        if path_obj.suffix == ".py":
            if "test" in path_obj.name or "tests" in path_obj.parts:
                return "test"
            return "python"
        elif path_obj.suffix == ".md":
            return "markdown"
        elif path_obj.suffix in [".yml", ".yaml", ".json", ".toml"]:
            return "config"
        else:
            return "other"

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory or self._should_ignore(event.src_path):
            return

        file_type = self._get_file_type(event.src_path)
        if file_type == "other":
            return

        file_event = FileEvent(
            type="file_modified",
            timestamp=datetime.now(),
            path=event.src_path,
            change_type="modified",
            file_type=file_type,
            metadata={}
        )

        # Log to telemetry
        self.telemetry.log("file_watcher_event", {
            "path": event.src_path,
            "file_type": file_type,
            "change_type": "modified"
        })

        self.callback(file_event)

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory or self._should_ignore(event.src_path):
            return

        file_type = self._get_file_type(event.src_path)
        if file_type == "other":
            return

        file_event = FileEvent(
            type="file_created",
            timestamp=datetime.now(),
            path=event.src_path,
            change_type="created",
            file_type=file_type,
            metadata={}
        )

        # Log to telemetry
        self.telemetry.log("file_watcher_event", {
            "path": event.src_path,
            "file_type": file_type,
            "change_type": "created"
        })

        self.callback(file_event)


class FileWatcher:
    """
    Monitors filesystem for changes that might trigger learning.

    Watches patterns as specified in SPEC-LEARNING-001:
    - **/*.py (Python source files)
    - **/*.md (Documentation)
    - **/tests/*.py (Test files)
    - .github/**/*.yml (CI/CD configs)
    """

    def __init__(self, callback: Optional[Callable[[FileEvent], None]] = None):
        self.callback = callback or self._default_callback
        self.observer = Observer()
        self.handler = FileWatchHandler(self.callback)
        self.telemetry = get_telemetry()
        self.is_running = False

        # Watch patterns from spec
        self.watch_patterns = [
            "**/*.py",           # Python source files
            "**/*.md",           # Documentation
            "**/tests/*.py",     # Test files
            ".github/**/*.yml"   # CI/CD configs
        ]

        # Root directory to watch
        self.watch_root = Path.cwd()

    def _default_callback(self, event: FileEvent):
        """Default callback that just logs events."""
        emit("file_change_detected", {
            "path": event.path,
            "file_type": event.file_type,
            "change_type": event.change_type
        })

    def start(self):
        """Start monitoring filesystem changes."""
        if self.is_running:
            return

        try:
            # Watch the root directory recursively
            self.observer.schedule(
                self.handler,
                str(self.watch_root),
                recursive=True
            )
            self.observer.start()
            self.is_running = True

            emit("file_watcher_started", {
                "watch_root": str(self.watch_root),
                "patterns": self.watch_patterns
            })

        except Exception as e:
            emit("file_watcher_error", {
                "error": str(e),
                "operation": "start"
            }, level="error")
            raise

    def stop(self):
        """Stop monitoring filesystem changes."""
        if not self.is_running:
            return

        try:
            self.observer.stop()
            self.observer.join()
            self.is_running = False

            emit("file_watcher_stopped", {})

        except Exception as e:
            emit("file_watcher_error", {
                "error": str(e),
                "operation": "stop"
            }, level="error")
            raise

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class ErrorMonitor:
    """
    Monitors logs and test outputs for errors.

    Sources as specified in SPEC-LEARNING-001:
    - logs/events/*.jsonl (Telemetry events)
    - pytest_output.log (Test failures)
    - .git/hooks/pre-commit.log (Commit failures)
    """

    def __init__(self, callback: Optional[Callable[[ErrorEvent], None]] = None):
        self.callback = callback or self._default_callback
        self.telemetry = get_telemetry()
        self.is_monitoring = False
        self._stop_event = threading.Event()
        self._monitor_thread = None

        # Error sources from spec
        self.error_sources = [
            "logs/events/*.jsonl",     # Telemetry events
            "pytest_output.log",       # Test failures
            ".git/hooks/pre-commit.log"  # Commit failures
        ]

        # Error patterns from spec
        self.error_patterns = {
            "NoneType": r"AttributeError.*'NoneType'.*has no attribute.*",
            "ImportError": r"(?:ImportError|ModuleNotFoundError).*",
            "TestFailure": r"FAILED.*test_.*",
            "SyntaxError": r"SyntaxError.*line\s+(\d+)",
            "TypeError": r"TypeError.*(?:arguments?|positional|keyword)"
        }

        # Track last read positions for efficient monitoring
        self._file_positions = {}

    def _default_callback(self, event: ErrorEvent):
        """Default callback that just logs errors."""
        emit("error_detected", {
            "error_type": event.error_type,
            "message": event.message,
            "source": event.source_file
        }, level="warning")

    def _extract_context(self, content: str, match: re.Match, lines_context: int = 3) -> str:
        """Extract context around a matched error."""
        lines = content.split('\n')

        # Find the line with the match
        match_line_idx = None
        match_text = match.group(0)

        for i, line in enumerate(lines):
            if match_text in line:
                match_line_idx = i
                break

        if match_line_idx is None:
            return match_text

        # Get context lines
        start_idx = max(0, match_line_idx - lines_context)
        end_idx = min(len(lines), match_line_idx + lines_context + 1)

        context_lines = lines[start_idx:end_idx]
        return '\n'.join(context_lines)

    def _extract_line_number(self, match: re.Match, error_type: str) -> Optional[int]:
        """Extract line number from error match if available."""
        if error_type == "SyntaxError" and len(match.groups()) > 0:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
        return None

    def detect_error(self, content: str, source_file: str) -> List[ErrorEvent]:
        """Extract error information from log content."""
        events = []

        for error_type, pattern in self.error_patterns.items():
            try:
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)

                for match in matches:
                    context = self._extract_context(content, match)
                    line_number = self._extract_line_number(match, error_type)

                    error_event = ErrorEvent(
                        type="error_detected",
                        timestamp=datetime.now(),
                        error_type=error_type,
                        message=match.group(0),
                        context=context,
                        source_file=source_file,
                        line_number=line_number,
                        metadata={}
                    )

                    events.append(error_event)

                    # Log to telemetry
                    emit("error_pattern_matched", {
                        "error_type": error_type,
                        "source_file": source_file,
                        "message": match.group(0)[:200]  # Truncate long messages
                    })

            except re.error as e:
                emit("error_monitor_regex_error", {
                    "pattern": pattern,
                    "error": str(e)
                }, level="error")

        return events

    def _monitor_file(self, file_path: Path) -> List[ErrorEvent]:
        """Monitor a single file for new errors."""
        events = []

        try:
            if not file_path.exists():
                return events

            # Get current file size
            current_size = file_path.stat().st_size
            last_position = self._file_positions.get(str(file_path), 0)

            # Only read new content
            if current_size <= last_position:
                return events

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                new_content = f.read()

                if new_content.strip():
                    events = self.detect_error(new_content, str(file_path))

                # Update position
                self._file_positions[str(file_path)] = f.tell()

        except Exception as e:
            emit("error_monitor_file_error", {
                "file": str(file_path),
                "error": str(e)
            }, level="warning")

        return events

    def _monitor_sources(self):
        """Monitor all error sources in a loop."""
        while not self._stop_event.is_set():
            try:
                # Expand glob patterns and monitor files
                for source_pattern in self.error_sources:
                    if "*" in source_pattern:
                        # Handle glob patterns
                        import glob
                        files = glob.glob(source_pattern, recursive=True)
                    else:
                        # Handle single files
                        files = [source_pattern] if os.path.exists(source_pattern) else []

                    for file_path_str in files:
                        file_path = Path(file_path_str)
                        events = self._monitor_file(file_path)

                        for event in events:
                            try:
                                self.callback(event)
                            except Exception as e:
                                emit("error_monitor_callback_error", {
                                    "error": str(e),
                                    "event": event.to_dict()
                                }, level="error")

                # Sleep before next monitoring cycle
                self._stop_event.wait(5.0)  # 5 second monitoring interval

            except Exception as e:
                emit("error_monitor_cycle_error", {
                    "error": str(e)
                }, level="error")
                self._stop_event.wait(10.0)  # Longer sleep on error

    @classmethod
    def stop_all(cls):
        """Stop all running ErrorMonitor instances (safety for tests/runs)."""
        try:
            # Create a snapshot to avoid concurrent modification
            for monitor in list(_ERROR_MONITOR_REGISTRY):
                try:
                    monitor.stop()
                except Exception:
                    continue
        except Exception:
            pass


    def start(self):
        """Start monitoring log files for errors."""
        if self.is_monitoring:
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_sources,
            name="ErrorMonitor",
            daemon=True
        )
        self._monitor_thread.start()
        self.is_monitoring = True

        # Register this monitor globally to prevent leakage across tests
        try:
            _ERROR_MONITOR_REGISTRY.add(self)
        except Exception:
            pass

        emit("error_monitor_started", {
            "sources": self.error_sources,
            "patterns": list(self.error_patterns.keys())
        })

    def stop(self):
        """Stop monitoring log files."""
        if not self.is_monitoring:
            return

        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10.0)

        self.is_monitoring = False

        # Deregister from global registry
        try:
            _ERROR_MONITOR_REGISTRY.discard(self)
        except Exception:
            pass

        emit("error_monitor_stopped", {})

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class EventDetectionSystem:
    """
    Orchestrates FileWatcher and ErrorMonitor components.

    Provides a unified interface for starting/stopping event detection
    and routing events to appropriate handlers.
    """

    def __init__(self,
                 file_callback: Optional[Callable[[FileEvent], None]] = None,
                 error_callback: Optional[Callable[[ErrorEvent], None]] = None):
        # Safety: stop any previously running error monitors to avoid cross-test leakage
        try:
            ErrorMonitor.stop_all()
        except Exception:
            pass

        self.file_watcher = FileWatcher(file_callback)
        self.error_monitor = ErrorMonitor(error_callback)
        self.telemetry = get_telemetry()
        self.is_running = False

    def start(self):
        """Start both file watching and error monitoring."""
        if self.is_running:
            return

        try:
            self.file_watcher.start()
            self.error_monitor.start()
            self.is_running = True

            emit("event_detection_started", {
                "components": ["FileWatcher", "ErrorMonitor"]
            })

        except Exception as e:
            # Cleanup on failure
            self.stop()
            emit("event_detection_start_error", {
                "error": str(e)
            }, level="error")
            raise

    def stop(self):
        """Stop both file watching and error monitoring."""
        if not self.is_running:
            return

        try:
            self.file_watcher.stop()
            self.error_monitor.stop()
            self.is_running = False

            emit("event_detection_stopped", {})

        except Exception as e:
            self.is_running = False  # Always set to False even on error
            emit("event_detection_stop_error", {
                "error": str(e)
            }, level="error")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()