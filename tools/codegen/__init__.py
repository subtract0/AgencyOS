"""
Intelligent Code Generation Suite (CodeGenEngine)

Additive code generation suite that accelerates development via:
- Refactor suggestions based on static analysis
- Test skeleton generation from specs
- Pattern-based scaffolding for new modules
"""
from .analyzer import suggest_refactors
from .test_gen import generate_tests_from_spec
from .scaffold import scaffold_module

__all__ = [
    "suggest_refactors",
    "generate_tests_from_spec",
    "scaffold_module",
]