"""
Predictive Analyzer - Pre-commit code quality prediction.

Analyzes code changes before commit to predict quality issues.
Uses historical patterns and heuristics to prevent issues proactively.

Constitutional Compliance:
- Article III: Automated enforcement (pre-commit prevention)
- Article IV: Learning integration (uses historical patterns)
"""

import ast
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


@dataclass
class PredictedIssue:
    """A predicted code quality issue."""

    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    confidence: float
    message: str
    suggestion: Optional[str] = None
    can_auto_fix: bool = False


@dataclass
class AnalysisResult:
    """Result of predictive analysis."""

    timestamp: datetime
    files_analyzed: int
    issues_found: list[PredictedIssue]
    risk_score: float  # 0-100
    recommendation: str  # 'proceed', 'review', 'block'
    auto_fixable: int = 0


# Issue detection patterns
ISSUE_PATTERNS = [
    {
        "name": "bare_except",
        "pattern": r"^\s*except\s*:",
        "severity": "high",
        "message": "Bare except clause catches all exceptions including KeyboardInterrupt",
        "suggestion": "Use 'except Exception:' or a specific exception type",
        "can_auto_fix": True,
    },
    {
        "name": "dict_any_any",
        "pattern": r"Dict\[Any,\s*Any\]",
        "severity": "medium",
        "message": "Dict[Any, Any] defeats type checking",
        "suggestion": "Use specific types or dict[str, Any] at minimum",
        "can_auto_fix": False,
    },
    {
        "name": "eval_usage",
        "pattern": r"\beval\s*\(",
        "severity": "critical",
        "message": "eval() is a security risk",
        "suggestion": "Use ast.literal_eval() for safe evaluation or refactor",
        "can_auto_fix": False,
    },
    {
        "name": "exec_usage",
        "pattern": r"\bexec\s*\(",
        "severity": "critical",
        "message": "exec() is a security risk",
        "suggestion": "Refactor to avoid dynamic code execution",
        "can_auto_fix": False,
    },
    {
        "name": "shell_injection",
        "pattern": r"subprocess\.(call|run|Popen).*shell\s*=\s*True",
        "severity": "critical",
        "message": "shell=True is a potential command injection vulnerability",
        "suggestion": "Pass command as list without shell=True",
        "can_auto_fix": False,
    },
    {
        "name": "hardcoded_secret",
        "pattern": r"(password|api_key|secret|token)\s*=\s*['\"][^'\"]+['\"]",
        "severity": "critical",
        "message": "Potential hardcoded secret detected",
        "suggestion": "Use environment variables or secret management",
        "can_auto_fix": False,
    },
    {
        "name": "print_statement",
        "pattern": r"^\s*print\s*\(",
        "severity": "low",
        "message": "print() statement may be debug code",
        "suggestion": "Use logging instead or remove if debug",
        "can_auto_fix": False,
    },
    {
        "name": "todo_comment",
        "pattern": r"#\s*(TODO|FIXME|XXX|HACK)",
        "severity": "low",
        "message": "TODO/FIXME comment indicates incomplete code",
        "suggestion": "Complete the TODO before committing or create a tracking issue",
        "can_auto_fix": False,
    },
    {
        "name": "long_function",
        "pattern": None,  # AST-based detection
        "severity": "medium",
        "message": "Function exceeds 50 lines (constitutional limit)",
        "suggestion": "Refactor into smaller, focused functions",
        "can_auto_fix": False,
    },
    {
        "name": "missing_return_type",
        "pattern": r"^\s*def\s+\w+\s*\([^)]*\)\s*:",
        "severity": "low",
        "message": "Function missing return type annotation",
        "suggestion": "Add return type annotation for type safety",
        "can_auto_fix": False,
    },
]


class PredictiveAnalyzer:
    """
    Analyzes code changes to predict quality issues.

    Uses pattern matching, AST analysis, and historical data
    to identify potential issues before they're committed.
    """

    def __init__(self):
        """Initialize the predictive analyzer."""
        self._pattern_store = None
        self._issue_history: list[dict] = []

    def _init_pattern_store(self) -> bool:
        """Initialize pattern store for historical patterns."""
        if self._pattern_store is not None:
            return True

        try:
            from tools.fix_pattern_store import FixPatternStore

            self._pattern_store = FixPatternStore()
            return True
        except ImportError:
            return False

    def analyze_staged_changes(self) -> Result[AnalysisResult, str]:
        """
        Analyze git staged changes for quality issues.

        Returns:
            Result containing analysis or error
        """
        # Get staged files
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            staged_files = [
                f.strip()
                for f in result.stdout.split("\n")
                if f.strip() and f.endswith(".py")
            ]
        except Exception as e:
            return Err(f"Failed to get staged files: {e}")

        if not staged_files:
            return Ok(
                AnalysisResult(
                    timestamp=datetime.now(),
                    files_analyzed=0,
                    issues_found=[],
                    risk_score=0,
                    recommendation="proceed",
                )
            )

        all_issues = []

        for file_path in staged_files:
            issues = self._analyze_file(file_path)
            all_issues.extend(issues)

        # Calculate risk score
        risk_score = self._calculate_risk_score(all_issues)

        # Determine recommendation
        recommendation = self._get_recommendation(risk_score, all_issues)

        # Count auto-fixable issues
        auto_fixable = sum(1 for i in all_issues if i.can_auto_fix)

        return Ok(
            AnalysisResult(
                timestamp=datetime.now(),
                files_analyzed=len(staged_files),
                issues_found=all_issues,
                risk_score=risk_score,
                recommendation=recommendation,
                auto_fixable=auto_fixable,
            )
        )

    def analyze_file(self, file_path: str) -> Result[list[PredictedIssue], str]:
        """
        Analyze a single file for quality issues.

        Args:
            file_path: Path to file to analyze

        Returns:
            Result containing list of issues
        """
        issues = self._analyze_file(file_path)
        return Ok(issues)

    def analyze_diff(self, diff_content: str) -> Result[list[PredictedIssue], str]:
        """
        Analyze a diff for quality issues.

        Args:
            diff_content: Git diff content

        Returns:
            Result containing list of issues
        """
        issues = []
        current_file = None
        line_offset = 0

        for line in diff_content.split("\n"):
            # Track current file
            if line.startswith("+++ b/"):
                current_file = line[6:]
                continue

            # Track line numbers from hunk header
            if line.startswith("@@"):
                match = re.search(r"\+(\d+)", line)
                if match:
                    line_offset = int(match.group(1))
                continue

            # Only analyze added lines
            if line.startswith("+") and not line.startswith("+++"):
                added_code = line[1:]  # Remove the leading +

                # Check patterns
                for pattern_def in ISSUE_PATTERNS:
                    if pattern_def["pattern"] is None:
                        continue

                    if re.search(pattern_def["pattern"], added_code, re.IGNORECASE):
                        issues.append(
                            PredictedIssue(
                                file_path=current_file or "unknown",
                                line_number=line_offset,
                                issue_type=pattern_def["name"],
                                severity=pattern_def["severity"],
                                confidence=0.9,
                                message=pattern_def["message"],
                                suggestion=pattern_def.get("suggestion"),
                                can_auto_fix=pattern_def.get("can_auto_fix", False),
                            )
                        )

                line_offset += 1

        return Ok(issues)

    def _analyze_file(self, file_path: str) -> list[PredictedIssue]:
        """Analyze a file for quality issues."""
        issues = []

        try:
            path = Path(file_path)
            if not path.exists() or not path.suffix == ".py":
                return issues

            content = path.read_text()
            lines = content.split("\n")

            # Pattern-based analysis
            for line_num, line in enumerate(lines, 1):
                for pattern_def in ISSUE_PATTERNS:
                    if pattern_def["pattern"] is None:
                        continue

                    if re.search(pattern_def["pattern"], line, re.IGNORECASE):
                        issues.append(
                            PredictedIssue(
                                file_path=file_path,
                                line_number=line_num,
                                issue_type=pattern_def["name"],
                                severity=pattern_def["severity"],
                                confidence=0.9,
                                message=pattern_def["message"],
                                suggestion=pattern_def.get("suggestion"),
                                can_auto_fix=pattern_def.get("can_auto_fix", False),
                            )
                        )

            # AST-based analysis
            ast_issues = self._analyze_ast(file_path, content)
            issues.extend(ast_issues)

        except Exception:
            pass

        return issues

    def _analyze_ast(self, file_path: str, content: str) -> list[PredictedIssue]:
        """Analyze code using AST for structural issues."""
        issues = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Check for long functions
                if isinstance(node, ast.FunctionDef):
                    # Count lines
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    func_lines = end_line - start_line + 1

                    if func_lines > 50:
                        issues.append(
                            PredictedIssue(
                                file_path=file_path,
                                line_number=start_line,
                                issue_type="long_function",
                                severity="medium",
                                confidence=1.0,
                                message=f"Function '{node.name}' has {func_lines} lines (limit: 50)",
                                suggestion="Refactor into smaller functions",
                                can_auto_fix=False,
                            )
                        )

                    # Check for missing return type annotation
                    if node.returns is None and not node.name.startswith("_"):
                        issues.append(
                            PredictedIssue(
                                file_path=file_path,
                                line_number=start_line,
                                issue_type="missing_return_type",
                                severity="low",
                                confidence=0.8,
                                message=f"Function '{node.name}' missing return type",
                                suggestion="Add -> ReturnType annotation",
                                can_auto_fix=False,
                            )
                        )

        except SyntaxError:
            pass

        return issues

    def _calculate_risk_score(self, issues: list[PredictedIssue]) -> float:
        """Calculate overall risk score from issues."""
        if not issues:
            return 0.0

        severity_weights = {
            "critical": 25,
            "high": 15,
            "medium": 8,
            "low": 3,
        }

        total_weight = sum(
            severity_weights.get(issue.severity, 5) * issue.confidence
            for issue in issues
        )

        # Normalize to 0-100
        return min(100, total_weight)

    def _get_recommendation(
        self, risk_score: float, issues: list[PredictedIssue]
    ) -> str:
        """Get recommendation based on risk score and issues."""
        # Check for critical issues
        critical_count = sum(1 for i in issues if i.severity == "critical")
        if critical_count > 0:
            return "block"

        # Check risk score thresholds
        if risk_score >= 50:
            return "block"
        elif risk_score >= 25:
            return "review"
        else:
            return "proceed"

    def get_historical_patterns(self, issue_type: str) -> list[dict]:
        """Get historical fix patterns for an issue type."""
        if not self._init_pattern_store():
            return []

        patterns = []
        if issue_type in self._pattern_store.patterns:
            for pattern in self._pattern_store.patterns[issue_type]:
                patterns.append(
                    {
                        "original": pattern.original_pattern,
                        "fixed": pattern.fixed_template,
                        "confidence": pattern.confidence,
                        "success_count": pattern.success_count,
                    }
                )

        return patterns

    def record_issue_outcome(
        self, issue: PredictedIssue, was_valid: bool, fix_applied: Optional[str] = None
    ) -> None:
        """Record whether a predicted issue was valid and how it was fixed."""
        self._issue_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "predicted_confidence": issue.confidence,
                "was_valid": was_valid,
                "fix_applied": fix_applied,
            }
        )

        # Update pattern store if fix was applied
        if was_valid and fix_applied and self._init_pattern_store():
            self._pattern_store.record_success(
                issue.issue_type, issue.message, fix_applied
            )

    def get_accuracy_stats(self) -> dict:
        """Get prediction accuracy statistics."""
        if not self._issue_history:
            return {
                "total_predictions": 0,
                "valid_predictions": 0,
                "accuracy": 0.0,
            }

        total = len(self._issue_history)
        valid = sum(1 for h in self._issue_history if h["was_valid"])

        return {
            "total_predictions": total,
            "valid_predictions": valid,
            "accuracy": valid / total if total > 0 else 0.0,
            "by_type": self._get_accuracy_by_type(),
        }

    def _get_accuracy_by_type(self) -> dict:
        """Get accuracy breakdown by issue type."""
        type_stats: dict[str, dict] = {}

        for record in self._issue_history:
            issue_type = record["issue_type"]
            if issue_type not in type_stats:
                type_stats[issue_type] = {"total": 0, "valid": 0}

            type_stats[issue_type]["total"] += 1
            if record["was_valid"]:
                type_stats[issue_type]["valid"] += 1

        # Calculate accuracy
        for stats in type_stats.values():
            stats["accuracy"] = (
                stats["valid"] / stats["total"] if stats["total"] > 0 else 0.0
            )

        return type_stats


def main():
    """Command-line interface for predictive analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Predictive code analyzer")
    parser.add_argument("--staged", action="store_true", help="Analyze staged changes")
    parser.add_argument("--file", help="Analyze specific file")
    parser.add_argument("--diff", help="Analyze diff from stdin", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    analyzer = PredictiveAnalyzer()

    if args.staged:
        result = analyzer.analyze_staged_changes()
    elif args.file:
        result = analyzer.analyze_file(args.file)
    elif args.diff:
        import sys

        diff_content = sys.stdin.read()
        result = analyzer.analyze_diff(diff_content)
    else:
        parser.print_help()
        return

    if result.is_ok():
        data = result.unwrap()

        if args.json:
            import json

            if isinstance(data, AnalysisResult):
                print(
                    json.dumps(
                        {
                            "files_analyzed": data.files_analyzed,
                            "issues": [i.__dict__ for i in data.issues_found],
                            "risk_score": data.risk_score,
                            "recommendation": data.recommendation,
                            "auto_fixable": data.auto_fixable,
                        },
                        indent=2,
                    )
                )
            else:
                print(json.dumps([i.__dict__ for i in data], indent=2))
        else:
            if isinstance(data, AnalysisResult):
                print(f"\n📊 Predictive Analysis Results")
                print(f"{'=' * 50}")
                print(f"Files analyzed: {data.files_analyzed}")
                print(f"Issues found: {len(data.issues_found)}")
                print(f"Risk score: {data.risk_score:.1f}/100")
                print(f"Recommendation: {data.recommendation.upper()}")
                print(f"Auto-fixable: {data.auto_fixable}")

                if data.issues_found:
                    print(f"\n{'Issues:'}")
                    for issue in data.issues_found:
                        icon = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🔵",
                        }.get(issue.severity, "⚪")
                        print(
                            f"  {icon} {issue.file_path}:{issue.line_number} - {issue.message}"
                        )
                        if issue.suggestion:
                            print(f"     💡 {issue.suggestion}")
            else:
                print(f"\nFound {len(data)} issues:")
                for issue in data:
                    print(f"  - {issue.file_path}:{issue.line_number}: {issue.message}")
    else:
        print(f"Error: {result.unwrap_err()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
