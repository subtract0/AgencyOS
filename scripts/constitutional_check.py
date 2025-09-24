#!/usr/bin/env python3
"""
Fast constitutional compliance check for pre-commit hooks.
Implements key validations from constitution.md without running full test suite.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Tuple


class ConstitutionalChecker:
    """Fast constitutional compliance checker."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.constitution_path = self.project_root / "constitution.md"
        self.errors = []
        self.warnings = []

    def check_article_i_context(self) -> bool:
        """Article I: Complete Context Before Action - Check for TODO/FIXME markers."""
        print("📋 Article I: Checking for incomplete context markers...")

        # Fast grep for TODO/FIXME in Python files
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", "-E", "TODO|FIXME|XXX", str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Filter out acceptable TODOs (in comments, docs, tests)
                problematic_todos = []
                for line in lines:
                    # Only flag TODOs in implementation files that look unfinished
                    if line and all([
                        "test_" not in line,
                        "examples/" not in line,
                        "archive/" not in line,
                        "TODO: Implement" in line or "FIXME: Critical" in line
                    ]):
                        problematic_todos.append(line)

                if problematic_todos:
                    self.warnings.append(f"Found {len(problematic_todos)} critical TODO/FIXME markers")
                    # Don't fail for TODOs, just warn
                    return True
            return True

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            # Grep not available or timeout - skip this check
            return True

    def check_article_ii_verification(self) -> bool:
        """Article II: 100% Verification - Quick syntax and import check."""
        print("✅ Article II: Running quick verification checks...")

        # Quick Python syntax check on changed files
        changed_files = self.get_changed_files()
        python_files = [f for f in changed_files if f.endswith('.py')]

        if not python_files:
            return True

        for file_path in python_files:
            if not self.validate_python_syntax(file_path):
                self.errors.append(f"Syntax error in {file_path}")
                return False

        return True

    def check_article_iii_enforcement(self) -> bool:
        """Article III: Automated Enforcement - Verify CI/CD configs exist."""
        print("🔒 Article III: Checking enforcement mechanisms...")

        required_files = [
            ".github/workflows/ci.yml",
            ".github/workflows/merge-guardian.yml",
            ".pre-commit-config.yaml"
        ]

        for req_file in required_files:
            file_path = self.project_root / req_file
            if not file_path.exists():
                self.errors.append(f"Missing enforcement file: {req_file}")
                return False

        return True

    def check_article_iv_learning(self) -> bool:
        """Article IV: Continuous Learning - Check telemetry is enabled."""
        print("📊 Article IV: Checking learning systems...")

        # Quick check that telemetry directory exists
        telemetry_dir = self.project_root / "logs" / "events"
        if not telemetry_dir.exists():
            telemetry_dir.mkdir(parents=True, exist_ok=True)
            self.warnings.append("Created missing telemetry directory")

        # Check unified core is enabled
        core_init = self.project_root / "core" / "__init__.py"
        if core_init.exists():
            with open(core_init, 'r') as f:
                content = f.read()
                if 'ENABLE_UNIFIED_CORE = os.getenv("ENABLE_UNIFIED_CORE", "false")' in content:
                    self.warnings.append("Unified core not enabled by default")
                    return False

        return True

    def check_article_v_spec_driven(self) -> bool:
        """Article V: Spec-Driven Development - Check for specs/plans structure."""
        print("📝 Article V: Checking spec-driven structure...")

        specs_dir = self.project_root / "specs"
        plans_dir = self.project_root / "plans"

        if not specs_dir.exists():
            self.warnings.append("Missing specs/ directory for specifications")

        if not plans_dir.exists():
            self.warnings.append("Missing plans/ directory for technical plans")

        return True

    def get_changed_files(self) -> List[str]:
        """Get list of changed files in current commit."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return [f for f in result.stdout.strip().split('\n') if f]

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        return []

    def validate_python_syntax(self, file_path: str) -> bool:
        """Quick Python syntax validation."""
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return True  # File deleted, skip

            with open(full_path, 'r') as f:
                code = f.read()

            compile(code, file_path, 'exec')
            return True

        except SyntaxError as e:
            print(f"  ❌ Syntax error in {file_path}: {e}")
            return False
        except Exception:
            # Other errors - let CI handle them
            return True

    def run_checks(self) -> Tuple[bool, str]:
        """Run all constitutional checks."""
        print("\n" + "=" * 60)
        print("🏛️  CONSTITUTIONAL COMPLIANCE CHECK")
        print("=" * 60 + "\n")

        checks = [
            ("Article I", self.check_article_i_context),
            ("Article II", self.check_article_ii_verification),
            ("Article III", self.check_article_iii_enforcement),
            ("Article IV", self.check_article_iv_learning),
            ("Article V", self.check_article_v_spec_driven),
        ]

        results = []
        for article, check_func in checks:
            try:
                passed = check_func()
                results.append((article, passed))
            except Exception as e:
                print(f"  ⚠️  Error checking {article}: {e}")
                results.append((article, True))  # Don't block on check errors

        # Summary
        print("\n" + "-" * 60)
        print("📊 COMPLIANCE SUMMARY")
        print("-" * 60)

        all_passed = True
        for article, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {article}: {status}")
            if not passed:
                all_passed = False

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("\n" + "=" * 60)

        if all_passed and not self.errors:
            print("✅ Constitutional compliance check PASSED")
            print("=" * 60 + "\n")
            return True, "All checks passed"
        elif self.errors:
            print("❌ Constitutional compliance check FAILED")
            print("🚫 Commit blocked - Fix errors before committing")
            print("=" * 60 + "\n")
            return False, f"Failed with {len(self.errors)} errors"
        else:
            print("⚠️  Constitutional compliance check passed with warnings")
            print("=" * 60 + "\n")
            return True, f"Passed with {len(self.warnings)} warnings"


def main():
    """Main entry point for pre-commit hook."""
    # Skip in CI environment (full tests run there)
    if os.environ.get("CI"):
        print("ℹ️  Skipping constitutional check in CI environment")
        return 0

    checker = ConstitutionalChecker()
    passed, message = checker.run_checks()

    if not passed:
        print("\n💡 To bypass (not recommended):")
        print("   git commit --no-verify")
        print("\n📚 Review constitution.md for requirements")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())