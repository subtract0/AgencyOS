"""
Tests for Predictive Analyzer (Phase 3).

Tests the pre-commit predictive analysis system including:
- Pattern detection
- Risk scoring
- Recommendation logic
- AST analysis
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestPredictedIssue:
    """Tests for PredictedIssue dataclass."""

    def test_predicted_issue_creation(self):
        """Test creating a predicted issue."""
        from tools.predictive_analyzer import PredictedIssue

        issue = PredictedIssue(
            file_path="test.py",
            line_number=10,
            issue_type="bare_except",
            severity="high",
            confidence=0.9,
            message="Bare except clause",
            suggestion="Use specific exception",
            can_auto_fix=True,
        )

        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.issue_type == "bare_except"
        assert issue.severity == "high"
        assert issue.confidence == 0.9
        assert issue.can_auto_fix is True


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_analysis_result_creation(self):
        """Test creating an analysis result."""
        from datetime import datetime

        from tools.predictive_analyzer import AnalysisResult, PredictedIssue

        issues = [
            PredictedIssue(
                file_path="test.py",
                line_number=1,
                issue_type="bare_except",
                severity="high",
                confidence=0.9,
                message="Test",
            )
        ]

        result = AnalysisResult(
            timestamp=datetime.now(),
            files_analyzed=1,
            issues_found=issues,
            risk_score=15.0,
            recommendation="review",
            auto_fixable=1,
        )

        assert result.files_analyzed == 1
        assert len(result.issues_found) == 1
        assert result.risk_score == 15.0
        assert result.recommendation == "review"
        assert result.auto_fixable == 1


class TestPredictiveAnalyzer:
    """Tests for PredictiveAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        from tools.predictive_analyzer import PredictiveAnalyzer

        return PredictiveAnalyzer()

    def test_analyze_file_detects_bare_except(self, analyzer, tmp_path):
        """Test detection of bare except clause."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
try:
    x = 1
except:
    pass
""")

        result = analyzer.analyze_file(str(test_file))
        assert result.is_ok()

        issues = result.unwrap()
        bare_excepts = [i for i in issues if i.issue_type == "bare_except"]
        assert len(bare_excepts) >= 1

    def test_analyze_file_detects_eval(self, analyzer, tmp_path):
        """Test detection of eval usage."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
result = eval("1 + 1")
""")

        result = analyzer.analyze_file(str(test_file))
        assert result.is_ok()

        issues = result.unwrap()
        evals = [i for i in issues if i.issue_type == "eval_usage"]
        assert len(evals) >= 1
        assert evals[0].severity == "critical"

    def test_analyze_file_detects_shell_injection(self, analyzer, tmp_path):
        """Test detection of shell injection risk."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import subprocess
subprocess.call(cmd, shell=True)
""")

        result = analyzer.analyze_file(str(test_file))
        assert result.is_ok()

        issues = result.unwrap()
        shell_issues = [i for i in issues if i.issue_type == "shell_injection"]
        assert len(shell_issues) >= 1
        assert shell_issues[0].severity == "critical"

    def test_analyze_file_detects_long_function(self, analyzer, tmp_path):
        """Test detection of functions exceeding 50 lines."""
        # Create a function with 60+ lines
        lines = ["    line = x"] * 60
        func_body = "\n".join(lines)
        test_file = tmp_path / "test.py"
        test_file.write_text(f"""
def long_function():
{func_body}
    return x
""")

        result = analyzer.analyze_file(str(test_file))
        assert result.is_ok()

        issues = result.unwrap()
        long_funcs = [i for i in issues if i.issue_type == "long_function"]
        assert len(long_funcs) >= 1

    def test_analyze_file_detects_todo_comments(self, analyzer, tmp_path):
        """Test detection of TODO comments."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
# TODO: fix this later
def broken():
    pass
""")

        result = analyzer.analyze_file(str(test_file))
        assert result.is_ok()

        issues = result.unwrap()
        todos = [i for i in issues if i.issue_type == "todo_comment"]
        assert len(todos) >= 1

    def test_analyze_clean_file(self, analyzer, tmp_path):
        """Test that clean code has low risk score."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def add(a: int, b: int) -> int:
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b
""")

        result = analyzer.analyze_file(str(test_file))
        assert result.is_ok()

        issues = result.unwrap()
        # Clean code should have minimal high-severity issues
        high_issues = [i for i in issues if i.severity in ("critical", "high")]
        assert len(high_issues) == 0

    def test_analyze_diff(self, analyzer):
        """Test analyzing diff content."""
        diff = """
diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,3 +1,5 @@
 def foo():
-    return 1
+    try:
+        return 1
+    except:
+        pass
"""

        result = analyzer.analyze_diff(diff)
        assert result.is_ok()

        issues = result.unwrap()
        bare_excepts = [i for i in issues if i.issue_type == "bare_except"]
        assert len(bare_excepts) >= 1

    def test_risk_score_calculation(self, analyzer):
        """Test risk score calculation."""
        from tools.predictive_analyzer import PredictedIssue

        # Critical issues should have high weight
        issues = [
            PredictedIssue(
                file_path="test.py",
                line_number=1,
                issue_type="eval_usage",
                severity="critical",
                confidence=0.9,
                message="eval",
            )
        ]

        score = analyzer._calculate_risk_score(issues)
        assert score >= 20  # Critical issues have weight 25

    def test_recommendation_block_on_critical(self, analyzer):
        """Test that critical issues result in block recommendation."""
        from tools.predictive_analyzer import PredictedIssue

        issues = [
            PredictedIssue(
                file_path="test.py",
                line_number=1,
                issue_type="eval_usage",
                severity="critical",
                confidence=0.9,
                message="eval",
            )
        ]

        risk_score = analyzer._calculate_risk_score(issues)
        recommendation = analyzer._get_recommendation(risk_score, issues)
        assert recommendation == "block"

    def test_recommendation_proceed_on_clean(self, analyzer):
        """Test that clean code gets proceed recommendation."""
        issues = []
        recommendation = analyzer._get_recommendation(0, issues)
        assert recommendation == "proceed"

    def test_auto_fix_flag(self, analyzer, tmp_path):
        """Test that bare_except is marked as auto-fixable."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
try:
    x = 1
except:
    pass
""")

        result = analyzer.analyze_file(str(test_file))
        assert result.is_ok()

        issues = result.unwrap()
        bare_excepts = [i for i in issues if i.issue_type == "bare_except"]
        assert len(bare_excepts) >= 1
        assert bare_excepts[0].can_auto_fix is True


class TestIssuePatterns:
    """Tests for issue detection patterns."""

    def test_pattern_count(self):
        """Test that we have expected patterns defined."""
        from tools.predictive_analyzer import ISSUE_PATTERNS

        assert len(ISSUE_PATTERNS) >= 8

    def test_critical_patterns_defined(self):
        """Test that critical patterns are defined."""
        from tools.predictive_analyzer import ISSUE_PATTERNS

        critical_patterns = [p for p in ISSUE_PATTERNS if p["severity"] == "critical"]
        assert len(critical_patterns) >= 3  # eval, exec, shell_injection

    def test_pattern_has_required_fields(self):
        """Test that all patterns have required fields."""
        from tools.predictive_analyzer import ISSUE_PATTERNS

        for pattern in ISSUE_PATTERNS:
            assert "name" in pattern
            assert "severity" in pattern
            assert "message" in pattern
            # pattern can be None for AST-based detection
