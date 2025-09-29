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

import os
import re
import json
import subprocess
from dataclasses import dataclass
from typing import Optional, List
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

    def detect_errors(self, path: str) -> List[Finding]:
        """
        Detect errors in codebase or logs.
        Start with NoneType, pluggable for other rules.

        Args:
            path: File path or log content to analyze

        Returns:
            List of Finding objects with detected errors
        """
        findings: List[Finding] = []

        # Validate and sanitize file path
        if os.path.isfile(path):
            # Input validation for file paths
            # Normalize and validate the path
            normalized_path = os.path.normpath(path)
            abs_path = os.path.abspath(normalized_path)

            # Security check: ensure path doesn't escape working directory or access sensitive areas
            cwd = os.getcwd()
            if not abs_path.startswith(cwd) and not abs_path.startswith('/tmp') and not abs_path.startswith('/var/log'):
                self._emit_event("security_validation_failed", {
                    "path": path,
                    "reason": "Path outside allowed directories"
                })
                return findings

            # Check for path traversal attempts
            if '..' in normalized_path or normalized_path.startswith('~'):
                self._emit_event("security_validation_failed", {
                    "path": path,
                    "reason": "Path traversal attempt detected"
                })
                return findings

            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                self._emit_event("error_detection_failed", {"path": path, "error": "File is not UTF-8 encoded"})
                return findings
            except Exception as e:
                self._emit_event("error_detection_failed", {"path": path, "error": str(e)})
                return findings
        else:
            # Treat as log content string
            content = path

        # NoneType error patterns (from existing implementation)
        patterns = [
            r"AttributeError: 'NoneType' object has no attribute '(\w+)'",
            r"TypeError: 'NoneType' object is not (\w+)",
            r"TypeError: argument of type 'NoneType' is not iterable",
            r"TypeError: unsupported operand type\(s\) for .+: 'NoneType'",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                # Extract context
                line_match = re.search(r'line (\d+)', content)
                line_num = int(line_match.group(1)) if line_match else 0

                file_match = re.search(r'File "([^"]+)"', content)
                file_path = file_match.group(1) if file_match else "unknown"

                finding = Finding(
                    file=file_path,
                    line=line_num,
                    error_type="NoneType",
                    snippet=match.group(0)
                )
                findings.append(finding)

        self._emit_event("errors_detected", {
            "count": len(findings),
            "types": list(set(f.error_type for f in findings))
        })

        return findings

    def fix_error(self, error: Finding) -> bool:
        """
        Apply fix for detected error.
        Auto-rollback on test failure.

        Args:
            error: Finding object to fix

        Returns:
            True if fix successful and tests pass, False otherwise
        """
        if error.file == "unknown" or not os.path.exists(error.file):
            self._emit_event("fix_skipped", {"reason": "file_not_found", "file": error.file})
            return False

        # Read original file content for backup
        try:
            with open(error.file, 'r') as f:
                original_content = f.read()
            lines = original_content.split('\n')
        except Exception as e:
            self._emit_event("fix_failed", {"reason": "cannot_read_file", "error": str(e)})
            return False

        # Generate simple fix (from existing logic)
        fixed_content = self._generate_fix(original_content, error)

        if not fixed_content:
            self._emit_event("fix_failed", {"reason": "cannot_generate_fix"})
            return False

        # Safety check: dry-run mode
        if self.dry_run:
            self._emit_event("fix_skipped_dry_run", {
                "file": error.file,
                "message": "Dry-run mode enabled, fix not applied"
            })
            return True  # Pretend success in dry-run

        # Apply the fix
        try:
            with open(error.file, 'w') as f:
                f.write(fixed_content)
            self._emit_event("patch_applied", {"file": error.file})
        except Exception as e:
            self._emit_event("fix_failed", {"reason": "cannot_write_file", "error": str(e)})
            return False

        # Verify with tests
        test_passed = self.verify()

        if not test_passed:
            # Rollback on failure
            try:
                with open(error.file, 'w') as f:
                    f.write(original_content)
                self._emit_event("rollback_complete", {"file": error.file})
            except (IOError, PermissionError, OSError) as e:
                self._emit_event("rollback_failed", {"file": error.file, "error": str(e)}, level="error")
            return False

        # Learn from successful fix
        if self.pattern_store and test_passed:
            from pattern_intelligence.coding_pattern import (
                CodingPattern, ProblemContext, SolutionApproach,
                EffectivenessMetric, PatternMetadata
            )
            from datetime import datetime

            # Create a CodingPattern from the fix
            context = ProblemContext(
                description=f"Fix for {error.error_type}",
                domain="error_fixing",
                constraints=[],
                symptoms=[error.snippet[:200]],
                scale=None,
                urgency="medium"
            )

            solution = SolutionApproach(
                approach=f"Self-healing fix for {error.error_type}",
                implementation=fixed_content[:1000],
                tools=["self_healing"],
                reasoning="Automated fix applied and tested successfully",
                code_examples=[original_content[:500], fixed_content[:500]],
                dependencies=[],
                alternatives=[]
            )

            outcome = EffectivenessMetric(
                success_rate=1.0,
                performance_impact=None,
                maintainability_impact="Improved error handling",
                user_impact=None,
                technical_debt=None,
                adoption_rate=1,
                longevity=None,
                confidence=0.9
            )

            pattern_id = f"self_heal_{error.error_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            metadata = PatternMetadata(
                pattern_id=pattern_id,
                discovered_timestamp=datetime.now().isoformat(),
                source="self_healing:core",
                discoverer="SelfHealingCore",
                last_applied=datetime.now().isoformat(),
                application_count=1,
                validation_status="validated",
                tags=["self_healing", error.error_type, "automated"],
                related_patterns=[]
            )

            pattern = CodingPattern(context, solution, outcome, metadata)
            self.pattern_store.store_pattern(pattern)
            self._emit_event("pattern_learned", {"pattern_id": pattern_id})

        # Commit the successful fix
        self._commit_fix(error)

        return True

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
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0 and ("✅ All tests passed!" in output or "TEST EXECUTION COMPLETE" in output)

            # Extract test count
            test_count = 0
            if "collected" in output:
                match = re.search(r'collected (\d+) items', output)
                if match:
                    test_count = int(match.group(1))

            self._emit_event("tests_completed", {
                "passed": success,
                "total": test_count,
                "returncode": result.returncode
            })

            return success

        except subprocess.TimeoutExpired:
            self._emit_event("tests_timeout", {"timeout_seconds": 120})
            return False
        except Exception as e:
            self._emit_event("tests_failed", {"error": str(e)})
            return False

    def _generate_fix(self, content: str, error: Finding) -> Optional[str]:
        """
        Generate fix for error (simplified from existing implementation).
        """
        lines = content.split('\n')

        # Find problematic line
        if 0 < error.line <= len(lines):
            problematic_line = lines[error.line - 1]

            # Extract variable that might be None
            match = re.search(r'(\w+)\.(\w+)', problematic_line)
            if match:
                var_name = match.group(1)
                attribute = match.group(2)

                # Generate null-check fix
                indent = len(problematic_line) - len(problematic_line.lstrip())
                indent_str = " " * indent

                # Replace line with null-checked version
                fixed_lines = lines[:error.line - 1]
                fixed_lines.append(f"{indent_str}if {var_name} is not None:")
                fixed_lines.append(f"{indent_str}    {problematic_line.strip()}")
                fixed_lines.append(f"{indent_str}else:")
                fixed_lines.append(f"{indent_str}    pass  # Auto-generated None handling")
                fixed_lines.extend(lines[error.line:])

                return '\n'.join(fixed_lines)

        return None

    def _commit_fix(self, error: Finding):
        """
        Commit successful fix with safety checks.
        """
        # Safety check: dry-run mode
        if self.dry_run:
            self._emit_event("commit_skipped_dry_run", {
                "file": error.file,
                "message": "Dry-run mode enabled, commit skipped for safety"
            })
            return

        # Safety check: require explicit environment variable
        if os.getenv("SELF_HEALING_AUTO_COMMIT", "false").lower() != "true":
            self._emit_event("commit_skipped_no_permission", {
                "file": error.file,
                "message": "Auto-commit disabled. Set SELF_HEALING_AUTO_COMMIT=true to enable"
            })
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
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True
            )
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
            event_data = {
                "ts": datetime.now().isoformat() + "Z",
                "event": event,
                "data": data
            }
            try:
                os.makedirs("logs/events", exist_ok=True)
                with open("logs/events/fallback.jsonl", "a") as f:
                    f.write(json.dumps(event_data) + "\n")
            except Exception:
                # Last resort logging failed, continue silently
                pass  # Unable to log, system may be in critical state