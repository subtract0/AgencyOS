import json
from pathlib import Path

from tools import NotebookEdit


def create_sample_notebook(file_path: str, cells_data: list = None):
    """Helper function to create a sample Jupyter notebook"""
    if cells_data is None:
        cells_data = [
            {
                "cell_type": "markdown",
                "id": "cell-1",
                "metadata": {},
                "source": ["# Original Title\n", "Original description."],
            },
            {
                "cell_type": "code",
                "id": "cell-2",
                "metadata": {},
                "execution_count": 1,
                "source": ["print('original code')\n", "x = 1"],
                "outputs": [],
            },
        ]

    notebook_content = {
        "cells": cells_data,
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

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(notebook_content, f, indent=2)


def test_notebook_edit_replace_cell(tmp_path: Path):
    """Test replacing cell content"""
    notebook_file = tmp_path / "test.ipynb"
    create_sample_notebook(str(notebook_file))

    # Replace the first cell (markdown)
    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="cell-1",
        new_source="# Updated Title\nUpdated description with more content.",
        edit_mode="replace",
    )
    result = tool.run()

    assert (
        "Successfully replaced cell" in result
        or "Successfully replaced content" in result
    )
    assert "cell-1" in result

    # Verify the change
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    updated_cell = updated_notebook["cells"][0]
    source_content = "".join(updated_cell["source"])
    assert "# Updated Title" in source_content
    assert "Updated description with more content." in source_content


def test_notebook_edit_replace_code_cell(tmp_path: Path):
    """Test replacing code cell content"""
    notebook_file = tmp_path / "code_test.ipynb"
    create_sample_notebook(str(notebook_file))

    # Replace the second cell (code)
    new_code = """import pandas as pd
import numpy as np

data = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print(data.head())"""

    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="cell-2",
        new_source=new_code,
        edit_mode="replace",
    )
    result = tool.run()

    assert (
        "Successfully replaced cell" in result
        or "Successfully replaced content" in result
    )

    # Verify the change
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    updated_cell = updated_notebook["cells"][1]
    source_content = "".join(updated_cell["source"])
    assert "import pandas as pd" in source_content
    assert "pd.DataFrame" in source_content
    assert "print(data.head())" in source_content


def test_notebook_edit_insert_cell(tmp_path: Path):
    """Test inserting a new cell"""
    notebook_file = tmp_path / "insert_test.ipynb"
    create_sample_notebook(str(notebook_file))

    # Insert a new markdown cell after cell-1
    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="cell-1",
        new_source="## New Section\nThis is a newly inserted cell.",
        cell_type="markdown",
        edit_mode="insert",
    )
    result = tool.run()

    assert (
        "Successfully inserted new cell" in result
        or "Successfully inserted new" in result
    )

    # Verify the insertion
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    # Should now have 3 cells
    assert len(updated_notebook["cells"]) == 3

    # Check the inserted cell (should be at index 1)
    inserted_cell = updated_notebook["cells"][1]
    assert inserted_cell["cell_type"] == "markdown"
    assert "## New Section" in "".join(inserted_cell["source"])
    assert "newly inserted cell" in "".join(inserted_cell["source"])


def test_notebook_edit_insert_code_cell(tmp_path: Path):
    """Test inserting a new code cell"""
    notebook_file = tmp_path / "insert_code.ipynb"
    create_sample_notebook(str(notebook_file))

    # Insert a new code cell at the beginning
    new_code = """# Setup and imports
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('seaborn')"""

    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id=None,  # Insert at beginning
        new_source=new_code,
        cell_type="code",
        edit_mode="insert",
    )
    result = tool.run()

    assert (
        "Successfully inserted new cell" in result
        or "Successfully inserted new" in result
    )

    # Verify the insertion
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    # Should now have 3 cells
    assert len(updated_notebook["cells"]) == 3

    # Check the inserted cell (should be at index 0)
    inserted_cell = updated_notebook["cells"][0]
    assert inserted_cell["cell_type"] == "code"
    source_content = "".join(inserted_cell["source"])
    assert "import matplotlib.pyplot as plt" in source_content
    assert "plt.style.use('seaborn')" in source_content


def test_notebook_edit_delete_cell(tmp_path: Path):
    """Test deleting a cell"""
    notebook_file = tmp_path / "delete_test.ipynb"

    # Create notebook with 3 cells
    cells_data = [
        {
            "cell_type": "markdown",
            "id": "cell-1",
            "metadata": {},
            "source": ["# Title"],
        },
        {
            "cell_type": "code",
            "id": "cell-2",
            "metadata": {},
            "source": ["print('to be deleted')"],
            "outputs": [],
        },
        {"cell_type": "markdown", "id": "cell-3", "metadata": {}, "source": ["# End"]},
    ]
    create_sample_notebook(str(notebook_file), cells_data)

    # Delete the middle cell
    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="cell-2",
        new_source="",  # Not used for delete
        edit_mode="delete",
    )
    result = tool.run()

    assert "Successfully deleted cell" in result or "Successfully deleted" in result

    # Verify the deletion
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    # Should now have 2 cells
    assert len(updated_notebook["cells"]) == 2
    assert updated_notebook["cells"][0]["id"] == "cell-1"
    assert updated_notebook["cells"][1]["id"] == "cell-3"

    # Deleted cell should not be present
    for cell in updated_notebook["cells"]:
        assert "to be deleted" not in "".join(cell.get("source", []))


def test_notebook_edit_nonexistent_cell(tmp_path: Path):
    """Test error when trying to edit nonexistent cell"""
    notebook_file = tmp_path / "nonexistent.ipynb"
    create_sample_notebook(str(notebook_file))

    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="nonexistent-cell",
        new_source="New content",
        edit_mode="replace",
    )
    result = tool.run()

    assert "Error: Cell with ID 'nonexistent-cell' not found" in result


def test_notebook_edit_requires_absolute_path():
    """Test that NotebookEdit requires absolute paths"""
    tool = NotebookEdit(
        notebook_path="relative/path.ipynb", cell_id="cell-1", new_source="New content"
    )
    result = tool.run()

    assert "Error: Notebook path must be absolute" in result


def test_notebook_edit_nonexistent_file():
    """Test error when notebook file doesn't exist"""
    tool = NotebookEdit(
        notebook_path="/nonexistent/notebook.ipynb",
        cell_id="cell-1",
        new_source="New content",
    )
    result = tool.run()

    assert "Error: Notebook file does not exist" in result


def test_notebook_edit_wrong_extension(tmp_path: Path):
    """Test error when file is not .ipynb"""
    text_file = tmp_path / "not_notebook.txt"
    text_file.write_text("Not a notebook")

    tool = NotebookEdit(
        notebook_path=str(text_file), cell_id="cell-1", new_source="New content"
    )
    result = tool.run()

    assert "Error: File is not a Jupyter notebook (.ipynb)" in result


def test_notebook_edit_invalid_json(tmp_path: Path):
    """Test error with invalid JSON"""
    notebook_file = tmp_path / "invalid.ipynb"
    notebook_file.write_text("{ invalid json }")

    tool = NotebookEdit(
        notebook_path=str(notebook_file), cell_id="cell-1", new_source="New content"
    )
    result = tool.run()

    assert "Error: Invalid JSON in notebook file" in result


def test_notebook_edit_insert_requires_cell_type(tmp_path: Path):
    """Test that insert mode requires cell_type"""
    notebook_file = tmp_path / "insert_type.ipynb"
    create_sample_notebook(str(notebook_file))

    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="cell-1",
        new_source="New content",
        edit_mode="insert",
        # Missing cell_type
    )
    result = tool.run()

    # Should require cell_type for insert mode
    assert "cell_type is required for insert mode" in result or "Error" in result


def test_notebook_edit_numeric_cell_id(tmp_path: Path):
    """Test using numeric cell ID (0-based index)"""
    notebook_file = tmp_path / "numeric_id.ipynb"
    create_sample_notebook(str(notebook_file))

    # Edit cell at index 0 (first cell)
    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="0",
        new_source="# Updated via numeric ID\nContent updated using index.",
        edit_mode="replace",
    )
    result = tool.run()

    assert (
        "Successfully replaced cell" in result
        or "Successfully replaced content" in result
    )

    # Verify the change
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    updated_cell = updated_notebook["cells"][0]
    source_content = "".join(updated_cell["source"])
    assert "Updated via numeric ID" in source_content


def test_notebook_edit_complex_markdown(tmp_path: Path):
    """Test editing with complex markdown content"""
    notebook_file = tmp_path / "markdown_complex.ipynb"
    create_sample_notebook(str(notebook_file))

    complex_markdown = """# Data Science Project

## Overview
This project analyzes customer behavior patterns using machine learning.

### Methodology
1. **Data Collection**: Gather customer transaction data
2. **Data Cleaning**: Remove duplicates and handle missing values
3. **Feature Engineering**: Create meaningful features
4. **Model Training**: Train multiple ML models
5. **Evaluation**: Compare model performance

### Results
- Achieved 85% accuracy with Random Forest
- Key features: purchase_frequency, avg_order_value
- Customer segments identified: 3 distinct groups

## Code Examples
```python
import pandas as pd
df = pd.read_csv('customer_data.csv')
```

## Next Steps
- [ ] Deploy model to production
- [ ] A/B test recommendations
- [ ] Monitor model performance"""

    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="cell-1",
        new_source=complex_markdown,
        edit_mode="replace",
    )
    result = tool.run()

    assert (
        "Successfully replaced cell" in result
        or "Successfully replaced content" in result
    )

    # Verify complex markdown was preserved
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    updated_cell = updated_notebook["cells"][0]
    source_content = "".join(updated_cell["source"])
    assert "Data Science Project" in source_content
    assert "Achieved 85% accuracy" in source_content
    assert "```python" in source_content
    assert "- [ ] Deploy model" in source_content


def test_notebook_edit_preserve_metadata(tmp_path: Path):
    """Test that cell metadata is preserved during edits"""
    notebook_file = tmp_path / "metadata_test.ipynb"

    cells_with_metadata = [
        {
            "cell_type": "code",
            "id": "tagged-cell",
            "metadata": {
                "tags": ["important", "analysis"],
                "collapsed": False,
                "scrolled": True,
            },
            "source": ["# Original code"],
            "outputs": [],
        }
    ]
    create_sample_notebook(str(notebook_file), cells_with_metadata)

    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="tagged-cell",
        new_source="# Updated code\nprint('metadata should be preserved')",
        edit_mode="replace",
    )
    result = tool.run()

    assert (
        "Successfully replaced cell" in result
        or "Successfully replaced content" in result
    )

    # Verify metadata was preserved
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    updated_cell = updated_notebook["cells"][0]
    assert updated_cell["metadata"]["tags"] == ["important", "analysis"]
    assert updated_cell["metadata"]["collapsed"] == False
    assert updated_cell["metadata"]["scrolled"] == True

    # But source should be updated
    source_content = "".join(updated_cell["source"])
    assert "Updated code" in source_content
    assert "metadata should be preserved" in source_content


def test_notebook_edit_empty_notebook(tmp_path: Path):
    """Test editing operations on empty notebook"""
    notebook_file = tmp_path / "empty.ipynb"
    create_sample_notebook(str(notebook_file), [])  # Empty cells list

    # Try to insert cell in empty notebook
    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id=None,
        new_source="# First cell\nThis is the first cell in an empty notebook.",
        cell_type="markdown",
        edit_mode="insert",
    )
    result = tool.run()

    assert (
        "Successfully inserted new cell" in result
        or "Successfully inserted new" in result
    )

    # Verify the insertion
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    assert len(updated_notebook["cells"]) == 1
    first_cell = updated_notebook["cells"][0]
    assert first_cell["cell_type"] == "markdown"
    assert "First cell" in "".join(first_cell["source"])


def test_notebook_edit_multiline_code(tmp_path: Path):
    """Test editing with multiline code containing special characters"""
    notebook_file = tmp_path / "multiline.ipynb"
    create_sample_notebook(str(notebook_file))

    multiline_code = '''"""
Multi-line string with various characters:
- Special chars: @#$%^&*()
- Unicode: 🐍 Python 📊 Data
- Code snippets:
"""

import re
import json

def process_data(data):
    """Process the data with regex and JSON."""
    pattern = r'\\d{4}-\\d{2}-\\d{2}'  # Date pattern
    dates = re.findall(pattern, data)

    result = {
        "dates_found": len(dates),
        "first_date": dates[0] if dates else None,
        "processed": True
    }

    return json.dumps(result, indent=2)

# Test the function
sample_data = "Created on 2023-12-25, updated 2024-01-15"
print(process_data(sample_data))'''

    tool = NotebookEdit(
        notebook_path=str(notebook_file),
        cell_id="cell-2",
        new_source=multiline_code,
        edit_mode="replace",
    )
    result = tool.run()

    assert (
        "Successfully replaced cell" in result
        or "Successfully replaced content" in result
    )

    # Verify complex code was preserved
    with open(notebook_file, "r") as f:
        updated_notebook = json.load(f)

    updated_cell = updated_notebook["cells"][1]
    source_content = "".join(updated_cell["source"])
    assert "🐍 Python 📊 Data" in source_content
    assert "def process_data" in source_content
    # The regex pattern might be escaped differently - check for the core pattern
    assert (
        "d{4}-" in source_content
        and "d{2}-" in source_content
        and "d{2}" in source_content
    )
    assert "json.dumps(result, indent=2)" in source_content
