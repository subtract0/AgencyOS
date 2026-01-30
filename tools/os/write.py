import os

from shared.lean_adapter import BaseTool
from pydantic import Field

# Import the global read files registry
from tools.read import _global_read_files

# Global registry for tracking written files when context is not available
_global_written_files = set()


class Write(BaseTool):  # type: ignore[misc]
    """
    Writes a file to the local filesystem.

    Usage:
    - This tool will overwrite the existing file if there is one at the provided path.
    - If this is an existing file, you MUST use the Read tool first to read the file's contents. This tool will fail if you did not read the file first.
    - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
    - NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
    - Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked.
    """

    file_path: str = Field(
        ...,
        description="Absolute or relative path to the file to write.",
    )
    content: str = Field(..., description="The content to write to the file")

    def run(self):
        try:
            # Enforce absolute path usage
            if not os.path.isabs(self.file_path):
                return f"Error: File path must be absolute: {self.file_path}"

            # Check if file already exists
            file_exists = os.path.exists(self.file_path)

            if file_exists:
                # For existing files, check if the file has been read first (YAML precondition)
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
                    return "Error: You must use Read tool at least once before overwriting this existing file. This tool will fail if you did not read the file first."

                # Verify it's a file and not a directory
                if not os.path.isfile(self.file_path):
                    return f"Error: Path exists but is not a file: {self.file_path}"

                operation = "overwritten"
            else:
                # Create directory if it doesn't exist
                directory = os.path.dirname(self.file_path)
                if directory and not os.path.exists(directory):
                    try:
                        os.makedirs(directory, exist_ok=True)
                    except Exception as e:
                        return f"Error creating directory {directory}: {str(e)}"
                operation = "created"

            # Atomic Write Pattern
            # 1. Write to a temporary file in the same directory (to ensure same filesystem)
            # 2. fsync to ensure data is on disk
            # 3. Rename temporary file to target file (atomic operation)
            
            import tempfile
            
            dir_name = os.path.dirname(self.file_path)
            prefix = os.path.basename(self.file_path) + "."
            
            try:
                # Create temp file in same directory
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=dir_name, prefix=prefix, delete=False) as temp_file:
                    temp_file.write(self.content)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                    temp_path = temp_file.name
                
                # Atomic rename
                os.replace(temp_path, self.file_path)
                
                # Get file stats
                file_size = os.path.getsize(self.file_path)
                line_count = self.content.count("\n") + (
                    1 if self.content and not self.content.endswith("\n") else 0
                )
                
                # Track and return success
                abs_path = os.path.abspath(self.file_path)
                if self.context is not None:
                    written_files = self.context.get("read_files", set())
                    written_files.add(abs_path)
                    self.context.set("read_files", written_files)
                
                _global_written_files.add(abs_path)
                
                return f"Successfully {operation} file: {self.file_path}\nSize: {file_size} bytes, Lines: {line_count}"
                
            except Exception as e:
                # Cleanup temp file if it exists
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                return f"Error writing file safely: {str(e)}"

        except Exception as e:
            return f"Error during write operation: {str(e)}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
write = Write

if __name__ == "__main__":
    # Test the tool
    test_file_path = "/tmp/test_write.py"
    test_content = '''#!/usr/bin/env python3
"""
Test Python file created by Write tool.
"""

def hello_world():
    """Print a greeting message."""
    print("Hello, World!")
    return True

def main():
    """Main function."""
    result = hello_world()
    if result:
        print("Success!")
    return 0

if __name__ == "__main__":
    exit(main())
'''

    # Test writing a new file
    tool = Write(file_path=test_file_path, content=test_content)
    result = tool.run()
    print("Write result:")
    print(result)

    # Verify the file was created
    if os.path.exists(test_file_path):
        print("\\nFile created successfully!")
        with open(test_file_path) as f:
            created_content = f.read()
        print("First few lines of created file:")
        print("\\n".join(created_content.split("\\n")[:10]))

    # Test overwriting the file
    new_content = "# This file has been overwritten\\nprint('New content')"
    tool2 = Write(file_path=test_file_path, content=new_content)
    result2 = tool2.run()
    print("\\n" + "=" * 50 + "\\n")
    print("Overwrite result:")
    print(result2)

    # Verify the file was overwritten
    with open(test_file_path) as f:
        overwritten_content = f.read()
    print("\\nOverwritten content:")
    print(overwritten_content)

    # Cleanup
    os.remove(test_file_path)
    print("\\nTest file cleaned up.")
