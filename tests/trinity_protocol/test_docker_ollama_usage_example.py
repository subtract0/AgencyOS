"""
Example usage of docker_ollama fixture for Trinity Protocol integration tests.

This demonstrates how to use the docker_ollama session fixture for integration
tests that require a running Ollama service.

Constitutional Compliance:
- Article I: Complete context (fixture waits for health check)
- Article II: 100% verification (tests only run if service is healthy)
"""

import os

import pytest


@pytest.mark.skipif(
    os.getenv("SKIP_OLLAMA_TESTS") == "1",
    reason="Skipping Docker Ollama integration tests",
)
class TestOllamaIntegrationExample:
    """Example integration tests using docker_ollama fixture."""

    def test_example_ollama_integration(self, docker_ollama):
        """
        Example test demonstrating docker_ollama fixture usage.

        The fixture:
        1. Starts Docker Compose with Ollama service
        2. Waits for health check (up to 120s with exponential backoff)
        3. Yields endpoint URL to this test
        4. Cleans up automatically after test session

        Args:
            docker_ollama: Session-scoped fixture that returns Ollama endpoint URL
        """
        # Arrange
        endpoint = docker_ollama
        assert endpoint == "http://localhost:11434"

        # Act - Your integration test logic here
        # Example: Test model inference, health checks, etc.

        # Assert
        # Validate your integration behavior
        pass

    def test_multiple_tests_share_same_docker_instance(self, docker_ollama):
        """
        Multiple tests share the same Docker instance (session scope).

        The docker_ollama fixture is session-scoped, so Docker Compose is started
        once at the beginning of the test session and torn down at the end.

        This is efficient for integration tests that need Ollama.
        """
        # Arrange
        endpoint = docker_ollama

        # Act & Assert
        # All tests in this session use the same Docker instance
        assert endpoint is not None
        pass


# Example: Integration test with ARCHITECT agent
@pytest.mark.skipif(
    os.getenv("SKIP_OLLAMA_TESTS") == "1", reason="Skipping Ollama integration tests"
)
class TestArchitectWithOllama:
    """Example: ARCHITECT agent integration test with real Ollama."""

    def test_architect_queries_ollama_for_code_analysis(
        self, docker_ollama, architect_agent
    ):
        """
        ARCHITECT agent uses Ollama for code analysis (integration test).

        This test validates that ARCHITECT can connect to Ollama for:
        - Code pattern analysis
        - ADR recommendations
        - Task decomposition

        Args:
            docker_ollama: Ollama endpoint URL (session fixture)
            architect_agent: ARCHITECT agent instance (test fixture)
        """
        # Arrange
        endpoint = docker_ollama
        agent = architect_agent

        # Act - ARCHITECT queries Ollama for code analysis
        # (This is an example - actual implementation depends on ARCHITECT API)

        # Assert
        # Validate ARCHITECT's analysis results
        pass


# Example: Performance test with cleanup validation
@pytest.mark.skipif(
    os.getenv("SKIP_OLLAMA_TESTS") == "1", reason="Skipping Ollama integration tests"
)
class TestOllamaCleanup:
    """Validate docker_ollama fixture cleanup behavior."""

    def test_cleanup_happens_after_all_tests(self, docker_ollama):
        """
        Fixture cleanup runs after ALL tests in session complete.

        Cleanup behavior:
        - Runs docker-compose down after session ends
        - Handles test failures gracefully (finalizer pattern)
        - Logs warnings on cleanup errors (doesn't fail tests)

        This test validates that cleanup doesn't interfere with test execution.
        """
        # Arrange & Act
        endpoint = docker_ollama

        # Assert - Service is available during test
        assert endpoint is not None

        # Cleanup will happen automatically after session via request.addfinalizer()
