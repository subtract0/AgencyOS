import glob as glob_module
import os
from datetime import datetime
from typing import List, Optional

from agency_swarm.tools import BaseTool
from pydantic import Field


class LS(BaseTool):
    """
    Lists files and directories in a given path. The path parameter must be an absolute path, not a relative path.
    You can optionally provide an array of glob patterns to ignore with the ignore parameter.
    You should generally prefer the Glob and Grep tools, if you know which directories to search.
    """

    path: str = Field(
        ...,
        description="The absolute path to the directory to list (must be absolute, not relative)",
    )
    ignore: Optional[List[str]] = Field(
        None, description="List of glob patterns to ignore"
    )

    def run(self):
        try:
            # Validate path is absolute
            if not os.path.isabs(self.path):
                return f"Error: Path must be absolute, not relative: {self.path}"

            # Check if path exists
            if not os.path.exists(self.path):
                return f"Error: Path does not exist: {self.path}"

            # Check if it's a directory
            if not os.path.isdir(self.path):
                return f"Error: Path is not a directory: {self.path}"

            try:
                # Get directory contents
                items = os.listdir(self.path)
            except PermissionError:
                return f"Error: Permission denied accessing: {self.path}"

            # Apply ignore patterns if provided
            if self.ignore:
                filtered_items = []
                for item in items:
                    should_ignore = False
                    for pattern in self.ignore:
                        if glob_module.fnmatch.fnmatch(item, pattern):
                            should_ignore = True
                            break
                    if not should_ignore:
                        filtered_items.append(item)
                items = filtered_items

            if not items:
                return f"Directory is empty (or all items were filtered): {self.path}"

            # Sort items
            items.sort()

            # Get detailed information for each item
            detailed_items = []
            for item in items:
                full_path = os.path.join(self.path, item)
                try:
                    stat_info = os.stat(full_path)

                    # Determine type (check symlink first since os.stat follows links)
                    if os.path.islink(full_path):
                        item_type = "LINK"
                    elif os.path.isdir(full_path):
                        item_type = "DIR"
                    elif os.path.isfile(full_path):
                        item_type = "FILE"
                    else:
                        item_type = "OTHER"

                    # Get size (for files)
                    if item_type == "FILE":
                        size = stat_info.st_size
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f}KB"
                        else:
                            size_str = f"{size / (1024 * 1024):.1f}MB"
                    else:
                        size_str = "-"

                    # Get modification time
                    mod_time = datetime.fromtimestamp(stat_info.st_mtime)
                    mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M")

                    # Get permissions
                    mode = stat_info.st_mode
                    permissions = ""
                    permissions += "r" if mode & 0o400 else "-"
                    permissions += "w" if mode & 0o200 else "-"
                    permissions += "x" if mode & 0o100 else "-"
                    permissions += "r" if mode & 0o040 else "-"
                    permissions += "w" if mode & 0o020 else "-"
                    permissions += "x" if mode & 0o010 else "-"
                    permissions += "r" if mode & 0o004 else "-"
                    permissions += "w" if mode & 0o002 else "-"
                    permissions += "x" if mode & 0o001 else "-"

                    detailed_items.append(
                        {
                            "name": item,
                            "type": item_type,
                            "size": size_str,
                            "permissions": permissions,
                            "modified": mod_time_str,
                            "full_path": full_path,
                        }
                    )

                except (OSError, IOError) as e:
                    detailed_items.append(
                        {
                            "name": item,
                            "type": "ERROR",
                            "size": "-",
                            "permissions": "-",
                            "modified": "-",
                            "full_path": full_path,
                        }
                    )

            # Format output
            result = f"Contents of {self.path}:\\n\\n"
            result += f"{'TYPE':<6} {'PERMISSIONS':<11} {'SIZE':<8} {'MODIFIED':<16} {'NAME'}\\n"
            result += "-" * 70 + "\\n"

            for item in detailed_items:
                result += f"{item['type']:<6} {item['permissions']:<11} {item['size']:<8} {item['modified']:<16} {item['name']}\\n"

            result += f"\\nTotal: {len(detailed_items)} items"
            if self.ignore:
                result += f" (filtered with patterns: {', '.join(self.ignore)})"

            return result

        except Exception as e:
            return f"Error listing directory: {str(e)}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
ls = LS

if __name__ == "__main__":
    # Test the tool with current directory
    import os

    current_dir = os.path.abspath(".")

    tool = LS(path=current_dir)
    print(tool.run())

    # Test with ignore patterns
    tool2 = LS(path=current_dir, ignore=["__pycache__", "*.pyc"])
    print("\\n" + "=" * 70 + "\\n")
    print("With ignore patterns:")
    print(tool2.run())
