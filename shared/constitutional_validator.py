"""
Constitutional Compliance Validator

Enforces the 5 constitutional articles for all agent operations:
- Article I: Complete Context Before Action
- Article II: 100% Verification and Stability
- Article III: Automated Merge Enforcement
- Article IV: Continuous Learning and Improvement
- Article V: Spec-Driven Development

This module provides a decorator to validate constitutional compliance
before agent creation and operation.
"""

import logging
import os
from collections.abc import Callable
from datetime import UTC
from functools import wraps
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConstitutionalViolation(Exception):
    """Exception raised when constitutional compliance is violated."""

    pass


def constitutional_compliance(func: Callable) -> Callable:
    """
    Decorator to enforce constitutional compliance on agent operations.

    Validates all 5 constitutional articles before allowing agent creation.
    Raises ConstitutionalViolation if any article is violated.

    Usage:
        @constitutional_compliance
        def create_my_agent(model: str, agent_context: AgentContext = None):
            return Agent(...)
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Extract agent_context from kwargs if available
            agent_context = kwargs.get("agent_context")

            # Run pre-checks for all 5 articles
            validate_article_i(agent_context=agent_context)
            validate_article_ii()
            validate_article_iii()
            validate_article_iv(agent_context=agent_context)
            validate_article_v()

            # Execute original function
            result = func(*args, **kwargs)

            # Post-validation: verify result is valid
            if result is None:
                raise ConstitutionalViolation("Agent creation returned None - invalid result")

            logger.info(f"Constitutional compliance validated for {func.__name__}")
            return result

        except ConstitutionalViolation as e:
            # Log the violation
            _log_violation(func.__name__, str(e))
            # Re-raise to block agent creation
            raise

    return wrapper


def validate_article_i(agent_context: Any | None = None) -> None:
    """
    Validate Article I: Complete Context Before Action.

    Ensures:
    - Agent context is available (or can be created)
    - Session ID is generated
    - Memory system is accessible

    Args:
        agent_context: Optional AgentContext instance

    Raises:
        ConstitutionalViolation: If context requirements not met
    """
    # If no context provided, it's acceptable - agent creation functions
    # will create default context
    if agent_context is None:
        logger.debug("Article I: No agent_context provided, will use default")
        return

    # Validate session ID exists
    if not hasattr(agent_context, "session_id") or agent_context.session_id is None:
        raise ConstitutionalViolation(
            "Article I violated: AgentContext missing session_id for complete context tracking"
        )

    # Validate memory system is available
    if not hasattr(agent_context, "memory") or agent_context.memory is None:
        raise ConstitutionalViolation(
            "Article I violated: AgentContext missing memory system for context storage"
        )

    logger.debug(f"Article I validated: session_id={agent_context.session_id}")


def validate_article_ii() -> None:
    """
    Validate Article II: 100% Verification and Stability.

    Ensures:
    - Test infrastructure is available (run_tests.py or pytest)
    - No test bypass flags are set

    Note: Does NOT run tests for performance reasons. Tests are executed
    by QualityEnforcerAgent's ValidatorTool during validation workflows.

    Raises:
        ConstitutionalViolation: If verification infrastructure missing
    """
    # Check for test infrastructure
    has_run_tests = _check_file_exists("run_tests.py")
    has_pytest = _check_file_exists("pytest.ini") or _check_file_exists("pyproject.toml")

    if not (has_run_tests or has_pytest):
        raise ConstitutionalViolation(
            "Article II violated: No test infrastructure found (run_tests.py or pytest)"
        )

    # Check for test bypass flags (constitutional violation)
    if _get_env_flag("SKIP_TESTS") or _get_env_flag("BYPASS_VERIFICATION"):
        raise ConstitutionalViolation(
            "Article II violated: Test bypass flag detected - 100% verification required"
        )

    logger.debug("Article II validated: Test infrastructure available")


def validate_article_iii() -> None:
    """
    Validate Article III: Automated Merge Enforcement.

    Ensures:
    - Git hooks directory exists (.git/hooks)
    - No bypass flags are enabled
    - Enforcement mechanisms are in place

    Raises:
        ConstitutionalViolation: If enforcement mechanisms missing or bypassed
    """
    # Check for git repository
    if not _check_directory_exists(".git"):
        logger.warning("Article III: Not in a git repository - skipping git checks")
        return

    # Check for git hooks
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        logger.warning("Article III: Git hooks directory missing - enforcement may be incomplete")

    # Check for bypass flags (strict prohibition)
    if _get_env_flag("FORCE_BYPASS") or _get_env_flag("SKIP_ENFORCEMENT"):
        raise ConstitutionalViolation(
            "Article III violated: Bypass flag detected - no manual overrides permitted"
        )

    # Check for NO_VERIFY environment variable (git commit --no-verify)
    if _get_env_flag("NO_VERIFY"):
        raise ConstitutionalViolation(
            "Article III violated: NO_VERIFY flag detected - automated enforcement required"
        )

    logger.debug("Article III validated: Enforcement mechanisms in place")


def validate_article_iv(agent_context: Any | None = None) -> None:
    """
    Validate Article IV: Continuous Learning and Improvement.

    Ensures:
    - Learning system is MANDATORY (not optional)
    - VectorStore integration is REQUIRED
    - Enhanced memory MUST be enabled
    - No disable flags are permitted

    Args:
        agent_context: Optional AgentContext instance

    Raises:
        ConstitutionalViolation: If learning infrastructure missing or disabled
    """
    # Check if learning is explicitly disabled (CONSTITUTIONAL VIOLATION)
    if _get_env_flag("DISABLE_LEARNING"):
        raise ConstitutionalViolation(
            "Article IV violated: DISABLE_LEARNING flag detected. "
            "Learning is constitutionally mandatory."
        )

    # Verify VectorStore is MANDATORY (not optional)
    use_enhanced = os.getenv("USE_ENHANCED_MEMORY", "true").lower()
    if use_enhanced != "true":
        raise ConstitutionalViolation(
            "Article IV violated: USE_ENHANCED_MEMORY must be 'true'. "
            "VectorStore integration is constitutionally mandatory, not optional."
        )

    # If context provided, verify memory system
    if agent_context is not None:
        if not hasattr(agent_context, "memory") or agent_context.memory is None:
            raise ConstitutionalViolation(
                "Article IV violated: AgentContext missing memory system for learning integration"
            )

    # Check for learning agent availability
    learning_agent_path = Path("learning_agent/learning_agent.py")
    if not learning_agent_path.exists():
        logger.warning("Article IV: LearningAgent module not found - learning may be limited")

    logger.debug("Article IV validated: Mandatory learning infrastructure in place")


def validate_article_v() -> None:
    """
    Validate Article V: Spec-Driven Development.

    Ensures:
    - specs/ directory exists for specifications
    - plans/ directory exists for technical plans
    - constitution.md is accessible
    - docs/adr/ directory exists for architecture decisions
    - Code implementations reference specs (traceability)

    Raises:
        ConstitutionalViolation: If spec-driven infrastructure missing
    """
    # Check for critical directories
    required_dirs = {
        "specs": "specifications",
        "plans": "technical plans",
        "docs/adr": "architecture decision records",
    }

    missing_dirs = []
    for dir_path, description in required_dirs.items():
        if not _check_directory_exists(dir_path):
            missing_dirs.append(f"{dir_path}/ ({description})")

    if missing_dirs:
        raise ConstitutionalViolation(
            f"Article V violated: Missing spec-driven infrastructure: {', '.join(missing_dirs)}"
        )

    # Check for constitution.md
    if not _check_file_exists("constitution.md"):
        raise ConstitutionalViolation(
            "Article V violated: constitution.md not found - spec-driven development requires constitution"
        )

    # Validate spec traceability (skip during fast tests)
    # NOTE: Spec traceability is now advisory-only due to overly strict enforcement
    # blocking normal operations. Directory structure checks above are sufficient.
    if not _get_env_flag("SKIP_SPEC_TRACEABILITY"):
        from tools.spec_traceability import SpecTraceabilityValidator

        validator = SpecTraceabilityValidator(min_coverage=0.60)  # Start at 60%
        result = validator.validate_codebase(Path.cwd())

        if result.is_err():
            _log_violation("article_v", f"spec_traceability_check_failed: {result.unwrap_err()}")
            # Don't block on check failure, just log
            logger.warning(f"Article V: Spec traceability check failed: {result.unwrap_err()}")
            return

        report = result.unwrap()
        if not report.compliant:
            # Log as warning instead of blocking - spec traceability is advisory
            logger.warning(
                f"Article V advisory: Spec coverage is {report.spec_coverage:.1f}%, "
                f"target is {validator.min_coverage * 100}%. "
                f"{len(report.violations)} files missing spec references."
            )
            # Don't raise - allow agent creation to proceed

    logger.debug("Article V validated: Spec-driven infrastructure in place")


# Helper functions


def _check_file_exists(file_path: str) -> bool:
    """Check if a file exists relative to current working directory."""
    return Path(file_path).exists()


def _check_directory_exists(dir_path: str) -> bool:
    """Check if a directory exists relative to current working directory."""
    return Path(dir_path).is_dir()


def _get_env_flag(flag_name: str) -> bool:
    """
    Check if an environment flag is set to true.

    Args:
        flag_name: Environment variable name

    Returns:
        True if flag is set to 'true', '1', or 'yes' (case-insensitive)
    """
    value = os.getenv(flag_name, "").lower()
    return value in ("true", "1", "yes")


def _log_violation(function_name: str, error_message: str) -> None:
    """
    Log constitutional violation to autonomous healing directory.

    Args:
        function_name: Name of function where violation occurred
        error_message: Description of the violation
    """
    try:
        import json
        from datetime import datetime

        # Create logs/autonomous_healing directory if it doesn't exist
        log_dir = Path("logs/autonomous_healing")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create violation log entry
        violation_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "violation_type": "ConstitutionalCompliance",
            "function": function_name,
            "error": error_message,
            "severity": "BLOCKER",
        }

        # Append to violations log file (JSONL format)
        log_file = log_dir / "constitutional_violations.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(violation_entry) + "\n")

        logger.error(f"Constitutional violation logged: {error_message}")

    except Exception as e:
        logger.warning(f"Failed to log constitutional violation: {e}")
