import os
from typing import List, Optional

from agency_swarm.tools import BaseTool
from pydantic import BaseModel, Field

# Import the global read files registry
from tools.read import _global_read_files


class EditOperation(BaseModel):
    old_string: str = Field(..., description="The text to replace")
    new_string: str = Field(..., description="The text to replace it with")
    replace_all: Optional[bool] = Field(
        False, description="Replace all occurrences of old_string (default false)."
    )


class MultiEdit(BaseTool):
    """
    This is a tool for making multiple edits to a single file in one operation. It is built on top of the Edit tool and allows you to perform multiple find-and-replace operations efficiently. Prefer this tool over the Edit tool when you need to make multiple edits to the same file.

    Before using this tool:
    1. Use the Read tool to understand the file's contents and context
    2. Verify the directory path is correct

    To make multiple file edits, provide the following:
    1. file_path: The absolute path to the file to modify (must be absolute, not relative)
    2. edits: An array of edit operations to perform, where each edit contains:
       - old_string: The text to replace (must match the file contents exactly, including all whitespace and indentation)
       - new_string: The edited text to replace the old_string
       - replace_all: Replace all occurrences of old_string. This parameter is optional and defaults to false.

    IMPORTANT:
    - All edits are applied in sequence, in the order they are provided
    - Each edit operates on the result of the previous edit
    - All edits must be valid for the operation to succeed - if any edit fails, none will be applied
    - This tool is ideal when you need to make several changes to different parts of the same file
    - For Jupyter notebooks (.ipynb files), use the NotebookEdit instead

    CRITICAL REQUIREMENTS:
    1. All edits follow the same requirements as the single Edit tool
    2. The edits are atomic - either all succeed or none are applied
    3. Plan your edits carefully to avoid conflicts between sequential operations

    WARNING:
    - The tool will fail if edits.old_string doesn't match the file contents exactly (including whitespace)
    - The tool will fail if edits.old_string and edits.new_string are the same
    - Since edits are applied in sequence, ensure that earlier edits don't affect the text that later edits are trying to find

    When making edits:
    - Ensure all edits result in idiomatic, correct code
    - Do not leave the code in a broken state
    - Always use absolute file paths (starting with /)
    - Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
    - Use replace_all for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.

    If you want to create a new file, use:
    - A new file path, including dir name if needed
    - First edit: empty old_string and the new file's contents as new_string
    - Subsequent edits: normal edit operations on the created content
    """

    file_path: str = Field(..., description="The absolute path to the file to modify")
    edits: List[EditOperation] = Field(
        ...,
        min_length=1,
        description="Array of edit operations to perform sequentially on the file",
    )

    def run(self):
        try:
            # Check if this is a new file creation (first edit has empty old_string)
            creating_new_file = len(self.edits) > 0 and self.edits[0].old_string == ""

            # For existing files, validate existence and file type first
            if creating_new_file:
                # Prepare for new file creation (but don't write yet - ensure atomicity)
                if os.path.exists(self.file_path):
                    return f"Error: File already exists, cannot create new file: {self.file_path}"

                # Check directory exists or can be created
                directory = os.path.dirname(self.file_path)
                if directory and not os.path.exists(directory):
                    try:
                        os.makedirs(directory, exist_ok=True)
                    except Exception as e:
                        return f"Error creating directory {directory}: {str(e)}"

                # Start with initial content from first edit (in memory only)
                content = self.edits[0].new_string
                remaining_edits = self.edits[
                    1:
                ]  # Skip first edit since it's file creation
            else:
                # Working with existing file
                if not os.path.exists(self.file_path):
                    return f"Error: File does not exist: {self.file_path}"

                if not os.path.isfile(self.file_path):
                    return f"Error: Path is not a file: {self.file_path}"

                # Enforce prior Read for all existing files
                abs_file_path = os.path.abspath(self.file_path)
                file_has_been_read = False
                if self.context is not None:
                    read_files = self.context.get("read_files", set())
                    file_has_been_read = abs_file_path in read_files
                if not file_has_been_read:
                    file_has_been_read = abs_file_path in _global_read_files
                if not file_has_been_read:
                    return "Error: You must use Read tool at least once before editing this file. This tool will error if you attempt an edit without reading the file first."

                # Read the existing file
                try:
                    with open(self.file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                except UnicodeDecodeError:
                    return f"Error: Unable to decode file {self.file_path}. It may be a binary file."

                remaining_edits = self.edits

            # Validate all edits before applying any
            for i, edit in enumerate(remaining_edits):
                # Check that old_string and new_string are different
                if edit.old_string == edit.new_string:
                    return f"Error in edit {i + 1}: old_string and new_string must be different"

                # Check if old_string exists in current content
                if edit.old_string not in content:
                    return f"Error in edit {i + 1}: String to replace not found in file.\\nString: {repr(edit.old_string)}"

                # If not replace_all, check for uniqueness
                if not edit.replace_all and content.count(edit.old_string) > 1:
                    count = content.count(edit.old_string)
                    return f"Error in edit {i + 1}: String appears {count} times in file. Either provide a larger string with more surrounding context to make it unique or use replace_all=True."

            # Apply all edits sequentially
            edit_count = 0
            for i, edit in enumerate(remaining_edits):
                if edit.replace_all:
                    occurrences = content.count(edit.old_string)
                    content = content.replace(edit.old_string, edit.new_string)
                    edit_count += occurrences
                else:
                    content = content.replace(edit.old_string, edit.new_string, 1)
                    edit_count += 1

            # Write the final content to the file
            try:
                with open(self.file_path, "w", encoding="utf-8") as file:
                    file.write(content)

                if creating_new_file:
                    total_operations = len(self.edits)
                    return f"Successfully created new file {self.file_path} and applied {total_operations} edit operations ({edit_count} total replacements)"
                else:
                    total_operations = len(self.edits)
                    return f"Successfully applied {total_operations} edit operations ({edit_count} total replacements) to {self.file_path}"

            except PermissionError:
                return f"Error: Permission denied writing to file: {self.file_path}"
            except Exception as e:
                return f"Error writing to file: {str(e)}"

        except Exception as e:
            return f"Error during multi-edit operation: {str(e)}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
multi_edit = MultiEdit

if __name__ == "__main__":
    # Test the tool - create a test file first
    test_file_path = "/tmp/test_multi_edit.py"
    test_content = '''def old_function_name(param1, param2):
    """This is an old function."""
    result = param1 + param2
    print("Old message")
    return result

def another_function():
    """Another function."""
    old_value = 42
    return old_value
'''

    # Create test file
    with open(test_file_path, "w") as f:
        f.write(test_content)

    print("Original content:")
    print(test_content)
    print("\\n" + "=" * 70 + "\\n")

    # Test multiple edits
    edits = [
        EditOperation(old_string="old_function_name", new_string="new_function_name"),
        EditOperation(old_string="Old message", new_string="New message"),
        EditOperation(old_string="old_value", new_string="new_value", replace_all=True),
    ]

    tool = MultiEdit(file_path=test_file_path, edits=edits)
    result = tool.run()
    print("Multi-edit result:")
    print(result)

    # Read and show the modified content
    with open(test_file_path, "r") as f:
        modified_content = f.read()
    print("\\nModified content:")
    print(modified_content)

    # Test creating a new file
    new_file_path = "/tmp/test_new_file.txt"
    new_file_edits = [
        EditOperation(
            old_string="", new_string="# New File\\nThis is a new file.\\nLine 2."
        ),
        EditOperation(old_string="Line 2", new_string="Modified Line 2"),
    ]

    tool2 = MultiEdit(file_path=new_file_path, edits=new_file_edits)
    result2 = tool2.run()
    print("\\n" + "=" * 70 + "\\n")
    print("New file creation result:")
    print(result2)

    # Read and show the new file content
    with open(new_file_path, "r") as f:
        new_content = f.read()
    print("\\nNew file content:")
    print(new_content)

    # Cleanup
    os.remove(test_file_path)
    os.remove(new_file_path)
