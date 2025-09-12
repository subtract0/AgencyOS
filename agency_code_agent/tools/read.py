import mimetypes
import os
from typing import Optional

from agency_swarm.tools import BaseTool
from pydantic import Field

# Global registry for tracking read files when context is not available
_global_read_files = set()


class Read(BaseTool):
    """
    Reads a file from the local filesystem. You can access any file directly by using this tool.
    Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.

    Usage:
    - The file_path parameter must be an absolute path, not a relative path
    - By default, it reads up to 2000 lines starting from the beginning of the file
    - You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters
    - Any lines longer than 2000 characters will be truncated
    - Results are returned using cat -n format, with line numbers starting at 1
    - This tool allows you to read images (eg PNG, JPG, etc). When reading an image file the contents are presented visually as you are a multimodal LLM.
    - For Jupyter notebooks (.ipynb files), use the NotebookRead instead
    - You will regularly be asked to read screenshots. If the user provides a path to a screenshot ALWAYS use this tool to view the file at the path. This tool will work with all temporary file paths like /var/folders/123/abc/T/TemporaryItems/NSIRD_screencaptureui_ZfB1tD/Screenshot.png
    - If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents.
    """

    file_path: str = Field(..., description="The absolute path to the file to read")
    offset: Optional[int] = Field(
        None,
        description="The line number to start reading from. Only provide if the file is too large to read at once",
    )
    limit: Optional[int] = Field(
        None,
        description="The number of lines to read. Only provide if the file is too large to read at once.",
    )

    def run(self):
        try:
            # Track that this file has been read in shared state (or global fallback)
            abs_path = os.path.abspath(self.file_path)
            if self.context is not None:
                read_files = self.context.get("read_files", set())
                read_files.add(abs_path)
                self.context.set("read_files", read_files)
            # Always mirror into global registry to ensure persistence across tool instances in tests
            global _global_read_files
            _global_read_files.add(abs_path)

            # Check if path exists
            if not os.path.exists(self.file_path):
                return f"Error: File does not exist: {self.file_path}"

            # Check if it's a file
            if not os.path.isfile(self.file_path):
                return f"Error: Path is not a file: {self.file_path}"

            # Check if it's an image file (basic check)
            mime_type, _ = mimetypes.guess_type(self.file_path)
            if mime_type and mime_type.startswith("image/"):
                return f"[IMAGE FILE: {self.file_path}]\nThis is an image file ({mime_type}). In a multimodal environment, the image content would be displayed visually."

            # Check if it's a Jupyter notebook
            if self.file_path.endswith(".ipynb"):
                return f"Error: This is a Jupyter notebook file. Please use the NotebookRead tool instead."

            # Try to read the file
            try:
                with open(self.file_path, "r", encoding="utf-8") as file:
                    lines = file.readlines()
            except UnicodeDecodeError:
                # Try with different encodings
                try:
                    with open(self.file_path, "r", encoding="latin-1") as file:
                        lines = file.readlines()
                except UnicodeDecodeError:
                    return f"Error: Unable to decode file {self.file_path}. It may be a binary file."

            # Handle empty file
            if not lines:
                return f"Warning: File exists but has empty contents: {self.file_path}"

            # Apply offset and limit
            start_line = (
                (self.offset - 1) if self.offset else 0
            )  # Convert to 0-based index
            start_line = max(0, start_line)  # Ensure non-negative

            if self.limit:
                end_line = start_line + self.limit
                selected_lines = lines[start_line:end_line]
            else:
                # Default limit of 2000 lines
                selected_lines = lines[start_line : start_line + 2000]

            # Format output with line numbers (cat -n style)
            result_lines = []
            for i, line in enumerate(selected_lines, start=start_line + 1):
                # Truncate lines longer than 2000 characters
                if len(line) > 2000:
                    line = line[:1997] + "...\n"
                # cat -n style: right-aligned 6-width line number, tab, then content
                result_lines.append(f"{i:>6}\t{line.rstrip()}\n")
            result = "".join(result_lines)

            # Add metadata about truncation
            total_lines = len(lines)
            lines_shown = len(selected_lines)

            if lines_shown < total_lines:
                if self.offset or self.limit:
                    result += f"\n[Truncated: showing lines {start_line + 1}-{start_line + lines_shown} of {total_lines} total lines]"
                else:
                    result += f"\n[Truncated: showing first {lines_shown} of {total_lines} total lines]"

            return result.rstrip()

        except PermissionError:
            return f"Error: Permission denied reading file: {self.file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
read = Read

if __name__ == "__main__":
    # Test the tool
    # Test with current file
    current_file = __file__

    tool = Read(file_path=current_file, limit=10)
    print("Reading first 10 lines:")
    print(tool.run())

    # Test with offset
    tool2 = Read(file_path=current_file, offset=20, limit=5)
    print("\n" + "=" * 50 + "\n")
    print("Reading 5 lines starting from line 20:")
    print(tool2.run())
