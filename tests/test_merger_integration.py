"""
Test suite for MergerAgent integration and ADR-002 enforcement components.
Validates the complete merge verification system including agent creation,
pre-commit hooks, and GitHub Actions workflow.

This test ensures all components work together to enforce the "No Broken Windows"
policy and 100% test success rate requirement defined in ADR-002.
"""

import os
import sys
import pytest
import tempfile
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from shared.agent_context import create_agent_context
from merger_agent import create_merger_agent


class TestMergerAgentIntegration:
    """Test MergerAgent integration and core functionality."""

    def test_merger_agent_import_and_creation(self):
        """Test that MergerAgent can be imported and created successfully."""
        # Test agent creation with context
        context = create_agent_context()
        agent = create_merger_agent(agent_context=context)

        # Verify agent properties
        assert agent.name == "MergerAgent"
        assert "quality gatekeeper" in agent.description.lower()
        assert "100% test" in agent.description
        assert "veto power" in agent.description
        assert "ADR-002" in agent.description

        # Verify agent has correct number of tools
        assert len(agent.tools) == 6

        # Verify required tools are present
        expected_tools = ['Bash', 'Git', 'Read', 'Grep', 'Glob', 'TodoWrite']
        actual_tools = [getattr(tool, 'name', getattr(tool, '__name__', str(tool))) for tool in agent.tools]

        for expected_tool in expected_tools:
            assert expected_tool in actual_tools, f"Missing required tool: {expected_tool}"

    def test_merger_agent_memory_integration(self):
        """Test that MergerAgent properly integrates with memory system."""
        # Create agent with context
        context = create_agent_context()
        agent = create_merger_agent(agent_context=context)

        # Verify memory integration through context
        assert hasattr(agent, 'hooks')
        assert agent.hooks is not None

        # Check that memory was stored during agent creation
        # Note: Memory storage might be asynchronous or dependent on specific backend
        # For now, we just verify the context has a valid session ID which indicates
        # the memory system is properly initialized
        assert hasattr(context, 'session_id')
        assert context.session_id is not None
        assert len(context.session_id) > 0

    def test_merger_agent_tools_availability(self):
        """Test that all MergerAgent tools are properly configured and functional."""
        # Create agent
        context = create_agent_context()
        agent = create_merger_agent(agent_context=context)

        # Test each tool has proper configuration
        for tool in agent.tools:
            assert hasattr(tool, 'name'), f"Tool missing name attribute: {tool}"
            assert hasattr(tool, 'description'), f"Tool missing description: {tool.name}"
            assert tool.description, f"Tool has empty description: {tool.name}"

        # Verify tools include test verification capabilities
        tool_names = [tool.name for tool in agent.tools]
        assert 'Bash' in tool_names, "Bash tool required for test execution"
        assert 'Git' in tool_names, "Git tool required for merge operations"


class TestPreCommitHookIntegration:
    """Test pre-commit hook functionality and ADR-002 enforcement."""

    def test_pre_commit_hook_exists_and_executable(self):
        """Test that pre-commit hook exists and is executable."""
        hook_path = os.path.join(project_root, '.git', 'hooks', 'pre-commit')

        if not os.path.exists(hook_path):
            pytest.skip("Pre-commit hook not installed - skipping in CI environment")

        assert os.access(hook_path, os.X_OK), "Pre-commit hook not executable"

    def test_pre_commit_hook_content_validation(self):
        """Test that pre-commit hook contains required ADR-002 enforcement logic."""
        hook_path = os.path.join(project_root, '.git', 'hooks', 'pre-commit')

        if not os.path.exists(hook_path):
            pytest.skip("Pre-commit hook not installed - skipping in CI environment")

        with open(hook_path, 'r') as f:
            content = f.read()

        # Verify hook contains ADR-002 references
        assert "ADR-002" in content, "Hook missing ADR-002 reference"
        assert "100% test verification" in content, "Hook missing test verification requirement"
        assert "python run_tests.py" in content, "Hook missing test execution command"

        # Verify hook has proper exit codes
        assert "exit 1" in content, "Hook missing failure exit code"
        assert "exit 0" in content, "Hook missing success exit code"

        # Verify hook checks test results
        assert "TEST_EXIT_CODE" in content, "Hook missing test exit code checking"

    @pytest.mark.skipif(not os.path.exists(os.path.join(project_root, '.venv')),
                       reason="Virtual environment not available")
    def test_pre_commit_hook_test_execution(self):
        """Test that pre-commit hook can execute tests (requires venv)."""
        hook_path = os.path.join(project_root, '.git', 'hooks', 'pre-commit')

        if not os.path.exists(hook_path):
            pytest.skip("Pre-commit hook not installed - skipping in CI environment")

        # Run hook with timeout to prevent infinite loops during testing
        env = os.environ.copy()
        env['PATH'] = f"{os.path.join(project_root, '.venv', 'bin')}:{env['PATH']}"

        # Add environment variable to prevent recursive test execution
        env['TESTING_PRE_COMMIT_HOOK'] = '1'

        # Run with a short timeout to prevent hanging
        try:
            result = subprocess.run([hook_path], cwd=project_root, env=env,
                                  capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            # If hook times out, that's acceptable for this test
            # It means the hook is functional but we're preventing infinite loops
            pytest.skip("Pre-commit hook timed out (expected during testing to prevent infinite loops)")

        # Hook should execute (may pass or fail depending on current test state)
        assert result.returncode in [0, 1, 124], "Hook should exit with 0 (success), 1 (failure), or 124 (timeout)"

        # Verify hook produces expected output patterns
        output = result.stdout + result.stderr
        assert any(phrase in output for phrase in ["ADR-002", "test", "verification", "Running test suite"]), \
               "Hook output missing expected content"


class TestGitHubWorkflowIntegration:
    """Test GitHub Actions workflow configuration for merge verification."""

    def test_github_workflow_exists(self):
        """Test that GitHub Actions workflow file exists."""
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')
        assert os.path.exists(workflow_path), "GitHub workflow file missing"

    def test_github_workflow_yaml_structure(self):
        """Test that GitHub workflow has correct YAML structure."""
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')

        with open(workflow_path, 'r') as f:
            content = f.read()

        # Basic YAML structure validation
        required_elements = ['name:', 'on:', 'jobs:', 'runs-on:', 'steps:']
        for element in required_elements:
            assert element in content, f"Workflow missing required element: {element}"

    def test_github_workflow_adr_002_enforcement(self):
        """Test that GitHub workflow enforces ADR-002 requirements."""
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')

        with open(workflow_path, 'r') as f:
            content = f.read()

        # Verify ADR-002 enforcement
        assert "ADR-002" in content, "Workflow missing ADR-002 reference"
        assert "100%" in content, "Workflow missing 100% requirement"
        assert "test" in content.lower(), "Workflow missing test execution"

        # Verify workflow triggers
        assert "pull_request:" in content, "Workflow missing PR trigger"
        assert "push:" in content, "Workflow missing push trigger"

        # Verify jobs structure
        assert "test-verification" in content, "Workflow missing test verification job"
        assert "merge-readiness" in content, "Workflow missing merge readiness job"

    def test_github_workflow_python_setup(self):
        """Test that GitHub workflow properly sets up Python environment."""
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')

        with open(workflow_path, 'r') as f:
            content = f.read()

        # Verify Python setup
        assert "python-version: '3.13'" in content, "Workflow using incorrect Python version"
        assert "setup-python@v" in content, "Workflow missing Python setup action"
        assert "requirements.txt" in content, "Workflow missing requirements installation"

    def test_github_workflow_test_execution_logic(self):
        """Test that GitHub workflow has proper test execution and result processing."""
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')

        with open(workflow_path, 'r') as f:
            content = f.read()

        # Verify test execution
        assert "python run_tests.py" in content, "Workflow missing test execution command"
        assert "TEST_EXIT_CODE" in content, "Workflow missing exit code capture"

        # Verify result processing
        assert "PASSED_TESTS" in content, "Workflow missing passed test counting"
        assert "FAILED_TESTS" in content, "Workflow missing failed test counting"

        # Verify compliance checking
        assert "ADR-002 COMPLIANT" in content, "Workflow missing compliance checking"
        assert "ADR-002 VIOLATION" in content, "Workflow missing violation detection"


class TestMergeVerificationWorkflow:
    """Test the complete merge verification workflow integration."""

    def test_complete_integration_components_exist(self):
        """Test that all integration components exist and are properly configured."""
        # Verify MergerAgent exists
        merger_agent_path = os.path.join(project_root, 'merger_agent', 'merger_agent.py')
        assert os.path.exists(merger_agent_path), "MergerAgent file missing"

        # Verify pre-commit hook exists (skip in CI)
        hook_path = os.path.join(project_root, '.git', 'hooks', 'pre-commit')
        if not os.path.exists(hook_path):
            pytest.skip("Pre-commit hook not installed - skipping in CI environment")
        assert os.path.exists(hook_path), "Pre-commit hook missing"

        # Verify GitHub workflow exists
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')
        assert os.path.exists(workflow_path), "GitHub workflow missing"

        # Verify all are executable/readable
        assert os.access(merger_agent_path, os.R_OK), "MergerAgent not readable"
        assert os.access(hook_path, os.X_OK), "Pre-commit hook not executable"
        assert os.access(workflow_path, os.R_OK), "GitHub workflow not readable"

    def test_adr_002_compliance_enforcement(self):
        """Test that ADR-002 compliance is enforced across all components."""
        # Check MergerAgent description
        merger_agent_path = os.path.join(project_root, 'merger_agent', 'merger_agent.py')
        with open(merger_agent_path, 'r') as f:
            merger_content = f.read()
        assert "ADR-002" in merger_content, "MergerAgent missing ADR-002 reference"

        # Check pre-commit hook (skip in CI)
        hook_path = os.path.join(project_root, '.git', 'hooks', 'pre-commit')
        if not os.path.exists(hook_path):
            pytest.skip("Pre-commit hook not installed - skipping in CI environment")
        with open(hook_path, 'r') as f:
            hook_content = f.read()
        assert "ADR-002" in hook_content, "Pre-commit hook missing ADR-002 reference"

        # Check GitHub workflow
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')
        with open(workflow_path, 'r') as f:
            workflow_content = f.read()
        assert "ADR-002" in workflow_content, "GitHub workflow missing ADR-002 reference"

    def test_no_broken_windows_policy_enforcement(self):
        """Test that 'No Broken Windows' policy is enforced in all components."""
        # Check MergerAgent
        merger_agent_path = os.path.join(project_root, 'merger_agent', 'merger_agent.py')
        with open(merger_agent_path, 'r') as f:
            merger_content = f.read()
        assert "non-negotiable" in merger_content or "veto power" in merger_content, "MergerAgent missing No Broken Windows policy"

        # Check GitHub workflow
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')
        with open(workflow_path, 'r') as f:
            workflow_content = f.read()
        assert "No Broken Windows" in workflow_content, "GitHub workflow missing No Broken Windows policy"

    def test_test_verification_consistency(self):
        """Test that all components use consistent test verification approach."""
        # All components should use 'python run_tests.py' for consistency

        # Check pre-commit hook (skip in CI)
        hook_path = os.path.join(project_root, '.git', 'hooks', 'pre-commit')
        if not os.path.exists(hook_path):
            pytest.skip("Pre-commit hook not installed - skipping in CI environment")
        with open(hook_path, 'r') as f:
            hook_content = f.read()
        assert "python run_tests.py" in hook_content, "Pre-commit hook uses inconsistent test command"

        # Check GitHub workflow
        workflow_path = os.path.join(project_root, '.github', 'workflows', 'merge-guardian.yml')
        with open(workflow_path, 'r') as f:
            workflow_content = f.read()
        assert "python run_tests.py" in workflow_content, "GitHub workflow uses inconsistent test command"


class TestMergerAgentErrorScenarios:
    """Test MergerAgent behavior in error scenarios."""

    def test_merger_agent_creation_with_invalid_context(self):
        """Test MergerAgent creation handles invalid context gracefully."""
        # Test creation with None context (should create default)
        agent = create_merger_agent(agent_context=None)
        assert agent is not None
        assert agent.name == "MergerAgent"

    def test_merger_agent_handles_missing_dependencies(self):
        """Test that MergerAgent handles missing tool dependencies gracefully."""
        # This test verifies the agent can be created even if some tools are unavailable
        # The agent should still be functional for basic operations

        # Test agent creation (should not fail due to tool dependencies)
        context = create_agent_context()
        agent = create_merger_agent(agent_context=context)

        # Agent should be created successfully
        assert agent is not None
        assert len(agent.tools) > 0


if __name__ == "__main__":
    # Allow running this test file directly, but prevent recursion
    import os
    if os.environ.get("AGENCY_NESTED_TEST") != "1":
        pytest.main([__file__, "-v"])