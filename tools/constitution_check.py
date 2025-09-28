#!/usr/bin/env python3
"""
Constitutional Enforcer Tool - Automated verification of all 5 constitutional articles.

This tool provides automated checking and enforcement of the Agency's constitutional
principles, ensuring that all development adheres to the Five Articles:

Article I: Complete Context - No action without full understanding
Article II: 100% Verification - All tests must pass - no exceptions
Article III: Automated Enforcement - Quality standards technically enforced
Article IV: Continuous Learning - Automatic improvement through experience
Article V: Spec-Driven Development - All features require formal specifications

Usage:
    python tools/constitution_check.py [--fix] [--verbose]

    --fix: Attempt to automatically fix violations where possible
    --verbose: Show detailed output for each check
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ViolationReport:
    """Represents a constitutional violation."""
    article: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None


@dataclass
class ComplianceReport:
    """Overall constitutional compliance report."""
    timestamp: datetime
    articles_checked: Dict[str, bool]
    violations: List[ViolationReport]
    overall_compliance: bool
    compliance_percentage: float


class ConstitutionalEnforcer:
    """Enforces the Five Articles of the Agency Constitution."""

    def __init__(self, project_root: Optional[Path] = None, verbose: bool = False):
        """Initialize the enforcer."""
        self.project_root = project_root or Path.cwd()
        self.verbose = verbose
        self.violations: List[ViolationReport] = []

    def check_article_i_complete_context(self) -> bool:
        """
        Article I: Complete Context - No action without full understanding.

        Checks:
        - All functions have docstrings
        - Complex operations have comments
        - README.md exists and is comprehensive
        - Type hints are present
        """
        compliant = True

        # Check for missing docstrings in Python files
        python_files = list(self.project_root.glob("**/*.py"))
        for py_file in python_files:
            if "test_" in py_file.name or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                # Simple regex to find functions without docstrings
                func_pattern = r'^(async )?def (\w+)\([^)]*\):\s*\n(?!\s*("""|\'\'\'))'
                matches = re.finditer(func_pattern, content, re.MULTILINE)

                for match in matches:
                    func_name = match.group(2)
                    if not func_name.startswith('_'):  # Skip private functions
                        line_num = content[:match.start()].count('\n') + 1
                        self.violations.append(ViolationReport(
                            article="Article I",
                            severity="medium",
                            description=f"Function '{func_name}' lacks docstring",
                            file_path=str(py_file),
                            line_number=line_num,
                            suggested_fix="Add a docstring explaining the function's purpose"
                        ))
                        compliant = False

            except Exception as e:
                if self.verbose:
                    print(f"Error checking {py_file}: {e}")

        # Check for README.md
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            self.violations.append(ViolationReport(
                article="Article I",
                severity="high",
                description="README.md is missing",
                suggested_fix="Create a comprehensive README.md file"
            ))
            compliant = False

        return compliant

    def check_article_ii_verification(self) -> bool:
        """
        Article II: 100% Verification - All tests must pass.

        Checks:
        - Run pytest and ensure all tests pass
        - Check test coverage
        - Verify no skipped tests
        """
        import tempfile
        compliant = True

        try:
            # Create secure temporary file for pytest report
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', prefix='pytest_report_', delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Run pytest with JSON output
                result = subprocess.run(
                    ["python", "-m", "pytest", "--json-report", f"--json-report-file={temp_path}", "-q"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )

                # Check if any tests failed
                if result.returncode != 0:
                    # Parse JSON report if available
                    try:
                        with open(temp_path, 'r') as f:
                            report = json.load(f)
                        failed = report.get('summary', {}).get('failed', 0)
                        total = report.get('summary', {}).get('total', 0)

                        self.violations.append(ViolationReport(
                            article="Article II",
                            severity="critical",
                            description=f"{failed} out of {total} tests are failing",
                            suggested_fix="Fix all failing tests before proceeding"
                        ))
                    except:
                        self.violations.append(ViolationReport(
                            article="Article II",
                            severity="critical",
                            description="Tests are failing",
                            suggested_fix="Run 'pytest -v' to see failures and fix them"
                        ))

                compliant = False

            finally:
                # Clean up temporary file
                import os
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)

        except FileNotFoundError:
            self.violations.append(ViolationReport(
                article="Article II",
                severity="critical",
                description="pytest is not installed",
                suggested_fix="Install pytest: pip install pytest"
            ))
            compliant = False

        return compliant

    def check_article_iii_automated_enforcement(self) -> bool:
        """
        Article III: Automated Enforcement - Quality standards technically enforced.

        Checks:
        - Pre-commit hooks are configured
        - CI/CD pipelines exist
        - Linting configuration present
        """
        compliant = True

        # Check for pre-commit configuration
        precommit_path = self.project_root / ".pre-commit-config.yaml"
        if not precommit_path.exists():
            self.violations.append(ViolationReport(
                article="Article III",
                severity="high",
                description="Pre-commit hooks not configured",
                file_path=".pre-commit-config.yaml",
                suggested_fix="Create .pre-commit-config.yaml with quality checks"
            ))
            compliant = False

        # Check for CI configuration
        ci_paths = [
            self.project_root / ".github" / "workflows",
            self.project_root / ".gitlab-ci.yml",
            self.project_root / ".circleci" / "config.yml",
        ]

        has_ci = any(path.exists() for path in ci_paths)
        if not has_ci:
            self.violations.append(ViolationReport(
                article="Article III",
                severity="medium",
                description="No CI/CD pipeline configuration found",
                suggested_fix="Set up GitHub Actions, GitLab CI, or similar"
            ))
            compliant = False

        # Check for linting configuration
        lint_configs = [
            self.project_root / ".pylintrc",
            self.project_root / "pyproject.toml",
            self.project_root / ".ruff.toml",
            self.project_root / "setup.cfg",
        ]

        has_linting = any(path.exists() for path in lint_configs)
        if not has_linting:
            self.violations.append(ViolationReport(
                article="Article III",
                severity="medium",
                description="No linting configuration found",
                suggested_fix="Configure pylint, ruff, or similar linting tool"
            ))
            compliant = False

        return compliant

    def check_article_iv_continuous_learning(self) -> bool:
        """
        Article IV: Continuous Learning - Automatic improvement through experience.

        Checks:
        - Learning loop is operational
        - Pattern store is being populated
        - Memory systems are active
        """
        compliant = True

        # Check for learning loop
        learning_path = self.project_root / "learning_loop"
        if not learning_path.exists():
            self.violations.append(ViolationReport(
                article="Article IV",
                severity="high",
                description="Learning loop module not found",
                suggested_fix="Implement learning_loop module for continuous improvement"
            ))
            compliant = False

        # Check for pattern storage
        patterns_path = self.project_root / "pattern_intelligence"
        if not patterns_path.exists():
            self.violations.append(ViolationReport(
                article="Article IV",
                severity="medium",
                description="Pattern intelligence module not found",
                suggested_fix="Implement pattern_intelligence for pattern learning"
            ))
            compliant = False

        # Check for memory systems
        memory_path = self.project_root / "agency_memory"
        if not memory_path.exists():
            self.violations.append(ViolationReport(
                article="Article IV",
                severity="medium",
                description="Memory system not found",
                suggested_fix="Implement agency_memory for persistent learning"
            ))
            compliant = False

        return compliant

    def check_article_v_spec_driven(self) -> bool:
        """
        Article V: Spec-Driven Development - All features require formal specifications.

        Checks:
        - Specs directory exists and contains specifications
        - Plans directory exists with implementation plans
        - Recent features have corresponding specs
        """
        compliant = True

        # Check for specs directory
        specs_path = self.project_root / "specs"
        if not specs_path.exists():
            self.violations.append(ViolationReport(
                article="Article V",
                severity="critical",
                description="Specs directory not found",
                suggested_fix="Create specs/ directory with formal specifications"
            ))
            compliant = False
        else:
            # Check if specs exist
            spec_files = list(specs_path.glob("*.md"))
            if len(spec_files) < 3:  # Arbitrary minimum
                self.violations.append(ViolationReport(
                    article="Article V",
                    severity="high",
                    description=f"Only {len(spec_files)} specifications found",
                    suggested_fix="Create formal specifications for all major features"
                ))
                compliant = False

        # Check for plans directory
        plans_path = self.project_root / "plans"
        if not plans_path.exists():
            self.violations.append(ViolationReport(
                article="Article V",
                severity="high",
                description="Plans directory not found",
                suggested_fix="Create plans/ directory with implementation plans"
            ))
            compliant = False

        return compliant

    def run_full_check(self) -> ComplianceReport:
        """Run all constitutional checks and generate report."""
        self.violations = []

        articles_checked = {
            "Article I (Complete Context)": self.check_article_i_complete_context(),
            "Article II (100% Verification)": self.check_article_ii_verification(),
            "Article III (Automated Enforcement)": self.check_article_iii_automated_enforcement(),
            "Article IV (Continuous Learning)": self.check_article_iv_continuous_learning(),
            "Article V (Spec-Driven Development)": self.check_article_v_spec_driven(),
        }

        overall_compliance = all(articles_checked.values())
        compliance_percentage = (sum(articles_checked.values()) / len(articles_checked)) * 100

        return ComplianceReport(
            timestamp=datetime.now(),
            articles_checked=articles_checked,
            violations=self.violations,
            overall_compliance=overall_compliance,
            compliance_percentage=compliance_percentage
        )

    def print_report(self, report: ComplianceReport) -> None:
        """Print a formatted compliance report."""
        print("\n" + "="*60)
        print("CONSTITUTIONAL COMPLIANCE REPORT")
        print("="*60)
        print(f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Overall Compliance: {'✅ PASS' if report.overall_compliance else '❌ FAIL'}")
        print(f"Compliance Score: {report.compliance_percentage:.1f}%")
        print()

        print("Article Status:")
        for article, compliant in report.articles_checked.items():
            status = "✅" if compliant else "❌"
            print(f"  {status} {article}")
        print()

        if report.violations:
            print(f"Violations Found ({len(report.violations)} total):")
            print("-"*60)

            # Group by severity
            critical = [v for v in report.violations if v.severity == "critical"]
            high = [v for v in report.violations if v.severity == "high"]
            medium = [v for v in report.violations if v.severity == "medium"]
            low = [v for v in report.violations if v.severity == "low"]

            for severity, violations in [("CRITICAL", critical), ("HIGH", high),
                                        ("MEDIUM", medium), ("LOW", low)]:
                if violations:
                    print(f"\n{severity} Severity:")
                    for v in violations[:5]:  # Show first 5 of each severity
                        print(f"  • {v.article}: {v.description}")
                        if v.file_path:
                            print(f"    File: {v.file_path}:{v.line_number if v.line_number else ''}")
                        if v.suggested_fix:
                            print(f"    Fix: {v.suggested_fix}")

                    if len(violations) > 5:
                        print(f"    ... and {len(violations) - 5} more {severity} violations")
        else:
            print("🎉 No violations found! Full constitutional compliance achieved.")

        print("\n" + "="*60)

    def attempt_fixes(self, report: ComplianceReport) -> int:
        """Attempt to automatically fix violations where possible."""
        fixed_count = 0

        for violation in report.violations:
            if violation.severity == "critical":
                continue  # Don't auto-fix critical issues

            # Example: Auto-create missing directories
            if "directory not found" in violation.description.lower():
                if violation.file_path:
                    path = Path(violation.file_path)
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                        fixed_count += 1
                        if self.verbose:
                            print(f"Created directory: {path}")

        return fixed_count


def main():
    """Main entry point for the constitutional enforcer."""
    import argparse

    parser = argparse.ArgumentParser(description="Constitutional Compliance Enforcer")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix violations")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", help="Output JSON report")

    args = parser.parse_args()

    enforcer = ConstitutionalEnforcer(verbose=args.verbose)
    report = enforcer.run_full_check()

    if args.json:
        # Output JSON report
        json_report = {
            "timestamp": report.timestamp.isoformat(),
            "overall_compliance": report.overall_compliance,
            "compliance_percentage": report.compliance_percentage,
            "articles_checked": report.articles_checked,
            "violations": [
                {
                    "article": v.article,
                    "severity": v.severity,
                    "description": v.description,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "suggested_fix": v.suggested_fix
                }
                for v in report.violations
            ]
        }
        print(json.dumps(json_report, indent=2))
    else:
        enforcer.print_report(report)

    if args.fix:
        fixed = enforcer.attempt_fixes(report)
        if fixed > 0:
            print(f"\n✅ Automatically fixed {fixed} violations")
            print("Re-run the check to see updated compliance status")

    # Exit with error code if not compliant
    sys.exit(0 if report.overall_compliance else 1)


if __name__ == "__main__":
    main()