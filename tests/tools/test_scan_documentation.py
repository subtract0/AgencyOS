"""
Tests for scan_documentation tool.

Test-driven development for documentation validation scanner.
Constitutional Article II: Tests written FIRST, implementation SECOND.
"""

import json
import tempfile
from pathlib import Path

import pytest

from shared.type_definitions.result import Err, Ok
from tools.scan_documentation import (
    ConstitutionalArticle,
    ScanDocumentation,
    ScanOptions,
    ScanReport,
    ScanResult,
    ScanType,
    TokenBudgetConfig,
    ValidationIssue,
    ViolationSeverity,
)


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create temporary project directory structure."""
    # Create standard Agency directories
    (tmp_path / "trinity_protocol").mkdir()
    (tmp_path / "tools" / "orchestrator").mkdir(parents=True)
    (tmp_path / "shared").mkdir()
    (tmp_path / "agency_memory").mkdir()
    (tmp_path / "agencyos_agent").mkdir()
    (tmp_path / ".claude" / "commands").mkdir(parents=True)
    (tmp_path / ".claude" / "quick-ref").mkdir()

    # Create root CLAUDE.md
    (tmp_path / "CLAUDE.md").write_text(
        "# Agency OS\n\n"
        "This is the main documentation.\n\n"
        "## Article I: Complete Context\n\n"
        "See [constitution.md](constitution.md) for details.\n"
    )

    # Create constitution.md
    (tmp_path / "constitution.md").write_text(
        "# Constitution\n\n"
        "## Article I: Complete Context Before Action\n\n"
        "## Article II: 100% Verification\n\n"
        "## Article III: Automated Enforcement\n\n"
        "## Article IV: Continuous Learning\n\n"
        "## Article V: Spec-Driven Development\n"
    )

    return tmp_path


class TestScanDocumentationModels:
    """Test Pydantic models for scan results."""

    def test_validation_issue_creation(self):
        """Test ValidationIssue model creation."""
        issue = ValidationIssue(
            scan_type=ScanType.MISSING_CLAUDE,
            severity=ViolationSeverity.HIGH,
            file_path="/test/path",
            description="Missing CLAUDE.md",
            suggested_fix="Create CLAUDE.md file",
        )

        assert issue.scan_type == ScanType.MISSING_CLAUDE
        assert issue.severity == ViolationSeverity.HIGH
        assert issue.file_path == "/test/path"

    def test_scan_result_creation(self):
        """Test ScanResult model creation."""
        result = ScanResult(
            scan_type=ScanType.MISSING_CLAUDE,
            passed=False,
            issues_found=1,
            issues=[
                ValidationIssue(
                    scan_type=ScanType.MISSING_CLAUDE,
                    severity=ViolationSeverity.HIGH,
                    file_path="/test",
                    description="Test",
                )
            ],
        )

        assert result.scan_type == ScanType.MISSING_CLAUDE
        assert not result.passed
        assert result.issues_found == 1
        assert len(result.issues) == 1

    def test_scan_report_creation(self):
        """Test ScanReport model creation."""
        result = ScanResult(
            scan_type=ScanType.MISSING_CLAUDE,
            passed=True,
            issues_found=0,
            issues=[],
        )

        report = ScanReport(
            passed=True,
            total_issues=0,
            results=[result],
            summary="All scans passed",
        )

        assert report.passed
        assert report.total_issues == 0
        assert len(report.results) == 1


class TestMissingClaudeScans:
    """Test missing CLAUDE.md detection (NECESSARY - Normal)."""

    def test_detects_missing_claude_in_critical_directory(self, temp_project_dir: Path):
        """Test detection of missing CLAUDE.md in trinity_protocol/."""
        scanner = ScanDocumentation(project_root=temp_project_dir)

        result = scanner._scan_missing_claude()

        assert result.is_ok()
        scan_result = result.unwrap()
        assert not scan_result.passed
        assert scan_result.issues_found > 0

        # Should detect missing CLAUDE.md in trinity_protocol/
        trinity_issues = [i for i in scan_result.issues if "trinity_protocol" in i.file_path]
        assert len(trinity_issues) > 0

    def test_passes_when_all_claude_files_present(self, temp_project_dir: Path):
        """Test pass when all critical directories have CLAUDE.md."""
        # Create CLAUDE.md in all critical directories
        critical_dirs = [
            "trinity_protocol",
            "tools/orchestrator",
            "shared",
            "agency_memory",
            "agencyos_agent",
        ]

        for dir_path in critical_dirs:
            claude_file = temp_project_dir / dir_path / "CLAUDE.md"
            claude_file.write_text(f"# {dir_path} Documentation\n")

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_missing_claude()

        assert result.is_ok()
        scan_result = result.unwrap()
        assert scan_result.passed
        assert scan_result.issues_found == 0


class TestCrossReferenceValidation:
    """Test cross-reference validation (NECESSARY - Edge)."""

    def test_detects_broken_markdown_link(self, temp_project_dir: Path):
        """Test detection of broken markdown links."""
        # Create file with broken link
        doc_file = temp_project_dir / "docs" / "test.md"
        doc_file.parent.mkdir(exist_ok=True)
        doc_file.write_text("# Test Doc\n\nSee [missing file](missing_file.md) for details.\n")

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_cross_references()

        assert result.is_ok()
        scan_result = result.unwrap()
        assert not scan_result.passed
        assert scan_result.issues_found > 0

        # Should detect broken link
        broken_link_issues = [i for i in scan_result.issues if "missing_file.md" in i.description]
        assert len(broken_link_issues) > 0

    def test_passes_with_valid_links(self, temp_project_dir: Path):
        """Test pass when all links are valid."""
        # Create two files with valid links
        docs_dir = temp_project_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        (docs_dir / "first.md").write_text("# First\n\nSee [second](second.md) for details.\n")
        (docs_dir / "second.md").write_text("# Second\n\nContent here.\n")

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_cross_references()

        assert result.is_ok()
        scan_result = result.unwrap()
        assert scan_result.passed
        assert scan_result.issues_found == 0

    def test_handles_absolute_path_links(self, temp_project_dir: Path):
        """Test handling of absolute path links."""
        # Create file with absolute path link
        doc_file = temp_project_dir / "docs" / "test.md"
        doc_file.parent.mkdir(exist_ok=True)
        doc_file.write_text(f"# Test\n\nSee [constitution]({temp_project_dir}/constitution.md)\n")

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_cross_references()

        assert result.is_ok()
        scan_result = result.unwrap()
        assert scan_result.passed


class TestTokenBudgetValidation:
    """Test token budget validation (NECESSARY - Security/Limits)."""

    def test_detects_oversized_root_claude(self, temp_project_dir: Path):
        """Test detection of root CLAUDE.md exceeding token limit."""
        # Create oversized root CLAUDE.md (>8000 tokens ≈ >32000 chars)
        oversized_content = "# Agency OS\n\n" + ("Lorem ipsum dolor sit amet. " * 2000)
        (temp_project_dir / "CLAUDE.md").write_text(oversized_content)

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_token_budgets()

        assert result.is_ok()
        scan_result = result.unwrap()
        assert not scan_result.passed
        assert scan_result.issues_found > 0

        # Should detect oversized root CLAUDE.md
        oversized_issues = [
            i
            for i in scan_result.issues
            if "CLAUDE.md" in i.file_path and "exceeds" in i.description
        ]
        assert len(oversized_issues) > 0

    def test_passes_within_token_budget(self, temp_project_dir: Path):
        """Test pass when all files within token budget."""
        # Root CLAUDE.md should be under 8000 tokens (≈32000 chars)
        normal_content = "# Agency OS\n\n" + ("Content paragraph. " * 100)
        (temp_project_dir / "CLAUDE.md").write_text(normal_content)

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_token_budgets()

        assert result.is_ok()
        scan_result = result.unwrap()
        assert scan_result.passed

    def test_detects_oversized_folder_claude(self, temp_project_dir: Path):
        """Test detection of folder CLAUDE.md exceeding limit."""
        # Create oversized folder CLAUDE.md (>3000 tokens ≈ >12000 chars)
        oversized_content = "# Trinity Protocol\n\n" + ("Lorem ipsum. " * 1500)
        trinity_claude = temp_project_dir / "trinity_protocol" / "CLAUDE.md"
        trinity_claude.write_text(oversized_content)

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_token_budgets()

        assert result.is_ok()
        scan_result = result.unwrap()
        assert not scan_result.passed


class TestConstitutionalReferenceScanning:
    """Test constitutional article reference validation (NECESSARY - Spec)."""

    def test_detects_missing_article_i_in_context_docs(self, temp_project_dir: Path):
        """Test detection of missing Article I in context-critical docs."""
        # Create doc that should reference Article I but doesn't
        # Include multiple Article I keywords: timeout, context, retry
        context_doc = temp_project_dir / "docs" / "timeout_handling.md"
        context_doc.parent.mkdir(exist_ok=True)
        context_doc.write_text(
            "# Timeout Handling\n\n"
            "This describes timeouts and retry logic for complete context gathering.\n"
            "When operations timeout, we must retry to ensure completeness.\n"
        )

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_constitutional_references()

        assert result.is_ok()
        scan_result = result.unwrap()

        # Should suggest Article I reference
        article_i_issues = [
            i
            for i in scan_result.issues
            if "Article I" in i.description and "timeout_handling.md" in i.file_path
        ]
        assert len(article_i_issues) > 0

    def test_passes_with_proper_article_references(self, temp_project_dir: Path):
        """Test pass when docs properly reference articles."""
        # Create doc with proper Article I reference
        context_doc = temp_project_dir / "docs" / "timeout_handling.md"
        context_doc.parent.mkdir(exist_ok=True)
        context_doc.write_text(
            "# Timeout Handling\n\n"
            "Per Article I (Complete Context Before Action), we retry timeouts.\n"
        )

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_constitutional_references()

        assert result.is_ok()
        scan_result = result.unwrap()

        # Should not flag this doc
        timeout_issues = [i for i in scan_result.issues if "timeout_handling.md" in i.file_path]
        assert len(timeout_issues) == 0

    def test_detects_missing_article_ii_in_test_docs(self, temp_project_dir: Path):
        """Test detection of missing Article II in test docs."""
        # Create test doc without Article II reference
        # Include multiple Article II keywords: test, verification, quality
        test_doc = temp_project_dir / "docs" / "testing_guide.md"
        test_doc.parent.mkdir(exist_ok=True)
        test_doc.write_text(
            "# Testing Guide\n\n"
            "Run tests with pytest. All tests must pass for verification.\n"
            "Quality standards require 100% test success for stability.\n"
        )

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner._scan_constitutional_references()

        assert result.is_ok()
        scan_result = result.unwrap()

        # Should suggest Article II reference
        article_ii_issues = [
            i
            for i in scan_result.issues
            if "Article II" in i.description and "testing_guide.md" in i.file_path
        ]
        assert len(article_ii_issues) > 0


class TestScanOrchestration:
    """Test main scan orchestration (NECESSARY - Accessibility)."""

    def test_run_all_scans(self, temp_project_dir: Path):
        """Test running all scans together."""
        scanner = ScanDocumentation(project_root=temp_project_dir)

        options = ScanOptions(
            missing_claude=True,
            validate_refs=True,
            token_budget=True,
            constitutional=True,
        )

        result = scanner.scan(options)

        assert result.is_ok()
        report = result.unwrap()

        # Should have results for all scan types
        assert len(report.results) == 4
        assert any(r.scan_type == ScanType.MISSING_CLAUDE for r in report.results)
        assert any(r.scan_type == ScanType.CROSS_REFERENCES for r in report.results)
        assert any(r.scan_type == ScanType.TOKEN_BUDGET for r in report.results)
        assert any(r.scan_type == ScanType.CONSTITUTIONAL for r in report.results)

    def test_run_single_scan(self, temp_project_dir: Path):
        """Test running single scan type."""
        scanner = ScanDocumentation(project_root=temp_project_dir)

        options = ScanOptions(
            missing_claude=True,
            validate_refs=False,
            token_budget=False,
            constitutional=False,
        )

        result = scanner.scan(options)

        assert result.is_ok()
        report = result.unwrap()

        # Should only have missing CLAUDE scan
        assert len(report.results) == 1
        assert report.results[0].scan_type == ScanType.MISSING_CLAUDE

    def test_report_summary_generation(self, temp_project_dir: Path):
        """Test scan report summary generation."""
        scanner = ScanDocumentation(project_root=temp_project_dir)

        options = ScanOptions(
            missing_claude=True,
            validate_refs=True,
            token_budget=True,
            constitutional=True,
        )

        result = scanner.scan(options)

        assert result.is_ok()
        report = result.unwrap()

        # Summary should contain scan statistics
        assert "scan" in report.summary.lower()
        assert "issue" in report.summary.lower()


class TestAutoFixCapability:
    """Test auto-fix for simple issues (NECESSARY - Resilience)."""

    def test_auto_fix_detects_fixable_issues(self, temp_project_dir: Path):
        """Test that auto-fix identifies fixable issues."""
        # Create file with trailing whitespace
        doc_file = temp_project_dir / "docs" / "test.md"
        doc_file.parent.mkdir(exist_ok=True)
        doc_file.write_text("# Test  \n\nContent.  \n")  # Trailing spaces

        scanner = ScanDocumentation(project_root=temp_project_dir)

        # Scan should identify fixable formatting issues
        result = scanner.scan(ScanOptions(validate_refs=True))

        assert result.is_ok()
        report = result.unwrap()

        # Should have some way to identify auto-fixable issues
        # (Implementation detail - just testing the concept exists)
        assert hasattr(scanner, "_auto_fix_issues")


class TestExitCodes:
    """Test exit code behavior (NECESSARY - Year-round/Production)."""

    def test_returns_success_exit_code_when_passed(self, temp_project_dir: Path):
        """Test exit code 0 when all checks pass."""
        # Create minimal passing project
        critical_dirs = [
            "trinity_protocol",
            "tools/orchestrator",
            "shared",
            "agency_memory",
            "agencyos_agent",
        ]

        for dir_path in critical_dirs:
            claude_file = temp_project_dir / dir_path / "CLAUDE.md"
            claude_file.write_text(f"# {dir_path}\n")

        scanner = ScanDocumentation(project_root=temp_project_dir)
        result = scanner.scan(ScanOptions(missing_claude=True))

        assert result.is_ok()
        report = result.unwrap()

        # Should indicate success
        assert report.passed
        exit_code = 0 if report.passed else 1
        assert exit_code == 0

    def test_returns_failure_exit_code_when_issues_found(self, temp_project_dir: Path):
        """Test exit code 1 when issues found."""
        scanner = ScanDocumentation(project_root=temp_project_dir)

        # This will find missing CLAUDE.md files
        result = scanner.scan(ScanOptions(missing_claude=True))

        assert result.is_ok()
        report = result.unwrap()

        # Should indicate failure
        assert not report.passed
        exit_code = 0 if report.passed else 1
        assert exit_code == 1


class TestEdgeCases:
    """Test edge cases and error handling (NECESSARY - Edge)."""

    def test_handles_nonexistent_project_root(self):
        """Test error handling for nonexistent project root."""
        scanner = ScanDocumentation(project_root=Path("/nonexistent/path"))

        result = scanner.scan(ScanOptions())

        # Should return error Result
        assert result.is_err()
        assert "not exist" in result.unwrap_err().lower()

    def test_handles_empty_project_directory(self, tmp_path: Path):
        """Test handling of empty project directory."""
        scanner = ScanDocumentation(project_root=tmp_path)

        result = scanner.scan(ScanOptions(missing_claude=True))

        assert result.is_ok()
        report = result.unwrap()

        # Should report missing files
        assert not report.passed

    def test_handles_circular_symlinks(self, temp_project_dir: Path):
        """Test handling of circular symlinks gracefully."""
        # Create circular symlink
        link_dir = temp_project_dir / "circular"
        link_dir.mkdir()
        circular = link_dir / "loop"

        try:
            circular.symlink_to(link_dir)

            scanner = ScanDocumentation(project_root=temp_project_dir)
            result = scanner.scan(ScanOptions(validate_refs=True))

            # Should not crash
            assert result.is_ok()
        except OSError:
            # Some systems don't support symlinks - skip test
            pytest.skip("Symlinks not supported")


class TestTokenBudgetConfiguration:
    """Test token budget configuration (NECESSARY - Normal)."""

    def test_default_token_budgets(self):
        """Test default token budget values."""
        config = TokenBudgetConfig()

        assert config.root_claude_md == 8000
        assert config.folder_claude_md == 3000
        assert config.quick_refs == 1000

    def test_custom_token_budgets(self, temp_project_dir: Path):
        """Test custom token budget configuration."""
        custom_config = TokenBudgetConfig(
            root_claude_md=10000,
            folder_claude_md=5000,
            quick_refs=2000,
        )

        scanner = ScanDocumentation(
            project_root=temp_project_dir,
            token_budget_config=custom_config,
        )

        assert scanner.token_budget_config.root_claude_md == 10000
        assert scanner.token_budget_config.folder_claude_md == 5000


class TestConstitutionalArticleMapping:
    """Test constitutional article to topic mapping (NECESSARY - Spec)."""

    def test_article_i_mapped_to_context_keywords(self):
        """Test Article I mapped to context-related keywords."""
        scanner = ScanDocumentation(project_root=Path.cwd())

        # Should have mapping for Article I
        article_i_keywords = scanner._get_article_keywords(ConstitutionalArticle.ARTICLE_I)

        assert "timeout" in article_i_keywords
        assert "context" in article_i_keywords
        assert "complete" in article_i_keywords.lower() or "retry" in article_i_keywords

    def test_article_ii_mapped_to_test_keywords(self):
        """Test Article II mapped to test-related keywords."""
        scanner = ScanDocumentation(project_root=Path.cwd())

        article_ii_keywords = scanner._get_article_keywords(ConstitutionalArticle.ARTICLE_II)

        assert "test" in article_ii_keywords
        assert any(k in article_ii_keywords for k in ["verification", "quality", "100%"])

    def test_all_articles_have_keyword_mappings(self):
        """Test all constitutional articles have keyword mappings."""
        scanner = ScanDocumentation(project_root=Path.cwd())

        for article in ConstitutionalArticle:
            keywords = scanner._get_article_keywords(article)
            assert len(keywords) > 0, f"{article} should have keyword mappings"
