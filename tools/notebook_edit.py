import json
import os
from typing import Literal, Optional

from agency_swarm.tools import BaseTool
from pydantic import Field


class NotebookEdit(BaseTool):
    """
    Completely replaces the contents of a specific cell in a Jupyter notebook (.ipynb file) with new source.
    Jupyter notebooks are interactive documents that combine code, text, and visualizations, commonly used for data analysis and scientific computing.
    The notebook_path parameter must be an absolute path, not a relative path.

    Targeting cells:
    - Use cell_id to specify the target cell. It may be either an explicit cell "id" value from the notebook, or a numeric string representing the 0-indexed cell position (e.g., "0", "1", ...).

    Edit modes:
    - edit_mode=replace (default): replaces the content of the targeted cell. If cell_type is provided, the cell's type will also be updated.
    - edit_mode=insert: inserts a new cell AFTER the cell specified by cell_id; if cell_id is not provided, inserts at the beginning. cell_type is required when inserting.
    - edit_mode=delete: deletes the targeted cell.
    """

    notebook_path: str = Field(
        ...,
        description="The absolute path to the Jupyter notebook file to edit (must be absolute, not relative)",
    )
    cell_id: Optional[str] = Field(
        None,
        description="The ID of the cell to edit. When inserting a new cell, the new cell will be inserted after the cell with this ID, or at the beginning if not specified.",
    )
    new_source: str = Field(..., description="The new source for the cell")
    cell_type: Optional[Literal["code", "markdown"]] = Field(
        None,
        description="The type of the cell (code or markdown). If not specified, it defaults to the current cell type. If using edit_mode=insert, this is required.",
    )
    edit_mode: Optional[Literal["replace", "insert", "delete"]] = Field(
        "replace",
        description="The type of edit to make (replace, insert, delete). Defaults to replace.",
    )

    def run(self):
        try:
            # Validate that the path is absolute
            if not os.path.isabs(self.notebook_path):
                return f"Error: Notebook path must be absolute, not relative: {self.notebook_path}"

            # Check if file exists
            if not os.path.exists(self.notebook_path):
                return f"Error: Notebook file does not exist: {self.notebook_path}"

            # Check if it's a file
            if not os.path.isfile(self.notebook_path):
                return f"Error: Path is not a file: {self.notebook_path}"

            # Check if it's a .ipynb file
            if not self.notebook_path.endswith(".ipynb"):
                return f"Error: File is not a Jupyter notebook (.ipynb): {self.notebook_path}"

            # Read and parse the notebook
            try:
                with open(self.notebook_path, "r", encoding="utf-8") as f:
                    notebook_data = json.load(f)
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON in notebook file: {str(e)}"
            except Exception as e:
                return f"Error reading notebook file: {str(e)}"

            # Validate notebook structure
            if "cells" not in notebook_data:
                return f"Error: Invalid notebook format - no 'cells' key found"

            cells = notebook_data["cells"]
            if not isinstance(cells, list):
                return f"Error: Invalid notebook format - 'cells' is not a list"

            # Handle different edit modes
            if self.edit_mode == "insert":
                return self._insert_cell(notebook_data, cells)
            elif self.edit_mode == "delete":
                return self._delete_cell(notebook_data, cells)
            else:  # replace mode
                return self._replace_cell(notebook_data, cells)

        except Exception as e:
            return f"Error editing notebook: {str(e)}"

    def _find_cell_index(self, cells):
        """Find the index of the cell to edit."""
        if self.cell_id is None:
            return 0  # Default to first cell

        for i, cell in enumerate(cells):
            # Check both 'id' field and index-based matching
            if "id" in cell and cell["id"] == self.cell_id:
                return i
            elif self.cell_id.isdigit() and i == int(self.cell_id):
                return i

        return None  # Cell not found

    def _insert_cell(self, notebook_data, cells):
        """Insert a new cell."""
        # cell_type is required for insert mode
        if self.cell_type is None:
            return "Error: cell_type is required when using edit_mode=insert"

        # Find insertion point
        if self.cell_id is None:
            insert_index = 0  # Insert at beginning
        else:
            cell_index = self._find_cell_index(cells)
            if cell_index is None:
                return f"Error: Cell with ID '{self.cell_id}' not found in notebook"
            insert_index = cell_index + 1  # Insert after the found cell

        # Create new cell
        new_cell = {
            "cell_type": self.cell_type,
            "source": self._format_source(self.new_source),
        }

        # Add cell-type specific fields
        if self.cell_type == "code":
            new_cell["execution_count"] = None
            new_cell["outputs"] = []

        # Generate a unique ID for the new cell
        existing_ids = {cell.get("id", f"cell-{i}") for i, cell in enumerate(cells)}
        new_id = f"new-cell-{len(cells)}"
        counter = 0
        while new_id in existing_ids:
            counter += 1
            new_id = f"new-cell-{len(cells)}-{counter}"
        new_cell["id"] = new_id

        # Insert the cell
        cells.insert(insert_index, new_cell)

        # Save the notebook
        self._save_notebook(notebook_data)

        return f"Successfully inserted new {self.cell_type} cell (ID: {new_id}) at position {insert_index} in {self.notebook_path}"

    def _delete_cell(self, notebook_data, cells):
        """Delete a cell."""
        if len(cells) == 0:
            return "Error: Cannot delete cell from empty notebook"

        cell_index = self._find_cell_index(cells)
        if cell_index is None:
            return f"Error: Cell with ID '{self.cell_id}' not found in notebook"

        if cell_index >= len(cells):
            return f"Error: Cell index {cell_index} is out of range (notebook has {len(cells)} cells)"

        # Get cell info before deletion
        deleted_cell = cells[cell_index]
        cell_type = deleted_cell.get("cell_type", "unknown")
        cell_id = deleted_cell.get("id", f"cell-{cell_index}")

        # Delete the cell
        cells.pop(cell_index)

        # Save the notebook
        self._save_notebook(notebook_data)

        return f"Successfully deleted {cell_type} cell (ID: {cell_id}) at position {cell_index} from {self.notebook_path}. Notebook now has {len(cells)} cells."

    def _replace_cell(self, notebook_data, cells):
        """Replace the content of an existing cell."""
        if len(cells) == 0:
            return "Error: Cannot replace cell in empty notebook"

        cell_index = self._find_cell_index(cells)
        if cell_index is None:
            return f"Error: Cell with ID '{self.cell_id}' not found in notebook"

        if cell_index >= len(cells):
            return f"Error: Cell index {cell_index} is out of range (notebook has {len(cells)} cells)"

        # Get the cell to modify
        cell = cells[cell_index]
        old_cell_type = cell.get("cell_type", "code")

        # Update source
        cell["source"] = self._format_source(self.new_source)

        # Update cell type if specified
        if self.cell_type and self.cell_type != old_cell_type:
            cell["cell_type"] = self.cell_type

            # Add/remove type-specific fields
            if self.cell_type == "code" and old_cell_type != "code":
                cell["execution_count"] = None
                cell["outputs"] = []
            elif self.cell_type != "code" and old_cell_type == "code":
                # Remove code-specific fields
                cell.pop("execution_count", None)
                cell.pop("outputs", None)

        # Clear execution count and outputs for code cells when source changes
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            cell["outputs"] = []

        # Save the notebook
        self._save_notebook(notebook_data)

        cell_id = cell.get("id", f"cell-{cell_index}")
        final_type = cell.get("cell_type", "unknown")

        return f"Successfully replaced content of {final_type} cell (ID: {cell_id}) at position {cell_index} in {self.notebook_path}"

    def _format_source(self, source_text):
        """Format source text as a list of strings (notebook format)."""
        if not source_text:
            return []

        # Split into lines and ensure each line ends with \\n
        lines = source_text.split("\\n")
        formatted_lines = []

        for i, line in enumerate(lines):
            if i == len(lines) - 1 and line == "":
                # Don't add an empty line at the very end
                continue
            formatted_lines.append(line + "\\n")

        # If the original text didn't end with a newline and we have content,
        # remove the newline from the last line
        if formatted_lines and not source_text.endswith("\\n"):
            formatted_lines[-1] = formatted_lines[-1].rstrip("\\n")

        return formatted_lines

    def _save_notebook(self, notebook_data):
        """Save the notebook data to file."""
        with open(self.notebook_path, "w", encoding="utf-8") as f:
            json.dump(notebook_data, f, indent=2, ensure_ascii=False)


# Create alias for Agency Swarm tool loading (expects class name = file name)
notebook_edit = NotebookEdit

if __name__ == "__main__":
    # Create a test notebook for testing
    test_notebook_path = "/tmp/test_notebook_edit.ipynb"
    test_notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "intro",
                "source": ["# Original Notebook\\n", "This is a test notebook."],
            },
            {
                "cell_type": "code",
                "id": "code1",
                "execution_count": 1,
                "source": ["# Original code\\n", "x = 1\\n", "print(x)"],
                "outputs": [],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }

    # Write test notebook
    with open(test_notebook_path, "w") as f:
        json.dump(test_notebook, f, indent=2)

    print("Original notebook created.")

    # Test replacing a cell
    tool1 = NotebookEdit(
        notebook_path=test_notebook_path,
        cell_id="code1",
        new_source="# Modified code\\ny = 2 + 3\\nprint(f'Result: {y}')",
        edit_mode="replace",
    )
    result1 = tool1.run()
    print("Replace result:")
    print(result1)

    # Test inserting a new cell
    tool2 = NotebookEdit(
        notebook_path=test_notebook_path,
        cell_id="intro",
        new_source="This is a new markdown cell inserted after the intro.",
        cell_type="markdown",
        edit_mode="insert",
    )
    result2 = tool2.run()
    print("\\nInsert result:")
    print(result2)

    # Test deleting a cell
    tool3 = NotebookEdit(
        notebook_path=test_notebook_path,
        cell_id="code1",
        new_source="",  # Not used in delete mode
        edit_mode="delete",
    )
    result3 = tool3.run()
    print("\\nDelete result:")
    print(result3)

    # Verify final notebook
    with open(test_notebook_path, "r") as f:
        final_notebook = json.load(f)

    print(f"\\nFinal notebook has {len(final_notebook['cells'])} cells:")
    for i, cell in enumerate(final_notebook["cells"]):
        cell_type = cell.get("cell_type", "unknown")
        cell_id = cell.get("id", f"cell-{i}")
        source_preview = "".join(cell.get("source", []))[:50].replace("\\n", " ")
        print(f"  Cell {i}: {cell_type} (ID: {cell_id}) - {source_preview}...")

    # Cleanup
    os.remove(test_notebook_path)
    print("\\nTest notebook cleaned up.")
