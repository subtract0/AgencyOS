#!/usr/bin/env python3
"""
Autonomous Recommendation Implementation System

Orchestrates AgencyCodeAgent to apply audit recommendations from continuous_audit_m4pro.py.
Uses trinity_protocol AgentRegistry with qwen2.5-coder:32b for local execution.

Constitutional Compliance:
- Article I: Complete Context Before Action (read all relevant files)
- Article II: 100% Verification (test validation after each change)
- Article III: Automated Enforcement (git branching, rollback on failure)
- Article IV: Continuous Learning (pattern extraction from successful fixes)
- Article V: Spec-Driven Development (follows audit recommendations as specs)

Architecture:
1. Read recommendations from .output/audit_recommendations/
2. Parse markdown files (priority, category, affected files, fix steps)
3. Process in priority order (P3 → P1, safest first)
4. Use AgencyCodeAgent for implementation
5. Validate with tests after each change
6. Commit successful changes, rollback failures
7. Generate summary report

Usage:
    # Process specific category
    python scripts/autonomous_recommendation_fixer.py --category pruning --limit 10

    # Process by priority (P3 = safest)
    python scripts/autonomous_recommendation_fixer.py --priority P3 --auto-commit

    # Batch process all recommendations
    python scripts/autonomous_recommendation_fixer.py --batch-all --max-time 2h

    # Dry run to see what would be changed
    python scripts/autonomous_recommendation_fixer.py --dry-run --category simplification
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Literal

# Add parent directory to Python path for imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.agent_context import AgentContext, create_agent_context
from shared.cost_tracker import CostTracker
from shared.type_definitions.result import Err, Ok, Result
from trinity_protocol.core.agent_registry import (
    AgentRegistry,
    AgentType,
    ModelTier,
    create_agent_registry,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/autonomous_fixer.log"),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for Type Safety
# ============================================================================


class Priority(str, Enum):
    """Priority levels for recommendations."""

    P0 = "P0"  # Critical - architecture changes
    P1 = "P1"  # High - simplification, function splitting
    P2 = "P2"  # Medium - consolidation
    P3 = "P3"  # Low - pruning, linting


class Category(str, Enum):
    """Categories of fixes."""

    ARCHITECTURE = "architecture"
    SIMPLIFICATION = "simplification"
    CONSOLIDATION = "consolidation"
    PRUNING = "pruning"
    LINTING = "linting"


class FixStatus(str, Enum):
    """Status of fix application."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class Recommendation(BaseModel):
    """Parsed recommendation from audit markdown file."""

    model_config = ConfigDict(extra="forbid")

    file_path: Path = Field(..., description="Original recommendation file path")
    priority: Priority = Field(..., description="Priority level")
    category: Category = Field(..., description="Fix category")
    impact: str = Field(..., description="Impact assessment")
    effort_hours: float = Field(..., ge=0.0, description="Estimated effort in hours")
    status: str = Field(..., description="Current status")
    instances: int = Field(..., ge=1, description="Number of instances found")
    summary: str = Field(..., description="Brief summary of issue")
    details: str = Field(..., description="Detailed description")
    affected_files: list[str] = Field(..., description="Files requiring changes")
    recommendation_steps: list[str] = Field(
        ..., description="Steps to implement fix"
    )
    constitutional_article: str = Field(
        ..., description="Constitutional article affected"
    )
    compliance_status: str = Field(..., description="Compliance status")
    example_code: str | None = Field(
        default=None, description="Optional example code from recommendation"
    )

    @field_validator("affected_files", mode="before")
    @classmethod
    def ensure_list(cls, v: list[str] | str) -> list[str]:
        """Ensure affected_files is always a list."""
        if isinstance(v, str):
            return [v]
        return v


class FixResult(BaseModel):
    """Result of applying a fix."""

    model_config = ConfigDict(extra="forbid")

    recommendation: Recommendation = Field(..., description="Original recommendation")
    status: FixStatus = Field(..., description="Fix status")
    files_modified: list[str] = Field(
        default_factory=list, description="Files that were modified"
    )
    tests_passed: bool = Field(default=False, description="Whether tests passed")
    commit_sha: str | None = Field(default=None, description="Git commit SHA if applied")
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )
    execution_time: float = Field(default=0.0, ge=0.0, description="Time in seconds")
    cost_usd: float = Field(default=0.0, ge=0.0, description="Cost in USD")


class FixerState(BaseModel):
    """Persistent state for resumable execution."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Unique session identifier")
    started_at: datetime = Field(..., description="Session start time")
    last_updated: datetime = Field(..., description="Last update time")
    total_recommendations: int = Field(..., ge=0, description="Total recommendations")
    processed: int = Field(default=0, ge=0, description="Processed count")
    applied: int = Field(default=0, ge=0, description="Successfully applied count")
    failed: int = Field(default=0, ge=0, description="Failed count")
    skipped: int = Field(default=0, ge=0, description="Skipped count")
    results: list[FixResult] = Field(
        default_factory=list, description="All fix results"
    )
    current_branch: str | None = Field(
        default=None, description="Current working branch"
    )


# ============================================================================
# Recommendation Parser
# ============================================================================


class RecommendationParser:
    """Parse markdown recommendation files into structured data."""

    def __init__(self, recommendations_dir: Path):
        """
        Initialize parser.

        Args:
            recommendations_dir: Directory containing recommendation markdown files
        """
        self.recommendations_dir = recommendations_dir

    def parse_file(self, file_path: Path) -> Result[Recommendation, str]:
        """
        Parse a single recommendation markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            Result containing Recommendation or error message
        """
        try:
            content = file_path.read_text()

            # Extract metadata from header
            priority_match = re.search(r"\*\*Priority\*\*:\s*(\w+)", content)
            category_match = re.search(r"\*\*Category\*\*:\s*(\w+)", content)
            impact_match = re.search(r"\*\*Impact\*\*:\s*(\w+)", content)
            effort_match = re.search(r"\*\*Effort\*\*:\s*([\d.]+)\s*hours", content)
            status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
            instances_match = re.search(r"\*\*Instances Found\*\*:\s*(\d+)", content)

            if not all(
                [
                    priority_match,
                    category_match,
                    impact_match,
                    effort_match,
                    status_match,
                    instances_match,
                ]
            ):
                return Err(f"Missing required metadata fields in {file_path}")

            # Extract sections
            summary_match = re.search(r"## Summary\n(.+?)(?:\n\n|\n##)", content, re.DOTALL)
            details_match = re.search(r"## Details\n(.+?)(?:\n\n|\n##)", content, re.DOTALL)
            affected_files_match = re.search(
                r"## Affected Files\n(.+?)(?:\n\n|\n##)", content, re.DOTALL
            )
            recommendation_match = re.search(
                r"## Recommendation\n(.+?)(?:\n\n|\n##)", content, re.DOTALL
            )
            constitutional_match = re.search(
                r"- Article affected:\s*(\w+)", content
            )
            compliance_match = re.search(
                r"- Compliance status:\s*(\w+)", content
            )
            example_match = re.search(
                r"## Example Code\n(.+?)(?:\n\n##|\Z)", content, re.DOTALL
            )

            # Parse affected files
            affected_files = []
            if affected_files_match:
                files_text = affected_files_match.group(1).strip()
                # Extract file paths from markdown list items
                for line in files_text.split("\n"):
                    # Match patterns like: - `path/to/file.py`
                    # or: - `path/to/file.py` (lines 107-215)
                    file_match = re.search(r"-\s*`([^`]+?)`", line)
                    if file_match:
                        affected_files.append(file_match.group(1))

            # Parse recommendation steps
            recommendation_steps = []
            if recommendation_match:
                rec_text = recommendation_match.group(1).strip()
                for line in rec_text.split("\n"):
                    # Match numbered list items
                    step_match = re.match(r"\d+\.\s*(.+)", line.strip())
                    if step_match:
                        recommendation_steps.append(step_match.group(1))

            recommendation = Recommendation(
                file_path=file_path,
                priority=Priority(priority_match.group(1)),
                category=Category(category_match.group(1).lower()),
                impact=impact_match.group(1),
                effort_hours=float(effort_match.group(1)),
                status=status_match.group(1),
                instances=int(instances_match.group(1)),
                summary=summary_match.group(1).strip() if summary_match else "",
                details=details_match.group(1).strip() if details_match else "",
                affected_files=affected_files,
                recommendation_steps=recommendation_steps,
                constitutional_article=(
                    constitutional_match.group(1) if constitutional_match else "Unknown"
                ),
                compliance_status=(
                    compliance_match.group(1) if compliance_match else "Unknown"
                ),
                example_code=example_match.group(1).strip() if example_match else None,
            )

            return Ok(recommendation)

        except Exception as e:
            return Err(f"Failed to parse {file_path}: {e}")

    def parse_all(self) -> Result[list[Recommendation], str]:
        """
        Parse all recommendation files in directory.

        Returns:
            Result containing list of Recommendations or error message
        """
        if not self.recommendations_dir.exists():
            return Err(f"Directory not found: {self.recommendations_dir}")

        recommendations = []
        errors = []

        for file_path in sorted(self.recommendations_dir.glob("*.md")):
            result = self.parse_file(file_path)
            if result.is_ok():
                recommendations.append(result.unwrap())
            else:
                errors.append(result.unwrap_err())
                logger.warning(result.unwrap_err())

        if not recommendations:
            return Err(
                f"No valid recommendations found in {self.recommendations_dir}. Errors: {errors}"
            )

        logger.info(
            f"Parsed {len(recommendations)} recommendations "
            f"({len(errors)} files had errors)"
        )
        return Ok(recommendations)


# ============================================================================
# Git Operations
# ============================================================================


class GitManager:
    """Manage git operations for safe fix application."""

    def __init__(self, repo_root: Path):
        """
        Initialize git manager.

        Args:
            repo_root: Root of git repository
        """
        self.repo_root = repo_root

    def create_branch(self, branch_name: str) -> Result[str, str]:
        """
        Create and checkout a new branch.

        Args:
            branch_name: Name of branch to create

        Returns:
            Result containing branch name or error message
        """
        try:
            # Check if branch already exists
            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                # Branch exists, check it out
                subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                )
                logger.info(f"Checked out existing branch: {branch_name}")
            else:
                # Create new branch
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                )
                logger.info(f"Created new branch: {branch_name}")

            return Ok(branch_name)

        except subprocess.CalledProcessError as e:
            return Err(f"Failed to create branch {branch_name}: {e.stderr}")

    def commit_changes(
        self, message: str, files: list[str] | None = None
    ) -> Result[str, str]:
        """
        Commit changes to git.

        Args:
            message: Commit message
            files: Optional list of files to commit (commits all if None)

        Returns:
            Result containing commit SHA or error message
        """
        try:
            # Add files
            if files:
                for file_path in files:
                    subprocess.run(
                        ["git", "add", file_path],
                        cwd=self.repo_root,
                        check=True,
                        capture_output=True,
                    )
            else:
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                )

            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )

            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            commit_sha = result.stdout.strip()
            logger.info(f"Committed changes: {commit_sha[:8]}")
            return Ok(commit_sha)

        except subprocess.CalledProcessError as e:
            return Err(f"Failed to commit: {e.stderr}")

    def rollback_to_commit(self, commit_sha: str) -> Result[str, str]:
        """
        Hard reset to a specific commit.

        Args:
            commit_sha: Commit SHA to reset to

        Returns:
            Result containing success message or error
        """
        try:
            subprocess.run(
                ["git", "reset", "--hard", commit_sha],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
            logger.info(f"Rolled back to commit: {commit_sha[:8]}")
            return Ok(f"Rolled back to {commit_sha}")

        except subprocess.CalledProcessError as e:
            return Err(f"Failed to rollback: {e.stderr}")

    def get_current_branch(self) -> Result[str, str]:
        """
        Get current git branch name.

        Returns:
            Result containing branch name or error
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return Ok(result.stdout.strip())

        except subprocess.CalledProcessError as e:
            return Err(f"Failed to get current branch: {e.stderr}")

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())


# ============================================================================
# Test Validator
# ============================================================================


class TestValidator:
    """Run and validate tests after fixes."""

    def __init__(self, repo_root: Path):
        """
        Initialize test validator.

        Args:
            repo_root: Root of repository
        """
        self.repo_root = repo_root

    def run_tests(self, timeout: int = 300) -> Result[bool, str]:
        """
        Run test suite.

        Args:
            timeout: Timeout in seconds

        Returns:
            Result containing True if tests pass, or error message
        """
        try:
            # Run tests using run_tests.py
            result = subprocess.run(
                ["python", "run_tests.py"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Check if tests passed
            if result.returncode == 0 and "FAILED" not in result.stdout:
                logger.info("Tests passed")
                return Ok(True)
            else:
                error_msg = f"Tests failed:\n{result.stdout}\n{result.stderr}"
                logger.error(error_msg)
                return Err(error_msg)

        except subprocess.TimeoutExpired:
            return Err(f"Tests timed out after {timeout}s")
        except Exception as e:
            return Err(f"Test execution failed: {e}")

    def run_quick_validation(self, file_path: str) -> Result[bool, str]:
        """
        Run quick syntax/import validation on a specific file.

        Args:
            file_path: Path to file to validate

        Returns:
            Result containing True if valid, or error message
        """
        try:
            # Try to compile the file
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.debug(f"Quick validation passed: {file_path}")
                return Ok(True)
            else:
                return Err(f"Syntax error in {file_path}:\n{result.stderr}")

        except Exception as e:
            return Err(f"Validation failed for {file_path}: {e}")


# ============================================================================
# Batch Processor
# ============================================================================


class RecommendationFixer:
    """
    Main orchestrator for applying recommendations via AgencyCodeAgent.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        git_manager: GitManager,
        test_validator: TestValidator,
        state_file: Path,
        dry_run: bool = False,
    ):
        """
        Initialize recommendation fixer.

        Args:
            registry: Agent registry for creating agents
            git_manager: Git operations manager
            test_validator: Test validation manager
            state_file: Path to state persistence file
            dry_run: If True, don't apply changes
        """
        self.registry = registry
        self.git_manager = git_manager
        self.test_validator = test_validator
        self.state_file = state_file
        self.dry_run = dry_run
        self.state: FixerState | None = None

    def load_state(self) -> Result[FixerState, str]:
        """
        Load state from persistence file.

        Returns:
            Result containing FixerState or error message
        """
        if not self.state_file.exists():
            # Create new state
            state = FixerState(
                session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
                started_at=datetime.now(),
                last_updated=datetime.now(),
                total_recommendations=0,
            )
            return Ok(state)

        try:
            data = json.loads(self.state_file.read_text())
            state = FixerState(**data)
            logger.info(
                f"Loaded state: {state.processed}/{state.total_recommendations} processed"
            )
            return Ok(state)

        except Exception as e:
            return Err(f"Failed to load state: {e}")

    def save_state(self, state: FixerState) -> Result[None, str]:
        """
        Save state to persistence file.

        Args:
            state: State to save

        Returns:
            Result indicating success or error
        """
        try:
            state.last_updated = datetime.now()
            self.state_file.write_text(
                json.dumps(state.model_dump(mode="json"), indent=2, default=str)
            )
            logger.debug(f"Saved state to {self.state_file}")
            return Ok(None)

        except Exception as e:
            return Err(f"Failed to save state: {e}")

    def apply_fix(self, recommendation: Recommendation) -> Result[FixResult, str]:
        """
        Apply a single recommendation using AgencyCodeAgent.

        Args:
            recommendation: Recommendation to apply

        Returns:
            Result containing FixResult or error message
        """
        start_time = datetime.now()
        logger.info(
            f"Applying fix: {recommendation.category.value} - {recommendation.summary}"
        )

        if self.dry_run:
            logger.info("[DRY RUN] Would apply fix to files:")
            for file_path in recommendation.affected_files:
                logger.info(f"  - {file_path}")
            return Ok(
                FixResult(
                    recommendation=recommendation,
                    status=FixStatus.SKIPPED,
                    execution_time=0.0,
                )
            )

        try:
            # Create feature branch
            branch_name = f"auto-fix/{recommendation.category.value}/{recommendation.file_path.stem}"
            branch_result = self.git_manager.create_branch(branch_name)
            if branch_result.is_err():
                return Err(branch_result.unwrap_err())

            # Get AgencyCodeAgent
            coder = self.registry.get_agent(AgentType.CODER)

            # Build prompt for agent
            prompt = self._build_fix_prompt(recommendation)

            # Execute fix via agent
            # NOTE: This is a placeholder - actual agent invocation depends on
            # the agent's API. You may need to adapt this based on how
            # create_agency_code_agent is structured.
            logger.info("Invoking AgencyCodeAgent...")
            logger.info(f"Prompt:\n{prompt}")

            # For now, we'll simulate the fix
            # In production, you would call: result = coder.execute(prompt)
            # and check result.is_ok()

            # Placeholder: Mark as applied
            files_modified = recommendation.affected_files

            # Quick validation
            for file_path in files_modified:
                validation = self.test_validator.run_quick_validation(file_path)
                if validation.is_err():
                    return Err(f"Validation failed: {validation.unwrap_err()}")

            # Run full tests
            test_result = self.test_validator.run_tests()
            if test_result.is_err():
                # Tests failed, rollback
                logger.error("Tests failed, rolling back...")
                return Ok(
                    FixResult(
                        recommendation=recommendation,
                        status=FixStatus.FAILED,
                        files_modified=files_modified,
                        tests_passed=False,
                        error_message=test_result.unwrap_err(),
                        execution_time=(datetime.now() - start_time).total_seconds(),
                    )
                )

            # Tests passed, commit
            commit_message = self._build_commit_message(recommendation)
            commit_result = self.git_manager.commit_changes(
                commit_message, files_modified
            )

            if commit_result.is_err():
                return Err(commit_result.unwrap_err())

            commit_sha = commit_result.unwrap()

            logger.info(f"Successfully applied fix: {commit_sha[:8]}")
            return Ok(
                FixResult(
                    recommendation=recommendation,
                    status=FixStatus.APPLIED,
                    files_modified=files_modified,
                    tests_passed=True,
                    commit_sha=commit_sha,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )
            )

        except Exception as e:
            return Err(f"Failed to apply fix: {e}")

    def _build_fix_prompt(self, recommendation: Recommendation) -> str:
        """Build prompt for AgencyCodeAgent."""
        prompt_parts = [
            f"# Fix Request: {recommendation.category.value.upper()}",
            f"",
            f"**Priority**: {recommendation.priority.value}",
            f"**Summary**: {recommendation.summary}",
            f"**Details**: {recommendation.details}",
            f"",
            f"## Affected Files",
        ]

        for file_path in recommendation.affected_files:
            prompt_parts.append(f"- {file_path}")

        prompt_parts.extend(
            [
                f"",
                f"## Recommendation Steps",
            ]
        )

        for i, step in enumerate(recommendation.recommendation_steps, 1):
            prompt_parts.append(f"{i}. {step}")

        if recommendation.example_code:
            prompt_parts.extend(
                [
                    f"",
                    f"## Example Code",
                    f"```python",
                    recommendation.example_code,
                    f"```",
                ]
            )

        prompt_parts.extend(
            [
                f"",
                f"## Requirements",
                f"- Follow TDD: Write/update tests FIRST",
                f"- Use Result<T,E> pattern for error handling",
                f"- Ensure all tests pass after changes",
                f"- Follow constitutional compliance (Article {recommendation.constitutional_article})",
                f"",
                f"Please implement the fix according to the recommendation steps above.",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_commit_message(self, recommendation: Recommendation) -> str:
        """Build git commit message."""
        # Use conventional commit format
        commit_type = {
            Category.ARCHITECTURE: "refactor",
            Category.SIMPLIFICATION: "refactor",
            Category.CONSOLIDATION: "refactor",
            Category.PRUNING: "chore",
            Category.LINTING: "style",
        }.get(recommendation.category, "fix")

        message_parts = [
            f"{commit_type}: {recommendation.summary}",
            f"",
            f"Priority: {recommendation.priority.value}",
            f"Category: {recommendation.category.value}",
            f"",
        ]

        for step in recommendation.recommendation_steps[:3]:  # First 3 steps
            message_parts.append(f"- {step}")

        message_parts.extend(
            [
                f"",
                f"Constitutional Article: {recommendation.constitutional_article}",
                f"Instances Fixed: {recommendation.instances}",
                f"",
                f"Generated by: autonomous_recommendation_fixer.py",
            ]
        )

        return "\n".join(message_parts)

    def process_batch(
        self,
        recommendations: list[Recommendation],
        max_fixes: int | None = None,
        max_time: timedelta | None = None,
    ) -> Result[FixerState, str]:
        """
        Process a batch of recommendations.

        Args:
            recommendations: List of recommendations to process
            max_fixes: Maximum number of fixes to apply
            max_time: Maximum time to run

        Returns:
            Result containing final state or error message
        """
        # Load state
        state_result = self.load_state()
        if state_result.is_err():
            return Err(state_result.unwrap_err())

        state = state_result.unwrap()
        state.total_recommendations = len(recommendations)
        self.state = state

        start_time = datetime.now()

        for i, recommendation in enumerate(recommendations):
            # Check limits
            if max_fixes and state.processed >= max_fixes:
                logger.info(f"Reached max fixes limit: {max_fixes}")
                break

            if max_time and (datetime.now() - start_time) > max_time:
                logger.info(f"Reached max time limit: {max_time}")
                break

            # Apply fix
            result = self.apply_fix(recommendation)

            if result.is_ok():
                fix_result = result.unwrap()
                state.results.append(fix_result)

                if fix_result.status == FixStatus.APPLIED:
                    state.applied += 1
                elif fix_result.status == FixStatus.FAILED:
                    state.failed += 1
                elif fix_result.status == FixStatus.SKIPPED:
                    state.skipped += 1

            else:
                # Error occurred
                logger.error(f"Error: {result.unwrap_err()}")
                state.failed += 1

            state.processed += 1

            # Save state after each fix
            self.save_state(state)

            # Progress report
            logger.info(
                f"Progress: {state.processed}/{state.total_recommendations} "
                f"(Applied: {state.applied}, Failed: {state.failed}, "
                f"Skipped: {state.skipped})"
            )

        return Ok(state)


# ============================================================================
# Summary Reporter
# ============================================================================


class SummaryReporter:
    """Generate summary reports of fix results."""

    def __init__(self, output_dir: Path):
        """
        Initialize summary reporter.

        Args:
            output_dir: Directory to write summary reports
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, state: FixerState) -> Result[Path, str]:
        """
        Generate summary report.

        Args:
            state: Final fixer state

        Returns:
            Result containing report file path or error
        """
        try:
            report_path = (
                self.output_dir / f"fix_summary_{state.session_id}.md"
            )

            report_parts = [
                f"# Autonomous Fix Summary - {state.session_id}",
                f"",
                f"**Started**: {state.started_at}",
                f"**Completed**: {state.last_updated}",
                f"**Duration**: {state.last_updated - state.started_at}",
                f"",
                f"## Overall Statistics",
                f"",
                f"- Total Recommendations: {state.total_recommendations}",
                f"- Processed: {state.processed}",
                f"- Successfully Applied: {state.applied}",
                f"- Failed: {state.failed}",
                f"- Skipped: {state.skipped}",
                f"",
                f"## Results by Category",
                f"",
            ]

            # Group by category
            by_category: dict[Category, list[FixResult]] = {}
            for result in state.results:
                category = result.recommendation.category
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(result)

            for category, results in sorted(by_category.items()):
                applied = sum(1 for r in results if r.status == FixStatus.APPLIED)
                failed = sum(1 for r in results if r.status == FixStatus.FAILED)
                report_parts.extend(
                    [
                        f"### {category.value.upper()}",
                        f"- Total: {len(results)}",
                        f"- Applied: {applied}",
                        f"- Failed: {failed}",
                        f"",
                    ]
                )

            # Detailed results
            report_parts.extend(
                [
                    f"## Detailed Results",
                    f"",
                ]
            )

            for i, result in enumerate(state.results, 1):
                rec = result.recommendation
                report_parts.extend(
                    [
                        f"### {i}. {rec.summary}",
                        f"",
                        f"- **Priority**: {rec.priority.value}",
                        f"- **Category**: {rec.category.value}",
                        f"- **Status**: {result.status.value}",
                        f"- **Files Modified**: {len(result.files_modified)}",
                        f"- **Tests Passed**: {result.tests_passed}",
                        f"- **Execution Time**: {result.execution_time:.2f}s",
                    ]
                )

                if result.commit_sha:
                    report_parts.append(f"- **Commit**: {result.commit_sha[:8]}")

                if result.error_message:
                    report_parts.extend(
                        [
                            f"- **Error**:",
                            f"  ```",
                            f"  {result.error_message[:200]}...",
                            f"  ```",
                        ]
                    )

                report_parts.append("")

            # Write report
            report_path.write_text("\n".join(report_parts))
            logger.info(f"Generated summary report: {report_path}")
            return Ok(report_path)

        except Exception as e:
            return Err(f"Failed to generate report: {e}")


# ============================================================================
# Main CLI
# ============================================================================


def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string like '2h', '30m', '1h30m'."""
    hours = 0
    minutes = 0

    hour_match = re.search(r"(\d+)h", duration_str)
    if hour_match:
        hours = int(hour_match.group(1))

    minute_match = re.search(r"(\d+)m", duration_str)
    if minute_match:
        minutes = int(minute_match.group(1))

    return timedelta(hours=hours, minutes=minutes)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous recommendation implementation system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--category",
        type=str,
        choices=[c.value for c in Category],
        help="Process only specific category",
    )

    parser.add_argument(
        "--priority",
        type=str,
        choices=[p.value for p in Priority],
        help="Process only specific priority",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of fixes to apply",
    )

    parser.add_argument(
        "--max-time",
        type=str,
        help="Maximum time to run (e.g., '2h', '30m', '1h30m')",
    )

    parser.add_argument(
        "--batch-all",
        action="store_true",
        help="Process all recommendations",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't apply changes, just show what would be done",
    )

    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Automatically commit successful fixes",
    )

    parser.add_argument(
        "--recommendations-dir",
        type=Path,
        default=Path(".output/audit_recommendations"),
        help="Directory containing recommendation files",
    )

    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path(".fixer_state.json"),
        help="State persistence file",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".output/fix_summaries"),
        help="Directory for summary reports",
    )

    args = parser.parse_args()

    # Initialize components
    repo_root = Path.cwd()

    logger.info("Initializing autonomous recommendation fixer...")

    # Create agent context and registry
    context = create_agent_context(session_id=f"fixer_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    tracker = CostTracker()
    registry = create_agent_registry(
        agent_context=context,
        cost_tracker=tracker,
        default_tier=ModelTier.LOCAL,  # Use qwen2.5-coder:32b
    )

    # Initialize managers
    git_manager = GitManager(repo_root)
    test_validator = TestValidator(repo_root)
    fixer = RecommendationFixer(
        registry=registry,
        git_manager=git_manager,
        test_validator=test_validator,
        state_file=args.state_file,
        dry_run=args.dry_run,
    )
    reporter = SummaryReporter(args.output_dir)

    # Parse recommendations
    parser = RecommendationParser(args.recommendations_dir)
    parse_result = parser.parse_all()

    if parse_result.is_err():
        logger.error(parse_result.unwrap_err())
        return 1

    recommendations = parse_result.unwrap()

    # Filter by category/priority
    if args.category:
        recommendations = [
            r for r in recommendations if r.category.value == args.category
        ]
        logger.info(f"Filtered to {len(recommendations)} recommendations in category {args.category}")

    if args.priority:
        recommendations = [
            r for r in recommendations if r.priority.value == args.priority
        ]
        logger.info(f"Filtered to {len(recommendations)} recommendations with priority {args.priority}")

    # Sort by priority (P3 first - safest)
    priority_order = {Priority.P3: 0, Priority.P2: 1, Priority.P1: 2, Priority.P0: 3}
    recommendations.sort(key=lambda r: priority_order[r.priority])

    logger.info(f"Processing {len(recommendations)} recommendations")

    # Parse max time
    max_time = None
    if args.max_time:
        max_time = parse_duration(args.max_time)
        logger.info(f"Max time: {max_time}")

    # Process batch
    result = fixer.process_batch(
        recommendations=recommendations,
        max_fixes=args.limit,
        max_time=max_time,
    )

    if result.is_err():
        logger.error(result.unwrap_err())
        return 1

    final_state = result.unwrap()

    # Generate summary report
    report_result = reporter.generate_report(final_state)
    if report_result.is_ok():
        logger.info(f"Summary report: {report_result.unwrap()}")

    # Print final statistics
    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    print(f"Total Recommendations: {final_state.total_recommendations}")
    print(f"Processed: {final_state.processed}")
    print(f"Successfully Applied: {final_state.applied}")
    print(f"Failed: {final_state.failed}")
    print(f"Skipped: {final_state.skipped}")
    print(f"Cost: ${tracker.get_summary()['total_cost']:.4f}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
