"""
E2E Test Fixtures - Constitutional Compliance

Provides realistic test environments for end-to-end testing.

CONSTITUTIONAL MANDATE:
- Article I: Complete context (fixtures fully initialize realistic environments)
- Article IV: VectorStore integration (fixtures provide real VectorStore instances)
- ADR-037: E2E testing framework with realistic fixtures

Fixtures:
- full_agent_context: Complete AgentContext with VectorStore, memory, telemetry
- tmp_git_repo: Realistic git repository with AgencyOS structure
- mock_openai_api: Deterministic OpenAI API responses
- e2e_test_env: Environment variable configuration for E2E testing
- sample_spec_file: Realistic specification file for testing
"""

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


# =============================================================================
# AGENT CONTEXT FIXTURE
# =============================================================================


@pytest.fixture
def full_agent_context() -> Generator:
    """
    Provide complete AgentContext with VectorStore, memory, telemetry.

    Includes:
    - Unique session ID (isolated per test)
    - VectorStore with temp storage (auto-cleanup)
    - Memory API enabled (store/search)
    - Telemetry disabled (avoid log pollution)

    Constitutional: Article IV (VectorStore integration mandatory)

    Usage:
        def test_e2e(full_agent_context):
            result = agent.execute(context=full_agent_context)
            assert full_agent_context.memory_store is not None
    """
    from shared.agent_context import create_agent_context

    # Create temp directory for VectorStore
    temp_dir = Path(tempfile.mkdtemp(prefix="e2e_test_"))
    vectorstore_dir = temp_dir / ".agency" / "vectorstore"
    vectorstore_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique session ID
    session_id = f"e2e_test_{uuid.uuid4()}"

    # Initialize AgentContext with VectorStore
    # Note: create_agent_context uses default EnhancedMemoryStore (Article IV compliance)
    context = create_agent_context(
        session_id=session_id,
    )

    yield context

    # Cleanup: Close VectorStore connections
    if hasattr(context, "memory_store") and context.memory_store:
        try:
            # Close VectorStore if it has a close method
            if hasattr(context.memory_store, "close"):
                context.memory_store.close()
        except Exception:
            pass  # Ignore cleanup errors

    # Remove temp files
    shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# GIT REPOSITORY FIXTURE
# =============================================================================


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Provide temporary git repository with realistic AgencyOS structure.

    Includes:
    - Initialized git repo (git init)
    - Directory structure (specs/, plans/, tests/, tools/, shared/)
    - .gitignore, README.md, pyproject.toml
    - Initial commit (clean working directory)

    Usage:
        def test_e2e(tmp_git_repo):
            result = orchestrator.execute(repo_path=tmp_git_repo)
            assert (tmp_git_repo / "specs" / "spec-001.md").exists()
    """
    repo_path = tmp_path / "agency_test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "E2E Test User"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "e2e@test.agency"],
        cwd=repo_path,
        check=True,
    )

    # Create realistic directory structure
    (repo_path / "specs").mkdir()
    (repo_path / "plans").mkdir()
    (repo_path / "tests").mkdir()
    (repo_path / "tools").mkdir()
    (repo_path / "shared").mkdir()

    # Create initial files
    (repo_path / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n.pytest_cache/\n.agency/\n*.log\n"
    )

    (repo_path / "README.md").write_text("# E2E Test Repository\n\nGenerated for testing.\n")

    (repo_path / "pyproject.toml").write_text(
        """[project]
name = "e2e-test-repo"
version = "0.1.0"
description = "E2E test repository"

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
    )

    # Initial commit
    subprocess.run(
        ["git", "add", "."],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    yield repo_path

    # Cleanup handled by tmp_path fixture


# =============================================================================
# MOCK OPENAI API FIXTURE
# =============================================================================


@pytest.fixture
def mock_openai_api() -> Generator:
    """
    Mock OpenAI API for deterministic E2E tests.

    Provides:
    - Deterministic responses (no real API calls)
    - Consistent embeddings
    - Predefined chat completions

    Usage:
        def test_e2e(mock_openai_api):
            # OpenAI calls will return mocked responses
            response = mock_openai_api.create_completion(...)
            assert response is not None
    """
    # Create mock API object
    mock_api = MagicMock()

    # Mock create_completion method
    def mock_create_completion(model: str, prompt: str, max_tokens: int = 50, **kwargs):
        """Return deterministic completion response."""
        return {
            "id": "mock-completion-id",
            "object": "text_completion",
            "created": 1234567890,
            "model": model,
            "choices": [
                {
                    "text": f"Mocked response for: {prompt[:50]}...",
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
        }

    mock_api.create_completion = mock_create_completion

    # Mock embeddings
    def mock_create_embedding(text: str, model: str = "text-embedding-ada-002", **kwargs):
        """Return deterministic embedding."""
        # Generate consistent embedding based on text hash
        import hashlib

        text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16)
        # Create 1536-dimensional embedding (OpenAI standard)
        embedding = [(text_hash % 1000) / 1000.0] * 1536

        return {
            "data": [{"embedding": embedding, "index": 0}],
            "model": model,
            "usage": {"prompt_tokens": len(text.split()), "total_tokens": len(text.split())},
        }

    mock_api.create_embedding = mock_create_embedding

    yield mock_api


# =============================================================================
# ENVIRONMENT FIXTURE
# =============================================================================


@pytest.fixture
def e2e_test_env(monkeypatch) -> Generator:
    """
    Configure environment variables for E2E testing.

    Sets:
    - E2E_TEST_MODE=true
    - USE_ENHANCED_MEMORY=true (Article IV requirement)
    - Safe API keys (no real credentials)
    - Test-specific timeouts

    Usage:
        def test_e2e(e2e_test_env):
            assert os.getenv("E2E_TEST_MODE") == "true"
    """
    # Set E2E test mode
    monkeypatch.setenv("E2E_TEST_MODE", "true")

    # Enable VectorStore (Article IV constitutional requirement)
    monkeypatch.setenv("USE_ENHANCED_MEMORY", "true")

    # Use safe test API keys
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-e2e-safe")

    # Set test timeouts
    monkeypatch.setenv("PYTEST_TIMEOUT", "120")

    # Disable ML A/B testing for deterministic behavior
    monkeypatch.setenv("ML_AB_TEST_ENABLED", "false")

    # Disable real telemetry
    monkeypatch.setenv("ENABLE_TELEMETRY", "false")

    yield

    # Cleanup handled by monkeypatch fixture


# =============================================================================
# SAMPLE DATA FIXTURE
# =============================================================================


@pytest.fixture
def sample_spec_file(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Provide realistic spec file for testing agent workflows.

    Includes:
    - Complete spec-kit format (Goals, Non-Goals, Personas, Acceptance Criteria)
    - Constitutional checklist
    - Realistic acceptance criteria (5+ items)

    Usage:
        def test_e2e(sample_spec_file):
            result = planner_agent.create_plan(spec_file=sample_spec_file)
            assert result.is_ok()
    """
    spec_content = """# Specification: E2E Test Feature

**ID**: SPEC-E2E-TEST-001
**Status**: Draft
**Created**: 2025-10-25
**Owner**: E2E Test Suite

## Goals

### What We're Building

**A simple feature for E2E testing validation.**

- **Goal 1**: Implement email validation function
- **Goal 2**: Add type hints to function signature
- **Goal 3**: Provide clear error messages for invalid emails

### Success Metrics

- **Coverage**: >95% test coverage
- **Performance**: Validation completes in <1ms
- **Quality**: Zero mypy errors

## Non-Goals

**Explicitly out of scope for this specification**

- **Non-goal 1**: OAuth integration
  - *Rationale*: Out of scope for simple validation

## Personas

### Persona 1: API Client (Primary User)

- **Context**: Makes API calls requiring email validation
- **Need**: Fast, accurate email validation
- **Current Pain Point**: No validation on email inputs
- **Desired Outcome**: Invalid emails rejected with clear errors

## Acceptance Criteria

### Functional Criteria (MUST HAVE)

- [ ] **FC-01**: Email Validation Function
  - Given: An email string
  - When: validate_email(email) is called
  - Then: Returns True for valid emails, False for invalid
  - Validation: Handles common email formats

- [ ] **FC-02**: Type Hints
  - Given: Function signature
  - When: mypy runs
  - Then: Zero type errors
  - Validation: Full type coverage

- [ ] **FC-03**: Error Messages
  - Given: Invalid email
  - When: Validation fails
  - Then: Clear error message returned
  - Validation: Error describes why email is invalid

### Non-Functional Criteria (MUST HAVE)

- [ ] **NF-01**: Performance: <1ms validation time
- [ ] **NF-02**: Test Coverage: >95%

### Quality Criteria (Constitutional Compliance - MUST HAVE)

- [ ] **QC-01**: Article I: Complete context before implementation
- [ ] **QC-02**: Article II: 100% test pass rate
- [ ] **QC-03**: Article IV: VectorStore patterns applied
- [ ] **QC-04**: Article VI: TDD (tests written first)

## Constitutional Compliance

- [ ] Article I: Complete Context Before Action
- [ ] Article II: 100% Verification and Stability
- [ ] Article IV: Continuous Learning and Improvement
- [ ] Article V: Spec-Driven Development
- [ ] Article VI: Test-Driven Development (TDD)

---

**Approval Date**: 2025-10-25
**Approver**: E2E Test Suite
"""

    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)

    spec_file = spec_dir / "spec-e2e-test-001.md"
    spec_file.write_text(spec_content)

    yield spec_file

    # Cleanup handled by tmp_path fixture


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Register E2E markers."""
    config.addinivalue_line("markers", "e2e: End-to-end tests (full workflows, slower)")
    config.addinivalue_line(
        "markers",
        "mission_e2e: Mission-level E2E tests (complete orchestrator workflows)",
    )
    config.addinivalue_line(
        "markers",
        "agent_e2e: Agent-level E2E tests (single agent lifecycle)",
    )
    config.addinivalue_line(
        "markers",
        "tool_e2e: Tool-level E2E tests (tool in system context)",
    )
    config.addinivalue_line("markers", "slow: Slow tests (>30s execution time)")
