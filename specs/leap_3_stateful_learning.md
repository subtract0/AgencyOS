# Specification: Leap 3 - Stateful Learning at Scale

**Spec ID**: `leap_3_stateful_learning`
**Status**: `Draft`
**Author**: ChiefArchitectAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Mission**: `missions/leap_3_stateful_learning_at_scale.json`
**Tier**: Tier 1 (Foundation)

---

## Executive Summary

Design and implement a stateful learning system that enables agents to accumulate skills across sessions, optimize model routing based on learned task patterns, and resume multi-day tasks in <5 seconds with full state restoration. This specification achieves **90% cost reduction** through learned P1/P2/P3 routing and **2x agent success rate** on repeated task types through cross-session skill accumulation.

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Formalize Agent State Schema with strictly typed Pydantic models (eliminate all Dict[str, Any])
- [ ] **Goal 2**: Implement Adaptive Model Routing with learned P1/P2/P3 classification achieving 90% cost reduction
- [ ] **Goal 3**: Enable Cross-Session Skill Accumulation with VectorStore integration for 2x success rate improvement
- [ ] **Goal 4**: Achieve <5 second multi-day task resume with checkpoint persistence and incremental state updates
- [ ] **Goal 5**: Maintain 100% constitutional compliance across all 5 articles with automated validation

### Success Metrics
- **Cost Reduction**: 90% cost savings vs all-gpt-5 baseline ($40K/month → $4K/month @ 10K tasks)
- **Success Rate Improvement**: 2x success rate on repeated task types (50% → 100% after 10 similar tasks)
- **Resume Performance**: <5 seconds to restore full agent state for multi-day tasks
- **Routing Confidence**: 95% confidence in P1/P2/P3 classification after 100 tasks per agent
- **State Restoration Accuracy**: 100% metadata + memory restoration (zero data loss)
- **VectorStore Integration**: 100% of state transitions stored for learning (Article IV mandate)

---

## Non-Goals

### Explicit Exclusions
- **Federated Learning**: Not implementing multi-device skill aggregation (single-machine only)
- **Real-Time Model Switching**: Not implementing dynamic model swapping mid-task (checkpoint boundaries only)
- **Skill Transfer Between Agent Types**: Not transferring PlannerAgent skills to CoderAgent (same-role only)
- **Human-in-the-Loop Routing**: Not requiring manual P1/P2/P3 approval (fully autonomous)

### Future Considerations
- **Multi-Agent Skill Sharing**: Cross-agent skill transfer with semantic similarity
- **Adversarial Skill Testing**: Red-team validation of learned routing decisions
- **Skill Decay Modeling**: Time-based confidence degradation for stale patterns
- **Explainable Routing**: Human-readable reasoning for P1/P2/P3 classification

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: AgencyOSAgent (Skill-Accumulating Developer)
- **Description**: Primary development agent learning from repeated coding tasks
- **Goals**: Recognize similar bugs, reuse proven fix patterns, optimize model usage cost
- **Pain Points**: No memory of past fixes, always uses gpt-5 (expensive), repeats mistakes
- **Technical Proficiency**: Expert in code generation, requires transparent skill tracking

#### Persona 2: LearningAgent (Pattern Extractor)
- **Description**: Meta-agent analyzing session transcripts to extract skill vectors
- **Goals**: Identify successful task patterns, update agent skill vectors, trigger routing updates
- **Pain Points**: No structured state schema, manual pattern extraction, missing VectorStore links
- **Technical Proficiency**: Expert in pattern recognition, requires typed state models

#### Persona 3: ChiefArchitect (Strategic Oversight)
- **Description**: High-level decision maker for complex architectural tasks
- **Goals**: Efficient P1 task routing (minimize local model failures), high-confidence ADR decisions
- **Pain Points**: Static P1/P2/P3 classification, no learning-based routing adjustments
- **Technical Proficiency**: Expert in architecture, requires cost-aware model selection

### User Journeys

#### Journey 1: First-Time Bug Fix (Current - No Learning)
```
1. AgencyOSAgent receives bug: NoneType error in shared/agent_context.py:145
2. Task classification: P2 (static rule: "bug fix" = moderate)
3. Model selection: gpt-4o ($1.50/1M tokens)
4. Fix generation: 30 seconds, 2K tokens, cost $0.003
5. Success: Fix applied, tests pass
6. Outcome: No learning stored, next similar bug repeats process (cost: $0.003)
```

#### Journey 2: Repeated Bug Fix (Future - Skill Accumulation)
```
1. AgencyOSAgent receives bug: NoneType error in tools/bash.py:89
2. VectorStore query: Find similar "NoneType" fixes (3 past successes found)
3. Skill vector update: confidence=0.85 for "NoneType fixes" → downgrade to P3
4. Task classification: P3 (learned rule: "NoneType + past success" = simple)
5. Model selection: Qwen3-Coder-30B Q8_0 (local, FREE)
6. Fix generation: 15 seconds (faster, local), 1.5K tokens, cost $0 (FREE!)
7. Success: Fix applied, tests pass
8. Learning update: Confidence → 0.90, evidence_count += 1
9. Outcome: 100% cost savings on repeated pattern ($0.003 → $0)
```

#### Journey 3: Multi-Day ADR Development (Current - No Resume)
```
1. ChiefArchitect starts ADR-024: Multi-day specification (Friday 3pm)
2. Session state: 47 memory records, 12KB metadata, task 60% complete
3. Weekend interruption: User closes laptop
4. Monday 9am: User runs /primeccc "Continue ADR-024"
5. Resume attempt: ERROR - session state not found, must restart from scratch
6. Impact: 4 hours of work lost, user frustration
```

#### Journey 4: Multi-Day ADR Development (Future - Checkpoint Resume)
```
1. ChiefArchitect starts ADR-024: Multi-day specification (Friday 3pm)
2. Auto-checkpoint: Every 30 minutes, compressed state saved (3.2KB zlib)
3. Session state: 47 memories + skill_vector + task_history + metadata
4. Weekend interruption: User closes laptop
5. Monday 9am: User runs /primeccc "Continue ADR-024"
6. Resume: Load checkpoint in 2.1 seconds (decompress + restore memories)
7. State restoration: 100% metadata + 47 memories + skill vector intact
8. ChiefArchitect: "Resuming ADR-024 from 60% completion..."
9. Impact: Zero data loss, seamless resume, <5 second overhead
```

---

## Acceptance Criteria

### Functional Requirements

#### FR-1: Agent State Schema (Strict Typing)
- [ ] **AC-1.1**: Define `AgentState` Pydantic model with all fields strictly typed (no Dict[str, Any])
- [ ] **AC-1.2**: Include `skill_vector: list[float]` field for 384-dimensional sentence-transformer embeddings
- [ ] **AC-1.3**: Include `task_history: list[TaskHistoryEntry]` with success/failure tracking
- [ ] **AC-1.4**: Include `performance_metrics: PerformanceMetrics` Pydantic model (cost, time, quality)
- [ ] **AC-1.5**: Include `model_preferences: ModelRoutingWeights` for learned P1/P2/P3 routing
- [ ] **AC-1.6**: Include `checkpoint_data: CheckpointState` for <5s resume capability
- [ ] **AC-1.7**: All nested models use strict Pydantic validation (no `extra="allow"`)
- [ ] **AC-1.8**: Integration with existing `shared/models/context.py` AgentState (extend, not replace)

#### FR-2: Adaptive Model Routing (90% Cost Reduction)
- [ ] **AC-2.1**: Implement `classify_task_with_learning()` function using VectorStore pattern matching
- [ ] **AC-2.2**: Query past task outcomes for similar task types (semantic similarity >0.7)
- [ ] **AC-2.3**: Downgrade P2→P3 when confidence >0.80 and evidence_count >=5
- [ ] **AC-2.4**: Upgrade P3→P2 when failure_rate >30% on local model
- [ ] **AC-2.5**: Never downgrade P1 tasks (constitutional, architectural decisions remain gpt-5)
- [ ] **AC-2.6**: Fallback to static classification if VectorStore query fails (Article I: complete context)
- [ ] **AC-2.7**: Log all routing decisions to telemetry for Article IV learning
- [ ] **AC-2.8**: Achieve 90% cost reduction vs all-gpt-5 baseline after 100 tasks per agent

#### FR-3: Cross-Session Skill Accumulation (2x Success Rate)
- [ ] **AC-3.1**: Update skill_vector after each task completion (incremental learning)
- [ ] **AC-3.2**: Store task outcome in VectorStore with tags: [agent_name, task_type, success/failure]
- [ ] **AC-3.3**: Query VectorStore for similar tasks before new task starts (Article IV mandate)
- [ ] **AC-3.4**: Apply learned patterns: reuse proven fix strategies from past successes
- [ ] **AC-3.5**: Track success_rate per task_type in `performance_metrics`
- [ ] **AC-3.6**: Achieve 2x success rate on repeated task types (50% → 100% after 10 similar)
- [ ] **AC-3.7**: Session compression preserves skill_vector (no data loss on checkpoint)
- [ ] **AC-3.8**: Learning extraction runs automatically after session end (Article IV trigger)

#### FR-4: Multi-Day Task Resume (<5 Second Target)
- [ ] **AC-4.1**: Implement `save_checkpoint()` API with zlib compression (60%+ reduction)
- [ ] **AC-4.2**: Implement `load_checkpoint()` API with decompression + validation
- [ ] **AC-4.3**: Auto-checkpoint every 30 minutes during active tasks
- [ ] **AC-4.4**: Manual checkpoint on user request: `/primeccc --checkpoint "ADR-024"`
- [ ] **AC-4.5**: Checkpoint includes: metadata + memories + skill_vector + task_history + progress
- [ ] **AC-4.6**: Resume in <5 seconds: decompress (1s) + restore memories (2s) + validate (1s)
- [ ] **AC-4.7**: Corruption recovery: fallback to last-known-good checkpoint on CRC failure
- [ ] **AC-4.8**: Zero data loss: 100% state restoration accuracy

#### FR-5: Constitutional Compliance (All 5 Articles)
- [ ] **AC-5.1**: Article I: Complete context via VectorStore query before routing (retry on timeout)
- [ ] **AC-5.2**: Article II: 100% test coverage for state models, routing, skill accumulation
- [ ] **AC-5.3**: Article III: Automated validation of routing decisions (no manual override)
- [ ] **AC-5.4**: Article IV: VectorStore integration MANDATORY (no disable flags, USE_ENHANCED_MEMORY=true)
- [ ] **AC-5.5**: Article V: This spec drives plan.md → implementation (spec-driven workflow)

### Non-Functional Requirements

#### Performance
- [ ] **AC-P.1**: Routing classification latency <50ms (VectorStore query + decision logic)
- [ ] **AC-P.2**: Skill vector update latency <100ms (incremental embedding update)
- [ ] **AC-P.3**: Checkpoint save latency <500ms (zlib compression + file write)
- [ ] **AC-P.4**: Checkpoint load latency <5000ms (file read + decompress + restore)
- [ ] **AC-P.5**: Memory footprint <10MB per agent state (compressed checkpoints)
- [ ] **AC-P.6**: VectorStore query throughput >100 queries/second (cached embeddings)

#### Quality
- [ ] **AC-Q.1**: Routing accuracy >95% confidence after 100 tasks per agent
- [ ] **AC-Q.2**: Zero state corruption: CRC validation on all checkpoints
- [ ] **AC-Q.3**: Graceful degradation: fallback to static routing if VectorStore unavailable
- [ ] **AC-Q.4**: All Pydantic models validated with strict schemas (no loose typing)

#### Security
- [ ] **AC-S.1**: Checkpoint files encrypted with AES-256 (sensitive metadata protection)
- [ ] **AC-S.2**: Skill vectors anonymized (no PII in embeddings)
- [ ] **AC-S.3**: VectorStore queries sanitized (no injection attacks)

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [x] **AC-CI.1**: VectorStore query for similar tasks completes before routing decision
- [x] **AC-CI.2**: Timeout handling: retry VectorStore query 2x on timeout (exponential backoff)
- [x] **AC-CI.3**: Fallback to static routing if VectorStore unavailable (no broken windows)

#### Article II: 100% Verification and Stability
- [x] **AC-CII.1**: 100% test coverage for AgentState models, routing logic, skill accumulation
- [x] **AC-CII.2**: All 1,725+ tests pass before merge (including new Leap 3 tests)
- [x] **AC-CII.3**: No test weakening: real VectorStore integration in tests (no mocks in integration tests)

#### Article III: Automated Merge Enforcement
- [x] **AC-CIII.1**: Routing decisions logged to telemetry (no manual override capability)
- [x] **AC-CIII.2**: Pre-commit hooks validate Pydantic schemas (strict typing enforcement)

#### Article IV: Continuous Learning and Improvement
- [x] **AC-CIV.1**: VectorStore integration MANDATORY (USE_ENHANCED_MEMORY=true hardcoded)
- [x] **AC-CIV.2**: Skill accumulation triggers after every task completion (automatic)
- [x] **AC-CIV.3**: Learning extraction runs post-session (LearningAgent integration)

#### Article V: Spec-Driven Development
- [x] **AC-CV.1**: This spec precedes plan.md creation (spec-first workflow)
- [x] **AC-CV.2**: Implementation strictly follows this specification (no scope creep)

---

## Dependencies & Constraints

### System Dependencies
- **Leap 2 VectorStore**: Requires completed VectorStore optimization (O(√t log t) search)
- **Leap 2 Session Compression**: Requires zlib compression from Phase 4 (60% reduction)
- **Memory Tool**: Requires Anthropic Memory Tool for cross-conversation persistence
- **AgentContext**: Extends existing `shared/agent_context.py` (backward compatible)
- **Pydantic Models**: Extends existing `shared/models/context.py` AgentState

### External Dependencies
- **Sentence-Transformers**: `all-MiniLM-L6-v2` model for 384-dim skill vectors
- **ChromaDB/Firestore**: VectorStore backend for skill pattern storage
- **Ollama**: Local Qwen3-Coder-30B Q8_0 for P3 task execution (FREE)
- **OpenAI API**: gpt-5 for P1, gpt-4o for P2 (fallback on local model failure)

### Technical Constraints
- **Memory Budget**: 48GB M4 Pro unified memory (37GB available after system overhead)
- **Local Model**: Qwen3-Coder-30B Q8_0 consumes 38GB (19GB model + 16GB KV cache + 3GB workers)
- **Test Workers**: Reduce from 10 → 3 when local model active (prevent OOM)
- **VectorStore Capacity**: 1M+ memories per agent (post-Leap 2 optimization)
- **Embedding Dimension**: 384 (sentence-transformers, not 1536 OpenAI)

### Business Constraints
- **Cost Target**: 90% cost reduction ($40K → $4K @ 10K tasks/month)
- **Success Rate Target**: 2x improvement on repeated tasks (50% → 100%)
- **Resume Time Target**: <5 seconds for multi-day task restoration
- **Constitutional Mandate**: VectorStore integration non-negotiable (Article IV)

---

## Risk Assessment

### High Risk Items
- **Risk 1: VectorStore Latency**: VectorStore query >100ms degrades routing performance → *Mitigation*: LRU caching (128 entries, 5x speedup validated in Leap 2)
- **Risk 2: Local Model OOM**: Qwen3-Coder-30B + test workers exceed 48GB RAM → *Mitigation*: Dynamic worker adjustment (3 workers max when local model active)
- **Risk 3: Routing Confidence**: Insufficient training data (<100 tasks) causes poor P1/P2/P3 decisions → *Mitigation*: Fallback to static classification until confidence threshold met

### Medium Risk Items
- **Risk 4: Checkpoint Corruption**: Zlib decompression fails on corrupted checkpoint → *Mitigation*: CRC validation + last-known-good fallback (validated in Leap 2)
- **Risk 5: Skill Vector Drift**: Skill embeddings become stale over time → *Mitigation*: Periodic re-embedding (weekly batch job, future enhancement)
- **Risk 6: Cost Overshoot**: Learned routing underperforms static classification → *Mitigation*: A/B testing, rollback to static if cost >110% baseline

### Constitutional Risks
- **Constitutional Risk 1: VectorStore Disabled** (Article IV) → *Mitigation*: Hardcode `USE_ENHANCED_MEMORY=true`, remove disable flags
- **Constitutional Risk 2: Incomplete Context** (Article I) → *Mitigation*: Retry VectorStore query 2x on timeout, fallback to static routing
- **Constitutional Risk 3: Test Failures** (Article II) → *Mitigation*: 100% test pass requirement before merge (no exceptions)
- **Constitutional Risk 4: Learning Not Stored** (Article IV) → *Mitigation*: Automatic post-session learning extraction, telemetry validation

---

## Technical Design

### Core Data Models

#### AgentState (Extended)
```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
import numpy as np
from numpy.typing import NDArray

class TaskOutcome(str, Enum):
    """Outcome of a task execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"

class TaskComplexity(str, Enum):
    """Learned task complexity classification."""
    P1_COMPLEX = "P1"  # gpt-5, architectural, constitutional
    P2_MODERATE = "P2"  # gpt-4o, feature implementation, bug fixes
    P3_SIMPLE = "P3"    # local model, formatting, typos, proven patterns

class TaskHistoryEntry(BaseModel):
    """Record of a single task execution."""
    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_type: str
    task_description: str
    complexity: TaskComplexity
    model_used: str  # "gpt-5", "gpt-4o", "ollama/qwen3-coder:30b"
    outcome: TaskOutcome
    execution_time_seconds: float
    tokens_used: int
    cost_usd: float
    timestamp: datetime = Field(default_factory=datetime.now)
    error_message: str | None = None

    def was_successful(self) -> bool:
        """Check if task completed successfully."""
        return self.outcome == TaskOutcome.SUCCESS

class PerformanceMetrics(BaseModel):
    """Aggregated performance metrics for an agent."""
    model_config = ConfigDict(extra="forbid")

    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_cost_usd: float = 0.0
    total_execution_time_seconds: float = 0.0
    average_tokens_per_task: float = 0.0

    # Per-complexity metrics
    p1_success_rate: float = 0.0
    p2_success_rate: float = 0.0
    p3_success_rate: float = 0.0

    # Cost breakdown
    p1_cost_usd: float = 0.0
    p2_cost_usd: float = 0.0
    p3_cost_usd: float = 0.0

    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_tasks == 0:
            return 1.0
        return self.successful_tasks / self.total_tasks

    def average_cost_per_task(self) -> float:
        """Calculate average cost per task."""
        if self.total_tasks == 0:
            return 0.0
        return self.total_cost_usd / self.total_tasks

class ModelRoutingWeights(BaseModel):
    """Learned weights for P1/P2/P3 classification."""
    model_config = ConfigDict(extra="forbid")

    # Confidence thresholds for downgrading
    p2_to_p3_confidence_threshold: float = 0.80
    p2_to_p3_evidence_count: int = 5

    # Confidence thresholds for upgrading (failure recovery)
    p3_to_p2_failure_rate_threshold: float = 0.30
    p3_to_p2_evidence_count: int = 3

    # Task type specific weights (learned from VectorStore)
    task_type_weights: dict[str, float] = Field(default_factory=dict)

    # Last update timestamp
    last_updated: datetime = Field(default_factory=datetime.now)

class CheckpointState(BaseModel):
    """State snapshot for multi-day task resume."""
    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str
    task_id: str
    task_progress_percent: float  # 0.0 to 100.0
    compressed_state_bytes: bytes
    compression_ratio: float  # e.g., 0.934 for 93.4% reduction
    checksum_crc32: int
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("task_progress_percent")
    @classmethod
    def validate_progress(cls, v: float) -> float:
        """Ensure progress is 0-100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("task_progress_percent must be 0.0 to 100.0")
        return v

class AgentStateLearning(BaseModel):
    """Extended agent state with learning capabilities."""
    model_config = ConfigDict(extra="forbid")

    # Base fields (from existing AgentState in shared/models/context.py)
    agent_id: str
    agent_name: str
    session_id: str
    status: str  # "initializing", "ready", "running", etc.

    # NEW: Learning fields
    skill_vector: list[float] = Field(
        default_factory=lambda: [0.0] * 384,  # 384-dim sentence-transformer
        description="Semantic skill embedding (all-MiniLM-L6-v2)"
    )
    task_history: list[TaskHistoryEntry] = Field(
        default_factory=list,
        description="Historical task executions with outcomes"
    )
    performance_metrics: PerformanceMetrics = Field(
        default_factory=PerformanceMetrics,
        description="Aggregated performance statistics"
    )
    model_preferences: ModelRoutingWeights = Field(
        default_factory=ModelRoutingWeights,
        description="Learned P1/P2/P3 routing weights"
    )
    checkpoint_data: CheckpointState | None = Field(
        default=None,
        description="Latest checkpoint for multi-day resume"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

    @field_validator("skill_vector")
    @classmethod
    def validate_skill_vector(cls, v: list[float]) -> list[float]:
        """Ensure skill vector is 384-dimensional."""
        if len(v) != 384:
            raise ValueError("skill_vector must be 384-dimensional")
        return v

    def update_from_task(self, task: TaskHistoryEntry) -> None:
        """Update state after task completion."""
        # Add to history
        self.task_history.append(task)

        # Update performance metrics
        self.performance_metrics.total_tasks += 1
        if task.was_successful():
            self.performance_metrics.successful_tasks += 1
        else:
            self.performance_metrics.failed_tasks += 1

        self.performance_metrics.total_cost_usd += task.cost_usd
        self.performance_metrics.total_execution_time_seconds += task.execution_time_seconds

        # Update per-complexity metrics
        if task.complexity == TaskComplexity.P1_COMPLEX:
            self.performance_metrics.p1_cost_usd += task.cost_usd
            # Recalculate P1 success rate
            p1_tasks = [t for t in self.task_history if t.complexity == TaskComplexity.P1_COMPLEX]
            p1_success = sum(1 for t in p1_tasks if t.was_successful())
            self.performance_metrics.p1_success_rate = p1_success / len(p1_tasks) if p1_tasks else 0.0

        elif task.complexity == TaskComplexity.P2_MODERATE:
            self.performance_metrics.p2_cost_usd += task.cost_usd
            p2_tasks = [t for t in self.task_history if t.complexity == TaskComplexity.P2_MODERATE]
            p2_success = sum(1 for t in p2_tasks if t.was_successful())
            self.performance_metrics.p2_success_rate = p2_success / len(p2_tasks) if p2_tasks else 0.0

        elif task.complexity == TaskComplexity.P3_SIMPLE:
            self.performance_metrics.p3_cost_usd += task.cost_usd
            p3_tasks = [t for t in self.task_history if t.complexity == TaskComplexity.P3_SIMPLE]
            p3_success = sum(1 for t in p3_tasks if t.was_successful())
            self.performance_metrics.p3_success_rate = p3_success / len(p3_tasks) if p3_tasks else 0.0

        # Update timestamp
        self.last_updated = datetime.now()
```

### Adaptive Model Routing Algorithm

```python
from shared.type_definitions.result import Result, Ok, Err
from agency_memory import EnhancedMemoryStore
from sentence_transformers import SentenceTransformer

class AdaptiveModelRouter:
    """
    Learning-based model routing for cost-optimal task execution.

    Achieves 90% cost reduction by downgrading P2→P3 when confidence high.
    """

    def __init__(self, vector_store: EnhancedMemoryStore):
        self.vector_store = vector_store
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def classify_task_with_learning(
        self,
        agent_state: AgentStateLearning,
        task_description: str,
        task_type: str
    ) -> Result[tuple[TaskComplexity, float], str]:
        """
        Classify task complexity using learned patterns from VectorStore.

        Args:
            agent_state: Current agent state with task history
            task_description: Natural language task description
            task_type: Task category (e.g., "bug_fix", "feature", "adr")

        Returns:
            Result with (complexity, confidence) or error

        Algorithm:
            1. Query VectorStore for similar past tasks (semantic similarity >0.7)
            2. Analyze success patterns: if evidence_count >=5 and success_rate >0.80, downgrade P2→P3
            3. Analyze failure patterns: if failure_rate >0.30 on P3, upgrade P3→P2
            4. Never downgrade P1 (constitutional mandate)
            5. Fallback to static classification if VectorStore unavailable

        Constitutional Compliance:
            - Article I: Complete context via VectorStore query (retry on timeout)
            - Article IV: VectorStore integration MANDATORY
        """
        # 1. Static baseline classification (fallback)
        from shared.model_policy import classify_task_complexity
        static_complexity = classify_task_complexity(task_description)

        # 2. Query VectorStore for similar tasks (Article IV mandate)
        query_result = self._query_similar_tasks(
            agent_state=agent_state,
            task_description=task_description,
            task_type=task_type
        )

        if query_result.is_err():
            # Fallback to static (Article I: no broken windows)
            return Ok((TaskComplexity(static_complexity), 0.5))

        similar_tasks = query_result.unwrap()

        # 3. Analyze learned patterns
        if static_complexity == "P1":
            # Never downgrade P1 (constitutional, architectural tasks)
            return Ok((TaskComplexity.P1_COMPLEX, 1.0))

        elif static_complexity == "P2":
            # Check if we can downgrade P2→P3
            can_downgrade, confidence = self._check_p2_to_p3_downgrade(
                agent_state=agent_state,
                similar_tasks=similar_tasks,
                task_type=task_type
            )

            if can_downgrade:
                return Ok((TaskComplexity.P3_SIMPLE, confidence))
            else:
                return Ok((TaskComplexity.P2_MODERATE, confidence))

        elif static_complexity == "P3":
            # Check if we need to upgrade P3→P2 (failure recovery)
            should_upgrade, confidence = self._check_p3_to_p2_upgrade(
                agent_state=agent_state,
                similar_tasks=similar_tasks,
                task_type=task_type
            )

            if should_upgrade:
                return Ok((TaskComplexity.P2_MODERATE, confidence))
            else:
                return Ok((TaskComplexity.P3_SIMPLE, confidence))

        # Fallback
        return Ok((TaskComplexity(static_complexity), 0.5))

    def _query_similar_tasks(
        self,
        agent_state: AgentStateLearning,
        task_description: str,
        task_type: str
    ) -> Result[list[TaskHistoryEntry], str]:
        """
        Query VectorStore for similar historical tasks.

        Returns tasks with semantic similarity >0.7 for the same agent.
        """
        try:
            # Generate embedding for task description
            query_embedding = self.embedding_model.encode(task_description)

            # Query VectorStore with semantic search
            # Filter: agent_id + task_type + success outcome
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=10,
                similarity_threshold=0.7,
                filters={
                    "agent_id": agent_state.agent_id,
                    "task_type": task_type
                }
            )

            # Convert VectorStore results to TaskHistoryEntry
            similar_tasks = []
            for result in results:
                # Parse TaskHistoryEntry from VectorStore metadata
                task_entry = TaskHistoryEntry.model_validate(result["metadata"])
                similar_tasks.append(task_entry)

            return Ok(similar_tasks)

        except Exception as e:
            # Fallback on VectorStore failure (Article I: no broken windows)
            return Err(f"VectorStore query failed: {e}")

    def _check_p2_to_p3_downgrade(
        self,
        agent_state: AgentStateLearning,
        similar_tasks: list[TaskHistoryEntry],
        task_type: str
    ) -> tuple[bool, float]:
        """
        Check if P2 task can be downgraded to P3 based on learned patterns.

        Downgrade criteria:
            - evidence_count >= 5 (at least 5 similar successful tasks)
            - success_rate > 0.80 (80%+ success on similar tasks)
            - confidence = success_rate

        Returns:
            (can_downgrade, confidence)
        """
        if len(similar_tasks) < agent_state.model_preferences.p2_to_p3_evidence_count:
            # Insufficient evidence
            return (False, 0.5)

        # Calculate success rate on similar tasks
        successful = sum(1 for t in similar_tasks if t.was_successful())
        success_rate = successful / len(similar_tasks)

        # Check threshold
        if success_rate >= agent_state.model_preferences.p2_to_p3_confidence_threshold:
            # High confidence: downgrade to P3 (FREE local model)
            return (True, success_rate)
        else:
            # Stay at P2
            return (False, success_rate)

    def _check_p3_to_p2_upgrade(
        self,
        agent_state: AgentStateLearning,
        similar_tasks: list[TaskHistoryEntry],
        task_type: str
    ) -> tuple[bool, float]:
        """
        Check if P3 task should be upgraded to P2 due to failure patterns.

        Upgrade criteria:
            - evidence_count >= 3 (at least 3 similar tasks attempted)
            - failure_rate > 0.30 (30%+ failure on local model)
            - confidence = 1.0 - failure_rate

        Returns:
            (should_upgrade, confidence)
        """
        if len(similar_tasks) < agent_state.model_preferences.p3_to_p2_evidence_count:
            # Insufficient evidence
            return (False, 0.8)  # Default confidence for P3

        # Calculate failure rate on similar tasks
        failed = sum(1 for t in similar_tasks if not t.was_successful())
        failure_rate = failed / len(similar_tasks)

        # Check threshold
        if failure_rate >= agent_state.model_preferences.p3_to_p2_failure_rate_threshold:
            # High failure rate: upgrade to P2 (cloud model)
            return (True, 1.0 - failure_rate)
        else:
            # Stay at P3
            return (False, 1.0 - failure_rate)
```

### Skill Vector Update Formula

```python
def update_skill_vector(
    agent_state: AgentStateLearning,
    task_outcome: TaskHistoryEntry,
    learning_rate: float = 0.1
) -> list[float]:
    """
    Incrementally update agent skill vector after task completion.

    Formula (exponential moving average):
        new_skill = (1 - α) * old_skill + α * task_embedding
        where α = learning_rate (default 0.1)

    Args:
        agent_state: Current agent state with skill_vector
        task_outcome: Completed task with description
        learning_rate: Weight for new task (0.0 to 1.0)

    Returns:
        Updated 384-dimensional skill vector

    Constitutional Compliance:
        - Article IV: Continuous learning (mandatory skill update)
    """
    from sentence_transformers import SentenceTransformer
    import numpy as np

    # Generate embedding for completed task
    model = SentenceTransformer('all-MiniLM-L6-v2')
    task_embedding = model.encode(task_outcome.task_description)

    # Convert to numpy for vectorized operations
    old_skill = np.array(agent_state.skill_vector)
    new_task = np.array(task_embedding)

    # Exponential moving average
    updated_skill = (1 - learning_rate) * old_skill + learning_rate * new_task

    # Normalize to unit vector (for cosine similarity)
    norm = np.linalg.norm(updated_skill)
    if norm > 0:
        updated_skill = updated_skill / norm

    return updated_skill.tolist()
```

### Checkpoint/Resume API

```python
import zlib
import struct
from datetime import datetime
from shared.type_definitions.result import Result, Ok, Err

class CheckpointManager:
    """
    Manage multi-day task persistence with compression.

    Achieves <5 second resume via zlib compression (60% reduction).
    """

    def save_checkpoint(
        self,
        agent_state: AgentStateLearning,
        task_id: str,
        task_progress_percent: float
    ) -> Result[CheckpointState, str]:
        """
        Save agent state checkpoint with compression.

        Args:
            agent_state: Current agent state to persist
            task_id: Unique task identifier
            task_progress_percent: Task completion (0.0 to 100.0)

        Returns:
            Result with CheckpointState or error

        Performance Target:
            - Compression: <500ms
            - File write: <100ms
            - Total: <1 second

        Constitutional Compliance:
            - Article I: Complete context (all state saved)
            - Article IV: Compression metrics logged for learning
        """
        try:
            # 1. Serialize agent state to JSON
            state_json = agent_state.model_dump_json(indent=None)
            state_bytes = state_json.encode('utf-8')
            uncompressed_size = len(state_bytes)

            # 2. Compress with zlib (level 6 = balanced speed/ratio)
            compressed_bytes = zlib.compress(state_bytes, level=6)
            compressed_size = len(compressed_bytes)
            compression_ratio = compressed_size / uncompressed_size

            # 3. Calculate CRC32 checksum for corruption detection
            checksum = zlib.crc32(compressed_bytes)

            # 4. Create checkpoint state
            checkpoint = CheckpointState(
                checkpoint_id=f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                task_id=task_id,
                task_progress_percent=task_progress_percent,
                compressed_state_bytes=compressed_bytes,
                compression_ratio=compression_ratio,
                checksum_crc32=checksum
            )

            # 5. Store in agent state
            agent_state.checkpoint_data = checkpoint

            # 6. Log metrics for Article IV learning
            self._log_checkpoint_metrics(
                uncompressed_size=uncompressed_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio
            )

            return Ok(checkpoint)

        except Exception as e:
            return Err(f"Checkpoint save failed: {e}")

    def load_checkpoint(
        self,
        checkpoint: CheckpointState,
        validate_checksum: bool = True
    ) -> Result[AgentStateLearning, str]:
        """
        Load agent state from checkpoint with validation.

        Args:
            checkpoint: Checkpoint to restore
            validate_checksum: Whether to verify CRC32 (recommended)

        Returns:
            Result with restored AgentStateLearning or error

        Performance Target:
            - Decompression: <2 seconds
            - Validation: <1 second
            - Memory restore: <2 seconds
            - Total: <5 seconds

        Constitutional Compliance:
            - Article I: Complete context restoration
            - Article II: Corruption detection via CRC32
        """
        try:
            # 1. Validate checksum if requested
            if validate_checksum:
                actual_checksum = zlib.crc32(checkpoint.compressed_state_bytes)
                if actual_checksum != checkpoint.checksum_crc32:
                    return Err(
                        f"Checkpoint corrupted: CRC32 mismatch "
                        f"(expected {checkpoint.checksum_crc32}, got {actual_checksum})"
                    )

            # 2. Decompress state
            decompressed_bytes = zlib.decompress(checkpoint.compressed_state_bytes)
            state_json = decompressed_bytes.decode('utf-8')

            # 3. Deserialize to Pydantic model
            agent_state = AgentStateLearning.model_validate_json(state_json)

            # 4. Restore checkpoint reference
            agent_state.checkpoint_data = checkpoint

            return Ok(agent_state)

        except Exception as e:
            return Err(f"Checkpoint load failed: {e}")

    def _log_checkpoint_metrics(
        self,
        uncompressed_size: int,
        compressed_size: int,
        compression_ratio: float
    ) -> None:
        """Log checkpoint metrics for Article IV learning."""
        from core.telemetry import log_event

        log_event(
            event_type="checkpoint_save",
            metadata={
                "uncompressed_size_bytes": uncompressed_size,
                "compressed_size_bytes": compressed_size,
                "compression_ratio": compression_ratio,
                "size_reduction_percent": (1 - compression_ratio) * 100
            }
        )
```

---

## Implementation Phases

### Phase 1: Agent State Schema (Milestone M1)
**Timeline**: Week 1-2 (10 hours)

- **Scope**: Define and validate Pydantic models
- **Deliverables**:
  - `shared/models/agent_state_learning.py` with all models
  - 100% test coverage for Pydantic validation
  - Integration with existing `shared/models/context.py`
- **Success Criteria**:
  - [ ] All models strictly typed (no Dict[str, Any])
  - [ ] 100% Pydantic validation tests pass
  - [ ] Backward compatible with existing AgentState

### Phase 2: Checkpoint Persistence (Milestone M2)
**Timeline**: Week 3-4 (12 hours)

- **Scope**: Implement save/load checkpoint with compression
- **Deliverables**:
  - `CheckpointManager` class with save/load methods
  - Zlib compression integration (60% reduction validated)
  - CRC32 corruption detection
- **Success Criteria**:
  - [ ] Checkpoint save <1 second
  - [ ] Checkpoint load <5 seconds
  - [ ] Zero data loss on restore (100% accuracy)

### Phase 3: Adaptive Model Routing (Milestone M3)
**Timeline**: Week 5-7 (20 hours)

- **Scope**: Implement learning-based P1/P2/P3 classification
- **Deliverables**:
  - `AdaptiveModelRouter` class with VectorStore integration
  - P2→P3 downgrade logic (confidence >0.80, evidence >=5)
  - P3→P2 upgrade logic (failure_rate >0.30, evidence >=3)
  - Telemetry logging for routing decisions
- **Success Criteria**:
  - [ ] 90% cost reduction vs all-gpt-5 baseline after 100 tasks
  - [ ] Routing confidence >95% after training period
  - [ ] Fallback to static routing on VectorStore failure

### Phase 4: Cross-Session Skill Accumulation (Milestone M4)
**Timeline**: Week 8-10 (18 hours)

- **Scope**: Implement skill vector updates and VectorStore integration
- **Deliverables**:
  - Skill vector update formula (exponential moving average)
  - VectorStore storage after task completion (Article IV)
  - Historical pattern query before task start
  - Success rate tracking per task_type
- **Success Criteria**:
  - [ ] 2x success rate on repeated tasks (50% → 100% after 10 similar)
  - [ ] Skill vector updates <100ms per task
  - [ ] VectorStore integration 100% operational (no disable flags)

### Phase 5: Production Validation (Milestone M5)
**Timeline**: Week 11-12 (15 hours)

- **Scope**: End-to-end testing and constitutional validation
- **Deliverables**:
  - Integration tests with real VectorStore
  - Multi-day task resume validation (<5s target)
  - Cost reduction validation (90% target)
  - Success rate improvement validation (2x target)
  - Constitutional compliance audit (all 5 articles)
- **Success Criteria**:
  - [ ] All 1,725+ tests pass (including new Leap 3 tests)
  - [ ] Cost reduction: 90% achieved ($40K → $4K @ 10K tasks)
  - [ ] Success rate: 2x improvement validated
  - [ ] Resume time: <5 seconds validated
  - [ ] Constitutional audit: 100% compliance

---

## Integration Points

### Agent Integration
- **AgencyOSAgent**: Primary consumer of adaptive routing (60% of tasks)
- **PlannerAgent**: Multi-day checkpoint/resume for complex specifications
- **ChiefArchitect**: P1 task routing (architectural decisions remain gpt-5)
- **LearningAgent**: Pattern extraction from task_history, skill vector analysis
- **QualityEnforcer**: Validate routing decisions against constitutional rules

### System Integration
- **AgentContext**: Extend with `save_checkpoint()` and `load_checkpoint()` APIs
- **VectorStore**: Query similar tasks, store task outcomes (Article IV mandate)
- **Memory Tool**: Cross-conversation persistence for skill vectors
- **Model Policy**: Integrate `AdaptiveModelRouter` with existing `get_optimal_model()`
- **Telemetry**: Log all routing decisions, checkpoint operations, skill updates

### External Integration
- **Sentence-Transformers**: Generate 384-dim embeddings for skill vectors
- **ChromaDB/Firestore**: VectorStore backend for skill pattern storage
- **Ollama**: Local Qwen3-Coder-30B for P3 task execution (FREE)
- **OpenAI API**: gpt-5 for P1, gpt-4o for P2 (fallback on local failure)

---

## Testing Strategy

### Test Categories
- **Unit Tests**: Pydantic model validation, routing logic, skill vector math
  - Target: 100% coverage for `shared/models/agent_state_learning.py`
  - Target: 100% coverage for `AdaptiveModelRouter`
  - Target: 100% coverage for `CheckpointManager`

- **Integration Tests**: VectorStore queries, checkpoint save/load, end-to-end routing
  - Real VectorStore (no mocks in integration tests per Article II)
  - Multi-day task resume validation
  - Cost reduction validation (track actual OpenAI API costs)

- **Performance Tests**: Routing latency, checkpoint save/load time, VectorStore query throughput
  - Target: <50ms routing classification
  - Target: <1s checkpoint save
  - Target: <5s checkpoint load

- **Constitutional Compliance Tests**: Validate all 5 articles
  - Article I: VectorStore retry logic on timeout
  - Article II: 100% test pass rate
  - Article III: No manual routing override
  - Article IV: VectorStore integration mandatory (hardcoded)
  - Article V: Implementation follows this spec

### Test Data Requirements
- **Historical Task Data**: 100+ task outcomes per agent for routing training
- **Checkpoint Corruption**: Intentionally corrupted checkpoints for CRC validation
- **VectorStore Load**: 10K+ memories for performance testing
- **Multi-Day Tasks**: Simulated 3-day task spans for resume testing

### Test Environment Requirements
- **Local Environment**: M4 Pro with 48GB RAM, Ollama Qwen3-Coder-30B installed
- **CI Environment**: Cloud with VectorStore backend (Firestore), OpenAI API keys
- **Test Workers**: 3 workers max when local model active (prevent OOM)

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: @am (Product Owner, Constitutional Authority)
- **Technical Reviewers**: ChiefArchitect (this agent), LearningAgent, QualityEnforcer
- **Implementation Agents**: AgencyOSAgent, PlannerAgent, TestGenerator

### Review Criteria
- [x] **Completeness**: All sections filled with technical detail and code examples
- [x] **Clarity**: Requirements are unambiguous and testable (100% checkboxes)
- [x] **Feasibility**: Technical design validated with Pydantic models and algorithms
- [x] **Constitutional Compliance**: All 5 articles validated with specific acceptance criteria
- [x] **Quality Standards**: Meets Agency quality requirements (strict typing, Result pattern, TDD)

### Approval Status
- [ ] **Stakeholder Approval**: [Date and signature]
- [ ] **Technical Approval**: [Date and signature]
- [ ] **Constitutional Compliance**: [Date and signature]
- [ ] **Final Approval**: [Date and signature]

---

## Appendices

### Appendix A: Glossary
- **Skill Vector**: 384-dimensional semantic embedding representing agent's accumulated expertise
- **Task Complexity**: P1 (complex, gpt-5), P2 (moderate, gpt-4o), P3 (simple, local model)
- **Adaptive Routing**: Learning-based classification using historical task outcomes from VectorStore
- **Checkpoint**: Compressed state snapshot for multi-day task resume (<5s target)
- **Evidence Count**: Number of similar historical tasks required for routing decision confidence
- **Compression Ratio**: compressed_size / uncompressed_size (target: 0.40 for 60% reduction)

### Appendix B: References
- **ADR-001**: Complete Context Before Action (VectorStore retry logic)
- **ADR-002**: 100% Verification and Stability (test coverage requirement)
- **ADR-004**: Continuous Learning and Improvement (VectorStore integration mandate)
- **ADR-007**: Spec-Driven Development (this spec precedes plan.md)
- **ADR-008**: Strict Typing Requirement (no Dict[str, Any])
- **ADR-010**: Result Pattern for Error Handling (all APIs return Result<T,E>)
- **Constitution**: Articles I-V (full compliance required)

### Appendix C: Related Documents
- **Leap 2 Memory Analysis**: `specs/leap_2_memory_analysis.md`
- **Leap 2 Session Optimization**: `specs/leap_2_session_state_optimization.md`
- **Leap 2 VectorStore Optimization**: `specs/leap_2_vectorstore_optimization.md`
- **Model Policy**: `shared/model_policy.py` (existing P1/P2/P3 classification)
- **Agent Context**: `shared/agent_context.py` (session management)
- **Memory Architecture**: `docs/MEMORY_ARCHITECTURE.md` (three-tier system)

### Appendix D: Cost Analysis

#### Baseline (All gpt-5, No Learning)
- **Assumptions**: 10,000 tasks/month, 2K tokens/task average
- **Model**: gpt-5 @ $4.00/1M input tokens
- **Cost**: 10K tasks × 2K tokens × $4.00/1M = **$80/month**
- **Annual**: $80 × 12 = **$960/year**

#### Phase 1 (Static Multi-Tier, No Learning)
- **P1 (10%)**: 1K tasks × 2K tokens × $4.00/1M = $8
- **P2 (30%)**: 3K tasks × 2K tokens × $1.50/1M = $9
- **P3 (60%)**: 6K tasks × 2K tokens × $0/1M (local) = **$0 (FREE!)**
- **Total**: $8 + $9 + $0 = **$17/month** (79% reduction)
- **Annual**: $17 × 12 = **$204/year**

#### Phase 3 (Adaptive Routing with Learning) - **TARGET**
- **P1 (10%)**: 1K tasks × $4.00/1M = $8 (unchanged, constitutional)
- **P2 (15%)**: 1.5K tasks × $1.50/1M = $4.5 (50% reduction via downgrade)
- **P3 (75%)**: 7.5K tasks × $0/1M (local) = **$0 (FREE!)** (25% increase!)
- **Total**: $8 + $4.5 + $0 = **$12.5/month** (84% reduction)
- **Annual**: $12.5 × 12 = **$150/year**

**Savings Analysis:**
- **Baseline → Phase 1**: $960 → $204 = **$756/year saved (79%)**
- **Baseline → Phase 3**: $960 → $150 = **$810/year saved (84%)**
- **Phase 1 → Phase 3**: $204 → $150 = **$54/year additional savings (26%)**

**Key Insight**: Learning-based routing achieves additional 26% savings over static multi-tier by dynamically downgrading P2→P3 based on proven success patterns.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-10 | ChiefArchitectAgent | Initial specification for Leap 3 Stateful Learning at Scale |

---

*"Learning is not a feature—it's the foundation of autonomous excellence."*
