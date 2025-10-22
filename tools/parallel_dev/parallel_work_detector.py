"""
Parallel Work Detector - Detect and analyze parallel development across worktrees.

Per spec-029-parallel-development-rails.md: Detect conflicts BEFORE they happen.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class WorktreeInfo:
    """Information about a git worktree."""

    path: Path
    branch: str
    commit: str
    is_bare: bool
    has_uncommitted_changes: bool
    modified_files: List[str]


class ConflictAnalysis(BaseModel):
    """Analysis of potential conflicts with parallel work."""

    conflict_probability: float = Field(ge=0.0, le=1.0, description="Probability of conflict (0-1)")
    overlapping_files: List[str] = Field(default_factory=list, description="Files modified by multiple agents")
    parallel_worktrees: List[str] = Field(default_factory=list, description="Active worktrees with uncommitted work")
    recommendation: str = Field(description="Recommended action (proceed/coordinate/worktree)")
    safe_to_proceed: bool = Field(description="Whether it's safe to proceed without worktree")


class ParallelWorkDetector:
    """
    Detect parallel work across git worktrees and analyze conflict probability.

    Usage:
        detector = ParallelWorkDetector()
        worktrees = detector.scan_worktrees()
        analysis = detector.analyze_conflicts(["src/auth.py", "tests/test_auth.py"])

        if not analysis.safe_to_proceed:
            print(f"⚠️  Conflict probability: {analysis.conflict_probability:.0%}")
            print(f"   Recommendation: {analysis.recommendation}")
    """

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize detector.

        Args:
            repo_root: Root of git repository (auto-detected if None)
        """
        self.repo_root = repo_root or self._find_repo_root()

    def _find_repo_root(self) -> Path:
        """Find git repository root."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            # Might be bare repo
            return Path.cwd()

    def scan_worktrees(self) -> List[WorktreeInfo]:
        """
        Scan all git worktrees for parallel work.

        Returns:
            List of worktree information with uncommitted changes status
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return []

        worktrees = []
        current_worktree = {}

        for line in result.stdout.split("\n"):
            if not line.strip():
                if current_worktree:
                    worktrees.append(self._parse_worktree(current_worktree))
                    current_worktree = {}
                continue

            if line.startswith("worktree "):
                current_worktree["path"] = line.split(" ", 1)[1]
            elif line.startswith("HEAD "):
                current_worktree["commit"] = line.split(" ", 1)[1]
            elif line.startswith("branch "):
                current_worktree["branch"] = line.split(" ", 1)[1].replace("refs/heads/", "")
            elif line == "bare":
                current_worktree["is_bare"] = True

        # Handle last worktree
        if current_worktree:
            worktrees.append(self._parse_worktree(current_worktree))

        return worktrees

    def _parse_worktree(self, data: dict) -> WorktreeInfo:
        """Parse worktree data dict into WorktreeInfo."""
        path = Path(data["path"])
        is_bare = data.get("is_bare", False)

        # Get modified files (skip for bare repos)
        modified_files = []
        has_uncommitted = False

        if not is_bare:
            try:
                # Change to worktree directory
                result = subprocess.run(
                    ["git", "-C", str(path), "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                if result.stdout.strip():
                    has_uncommitted = True
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            # Extract filename (after status codes)
                            parts = line.strip().split(None, 1)
                            if len(parts) == 2:
                                modified_files.append(parts[1])
            except subprocess.CalledProcessError:
                pass  # Can't read status, treat as no changes

        return WorktreeInfo(
            path=path,
            branch=data.get("branch", ""),
            commit=data.get("commit", ""),
            is_bare=is_bare,
            has_uncommitted_changes=has_uncommitted,
            modified_files=modified_files,
        )

    def analyze_conflicts(self, files_to_modify: List[str]) -> ConflictAnalysis:
        """
        Analyze potential conflicts if user modifies given files.

        Args:
            files_to_modify: List of files user intends to modify

        Returns:
            Conflict analysis with probability and recommendations
        """
        worktrees = self.scan_worktrees()

        # Get all modified files from parallel work
        parallel_files = set()
        active_worktrees = []

        for wt in worktrees:
            if wt.has_uncommitted_changes and not wt.is_bare:
                parallel_files.update(wt.modified_files)
                active_worktrees.append(str(wt.path.name))

        # Calculate overlap
        user_files = set(files_to_modify)
        overlapping = list(user_files & parallel_files)

        # Calculate conflict probability
        if not user_files:
            probability = 0.0
        elif not parallel_files:
            probability = 0.0
        else:
            # Base probability on file overlap
            probability = len(overlapping) / len(user_files)

            # Adjust for total parallel work volume
            if len(active_worktrees) > 2:
                probability *= 1.2  # More agents = higher risk
            elif len(active_worktrees) == 0:
                probability = 0.0

        # Determine recommendation
        if probability == 0.0:
            recommendation = "proceed"
            safe = True
        elif probability < 0.1:
            recommendation = "proceed_with_caution"
            safe = True
        elif probability < 0.3:
            recommendation = "use_worktree"
            safe = False
        else:
            recommendation = "coordinate_with_agents"
            safe = False

        return ConflictAnalysis(
            conflict_probability=min(probability, 1.0),
            overlapping_files=overlapping,
            parallel_worktrees=active_worktrees,
            recommendation=recommendation,
            safe_to_proceed=safe,
        )

    def get_status_summary(self) -> str:
        """
        Get human-readable summary of all parallel work.

        Returns:
            Formatted status string suitable for display
        """
        worktrees = self.scan_worktrees()

        lines = ["🤖 ACTIVE WORKTREES:"]
        lines.append("─" * 60)

        for wt in worktrees:
            status_icon = "📝" if wt.has_uncommitted_changes else "✅"
            branch_name = wt.branch or "(bare)"
            changes = f"{len(wt.modified_files)} files" if wt.modified_files else "clean"

            lines.append(f"{status_icon} {wt.path.name:30} [{branch_name}] {changes}")

        active_count = sum(1 for wt in worktrees if wt.has_uncommitted_changes)
        lines.append(f"\nTotal: {len(worktrees)} worktrees ({active_count} with uncommitted work)")

        return "\n".join(lines)
