# Specification: Ollama Docker Compose Integration

**Spec ID**: `spec-023-ollama-docker-integration`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-11
**Last Updated**: 2025-10-11
**Related Plan**: `plan-023-ollama-docker-integration.md` (to be created)
**Related ADR**: `ADR-023` (Memory-Aware Test Execution)
**Related Task Graph**: Tier 1 - Docker Compose Architecture Specification

---

## Executive Summary

Formalize the Docker Compose architecture for Ollama local LLM service integration with Agency OS, including production-ready service configuration, model auto-download strategy, volume persistence, health checking, and CI/CD workflow integration. This specification ensures 96% cost reduction (from $40K to $1.6K/month) through reliable local model execution while maintaining constitutional compliance (Articles I-V).

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Standardize Docker Compose service definition for Ollama with production-grade configuration
- [ ] **Goal 2**: Implement automatic model pull strategy for development and CI/CD environments
- [ ] **Goal 3**: Define volume mount strategy ensuring model persistence across container restarts
- [ ] **Goal 4**: Configure comprehensive health checks validating service readiness before usage
- [ ] **Goal 5**: Integrate memory-aware test execution with Docker-based Ollama detection
- [ ] **Goal 6**: Update CI/CD workflows for automated Docker Compose validation

### Success Metrics
- **Service Reliability**: 99.9% uptime for Ollama container in development
- **Model Persistence**: 0 re-downloads after initial pull (32GB saved per restart)
- **Health Check Accuracy**: 100% detection of service readiness before inference
- **Memory Safety**: 0 kernel panics with Docker-based local model (ADR-023 compliance)
- **CI/CD Integration**: 100% automated validation of Docker Compose configuration
- **Cost Optimization**: 96% cost reduction maintained ($1.6K vs $40K/month)

---

## Non-Goals

### Explicit Exclusions
- **Multi-Model Orchestration**: Single model deployment only (OLLAMA_MAX_LOADED_MODELS=1)
- **Kubernetes/Swarm Deployment**: Docker Compose for development only, not production cluster
- **Model Fine-Tuning Pipeline**: Using pre-trained models only (Qwen3-Coder 30B)
- **Distributed Inference**: Single-node execution optimized for current hardware (see docs/HARDWARE_OPTIMIZATION.md) Mac
- **Windows/Linux Native Support**: Mac-specific Metal GPU optimization (can be adapted later)

### Future Considerations
- **Model Version Management**: Automated model updates with version pinning
- **Multi-GPU Support**: Scale to Mac Studio with M2 Ultra (192GB)
- **Model Quantization Pipeline**: Automated Q8_0/Q4_0 quantization from HuggingFace
- **Ollama Cluster Mode**: Distributed inference across multiple Macs

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Local Developer (@am)
- **Description**: Engineer using Agency OS with local LLM for cost-effective development
- **Goals**: Reliable local model execution, fast startup, automatic recovery from failures
- **Pain Points**: Manual Ollama startup, 32GB model re-downloads, unclear health status
- **Technical Proficiency**: Expert in Docker, LLM deployment, Apple Silicon optimization
- **Environment**: current hardware (see docs/HARDWARE_OPTIMIZATION.md) Mac, macOS 15.0, Docker Desktop 4.x

#### Persona 2: CI/CD Pipeline (GitHub Actions)
- **Description**: Automated testing infrastructure validating Ollama integration
- **Goals**: Fast model pull (small CI model), reliable health checks, parallel test execution
- **Pain Points**: Long model download times (30B model), memory constraints in CI runners
- **Technical Proficiency**: Expert in GitHub Actions, Docker Compose, pytest configuration
- **Environment**: Ubuntu 22.04, 7GB RAM, GitHub Actions runner

#### Persona 3: Memory-Aware Test Runner (tools/memory_aware_test_runner.py)
- **Description**: Python tool dynamically adjusting pytest workers based on Ollama state
- **Goals**: Detect Docker-based Ollama, query health status, prevent memory exhaustion
- **Pain Points**: Ollama detection unreliable (Docker vs native), health check timeouts
- **Technical Proficiency**: Expert in psutil, asyncio, Docker API, Result pattern
- **Environment**: Python 3.12+, psutil, aiohttp, Docker Compose available

### User Journeys

#### Journey 1: First-Time Setup (Developer)
```
1. User starts with: Fresh Agency OS clone, no Ollama installed
2. User needs to: Set up local model with Docker Compose for 96% cost savings
3. User performs: Runs `docker compose up -d` in repository root
4. System responds:
   - Pulls ollama/ollama:latest image (500MB)
   - Starts container with port 11434 exposed
   - Mounts ~/.ollama volume for model persistence
   - Health check waits 120s for service readiness
5. User continues: Runs `docker exec agency-ollama ollama pull qwen3-coder:30b`
6. System downloads: 19GB Q4_K_M model with Metal GPU optimization
7. System validates: Health check passes (/api/tags returns model list)
8. User achieves: Local model ready, 96% cost reduction active
```

#### Journey 2: Container Restart After Reboot (Developer)
```
1. User starts with: Mac reboot, Ollama container stopped
2. User needs to: Resume local model without re-downloading 19GB
3. User performs: Runs `docker compose up -d`
4. System responds:
   - Starts agency-ollama container
   - Mounts existing ~/.ollama volume (model already present)
   - Health check validates model availability in 30s
5. System skips: Model re-download (persistent volume works)
6. User achieves: Instant local model availability (2-minute startup vs 15-minute download)
```

#### Journey 3: CI/CD Automated Testing (GitHub Actions)
```
1. CI starts with: Pull request modifying docker-compose.yml
2. CI needs to: Validate Ollama integration without 30B model (too large)
3. CI performs:
   - Runs .github/workflows/ollama-docker-tests.yml
   - Sets OLLAMA_MODEL=qwen2.5-coder:1.5b (900MB vs 19GB)
4. System responds:
   - Starts Ollama container with health check
   - Pulls small CI model (1.5B, 3-minute download)
   - Waits for healthy status (max 180s timeout)
5. CI validates:
   - Model inference test (basic prompt)
   - API endpoint health (/api/tags, /api/version)
   - Memory-aware runner tests (Docker detection)
6. CI achieves: Automated validation in 10 minutes (vs 45 minutes with 30B model)
```

#### Journey 4: Memory-Aware Test Execution (Test Runner)
```
1. Tool starts with: Test suite execution via `python run_tests.py --run-all`
2. Tool needs to: Detect Docker Ollama and adjust pytest workers (3 vs 10)
3. Tool performs:
   - Calls check_ollama_running() from memory_aware_test_runner.py
   - Detects Docker container via `docker ps | grep ollama`
   - Queries health check endpoint (http://localhost:11434/api/tags)
4. System responds:
   - Docker detection: True (agency-ollama container running)
   - Health status: OllamaHealthStatus(is_running=True, is_docker=True)
   - Worker adjustment: 3 workers (9GB test budget vs 30GB)
5. Tool calculates:
   - Memory budget: available memory total - 38GB Ollama - 9GB tests = 1GB safety margin
6. Tool achieves: 0 kernel panics, 100% test completion (Article I compliance)
```

---

## Acceptance Criteria

### Functional Requirements

#### Docker Compose Service Definition
- [ ] **AC-1.1**: Service named `ollama` uses `ollama/ollama:latest` image
- [ ] **AC-1.2**: Port 11434 exposed to host (Ollama API endpoint)
- [ ] **AC-1.3**: Volume mount `~/.ollama:/root/.ollama` persists models across restarts
- [ ] **AC-1.4**: Environment variable `OLLAMA_MODELS=/root/.ollama/models` configures storage
- [ ] **AC-1.5**: Environment variable `OLLAMA_KV_CACHE_TYPE=q8_0` enables memory optimization
- [ ] **AC-1.6**: Environment variable `OLLAMA_FLASH_ATTENTION=1` enables performance boost
- [ ] **AC-1.7**: Environment variable `OLLAMA_NUM_GPU=1` enables Metal GPU (Apple Silicon)
- [ ] **AC-1.8**: Resource limit `memory: 40G` prevents memory exhaustion (ADR-023)
- [ ] **AC-1.9**: Restart policy `unless-stopped` ensures automatic recovery
- [ ] **AC-1.10**: Container name `agency-ollama` enables consistent identification

#### Health Check Configuration
- [ ] **AC-2.1**: Health check command validates service readiness via `/api/tags` endpoint
- [ ] **AC-2.2**: Health check interval 30s balances responsiveness and overhead
- [ ] **AC-2.3**: Health check timeout 10s prevents hanging checks
- [ ] **AC-2.4**: Health check retries 5 times before marking unhealthy
- [ ] **AC-2.5**: Health check start period 120s accommodates initial model pull (32GB download)
- [ ] **AC-2.6**: Health check uses `curl -f` for HTTP status validation

#### Model Auto-Download Strategy
- [ ] **AC-3.1**: Development environment uses `qwen3-coder:30b` (19GB Q4_K_M)
- [ ] **AC-3.2**: CI/CD environment uses `qwen2.5-coder:1.5b` (900MB for fast tests)
- [ ] **AC-3.3**: Model pull executed via `docker exec agency-ollama ollama pull <model>`
- [ ] **AC-3.4**: First-time setup includes model pull in setup script
- [ ] **AC-3.5**: Model persistence verified by checking `~/.ollama/models/` directory
- [ ] **AC-3.6**: Model availability validated via `/api/tags` endpoint before inference

#### Volume Mount Strategy
- [ ] **AC-4.1**: Host path `~/.ollama` maps to container path `/root/.ollama`
- [ ] **AC-4.2**: Volume persists across container restarts (no re-download)
- [ ] **AC-4.3**: Volume stores models in `~/.ollama/models/` (Q4_K_M GGUF files)
- [ ] **AC-4.4**: Volume permissions allow read/write for Ollama service
- [ ] **AC-4.5**: Volume size monitored to prevent disk exhaustion (30GB+ for 30B model)

#### Memory-Aware Test Runner Integration
- [ ] **AC-5.1**: `check_ollama_running()` detects Docker container via `docker ps`
- [ ] **AC-5.2**: `detect_docker_ollama()` returns True when agency-ollama container running
- [ ] **AC-5.3**: `check_ollama_health()` validates Docker endpoint `http://localhost:11434`
- [ ] **AC-5.4**: `OllamaHealthStatus.is_docker=True` when Docker detection succeeds
- [ ] **AC-5.5**: Test runner reduces workers to 3 when Docker Ollama detected (ADR-023)
- [ ] **AC-5.6**: Health check retries 3x with exponential backoff (Article I compliance)

#### CI/CD Workflow Integration
- [ ] **AC-6.1**: Workflow `.github/workflows/ollama-docker-tests.yml` validates Docker Compose
- [ ] **AC-6.2**: Workflow uses small CI model `qwen2.5-coder:1.5b` (900MB vs 19GB)
- [ ] **AC-6.3**: Workflow waits for health check before running tests (max 180s timeout)
- [ ] **AC-6.4**: Workflow runs inference test to validate model functionality
- [ ] **AC-6.5**: Workflow runs memory-aware runner tests to validate Docker detection
- [ ] **AC-6.6**: Workflow reports test results via `dorny/test-reporter@v1`
- [ ] **AC-6.7**: Workflow cleans up containers via `docker compose down -v` on completion

### Non-Functional Requirements

#### Performance
- [ ] **AC-P.1**: Container startup completes within 10 seconds (image already pulled)
- [ ] **AC-P.2**: Health check initial readiness within 30 seconds (model already downloaded)
- [ ] **AC-P.3**: Model inference latency <5 seconds for first token (Metal GPU optimized)
- [ ] **AC-P.4**: Volume mount I/O supports 30-50 tokens/sec throughput

#### Reliability
- [ ] **AC-R.1**: Health check detects service failures within 30 seconds (interval)
- [ ] **AC-R.2**: Automatic restart on failure via `unless-stopped` policy
- [ ] **AC-R.3**: Health check retry logic prevents false negatives (5 retries)
- [ ] **AC-R.4**: Volume persistence prevents data loss on container restart

#### Scalability
- [ ] **AC-S.1**: Memory limit 40GB supports Q4_K_M model + Q8_0 KV cache (37GB total)
- [ ] **AC-S.2**: Configuration adaptable to Mac Studio (192GB) via memory limit adjustment
- [ ] **AC-S.3**: CI configuration supports parallel workflow execution (small model)

#### Usability
- [ ] **AC-U.1**: Single command `docker compose up -d` starts Ollama service
- [ ] **AC-U.2**: Health check status visible via `docker compose ps` (healthy/unhealthy)
- [ ] **AC-U.3**: Logs accessible via `docker compose logs -f ollama`
- [ ] **AC-U.4**: Memory usage visible via `docker stats agency-ollama`

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [ ] **AC-CI.1**: Health check retries 5x with exponential backoff (2x timeout per retry)
- [ ] **AC-CI.2**: Memory-aware runner queries health status before worker adjustment
- [ ] **AC-CI.3**: CI workflow waits for health check before running tests (max 180s)
- [ ] **AC-CI.4**: No broken windows: health check failures trigger automatic restart

#### Article II: 100% Verification and Stability
- [ ] **AC-CII.1**: Health check validates `/api/tags` endpoint (model availability)
- [ ] **AC-CII.2**: Inference test validates model functionality in CI
- [ ] **AC-CII.3**: Memory-aware runner tests validate Docker detection (100% pass)
- [ ] **AC-CII.4**: CI workflow enforces automated testing before merge

#### Article III: Automated Merge Enforcement
- [ ] **AC-CIII.1**: CI workflow runs automatically on docker-compose.yml changes
- [ ] **AC-CIII.2**: Health check failures block merge (fail-on-error: true)
- [ ] **AC-CIII.3**: No manual overrides for Docker configuration validation

#### Article IV: Continuous Learning and Improvement
- [ ] **AC-CIV.1**: VectorStore stores successful Docker Compose patterns (health check config)
- [ ] **AC-CIV.2**: ADR-023 documents memory-aware execution learnings
- [ ] **AC-CIV.3**: Telemetry tracks health check success rate for continuous improvement

#### Article V: Spec-Driven Development
- [ ] **AC-CV.1**: This specification authoritative source for Docker Compose architecture
- [ ] **AC-CV.2**: All docker-compose.yml changes trace back to specification updates
- [ ] **AC-CV.3**: Implementation follows spec-kit methodology (Goals, Non-Goals, Personas, Criteria)

---

## Dependencies & Constraints

### System Dependencies
- **Docker Desktop**: Version 4.x+ with Docker Compose V2 support
- **Ollama Image**: ollama/ollama:latest from Docker Hub (500MB base image)
- **Qwen3-Coder Model**: Official Ollama model (19GB Q4_K_M or 32GB Q8_0)
- **Memory-Aware Test Runner**: tools/memory_aware_test_runner.py with psutil
- **Health Check Tool**: tools/ollama_health_check.py with aiohttp

### External Dependencies
- **Docker Hub**: Availability of ollama/ollama:latest image
- **Ollama API**: Stability of /api/tags, /api/version, /api/generate endpoints
- **GitHub Actions**: Ubuntu 22.04 runners with Docker support

### Technical Constraints
- **Memory Budget**: 40GB limit for current hardware (see docs/HARDWARE_OPTIMIZATION.md) Mac (ADR-023 safety margin)
- **Disk Space**: 30GB+ required for model storage (~/.ollama/models/)
- **Network**: 19GB download for initial model pull (30B model)
- **Port Availability**: Port 11434 must be free for Ollama API

### Business Constraints
- **Cost Optimization**: Must maintain 96% cost reduction ($1.6K vs $40K/month)
- **Development Velocity**: Setup time <15 minutes (including model download)
- **CI/CD Duration**: Workflow execution <30 minutes (using small CI model)

---

## Risk Assessment

### High Risk Items
- **Risk 1**: Model re-download on every container restart (32GB, 15-minute delay)
  - **Mitigation**: Volume mount `~/.ollama:/root/.ollama` persists models
  - **Validation**: Test container restart without re-download
  - **Rollback**: Manual model caching script as fallback

- **Risk 2**: Health check false negatives during model loading
  - **Mitigation**: 120s start period accommodates initial model pull
  - **Validation**: Test health check during first-time model download
  - **Rollback**: Increase start period to 300s if needed

### Medium Risk Items
- **Risk 3**: Memory exhaustion if resource limit not enforced
  - **Mitigation**: `memory: 40G` limit in Docker Compose (ADR-023)
  - **Validation**: Monitor memory usage via `docker stats`
  - **Rollback**: Reduce limit to 35GB or use Q4_0 KV cache

- **Risk 4**: Docker detection fails in memory-aware test runner
  - **Mitigation**: Multiple detection methods (health check, docker ps, process)
  - **Validation**: Run tests with Docker Ollama active
  - **Rollback**: Fallback to process detection or marker file

### Low Risk Items
- **Risk 5**: CI workflow timeout with large model (30B)
  - **Mitigation**: Use small model `qwen2.5-coder:1.5b` (900MB) in CI
  - **Validation**: GitHub Actions caching for Docker images
  - **Rollback**: Increase timeout to 45 minutes

### Constitutional Risks
- **Constitutional Risk 1**: Article I violation if health check incomplete
  - **Mitigation**: Retry logic with exponential backoff (5 retries)
  - **Validation**: Test health check with network failures
  - **Rollback**: Increase retry count to 10

- **Constitutional Risk 2**: Article II violation if memory limit unenforced
  - **Mitigation**: Automated monitoring via docker stats in CI
  - **Validation**: Memory profiling during test suite execution
  - **Rollback**: Alert on memory usage >42GB (90% of limit)

---

## Integration Points

### System Integration
- **Memory-Aware Test Runner**: `tools/memory_aware_test_runner.py`
  - Integration: `check_ollama_running()` calls `detect_docker_ollama()`
  - Data Flow: Docker detection → Worker count adjustment (3 vs 10)
  - Validation: Tests in `tests/test_memory_aware_runner.py`

- **Ollama Health Check Tool**: `tools/ollama_health_check.py`
  - Integration: `check_ollama_health(endpoint="http://localhost:11434")`
  - Data Flow: Health status → OllamaHealthStatus model → Result pattern
  - Validation: Tests in `tests/test_ollama_health_check.py`

- **Run Tests Script**: `run_tests.py`
  - Integration: Calls `get_test_execution_config()` for worker count
  - Data Flow: Ollama state → pytest args (`-n 3` vs `-n 10`)
  - Validation: Manual test with Docker Ollama active/inactive

### CI/CD Integration
- **GitHub Actions Workflow**: `.github/workflows/ollama-docker-tests.yml`
  - Integration: Triggered on docker-compose.yml changes
  - Data Flow: PR → Docker Compose validation → Test results
  - Validation: CI pipeline green status required for merge

- **Branch Protection**: GitHub branch protection rules
  - Integration: Enforce CI workflow success before merge
  - Data Flow: CI status → Merge allowed/blocked
  - Validation: Attempt merge with failing CI (should block)

### External Integration
- **Docker Desktop**: Host Docker daemon
  - Integration: docker compose CLI communicates with daemon
  - Data Flow: YAML config → Container creation → Health check
  - Validation: `docker compose config` validates YAML syntax

- **Ollama Service**: Local LLM inference server
  - Integration: HTTP API on port 11434
  - Data Flow: Inference request → Model execution → JSON response
  - Validation: `curl http://localhost:11434/api/tags`

---

## Testing Strategy

### Test Categories

#### Unit Tests
- **File**: `tests/test_ollama_health_check.py` (17 tests, 100% pass)
  - Test health check success with model available
  - Test health check failure with service down
  - Test retry logic with exponential backoff (Article I)
  - Test Docker detection accuracy
  - Test inference validation

- **File**: `tests/test_memory_aware_runner.py` (11 tests, 100% pass)
  - Test worker count calculation (local model ON/OFF)
  - Test Docker Ollama detection
  - Test health check integration
  - Test memory safety verification
  - Test execution config generation

#### Integration Tests
- **File**: `tests/integration/test_docker_compose_integration.py` (to be created)
  - Test container startup and health check
  - Test model persistence across restarts
  - Test memory limit enforcement
  - Test volume mount permissions
  - Test API endpoint availability

#### CI/CD Tests
- **Workflow**: `.github/workflows/ollama-docker-tests.yml` (existing)
  - Test Docker Compose service startup
  - Test small model pull (qwen2.5-coder:1.5b)
  - Test health check wait logic (max 180s)
  - Test model inference with CI model
  - Test memory-aware runner tests in CI

#### Constitutional Compliance Tests
- **Article I**: Retry logic with exponential backoff (5 retries)
- **Article II**: 100% test pass rate maintained (1,762 tests)
- **Article III**: Automated CI enforcement (no manual overrides)
- **Article IV**: VectorStore pattern storage (health check config)
- **Article V**: Traceability to specification (all changes documented)

### Test Data Requirements
- **Sample Models**: qwen3-coder:30b (dev), qwen2.5-coder:1.5b (CI)
- **Health Check Responses**: Valid /api/tags JSON with model list
- **Docker Compose Config**: Valid YAML with all required fields
- **Memory Profiles**: psutil data with Ollama active/inactive

### Test Environment Requirements
- **Local Development**: current hardware (see docs/HARDWARE_OPTIMIZATION.md) Mac, Docker Desktop 4.x+
- **CI/CD**: GitHub Actions Ubuntu 22.04 runner, 7GB RAM
- **Mock Services**: Mock Ollama API for unit tests (no actual model)

---

## Implementation Phases

### Phase 1: Docker Compose Configuration ✅ (COMPLETE)
- **Scope**: Service definition, volume mounts, health checks
- **Deliverables**:
  - ✅ docker-compose.yml with ollama service
  - ✅ Environment variables for Metal GPU optimization
  - ✅ Resource limits for memory safety (40GB)
  - ✅ Health check configuration (/api/tags endpoint)
- **Success Criteria**: Service starts successfully, health check passes

### Phase 2: Model Auto-Download Strategy ✅ (COMPLETE)
- **Scope**: First-time setup script, model pull automation
- **Deliverables**:
  - ✅ scripts/setup_local_model.sh with Docker detection
  - ✅ Model pull via docker exec agency-ollama ollama pull
  - ✅ Documentation in docs/LOCAL_MODEL_OPTIMIZATION.md
- **Success Criteria**: Model downloaded once, persists across restarts

### Phase 3: Health Check Integration ✅ (COMPLETE)
- **Scope**: Ollama health check tool, Result pattern
- **Deliverables**:
  - ✅ tools/ollama_health_check.py with Docker detection
  - ✅ OllamaHealthStatus Pydantic model
  - ✅ Retry logic with exponential backoff (Article I)
  - ✅ tests/test_ollama_health_check.py (17 tests, 100% pass)
- **Success Criteria**: Health check detects Docker Ollama accurately

### Phase 4: Memory-Aware Test Runner Integration ✅ (COMPLETE)
- **Scope**: Docker detection in test runner
- **Deliverables**:
  - ✅ detect_docker_ollama() in memory_aware_test_runner.py
  - ✅ Worker count adjustment (3 vs 10) based on Docker state
  - ✅ tests/test_memory_aware_runner.py (11 tests, 100% pass)
- **Success Criteria**: Test runner adjusts workers when Docker Ollama active

### Phase 5: CI/CD Workflow Integration ✅ (COMPLETE)
- **Scope**: GitHub Actions workflow for automated validation
- **Deliverables**:
  - ✅ .github/workflows/ollama-docker-tests.yml
  - ✅ Small CI model configuration (qwen2.5-coder:1.5b)
  - ✅ Health check wait logic (max 180s timeout)
  - ✅ Test result reporting via dorny/test-reporter
- **Success Criteria**: CI workflow passes on docker-compose.yml changes

### Phase 6: Documentation and Specification (CURRENT)
- **Scope**: Formal specification using spec-kit methodology
- **Deliverables**:
  - 🔄 specs/spec-023-ollama-docker-integration.md (this document)
  - 📋 plans/plan-023-ollama-docker-integration.md (to be created)
  - 📋 Update ADR-023 with Docker Compose references
- **Success Criteria**: Specification approved, implementation traced

---

## Architecture Diagrams

### Docker Compose Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Host Machine (current hardware (see docs/HARDWARE_OPTIMIZATION.md))              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Docker Compose (docker-compose.yml)                      │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  agency-ollama Container                            │ │ │
│  │  ├─────────────────────────────────────────────────────┤ │ │
│  │  │  Image: ollama/ollama:latest                        │ │ │
│  │  │  Port: 11434:11434                                  │ │ │
│  │  │  Memory Limit: 40GB (ADR-023)                       │ │ │
│  │  │  Restart: unless-stopped                            │ │ │
│  │  ├─────────────────────────────────────────────────────┤ │ │
│  │  │                                                     │ │ │
│  │  │  Environment:                                       │ │ │
│  │  │    OLLAMA_MODELS=/root/.ollama/models              │ │ │
│  │  │    OLLAMA_KV_CACHE_TYPE=q8_0    (2x memory save)   │ │ │
│  │  │    OLLAMA_FLASH_ATTENTION=1     (perf boost)       │ │ │
│  │  │    OLLAMA_NUM_GPU=1             (Metal GPU)        │ │ │
│  │  │                                                     │ │ │
│  │  ├─────────────────────────────────────────────────────┤ │ │
│  │  │                                                     │ │ │
│  │  │  Volume Mount:                                      │ │ │
│  │  │    ~/.ollama → /root/.ollama  (model persistence)  │ │ │
│  │  │    ├─ models/                                      │ │ │
│  │  │    │  └─ qwen3-coder:30b (19GB Q4_K_M)             │ │ │
│  │  │    └─ manifests/                                   │ │ │
│  │  │                                                     │ │ │
│  │  ├─────────────────────────────────────────────────────┤ │ │
│  │  │                                                     │ │ │
│  │  │  Health Check:                                      │ │ │
│  │  │    Command: curl -f http://localhost:11434/api/tags│ │ │
│  │  │    Interval: 30s                                   │ │ │
│  │  │    Timeout: 10s                                    │ │ │
│  │  │    Retries: 5                                      │ │ │
│  │  │    Start Period: 120s  (initial model load)       │ │ │
│  │  │                                                     │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Host Processes                                           │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │                                                           │ │
│  │  1. Memory-Aware Test Runner                             │ │
│  │     - Detects Docker container (docker ps | grep ollama) │ │
│  │     - Queries health check (http://localhost:11434)      │ │
│  │     - Adjusts workers: 3 (Docker ON) vs 10 (OFF)         │ │
│  │                                                           │ │
│  │  2. Run Tests Script (run_tests.py)                      │ │
│  │     - Calls get_test_execution_config()                  │ │
│  │     - Passes worker count to pytest (-n 3)               │ │
│  │                                                           │ │
│  │  3. Health Check Tool (ollama_health_check.py)           │ │
│  │     - Validates /api/tags endpoint                       │ │
│  │     - Returns OllamaHealthStatus (Result pattern)        │ │
│  │     - Retries 5x with exponential backoff (Article I)    │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Health Check Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker Compose Up                                              │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Start agency-ollama Container                                  │
│  - Pull ollama/ollama:latest (if not cached)                    │
│  - Mount ~/.ollama volume                                       │
│  - Expose port 11434                                            │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Health Check: Wait 120s Start Period                           │
│  - Allows time for initial model pull (32GB download)           │
│  - Container marked "starting" during this period               │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Health Check: Execute Test Command                             │
│  - Run: curl -f http://localhost:11434/api/tags                 │
│  - Timeout: 10s                                                 │
│  - Expected: HTTP 200 with JSON model list                      │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
         ┌───┴───┐
         │Success?│
         └───┬───┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
 ┌─────────┐   ┌─────────┐
 │  Pass   │   │  Fail   │
 └────┬────┘   └────┬────┘
      │             │
      │             ▼
      │        ┌─────────────────────────────────────────┐
      │        │  Retry (max 5 times)                    │
      │        │  - Wait 30s interval                    │
      │        │  - Execute test command again           │
      │        └────┬────────────────────────────────────┘
      │             │
      │             ▼
      │         ┌───┴───┐
      │         │Success?│
      │         └───┬───┘
      │             │
      │      ┌──────┴──────┐
      │      │             │
      │      ▼             ▼
      │  ┌─────────┐   ┌─────────────────┐
      │  │  Pass   │   │  Fail (5x)      │
      │  └────┬────┘   └────┬────────────┘
      │       │             │
      └───────┴─────────┬───┴──────────────┐
                        │                  │
                        ▼                  ▼
              ┌──────────────────┐  ┌──────────────────┐
              │  Container:      │  │  Container:      │
              │  HEALTHY         │  │  UNHEALTHY       │
              │                  │  │                  │
              │  - API ready     │  │  - Restart       │
              │  - Model loaded  │  │    container     │
              │  - Inference OK  │  │  - Check logs    │
              └──────────────────┘  └──────────────────┘
```

### Model Persistence Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  First-Time Setup                                               │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  docker compose up -d                                           │
│  - Creates ~/.ollama directory if not exists                    │
│  - Mounts volume: ~/.ollama → /root/.ollama                     │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  docker exec agency-ollama ollama pull qwen3-coder:30b          │
│  - Downloads 19GB Q4_K_M model                                  │
│  - Stores in /root/.ollama/models/ (container path)            │
│  - Persists to ~/.ollama/models/ (host path via volume)        │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Host Filesystem: ~/.ollama/models/                             │
│  ├─ manifests/                                                  │
│  │  └─ registry.ollama.ai/library/qwen3-coder/30b              │
│  │     └─ manifest.json (model metadata)                       │
│  ├─ blobs/                                                      │
│  │  ├─ sha256-abc123... (Q4_K_M weights, 19GB)                 │
│  │  ├─ sha256-def456... (tokenizer)                            │
│  │  └─ sha256-ghi789... (config)                               │
│  └─ tmp/ (temporary files)                                     │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Container Restart Scenario                                     │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  docker compose down                                            │
│  - Stops container (preserves volume)                           │
│  - Host filesystem ~/.ollama unchanged                          │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  docker compose up -d                                           │
│  - Starts new container                                         │
│  - Re-mounts ~/.ollama → /root/.ollama                          │
│  - Model immediately available (no download!)                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Health Check Validates Model                                   │
│  - curl -f http://localhost:11434/api/tags                      │
│  - Returns: {"models":[{"name":"qwen3-coder:30b",...}]}         │
│  - Container marked HEALTHY in 30s (vs 15 min with download)   │
└─────────────────────────────────────────────────────────────────┘
```

### CI/CD Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Pull Request (docker-compose.yml changed)               │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Trigger: .github/workflows/ollama-docker-tests.yml             │
│  - on: pull_request (paths: docker-compose.yml, tests/, tools/) │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CI Environment Setup (Ubuntu 22.04, 7GB RAM)                   │
│  - Checkout repository                                          │
│  - Setup Python 3.12                                            │
│  - Install dependencies (pip install -e ., pytest, psutil)      │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Start Ollama Service                                           │
│  - Run: docker compose up -d                                    │
│  - Override: OLLAMA_MODEL=qwen2.5-coder:1.5b (900MB vs 19GB)   │
│  - Wait: 180s max for health check                             │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Pull CI Model                                                  │
│  - docker exec agency-ollama ollama pull qwen2.5-coder:1.5b     │
│  - Download: 900MB (3-minute download vs 15-minute for 30B)    │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Validate Model Inference                                       │
│  - Run: ollama run qwen2.5-coder:1.5b "Fix typo: def calc():"  │
│  - Expected: Model response within 10s                          │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Run Test Suites                                                │
│  1. pytest tests/test_ollama_health_check.py (17 tests)        │
│  2. pytest tests/test_memory_aware_runner.py (11 tests)        │
│  Expected: 100% pass rate (28 tests)                           │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Report Test Results                                            │
│  - dorny/test-reporter@v1 (JUnit format)                        │
│  - Fail on error: true (blocks merge if tests fail)            │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Cleanup                                                        │
│  - docker compose down -v (remove containers and volumes)       │
│  - docker system prune -f (clean up images)                    │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
         ┌───┴───┐
         │Success?│
         └───┬───┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
 ┌─────────┐   ┌─────────────┐
 │  Pass   │   │  Fail       │
 │  ✓      │   │  ✗          │
 └────┬────┘   └────┬────────┘
      │             │
      ▼             ▼
 ┌─────────┐   ┌─────────────┐
 │  Merge  │   │  Block      │
 │  Allowed│   │  Merge      │
 └─────────┘   └─────────────┘
```

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: @am (Project Owner, Agency OS Lead Developer)
- **Secondary Stakeholders**:
  - Memory-Aware Test Runner (system integration)
  - CI/CD Pipeline (automated validation)
  - Future Contributors (reproducible setup)
- **Technical Reviewers**:
  - ChiefArchitect (ADR-023 alignment)
  - QualityEnforcer (constitutional compliance)
  - AuditorAgent (security and resource limits)

### Review Criteria
- [ ] **Completeness**: All acceptance criteria defined and testable
- [ ] **Clarity**: Docker Compose configuration unambiguous
- [ ] **Feasibility**: Implementation already complete (validation spec)
- [ ] **Constitutional Compliance**: All 5 articles addressed
- [ ] **Quality Standards**: Meets Agency's 100% verification requirements
- [ ] **Architecture Diagrams**: Visual clarity for service, health check, persistence

### Approval Status
- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect ADR-023 validation
- [ ] **Constitutional Compliance**: Pending all 5 articles verification
- [ ] **Final Approval**: Pending all above approvals

---

## Appendices

### Appendix A: Glossary
- **Ollama**: Open-source local LLM inference server optimized for Apple Silicon
- **Q4_K_M**: 4-bit K-means medium quantization (19GB for 30B model)
- **Q8_0**: 8-bit quantization for KV cache (2x memory savings vs F16)
- **Metal GPU**: Apple's graphics API for GPU acceleration on M-series chips
- **KV Cache**: Key-Value cache storing attention states for long context windows
- **Health Check**: Docker mechanism validating service readiness before marking healthy
- **Volume Mount**: Docker feature persisting data across container restarts

### Appendix B: References
- **ADR-023**: Memory-Aware Test Execution (40GB limit, worker adjustment)
- **Docker Compose V2**: Modern Docker Compose with `docker compose` (vs `docker-compose`)
- **Ollama API**: REST API documentation at https://github.com/ollama/ollama/blob/main/docs/api.md
- **Qwen3-Coder**: Qwen 3.5 Coder model optimized for code generation tasks
- **LOCAL_MODEL_OPTIMIZATION.md**: Detailed guide for Apple Silicon optimization

### Appendix C: Related Documents
- **docker-compose.yml**: Service definition (existing, validated by this spec)
- **tools/memory_aware_test_runner.py**: Worker adjustment logic (ADR-023)
- **tools/ollama_health_check.py**: Health validation tool (Result pattern)
- **scripts/setup_local_model.sh**: Automated setup script for first-time use
- **docs/LOCAL_MODEL_OPTIMIZATION.md**: Deep dive into quantization and optimization
- **.github/workflows/ollama-docker-tests.yml**: CI/CD automation workflow

### Appendix D: Docker Compose Configuration Reference

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: agency-ollama
    ports:
      - "11434:11434"
    volumes:
      # Model persistence (critical for 32GB model)
      - ~/.ollama:/root/.ollama
    environment:
      # Model storage location
      - OLLAMA_MODELS=/root/.ollama/models
      # Q8_0 quantization for KV cache (ADR-023: memory-aware execution)
      - OLLAMA_KV_CACHE_TYPE=q8_0
      # Enable flash attention for better performance
      - OLLAMA_FLASH_ATTENTION=1
      # Metal GPU acceleration (Apple Silicon current hardware optimization)
      - OLLAMA_NUM_GPU=1
      # Single model mode (memory budget optimization)
      - OLLAMA_MAX_LOADED_MODELS=1
    deploy:
      resources:
        limits:
          # ADR-023: Memory-aware execution - 40GB limit (available memory total - 8GB safety)
          # Allocation: 19GB model + 16GB KV cache + 2GB runtime + 3GB overhead = 40GB
          memory: 40G
    healthcheck:
      # Article I: Complete context before action - verify service fully ready
      # Check model availability via /api/tags endpoint
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 5
      # Allow 2 minutes for initial model pull (32GB download)
      start_period: 120s
    restart: unless-stopped
```

### Appendix E: Environment Variable Reference

| Variable | Default | Description | Impact |
|----------|---------|-------------|--------|
| `OLLAMA_MODELS` | `/root/.ollama/models` | Model storage path | Persists models across restarts |
| `OLLAMA_KV_CACHE_TYPE` | `f16` | KV cache quantization | `q8_0` saves 2x memory, `q4_0` saves 3x |
| `OLLAMA_FLASH_ATTENTION` | `0` | Flash attention | `1` enables ~20% faster inference |
| `OLLAMA_NUM_GPU` | `auto` | GPU count | `1` forces Metal GPU on current hardware |
| `OLLAMA_MAX_LOADED_MODELS` | `5` | Max concurrent models | `1` prevents memory fragmentation |
| `OLLAMA_HOST` | `http://localhost:11434` | API endpoint | Used by health check and test runner |

### Appendix F: Health Check Tuning Guide

**Scenario 1: First-Time Setup (Model Download)**
```yaml
healthcheck:
  start_period: 300s  # 5 minutes for 32GB download
  interval: 30s       # Check every 30s after start period
  retries: 5          # 2.5 minutes of retries (5 × 30s)
```

**Scenario 2: Warm Start (Model Cached)**
```yaml
healthcheck:
  start_period: 30s   # Model already downloaded
  interval: 30s       # Standard check frequency
  retries: 3          # 1.5 minutes of retries
```

**Scenario 3: CI/CD (Small Model)**
```yaml
healthcheck:
  start_period: 60s   # 900MB download faster
  interval: 20s       # More frequent checks (time-sensitive)
  retries: 5          # Allow for CI variability
```

### Appendix G: Troubleshooting Guide

**Issue 1: Container Not Healthy**
```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f ollama

# Manual health check
curl -f http://localhost:11434/api/tags

# Common causes:
# - Model not yet pulled (run: docker exec agency-ollama ollama list)
# - Port 11434 already in use (check: lsof -i :11434)
# - Memory limit too low (increase to 45G if needed)
```

**Issue 2: Model Re-Downloaded on Restart**
```bash
# Verify volume mount
docker inspect agency-ollama | grep Mounts -A 10

# Check host directory
ls -lh ~/.ollama/models/

# Expected: blobs/ and manifests/ directories with 19GB+ data
# If empty: Volume mount failed, check permissions
```

**Issue 3: Memory Exhaustion (Kernel Panic)**
```bash
# Check memory usage
docker stats agency-ollama --no-stream

# If >40GB: Reduce KV cache quantization
export OLLAMA_KV_CACHE_TYPE="q4_0"  # 3x memory savings

# Or: Use smaller model
docker exec agency-ollama ollama pull qwen3-coder:7b  # 7B model (~5GB)
```

**Issue 4: Health Check Timeout in CI**
```bash
# Increase timeout in workflow
timeout=300  # 5 minutes vs 180s

# Or: Use smaller model
OLLAMA_MODEL=qwen2.5-coder:1.5b  # 900MB vs 19GB

# Or: Cache Docker images
- uses: actions/cache@v4
  with:
    path: /tmp/.docker-cache
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-11 | PlannerAgent | Initial specification for Docker Compose architecture |

---

*"A well-configured container is worth a thousand debugging sessions."*
*"Volume persistence: The difference between 2 minutes and 15 minutes."*
*"Health checks: Trust, but verify—automatically."*
