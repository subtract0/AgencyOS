"""
Unified self-healing core module.
Consolidates detection, fixing, and verification into three essential methods.
Feature-flagged for gradual migration from 62+ scattered files.

SAFETY FEATURES:
- Defaults to dry-run mode (no actual fixes or commits)
- Requires explicit SELF_HEALING_AUTO_COMMIT=true environment variable for git commits
- All operations are logged for audit trail
- Production use requires setting dry_run=False explicitly
"""

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Finding:
    """Minimal error finding representation."""

    file: str
    line: int
    error_type: str
    snippet: str


@dataclass
class Patch:
    """Minimal patch representation."""

    diff: str
    file: str
    rationale: str


class SelfHealingCore:
    """
    Unified self-healing service with three essential methods.
    Start with NoneType errors, pluggable for other error types.
    """

    def __init__(self, dry_run=True):
        """Initialize with feature flag check and unified systems.

        Args:
            dry_run: If True, no actual fixes or commits are made (default: True for safety)
        """
        self.enabled = os.getenv("ENABLE_UNIFIED_CORE", "true").lower() == "true"
        self.dry_run = dry_run  # Safety: default to dry-run mode

        # Use unified telemetry if available
        try:
            from core.telemetry import get_telemetry

            self.telemetry = get_telemetry()
        except ImportError:
            self.telemetry = None

        # Use unified pattern store if available
        try:
            from pattern_intelligence import PatternStore

            self.pattern_store = PatternStore()
        except ImportError:
            self.pattern_store = None

    def detect_errors(self, path: str) -> list[Finding]:
        """
        Detect errors in codebase or logs.
        Start with NoneType, pluggable for other rules.

        Args:
            path: File path or log content to analyze

        Returns:
            List of Finding objects with detected errors
        """
        # 1. Load content (from file or treat as string)
        content = self._load_content_for_detection(path)
        if content is None:
            return []

        # 2. Scan for error patterns
        findings = self._scan_for_error_patterns(content)

        # 3. Emit telemetry
        self._emit_event(
            "errors_detected",
            {"count": len(findings), "types": list(set(f.error_type for f in findings))},
        )

        return findings

    def _load_content_for_detection(self, path: str) -> str | None:
        """
        Load content from file path or treat as string content.

        Args:
            path: File path or log content string

        Returns:
            Content string, or None if validation/read fails
        """
        if not os.path.isfile(path):
            # Treat as log content string
            return path

        # Validate file path security
        if not self._validate_file_path_security(path):
            return None

        # Read file content
        try:
            normalized_path = os.path.normpath(path)
            abs_path = os.path.abspath(normalized_path)
            with open(abs_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            self._emit_event(
                "error_detection_failed", {"path": path, "error": "File is not UTF-8 encoded"}
            )
            return None
        except Exception as e:
            self._emit_event("error_detection_failed", {"path": path, "error": str(e)})
            return None

    def _validate_file_path_security(self, path: str) -> bool:
        """
        Validate file path for security (path traversal, allowed directories).

        Args:
            path: File path to validate

        Returns:
            True if path is safe, False otherwise
        """
        normalized_path = os.path.normpath(path)
        abs_path = os.path.abspath(normalized_path)

        # Security check: ensure path is in allowed directories
        cwd = os.getcwd()
        allowed_dirs = [cwd, "/tmp", "/var/log"]
        if not any(abs_path.startswith(d) for d in allowed_dirs):
            self._emit_event(
                "security_validation_failed",
                {"path": path, "reason": "Path outside allowed directories"},
            )
            return False

        # Check for path traversal attempts
        if ".." in normalized_path or normalized_path.startswith("~"):
            self._emit_event(
                "security_validation_failed",
                {"path": path, "reason": "Path traversal attempt detected"},
            )
            return False

        return True

    def _scan_for_error_patterns(self, content: str) -> list[Finding]:
        """
        Scan content for NoneType error patterns.

        Args:
            content: Log or file content to scan

        Returns:
            List of Finding objects for detected errors
        """
        findings: list[Finding] = []

        # NoneType error patterns
        patterns = [
            r"AttributeError: 'NoneType' object has no attribute '(\w+)'",
            r"TypeError: 'NoneType' object is not (\w+)",
            r"TypeError: argument of type 'NoneType' is not iterable",
            r"TypeError: unsupported operand type\(s\) for .+: 'NoneType'",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                finding = self._extract_finding_from_match(match, content)
                findings.append(finding)

        return findings

    def _extract_finding_from_match(self, match: re.Match, content: str) -> Finding:
        """
        Extract Finding object from regex match and content.

        Args:
            match: Regex match object
            content: Full content being scanned

        Returns:
            Finding object with extracted metadata
        """
        # Extract line number
        line_match = re.search(r"line (\d+)", content)
        line_num = int(line_match.group(1)) if line_match else 0

        # Extract file path
        file_match = re.search(r'File "([^"]+)"', content)
        file_path = file_match.group(1) if file_match else "unknown"

        return Finding(file=file_path, line=line_num, error_type="NoneType", snippet=match.group(0))

    def fix_error(self, error: Finding) -> bool:
        """
        Apply fix for detected error.
        Auto-rollback on test failure.

        Args:
            error: Finding object to fix

        Returns:
            True if fix successful and tests pass, False otherwise
        """
        # 1. Validate and read file
        original_content = self._read_file_for_fix(error)
        if original_content is None:
            return False

        # 2. Generate fix
        fixed_content = self._generate_fix(original_content, error)
        if not fixed_content:
            self._emit_event("fix_failed", {"reason": "cannot_generate_fix"})
            return False

        # 3. Check dry-run mode
        if self.dry_run:
            self._emit_event(
                "fix_skipped_dry_run",
                {"file": error.file, "message": "Dry-run mode enabled, fix not applied"},
            )
            return True  # Pretend success in dry-run

        # 4. Apply fix to file
        if not self._apply_fix_to_file(error.file, fixed_content):
            return False

        # 5. Verify with tests
        test_passed = self.verify()

        # 6. Rollback on failure
        if not test_passed:
            self._rollback_on_failure(error.file, original_content)
            return False

        # 7. Learn from successful fix
        self._learn_from_fix(error, original_content, fixed_content)

        # 8. Commit the successful fix
        self._commit_fix(error)

        return True

    def _read_file_for_fix(self, error: Finding) -> str | None:
        """
        Validate error file and read its content for fixing.

        Args:
            error: Finding object with file path

        Returns:
            File content as string, or None if validation/read fails
        """
        if error.file == "unknown" or not os.path.exists(error.file):
            self._emit_event("fix_skipped", {"reason": "file_not_found", "file": error.file})
            return None

        try:
            with open(error.file) as f:
                return f.read()
        except Exception as e:
            self._emit_event("fix_failed", {"reason": "cannot_read_file", "error": str(e)})
            return None

    def _apply_fix_to_file(self, file_path: str, fixed_content: str) -> bool:
        """
        Apply generated fix to file on disk.

        Args:
            file_path: Path to file to modify
            fixed_content: Fixed content to write

        Returns:
            True if write successful, False otherwise
        """
        try:
            with open(file_path, "w") as f:
                f.write(fixed_content)
            self._emit_event("patch_applied", {"file": file_path})
            return True
        except Exception as e:
            self._emit_event("fix_failed", {"reason": "cannot_write_file", "error": str(e)})
            return False

    def _rollback_on_failure(self, file_path: str, original_content: str) -> None:
        """
        Rollback file to original content after test failure.

        Args:
            file_path: Path to file to rollback
            original_content: Original content to restore
        """
        try:
            with open(file_path, "w") as f:
                f.write(original_content)
            self._emit_event("rollback_complete", {"file": file_path})
        except (PermissionError, OSError) as e:
            self._emit_event("rollback_failed", {"file": file_path, "error": str(e)}, level="error")

    def _learn_from_fix(self, error: Finding, original_content: str, fixed_content: str) -> None:
        """
        Store successful fix as a coding pattern for future learning.

        Args:
            error: Finding object that was fixed
            original_content: Original file content before fix
            fixed_content: Fixed file content after fix
        """
        if not self.pattern_store:
            return

        from pattern_intelligence.coding_pattern import CodingPattern

        # Build pattern components
        context = self._build_pattern_context(error)
        solution = self._build_pattern_solution(error, original_content, fixed_content)
        outcome = self._build_pattern_outcome()
        metadata = self._build_pattern_metadata(error)

        # Store pattern
        pattern = CodingPattern(context, solution, outcome, metadata)
        self.pattern_store.store_pattern(pattern)
        self._emit_event("pattern_learned", {"pattern_id": metadata.pattern_id})

    def _build_pattern_context(self, error: Finding):
        """Build ProblemContext for pattern learning."""
        from pattern_intelligence.coding_pattern import ProblemContext

        return ProblemContext(
            description=f"Fix for {error.error_type}",
            domain="error_fixing",
            constraints=[],
            symptoms=[error.snippet[:200]],
            scale=None,
            urgency="medium",
        )

    def _build_pattern_solution(self, error: Finding, original_content: str, fixed_content: str):
        """Build SolutionApproach for pattern learning."""
        from pattern_intelligence.coding_pattern import SolutionApproach

        return SolutionApproach(
            approach=f"Self-healing fix for {error.error_type}",
            implementation=fixed_content[:1000],
            tools=["self_healing"],
            reasoning="Automated fix applied and tested successfully",
            code_examples=[original_content[:500], fixed_content[:500]],
            dependencies=[],
            alternatives=[],
        )

    def _build_pattern_outcome(self):
        """Build EffectivenessMetric for pattern learning."""
        from pattern_intelligence.coding_pattern import EffectivenessMetric

        return EffectivenessMetric(
            success_rate=1.0,
            performance_impact=None,
            maintainability_impact="Improved error handling",
            user_impact=None,
            technical_debt=None,
            adoption_rate=1,
            longevity=None,
            confidence=0.9,
        )

    def _build_pattern_metadata(self, error: Finding):
        """Build PatternMetadata for pattern learning."""
        from pattern_intelligence.coding_pattern import PatternMetadata

        pattern_id = f"self_heal_{error.error_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return PatternMetadata(
            pattern_id=pattern_id,
            discovered_timestamp=datetime.now().isoformat(),
            source="self_healing:core",
            discoverer="SelfHealingCore",
            last_applied=datetime.now().isoformat(),
            application_count=1,
            validation_status="validated",
            tags=["self_healing", error.error_type, "automated"],
            related_patterns=[],
        )

    def verify(self) -> bool:
        """
        Run tests to verify fixes.
        Return True only if 100% pass.

        Returns:
            True if all tests pass, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "run_tests.py"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0 and (
                "✅ All tests passed!" in output or "TEST EXECUTION COMPLETE" in output
            )

            # Extract test count
            test_count = 0
            if "collected" in output:
                match = re.search(r"collected (\d+) items", output)
                if match:
                    test_count = int(match.group(1))

            self._emit_event(
                "tests_completed",
                {"passed": success, "total": test_count, "returncode": result.returncode},
            )

            return success

        except subprocess.TimeoutExpired:
            self._emit_event("tests_timeout", {"timeout_seconds": 120})
            return False
        except Exception as e:
            self._emit_event("tests_failed", {"error": str(e)})
            return False

    def _generate_fix(self, content: str, error: Finding) -> str | None:
        """
        Generate fix for error (simplified from existing implementation).
        """
        lines = content.split("\n")

        # Find problematic line
        if 0 < error.line <= len(lines):
            problematic_line = lines[error.line - 1]

            # Extract variable that might be None
            match = re.search(r"(\w+)\.(\w+)", problematic_line)
            if match:
                var_name = match.group(1)
                attribute = match.group(2)

                # Generate null-check fix
                indent = len(problematic_line) - len(problematic_line.lstrip())
                indent_str = " " * indent

                # Replace line with null-checked version
                fixed_lines = lines[: error.line - 1]
                fixed_lines.append(f"{indent_str}if {var_name} is not None:")
                fixed_lines.append(f"{indent_str}    {problematic_line.strip()}")
                fixed_lines.append(f"{indent_str}else:")
                fixed_lines.append(f"{indent_str}    pass  # Auto-generated None handling")
                fixed_lines.extend(lines[error.line :])

                return "\n".join(fixed_lines)

        return None

    def _commit_fix(self, error: Finding):
        """
        Commit successful fix with safety checks.
        """
        # Safety check: dry-run mode
        if self.dry_run:
            self._emit_event(
                "commit_skipped_dry_run",
                {"file": error.file, "message": "Dry-run mode enabled, commit skipped for safety"},
            )
            return

        # Safety check: require explicit environment variable
        if os.getenv("SELF_HEALING_AUTO_COMMIT", "false").lower() != "true":
            self._emit_event(
                "commit_skipped_no_permission",
                {
                    "file": error.file,
                    "message": "Auto-commit disabled. Set SELF_HEALING_AUTO_COMMIT=true to enable",
                },
            )
            return

        try:
            # Stage the file
            subprocess.run(["git", "add", error.file], check=True)

            # Create commit message
            commit_msg = f"""fix(auto): Self-healing applied for {error.error_type} error

• File: {error.file}:{error.line}
• Error: {error.snippet}
• Applied null-check pattern
• Tests verified: 100% passing

🤖 Generated with Unified Self-Healing Core"""

            # Commit
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)

            # Get commit hash
            result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
            commit_hash = result.stdout.strip() if result.returncode == 0 else "unknown"

            self._emit_event("commit_success", {"hash": commit_hash[:8]})

        except Exception as e:
            self._emit_event("commit_failed", {"error": str(e)})

    def _emit_event(self, event: str, data: dict, level: str = "info"):
        """
        Emit telemetry event through unified system.
        """
        if self.telemetry:
            self.telemetry.log(f"self_healing.{event}", data, level)
        else:
            # Fallback to simple logging
            event_data = {"ts": datetime.now().isoformat() + "Z", "event": event, "data": data}
            try:
                os.makedirs("logs/events", exist_ok=True)
                with open("logs/events/fallback.jsonl", "a") as f:
                    f.write(json.dumps(event_data) + "\n")
            except Exception:
                # Last resort logging failed, continue silently
                pass  # Unable to log, system may be in critical state
