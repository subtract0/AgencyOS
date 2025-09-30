# Trinity Protocol - Agent Prompts

Production-ready system prompts for Trinity Protocol agents. Maximum function, minimum mass.

---

## Production Prompts (Use These)

### 👁️ WITNESS
**File**: `WITNESS.md` (287 lines, 8.6KB)  
**Role**: Perception - AUDITLEARN  
**Model**: `qwen2.5-coder:7b-q3` (local, via Ollama)  
**Function**: Stateless signal intelligence - detects patterns from telemetry/context

**Core Loop**: LISTEN → CLASSIFY → VALIDATE → ENRICH → SELF-VERIFY → PUBLISH → PERSIST → RESET

**Key Features**:
- Mathematical confidence scoring: `base + Σ(keyword × weight)`
- Self-verification against JSON schema (Article II)
- Firestore persistence for cross-session learning (Article IV)
- Adaptive thresholds (0.7 → 0.6 for critical patterns)
- Pattern types: failure, opportunity, user_intent

---

### 🏛️ ARCHITECT
**File**: `ARCHITECT.md` (390 lines, 12KB)  
**Role**: Cognition - PLAN  
**Model**: `codestral-22b` (local) + `gpt-5`/`claude-4.1` (escalation)  
**Function**: Strategic orchestrator - strategizes, decomposes, routes

**Core Loop**: LISTEN → TRIAGE → GATHER CONTEXT → SELECT ENGINE → FORMULATE STRATEGY → EXTERNALIZE → GENERATE TASK GRAPH → SELF-VERIFY → PUBLISH → RESET

**Key Features**:
- Hybrid reasoning: local for routine, API for complex/critical
- Complexity assessment and routing logic
- Spec/ADR generation for complex tasks (Article V)
- Historical pattern queries from Firestore
- Task graph with DAG (directed acyclic graph)

---

### ⚙️ EXECUTOR
**File**: `EXECUTOR.md` (265 lines, 9.1KB)  
**Role**: Action - EXECUTE  
**Model**: `claude-sonnet-4.5`  
**Function**: Meta-orchestrator - delegates, verifies, reports

**Core Loop**: LISTEN → DECONSTRUCT → PLAN & EXTERNALIZE → ORCHESTRATE (PARALLEL) → HANDLE FAILURES → DELEGATE MERGE → ABSOLUTE VERIFICATION → REPORT → RESET

**Key Features**:
- Parallel execution (CodeWriter + TestArchitect concurrent)
- State externalization (`/tmp/executor_plans/<task_id>_plan.md`)
- 100% test verification before success (Article II)
- Sub-agent roster: CodeWriter, TestArchitect, ReleaseManager, etc.
- Constitutional enforcement (Articles II, III, V)

---

## Trinity Architecture

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│ WITNESS  │─────>│ARCHITECT │─────>│ EXECUTOR │
│          │      │          │      │          │
│ Sees     │      │Understands│      │   Does   │
│ Detects  │      │ Strategize│      │ Verifies │
│ Learns   │      │ Decomposes│      │  Reports │
└────┬─────┘      └──────────┘      └────┬─────┘
     │                                     │
     │         ┌────────────┐             │
     └────────>│Message Bus │<────────────┘
               │(Telemetry) │
               └────────────┘
```

**Message Flow**:
1. WITNESS monitors `telemetry_stream` + `personal_context_stream`
2. Publishes patterns to `improvement_queue`
3. ARCHITECT consumes `improvement_queue`, creates tasks
4. Publishes to `execution_queue`
5. EXECUTOR consumes `execution_queue`, delegates work
6. Publishes outcomes to `telemetry_stream`
7. Loop closes: WITNESS learns from outcomes

---

## Constitutional Compliance

All agents bound by `constitution.md`:

- **Article I**: Complete Context Before Action
- **Article II**: 100% Verification and Stability
- **Article III**: Automated Merge Enforcement
- **Article IV**: Continuous Learning (Firestore)
- **Article V**: Spec-Driven Development

---

## Implementation Status

| Agent | Prompt | Implementation | Phase |
|-------|--------|----------------|-------|
| WITNESS | ✅ Ready | 🚧 In Progress | Weeks 1-4 |
| ARCHITECT | ✅ Ready | 📋 Not Started | Weeks 5-6 |
| EXECUTOR | ✅ Ready | 📋 Not Started | Weeks 5-6 |

---

## Archive Files

Original verbose versions preserved for reference:
- `gemini_auditlearn_prompt.md` (428 lines, 17KB)
- `gemini_executor_prompt.md` (192 lines, 9.1KB)

**When to use archives**: Training, understanding rationale, historical reference

**Default**: Always use production prompts (`WITNESS.md`, `ARCHITECT.md`, `EXECUTOR.md`)

---

## Related Docs

- `../trinity_protocol_implementation.md` - 6-week implementation plan
- `../../constitution.md` - Governance framework
- `../adr/ADR-004-continuous-learning-system.md` - Learning architecture
- `VERSIONS.md` - Version comparison
- MCP Ref: `688cf28d-e69c-4624-b7cb-0725f36f9518`

---

## Quick Start

```bash
# WITNESS (local model)
ollama pull qwen2.5-coder:7b-q3
python -m trinity_protocol.witness_agent

# ARCHITECT (hybrid local/cloud)
ollama pull codestral-22b
python -m trinity_protocol.architect_agent

# EXECUTOR (cloud model)
# Set ANTHROPIC_API_KEY in .env
python -m trinity_protocol.executor_agent
```

---

Last updated: 2025-09-30
