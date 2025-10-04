"""
Agency Swarm Tool wrapper for GitWorkflowTool.

Provides professional Git workflow operations for Agency agents:
- Branch management (create, switch, delete)
- Atomic commits with validation
- Push operations with upstream tracking
- Pull Request creation via GitHub CLI
- Complete workflow protocol enforcement

Constitutional Compliance:
- Article II: 100% verification (Green Main enforcement)
- Article III: Automated merge enforcement (PR required)
- Article V: Spec-driven development (commit message validation)

Usage by agents:
    from tools import GitWorkflowToolAgency

    # Create branch
    result = git_workflow.run(
        operation="create_branch",
        branch_name="feature/new-feature"
    )

    # Commit changes
    result = git_workflow.run(
        operation="commit",
        message="feat: Add new feature",
        files=["file1.py", "file2.py"]
    )

    # Create PR
    result = git_workflow.run(
        operation="create_pr",
        title="feat: New Feature",
        body="Description",
        reviewers=["username"]
    )
"""

import os
from typing import Literal

from agency_swarm.tools import BaseTool
from pydantic import Field

from tools.git_workflow import GitWorkflowProtocol, GitWorkflowTool


class GitWorkflowToolAgency(BaseTool):  # type: ignore[misc]
    """
    Professional Git workflow tool for Agency agents.

    Wraps GitWorkflowTool to provide Agency Swarm-compatible interface.
    Supports complete Git workflow: branch → commit → push → PR.
    """

    operation: Literal[
        "create_branch",
        "switch_branch",
        "delete_branch",
        "get_current_branch",
        "commit",
        "push",
        "create_pr",
        "get_status",
        "start_feature",
        "cleanup_after_merge",
    ] = Field(
        ...,
        description=(
            "Git operation to perform:\n"
            "- create_branch: Create new branch from main\n"
            "- switch_branch: Switch to existing branch\n"
            "- delete_branch: Delete branch\n"
            "- get_current_branch: Get current branch name\n"
            "- commit: Create commit with staged changes\n"
            "- push: Push current branch to remote\n"
            "- create_pr: Create Pull Request\n"
            "- get_status: Get git status\n"
            "- start_feature: High-level feature workflow start\n"
            "- cleanup_after_merge: Clean up after PR merge"
        ),
    )

    branch_name: str | None = Field(
        None, description="Branch name (required for create_branch, switch_branch, delete_branch)"
    )

    message: str | None = Field(
        None, description="Commit message (required for commit operation)"
    )

    files: list[str] | None = Field(
        None, description="Files to commit (optional, commits all if not specified)"
    )

    pr_title: str | None = Field(None, description="Pull Request title (required for create_pr)")

    pr_body: str | None = Field(
        None, description="Pull Request description (required for create_pr)"
    )

    reviewers: list[str] | None = Field(None, description="PR reviewer usernames (optional)")

    base_branch: str | None = Field(
        "main", description="Base branch for operations (default: main)"
    )

    force: bool = Field(False, description="Force operation (e.g., force delete branch)")

    def run(self) -> str:
        """
        Execute Git workflow operation.

        Returns:
            str: Operation result or error message
        """
        import warnings

        warnings.warn(
            "GitWorkflowToolAgency is deprecated. Use GitUnified instead. "
            "This tool will be removed after 2025-11-02.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            # Get repository root
            repo_path = os.getcwd()

            # Operations using low-level GitWorkflowTool
            if self.operation in [
                "create_branch",
                "switch_branch",
                "delete_branch",
                "get_current_branch",
                "commit",
                "push",
                "get_status",
            ]:
                tool = GitWorkflowTool(repo_path=repo_path)
                return self._execute_low_level(tool)

            # Operations using high-level GitWorkflowProtocol
            elif self.operation in ["start_feature", "cleanup_after_merge"]:
                protocol = GitWorkflowProtocol(repo_path=repo_path)
                return self._execute_high_level(protocol)

            # Create PR uses both
            elif self.operation == "create_pr":
                protocol = GitWorkflowProtocol(repo_path=repo_path)
                return self._execute_create_pr(protocol)

            else:
                return f"Unknown operation: {self.operation}"

        except Exception as e:
            return f"Error: {str(e)}"

    def _execute_low_level(self, tool: GitWorkflowTool) -> str:
        """Execute low-level git operations."""
        if self.operation == "create_branch":
            if not self.branch_name:
                return "Error: branch_name required for create_branch"

            result = tool.create_branch(self.branch_name, base=self.base_branch or "main")

            if result.is_ok():
                branch_info = result.unwrap()
                return f"✅ Created branch: {branch_info.name} (from {branch_info.base_branch})"
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        elif self.operation == "switch_branch":
            if not self.branch_name:
                return "Error: branch_name required for switch_branch"

            result = tool.switch_branch(self.branch_name)

            if result.is_ok():
                return f"✅ Switched to branch: {self.branch_name}"
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        elif self.operation == "delete_branch":
            if not self.branch_name:
                return "Error: branch_name required for delete_branch"

            result = tool.delete_branch(self.branch_name, force=self.force)

            if result.is_ok():
                return f"✅ Deleted branch: {self.branch_name}"
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        elif self.operation == "get_current_branch":
            result = tool.get_current_branch()

            if result.is_ok():
                return f"Current branch: {result.unwrap()}"
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        elif self.operation == "commit":
            if not self.message:
                return "Error: message required for commit"

            # Stage files first
            if self.files:
                stage_result = tool.stage_files(self.files)
                if not stage_result.is_ok():
                    error = stage_result.unwrap_err()
                    return f"❌ Failed to stage files: {error.message}"
            else:
                stage_result = tool.stage_all()
                if not stage_result.is_ok():
                    error = stage_result.unwrap_err()
                    return f"❌ Failed to stage files: {error.message}"

            # Create commit
            result = tool.commit(self.message)

            if result.is_ok():
                commit_info = result.unwrap()
                return f"✅ Committed: {commit_info.sha[:8]} - {self.message.split(chr(10))[0]}"
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        elif self.operation == "push":
            # Get current branch
            branch_result = tool.get_current_branch()
            if not branch_result.is_ok():
                return "❌ Failed to get current branch"

            branch = branch_result.unwrap()
            result = tool.push_branch(branch, set_upstream=True)

            if result.is_ok():
                return f"✅ Pushed branch: {branch}"
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        elif self.operation == "get_status":
            result = tool.get_status()

            if result.is_ok():
                status = result.unwrap()
                if not status.strip():
                    return "✅ Working tree clean"
                return f"Status:\n{status}"
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        return "Unknown operation"

    def _execute_high_level(self, protocol: GitWorkflowProtocol) -> str:
        """Execute high-level workflow operations."""
        if self.operation == "start_feature":
            if not self.branch_name:
                return "Error: branch_name required for start_feature"

            result = protocol.start_feature(self.branch_name, base=self.base_branch or "main")

            if result.is_ok():
                workflow = result.unwrap()
                return (
                    f"✅ Started feature workflow:\n"
                    f"  - Branch: {workflow['branch_name']}\n"
                    f"  - Base: {workflow['base_branch']}\n"
                    f"  - Started: {workflow['started_at']}"
                )
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        elif self.operation == "cleanup_after_merge":
            if not self.branch_name:
                return "Error: branch_name required for cleanup_after_merge"

            result = protocol.cleanup_after_merge(self.branch_name)

            if result.is_ok():
                return f"✅ Cleaned up after merge: switched to main, pulled latest, deleted {self.branch_name}"
            else:
                error = result.unwrap_err()
                return f"❌ Failed: {error.message}"

        return "Unknown operation"

    def _execute_create_pr(self, protocol: GitWorkflowProtocol) -> str:
        """Execute PR creation."""
        if not self.pr_title or not self.pr_body:
            return "Error: pr_title and pr_body required for create_pr"

        result = protocol.create_pr(
            title=self.pr_title,
            body=self.pr_body,
            base=self.base_branch or "main",
            reviewers=self.reviewers,
        )

        if result.is_ok():
            pr_info = result.unwrap()
            output = [
                "✅ Pull Request created:",
                f"  - URL: {pr_info.url}",
                f"  - Title: {pr_info.title}",
                f"  - Base: {pr_info.base} ← {pr_info.head}",
            ]
            if self.reviewers:
                output.append(f"  - Reviewers: {', '.join(self.reviewers)}")
            return "\n".join(output)
        else:
            error = result.unwrap_err()
            return f"❌ Failed: {error.message}"


# Export for tools/__init__.py
git_workflow_tool_agency = GitWorkflowToolAgency
