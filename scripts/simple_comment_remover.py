#!/usr/bin/env python3
"""Simple standalone comment remover for P3 pruning fixes."""

import sys
from pathlib import Path


def remove_standalone_comments(file_path: Path) -> bool:
    """Remove standalone comment lines (keep inline comments and docstrings)."""
    with open(file_path) as f:
        lines = f.readlines()

    filtered_lines = []
    in_multiline_comment = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip standalone single-line comments (but keep shebangs)
        if stripped.startswith("#") and not stripped.startswith("#!"):
            # Check if previous line is a function/class definition
            if i > 0:
                prev = lines[i - 1].strip()
                if (
                    prev.startswith("def ")
                    or prev.startswith("class ")
                    or prev.startswith("async def")
                ):
                    # This might be a docstring, keep it
                    filtered_lines.append(line)
                    continue
            # Skip standalone comment
            continue

        # Handle multiline comment blocks (""" or ''')
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if in_multiline_comment:
                in_multiline_comment = False
                continue
            else:
                # Check if it's a docstring (after def/class)
                if i > 0:
                    prev = lines[i - 1].strip()
                    if (
                        prev.startswith("def ")
                        or prev.startswith("class ")
                        or prev.startswith("async def")
                    ):
                        filtered_lines.append(line)  # Keep docstring
                        continue
                in_multiline_comment = True
                continue

        if not in_multiline_comment:
            filtered_lines.append(line)

    # Write back
    with open(file_path, "w") as f:
        f.writelines(filtered_lines)

    removed = len(lines) - len(filtered_lines)
    if removed > 0:
        print(f"✓ Removed {removed} standalone comment lines from {file_path}")
        return True
    return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python simple_comment_remover.py <file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    remove_standalone_comments(file_path)
