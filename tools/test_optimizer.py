"""
Test Suite Optimizer - Analyze and optimize test execution.

This module identifies optimization opportunities including:
- Parallelizable tests
- Expensive fixtures
- Redundant test coverage
- Mocking opportunities

Constitutional Compliance:
- Article I: Complete context before action
- Article II: 100% verification
- Result<T,E> pattern for error handling
"""

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result


@dataclass
class TestMetadata:
    """Metadata about a test function."""

    name: str
    file_path: str
    imports: set[str]
    fixtures_used: set[str]
    has_db_access: bool
    has_file_io: bool
    has_network_calls: bool
    has_external_deps: bool
    is_async: bool
    line_number: int


@dataclass
class FixtureMetadata:
    """Metadata about a fixture."""

    name: str
    file_path: str
    scope: str  # function, class, module, session
    has_db_setup: bool
    has_network_setup: bool
    estimated_cost_ms: float


class OptimizationPlan(BaseModel):
    """Test optimization plan with actionable recommendations."""

    parallelizable_tests: list[str] = Field(..., description="Tests safe to parallelize")
    expensive_fixtures: dict[str, float] = Field(..., description="Fixtures and their cost in ms")
    mock_candidates: list[dict[str, str]] = Field(..., description="Tests needing mocks")
    redundant_tests: list[dict[str, str]] = Field(..., description="Potentially redundant tests")
    estimated_savings_seconds: float = Field(..., description="Total estimated time savings")

    class Config:
        json_schema_extra = {
            "example": {
                "parallelizable_tests": ["test_unit_calc", "test_parser"],
                "expensive_fixtures": {"db_session": 500.0},
                "mock_candidates": [{"test": "test_api_call", "target": "requests.get"}],
                "redundant_tests": [],
                "estimated_savings_seconds": 45.0,
            }
        }


class TestOptimizer:
    """Analyze and optimize test suite performance."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_metadata: dict[str, TestMetadata] = {}
        self.fixture_metadata: dict[str, FixtureMetadata] = {}

    def analyze_tests(self, test_dir: str = "tests/") -> Result[OptimizationPlan, str]:
        """
        Analyze test suite and generate optimization plan.

        Args:
            test_dir: Directory containing tests

        Returns:
            Result containing OptimizationPlan or error message
        """
        try:
            test_path = self.project_root / test_dir

            # Scan all test files
            test_files = list(test_path.rglob("test_*.py"))

            for test_file in test_files:
                self._analyze_test_file(test_file)

            # Generate optimization plan
            plan = self._generate_optimization_plan()

            return Ok(plan)

        except Exception as e:
            return Err(f"Test analysis failed: {str(e)}")

    def _analyze_test_file(self, file_path: Path) -> None:
        """Analyze a single test file for optimization opportunities."""
        try:
            with open(file_path) as f:
                source = f.read()

            tree = ast.parse(source)

            # Extract imports
            imports = self._extract_imports(tree)

            # Find fixtures
            fixtures = self._extract_fixtures(tree, file_path)
            for fixture_name, fixture_meta in fixtures.items():
                self.fixture_metadata[fixture_name] = fixture_meta

            # Find test functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    metadata = self._analyze_test_function(node, file_path, imports)
                    self.test_metadata[f"{file_path}::{node.name}"] = metadata

        except Exception:
            # Skip files that can't be parsed
            pass

    def _extract_imports(self, tree: ast.AST) -> set[str]:
        """Extract all imports from AST."""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

        return imports

    def _extract_fixtures(self, tree: ast.AST, file_path: Path) -> dict[str, FixtureMetadata]:
        """Extract pytest fixtures from AST."""
        fixtures = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for @pytest.fixture decorator
                for decorator in node.decorator_list:
                    if self._is_fixture_decorator(decorator):
                        scope = self._get_fixture_scope(decorator)
                        has_db = self._contains_db_setup(node)
                        has_network = self._contains_network_setup(node)

                        # Estimate cost based on setup complexity
                        cost_ms = 10.0  # Base cost
                        if has_db:
                            cost_ms += 200.0
                        if has_network:
                            cost_ms += 100.0
                        if scope == "function":
                            cost_ms *= 1.5  # Higher cost for function scope

                        fixtures[node.name] = FixtureMetadata(
                            name=node.name,
                            file_path=str(file_path),
                            scope=scope,
                            has_db_setup=has_db,
                            has_network_setup=has_network,
                            estimated_cost_ms=cost_ms,
                        )

        return fixtures

    def _is_fixture_decorator(self, decorator: ast.expr) -> bool:
        """Check if decorator is pytest.fixture."""
        if isinstance(decorator, ast.Name) and decorator.id == "fixture":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "fixture":
            return True
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name) and decorator.func.id == "fixture":
                return True
            if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "fixture":
                return True
        return False

    def _get_fixture_scope(self, decorator: ast.expr) -> str:
        """Extract fixture scope from decorator."""
        if isinstance(decorator, ast.Call):
            for keyword in decorator.keywords:
                if keyword.arg == "scope":
                    if isinstance(keyword.value, ast.Constant):
                        return keyword.value.value
        return "function"  # Default scope

    def _contains_db_setup(self, node: ast.FunctionDef) -> bool:
        """Check if function contains database setup."""
        source = ast.get_source_segment(ast.unparse(node), node)
        if source:
            db_keywords = [
                "database",
                "db",
                "session",
                "engine",
                "sqlalchemy",
                "create_all",
                "drop_all",
            ]
            return any(keyword in source.lower() for keyword in db_keywords)
        return False

    def _contains_network_setup(self, node: ast.FunctionDef) -> bool:
        """Check if function contains network setup."""
        source = ast.get_source_segment(ast.unparse(node), node)
        if source:
            network_keywords = ["requests", "httpx", "urllib", "socket", "api", "http"]
            return any(keyword in source.lower() for keyword in network_keywords)
        return False

    def _analyze_test_function(
        self, node: ast.FunctionDef, file_path: Path, imports: set[str]
    ) -> TestMetadata:
        """Analyze a test function for optimization opportunities."""

        # Extract fixtures used
        fixtures_used = set()
        if node.args.args:
            fixtures_used = {arg.arg for arg in node.args.args if arg.arg != "self"}

        # Check for external dependencies
        source = ast.unparse(node)

        has_db = any(
            keyword in source.lower() for keyword in ["session", "database", "db", "query"]
        )
        has_file_io = any(
            keyword in source.lower() for keyword in ["open(", "read(", "write(", "file"]
        )
        has_network = any(
            keyword in source.lower() for keyword in ["requests", "urllib", "http", "api"]
        )
        has_external = has_db or has_file_io or has_network

        # Check if async
        is_async = isinstance(node, ast.AsyncFunctionDef)

        return TestMetadata(
            name=node.name,
            file_path=str(file_path),
            imports=imports,
            fixtures_used=fixtures_used,
            has_db_access=has_db,
            has_file_io=has_file_io,
            has_network_calls=has_network,
            has_external_deps=has_external,
            is_async=is_async,
            line_number=node.lineno,
        )

    def _generate_optimization_plan(self) -> OptimizationPlan:
        """Generate comprehensive optimization plan."""

        parallelizable = self.find_parallelizable_tests()
        expensive_fixtures = self.identify_expensive_fixtures()
        mock_candidates = self.suggest_mocks()
        redundant = self.find_redundant_tests()

        # Estimate savings
        savings = 0.0

        # Parallel execution saves ~50% for parallelizable tests
        if parallelizable:
            savings += len(parallelizable) * 0.05  # Assume 50ms avg per test

        # Fixture optimization
        for fixture_name, cost_ms in expensive_fixtures.items():
            if cost_ms > 100:
                savings += (cost_ms / 1000.0) * 0.6  # 60% improvement with scope change

        # Mocking saves ~80% of external call time
        for candidate in mock_candidates:
            savings += 0.5  # Assume 500ms saved per mocked test

        return OptimizationPlan(
            parallelizable_tests=parallelizable,
            expensive_fixtures=expensive_fixtures,
            mock_candidates=mock_candidates,
            redundant_tests=redundant,
            estimated_savings_seconds=round(savings, 2),
        )

    def find_parallelizable_tests(self) -> list[str]:
        """
        Find tests that can safely run in parallel.

        Safe tests have:
        - No shared state (no database, no file I/O)
        - No external dependencies
        - Pure computation or mocked dependencies
        """
        parallelizable = []

        for test_id, metadata in self.test_metadata.items():
            # Check if test has no shared state
            is_safe = (
                not metadata.has_db_access
                and not metadata.has_file_io
                and not metadata.has_network_calls
            )

            # Check if fixtures are safe
            fixtures_safe = all(
                self.fixture_metadata.get(
                    fixture,
                    FixtureMetadata(
                        name=fixture,
                        file_path="",
                        scope="function",
                        has_db_setup=False,
                        has_network_setup=False,
                        estimated_cost_ms=0,
                    ),
                ).scope
                in ["function", "class"]
                for fixture in metadata.fixtures_used
            )

            if is_safe and fixtures_safe:
                parallelizable.append(test_id)

        return parallelizable

    def identify_expensive_fixtures(self) -> dict[str, float]:
        """Find fixtures taking >100ms."""
        expensive = {}

        for fixture_name, metadata in self.fixture_metadata.items():
            if metadata.estimated_cost_ms > 100:
                expensive[fixture_name] = round(metadata.estimated_cost_ms, 2)

        return expensive

    def suggest_mocks(self) -> list[dict[str, str]]:
        """Suggest where to add mocks to improve performance."""
        suggestions = []

        for test_id, metadata in self.test_metadata.items():
            # Suggest mocking for tests with external dependencies
            if metadata.has_network_calls:
                suggestions.append(
                    {
                        "test": test_id,
                        "target": "network calls",
                        "reason": "External API calls detected",
                        "estimated_savings": "500ms",
                    }
                )

            if metadata.has_db_access and not any(
                "mock" in fixture.lower() for fixture in metadata.fixtures_used
            ):
                suggestions.append(
                    {
                        "test": test_id,
                        "target": "database access",
                        "reason": "Real database usage detected",
                        "estimated_savings": "200ms",
                    }
                )

        return suggestions

    def find_redundant_tests(self) -> list[dict[str, str]]:
        """Identify potentially redundant test coverage."""
        redundant = []

        # Group tests by similarity (same fixtures, similar names)
        test_groups: dict[str, list[str]] = defaultdict(list)

        for test_id, metadata in self.test_metadata.items():
            # Create key from fixtures
            key = tuple(sorted(metadata.fixtures_used))
            test_groups[key].append(test_id)

        # Flag groups with many similar tests
        for key, tests in test_groups.items():
            if len(tests) > 5:
                redundant.append(
                    {
                        "group": f"tests using fixtures: {', '.join(key)}",
                        "count": str(len(tests)),
                        "suggestion": "Consider consolidating similar tests",
                    }
                )

        return redundant

    def generate_optimization_report(self, plan: OptimizationPlan) -> str:
        """Generate human-readable optimization report."""
        lines = [
            "# Test Suite Optimization Analysis",
            "",
            "## Parallelization Opportunities",
            "",
            f"**Found {len(plan.parallelizable_tests)} tests safe for parallel execution**",
            "",
        ]

        if plan.parallelizable_tests:
            lines.append("These tests have no shared state and can run concurrently:")
            lines.append("")
            for test in plan.parallelizable_tests[:10]:
                lines.append(f"- {test}")
            if len(plan.parallelizable_tests) > 10:
                lines.append(f"- ... and {len(plan.parallelizable_tests) - 10} more")
            lines.append("")
            lines.append("**Action:** Run with `pytest -n auto` to enable parallel execution")
        else:
            lines.append("⚠️ No tests identified as safe for parallelization")

        lines.extend(["", "## Expensive Fixtures", ""])

        if plan.expensive_fixtures:
            lines.append("| Fixture Name | Estimated Cost (ms) | Recommendation |")
            lines.append("|--------------|-------------------|----------------|")

            for fixture, cost in sorted(
                plan.expensive_fixtures.items(), key=lambda x: x[1], reverse=True
            ):
                rec = "Change to module/session scope" if cost > 200 else "Consider mocking"
                lines.append(f"| {fixture} | {cost:.1f} | {rec} |")
        else:
            lines.append("✅ No expensive fixtures detected")

        lines.extend(["", "## Mocking Opportunities", ""])

        if plan.mock_candidates:
            lines.append(f"**Found {len(plan.mock_candidates)} tests that should use mocks**")
            lines.append("")

            for candidate in plan.mock_candidates[:10]:
                lines.append(f"### {candidate['test']}")
                lines.append(f"- **Target:** {candidate['target']}")
                lines.append(f"- **Reason:** {candidate['reason']}")
                lines.append(f"- **Estimated Savings:** {candidate['estimated_savings']}")
                lines.append("")
        else:
            lines.append("✅ No obvious mocking opportunities")

        lines.extend(["", "## Redundant Test Coverage", ""])

        if plan.redundant_tests:
            for redundant in plan.redundant_tests:
                lines.append(f"- **{redundant['group']}**: {redundant['count']} tests")
                lines.append(f"  - {redundant['suggestion']}")
                lines.append("")
        else:
            lines.append("✅ No redundant test patterns detected")

        lines.extend(
            [
                "",
                "## Estimated Time Savings",
                "",
                f"**Total estimated savings: {plan.estimated_savings_seconds:.1f} seconds**",
                "",
                "### Implementation Priority",
                "",
                "1. **Quick Wins (1 day):**",
                "   - Enable pytest-xdist for parallel execution",
                "   - Mock external API calls",
                "",
                "2. **Medium Effort (2-3 days):**",
                "   - Optimize fixture scopes",
                "   - Replace real database with in-memory mocks",
                "",
                "3. **Long Term (1 week):**",
                "   - Consolidate redundant tests",
                "   - Implement smart test selection",
                "",
                "---",
                "",
                "*Generated by Agency Test Optimizer*",
            ]
        )

        return "\n".join(lines)


# CLI Interface
def main() -> int:
    """Command-line interface for test optimization."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze test suite and identify optimization opportunities"
    )
    parser.add_argument(
        "--test-dir", default="tests/", help="Directory containing tests (default: tests/)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/testing/TEST_OPTIMIZATION.md"),
        help="Output path for report",
    )

    args = parser.parse_args()

    # Run optimizer
    project_root = Path.cwd()
    optimizer = TestOptimizer(project_root)

    print("🔍 Analyzing test suite for optimization opportunities...")
    result = optimizer.analyze_tests(args.test_dir)

    if result.is_err():
        print(f"❌ Analysis failed: {result.unwrap_err()}")
        return 1

    plan = result.unwrap()

    # Generate report
    report = optimizer.generate_optimization_report(plan)

    # Save report
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)

        print("\n✅ Optimization analysis complete!")
        print(f"📊 Found {len(plan.parallelizable_tests)} parallelizable tests")
        print(f"🔧 Found {len(plan.expensive_fixtures)} expensive fixtures")
        print(f"🎯 Found {len(plan.mock_candidates)} mocking opportunities")
        print(f"💾 Estimated savings: {plan.estimated_savings_seconds:.1f}s")
        print(f"📝 Report saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
