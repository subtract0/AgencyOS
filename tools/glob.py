import fnmatch
import os
from typing import List, Optional

from agency_swarm.tools import BaseTool
from pydantic import Field


class Glob(BaseTool):
    """
    Fast file pattern matching tool that works with any codebase size.

    - Supports glob patterns like "**/*.js" or "src/**/*.ts"
    - Returns matching file paths sorted by modification time
    - Use this tool when you need to find files by name patterns
    - When doing open-ended searches that may require multiple rounds, use the Task tool instead
    """

    pattern: str = Field(..., description="The glob pattern to match files against")
    path: Optional[str] = Field(
        None,
        description="The directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter 'undefined' or 'null' - simply omit it for the default behavior. Must be a valid directory path if provided.",
    )

    def run(self):
        try:
            # Determine search directory
            search_dir = self.path if self.path else os.getcwd()

            # Validate directory exists
            if not os.path.isdir(search_dir):
                return f"Error: Directory does not exist: {search_dir}"

            # Use our own glob implementation and respect .gitignore patterns
            gitignore_patterns = self._load_gitignore_patterns(search_dir)
            matches = self._find_files_matching_pattern(
                search_dir, self.pattern, gitignore_patterns
            )

            if not matches:
                return f"No files found matching pattern: {self.pattern}"

            # Sort by modification time (newest first)
            try:
                matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            except (OSError, IOError):
                # If we can't get modification times, just sort alphabetically
                matches.sort()

            # Return results
            result = f"Found {len(matches)} files matching '{self.pattern}':\\n\\n"
            for match in matches:
                result += f"{match}\\n"

            return result.strip()

        except Exception as e:
            return f"Error during glob search: {str(e)}"

    def _find_files_matching_pattern(
        self, root_dir: str, pattern: str, gitignore_patterns: List[str]
    ):
        """Custom implementation to find files matching a glob pattern."""
        matches = []

        # Handle different pattern types
        if "**" in pattern:
            # Recursive pattern
            matches = self._recursive_glob(root_dir, pattern, gitignore_patterns)
        else:
            # Simple pattern
            matches = self._simple_glob(root_dir, pattern, gitignore_patterns)

        return [os.path.abspath(match) for match in matches]

    def _recursive_glob(
        self, root_dir: str, pattern: str, gitignore_patterns: List[str]
    ):
        """Handle recursive patterns with **."""
        matches = []

        # Split the pattern at **
        if "**/" in pattern:
            before, after = pattern.split("**/", 1)
        else:
            before = ""
            after = pattern.replace("**", "*")

        # Walk the directory tree
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Prune ignored directories per .gitignore
            for d in list(dirnames):
                full_d = os.path.join(dirpath, d)
                if self._is_ignored(root_dir, full_d, gitignore_patterns):
                    dirnames.remove(d)
            # Check if current directory matches the 'before' part
            rel_path = os.path.relpath(dirpath, root_dir)
            if before and not fnmatch.fnmatch(rel_path, before):
                continue

            # Check files in this directory against the 'after' pattern
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                if self._is_ignored(root_dir, full_path, gitignore_patterns):
                    continue
                if fnmatch.fnmatch(filename, after):
                    matches.append(full_path)

        return matches

    def _simple_glob(self, root_dir: str, pattern: str, gitignore_patterns: List[str]):
        """Handle simple patterns without **."""
        matches = []

        # If pattern contains path separators, handle directory structure
        if "/" in pattern or "\\\\" in pattern:
            # Split pattern into directory and file parts
            pattern_parts = pattern.replace("\\\\", "/").split("/")
            self._match_path_pattern(
                root_dir, pattern_parts, "", matches, gitignore_patterns
            )
        else:
            # Simple filename pattern
            try:
                for item in os.listdir(root_dir):
                    item_path = os.path.join(root_dir, item)
                    if self._is_ignored(root_dir, item_path, gitignore_patterns):
                        continue
                    if os.path.isfile(item_path) and fnmatch.fnmatch(item, pattern):
                        matches.append(item_path)
            except PermissionError:
                pass

        return matches

    def _match_path_pattern(
        self,
        base_dir: str,
        pattern_parts: List[str],
        current_path: str,
        matches: List[str],
        gitignore_patterns: List[str],
    ):
        """Recursively match path patterns."""
        if not pattern_parts:
            # End of pattern, check if it's a file
            full_path = (
                os.path.join(base_dir, current_path) if current_path else base_dir
            )
            if os.path.isfile(full_path) and not self._is_ignored(
                base_dir, full_path, gitignore_patterns
            ):
                matches.append(full_path)
            return

        current_pattern = pattern_parts[0]
        remaining_patterns = pattern_parts[1:]

        search_path = os.path.join(base_dir, current_path) if current_path else base_dir

        if not os.path.isdir(search_path):
            return

        try:
            for item in os.listdir(search_path):
                full_item = os.path.join(search_path, item)
                if self._is_ignored(base_dir, full_item, gitignore_patterns):
                    continue
                if fnmatch.fnmatch(item, current_pattern):
                    new_path = (
                        os.path.join(current_path, item) if current_path else item
                    )
                    self._match_path_pattern(
                        base_dir,
                        remaining_patterns,
                        new_path,
                        matches,
                        gitignore_patterns,
                    )
        except PermissionError:
            pass

    def _load_gitignore_patterns(self, root_dir: str) -> List[str]:
        patterns: List[str] = []
        try:
            gi = os.path.join(root_dir, ".gitignore")
            if os.path.isfile(gi):
                with open(gi, "r", encoding="utf-8") as f:
                    for line in f:
                        s = line.strip()
                        if not s or s.startswith("#"):
                            continue
                        patterns.append(s)
        except Exception:
            pass
        return patterns

    def _is_ignored(self, root_dir: str, path: str, patterns: List[str]) -> bool:
        if not patterns:
            return False
        try:
            rel = os.path.relpath(path, root_dir)
        except Exception:
            rel = path
        rel_norm = rel.replace(os.sep, "/")
        for pat in patterns:
            pat_norm = pat.replace(os.sep, "/")
            # Directory patterns (e.g., "ignored_dir/")
            if pat_norm.endswith("/"):
                base = pat_norm[:-1]
                # Anchored directory
                if pat_norm.startswith("/"):
                    if ("/" + rel_norm == pat_norm[:-1]) or ("/" + rel_norm).startswith(
                        pat_norm
                    ):
                        return True
                else:
                    if (rel_norm == base) or rel_norm.startswith(pat_norm):
                        return True
                continue

            # File or general patterns
            if pat_norm.startswith("/"):
                if fnmatch.fnmatch("/" + rel_norm, pat_norm):
                    return True
            else:
                if fnmatch.fnmatch(rel_norm, pat_norm) or fnmatch.fnmatch(
                    os.path.basename(rel_norm), pat_norm
                ):
                    return True
        return False


# Create alias for Agency Swarm tool loading (expects class name = file name)
glob = Glob

if __name__ == "__main__":
    # Test the tool
    tool = Glob(pattern="*.py")
    print(tool.run())

    # Test recursive pattern
    tool2 = Glob(pattern="**/*.py")
    print("\\n" + "=" * 50 + "\\n")
    print(tool2.run())
