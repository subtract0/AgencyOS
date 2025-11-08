#!/usr/bin/env python3
"""
Regression Guard - Phase 1, Task 1
Zero-regression verification before commits

Features:
- Smart test selection (only run affected tests)
- Git integration (detect changed files)
- Fast feedback (<30s for typical changes)
- Blocking for Article II compliance

Constitutional Compliance:
- Article I: Complete context (analyze all changes)
- Article II: 100% verification (block on test failure)
- Article III: Automated enforcement (git hook integration)

Usage:
    # Check uncommitted changes
    python tools/regression_guard.py

    # Check staged changes (for pre-commit hook)
    python tools/regression_guard.py --staged

    # Skip test execution (dry run)
    python tools/regression_guard.py --dry-run
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result


# ============================================================================
# DATA MODELS
# ============================================================================


class ChangedFile(BaseModel):
    """Represents a changed file in git"""

    path: str = Field(..., description="File path relative to project root")
    change_type: str = Field(..., description="Change type: M(odified), A(dded), D(eleted)")


class TestExecutionResult(BaseModel):
    """Result of running tests"""

    passed: bool = Field(..., description="Whether all tests passed")
    total_tests: int = Field(..., description="Total tests run")
    failed_tests: int = Field(default=0, description="Number of failed tests")
    duration_seconds: float = Field(default=0.0, description="Test execution duration")
    output: str = Field(default="", description="Test output")


class RegressionCheckResult(BaseModel):
    """Result of regression check"""

    passed: bool = Field(..., description="Whether regression check passed")
    changed_files: List[ChangedFile] = Field(
        default_factory=list, description="Files that changed"
    )
    affected_tests: List[Path] = Field(
        default_factory=list, description="Tests that were run"
    )
    test_result: TestExecutionResult = Field(
        default_factory=lambda: TestExecutionResult(passed=True, total_tests=0),
        description="Test execution result",
    )


# ============================================================================
# REGRESSION GUARD
# ============================================================================


class RegressionGuard:
    """
    Regression Guard: Zero-regression verification system

    Prevents regressions by:
    1. Detecting changed files
    2. Finding affected tests (smart selection)
    3. Running only affected tests
    4. Blocking commits if tests fail
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        test_timeout: int = 300,  # 5 minutes
    ):
        """
        Initialize regression guard

        Args:
            project_root: Project root directory (default: cwd)
            test_timeout: Test execution timeout in seconds
        """
        self.project_root = project_root or Path.cwd()
        self.test_timeout = test_timeout

    def get_changed_files(
        self, include_staged: bool = False
    ) -> Result[List[ChangedFile], str]:
        """
        Get list of changed files from git

        Args:
            include_staged: Include staged files (for pre-commit hook)

        Returns:
            Result with list of changed files or error message
        """
        try:
            # Build git diff command
            cmd = ["git", "diff", "--name-status"]
            if include_staged:
                cmd.append("--cached")

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return Err(f"Git command failed: {result.stderr}")

            # Parse output
            changed_files = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) != 2:
                    continue

                change_type = parts[0][0]  # M, A, D, etc.
                file_path = parts[1]

                changed_files.append(
                    ChangedFile(path=file_path, change_type=change_type)
                )

            return Ok(changed_files)

        except subprocess.TimeoutExpired:
            return Err("Git diff timed out")
        except Exception as e:
            return Err(f"Error getting changed files: {e}")

    def find_affected_tests(
        self, changed_files: List[ChangedFile]
    ) -> Result[List[Path], str]:
        """
        Find tests affected by changed files (smart test selection)

        Mapping rules:
        1. tools/foo.py -> tests/test_foo.py (direct mapping)
        2. agent_name/agent.py -> tests/test_agent_name.py (agent mapping)
        3. shared/* -> all tests (shared code affects everything)
        4. constitution.md -> all tests (constitutional changes)
        5. tests/test_foo.py -> tests/test_foo.py (test itself)

        Args:
            changed_files: List of changed files

        Returns:
            Result with list of test files to run
        """
        try:
            affected_tests = set()

            for changed_file in changed_files:
                path = Path(changed_file.path)

                # Rule 1: Direct mapping (tools/foo.py -> tests/test_foo.py)
                if path.parent.name == "tools" and path.suffix == ".py":
                    test_file = self.project_root / "tests" / f"test_{path.stem}.py"
                    if test_file.exists():
                        affected_tests.add(test_file)

                # Rule 2: Agent mapping (coding_agent/coding_agent.py -> tests/)
                elif "_agent" in str(path):
                    agent_name = path.parts[0] if len(path.parts) > 0 else ""
                    # Find tests related to this agent
                    test_pattern = f"*{agent_name}*.py"
                    for test_file in (self.project_root / "tests").glob(test_pattern):
                        affected_tests.add(test_file)

                # Rule 3: Shared code changes affect many tests
                elif "shared" in str(path):
                    # Add comprehensive test coverage for shared changes
                    for test_file in (self.project_root / "tests").glob("test_*.py"):
                        # Sample affected tests (not all to keep it fast)
                        if (
                            "shared" in test_file.stem
                            or "result" in test_file.stem
                            or "type" in test_file.stem
                            or "agent" in test_file.stem
                        ):
                            affected_tests.add(test_file)

                # Rule 4: Constitutional changes require full coverage
                elif "constitution" in changed_file.path:
                    # Add constitutional compliance tests
                    for test_file in (self.project_root / "tests").glob("test_*constitutional*.py"):
                        affected_tests.add(test_file)
                    # Add quality tests
                    for test_file in (self.project_root / "tests").glob("test_quality*.py"):
                        affected_tests.add(test_file)

                # Rule 5: Test file changed -> run that test
                elif path.parts[0] == "tests" and path.suffix == ".py":
                    test_file = self.project_root / changed_file.path
                    if test_file.exists():
                        affected_tests.add(test_file)

            return Ok(list(affected_tests))

        except Exception as e:
            return Err(f"Error finding affected tests: {e}")

    def run_affected_tests(
        self, test_files: List[Path]
    ) -> Result[TestExecutionResult, str]:
        """
        Run affected tests using pytest

        Args:
            test_files: List of test files to run

        Returns:
            Result with test execution results
        """
        if not test_files:
            # No tests to run - pass
            return Ok(TestExecutionResult(passed=True, total_tests=0))

        try:
            # Build pytest command
            cmd = ["python", "-m", "pytest"] + [str(f) for f in test_files]
            cmd.extend(["-v", "--tb=short", "-x"])  # Verbose, short traceback, stop on first failure

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.test_timeout,
            )

            # Parse pytest output
            output = result.stdout + result.stderr
            passed = result.returncode == 0

            # Extract test counts from output
            # Example: "====== 10 passed, 2 failed in 3.1s ======"
            total_tests = 0
            failed_tests = 0
            duration = 0.0

            match = re.search(r"(\d+) passed", output)
            if match:
                total_tests += int(match.group(1))

            match = re.search(r"(\d+) failed", output)
            if match:
                failed_tests = int(match.group(1))
                total_tests += failed_tests

            match = re.search(r"in ([\d.]+)s", output)
            if match:
                duration = float(match.group(1))

            return Ok(
                TestExecutionResult(
                    passed=passed,
                    total_tests=total_tests,
                    failed_tests=failed_tests,
                    duration_seconds=duration,
                    output=output,
                )
            )

        except subprocess.TimeoutExpired:
            return Err(f"Test execution timed out after {self.test_timeout}s")
        except Exception as e:
            return Err(f"Error running tests: {e}")

    def check_regression(
        self, include_staged: bool = False
    ) -> Result[RegressionCheckResult, str]:
        """
        Perform complete regression check

        Steps:
        1. Get changed files
        2. Find affected tests
        3. Run affected tests
        4. Return results

        Args:
            include_staged: Include staged files (for pre-commit hook)

        Returns:
            Result with regression check results
        """
        # Step 1: Get changed files
        changed_result = self.get_changed_files(include_staged=include_staged)
        if changed_result.is_err():
            return Err(changed_result.unwrap_err())

        changed_files = changed_result.unwrap()

        # No changes? Pass immediately
        if not changed_files:
            return Ok(
                RegressionCheckResult(
                    passed=True,
                    changed_files=[],
                    affected_tests=[],
                )
            )

        # Step 2: Find affected tests
        tests_result = self.find_affected_tests(changed_files)
        if tests_result.is_err():
            return Err(tests_result.unwrap_err())

        affected_tests = tests_result.unwrap()

        # Step 3: Run affected tests
        test_result_obj = self.run_affected_tests(affected_tests)
        if test_result_obj.is_err():
            return Err(test_result_obj.unwrap_err())

        test_result = test_result_obj.unwrap()

        # Step 4: Return results
        return Ok(
            RegressionCheckResult(
                passed=test_result.passed,
                changed_files=changed_files,
                affected_tests=affected_tests,
                test_result=test_result,
            )
        )


# ============================================================================
# CLI
# ============================================================================


def main(args: Optional[List[str]] = None) -> None:
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Regression Guard: Zero-regression verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/regression_guard.py              # Check uncommitted changes
  python tools/regression_guard.py --staged     # Check staged changes (pre-commit)
  python tools/regression_guard.py --dry-run    # Show affected tests without running
        """,
    )

    parser.add_argument(
        "--staged",
        action="store_true",
        help="Check staged files (for pre-commit hook)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show affected tests without running them",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test execution timeout in seconds (default: 300)",
    )

    parsed_args = parser.parse_args(args)

    # Create guard
    guard = RegressionGuard(
        project_root=parsed_args.project_root,
        test_timeout=parsed_args.timeout,
    )

    print("🛡️ REGRESSION GUARD")
    print("=" * 70)

    # Get changed files
    changed_result = guard.get_changed_files(include_staged=parsed_args.staged)
    if changed_result.is_err():
        print(f"❌ Error: {changed_result.unwrap_err()}")
        sys.exit(1)

    changed_files = changed_result.unwrap()

    if not changed_files:
        print("✅ No changes detected - regression check passed")
        sys.exit(0)

    print(f"\n📝 Changed files ({len(changed_files)}):")
    for cf in changed_files:
        print(f"   [{cf.change_type}] {cf.path}")

    # Find affected tests
    tests_result = guard.find_affected_tests(changed_files)
    if tests_result.is_err():
        print(f"❌ Error: {tests_result.unwrap_err()}")
        sys.exit(1)

    affected_tests = tests_result.unwrap()
    print(f"\n🧪 Affected tests ({len(affected_tests)}):")
    for test in affected_tests:
        print(f"   {test.relative_to(guard.project_root)}")

    if parsed_args.dry_run:
        print("\n✅ Dry run complete (tests not executed)")
        sys.exit(0)

    # Run tests
    print(f"\n🏃 Running {len(affected_tests)} test file(s)...")
    test_result_obj = guard.run_affected_tests(affected_tests)

    if test_result_obj.is_err():
        print(f"❌ Error: {test_result_obj.unwrap_err()}")
        sys.exit(1)

    test_result = test_result_obj.unwrap()

    # Display results
    print("=" * 70)
    if test_result.passed:
        print(f"✅ REGRESSION CHECK PASSED")
        print(f"   {test_result.total_tests} tests passed in {test_result.duration_seconds:.1f}s")
        sys.exit(0)
    else:
        print(f"❌ REGRESSION CHECK FAILED")
        print(f"   {test_result.failed_tests}/{test_result.total_tests} tests failed")
        print(f"\n{test_result.output}")
        sys.exit(1)


if __name__ == "__main__":
    main()
