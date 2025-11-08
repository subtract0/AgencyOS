#!/usr/bin/env python3
"""
CI Failure Log Parser - Extract test failure history from GitHub Actions.

Constitutional Article I: Idempotency - Upsert-based, safe to re-run.
Performance SLA: Queries <100ms for 5k tests, DB <50MB for 90 days.
"""

import os
import re
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import subprocess


@dataclass
class TestFailure:
    """Test failure event from CI logs."""
    test_id: str
    failure_date: str  # ISO 8601
    ci_run_id: str
    failure_reason: str
    traceback: Optional[str] = None
    fixed_date: Optional[str] = None
    is_flaky: bool = False


class CIFailureParser:
    """Parse CI logs for test failure history."""

    def __init__(self, db_path: Path = Path(".audit/failure_history.sqlite")):
        """
        Initialize CI failure parser with SQLite database.

        Args:
            db_path: Path to SQLite database (default: .audit/failure_history.sqlite)
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Create SQLite schema with indexes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                failure_date TEXT NOT NULL,
                ci_run_id TEXT,
                failure_reason TEXT,
                traceback TEXT,
                fixed_date TEXT,
                is_flaky BOOLEAN DEFAULT 0,
                UNIQUE(test_id, failure_date, ci_run_id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_id ON test_failures(test_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_failure_date ON test_failures(failure_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fixed_date ON test_failures(fixed_date)")

        conn.commit()
        conn.close()

    def parse_github_actions_logs(
        self,
        owner: str,
        repo: str,
        days_back: int = 90,
        gh_token: Optional[str] = None
    ) -> List[TestFailure]:
        """
        Parse GitHub Actions workflow logs via gh CLI.

        Falls back to local pytest cache if gh CLI unavailable.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            days_back: How many days back to fetch logs (default: 90)
            gh_token: Optional GitHub token (uses $GITHUB_TOKEN if None)

        Returns:
            List of TestFailure objects
        """
        failures = []

        # Check if gh CLI is available
        try:
            run_spec_command(['gh', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  GitHub CLI (gh) not available, falling back to local cache")
            return self._parse_local_pytest_cache()

        # Set token if provided
        env = os.environ.copy()
        if gh_token:
            env['GITHUB_TOKEN'] = gh_token

        # Get workflow runs from last N days
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        try:
            # List recent workflow runs
            result = run_spec_command(
                ['gh', 'run', 'list', '--repo', f'{owner}/{repo}',
                 '--limit', '100', '--json', 'databaseId,conclusion,createdAt,name'],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )

            if result.returncode != 0:
                print(f"⚠️  Failed to fetch workflow runs: {result.stderr}")
                return self._parse_local_pytest_cache()

            runs = json.loads(result.stdout)

            # Filter to failed runs in date range
            failed_runs = [
                r for r in runs
                if r.get('conclusion') == 'failure' and r.get('createdAt', '') >= cutoff_date
            ]

            print(f"🔍 Found {len(failed_runs)} failed CI runs in last {days_back} days")

            # Parse each failed run's logs
            for run in failed_runs[:20]:  # Limit to 20 runs to avoid rate limits
                run_id = run['databaseId']
                run_date = run['createdAt']

                run_failures = self._parse_workflow_run_logs(owner, repo, run_id, run_date, env)
                failures.extend(run_failures)

        except Exception as e:
            print(f"⚠️  Error parsing GitHub Actions logs: {e}")
            return self._parse_local_pytest_cache()

        return failures

    def _parse_workflow_run_logs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        run_date: str,
        env: dict
    ) -> List[TestFailure]:
        """Parse logs from a single workflow run."""
        failures = []

        try:
            # Get run logs
            result = run_spec_command(
                ['gh', 'run', 'view', str(run_id), '--repo', f'{owner}/{repo}', '--log'],
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )

            if result.returncode != 0:
                return failures

            logs = result.stdout

            # Extract pytest failures from logs
            # Pattern: FAILED tests/test_foo.py::test_bar - AssertionError: ...
            failure_pattern = r'FAILED\s+([\w/]+\.py::\S+)\s+-\s+(.+?)(?=\n|$)'

            for match in re.finditer(failure_pattern, logs):
                test_id = match.group(1)
                failure_reason = match.group(2).strip()[:500]  # Truncate long reasons

                # Extract traceback (up to 10 lines after FAILED line)
                traceback = self._extract_traceback(logs, match.start())

                failure = TestFailure(
                    test_id=test_id,
                    failure_date=run_date,
                    ci_run_id=str(run_id),
                    failure_reason=failure_reason,
                    traceback=traceback
                )
                failures.append(failure)

        except Exception as e:
            print(f"⚠️  Error parsing run {run_id}: {e}")

        return failures

    def _extract_traceback(self, logs: str, start_pos: int, max_lines: int = 10) -> Optional[str]:
        """Extract traceback from logs starting at position."""
        lines = logs[start_pos:start_pos + 1000].split('\n')[:max_lines]

        # Find lines that look like traceback
        traceback_lines = []
        for line in lines:
            if any(keyword in line for keyword in ['File "', 'line ', 'Error:', 'Exception:']):
                traceback_lines.append(line.strip())

        return '\n'.join(traceback_lines) if traceback_lines else None

    def _parse_local_pytest_cache(self) -> List[TestFailure]:
        """Fallback: Parse local pytest cache for failure history."""
        failures = []
        cache_file = Path('.pytest_cache/v/cache/lastfailed')

        if not cache_file.exists():
            return failures

        try:
            with open(cache_file, 'r') as f:
                lastfailed = json.load(f)

            # These are tests that failed in last run
            # We don't have date info, so use current date
            current_date = datetime.now().isoformat()

            for test_id in lastfailed.keys():
                failure = TestFailure(
                    test_id=test_id,
                    failure_date=current_date,
                    ci_run_id='local',
                    failure_reason='Local pytest failure (from .pytest_cache)'
                )
                failures.append(failure)

            print(f"✅ Loaded {len(failures)} failures from local pytest cache")

        except Exception as e:
            print(f"⚠️  Error parsing pytest cache: {e}")

        return failures

    def store_failures(self, failures: List[TestFailure]) -> None:
        """
        Store failures in SQLite database (idempotent upsert).

        Args:
            failures: List of TestFailure objects to store
        """
        if not failures:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for failure in failures:
            cursor.execute("""
                INSERT OR REPLACE INTO test_failures
                (test_id, failure_date, ci_run_id, failure_reason, traceback, fixed_date, is_flaky)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                failure.test_id,
                failure.failure_date,
                failure.ci_run_id,
                failure.failure_reason,
                failure.traceback,
                failure.fixed_date,
                failure.is_flaky
            ))

        conn.commit()
        conn.close()

        print(f"✅ Stored {len(failures)} failures in database")

    def get_failure_count(self, test_id: str, days_back: int = 90) -> int:
        """Get total failure count for a test in last N days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        cursor.execute("""
            SELECT COUNT(*) FROM test_failures
            WHERE test_id = ? AND failure_date >= ?
        """, (test_id, cutoff_date))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def get_fixed_failure_count(self, test_id: str, days_back: int = 90) -> int:
        """
        Get count of FIXED failures (proven bug detectors).

        Fixed = Failure followed by 3 consecutive passes in CI.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        cursor.execute("""
            SELECT COUNT(*) FROM test_failures
            WHERE test_id = ? AND failure_date >= ? AND fixed_date IS NOT NULL
        """, (test_id, cutoff_date))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def is_flaky(self, test_id: str, lookback_runs: int = 10) -> bool:
        """
        Determine if test is flaky (fails 2-9/10 runs, never fixed).

        Args:
            test_id: Test identifier
            lookback_runs: Number of recent runs to check (default: 10)

        Returns:
            True if flaky, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent failures (last 30 days)
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()

        cursor.execute("""
            SELECT fixed_date FROM test_failures
            WHERE test_id = ? AND failure_date >= ?
            ORDER BY failure_date DESC
            LIMIT ?
        """, (test_id, cutoff_date, lookback_runs))

        failures = cursor.fetchall()
        conn.close()

        if not failures:
            return False

        failure_count = len(failures)

        # Flaky: 2-9 failures out of lookback_runs
        if 2 <= failure_count <= 9:
            # Check if any were fixed (3 consecutive passes)
            for (fixed_date,) in failures:
                if fixed_date is not None:
                    return False  # Was fixed, not flaky

            return True  # Never fixed = flaky

        return False

    def mark_as_fixed(self, test_id: str, fixed_date: str) -> None:
        """
        Mark all unfixed failures for a test as fixed.

        Call this when a test has 3 consecutive passes in CI.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE test_failures
            SET fixed_date = ?
            WHERE test_id = ? AND fixed_date IS NULL
        """, (fixed_date, test_id))

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
            print(f"✅ Marked {affected} failures for {test_id} as fixed")

    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics for monitoring."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) FROM test_failures")
        stats['total_failures'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT test_id) FROM test_failures")
        stats['unique_tests'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM test_failures WHERE fixed_date IS NOT NULL")
        stats['fixed_failures'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM test_failures WHERE is_flaky = 1")
        stats['flaky_tests'] = cursor.fetchone()[0]

        # Database file size
        stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)

        conn.close()

        return stats


if __name__ == '__main__':
    # Demo: Parse CI failures
    parser = CIFailureParser()

    # Try to parse from GitHub Actions (requires gh CLI + token)
    owner = os.getenv('GITHUB_REPOSITORY_OWNER', 'subtract0')
    repo = os.getenv('GITHUB_REPOSITORY', 'Agency').split('/')[-1]

    print(f"🔍 Parsing CI failures for {owner}/{repo}...")

    failures = parser.parse_github_actions_logs(owner, repo, days_back=90)

    if failures:
        parser.store_failures(failures)
    else:
        print("⚠️  No failures found (or CI access unavailable)")

    # Show stats
    stats = parser.get_database_stats()
    print(f"\n📊 Database Statistics:")
    print(f"  Total failures: {stats['total_failures']}")
    print(f"  Unique tests: {stats['unique_tests']}")
    print(f"  Fixed failures: {stats['fixed_failures']}")
    print(f"  Flaky tests: {stats['flaky_tests']}")
    print(f"  DB size: {stats['db_size_mb']:.2f} MB")
