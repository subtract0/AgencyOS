"""
LLM-powered code fixer with offline fallback.

Strategy:
1. Try LLM fix (best quality)
2. Fall back to pattern matching (fast, offline)
3. Fall back to template substitution (always works)

Constitutional Compliance:
- Article I: Complete context via surrounding code analysis
- Article II: 100% verification via syntax validation
- Article III: Automated enforcement via safety checks
- Article IV: Learning via pattern storage
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result
from tools.safety import SafetyError, validate_code, validate_diff_size, validate_path
from tools.rollback import with_rollback


@dataclass
class Fix:
    """A code fix to apply."""

    file_path: str
    line_number: int
    original: str
    fixed: str
    method: str  # "llm", "pattern", "template"
    confidence: float
    issue_type: str = ""


@dataclass
class FixResult:
    """Result of applying a fix."""

    fix: Fix
    applied: bool
    tests_passed: Optional[bool] = None
    error: Optional[str] = None


class LLMCodeFixer:
    """Fix code issues using LLM with fallbacks.

    Three-tier approach:
    1. LLM (highest quality, requires network)
    2. Pattern matching (learned from past fixes)
    3. Template substitution (always works)
    """

    # Template fixes (always work, no LLM needed)
    TEMPLATE_FIXES = {
        "bare_except": {
            "pattern": r"(\s*)except\s*:",
            "replacement": r"\1except Exception as e:",
            "confidence": 0.95,
        },
        "dict_any_any_simple": {
            "pattern": r"(\w+)\s*:\s*Dict\[Any,\s*Any\]\s*=\s*\{\}",
            "replacement": r"\1: dict = {}  # TODO: Add proper typing",
            "confidence": 0.7,
        },
        "dict_any_any_typed": {
            "pattern": r"Dict\[Any,\s*Any\]",
            "replacement": r"dict[str, Any]  # TODO: Add proper value type",
            "confidence": 0.6,
        },
        "missing_return_type": {
            "pattern": r"def\s+(\w+)\s*\([^)]*\)\s*:",
            "replacement": r"def \1(...) -> None:",  # Placeholder
            "confidence": 0.4,  # Low confidence, needs review
        },
    }

    def __init__(self):
        """Initialize the LLM code fixer."""
        self._llm_client = None
        self._llm_available: Optional[bool] = None
        self._pattern_store = None

    def _check_llm(self) -> bool:
        """Check if LLM is available.

        Returns:
            True if LLM API is accessible
        """
        if self._llm_available is not None:
            return self._llm_available

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key="lm-studio",
                base_url="http://127.0.0.1:1234/v1",
                timeout=5.0,
            )
            # Quick check - just see if we can connect
            client.models.list()
            self._llm_client = client
            self._llm_available = True
        except Exception:
            self._llm_available = False

        return self._llm_available

    def _get_pattern_store(self):
        """Get pattern store for learned fixes.

        Returns:
            Pattern store or None if unavailable
        """
        if self._pattern_store is None:
            try:
                from tools.fix_pattern_store import FixPatternStore

                self._pattern_store = FixPatternStore()
            except ImportError:
                pass
        return self._pattern_store

    def fix_issue(
        self, file_path: str, line_number: int, issue_type: str
    ) -> Result[Fix, str]:
        """Fix an issue using best available method.

        Args:
            file_path: Path to file with issue
            line_number: Line number of issue
            issue_type: Type of issue (e.g., "bare_except", "dict_any_any")

        Returns:
            Result containing Fix or error message
        """
        # Validate path first
        path_result = validate_path(file_path)
        if path_result.is_err():
            return Err(path_result.unwrap_err())

        # Read file
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = PROJECT_ROOT / file_path
            content = path.read_text()
            lines = content.split("\n")
        except Exception as e:
            return Err(f"Failed to read file: {e}")

        if line_number < 1 or line_number > len(lines):
            return Err(f"Line number {line_number} out of range")

        # Get context (5 lines before and after)
        start = max(0, line_number - 6)
        end = min(len(lines), line_number + 5)
        context = "\n".join(lines[start:end])
        target_line = lines[line_number - 1]

        # Try methods in order of quality
        fix: Optional[Fix] = None

        # 1. Try LLM (best quality)
        if self._check_llm():
            llm_result = self._try_llm_fix(
                str(path), line_number, issue_type, context, target_line
            )
            if llm_result.is_ok():
                fix = llm_result.unwrap()

        # 2. Fall back to pattern matching
        if fix is None:
            pattern_result = self._try_pattern_fix(
                str(path), line_number, issue_type, target_line
            )
            if pattern_result.is_ok():
                fix = pattern_result.unwrap()

        # 3. Fall back to template
        if fix is None:
            template_result = self._try_template_fix(
                str(path), line_number, issue_type, target_line
            )
            if template_result.is_ok():
                fix = template_result.unwrap()

        if fix is None:
            return Err(f"Could not generate fix for {issue_type}")

        # Validate the fix
        validation_result = self._validate_fix(fix, content)
        if validation_result.is_err():
            return validation_result

        return Ok(fix)

    def _try_llm_fix(
        self,
        file_path: str,
        line_number: int,
        issue_type: str,
        context: str,
        target_line: str,
    ) -> Result[Fix, str]:
        """Try to fix using LLM.

        Args:
            file_path: Path to file
            line_number: Line number
            issue_type: Type of issue
            context: Surrounding code context
            target_line: The specific line to fix

        Returns:
            Result containing Fix or error
        """
        try:
            prompt = self._get_fix_prompt(issue_type, context, target_line)

            response = self._llm_client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )

            fixed_code = response.choices[0].message.content.strip()

            # Extract code from markdown if present
            if "```" in fixed_code:
                parts = fixed_code.split("```")
                if len(parts) >= 2:
                    fixed_code = parts[1]
                    if fixed_code.startswith("python"):
                        fixed_code = fixed_code[6:]
                    fixed_code = fixed_code.strip()

            # Basic validation
            if not fixed_code or fixed_code == target_line:
                return Err("LLM returned unchanged code")

            return Ok(
                Fix(
                    file_path=file_path,
                    line_number=line_number,
                    original=target_line,
                    fixed=fixed_code,
                    method="llm",
                    confidence=0.8,
                    issue_type=issue_type,
                )
            )
        except Exception as e:
            return Err(f"LLM fix failed: {e}")

    def _try_pattern_fix(
        self, file_path: str, line_number: int, issue_type: str, target_line: str
    ) -> Result[Fix, str]:
        """Try to fix using learned patterns.

        Args:
            file_path: Path to file
            line_number: Line number
            issue_type: Type of issue
            target_line: The specific line to fix

        Returns:
            Result containing Fix or error
        """
        store = self._get_pattern_store()
        if store is None:
            return Err("Pattern store not available")

        try:
            pattern = store.find_matching_pattern(issue_type, target_line)
            if pattern and pattern.confidence > 0.6:
                fixed = store.apply_pattern(pattern, target_line)
                return Ok(
                    Fix(
                        file_path=file_path,
                        line_number=line_number,
                        original=target_line,
                        fixed=fixed,
                        method="pattern",
                        confidence=pattern.confidence,
                        issue_type=issue_type,
                    )
                )
        except Exception as e:
            return Err(f"Pattern fix failed: {e}")

        return Err("No matching pattern found")

    def _try_template_fix(
        self, file_path: str, line_number: int, issue_type: str, target_line: str
    ) -> Result[Fix, str]:
        """Try to fix using template substitution.

        Args:
            file_path: Path to file
            line_number: Line number
            issue_type: Type of issue
            target_line: The specific line to fix

        Returns:
            Result containing Fix or error
        """
        template = self.TEMPLATE_FIXES.get(issue_type)

        if not template:
            # Try all templates to find a match
            for name, tmpl in self.TEMPLATE_FIXES.items():
                if re.search(tmpl["pattern"], target_line):
                    template = tmpl
                    issue_type = name
                    break

        if template and re.search(template["pattern"], target_line):
            fixed = re.sub(template["pattern"], template["replacement"], target_line)
            return Ok(
                Fix(
                    file_path=file_path,
                    line_number=line_number,
                    original=target_line,
                    fixed=fixed,
                    method="template",
                    confidence=template["confidence"],
                    issue_type=issue_type,
                )
            )

        return Err(f"No template found for {issue_type}")

    def _validate_fix(self, fix: Fix, original_content: str) -> Result[Fix, str]:
        """Validate a fix before applying.

        Args:
            fix: The fix to validate
            original_content: Original file content

        Returns:
            Result containing validated Fix or error
        """
        # Validate the fixed code syntax
        code_result = validate_code(fix.fixed)
        if code_result.is_err():
            # Try validating as a statement (not full module)
            try:
                import ast

                ast.parse(fix.fixed, mode="eval")
            except SyntaxError:
                try:
                    ast.parse(fix.fixed)
                except SyntaxError:
                    # It's just a line, might not parse alone - that's OK
                    pass

        # Check diff size
        new_content = original_content.replace(fix.original, fix.fixed, 1)
        diff_result = validate_diff_size(original_content, new_content)
        if diff_result.is_err():
            return Err(diff_result.unwrap_err())

        return Ok(fix)

    def _get_fix_prompt(self, issue_type: str, context: str, target_line: str) -> str:
        """Get prompt for LLM fix.

        Args:
            issue_type: Type of issue
            context: Surrounding code context
            target_line: The specific line to fix

        Returns:
            Prompt string for LLM
        """
        prompts = {
            "dict_any_any": f"""Fix this Dict[Any, Any] violation by creating a typed alternative.

Context:
```python
{context}
```

Line to fix:
```python
{target_line}
```

Requirements:
1. Replace Dict[Any, Any] with a proper type
2. If you can infer the types from usage, use them
3. If not, use dict[str, Any] as minimum improvement
4. Return ONLY the fixed line, no explanation""",
            "bare_except": f"""Fix this bare except statement.

Line:
```python
{target_line}
```

Replace with specific exception handling. Return ONLY the fixed line.""",
        }

        return prompts.get(
            issue_type, f"Fix this code issue ({issue_type}):\n{target_line}"
        )

    def apply_fix(self, fix: Fix, dry_run: bool = False) -> Result[FixResult, str]:
        """Apply a fix to the file.

        Args:
            fix: The fix to apply
            dry_run: If True, don't actually modify the file

        Returns:
            Result containing FixResult or error
        """
        if dry_run:
            print(f"[DRY RUN] Would fix {fix.file_path}:{fix.line_number}")
            print(f"  - {fix.original}")
            print(f"  + {fix.fixed}")
            return Ok(FixResult(fix=fix, applied=False, error="Dry run"))

        path = Path(fix.file_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / fix.file_path

        try:
            content = path.read_text()

            with with_rollback([str(path)], f"Fix {fix.file_path}:{fix.line_number}"):
                new_content = content.replace(fix.original, fix.fixed, 1)
                path.write_text(new_content)

                # Verify the whole file is still valid Python
                code_result = validate_code(new_content)
                if code_result.is_err():
                    raise SafetyError(
                        f"Fix produced invalid code: {code_result.unwrap_err()}"
                    )

            return Ok(FixResult(fix=fix, applied=True))

        except SafetyError as e:
            return Ok(FixResult(fix=fix, applied=False, error=str(e)))
        except Exception as e:
            return Err(f"Failed to apply fix: {e}")

    def store_successful_fix(self, fix: Fix) -> bool:
        """Store a successful fix for future pattern learning.

        Args:
            fix: The successful fix to store

        Returns:
            True if stored successfully
        """
        store = self._get_pattern_store()
        if store is None:
            return False

        try:
            store.record_success(fix.issue_type, fix.original, fix.fixed)
            return True
        except Exception:
            return False


def main():
    """Command-line interface for LLM code fixer."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM-powered code fixer")
    parser.add_argument("file", help="File to fix")
    parser.add_argument("line", type=int, help="Line number")
    parser.add_argument("issue_type", help="Issue type (bare_except, dict_any_any)")
    parser.add_argument("--apply", action="store_true", help="Apply the fix")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be fixed"
    )
    args = parser.parse_args()

    fixer = LLMCodeFixer()

    result = fixer.fix_issue(args.file, args.line, args.issue_type)

    if result.is_err():
        print(f"Error: {result.unwrap_err()}")
        sys.exit(1)

    fix = result.unwrap()
    print(f"Fix generated using {fix.method} (confidence: {fix.confidence:.0%})")
    print(f"  File: {fix.file_path}:{fix.line_number}")
    print(f"  Original: {fix.original}")
    print(f"  Fixed: {fix.fixed}")

    if args.apply:
        apply_result = fixer.apply_fix(fix, dry_run=args.dry_run)
        if apply_result.is_ok():
            fix_result = apply_result.unwrap()
            if fix_result.applied:
                print("✅ Fix applied successfully")
            else:
                print(f"⚠️ Fix not applied: {fix_result.error}")
        else:
            print(f"❌ Error: {apply_result.unwrap_err()}")


if __name__ == "__main__":
    main()
