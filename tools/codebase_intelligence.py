"""
Codebase Intelligence - Deep codebase understanding and indexing.

Provides intelligent code analysis including:
- Module dependency mapping
- Function/class discovery
- Symbol resolution
- Impact analysis for changes
- Code pattern detection

Constitutional Compliance:
- Article IV: Learning integration (stores patterns in VectorStore)
- Article V: Spec-driven (supports spec traceability)
"""

import ast
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


@dataclass
class Symbol:
    """A code symbol (function, class, variable)."""

    name: str
    kind: str  # 'function', 'class', 'method', 'variable', 'import'
    file_path: str
    line_number: int
    end_line: int
    docstring: Optional[str] = None
    signature: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    parent: Optional[str] = None  # For methods, the class name


@dataclass
class Import:
    """An import statement."""

    module: str
    names: list[str]  # Imported names (or ['*'] for star import)
    alias: Optional[str] = None
    file_path: str = ""
    line_number: int = 0


@dataclass
class Dependency:
    """A dependency between modules."""

    source: str  # Source module
    target: str  # Target module
    import_type: str  # 'import', 'from'
    symbols: list[str]  # Imported symbols


@dataclass
class CodebaseIndex:
    """Complete codebase index."""

    symbols: dict[str, list[Symbol]]  # file_path -> symbols
    imports: dict[str, list[Import]]  # file_path -> imports
    dependencies: list[Dependency]
    file_count: int
    symbol_count: int
    patterns_detected: list[str]


class SymbolExtractor(ast.NodeVisitor):
    """Extract symbols from Python AST."""

    def __init__(self, file_path: str):
        """Initialize extractor."""
        self.file_path = file_path
        self.symbols: list[Symbol] = []
        self.imports: list[Import] = []
        self._current_class: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self._extract_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self._extract_function(node, is_async=True)
        self.generic_visit(node)

    def _extract_function(self, node: ast.FunctionDef, is_async: bool) -> None:
        """Extract function/method symbol."""
        kind = "method" if self._current_class else "function"
        if is_async:
            kind = f"async_{kind}"

        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(dec.func.attr)

        # Get signature
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"

        signature = f"({', '.join(args)}){returns}"

        # Get docstring
        docstring = ast.get_docstring(node)

        self.symbols.append(
            Symbol(
                name=node.name,
                kind=kind,
                file_path=self.file_path,
                line_number=node.lineno,
                end_line=node.end_lineno or node.lineno,
                docstring=docstring,
                signature=signature,
                decorators=decorators,
                parent=self._current_class,
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        signature = f"({', '.join(bases)})" if bases else ""
        docstring = ast.get_docstring(node)

        self.symbols.append(
            Symbol(
                name=node.name,
                kind="class",
                file_path=self.file_path,
                line_number=node.lineno,
                end_line=node.end_lineno or node.lineno,
                docstring=docstring,
                signature=signature,
                decorators=decorators,
            )
        )

        # Track current class for methods
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            self.imports.append(
                Import(
                    module=alias.name,
                    names=[alias.name.split(".")[-1]],
                    alias=alias.asname,
                    file_path=self.file_path,
                    line_number=node.lineno,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statement."""
        module = node.module or ""
        names = [alias.name for alias in node.names]

        self.imports.append(
            Import(
                module=module,
                names=names,
                file_path=self.file_path,
                line_number=node.lineno,
            )
        )


class CodebaseIntelligence:
    """
    Intelligent codebase analysis and indexing.

    Provides deep understanding of code structure, dependencies,
    and patterns for autonomous development.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize codebase intelligence."""
        self.project_root = project_root or PROJECT_ROOT
        self._index: Optional[CodebaseIndex] = None
        self._symbol_cache: dict[str, list[Symbol]] = {}
        self._import_cache: dict[str, list[Import]] = {}

    def index_codebase(
        self, paths: Optional[list[str]] = None, exclude_tests: bool = False
    ) -> Result[CodebaseIndex, str]:
        """
        Index the codebase for analysis.

        Args:
            paths: Specific paths to index (default: all Python files)
            exclude_tests: Whether to exclude test files

        Returns:
            Result containing CodebaseIndex
        """
        try:
            all_symbols: dict[str, list[Symbol]] = {}
            all_imports: dict[str, list[Import]] = {}
            dependencies: list[Dependency] = []
            patterns_detected: list[str] = []

            # Find Python files
            if paths:
                py_files = [Path(p) for p in paths if p.endswith(".py")]
            else:
                py_files = list(self.project_root.rglob("*.py"))

            # Filter out tests if requested
            if exclude_tests:
                py_files = [
                    f
                    for f in py_files
                    if "test" not in f.name.lower() and "tests" not in str(f)
                ]

            # Filter out common exclusions
            py_files = [
                f
                for f in py_files
                if ".venv" not in str(f)
                and "__pycache__" not in str(f)
                and ".git" not in str(f)
            ]

            symbol_count = 0

            for py_file in py_files:
                result = self._index_file(py_file)
                if result.is_ok():
                    symbols, imports = result.unwrap()
                    rel_path = str(py_file.relative_to(self.project_root))
                    all_symbols[rel_path] = symbols
                    all_imports[rel_path] = imports
                    symbol_count += len(symbols)

                    # Build dependencies
                    for imp in imports:
                        dep = Dependency(
                            source=rel_path,
                            target=imp.module,
                            import_type="from" if imp.names != [imp.module.split(".")[-1]] else "import",
                            symbols=imp.names,
                        )
                        dependencies.append(dep)

            # Detect patterns
            patterns_detected = self._detect_patterns(all_symbols)

            self._index = CodebaseIndex(
                symbols=all_symbols,
                imports=all_imports,
                dependencies=dependencies,
                file_count=len(py_files),
                symbol_count=symbol_count,
                patterns_detected=patterns_detected,
            )

            return Ok(self._index)

        except Exception as e:
            return Err(f"Failed to index codebase: {e}")

    def _index_file(
        self, file_path: Path
    ) -> Result[tuple[list[Symbol], list[Import]], str]:
        """Index a single Python file."""
        try:
            source = file_path.read_text()
            tree = ast.parse(source)

            extractor = SymbolExtractor(str(file_path))
            extractor.visit(tree)

            return Ok((extractor.symbols, extractor.imports))

        except SyntaxError as e:
            return Err(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            return Err(f"Failed to index {file_path}: {e}")

    def _detect_patterns(self, symbols: dict[str, list[Symbol]]) -> list[str]:
        """Detect code patterns in the codebase."""
        patterns = []

        # Count pattern occurrences
        has_dataclass = False
        has_result_pattern = False
        has_pydantic = False
        has_async = False
        has_decorators = False

        for file_symbols in symbols.values():
            for sym in file_symbols:
                if "dataclass" in sym.decorators:
                    has_dataclass = True
                if sym.signature and "Result[" in sym.signature:
                    has_result_pattern = True
                if "BaseModel" in (sym.signature or ""):
                    has_pydantic = True
                if sym.kind.startswith("async_"):
                    has_async = True
                if sym.decorators:
                    has_decorators = True

        if has_dataclass:
            patterns.append("dataclass")
        if has_result_pattern:
            patterns.append("result_pattern")
        if has_pydantic:
            patterns.append("pydantic")
        if has_async:
            patterns.append("async_await")
        if has_decorators:
            patterns.append("decorators")

        return patterns

    def find_symbol(self, name: str, kind: Optional[str] = None) -> list[Symbol]:
        """
        Find symbols by name.

        Args:
            name: Symbol name to find
            kind: Optional kind filter ('function', 'class', 'method')

        Returns:
            List of matching symbols
        """
        if self._index is None:
            return []

        results = []
        for file_symbols in self._index.symbols.values():
            for sym in file_symbols:
                if sym.name == name:
                    if kind is None or sym.kind == kind:
                        results.append(sym)

        return results

    def find_references(self, symbol_name: str) -> list[tuple[str, int]]:
        """
        Find references to a symbol.

        Args:
            symbol_name: Name of symbol to find references to

        Returns:
            List of (file_path, line_number) tuples
        """
        if self._index is None:
            return []

        references = []

        # Check imports
        for file_path, imports in self._index.imports.items():
            for imp in imports:
                if symbol_name in imp.names:
                    references.append((file_path, imp.line_number))

        return references

    def get_dependencies(self, file_path: str) -> list[str]:
        """
        Get dependencies of a file.

        Args:
            file_path: Path to file

        Returns:
            List of module dependencies
        """
        if self._index is None:
            return []

        deps = []
        for dep in self._index.dependencies:
            if dep.source == file_path:
                deps.append(dep.target)

        return list(set(deps))

    def get_dependents(self, module_name: str) -> list[str]:
        """
        Get files that depend on a module.

        Args:
            module_name: Module name

        Returns:
            List of dependent file paths
        """
        if self._index is None:
            return []

        dependents = []
        for dep in self._index.dependencies:
            if module_name in dep.target:
                dependents.append(dep.source)

        return list(set(dependents))

    def analyze_impact(self, file_path: str) -> Result[dict, str]:
        """
        Analyze impact of changes to a file.

        Args:
            file_path: Path to file being changed

        Returns:
            Result containing impact analysis
        """
        if self._index is None:
            result = self.index_codebase()
            if result.is_err():
                return Err(result.unwrap_err())

        # Get symbols in the file
        symbols = self._index.symbols.get(file_path, [])  # type: ignore
        symbol_names = [s.name for s in symbols]

        # Find dependents
        dependents = self.get_dependents(file_path.replace("/", ".").replace(".py", ""))

        # Find which symbols are used externally
        external_refs = []
        for sym_name in symbol_names:
            refs = self.find_references(sym_name)
            external_refs.extend([r for r in refs if r[0] != file_path])

        # Calculate risk score
        risk_score = min(1.0, len(external_refs) * 0.1 + len(dependents) * 0.2)

        return Ok(
            {
                "file": file_path,
                "symbols_defined": len(symbols),
                "external_references": len(external_refs),
                "dependent_files": len(dependents),
                "dependents": dependents[:10],  # Limit output
                "risk_score": risk_score,
                "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.3 else "low",
            }
        )

    def get_module_graph(self) -> dict[str, list[str]]:
        """
        Get the module dependency graph.

        Returns:
            Dict mapping module -> list of dependencies
        """
        if self._index is None:
            return {}

        graph: dict[str, list[str]] = defaultdict(list)
        for dep in self._index.dependencies:
            graph[dep.source].append(dep.target)

        return dict(graph)

    def find_similar_code(
        self, code_snippet: str, top_k: int = 5
    ) -> list[tuple[Symbol, float]]:
        """
        Find similar code in the codebase.

        Args:
            code_snippet: Code to find similar matches for
            top_k: Number of results to return

        Returns:
            List of (symbol, similarity_score) tuples
        """
        if self._index is None:
            return []

        # Simple token-based similarity
        query_tokens = set(code_snippet.lower().split())

        scored = []
        for file_symbols in self._index.symbols.values():
            for sym in file_symbols:
                if sym.docstring:
                    sym_tokens = set(sym.docstring.lower().split())
                    if sym_tokens:
                        intersection = len(query_tokens & sym_tokens)
                        union = len(query_tokens | sym_tokens)
                        similarity = intersection / union if union > 0 else 0
                        if similarity > 0:
                            scored.append((sym, similarity))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_stats(self) -> dict:
        """Get codebase statistics."""
        if self._index is None:
            return {
                "indexed": False,
                "file_count": 0,
                "symbol_count": 0,
            }

        # Count by kind
        kind_counts: dict[str, int] = defaultdict(int)
        for file_symbols in self._index.symbols.values():
            for sym in file_symbols:
                kind_counts[sym.kind] += 1

        return {
            "indexed": True,
            "file_count": self._index.file_count,
            "symbol_count": self._index.symbol_count,
            "symbols_by_kind": dict(kind_counts),
            "patterns_detected": self._index.patterns_detected,
            "dependency_count": len(self._index.dependencies),
        }


def main():
    """Command-line interface for codebase intelligence."""
    import argparse

    parser = argparse.ArgumentParser(description="Codebase intelligence tool")
    parser.add_argument("--index", action="store_true", help="Index the codebase")
    parser.add_argument("--find", help="Find symbol by name")
    parser.add_argument("--impact", help="Analyze impact of file changes")
    parser.add_argument("--deps", help="Get dependencies of a file")
    parser.add_argument("--stats", action="store_true", help="Show codebase statistics")
    args = parser.parse_args()

    intel = CodebaseIntelligence()

    if args.index or args.stats:
        print("🔍 Indexing codebase...")
        result = intel.index_codebase()
        if result.is_ok():
            index = result.unwrap()
            print(f"✅ Indexed {index.file_count} files, {index.symbol_count} symbols")
            print(f"📦 Patterns: {', '.join(index.patterns_detected)}")
        else:
            print(f"❌ Error: {result.unwrap_err()}")
            return

    if args.stats:
        stats = intel.get_stats()
        print("\n📊 Codebase Statistics")
        print("=" * 50)
        print(f"Files: {stats['file_count']}")
        print(f"Symbols: {stats['symbol_count']}")
        print(f"Dependencies: {stats['dependency_count']}")
        if stats.get("symbols_by_kind"):
            print("\nSymbols by kind:")
            for kind, count in stats["symbols_by_kind"].items():
                print(f"  {kind}: {count}")

    if args.find:
        symbols = intel.find_symbol(args.find)
        if symbols:
            print(f"\n🔎 Found {len(symbols)} symbols named '{args.find}':")
            for sym in symbols:
                print(f"  - {sym.kind} in {sym.file_path}:{sym.line_number}")
                if sym.docstring:
                    print(f"    {sym.docstring[:100]}...")
        else:
            print(f"No symbols found with name '{args.find}'")

    if args.impact:
        result = intel.analyze_impact(args.impact)
        if result.is_ok():
            impact = result.unwrap()
            print(f"\n⚡ Impact Analysis for {args.impact}")
            print("=" * 50)
            print(f"Symbols defined: {impact['symbols_defined']}")
            print(f"External references: {impact['external_references']}")
            print(f"Dependent files: {impact['dependent_files']}")
            print(f"Risk level: {impact['risk_level']} ({impact['risk_score']:.2f})")
        else:
            print(f"Error: {result.unwrap_err()}")

    if args.deps:
        deps = intel.get_dependencies(args.deps)
        print(f"\n📦 Dependencies of {args.deps}:")
        for dep in deps:
            print(f"  - {dep}")


if __name__ == "__main__":
    main()
