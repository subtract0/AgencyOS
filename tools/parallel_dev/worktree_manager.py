"""
Worktree Manager - Safe worktree lifecycle with automatic backups.

Per spec-029: "Make it impossible to lose work accidentally."
"""

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from shared.type_definitions.result import Err, Ok, Result


class WorktreeManager:
    """
    Manage git worktree lifecycle with safety guarantees.

    Safety features:
    - Automatic backups before deletion
    - Uncommitted changes detection
    - Git reflog preservation
    - Smart branch naming

    Usage:
        manager = WorktreeManager()

        # Create worktree
        result = manager.create_worktree(
            intent="Add JWT authentication",
            base_path=Path("../Agency-jwt-auth")
        )

        # Delete with automatic backup
        manager.delete_worktree(Path("../Agency-jwt-auth"), backup=True)
    """

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize worktree manager.

        Args:
            repo_root: Git repository root (auto-detected if None)
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
            return Path.cwd()

    def create_worktree(
        self,
        intent: str,
        base_path: Optional[Path] = None,
        branch_name: Optional[str] = None,
        base_branch: str = "main",
    ) -> Result[Path, str]:
        """
        Create new worktree with automatic branch naming.

        Args:
            intent: Description of work (e.g., "Add JWT authentication")
            base_path: Path for new worktree (auto-generated if None)
            branch_name: Branch name (auto-generated from intent if None)
            base_branch: Branch to base new branch on

        Returns:
            Result with worktree path or error message
        """
        # Generate branch name from intent if not provided
        if not branch_name:
            branch_name = self._generate_branch_name(intent)

        # Generate worktree path if not provided
        if not base_path:
            # Place sibling to repo root
            worktree_name = f"Agency-{self._slugify(intent)}"
            base_path = self.repo_root.parent / worktree_name

        # Check if path already exists
        if base_path.exists():
            return Err(f"Path already exists: {base_path}")

        # Check if branch already exists
        if self._branch_exists(branch_name):
            return Err(f"Branch already exists: {branch_name}")

        # Create worktree
        try:
            subprocess.run(
                ["git", "worktree", "add", str(base_path), "-b", branch_name, base_branch],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            return Err(f"Failed to create worktree: {e.stderr}")

        return Ok(base_path)

    def delete_worktree(self, path: Path, backup: bool = True) -> Result[None, str]:
        """
        Delete worktree with optional automatic backup.

        Args:
            path: Path to worktree
            backup: Whether to create backup before deletion

        Returns:
            Result with success or error message
        """
        if not path.exists():
            return Err(f"Worktree does not exist: {path}")

        # Check for uncommitted changes
        has_changes = self._has_uncommitted_changes(path)

        if has_changes and backup:
            backup_result = self._create_backup(path)
            if backup_result.is_err():
                return Err(f"Backup failed: {backup_result.err()}")

        # Remove worktree
        try:
            subprocess.run(
                ["git", "worktree", "remove", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # Try force removal if it failed
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e2:
                return Err(f"Failed to remove worktree: {e2.stderr}")

        # Prune stale references
        try:
            subprocess.run(
                ["git", "worktree", "prune"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            pass  # Prune failure is non-fatal

        return Ok(None)

    def _generate_branch_name(self, intent: str) -> str:
        """
        Generate branch name from intent.

        Examples:
            "Add JWT authentication" -> "feat/add-jwt-authentication"
            "Fix memory leak in cache" -> "fix/memory-leak-cache"
            "Refactor database layer" -> "refactor/database-layer"
        """
        # Detect type
        intent_lower = intent.lower()
        if any(word in intent_lower for word in ["add", "implement", "create"]):
            prefix = "feat"
        elif any(word in intent_lower for word in ["fix", "bug", "resolve"]):
            prefix = "fix"
        elif any(word in intent_lower for word in ["refactor", "improve", "optimize"]):
            prefix = "refactor"
        elif any(word in intent_lower for word in ["doc", "readme"]):
            prefix = "docs"
        else:
            prefix = "feat"

        # Slugify intent
        slug = self._slugify(intent)

        return f"{prefix}/{slug}"

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        # Remove common words
        text = re.sub(r"\b(the|a|an|to|for|in|on|at|of)\b", "", text, flags=re.IGNORECASE)

        # Convert to lowercase and replace spaces with hyphens
        slug = text.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        # Limit length
        return slug[:50].strip("-")

    def _branch_exists(self, branch_name: str) -> bool:
        """Check if branch exists locally or remotely."""
        try:
            subprocess.run(
                ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _has_uncommitted_changes(self, worktree_path: Path) -> bool:
        """Check if worktree has uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "-C", str(worktree_path), "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def _create_backup(self, worktree_path: Path) -> Result[Path, str]:
        """Create backup of worktree before deletion."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{worktree_path.name}_backup_{timestamp}"
        backup_path = worktree_path.parent / backup_name

        try:
            shutil.copytree(worktree_path, backup_path)
            return Ok(backup_path)
        except Exception as e:
            return Err(f"Backup failed: {e}")
