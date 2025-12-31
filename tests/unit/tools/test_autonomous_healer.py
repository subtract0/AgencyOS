"""Unit tests for autonomous healer and LLM code fixer.

Tests the Phase 1 components with safety checks.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestLLMCodeFixer:
    """Tests for LLM code fixer."""

    def test_template_fix_bare_except(self):
        """Test that bare except is fixed with template."""
        from tools.llm_code_fixer import LLMCodeFixer

        fixer = LLMCodeFixer()
        result = fixer._try_template_fix(
            "tools/test.py", 10, "bare_except", "    except:"
        )

        assert result.is_ok()
        fix = result.unwrap()
        assert "Exception" in fix.fixed
        assert fix.method == "template"
        assert fix.confidence > 0.9

    def test_template_fix_dict_any_simple(self):
        """Test that Dict[Any, Any] = {} is fixed."""
        from tools.llm_code_fixer import LLMCodeFixer

        fixer = LLMCodeFixer()
        result = fixer._try_template_fix(
            "tools/test.py", 10, "dict_any_any_simple", "data: Dict[Any, Any] = {}"
        )

        assert result.is_ok()
        fix = result.unwrap()
        assert "dict" in fix.fixed
        assert "Dict[Any, Any]" not in fix.fixed

    def test_template_returns_error_for_unknown_type(self):
        """Test that unknown issue types return error."""
        from tools.llm_code_fixer import LLMCodeFixer

        fixer = LLMCodeFixer()
        result = fixer._try_template_fix(
            "tools/test.py", 10, "unknown_type", "some code"
        )

        assert result.is_err()

    def test_fix_issue_validates_path(self):
        """Test that fix_issue validates the file path."""
        from tools.llm_code_fixer import LLMCodeFixer

        fixer = LLMCodeFixer()
        result = fixer.fix_issue("tests/test.py", 1, "bare_except")

        assert result.is_err()
        assert "Forbidden" in result.unwrap_err()

    def test_fix_validates_line_range(self, tmp_path):
        """Test that fix validates line number is in range."""
        from tools.llm_code_fixer import LLMCodeFixer

        # Create test file
        test_file = tmp_path / "tools" / "test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("line1\nline2\nline3")

        fixer = LLMCodeFixer()

        # Mock validate_path to allow our temp path
        with patch("tools.llm_code_fixer.validate_path") as mock_validate:
            mock_validate.return_value = MagicMock(is_err=lambda: False, unwrap=lambda: str(test_file))

            result = fixer.fix_issue(str(test_file), 100, "bare_except")
            assert result.is_err()
            assert "out of range" in result.unwrap_err()

    def test_llm_check_handles_unavailable(self):
        """Test that LLM check handles unavailable LLM gracefully."""
        from tools.llm_code_fixer import LLMCodeFixer

        fixer = LLMCodeFixer()

        # Force check with mocked failure (patch where it's imported)
        with patch("openai.OpenAI") as mock_openai:
            mock_openai.side_effect = Exception("Connection failed")
            fixer._llm_available = None  # Reset cache

            result = fixer._check_llm()
            assert result is False

    def test_fix_dataclass_structure(self):
        """Test that Fix dataclass has correct fields."""
        from tools.llm_code_fixer import Fix

        fix = Fix(
            file_path="test.py",
            line_number=10,
            original="except:",
            fixed="except Exception as e:",
            method="template",
            confidence=0.95,
            issue_type="bare_except",
        )

        assert fix.file_path == "test.py"
        assert fix.line_number == 10
        assert fix.method == "template"
        assert fix.confidence == 0.95


class TestAutonomousHealer:
    """Tests for autonomous healer."""

    def test_escalates_complex_issues(self):
        """Test that complex issues are escalated."""
        from tools.autonomous_healer import AutonomousHealer

        healer = AutonomousHealer()

        # Should escalate class definitions
        issue = {"content": "class Foo(Bar):"}
        assert healer._should_escalate(issue)

        # Should escalate dunder methods
        issue = {"content": "def __init__(self):"}
        assert healer._should_escalate(issue)

        # Should escalate async functions
        issue = {"content": "async def fetch():"}
        assert healer._should_escalate(issue)

        # Should escalate generators
        issue = {"content": "yield value"}
        assert healer._should_escalate(issue)

    def test_does_not_escalate_simple_issues(self):
        """Test that simple issues are not escalated."""
        from tools.autonomous_healer import AutonomousHealer

        healer = AutonomousHealer()

        # Should not escalate simple functions
        issue = {"content": "def foo():", "confidence": 0.8}
        assert not healer._should_escalate(issue)

        # Should not escalate simple statements
        issue = {"content": "x = Dict[Any, Any]", "confidence": 0.8}
        assert not healer._should_escalate(issue)

    def test_escalates_low_confidence(self):
        """Test that low confidence issues are escalated."""
        from tools.autonomous_healer import AutonomousHealer

        healer = AutonomousHealer()

        issue = {"content": "x = 1", "confidence": 0.2}
        assert healer._should_escalate(issue)

    def test_respects_rate_limit(self):
        """Test that healer respects rate limit."""
        from tools.autonomous_healer import AutonomousHealer
        from tools.safety import get_safety_state, MAX_FIXES_PER_HOUR

        healer = AutonomousHealer()
        state = get_safety_state()
        state.reset()

        # Use up all fixes
        for _ in range(MAX_FIXES_PER_HOUR):
            state.record_fix()

        result = healer.run_healing_cycle()
        assert result.is_ok()

        report = result.unwrap()
        assert report.rate_limited
        assert report.fixes_attempted == 0

    def test_healing_cycle_returns_report(self):
        """Test that healing cycle returns a report."""
        from tools.autonomous_healer import AutonomousHealer
        from tools.safety import get_safety_state

        healer = AutonomousHealer()
        state = get_safety_state()
        state.reset()

        # Mock the scanner to return no issues (patch where it's used)
        with patch("tools.self_healing_monitor.SelfHealingMonitor") as mock_monitor:
            mock_instance = MagicMock()
            mock_instance.scan_code_quality.return_value = []
            mock_monitor.return_value = mock_instance

            result = healer.run_healing_cycle()

            assert result.is_ok()
            report = result.unwrap()
            assert report.issues_found == 0
            assert report.fixes_attempted == 0

    def test_healing_result_dataclass(self):
        """Test HealingResult dataclass structure."""
        from tools.autonomous_healer import HealingResult
        from tools.llm_code_fixer import Fix

        fix = Fix(
            file_path="test.py",
            line_number=10,
            original="x",
            fixed="y",
            method="template",
            confidence=0.9,
        )

        result = HealingResult(
            fix=fix,
            success=True,
            tests_passed=True,
            error=None,
            rollback_performed=False,
        )

        assert result.success
        assert result.tests_passed
        assert result.error is None

    def test_healing_cycle_report_dataclass(self):
        """Test HealingCycleReport dataclass structure."""
        from datetime import datetime
        from tools.autonomous_healer import HealingCycleReport

        report = HealingCycleReport(
            timestamp=datetime.now(),
            issues_found=10,
            fixes_attempted=5,
            fixes_successful=3,
            fixes_failed=2,
        )

        assert report.issues_found == 10
        assert report.fixes_successful == 3
        assert report.results == []
        assert report.escalated_to_human == []

    def test_get_status_returns_dict(self):
        """Test that get_status returns status dictionary."""
        from tools.autonomous_healer import AutonomousHealer

        healer = AutonomousHealer()
        status = healer.get_status()

        assert isinstance(status, dict)
        assert "safety" in status
        assert "project_root" in status
        assert "llm_available" in status

    def test_dry_run_does_not_modify(self):
        """Test that dry run doesn't modify files or record fixes."""
        from tools.autonomous_healer import AutonomousHealer
        from tools.safety import get_safety_state

        healer = AutonomousHealer()
        state = get_safety_state()
        state.reset()
        initial_fixes = state.fixes_this_hour

        # Mock the scanner to return an issue (patch the import inside the function)
        with patch.dict("sys.modules", {"tools.self_healing_monitor": MagicMock()}):
            import sys
            mock_module = sys.modules["tools.self_healing_monitor"]
            mock_instance = MagicMock()
            mock_instance.scan_code_quality.return_value = [
                {
                    "file": "tools/test.py",
                    "line": 10,
                    "pattern": "bare_except",
                    "severity": "high",
                    "content": "except:",
                    "confidence": 0.8,
                }
            ]
            mock_module.SelfHealingMonitor.return_value = mock_instance

            # Mock the fixer
            with patch.object(healer.fixer, "fix_issue") as mock_fix:
                from tools.llm_code_fixer import Fix
                from shared.type_definitions.result import Ok

                mock_fix.return_value = Ok(
                    Fix(
                        file_path="tools/test.py",
                        line_number=10,
                        original="except:",
                        fixed="except Exception as e:",
                        method="template",
                        confidence=0.95,
                    )
                )

                result = healer.run_healing_cycle(dry_run=True)

                assert result.is_ok()
                # Should not record fix in dry run
                assert state.fixes_this_hour == initial_fixes


class TestFixPatternStore:
    """Tests for pattern store integration (Phase 2 complete)."""

    def test_pattern_store_finds_matching_pattern(self):
        """Test that pattern store finds matching patterns."""
        from tools.llm_code_fixer import LLMCodeFixer

        fixer = LLMCodeFixer()
        result = fixer._try_pattern_fix("tools/test.py", 10, "bare_except", "except:")

        # Pattern store should find a match for bare_except (seeded in Phase 2)
        assert result.is_ok()
        fix = result.unwrap()
        assert "Exception" in fix.fixed
        assert fix.method == "pattern"


class TestIntegration:
    """Integration tests for healer components."""

    def test_fixer_and_healer_work_together(self):
        """Test that fixer and healer integrate correctly."""
        from tools.autonomous_healer import AutonomousHealer
        from tools.llm_code_fixer import LLMCodeFixer

        healer = AutonomousHealer()

        # Healer should have a fixer
        assert isinstance(healer.fixer, LLMCodeFixer)

        # Fixer should be initialized
        assert healer.fixer._llm_available is None  # Not checked yet

    def test_safety_state_shared(self):
        """Test that safety state is shared correctly."""
        from tools.autonomous_healer import AutonomousHealer
        from tools.safety import get_safety_state

        healer = AutonomousHealer()
        global_state = get_safety_state()

        assert healer.safety_state is global_state

    def test_rollback_manager_initialized(self):
        """Test that rollback manager is initialized."""
        from tools.autonomous_healer import AutonomousHealer
        from tools.rollback import RollbackManager

        healer = AutonomousHealer()
        assert isinstance(healer.rollback, RollbackManager)
