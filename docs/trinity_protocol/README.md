# Trinity Protocol - Agent Prompt Specifications

This directory contains the canonical, competition-winning system prompts for the Trinity Protocol agents.

---

## 📚 Files

### 🔍 **AUDITLEARN Agent**
**File**: `gemini_auditlearn_prompt.md` (428 lines, 17KB)  
**Status**: ✅ APPROVED  
**Author**: Gemini (Google DeepMind)  
**Purpose**: Stateless signal intelligence agent - detects patterns from telemetry and user context

**Key Features**:
- 8-step stateless loop (LISTEN → CLASSIFY → VALIDATE → ENRICH → SELF-VERIFY → PUBLISH → PERSIST → RESET)
- Mathematical confidence scoring: `confidence = base + Σ(keyword_matches × weight)`
- Self-verification against JSON schema before publishing (Article II compliance)
- Firestore persistence for cross-session learning (Article IV compliance)
- Local model: `qwen2.5-coder:7b-q3` via Ollama

---

### 🚀 **EXECUTE Agent**
**File**: `gemini_executor_prompt.md` (192 lines, 9.1KB)  
**Status**: ✅ APPROVED  
**Author**: Gemini (Google DeepMind)  
**Purpose**: Meta-orchestrator agent - delegates tasks to specialized sub-agents and verifies outcomes

**Key Features**:
- 6-step execution loop with state externalization (`/tmp/execution_plan.md`)
- Parallel execution groups (CodeWriter + TestArchitect concurrent)
- Constitutional enforcement (Articles II, III, V)
- 100% test verification before merge
- Minimal telemetry reporting

---

### 📋 **Design Decision**
**File**: `AUDITLEARN_DESIGN_DECISION.md` (153 lines, 5.7KB)  
**Purpose**: Documents the selection rationale for Gemini's AUDITLEARN design

**Contents**:
- Competition evaluation (Gemini vs ChatGPT)
- Key innovations and enhancements
- Implementation roadmap (3 phases)
- Critical requirements and success criteria

---

## 🏛️ Trinity Protocol Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     TRINITY PROTOCOL                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │ AUDITLEARN   │─────>│    PLAN      │─────>│ EXECUTE  │  │
│  │              │      │              │      │          │  │
│  │ • Monitor    │      │ • Strategize │      │ • Route  │  │
│  │ • Detect     │      │ • Prioritize │      │ • Run    │  │
│  │ • Learn      │      │ • Create     │      │ • Verify │  │
│  └──────┬───────┘      └──────────────┘      └────┬─────┘  │
│         │                                           │        │
│         │          ┌──────────────────┐            │        │
│         └─────────>│  Message Bus     │<───────────┘        │
│                    │  (Telemetry)     │                     │
│                    └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

**Flow**:
1. **AUDITLEARN** monitors `telemetry_stream` + `personal_context_stream`
2. Detects patterns → publishes to `improvement_queue`
3. **PLAN** subscribes to `improvement_queue` → creates execution tasks
4. Publishes to `execution_queue`
5. **EXECUTE** subscribes to `execution_queue` → delegates to specialized agents
6. Verifies results → publishes outcome to `telemetry_stream`
7. Loop closes: AUDITLEARN learns from execution outcomes

---

## 📜 Constitutional Compliance

All Trinity agents are bound by `constitution.md`:

- **Article I**: Complete Context Before Action
- **Article II**: 100% Verification and Stability
- **Article III**: Automated Merge Enforcement
- **Article IV**: Continuous Learning and Improvement
- **Article V**: Spec-Driven Development

---

## 🔧 Implementation Status

| Agent | Prompt | Implementation | Status |
|-------|--------|----------------|--------|
| **AUDITLEARN** | ✅ Complete | 🚧 In Progress | Phase 1 (Weeks 1-2) |
| **PLAN** | 📋 Pending | 📋 Pending | Phase 2 (Weeks 5-6) |
| **EXECUTE** | ✅ Complete | 📋 Pending | Phase 2 (Weeks 5-6) |

---

## 🔗 Related Documentation

- **Trinity Spec**: `../trinity_protocol_implementation.md` (full 6-week implementation plan)
- **Constitution**: `../../constitution.md` (governance framework)
- **ADR-004**: `../adr/ADR-004-continuous-learning-system.md` (learning architecture)
- **Preflight Checklist**: `../TRINITY_PREFLIGHT_CHECKLIST.md` (pre-deployment validation)

---

## 🎯 Next Steps

1. **Week 1-2**: Implement AUDITLEARN core infrastructure
   - Set up Firestore `trinity_patterns` collection
   - Configure Ollama with Qwen 2.5-Coder 7B
   - Implement 8-step stateless loop

2. **Week 3**: Pattern detection testing
   - Test on real telemetry events
   - Verify Firestore persistence
   - Tune confidence thresholds

3. **Week 4**: Integration
   - Connect to message bus
   - Test end-to-end loop
   - 24-hour continuous operation test

4. **Week 5-6**: PLAN agent development (prompt pending)

---

## 📝 Version History

- **2025-09-30**: Initial prompts approved (AUDITLEARN + EXECUTE)
- **2025-09-30**: AUDITLEARN design decision documented
- **2025-09-30**: Implementation roadmap established

---

*"This is not a prompt. This is a constitution—a core identity from which all actions must flow."* - Gemini
