#!/usr/bin/env python3
"""
Git Churn Analyzer - Track test brittleness via co-change frequency.

High co-change = brittle test (breaks on refactor).

Performance SLA: <5s for 5,000 test files.
"""

import subprocess
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class GitChurnMetrics:
    """Git churn metrics for a test file."""
    file_path: str
    commits_last_90_days: int
    lines_changed: int
    co_change_count: int  # Times test + production code changed together
    last_modified_date: str  # ISO 8601
    age_years: float  # Years since last modification


class GitChurnAnalyzer:
    """Analyze git history for test churn and brittleness."""

    def __init__(self, repo_path: Path = Path.cwd()):
        """
        Initialize git churn analyzer.

        Args:
            repo_path: Path to git repository (default: current directory)
        """
        self.repo_path = repo_path

    def get_test_churn_metrics(self, test_file: Path, days_back: int = 90) -> GitChurnMetrics:
        """
        Get git churn metrics for a test file.

        Args:
            test_file: Path to test file
            days_back: Days to look back (default: 90)

        Returns:
            GitChurnMetrics object
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # Get commit count for test file
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '--since', cutoff_date, '--follow', '--', str(test_file)],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                timeout=10
            )
            commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        except Exception:
            commits = 0

        # Get lines changed (insertions + deletions)
        try:
            result = subprocess.run(
                ['git', 'log', '--numstat', '--since', cutoff_date, '--follow', '--', str(test_file)],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                timeout=10
            )
            lines_changed = self._parse_numstat(result.stdout)
        except Exception:
            lines_changed = 0

        # Get co-change count (commits that modified both test and production code)
        co_changes = self._count_co_changes(test_file, days_back)

        # Get last modified date
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cI', '--', str(test_file)],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                timeout=5
            )
            last_modified = result.stdout.strip() or datetime.now().isoformat()
        except Exception:
            last_modified = datetime.now().isoformat()

        # Calculate age in years
        try:
            last_mod_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            age_years = (datetime.now() - last_mod_date.replace(tzinfo=None)).days / 365.25
        except Exception:
            age_years = 0.0

        return GitChurnMetrics(
            file_path=str(test_file),
            commits_last_90_days=commits,
            lines_changed=lines_changed,
            co_change_count=co_changes,
            last_modified_date=last_modified,
            age_years=age_years
        )

    def _parse_numstat(self, numstat_output: str) -> int:
        """Parse git log --numstat output to count total lines changed."""
        total_lines = 0
        for line in numstat_output.split('\n'):
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        additions = int(parts[0]) if parts[0] != '-' else 0
                        deletions = int(parts[1]) if parts[1] != '-' else 0
                        total_lines += additions + deletions
                    except ValueError:
                        continue
        return total_lines

    def _count_co_changes(self, test_file: Path, days_back: int) -> int:
        """
        Count commits where test file AND production code changed together.

        High co-change = brittle test (breaks when prod code refactored).
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # Get commit hashes for test file
        try:
            result = subprocess.run(
                ['git', 'log', '--format=%H', '--since', cutoff_date, '--follow', '--', str(test_file)],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                timeout=10
            )
            test_commits = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
        except Exception:
            return 0

        if not test_commits:
            return 0

        # Infer production file from test file path
        # e.g., tests/test_foo.py -> src/foo.py or tools/foo.py
        prod_file = self._infer_production_file(test_file)

        if not prod_file or not prod_file.exists():
            return 0

        # Get commit hashes for production file
        try:
            result = subprocess.run(
                ['git', 'log', '--format=%H', '--since', cutoff_date, '--follow', '--', str(prod_file)],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                timeout=10
            )
            prod_commits = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
        except Exception:
            return 0

        # Co-changes = intersection of commits
        co_changes = test_commits & prod_commits
        return len(co_changes)

    def _infer_production_file(self, test_file: Path) -> Path:
        """Infer production file from test file path."""
        # tests/test_foo.py -> foo.py
        test_name = test_file.name.replace('test_', '')

        # Common locations
        search_paths = [
            self.repo_path / 'src' / test_name,
            self.repo_path / 'tools' / test_name,
            self.repo_path / test_name,
            self.repo_path / test_name.replace('.py', '') / '__init__.py',
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def calculate_maintenance_burden(self, metrics: GitChurnMetrics, config: Dict = None) -> float:
        """
        Calculate maintenance burden from churn metrics.

        Formula: burden = (co_change_count * CHURN_WEIGHT) + (age_years * AGE_PENALTY_WEIGHT)

        Args:
            metrics: GitChurnMetrics object
            config: Optional config with churn_weight (default: 1.5) and age_penalty_weight (default: 0.5)

        Returns:
            Maintenance burden score (higher = worse)
        """
        if config is None:
            config = {}

        churn_weight = config.get('churn_weight', 1.5)
        age_penalty_weight = config.get('age_penalty_weight', 0.5)

        churn_burden = metrics.co_change_count * churn_weight
        age_burden = metrics.age_years * age_penalty_weight

        return churn_burden + age_burden

    def bulk_analyze_tests(self, test_files: list[Path]) -> Dict[str, GitChurnMetrics]:
        """
        Analyze multiple test files efficiently.

        Args:
            test_files: List of test file paths

        Returns:
            dict[file_path, GitChurnMetrics]
        """
        metrics = {}
        for test_file in test_files:
            try:
                metrics[str(test_file)] = self.get_test_churn_metrics(test_file)
            except Exception as e:
                # Skip files with errors
                continue
        return metrics


if __name__ == '__main__':
    # Demo: Analyze git churn
    analyzer = GitChurnAnalyzer()

    # Find test files
    test_files = list(Path('tests').rglob('test_*.py'))[:10]  # Sample 10 files

    print(f"🔍 Analyzing git churn for {len(test_files)} test files...\n")

    for test_file in test_files:
        metrics = analyzer.get_test_churn_metrics(test_file)
        burden = analyzer.calculate_maintenance_burden(metrics)

        print(f"{test_file.name:40} | Commits: {metrics.commits_last_90_days:3} | Co-changes: {metrics.co_change_count:2} | Age: {metrics.age_years:.1f}y | Burden: {burden:.1f}")

    print(f"\n✅ Git churn analysis complete")
