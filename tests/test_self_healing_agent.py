"""
Unit tests for Self-Healing Agent (Mission 3).

TDD Protocol (Article VI):
- RED PHASE: Tests written FIRST (all fail initially)
- GREEN PHASE: Implementation makes tests pass
- REFACTOR PHASE: Clean up while keeping tests green

Test Coverage:
- TestFailureDetector: JSON parsing, failure extraction
- CladeSelector Integration: Epsilon-greedy bandit selection
- FixGenerator: Prompt building, LLM interaction
- PRWorkflow: Branch naming, metadata generation
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import module to avoid namespace collision with test class names
import tools.self_healing_agent as sha

# Also import specific items for convenience
from tools.self_healing_agent import (
    SELF_HEALING_CLADES,
)


class TestFailureDetector:
    """Tests for TestFailureDetector class."""

    def test_load_valid_json(self):
        """Test loading valid test results JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test results JSON
            json_path = Path(tmpdir) / "test_results.json"
            test_data = {
                "summary": {
                    "total": 10,
                    "passed": 7,
                    "failed": 3
                },
                "tests": [
                    {
                        "nodeid": "tests/test_validation.py::test_validation_error",
                        "outcome": "failed",
                        "lineno": 42,
                        "call": {
                            "longrepr": "AssertionError: Expected 5, got 3"
                        }
                    },
                    {
                        "nodeid": "tests/test_utils.py::test_parse_json",
                        "outcome": "passed",
                        "lineno": 10,
                        "call": {}
                    }
                ]
            }
            json_path.write_text(json.dumps(test_data))

            # Test
            detector = sha.TestFailureDetector()
            result = detector.load_test_results(str(json_path))

            assert result.is_ok()
            test_results = result.unwrap()
            assert test_results["summary"]["failed"] == 3

    def test_load_missing_file(self):
        """Test loading missing JSON file returns error."""
        detector = sha.TestFailureDetector()
        result = detector.load_test_results("/nonexistent/file.json")

        assert result.is_err()
        error = result.unwrap_err()
        assert "not found" in str(error).lower() or "no such file" in str(error).lower()

    def test_load_malformed_json(self):
        """Test loading malformed JSON returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "malformed.json"
            json_path.write_text("{invalid json}")

            detector = sha.TestFailureDetector()
            result = detector.load_test_results(str(json_path))

            assert result.is_err()
            error = result.unwrap_err()
            assert "parse" in str(error).lower() or "decode" in str(error).lower()

    def test_extract_failures_3_failures(self):
        """Test extracting 3 failures from test results."""
        test_results = {
            "summary": {"total": 10, "failed": 3},
            "tests": [
                {
                    "nodeid": "tests/test_a.py::test_1",
                    "outcome": "failed",
                    "lineno": 10,
                    "call": {"longrepr": "Error 1"}
                },
                {
                    "nodeid": "tests/test_b.py::test_2",
                    "outcome": "passed",
                    "lineno": 20,
                    "call": {}
                },
                {
                    "nodeid": "tests/test_c.py::test_3",
                    "outcome": "failed",
                    "lineno": 30,
                    "call": {"longrepr": "Error 2"}
                },
                {
                    "nodeid": "tests/test_d.py::test_4",
                    "outcome": "failed",
                    "lineno": 40,
                    "call": {"longrepr": "Error 3"}
                },
            ]
        }

        detector = sha.TestFailureDetector()
        failures = detector.extract_failures(test_results)

        assert len(failures) == 3
        assert failures[0].test_name == "test_1"
        assert failures[0].file_path == "tests/test_a.py"
        assert failures[0].line_number == 10
        assert failures[0].error_message == "Error 1"

    def test_extract_failures_0_failures(self):
        """Test extracting 0 failures returns empty list."""
        test_results = {
            "summary": {"total": 5, "failed": 0},
            "tests": [
                {"nodeid": "tests/test_a.py::test_1", "outcome": "passed", "lineno": 10, "call": {}},
                {"nodeid": "tests/test_b.py::test_2", "outcome": "passed", "lineno": 20, "call": {}},
            ]
        }

        detector = sha.TestFailureDetector()
        failures = detector.extract_failures(test_results)

        assert len(failures) == 0

    def test_extract_failures_skips_skipped_tests(self):
        """Test that skipped tests are ignored."""
        test_results = {
            "summary": {"total": 5, "failed": 1, "skipped": 2},
            "tests": [
                {"nodeid": "tests/test_a.py::test_1", "outcome": "failed", "lineno": 10, "call": {"longrepr": "Error"}},
                {"nodeid": "tests/test_b.py::test_2", "outcome": "skipped", "lineno": 20, "call": {}},
                {"nodeid": "tests/test_c.py::test_3", "outcome": "skipped", "lineno": 30, "call": {}},
            ]
        }

        detector = sha.TestFailureDetector()
        failures = detector.extract_failures(test_results)

        assert len(failures) == 1
        assert failures[0].test_name == "test_1"


class TestCladeConfig:
    """Tests for CladeConfig dataclass."""

    def test_to_clade_id(self):
        """Test converting CladeConfig to clade_id string."""
        config = sha.CladeConfig(
            agent_id="self_healer_v1",
            model_name="gpt-5",
            prompt_profile="prompt_full_context",
            strategy="strategy_careful"
        )

        clade_id = config.to_clade_id()

        assert clade_id == "self_healer_v1::gpt-5::prompt_full_context::strategy_careful"

    def test_registry_has_3_plus_clades(self):
        """Test clade registry has at least 3 configurations."""
        assert len(SELF_HEALING_CLADES) >= 3

    def test_registry_clades_valid_format(self):
        """Test all registry clades follow format validation."""
        import re
        # Allow alphanumeric, underscores, hyphens
        clade_id_pattern = re.compile(r"^[\w-]+::[\w-]+::[\w-]+::[\w-]+$")

        for clade in SELF_HEALING_CLADES:
            clade_id = clade.to_clade_id()
            assert clade_id_pattern.match(clade_id), f"Invalid format: {clade_id}"


class TestCladeSelectorIntegration:
    """Tests for CladeSelector integration."""

    @patch("tools.self_healing_agent.CmpStore")
    def test_select_clade_explore(self, mock_store_class):
        """Test epsilon=1.0 always explores (random selection)."""
        # Mock CmpStore to return no events
        mock_store = Mock()
        mock_store.load_events.return_value = []
        mock_store_class.return_value = mock_store

        from agency_memory.learning import CladeSelector

        selector = CladeSelector(mock_store)
        available_clades = ["clade_1", "clade_2", "clade_3"]

        # With epsilon=1.0, should always explore (random)
        selected = selector.select_clade(
            task_type="self_heal",
            available_clades=available_clades,
            epsilon=1.0
        )

        assert selected in available_clades

    @patch("tools.self_healing_agent.CmpStore")
    @patch("agency_memory.learning.compute_clade_score")
    def test_select_clade_exploit(self, mock_compute_score, mock_store_class):
        """Test epsilon=0.0 always exploits (chooses best clade)."""
        from agency_memory.learning import CladeSelector, CmpScore

        # Mock CmpStore with events
        mock_store = Mock()
        mock_store.load_events.return_value = []
        mock_store_class.return_value = mock_store

        # Mock compute_clade_score to return different scores
        def score_side_effect(events, clade_id):
            scores = {
                "clade_1": CmpScore(clade_id="clade_1", total_events=10, approvals=9, rejections=1, reverts=0, approval_rate=0.9, revert_rate=0.0, avg_loc_delta_rejected=100.0, score=0.9),
                "clade_2": CmpScore(clade_id="clade_2", total_events=10, approvals=5, rejections=5, reverts=0, approval_rate=0.5, revert_rate=0.0, avg_loc_delta_rejected=100.0, score=0.5),
            }
            return scores.get(clade_id, CmpScore(clade_id=clade_id, total_events=0, approvals=0, rejections=0, reverts=0, approval_rate=0.0, revert_rate=0.0, avg_loc_delta_rejected=0.0, score=0.0))

        mock_compute_score.side_effect = score_side_effect

        selector = CladeSelector(mock_store)
        available_clades = ["clade_1", "clade_2"]

        # With epsilon=0.0, should always exploit (choose best)
        selected = selector.select_clade(
            task_type="self_heal",
            available_clades=available_clades,
            epsilon=0.0
        )

        # Should choose clade_1 (score 0.9 > 0.5)
        assert selected == "clade_1"


class TestFixGenerator:
    """Tests for FixGenerator class."""

    def test_build_prompt_full_context(self):
        """Test building prompt with full context profile."""
        config = sha.CladeConfig(
            agent_id="self_healer_v1",
            model_name="gpt-5",
            prompt_profile="prompt_full_context",
            strategy="strategy_careful"
        )
        generator = sha.FixGenerator(config)

        failure = sha.TestFailure(
            test_name="test_validation",
            file_path="tests/test_validation.py",
            line_number=42,
            error_type="AssertionError",
            error_message="Expected 5, got 3",
            test_code="def test_validation():\n    assert func() == 5"
        )

        prompt = generator._build_prompt(failure)

        # Full context should include test file, error, and request for implementation file
        assert "test_validation" in prompt
        assert "AssertionError" in prompt
        assert "Expected 5, got 3" in prompt
        assert len(prompt) > 200  # Full context is verbose

    def test_build_prompt_small_diff(self):
        """Test building prompt with small diff profile."""
        config = sha.CladeConfig(
            agent_id="self_healer_v1",
            model_name="qwen-32b",
            prompt_profile="prompt_small_diff_v1",
            strategy="strategy_minimal"
        )
        generator = sha.FixGenerator(config)

        failure = sha.TestFailure(
            test_name="test_parse",
            file_path="tests/test_utils.py",
            line_number=10,
            error_type="ValueError",
            error_message="invalid literal for int()",
            test_code="def test_parse():\n    assert parse('5') == 5"
        )

        prompt = generator._build_prompt(failure)

        # Small diff should be concise
        assert "test_parse" in prompt
        assert "ValueError" in prompt
        assert len(prompt) < 500  # Small diff is concise

    def test_build_prompt_terse(self):
        """Test building prompt with terse profile."""
        config = sha.CladeConfig(
            agent_id="self_healer_v1",
            model_name="gpt-5-mini",
            prompt_profile="prompt_terse",
            strategy="strategy_quick"
        )
        generator = sha.FixGenerator(config)

        failure = sha.TestFailure(
            test_name="test_add",
            file_path="tests/test_math.py",
            line_number=5,
            error_type="AssertionError",
            error_message="1 + 1 != 3",
            test_code=None
        )

        prompt = generator._build_prompt(failure)

        # Terse should be minimal
        assert "AssertionError" in prompt or "1 + 1 != 3" in prompt
        assert len(prompt) < 200  # Terse is very brief

    @patch("tools.self_healing_agent.FixGenerator._call_llm")
    def test_generate_fix_valid_response(self, mock_llm):
        """Test generating fix with valid LLM response."""
        mock_llm.return_value = sha.LLMResponse(
            files_changed={
                "shared/math_utils.py": "def add(a, b):\n    return a + b\n"
            },
            reasoning="Fixed add function to return correct sum"
        )

        config = sha.CladeConfig(
            agent_id="self_healer_v1",
            model_name="gpt-5",
            prompt_profile="prompt_full_context",
            strategy="strategy_careful"
        )
        generator = sha.FixGenerator(config)

        failure = sha.TestFailure(
            test_name="test_add",
            file_path="tests/test_math.py",
            line_number=5,
            error_type="AssertionError",
            error_message="1 + 1 != 3",
            test_code=None
        )

        result = generator.generate_fix(failure)

        assert result.is_ok()
        proposal = result.unwrap()
        assert proposal.clade_id == config.to_clade_id()
        assert "shared/math_utils.py" in proposal.files_changed
        assert "Fixed add function" in proposal.reasoning

    @patch("tools.self_healing_agent.FixGenerator._call_llm")
    def test_generate_fix_invalid_llm_response(self, mock_llm):
        """Test generating fix with invalid LLM response returns error."""
        mock_llm.side_effect = ValueError("Invalid LLM response format")

        config = sha.CladeConfig(
            agent_id="self_healer_v1",
            model_name="gpt-5",
            prompt_profile="prompt_full_context",
            strategy="strategy_careful"
        )
        generator = sha.FixGenerator(config)

        failure = sha.TestFailure(
            test_name="test_add",
            file_path="tests/test_math.py",
            line_number=5,
            error_type="AssertionError",
            error_message="1 + 1 != 3",
            test_code=None
        )

        result = generator.generate_fix(failure)

        assert result.is_err()
        error = result.unwrap_err()
        assert "invalid" in str(error).lower() or "missing" in str(error).lower()


class TestPRWorkflow:
    """Tests for PRWorkflow class."""

    def test_build_branch_name(self):
        """Test building autogen/* branch name."""
        workflow = sha.PRWorkflow()
        clade_id = "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"

        branch_name = workflow.build_branch_name(clade_id, short_id="abc123")

        assert branch_name.startswith("autogen/selfheal-")
        assert "abc123" in branch_name
        assert len(branch_name) < 100  # Reasonable length

    def test_build_pr_body(self):
        """Test building PR body with HTML comment metadata."""
        workflow = sha.PRWorkflow()

        failure = sha.TestFailure(
            test_name="test_validation",
            file_path="tests/test_validation.py",
            line_number=42,
            error_type="AssertionError",
            error_message="Expected 5, got 3",
            test_code=None
        )

        proposal = sha.FixProposal(
            files_changed={"shared/validation.py": "def validate(): return 5"},
            reasoning="Fixed validation logic",
            clade_id="self_healer_v1::gpt-5::prompt_full_context::strategy_careful"
        )

        pr_body = workflow.build_pr_body(failure, proposal, proposal.clade_id)

        # Verify HTML comments
        assert "<!-- agent_id: self_healer_v1 -->" in pr_body
        assert f"<!-- clade_id: {proposal.clade_id} -->" in pr_body
        assert "<!-- task_type: self_heal -->" in pr_body
        # Verify description
        assert "test_validation" in pr_body
        assert "Fixed validation logic" in pr_body

    def test_build_pr_metadata(self):
        """Test building PRMetadata object."""
        workflow = sha.PRWorkflow()

        failure = sha.TestFailure(
            test_name="test_add",
            file_path="tests/test_math.py",
            line_number=5,
            error_type="AssertionError",
            error_message="1 + 1 != 3",
            test_code=None
        )

        proposal = sha.FixProposal(
            files_changed={"shared/math.py": "def add(a, b): return a + b"},
            reasoning="Fixed add",
            clade_id="self_healer_v1::gpt-5::prompt_full_context::strategy_careful"
        )

        metadata = workflow.build_pr_metadata(failure, proposal, memory_ids=["mem_001", "mem_002"])

        assert metadata.agent_id == "self_healer_v1"
        assert metadata.clade_id == proposal.clade_id
        assert metadata.task_type == "self_heal"
        assert metadata.memory_ids == ["mem_001", "mem_002"]
        assert metadata.test_failure == failure
        assert metadata.fix_proposal == proposal
