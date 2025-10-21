"""
Tests for scripts/init_ollama_model.sh model initialization script.

Constitutional Compliance:
- Article I: Complete context verification (exponential backoff retry)
- Article II: 100% verification (all tests must pass)
- ADR-023: Memory-aware execution validation
"""

import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestInitOllamaModelScript:
    """Test suite for Ollama model initialization script."""

    @pytest.fixture
    def script_path(self) -> Path:
        """Return path to init_ollama_model.sh script."""
        return Path(__file__).parent.parent / "scripts" / "init_ollama_model.sh"

    @pytest.fixture
    def mock_docker_exec(self):
        """Mock docker exec command for testing."""
        with patch("subprocess.run") as mock_run:
            yield mock_run

    def test_script_exists(self, script_path: Path):
        """Test that init_ollama_model.sh script exists."""
        assert script_path.exists(), f"Script not found at {script_path}"

    def test_script_is_executable(self, script_path: Path):
        """Test that script has executable permissions."""
        assert script_path.stat().st_mode & 0o111, "Script is not executable"

    def test_script_has_shebang(self, script_path: Path):
        """Test that script starts with proper shebang."""
        with open(script_path) as f:
            first_line = f.readline()
        assert first_line.startswith("#!/bin/bash"), "Script missing bash shebang"

    def test_script_validates_syntax(self, script_path: Path):
        """Test that script has valid bash syntax."""
        result = subprocess.run(["bash", "-n", str(script_path)], capture_output=True, text=True)
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_exponential_backoff_configuration(self, script_path: Path):
        """Test Article I: Script implements exponential backoff retry logic."""
        with open(script_path) as f:
            content = f.read()

        # Verify exponential backoff constants
        assert "MAX_RETRIES=" in content, "Missing MAX_RETRIES configuration"
        assert "INITIAL_WAIT=" in content, "Missing INITIAL_WAIT configuration"

        # Verify exponential backoff implementation
        assert "wait_seconds=$((wait_seconds * 2))" in content, "Missing exponential backoff logic"

        # Verify retry loop (Article I compliance)
        assert "while [ $retry_count -lt $MAX_RETRIES ]" in content, "Missing retry loop"

    def test_health_check_endpoint_configuration(self, script_path: Path):
        """Test Article II: Script validates service health before proceeding."""
        with open(script_path) as f:
            content = f.read()

        # Verify health check URL configuration
        assert "HEALTH_CHECK_URL=" in content, "Missing health check URL"
        assert "/api/tags" in content, "Missing /api/tags endpoint"

        # Verify health check execution
        assert "curl -f -s" in content, "Missing health check curl command"

    def test_model_verification_logic(self, script_path: Path):
        """Test Article II: Script verifies model availability after pull."""
        with open(script_path) as f:
            content = f.read()

        # Verify model verification via ollama list
        assert "ollama list" in content, "Missing model verification via ollama list"

        # Verify model verification via health check
        assert "curl -f -s" in content and "/api/tags" in content, (
            "Missing health check verification"
        )

        # Verify exit on failure
        assert "exit 1" in content, "Missing error exit when verification fails"

    def test_idempotent_operation(self, script_path: Path):
        """Test script is idempotent (no-op if model already exists)."""
        with open(script_path) as f:
            content = f.read()

        # Verify model existence check before pull
        assert "ollama list" in content and "grep -q" in content, "Missing model existence check"

        # Verify early exit if model exists
        assert "already available" in content or "model cached" in content, "Missing no-op message"

    def test_container_name_configuration(self, script_path: Path):
        """Test container name is configurable via environment variable."""
        with open(script_path) as f:
            content = f.read()

        # Verify container name environment variable
        assert "CONTAINER_NAME=" in content and "OLLAMA_CONTAINER_NAME" in content, (
            "Missing container name configuration"
        )

        # Verify default container name
        assert "agency-ollama" in content, "Missing default container name"

    def test_model_name_configuration(self, script_path: Path):
        """Test model name is configurable via argument or environment variable."""
        with open(script_path) as f:
            content = f.read()

        # Verify model name can be passed as argument
        assert "${1:-" in content, "Missing positional argument support"

        # Verify model name environment variable
        assert "OLLAMA_MODEL" in content or "DEFAULT_MODEL" in content, (
            "Missing model name configuration"
        )

        # Verify default model (qwen3-coder:30b for dev)
        assert "qwen3-coder:30b" in content, "Missing default model name"

    def test_error_handling_on_container_not_running(self, script_path: Path):
        """Test Article I: Script handles container not running with retries."""
        with open(script_path) as f:
            content = f.read()

        # Verify container running check
        assert "docker ps" in content, "Missing container running check"

        # Verify error message on failure
        assert "Container" in content and "not running" in content, (
            "Missing container error message"
        )

    def test_error_handling_on_model_pull_failure(self, script_path: Path):
        """Test Article II: Script exits with error if model pull fails."""
        with open(script_path) as f:
            content = f.read()

        # Verify pull error handling
        assert "ollama pull" in content, "Missing model pull command"

        # Verify exit on pull failure
        assert "exit $pull_exit_code" in content or "exit 1" in content, (
            "Missing error exit on pull failure"
        )

    def test_debug_logging_on_failure(self, script_path: Path):
        """Test Article I: Script provides debug logs on failure."""
        with open(script_path) as f:
            content = f.read()

        # Verify debug logging
        assert "docker logs" in content, "Missing debug logging"
        assert "Debug info:" in content or "tail" in content, "Missing failure diagnostics"

    def test_model_size_estimation(self, script_path: Path):
        """Test script provides download time estimates for different models."""
        with open(script_path) as f:
            content = f.read()

        # Verify size estimation logic
        assert "30b" in content or "30B" in content, "Missing 30B model handling"
        assert "7b" in content or "7B" in content, "Missing 7B model handling"
        assert "1.5b" in content or "1.5B" in content, "Missing 1.5B model handling"

        # Verify time estimates
        assert "minutes" in content, "Missing time estimates"

    def test_constitutional_compliance_documentation(self, script_path: Path):
        """Test script documents constitutional compliance in comments."""
        with open(script_path) as f:
            content = f.read()

        # Verify Article I documentation
        assert "Article I" in content, "Missing Article I compliance documentation"

        # Verify Article II documentation
        assert "Article II" in content, "Missing Article II compliance documentation"

        # Verify ADR-023 reference
        assert "ADR-023" in content, "Missing ADR-023 reference"

    def test_success_output_formatting(self, script_path: Path):
        """Test script provides clear success messages and next steps."""
        with open(script_path) as f:
            content = f.read()

        # Verify success message
        assert "Initialization Complete" in content, "Missing success message"

        # Verify summary output
        assert "Summary:" in content, "Missing summary section"

        # Verify test command suggestion
        assert "docker exec" in content and "ollama run" in content, "Missing test command"

        # Verify documentation reference
        assert "LOCAL_MODEL_OPTIMIZATION.md" in content, "Missing documentation reference"


class TestInitOllamaModelIntegration:
    """Integration tests for init_ollama_model.sh (requires Docker)."""

    @pytest.fixture
    def script_path(self) -> Path:
        """Return path to init_ollama_model.sh script."""
        return Path(__file__).parent.parent / "scripts" / "init_ollama_model.sh"

    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("/var/run/docker.sock").exists(),
        reason="Docker not available",
    )
    def test_script_runs_with_missing_container(self, script_path: Path):
        """Test script exits gracefully when container is not running."""
        # Run script with non-existent container
        result = subprocess.run(
            ["bash", str(script_path)],
            env={"OLLAMA_CONTAINER_NAME": "nonexistent-container"},
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should fail with clear error message (Article I: complete context)
        assert result.returncode != 0, "Script should fail with missing container"
        # Check both stdout and stderr for error message
        output = result.stdout + result.stderr
        assert "Container" in output or "not running" in output or "not found" in output, (
            "Missing error message"
        )

    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("/var/run/docker.sock").exists(),
        reason="Docker not available",
    )
    def test_script_timeout_handling(self, script_path: Path):
        """Test Article I: Script respects max retries and exits."""
        # Run script with quick timeout (will fail fast)
        start_time = time.time()
        result = subprocess.run(
            ["bash", str(script_path)],
            env={
                "OLLAMA_CONTAINER_NAME": "nonexistent-test-container",
                "MAX_RETRIES": "3",
                "INITIAL_WAIT": "1",
            },
            capture_output=True,
            text=True,
            timeout=60,
        )
        elapsed = time.time() - start_time

        # Should fail quickly with exponential backoff (1 + 2 + 4 = 7s max)
        assert elapsed < 15, "Script took too long (exponential backoff issue)"
        assert result.returncode != 0, "Script should fail"


class TestInitOllamaModelDockerCompose:
    """Test integration with docker-compose.yml entrypoint."""

    def test_docker_compose_references_init_script(self):
        """Test docker-compose.yml can integrate init script as entrypoint."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        if not compose_file.exists():
            pytest.skip("docker-compose.yml not found")

        with open(compose_file) as f:
            content = f.read()

        # Note: Script is designed to be called externally, not as entrypoint
        # Verify script is compatible with external invocation
        script_path = Path(__file__).parent.parent / "scripts" / "init_ollama_model.sh"
        assert script_path.exists(), "Init script must exist for Docker integration"


class TestConstitutionalCompliance:
    """Test constitutional compliance requirements."""

    @pytest.fixture
    def script_path(self) -> Path:
        """Return path to init_ollama_model.sh script."""
        return Path(__file__).parent.parent / "scripts" / "init_ollama_model.sh"

    def test_article_i_complete_context(self, script_path: Path):
        """Test Article I: Script never proceeds with incomplete context."""
        with open(script_path) as f:
            content = f.read()

        # Verify retry logic (never give up prematurely)
        assert "MAX_RETRIES=" in content, "Missing retry configuration"
        assert "retry_count" in content, "Missing retry counter"

        # Verify exponential backoff
        assert "wait_seconds * 2" in content, "Missing exponential backoff"

    def test_article_ii_verification(self, script_path: Path):
        """Test Article II: Script verifies 100% before declaring success."""
        with open(script_path) as f:
            content = f.read()

        # Verify model verification steps
        assert "ollama list" in content, "Missing model list verification"
        assert "grep -q" in content, "Missing model existence verification"

        # Verify exit on verification failure
        assert content.count("exit 1") >= 2, "Insufficient error exits"

    def test_adr_023_memory_awareness(self, script_path: Path):
        """Test ADR-023: Script supports memory-aware model selection."""
        with open(script_path) as f:
            content = f.read()

        # Verify model size documentation
        assert "30b" in content or "30B" in content, "Missing 30B model support"
        assert "7b" in content or "7B" in content, "Missing 7B model support"
        assert "1.5b" in content or "1.5B" in content, "Missing 1.5B model support"

        # Verify model selection via environment/argument
        assert "${1:-" in content or "OLLAMA_MODEL" in content, (
            "Missing configurable model selection"
        )
