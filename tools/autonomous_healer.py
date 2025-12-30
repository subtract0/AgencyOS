"""
Autonomous healing with safety circuit breakers.

Features:
- Rate limiting (5 fixes/hour max)
- Automatic rollback on failure
- Human escalation for complex issues
- VectorStore learning after each fix
- Test verification before committing

Constitutional Compliance:
- Article I: Complete context via full file analysis
- Article II: 100% verification via test gates
- Article III: Automated enforcement via safety checks
- Article IV: Learning via pattern storage
"""

import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result
from tools.llm_code_fixer import Fix, LLMCodeFixer
from tools.rollback import RollbackManager
from tools.safety import MAX_FIXES_PER_HOUR, SafetyError, get_safety_state, validate_path


@dataclass
class HealingResult:
    """Result of a healing attempt."""

    fix: Fix
    success: bool
    tests_passed: bool
    error: Optional[str] = None
    rollback_performed: bool = False


@dataclass
class HealingCycleReport:
    """Report for one healing cycle."""

    timestamp: datetime
    issues_found: int
    fixes_attempted: int
    fixes_successful: int
    fixes_failed: int
    results: list[HealingResult] = field(default_factory=list)
    rate_limited: bool = False
    escalated_to_human: list[dict] = field(default_factory=list)
    duration_seconds: float = 0.0


class AutonomousHealer:
    """Autonomous code healer with safety guarantees.

    Uses a three-tier fix strategy with safety circuit breakers:
    1. Rate limiting prevents runaway automation
    2. Test verification ensures fixes don't break code
    3. Automatic rollback on any failure
    4. Human escalation for complex issues
    """

    # Issues too complex for auto-fix (escalate to human)
    ESCALATE_PATTERNS = [
        r"class\s+\w+\s*\([^)]+\)\s*:",  # Class with inheritance
        r"def\s+__\w+__",  # Dunder methods
        r"@property",  # Property decorators
        r"async\s+def",  # Async functions
        r"@abstractmethod",  # Abstract methods
        r"@classmethod",  # Class methods with complex logic
        r"@staticmethod",  # Static methods
        r"lambda\s+.*:",  # Lambda expressions
        r"yield\s+",  # Generators
        r"with\s+.*\s+as\s+",  # Context managers
    ]

    def __init__(self, project_root: Path | None = None):
        """Initialize the autonomous healer.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or PROJECT_ROOT
        self.fixer = LLMCodeFixer()
        self.rollback = RollbackManager()
        self.safety_state = get_safety_state()

    def run_healing_cycle(
        self, max_fixes: int = 3, dry_run: bool = False
    ) -> Result[HealingCycleReport, str]:
        """Run one healing cycle.

        Args:
            max_fixes: Maximum fixes to attempt this cycle
            dry_run: If True, don't apply any fixes

        Returns:
            Result containing HealingCycleReport or error
        """
        import re

        start_time = time.time()

        report = HealingCycleReport(
            timestamp=datetime.now(),
            issues_found=0,
            fixes_attempted=0,
            fixes_successful=0,
            fixes_failed=0,
        )

        # Check rate limit
        remaining = MAX_FIXES_PER_HOUR - self.safety_state.fixes_this_hour
        if remaining <= 0:
            report.rate_limited = True
            print(
                f"⚠️ Rate limited: {self.safety_state.fixes_this_hour}/{MAX_FIXES_PER_HOUR} fixes this hour"
            )
            return Ok(report)

        # Scan for issues
        try:
            from tools.self_healing_monitor import SelfHealingMonitor

            monitor = SelfHealingMonitor(project_root=self.project_root)
            issues = monitor.scan_code_quality()
            report.issues_found = len(issues)
        except Exception as e:
            return Err(f"Failed to scan for issues: {e}")

        # Prioritize: high severity first, then by confidence
        high_severity = [i for i in issues if i.get("severity") == "high"]
        high_severity.sort(key=lambda i: i.get("confidence", 0.5), reverse=True)

        # Attempt fixes
        fixes_remaining = min(max_fixes, remaining)

        for issue in high_severity[:fixes_remaining]:
            # Check if should escalate
            if self._should_escalate(issue):
                report.escalated_to_human.append(issue)
                continue

            # Validate path
            path_result = validate_path(issue.get("file", ""))
            if path_result.is_err():
                continue

            # Attempt fix
            report.fixes_attempted += 1
            result = self._attempt_fix(issue, dry_run=dry_run)
            report.results.append(result)

            if result.success:
                report.fixes_successful += 1
                if not dry_run:
                    self.safety_state.record_fix()
                    self._store_learning(result)
            else:
                report.fixes_failed += 1

        report.duration_seconds = time.time() - start_time
        return Ok(report)

    def _should_escalate(self, issue: dict) -> bool:
        """Check if issue should be escalated to human.

        Args:
            issue: Issue dictionary with content

        Returns:
            True if issue is too complex for auto-fix
        """
        import re

        content = issue.get("content", "")
        for pattern in self.ESCALATE_PATTERNS:
            if re.search(pattern, content):
                return True

        # Also escalate if confidence is too low
        if issue.get("confidence", 0.5) < 0.4:
            return True

        return False

    def _attempt_fix(self, issue: dict, dry_run: bool = False) -> HealingResult:
        """Attempt to fix a single issue.

        Args:
            issue: Issue dictionary
            dry_run: If True, don't apply the fix

        Returns:
            HealingResult with outcome
        """
        file_path = issue.get("file", "")
        line_number = issue.get("line", 0)
        issue_type = issue.get("pattern", "unknown")

        # Create a placeholder fix for error cases
        placeholder_fix = Fix(
            file_path=file_path,
            line_number=line_number,
            original="",
            fixed="",
            method="none",
            confidence=0,
            issue_type=issue_type,
        )

        try:
            # Generate fix
            fix_result = self.fixer.fix_issue(file_path, line_number, issue_type)

            if fix_result.is_err():
                return HealingResult(
                    fix=placeholder_fix,
                    success=False,
                    tests_passed=False,
                    error=fix_result.unwrap_err(),
                )

            fix = fix_result.unwrap()

            if dry_run:
                print(f"[DRY RUN] Would fix {file_path}:{line_number}")
                print(f"  - {fix.original}")
                print(f"  + {fix.fixed}")
                return HealingResult(
                    fix=fix, success=True, tests_passed=True, error="Dry run"
                )

            # Create snapshot
            snapshot_result = self.rollback.create_snapshot(
                [file_path], f"Fix {issue_type} at {file_path}:{line_number}"
            )
            if snapshot_result.is_err():
                return HealingResult(
                    fix=fix,
                    success=False,
                    tests_passed=False,
                    error=f"Snapshot failed: {snapshot_result.unwrap_err()}",
                )

            snapshot = snapshot_result.unwrap()

            # Apply fix
            apply_result = self.fixer.apply_fix(fix)
            if apply_result.is_err():
                return HealingResult(
                    fix=fix,
                    success=False,
                    tests_passed=False,
                    error=apply_result.unwrap_err(),
                )

            fix_result_obj = apply_result.unwrap()
            if not fix_result_obj.applied:
                return HealingResult(
                    fix=fix,
                    success=False,
                    tests_passed=False,
                    error=fix_result_obj.error or "Fix not applied",
                )

            # Run tests
            tests_passed = self._run_tests()

            if not tests_passed:
                # Rollback
                self.rollback.rollback(snapshot.id)
                return HealingResult(
                    fix=fix,
                    success=False,
                    tests_passed=False,
                    error="Tests failed after fix",
                    rollback_performed=True,
                )

            # Commit fix
            self._commit_fix(fix)

            return HealingResult(fix=fix, success=True, tests_passed=True)

        except SafetyError as e:
            return HealingResult(
                fix=placeholder_fix,
                success=False,
                tests_passed=False,
                error=f"Safety error: {e}",
            )
        except Exception as e:
            return HealingResult(
                fix=placeholder_fix,
                success=False,
                tests_passed=False,
                error=f"Unexpected error: {e}",
            )

    def _run_tests(self, test_path: str = "tests/unit/") -> bool:
        """Run tests to verify fix.

        Args:
            test_path: Path to tests to run

        Returns:
            True if tests pass
        """
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", test_path, "-x", "--tb=no", "-q"],
                capture_output=True,
                timeout=300,
                cwd=str(self.project_root),
            )
            return result.returncode == 0
        except Exception:
            return False

    def _commit_fix(self, fix: Fix) -> bool:
        """Commit the fix to git.

        Args:
            fix: The fix that was applied

        Returns:
            True if commit succeeded
        """
        try:
            subprocess.run(
                ["git", "add", fix.file_path],
                cwd=str(self.project_root),
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"fix(auto): {fix.issue_type} at {fix.file_path}:{fix.line_number}\n\n"
                    f"Method: {fix.method} (confidence: {fix.confidence:.0%})\n"
                    f"🤖 Auto-fixed by AgencyOS Autonomous Healer",
                ],
                cwd=str(self.project_root),
                capture_output=True,
            )
            return True
        except Exception:
            return False

    def _store_learning(self, result: HealingResult) -> bool:
        """Store successful fix for future learning.

        Args:
            result: The successful healing result

        Returns:
            True if stored successfully
        """
        if not result.success:
            return False

        return self.fixer.store_successful_fix(result.fix)

    def run_daemon(
        self,
        interval_minutes: int = 30,
        max_cycles: int = 0,
        dry_run: bool = False,
    ) -> None:
        """Run healing daemon continuously.

        Args:
            interval_minutes: Minutes between healing cycles
            max_cycles: Maximum cycles to run (0=infinite)
            dry_run: If True, don't apply any fixes
        """
        cycle = 0

        print("=" * 60)
        print("AgencyOS Autonomous Healer Started")
        print(f"Interval: {interval_minutes}min | Max: {max_cycles or '∞'} cycles")
        print(f"Safety: {MAX_FIXES_PER_HOUR} fixes/hour max")
        print(f"Dry run: {dry_run}")
        print("=" * 60)

        try:
            while max_cycles == 0 or cycle < max_cycles:
                cycle += 1
                print(f"\n[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                result = self.run_healing_cycle(dry_run=dry_run)

                if result.is_ok():
                    report = result.unwrap()
                    print(f"  Found: {report.issues_found} issues")
                    print(
                        f"  Fixed: {report.fixes_successful}/{report.fixes_attempted}"
                    )
                    print(f"  Duration: {report.duration_seconds:.1f}s")

                    if report.rate_limited:
                        print("  ⚠️ Rate limited - waiting for next hour")

                    if report.escalated_to_human:
                        print(f"  👤 Escalated {len(report.escalated_to_human)} to human")
                        for issue in report.escalated_to_human[:3]:
                            print(f"      - {issue.get('file', '?')}:{issue.get('line', '?')}")
                else:
                    print(f"  ❌ Error: {result.unwrap_err()}")

                if max_cycles == 0 or cycle < max_cycles:
                    print(f"  Next cycle in {interval_minutes}min...")
                    time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\nHealer stopped by user.")

    def get_status(self) -> dict:
        """Get current healer status.

        Returns:
            Dictionary with status information
        """
        from tools.safety import get_safety_status

        return {
            "safety": get_safety_status(),
            "project_root": str(self.project_root),
            "llm_available": self.fixer._check_llm(),
            "escalate_patterns": len(self.ESCALATE_PATTERNS),
        }


def main():
    """Command-line interface for autonomous healer."""
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous code healer")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument(
        "--interval", type=int, default=30, help="Minutes between cycles"
    )
    parser.add_argument("--cycles", type=int, default=0, help="Max cycles (0=infinite)")
    parser.add_argument("--once", action="store_true", help="Run single cycle")
    parser.add_argument("--dry-run", action="store_true", help="Don't apply fixes")
    parser.add_argument("--status", action="store_true", help="Show healer status")
    parser.add_argument(
        "--max-fixes", type=int, default=3, help="Max fixes per cycle"
    )
    args = parser.parse_args()

    healer = AutonomousHealer()

    if args.status:
        import json

        status = healer.get_status()
        print(json.dumps(status, indent=2, default=str))

    elif args.daemon:
        healer.run_daemon(
            interval_minutes=args.interval,
            max_cycles=args.cycles,
            dry_run=args.dry_run,
        )

    elif args.once:
        result = healer.run_healing_cycle(max_fixes=args.max_fixes, dry_run=args.dry_run)
        if result.is_ok():
            report = result.unwrap()
            print(f"\nResults:")
            print(f"  Issues found: {report.issues_found}")
            print(f"  Fixes attempted: {report.fixes_attempted}")
            print(f"  Successful: {report.fixes_successful}")
            print(f"  Failed: {report.fixes_failed}")
            print(f"  Duration: {report.duration_seconds:.1f}s")

            if report.escalated_to_human:
                print(f"\n  Escalated to human ({len(report.escalated_to_human)}):")
                for issue in report.escalated_to_human[:5]:
                    print(f"    - {issue.get('file', '?')}:{issue.get('line', '?')}")
        else:
            print(f"Error: {result.unwrap_err()}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
