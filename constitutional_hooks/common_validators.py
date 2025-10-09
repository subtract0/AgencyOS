"""
Common validation functions for constitutional enforcement.

These validators implement deterministic rule checking for Constitutional Articles.
"""

import json
import re
import subprocess

from constitutional_hooks.config import (
    ARTICLE_II_ALLOW_SKIPPED,
    ARTICLE_II_MIN_PASS_PERCENTAGE,
    PROMPT_DENY_LIST_PATTERNS,
)
from constitutional_hooks.errors import ConstitutionalError
from shared.type_definitions.result import Err, Ok, Result


def validate_prompt_content(prompt: str) -> Result[bool, ConstitutionalError]:
    """
    Validate user prompt against Article I rules.

    Article I requires complete context before action. Prompts that attempt to
    skip verification, use loose typing, or bypass checks violate this principle.

    Args:
        prompt: User's input prompt text

    Returns:
        Ok(True) if compliant, Err(ConstitutionalError) if violation detected
    """
    for pattern in PROMPT_DENY_LIST_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return Err(
                ConstitutionalError(
                    message=f"Prompt contains prohibited pattern '{pattern}' that violates complete context requirement",
                    rule_id="Article I",
                )
            )

    return Ok(True)


def check_test_results() -> Result[bool, ConstitutionalError]:
    """
    Check test results for Article II compliance: 100% pass rate.

    Article II mandates 100% test success before any merge or deployment.
    Skipped tests count as incomplete context (Article I).

    Returns:
        Ok(True) if all tests pass, Err(ConstitutionalError) if failures/skips
    """
    try:
        # Run pytest with JSON report
        subprocess.run(
            ["pytest", "--json-report", "--json-report-file=/tmp/pytest_report.json"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Parse JSON report
        try:
            with open("/tmp/pytest_report.json") as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Fallback: parse stdout for basic stats
            return Err(
                ConstitutionalError(
                    message=f"Failed to parse test report: {e}",
                    rule_id="Article II",
                )
            )

        total = report.get("total", 0)
        passed = report.get("passed", 0)
        failed = report.get("failed", 0)
        skipped = report.get("skipped", 0)

        # Article II: 100% pass rate required
        if total == 0:
            return Err(
                ConstitutionalError(
                    message="No tests run - verification required before action",
                    rule_id="Article II",
                )
            )

        if failed > 0:
            return Err(
                ConstitutionalError(
                    message=f"Test failures detected: {failed}/{total} tests failed",
                    rule_id="Article II",
                )
            )

        if not ARTICLE_II_ALLOW_SKIPPED and skipped > 0:
            return Err(
                ConstitutionalError(
                    message=f"Skipped tests detected: {skipped}/{total} tests skipped (incomplete context)",
                    rule_id="Article II",
                )
            )

        # Check pass percentage
        pass_rate = passed / total if total > 0 else 0.0
        if pass_rate < ARTICLE_II_MIN_PASS_PERCENTAGE:
            return Err(
                ConstitutionalError(
                    message=f"Pass rate {pass_rate:.1%} below required {ARTICLE_II_MIN_PASS_PERCENTAGE:.0%}",
                    rule_id="Article II",
                )
            )

        return Ok(True)

    except Exception as e:
        return Err(
            ConstitutionalError(
                message=f"Test execution failed: {str(e)}",
                rule_id="Article II",
            )
        )


def check_git_status() -> Result[bool, ConstitutionalError]:
    """
    Check git working directory is clean before commit/push.

    Article III requires automated merge enforcement, which depends on
    a clean git state for reliable verification.

    Returns:
        Ok(True) if clean, Err(ConstitutionalError) if dirty or error
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )

        # Porcelain output is empty for clean working directory
        if result.stdout.strip():
            return Err(
                ConstitutionalError(
                    message="Working directory has uncommitted changes - commit or stash before proceeding",
                    rule_id="Article III",
                )
            )

        return Ok(True)

    except subprocess.CalledProcessError as e:
        return Err(
            ConstitutionalError(
                message=f"Git status check failed: {e}",
                rule_id="Article III",
            )
        )
    except Exception as e:
        return Err(
            ConstitutionalError(
                message=f"Git status check error: {str(e)}",
                rule_id="Article III",
            )
        )
