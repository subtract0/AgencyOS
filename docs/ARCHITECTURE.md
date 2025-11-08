# Architecture Overview - AgencyOS

**Last Updated**: 2025-01-30
**Status**: Honest technical assessment of current implementation

---

## System Overview

AgencyOS is a multi-agent orchestration platform built on the `agency_swarm` framework. It coordinates 10 specialized agents to perform software development tasks.

**Key Insight**: Agents are currently **factory functions wrapping Claude API**, not fully autonomous local reasoning engines.

---

## Core Components

### 1. Agent Layer (10 Specialized Agents)

Each agent is a ~150-300 LOC factory function in `{agent_name}_agent/agent.py`:

```python
def create_{agent}_agent(context: AgentContext, model: str) -> Agent:
    """Factory that returns agency_swarm.Agent configured for specific role."""
    return Agent(
        name="{Agent}Agent",
        instructions="...",  # Role definition
        tools=[...],         # Tool assignments
        model=model          # Claude API model
    )
```

**Current Implementation**:
- `agency_swarm.Agent` makes direct Claude API calls
- No local reasoning - all intelligence from Claude
- Agents communicate via `agency_swarm` built-in mechanisms

**10 Agents**:
1. **PlannerAgent** - `planner_agent/agent.py` - Spec → Plan conversion
2. **CodingAgent** - `coding_agent/agent.py` - Feature implementation
3. **TestGeneratorAgent** - `test_generator_agent/agent.py` - Test creation
4. **QualityEnforcerAgent** - `quality_enforcer_agent/agent.py` - Constitutional compliance
5. **AuditorAgent** - `auditor_agent/agent.py` - AST-based code analysis (most substantive local logic)
6. **ChiefArchitectAgent** - `chief_architect_agent/agent.py` - ADR creation
7. **LearningAgent** - `learning_agent/agent.py` - Pattern extraction
8. **MergerAgent** - `merger_agent/agent.py` - Git operations
9. **ToolsmithAgent** - `toolsmith_agent/agent.py` - Tool development
10. **WorkCompletionSummaryAgent** - `work_completion_summary_agent/agent.py` - Task summaries

---

### 2. Shared Infrastructure (`shared/`)

**Core Modules** (47 files):

- **`agent_context.py`** (302 LOC) - AgentContext class, memory API
- **`model_policy.py`** (180 LOC) - Per-agent model selection with env overrides
- **`type_definitions/`** - Result<T,E> pattern, JSONValue types
- **`models/`** - Pydantic models (memory, learning, telemetry, orchestrator)
- **`utils.py`** - Retry controllers, system hooks

**Key Pattern**:
```python
from shared.agent_context import AgentContext

context = create_agent_context(session_id="feature_dev")
context.store_memory("key", content, tags=["pattern"])
results = context.search_memories(["pattern"])
```

---

### 3. Memory Systems (`agency_memory/`)

**Three-Tier Architecture**:

1. **Anthropic Memory Tool** - File-based persistence (`~/.agency/memories/`)
   - Cross-conversation knowledge
   - Manual file management
   - Located: `tools/anthropic_memory_tool.py`

2. **VectorStore** - Semantic search with embeddings
   - `agency_memory/vector_store.py` (5k LOC)
   - Institutional learning
   - Auto-extraction from sessions
   - Located: `agency_memory/`

3. **Session Context** - Temporary working memory
   - `AgentContext.metadata` dictionary
   - Session-scoped only
   - Located: `shared/agent_context.py`

---

### 4. Tool Ecosystem (`tools/`)

**56 Production Tools** organized by category:

```
tools/
├── File Ops (7):        read.py, write.py, edit.py, multi_edit.py, glob.py, grep.py, ls.py
├── Git Ops (5):         git.py, git_unified.py, git_workflow.py, undo_snapshot.py
├── Execution (1):       bash.py
├── Planning (2):        todo_write.py, exit_plan_mode.py
├── Agent Comms (2):     context_handoff.py, handoff_context_read.py
├── Constitutional (4):  constitution_check.py, analyze_type_patterns.py, fix_dict_any.py
├── Quality (3):         auto_fix_nonetype.py, apply_and_verify_patch.py
├── Memory (2):          anthropic_memory_tool.py, learning_dashboard.py
├── Monitoring (3):      heartbeat_thread.py, performance_profiling.py
└── [Additional 27]:     Scattered across subdirectories
```

**Tool Design Pattern**:
- Each tool is a Python function with `@tool` decorator
- Tools passed to agents via `agency_swarm` framework
- No sandboxing (agents have full system access)

---

### 5. Constitutional Framework (`constitution.md`)

**7 Articles** enforced through:

- **Pre-commit hooks** - Block direct main commits
- **Test requirements** - 100% pass rate mandate
- **Quality checkers** - `tools/constitutional/` validators
- **Agent instructions** - Baked into agent prompts

**Key Articles**:
- I: Complete Context Before Action
- II: 100% Verification (tests must pass)
- III: Automated Local Enforcement
- IV: Continuous Learning (VectorStore)
- V: Spec-Driven Development
- VI: TDD (Red-Green-Refactor)
- VII: Value-First Testing

---

### 6. Orchestration (`agency.py`)

**Main Entry Point** (250 LOC):

```python
# agency.py - Simplified structure
def main():
    context = create_agent_context()
    agents = {
        "planner": create_planner_agent(context),
        "coder": create_coding_agent(context),
        # ... 8 more agents
    }

    # agency_swarm handles communication
    agency_swarm.run_agent_workflow(agents)
```

**Current Limitation**: Orchestration logic is minimal - most coordination happens via `agency_swarm` framework internals.

---

## Data Flow

### Typical Development Workflow

```
User Request (natural language)
    ↓
ChiefArchitect (strategic planning)
    ↓
Planner (spec.md → plan.md)
    ↓
CodingAgent (implementation) ←→ QualityEnforcer (compliance)
    ↓
TestGenerator (test creation)
    ↓
Auditor (quality analysis)
    ↓
Merger (git commit/PR)
    ↓
Summary (task completion report)
```

**All agent-to-agent communication** currently happens via `agency_swarm` built-in mechanisms, not custom orchestration.

---

## Dependency Chain

### External Dependencies

**Critical**:
- `anthropic>=0.42.0` - Claude API (required for all agents)
- `agency-swarm>=0.2.0` - Agent framework (⚠️ Python 3.13 threading bugs)
- `pydantic>=2.0` - Data validation
- `openai>=1.0` - Model routing

**Infrastructure**:
- `chromadb>=0.4.0` - VectorStore backend
- `scikit-learn>=1.0.0` - ML routing (embeddings, classification)

**Testing**:
- `pytest>=7.0` - Test framework
- `pytest-xdist` - Parallel execution
- `uv` - Environment management (required for test runner)

### Python Version Constraint

- **Recommended**: Python 3.12
- **Supported**: Python 3.13 (⚠️ **segfaults** with `agency-swarm` due to threading bugs)
- **Test Runner**: **MUST** use `python run_tests.py` (NOT direct pytest)

---

## What's Missing

### Local-First Execution

**Claimed**: "96% cost reduction via local Ollama models"
**Reality**:
- All agents call Claude API
- Ollama integration is documented (`docs/LOCAL_MODEL_OPTIMIZATION.md`) but not wired to agents
- `tools/ollama_health_check.py` exists but only checks health, doesn't execute
- No agent actually uses local models for reasoning

**To Achieve Local-First**:
1. Decompose `agency_swarm` dependency
2. Implement local LLM inference wrapper
3. Wire agents to use Ollama/local models
4. Add model router (local → cloud escalation)

---

### Autonomous Orchestration

**Claimed**: "Fully autonomous multi-agent orchestration"
**Reality**:
- Orchestration delegated to `agency_swarm` framework
- No custom task graph execution
- No visible agent-to-agent communication protocol
- PrimeA orchestrator (`/primeA` command) exists but execution unclear

**To Achieve Autonomy**:
1. Build custom orchestration engine
2. Implement task graph DSL
3. Add agent-to-agent messaging protocol
4. Create autonomous decision-making loop

---

## Test Infrastructure

### Test Suite

- **5,822 tests passing** (164 skipped)
- **100% pass rate** (with correct test runner)
- **3:51 execution time** (full suite)

### Test Runner Architecture

```bash
run_tests.py
    ↓
uv run pytest
    ↓
pytest-xdist (parallel execution)
    ↓
Memory-aware worker allocation
```

**Critical**: Direct `pytest` execution fails (Python 3.13 + agency-swarm segfaults). Use `python run_tests.py`.

---

## Known Technical Debt

1. **Agent Stubs**: Agents are thin wrappers, not autonomous
2. **Cloud Dependency**: 100% reliant on Claude API
3. **Orchestration**: Delegated to external framework
4. **Type Safety**: 107 `Dict[Any, ...]` violations remaining
5. **Python 3.13**: Threading bugs in agency-swarm
6. **CI/CD**: GitHub Actions blocked by billing

---

## References

- **Agent Definitions**: `.claude/agents/*.md`
- **Tool Reference**: `tools/README.md` (if exists) or `tools/*/`
- **ADRs**: `docs/adr/ADR-INDEX.md` (47 architectural decisions)
- **Constitution**: `constitution.md` (governance framework)

---

**Next**: See [ROADMAP.md](ROADMAP.md) for evolution from current state to vision.
