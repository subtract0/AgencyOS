"""Anthropic Memory Tool Implementation

Implements BetaAbstractMemoryTool for file-based persistent memory storage.
Enables Claude to maintain context across conversations via /memories directory.

Security Features:
- Path traversal attack prevention (../, %2e%2e/, etc.)
- Restricted to /memories base directory
- File size limits to prevent unbounded growth
- Safe path validation and normalization

Usage:
    from tools.anthropic_memory_tool import AgencyMemoryTool

    tool = AgencyMemoryTool(base_dir="~/.agency/memories")

    # View directory
    content = tool.view("/memories")

    # Create file
    tool.create("/memories/notes.txt", "Important information")

    # Edit file
    tool.str_replace("/memories/notes.txt", "old", "new")
"""

import os
import re
import shutil
from pathlib import Path
from typing import Any

try:
    from anthropic.types.beta import BetaAbstractMemoryTool
except ImportError:
    # Fallback for older versions
    class BetaAbstractMemoryTool:
        """Fallback base class if anthropic SDK doesn't have memory tool"""

        pass


class AgencyMemoryTool(BetaAbstractMemoryTool):
    """File-based memory tool for Anthropic Claude

    Implements the 6 memory operations required by BetaAbstractMemoryTool:
    - view: Read directory/file contents
    - create: Create or overwrite files
    - str_replace: Replace text in files
    - insert: Insert text at specific line
    - delete: Delete files/directories
    - rename: Rename or move files/directories

    Args:
        base_dir: Root directory for memory storage (default: ~/.agency/memories)
        max_file_size: Maximum file size in bytes (default: 1MB)
        max_view_lines: Maximum lines to show in view (default: 1000)
    """

    def __init__(
        self,
        base_dir: str | None = None,
        max_file_size: int = 1_000_000,  # 1MB
        max_view_lines: int = 1000,
    ):
        if base_dir is None:
            base_dir = str(Path.home() / ".agency" / "memories")

        self.base_dir = Path(base_dir).resolve()
        self.max_file_size = max_file_size
        self.max_view_lines = max_view_lines

        # Create base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: str) -> Path:
        """Validate and normalize path to prevent security issues

        Prevents:
        - Path traversal attacks (../, ../../, etc.)
        - URL-encoded traversal (%2e%2e%2f)
        - Absolute paths outside /memories
        - Symlink attacks

        Args:
            path: Virtual path starting with /memories

        Returns:
            Resolved absolute path within base_dir

        Raises:
            ValueError: If path is invalid or contains traversal attempts
        """
        # Must start with /memories
        if not path.startswith("/memories"):
            raise ValueError(f"Invalid path: must start with /memories (got: {path})")

        # Detect traversal patterns (before and after URL decoding)
        traversal_patterns = [
            r"\.\.",  # ..
            r"%2e%2e",  # URL-encoded ..
            r"%252e%252e",  # Double-encoded ..
            r"\.%2e",  # Mixed encoding
        ]

        for pattern in traversal_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                raise ValueError(f"Path traversal attempt detected: {path}")

        # Remove /memories prefix and normalize
        relative_path = path[len("/memories") :].lstrip("/")

        # Resolve to absolute path
        full_path = (self.base_dir / relative_path).resolve()

        # Ensure resolved path is within base_dir
        try:
            full_path.relative_to(self.base_dir)
        except ValueError as e:
            raise ValueError(f"Path escapes memory directory: {path} -> {full_path}") from e

        return full_path

    def view(self, path: str, view_range: list[int] | None = None) -> str:
        """View directory contents or file contents

        For directories: Returns list of files/subdirectories
        For files: Returns file contents with optional line range

        Args:
            path: Virtual path (e.g., /memories/notes.txt)
            view_range: Optional [start_line, end_line] (1-indexed, inclusive)

        Returns:
            String representation of directory or file contents
        """
        full_path = self._validate_path(path)

        if not full_path.exists():
            return f"Error: Path does not exist: {path}"

        # Directory listing
        if full_path.is_dir():
            try:
                entries = sorted(full_path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
                lines = []
                for entry in entries:
                    prefix = "[DIR]" if entry.is_dir() else "[FILE]"
                    size = "" if entry.is_dir() else f" ({entry.stat().st_size} bytes)"
                    lines.append(f"{prefix} {entry.name}{size}")

                return "\n".join(lines) if lines else "(empty directory)"
            except Exception as e:
                return f"Error reading directory: {e}"

        # File contents
        try:
            with open(full_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Apply line range if specified
            if view_range:
                start, end = view_range
                # Convert to 0-indexed, clamp to valid range
                start = max(0, start - 1)
                end = min(len(lines), end)
                lines = lines[start:end]

            # Limit total lines shown
            if len(lines) > self.max_view_lines:
                lines = lines[: self.max_view_lines]
                lines.append(f"\n... (truncated, showing first {self.max_view_lines} lines)")

            return "".join(lines)
        except UnicodeDecodeError:
            return f"Error: File is not valid UTF-8 text: {path}"
        except Exception as e:
            return f"Error reading file: {e}"

    def create(self, path: str, file_text: str) -> str:
        """Create or overwrite a file

        Args:
            path: Virtual path (e.g., /memories/notes.txt)
            file_text: File contents

        Returns:
            Success or error message
        """
        full_path = self._validate_path(path)

        # Check file size limit
        if len(file_text.encode("utf-8")) > self.max_file_size:
            return f"Error: File exceeds size limit ({self.max_file_size} bytes)"

        # Prevent overwriting directories
        if full_path.exists() and full_path.is_dir():
            return f"Error: Cannot overwrite directory: {path}"

        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_text)

            return f"Successfully created: {path} ({len(file_text)} chars)"
        except Exception as e:
            return f"Error creating file: {e}"

    def str_replace(self, path: str, old_str: str, new_str: str) -> str:
        """Replace text in a file

        Args:
            path: Virtual path (e.g., /memories/notes.txt)
            old_str: Text to find
            new_str: Replacement text

        Returns:
            Success or error message
        """
        full_path = self._validate_path(path)

        if not full_path.exists():
            return f"Error: File does not exist: {path}"

        if full_path.is_dir():
            return f"Error: Cannot edit directory: {path}"

        try:
            # Read file
            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            # Check if old_str exists
            if old_str not in content:
                return f"Error: String not found in file: {old_str[:50]}..."

            # Replace
            new_content = content.replace(old_str, new_str)

            # Check size limit
            if len(new_content.encode("utf-8")) > self.max_file_size:
                return f"Error: Replacement exceeds size limit ({self.max_file_size} bytes)"

            # Write back
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            occurrences = content.count(old_str)
            return f"Successfully replaced {occurrences} occurrence(s) in {path}"
        except UnicodeDecodeError:
            return f"Error: File is not valid UTF-8 text: {path}"
        except Exception as e:
            return f"Error replacing text: {e}"

    def insert(self, path: str, insert_line: int, insert_text: str) -> str:
        """Insert text at a specific line

        Args:
            path: Virtual path (e.g., /memories/notes.txt)
            insert_line: Line number (1-indexed, inserts before this line)
            insert_text: Text to insert

        Returns:
            Success or error message
        """
        full_path = self._validate_path(path)

        if not full_path.exists():
            return f"Error: File does not exist: {path}"

        if full_path.is_dir():
            return f"Error: Cannot edit directory: {path}"

        try:
            # Read file
            with open(full_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Convert to 0-indexed, clamp to valid range
            insert_pos = max(0, min(len(lines), insert_line - 1))

            # Insert text
            lines.insert(insert_pos, insert_text)

            # Check size limit
            new_content = "".join(lines)
            if len(new_content.encode("utf-8")) > self.max_file_size:
                return f"Error: Insertion exceeds size limit ({self.max_file_size} bytes)"

            # Write back
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return f"Successfully inserted at line {insert_line} in {path}"
        except UnicodeDecodeError:
            return f"Error: File is not valid UTF-8 text: {path}"
        except Exception as e:
            return f"Error inserting text: {e}"

    def delete(self, path: str) -> str:
        """Delete a file or directory

        Args:
            path: Virtual path (e.g., /memories/notes.txt)

        Returns:
            Success or error message
        """
        full_path = self._validate_path(path)

        # Don't allow deleting root /memories
        if full_path == self.base_dir:
            return "Error: Cannot delete root /memories directory"

        if not full_path.exists():
            return f"Error: Path does not exist: {path}"

        try:
            if full_path.is_dir():
                shutil.rmtree(full_path)
                return f"Successfully deleted directory: {path}"
            else:
                full_path.unlink()
                return f"Successfully deleted file: {path}"
        except Exception as e:
            return f"Error deleting: {e}"

    def rename(self, old_path: str, new_path: str) -> str:
        """Rename or move a file/directory

        Args:
            old_path: Current virtual path
            new_path: New virtual path

        Returns:
            Success or error message
        """
        old_full_path = self._validate_path(old_path)
        new_full_path = self._validate_path(new_path)

        if not old_full_path.exists():
            return f"Error: Source does not exist: {old_path}"

        if new_full_path.exists():
            return f"Error: Destination already exists: {new_path}"

        # Don't allow renaming root /memories
        if old_full_path == self.base_dir:
            return "Error: Cannot rename root /memories directory"

        try:
            # Create parent directory for destination if needed
            new_full_path.parent.mkdir(parents=True, exist_ok=True)

            # Rename/move
            old_full_path.rename(new_full_path)

            return f"Successfully renamed: {old_path} -> {new_path}"
        except Exception as e:
            return f"Error renaming: {e}"


def create_memory_tool(
    session_id: str | None = None, base_dir: str | None = None
) -> AgencyMemoryTool:
    """Factory function to create a memory tool instance

    Args:
        session_id: Optional session ID for isolated memory space
        base_dir: Optional custom base directory

    Returns:
        Configured AgencyMemoryTool instance
    """
    if base_dir is None:
        base_dir = str(Path.home() / ".agency" / "memories")
        if session_id:
            base_dir = str(Path(base_dir) / session_id)

    return AgencyMemoryTool(base_dir=base_dir)
