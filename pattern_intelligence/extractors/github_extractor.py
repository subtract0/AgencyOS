"""
GitHubPatternExtractor - Extract patterns from GitHub repositories.

Uses existing Git and Bash tools to:
- Analyze successful commit patterns
- Extract problem-solution pairs from PR descriptions
- Identify refactoring patterns from code changes
- Mine issue resolution strategies
"""

import os
import re
import json
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .base_extractor import BasePatternExtractor
from ..coding_pattern import CodingPattern, ProblemContext, SolutionApproach, EffectivenessMetric

logger = logging.getLogger(__name__)


class GitHubPatternExtractor(BasePatternExtractor):
    """Extract coding patterns from GitHub repositories."""

    def __init__(self, repo_path: str = ".", confidence_threshold: float = 0.6):
        """
        Initialize GitHub pattern extractor.

        Args:
            repo_path: Path to the git repository
            confidence_threshold: Minimum confidence for patterns
        """
        super().__init__("github", confidence_threshold)
        self.repo_path = os.path.abspath(repo_path)

    def extract_patterns(self, days_back: int = 90, **kwargs) -> List[CodingPattern]:
        """
        Extract patterns from GitHub repository history.

        Args:
            days_back: How many days of history to analyze

        Returns:
            List of discovered patterns
        """
        patterns = []

        try:
            # Verify we're in a git repository
            if not self._is_git_repo():
                logger.warning("Not in a git repository")
                return patterns

            # Extract different types of patterns
            patterns.extend(self._extract_commit_patterns(days_back))
            patterns.extend(self._extract_fix_patterns(days_back))
            patterns.extend(self._extract_refactoring_patterns(days_back))
            patterns.extend(self._extract_feature_patterns(days_back))

            logger.info(f"Extracted {len(patterns)} patterns from GitHub history")
            return patterns

        except Exception as e:
            logger.error(f"Failed to extract patterns from GitHub: {e}")
            return []

    def _is_git_repo(self) -> bool:
        """Check if we're in a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _extract_commit_patterns(self, days_back: int) -> List[CodingPattern]:
        """Extract patterns from commit messages and changes."""
        patterns = []

        try:
            # Get commits with their stats
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            cmd = [
                "git", "log",
                f"--since={since_date}",
                "--pretty=format:%H|%s|%an|%ad",
                "--date=iso",
                "--numstat"
            ]

            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            if result.returncode != 0:
                return patterns

            # Parse commit data
            commit_data = self._parse_git_log_output(result.stdout)

            # Analyze commit patterns
            patterns.extend(self._analyze_commit_frequency_patterns(commit_data))
            patterns.extend(self._analyze_commit_size_patterns(commit_data))

        except Exception as e:
            logger.warning(f"Commit pattern extraction failed: {e}")

        return patterns

    def _extract_fix_patterns(self, days_back: int) -> List[CodingPattern]:
        """Extract patterns from bug fix commits."""
        patterns = []

        try:
            # Get commits that mention fixes
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            cmd = [
                "git", "log",
                f"--since={since_date}",
                "--grep=fix",
                "--grep=bug",
                "--grep=resolve",
                "--grep=solve",
                "-i",  # case insensitive
                "--pretty=format:%H|%s|%an|%ad",
                "--date=iso"
            ]

            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            if result.returncode != 0:
                return patterns

            fix_commits = result.stdout.strip().split('\n')
            if not fix_commits or fix_commits == ['']:
                return patterns

            # Analyze fix patterns
            for commit_line in fix_commits[:10]:  # Analyze top 10 fix commits
                if '|' not in commit_line:
                    continue

                parts = commit_line.split('|')
                if len(parts) < 4:
                    continue

                commit_hash, message, author, date = parts

                # Extract fix pattern
                fix_pattern = self._analyze_fix_commit(commit_hash, message)
                if fix_pattern:
                    patterns.append(fix_pattern)

        except Exception as e:
            logger.warning(f"Fix pattern extraction failed: {e}")

        return patterns

    def _extract_refactoring_patterns(self, days_back: int) -> List[CodingPattern]:
        """Extract patterns from refactoring commits."""
        patterns = []

        try:
            # Get commits that mention refactoring
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            cmd = [
                "git", "log",
                f"--since={since_date}",
                "--grep=refactor",
                "--grep=cleanup",
                "--grep=improve",
                "--grep=optimize",
                "-i",
                "--pretty=format:%H|%s|%an|%ad",
                "--date=iso"
            ]

            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            if result.returncode != 0:
                return patterns

            refactor_commits = result.stdout.strip().split('\n')
            if not refactor_commits or refactor_commits == ['']:
                return patterns

            # Analyze refactoring patterns
            for commit_line in refactor_commits[:5]:  # Analyze top 5 refactoring commits
                if '|' not in commit_line:
                    continue

                parts = commit_line.split('|')
                if len(parts) < 4:
                    continue

                commit_hash, message, author, date = parts

                refactor_pattern = self._analyze_refactoring_commit(commit_hash, message)
                if refactor_pattern:
                    patterns.append(refactor_pattern)

        except Exception as e:
            logger.warning(f"Refactoring pattern extraction failed: {e}")

        return patterns

    def _extract_feature_patterns(self, days_back: int) -> List[CodingPattern]:
        """Extract patterns from feature implementation commits."""
        patterns = []

        try:
            # Get commits that mention features
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            cmd = [
                "git", "log",
                f"--since={since_date}",
                "--grep=feat",
                "--grep=add",
                "--grep=implement",
                "--grep=create",
                "-i",
                "--pretty=format:%H|%s|%an|%ad",
                "--date=iso"
            ]

            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            if result.returncode != 0:
                return patterns

            feature_commits = result.stdout.strip().split('\n')
            if not feature_commits or feature_commits == ['']:
                return patterns

            # Analyze feature patterns
            for commit_line in feature_commits[:5]:  # Analyze top 5 feature commits
                if '|' not in commit_line:
                    continue

                parts = commit_line.split('|')
                if len(parts) < 4:
                    continue

                commit_hash, message, author, date = parts

                feature_pattern = self._analyze_feature_commit(commit_hash, message)
                if feature_pattern:
                    patterns.append(feature_pattern)

        except Exception as e:
            logger.warning(f"Feature pattern extraction failed: {e}")

        return patterns

    def _parse_git_log_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse git log output into structured data."""
        commits = []
        current_commit = None

        for line in output.split('\n'):
            if '|' in line and len(line.split('|')) == 4:
                # New commit line
                if current_commit:
                    commits.append(current_commit)

                parts = line.split('|')
                current_commit = {
                    'hash': parts[0],
                    'message': parts[1],
                    'author': parts[2],
                    'date': parts[3],
                    'files_changed': [],
                    'total_insertions': 0,
                    'total_deletions': 0
                }
            elif line.strip() and current_commit:
                # File change line (insertions/deletions/filename)
                parts = line.strip().split('\t')
                if len(parts) == 3:
                    insertions = int(parts[0]) if parts[0].isdigit() else 0
                    deletions = int(parts[1]) if parts[1].isdigit() else 0
                    filename = parts[2]

                    current_commit['files_changed'].append({
                        'filename': filename,
                        'insertions': insertions,
                        'deletions': deletions
                    })
                    current_commit['total_insertions'] += insertions
                    current_commit['total_deletions'] += deletions

        if current_commit:
            commits.append(current_commit)

        return commits

    def _analyze_commit_frequency_patterns(self, commits: List[Dict[str, Any]]) -> List[CodingPattern]:
        """Analyze commit frequency patterns."""
        patterns = []

        if len(commits) < 10:
            return patterns

        # Calculate average commits per day
        if commits:
            dates = [commit['date'][:10] for commit in commits]  # Extract date part
            unique_dates = set(dates)
            avg_commits_per_day = len(commits) / len(unique_dates)

            if avg_commits_per_day >= 2:  # High frequency pattern
                context = ProblemContext(
                    description="Maintain consistent development velocity with frequent commits",
                    domain="development_workflow",
                    constraints=["Quality maintenance", "Integration stability", "Team coordination"],
                    symptoms=["Complex features", "Need for incremental progress", "Team collaboration"],
                    scale=f"{len(commits)} commits over {len(unique_dates)} days"
                )

                solution = SolutionApproach(
                    approach="Frequent, small commits with clear messages",
                    implementation="Break work into small, atomic changes with descriptive commit messages",
                    tools=["git", "conventional_commits", "continuous_integration"],
                    reasoning="Enable better tracking, easier rollbacks, and improved collaboration"
                )

                outcome = EffectivenessMetric(
                    success_rate=0.8,
                    maintainability_impact="Easier to track changes and debug issues",
                    user_impact="Faster delivery and reduced risk",
                    adoption_rate=len(commits),
                    confidence=0.7
                )

                pattern = self.create_pattern(
                    context, solution, outcome,
                    f"frequent_commits_{len(commits)}",
                    ["workflow", "commits", "velocity"]
                )
                patterns.append(pattern)

        return patterns

    def _analyze_commit_size_patterns(self, commits: List[Dict[str, Any]]) -> List[CodingPattern]:
        """Analyze commit size patterns."""
        patterns = []

        if not commits:
            return patterns

        # Calculate commit sizes
        commit_sizes = [commit['total_insertions'] + commit['total_deletions'] for commit in commits]
        avg_size = sum(commit_sizes) / len(commit_sizes)

        if avg_size < 100:  # Small commit pattern
            context = ProblemContext(
                description="Maintain code quality through small, focused commits",
                domain="development_workflow",
                constraints=["Atomic changes", "Clear scope", "Easy review"],
                symptoms=["Large, complex changes", "Difficult reviews", "Integration issues"],
                scale=f"Average {avg_size:.0f} lines per commit"
            )

            solution = SolutionApproach(
                approach="Small, atomic commits with single responsibility",
                implementation="Limit commits to single logical change, break large features into smaller parts",
                tools=["git", "code_review", "feature_flags"],
                reasoning="Easier code review, better git history, reduced merge conflicts"
            )

            outcome = EffectivenessMetric(
                success_rate=0.85,
                maintainability_impact="Cleaner git history and easier debugging",
                user_impact="More stable releases with faster issue resolution",
                adoption_rate=len(commits),
                confidence=0.75
            )

            pattern = self.create_pattern(
                context, solution, outcome,
                f"small_commits_avg_{avg_size:.0f}",
                ["workflow", "commits", "size"]
            )
            patterns.append(pattern)

        return patterns

    def _analyze_fix_commit(self, commit_hash: str, message: str) -> Optional[CodingPattern]:
        """Analyze a specific fix commit for patterns."""
        try:
            # Get the diff for this commit
            cmd = ["git", "show", "--stat", commit_hash]
            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                return None

            diff_output = result.stdout

            # Extract problem from commit message
            problem_description = self._extract_problem_from_message(message)
            if not problem_description:
                return None

            # Analyze the fix approach
            fix_approach = self._analyze_fix_approach(diff_output, message)

            context = ProblemContext(
                description=problem_description,
                domain="debugging",
                constraints=["No breaking changes", "Maintain functionality", "Test validation"],
                symptoms=["Bug reports", "Test failures", "Unexpected behavior"]
            )

            solution = SolutionApproach(
                approach=fix_approach.get("approach", "Code fix with testing"),
                implementation=fix_approach.get("implementation", "Identify issue, implement fix, validate"),
                tools=fix_approach.get("tools", ["git", "testing"]),
                reasoning="Resolve issue while maintaining system stability"
            )

            outcome = EffectivenessMetric(
                success_rate=0.9,  # Assume fixes are generally successful
                maintainability_impact="Improved system stability",
                user_impact="Bug resolved",
                adoption_rate=1,
                confidence=0.6
            )

            return self.create_pattern(
                context, solution, outcome,
                f"fix_{commit_hash[:8]}",
                ["debugging", "fixes", "bug_resolution"]
            )

        except Exception as e:
            logger.debug(f"Failed to analyze fix commit {commit_hash}: {e}")
            return None

    def _analyze_refactoring_commit(self, commit_hash: str, message: str) -> Optional[CodingPattern]:
        """Analyze a refactoring commit for patterns."""
        try:
            # Get commit stats
            cmd = ["git", "show", "--stat", commit_hash]
            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                return None

            # Extract refactoring motivation
            refactor_reason = self._extract_refactoring_reason(message)

            context = ProblemContext(
                description=refactor_reason,
                domain="refactoring",
                constraints=["Maintain functionality", "Improve code quality", "No breaking changes"],
                symptoms=["Code complexity", "Maintainability issues", "Performance concerns"]
            )

            solution = SolutionApproach(
                approach="Code refactoring with behavior preservation",
                implementation="Restructure code while maintaining existing functionality",
                tools=["refactoring_tools", "testing", "code_analysis"],
                reasoning="Improve code quality and maintainability"
            )

            outcome = EffectivenessMetric(
                success_rate=0.85,
                maintainability_impact="Improved code structure and readability",
                user_impact="Better long-term maintainability",
                adoption_rate=1,
                confidence=0.7
            )

            return self.create_pattern(
                context, solution, outcome,
                f"refactor_{commit_hash[:8]}",
                ["refactoring", "code_quality", "maintenance"]
            )

        except Exception as e:
            logger.debug(f"Failed to analyze refactoring commit {commit_hash}: {e}")
            return None

    def _analyze_feature_commit(self, commit_hash: str, message: str) -> Optional[CodingPattern]:
        """Analyze a feature implementation commit."""
        try:
            # Extract feature description
            feature_description = self._extract_feature_description(message)

            context = ProblemContext(
                description=feature_description,
                domain="feature_development",
                constraints=["Requirements compliance", "Integration compatibility", "Performance"],
                symptoms=["User needs", "Business requirements", "System gaps"]
            )

            solution = SolutionApproach(
                approach="Incremental feature implementation",
                implementation="Design, implement, test, and integrate new functionality",
                tools=["development_tools", "testing", "integration"],
                reasoning="Add new capabilities while maintaining system stability"
            )

            outcome = EffectivenessMetric(
                success_rate=0.8,
                maintainability_impact="Extended system capabilities",
                user_impact="New functionality available",
                adoption_rate=1,
                confidence=0.6
            )

            return self.create_pattern(
                context, solution, outcome,
                f"feature_{commit_hash[:8]}",
                ["feature_development", "implementation", "enhancement"]
            )

        except Exception as e:
            logger.debug(f"Failed to analyze feature commit {commit_hash}: {e}")
            return None

    def _extract_problem_from_message(self, message: str) -> Optional[str]:
        """Extract problem description from commit message."""
        # Look for common fix patterns
        fix_patterns = [
            r"fix:?\s*(.+)",
            r"bug:?\s*(.+)",
            r"resolve:?\s*(.+)",
            r"solve:?\s*(.+)",
        ]

        for pattern in fix_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback to the full message if no specific pattern found
        return message if len(message) > 10 else None

    def _extract_refactoring_reason(self, message: str) -> str:
        """Extract refactoring reasoning from commit message."""
        refactor_patterns = [
            r"refactor:?\s*(.+)",
            r"cleanup:?\s*(.+)",
            r"improve:?\s*(.+)",
            r"optimize:?\s*(.+)",
        ]

        for pattern in refactor_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "Code refactoring for improved maintainability"

    def _extract_feature_description(self, message: str) -> str:
        """Extract feature description from commit message."""
        feature_patterns = [
            r"feat:?\s*(.+)",
            r"add:?\s*(.+)",
            r"implement:?\s*(.+)",
            r"create:?\s*(.+)",
        ]

        for pattern in feature_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "New feature implementation"

    def _analyze_fix_approach(self, diff_output: str, message: str) -> Dict[str, Any]:
        """Analyze the approach used in a fix."""
        approach_data = {
            "approach": "Code modification to resolve issue",
            "implementation": "Direct code changes",
            "tools": ["git", "editor"]
        }

        # Look for test-related changes
        if "test" in diff_output.lower():
            approach_data["tools"].append("testing")
            approach_data["implementation"] = "Code changes with test validation"

        # Look for configuration changes
        if any(ext in diff_output for ext in [".json", ".yaml", ".yml", ".conf"]):
            approach_data["tools"].append("configuration")

        # Look for dependency changes
        if any(file in diff_output for file in ["requirements.txt", "package.json", "Cargo.toml"]):
            approach_data["tools"].append("dependency_management")

        return approach_data