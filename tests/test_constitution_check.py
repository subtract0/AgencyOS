#!/usr/bin/env python3
"""
Test suite for Constitutional Enforcer Tool.

Tests the automated verification of all 5 constitutional articles:
- Article I: Complete Context
- Article II: 100% Verification
- Article III: Automated Enforcement
- Article IV: Continuous Learning
- Article V: Spec-Driven Development
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

# Import the module under test
import sys
sys.path.append(str(Path(__file__).parent.parent))
from tools.constitution_check import (
    ConstitutionalEnforcer,
    ViolationReport,
    ComplianceReport,
)


class TestConstitutionalEnforcer:
    """Test suite for the Constitutional Enforcer."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def enforcer(self, temp_project):
        """Create an enforcer instance with test project."""
        return ConstitutionalEnforcer(project_root=temp_project, verbose=False)

    def test_enforcer_initialization(self):
        """Test that enforcer can be initialized properly."""
        enforcer = ConstitutionalEnforcer(verbose=True)
        assert enforcer is not None
        assert enforcer.verbose is True
        assert enforcer.violations == []
        assert enforcer.project_root == Path.cwd()

    def test_enforcer_custom_project_root(self, temp_project):
        """Test enforcer with custom project root."""
        enforcer = ConstitutionalEnforcer(project_root=temp_project)
        assert enforcer.project_root == temp_project

    def test_violation_report_creation(self):
        """Test creation of violation reports."""
        violation = ViolationReport(
            article="Article I",
            severity="critical",
            description="Missing complete context",
            file_path="/test/file.py",
            line_number=42,
            suggested_fix="Add proper documentation"
        )

        assert violation.article == "Article I"
        assert violation.severity == "critical"
        assert violation.description == "Missing complete context"
        assert violation.file_path == "/test/file.py"
        assert violation.line_number == 42
        assert violation.suggested_fix == "Add proper documentation"

    def test_compliance_report_creation(self):
        """Test creation of compliance reports."""
        timestamp = datetime.now()
        violations = [
            ViolationReport(
                article="Article I",
                severity="high",
                description="Test violation"
            )
        ]

        report = ComplianceReport(
            timestamp=timestamp,
            articles_checked={"Article I": False, "Article II": True},
            violations=violations,
            overall_compliance=False,
            compliance_percentage=50.0
        )

        assert report.timestamp == timestamp
        assert report.articles_checked["Article I"] is False
        assert report.articles_checked["Article II"] is True
        assert len(report.violations) == 1
        assert report.overall_compliance is False
        assert report.compliance_percentage == 50.0

    def test_article_i_complete_context_no_violations(self, temp_project, enforcer):
        """Test Article I check with compliant code."""
        # Create a Python file with proper docstrings
        test_file = temp_project / "test_module.py"
        test_file.write_text('''
"""Module docstring."""

def test_function():
    """Function docstring."""
    pass

class TestClass:
    """Class docstring."""

    def test_method(self):
        """Method docstring."""
        pass
''')

        # Check Article I compliance
        result = enforcer.check_article_i_complete_context()

        assert result is True
        assert len(enforcer.violations) == 0

    def test_article_i_complete_context_with_violations(self, temp_project, enforcer):
        """Test Article I check with non-compliant code."""
        # Create a Python file without docstrings
        test_file = temp_project / "bad_module.py"
        test_file.write_text('''
def function_without_docstring():
    pass

class ClassWithoutDocstring:
    def method_without_docstring(self):
        pass
''')

        # Check Article I compliance
        result = enforcer.check_article_i_complete_context()

        assert result is False
        assert len(enforcer.violations) > 0

        # Check that violations are for missing docstrings
        for violation in enforcer.violations:
            assert "docstring" in violation.description.lower()

    @patch('subprocess.run')
    def test_article_ii_verification_all_tests_pass(self, mock_run, enforcer):
        """Test Article II check when all tests pass."""
        # Mock successful test run
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="All tests passed",
            stderr=""
        )

        result = enforcer.check_article_ii_verification()

        assert result is True
        assert len(enforcer.violations) == 0
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_article_ii_verification_tests_fail(self, mock_run, enforcer):
        """Test Article II check when tests fail."""
        # Mock failed test run
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="1 test failed",
            stderr="Error in test"
        )

        result = enforcer.check_article_ii_verification()

        assert result is False
        assert len(enforcer.violations) > 0
        assert any("test" in v.description.lower() for v in enforcer.violations)

    @patch('subprocess.run')
    def test_article_iii_automated_enforcement_enabled(self, mock_run, temp_project, enforcer):
        """Test Article III check with enforcement enabled."""
        # Create pre-commit config
        precommit_file = temp_project / ".pre-commit-config.yaml"
        precommit_file.write_text("repos: []")

        # Create CI config
        ci_dir = temp_project / ".github" / "workflows"
        ci_dir.mkdir(parents=True, exist_ok=True)
        ci_file = ci_dir / "ci.yml"
        ci_file.write_text("name: CI")

        # Mock successful git hook check
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=".git/hooks/pre-commit",
            stderr=""
        )

        result = enforcer.check_article_iii_automated_enforcement()

        assert result is True
        assert len(enforcer.violations) == 0

    def test_article_iii_automated_enforcement_missing(self, temp_project, enforcer):
        """Test Article III check with missing enforcement."""
        # No pre-commit or CI configs
        result = enforcer.check_article_iii_automated_enforcement()

        assert result is False
        assert len(enforcer.violations) > 0
        assert any("pre-commit" in v.description.lower() or "ci" in v.description.lower()
                  for v in enforcer.violations)

    def test_article_iv_continuous_learning_present(self, temp_project, enforcer):
        """Test Article IV check with learning infrastructure."""
        # Create learning-related files
        learning_dir = temp_project / "learning_agent"
        learning_dir.mkdir(exist_ok=True)
        (learning_dir / "__init__.py").touch()

        logs_dir = temp_project / "logs" / "sessions"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Create memory store
        memory_dir = temp_project / "agency_memory"
        memory_dir.mkdir(exist_ok=True)

        result = enforcer.check_article_iv_continuous_learning()

        assert result is True
        assert len([v for v in enforcer.violations if v.article == "Article IV"]) == 0

    def test_article_iv_continuous_learning_missing(self, temp_project, enforcer):
        """Test Article IV check without learning infrastructure."""
        result = enforcer.check_article_iv_continuous_learning()

        assert result is False
        violations = [v for v in enforcer.violations if v.article == "Article IV"]
        assert len(violations) > 0

    def test_article_v_spec_driven_development_compliant(self, temp_project, enforcer):
        """Test Article V check with proper spec structure."""
        # Create specs directory
        specs_dir = temp_project / "specs"
        specs_dir.mkdir(exist_ok=True)

        # Create a spec file
        spec_file = specs_dir / "spec-001.md"
        spec_file.write_text('''
# Spec 001

## Goals
- Goal 1

## Non-Goals
- Non-goal 1

## Personas
- Developer

## Acceptance Criteria
- Criteria 1
''')

        # Create plans directory
        plans_dir = temp_project / "plans"
        plans_dir.mkdir(exist_ok=True)
        plan_file = plans_dir / "plan-001.md"
        plan_file.write_text("# Plan 001")

        result = enforcer.check_article_v_spec_driven()

        assert result is True
        violations = [v for v in enforcer.violations if v.article == "Article V"]
        assert len(violations) == 0

    def test_article_v_spec_driven_development_missing(self, temp_project, enforcer):
        """Test Article V check without spec structure."""
        result = enforcer.check_article_v_spec_driven()

        assert result is False
        violations = [v for v in enforcer.violations if v.article == "Article V"]
        assert len(violations) > 0
        assert any("specs" in v.description.lower() for v in violations)

    def test_full_compliance_check(self, temp_project):
        """Test full compliance check across all articles."""
        enforcer = ConstitutionalEnforcer(project_root=temp_project)

        with patch.object(enforcer, 'check_article_i_complete_context', return_value=True), \
             patch.object(enforcer, 'check_article_ii_verification', return_value=True), \
             patch.object(enforcer, 'check_article_iii_automated_enforcement', return_value=True), \
             patch.object(enforcer, 'check_article_iv_continuous_learning', return_value=True), \
             patch.object(enforcer, 'check_article_v_spec_driven', return_value=True):

            report = enforcer.check_compliance()

            assert report.overall_compliance is True
            assert report.compliance_percentage == 100.0
            assert all(report.articles_checked.values())
            assert len(report.violations) == 0

    def test_partial_compliance_check(self, temp_project):
        """Test partial compliance check."""
        enforcer = ConstitutionalEnforcer(project_root=temp_project)

        with patch.object(enforcer, 'check_article_i_complete_context', return_value=True), \
             patch.object(enforcer, 'check_article_ii_verification', return_value=False), \
             patch.object(enforcer, 'check_article_iii_automated_enforcement', return_value=True), \
             patch.object(enforcer, 'check_article_iv_continuous_learning', return_value=False), \
             patch.object(enforcer, 'check_article_v_spec_driven', return_value=True):

            # Add some mock violations
            enforcer.violations.append(
                ViolationReport(
                    article="Article II",
                    severity="critical",
                    description="Tests failing"
                )
            )

            report = enforcer.check_compliance()

            assert report.overall_compliance is False
            assert report.compliance_percentage == 60.0  # 3 out of 5
            assert report.articles_checked["Article I"] is True
            assert report.articles_checked["Article II"] is False
            assert len(report.violations) > 0

    def test_auto_fix_functionality(self, temp_project, enforcer):
        """Test auto-fix functionality."""
        # Create a file that needs fixing
        test_file = temp_project / "needs_fix.py"
        test_file.write_text("def function_without_docstring():\n    pass")

        with patch.object(enforcer, '_fix_missing_docstring') as mock_fix:
            enforcer.violations.append(
                ViolationReport(
                    article="Article I",
                    severity="high",
                    description="Missing docstring",
                    file_path=str(test_file),
                    line_number=1,
                    suggested_fix="Add docstring"
                )
            )

            fixed_count = enforcer.attempt_fixes()

            # Should attempt to fix but actual fixing is mocked
            mock_fix.assert_called()

    def test_report_generation(self, temp_project, enforcer):
        """Test report generation in different formats."""
        # Add some violations
        enforcer.violations.append(
            ViolationReport(
                article="Article I",
                severity="high",
                description="Test violation"
            )
        )

        report = enforcer.check_compliance()

        # Test text report
        text_report = enforcer.generate_report(report, format="text")
        assert "Constitutional Compliance Report" in text_report
        assert "Article I" in text_report
        assert "Test violation" in text_report

        # Test JSON report
        json_report = enforcer.generate_report(report, format="json")
        import json
        data = json.loads(json_report)
        assert "violations" in data
        assert len(data["violations"]) == 1

    def test_verbose_output(self, temp_project, capsys):
        """Test verbose output functionality."""
        enforcer = ConstitutionalEnforcer(project_root=temp_project, verbose=True)

        # Trigger some verbose output
        enforcer.check_article_i_complete_context()

        captured = capsys.readouterr()
        # Verbose mode should produce output
        assert len(captured.out) > 0 or len(captured.err) > 0

    def test_severity_levels(self):
        """Test different severity levels in violations."""
        severities = ["critical", "high", "medium", "low"]

        for severity in severities:
            violation = ViolationReport(
                article="Article I",
                severity=severity,
                description=f"{severity} violation"
            )
            assert violation.severity == severity

    def test_empty_project_handling(self, temp_project, enforcer):
        """Test handling of empty project directory."""
        # Run compliance check on empty project
        report = enforcer.check_compliance()

        # Should have violations but not crash
        assert report.overall_compliance is False
        assert len(report.violations) > 0
        assert report.compliance_percentage < 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])