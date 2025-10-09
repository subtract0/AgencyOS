#!/usr/bin/env python3
"""
Git Worktree Manager for Isolated Agent Execution

Enables parallel agent missions by creating isolated git worktrees.
Each agent runs in its own filesystem space, preventing conflicts.

CONSTITUTIONAL COMPLIANCE:
- Article I: Systematic Safety - Filesystem isolation prevents conflicts
- Article II: 100% Verification - Each run is independently auditable
- Article III: No manual overrides - Automated worktree lifecycle
- Article IV: Continuous Learning - Execution results captured for analysis
- Article V: Spec-Driven - Built per Phase 1.5 Integration Plan

Version: 1.0.0
Created: 2025-10-08
"""

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class AgentExecutionResult(BaseModel):
    """Result from agent execution in worktree (typed, no Dict[str, Any])."""

    success: bool
    output_file: str | None = None
    stdout: str
    stderr: str
    execution_time: float


@dataclass
class WorktreeConfig:
    """Configuration for worktree creation.

    Attributes:
        branch_name: Unique branch name for the worktree
        base_path: Root directory for all worktrees
        context_files: Essential files to sync to worktree for agent context
    """

    branch_name: str
    base_path: Path = Path("worktrees")
    context_files: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default context files if not provided."""
        if not self.context_files:
            # Essential files to sync to worktree
            self.context_files = [
                ".env",
                ".claude/",
                ".cursor/",
                "meta_learning/",
                "dspy_agents/",
                "agency_config.yaml",
            ]


class WorktreeManager:
    """Manages git worktrees for isolated agent execution.

    This class provides the foundation for true parallel agent execution
    by creating isolated filesystem environments using git worktrees.
    Each worktree is a complete working copy of the repository on a
    separate branch, allowing multiple agents to work simultaneously
    without conflicts.

    Key Features:
    - Isolated filesystem space per agent
    - Automatic context synchronization (.env, configs, etc.)
    - Agent invocation with mission files
    - Automatic cleanup and branch management
    - Parallel execution support

    Example:
        >>> manager = WorktreeManager()
        >>> config = WorktreeConfig(branch_name="agent-1-task-abc")
        >>> path = manager.create_worktree(config)
        >>> result = manager.invoke_agent(path, "Fix bug in auth", "agent-1")
        >>> manager._remove_worktree("agent-1-task-abc")
    """

    def __init__(self, base_path: Path = Path("worktrees")):
        """Initialize the worktree manager.

        Args:
            base_path: Root directory for all worktrees (default: ./worktrees)
        """
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)

    def create_worktree(self, config: WorktreeConfig) -> Path:
        """Create a new git worktree with synced context.

        This method:
        1. Creates a new git worktree on a new branch
        2. Syncs essential context files (.env, .claude/, etc.)
        3. Returns the path to the isolated environment

        Args:
            config: WorktreeConfig with branch name and context files

        Returns:
            Path to the created worktree directory

        Raises:
            subprocess.CalledProcessError: If git worktree creation fails

        Constitutional Compliance:
            - Article I: Complete context via file sync
            - Article II: Verifiable isolation (separate branch)
        """
        worktree_path = self.base_path / config.branch_name

        # Remove if exists (from previous run)
        if worktree_path.exists():
            print(f"⚠️  Worktree exists, removing: {config.branch_name}")
            self._remove_worktree(config.branch_name)

        # Create git worktree
        print(f"📁 Creating worktree: {config.branch_name}")
        try:
            result = subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", config.branch_name],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"   ✓ Git worktree created at {worktree_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create worktree: {e.stderr}")
            raise

        # Sync essential context files
        self._sync_context(worktree_path, config.context_files)

        return worktree_path

    def _sync_context(self, worktree_path: Path, context_files: list[str]) -> None:
        """Copy essential files to worktree for full agent context.

        This ensures the agent has access to:
        - Environment variables (.env)
        - Configuration files (.claude/, .cursor/)
        - Meta-learning data (meta_learning/)
        - DSPy agent definitions (dspy_agents/)

        Args:
            worktree_path: Path to the worktree directory
            context_files: List of files/directories to sync

        Constitutional Compliance:
            - Article I: Complete context before action
        """
        print("🔄 Syncing context files to worktree...")

        for item in context_files:
            src = Path(item)
            if not src.exists():
                print(f"  ⊘ Skipped (not found): {item}")
                continue

            dest = worktree_path / item

            try:
                if src.is_dir():
                    # Copy directory recursively
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest, symlinks=True)
                    print(f"  ✓ Synced directory: {item}")
                else:
                    # Copy file
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    print(f"  ✓ Synced file: {item}")
            except Exception as e:
                print(f"  ⚠️  Failed to sync {item}: {e}")
                # Continue with other files - non-critical failure

    def invoke_agent(
        self, worktree_path: Path, mission: str, agent_id: str, timeout: int | None = None
    ) -> AgentExecutionResult:
        """Invoke an agent in the worktree with a specific mission.

        This method:
        1. Creates a mission.json file with the task specification
        2. Invokes agency.py in the worktree directory
        3. Collects results from benchmark_output.json
        4. Returns structured results

        Args:
            worktree_path: Path to the worktree directory
            mission: Task description for the agent
            agent_id: Unique identifier for the agent
            timeout: Optional timeout in seconds (default: no timeout)

        Returns:
            dict: Agent execution results with keys:
                - success: bool indicating if execution succeeded
                - output_file: str path to output file (if exists)
                - stdout: str standard output from agent
                - stderr: str standard error from agent
                - execution_time: float seconds elapsed

        Constitutional Compliance:
            - Article II: 100% verification via output capture
            - Article IV: Learning data captured in results
        """
        print(f"🤖 Invoking agent in worktree: {mission[:50]}...")

        # Prepare mission file
        mission_file = worktree_path / "mission.json"
        mission_data = {
            "mission": mission,
            "agent_id": agent_id,
            "output_file": "benchmark_output.json",
            "timestamp": time.time(),
        }
        mission_file.write_text(json.dumps(mission_data, indent=2))
        print("   ✓ Mission file created: mission.json")

        # Run agent (blocks until completion)
        start_time = time.time()
        try:
            result = subprocess.run(
                ["python", "agency.py", "--mission-file", "mission.json"],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            execution_time = time.time() - start_time

            print(f"   ✓ Agent execution complete ({execution_time:.2f}s)")

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print(f"   ⏱️  Agent execution timed out after {execution_time:.2f}s")
            return AgentExecutionResult(
                success=False,
                output_file=None,
                stdout="",
                stderr=f"timeout after {timeout}s",
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"   ❌ Agent execution failed: {e}")
            return AgentExecutionResult(
                success=False,
                output_file=None,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
            )

        # Collect results
        output_file = worktree_path / "benchmark_output.json"
        if output_file.exists():
            try:
                json.loads(output_file.read_text())  # Validate JSON
                return AgentExecutionResult(
                    success=True,
                    output_file=str(output_file),
                    stdout=result.stdout,
                    stderr=result.stderr,
                    execution_time=execution_time,
                )
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Failed to parse output JSON: {e}")
                # Fallback to raw output

        # Fallback: parse from stdout/stderr if no output file
        return AgentExecutionResult(
            success=result.returncode == 0,
            output_file=None,
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time=execution_time,
        )

    def _remove_worktree(self, branch_name: str) -> bool:
        """Remove a worktree and its branch.

        This method:
        1. Removes the git worktree (filesystem)
        2. Deletes the associated branch
        3. Returns success status

        Args:
            branch_name: Name of the branch/worktree to remove

        Returns:
            bool: True if worktree was removed, False if it didn't exist

        Constitutional Compliance:
            - Article III: Automated cleanup (no manual intervention)
        """
        worktree_path = self.base_path / branch_name

        if not worktree_path.exists():
            print(f"  ⊘ Worktree not found: {branch_name}")
            return False

        print(f"🗑️  Removing worktree: {branch_name}")

        try:
            # Remove git worktree (--force handles uncommitted changes)
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"   ✓ Worktree removed: {worktree_path}")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Failed to remove worktree: {e.stderr}")
            # Try manual removal as fallback
            try:
                shutil.rmtree(worktree_path)
                print(f"   ✓ Manually removed directory: {worktree_path}")
            except Exception as e2:
                print(f"   ❌ Manual removal failed: {e2}")
                return False

        # Delete branch if it exists (don't fail if branch doesn't exist)
        try:
            subprocess.run(
                ["git", "branch", "-D", branch_name], check=True, capture_output=True, text=True
            )
            print(f"   ✓ Branch deleted: {branch_name}")
        except subprocess.CalledProcessError:
            # Branch might not exist or already deleted - not critical
            print(f"   ⊘ Branch not found or already deleted: {branch_name}")

        return True

    def cleanup_all(self, keep_recent: int = 3) -> int:
        """Clean up old worktrees, keeping only recent ones.

        This method:
        1. Lists all worktrees in base_path
        2. Sorts by modification time (most recent first)
        3. Removes old worktrees beyond keep_recent count
        4. Prunes stale git worktree references

        Args:
            keep_recent: Number of recent worktrees to keep (default: 3)

        Returns:
            int: Number of worktrees removed

        Constitutional Compliance:
            - Article III: Automated cleanup prevents worktree buildup
        """
        print(f"🧹 Cleaning up old worktrees (keeping {keep_recent} most recent)...")

        # List all worktrees
        worktrees = sorted(self.base_path.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)

        if not worktrees:
            print("   ⊘ No worktrees found")
            return 0

        print(f"   Found {len(worktrees)} worktrees")

        # Remove old worktrees
        removed_count = 0
        for worktree in worktrees[keep_recent:]:
            if self._remove_worktree(worktree.name):
                removed_count += 1

        # Prune stale git worktree references
        try:
            subprocess.run(["git", "worktree", "prune"], check=True, capture_output=True, text=True)
            print("   ✓ Pruned stale worktree references")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Failed to prune worktrees: {e.stderr}")

        print(f"✅ Cleanup complete: {removed_count} worktrees removed")
        return removed_count

    def list_worktrees(self) -> list[dict[str, Any]]:
        """List all active worktrees with metadata.

        Returns:
            List of dicts with keys:
                - name: str branch name
                - path: Path to worktree directory
                - created: float timestamp
                - size_mb: float directory size in megabytes
        """
        worktrees = []

        for worktree_path in self.base_path.glob("*"):
            if not worktree_path.is_dir():
                continue

            # Calculate directory size
            size_bytes = sum(f.stat().st_size for f in worktree_path.rglob("*") if f.is_file())

            worktrees.append(
                {
                    "name": worktree_path.name,
                    "path": worktree_path,
                    "created": worktree_path.stat().st_mtime,
                    "size_mb": size_bytes / (1024 * 1024),
                }
            )

        return sorted(worktrees, key=lambda x: x["created"], reverse=True)


# CLI Interface
def main():
    """Command-line interface for worktree management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage git worktrees for agent execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create worktree and run agent
  %(prog)s create --branch agent-1-task-1 --mission "Fix auth bug" --agent-id agent-1

  # List all worktrees
  %(prog)s list

  # Clean up old worktrees
  %(prog)s cleanup --keep 3

  # Remove specific worktree
  %(prog)s remove --branch agent-1-task-1
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create worktree
    create = subparsers.add_parser("create", help="Create a new worktree and run agent")
    create.add_argument("--branch", required=True, help="Branch name for worktree")
    create.add_argument("--mission", required=True, help="Agent mission description")
    create.add_argument("--agent-id", required=True, help="Agent ID from registry")
    create.add_argument("--timeout", type=int, help="Timeout in seconds (optional)")

    # List worktrees
    list_cmd = subparsers.add_parser("list", help="List all active worktrees")

    # Remove worktree
    remove = subparsers.add_parser("remove", help="Remove a specific worktree")
    remove.add_argument("--branch", required=True, help="Branch name to remove")

    # Cleanup
    cleanup = subparsers.add_parser("cleanup", help="Clean up old worktrees")
    cleanup.add_argument("--keep", type=int, default=3, help="Keep N recent worktrees")

    args = parser.parse_args()
    manager = WorktreeManager()

    if args.command == "create":
        # Create worktree and invoke agent
        config = WorktreeConfig(branch_name=args.branch)
        path = manager.create_worktree(config)
        result = manager.invoke_agent(path, args.mission, args.agent_id, timeout=args.timeout)

        print(f"\n{'=' * 60}")
        print("✅ Agent execution complete!")
        print(f"{'=' * 60}")
        print(json.dumps(result, indent=2))

        # Cleanup after execution
        cleanup_input = input("\nRemove worktree now? [Y/n]: ")
        if cleanup_input.lower() != "n":
            manager._remove_worktree(args.branch)

    elif args.command == "list":
        # List all worktrees
        worktrees = manager.list_worktrees()

        if not worktrees:
            print("No worktrees found")
            return

        print(f"\n{'=' * 60}")
        print(f"Active Worktrees ({len(worktrees)})")
        print(f"{'=' * 60}")
        for wt in worktrees:
            print(f"\n📁 {wt['name']}")
            print(f"   Path: {wt['path']}")
            print(f"   Created: {time.ctime(wt['created'])}")
            print(f"   Size: {wt['size_mb']:.2f} MB")

    elif args.command == "remove":
        # Remove specific worktree
        success = manager._remove_worktree(args.branch)
        if success:
            print(f"✅ Worktree removed: {args.branch}")
        else:
            print(f"❌ Failed to remove worktree: {args.branch}")

    elif args.command == "cleanup":
        # Cleanup old worktrees
        removed = manager.cleanup_all(keep_recent=args.keep)
        print(f"✅ Cleanup complete: {removed} worktrees removed")


if __name__ == "__main__":
    main()
