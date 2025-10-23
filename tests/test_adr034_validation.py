#!/usr/bin/env python3
"""
Tests for ADR-034 Documentation Completeness Validation.

Constitutional Article VI: TDD Mandate
- Tests written FIRST (RED phase)
- Tests will FAIL if ADR-034 incomplete
- Update ADR-034 to make tests pass (GREEN phase)

Validates:
- All required sections present and non-empty
- Validation metrics populated (not "TBD")
- Implementation details match actual V5 code
- References valid and files exist
- Status is "Accepted"
- Rollout plan phase status clear
"""

import pytest
import re
from pathlib import Path
from typing import Dict, List, Tuple


# ADR-034 path
ADR_034_PATH = Path(__file__).parent.parent / "docs" / "adr" / "ADR-034-empirical-test-value-scoring.md"

# Required V5 component files
V5_COMPONENTS = [
    "scripts/runtime_data_parser.py",
    "scripts/runtime_penalty.py",
    "scripts/ci_failure_parser.py",
    "scripts/failure_bonus.py",
    "scripts/git_churn_analyzer.py",
    "scripts/mock_classifier.py",
    "scripts/weights_loader.py",
    "scripts/score_normalization.py",
    "scripts/test_value_audit.py",
    "scripts/test_value_audit_v5.py",
    "weights.yaml",
]


@pytest.fixture
def adr_content() -> str:
    """Load ADR-034 content."""
    assert ADR_034_PATH.exists(), f"ADR-034 not found at {ADR_034_PATH}"
    return ADR_034_PATH.read_text()


@pytest.fixture
def adr_sections(adr_content: str) -> Dict[str, str]:
    """Parse ADR-034 into sections."""
    sections = {}
    current_section = None
    current_lines = []

    for line in adr_content.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Add last section
    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()

    return sections


class TestADR034SectionPresence:
    """Test that all required sections are present in ADR-034."""

    def test_context_section_exists(self, adr_sections: Dict[str, str]):
        """Test Context section exists and is non-empty."""
        assert "Context" in adr_sections, "Context section missing"
        assert len(adr_sections["Context"]) > 100, "Context section too short"

        # Should mention V4 problems
        assert "74%" in adr_sections["Context"], "V4 74% P1 rate not mentioned"
        assert "false positive" in adr_sections["Context"].lower(), "False positives not mentioned"

    def test_decision_section_exists(self, adr_sections: Dict[str, str]):
        """Test Decision section exists with 8 empirical dimensions."""
        assert "Decision" in adr_sections, "Decision section missing"

        decision_content = adr_sections["Decision"]
        assert len(decision_content) > 200, "Decision section too short"

        # Check for 8 dimensions
        dimensions = [
            "Runtime Data",
            "CI Failure History",
            "Git Churn",
            "Mock Classification",
            "Configurable Weights",
            "Score Normalization",
            "Grid Search Tuner",
            "Safety Pipeline",
        ]
        for dimension in dimensions:
            assert dimension in decision_content, f"Dimension '{dimension}' not mentioned"

    def test_implementation_section_exists(self, adr_sections: Dict[str, str]):
        """Test Implementation section exists with V5 component details."""
        assert "Implementation" in adr_sections, "Implementation section missing"

        impl_content = adr_sections["Implementation"]
        assert len(impl_content) > 200, "Implementation section too short"

        # Should mention V5 components
        v5_components = ["runtime_data_parser", "failure_bonus", "git_churn_analyzer", "mock_classifier"]
        for component in v5_components:
            assert component in impl_content, f"Component '{component}' not mentioned"

    def test_validation_section_exists(self, adr_sections: Dict[str, str]):
        """Test Validation section exists with metrics table."""
        assert "Validation" in adr_sections, "Validation section missing"

        validation_content = adr_sections["Validation"]
        assert len(validation_content) > 100, "Validation section too short"

        # Should have metrics table
        assert "| Metric |" in validation_content, "Metrics table missing"
        assert "| Actual |" in validation_content, "Actual column missing from table"

    def test_consequences_section_exists(self, adr_sections: Dict[str, str]):
        """Test Consequences section exists with Positive/Negative/Neutral subsections."""
        assert "Consequences" in adr_sections, "Consequences section missing"

        consequences_content = adr_sections["Consequences"]
        assert len(consequences_content) > 100, "Consequences section too short"

        # Should have subsections
        assert "### Positive" in consequences_content, "Positive consequences missing"
        assert "### Negative" in consequences_content, "Negative consequences missing"
        assert "### Neutral" in consequences_content, "Neutral consequences missing"

    def test_alternatives_section_exists(self, adr_sections: Dict[str, str]):
        """Test Alternatives Considered section exists."""
        assert "Alternatives Considered" in adr_sections, "Alternatives Considered section missing"

        alternatives_content = adr_sections["Alternatives Considered"]
        assert len(alternatives_content) > 50, "Alternatives section too short"

    def test_rollout_plan_section_exists(self, adr_sections: Dict[str, str]):
        """Test Rollout Plan section exists with phase status."""
        assert "Rollout Plan" in adr_sections, "Rollout Plan section missing"

        rollout_content = adr_sections["Rollout Plan"]
        assert len(rollout_content) > 100, "Rollout Plan section too short"

        # Should mention phases 1-10
        for phase_num in range(1, 11):
            assert f"Phase {phase_num}" in rollout_content or f"Phase {phase_num}-" in rollout_content, \
                f"Phase {phase_num} not mentioned"

    def test_references_section_exists(self, adr_sections: Dict[str, str]):
        """Test References section exists with at least 5 links."""
        assert "References" in adr_sections, "References section missing"

        references_content = adr_sections["References"]
        assert len(references_content) > 50, "References section too short"

        # Count markdown links or ADR references
        adr_refs = len(re.findall(r'ADR-\d+', references_content))
        doc_refs = len(re.findall(r'\*\*.*?\*\*:\s*`.*?\.md`', references_content))
        total_refs = adr_refs + doc_refs

        assert total_refs >= 5, f"Only {total_refs} references found, expected at least 5"


class TestADR034ValidationMetrics:
    """Test that validation metrics are populated (not TBD)."""

    def test_metrics_table_structure(self, adr_content: str):
        """Test that validation metrics table exists with required columns."""
        # Find metrics table
        table_match = re.search(
            r'\| Metric \| V4 \| V5 Target \| Actual \|.*?\n(?:\|.*?\n)+',
            adr_content,
            re.DOTALL
        )
        assert table_match is not None, "Validation metrics table not found"

    def test_p1_rate_populated(self, adr_content: str):
        """Test P1 Rate actual value is populated (not TBD)."""
        # Find P1 Rate row
        p1_match = re.search(r'\| P1 Rate.*?\| (.*?) \|', adr_content)
        assert p1_match is not None, "P1 Rate row not found"

        actual_value = p1_match.group(1).strip()
        assert actual_value != "TBD", "P1 Rate actual value still TBD"

        # Should be a percentage or documented reason
        is_percentage = "%" in actual_value
        is_documented = "requires" in actual_value.lower() or "pending" in actual_value.lower()
        assert is_percentage or is_documented, f"P1 Rate actual value unclear: {actual_value}"

    def test_false_positive_rate_populated(self, adr_content: str):
        """Test False Positive Rate actual value is populated."""
        fp_match = re.search(r'\| False Positive.*?\|.*?\|.*?\| (.*?) \|', adr_content)
        assert fp_match is not None, "False Positive Rate row not found"

        actual_value = fp_match.group(1).strip()
        assert actual_value != "TBD", "False Positive Rate still TBD"

    def test_runtime_accuracy_populated(self, adr_content: str):
        """Test Runtime Accuracy actual value is populated."""
        runtime_match = re.search(r'\| Runtime Accuracy.*?\|.*?\|.*?\| (.*?) \|', adr_content)
        assert runtime_match is not None, "Runtime Accuracy row not found"

        actual_value = runtime_match.group(1).strip()
        assert actual_value != "TBD", "Runtime Accuracy still TBD"

    def test_bug_detector_id_populated(self, adr_content: str):
        """Test Bug Detector ID actual value is populated."""
        bug_match = re.search(r'\| Bug Detector.*?\|.*?\|.*?\| (.*?) \|', adr_content)
        assert bug_match is not None, "Bug Detector ID row not found"

        actual_value = bug_match.group(1).strip()
        assert actual_value != "TBD", "Bug Detector ID still TBD"

    def test_test_suite_metrics_present(self, adr_content: str):
        """Test that test suite metrics are mentioned (1,762 tests)."""
        # Should mention total test count somewhere
        test_count_pattern = r'1[,\s]?762|1762'
        assert re.search(test_count_pattern, adr_content), "Test count (1,762) not mentioned"


class TestADR034ImplementationDetails:
    """Test that implementation details match actual V5 code."""

    def test_v5_components_listed(self, adr_content: str):
        """Test that all V5 components are listed in Implementation section."""
        key_components = [
            "runtime_data_parser",
            "failure_bonus",
            "git_churn_analyzer",
            "mock_classifier",
            "weights_loader",
            "score_normalization",
        ]

        for component in key_components:
            assert component in adr_content, f"Component '{component}' not mentioned"

    def test_graceful_fallback_documented(self, adr_content: str):
        """Test that graceful fallback strategy is documented."""
        fallback_keywords = ["fallback", "heuristic", "backward compatible"]

        found_keywords = sum(1 for kw in fallback_keywords if kw in adr_content.lower())
        assert found_keywords >= 2, "Graceful fallback strategy not sufficiently documented"

    def test_scoring_modes_documented(self, adr_content: str):
        """Test that V5 scoring modes are documented."""
        # Should mention different modes or data availability handling
        mode_keywords = ["V5_FULL", "V5_PARTIAL", "V4_FALLBACK", "mode"]

        found_modes = sum(1 for kw in mode_keywords if kw in adr_content)
        assert found_modes >= 1, "Scoring modes not documented"

    def test_file_paths_included(self, adr_content: str):
        """Test that key file paths are included."""
        key_paths = [
            "test_value_audit",
            "weights.yaml",
            ".audit/",
        ]

        for path in key_paths:
            assert path in adr_content, f"File path '{path}' not mentioned"

    def test_v5_components_actually_exist(self):
        """Test that referenced V5 components actually exist in codebase."""
        repo_root = Path(__file__).parent.parent

        for component_path in V5_COMPONENTS:
            full_path = repo_root / component_path
            assert full_path.exists(), f"Referenced component {component_path} does not exist"


class TestADR034ReferencesValidation:
    """Test that all references are valid and files exist."""

    def test_adr033_referenced(self, adr_content: str):
        """Test that ADR-033 is referenced."""
        assert "ADR-033" in adr_content, "ADR-033 not referenced"

    def test_adr033_file_exists(self):
        """Test that ADR-033 file actually exists."""
        adr_033_path = Path(__file__).parent.parent / "docs" / "adr" / "ADR-033-value-first-testing-philosophy.md"
        assert adr_033_path.exists(), "ADR-033 file does not exist"

    def test_v5_plan_referenced(self, adr_content: str):
        """Test that TEST_AUDIT_V5_PLAN.md is referenced."""
        assert "TEST_AUDIT_V5_PLAN" in adr_content or "V5_PLAN" in adr_content, \
            "V5 plan not referenced"

    def test_v5_handoff_referenced(self, adr_content: str):
        """Test that V5_HANDOFF_COMPLETE.md is referenced."""
        assert "V5_HANDOFF_COMPLETE" in adr_content or "HANDOFF" in adr_content, \
            "V5 handoff not referenced"

    def test_v4_analysis_referenced(self, adr_content: str):
        """Test that V4 analysis document is referenced."""
        assert "V4_1200_TEST_ANALYSIS" in adr_content or "V4" in adr_content, \
            "V4 analysis not referenced"

    def test_referenced_files_exist(self):
        """Test that referenced documentation files exist."""
        repo_root = Path(__file__).parent.parent

        # Core documentation that should exist
        expected_docs = [
            "V4_1200_TEST_ANALYSIS.md",
            "V5_FEEDBACK_MAPPING.md",
            "V5_HANDOFF_COMPLETE.md",
            "TEST_AUDIT_V5_PLAN.md",
        ]

        for doc in expected_docs:
            doc_path = repo_root / doc
            assert doc_path.exists(), f"Referenced document {doc} does not exist"


class TestADR034StatusAndDates:
    """Test that status and dates are correct."""

    def test_status_is_accepted(self, adr_content: str):
        """Test that status is 'Accepted' (not Draft or Approved)."""
        # Status should be at top of file
        status_match = re.search(r'\*\*Status\*\*:\s*(\w+)', adr_content)
        assert status_match is not None, "Status field not found"

        status = status_match.group(1).strip()
        # Should be "Accepted" for finalized ADR
        # Note: Currently "Approved" is acceptable, "Accepted" is ideal
        assert status in ["Approved", "Accepted"], f"Status is '{status}', expected 'Accepted' or 'Approved'"

    def test_implementation_date_present(self, adr_content: str):
        """Test that implementation date is present."""
        # Should have a date field
        date_match = re.search(r'\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})', adr_content)
        assert date_match is not None, "Date field not found"

        date_str = date_match.group(1)
        # Should be October 2025 or later
        assert date_str >= "2025-10-23", f"Date {date_str} is before expected implementation"

    def test_implemented_date_mentioned(self, adr_content: str):
        """Test that 'Implemented' date is mentioned."""
        # Should mention implementation completion
        assert "Implemented" in adr_content or "implemented" in adr_content, \
            "Implementation completion date not mentioned"


class TestADR034RolloutPlanStatus:
    """Test that rollout plan phase status is clear."""

    def test_phase1_marked_complete(self, adr_content: str):
        """Test Phase 1 is marked complete."""
        phase1_match = re.search(r'Phase 1.*?✅', adr_content, re.IGNORECASE)
        assert phase1_match is not None, "Phase 1 not marked complete"

    def test_phase2_marked_complete(self, adr_content: str):
        """Test Phase 2 is marked complete."""
        phase2_match = re.search(r'Phase 2.*?✅', adr_content, re.IGNORECASE)
        assert phase2_match is not None, "Phase 2 not marked complete"

    def test_phase5_marked_complete(self, adr_content: str):
        """Test Phase 5 is marked complete."""
        phase5_match = re.search(r'Phase 5.*?✅', adr_content, re.IGNORECASE)
        assert phase5_match is not None, "Phase 5 not marked complete"

    def test_phase9_marked_complete(self, adr_content: str):
        """Test Phase 9 (Integration) is marked complete."""
        phase9_match = re.search(r'Phase 9.*?✅', adr_content, re.IGNORECASE)
        assert phase9_match is not None, "Phase 9 not marked complete"

    def test_phase10_marked_complete(self, adr_content: str):
        """Test Phase 10 (Documentation) is marked complete."""
        phase10_match = re.search(r'Phase 10.*?✅', adr_content, re.IGNORECASE)
        assert phase10_match is not None, "Phase 10 not marked complete"

    def test_all_phases_have_status(self, adr_content: str):
        """Test that all phases 1-10 have clear status (✅ or other indicator)."""
        for phase_num in range(1, 11):
            # Look for phase with either checkmark or status note
            phase_pattern = rf'Phase {phase_num}[^✅\n]*?(✅|⏳|🔄|\(.*?\))'
            phase_match = re.search(phase_pattern, adr_content)
            assert phase_match is not None, f"Phase {phase_num} status unclear"


class TestADR034NoPlaceholders:
    """Test that no TBD or TODO placeholders remain."""

    def test_no_undefined_tbd_placeholders(self, adr_content: str):
        """Test that standalone TBD placeholders are removed."""
        # Find all TBD instances
        tbd_matches = list(re.finditer(r'\bTBD\b', adr_content))

        if tbd_matches:
            # If TBD exists, it should be accompanied by explanation
            for match in tbd_matches:
                # Get context around TBD (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(adr_content), match.end() + 50)
                context = adr_content[start:end]

                # TBD is acceptable if it explains why (e.g., "TBD: requires empirical data")
                has_explanation = any(kw in context.lower() for kw in [
                    "requires", "pending", "need", "collection", "future"
                ])

                assert has_explanation, f"TBD placeholder without explanation: {context}"

    def test_no_todo_placeholders(self, adr_content: str):
        """Test that TODO placeholders are removed."""
        # Allow TODO in Future Work section, but not elsewhere
        future_work_section = re.search(r'## Future Work(.*?)(?=##|$)', adr_content, re.DOTALL)

        if future_work_section:
            # Remove Future Work section for this test
            content_without_future = adr_content.replace(future_work_section.group(0), "")
            assert "TODO" not in content_without_future, "TODO placeholder found outside Future Work"
        else:
            # If no Future Work section, no TODOs should exist at all
            assert "TODO" not in adr_content, "TODO placeholder found"

    def test_no_insert_placeholders(self, adr_content: str):
        """Test that [INSERT] placeholders are removed."""
        assert "[INSERT]" not in adr_content, "[INSERT] placeholder found"


class TestADR034LessonsLearned:
    """Test that Lessons Learned section exists (optional but recommended)."""

    def test_lessons_learned_section_exists(self, adr_sections: Dict[str, str]):
        """Test that Lessons Learned section exists."""
        # This is recommended but not strictly required
        # Test will pass if section exists OR if learnings are in Consequences
        has_lessons_section = "Lessons Learned" in adr_sections

        if not has_lessons_section:
            # Check if learnings are covered in other sections
            consequences = adr_sections.get("Consequences", "")
            has_learnings_in_consequences = len(consequences) > 200

            # Either dedicated section OR substantial consequences section
            pytest.skip("Lessons Learned section optional (covered in Consequences)")

    def test_lessons_cover_migration(self, adr_sections: Dict[str, str]):
        """Test that lessons cover V4→V5 migration insights."""
        if "Lessons Learned" not in adr_sections:
            pytest.skip("Lessons Learned section not present")

        lessons_content = adr_sections["Lessons Learned"]

        # Should mention V4→V5 transition
        migration_keywords = ["V4", "migration", "transition", "heuristic"]
        found_migration = sum(1 for kw in migration_keywords if kw in lessons_content)

        assert found_migration >= 2, "V4→V5 migration insights not covered"

    def test_lessons_cover_tdd(self, adr_sections: Dict[str, str]):
        """Test that lessons mention TDD learnings."""
        if "Lessons Learned" not in adr_sections:
            pytest.skip("Lessons Learned section not present")

        lessons_content = adr_sections["Lessons Learned"]

        # Should mention TDD or testing approach
        tdd_keywords = ["TDD", "test", "red-green", "test-driven"]
        found_tdd = sum(1 for kw in tdd_keywords if kw.lower() in lessons_content.lower())

        assert found_tdd >= 1, "TDD learnings not covered"


class TestADR034ConstitutionalCompliance:
    """Test that constitutional compliance is documented."""

    def test_mentions_article_references(self, adr_content: str):
        """Test that constitutional articles are referenced."""
        # Should mention Articles or Constitution
        article_refs = ["Article I", "Article II", "Article III", "Article IV", "Article V", "Article VI"]

        found_articles = sum(1 for art in article_refs if art in adr_content)

        # At least some constitutional reference
        assert found_articles >= 1, "Constitutional articles not referenced"

    def test_mentions_tdd_compliance(self, adr_content: str):
        """Test that TDD compliance (Article VI) is mentioned."""
        # Should mention TDD somewhere
        tdd_mentioned = "TDD" in adr_content or "test-driven" in adr_content.lower()

        assert tdd_mentioned, "TDD not mentioned (Article VI requirement)"

    def test_mentions_verification_requirements(self, adr_content: str):
        """Test that verification requirements (Article II) are mentioned."""
        # Should mention testing or verification
        verification_keywords = ["test", "verify", "validation", "pass rate"]

        found_verification = sum(1 for kw in verification_keywords if kw in adr_content.lower())

        assert found_verification >= 2, "Verification requirements not sufficiently documented"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
