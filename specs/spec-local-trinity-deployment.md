# Specification: Local Trinity Loop Deployment for M4 MacBook

**Date**: 2025-10-04
**Status**: Draft
**Author**: Constitutional Agent
**Context**: Deploy self-contained 3-LLM Trinity loop on 48GB M4 MacBook

---

## Goals

1. **Self-Contained Package**: Single installation script that deploys entire Trinity loop locally
2. **3-Model Architecture**: WITNESS (1.5B), ARCHITECT (7B), EXECUTOR (22B) running on Ollama
3. **Recursive Sub-Execution**: Same models handle sub-agent work (CODE_WRITER, TEST_ARCHITECT, etc.)
4. **Zero Cloud Dependency**: 100% offline operation after initial setup
5. **48GB Memory Optimized**: Efficient memory management for M4 MacBook constraints

## Non-Goals

- Cloud hybrid mode (pure local operation)
- Multi-machine distributed execution
- GPU acceleration (M4 Neural Engine sufficient)
- Audio/ambient experimental features (core Trinity only)

## Personas

### Primary User: Developer with M4 MacBook
- **Need**: Autonomous coding assistant running 24/7 without API costs
- **Constraint**: 48GB unified memory, no cloud connectivity desired
- **Workflow**: Start Trinity loop, let it observe/improve codebase autonomously

### Secondary User: AI Researcher
- **Need**: Study multi-agent coordination patterns locally
- **Constraint**: Privacy-sensitive code, cannot use cloud APIs
- **Workflow**: Analyze Trinity decision-making through local telemetry

## Architecture

### 3-Model Trinity Hierarchy

```
┌─────────────────────────────────────────────────────┐
│  WITNESS Agent (qwen2.5-coder:1.5b)                 │
│  - Pattern detection from telemetry                 │
│  - <200ms latency required                          │
│  - Memory: ~2GB                                      │
└──────────────────┬──────────────────────────────────┘
                   │ Signal
                   ▼
┌─────────────────────────────────────────────────────┐
│  ARCHITECT Agent (qwen2.5-coder:7b)                 │
│  - Spec/plan generation from signals                │
│  - Strategic decision-making                        │
│  - Memory: ~8GB                                      │
└──────────────────┬──────────────────────────────────┘
                   │ Task
                   ▼
┌─────────────────────────────────────────────────────┐
│  EXECUTOR Agent (codestral-22b)                     │
│  - Task execution via 6 sub-agents                  │
│  - Code generation, test writing, review            │
│  - Memory: ~24GB                                     │
│  │                                                   │
│  ├─► CODE_WRITER (codestral-22b - same)            │
│  ├─► TEST_ARCHITECT (codestral-22b - same)         │
│  ├─► TOOL_DEVELOPER (codestral-22b - same)         │
│  ├─► IMMUNITY_ENFORCER (qwen2.5-coder:7b - ARCH)   │
│  ├─► RELEASE_MANAGER (qwen2.5-coder:7b - ARCH)     │
│  └─► TASK_SUMMARIZER (qwen2.5-coder:1.5b - WIT)    │
└─────────────────────────────────────────────────────┘

Total Memory Budget: ~34GB (14GB headroom for OS + apps)
```

### Model Selection Rationale

| Agent | Model | Size | Reason |
|-------|-------|------|--------|
| WITNESS | qwen2.5-coder:1.5b | 2GB | Fast detection, low latency |
| ARCHITECT | qwen2.5-coder:7b | 8GB | Strategic planning, spec quality |
| EXECUTOR | codestral-22b | 24GB | Code generation quality critical |
| Sub-Agents | Reuse above | 0GB* | No new memory allocation |

*Sub-agents reuse parent model contexts via Ollama's context management

### Memory Management Strategy

**Ollama Context Caching**:
- WITNESS: 2048 token context (patterns only)
- ARCHITECT: 4096 token context (specs/plans)
- EXECUTOR: 8192 token context (full codebase awareness)

**Sequential Execution** (not parallel):
1. WITNESS runs → detects pattern → unloads
2. ARCHITECT loads → creates spec → unloads
3. EXECUTOR loads → executes task → unloads

**Peak Memory**: 24GB (EXECUTOR only) + 10GB OS = 34GB total

## Technical Requirements

### Ollama Model Installation

```bash
# Required models (auto-downloaded by installer)
ollama pull qwen2.5-coder:1.5b    # ~1.0GB download
ollama pull qwen2.5-coder:7b      # ~4.7GB download
ollama pull codestral:22b         # ~13GB download

Total Download: ~19GB (one-time)
Total Disk: ~34GB (with quantization artifacts)
```

### Python Dependencies

```python
# Core Trinity dependencies
httpx>=0.27.0          # Ollama API client
pydantic>=2.0.0        # Data models
sqlalchemy>=2.0.0      # PersistentStore backend
```

**No OpenAI/Anthropic SDKs required** - pure local operation.

### System Requirements

- **OS**: macOS 14+ (M4 optimized)
- **RAM**: 48GB unified memory
- **Disk**: 50GB free (models + logs)
- **CPU**: M4 chip (Neural Engine utilization)
- **Network**: Required for initial setup only

## Deployment Package Structure

```
trinity-local-m4/
├── install.sh                    # One-command installer
├── requirements.txt              # Python deps
├── trinity_config.yaml           # Model/memory config
├── trinity_protocol/             # Core modules (from Agency)
│   ├── core/
│   │   ├── witness.py
│   │   ├── architect.py
│   │   ├── executor.py
│   │   └── orchestrator.py
│   └── models/
├── shared/                       # Shared infrastructure
│   ├── local_model_server.py    # Ollama adapter
│   ├── message_bus.py
│   ├── persistent_store.py
│   └── cost_tracker.py          # Track compute time, not $
├── start_trinity.sh              # Launch script
├── stop_trinity.sh               # Graceful shutdown
├── monitor_trinity.sh            # Real-time status
└── README.md                     # Quick start guide
```

## Installation Flow

```bash
# One-command deployment
curl -fsSL https://raw.githubusercontent.com/subtract0/AgencyOS/main/deploy/trinity-local-m4/install.sh | bash

# Or manual
git clone https://github.com/subtract0/AgencyOS.git
cd AgencyOS/deploy/trinity-local-m4
./install.sh
```

### Install Script Steps

1. **Verify System**:
   - Check macOS version (14+)
   - Check available RAM (48GB)
   - Check disk space (50GB+)
   - Verify M4 chip

2. **Install Ollama** (if not present):
   - Download Ollama installer
   - Install to /usr/local/bin
   - Start Ollama service

3. **Pull Models**:
   - `ollama pull qwen2.5-coder:1.5b`
   - `ollama pull qwen2.5-coder:7b`
   - `ollama pull codestral:22b`
   - Verify model integrity

4. **Setup Python Environment**:
   - Create virtualenv `.venv`
   - Install Trinity dependencies
   - Verify imports

5. **Initialize Trinity**:
   - Create SQLite databases (message_bus.db, patterns.db)
   - Initialize telemetry logging
   - Create empty session state

6. **Validate Installation**:
   - Run health check: `./monitor_trinity.sh --check`
   - Expected: All 3 models available, 0 errors

## Runtime Configuration

**trinity_config.yaml**:

```yaml
# Trinity Local Configuration for M4 MacBook (48GB)

models:
  witness:
    name: "qwen2.5-coder:1.5b"
    context_length: 2048
    temperature: 0.3
    timeout: 30  # Fast detection required

  architect:
    name: "qwen2.5-coder:7b"
    context_length: 4096
    temperature: 0.5
    timeout: 120

  executor:
    name: "codestral:22b"
    context_length: 8192
    temperature: 0.3
    timeout: 300

  sub_agents:
    code_writer: "codestral:22b"       # Reuse EXECUTOR
    test_architect: "codestral:22b"    # Reuse EXECUTOR
    tool_developer: "codestral:22b"    # Reuse EXECUTOR
    immunity_enforcer: "qwen2.5-coder:7b"  # Reuse ARCHITECT
    release_manager: "qwen2.5-coder:7b"    # Reuse ARCHITECT
    task_summarizer: "qwen2.5-coder:1.5b"  # Reuse WITNESS

memory:
  max_total_mb: 34000  # Leave 14GB for OS
  ollama_num_ctx: 8192
  sequential_execution: true  # Never load multiple models

telemetry:
  log_dir: "logs/trinity_local/"
  enable_metrics: true
  enable_cost_tracker: true  # Track compute time, not API $

constitutional:
  enable_learning: true  # VectorStore required (Article IV)
  enforce_tests: true    # 100% test compliance (Article II)
  max_autonomous_commits: 10  # Safety limit per cycle
```

## Acceptance Criteria

### AC-1: One-Command Installation
- **Given**: Fresh M4 MacBook with 48GB RAM
- **When**: User runs `curl ... | bash`
- **Then**:
  - All 3 models downloaded and verified
  - Python environment configured
  - Trinity starts successfully
  - Status dashboard accessible

### AC-2: 100% Local Operation
- **Given**: Trinity installed and running
- **When**: Network disconnected
- **Then**:
  - WITNESS detects patterns normally
  - ARCHITECT creates specs normally
  - EXECUTOR executes tasks normally
  - No cloud API calls attempted

### AC-3: Memory Budget Compliance
- **Given**: Trinity running full cycle
- **When**: Monitoring peak memory usage
- **Then**:
  - Peak ≤ 34GB (leaves 14GB headroom)
  - No OOM errors
  - Sequential model loading observed

### AC-4: Recursive Sub-Execution
- **Given**: EXECUTOR receives complex task
- **When**: Task delegated to CODE_WRITER sub-agent
- **Then**:
  - CODE_WRITER uses codestral:22b (same as EXECUTOR)
  - No new model loaded (context reuse)
  - Sub-agent completes work successfully

### AC-5: Constitutional Compliance
- **Given**: Trinity cycle running
- **When**: Code changes generated
- **Then**:
  - Tests written first (Article V)
  - 100% test pass before commit (Article II)
  - VectorStore learning active (Article IV)
  - Complete context gathered (Article I)

### AC-6: Performance Targets
- **Given**: Telemetry stream active
- **When**: WITNESS processes events
- **Then**:
  - Pattern detection <200ms (per event)
  - ARCHITECT spec generation <2 minutes
  - EXECUTOR task execution <10 minutes (varies by complexity)

## Testing Strategy

### Unit Tests
- Ollama client connectivity
- Model loading/unloading
- Memory budget enforcement
- Config file parsing

### Integration Tests
- WITNESS → ARCHITECT signal flow
- ARCHITECT → EXECUTOR task delegation
- EXECUTOR → Sub-agent recursion
- End-to-end Trinity cycle

### System Tests
- 24-hour continuous operation (stability)
- Network disconnect handling (offline mode)
- Memory leak detection (long-running)
- Model context caching efficiency

### Performance Benchmarks
- Pattern detection latency (target: <200ms)
- Spec generation time (target: <2 min)
- Task execution time (varies, baseline)
- Memory overhead (target: <34GB peak)

## Risks and Mitigations

### Risk 1: Model Download Failures
- **Impact**: Installation fails, user blocked
- **Probability**: Medium (network issues, Ollama registry downtime)
- **Mitigation**:
  - Retry logic with exponential backoff
  - Provide manual download instructions
  - Verify checksums after download

### Risk 2: Memory Exhaustion
- **Impact**: System freeze, kernel panic on M4
- **Probability**: Low (with sequential execution)
- **Mitigation**:
  - Hard limit: Max 34GB total allocation
  - Monitor actual usage in real-time
  - Graceful degradation (unload EXECUTOR if low memory)

### Risk 3: Model Quality Insufficient
- **Impact**: Poor code generation, failing tests
- **Probability**: Medium (local models vs GPT-5)
- **Mitigation**:
  - Hybrid doctrine: Allow cloud fallback for critical tasks
  - Constitutional enforcement prevents merging bad code
  - User can override model selection in config

### Risk 4: Ollama Service Crashes
- **Impact**: Trinity halts mid-cycle
- **Probability**: Low (Ollama is stable)
- **Mitigation**:
  - Watchdog script restarts Ollama automatically
  - Trinity resumes from last checkpoint
  - Telemetry logs capture crash context

## Future Enhancements

### Phase 2: Hybrid Intelligence
- Allow cloud escalation for critical tasks (user opt-in)
- Model router: Local first, cloud for high-stakes decisions
- Cost-benefit analysis: When to use GPT-5 vs local

### Phase 3: Model Fine-Tuning
- Collect successful code generations
- Fine-tune qwen2.5-coder:7b on user's codebase style
- Personalized ARCHITECT for user-specific patterns

### Phase 4: Multi-MacBook Cluster
- Distribute WITNESS/ARCHITECT/EXECUTOR across 3 MacBooks
- Shared message bus via network
- Load balancing for parallel task execution

---

## Implementation Plan Reference

See: `plans/plan-local-trinity-deployment.md` (to be generated by Planner)

---

**Status**: Draft
**Next Step**: Planner creates implementation plan
**Review**: ChiefArchitect approval required before implementation
