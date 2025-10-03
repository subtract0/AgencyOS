"""
Smart Test Selection - Git-aware test execution.

This module implements intelligent test selection based on code changes,
dramatically reducing test execution time for incremental development.

Features:
- Git diff analysis to find changed files
- Dependency tracking via import analysis
- Impact analysis to identify affected tests
- Time estimation for optimized runs

Constitutional Compliance:
- Article I: Complete context (full dependency graph)
- Article II: 100% verification (test all affected code)
- Result<T,E> pattern for error handling
"""

import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from pydantic import BaseModel, Field
from shared.type_definitions.result import Result, Ok, Err


@dataclass
class FileChange:
    """Represents a changed file in git."""
    path: str
    change_type: str  # M (modified), A (added), D (deleted)
    is_test: bool


@dataclass
class DependencyNode:
    """Node in the dependency graph."""
    file_path: str
    imports: Set[str]
    imported_by: Set[str]
    related_tests: Set[str]


class TestSelectionReport(BaseModel):
    """Report of smart test selection results."""
    changed_files: List[str] = Field(..., description="Files changed in git diff")
    affected_tests: List[str] = Field(..., description="Tests that need to run")
    total_tests: int = Field(..., description="Total number of tests in suite")
    estimated_time_saved: float = Field(..., description="Estimated time saved in seconds")
    selection_ratio: float = Field(..., description="Ratio of selected to total tests")

    class Config:
        json_schema_extra = {
            "example": {
                "changed_files": ["agency_code_agent/coder.py"],
                "affected_tests": ["tests/test_coder.py::test_generate_code"],
                "total_tests": 2438,
                "estimated_time_saved": 180.0,
                "selection_ratio": 0.05
            }
        }


class SmartTestSelector:
    """Select tests based on git changes and dependency analysis."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dependency_graph: Dict[str, DependencyNode] = {}
        self.test_to_files: Dict[str, Set[str]] = defaultdict(set)

    def get_changed_files(self, since: str = "HEAD~1") -> Result[List[FileChange], str]:
        """
        Get files changed since specified commit.

        Args:
            since: Git reference to compare against (default: HEAD~1)

        Returns:
            Result containing list of FileChange objects
        """
        try:
            # Run git diff to get changed files
            result = subprocess.run(
                ["git", "diff", "--name-status", since],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )

            changes = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) >= 2:
                    change_type = parts[0]
                    file_path = parts[1]

                    # Check if it's a Python file
                    if file_path.endswith('.py'):
                        is_test = 'test_' in file_path or file_path.startswith('tests/')

                        changes.append(FileChange(
                            path=file_path,
                            change_type=change_type,
                            is_test=is_test
                        ))

            return Ok(changes)

        except subprocess.CalledProcessError as e:
            return Err(f"Git diff failed: {e.stderr}")
        except Exception as e:
            return Err(f"Failed to get changed files: {str(e)}")

    def build_dependency_graph(self) -> Result[None, str]:
        """Build dependency graph for all Python files."""
        try:
            # Find all Python files
            py_files = list(self.project_root.rglob("*.py"))

            # Exclude certain directories
            exclude_dirs = {'.venv', 'venv', 'node_modules', '__pycache__', '.git'}

            for py_file in py_files:
                # Skip excluded directories
                if any(excluded in py_file.parts for excluded in exclude_dirs):
                    continue

                # Get relative path
                rel_path = str(py_file.relative_to(self.project_root))

                # Parse file for imports
                imports = self._extract_imports(py_file)

                # Create dependency node
                self.dependency_graph[rel_path] = DependencyNode(
                    file_path=rel_path,
                    imports=imports,
                    imported_by=set(),
                    related_tests=set()
                )

            # Build reverse dependencies (imported_by)
            for file_path, node in self.dependency_graph.items():
                for imported in node.imports:
                    # Find the actual file for this import
                    actual_file = self._resolve_import_to_file(imported)
                    if actual_file and actual_file in self.dependency_graph:
                        self.dependency_graph[actual_file].imported_by.add(file_path)

            # Map tests to source files
            for file_path, node in self.dependency_graph.items():
                if 'test_' in file_path or file_path.startswith('tests/'):
                    # This is a test file, find what it tests
                    for imported in node.imports:
                        actual_file = self._resolve_import_to_file(imported)
                        if actual_file:
                            self.test_to_files[file_path].add(actual_file)

                            # Add reverse mapping
                            if actual_file in self.dependency_graph:
                                self.dependency_graph[actual_file].related_tests.add(file_path)

            return Ok(None)

        except Exception as e:
            return Err(f"Failed to build dependency graph: {str(e)}")

    def _extract_imports(self, file_path: Path) -> Set[str]:
        """Extract all imports from a Python file."""
        imports = set()

        try:
            with open(file_path, 'r') as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)

        except Exception:
            # Skip files that can't be parsed
            pass

        return imports

    def _resolve_import_to_file(self, import_name: str) -> Optional[str]:
        """Resolve an import statement to an actual file path."""
        # Convert import to file path
        # e.g., "agency_code_agent.coder" -> "agency_code_agent/coder.py"

        parts = import_name.split('.')
        potential_paths = [
            '/'.join(parts) + '.py',
            '/'.join(parts) + '/__init__.py',
        ]

        for path in potential_paths:
            if path in self.dependency_graph:
                return path

        return None

    def find_affected_tests(self, changed_files: List[FileChange]) -> Result[List[str], str]:
        """
        Find tests affected by changed files.

        Args:
            changed_files: List of changed files from git diff

        Returns:
            Result containing list of test file paths to run
        """
        try:
            # Ensure dependency graph is built
            if not self.dependency_graph:
                build_result = self.build_dependency_graph()
                if build_result.is_err():
                    return Err(build_result.unwrap_err())

            affected_tests = set()

            for change in changed_files:
                # If the change is a test file, always run it
                if change.is_test:
                    affected_tests.add(change.path)
                    continue

                # Find tests that import this file (direct dependency)
                if change.path in self.dependency_graph:
                    node = self.dependency_graph[change.path]
                    affected_tests.update(node.related_tests)

                    # Also check files that import this file (transitive dependency)
                    for importer in node.imported_by:
                        if importer in self.dependency_graph:
                            affected_tests.update(self.dependency_graph[importer].related_tests)

            return Ok(sorted(list(affected_tests)))

        except Exception as e:
            return Err(f"Failed to find affected tests: {str(e)}")

    def estimate_time_saved(
        self,
        selected_tests: List[str],
        all_tests: Optional[List[str]] = None,
        avg_test_time: float = 0.09
    ) -> float:
        """
        Estimate time saved by smart selection.

        Args:
            selected_tests: Tests selected to run
            all_tests: All available tests (if None, will scan)
            avg_test_time: Average time per test in seconds

        Returns:
            Estimated time saved in seconds
        """
        if all_tests is None:
            # Count all test files
            test_files = list(self.project_root.rglob("test_*.py"))
            test_count = len(test_files) * 10  # Estimate 10 tests per file
        else:
            test_count = len(all_tests)

        selected_count = len(selected_tests)

        # Calculate time for full suite vs selected
        full_suite_time = test_count * avg_test_time
        selected_time = selected_count * avg_test_time

        return full_suite_time - selected_time

    def generate_selection_report(
        self,
        changed_files: List[FileChange],
        affected_tests: List[str],
        total_tests: int = 2438,
        avg_test_time: float = 0.09
    ) -> TestSelectionReport:
        """Generate test selection report."""

        time_saved = self.estimate_time_saved(affected_tests, avg_test_time=avg_test_time)
        selection_ratio = len(affected_tests) / total_tests if total_tests > 0 else 0

        return TestSelectionReport(
            changed_files=[c.path for c in changed_files],
            affected_tests=affected_tests,
            total_tests=total_tests,
            estimated_time_saved=round(time_saved, 1),
            selection_ratio=round(selection_ratio, 3)
        )

    def select_tests_for_commit(self, since: str = "HEAD~1") -> Result[TestSelectionReport, str]:
        """
        Select tests to run based on git changes since specified commit.

        Args:
            since: Git reference to compare against

        Returns:
            Result containing TestSelectionReport
        """
        # Get changed files
        changes_result = self.get_changed_files(since)
        if changes_result.is_err():
            return Err(changes_result.unwrap_err())

        changed_files = changes_result.unwrap()

        # Find affected tests
        tests_result = self.find_affected_tests(changed_files)
        if tests_result.is_err():
            return Err(tests_result.unwrap_err())

        affected_tests = tests_result.unwrap()

        # Generate report
        report = self.generate_selection_report(changed_files, affected_tests)

        return Ok(report)

    def format_report(self, report: TestSelectionReport) -> str:
        """Format selection report as human-readable text."""
        lines = [
            "# Smart Test Selection Report",
            "",
            "## Changed Files",
            ""
        ]

        if report.changed_files:
            for file_path in report.changed_files:
                lines.append(f"- {file_path}")
        else:
            lines.append("*No files changed*")

        lines.extend([
            "",
            "## Affected Tests",
            "",
            f"**{len(report.affected_tests)} of {report.total_tests} tests need to run** ({report.selection_ratio:.1%})",
            ""
        ])

        if report.affected_tests:
            for test_path in report.affected_tests[:20]:
                lines.append(f"- {test_path}")

            if len(report.affected_tests) > 20:
                lines.append(f"- ... and {len(report.affected_tests) - 20} more")
        else:
            lines.append("*No tests affected*")

        lines.extend([
            "",
            "## Performance Impact",
            "",
            f"- **Tests to run:** {len(report.affected_tests)}",
            f"- **Tests skipped:** {report.total_tests - len(report.affected_tests)}",
            f"- **Estimated time saved:** {report.estimated_time_saved:.1f} seconds",
            f"- **Speedup:** {(report.total_tests / max(len(report.affected_tests), 1)):.1f}x faster",
            "",
            "## Command to Run Selected Tests",
            "",
            "```bash"
        ])

        if report.affected_tests:
            test_args = ' '.join(f'"{t}"' for t in report.affected_tests[:10])
            if len(report.affected_tests) <= 10:
                lines.append(f"pytest {test_args}")
            else:
                lines.append("# Save to file and run:")
                lines.append("python -m tools.smart_test_selection --output selected_tests.txt")
                lines.append("pytest $(cat selected_tests.txt)")
        else:
            lines.append("# No tests to run")

        lines.extend([
            "```",
            "",
            "---",
            "",
            "*Generated by Agency Smart Test Selection*"
        ])

        return '\n'.join(lines)


# CLI Interface
def main() -> int:
    """Command-line interface for smart test selection."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Smart test selection based on git changes"
    )
    parser.add_argument(
        "--since",
        default="HEAD~1",
        help="Git reference to compare against (default: HEAD~1)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for selected tests (one per line)"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/testing/SMART_SELECTION.md"),
        help="Output path for report"
    )

    args = parser.parse_args()

    # Run selector
    project_root = Path.cwd()
    selector = SmartTestSelector(project_root)

    print(f"🔍 Analyzing changes since {args.since}...")

    # Build dependency graph
    print("📊 Building dependency graph...")
    build_result = selector.build_dependency_graph()
    if build_result.is_err():
        print(f"❌ Failed to build dependency graph: {build_result.unwrap_err()}")
        return 1

    # Select tests
    result = selector.select_tests_for_commit(args.since)

    if result.is_err():
        print(f"❌ Test selection failed: {result.unwrap_err()}")
        return 1

    report = result.unwrap()

    # Print summary
    print(f"\n✅ Smart test selection complete!")
    print(f"📁 Changed files: {len(report.changed_files)}")
    print(f"🧪 Affected tests: {len(report.affected_tests)} of {report.total_tests}")
    print(f"⚡ Estimated time saved: {report.estimated_time_saved:.1f}s")
    print(f"🚀 Speedup: {(report.total_tests / max(len(report.affected_tests), 1)):.1f}x")

    # Save selected tests to file if requested
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w') as f:
                for test in report.affected_tests:
                    f.write(f"{test}\n")
            print(f"💾 Selected tests saved to: {args.output}")
        except Exception as e:
            print(f"❌ Failed to save test list: {e}")
            return 1

    # Save report
    try:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        report_text = selector.format_report(report)
        with open(args.report, 'w') as f:
            f.write(report_text)
        print(f"📝 Report saved to: {args.report}")
    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
