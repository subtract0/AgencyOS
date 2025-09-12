import os
from typing import Optional

from agency_swarm.tools import BaseTool
from pydantic import Field

# Import the global read files registry
from tools.read import _global_read_files


class Edit(BaseTool):
    """
    Performs exact string replacements in files.

    Usage:
    - You must use your `Read` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file.
    - When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.
    - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
    - Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
    - The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique or use `replace_all` to change every instance of `old_string`.
    - Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.
    """

    file_path: str = Field(..., description="The absolute path to the file to modify")
    old_string: str = Field(..., description="The text to replace")
    new_string: str = Field(
        ...,
        description="The text to replace it with (must be different from old_string)",
    )
    replace_all: Optional[bool] = Field(
        False, description="Replace all occurrences of old_string (default false)"
    )

    def run(self):
        try:
            # Check if the file has been read first (YAML precondition)
            abs_file_path = os.path.abspath(self.file_path)
            file_has_been_read = False

            # Check in shared state first
            if self.context is not None:
                read_files = self.context.get("read_files", set())
                file_has_been_read = abs_file_path in read_files

            # Check global fallback if not found in context
            if not file_has_been_read:
                file_has_been_read = abs_file_path in _global_read_files

            if not file_has_been_read:
                return "Error: You must use Read tool at least once before editing this file. This tool will error if you attempt an edit without reading the file first."

            # Validate that old_string and new_string are different
            if self.old_string == self.new_string:
                return "Error: old_string and new_string must be different"

            # Check if file exists
            if not os.path.exists(self.file_path):
                return f"Error: File does not exist: {self.file_path}"

            # Check if it's a file
            if not os.path.isfile(self.file_path):
                return f"Error: Path is not a file: {self.file_path}"

            # Read the file
            try:
                with open(self.file_path, "r", encoding="utf-8") as file:
                    content = file.read()
            except UnicodeDecodeError:
                return f"Error: Unable to decode file {self.file_path}. It may be a binary file."

            # Check if old_string exists in the file
            if self.old_string not in content:
                return f"Error: String to replace not found in file.\\nString: {repr(self.old_string)}"

            # Count occurrences
            occurrences = content.count(self.old_string)

            # If there are multiple occurrences and replace_all is False, require uniqueness
            if occurrences > 1 and not self.replace_all:
                # Build a preview of first two matches
                previews = []
                start_idx = 0
                for _ in range(2):
                    idx = content.find(self.old_string, start_idx)
                    if idx == -1:
                        break
                    a = max(0, idx - 30)
                    b = min(len(content), idx + len(self.old_string) + 30)
                    previews.append("..." + content[a:b] + "...")
                    start_idx = idx + len(self.old_string)
                preview_block = "\n".join(previews)
                return (
                    f"Error: String appears {occurrences} times in file. Either provide a larger string with more "
                    f"surrounding context to make it unique or use replace_all=True to change every instance.\n"
                    f"First matches:\n{preview_block}"
                )

            # Perform the replacement
            if self.replace_all:
                new_content = content.replace(self.old_string, self.new_string)
                replacement_count = occurrences
            else:
                # Replace only the first occurrence
                new_content = content.replace(self.old_string, self.new_string, 1)
                replacement_count = 1

            # Write the modified content back to the file
            try:
                with open(self.file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)

                # Create a short diff-like preview snippet (first and last replacement context)
                preview_lines = []
                old_preview_indices = []
                start_idx = 0
                while True:
                    idx = content.find(self.old_string, start_idx)
                    if idx == -1:
                        break
                    old_preview_indices.append(idx)
                    start_idx = idx + len(self.old_string)
                    if not self.replace_all and len(old_preview_indices) >= 1:
                        break

                def make_context(src: str, idx: int, needle: str, repl: str) -> str:
                    a = max(0, idx - 30)
                    b = min(len(src), idx + len(needle) + 30)
                    before = src[a:idx]
                    after = src[idx + len(needle) : b]
                    return f"...{before}[{needle}->{repl}]{after}..."

                if old_preview_indices:
                    first_idx = old_preview_indices[0]
                    preview_lines.append(
                        make_context(
                            content, first_idx, self.old_string, self.new_string
                        )
                    )
                    if self.replace_all and len(old_preview_indices) > 1:
                        last_idx = old_preview_indices[-1]
                        if last_idx != first_idx:
                            preview_lines.append(
                                make_context(
                                    content, last_idx, self.old_string, self.new_string
                                )
                            )

                preview = "\n".join(preview_lines) if preview_lines else ""

                msg = f"Successfully replaced {replacement_count} occurrence(s) in {self.file_path}"
                if preview:
                    msg += f"\nPreview:\n{preview}"
                return msg

            except PermissionError:
                return f"Error: Permission denied writing to file: {self.file_path}"
            except Exception as e:
                return f"Error writing to file: {str(e)}"

        except Exception as e:
            return f"Error during edit operation: {str(e)}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
edit = Edit

if __name__ == "__main__":
    # Test the tool - create a test file first
    test_file_path = "/tmp/test_edit.txt"
    test_content = """This is a test file.
Line 2 has some text.
Line 3 has the same text.
Final line."""

    # Create test file
    with open(test_file_path, "w") as f:
        f.write(test_content)

    print("Original content:")
    print(test_content)
    print("\\n" + "=" * 50 + "\\n")

    # Test single replacement
    tool = Edit(
        file_path=test_file_path, old_string="some text", new_string="REPLACED TEXT"
    )
    result = tool.run()
    print("Single replacement result:")
    print(result)

    # Read and show the modified content
    with open(test_file_path, "r") as f:
        modified_content = f.read()
    print("\\nModified content:")
    print(modified_content)

    # Test replace_all
    tool2 = Edit(
        file_path=test_file_path,
        old_string="text",
        new_string="content",
        replace_all=True,
    )
    result2 = tool2.run()
    print("\\n" + "=" * 50 + "\\n")
    print("Replace all result:")
    print(result2)

    # Read and show final content
    with open(test_file_path, "r") as f:
        final_content = f.read()
    print("\\nFinal content:")
    print(final_content)

    # Cleanup
    os.remove(test_file_path)
