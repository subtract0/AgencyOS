"""
AAA Tests for Leap 7 Completion Report Validation.

Constitutional Compliance:
- Article I: TDD - Tests written BEFORE implementation
- Article II: 100% verification - Comprehensive test coverage
- Article V: Spec-driven development - Traceability to mission/leap_7_test_driven_autonomy.json

NECESSARY Pattern Compliance:
- N: Normal operation - Valid report with all sections
- E: Edge cases - Missing sections, partial content
- C: Corner cases - Empty report, malformed Markdown
- E: Error conditions - Invalid metrics, incorrect format
- S: Security - No injection attacks via report content
- S: Stress - Large reports, many metrics
- A: Accessibility - Report structure readable
- R: Regression - Validate against leap 4 report format
- Y: Yield - Correct validation results

Verification Target: code_leap7_completion_report
"""

import re
from pathlib import Path

import pytest


class TestLeap7CompletionReportStructure:
    """Test completion report Markdown structure validation (NECESSARY: Normal)."""

    def test_report_contains_all_required_sections(self):
        """
        Test that Leap 7 completion report contains all mandatory sections.

        AAA Pattern:
        - Arrange: Define expected sections for leap completion reports
        - Act: Parse report Markdown and extract section headers
        - Assert: All required sections present in correct order
        """
        # Arrange: Expected sections based on leap_4_complete.md structure
        expected_sections = [
            "Executive Summary",
            "Implementation Details",
            "Test Suite Summary",
            "File Manifest",
            "Constitutional Compliance Validation",
            "Performance Metrics",
            "Next Steps",
            "Lessons Learned",
            "Conclusion",
        ]

        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        # Act: Parse report and extract section headers (## Level 2)
        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        report_content = report_path.read_text()
        section_headers = re.findall(r"^## (.+)$", report_content, re.MULTILINE)

        # Assert: All expected sections present
        for section in expected_sections:
            assert section in section_headers, f"Missing required section: {section}"

    def test_report_has_valid_markdown_structure(self):
        """
        Test that report uses valid Markdown hierarchy (h1 > h2 > h3).

        AAA Pattern:
        - Arrange: Load report file
        - Act: Extract all header levels
        - Assert: Header hierarchy is valid (no h4 before h3, etc.)
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Extract headers with levels
        report_content = report_path.read_text()
        headers = re.findall(r"^(#{1,6}) (.+)$", report_content, re.MULTILINE)

        # Assert: At least one h1 title, multiple h2 sections
        h1_count = sum(1 for level, _ in headers if level == "#")
        h2_count = sum(1 for level, _ in headers if level == "##")

        assert h1_count >= 1, "Report must have at least one h1 title"
        assert h2_count >= 5, "Report must have at least 5 h2 sections"

    def test_report_has_status_and_date_metadata(self):
        """
        Test that report includes status and date metadata at the top.

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for Status and Date fields in first 20 lines
        - Assert: Both fields present with valid values
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Extract first 20 lines (metadata section)
        report_content = report_path.read_text()
        lines = report_content.split("\n")[:20]
        first_section = "\n".join(lines)

        # Assert: Status and Date fields present
        assert re.search(r"\*\*Status\*\*:\s*✅\s*\*\*COMPLETE\*\*", first_section), "Status field missing or incorrect"
        assert re.search(r"\*\*Date\*\*:\s*\d{4}-\d{2}-\d{2}", first_section), "Date field missing or incorrect format"
        assert re.search(r"\*\*Leap\*\*:\s*Leap 7", first_section, re.IGNORECASE), "Leap number missing"


class TestLeap7MetricsValidation:
    """Test metrics accuracy in completion report (NECESSARY: Normal + Error)."""

    def test_report_contains_task_count_metrics(self):
        """
        Test that report includes accurate task count (26 tasks expected per mission file).

        AAA Pattern:
        - Arrange: Load mission file to get expected task count
        - Act: Parse report for task count metrics
        - Assert: Task count matches mission file (26 tasks total)
        """
        # Arrange: Load mission file
        mission_path = Path(__file__).parent.parent.parent / "missions" / "leap_7_test_driven_autonomy.json"
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Count tasks in mission file
        import json

        mission_data = json.loads(mission_path.read_text())
        total_tasks = sum(len(phase["tasks"]) for phase in mission_data["phases"])

        # Parse report for task count
        report_content = report_path.read_text()

        # Assert: Report mentions correct task count (26 tasks)
        assert str(total_tasks) in report_content, f"Report must mention {total_tasks} tasks"
        assert re.search(rf"\b{total_tasks}\s+tasks?\b", report_content, re.IGNORECASE), "Task count not found in report"

    def test_report_contains_test_pass_rate_metrics(self):
        """
        Test that report includes test pass rate (100% required per Article II).

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for test pass rate mentions
        - Assert: 100% pass rate mentioned (Article II compliance)
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report for test metrics
        report_content = report_path.read_text()

        # Assert: 100% pass rate mentioned
        assert re.search(r"100%\s+pass", report_content, re.IGNORECASE), "100% test pass rate not mentioned"
        assert "0 failures" in report_content or "zero failures" in report_content.lower(), "Zero failures not mentioned"

    def test_report_contains_cost_metrics_within_budget(self):
        """
        Test that report includes cost metrics within budget ($20 USD limit per mission).

        AAA Pattern:
        - Arrange: Load mission file for budget limit
        - Act: Parse report for cost metrics
        - Assert: Cost mentioned and within budget
        """
        # Arrange: Load mission file
        mission_path = Path(__file__).parent.parent.parent / "missions" / "leap_7_test_driven_autonomy.json"
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Get budget limit
        import json

        mission_data = json.loads(mission_path.read_text())
        budget_limit = mission_data["metadata"]["budget_limit_usd"]

        # Parse report for cost
        report_content = report_path.read_text()
        cost_matches = re.findall(r"\$(\d+(?:\.\d+)?)", report_content)

        # Assert: Cost metrics present and within budget
        assert len(cost_matches) > 0, "No cost metrics found in report"

        # Check that at least one cost value is mentioned in context of total cost
        total_cost_pattern = re.search(r"total.*cost.*\$(\d+(?:\.\d+)?)", report_content, re.IGNORECASE)
        if total_cost_pattern:
            total_cost = float(total_cost_pattern.group(1))
            assert total_cost <= budget_limit, f"Total cost ${total_cost} exceeds budget ${budget_limit}"

    def test_report_contains_new_tests_count(self):
        """
        Test that report includes count of new tests added in Leap 7.

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for new tests metrics
        - Assert: New tests count mentioned (expected ~10 test files)
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report for test count
        report_content = report_path.read_text()

        # Assert: New tests mentioned (10 Test tasks in mission)
        assert re.search(r"new test", report_content, re.IGNORECASE), "New tests not mentioned"
        assert re.search(r"\+\d+\s+tests?", report_content, re.IGNORECASE), "Test count increment not found"


class TestLeap7ConstitutionalCompliance:
    """Test constitutional compliance section (NECESSARY: Accessibility)."""

    def test_report_contains_all_five_articles(self):
        """
        Test that report validates all 5 constitutional articles.

        AAA Pattern:
        - Arrange: Define 5 articles to check
        - Act: Parse report for article mentions
        - Assert: All 5 articles referenced with compliance status
        """
        # Arrange: 5 Constitutional Articles
        articles = [
            "Article I",
            "Article II",
            "Article III",
            "Article IV",
            "Article V",
        ]

        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: All articles mentioned
        for article in articles:
            assert article in report_content, f"{article} not found in report"

    def test_report_shows_article_i_compliance(self):
        """
        Test that report validates Article I (Complete Context Before Action).

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for Article I section with retry logic mention
        - Assert: Article I compliance validated (retry logic implemented)
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: Article I compliance with retry logic
        assert "Article I" in report_content, "Article I not found"
        assert re.search(r"retry.*logic", report_content, re.IGNORECASE), "Retry logic not mentioned for Article I"

    def test_report_shows_article_ii_compliance(self):
        """
        Test that report validates Article II (100% Verification and Stability).

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for Article II section with 100% test pass mention
        - Assert: Article II compliance validated (100% test pass rate)
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: Article II compliance with 100% tests
        assert "Article II" in report_content, "Article II not found"
        assert re.search(r"100%.*test", report_content, re.IGNORECASE), "100% test pass not mentioned for Article II"

    def test_report_shows_article_v_compliance(self):
        """
        Test that report validates Article V (Spec-Driven Development).

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for Article V section with spec-kit mention
        - Assert: Article V compliance validated (spec-driven workflow)
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: Article V compliance with spec-driven
        assert "Article V" in report_content, "Article V not found"
        assert re.search(r"spec.*driven", report_content, re.IGNORECASE), "Spec-driven not mentioned for Article V"


class TestLeap7AchievementsSection:
    """Test achievements section content (NECESSARY: Yield)."""

    def test_report_lists_key_achievements(self):
        """
        Test that report lists all key achievements for Leap 7.

        AAA Pattern:
        - Arrange: Define expected achievements (8 components per mission)
        - Act: Parse report for achievements section
        - Assert: All key components mentioned
        """
        # Arrange: Expected components from mission file
        expected_components = [
            "IntentParser",
            "SpecGenerator",
            "ApprovalCheckpoint",
            "TDDGraphGenerator",
            "NECESSARYValidator",
            "TestVerificationGate",
            "PRCreator",
            "TwoStageOrchestrator",
        ]

        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: All components mentioned
        for component in expected_components:
            assert component in report_content, f"Key component not mentioned: {component}"

    def test_report_mentions_tdd_workflow_achievement(self):
        """
        Test that report highlights TDD workflow as key achievement.

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for TDD workflow mentions in achievements
        - Assert: TDD workflow highlighted as achievement
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: TDD workflow achievement
        assert re.search(r"TDD.*workflow", report_content, re.IGNORECASE), "TDD workflow not mentioned"
        assert re.search(r"two.*stage", report_content, re.IGNORECASE), "Two-stage workflow not mentioned"


class TestLeap7EdgeCases:
    """Test edge cases for report validation (NECESSARY: Edge cases)."""

    def test_report_handles_missing_sections_gracefully(self):
        """
        Test validation when report has missing sections.

        AAA Pattern:
        - Arrange: Create report with missing section
        - Act: Validate report structure
        - Assert: Validation detects missing section
        """
        # Arrange: Incomplete report content
        incomplete_report = """
# Leap 7 Complete: Test-Driven Autonomy

**Status**: ✅ **COMPLETE**
**Date**: 2025-10-11

## Executive Summary

Test content.

## Conclusion

Done.
"""

        # Act: Parse sections
        section_headers = re.findall(r"^## (.+)$", incomplete_report, re.MULTILINE)

        # Assert: Detect missing sections
        required_sections = [
            "Implementation Details",
            "Test Suite Summary",
            "Constitutional Compliance Validation",
        ]

        missing_sections = [s for s in required_sections if s not in section_headers]
        assert len(missing_sections) > 0, "Should detect missing sections"
        assert "Implementation Details" in missing_sections

    def test_report_validates_metric_format(self):
        """
        Test that metrics follow expected format (numbers with units).

        AAA Pattern:
        - Arrange: Define expected metric patterns
        - Act: Search report for metrics
        - Assert: Metrics match expected format
        """
        # Arrange: Expected metric patterns
        metric_patterns = [
            r"\d+\s+tasks?",  # Task count
            r"\d+\s+tests?",  # Test count
            r"\$\d+(?:\.\d+)?",  # Cost in USD
            r"\d+%\s+pass",  # Pass rate percentage
        ]

        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: At least 3 metric patterns found
        matches_found = sum(1 for pattern in metric_patterns if re.search(pattern, report_content, re.IGNORECASE))
        assert matches_found >= 3, f"Expected at least 3 metric patterns, found {matches_found}"

    def test_report_handles_empty_file_gracefully(self):
        """
        Test validation behavior with empty report file.

        AAA Pattern:
        - Arrange: Empty report content
        - Act: Attempt to parse sections
        - Assert: No sections found (graceful handling)
        """
        # Arrange: Empty report
        empty_report = ""

        # Act: Parse sections
        section_headers = re.findall(r"^## (.+)$", empty_report, re.MULTILINE)

        # Assert: No sections found
        assert len(section_headers) == 0, "Empty report should have no sections"


class TestLeap7NextStepsSection:
    """Test Next Steps section (NECESSARY: Regression)."""

    def test_report_includes_next_steps_section(self):
        """
        Test that report includes Next Steps section with Leap 8 proposal.

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for Next Steps section
        - Assert: Section present with future work mentioned
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: Next Steps section present
        assert re.search(r"##\s+Next Steps", report_content, re.IGNORECASE), "Next Steps section not found"

    def test_report_mentions_leap_8_or_future_work(self):
        """
        Test that report proposes future work or Leap 8 direction.

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for Leap 8 or future work mentions
        - Assert: Future direction mentioned
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: Future work mentioned
        has_leap_8 = "Leap 8" in report_content or "leap 8" in report_content.lower()
        has_future_work = re.search(r"future.*work", report_content, re.IGNORECASE)

        assert has_leap_8 or has_future_work, "No future work or Leap 8 proposal mentioned"


class TestLeap7LessonsLearnedSection:
    """Test Lessons Learned section (NECESSARY: Yield + Learning)."""

    def test_report_includes_lessons_learned_section(self):
        """
        Test that report includes Lessons Learned section.

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for Lessons Learned section
        - Assert: Section present with reflections
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: Lessons Learned section present
        assert re.search(r"##\s+Lessons Learned", report_content, re.IGNORECASE), "Lessons Learned section not found"

    def test_report_includes_what_went_well_subsection(self):
        """
        Test that Lessons Learned includes 'What Went Well' subsection.

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for What Went Well subsection
        - Assert: Subsection present with positive outcomes
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: What Went Well subsection
        assert re.search(r"###\s+What Went Well", report_content, re.IGNORECASE), "What Went Well subsection not found"


class TestLeap7SecurityAndStress:
    """Test security and stress scenarios (NECESSARY: Security + Stress)."""

    def test_report_does_not_contain_sensitive_information(self):
        """
        Test that report does not leak sensitive information (API keys, secrets).

        AAA Pattern:
        - Arrange: Load report file
        - Act: Search for common secret patterns
        - Assert: No secrets found in report
        """
        # Arrange: Common secret patterns
        secret_patterns = [
            r"sk-[a-zA-Z0-9]{32,}",  # OpenAI API key
            r"AKIA[0-9A-Z]{16}",  # AWS access key
            r"ghp_[a-zA-Z0-9]{36}",  # GitHub personal access token
            r"-----BEGIN.*PRIVATE KEY-----",  # Private key
        ]

        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report
        report_content = report_path.read_text()

        # Assert: No secrets found
        for pattern in secret_patterns:
            assert not re.search(pattern, report_content), f"Potential secret found matching pattern: {pattern}"

    def test_report_handles_large_content_gracefully(self):
        """
        Test that report can be parsed even if very large (stress test).

        AAA Pattern:
        - Arrange: Load report file (may be large)
        - Act: Parse all sections and metrics
        - Assert: Parsing completes without errors
        """
        # Arrange
        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Parse report (stress test)
        report_content = report_path.read_text()
        section_headers = re.findall(r"^## (.+)$", report_content, re.MULTILINE)
        h3_headers = re.findall(r"^### (.+)$", report_content, re.MULTILINE)

        # Assert: Parsing successful (no exceptions)
        assert len(section_headers) > 0, "Should parse at least one section"
        assert len(report_content) > 1000, "Report should be substantive (>1000 chars)"
        # Stress: Even if 100KB+ report, parsing should complete
        assert len(report_content) < 500_000, "Report should be under 500KB (readability limit)"


class TestLeap7ReportComparison:
    """Test report consistency with previous leaps (NECESSARY: Regression)."""

    def test_report_structure_consistent_with_leap_4(self):
        """
        Test that Leap 7 report follows same structure as Leap 4 (regression check).

        AAA Pattern:
        - Arrange: Load Leap 4 report as reference
        - Act: Compare section structure
        - Assert: Leap 7 follows established pattern
        """
        # Arrange: Load Leap 4 report as reference
        leap4_path = Path(__file__).parent.parent.parent / "docs" / "leap_4_complete.md"
        leap7_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not leap4_path.exists():
            pytest.skip("Leap 4 report not available for comparison")

        if not leap7_path.exists():
            pytest.skip(f"Report not yet generated: {leap7_path}")

        # Act: Parse both reports
        leap4_content = leap4_path.read_text()
        leap7_content = leap7_path.read_text()

        leap4_sections = re.findall(r"^## (.+)$", leap4_content, re.MULTILINE)
        leap7_sections = re.findall(r"^## (.+)$", leap7_content, re.MULTILINE)

        # Assert: Common sections present in both
        common_sections = [
            "Executive Summary",
            "Implementation Details",
            "Test Suite Summary",
            "Constitutional Compliance Validation",
            "Next Steps",
        ]

        for section in common_sections:
            assert section in leap4_sections, f"Leap 4 missing expected section: {section}"
            assert section in leap7_sections, f"Leap 7 missing expected section: {section}"

    def test_report_file_naming_convention(self):
        """
        Test that report file follows naming convention (leap_N_*_complete.md).

        AAA Pattern:
        - Arrange: Define expected filename pattern
        - Act: Check if file matches pattern
        - Assert: Filename follows convention
        """
        # Arrange: Expected pattern
        filename_pattern = r"leap_\d+_[a-z_]+_complete\.md"

        report_path = Path(__file__).parent.parent.parent / "docs" / "leap_7_test_driven_autonomy_complete.md"

        if not report_path.exists():
            pytest.skip(f"Report not yet generated: {report_path}")

        # Act: Check filename
        filename = report_path.name

        # Assert: Matches pattern
        assert re.match(filename_pattern, filename), f"Filename does not match pattern: {filename_pattern}"
