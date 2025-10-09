"""
Pydantic models for constitutional hooks data transfer.

These models define the JSON structure for data passed between the
Agent Orchestration Layer and hook scripts via stdin/stdout.
"""

from typing import Any
from pydantic import BaseModel, Field


class UserPrompt(BaseModel):
    """User prompt submitted to the system."""

    prompt: str = Field(..., description="User's input prompt text")


class ToolCall(BaseModel):
    """Tool call about to be executed."""

    tool_name: str = Field(..., description="Name of the tool being called")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class GitCommitArgs(BaseModel):
    """Arguments for git commit tool."""

    message: str = Field(..., description="Commit message")
    files: list[str] = Field(default_factory=list, description="Files to commit")


class GitPushArgs(BaseModel):
    """Arguments for git push tool."""

    remote: str = Field(default="origin", description="Remote to push to")
    branch: str = Field(..., description="Branch to push")
    force: bool = Field(default=False, description="Force push flag")


class SessionState(BaseModel):
    """Current session state for Definition of Done validation."""

    tasks_completed: list[str] = Field(
        default_factory=list, description="List of completed task IDs"
    )
    tasks_total: list[str] = Field(
        default_factory=list, description="List of all task IDs"
    )
    status: str = Field(..., description="Session status (active, stopping, etc.)")


class TestReport(BaseModel):
    """Test execution results for Article II validation."""

    total_tests: int = Field(..., description="Total number of tests run")
    failed_tests: int = Field(default=0, description="Number of failed tests")
    passed_tests: int = Field(..., description="Number of passed tests")
    skipped_tests: int = Field(default=0, description="Number of skipped tests")
    duration: float = Field(default=0.0, description="Test duration in seconds")
