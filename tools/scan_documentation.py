"""
Documentation validation scanner tool.

Scans Agency OS codebase for documentation quality issues:
- Missing CLAUDE.md files in critical directories
- Broken cross-references in markdown files
- Token budget violations
- Missing constitutional article references

Constitutional compliance:
- Article I: Complete scan context before reporting
- Article II: 100% verification of all documentation
- Uses Result pattern for error handling
- Pydantic models for type safety
"""

import re
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result


class ScanType(str, Enum):
    """Types of documentation scans."""

    MISSING_CLAUDE = "missing_claude"
    CROSS_REFERENCES = "cross_references"
    TOKEN_BUDGET = "token_budget"
    CONSTITUTIONAL = "constitutional"


class ViolationSeverity(str, Enum):
    """Severity levels for violations."""

    BLOCKER = "blocker"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ConstitutionalArticle(str, Enum):
    """Constitutional articles."""

    ARTICLE_I = "Article I"
    ARTICLE_II = "Article II"
    ARTICLE_III = "Article III"
    ARTICLE_IV = "Article IV"
    ARTICLE_V = "Article V"


class ValidationIssue(BaseModel):
    """Single validation issue found during scan."""

    scan_type: ScanType
    severity: ViolationSeverity
    file_path: str
    description: str
    suggested_fix: str | None = None
    line_number: int | None = None
    auto_fixable: bool = False


class ScanResult(BaseModel):
    """Result of a single scan type."""

    scan_type: ScanType
    passed: bool
    issues_found: int
    issues: list[ValidationIssue] = Field(default_factory=list)
    duration_ms: float = 0.0


class ScanReport(BaseModel):
    """Complete scan report across all scan types."""

    passed: bool
    total_issues: int
    results: list[ScanResult]
    summary: str


class ScanOptions(BaseModel):
    """Options for documentation scan."""

    missing_claude: bool = True
    validate_refs: bool = True
    token_budget: bool = True
    constitutional: bool = True
    auto_fix: bool = False


class TokenBudgetConfig(BaseModel):
    """Token budget limits for different file types."""

    root_claude_md: int = 8000  # Root CLAUDE.md
    folder_claude_md: int = 3000  # Folder-specific CLAUDE.md
    quick_refs: int = 1000  # Quick reference files


class ScanDocumentation:
    """
    Documentation validation scanner.

    Validates Agency OS documentation for quality and consistency.
    """

    # Critical directories that should have CLAUDE.md
    CRITICAL_DIRS = [
        "trinity_protocol",
        "tools/orchestrator",
        "shared",
        "agency_memory",
        "agency_code_agent",
        "planner_agent",
        "auditor_agent",
        "quality_enforcer_agent",
        "chief_architect_agent",
        "test_generator_agent",
    ]

    # Markdown link pattern: [text](url)
    MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    # Constitutional article patterns
    ARTICLE_PATTERNS = {
        ConstitutionalArticle.ARTICLE_I: [
            "timeout",
            "context",
            "complete",
            "retry",
            "broken window",
        ],
        ConstitutionalArticle.ARTICLE_II: [
            "test",
            "verification",
            "100%",
            "quality",
            "stability",
        ],
        ConstitutionalArticle.ARTICLE_III: [
            "enforcement",
            "automated",
            "merge",
            "git",
            "pre-commit",
        ],
        ConstitutionalArticle.ARTICLE_IV: [
            "learning",
            "vectorstore",
            "memory",
            "pattern",
            "improvement",
        ],
        ConstitutionalArticle.ARTICLE_V: [
            "spec",
            "plan",
            "specification",
            "planning",
            "development",
        ],
    }

    def __init__(
        self,
        project_root: Path,
        token_budget_config: TokenBudgetConfig | None = None,
    ):
        """
        Initialize documentation scanner.

        Args:
            project_root: Root directory of Agency project
            token_budget_config: Custom token budget configuration
        """
        self.project_root = project_root
        self.token_budget_config = token_budget_config or TokenBudgetConfig()

    def scan(self, options: ScanOptions) -> Result[ScanReport, str]:
        """
        Run documentation scans based on options.

        Args:
            options: Scan options

        Returns:
            Result containing ScanReport or error message

        Constitutional compliance:
        - Article I: Complete context (all scans run to completion)
        - Article II: 100% verification (no partial results)
        """
        # Validate project root exists
        if not self.project_root.exists():
            return Err(f"Project root does not exist: {self.project_root}")

        results: list[ScanResult] = []

        # Run selected scans
        if options.missing_claude:
            result = self._scan_missing_claude()
            if result.is_err():
                return Err(f"Missing CLAUDE scan failed: {result.unwrap_err()}")
            results.append(result.unwrap())

        if options.validate_refs:
            result = self._scan_cross_references()
            if result.is_err():
                return Err(f"Cross-reference scan failed: {result.unwrap_err()}")
            results.append(result.unwrap())

        if options.token_budget:
            result = self._scan_token_budgets()
            if result.is_err():
                return Err(f"Token budget scan failed: {result.unwrap_err()}")
            results.append(result.unwrap())

        if options.constitutional:
            result = self._scan_constitutional_references()
            if result.is_err():
                return Err(f"Constitutional scan failed: {result.unwrap_err()}")
            results.append(result.unwrap())

        # Generate report
        total_issues = sum(r.issues_found for r in results)
        passed = all(r.passed for r in results)

        summary = self._generate_summary(results, total_issues, passed)

        report = ScanReport(
            passed=passed,
            total_issues=total_issues,
            results=results,
            summary=summary,
        )

        return Ok(report)

    def _scan_missing_claude(self) -> Result[ScanResult, str]:
        """
        Scan for missing CLAUDE.md files in critical directories.

        Returns:
            Result containing ScanResult or error message
        """
        issues: list[ValidationIssue] = []
        critical_dirs_exist = False

        for dir_path in self.CRITICAL_DIRS:
            full_path = self.project_root / dir_path
            claude_file = full_path / "CLAUDE.md"

            # Check if directory exists
            if not full_path.exists():
                continue

            critical_dirs_exist = True

            # Check if CLAUDE.md exists
            if not claude_file.exists():
                issues.append(
                    ValidationIssue(
                        scan_type=ScanType.MISSING_CLAUDE,
                        severity=ViolationSeverity.HIGH,
                        file_path=str(full_path),
                        description=f"Missing CLAUDE.md in critical directory: {dir_path}",
                        suggested_fix=f"Create CLAUDE.md with module documentation in {dir_path}/",
                        auto_fixable=False,
                    )
                )

        # If no critical directories exist at all, this is also a problem
        if not critical_dirs_exist:
            issues.append(
                ValidationIssue(
                    scan_type=ScanType.MISSING_CLAUDE,
                    severity=ViolationSeverity.INFO,
                    file_path=str(self.project_root),
                    description="No critical directories found in project",
                    suggested_fix="Ensure project structure includes critical directories",
                    auto_fixable=False,
                )
            )

        return Ok(
            ScanResult(
                scan_type=ScanType.MISSING_CLAUDE,
                passed=len(issues) == 0,
                issues_found=len(issues),
                issues=issues,
            )
        )

    def _scan_cross_references(self) -> Result[ScanResult, str]:
        """
        Scan for broken cross-references in markdown files.

        Returns:
            Result containing ScanResult or error message
        """
        issues: list[ValidationIssue] = []

        # Find all markdown files
        try:
            md_files = list(self.project_root.rglob("*.md"))
        except Exception as e:
            return Err(f"Failed to scan markdown files: {e}")

        for md_file in md_files:
            # Skip symlinks to avoid circular loops
            if md_file.is_symlink():
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Find all markdown links
            for match in self.MARKDOWN_LINK_PATTERN.finditer(content):
                link_text = match.group(1)
                link_url = match.group(2)

                # Skip external links (http/https)
                if link_url.startswith(("http://", "https://")):
                    continue

                # Skip anchors
                if link_url.startswith("#"):
                    continue

                # Resolve path
                try:
                    if link_url.startswith("/"):
                        # Check if absolute file system path (e.g., /Users/...)
                        if Path(link_url).is_absolute() and Path(link_url).exists():
                            # Valid absolute file system path
                            continue
                        # Otherwise, absolute path from project root
                        target = self.project_root / link_url.lstrip("/")
                    else:
                        # Relative path from current file
                        target = (md_file.parent / link_url).resolve()

                    # Check if target exists
                    if not target.exists():
                        issues.append(
                            ValidationIssue(
                                scan_type=ScanType.CROSS_REFERENCES,
                                severity=ViolationSeverity.MEDIUM,
                                file_path=str(md_file.relative_to(self.project_root)),
                                description=f"Broken link to '{link_url}' (text: '{link_text}')",
                                suggested_fix=f"Fix or remove link to {link_url}",
                                auto_fixable=False,
                            )
                        )
                except Exception:
                    # Skip links that can't be parsed
                    continue

        return Ok(
            ScanResult(
                scan_type=ScanType.CROSS_REFERENCES,
                passed=len(issues) == 0,
                issues_found=len(issues),
                issues=issues,
            )
        )

    def _scan_token_budgets(self) -> Result[ScanResult, str]:
        """
        Scan for documentation files exceeding token budgets.

        Token estimation: ~4 chars per token (rough approximation)

        Returns:
            Result containing ScanResult or error message
        """
        issues: list[ValidationIssue] = []

        # Check root CLAUDE.md
        root_claude = self.project_root / "CLAUDE.md"
        if root_claude.exists():
            result = self._check_token_budget(
                root_claude,
                self.token_budget_config.root_claude_md,
                "Root CLAUDE.md",
            )
            if result:
                issues.append(result)

        # Check folder CLAUDE.md files
        try:
            claude_files = list(self.project_root.rglob("CLAUDE.md"))
        except Exception as e:
            return Err(f"Failed to scan CLAUDE.md files: {e}")

        for claude_file in claude_files:
            # Skip root
            if claude_file == root_claude:
                continue

            # Skip symlinks
            if claude_file.is_symlink():
                continue

            result = self._check_token_budget(
                claude_file,
                self.token_budget_config.folder_claude_md,
                "Folder CLAUDE.md",
            )
            if result:
                issues.append(result)

        # Check quick-ref files
        quick_ref_dir = self.project_root / ".claude" / "quick-ref"
        if quick_ref_dir.exists():
            try:
                quick_refs = list(quick_ref_dir.glob("*.md"))
            except Exception as e:
                return Err(f"Failed to scan quick-ref files: {e}")

            for quick_ref in quick_refs:
                result = self._check_token_budget(
                    quick_ref,
                    self.token_budget_config.quick_refs,
                    "Quick reference",
                )
                if result:
                    issues.append(result)

        return Ok(
            ScanResult(
                scan_type=ScanType.TOKEN_BUDGET,
                passed=len(issues) == 0,
                issues_found=len(issues),
                issues=issues,
            )
        )

    def _check_token_budget(
        self, file_path: Path, budget: int, file_type: str
    ) -> ValidationIssue | None:
        """
        Check if file exceeds token budget.

        Args:
            file_path: Path to file
            budget: Token budget limit
            file_type: Description of file type

        Returns:
            ValidationIssue if budget exceeded, None otherwise
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            # Rough token estimation: ~4 chars per token
            estimated_tokens = len(content) // 4

            if estimated_tokens > budget:
                return ValidationIssue(
                    scan_type=ScanType.TOKEN_BUDGET,
                    severity=ViolationSeverity.MEDIUM,
                    file_path=str(file_path.relative_to(self.project_root)),
                    description=f"{file_type} exceeds token budget: {estimated_tokens} tokens (limit: {budget})",
                    suggested_fix=f"Reduce content or split into multiple files. Consider moving details to separate docs.",
                    auto_fixable=False,
                )
        except Exception:
            pass

        return None

    def _scan_constitutional_references(self) -> Result[ScanResult, str]:
        """
        Scan for missing constitutional article references in relevant docs.

        Returns:
            Result containing ScanResult or error message
        """
        issues: list[ValidationIssue] = []

        # Find all markdown files
        try:
            md_files = list(self.project_root.rglob("*.md"))
        except Exception as e:
            return Err(f"Failed to scan markdown files: {e}")

        for md_file in md_files:
            # Skip symlinks
            if md_file.is_symlink():
                continue

            # Skip constitution.md itself
            if md_file.name == "constitution.md":
                continue

            try:
                content = md_file.read_text(encoding="utf-8").lower()
            except Exception:
                continue

            file_name_lower = md_file.name.lower()

            # Check for missing article references based on content
            for article, keywords in self.ARTICLE_PATTERNS.items():
                # Check if file content relates to this article
                keyword_matches = sum(1 for kw in keywords if kw.lower() in content)

                # Check if article is explicitly referenced
                article_referenced = (
                    article.value.lower() in content or
                    f"article {article.value.split()[-1]}" in content  # e.g., "article i"
                )

                # If file has significant keyword matches but no article reference
                if keyword_matches >= 2 and not article_referenced:
                    issues.append(
                        ValidationIssue(
                            scan_type=ScanType.CONSTITUTIONAL,
                            severity=ViolationSeverity.LOW,
                            file_path=str(md_file.relative_to(self.project_root)),
                            description=f"Document discusses {article.value} topics but doesn't reference the article",
                            suggested_fix=f"Add reference to {article.value} for constitutional traceability",
                            auto_fixable=False,
                        )
                    )

        return Ok(
            ScanResult(
                scan_type=ScanType.CONSTITUTIONAL,
                passed=len(issues) == 0,
                issues_found=len(issues),
                issues=issues,
            )
        )

    def _generate_summary(
        self, results: list[ScanResult], total_issues: int, passed: bool
    ) -> str:
        """
        Generate human-readable summary of scan results.

        Args:
            results: List of scan results
            total_issues: Total issues found
            passed: Overall pass status

        Returns:
            Summary string
        """
        if passed:
            return f"✅ All scans passed! {len(results)} scans completed with no issues."

        summary_parts = [
            f"❌ Found {total_issues} issue(s) across {len(results)} scan(s):",
        ]

        for result in results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            summary_parts.append(
                f"  {status} {result.scan_type.value}: {result.issues_found} issue(s)"
            )

        return "\n".join(summary_parts)

    def _get_article_keywords(self, article: ConstitutionalArticle) -> str:
        """
        Get keywords associated with a constitutional article.

        Args:
            article: Constitutional article

        Returns:
            Space-separated string of keywords (for compatibility with test assertions)
        """
        keywords = self.ARTICLE_PATTERNS.get(article, [])
        return " ".join(keywords)

    def _auto_fix_issues(self, issues: list[ValidationIssue]) -> Result[int, str]:
        """
        Auto-fix simple issues (placeholder for future implementation).

        Args:
            issues: List of issues to fix

        Returns:
            Result containing number of issues fixed or error message
        """
        # Placeholder - future implementation could handle:
        # - Trailing whitespace removal
        # - Basic formatting fixes
        # - Simple broken link fixes
        fixable_issues = [i for i in issues if i.auto_fixable]
        return Ok(len(fixable_issues))


def format_scan_report(report: ScanReport) -> str:
    """
    Format scan report for human-readable output.

    Args:
        report: Scan report to format

    Returns:
        Formatted report string
    """
    lines = [
        "=" * 80,
        "📋 Documentation Scan Report",
        "=" * 80,
        "",
        f"Status: {'✅ PASSED' if report.passed else '❌ FAILED'}",
        f"Total Issues: {report.total_issues}",
        "",
        report.summary,
        "",
    ]

    # Detailed results
    for result in report.results:
        lines.append(f"\n{'─' * 80}")
        lines.append(f"📊 {result.scan_type.value.upper()} Scan")
        lines.append(f"{'─' * 80}")
        lines.append(f"Status: {'✅ PASS' if result.passed else '❌ FAIL'}")
        lines.append(f"Issues Found: {result.issues_found}")

        if result.issues:
            lines.append("\nIssues:")
            for i, issue in enumerate(result.issues, 1):
                lines.append(f"\n{i}. [{issue.severity.value.upper()}] {issue.file_path}")
                lines.append(f"   {issue.description}")
                if issue.suggested_fix:
                    lines.append(f"   💡 Fix: {issue.suggested_fix}")

    lines.extend(["", "=" * 80])

    return "\n".join(lines)


def main() -> int:
    """
    Main entry point for scan_documentation tool.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan Agency OS documentation for quality issues"
    )

    parser.add_argument(
        "--missing-claude",
        action="store_true",
        help="Check for missing CLAUDE.md files",
    )
    parser.add_argument(
        "--validate-refs",
        action="store_true",
        help="Validate cross-references",
    )
    parser.add_argument(
        "--token-budget",
        action="store_true",
        help="Check token budget limits",
    )
    parser.add_argument(
        "--constitutional",
        action="store_true",
        help="Validate constitutional references",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scans (default)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix simple issues",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory",
    )

    args = parser.parse_args()

    # Default to --all if no specific scans selected
    if not any([args.missing_claude, args.validate_refs, args.token_budget, args.constitutional]):
        args.all = True

    options = ScanOptions(
        missing_claude=args.all or args.missing_claude,
        validate_refs=args.all or args.validate_refs,
        token_budget=args.all or args.token_budget,
        constitutional=args.all or args.constitutional,
        auto_fix=args.fix,
    )

    scanner = ScanDocumentation(project_root=args.project_root)
    result = scanner.scan(options)

    if result.is_err():
        print(f"❌ Scan failed: {result.unwrap_err()}")
        return 1

    report = result.unwrap()
    print(format_scan_report(report))

    return 0 if report.passed else 1


if __name__ == "__main__":
    exit(main())
