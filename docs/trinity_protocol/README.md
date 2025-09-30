# Trinity Protocol - Agent Prompts

Production-ready system prompts for Trinity Protocol agents. SpaceX style: maximum function, minimum mass.

---

## Production Prompts (Use These)

### 🔍 AUDITLEARN
**File**: `auditlearn_prompt.md` (287 lines, 8.6KB)  
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

### 🚀 EXECUTOR
**File**: `executor_prompt.md` (265 lines, 9.1KB)  
**Model**: `claude-sonnet-4.5`  
**Function**: Meta-orchestrator - delegates to sub-agents, verifies, reports

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
┌──────────────┐      ┌──────────────┐      ┌──────────┐
│ AUDITLEARN   │─────>│    PLAN      │─────>│ EXECUTE  │
│              │      │              │      │          │
│ • Monitor    │      │ • Strategize │      │ • Route  │
│ • Detect     │      │ • Prioritize │      │ • Run    │
│ • Learn      │      │ • Create     │      │ • Verify │
└──────┬───────┘      └──────────────┘      └────┬─────┘
       │                                           │
       │          ┌──────────────────┐            │
       └─────────>│  Message Bus     │<───────────┘
                  │  (Telemetry)     │
                  └──────────────────┘
```

**Message Flow**:
1. AUDITLEARN monitors `telemetry_stream` + `personal_context_stream`
2. Publishes patterns to `improvement_queue`
3. PLAN consumes `improvement_queue`, creates tasks
4. Publishes to `execution_queue`
5. EXECUTE consumes `execution_queue`, delegates work
6. Publishes outcomes to `telemetry_stream`
7. Loop closes: AUDITLEARN learns from outcomes

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
| AUDITLEARN | ✅ Ready | 🚧 In Progress | Weeks 1-4 |
| PLAN | 📋 Pending | 📋 Not Started | Weeks 5-6 |
| EXECUTE | ✅ Ready | 📋 Not Started | Weeks 5-6 |

---

## Archive Files

Original verbose versions preserved for reference:
- `gemini_auditlearn_prompt.md` (428 lines, 17KB) - Full documentation
- `gemini_executor_prompt.md` (192 lines, 9.1KB) - Original with philosophy

**When to use archives**: Training, understanding rationale, historical reference

**Default**: Always use the production prompts (`auditlearn_prompt.md`, `executor_prompt.md`)

---

## Related Docs

- `../trinity_protocol_implementation.md` - 6-week implementation plan
- `../../constitution.md` - Governance framework
- `../adr/ADR-004-continuous-learning-system.md` - Learning architecture
- `VERSIONS.md` - Version comparison and efficiency metrics
- MCP Ref: `688cf28d-e69c-4624-b7cb-0725f36f9518`

---

## Quick Start

```bash
# AUDITLEARN (local model)
ollama pull qwen2.5-coder:7b-q3
python -m trinity_protocol.auditlearn_agent

# EXECUTE (cloud model)
# Set ANTHROPIC_API_KEY in .env
python -m trinity_protocol.execute_agent
```

---

Last updated: 2025-09-30
