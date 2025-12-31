"""
Tests for Codebase Intelligence (Phase 4).

Tests the codebase analysis and indexing including:
- Symbol extraction
- Dependency mapping
- Impact analysis
- Pattern detection
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestSymbol:
    """Tests for Symbol dataclass."""

    def test_symbol_creation(self):
        """Test creating a symbol."""
        from tools.codebase_intelligence import Symbol

        symbol = Symbol(
            name="process_data",
            kind="function",
            file_path="tools/processor.py",
            line_number=10,
            end_line=25,
            docstring="Process the data.",
            signature="(data: dict) -> Result",
            decorators=["staticmethod"],
        )

        assert symbol.name == "process_data"
        assert symbol.kind == "function"
        assert symbol.line_number == 10

    def test_symbol_with_parent(self):
        """Test symbol with parent class."""
        from tools.codebase_intelligence import Symbol

        symbol = Symbol(
            name="get_value",
            kind="method",
            file_path="models.py",
            line_number=15,
            end_line=20,
            parent="DataModel",
        )

        assert symbol.parent == "DataModel"
        assert symbol.kind == "method"


class TestImport:
    """Tests for Import dataclass."""

    def test_import_creation(self):
        """Test creating an import."""
        from tools.codebase_intelligence import Import

        imp = Import(
            module="json",
            names=["dumps", "loads"],
            file_path="utils.py",
            line_number=1,
        )

        assert imp.module == "json"
        assert "dumps" in imp.names

    def test_import_with_alias(self):
        """Test import with alias."""
        from tools.codebase_intelligence import Import

        imp = Import(
            module="numpy",
            names=["numpy"],
            alias="np",
        )

        assert imp.alias == "np"


class TestDependency:
    """Tests for Dependency dataclass."""

    def test_dependency_creation(self):
        """Test creating a dependency."""
        from tools.codebase_intelligence import Dependency

        dep = Dependency(
            source="tools/main.py",
            target="shared.utils",
            import_type="from",
            symbols=["helper", "validator"],
        )

        assert dep.source == "tools/main.py"
        assert dep.target == "shared.utils"


class TestSymbolExtractor:
    """Tests for SymbolExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        from tools.codebase_intelligence import SymbolExtractor

        return SymbolExtractor("test.py")

    def test_extract_function(self, extractor):
        """Test extracting a function."""
        import ast

        code = """
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b
"""
        tree = ast.parse(code)
        extractor.visit(tree)

        assert len(extractor.symbols) == 1
        assert extractor.symbols[0].name == "add"
        assert extractor.symbols[0].kind == "function"

    def test_extract_async_function(self, extractor):
        """Test extracting async function."""
        import ast

        code = """
async def fetch(url: str) -> str:
    '''Fetch data.'''
    return await response.text()
"""
        tree = ast.parse(code)
        extractor.visit(tree)

        assert len(extractor.symbols) == 1
        assert "async" in extractor.symbols[0].kind

    def test_extract_class(self, extractor):
        """Test extracting a class."""
        import ast

        code = """
class DataProcessor:
    '''Process data.'''

    def process(self):
        pass
"""
        tree = ast.parse(code)
        extractor.visit(tree)

        # Should have class and method
        assert len(extractor.symbols) == 2
        class_sym = [s for s in extractor.symbols if s.kind == "class"][0]
        assert class_sym.name == "DataProcessor"

    def test_extract_imports(self, extractor):
        """Test extracting imports."""
        import ast

        code = """
import json
from typing import Optional, List
"""
        tree = ast.parse(code)
        extractor.visit(tree)

        assert len(extractor.imports) == 2

    def test_extract_decorators(self, extractor):
        """Test extracting decorated functions."""
        import ast

        code = """
@staticmethod
@property
def get_value():
    pass
"""
        tree = ast.parse(code)
        extractor.visit(tree)

        assert len(extractor.symbols) == 1
        assert "staticmethod" in extractor.symbols[0].decorators
        assert "property" in extractor.symbols[0].decorators


class TestCodebaseIntelligence:
    """Tests for CodebaseIntelligence class."""

    @pytest.fixture
    def intel(self, tmp_path):
        """Create intelligence instance with test project."""
        from tools.codebase_intelligence import CodebaseIntelligence

        # Create test project structure
        (tmp_path / "main.py").write_text("""
import json
from utils import helper

def main():
    '''Main function.'''
    return helper()
""")

        (tmp_path / "utils.py").write_text("""
def helper():
    '''Helper function.'''
    return 42

class DataClass:
    '''Data class.'''
    def get(self):
        return self.data
""")

        return CodebaseIntelligence(tmp_path)

    def test_index_codebase(self, intel):
        """Test indexing the codebase."""
        result = intel.index_codebase()

        assert result.is_ok()
        index = result.unwrap()
        assert index.file_count == 2
        assert index.symbol_count > 0

    def test_index_codebase_excludes_tests(self, intel, tmp_path):
        """Test that tests can be excluded."""
        # Add a test file
        (tmp_path / "test_main.py").write_text("def test_foo(): pass")

        result = intel.index_codebase(exclude_tests=True)

        assert result.is_ok()
        index = result.unwrap()
        # Should not include test file
        assert "test_main.py" not in index.symbols

    def test_find_symbol(self, intel):
        """Test finding symbols by name."""
        intel.index_codebase()

        symbols = intel.find_symbol("helper")

        assert len(symbols) >= 1
        assert symbols[0].name == "helper"

    def test_find_symbol_by_kind(self, intel):
        """Test finding symbols by kind."""
        intel.index_codebase()

        symbols = intel.find_symbol("DataClass", kind="class")

        assert len(symbols) == 1
        assert symbols[0].kind == "class"

    def test_find_references(self, intel):
        """Test finding references to a symbol."""
        intel.index_codebase()

        refs = intel.find_references("helper")

        # helper is imported in main.py
        assert len(refs) >= 1

    def test_get_dependencies(self, intel):
        """Test getting file dependencies."""
        intel.index_codebase()

        deps = intel.get_dependencies("main.py")

        assert "json" in deps or "utils" in deps

    def test_get_dependents(self, intel):
        """Test getting files that depend on a module."""
        intel.index_codebase()

        dependents = intel.get_dependents("utils")

        assert len(dependents) >= 1

    def test_analyze_impact(self, intel):
        """Test impact analysis."""
        intel.index_codebase()

        result = intel.analyze_impact("utils.py")

        assert result.is_ok()
        impact = result.unwrap()
        assert "symbols_defined" in impact
        assert "risk_score" in impact
        assert "risk_level" in impact

    def test_get_module_graph(self, intel):
        """Test getting module dependency graph."""
        intel.index_codebase()

        graph = intel.get_module_graph()

        assert isinstance(graph, dict)

    def test_get_stats(self, intel):
        """Test getting codebase statistics."""
        intel.index_codebase()

        stats = intel.get_stats()

        assert stats["indexed"] is True
        assert stats["file_count"] == 2
        assert stats["symbol_count"] > 0

    def test_stats_before_index(self, intel):
        """Test stats before indexing."""
        stats = intel.get_stats()

        assert stats["indexed"] is False

    def test_detect_patterns(self, intel, tmp_path):
        """Test pattern detection."""
        # Add file with patterns
        (tmp_path / "patterns.py").write_text("""
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class DataItem:
    value: int

async def fetch():
    pass
""")

        result = intel.index_codebase()

        assert result.is_ok()
        index = result.unwrap()
        assert "dataclass" in index.patterns_detected or "async_await" in index.patterns_detected


class TestCodebaseIndex:
    """Tests for CodebaseIndex dataclass."""

    def test_codebase_index_creation(self):
        """Test creating a codebase index."""
        from tools.codebase_intelligence import CodebaseIndex

        index = CodebaseIndex(
            symbols={},
            imports={},
            dependencies=[],
            file_count=10,
            symbol_count=50,
            patterns_detected=["result_pattern", "pydantic"],
        )

        assert index.file_count == 10
        assert index.symbol_count == 50
        assert len(index.patterns_detected) == 2


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def intel(self, tmp_path):
        """Create intelligence for edge case testing."""
        from tools.codebase_intelligence import CodebaseIntelligence

        return CodebaseIntelligence(tmp_path)

    def test_index_empty_directory(self, intel):
        """Test indexing empty directory."""
        result = intel.index_codebase()

        assert result.is_ok()
        index = result.unwrap()
        assert index.file_count == 0

    def test_index_syntax_error_file(self, intel, tmp_path):
        """Test indexing file with syntax error."""
        (tmp_path / "broken.py").write_text("def broken(:\n    pass")

        result = intel.index_codebase()

        # Should still succeed, just skip broken file
        assert result.is_ok()

    def test_find_symbol_not_indexed(self, intel):
        """Test finding symbol before indexing."""
        symbols = intel.find_symbol("anything")

        assert len(symbols) == 0

    def test_find_similar_code(self, intel, tmp_path):
        """Test finding similar code."""
        (tmp_path / "functions.py").write_text('''
def calculate_total():
    """Calculate the total amount."""
    pass

def compute_sum():
    """Compute the sum of values."""
    pass
''')
        intel.index_codebase()

        similar = intel.find_similar_code("calculate sum")

        assert isinstance(similar, list)
