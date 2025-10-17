"""Shared fixtures for orchestrator tests.

Imports fixtures from foundation_automation tests for reuse.
Provides orchestrator-specific fixtures.

Constitutional Compliance:
- Article I: Complete context (isolated fixtures)
- Article II: 100% verification (fixtures ensure clean state)
"""

# Import foundation automation fixtures for reuse
from tests.foundation_automation.conftest import (
    cleanup_test_artifacts,
    create_backlog_file,
    isolated_git_repo,
    mock_agent_context,
    mock_budget_guard,
    mock_completion_validator,
    mock_github_api,
    mock_slop_guardian,
    mock_trm_validator,
    mock_vectorstore,
    performance_baseline,
    sample_backlog_content,
    sample_intents,
    simple_task_graph,
    complex_task_graph,
)

__all__ = [
    "cleanup_test_artifacts",
    "create_backlog_file",
    "isolated_git_repo",
    "mock_agent_context",
    "mock_budget_guard",
    "mock_completion_validator",
    "mock_github_api",
    "mock_slop_guardian",
    "mock_trm_validator",
    "mock_vectorstore",
    "performance_baseline",
    "sample_backlog_content",
    "sample_intents",
    "simple_task_graph",
    "complex_task_graph",
]
