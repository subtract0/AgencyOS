"""
Grid Transformation Utilities for TRM-7M Validation

Converts AgencyOS validation tasks to 2D grid format for TRM-7M inference:
1. Task graph → adjacency matrix (DAG validation)
2. Python code → type constraint grid (Dict[Any, Any] detection)
3. Function signature → edge case grid (boundary inference)
4. Python code → lint grid (format validation)
"""

import ast
import re
from pathlib import Path
from typing import Optional

from shared.models.task_graph import TaskGraph


def task_graph_to_adjacency_matrix(graph: TaskGraph) -> tuple[list[list[int]], list[str]]:
    """Convert TaskGraph to adjacency matrix for DAG validation.

    Args:
        graph: TaskGraph with tasks and dependencies

    Returns:
        Tuple of (adjacency_matrix, task_ids) where:
        - adjacency_matrix[i][j] = 1 if task_i depends on task_j
        - task_ids: list of task IDs in matrix order

    Example:
        # Task graph: task_1 → task_2 → task_4
        #                   ↘ task_3 ↗
        graph = TaskGraph(...)
        adj_matrix, task_ids = task_graph_to_adjacency_matrix(graph)
        # adj_matrix = [
        #     [0, 1, 1, 0],  # task_1 → task_2, task_3
        #     [0, 0, 0, 1],  # task_2 → task_4
        #     [0, 0, 0, 1],  # task_3 → task_4
        #     [0, 0, 0, 0]   # task_4 no deps
        # ]
    """
    all_tasks = graph.all_tasks()
    task_ids = [t.id for t in all_tasks]
    n_tasks = len(task_ids)

    # Initialize adjacency matrix (n x n)
    adj_matrix = [[0] * n_tasks for _ in range(n_tasks)]

    # Build adjacency matrix: adj_matrix[i][j] = 1 if task_i depends on task_j
    for task in all_tasks:
        i = task_ids.index(task.id)
        for dep_id in task.dependencies:
            try:
                j = task_ids.index(dep_id)
                adj_matrix[i][j] = 1
            except ValueError:
                # Dependency not in graph (validation error caught earlier)
                pass

    return adj_matrix, task_ids


def code_to_type_constraint_grid(code: str) -> tuple[list[list[int]], list[int]]:
    """Extract type constraint grid from Python code for Dict[Any, Any] detection.

    Args:
        code: Python source code string

    Returns:
        Tuple of (type_grid, line_numbers) where:
        - type_grid[i] = [has_param_types, has_return_type, uses_any, uses_dict_any]
        - line_numbers[i]: Line number for type_grid row i

    Grid encoding:
        - has_param_types: 1 if all function parameters have type annotations, 0 otherwise
        - has_return_type: 1 if function has return type annotation, 0 otherwise
        - uses_any: 1 if type annotation contains 'Any', 0 otherwise
        - uses_dict_any: 1 if type annotation contains 'Dict[Any, Any]', 0 otherwise

    Example:
        code = '''
        def process_data(items: list[str], config: Dict[Any, Any]) -> bool:
            ...
        '''
        type_grid, lines = code_to_type_constraint_grid(code)
        # type_grid = [[1, 1, 1, 1]]  # has params, has return, uses Any, uses Dict[Any, Any]
        # lines = [1]
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Invalid Python syntax, return empty grid
        return [], []

    type_grid = []
    line_numbers = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Extract function type annotations
            has_param_types = all(
                arg.annotation is not None for arg in node.args.args if arg.arg != "self"  # Exclude self parameter
            )
            has_return_type = node.returns is not None

            # Check for 'Any' usage in annotations
            func_source = ast.get_source_segment(code, node) or ""
            uses_any = "Any" in func_source
            uses_dict_any = re.search(r"Dict\s*\[\s*Any\s*,\s*Any\s*\]", func_source) is not None

            type_grid.append(
                [
                    1 if has_param_types else 0,
                    1 if has_return_type else 0,
                    1 if uses_any else 0,
                    1 if uses_dict_any else 0,
                ]
            )
            line_numbers.append(node.lineno)

    return type_grid, line_numbers


def function_signature_to_grid(signature: str) -> tuple[list[list[int]], list[str]]:
    """Convert function signature to grid for edge case inference.

    Args:
        signature: Function signature string (e.g., "def rate_limit(requests_per_min: int, burst_size: int) -> bool")

    Returns:
        Tuple of (signature_grid, param_names) where:
        - signature_grid[i] = [is_int, is_optional, max_value]
        - param_names[i]: Parameter name for grid row i

    Grid encoding:
        - is_int: 1 if parameter is int type, 0 otherwise
        - is_optional: 1 if parameter has Optional[] or default value, 0 otherwise
        - max_value: Inferred max value from context (default: 100)

    Example:
        signature = "def rate_limit(requests_per_min: int, burst_size: int = 50) -> bool"
        sig_grid, params = function_signature_to_grid(signature)
        # sig_grid = [
        #     [1, 0, 100],  # requests_per_min: int (no default)
        #     [1, 1, 50]    # burst_size: int = 50 (has default)
        # ]
        # params = ["requests_per_min", "burst_size"]
    """
    # Parse function signature using regex (simplified for MVP)
    # Match pattern: def func_name(param1: type1, param2: type2 = default, ...) -> return_type
    # Updated: Capture default value without trailing ) or ,
    param_pattern = r"(\w+)\s*:\s*(\w+(?:\[.*?\])?)\s*(?:=\s*([^,)]+))?"
    params = re.findall(param_pattern, signature)

    signature_grid = []
    param_names = []

    for param_name, param_type, default_value in params:
        # Check if parameter is int type
        is_int = "int" in param_type.lower()

        # Check if parameter is optional (has default value or Optional[])
        is_optional = bool(default_value) or "Optional" in param_type

        # Infer max value from default or use default as baseline
        max_value = 100  # Default max for parameters without defaults
        if default_value:
            # Try to parse default value as integer (strip whitespace first)
            try:
                parsed_default = int(default_value.strip())
                # Use default value itself as max_value for optional parameters
                max_value = parsed_default
            except ValueError:
                pass  # Keep default 100

        signature_grid.append([1 if is_int else 0, 1 if is_optional else 0, max_value])
        param_names.append(param_name)

    return signature_grid, param_names


def code_to_lint_grid(code: str, file_path: Path | None = None) -> tuple[list[list[int]], list[int]]:
    """Convert Python code to lint grid for format validation.

    Args:
        code: Python source code string
        file_path: Optional file path for import order validation

    Returns:
        Tuple of (lint_grid, line_numbers) where:
        - lint_grid[i] = [length, trailing_space, is_import, sorted]
        - line_numbers[i]: Line number for grid row i

    Grid encoding:
        - length: Line length (number of characters)
        - trailing_space: 1 if line has trailing whitespace, 0 otherwise
        - is_import: 1 if line is import statement, 0 otherwise
        - sorted: 1 if imports are alphabetically sorted up to this line, 0 otherwise

    Example:
        code = '''import os
        import sys

        def foo():
            x = 1
        '''
        lint_grid, lines = code_to_lint_grid(code)
        # lint_grid = [
        #     [9, 0, 1, 1],   # "import os" (length=9, no trailing, is_import, sorted)
        #     [10, 0, 1, 1],  # "import sys" (length=10, no trailing, is_import, sorted)
        #     [0, 0, 0, 0],   # empty line
        #     [10, 0, 0, 0],  # "def foo():"
        #     [8, 1, 0, 0]    # "    x = 1 " (HAS trailing space)
        # ]
    """
    lines = code.split("\n")
    lint_grid = []
    line_numbers = []

    import_lines = []
    previous_import = ""

    for line_num, line in enumerate(lines, start=1):
        # Calculate line length
        length = len(line)

        # Check for trailing whitespace
        has_trailing = line.endswith((" ", "\t")) and len(line.strip()) > 0

        # Check if line is import statement
        stripped = line.strip()
        is_import = stripped.startswith("import ") or stripped.startswith("from ")

        # Check if imports are sorted alphabetically
        is_sorted = True
        if is_import:
            import_lines.append(stripped)
            if previous_import and stripped < previous_import:
                is_sorted = False
            previous_import = stripped

        lint_grid.append(
            [
                length,
                1 if has_trailing else 0,
                1 if is_import else 0,
                1 if is_sorted else 0,
            ]
        )
        line_numbers.append(line_num)

    return lint_grid, line_numbers


def extract_function_signature_from_description(description: str) -> str | None:
    """Extract function signature from task description for edge case inference.

    Args:
        description: Task description (e.g., "Implement rate_limit(requests_per_min: int, burst_size: int) -> bool")

    Returns:
        Function signature string or None if not found

    Example:
        desc = "Implement rate limiting function: rate_limit(requests_per_min: int, burst_size: int) -> bool"
        sig = extract_function_signature_from_description(desc)
        # sig = "def rate_limit(requests_per_min: int, burst_size: int) -> bool"
    """
    # Pattern: function_name(params) -> return_type
    pattern = r"(\w+)\s*\(([^)]+)\)\s*(?:->\s*(\w+))?"
    match = re.search(pattern, description)

    if match:
        func_name = match.group(1)
        params = match.group(2)
        return_type = match.group(3) or "None"
        return f"def {func_name}({params}) -> {return_type}"

    return None


def apply_lint_fix(file_path: Path, fix: "LintFix") -> bool:  # noqa: F821
    """Apply auto-fix for lint violations.

    Args:
        file_path: Path to Python file
        fix: LintFix object with line number and fix type

    Returns:
        True if fix applied successfully, False otherwise

    Supported fixes:
        - remove_trailing_space: Remove trailing whitespace from line
        - sort_imports: Sort import statements alphabetically
        - fix_indentation: Correct indentation to 4 spaces
    """
    try:
        with open(file_path) as f:
            lines = f.readlines()

        if fix.fix_type == "remove_trailing_space":
            if 1 <= fix.line <= len(lines):
                lines[fix.line - 1] = lines[fix.line - 1].rstrip() + "\n"
        elif fix.fix_type == "sort_imports":
            # Collect all import lines and sort
            import_lines = []
            import_indices = []
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith("from "):
                    import_lines.append(line)
                    import_indices.append(i)

            # Sort imports alphabetically
            import_lines.sort()

            # Replace original import lines with sorted
            for i, idx in enumerate(import_indices):
                lines[idx] = import_lines[i]
        elif fix.fix_type == "fix_indentation":
            # Correct indentation to 4 spaces
            if 1 <= fix.line <= len(lines):
                line = lines[fix.line - 1]
                stripped = line.lstrip()
                indent_level = (len(line) - len(stripped)) // 4
                lines[fix.line - 1] = "    " * indent_level + stripped

        # Write fixed content back to file
        with open(file_path, "w") as f:
            f.writelines(lines)

        return True

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to apply lint fix {fix.fix_type} at line {fix.line}: {e}")
        return False
