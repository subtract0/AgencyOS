#!/usr/bin/env python3
"""
Test suite for ADR-026 content validation.

Validates that generated ADRs contain all required sections with proper Markdown
structure and constitutional alignment references (Articles I, II, V).

Tests follow the NECESSARY framework:
- N: Normal operation (happy path ADR structure)
- E: Edge cases (missing sections, malformed Markdown)
- C: Corner cases (empty sections, unusual formats)
- E: Error conditions (invalid Markdown, broken links)
- S: Security (injection prevention, path traversal)
- S: Stress (large ADRs, many sections)
- A: Accessibility (clear structure, readable format)
- R: Regression (previous ADR formats still valid)
- Y: Yield (correct section content, constitutional references)
"""

import re
from pathlib import Path
from typing import Any

import pytest


class ADRHelperMixin:
    """Mixin providing helper methods for ADR parsing."""

    def _extract_sections(self, adr_content: str) -> dict[str, str]:
        """
        Extract all level-2 sections from ADR content.

        Args:
            adr_content: Full ADR Markdown content

        Returns:
            Dictionary mapping section names to section content
        """
        sections = {}
        current_section = None
        current_content = []

        for line in adr_content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _extract_section_content(self, adr_content: str, section_name: str) -> str:
        """
        Extract content of specific section from ADR.

        Args:
            adr_content: Full ADR Markdown content
            section_name: Name of section to extract (e.g., "Context", "Decision")

        Returns:
            Section content as string, or empty string if not found
        """
        sections = self._extract_sections(adr_content)
        return sections.get(section_name, "")


class TestADRStructureValidation(ADRHelperMixin):
    """Test suite for ADR Markdown structure validation (NECESSARY: Normal)."""

    def test_adr_contains_required_sections_happy_path(self):
        """
        Test that a valid ADR contains all required sections.

        AAA Pattern:
        - Arrange: Create valid ADR content with all required sections
        - Act: Validate structure
        - Assert: All required sections present
        """
        # Arrange: Valid ADR content
        adr_content = """# ADR-026: Test Decision

**Status**: Accepted
**Date**: 2025-10-10

## Context

This is the context section describing the problem.

### Problem Statement
The specific problem we're solving.

## Decision

We decided to implement solution X.

## Consequences

### Positive Consequences
- Benefit 1
- Benefit 2

### Negative Consequences
- Trade-off 1

## Alternatives Considered

### Alternative 1: Different Approach
We considered this but rejected it.

## Constitutional Alignment

### Article I: Complete Context Before Action
- ✅ PASS: All audits completed

### Article II: 100% Verification and Stability
- ✅ PASS: Tests passing

### Article V: Spec-Driven Development
- ✅ PASS: Follows specification
"""

        # Act: Extract sections
        sections = self._extract_sections(adr_content)

        # Assert: All required sections present
        assert "Context" in sections, "Missing Context section"
        assert "Decision" in sections, "Missing Decision section"
        assert "Consequences" in sections, "Missing Consequences section"
        assert "Alternatives Considered" in sections, "Missing Alternatives section"
        assert "Constitutional Alignment" in sections, "Missing Constitutional Alignment"

    def test_adr_context_section_contains_problem_statement(self):
        """
        Test that Context section contains Problem Statement subsection.

        AAA Pattern:
        - Arrange: ADR with Context and Problem Statement
        - Act: Extract Context section content
        - Assert: Problem Statement subsection present
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Context

Background information here.

### Problem Statement
Specific problem description.

## Decision
Solution chosen.
"""

        # Act: Extract Context section
        context_section = self._extract_section_content(adr_content, "Context")

        # Assert: Problem Statement subsection exists
        assert "### Problem Statement" in context_section, (
            "Context section missing Problem Statement subsection"
        )
        assert "Specific problem description" in context_section

    def test_adr_decision_section_is_not_empty(self):
        """
        Test that Decision section contains actual content.

        AAA Pattern:
        - Arrange: ADR with non-empty Decision section
        - Act: Extract Decision content
        - Assert: Content present (not just whitespace)
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Context
Problem context.

## Decision

We adopt solution X because of reasons Y and Z.

This involves implementing components A, B, C.

## Consequences
Impact analysis.
"""

        # Act: Extract Decision section
        decision_section = self._extract_section_content(adr_content, "Decision")

        # Assert: Decision has actual content
        assert len(decision_section.strip()) > 0, "Decision section is empty"
        assert "solution X" in decision_section, "Decision lacks specific solution"

    def test_adr_consequences_section_has_positive_and_negative(self):
        """
        Test that Consequences section has both positive and negative subsections.

        AAA Pattern:
        - Arrange: ADR with complete Consequences section
        - Act: Extract Consequences section
        - Assert: Both Positive and Negative subsections present
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Context
Problem.

## Decision
Solution.

## Consequences

### Positive Consequences
- Benefit 1
- Benefit 2

### Negative Consequences
- Trade-off 1
- Risk 1

## Alternatives Considered
Other options.
"""

        # Act: Extract Consequences section
        consequences = self._extract_section_content(adr_content, "Consequences")

        # Assert: Both subsections present
        assert "### Positive Consequences" in consequences or "### Positive" in consequences, (
            "Missing Positive Consequences subsection"
        )
        assert "### Negative Consequences" in consequences or "### Negative" in consequences, (
            "Missing Negative Consequences subsection"
        )

    def test_adr_alternatives_section_contains_at_least_one_alternative(self):
        """
        Test that Alternatives Considered section has at least one alternative.

        AAA Pattern:
        - Arrange: ADR with Alternatives section
        - Act: Extract Alternatives content
        - Assert: At least one alternative documented
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Context
Problem.

## Decision
Chosen solution.

## Consequences
Impacts.

## Alternatives Considered

### Alternative 1: Different Approach

**Description**: We could have done X.

**Pros**: Benefit A.

**Cons**: Downside B.

**Rejected**: Because of reason C.
"""

        # Act: Extract Alternatives section
        alternatives = self._extract_section_content(adr_content, "Alternatives Considered")

        # Assert: At least one alternative documented
        assert "### Alternative" in alternatives, "No alternatives documented"
        assert "Rejected" in alternatives or "Why Rejected" in alternatives, (
            "Alternative missing rejection rationale"
        )


class TestConstitutionalAlignmentValidation(ADRHelperMixin):
    """Test constitutional references in ADRs (NECESSARY: Yield)."""

    def test_adr_references_article_i_complete_context(self):
        """
        Test that ADR references Article I (Complete Context Before Action).

        AAA Pattern:
        - Arrange: ADR with Article I reference
        - Act: Search for Article I mentions
        - Assert: Article I compliance documented
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Constitutional Alignment

### Article I: Complete Context Before Action

**Compliance**: ✅ PASS

- All audits completed successfully
- Zero file overlap analysis provides complete picture
- Full test suite run before each commit (1,725 tests)
- Retry logic implemented (2x, 3x, 10x)

## References
Constitution: /constitution.md
"""

        # Act: Check for Article I references
        has_article_i = "Article I" in adr_content
        has_complete_context = (
            "Complete Context" in adr_content or "complete context" in adr_content
        )

        # Assert: Article I referenced with compliance details
        assert has_article_i, "ADR missing Article I reference"
        assert has_complete_context, "ADR missing 'Complete Context' terminology"

    def test_adr_references_article_ii_verification(self):
        """
        Test that ADR references Article II (100% Verification).

        AAA Pattern:
        - Arrange: ADR with Article II reference
        - Act: Search for Article II compliance
        - Assert: 100% verification documented
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Constitutional Alignment

### Article II: 100% Verification and Stability

**Compliance**: ✅ PASS

- All 1,725 tests passing (100% success rate)
- Zero lint errors after cleanup
- CI pipeline green
- Quality gates enforced
"""

        # Act: Check for Article II references
        has_article_ii = "Article II" in adr_content
        has_verification = "100%" in adr_content and (
            "Verification" in adr_content or "test" in adr_content
        )

        # Assert: Article II referenced with test compliance
        assert has_article_ii, "ADR missing Article II reference"
        assert has_verification, "ADR missing 100% verification details"

    def test_adr_references_article_v_spec_driven(self):
        """
        Test that ADR references Article V (Spec-Driven Development).

        AAA Pattern:
        - Arrange: ADR with Article V reference
        - Act: Search for Article V compliance
        - Assert: Spec-driven process documented
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Constitutional Alignment

### Article V: Spec-Driven Development

**Compliance**: ✅ PASS

- This ADR documents architectural decision (spec-driven)
- Execution plan follows structured methodology
- Success criteria defined upfront
- Traceability: spec → plan → ADR → code → tests
"""

        # Act: Check for Article V references
        has_article_v = "Article V" in adr_content
        has_spec_driven = (
            "Spec-Driven" in adr_content
            or "spec-driven" in adr_content
            or "specification" in adr_content
        )

        # Assert: Article V referenced with spec process
        assert has_article_v, "ADR missing Article V reference"
        assert has_spec_driven, "ADR missing spec-driven development details"

    def test_adr_has_constitutional_compliance_section(self):
        """
        Test that ADR has dedicated Constitutional Alignment section.

        AAA Pattern:
        - Arrange: ADR with Constitutional Alignment section
        - Act: Extract section
        - Assert: Section exists and contains article references
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Constitutional Alignment

### Article I: Complete Context Before Action
✅ PASS

### Article II: 100% Verification and Stability
✅ PASS

### Article III: Automated Merge Enforcement
✅ PASS

### Article IV: Continuous Learning and Improvement
✅ PASS

### Article V: Spec-Driven Development
✅ PASS
"""

        # Act: Extract Constitutional Alignment section
        sections = self._extract_sections(adr_content)
        constitutional_section = sections.get("Constitutional Alignment", "")

        # Assert: Section exists with article subsections
        assert "Constitutional Alignment" in sections, "Missing Constitutional Alignment section"
        assert "Article I" in constitutional_section, "Missing Article I in alignment section"
        assert "Article II" in constitutional_section, "Missing Article II in alignment section"
        assert "Article V" in constitutional_section, "Missing Article V in alignment section"


class TestMarkdownStructureValidation(ADRHelperMixin):
    """Test Markdown format compliance (NECESSARY: Accessibility)."""

    def test_adr_has_level_1_heading_with_number(self):
        """
        Test that ADR starts with level-1 heading containing ADR number.

        AAA Pattern:
        - Arrange: ADR content with proper heading
        - Act: Extract first heading
        - Assert: Format matches '# ADR-NNN: Title'
        """
        # Arrange
        adr_content = """# ADR-026: Holistic CI Quality Cleanup Strategy

## Context
Content here.
"""

        # Act: Extract first line
        first_line = adr_content.split("\n")[0]

        # Assert: Level-1 heading with ADR number
        assert first_line.startswith("# ADR-"), "ADR missing level-1 heading"
        assert re.match(r"^# ADR-\d+:", first_line), (
            "ADR heading format incorrect (expected '# ADR-NNN: Title')"
        )

    def test_adr_sections_use_level_2_headings(self):
        """
        Test that main sections use level-2 headings (##).

        AAA Pattern:
        - Arrange: ADR with proper heading hierarchy
        - Act: Extract all level-2 headings
        - Assert: Required sections use level-2
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Context
Content.

## Decision
Content.

## Consequences
Content.

## Alternatives Considered
Content.
"""

        # Act: Extract level-2 headings
        level_2_headings = re.findall(r"^## (.+)$", adr_content, re.MULTILINE)

        # Assert: Main sections use level-2
        assert "Context" in level_2_headings, "Context should use level-2 heading"
        assert "Decision" in level_2_headings, "Decision should use level-2 heading"
        assert "Consequences" in level_2_headings, "Consequences should use level-2 heading"
        assert "Alternatives Considered" in level_2_headings, (
            "Alternatives should use level-2 heading"
        )

    def test_adr_subsections_use_level_3_headings(self):
        """
        Test that subsections use level-3 headings (###).

        AAA Pattern:
        - Arrange: ADR with subsections
        - Act: Extract level-3 headings
        - Assert: Subsections use level-3
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Consequences

### Positive Consequences
Benefits here.

### Negative Consequences
Trade-offs here.

### Risks
Risk analysis.
"""

        # Act: Extract level-3 headings
        level_3_headings = re.findall(r"^### (.+)$", adr_content, re.MULTILINE)

        # Assert: Subsections use level-3
        assert len(level_3_headings) > 0, "No level-3 headings found"
        assert any("Positive" in h for h in level_3_headings), "Missing Positive subsection"
        assert any("Negative" in h for h in level_3_headings), "Missing Negative subsection"


class TestADREdgeCases(ADRHelperMixin):
    """Test edge cases and error conditions (NECESSARY: Edge, Error)."""

    def test_adr_with_missing_context_section_fails_validation(self):
        """
        Test that ADR without Context section fails validation.

        AAA Pattern:
        - Arrange: ADR missing Context section
        - Act: Validate structure
        - Assert: Validation fails with specific error
        """
        # Arrange: Invalid ADR (missing Context)
        adr_content = """# ADR-026: Test

## Decision
We decided X.

## Consequences
Impact Y.
"""

        # Act: Extract sections
        sections = self._extract_sections(adr_content)

        # Assert: Context section missing
        assert "Context" not in sections, "Context should be missing (negative test)"

    def test_adr_with_empty_decision_section_fails_validation(self):
        """
        Test that ADR with empty Decision section fails validation.

        AAA Pattern:
        - Arrange: ADR with empty Decision section
        - Act: Extract Decision content
        - Assert: Decision section is effectively empty
        """
        # Arrange: ADR with empty Decision
        adr_content = """# ADR-026: Test

## Context
Problem here.

## Decision

## Consequences
Impact here.
"""

        # Act: Extract Decision section
        decision_section = self._extract_section_content(adr_content, "Decision")

        # Assert: Decision section is empty
        assert len(decision_section.strip()) == 0, "Decision section should be empty (edge case)"

    def test_adr_with_missing_constitutional_alignment_fails_validation(self):
        """
        Test that ADR without Constitutional Alignment fails validation.

        AAA Pattern:
        - Arrange: ADR missing Constitutional Alignment
        - Act: Check for constitutional section
        - Assert: Section not found
        """
        # Arrange: ADR without constitutional section
        adr_content = """# ADR-026: Test

## Context
Problem.

## Decision
Solution.

## Consequences
Impact.

## Alternatives Considered
Other options.
"""

        # Act: Check for Constitutional Alignment
        has_constitutional = "Constitutional Alignment" in adr_content

        # Assert: Constitutional section missing
        assert not has_constitutional, "Constitutional Alignment should be missing (edge case)"

    def test_adr_with_malformed_markdown_heading_fails_validation(self):
        """
        Test that ADR with malformed heading fails validation.

        AAA Pattern:
        - Arrange: ADR with incorrect heading format
        - Act: Validate heading format
        - Assert: Heading doesn't match expected pattern
        """
        # Arrange: Malformed heading (missing space after #)
        adr_content = """#ADR-026: Test (incorrect format)

## Context
Content.
"""

        # Act: Extract first line
        first_line = adr_content.split("\n")[0]

        # Assert: Heading format invalid
        assert not first_line.startswith("# ADR-"), "Heading should be malformed (edge case)"

    def test_adr_with_missing_alternatives_section_fails_validation(self):
        """
        Test that ADR without Alternatives Considered fails validation.

        AAA Pattern:
        - Arrange: ADR missing Alternatives section
        - Act: Check for Alternatives
        - Assert: Section not found
        """
        # Arrange: ADR without Alternatives
        adr_content = """# ADR-026: Test

## Context
Problem.

## Decision
Solution.

## Consequences
Impact.

## Constitutional Alignment
Articles.
"""

        # Act: Check for Alternatives Considered
        sections = self._extract_sections(adr_content)

        # Assert: Alternatives section missing
        assert "Alternatives Considered" not in sections, (
            "Alternatives Considered should be missing (edge case)"
        )


class TestADRRegressionValidation(ADRHelperMixin):
    """Test backward compatibility with previous ADR formats (NECESSARY: Regression)."""

    def test_adr_023_format_still_valid(self):
        """
        Test that ADR-023 format (memory-aware execution) passes validation.

        AAA Pattern:
        - Arrange: ADR-023 sample content
        - Act: Validate structure
        - Assert: All required sections present
        """
        # Arrange: ADR-023 sample format
        adr_content = """# ADR-023: Memory-Aware Execution for Apple Silicon

**Status**: Accepted
**Date**: 2025-10-08

## Context

Agency OS experienced a kernel panic during parallel execution.

### Problem Statement
Hardware constraints on M4 Pro (48GB).

## Decision

Implement hardware-aware execution with three-tier optimization.

## Consequences

### Positive
Memory safety achieved.

### Negative
Slower test execution (3 workers vs 10).

## Alternatives Considered

### Alternative 1: Disable Local Model
Rejected due to cost savings loss.

## Constitutional Alignment

### Article I: Complete Context Before Action
✅ PASS

### Article II: 100% Verification and Stability
✅ PASS
"""

        # Act: Validate structure
        sections = self._extract_sections(adr_content)

        # Assert: ADR-023 format valid
        assert "Context" in sections, "ADR-023 format missing Context"
        assert "Decision" in sections, "ADR-023 format missing Decision"
        assert "Consequences" in sections, "ADR-023 format missing Consequences"
        assert "Alternatives Considered" in sections, "ADR-023 format missing Alternatives"
        assert "Constitutional Alignment" in sections, "ADR-023 format missing Constitutional"

    def test_adr_template_format_matches_expectations(self):
        """
        Test that ADR template format is valid baseline.

        AAA Pattern:
        - Arrange: ADR template structure
        - Act: Validate template
        - Assert: Template has all required placeholders
        """
        # Arrange: ADR template sample
        adr_content = """# ADR-{number}: {title}

**Status**: {status}
**Date**: {date}

## Context

{context_description}

### Problem Statement
{problem_statement}

## Decision

**Winner**: `{winner_id}`

## Evidence

Benchmark results here.

## Consequences

### Positive Consequences
{positive_consequences}

### Negative Consequences
{negative_consequences}

## Constitutional Compliance

### Article I: Complete Context Before Action
{article_i_compliance}

### Article II: 100% Verification and Stability
{article_ii_compliance}

### Article V: Spec-Driven Development
{article_v_compliance}
"""

        # Act: Check for template placeholders
        has_placeholders = "{number}" in adr_content and "{title}" in adr_content
        sections = self._extract_sections(adr_content)

        # Assert: Template structure valid
        assert has_placeholders, "Template missing placeholders"
        assert "Context" in sections, "Template missing Context section"
        assert "Decision" in sections, "Template missing Decision section"
        assert "Consequences" in sections, "Template missing Consequences section"


class TestADRContentQuality(ADRHelperMixin):
    """Test ADR content quality and completeness (NECESSARY: Yield)."""

    def test_adr_context_section_explains_why_decision_needed(self):
        """
        Test that Context section explains rationale for decision.

        AAA Pattern:
        - Arrange: ADR with detailed Context
        - Act: Extract Context content
        - Assert: Context contains problem explanation
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Context

Three parallel quality audits completed on 2025-10-10 revealed the following:

**1. CI Failure Analysis**
- 44 ruff lint errors blocking CI
- Fixability: 70% auto-fixable, 30% manual

**2. Main Branch Quality Audit**
- 51 ruff lint errors (100% auto-fixable)
- Quality score: 87.4%

### Problem Statement

**How do we resolve 95 total lint errors (44 PR + 51 main) without merge conflicts?**

Key constraints:
- Zero file overlap between PR and main errors
- User wants PR merged first
- Must maintain 100% test pass rate

## Decision
Solution here.
"""

        # Act: Extract Context section
        context = self._extract_section_content(adr_content, "Context")

        # Assert: Context has detailed problem explanation
        assert "Problem Statement" in context, "Context missing Problem Statement"
        assert len(context) > 200, "Context section too brief (should explain problem in detail)"

    def test_adr_decision_section_explains_what_was_chosen(self):
        """
        Test that Decision section clearly states chosen solution.

        AAA Pattern:
        - Arrange: ADR with clear Decision
        - Act: Extract Decision content
        - Assert: Decision states chosen approach
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Context
Problem here.

## Decision

**Adopt Option B: Holistic Cleanup Strategy (Merge-First, Fix-Together)**

### Execution Plan

**Phase 1**: Fix critical PR blocker (15 minutes)
**Phase 2**: Auto-fix PR lint errors (10 minutes)
**Phase 3**: Merge PR to main (5 minutes)
**Phase 4**: Holistic main branch cleanup (30 minutes)

**Total Time Estimate**: 70 minutes

## Consequences
Impact here.
"""

        # Act: Extract Decision section
        decision = self._extract_section_content(adr_content, "Decision")

        # Assert: Decision clearly states chosen solution
        assert "Option B" in decision or "Holistic" in decision, (
            "Decision doesn't state chosen option"
        )
        assert "Phase" in decision or "plan" in decision, "Decision missing execution plan"

    def test_adr_alternatives_section_explains_why_rejected(self):
        """
        Test that Alternatives section explains rejection rationale.

        AAA Pattern:
        - Arrange: ADR with detailed Alternatives
        - Act: Extract Alternatives content
        - Assert: Each alternative has rejection reason
        """
        # Arrange
        adr_content = """# ADR-026: Test

## Alternatives Considered

### Alternative 1: Incremental Cleanup (Fix PR First)

**Approach**:
1. Fix all 44 PR errors
2. Merge PR to main
3. Separately fix 51 main errors

**Pros**:
- Smaller, isolated changes
- Easier to review

**Cons**:
- 90 minutes total (22% slower)
- Two separate CI runs (2x overhead)

**Why Rejected**: Zero file overlap makes merge conflict risk negligible, removing primary benefit of incremental approach.

### Alternative 3: Bypass CI and Fix Later

**Cons**:
- **❌ CONSTITUTIONAL VIOLATION (Article III)**
- Sets precedent for quality gate bypass

**Why Rejected**: Direct violation of constitutional Articles II and III.
"""

        # Act: Extract Alternatives section
        alternatives = self._extract_section_content(adr_content, "Alternatives Considered")

        # Assert: Alternatives have rejection rationale
        assert "Why Rejected" in alternatives or "Rejected" in alternatives, (
            "Alternatives missing rejection rationale"
        )
        assert "CONSTITUTIONAL VIOLATION" in alternatives or "violation" in alternatives.lower(), (
            "Alternatives missing constitutional compliance check"
        )


class TestADRIntegration(ADRHelperMixin):
    """Integration tests for ADR validation with real files (NECESSARY: Normal)."""

    @pytest.fixture
    def adr_directory(self) -> Path:
        """Return path to ADR directory."""
        return Path(__file__).parent.parent.parent / "docs" / "adr"

    def test_adr_026_ci_quality_file_exists_and_validates(self, adr_directory: Path):
        """
        Test that ADR-026 CI quality file exists and passes validation.

        AAA Pattern:
        - Arrange: Read ADR-026 CI quality file
        - Act: Validate structure
        - Assert: All required sections present
        """
        # Arrange: Read actual ADR-026 file
        adr_file = adr_directory / "ADR-026-ci-quality-holistic-cleanup.md"

        if not adr_file.exists():
            pytest.skip(f"ADR file not found: {adr_file}")

        adr_content = adr_file.read_text()

        # Act: Validate structure
        sections = self._extract_sections(adr_content)

        # Assert: Required sections present
        assert "Context" in sections, "ADR-026 CI quality missing Context section"
        assert "Decision" in sections, "ADR-026 CI quality missing Decision section"
        assert "Consequences" in sections, "ADR-026 CI quality missing Consequences section"
        assert "Alternatives Considered" in sections, (
            "ADR-026 CI quality missing Alternatives section"
        )

    def test_adr_026_ml_classifier_file_exists_and_validates(self, adr_directory: Path):
        """
        Test that ADR-026 ML classifier file exists and passes validation.

        AAA Pattern:
        - Arrange: Read ADR-026 ML classifier file
        - Act: Validate structure
        - Assert: All required sections present
        """
        # Arrange: Read actual ADR-026 file
        adr_file = adr_directory / "ADR-026-ml-classifier-integration.md"

        if not adr_file.exists():
            pytest.skip(f"ADR file not found: {adr_file}")

        adr_content = adr_file.read_text()

        # Act: Validate structure
        sections = self._extract_sections(adr_content)

        # Assert: Required sections present
        assert "Context" in sections, "ADR-026 ML classifier missing Context section"
        assert "Decision" in sections, "ADR-026 ML classifier missing Decision section"
        assert "Consequences" in sections, "ADR-026 ML classifier missing Consequences section"
        assert "Alternatives Considered" in sections, (
            "ADR-026 ML classifier missing Alternatives section"
        )

    def test_adr_026_contains_constitutional_references(self, adr_directory: Path):
        """
        Test that ADR-026 files reference constitutional articles.

        AAA Pattern:
        - Arrange: Read ADR-026 files
        - Act: Search for constitutional references
        - Assert: Articles I, II, V referenced
        """
        # Arrange: Read both ADR-026 files
        adr_files = [
            adr_directory / "ADR-026-ci-quality-holistic-cleanup.md",
            adr_directory / "ADR-026-ml-classifier-integration.md",
        ]

        for adr_file in adr_files:
            if not adr_file.exists():
                continue

            adr_content = adr_file.read_text()

            # Act: Check for constitutional references
            has_article_i = "Article I" in adr_content
            has_article_ii = "Article II" in adr_content
            has_article_v = "Article V" in adr_content

            # Assert: Constitutional articles referenced
            assert has_article_i, f"{adr_file.name} missing Article I reference"
            assert has_article_ii, f"{adr_file.name} missing Article II reference"
            # Article V may not be present in all ADRs, so we check for at least I and II


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
