"""
Codegen System - Code analysis, test generation, and scaffolding.

This module provides development automation tools extracted from enterprise infrastructure:

- analyzer: Static code analysis with refactoring suggestions
- test_gen: Automatic test skeleton generation from specifications
- scaffold: Module and file scaffolding from templates

Usage:
    from tools.codegen.analyzer import suggest_refactors
    from tools.codegen.test_gen import generate_tests_from_spec
    from tools.codegen.scaffold import scaffold_module

    # Code analysis
    suggestions = suggest_refactors(["path/to/file.py"])

    # Test generation
    tests = generate_tests_from_spec("spec.md", "tests/")

    # Scaffolding
    files = scaffold_module("tool", "my_tool", "tools/my_tool/")
"""

from .analyzer import suggest_refactors, Suggestion
from .test_gen import generate_tests_from_spec, GeneratedTest
from .scaffold import scaffold_module, CreatedFile

__all__ = [
    "suggest_refactors",
    "Suggestion",
    "generate_tests_from_spec",
    "GeneratedTest",
    "scaffold_module",
    "CreatedFile"
]