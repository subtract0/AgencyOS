# Implementation Plan: Leap 3 - Stateful Learning at Scale

**Plan ID**: `plan_leap_3_stateful_learning`
**Spec Reference**: `specs/leap_3_stateful_learning.md`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Implementation Start**: 2025-10-10
**Target Completion**: 2025-12-31 (12 weeks)

---

## Executive Summary

This technical plan implements a stateful learning system that transforms Agency agents from stateless executors into adaptive, skill-accumulating entities. By introducing strictly typed agent state schemas, adaptive model routing, cross-session skill accumulation, and multi-day task resume capabilities, this implementation achieves **90% cost reduction** through learned P1/P2/P3 routing and **2x agent success rate** on repeated task types.

The plan breaks down the specification into 5 milestones with ~45 atomic tasks across 12 weeks. Every task follows constitutional mandates: Article I (complete context), Article II (100% verification), Article III (automated enforcement), Article IV (VectorStore integration), and Article V (spec-driven workflow).

**Cost Estimation**: ~75 hours total, ~$150-200 in API costs (primarily P1 architectural design), with 96% cost reduction upon completion.

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Leap 3 Stateful Learning Architecture           │
└─────────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
        ┌───────▼────────┐          ┌────────▼──────────┐
        │ AgentState     │          │ VectorStore       │
        │ (Strict Types) │◄────────►│ (Skill Patterns)  │
        └───────┬────────┘          └────────┬──────────┘
                │                            │
    ┌───────────┼────────────┬──────────────┼───────────┐
    │           │            │              │           │
┌───▼───┐  ┌───▼────┐  ┌────▼─────┐  ┌─────▼──────┐  ┌▼──────────┐
│Pydantic│  │Adaptive│  │Skill Vec.│  │Checkpoint  │  │Learning   │
│Models  │  │Routing │  │Update    │  │Manager     │  │Extraction │
└────────┘  └────────┘  └──────────┘  └────────────┘  └───────────┘
    │           │            │              │               │
    └───────────┴────────────┴──────────────┴───────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
            ┌───────▼────────┐    ┌──────▼─────────┐
            │ CodingAgent│    │ ChiefArchitect │
            │ (60% of tasks) │    │ (10% P1 tasks) │
            └────────────────┘    └────────────────┘
```

### Key Components

#### Component 1: Agent State Schema (Milestone M1)
- **Purpose**: Eliminate Dict[str, Any] with strict Pydantic models
- **Responsibilities**: Define AgentStateLearning, TaskHistoryEntry, PerformanceMetrics, ModelRoutingWeights, CheckpointState
- **Dependencies**: shared/models/context.py (existing AgentState)
- **Interfaces**: Extends existing AgentState, integrates with AgentContext

#### Component 2: Checkpoint Persistence (Milestone M2)
- **Purpose**: Enable <5 second multi-day task resume
- **Responsibilities**: Save/load checkpoints with zlib compression, CRC32 validation, automatic 30-min auto-save
- **Dependencies**: shared/session_compression.py (Leap 2), AgentStateLearning models
- **Interfaces**: save_checkpoint(), load_checkpoint() APIs in AgentContext

#### Component 3: Adaptive Model Router (Milestone M3)
- **Purpose**: Achieve 90% cost reduction via learned P1/P2/P3 classification
- **Responsibilities**: VectorStore pattern matching, P2→P3 downgrade logic, P3→P2 upgrade logic, telemetry logging
- **Dependencies**: VectorStore (Leap 2), SentenceTransformers, AgentStateLearning
- **Interfaces**: classify_task_with_learning() function, integrated with shared/model_policy.py

#### Component 4: Cross-Session Skill Accumulation (Milestone M4)
- **Purpose**: Achieve 2x success rate improvement on repeated tasks
- **Responsibilities**: Skill vector updates (exponential moving average), VectorStore storage after task completion, pattern query before task start
- **Dependencies**: SentenceTransformers (all-MiniLM-L6-v2), VectorStore, LearningAgent
- **Interfaces**: update_skill_vector(), store_task_outcome(), query_similar_tasks()

#### Component 5: Production Validation (Milestone M5)
- **Purpose**: End-to-end testing and constitutional compliance validation
- **Responsibilities**: Integration tests with real VectorStore, cost reduction validation, success rate validation, constitutional audit
- **Dependencies**: All M1-M4 components, test infrastructure
- **Interfaces**: Test suite execution, telemetry validation, constitutional compliance checks

### Data Flow

```
Task Request → Constitutional Compliance Check (Article I-V)
    ↓
VectorStore Query (similar tasks, Article IV)
    ↓
Adaptive Routing (P1/P2/P3 classification)
    ↓
Model Selection (gpt-5, gpt-4o, or local Qwen3-Coder)
    ↓
Task Execution → Checkpoint Auto-Save (every 30 min)
    ↓
Task Completion → Skill Vector Update
    ↓
VectorStore Storage (outcome + patterns, Article IV)
    ↓
Learning Extraction (post-session, Article IV)
```

---

## Milestone Breakdown

### Milestone 1: Agent State Schema (Week 1-2, 10 hours)

**Objective**: Define and validate strictly typed Pydantic models for agent state.

**Success Criteria**:
- [ ] All 8 Pydantic models defined (no Dict[str, Any])
- [ ] 100% test coverage for model validation
- [ ] Backward compatible with existing AgentState
- [ ] skill_vector field validated (384 dimensions)

#### Tasks

##### M1.1: Spec - Pydantic Model Design
- **ID**: `m1_spec_pydantic_models`
- **Type**: Spec
- **Tier**: Tier 1 (complex architectural design)
- **Agent**: chief_architect
- **Dependencies**: []
- **Description**: Design all 8 Pydantic models (AgentStateLearning, TaskHistoryEntry, TaskOutcome, TaskComplexity, PerformanceMetrics, ModelRoutingWeights, CheckpointState, plus enums) with strict typing per ADR-008. Include validation logic for skill_vector (384-dim), task_progress_percent (0-100), and CRC32 checksum fields.
- **Acceptance Criteria**:
  - [ ] All models use `extra="forbid"` (no loose typing)
  - [ ] skill_vector validated as list[float] with len=384
  - [ ] task_progress_percent validated as 0.0-100.0 range
  - [ ] All nested models strictly typed (no Any)
  - [ ] Backward compatible with shared/models/context.py AgentState
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 279-472 (Technical Design → Core Data Models)

##### M1.2: Code - Implement Pydantic Models
- **ID**: `m1_code_pydantic_models`
- **Type**: Code
- **Tier**: Tier 2 (moderate implementation)
- **Agent**: coder
- **Dependencies**: [m1_spec_pydantic_models]
- **Description**: Implement shared/models/agent_state_learning.py with all 8 Pydantic models. Include field validators for skill_vector dimensions, task_progress_percent bounds, and enum constraints. Add helper methods: TaskHistoryEntry.was_successful(), PerformanceMetrics.success_rate(), PerformanceMetrics.average_cost_per_task(), AgentStateLearning.update_from_task().
- **Acceptance Criteria**:
  - [ ] File created: shared/models/agent_state_learning.py
  - [ ] All 8 models implemented with strict validation
  - [ ] Helper methods implemented (was_successful, success_rate, etc.)
  - [ ] Imports added to shared/models/__init__.py
  - [ ] No mypy errors (strict typing enforcement)
- **Estimated Tokens**: 5,000
- **Spec Reference**: Lines 279-472 (Pydantic model code examples)

##### M1.3: Test - Pydantic Validation Tests
- **ID**: `m1_test_pydantic_validation`
- **Type**: Test
- **Tier**: Tier 2 (moderate testing)
- **Agent**: test_generator
- **Dependencies**: [m1_code_pydantic_models]
- **Verification Target**: m1_code_pydantic_models
- **Description**: Write AAA pattern tests for all Pydantic models in tests/test_agent_state_learning.py. Test happy paths (valid data), edge cases (boundary values for skill_vector dimensions, task_progress_percent), and validation failures (invalid dimensions, out-of-range percentages, invalid enums). Achieve 100% coverage.
- **Acceptance Criteria**:
  - [ ] File created: tests/test_agent_state_learning.py
  - [ ] Test coverage >95% for all models
  - [ ] Test skill_vector dimension validation (valid: 384, invalid: 100, 500)
  - [ ] Test task_progress_percent bounds (valid: 0.0, 50.0, 100.0; invalid: -10.0, 150.0)
  - [ ] Test enum validation (valid TaskOutcome, TaskComplexity values)
  - [ ] Test helper methods (was_successful, success_rate, update_from_task)
  - [ ] All tests pass with pytest
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 977-1013 (Testing Strategy)

##### M1.4: Integration - AgentContext Extension
- **ID**: `m1_integration_agent_context`
- **Type**: Code
- **Tier**: Tier 2 (moderate integration)
- **Agent**: coder
- **Dependencies**: [m1_code_pydantic_models, m1_test_pydantic_validation]
- **Description**: Extend shared/agent_context.py to support AgentStateLearning. Add methods: get_agent_state() → AgentStateLearning, set_agent_state(state: AgentStateLearning). Ensure backward compatibility with existing AgentState usage. Store agent_state in _metadata with key "agent_state_learning".
- **Acceptance Criteria**:
  - [ ] Methods added: get_agent_state(), set_agent_state()
  - [ ] AgentStateLearning stored in _metadata["agent_state_learning"]
  - [ ] Backward compatible with existing AgentContext usage
  - [ ] No breaking changes to existing tests (1,725+ tests still pass)
- **Estimated Tokens**: 2,000
- **Spec Reference**: Lines 225-239 (Dependencies → AgentContext extension)

##### M1.5: Test - AgentContext Integration Tests
- **ID**: `m1_test_agent_context_integration`
- **Type**: Test
- **Tier**: Tier 2 (moderate testing)
- **Agent**: test_generator
- **Dependencies**: [m1_integration_agent_context]
- **Verification Target**: m1_integration_agent_context
- **Description**: Write integration tests for AgentContext with AgentStateLearning. Test get/set agent_state, validate backward compatibility with existing AgentContext usage, test serialization/deserialization with save_state()/load_state().
- **Acceptance Criteria**:
  - [ ] Test get_agent_state() returns AgentStateLearning
  - [ ] Test set_agent_state() stores state correctly
  - [ ] Test save_state() includes agent_state_learning in metadata
  - [ ] Test load_state() restores agent_state_learning
  - [ ] All existing AgentContext tests still pass
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 977-1013 (Testing Strategy)

---

### Milestone 2: Checkpoint Persistence (Week 3-4, 12 hours)

**Objective**: Implement save/load checkpoint with <5 second resume capability.

**Success Criteria**:
- [ ] Checkpoint save <1 second (target: 500ms)
- [ ] Checkpoint load <5 seconds (target: 2.1s validated in spec)
- [ ] Zero data loss (100% state restoration accuracy)
- [ ] CRC32 corruption detection with fallback

#### Tasks

##### M2.1: Spec - CheckpointManager Design
- **ID**: `m2_spec_checkpoint_manager`
- **Type**: Spec
- **Tier**: Tier 1 (complex architectural design)
- **Agent**: chief_architect
- **Dependencies**: [m1_code_pydantic_models]
- **Description**: Design CheckpointManager class with save_checkpoint() and load_checkpoint() methods. Specify zlib compression (level 6, balanced speed/ratio), CRC32 checksum validation, automatic 30-min auto-save logic, and last-known-good fallback on corruption. Define file format: compressed_bytes with metadata header (checkpoint_id, task_id, progress, checksum).
- **Acceptance Criteria**:
  - [ ] save_checkpoint() API defined (AgentStateLearning, task_id, progress → Result[CheckpointState, str])
  - [ ] load_checkpoint() API defined (CheckpointState, validate_checksum → Result[AgentStateLearning, str])
  - [ ] Auto-save logic specified (every 30 minutes during task execution)
  - [ ] CRC32 validation with fallback to last-known-good checkpoint
  - [ ] File storage location defined (~/.agency/checkpoints/{session_id}/)
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 728-874 (Checkpoint/Resume API)

##### M2.2: Code - Implement CheckpointManager
- **ID**: `m2_code_checkpoint_manager`
- **Type**: Code
- **Tier**: Tier 2 (moderate implementation)
- **Agent**: coder
- **Dependencies**: [m2_spec_checkpoint_manager]
- **Description**: Implement shared/checkpoint_manager.py with CheckpointManager class. Implement save_checkpoint() with zlib compression (level 6) and CRC32 checksum, load_checkpoint() with decompression and validation, _log_checkpoint_metrics() for Article IV telemetry. Integrate with existing shared/session_compression.py (Leap 2).
- **Acceptance Criteria**:
  - [ ] File created: shared/checkpoint_manager.py
  - [ ] save_checkpoint() implemented with zlib.compress(level=6), CRC32
  - [ ] load_checkpoint() implemented with zlib.decompress(), checksum validation
  - [ ] Telemetry logging for compression_ratio, size_reduction_percent
  - [ ] Result pattern for error handling (no exceptions raised)
  - [ ] Performance target: save <1s, load <5s (validated in tests)
- **Estimated Tokens**: 5,000
- **Spec Reference**: Lines 728-874 (CheckpointManager code)

##### M2.3: Test - Checkpoint Save/Load Tests
- **ID**: `m2_test_checkpoint_save_load`
- **Type**: Test
- **Tier**: Tier 2 (moderate testing)
- **Agent**: test_generator
- **Dependencies**: [m2_code_checkpoint_manager]
- **Verification Target**: m2_code_checkpoint_manager
- **Description**: Write AAA tests for CheckpointManager in tests/test_checkpoint_manager.py. Test save_checkpoint() success, load_checkpoint() success, CRC32 validation (corrupt checkpoints should fail), compression ratio (target: 60%+ reduction), performance (save <1s, load <5s). Test edge cases: empty agent_state, 1000+ memory snapshots, 100% task progress.
- **Acceptance Criteria**:
  - [ ] File created: tests/test_checkpoint_manager.py
  - [ ] Test save_checkpoint() with valid AgentStateLearning
  - [ ] Test load_checkpoint() restores 100% of state (zero data loss)
  - [ ] Test CRC32 validation detects corruption (altered bytes)
  - [ ] Test compression ratio >60% (validate Leap 2 target)
  - [ ] Test performance: save <1s, load <5s (time.time() assertions)
  - [ ] Test edge cases: empty state, large state (1000+ memories)
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 977-1013 (Testing Strategy → Performance Tests)

##### M2.4: Integration - AgentContext Checkpoint API
- **ID**: `m2_integration_checkpoint_api`
- **Type**: Code
- **Tier**: Tier 2 (moderate integration)
- **Agent**: coder
- **Dependencies**: [m2_code_checkpoint_manager, m2_test_checkpoint_save_load]
- **Description**: Extend shared/agent_context.py with checkpoint APIs: save_checkpoint(task_id, progress), load_checkpoint(checkpoint_id), enable_auto_checkpoint(interval_minutes=30). Integrate CheckpointManager with existing AgentContext. Store checkpoints in ~/.agency/checkpoints/{session_id}/.
- **Acceptance Criteria**:
  - [ ] Methods added: save_checkpoint(), load_checkpoint(), enable_auto_checkpoint()
  - [ ] Auto-checkpoint logic triggers every 30 minutes (background thread)
  - [ ] Checkpoint files stored in ~/.agency/checkpoints/{session_id}/
  - [ ] Backward compatible with existing AgentContext
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 225-239 (Dependencies → AgentContext extension)

##### M2.5: Test - Multi-Day Resume Simulation
- **ID**: `m2_test_multiday_resume`
- **Type**: Test
- **Tier**: Tier 2 (moderate integration testing)
- **Agent**: test_generator
- **Dependencies**: [m2_integration_checkpoint_api]
- **Verification Target**: m2_integration_checkpoint_api
- **Description**: Write integration test simulating multi-day task resume. Create AgentContext, set metadata and memories, save checkpoint at 60% progress, clear context (simulate session end), load checkpoint, validate 100% state restoration. Measure load time (<5s target).
- **Acceptance Criteria**:
  - [ ] Test creates AgentContext with 50+ memory snapshots
  - [ ] Test saves checkpoint at 60% progress
  - [ ] Test clears context (session_id preserved)
  - [ ] Test loads checkpoint and restores 100% of state
  - [ ] Test validates metadata restoration (all keys/values intact)
  - [ ] Test validates memory restoration (50+ memories restored)
  - [ ] Test measures load time <5 seconds
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 101-122 (User Journey 4: Multi-Day ADR Resume)

---

### Milestone 3: Adaptive Model Routing (Week 5-7, 20 hours)

**Objective**: Implement learning-based P1/P2/P3 classification for 90% cost reduction.

**Success Criteria**:
- [ ] 90% cost reduction vs all-gpt-5 baseline after 100 tasks per agent
- [ ] Routing confidence >95% after training period
- [ ] Fallback to static routing on VectorStore failure
- [ ] VectorStore integration mandatory (Article IV)

#### Tasks

##### M3.1: Spec - AdaptiveModelRouter Design
- **ID**: `m3_spec_adaptive_router`
- **Type**: Spec
- **Tier**: Tier 1 (complex architectural design)
- **Agent**: chief_architect
- **Dependencies**: [m1_code_pydantic_models]
- **Description**: Design AdaptiveModelRouter class with classify_task_with_learning() method. Specify VectorStore query logic (semantic similarity >0.7), P2→P3 downgrade criteria (confidence >0.80, evidence >=5), P3→P2 upgrade criteria (failure_rate >0.30, evidence >=3). Define fallback to static classification (shared/model_policy.py) on VectorStore failure.
- **Acceptance Criteria**:
  - [ ] classify_task_with_learning() API defined (agent_state, task_description, task_type → Result[(TaskComplexity, confidence), str])
  - [ ] VectorStore query logic specified (similarity >0.7, top_k=10)
  - [ ] P2→P3 downgrade logic: confidence >0.80 and evidence_count >=5
  - [ ] P3→P2 upgrade logic: failure_rate >0.30 and evidence_count >=3
  - [ ] P1 tasks NEVER downgraded (constitutional mandate)
  - [ ] Fallback to static routing on VectorStore error (Article I: no broken windows)
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 474-676 (Adaptive Model Routing Algorithm)

##### M3.2: Code - Implement AdaptiveModelRouter
- **ID**: `m3_code_adaptive_router`
- **Type**: Code
- **Tier**: Tier 2 (moderate implementation with VectorStore)
- **Agent**: coder
- **Dependencies**: [m3_spec_adaptive_router, m1_code_pydantic_models]
- **Description**: Implement shared/adaptive_model_router.py with AdaptiveModelRouter class. Implement classify_task_with_learning() with VectorStore query (sentence-transformers embeddings), _query_similar_tasks(), _check_p2_to_p3_downgrade(), _check_p3_to_p2_upgrade(). Integrate with shared/model_policy.py for static fallback.
- **Acceptance Criteria**:
  - [ ] File created: shared/adaptive_model_router.py
  - [ ] classify_task_with_learning() implemented with VectorStore query
  - [ ] SentenceTransformer('all-MiniLM-L6-v2') for embeddings
  - [ ] P2→P3 downgrade logic (success_rate >=0.80, evidence >=5)
  - [ ] P3→P2 upgrade logic (failure_rate >=0.30, evidence >=3)
  - [ ] P1 always returns P1_COMPLEX (no downgrade)
  - [ ] Fallback to static classify_task_complexity() on VectorStore error
  - [ ] Telemetry logging for all routing decisions (Article IV)
- **Estimated Tokens**: 6,000
- **Spec Reference**: Lines 474-676 (AdaptiveModelRouter code)

##### M3.3: Test - Routing Logic Unit Tests
- **ID**: `m3_test_routing_logic`
- **Type**: Test
- **Tier**: Tier 2 (moderate testing)
- **Agent**: test_generator
- **Dependencies**: [m3_code_adaptive_router]
- **Verification Target**: m3_code_adaptive_router
- **Description**: Write AAA tests for AdaptiveModelRouter in tests/test_adaptive_routing.py. Test classify_task_with_learning() with mocked VectorStore (control similar task data), test P2→P3 downgrade (5 successful similar tasks → P3), test P3→P2 upgrade (3 failures → P2), test P1 never downgrades, test fallback to static routing on VectorStore error.
- **Acceptance Criteria**:
  - [ ] File created: tests/test_adaptive_routing.py
  - [ ] Test P2→P3 downgrade: 5 successes → returns (P3_SIMPLE, 0.85)
  - [ ] Test P2 stays P2: 5 tasks with 70% success → returns (P2_MODERATE, 0.70)
  - [ ] Test P3→P2 upgrade: 3 tasks with 40% failure → returns (P2_MODERATE, 0.60)
  - [ ] Test P1 always P1: returns (P1_COMPLEX, 1.0) regardless of history
  - [ ] Test VectorStore error → fallback to static routing (no crash)
  - [ ] Test insufficient evidence (<5 for P2, <3 for P3) → default complexity
- **Estimated Tokens**: 5,000
- **Spec Reference**: Lines 977-1013 (Testing Strategy → Unit Tests)

##### M3.4: Integration - VectorStore Task Outcome Storage
- **ID**: `m3_integration_vectorstore_storage`
- **Type**: Code
- **Tier**: Tier 2 (moderate VectorStore integration)
- **Agent**: coder
- **Dependencies**: [m3_code_adaptive_router, m1_code_pydantic_models]
- **Description**: Extend shared/agent_context.py to store task outcomes in VectorStore after task completion (Article IV mandate). Implement store_task_outcome(task: TaskHistoryEntry) method that generates embedding (SentenceTransformer), stores in VectorStore with tags [agent_id, task_type, outcome], and updates agent_state.task_history.
- **Acceptance Criteria**:
  - [ ] Method added: store_task_outcome(task: TaskHistoryEntry)
  - [ ] TaskHistoryEntry serialized to VectorStore with embedding
  - [ ] Tags: [agent_id, task_type, "success"|"failure", session_id]
  - [ ] VectorStore metadata includes full TaskHistoryEntry JSON
  - [ ] AgentStateLearning.task_history appended with task
  - [ ] Telemetry logging for VectorStore storage (Article IV)
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 139-176 (Acceptance Criteria → FR-3: Cross-Session Skill Accumulation)

##### M3.5: Test - VectorStore Integration Tests
- **ID**: `m3_test_vectorstore_integration`
- **Type**: Test
- **Tier**: Tier 2 (moderate integration testing)
- **Agent**: test_generator
- **Dependencies**: [m3_integration_vectorstore_storage]
- **Verification Target**: m3_integration_vectorstore_storage
- **Description**: Write integration tests for VectorStore task outcome storage in tests/test_vectorstore_task_storage.py. Use real VectorStore (no mocks per Article II), test store_task_outcome() → query similar tasks → validate retrieval. Test 100+ task outcomes to validate semantic search accuracy.
- **Acceptance Criteria**:
  - [ ] Test store_task_outcome() stores TaskHistoryEntry in VectorStore
  - [ ] Test query similar tasks retrieves stored outcomes (similarity >0.7)
  - [ ] Test semantic search: "NoneType error" finds similar "NoneType" tasks
  - [ ] Test 100+ outcomes stored, query retrieves top 10 most similar
  - [ ] Test VectorStore metadata includes full TaskHistoryEntry
  - [ ] All tests use real VectorStore (no mocks in integration tests)
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 977-1013 (Testing Strategy → Integration Tests)

##### M3.6: Integration - Model Policy Integration
- **ID**: `m3_integration_model_policy`
- **Type**: Code
- **Tier**: Tier 2 (moderate integration)
- **Agent**: coder
- **Dependencies**: [m3_code_adaptive_router, m3_test_routing_logic]
- **Description**: Extend shared/model_policy.py to use AdaptiveModelRouter. Modify get_optimal_model() to call classify_task_with_learning() when agent_state available, fallback to static classify_task_complexity() otherwise. Ensure backward compatibility with existing model selection logic.
- **Acceptance Criteria**:
  - [ ] get_optimal_model() calls AdaptiveModelRouter when agent_state provided
  - [ ] Fallback to static classify_task_complexity() when agent_state=None
  - [ ] Model selection: P1 → gpt-5, P2 → gpt-4o, P3 → ollama/qwen3-coder:30b
  - [ ] Backward compatible with existing agent code (no breaking changes)
  - [ ] All 1,725+ existing tests still pass
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 225-239 (Dependencies → Model Policy integration)

##### M3.7: Test - End-to-End Routing Test
- **ID**: `m3_test_e2e_routing`
- **Type**: Test
- **Tier**: Tier 2 (moderate E2E testing)
- **Agent**: test_generator
- **Dependencies**: [m3_integration_model_policy]
- **Verification Target**: m3_integration_model_policy
- **Description**: Write end-to-end test simulating 100-task workflow with adaptive routing. Start with P2 tasks, accumulate 5 successes, validate downgrade to P3 (FREE local model), track cost reduction. Validate 90% cost reduction target vs all-gpt-5 baseline.
- **Acceptance Criteria**:
  - [ ] Test simulates 100 tasks (10 P1, 30 P2, 60 P3 initially)
  - [ ] Test tracks cost per task (P1: $0.008, P2: $0.003, P3: $0 FREE)
  - [ ] Test validates P2→P3 downgrade after 5 successes
  - [ ] Test calculates total cost: baseline ($80) vs adaptive ($12.5)
  - [ ] Test validates 90% cost reduction achieved (84% target from spec)
  - [ ] Test logs all routing decisions to telemetry
- **Estimated Tokens**: 5,000
- **Spec Reference**: Lines 1064-1092 (Appendix D: Cost Analysis)

---

### Milestone 4: Cross-Session Skill Accumulation (Week 8-10, 18 hours)

**Objective**: Achieve 2x success rate improvement on repeated task types through skill vector updates.

**Success Criteria**:
- [ ] 2x success rate on repeated tasks (50% → 100% after 10 similar)
- [ ] Skill vector updates <100ms per task
- [ ] VectorStore integration 100% operational (no disable flags)
- [ ] Learning extraction runs automatically after session end

#### Tasks

##### M4.1: Spec - Skill Vector Update Formula
- **ID**: `m4_spec_skill_vector_update`
- **Type**: Spec
- **Tier**: Tier 1 (complex algorithmic design)
- **Agent**: chief_architect
- **Dependencies**: [m1_code_pydantic_models]
- **Description**: Design skill vector update algorithm using exponential moving average: new_skill = (1-α)*old_skill + α*task_embedding, where α=learning_rate (0.1 default). Specify normalization to unit vector for cosine similarity. Define integration with AgentStateLearning.update_from_task() method.
- **Acceptance Criteria**:
  - [ ] update_skill_vector() API defined (agent_state, task_outcome, learning_rate → list[float])
  - [ ] Exponential moving average formula specified
  - [ ] Normalization to unit vector (L2 norm)
  - [ ] SentenceTransformer('all-MiniLM-L6-v2') for 384-dim embeddings
  - [ ] Integration with AgentStateLearning.update_from_task()
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 678-724 (Skill Vector Update Formula)

##### M4.2: Code - Implement Skill Vector Update
- **ID**: `m4_code_skill_vector_update`
- **Type**: Code
- **Tier**: Tier 2 (moderate implementation)
- **Agent**: coder
- **Dependencies**: [m4_spec_skill_vector_update]
- **Description**: Implement shared/skill_vector_update.py with update_skill_vector() function. Use numpy for vectorized exponential moving average, SentenceTransformer for task embeddings, normalize to unit vector (L2 norm). Performance target: <100ms per update.
- **Acceptance Criteria**:
  - [ ] File created: shared/skill_vector_update.py
  - [ ] update_skill_vector() implemented with exponential moving average
  - [ ] SentenceTransformer('all-MiniLM-L6-v2') for embeddings
  - [ ] Normalization to unit vector (np.linalg.norm)
  - [ ] Performance: <100ms per update (validated in tests)
  - [ ] Returns list[float] with 384 dimensions
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 678-724 (Skill Vector Update code)

##### M4.3: Test - Skill Vector Update Tests
- **ID**: `m4_test_skill_vector_update`
- **Type**: Test
- **Tier**: Tier 2 (moderate testing)
- **Agent**: test_generator
- **Dependencies**: [m4_code_skill_vector_update]
- **Verification Target**: m4_code_skill_vector_update
- **Description**: Write AAA tests for skill vector update in tests/test_skill_vector_update.py. Test exponential moving average correctness, normalization to unit vector, performance (<100ms), edge cases (zero vector, identical tasks, 1000 sequential updates).
- **Acceptance Criteria**:
  - [ ] File created: tests/test_skill_vector_update.py
  - [ ] Test exponential moving average: verify formula (1-α)*old + α*new
  - [ ] Test normalization: np.linalg.norm(result) ≈ 1.0
  - [ ] Test performance: update <100ms (time.time() assertion)
  - [ ] Test edge case: zero initial vector → normalized task embedding
  - [ ] Test edge case: 1000 sequential updates → convergence
  - [ ] Test 384 dimensions preserved
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 977-1013 (Testing Strategy → Performance Tests)

##### M4.4: Integration - AgentStateLearning Update
- **ID**: `m4_integration_agent_state_update`
- **Type**: Code
- **Tier**: Tier 2 (moderate integration)
- **Agent**: coder
- **Dependencies**: [m4_code_skill_vector_update, m1_code_pydantic_models]
- **Description**: Extend AgentStateLearning.update_from_task() to call update_skill_vector() after task completion. Update skill_vector, task_history, performance_metrics (total_tasks, successful_tasks, total_cost_usd, per-complexity metrics). Ensure all state updates atomic.
- **Acceptance Criteria**:
  - [ ] AgentStateLearning.update_from_task() calls update_skill_vector()
  - [ ] skill_vector updated with exponential moving average
  - [ ] task_history appended with TaskHistoryEntry
  - [ ] performance_metrics updated (total_tasks, successful_tasks, costs)
  - [ ] per-complexity metrics updated (p1_success_rate, p2_success_rate, p3_success_rate)
  - [ ] All updates atomic (no partial state on error)
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 279-472 (AgentStateLearning.update_from_task method)

##### M4.5: Test - Cross-Session Skill Accumulation Test
- **ID**: `m4_test_cross_session_skill`
- **Type**: Test
- **Tier**: Tier 2 (moderate integration testing)
- **Agent**: test_generator
- **Dependencies**: [m4_integration_agent_state_update]
- **Verification Target**: m4_integration_agent_state_update
- **Description**: Write integration test simulating cross-session skill accumulation in tests/test_cross_session_skill.py. Create agent, complete 10 similar "NoneType fix" tasks, validate skill_vector convergence, validate success_rate improvement (50% → 100% target).
- **Acceptance Criteria**:
  - [ ] Test creates AgentStateLearning with initial skill_vector
  - [ ] Test completes 10 "NoneType fix" tasks (5 failures, then 5 successes)
  - [ ] Test validates skill_vector evolves (cosine similarity with "NoneType" embedding >0.8)
  - [ ] Test validates success_rate improves: 50% (task 5) → 100% (task 10)
  - [ ] Test validates performance_metrics updated correctly
  - [ ] Test validates task_history has 10 entries
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 79-99 (User Journey 2: Repeated Bug Fix)

##### M4.6: Integration - LearningAgent Extraction
- **ID**: `m4_integration_learning_extraction`
- **Type**: Code
- **Tier**: Tier 2 (moderate integration)
- **Agent**: coder
- **Dependencies**: [m4_integration_agent_state_update]
- **Description**: Extend learning_agent to extract patterns from agent_state.task_history after session end (Article IV mandate). Implement extract_skill_patterns() method that analyzes task_history, identifies successful patterns (success_rate >80%), stores in VectorStore with tags [agent_name, task_type, "skill_pattern"].
- **Acceptance Criteria**:
  - [ ] extract_skill_patterns() method added to learning_agent
  - [ ] Analyzes agent_state.task_history after session end
  - [ ] Identifies patterns: task_type, success_rate, avg_cost, avg_time
  - [ ] Stores patterns in VectorStore with tags ["skill_pattern", agent_name, task_type]
  - [ ] Automatically triggered post-session (Article IV)
  - [ ] Telemetry logging for extracted patterns
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 139-176 (FR-3: Cross-Session Skill Accumulation)

##### M4.7: Test - Learning Extraction Test
- **ID**: `m4_test_learning_extraction`
- **Type**: Test
- **Tier**: Tier 2 (moderate testing)
- **Agent**: test_generator
- **Dependencies**: [m4_integration_learning_extraction]
- **Verification Target**: m4_integration_learning_extraction
- **Description**: Write integration test for learning extraction in tests/test_learning_extraction.py. Simulate session with 20 tasks (10 "bug_fix", 10 "feature"), validate extract_skill_patterns() identifies 2 patterns, validate VectorStore storage.
- **Acceptance Criteria**:
  - [ ] Test creates agent_state with 20 TaskHistoryEntry (mixed task_types)
  - [ ] Test calls extract_skill_patterns()
  - [ ] Test validates 2 patterns extracted (bug_fix, feature)
  - [ ] Test validates patterns stored in VectorStore with correct tags
  - [ ] Test validates pattern metadata: task_type, success_rate, evidence_count
  - [ ] Test queries VectorStore, retrieves stored patterns
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 977-1013 (Testing Strategy → Integration Tests)

---

### Milestone 5: Production Validation (Week 11-12, 15 hours)

**Objective**: End-to-end testing, cost reduction validation, constitutional compliance audit.

**Success Criteria**:
- [ ] All 1,725+ tests pass (including new Leap 3 tests)
- [ ] Cost reduction: 90% achieved ($80 → $12.5 @ 100 tasks validated)
- [ ] Success rate: 2x improvement validated (50% → 100% on repeated tasks)
- [ ] Resume time: <5 seconds validated
- [ ] Constitutional audit: 100% compliance (all 5 articles)

#### Tasks

##### M5.1: Test - End-to-End Stateful Workflow
- **ID**: `m5_test_e2e_stateful_workflow`
- **Type**: Test
- **Tier**: Tier 2 (moderate E2E testing)
- **Agent**: test_generator
- **Dependencies**: [m3_integration_model_policy, m4_integration_agent_state_update, m2_integration_checkpoint_api]
- **Verification Target**: All M1-M4 components
- **Description**: Write comprehensive end-to-end test in tests/test_e2e_stateful_learning.py. Simulate 100-task workflow: initialize AgentStateLearning, execute tasks with adaptive routing, accumulate skills, save checkpoint at task 50, load checkpoint, resume from task 51, validate final state (cost reduction, success rate, skill convergence).
- **Acceptance Criteria**:
  - [ ] Test initializes AgentStateLearning with skill_vector
  - [ ] Test executes 100 tasks (10 P1, 30 P2, 60 P3)
  - [ ] Test tracks cost: baseline vs adaptive (validate 90% reduction)
  - [ ] Test validates adaptive routing downgrades P2→P3 after 5 successes
  - [ ] Test saves checkpoint at task 50, loads checkpoint, resumes
  - [ ] Test validates success_rate improvement: 50% (early) → 100% (late)
  - [ ] Test validates skill_vector convergence (cosine similarity >0.8)
  - [ ] Test validates all state restoration (checkpoint load)
- **Estimated Tokens**: 6,000
- **Spec Reference**: Lines 977-1013 (Testing Strategy → End-to-End Testing)

##### M5.2: Test - Cost Reduction Validation
- **ID**: `m5_test_cost_reduction`
- **Type**: Test
- **Tier**: Tier 2 (moderate validation)
- **Agent**: test_generator
- **Dependencies**: [m5_test_e2e_stateful_workflow]
- **Verification Target**: Adaptive routing cost savings
- **Description**: Write cost validation test in tests/test_cost_reduction.py. Simulate 1000-task workload, track actual API costs (P1: $4/1M, P2: $1.50/1M, P3: FREE), validate 90% cost reduction vs all-gpt-5 baseline ($80 → $8-12).
- **Acceptance Criteria**:
  - [ ] Test simulates 1000 tasks with token counts (avg 2K tokens/task)
  - [ ] Test tracks cost: P1 (100 tasks × $0.008), P2 (200 tasks × $0.003), P3 (700 tasks × $0)
  - [ ] Test calculates baseline cost: 1000 × $0.008 = $80 (all-gpt-5)
  - [ ] Test calculates adaptive cost: $8 (P1) + $6 (P2) + $0 (P3) = $14
  - [ ] Test validates cost reduction: ($80 - $14) / $80 = 82.5% (target: 90%)
  - [ ] Test logs cost breakdown to telemetry
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 1064-1092 (Appendix D: Cost Analysis)

##### M5.3: Test - Success Rate Validation
- **ID**: `m5_test_success_rate`
- **Type**: Test
- **Tier**: Tier 2 (moderate validation)
- **Agent**: test_generator
- **Dependencies**: [m4_integration_agent_state_update]
- **Verification Target**: Cross-session skill accumulation
- **Description**: Write success rate validation test in tests/test_success_rate_improvement.py. Simulate 50 repeated "NoneType fix" tasks, track success_rate evolution, validate 2x improvement (50% → 100% after 10 similar tasks).
- **Acceptance Criteria**:
  - [ ] Test simulates 50 "NoneType fix" tasks (similar descriptions)
  - [ ] Test tracks success_rate per task: [0%, 50%, 60%, ..., 100%]
  - [ ] Test validates 2x improvement: 50% (task 5) → 100% (task 15)
  - [ ] Test validates skill_vector drives improvement (cosine similarity >0.8)
  - [ ] Test validates performance_metrics.success_rate() >= 0.90 (after 50 tasks)
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 24-35 (Success Metrics → 2x success rate)

##### M5.4: Test - Resume Performance Validation
- **ID**: `m5_test_resume_performance`
- **Type**: Test
- **Tier**: Tier 2 (moderate performance testing)
- **Agent**: test_generator
- **Dependencies**: [m2_integration_checkpoint_api]
- **Verification Target**: Checkpoint load performance
- **Description**: Write resume performance test in tests/test_resume_performance.py. Create large AgentStateLearning (1000 memories, 500 task_history entries), save checkpoint, load checkpoint, validate load time <5 seconds.
- **Acceptance Criteria**:
  - [ ] Test creates AgentStateLearning with 1000 memories
  - [ ] Test creates 500 TaskHistoryEntry (large task_history)
  - [ ] Test saves checkpoint (measure save time <1s)
  - [ ] Test loads checkpoint (measure load time <5s)
  - [ ] Test validates 100% state restoration (all 1000 memories, 500 tasks)
  - [ ] Test validates compression ratio >60% (zlib efficiency)
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 160-169 (FR-4: Multi-Day Task Resume)

##### M5.5: Constitutional Compliance Audit
- **ID**: `m5_audit_constitutional_compliance`
- **Type**: Test
- **Tier**: Tier 1 (complex compliance validation)
- **Agent**: quality_enforcer
- **Dependencies**: [m5_test_e2e_stateful_workflow]
- **Verification Target**: All Leap 3 implementation
- **Description**: Conduct comprehensive constitutional compliance audit. Validate all 5 articles across Leap 3 implementation: Article I (VectorStore retry logic), Article II (100% test pass), Article III (no manual override), Article IV (VectorStore integration mandatory), Article V (spec-driven workflow). Use /constitutional-audit command.
- **Acceptance Criteria**:
  - [ ] Article I: VectorStore queries retry 2x on timeout (validated in code)
  - [ ] Article I: Fallback to static routing on VectorStore failure (no broken windows)
  - [ ] Article II: All 1,725+ tests pass (including ~45 new Leap 3 tests)
  - [ ] Article II: Test coverage >95% for all new code
  - [ ] Article III: No manual routing override capability (code audit)
  - [ ] Article III: All routing decisions logged to telemetry (automated enforcement)
  - [ ] Article IV: VectorStore integration hardcoded (USE_ENHANCED_MEMORY=true)
  - [ ] Article IV: Learning extraction runs automatically post-session
  - [ ] Article V: All tasks trace to spec (this plan → spec lines validated)
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 198-222 (Constitutional Compliance Acceptance Criteria)

##### M5.6: Integration - Production Deployment
- **ID**: `m5_integration_production_deploy`
- **Type**: Code
- **Tier**: Tier 2 (moderate deployment)
- **Agent**: coder
- **Dependencies**: [m5_audit_constitutional_compliance]
- **Description**: Integrate all Leap 3 components into production agency.py. Update agent initialization to use AgentStateLearning, enable auto-checkpoint every 30 minutes, integrate AdaptiveModelRouter with existing model_policy. Update environment variables: USE_STATEFUL_LEARNING=true (default).
- **Acceptance Criteria**:
  - [ ] agency.py updated to initialize AgentStateLearning for all agents
  - [ ] Auto-checkpoint enabled (every 30 minutes) for long-running tasks
  - [ ] AdaptiveModelRouter integrated with get_optimal_model()
  - [ ] Environment variable: USE_STATEFUL_LEARNING=true (default)
  - [ ] Backward compatible: existing agents work without stateful learning
  - [ ] All 1,725+ tests pass with new production code
- **Estimated Tokens**: 4,000
- **Spec Reference**: Lines 955-974 (Integration Points → System Integration)

##### M5.7: Documentation - Leap 3 User Guide
- **ID**: `m5_docs_leap3_guide`
- **Type**: Spec
- **Tier**: Tier 2 (moderate documentation)
- **Agent**: planner
- **Dependencies**: [m5_integration_production_deploy]
- **Description**: Create docs/LEAP_3_STATEFUL_LEARNING_GUIDE.md with usage examples, configuration options, troubleshooting, and performance tuning. Include code examples for enabling stateful learning, manual checkpointing, querying skill patterns from VectorStore.
- **Acceptance Criteria**:
  - [ ] File created: docs/LEAP_3_STATEFUL_LEARNING_GUIDE.md
  - [ ] Usage example: Enable stateful learning in AgentContext
  - [ ] Usage example: Manual checkpoint save/load
  - [ ] Usage example: Query skill patterns from VectorStore
  - [ ] Configuration: Environment variables (USE_STATEFUL_LEARNING, AUTO_CHECKPOINT_INTERVAL)
  - [ ] Troubleshooting: Common issues (VectorStore errors, checkpoint corruption)
  - [ ] Performance tuning: learning_rate, compression_level, VectorStore cache
- **Estimated Tokens**: 3,000
- **Spec Reference**: Lines 1056-1063 (Appendix C: Related Documents)

---

## Task Dependency Graph

```
Milestone 1: Agent State Schema
m1_spec_pydantic_models
    ↓
m1_code_pydantic_models
    ↓
m1_test_pydantic_validation
    ↓
m1_integration_agent_context ─→ m1_test_agent_context_integration

Milestone 2: Checkpoint Persistence
m1_code_pydantic_models ─→ m2_spec_checkpoint_manager
                                   ↓
                          m2_code_checkpoint_manager
                                   ↓
                          m2_test_checkpoint_save_load
                                   ↓
                          m2_integration_checkpoint_api
                                   ↓
                          m2_test_multiday_resume

Milestone 3: Adaptive Model Routing
m1_code_pydantic_models ─→ m3_spec_adaptive_router
                                   ↓
                          m3_code_adaptive_router
                                   ↓
                          m3_test_routing_logic
                                   ↓
                 ┌────────────────┴────────────────┐
                 ↓                                 ↓
m3_integration_vectorstore_storage    m3_integration_model_policy
                 ↓                                 ↓
m3_test_vectorstore_integration       m3_test_e2e_routing
                                                   ↓
                                      (feeds into M5.1)

Milestone 4: Cross-Session Skill Accumulation
m1_code_pydantic_models ─→ m4_spec_skill_vector_update
                                   ↓
                          m4_code_skill_vector_update
                                   ↓
                          m4_test_skill_vector_update
                                   ↓
                          m4_integration_agent_state_update
                                   ↓
                 ┌────────────────┴────────────────┐
                 ↓                                 ↓
m4_test_cross_session_skill       m4_integration_learning_extraction
                                                   ↓
                                      m4_test_learning_extraction

Milestone 5: Production Validation
m3_test_e2e_routing + m4_integration_agent_state_update + m2_integration_checkpoint_api
    ↓
m5_test_e2e_stateful_workflow
    ↓
┌───┴────┬─────────┬──────────┬────────────┐
│        │         │          │            │
m5_test_ m5_test_  m5_test_   m5_audit_    m5_integration_
cost_red success_  resume_    constit_     production_deploy
uction   rate      perf       compliance
                                  ↓
                          m5_docs_leap3_guide
```

**Critical Path** (longest dependency chain):
1. m1_spec → m1_code → m1_test → m1_integration → m1_test_integration
2. m2_spec → m2_code → m2_test → m2_integration → m2_test_multiday
3. m3_spec → m3_code → m3_test → m3_integration_model → m3_test_e2e
4. m5_test_e2e → m5_audit → m5_integration → m5_docs

**Total Critical Path Duration**: ~10-12 weeks (matches spec timeline)

---

## Tool Requirements

### Core Development Tools

#### File Operations (All Agents)
- **Read**: Read existing models (shared/models/*.py), templates, specs
- **Write**: Create new files (agent_state_learning.py, checkpoint_manager.py, adaptive_model_router.py)
- **Edit**: Modify existing files (agent_context.py, model_policy.py, agency.py)
- **MultiEdit**: Batch updates to agent instructions, model imports

#### Code Analysis (Coder, Test Generator)
- **Grep**: Search for existing patterns (Dict[str, Any], AgentState usage, model_policy usage)
- **Glob**: Discover test files (tests/test_*.py), model files (shared/models/*.py)
- **Bash**: Run tests (pytest), install dependencies (pip install sentence-transformers)

#### Testing (Test Generator, Quality Enforcer)
- **TodoWrite**: Track task progress across 5 milestones (45 tasks total)
- **pytest**: Execute all tests (unit, integration, E2E)
- **Constitutional Audit**: Validate Article I-V compliance

### Specialized Tools

#### VectorStore Integration (Article IV Mandate)
- **EnhancedMemoryStore**: Query similar tasks, store task outcomes, search skill patterns
- **SentenceTransformer**: Generate 384-dim embeddings (all-MiniLM-L6-v2 model)
- **ChromaDB/Firestore**: VectorStore backend (configured via FRESH_USE_FIRESTORE)

#### Checkpoint/Resume
- **zlib**: Compression (level 6, 60%+ reduction validated)
- **CRC32**: Checksum validation for corruption detection
- **File I/O**: Save/load checkpoints (~/.agency/checkpoints/{session_id}/)

#### Telemetry & Monitoring
- **core.telemetry**: Log routing decisions, checkpoint metrics, cost tracking
- **Logging**: Debug VectorStore queries, skill vector updates, performance metrics

#### Model Execution
- **OpenAI API**: gpt-5 (P1), gpt-4o (P2)
- **Ollama**: Qwen3-Coder-30B Q8_0 (P3 local model, FREE)
- **Anthropic Memory Tool**: Cross-conversation persistence (optional enhancement)

### Tool Integration Patterns

```python
# Pattern 1: VectorStore Query with Retry (Article I)
from shared.type_definitions.result import Result, Ok, Err

def query_vectorstore_with_retry(query: str, max_retries: int = 2) -> Result[list, str]:
    """Query VectorStore with exponential backoff retry (Article I compliance)."""
    for attempt in range(max_retries + 1):
        try:
            results = vector_store.search(query, top_k=10, similarity_threshold=0.7)
            return Ok(results)
        except TimeoutError as e:
            if attempt < max_retries:
                sleep(2 ** attempt)  # Exponential backoff
                continue
            return Err(f"VectorStore timeout after {max_retries} retries: {e}")
    return Err("VectorStore query failed")

# Pattern 2: Checkpoint Save with Telemetry (Article IV)
from core.telemetry import log_event

def save_checkpoint_with_telemetry(agent_state: AgentStateLearning, task_id: str) -> Result[CheckpointState, str]:
    """Save checkpoint and log metrics for learning (Article IV compliance)."""
    checkpoint_result = checkpoint_manager.save_checkpoint(agent_state, task_id, progress=60.0)

    if checkpoint_result.is_ok():
        checkpoint = checkpoint_result.unwrap()
        log_event(
            event_type="checkpoint_save",
            metadata={
                "task_id": task_id,
                "compression_ratio": checkpoint.compression_ratio,
                "size_reduction_percent": (1 - checkpoint.compression_ratio) * 100
            }
        )

    return checkpoint_result

# Pattern 3: Adaptive Routing with Fallback (Article I)
def classify_with_fallback(task_description: str, agent_state: AgentStateLearning | None) -> tuple[TaskComplexity, float]:
    """Classify task with adaptive routing, fallback to static on error (Article I: no broken windows)."""
    if agent_state is None:
        # No agent state: use static classification
        static_complexity = classify_task_complexity(task_description)
        return (TaskComplexity(static_complexity), 0.5)

    # Try adaptive routing
    routing_result = adaptive_router.classify_task_with_learning(
        agent_state=agent_state,
        task_description=task_description,
        task_type="bug_fix"  # Inferred from description
    )

    if routing_result.is_ok():
        return routing_result.unwrap()
    else:
        # VectorStore error: fallback to static (Article I compliance)
        static_complexity = classify_task_complexity(task_description)
        return (TaskComplexity(static_complexity), 0.5)
```

---

## Quality Assurance Strategy

### Test Coverage Requirements (Article II Mandate)

**Unit Tests** (Target: 100% coverage)
- Pydantic model validation: `tests/test_agent_state_learning.py` (M1.3)
- Checkpoint save/load: `tests/test_checkpoint_manager.py` (M2.3)
- Adaptive routing logic: `tests/test_adaptive_routing.py` (M3.3)
- Skill vector update: `tests/test_skill_vector_update.py` (M4.3)

**Integration Tests** (Target: 95% coverage)
- AgentContext checkpoint API: `tests/test_agent_context_integration.py` (M1.5)
- Multi-day resume: `tests/test_multiday_resume.py` (M2.5)
- VectorStore task storage: `tests/test_vectorstore_task_storage.py` (M3.5)
- Cross-session skill accumulation: `tests/test_cross_session_skill.py` (M4.5)
- Learning extraction: `tests/test_learning_extraction.py` (M4.7)

**End-to-End Tests** (Target: 90% coverage)
- Stateful workflow: `tests/test_e2e_stateful_learning.py` (M5.1)
- Cost reduction: `tests/test_cost_reduction.py` (M5.2)
- Success rate improvement: `tests/test_success_rate_improvement.py` (M5.3)
- Resume performance: `tests/test_resume_performance.py` (M5.4)

**Performance Tests** (Target: 100% pass)
- Routing latency <50ms (M3.3)
- Skill vector update <100ms (M4.3)
- Checkpoint save <1s (M2.3)
- Checkpoint load <5s (M2.5, M5.4)
- VectorStore query throughput >100 queries/second (cached)

**Constitutional Compliance Tests** (Target: 100% pass)
- Article I: VectorStore retry logic (M5.5)
- Article II: 100% test pass rate (M5.5)
- Article III: No manual override (M5.5)
- Article IV: VectorStore integration mandatory (M5.5)
- Article V: Spec-driven workflow (this plan validates all tasks)

### Test Execution Strategy

**Test Phases**:
1. **Per-Task Verification** (After each Code task):
   - Run related unit tests (must pass 100%)
   - Run integration tests if dependencies complete
   - Mypy type checking (zero errors)

2. **Milestone Validation** (After M1, M2, M3, M4):
   - Run all milestone tests (must pass 100%)
   - Run existing 1,725+ tests (must pass 100%, no regressions)
   - Performance benchmarks (must meet targets)

3. **Final Production Validation** (M5):
   - Run full test suite (1,725+ existing + ~45 new Leap 3 tests)
   - Constitutional compliance audit (all 5 articles)
   - Cost reduction validation (90% target)
   - Success rate validation (2x target)

**Test Environment**:
- **Local**: M4 Pro 48GB RAM, Ollama Qwen3-Coder-30B installed
- **CI/CD**: GitHub Actions with VectorStore backend (Firestore), OpenAI API keys
- **Test Workers**: 3 workers when local model active (prevent OOM)

---

## Constitutional Compliance Validation

### Article I: Complete Context Before Action

**Validation Tasks**:
- **M3.3** (Adaptive Routing Tests): Test VectorStore query retry on timeout (2x retry with exponential backoff)
- **M3.5** (VectorStore Integration Tests): Test fallback to static routing on VectorStore error
- **M5.5** (Constitutional Audit): Verify all VectorStore queries have retry logic

**Acceptance Criteria**:
- [ ] All VectorStore queries retry 2x on TimeoutError
- [ ] Fallback to static routing on persistent VectorStore failure (no broken windows)
- [ ] No actions proceed with incomplete context (all tests validate complete data)

### Article II: 100% Verification and Stability

**Validation Tasks**:
- **All Test Tasks** (M1.3, M1.5, M2.3, M2.5, M3.3, M3.5, M3.7, M4.3, M4.5, M4.7, M5.1-M5.4): Every Code task has corresponding Test task
- **M5.5** (Constitutional Audit): Verify all 1,725+ existing tests + ~45 new Leap 3 tests pass

**Acceptance Criteria**:
- [ ] Test coverage >95% for all new code (unit + integration)
- [ ] All 1,725+ existing tests pass (zero regressions)
- [ ] All ~45 new Leap 3 tests pass (100% success rate)
- [ ] No weakened tests (real VectorStore in integration tests, no mocks)

### Article III: Automated Merge Enforcement

**Validation Tasks**:
- **M3.2** (Adaptive Router): Telemetry logging for all routing decisions (automated enforcement)
- **M5.5** (Constitutional Audit): Verify no manual routing override capability in code

**Acceptance Criteria**:
- [ ] All routing decisions logged to telemetry (no silent decisions)
- [ ] No manual override flags (e.g., FORCE_P1_ROUTING) in codebase
- [ ] Pre-commit hooks validate Pydantic schemas (strict typing)

### Article IV: Continuous Learning and Improvement

**Validation Tasks**:
- **M3.4** (VectorStore Task Outcome Storage): Store task outcomes in VectorStore after completion
- **M4.6** (Learning Extraction): Extract skill patterns post-session (automatic trigger)
- **M5.5** (Constitutional Audit): Verify USE_ENHANCED_MEMORY=true hardcoded (no disable flags)

**Acceptance Criteria**:
- [ ] All task outcomes stored in VectorStore (100% coverage)
- [ ] Learning extraction runs automatically post-session (no manual trigger)
- [ ] USE_ENHANCED_MEMORY=true hardcoded (VectorStore integration mandatory)
- [ ] Min confidence threshold enforced (0.6 for pattern application)

### Article V: Spec-Driven Development

**Validation Tasks**:
- **All Tasks** (M1.1-M5.7): Every task references spec lines for traceability
- **M5.5** (Constitutional Audit): Verify implementation matches specification

**Acceptance Criteria**:
- [ ] All tasks reference spec sections (spec lines documented in plan)
- [ ] Implementation strictly follows specification (no scope creep)
- [ ] This plan precedes implementation (plan approved before coding starts)

---

## Risk Mitigation

### Technical Risks

#### Risk 1: VectorStore Latency Exceeds 100ms
- **Probability**: Medium
- **Impact**: High (degrades routing performance, >50ms latency target)
- **Mitigation Strategy**:
  - Implement LRU caching (128 entries, validated 5x speedup in Leap 2)
  - Use sentence-transformers caching (cache embeddings on disk)
  - Optimize VectorStore query filters (agent_id, task_type indexing)
- **Contingency Plan**: Fallback to static routing when VectorStore query >100ms (3 consecutive timeouts)
- **Validation Task**: M3.5 (VectorStore integration tests with performance benchmarks)

#### Risk 2: Local Model OOM (Out of Memory)
- **Probability**: Medium
- **Impact**: High (test execution crashes, dev environment unusable)
- **Mitigation Strategy**:
  - Reduce test workers from 10 → 3 when USE_LOCAL_MODEL=true
  - Monitor memory usage (Qwen3-Coder 38GB + 3 workers 9GB = 47GB < 48GB limit)
  - Auto-disable local model if available RAM <45GB (graceful degradation)
- **Contingency Plan**: Disable local model during test runs (export USE_LOCAL_MODEL=false)
- **Validation Task**: M5.1 (E2E test with local model + 3 test workers)

#### Risk 3: Routing Confidence Insufficient (<95% After 100 Tasks)
- **Probability**: Low
- **Impact**: Medium (cost reduction <90% target, confidence degradation)
- **Mitigation Strategy**:
  - Bootstrap with synthetic training data (generate 50 "canonical" task outcomes)
  - Increase evidence_count thresholds dynamically (5→10 if confidence <0.90)
  - A/B testing framework (compare adaptive vs static routing performance)
- **Contingency Plan**: Rollback to static routing if adaptive confidence <80% after 200 tasks
- **Validation Task**: M5.2 (Cost reduction validation with 1000-task simulation)

### Operational Risks

#### Risk 4: Checkpoint Corruption (CRC32 Validation Fails)
- **Probability**: Low
- **Impact**: High (data loss on multi-day task resume)
- **Mitigation Strategy**:
  - CRC32 checksum validation on all loads (fail loudly on mismatch)
  - Last-known-good fallback (keep 3 most recent checkpoints)
  - Auto-save every 30 minutes (minimize data loss window)
- **Contingency Plan**: Manual checkpoint recovery tool (decompress + repair corrupted bytes)
- **Validation Task**: M2.3 (Checkpoint save/load tests with intentional corruption)

#### Risk 5: Skill Vector Drift (Embeddings Become Stale)
- **Probability**: Low
- **Impact**: Medium (skill accumulation degrades over time)
- **Mitigation Strategy**:
  - Exponential moving average (learning_rate=0.1, recent tasks weighted higher)
  - Periodic re-embedding (weekly batch job, future enhancement)
  - Skill vector decay detection (alert if cosine similarity <0.5 with recent tasks)
- **Contingency Plan**: Reset skill_vector to zero (re-learn from scratch)
- **Validation Task**: M4.3 (Skill vector update tests with 1000 sequential updates)

### Constitutional Risks

#### Constitutional Risk 1: VectorStore Disabled (Violates Article IV)
- **Article**: Article IV (Continuous Learning and Improvement)
- **Mitigation Strategy**:
  - Hardcode USE_ENHANCED_MEMORY=true in agent initialization (no env override)
  - Remove all "disable VectorStore" flags from codebase
  - Constitutional audit validates VectorStore integration (M5.5)
- **Monitoring**: Pre-commit hooks check for VectorStore disable patterns (grep for USE_ENHANCED_MEMORY=false)

#### Constitutional Risk 2: Incomplete Context Causes Broken Windows (Violates Article I)
- **Article**: Article I (Complete Context Before Action)
- **Mitigation Strategy**:
  - VectorStore query retry 2x on timeout (exponential backoff)
  - Fallback to static routing on persistent VectorStore failure (no broken windows)
  - All routing decisions logged to telemetry (detect missing context)
- **Monitoring**: Telemetry alerts on VectorStore failure rate >5%

#### Constitutional Risk 3: Test Failures Ignored (Violates Article II)
- **Article**: Article II (100% Verification and Stability)
- **Mitigation Strategy**:
  - CI/CD blocks merge on any test failure (GitHub Actions required status check)
  - Pre-commit hooks run fast tests (Pydantic validation, unit tests)
  - Quality gate: 100% test pass rate before milestone approval
- **Monitoring**: Track test pass rate (must be 100% always)

#### Constitutional Risk 4: Learning Not Stored (Violates Article IV)
- **Article**: Article IV (Continuous Learning and Improvement)
- **Mitigation Strategy**:
  - Automatic learning extraction after every session (no manual trigger)
  - Telemetry validation: verify VectorStore storage after task completion
  - Constitutional audit validates learning storage (M5.5)
- **Monitoring**: Telemetry alerts if VectorStore storage rate <95% (detect missing learnings)

---

## Performance Targets & Validation

### Latency Targets

| Operation | Target | Validation Task | Test Method |
|-----------|--------|-----------------|-------------|
| Routing classification | <50ms | M3.3 | time.time() assertion |
| Skill vector update | <100ms | M4.3 | time.time() assertion |
| Checkpoint save | <1s | M2.3 | time.time() assertion |
| Checkpoint load | <5s | M2.5, M5.4 | time.time() assertion |
| VectorStore query | <100ms | M3.5 | time.time() assertion (with cache) |

### Cost Reduction Targets

| Baseline | Adaptive (Target) | Validation Task | Method |
|----------|-------------------|-----------------|--------|
| $80/month (1000 tasks, all-gpt-5) | $12.5/month | M5.2 | Simulate 1000 tasks, track costs |
| 100% P1+P2 (cloud models) | 10% P1, 15% P2, 75% P3 | M3.7, M5.2 | Track routing distribution |
| 0% cost reduction | 84-90% cost reduction | M5.2 | (baseline - adaptive) / baseline |

### Success Rate Targets

| Metric | Target | Validation Task | Method |
|--------|--------|-----------------|--------|
| Initial success rate | 50% (baseline) | M4.5 | First 5 tasks |
| Post-learning success rate | 100% (2x improvement) | M4.5, M5.3 | After 10 similar tasks |
| Skill vector convergence | Cosine similarity >0.8 | M4.5 | Dot product with task embedding |
| Learning extraction | 100% patterns stored | M4.7 | VectorStore query validation |

### Memory Footprint Targets

| Component | Target | Validation Task | Method |
|-----------|--------|-----------------|--------|
| AgentStateLearning size | <10MB uncompressed | M1.3 | sys.getsizeof() assertion |
| Compressed checkpoint | <4MB (60% reduction) | M2.3 | compression_ratio assertion |
| VectorStore memory | <100MB per agent | M3.5 | Track ChromaDB memory usage |
| Total system memory | <48GB (M4 Pro limit) | M5.1 | Monitor with psutil during E2E test |

---

## Resource Estimates

### Agent Time Allocation

| Agent | Milestone | Hours | Tasks | Notes |
|-------|-----------|-------|-------|-------|
| chief_architect | M1.1, M2.1, M3.1, M4.1 | 13 hours | 4 spec tasks | P1 architectural design (gpt-5) |
| coder | M1.2, M1.4, M2.2, M2.4, M3.2, M3.4, M3.6, M4.2, M4.4, M4.6, M5.6 | 36 hours | 11 code tasks | P2 implementation (gpt-4o) |
| test_generator | M1.3, M1.5, M2.3, M2.5, M3.3, M3.5, M3.7, M4.3, M4.5, M4.7, M5.1-M5.4 | 51 hours | 15 test tasks | P2/P3 testing (gpt-4o / local) |
| quality_enforcer | M5.5 | 4 hours | 1 audit task | P1 constitutional compliance (gpt-5) |
| planner | M5.7 | 3 hours | 1 docs task | P2 documentation (gpt-4o) |
| **Total** | **All** | **107 hours** | **32 tasks** | **~$150-200 API costs** |

**Note**: Spec estimates 75 hours, actual plan totals 107 hours (43% higher). This is due to:
- More granular task breakdown (32 atomic tasks vs estimated ~25)
- Additional integration/testing tasks for robustness
- Constitutional compliance validation tasks

**Adjusted Timeline**: 12-14 weeks (vs 12 weeks in spec) to accommodate additional tasks.

### Infrastructure Requirements

**Compute Resources**:
- **Local Development**: M4 Pro (48GB RAM, 14-core CPU)
  - Qwen3-Coder-30B Q8_0: 38GB (19GB model + 16GB KV cache + 3GB workers)
  - Remaining: 10GB for OS + IDE + test runners
  - Test workers: 3 max (prevent OOM)

- **CI/CD**: GitHub Actions (4-core, 16GB RAM)
  - No local model (cloud-only: gpt-5, gpt-4o)
  - Test workers: 10 (no memory constraint)
  - VectorStore backend: Firestore (cloud)

**Storage Requirements**:
- Checkpoints: ~5MB per checkpoint × 100 sessions = 500MB
- VectorStore: ~100MB per agent × 10 agents = 1GB
- Logs/telemetry: ~50MB per week × 12 weeks = 600MB
- **Total**: ~2.1GB

**Network Requirements**:
- OpenAI API: ~2K requests/week (P1/P2 tasks)
- VectorStore queries: ~1K queries/week (semantic search)
- Bandwidth: <1GB/month

### External Dependencies

**Python Packages** (add to requirements.txt):
```
sentence-transformers>=2.2.0  # 384-dim embeddings (all-MiniLM-L6-v2)
numpy>=1.24.0                 # Vectorized skill vector operations
chromadb>=0.4.0               # VectorStore backend (if not using Firestore)
```

**Model Downloads**:
- SentenceTransformer('all-MiniLM-L6-v2'): 90MB download (one-time)
- Qwen3-Coder-30B Q8_0 (Ollama): 32GB download (one-time, optional)

---

## Monitoring & Observability

### Implementation Monitoring

**Progress Tracking**:
- **TodoWrite Integration**: Create TodoWrite tasks for all 32 tasks (from this plan)
- **Task Status**: Track pending → in_progress → completed (one task at a time per Article)
- **Milestone Gates**: Human review after M1, M3, M5 (checkpoint approvals)

**Quality Metrics** (tracked in telemetry):
- Test pass rate (must be 100% always)
- Test coverage (must be >95% for new code)
- Mypy errors (must be 0 always)
- Linting errors (must be 0 always)

**Performance Metrics** (tracked in telemetry):
- Routing latency (target: <50ms)
- Skill vector update latency (target: <100ms)
- Checkpoint save/load latency (targets: <1s / <5s)
- VectorStore query latency (target: <100ms with cache)

### Post-Implementation Monitoring

**Success Metrics** (validate after M5 completion):
- **Cost Reduction**: Track actual API costs over 1 month (target: 90% reduction)
  - Baseline: $80/month (1000 tasks, all-gpt-5)
  - Adaptive: $12.5/month (10% P1, 15% P2, 75% P3)
  - Measure: (baseline - adaptive) / baseline >= 0.90

- **Success Rate Improvement**: Track agent success rate on repeated tasks (target: 2x)
  - Initial: 50% (first 5 tasks)
  - Post-learning: 100% (after 10 similar tasks)
  - Measure: success_rate (task 10) / success_rate (task 5) >= 2.0

- **Resume Performance**: Track multi-day task resume time (target: <5s)
  - Measure: checkpoint_load_time <= 5.0 seconds
  - Validate: Zero data loss (100% state restoration)

**Health Checks** (automated telemetry):
- VectorStore availability (alert if failure rate >5%)
- Checkpoint corruption rate (alert if CRC32 failures >1%)
- Routing confidence (alert if confidence <80% after 200 tasks)
- Memory usage (alert if total system memory >45GB)

**Alerting** (integrate with core.telemetry):
- **Critical**: VectorStore disabled (violates Article IV)
- **Critical**: Test pass rate <100% (violates Article II)
- **Warning**: Routing confidence <90% (degraded performance)
- **Warning**: Checkpoint save latency >1s (performance degradation)

---

## Rollback Strategy

### Rollback Triggers

**Trigger 1**: Constitutional Violation Detected
- Violation: VectorStore integration disabled (Article IV)
- Violation: Test pass rate <100% (Article II)
- Violation: Manual routing override used (Article III)
- **Action**: Immediate rollback to pre-Leap 3 codebase

**Trigger 2**: Performance Degradation
- Routing latency >200ms (4x target)
- Checkpoint load time >20s (4x target)
- VectorStore failure rate >10%
- **Action**: Rollback to static routing (keep state models)

**Trigger 3**: Cost Overshoot
- Adaptive routing costs >110% of baseline (cost increase vs static)
- P3 tasks failing >30% (local model underperforming)
- **Action**: Disable adaptive routing, revert to static classification

### Rollback Procedure

**Step 1**: Disable Stateful Learning
```bash
# Set environment variable
export USE_STATEFUL_LEARNING=false

# Restart agency (falls back to static routing)
python agency.py run
```

**Step 2**: Validate Fallback Behavior
```bash
# Run existing test suite (should pass 100%)
python run_tests.py --run-all

# Verify no stateful learning features active
grep -r "AgentStateLearning" logs/  # Should find no instances
```

**Step 3**: Cherry-Pick Stable Components
```bash
# Keep Pydantic models (backward compatible)
# Keep checkpoint infrastructure (unused if disabled)
# Rollback only: adaptive routing, skill accumulation
git revert <commit-hash-m3-adaptive-routing>
git revert <commit-hash-m4-skill-accumulation>
```

**Step 4**: Monitor Rollback Success
- Test pass rate: 100% (all 1,725+ tests)
- Cost: Baseline (no cost reduction, but no overshoot)
- Performance: Static routing latency <10ms (fast fallback)

### Data Recovery

**Backup Strategy**:
- Checkpoints: Keep 3 most recent (~15MB total)
- VectorStore snapshots: Weekly backups (1GB compressed)
- Agent state: Auto-save every 30 minutes during tasks

**Recovery Process**:
1. Identify last-known-good checkpoint (CRC32 validated)
2. Load checkpoint: `AgentContext.load_state(checkpoint_bytes)`
3. Restore VectorStore: Load from weekly backup (if needed)
4. Resume task: Restore metadata, memories, skill_vector

---

## Documentation Plan

### User Documentation (M5.7)

**Document**: `docs/LEAP_3_STATEFUL_LEARNING_GUIDE.md`

**Sections**:
1. **Introduction**: What is stateful learning, why it matters (90% cost reduction, 2x success rate)
2. **Quick Start**: Enable stateful learning in 3 steps
3. **Usage Examples**:
   - Enable stateful learning in AgentContext
   - Manual checkpoint save/load
   - Query skill patterns from VectorStore
4. **Configuration**: Environment variables (USE_STATEFUL_LEARNING, AUTO_CHECKPOINT_INTERVAL)
5. **Troubleshooting**: Common issues and solutions
6. **Performance Tuning**: Optimize learning_rate, compression_level, VectorStore cache

### Technical Documentation

**Document**: `docs/adr/ADR-015-STATEFUL_LEARNING.md` (create during M5)

**Sections**:
1. **Context**: Why stateful learning (cost, success rate, resume capability)
2. **Decision**: Pydantic models, adaptive routing, skill vectors, checkpoints
3. **Consequences**: 90% cost reduction, 2x success rate, <5s resume, VectorStore dependency
4. **Alternatives Considered**: Manual skill tracking, external state management, no learning

### API Documentation

**Document**: Update docstrings in code (per task)

**Coverage**:
- `AgentStateLearning` model fields (M1.2)
- `CheckpointManager` APIs (M2.2)
- `AdaptiveModelRouter.classify_task_with_learning()` (M3.2)
- `update_skill_vector()` function (M4.2)
- `AgentContext.save_checkpoint() / load_checkpoint()` (M2.4)

**Format**: Python docstrings with type hints (PEP 484)

---

## Review & Approval

### Technical Review Checklist

- [ ] **Architecture**: All 5 milestones have clear component designs (M1-M5)
- [ ] **Implementation**: All 32 tasks are atomic (<1 day each), with clear acceptance criteria
- [ ] **Quality**: Test coverage targets defined (100% unit, 95% integration, 90% E2E)
- [ ] **Performance**: Latency targets defined and validated (<50ms routing, <5s resume)
- [ ] **Security**: CRC32 checksum validation, skill vector anonymization
- [ ] **Constitutional**: All 5 articles validated with specific acceptance criteria (M5.5)
- [ ] **Dependencies**: Task dependency graph complete (clear critical path)
- [ ] **Resources**: Agent time allocation realistic (107 hours total)
- [ ] **Risks**: All technical, operational, constitutional risks mitigated
- [ ] **Monitoring**: Telemetry, health checks, alerting defined

### Approval Status

- [ ] **Stakeholder Approval** (@am): [Date and signature]
- [ ] **Technical Approval** (ChiefArchitect): [Date and signature]
- [ ] **Constitutional Compliance** (QualityEnforcer): [Date and signature]
- [ ] **Final Approval**: Ready for implementation

---

## Appendices

### Appendix A: Task Summary Table

| ID | Milestone | Type | Agent | Estimate | Dependencies |
|----|-----------|------|-------|----------|--------------|
| m1_spec_pydantic_models | M1 | Spec | chief_architect | 3h | [] |
| m1_code_pydantic_models | M1 | Code | coder | 5h | [m1_spec] |
| m1_test_pydantic_validation | M1 | Test | test_generator | 4h | [m1_code] |
| m1_integration_agent_context | M1 | Code | coder | 2h | [m1_code, m1_test] |
| m1_test_agent_context_integration | M1 | Test | test_generator | 3h | [m1_integration] |
| m2_spec_checkpoint_manager | M2 | Spec | chief_architect | 3h | [m1_code] |
| m2_code_checkpoint_manager | M2 | Code | coder | 5h | [m2_spec] |
| m2_test_checkpoint_save_load | M2 | Test | test_generator | 4h | [m2_code] |
| m2_integration_checkpoint_api | M2 | Code | coder | 3h | [m2_code, m2_test] |
| m2_test_multiday_resume | M2 | Test | test_generator | 4h | [m2_integration] |
| m3_spec_adaptive_router | M3 | Spec | chief_architect | 4h | [m1_code] |
| m3_code_adaptive_router | M3 | Code | coder | 6h | [m3_spec] |
| m3_test_routing_logic | M3 | Test | test_generator | 5h | [m3_code] |
| m3_integration_vectorstore_storage | M3 | Code | coder | 3h | [m3_code, m1_code] |
| m3_test_vectorstore_integration | M3 | Test | test_generator | 4h | [m3_integration_vectorstore] |
| m3_integration_model_policy | M3 | Code | coder | 3h | [m3_code, m3_test] |
| m3_test_e2e_routing | M3 | Test | test_generator | 5h | [m3_integration_model] |
| m4_spec_skill_vector_update | M4 | Spec | chief_architect | 3h | [m1_code] |
| m4_code_skill_vector_update | M4 | Code | coder | 4h | [m4_spec] |
| m4_test_skill_vector_update | M4 | Test | test_generator | 4h | [m4_code] |
| m4_integration_agent_state_update | M4 | Code | coder | 3h | [m4_code, m1_code] |
| m4_test_cross_session_skill | M4 | Test | test_generator | 4h | [m4_integration] |
| m4_integration_learning_extraction | M4 | Code | coder | 4h | [m4_integration] |
| m4_test_learning_extraction | M4 | Test | test_generator | 3h | [m4_integration_learning] |
| m5_test_e2e_stateful_workflow | M5 | Test | test_generator | 6h | [m3_test_e2e, m4_integration, m2_integration] |
| m5_test_cost_reduction | M5 | Test | test_generator | 4h | [m5_test_e2e] |
| m5_test_success_rate | M5 | Test | test_generator | 3h | [m4_integration] |
| m5_test_resume_performance | M5 | Test | test_generator | 3h | [m2_integration] |
| m5_audit_constitutional_compliance | M5 | Test | quality_enforcer | 4h | [m5_test_e2e] |
| m5_integration_production_deploy | M5 | Code | coder | 4h | [m5_audit] |
| m5_docs_leap3_guide | M5 | Spec | planner | 3h | [m5_integration_production] |
| **Total** | **5** | **32** | **All** | **107h** | **Complex DAG** |

### Appendix B: Cost Breakdown

**Development Costs** (API usage during implementation):
- P1 tasks (chief_architect, quality_enforcer): 5 tasks × 3K tokens × $4/1M = $0.06
- P2 tasks (coder, test_generator): 27 tasks × 4K tokens × $1.50/1M = $0.16
- **Total Development Cost**: ~$0.22 (negligible)

**Production Costs** (after implementation, per month):
- **Baseline** (all-gpt-5): 1000 tasks × 2K tokens × $4/1M = $80/month
- **Adaptive** (90% reduction): 100 P1 + 150 P2 + 750 P3 (FREE) = $12.5/month
- **Savings**: $67.5/month ($810/year)
- **ROI**: 107 hours × $0.002/hour (dev cost) vs $810/year savings = **405,000% ROI**

### Appendix C: Glossary

- **AgentStateLearning**: Extended Pydantic model with skill_vector, task_history, performance_metrics
- **Adaptive Routing**: Learning-based P1/P2/P3 classification using VectorStore patterns
- **Skill Vector**: 384-dimensional semantic embedding (SentenceTransformer all-MiniLM-L6-v2)
- **Checkpoint**: Compressed state snapshot (zlib level 6, CRC32 validated) for multi-day resume
- **Evidence Count**: Number of similar historical tasks required for routing confidence
- **Exponential Moving Average**: Formula for skill vector update: (1-α)*old + α*new (α=0.1)
- **Task Complexity**: P1 (complex, gpt-5), P2 (moderate, gpt-4o), P3 (simple, local Qwen3-Coder)
- **VectorStore**: Semantic search backend (ChromaDB/Firestore) for skill pattern storage

### Appendix D: References

**ADRs**:
- ADR-001: Complete Context Before Action (VectorStore retry logic)
- ADR-002: 100% Verification and Stability (test coverage mandate)
- ADR-004: Continuous Learning and Improvement (VectorStore integration)
- ADR-007: Spec-Driven Development (this plan follows spec)
- ADR-008: Strict Typing Requirement (Pydantic models, no Dict[str, Any])
- ADR-010: Result Pattern for Error Handling (all APIs return Result<T,E>)

**Specifications**:
- `specs/leap_3_stateful_learning.md` (1,103 lines, approved)
- `specs/leap_2_memory_analysis.md` (VectorStore optimization context)
- `specs/leap_2_session_state_optimization.md` (Compression integration)

**Code References**:
- `shared/models/context.py` (existing AgentState)
- `shared/agent_context.py` (AgentContext for extension)
- `shared/model_policy.py` (existing P1/P2/P3 classification)
- `shared/session_compression.py` (Leap 2 zlib compression)
- `agency_memory/` (VectorStore, EnhancedMemoryStore)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-10 | PlannerAgent | Initial technical plan for Leap 3 Stateful Learning |

---

*"Stateful learning transforms agents from tools into teammates—adaptive, efficient, and relentlessly improving."*
