"""
Unified Edit Interface - Consolidates edit, multi_edit, and notebook_edit functionality.
Single entry point for all file modification operations.
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


class UnifiedEdit:
    """
    Unified interface for all file editing operations.
    Consolidates edit.py, multi_edit.py, and notebook_edit.py functionality.
    """

    def __init__(self):
        """Initialize unified edit interface."""
        # Import actual tools lazily to avoid circular dependencies
        self._edit_tool = None
        self._multi_edit_tool = None
        self._notebook_edit_tool = None

    def _get_edit_tool(self):
        """Lazy load edit tool."""
        if self._edit_tool is None:
            from tools.edit import Edit
            self._edit_tool = Edit
        return self._edit_tool

    def _get_multi_edit_tool(self):
        """Lazy load multi edit tool."""
        if self._multi_edit_tool is None:
            from tools.multi_edit import MultiEdit
            self._multi_edit_tool = MultiEdit
        return self._multi_edit_tool

    def _get_notebook_edit_tool(self):
        """Lazy load notebook edit tool."""
        if self._notebook_edit_tool is None:
            from tools.notebook_edit import NotebookEdit
            self._notebook_edit_tool = NotebookEdit
        return self._notebook_edit_tool

    def edit(
        self,
        file_path: str,
        old_string: str = None,
        new_string: str = None,
        edits: List[Dict[str, str]] = None,
        cell_id: str = None,
        cell_type: str = None,
        edit_mode: str = "replace",
        replace_all: bool = False
    ) -> str:
        """
        Unified edit method that automatically selects the appropriate tool.

        Args:
            file_path: Path to the file to edit
            old_string: String to replace (for single edits)
            new_string: Replacement string (for single edits)
            edits: List of edit operations (for multiple edits)
            cell_id: Jupyter notebook cell ID (for notebook edits)
            cell_type: Jupyter notebook cell type
            edit_mode: Edit mode for notebooks (replace, insert, delete)
            replace_all: Replace all occurrences

        Returns:
            Result string from the appropriate edit tool
        """
        file_path = str(file_path)

        # Detect file type
        if file_path.endswith('.ipynb'):
            return self._edit_notebook(
                file_path, old_string or new_string,
                cell_id, cell_type, edit_mode
            )
        elif edits and len(edits) > 1:
            return self._multi_edit(file_path, edits)
        else:
            return self._single_edit(
                file_path, old_string, new_string, replace_all
            )

    def _single_edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False
    ) -> str:
        """
        Perform a single edit operation.

        Args:
            file_path: File to edit
            old_string: String to replace
            new_string: Replacement string
            replace_all: Replace all occurrences

        Returns:
            Edit result
        """
        Edit = self._get_edit_tool()
        tool = Edit(
            file_path=file_path,
            old_string=old_string,
            new_string=new_string,
            replace_all=replace_all
        )
        return tool.run()

    def _multi_edit(
        self,
        file_path: str,
        edits: List[Dict[str, str]]
    ) -> str:
        """
        Perform multiple edit operations.

        Args:
            file_path: File to edit
            edits: List of edit operations

        Returns:
            Edit result
        """
        MultiEdit = self._get_multi_edit_tool()
        tool = MultiEdit(
            file_path=file_path,
            edits=edits
        )
        return tool.run()

    def _edit_notebook(
        self,
        notebook_path: str,
        new_source: str,
        cell_id: str = None,
        cell_type: str = None,
        edit_mode: str = "replace"
    ) -> str:
        """
        Edit a Jupyter notebook.

        Args:
            notebook_path: Path to notebook
            new_source: New cell content
            cell_id: Cell ID to edit
            cell_type: Cell type (code/markdown)
            edit_mode: Edit mode (replace/insert/delete)

        Returns:
            Edit result
        """
        NotebookEdit = self._get_notebook_edit_tool()
        tool = NotebookEdit(
            notebook_path=notebook_path,
            new_source=new_source,
            cell_id=cell_id,
            cell_type=cell_type,
            edit_mode=edit_mode
        )
        return tool.run()

    def smart_edit(
        self,
        file_path: str,
        changes: Union[str, Dict[str, str], List[Dict[str, str]]]
    ) -> str:
        """
        Smart edit that automatically determines the best approach.

        Args:
            file_path: File to edit
            changes: Changes to make (various formats supported)

        Returns:
            Edit result
        """
        file_path = str(file_path)

        # Handle different input formats
        if isinstance(changes, str):
            # Simple replacement assumed
            lines = changes.split('\n')
            if len(lines) >= 2:
                return self.edit(
                    file_path=file_path,
                    old_string=lines[0],
                    new_string=lines[1]
                )
            else:
                return "Invalid change format: Need old and new strings"

        elif isinstance(changes, dict):
            # Single edit operation
            return self.edit(
                file_path=file_path,
                old_string=changes.get('old', changes.get('old_string')),
                new_string=changes.get('new', changes.get('new_string')),
                replace_all=changes.get('replace_all', False)
            )

        elif isinstance(changes, list):
            # Multiple edits
            if len(changes) == 1:
                return self.smart_edit(file_path, changes[0])
            else:
                return self.edit(file_path=file_path, edits=changes)

        else:
            return f"Unsupported changes format: {type(changes)}"

    def validate_edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str
    ) -> Dict[str, Any]:
        """
        Validate an edit before applying it.

        Args:
            file_path: File to edit
            old_string: String to replace
            new_string: Replacement string

        Returns:
            Validation result with details
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {}
        }

        # Check file exists
        if not os.path.exists(file_path):
            result["valid"] = False
            result["errors"].append(f"File not found: {file_path}")
            return result

        # Check file is readable
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Cannot read file: {e}")
            return result

        # Check old_string exists
        occurrences = content.count(old_string)
        if occurrences == 0:
            result["valid"] = False
            result["errors"].append(f"String not found: {old_string}")
        elif occurrences > 1:
            result["warnings"].append(
                f"String appears {occurrences} times. Consider using replace_all=True"
            )
            result["info"]["occurrences"] = occurrences

        # Check strings are different
        if old_string == new_string:
            result["valid"] = False
            result["errors"].append("old_string and new_string are identical")

        # Add preview
        if result["valid"]:
            preview_start = max(0, content.find(old_string) - 50)
            preview_end = min(len(content), content.find(old_string) + len(old_string) + 50)
            result["info"]["preview"] = content[preview_start:preview_end]

        return result

    def batch_edit(
        self,
        operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Perform batch edit operations across multiple files.

        Args:
            operations: List of edit operations with file_path and changes

        Returns:
            List of results for each operation
        """
        results = []

        for op in operations:
            file_path = op.get('file_path')
            changes = op.get('changes', op)

            try:
                result = self.smart_edit(file_path, changes)
                results.append({
                    "file": file_path,
                    "success": "Successfully" in result,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "file": file_path,
                    "success": False,
                    "error": str(e)
                })

        return results


# Global singleton instance
_unified_edit = None


def get_unified_edit() -> UnifiedEdit:
    """
    Get the global unified edit instance.

    Returns:
        UnifiedEdit: The global unified edit instance
    """
    global _unified_edit
    if _unified_edit is None:
        _unified_edit = UnifiedEdit()
    return _unified_edit


# Convenience function for direct editing
def edit_file(
    file_path: str,
    old_string: str = None,
    new_string: str = None,
    **kwargs
) -> str:
    """
    Convenience function for editing files.

    Args:
        file_path: File to edit
        old_string: String to replace
        new_string: Replacement string
        **kwargs: Additional arguments

    Returns:
        Edit result
    """
    editor = get_unified_edit()
    return editor.edit(
        file_path=file_path,
        old_string=old_string,
        new_string=new_string,
        **kwargs
    )