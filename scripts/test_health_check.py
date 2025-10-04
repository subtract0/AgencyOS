#!/usr/bin/env python3
"""Test health check script for Agency OS.

This script performs comprehensive health checks on the test suite to prevent
collection failures and improve reliability. It validates test files, checks
dependencies, and reports any issues found.
"""

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path


class TestHealthChecker:
    """Comprehensive test health checker for the Agency OS test suite."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.test_paths = [
            self.project_root / "tests",
        ]
        self.issues: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []

    def add_issue(self, file_path: str, issue_type: str, message: str, severity: str = "error"):
        """Add an issue to the tracking lists."""
        issue = {"file": file_path, "type": issue_type, "message": message, "severity": severity}

        if severity == "error":
            self.issues.append(issue)
        else:
            self.warnings.append(issue)

    def find_test_files(self) -> list[Path]:
        """Find all test files in the project."""
        test_files = []

        for test_path in self.test_paths:
            if test_path.exists():
                # Find all Python test files
                test_files.extend(test_path.rglob("test_*.py"))
                test_files.extend(test_path.rglob("*_test.py"))

        return sorted(test_files)

    def check_syntax(self, file_path: Path) -> bool:
        """Check if a Python file has valid syntax."""
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            ast.parse(source, filename=str(file_path))
            return True

        except SyntaxError as e:
            self.add_issue(
                str(file_path), "syntax_error", f"Syntax error at line {e.lineno}: {e.msg}"
            )
            return False
        except Exception as e:
            self.add_issue(str(file_path), "parsing_error", f"Failed to parse file: {str(e)}")
            return False

    def check_imports(self, file_path: Path) -> bool:
        """Check if all imports in a test file are available."""
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            has_issues = False

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._check_module_exists(alias.name):
                            self.add_issue(
                                str(file_path),
                                "import_error",
                                f"Cannot import module: {alias.name}",
                                "warning",
                            )
                            has_issues = True

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if not self._check_module_exists(node.module):
                            self.add_issue(
                                str(file_path),
                                "import_error",
                                f"Cannot import from module: {node.module}",
                                "warning",
                            )
                            has_issues = True

            return not has_issues

        except Exception as e:
            self.add_issue(
                str(file_path),
                "import_check_error",
                f"Failed to check imports: {str(e)}",
                "warning",
            )
            return False

    def _check_module_exists(self, module_name: str) -> bool:
        """Check if a module can be imported."""
        try:
            # Skip relative imports and special modules
            if module_name.startswith(".") or module_name in ["__future__"]:
                return True

            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False

    def check_pytest_collection(self) -> bool:
        """Check if pytest can collect all tests."""
        try:
            # Run pytest in collection-only mode
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                # Parse the error output for specific issues
                error_lines = result.stdout + result.stderr
                self.add_issue(
                    "pytest_collection",
                    "collection_failure",
                    f"Pytest collection failed:\n{error_lines}",
                )
                return False

            # Check for collection warnings
            if "warnings summary" in result.stdout or "warning" in result.stdout.lower():
                self.add_issue(
                    "pytest_collection",
                    "collection_warning",
                    f"Pytest collection has warnings:\n{result.stdout}",
                    "warning",
                )

            return True

        except subprocess.TimeoutExpired:
            self.add_issue(
                "pytest_collection",
                "collection_timeout",
                "Pytest collection timed out after 60 seconds",
            )
            return False
        except Exception as e:
            self.add_issue(
                "pytest_collection",
                "collection_error",
                f"Failed to run pytest collection: {str(e)}",
            )
            return False

    def check_test_dependencies(self) -> bool:
        """Check if test dependencies are available."""
        required_packages = ["pytest", "pytest-asyncio", "pytest-cov", "pytest-mock"]

        missing_packages = []

        for package in required_packages:
            try:
                spec = importlib.util.find_spec(package.replace("-", "_"))
                if spec is None:
                    missing_packages.append(package)
            except (ImportError, ModuleNotFoundError):
                missing_packages.append(package)

        if missing_packages:
            self.add_issue(
                "dependencies",
                "missing_packages",
                f"Missing test dependencies: {', '.join(missing_packages)}",
            )
            return False

        return True

    def check_test_markers(self) -> bool:
        """Check for proper test markers and configurations."""
        pytest_ini = self.project_root / "pytest.ini"

        if not pytest_ini.exists():
            self.add_issue(
                "configuration",
                "missing_config",
                "pytest.ini configuration file not found",
                "warning",
            )
            return False

        try:
            with open(pytest_ini) as f:
                config_content = f.read()

            # Check for required markers
            if "markers" not in config_content:
                self.add_issue(
                    str(pytest_ini),
                    "missing_markers",
                    "No test markers defined in pytest.ini",
                    "warning",
                )

            return True

        except Exception as e:
            self.add_issue(
                str(pytest_ini), "config_error", f"Failed to read pytest.ini: {str(e)}", "warning"
            )
            return False

    def check_test_structure(self) -> bool:
        """Check test file structure and naming conventions."""
        test_files = self.find_test_files()
        has_issues = False

        for test_file in test_files:
            # Check naming convention
            if not (test_file.name.startswith("test_") or test_file.name.endswith("_test.py")):
                self.add_issue(
                    str(test_file),
                    "naming_convention",
                    "Test file doesn't follow naming convention (test_*.py or *_test.py)",
                    "warning",
                )
                has_issues = True

            # Check if file is empty
            try:
                if test_file.stat().st_size == 0:
                    self.add_issue(str(test_file), "empty_file", "Test file is empty", "warning")
                    has_issues = True
            except Exception:
                pass

        return not has_issues

    def run_health_check(self) -> bool:
        """Run all health checks and return True if all pass."""
        print("🔍 Running test health check...")

        # Find all test files
        test_files = self.find_test_files()
        print(f"📁 Found {len(test_files)} test files")

        if not test_files:
            self.add_issue("test_discovery", "no_tests", "No test files found in the project")
            return False

        # Check dependencies first
        print("📦 Checking test dependencies...")
        self.check_test_dependencies()

        # Check configuration
        print("⚙️  Checking test configuration...")
        self.check_test_markers()

        # Check test structure
        print("🏗️  Checking test structure...")
        self.check_test_structure()

        # Check syntax for each test file
        print("🔍 Checking syntax of test files...")
        syntax_ok = True
        for test_file in test_files:
            if not self.check_syntax(test_file):
                syntax_ok = False

        # Check imports for each test file
        print("📥 Checking imports in test files...")
        for test_file in test_files:
            self.check_imports(test_file)

        # Check pytest collection (only if syntax is OK)
        if syntax_ok:
            print("🧪 Checking pytest collection...")
            self.check_pytest_collection()
        else:
            self.add_issue(
                "pytest_collection", "skipped", "Skipped collection check due to syntax errors"
            )

        return len(self.issues) == 0

    def generate_report(self) -> str:
        """Generate a detailed health check report."""
        report = []
        report.append("=" * 60)
        report.append("TEST HEALTH CHECK REPORT")
        report.append("=" * 60)

        if not self.issues and not self.warnings:
            report.append("✅ All checks passed! Test suite is healthy.")
            return "\n".join(report)

        if self.issues:
            report.append(f"\n❌ ERRORS FOUND ({len(self.issues)}):")
            report.append("-" * 40)
            for issue in self.issues:
                report.append(f"File: {issue['file']}")
                report.append(f"Type: {issue['type']}")
                report.append(f"Message: {issue['message']}")
                report.append("")

        if self.warnings:
            report.append(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            report.append("-" * 40)
            for warning in self.warnings:
                report.append(f"File: {warning['file']}")
                report.append(f"Type: {warning['type']}")
                report.append(f"Message: {warning['message']}")
                report.append("")

        # Summary
        report.append("=" * 60)
        report.append("SUMMARY:")
        report.append(f"- Errors: {len(self.issues)}")
        report.append(f"- Warnings: {len(self.warnings)}")

        if self.issues:
            report.append("\n❌ Test suite has critical issues that need to be fixed.")
        else:
            report.append("\n✅ No critical issues found, but some warnings exist.")

        return "\n".join(report)


def main() -> int:
    """Main entry point for the test health check."""
    checker = TestHealthChecker()

    try:
        success = checker.run_health_check()
        report = checker.generate_report()

        print("\n" + report)

        # Save report to file
        report_file = checker.project_root / "logs" / "test_health_report.txt"
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, "w") as f:
            f.write(report)

        print(f"\n📄 Report saved to: {report_file}")

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️  Health check interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error during health check: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
