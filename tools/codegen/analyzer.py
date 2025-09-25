"""
Static analysis and refactoring suggestions using AST.
"""
from __future__ import annotations

import ast
import dataclasses
import os
from typing import Any, Dict, List, Optional


@dataclasses.dataclass
class Suggestion:
    """A refactoring suggestion."""
    path: str
    line: int
    severity: str  # "info", "warning", "error"
    rule_id: str
    message: str
    fix_hint: Optional[str] = None
    diff: Optional[str] = None


class RefactorAnalyzer(ast.NodeVisitor):
    """AST visitor that detects code patterns for refactoring suggestions."""

    def __init__(self, path: str, rules: List[str]):
        self.path = path
        self.rules = rules
        self.suggestions: List[Suggestion] = []
        self.source_lines: List[str] = []

    def visit_Try(self, node: ast.Try) -> None:
        """Detect broad exception catches."""
        if "broad-except" in self.rules:
            for handler in node.handlers:
                if (handler.type is None or
                    (isinstance(handler.type, ast.Name) and handler.type.id in ["Exception", "BaseException"])):
                    self.suggestions.append(Suggestion(
                        path=self.path,
                        line=handler.lineno,
                        severity="warning",
                        rule_id="broad-except",
                        message="Catching too general exception",
                        fix_hint="Catch specific exception types instead"
                    ))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Detect long functions and missing type hints."""
        if "long-function" in self.rules:
            # Count non-empty lines in function
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1
            if end_line - start_line > 50:  # threshold: 50 lines
                self.suggestions.append(Suggestion(
                    path=self.path,
                    line=node.lineno,
                    severity="info",
                    rule_id="long-function",
                    message=f"Function '{node.name}' is {end_line - start_line} lines long",
                    fix_hint="Consider breaking into smaller functions"
                ))

        if "missing-type-hints" in self.rules:
            # Check if public function (not starting with _) has type annotations
            if not node.name.startswith('_'):
                has_return_annotation = node.returns is not None
                has_arg_annotations = all(arg.annotation is not None for arg in node.args.args)

                if not (has_return_annotation and has_arg_annotations):
                    self.suggestions.append(Suggestion(
                        path=self.path,
                        line=node.lineno,
                        severity="info",
                        rule_id="missing-type-hints",
                        message=f"Public function '{node.name}' missing type hints",
                        fix_hint="Add type annotations for parameters and return value"
                    ))

        self.generic_visit(node)

    def visit_Comment(self, node: Any) -> None:
        """Detect dead-code markers in comments."""
        if "dead-code-markers" in self.rules:
            # This is a simplified approach - in real implementation we'd need to parse comments
            pass


def suggest_refactors(paths: List[str], rules: Optional[List[str]] = None) -> List[Suggestion]:
    """
    Analyze code paths and suggest refactoring opportunities.

    Args:
        paths: List of file paths to analyze
        rules: List of rule IDs to apply (default: all basic rules)

    Returns:
        List of suggestions for improvements
    """
    if rules is None:
        rules = ["broad-except", "long-function", "missing-type-hints", "dead-code-markers"]

    suggestions: List[Suggestion] = []

    for path in paths:
        if not path.endswith('.py'):
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
                source_lines = source.splitlines()

            # Parse AST
            tree = ast.parse(source, filename=path)

            # Analyze with visitor
            analyzer = RefactorAnalyzer(path, rules)
            analyzer.source_lines = source_lines
            analyzer.visit(tree)
            suggestions.extend(analyzer.suggestions)

            # Check for dead-code markers in comments
            if "dead-code-markers" in rules:
                for i, line in enumerate(source_lines):
                    if any(marker in line.lower() for marker in ["todo", "xxx", "fixme", "hack"]):
                        suggestions.append(Suggestion(
                            path=path,
                            line=i + 1,
                            severity="info",
                            rule_id="dead-code-markers",
                            message=f"Dead code marker found: {line.strip()}",
                            fix_hint="Consider addressing or removing the marker"
                        ))

        except (OSError, SyntaxError) as e:
            suggestions.append(Suggestion(
                path=path,
                line=1,
                severity="error",
                rule_id="parse-error",
                message=f"Could not analyze file: {e}",
                fix_hint="Fix syntax errors or file access issues"
            ))

    return suggestions