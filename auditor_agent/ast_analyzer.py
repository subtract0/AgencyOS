"""
Lightweight AST analyzer for code quality assessment.
Extracts functions, classes, and behavioral coverage metrics.
"""

import ast
from typing import Dict, Any
from shared.type_definitions.json import JSONValue
from pathlib import Path


class ASTAnalyzer:
    """Analyzes Python code structure for quality assessment."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset analyzer state."""
        self.functions = []
        self.classes = []
        self.test_functions = []
        self.behaviors = []
        self.complexity_metrics = {}

    def analyze_file(self, file_path: str) -> Dict[str, JSONValue]:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)
            self.reset()

            visitor = CodeVisitor(file_path)
            visitor.visit(tree)

            is_test_file = self._is_test_file(file_path)

            return {
                "file_path": file_path,
                "is_test_file": is_test_file,
                "functions": visitor.functions,
                "classes": visitor.classes,
                "test_functions": visitor.test_functions if is_test_file else [],
                "behaviors": len(visitor.functions),
                "complexity": visitor.calculate_complexity(),
                "lines_of_code": len(content.splitlines()),
                "has_docstrings": visitor.has_docstrings(),
                "imports": visitor.imports
            }
        except Exception as e:
            return {"error": str(e), "file_path": file_path}

    def analyze_directory(self, dir_path: str) -> Dict[str, JSONValue]:
        """Analyze all Python files in directory."""
        results = {
            "source_files": [],
            "test_files": [],
            "total_behaviors": 0,
            "total_test_functions": 0,
            "coverage_ratio": 0.0
        }

        for py_file in Path(dir_path).rglob("*.py"):
            if self._should_skip_file(str(py_file)):
                continue

            analysis = self.analyze_file(str(py_file))
            if "error" in analysis:
                continue

            if analysis["is_test_file"]:
                results["test_files"].append(analysis)
                results["total_test_functions"] += len(analysis["test_functions"])
            else:
                results["source_files"].append(analysis)
                results["total_behaviors"] += analysis["behaviors"]

        # Calculate basic coverage ratio
        if results["total_behaviors"] > 0:
            results["coverage_ratio"] = results["total_test_functions"] / results["total_behaviors"]

        return results

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        path_lower = file_path.lower()
        return "test" in path_lower or file_path.endswith("_test.py")

    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped."""
        skip_patterns = ["__pycache__", ".git", "venv", "node_modules", "build", "dist"]
        return any(pattern in file_path for pattern in skip_patterns)


class CodeVisitor(ast.NodeVisitor):
    """AST visitor to extract code structure."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.functions = []
        self.classes = []
        self.test_functions = []
        self.imports = []
        self.current_class = None
        self.complexity_count = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        func_info = {
            "name": node.name,
            "lineno": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "is_method": self.current_class is not None,
            "parent_class": self.current_class,
            "is_async": False,
            "has_docstring": ast.get_docstring(node) is not None
        }

        self.functions.append(func_info)

        # Check if it's a test function
        if self._is_test_function(node.name):
            self.test_functions.append(func_info)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        func_info = {
            "name": node.name,
            "lineno": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "is_method": self.current_class is not None,
            "parent_class": self.current_class,
            "is_async": True,
            "has_docstring": ast.get_docstring(node) is not None
        }

        self.functions.append(func_info)

        if self._is_test_function(node.name):
            self.test_functions.append(func_info)

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        class_info = {
            "name": node.name,
            "lineno": node.lineno,
            "bases": [self._get_name(base) for base in node.bases],
            "has_docstring": ast.get_docstring(node) is not None
        }

        self.classes.append(class_info)

        # Track current class for method analysis
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import statement."""
        if node.module:
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_If(self, node):
        """Count if statements for complexity."""
        self.complexity_count += 1
        self.generic_visit(node)

    def visit_For(self, node):
        """Count for loops for complexity."""
        self.complexity_count += 1
        self.generic_visit(node)

    def visit_While(self, node):
        """Count while loops for complexity."""
        self.complexity_count += 1
        self.generic_visit(node)

    def calculate_complexity(self) -> int:
        """Calculate cyclomatic complexity approximation."""
        return max(1, self.complexity_count)

    def has_docstrings(self) -> float:
        """Calculate percentage of functions with docstrings."""
        if not self.functions:
            return 0.0

        documented = sum(1 for f in self.functions if f["has_docstring"])
        return documented / len(self.functions)

    def _is_test_function(self, name: str) -> bool:
        """Check if function name indicates a test."""
        return name.startswith("test_") or name.endswith("_test")

    def _get_name(self, node) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)