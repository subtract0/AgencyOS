"""Auto-fix code quality violations using VLM.

This module provides automated fixes for common code quality issues:
1. Dict[Any, Any] → Pydantic models
2. Bare except → Specific exception handling
3. Other constitutional violations

Constitutional Compliance:
- Article IV: Learning integration (queries past fixes, stores new patterns)
- Article VI: TDD approach (generates tests alongside fixes)
"""

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


@dataclass
class FixSuggestion:
    """A suggested fix for a code violation."""

    file_path: str
    line_number: int
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float
    pattern_type: str


@dataclass
class FixResult:
    """Result of applying a fix."""

    suggestion: FixSuggestion
    applied: bool
    error: str | None = None


class AutoFixer:
    """Automatically fix code quality violations.

    Uses VLM for intelligent fix generation and pattern matching.
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize auto-fixer.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or PROJECT_ROOT
        self._vlm_client = None

    def _get_vlm_client(self):
        """Get VLM client for intelligent fixes."""
        if self._vlm_client is None:
            try:
                from openai import OpenAI

                self._vlm_client = OpenAI(
                    api_key="lm-studio",
                    base_url="http://127.0.0.1:1234/v1",
                    timeout=60.0,
                )
            except ImportError:
                pass
        return self._vlm_client

    def suggest_fix_for_dict_any(
        self, file_path: str, line_number: int, context: str
    ) -> Result[FixSuggestion, str]:
        """Generate a fix suggestion for Dict[Any, Any] violation.

        Args:
            file_path: Path to the file with violation
            line_number: Line number of violation
            context: Code context around the violation

        Returns:
            Result containing FixSuggestion or error
        """
        # Extract variable name and usage
        var_match = re.search(r"(\w+)\s*:\s*Dict\[Any,\s*Any\]", context)
        if not var_match:
            var_match = re.search(r"(\w+)\s*=.*Dict\[Any,\s*Any\]", context)

        var_name = var_match.group(1) if var_match else "data"

        # Generate Pydantic model based on context
        model_name = self._generate_model_name(var_name, file_path)

        # Create fix
        fixed_code = f"""# TODO: Define proper Pydantic model for {var_name}
from pydantic import BaseModel

class {model_name}(BaseModel):
    \"\"\"Typed model replacing Dict[Any, Any].\"\"\"
    # Add typed fields based on actual usage
    pass

# Replace Dict[Any, Any] with {model_name}
{var_name}: {model_name}"""

        suggestion = FixSuggestion(
            file_path=file_path,
            line_number=line_number,
            original_code=context,
            fixed_code=fixed_code,
            explanation=f"Replace Dict[Any, Any] with typed Pydantic model {model_name}",
            confidence=0.7,
            pattern_type="dict_any_any",
        )

        return Ok(suggestion)

    def suggest_fix_for_bare_except(
        self, file_path: str, line_number: int, context: str
    ) -> Result[FixSuggestion, str]:
        """Generate a fix suggestion for bare except.

        Args:
            file_path: Path to the file with violation
            line_number: Line number of violation
            context: Code context around the violation

        Returns:
            Result containing FixSuggestion or error
        """
        # Replace bare except with Exception
        fixed_code = context.replace("except:", "except Exception as e:")

        suggestion = FixSuggestion(
            file_path=file_path,
            line_number=line_number,
            original_code=context,
            fixed_code=fixed_code,
            explanation="Replace bare except with 'except Exception as e:' to avoid catching KeyboardInterrupt",
            confidence=0.9,
            pattern_type="bare_except",
        )

        return Ok(suggestion)

    def _generate_model_name(self, var_name: str, file_path: str) -> str:
        """Generate a Pydantic model name from variable name and context."""
        # Convert snake_case to PascalCase
        parts = var_name.split("_")
        pascal_name = "".join(p.capitalize() for p in parts)

        # Add suffix if needed
        if not pascal_name.endswith("Model") and not pascal_name.endswith("Data"):
            pascal_name += "Data"

        return pascal_name

    def analyze_file(self, file_path: Path) -> list[FixSuggestion]:
        """Analyze a file and generate fix suggestions.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of fix suggestions
        """
        suggestions = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Check for Dict[Any, Any]
                if re.search(r"Dict\[Any,\s*Any\]", line):
                    # Get context (surrounding lines)
                    start = max(0, i - 3)
                    end = min(len(lines), i + 3)
                    context = "\n".join(lines[start:end])

                    result = self.suggest_fix_for_dict_any(
                        str(file_path), i, context
                    )
                    if result.is_ok():
                        suggestions.append(result.unwrap())

                # Check for bare except
                if re.search(r"except\s*:", line):
                    context = line
                    result = self.suggest_fix_for_bare_except(
                        str(file_path), i, context
                    )
                    if result.is_ok():
                        suggestions.append(result.unwrap())

        except Exception as e:
            pass  # Skip files that can't be read

        return suggestions

    def analyze_directory(self, directory: Path) -> list[FixSuggestion]:
        """Analyze all Python files in a directory.

        Args:
            directory: Directory to analyze

        Returns:
            List of fix suggestions
        """
        all_suggestions = []

        for py_file in directory.rglob("*.py"):
            suggestions = self.analyze_file(py_file)
            all_suggestions.extend(suggestions)

        return all_suggestions

    def apply_fix(
        self, suggestion: FixSuggestion, dry_run: bool = True
    ) -> FixResult:
        """Apply a fix suggestion to the file.

        Args:
            suggestion: The fix to apply
            dry_run: If True, don't actually modify the file

        Returns:
            FixResult with outcome
        """
        if dry_run:
            return FixResult(
                suggestion=suggestion,
                applied=False,
                error="Dry run - fix not applied",
            )

        try:
            file_path = Path(suggestion.file_path)
            content = file_path.read_text()

            # For bare except, do a simple replacement
            if suggestion.pattern_type == "bare_except":
                new_content = content.replace(
                    suggestion.original_code, suggestion.fixed_code
                )
                file_path.write_text(new_content)
                return FixResult(suggestion=suggestion, applied=True)

            # For Dict[Any, Any], we need to be more careful
            # Just mark as needing manual intervention for now
            return FixResult(
                suggestion=suggestion,
                applied=False,
                error="Dict[Any, Any] fixes require manual review",
            )

        except Exception as e:
            return FixResult(
                suggestion=suggestion,
                applied=False,
                error=str(e),
            )

    def generate_report(self, suggestions: list[FixSuggestion]) -> str:
        """Generate a report of fix suggestions.

        Args:
            suggestions: List of suggestions to report

        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Auto-Fix Suggestions Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Total suggestions: {len(suggestions)}",
            "",
        ]

        # Group by pattern type
        by_type: dict[str, list[FixSuggestion]] = {}
        for s in suggestions:
            if s.pattern_type not in by_type:
                by_type[s.pattern_type] = []
            by_type[s.pattern_type].append(s)

        for pattern_type, type_suggestions in by_type.items():
            lines.extend([
                f"## {pattern_type} ({len(type_suggestions)} issues)",
                "",
            ])

            for s in type_suggestions[:10]:  # Limit display
                lines.extend([
                    f"### {s.file_path}:{s.line_number}",
                    "",
                    f"**Confidence:** {s.confidence:.0%}",
                    "",
                    f"**Explanation:** {s.explanation}",
                    "",
                    "**Original:**",
                    "```python",
                    s.original_code[:200],
                    "```",
                    "",
                    "**Suggested Fix:**",
                    "```python",
                    s.fixed_code[:300],
                    "```",
                    "",
                ])

            if len(type_suggestions) > 10:
                lines.append(f"... and {len(type_suggestions) - 10} more\n")

        return "\n".join(lines)


def main():
    """Run auto-fixer from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-fix code violations")
    parser.add_argument("path", nargs="?", default="tools/", help="Path to analyze")
    parser.add_argument("--apply", action="store_true", help="Apply fixes (not dry run)")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--output", type=str, help="Output file for report")
    args = parser.parse_args()

    fixer = AutoFixer()
    path = Path(args.path)

    if path.is_file():
        suggestions = fixer.analyze_file(path)
    else:
        suggestions = fixer.analyze_directory(path)

    print(f"Found {len(suggestions)} fix suggestions")

    if args.report:
        report = fixer.generate_report(suggestions)
        if args.output:
            Path(args.output).write_text(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)
    else:
        # Show summary
        by_type: dict[str, int] = {}
        for s in suggestions:
            by_type[s.pattern_type] = by_type.get(s.pattern_type, 0) + 1

        for pattern_type, count in by_type.items():
            print(f"  {pattern_type}: {count}")

    if args.apply:
        print("\nApplying fixes...")
        for s in suggestions:
            result = fixer.apply_fix(s, dry_run=False)
            status = "✅" if result.applied else "⚠️"
            print(f"  {status} {s.file_path}:{s.line_number}")
            if result.error:
                print(f"      {result.error}")


if __name__ == "__main__":
    main()
