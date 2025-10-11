#!/usr/bin/env python3
"""
Store Ollama Docker Setup mission patterns to VectorStore.

This script stores 12 high-confidence patterns extracted from the mission
to enable 140 Ollama integration tests via Docker Compose.

Constitutional Compliance:
- Article IV: Continuous Learning (mandatory VectorStore storage)
- Confidence threshold: ≥0.65 (all patterns meet requirement)
- Evidence threshold: ≥3 occurrences (all patterns validated)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path (must be before imports)
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from shared.agent_context import create_agent_context  # noqa: E402


def store_patterns():
    """Store validated patterns to VectorStore."""
    # Initialize agent context
    context = create_agent_context(session_id="ollama_docker_pattern_extraction")

    # Pattern 1.1: Docker Compose Service Lifecycle Management
    context.store_memory(
        key="pattern_docker_compose_lifecycle_management",
        content={
            "pattern_id": "ollama_docker_pattern_1_1",
            "pattern_name": "Docker Compose Service Lifecycle Management",
            "category": "architecture",
            "confidence": 0.95,
            "evidence_count": 6,
            "description": (
                "Manage external service dependencies (LLMs, databases, message queues) via Docker Compose with: "
                "(1) Declarative service definition (YAML), "
                "(2) Volume persistence for expensive resources, "
                "(3) Health checks with exponential backoff retry, "
                "(4) Memory limits for resource constraints, "
                "(5) Automatic cleanup via pytest finalizers."
            ),
            "implementation_template": """
services:
  external_service:
    image: service/image:latest
    container_name: agency-service
    ports:
      - "PORT:PORT"
    volumes:
      - ~/.service_data:/root/.service_data
    environment:
      - SERVICE_CONFIG_KEY=value
    deploy:
      resources:
        limits:
          memory: 40G  # ADR-023 compliance
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
    restart: unless-stopped
""",
            "applicability": ["LLM services (Ollama, vLLM, TGI)", "Database integration tests", "Message queue tests"],
            "trade_offs": {
                "pro": ["Deterministic", "Portable", "CI/CD-ready", "Volume persistence", "Memory limits"],
                "con": ["Docker dependency", "Initial startup time"]
            },
            "constitutional_alignment": ["article-i", "article-ii", "article-iii"],
            "related_files": [
                "docker-compose.yml",
                "tests/conftest.py",
                "docs/adr/ADR-028-ollama-docker-integration.md"
            ],
            "mission_context": "Enable 140 Ollama integration tests via Docker Compose"
        },
        tags=["docker-compose", "lifecycle-management", "health-checks", "volume-persistence", "adr-023", "article-i", "article-ii", "architecture"]
    )

    # Pattern 1.2: Exponential Backoff Health Check Protocol
    context.store_memory(
        key="pattern_exponential_backoff_health_check",
        content={
            "pattern_id": "ollama_docker_pattern_1_2",
            "pattern_name": "Exponential Backoff Health Check Protocol",
            "category": "architecture",
            "confidence": 0.88,
            "evidence_count": 4,
            "description": (
                "Implement robust health check protocol with exponential backoff for external service readiness: "
                "(1) Initial fast retries (2s, 4s), "
                "(2) Exponential backoff (2x multiplier), "
                "(3) Maximum interval cap (16s), "
                "(4) Total timeout (120s), "
                "(5) Verification beyond HTTP 200 (check resource availability)."
            ),
            "implementation_template": """
def wait_for_service_healthy(endpoint: str, max_wait: int = 120) -> Result[str, str]:
    interval = 2
    elapsed = 0

    while elapsed < max_wait:
        try:
            response = requests.get(f"{endpoint}/health", timeout=5)
            if response.status_code == 200:
                if verify_resource_ready(endpoint):
                    return Ok(endpoint)
        except Exception:
            pass

        time.sleep(interval)
        elapsed += interval
        interval = min(interval * 2, 16)  # 2x backoff, cap at 16s

    return Err(f"Service failed to start after {max_wait}s")
""",
            "applicability": ["Distributed system health checks", "External API dependency verification", "Model loading validation"],
            "trade_offs": {
                "pro": ["Resilient to slow starts", "Reduces load during startup", "Verifies actual resource"],
                "con": ["Longer maximum wait time", "Complexity increase"]
            },
            "constitutional_alignment": ["article-i", "article-ii"],
            "related_files": [
                "tests/conftest.py",
                "docker-compose.yml",
                "docs/adr/ADR-028-ollama-docker-integration.md"
            ],
            "mission_context": "Health check retry logic for Docker Ollama startup"
        },
        tags=["exponential-backoff", "health-checks", "article-i", "retry-logic", "docker-healthcheck", "architecture"]
    )

    # Pattern 1.3: Volume Persistence for Expensive Resources
    context.store_memory(
        key="pattern_volume_persistence_expensive_resources",
        content={
            "pattern_id": "ollama_docker_pattern_1_3",
            "pattern_name": "Volume Persistence for Expensive Resources",
            "category": "architecture",
            "confidence": 0.85,
            "evidence_count": 5,
            "description": (
                "Persist expensive resources (models, datasets, compiled artifacts) across container restarts: "
                "(1) Host volume mount for durable storage, "
                "(2) Container path mapping, "
                "(3) One-time initialization with cached access, "
                "(4) Disk space trade-off (storage cost vs re-initialization time)."
            ),
            "implementation_template": """
# docker-compose.yml
services:
  ml_service:
    volumes:
      - ~/.service_data:/root/.service_data  # Durable storage
    environment:
      - SERVICE_STORAGE_PATH=/root/.service_data
""",
            "applicability": ["LLM model storage", "ML dataset caching", "Compiled artifacts", "Database fixtures"],
            "trade_offs": {
                "pro": ["96% faster subsequent starts (32s vs 15min)", "One-time download cost", "CI/CD caching"],
                "con": ["32GB disk space requirement", "Volume mount complexity"]
            },
            "constitutional_alignment": ["article-iii", "article-iv"],
            "related_files": [
                "docker-compose.yml",
                "docs/adr/ADR-028-ollama-docker-integration.md",
                "specs/spec-023-ollama-docker-integration.md"
            ],
            "mission_context": "Persist 32GB Ollama model across container restarts"
        },
        tags=["volume-persistence", "docker-volumes", "resource-caching", "performance-optimization", "disk-space-tradeoff", "architecture"]
    )

    # Pattern 2.1: Session-Scoped Pytest Fixtures for External Services
    context.store_memory(
        key="pattern_session_scoped_pytest_fixtures",
        content={
            "pattern_id": "ollama_docker_pattern_2_1",
            "pattern_name": "Session-Scoped Pytest Fixtures for External Services",
            "category": "testing",
            "confidence": 0.90,
            "evidence_count": 7,
            "description": (
                "Use session-scoped pytest fixtures to manage expensive external service lifecycle: "
                "(1) Session scope (not function), "
                "(2) Automatic cleanup via request.addfinalizer(), "
                "(3) Skip support via environment variable, "
                "(4) Health gate to prevent tests on unhealthy services."
            ),
            "implementation_template": """
@pytest.fixture(scope="session")
def docker_service(request):
    if os.getenv("SKIP_SERVICE_TESTS") == "1":
        pytest.skip("Service tests disabled")

    subprocess.run(["docker", "compose", "up", "-d", "service"], check=True)

    endpoint = wait_for_service_healthy(timeout=120)
    if endpoint.is_err():
        subprocess.run(["docker", "compose", "down"])
        pytest.skip(f"Service failed to start: {endpoint.unwrap_err()}")

    yield endpoint.unwrap()

    request.addfinalizer(
        lambda: subprocess.run(["docker", "compose", "down"], timeout=30)
    )
""",
            "applicability": ["Database integration tests", "Message queue tests", "External API mocking servers", "LLM service tests"],
            "trade_offs": {
                "pro": ["Shared Docker instance (efficient)", "Guaranteed cleanup", "Graceful skip support"],
                "con": ["Single shared state (tests must be independent)", "Longer setup time (amortized)"]
            },
            "constitutional_alignment": ["article-i", "article-ii", "article-iii"],
            "related_files": [
                "tests/conftest.py",
                "tests/trinity_protocol/README_DOCKER_OLLAMA_FIXTURE.md",
                "docs/adr/ADR-028-ollama-docker-integration.md"
            ],
            "mission_context": "Manage Docker Ollama lifecycle for 140 integration tests"
        },
        tags=["pytest-fixtures", "session-scope", "docker-lifecycle", "integration-testing", "cleanup-patterns", "testing"]
    )

    # Pattern 2.2: Remove Import-Time Checks, Use Fixture Dependencies
    context.store_memory(
        key="pattern_remove_import_time_checks",
        content={
            "pattern_id": "ollama_docker_pattern_2_2",
            "pattern_name": "Remove Import-Time Checks, Use Fixture Dependencies",
            "category": "testing",
            "confidence": 0.78,
            "evidence_count": 4,
            "description": (
                "Replace import-time dependency checks with pytest fixture dependencies to enable fixture-managed lifecycle. "
                "Import-time checks run BEFORE pytest fixtures, preventing fixtures from managing dependency lifecycle. "
                "Use fixture parameters instead of global availability variables."
            ),
            "anti_pattern": """
# ❌ BAD: Import-time check
OLLAMA_AVAILABLE = is_ollama_available()

@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not available")
class TestIntegrationWorkflows:
    # Tests skipped before fixtures can start Docker
""",
            "correct_pattern": """
# ✅ GOOD: Fixture dependency
class TestIntegrationWorkflows:
    def test_workflow(self, docker_ollama, real_message_bus):
        # Fixture manages Docker lifecycle
        endpoint = docker_ollama
        # ... test logic
""",
            "applicability": ["External service integration tests", "Hardware-dependent tests", "CI/CD vs local execution"],
            "trade_offs": {
                "pro": ["Fixtures control lifecycle", "Automated service management", "No manual setup"],
                "con": ["Refactoring existing tests", "Test parameter increase"]
            },
            "constitutional_alignment": ["article-i", "article-iii"],
            "related_files": [
                "tests/trinity_protocol/core/test_hybrid_executor.py",
                "docs/adr/ADR-028-ollama-docker-integration.md"
            ],
            "mission_context": "Removed OLLAMA_AVAILABLE import-time check for 140 tests"
        },
        tags=["pytest-refactoring", "import-time-checks", "fixture-dependencies", "test-architecture", "testing"]
    )

    # Pattern 2.3: Memory-Aware Test Execution (ADR-023)
    context.store_memory(
        key="pattern_memory_aware_test_execution",
        content={
            "pattern_id": "ollama_docker_pattern_2_3",
            "pattern_name": "Memory-Aware Test Execution (ADR-023 Pattern)",
            "category": "testing",
            "confidence": 0.82,
            "evidence_count": 5,
            "description": (
                "Dynamically adjust test parallelism based on resource constraints to prevent system instability: "
                "(1) Detect expensive processes (local LLMs, large models), "
                "(2) Calculate safe worker count based on memory budget, "
                "(3) Enforce memory limits via Docker, "
                "(4) Reduce parallelism when resource-intensive services active."
            ),
            "implementation_template": """
def get_safe_worker_count() -> int:
    # Detect Docker Ollama (38GB footprint)
    if detect_docker_ollama():
        return 3  # 3 workers × 3GB = 9GB tests

    # No local model
    available_memory_gb = psutil.virtual_memory().available / (1024**3)

    if available_memory_gb < 10:
        return 1  # Critical memory
    elif available_memory_gb < 20:
        return 6  # Moderate parallelism
    else:
        return 10  # Full parallelism
""",
            "applicability": ["Large model testing", "Memory-intensive operations", "Resource-constrained CI"],
            "trade_offs": {
                "pro": ["Prevents OOM crashes", "Maintains 100% test completion", "ADR-023 compliance"],
                "con": ["Slower test execution (8min vs 3min)", "Complexity in worker calculation"]
            },
            "constitutional_alignment": ["article-i", "article-ii"],
            "related_files": [
                "run_tests.py",
                "tools/memory_aware_test_runner.py",
                "docker-compose.yml",
                "docs/adr/ADR-023-memory-aware-test-execution.md",
                "docs/adr/ADR-028-ollama-docker-integration.md"
            ],
            "mission_context": "Memory-safe test execution with Docker Ollama (3 workers, 9GB budget)"
        },
        tags=["memory-aware-execution", "adr-023", "worker-adjustment", "docker-memory-limits", "resource-constraints", "testing"]
    )

    # Pattern 2.4: CI/CD Small Model Strategy
    context.store_memory(
        key="pattern_cicd_small_model_strategy",
        content={
            "pattern_id": "ollama_docker_pattern_2_4",
            "pattern_name": "CI/CD Small Model Strategy",
            "category": "testing",
            "confidence": 0.72,
            "evidence_count": 3,
            "description": (
                "Use smaller, faster models in CI/CD while maintaining full model in development: "
                "(1) Dual model configuration (dev: large, CI: small), "
                "(2) API compatibility (same API, different model), "
                "(3) Fast CI validation (3-min download vs 15-min), "
                "(4) Environment-based override."
            ),
            "implementation_template": """
# .github/workflows/test.yml
- name: Pull CI Model (Small)
  run: |
    docker exec agency-ollama ollama pull qwen2.5-coder:1.5b  # 900MB

- name: Run Integration Tests
  env:
    OLLAMA_MODEL: qwen2.5-coder:1.5b  # Override dev model
  run: pytest tests/trinity_protocol/
""",
            "applicability": ["LLM integration tests", "ML model validation", "Database fixtures (small dataset in CI)"],
            "trade_offs": {
                "pro": ["3-min CI download vs 15-min dev", "Same API compatibility", "Fast validation"],
                "con": ["Different model behavior in CI vs dev", "Potential false positives"]
            },
            "constitutional_alignment": ["article-iii"],
            "related_files": [
                "docs/adr/ADR-028-ollama-docker-integration.md",
                "specs/spec-023-ollama-docker-integration.md"
            ],
            "mission_context": "CI uses qwen2.5-coder:1.5b (900MB) vs dev qwen3-coder:30b (19GB)"
        },
        tags=["ci-cd-optimization", "model-strategy", "dual-configuration", "fast-validation", "testing"]
    )

    # Pattern 3.1: Shell Script with Comprehensive Error Handling
    context.store_memory(
        key="pattern_shell_script_error_handling",
        content={
            "pattern_id": "ollama_docker_pattern_3_1",
            "pattern_name": "Shell Script with Comprehensive Error Handling",
            "category": "tooling",
            "confidence": 0.70,
            "evidence_count": 3,
            "description": (
                "Implement robust shell scripts with defensive error handling: "
                "(1) Strict error checking (set -euo pipefail), "
                "(2) Function decomposition (single-purpose), "
                "(3) Status messages with visual indicators, "
                "(4) Graceful fallbacks for multiple execution modes."
            ),
            "implementation_template": """
#!/bin/bash
set -euo pipefail

readonly GREEN='\\033[0;32m'
readonly RED='\\033[0;31m'
readonly YELLOW='\\033[1;33m'
readonly NC='\\033[0m'

log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1" >&2; }
log_info() { echo -e "${YELLOW}→${NC} $1"; }

cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Script failed with exit code $exit_code"
    fi
}
trap cleanup EXIT
""",
            "applicability": ["Setup scripts", "Health check scripts", "CI/CD automation"],
            "trade_offs": {
                "pro": ["Early error detection", "Visual clarity", "Guaranteed cleanup"],
                "con": ["Complexity increase", "Strict mode may catch false positives"]
            },
            "constitutional_alignment": ["article-i", "article-ii"],
            "related_files": [
                "scripts/init_ollama_model.sh",
                "scripts/verify_ollama_docker.sh"
            ],
            "mission_context": "Robust model initialization script with Docker detection"
        },
        tags=["shell-scripting", "error-handling", "defensive-programming", "logging-patterns", "tooling"]
    )

    # Pattern 3.2: Multi-Layer Service Detection
    context.store_memory(
        key="pattern_multi_layer_service_detection",
        content={
            "pattern_id": "ollama_docker_pattern_3_2",
            "pattern_name": "Multi-Layer Service Detection (Docker → Native → Fail)",
            "category": "tooling",
            "confidence": 0.75,
            "evidence_count": 4,
            "description": (
                "Implement cascading detection logic for services that can run in multiple modes: "
                "(1) Docker detection (preferred for isolation), "
                "(2) Native process detection (fallback), "
                "(3) Graceful failure with diagnostic message."
            ),
            "implementation_template": """
def detect_service() -> Result[ServiceInfo, str]:
    # Layer 1: Docker (preferred)
    result = subprocess.run(["docker", "ps", "-f", "name=agency-service"], capture_output=True)
    if "service" in result.stdout.decode():
        return Ok(ServiceInfo(mode="docker", endpoint="http://localhost:PORT", is_memory_limited=True))

    # Layer 2: Native (fallback)
    if is_process_running("service"):
        return Ok(ServiceInfo(mode="native", endpoint="http://localhost:PORT", is_memory_limited=False))

    # Layer 3: Graceful failure
    return Err("Service not available. Try:\\n  - Docker: docker compose up -d\\n  - Native: service serve &")
""",
            "applicability": ["Services with dual deployment modes", "Development vs production detection", "CI/CD vs local execution"],
            "trade_offs": {
                "pro": ["Flexible deployment", "Graceful degradation", "Clear diagnostic messages"],
                "con": ["Detection complexity", "Multiple code paths to maintain"]
            },
            "constitutional_alignment": ["article-i"],
            "related_files": [
                "scripts/init_ollama_model.sh",
                "tools/memory_aware_test_runner.py",
                "tests/conftest.py"
            ],
            "mission_context": "Detect Docker vs native Ollama for memory-aware execution"
        },
        tags=["service-detection", "fallback-logic", "multi-layer-detection", "docker-vs-native", "tooling"]
    )

    # Pattern 3.3: Pytest Test Validation for Shell Scripts
    context.store_memory(
        key="pattern_pytest_shell_script_validation",
        content={
            "pattern_id": "ollama_docker_pattern_3_3",
            "pattern_name": "Pytest Test Validation for Shell Scripts",
            "category": "tooling",
            "confidence": 0.68,
            "evidence_count": 3,
            "description": (
                "Validate shell scripts with pytest to ensure correctness and catch regressions: "
                "(1) Mock subprocess calls to avoid external dependencies, "
                "(2) Test success paths (Docker available, native available), "
                "(3) Test failure paths (service not available), "
                "(4) Verify output messages for user clarity."
            ),
            "implementation_template": """
@patch("subprocess.run")
def test_docker_detection_success(self, mock_run):
    mock_run.return_value = Mock(stdout=b"agency-ollama", returncode=0)

    result = subprocess.run(["bash", "scripts/init_ollama_model.sh"], capture_output=True)

    assert "docker exec agency-ollama" in result.stdout.decode()
    assert result.returncode == 0
""",
            "applicability": ["Setup scripts validation", "Health check scripts", "CI/CD automation scripts"],
            "trade_offs": {
                "pro": ["Catch regressions early", "Validate error paths", "No external dependencies in tests"],
                "con": ["Mock complexity", "May diverge from real execution"]
            },
            "constitutional_alignment": ["article-ii"],
            "related_files": [
                "tests/test_init_ollama_model.py",
                "scripts/init_ollama_model.sh"
            ],
            "mission_context": "Validate model initialization script with 334 lines of pytest tests"
        },
        tags=["pytest-shell-testing", "script-validation", "mock-subprocess", "regression-testing", "tooling"]
    )

    # Pattern 4.1: Spec-Driven Development with Acceptance Criteria
    context.store_memory(
        key="pattern_spec_driven_development",
        content={
            "pattern_id": "ollama_docker_pattern_4_1",
            "pattern_name": "Spec-Driven Development with Acceptance Criteria",
            "category": "documentation",
            "confidence": 0.85,
            "evidence_count": 6,
            "description": (
                "Document complex features with formal specifications containing: "
                "(1) Goals & Non-Goals (scope clarity), "
                "(2) User Personas & Journeys (use case validation), "
                "(3) Acceptance Criteria (testable requirements), "
                "(4) Architecture Diagrams (visual clarity), "
                "(5) Risk Assessment (mitigation planning)."
            ),
            "implementation_template": """
# Specification: Feature Name
**Spec ID**: `spec-XXX-feature-name`
**Status**: Draft | Approved | Implemented
**Related ADR**: `ADR-XXX`

## Goals
- [ ] Goal 1: Primary objective (measurable)

### Success Metrics
- Metric 1: Target value

## Non-Goals (Explicit Exclusions)
- Exclusion 1: Out of scope (rationale)

## Acceptance Criteria
- [ ] AC-1: Service starts successfully (testable)

### Constitutional Compliance
- [ ] AC-CI.1: Article I compliance (retry logic)
""",
            "applicability": ["Complex feature development", "External integration projects", "Regulatory compliance features"],
            "trade_offs": {
                "pro": ["Clear scope", "Testable requirements", "Traceability", "Risk mitigation"],
                "con": ["Upfront documentation cost", "Maintenance overhead"]
            },
            "constitutional_alignment": ["article-v"],
            "related_files": [
                "specs/spec-023-ollama-docker-integration.md",
                "docs/adr/ADR-028-ollama-docker-integration.md"
            ],
            "mission_context": "48 acceptance criteria for Docker Compose integration"
        },
        tags=["spec-driven-development", "acceptance-criteria", "article-v", "documentation-patterns", "formal-specifications", "documentation"]
    )

    # Pattern 4.2: ADR with Constitutional Alignment Section
    context.store_memory(
        key="pattern_adr_constitutional_alignment",
        content={
            "pattern_id": "ollama_docker_pattern_4_2",
            "pattern_name": "ADR with Constitutional Alignment Section",
            "category": "documentation",
            "confidence": 0.80,
            "evidence_count": 5,
            "description": (
                "Document architectural decisions with explicit constitutional compliance section: "
                "(1) Context (problem statement), "
                "(2) Decision (chosen solution with alternatives), "
                "(3) Consequences (trade-offs), "
                "(4) Constitutional Alignment (Article I-V compliance)."
            ),
            "implementation_template": """
# ADR-XXX: Decision Title
**Constitutional Alignment**: Articles I, II, III, IV, V

## Constitutional Alignment

### Article I: Complete Context Before Action
**Compliance Mechanisms**:
- Retry logic with exponential backoff
- Complete data before processing

**Implementation**:
```python
# Code example showing Article I compliance
```

### Article II: 100% Verification and Stability
**Compliance Mechanisms**:
- Real functionality tests (no mocks)
- 100% test coverage
""",
            "applicability": ["Major architectural changes", "Constitutional compliance validation", "Pattern documentation"],
            "trade_offs": {
                "pro": ["Explicit compliance", "Pattern reusability", "Audit trail"],
                "con": ["Documentation effort", "Requires constitutional knowledge"]
            },
            "constitutional_alignment": ["article-i", "article-ii", "article-iii", "article-iv", "article-v"],
            "related_files": [
                "docs/adr/ADR-028-ollama-docker-integration.md"
            ],
            "mission_context": "ADR-028 with comprehensive constitutional alignment section"
        },
        tags=["adr-patterns", "constitutional-alignment", "architectural-decisions", "compliance-documentation", "documentation"]
    )

    print("✓ Successfully stored 12 patterns to VectorStore")
    print(f"  - Session ID: {context.session_id}")
    print("  - Average confidence: 0.82")
    print("  - Constitutional compliance: Articles I-V")
    print("\nPatterns stored:")
    print("  1. Docker Compose Service Lifecycle Management (0.95)")
    print("  2. Exponential Backoff Health Check Protocol (0.88)")
    print("  3. Volume Persistence for Expensive Resources (0.85)")
    print("  4. Session-Scoped Pytest Fixtures for External Services (0.90)")
    print("  5. Remove Import-Time Checks, Use Fixture Dependencies (0.78)")
    print("  6. Memory-Aware Test Execution (ADR-023 Pattern) (0.82)")
    print("  7. CI/CD Small Model Strategy (0.72)")
    print("  8. Shell Script with Comprehensive Error Handling (0.70)")
    print("  9. Multi-Layer Service Detection (Docker → Native → Fail) (0.75)")
    print(" 10. Pytest Test Validation for Shell Scripts (0.68)")
    print(" 11. Spec-Driven Development with Acceptance Criteria (0.85)")
    print(" 12. ADR with Constitutional Alignment Section (0.80)")

    return context


if __name__ == "__main__":
    context = store_patterns()
    print("\n✓ Pattern extraction complete - VectorStore updated")
    print("  Query example: context.search_memories(['docker-compose', 'article-i'])")
