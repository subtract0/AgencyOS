# Architecture Decision Records (ADR) Index

## Overview
This index catalogs all Architecture Decision Records for the Agency multi-agent system. These ADRs document key architectural decisions and are directly referenced in the Agency Constitution.

## Core Constitutional ADRs

### ADR-001: Complete Context Before Action
**Status:** Ratified (Constitution Article I)
**Date:** 2025-09-22
**Decision:** No action shall be taken without complete contextual understanding.

**Key Requirements:**
- Timeout handling with automatic retries (2x, 3x, up to 10x)
- Test execution must run to completion
- Zero tolerance for broken windows
- Complete context verification before proceeding

---

### ADR-002: 100% Verification and Stability
**Status:** Ratified (Constitution Article II)
**Date:** 2025-09-22
**Decision:** A task is complete ONLY when 100% verified and stable.

**Key Requirements:**
- Main branch maintains 100% test success rate
- No merge without green CI pipeline
- Tests verify real functionality
- "Delete the Fire First" priority

---

### ADR-003: Automated Merge Enforcement
**Status:** Ratified (Constitution Article III)
**Date:** 2025-09-22
**Decision:** Quality standards SHALL be technically enforced, not manually governed.

**Key Requirements:**
- Zero-tolerance policy with no manual overrides
- Multi-layer enforcement (pre-commit, agent validation, CI/CD, branch protection)
- No bypass authority for any human or emergency
- Quality gates are absolute barriers

---

### ADR-004: Continuous Learning and Improvement
**Status:** Ratified (Constitution Article IV)
**Date:** 2025-09-22
**Decision:** The Agency SHALL continuously improve through experiential learning.

**Key Requirements:**
- Automatic learning triggers after successful sessions
- Minimum confidence threshold: 0.6
- Cross-session pattern recognition
- VectorStore integration for knowledge accumulation

---

### ADR-005: Per-Agent Model Policy
**Status:** Active
**Date:** 2025-09-27
**Decision:** Implement centralized per-agent model selection with environment overrides.

**Key Requirements:**
- Safe defaults prioritizing quality-critical agents on GPT-5
- Cost-saving agents can use GPT-5-mini/nano
- Environment variable overrides for flexible configuration
- Planner defaults to o3 model for advanced reasoning

---

## Architectural Principles

### ADR-006: LLM-First Architecture
**Status:** Active
**Date:** 2025-09-23
**Decision:** Delegate complex analysis to LLM intelligence rather than building complex Python systems.

**Rationale:** Leverages GPT-5/o3 capabilities for intelligent decision-making instead of maintaining complex algorithmic implementations.

---

### ADR-007: Spec-Driven Development
**Status:** Active (Constitution Article V)
**Date:** 2025-09-22
**Decision:** All development SHALL follow formal specification and planning processes.

**Key Requirements:**
- New features begin with formal spec.md
- Technical plans generated from approved specs
- TodoWrite integration for task tracking
- Living documents updated during implementation

---

### ADR-008: Strict Typing Requirement
**Status:** Active
**Date:** 2025-09-24
**Decision:** No Dict[str, Any] usage - all data structures must use concrete Pydantic models.

**Rationale:** Type safety prevents runtime errors and improves code maintainability. Dict[str, Any] defeats type checking.

---

### ADR-009: Function Complexity Limits
**Status:** Active
**Date:** 2025-09-24
**Decision:** Keep functions under 50 lines with single, focused purpose.

**Rationale:** Smaller functions are easier to test, understand, and maintain. Complexity breeds bugs.

---

### ADR-010: Result Pattern for Error Handling
**Status:** Active
**Date:** 2025-09-24
**Decision:** Use Result<T, E> pattern for functional error handling instead of try/catch for control flow.

**Rationale:** Explicit error handling improves code reliability and makes error paths visible in type system.

---

## Testing & Quality Standards

### ADR-011: NECESSARY Pattern for Tests
**Status:** Active
**Date:** 2025-09-23
**Decision:** All tests must follow the NECESSARY pattern for quality and completeness.

**NECESSARY Components:**
- **N**amed clearly with test purpose
- **E**xecutable in isolation
- **C**omprehensive coverage
- **E**rror handling validated
- **S**tate changes verified
- **S**ide effects controlled
- **A**ssertions meaningful
- **R**epeatable results
- **Y**ield fast execution

---

### ADR-012: Test-Driven Development (TDD)
**Status:** Mandatory
**Date:** 2025-09-22
**Decision:** Write tests BEFORE implementation for all new features.

**Rationale:** TDD ensures code is testable, requirements are clear, and regressions are prevented.

---

## Memory & Learning Architecture

### ADR-013: VectorStore Integration
**Status:** Active
**Date:** 2025-09-23
**Decision:** Use VectorStore for semantic search and pattern matching in learning system.

**Components:**
- EnhancedMemoryStore with sentence-transformers
- Cross-session learning persistence
- Pattern recognition and institutional memory

---

### ADR-014: Shared Agent Context
**Status:** Active
**Date:** 2025-09-23
**Decision:** All agents share context through AgentContext for memory and coordination.

**Rationale:** Enables collective intelligence and consistent decision-making across agents.

---

## Autonomous Healing

### ADR-015: Self-Healing Capabilities
**Status:** Active
**Date:** 2025-09-25
**Decision:** Implement autonomous detection, analysis, and fixing of runtime errors.

**Components:**
- Automatic NoneType error detection
- LLM-powered fix generation
- Test verification before applying fixes
- Automatic rollback on failure

---

### ADR-006: Claude Agent SDK Adoption  
**Status:** Accepted  
**Date:** 2025-09-30  
**File:** `docs/adr/ADR-006-claude-agent-sdk-adoption.md`

**Decision:** Adopt Claude Agent SDK (Python) via environment-gated wrapper.

---

### ADR-007: DSPy Agent Loader - Hybrid Architecture
**Status:** Accepted
**Date:** 2025-09-30
**File:** `docs/adr/ADR-007-dspy-agent-loader-hybrid-architecture.md`

**Decision:** Implement hybrid loader for dual DSPy/traditional agent implementations with fallback.

**Constitutional Compliance:** Articles I (Context), II (Verification), IV (Learning), V (Spec-driven)

---

## Trinity Life Assistant Architecture

### ADR-016: Ambient Listener Architecture
**Status:** Accepted
**Date:** 2025-10-01
**File:** `docs/adr/ADR-016-ambient-listener-architecture.md`

**Decision:** Implement privacy-first ambient intelligence system with local Whisper AI transcription.

**Key Components:**
- 100% on-device audio processing (zero cloud transmission)
- Whisper.cpp integration with Metal GPU acceleration
- Memory-only audio buffer (never written to disk)
- Pattern detection integration with WITNESS agent
- Instant mute capability (<100ms)

**Constitutional Compliance:** Articles I (Complete Context), II (100% Verification), IV (Continuous Learning), V (Spec-Driven)

---

### ADR-017: Phase 3 Project Execution Architecture
**Status:** Accepted
**Date:** 2025-10-01
**File:** `docs/adr/ADR-017-phase3-project-execution.md`

**Decision:** Implement spec-driven project execution engine for real-world task completion.

**Key Components:**
- Project initialization through conversational Q&A (5-10 questions)
- LLM-powered spec generation from conversation transcripts
- Daily check-in coordination (1-3 questions maximum)
- Micro-task breakdown for adaptive execution
- Real-world tool integration (web research, document generation, calendar)
- Firestore persistence for cross-session project continuity
- Budget enforcement and graceful degradation

**Integration Points:**
- HITL protocol for user approval workflows
- Preference learning for optimal question timing
- Pattern detection feeds project initialization
- Foundation verifier ensures green main before execution

**Constitutional Compliance:** All 5 Articles (I: Complete Context, II: 100% Verification, III: Automated Enforcement, IV: Continuous Learning, V: Spec-Driven Development)

---

## Review Schedule

- **Weekly:** Review new ADR proposals
- **Monthly:** Validate ADR compliance across codebase
- **Quarterly:** Assess ADR effectiveness and updates needed
- **Annually:** Comprehensive ADR review and consolidation

## Amendment Process

1. Propose new ADR with clear problem statement
2. Document decision and rationale
3. Assess impact on existing architecture
4. Test implementation approach
5. Update this index upon approval

---

*Last Updated: 2025-10-01*
*Next Review: 2025-11-01*