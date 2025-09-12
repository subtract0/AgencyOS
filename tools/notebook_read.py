import json
import os
from typing import Optional

from agency_swarm.tools import BaseTool
from pydantic import Field


class NotebookRead(BaseTool):
    """
    Reads a Jupyter notebook (.ipynb file) and returns all of the cells with their outputs.
    Jupyter notebooks are interactive documents that combine code, text, and visualizations, commonly used for data analysis and scientific computing.
    The notebook_path parameter must be an absolute path, not a relative path.
    """

    notebook_path: str = Field(
        ...,
        description="The absolute path to the Jupyter notebook file to read (must be absolute, not relative)",
    )
    cell_id: Optional[str] = Field(
        None,
        description="The ID of a specific cell to read. If not provided, all cells will be read.",
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

            # If specific cell_id requested, find and return that cell
            if self.cell_id:
                for i, cell in enumerate(cells):
                    # Check both 'id' field and index-based matching
                    cell_matches = False
                    if "id" in cell and cell["id"] == self.cell_id:
                        cell_matches = True
                    elif self.cell_id.isdigit() and i == int(self.cell_id):
                        cell_matches = True

                    if cell_matches:
                        return self._format_single_cell(cell, i)

                return f"Error: Cell with ID '{self.cell_id}' not found in notebook"

            # Return all cells
            result = f"Jupyter Notebook: {self.notebook_path}\\n"
            result += f"Total cells: {len(cells)}\\n\\n"

            for i, cell in enumerate(cells):
                result += self._format_single_cell(cell, i) + "\\n\\n"

            return result.strip()

        except Exception as e:
            return f"Error reading notebook: {str(e)}"

    def _format_single_cell(self, cell, index):
        """Format a single cell for display."""
        cell_type = cell.get("cell_type", "unknown")
        cell_id = cell.get("id", f"cell-{index}")

        result = f"=== Cell {index} (ID: {cell_id}, Type: {cell_type}) ==="

        # Add source code
        source = cell.get("source", [])
        if isinstance(source, list):
            source_text = "".join(source)
        else:
            source_text = str(source)

        if source_text.strip():
            result += f"\\nSource:\\n{source_text}"
        else:
            result += "\\nSource: [empty]"

        # Add outputs for code cells
        if cell_type == "code" and "outputs" in cell:
            outputs = cell["outputs"]
            if outputs:
                result += "\\n\\nOutputs:"
                for i, output in enumerate(outputs):
                    result += f"\\n  Output {i + 1}:"

                    output_type = output.get("output_type", "unknown")
                    result += f" (Type: {output_type})"

                    # Handle different output types
                    if output_type == "stream":
                        text = output.get("text", [])
                        if isinstance(text, list):
                            text = "".join(text)
                        result += f"\\n    {text.strip()}"

                    elif output_type in ["execute_result", "display_data"]:
                        data = output.get("data", {})
                        if "text/plain" in data:
                            plain_text = data["text/plain"]
                            if isinstance(plain_text, list):
                                plain_text = "".join(plain_text)
                            result += f"\\n    {plain_text.strip()}"

                        # Note other data types
                        other_types = [k for k in data.keys() if k != "text/plain"]
                        if other_types:
                            result += (
                                f"\\n    [Also contains: {', '.join(other_types)}]"
                            )

                    elif output_type == "error":
                        ename = output.get("ename", "Error")
                        evalue = output.get("evalue", "")
                        result += f"\\n    {ename}: {evalue}"
            else:
                result += "\\n\\nOutputs: [none]"

        # Add execution count for code cells
        if cell_type == "code" and "execution_count" in cell:
            exec_count = cell["execution_count"]
            result += f"\\n\\nExecution Count: {exec_count}"

        return result


# Create alias for Agency Swarm tool loading (expects class name = file name)
notebook_read = NotebookRead

if __name__ == "__main__":
    # Create a test notebook for testing
    test_notebook_path = "/tmp/test_notebook.ipynb"
    test_notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "intro",
                "source": [
                    "# Test Notebook\\n",
                    "This is a test notebook for the NotebookRead tool.",
                ],
            },
            {
                "cell_type": "code",
                "id": "code1",
                "execution_count": 1,
                "source": [
                    "# Simple calculation\\n",
                    "x = 2 + 3\\n",
                    "print(f'Result: {x}')",
                ],
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": ["Result: 5\\n"],
                    }
                ],
            },
            {
                "cell_type": "code",
                "id": "code2",
                "execution_count": 2,
                "source": ["# Another calculation\\n", "y = x * 2\\n", "y"],
                "outputs": [
                    {
                        "output_type": "execute_result",
                        "execution_count": 2,
                        "data": {"text/plain": ["10"]},
                    }
                ],
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

    # Test reading all cells
    tool = NotebookRead(notebook_path=test_notebook_path)
    result = tool.run()
    print("Reading all cells:")
    print(result)

    # Test reading specific cell
    tool2 = NotebookRead(notebook_path=test_notebook_path, cell_id="code1")
    result2 = tool2.run()
    print("\\n" + "=" * 70 + "\\n")
    print("Reading specific cell:")
    print(result2)

    # Cleanup
    os.remove(test_notebook_path)
    print("\\nTest notebook cleaned up.")
