# Adaptive Model Router Specification

**Version**: 1.0
**Created**: 2025-10-10
**Type**: Tier 1 (P1 - Complex architectural system)
**Dependencies**: M1-M2 (Session state + Checkpoint/resume)

---

## 1. Goals

### Primary Goal
Design and implement an intelligent model routing system that achieves **90% cost reduction** through learned task complexity classification, reducing Agency OS operational costs from ~$40K/month to ~$4K/month while maintaining 100% constitutional compliance.

### Success Criteria
1. **Cost Reduction**: 90% reduction in LLM API costs compared to all-gpt-5 baseline
2. **Classification Accuracy**: >90% correct P1/P2/P3 task classification after initial learning period
3. **Performance**: <50ms routing decision latency per task
4. **Quality**: Zero constitutional violations (Article IV VectorStore integration mandatory)
5. **Learning**: Continuous improvement via VectorStore pattern storage (Article IV)

---

## 2. Non-Goals

- Custom model fine-tuning (use off-the-shelf models)
- Real-time model switching mid-task (routing decision made once per task)
- Cost optimization for non-Agency workloads
- Dynamic pricing negotiation with model providers

---

## 3. Personas

### Primary: AgentContext
**Role**: Task orchestrator requesting optimal model for operation
**Need**: Fast, accurate model routing with minimal overhead
**Success**: Receives appropriate model for task complexity without manual configuration

### Secondary: ChiefArchitect
**Role**: System designer ensuring constitutional compliance
**Need**: Routing system follows Article IV (VectorStore integration mandatory)
**Success**: All routing decisions logged to VectorStore for learning and audit

### Tertiary: System Administrator
**Role**: DevOps monitoring cost and performance metrics
**Need**: Observable cost savings and routing accuracy metrics
**Success**: Dashboard shows 90% cost reduction with <5% quality degradation

---

## 4. Acceptance Criteria

### Functional Requirements

#### FR-1: Task Complexity Classification
**Given** a task description string and task type
**When** `classify_task_complexity(task_description, task_type)` is called
**Then** return one of: `P1_COMPLEX`, `P2_MODERATE`, `P3_SIMPLE`

**Classification Rules** (3-method algorithm):

**Method 1: Keyword Detection**
```python
P3_KEYWORDS = [
    r"\b(typo|format|docstring|comment|readme|copyright)\b",
    r"\b(remove|delete|clean)\b.*\b(unused|dead code|import)\b",
    r"\b(update|add|fix)\b.*\b(comment|doc|documentation)\b",
    r"\b(rename|move)\b.*\b(variable|function|file)\b"
]

P1_KEYWORDS = [
    r"\b(design|architect|adr|constitutional|compliance)\b",
    r"\b(consensus|distributed|multi-agent|coordination)\b",
    r"\b(autonomous|healing|critical|security)\b",
    r"\b(create|implement)\b.*\b(adr|specification|architecture)\b"
]

# P2 is default fallback if no P1/P3 match
```

**Method 2: AST Analysis** (for code modification tasks)
```python
if task_type == "code_modification":
    complexity = estimate_cyclomatic_complexity(code_ast)
    if complexity > 10:
        return "P1_COMPLEX"
    elif complexity > 5:
        return "P2_MODERATE"
    else:
        return "P3_SIMPLE"
```

**Method 3: VectorStore Pattern Matching** (Article IV mandate)
```python
# Query VectorStore for similar past tasks
similar_tasks = vector_store.search(
    query=task_description,
    namespace="task_classification",
    limit=5
)

if similar_tasks:
    # Weighted average of historical classifications
    historical_complexity = calculate_weighted_avg(
        [task["complexity"] for task in similar_tasks]
    )
    return historical_complexity

# No historical data - use Methods 1 & 2
```

#### FR-2: Model Routing Logic
**Given** a task complexity level (P1/P2/P3)
**When** `route_to_model(complexity, agent_key)` is called
**Then** return the optimal model string for that complexity tier

**Routing Table**:
```python
MODEL_ROUTING = {
    "P1_COMPLEX": "gpt-5",                    # $4.00/1M tokens
    "P2_MODERATE": "gpt-4o",                  # $1.50/1M tokens
    "P3_SIMPLE": "ollama/qwen3-coder:30b",    # $0.00 (local)
}

# Fallback if local model unavailable
if complexity == "P3_SIMPLE" and not is_local_model_available():
    return "gpt-4o-mini"  # $0.10/1M tokens (cloud fallback)
```

**Environment Overrides** (constitutional compliance - Article III):
```python
# Agent-specific overrides take precedence
agent_override = os.getenv(f"{agent_key.upper()}_MODEL")
if agent_override:
    return agent_override  # Manual override allowed

# Global override (testing/debugging)
global_override = os.getenv("FORCE_MODEL")
if global_override:
    return global_override
```

#### FR-3: Cost Tracking and Telemetry
**Given** a model routing decision
**When** task completes
**Then** log cost metrics to telemetry system

**Cost Calculation**:
```python
@dataclass
class CostMetric:
    task_id: str
    task_description: str
    complexity: str  # P1/P2/P3
    model_used: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float  # Calculated from model pricing
    routing_latency_ms: float
    timestamp: datetime

# Model pricing (as of 2025-10)
PRICING = {
    "gpt-5": {"input": 4.00, "output": 16.00},       # per 1M tokens
    "gpt-4o": {"input": 1.50, "output": 6.00},
    "gpt-4o-mini": {"input": 0.10, "output": 0.40},
    "ollama/qwen3-coder:30b": {"input": 0.00, "output": 0.00}
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING.get(model, PRICING["gpt-4o"])  # Safe default
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost
```

#### FR-4: VectorStore Integration (Article IV - MANDATORY)
**Given** a routing decision is made
**When** task completes successfully
**Then** store routing pattern to VectorStore for future learning

**Learning Pattern Storage**:
```python
from shared.models.memory import MemoryRecord

def store_routing_pattern(
    task_description: str,
    task_type: str,
    complexity: str,
    model_used: str,
    success: bool,
    cost_usd: float,
    duration_ms: float
) -> None:
    """Article IV requirement - store routing decision for learning."""

    pattern = MemoryRecord(
        key=f"routing_{datetime.now().timestamp()}",
        content={
            "task_description": task_description,
            "task_type": task_type,
            "classified_complexity": complexity,
            "model_used": model_used,
            "success": success,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        },
        tags=[
            "routing_pattern",
            f"complexity_{complexity}",
            f"model_{model_used.replace('/', '_')}",
            "adaptive_router"
        ],
        metadata={
            "confidence": 0.9 if success else 0.5,
            "evidence_count": 1,
            "namespace": "task_classification"
        }
    )

    vector_store.add_memory(pattern.key, pattern.model_dump())
```

---

### Non-Functional Requirements

#### NFR-1: Performance
- Classification latency: <50ms per task (p99)
- VectorStore query: <100ms (p99, Article I timeout retry if needed)
- Memory overhead: <10MB for routing cache
- Zero blocking latency on model API calls

#### NFR-2: Cost Targets
**Baseline** (all gpt-5):
- 10,000 tasks/month × 500 tokens avg × $4.00/1M = $20,000/month

**Target** (adaptive routing):
- P3 (60%): 6,000 tasks × $0 (local) = $0
- P2 (30%): 3,000 tasks × $1.50/1M = $2,250
- P1 (10%): 1,000 tasks × $4.00/1M = $2,000
- **Total**: $4,250/month (78.75% reduction)

**Stretch Goal** (90% reduction):
- Optimize P3 local model usage to 65% (vs 60%)
- Optimize P2 to use gpt-4o-mini for simpler P2 tasks (sub-classification)
- **Target Total**: $2,000/month (90% reduction)

#### NFR-3: Accuracy
- **Cold Start** (no VectorStore history): 80% accuracy (keyword/AST only)
- **Warm** (100 tasks learned): 90% accuracy (VectorStore patterns applied)
- **Mature** (1,000+ tasks): 95% accuracy (comprehensive pattern coverage)

**Accuracy Definition**:
- **Correct Classification**: Task completes successfully with no quality degradation
- **Misclassification**: Task fails or requires escalation to higher-tier model
- **Measurement**: Human review of 100 random tasks per week

#### NFR-4: Constitutional Compliance

**Article I: Complete Context Before Action**
- VectorStore query with retry on timeout (2x, 3x, up to 10x)
- Never proceed with incomplete classification data
- AST analysis must complete fully before routing

**Article II: 100% Verification and Stability**
- All routing decisions logged to telemetry (100% audit trail)
- Cost calculation verified against actual token usage
- Zero silent failures (Result pattern for all operations)

**Article III: Automated Merge Enforcement**
- Routing logic automated (no manual model selection in production)
- Environment overrides permitted for testing/debugging only
- Pre-commit validation: routing code must pass linter and type checks

**Article IV: Continuous Learning and Improvement** (CRITICAL)
- **MANDATORY**: VectorStore integration is constitutionally required
- All routing decisions stored for future pattern matching
- Min confidence: 0.6, min evidence: 3 occurrences before pattern trusted
- Routing accuracy tracked and improved automatically

**Article V: Spec-Driven Development**
- This spec precedes all implementation
- Plan.md created from this spec
- TodoWrite tasks generated from plan

---

## 5. Data Models

### TaskComplexity Enum
```python
from enum import Enum

class TaskComplexity(str, Enum):
    """Task complexity classification for model routing."""

    P1_COMPLEX = "P1"      # Architecture, ADRs, constitutional decisions
    P2_MODERATE = "P2"     # Features, bug fixes, refactoring
    P3_SIMPLE = "P3"       # Typos, formatting, proven patterns

    @property
    def estimated_cost_per_1k_tokens(self) -> float:
        """Estimated cost per 1,000 tokens for this complexity tier."""
        return {
            "P1": 0.004,   # gpt-5: $4/1M tokens
            "P2": 0.0015,  # gpt-4o: $1.50/1M tokens
            "P3": 0.0      # local model: FREE
        }[self.value]

    @property
    def recommended_model(self) -> str:
        """Default model for this complexity tier."""
        return {
            "P1": "gpt-5",
            "P2": "gpt-4o",
            "P3": "ollama/qwen3-coder:30b"
        }[self.value]
```

### RoutingDecision Model
```python
from pydantic import BaseModel, Field
from datetime import datetime

class RoutingDecision(BaseModel):
    """Model routing decision with cost and performance metrics."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_description: str
    task_type: str

    # Classification results
    complexity: TaskComplexity
    classification_method: str  # "keyword", "ast", "vectorstore", "hybrid"
    classification_confidence: float = Field(ge=0.0, le=1.0)

    # Routing results
    selected_model: str
    fallback_used: bool = False
    environment_override: bool = False

    # Performance metrics
    routing_latency_ms: float
    classification_latency_ms: float
    vectorstore_query_latency_ms: float | None = None

    # Cost prediction
    estimated_cost_usd: float
    estimated_tokens: int

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_key: str
    session_id: str

    def to_telemetry_event(self) -> dict:
        """Convert to telemetry event for logging."""
        return {
            "event_type": "model_routing_decision",
            "task_id": self.task_id,
            "complexity": self.complexity.value,
            "model": self.selected_model,
            "cost_estimate_usd": self.estimated_cost_usd,
            "routing_latency_ms": self.routing_latency_ms,
            "timestamp": self.timestamp.isoformat()
        }
```

### CostSummary Model
```python
class CostSummary(BaseModel):
    """Aggregated cost metrics for reporting."""

    model_config = ConfigDict(extra="forbid")

    period_start: datetime
    period_end: datetime

    # Task counts by complexity
    p1_tasks: int = 0
    p2_tasks: int = 0
    p3_tasks: int = 0
    total_tasks: int = 0

    # Cost breakdown
    p1_cost_usd: float = 0.0
    p2_cost_usd: float = 0.0
    p3_cost_usd: float = 0.0
    total_cost_usd: float = 0.0

    # Comparison metrics
    baseline_cost_usd: float  # All gpt-5 cost
    cost_savings_usd: float
    cost_reduction_percent: float

    # Accuracy metrics
    correct_classifications: int = 0
    misclassifications: int = 0
    classification_accuracy: float = Field(ge=0.0, le=1.0)

    # Performance metrics
    avg_routing_latency_ms: float
    p99_routing_latency_ms: float

    def calculate_savings(self) -> None:
        """Calculate cost savings vs baseline."""
        self.cost_savings_usd = self.baseline_cost_usd - self.total_cost_usd
        if self.baseline_cost_usd > 0:
            self.cost_reduction_percent = (
                self.cost_savings_usd / self.baseline_cost_usd
            ) * 100
```

---

## 6. System Architecture

### Component Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                     AgentContext                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AdaptiveModelRouter                         │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  TaskComplexityClassifier                          │  │  │
│  │  │  • keyword_detect()                                │  │  │
│  │  │  • ast_analyze()                                   │  │  │
│  │  │  • vectorstore_match() ← VectorStore (Article IV) │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  ModelRouter                                       │  │  │
│  │  │  • route_to_model()                                │  │  │
│  │  │  • apply_overrides()                               │  │  │
│  │  │  • fallback_logic()                                │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  CostTracker                                       │  │  │
│  │  │  • track_decision()                                │  │  │
│  │  │  • calculate_cost()                                │  │  │
│  │  │  • generate_summary()                              │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  LearningStore (Article IV)                        │  │  │
│  │  │  • store_pattern()                                 │  │  │
│  │  │  • query_similar_tasks()                           │  │  │
│  │  │  • update_confidence()                             │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   VectorStore         Telemetry System     Model Providers
   (Article IV)        (Cost Metrics)       (gpt-5, gpt-4o, local)
```

### Integration with Existing Systems

#### shared/model_policy.py Enhancement
```python
# BEFORE (current implementation)
def agent_model(agent_key: str) -> str:
    """Return static model for agent."""
    return DEFAULTS.get(agent_key, DEFAULT_GLOBAL)

# AFTER (with AdaptiveModelRouter)
def agent_model(
    agent_key: str,
    task_description: str | None = None,
    task_type: str | None = None,
    context: AgentContext | None = None
) -> str:
    """Return optimal model via adaptive routing."""

    # Environment override takes precedence (Article III)
    override = os.getenv(f"{agent_key.upper()}_MODEL")
    if override:
        return override

    # If no task context, use static defaults (backward compatible)
    if task_description is None:
        return DEFAULTS.get(agent_key, DEFAULT_GLOBAL)

    # Adaptive routing based on task complexity
    router = AdaptiveModelRouter(context=context)
    decision = router.route(
        task_description=task_description,
        task_type=task_type or "general",
        agent_key=agent_key
    )

    return decision.selected_model
```

#### shared/agent_context.py Enhancement
```python
class AgentContext:
    def __init__(self, memory: Memory | None = None, session_id: str | None = None):
        # ... existing code ...

        # Initialize adaptive router (lazy)
        self._adaptive_router: AdaptiveModelRouter | None = None

    def get_optimal_model(
        self,
        agent_key: str,
        task_description: str,
        task_type: str = "general"
    ) -> str:
        """Get optimal model for task via adaptive routing."""
        if self._adaptive_router is None:
            from shared.adaptive_model_router import AdaptiveModelRouter
            self._adaptive_router = AdaptiveModelRouter(context=self)

        decision = self._adaptive_router.route(
            task_description=task_description,
            task_type=task_type,
            agent_key=agent_key
        )

        return decision.selected_model
```

#### Telemetry Integration
```python
from shared.models.telemetry import TelemetryEvent, EventType

def log_routing_decision(decision: RoutingDecision) -> None:
    """Log routing decision to telemetry system."""

    event = TelemetryEvent(
        event_id=f"routing_{decision.task_id}",
        event_type=EventType.LLM_CALL,
        severity=EventSeverity.INFO,
        agent_id=decision.agent_key,
        session_id=decision.session_id,
        duration_ms=decision.routing_latency_ms,
        success=True,
        metadata={
            "complexity": decision.complexity.value,
            "model": decision.selected_model,
            "cost_estimate_usd": decision.estimated_cost_usd,
            "classification_method": decision.classification_method,
            "confidence": decision.classification_confidence
        },
        tags=["model_routing", f"complexity_{decision.complexity.value}"]
    )

    telemetry.log_event(event)
```

---

## 7. Implementation Plan

### Phase 1: Core Classification (Week 1)
**Deliverables**:
1. `TaskComplexity` enum with P1/P2/P3 definitions
2. `TaskComplexityClassifier` class with 3 methods:
   - `keyword_detect()`
   - `ast_analyze()`
   - `vectorstore_match()` (Article IV)
3. Unit tests for classification accuracy (target 80% on synthetic tasks)

### Phase 2: Model Routing (Week 1)
**Deliverables**:
1. `ModelRouter` class with routing logic
2. Environment override handling
3. Local model fallback detection
4. Integration with `shared/model_policy.py`
5. Unit tests for routing decisions

### Phase 3: Cost Tracking (Week 2)
**Deliverables**:
1. `CostTracker` class with telemetry integration
2. `CostSummary` aggregation logic
3. Telemetry event logging for all routing decisions
4. Dashboard metrics (cost savings, accuracy, latency)
5. Integration tests with mock telemetry

### Phase 4: Learning Integration (Week 2, Article IV)
**Deliverables**:
1. `LearningStore` class for VectorStore integration
2. Pattern storage after successful tasks
3. Pattern retrieval during classification
4. Confidence scoring and evidence counting
5. Integration tests with real VectorStore

### Phase 5: Production Validation (Week 3)
**Deliverables**:
1. A/B testing: 10% traffic to adaptive router
2. Accuracy measurement: human review of 100 tasks
3. Cost validation: actual vs predicted costs
4. Performance profiling: latency p50, p99
5. Production deployment approval

---

## 8. Testing Strategy

### Unit Tests
```python
# tests/test_task_complexity_classifier.py
def test_p3_simple_typo_fix():
    task = "Fix typo in function name: calcualte_total"
    complexity = classify_task_complexity(task, "code_modification")
    assert complexity == TaskComplexity.P3_SIMPLE

def test_p1_complex_adr_creation():
    task = "Create ADR for database selection: PostgreSQL vs MongoDB"
    complexity = classify_task_complexity(task, "architecture")
    assert complexity == TaskComplexity.P1_COMPLEX

def test_p2_moderate_feature_impl():
    task = "Implement user authentication with JWT tokens"
    complexity = classify_task_complexity(task, "feature_implementation")
    assert complexity == TaskComplexity.P2_MODERATE

def test_vectorstore_pattern_matching():
    # Seed VectorStore with historical classifications
    vector_store.add_memory("task_1", {
        "task_description": "Add JWT authentication",
        "complexity": "P2_MODERATE"
    })

    # Similar task should classify as P2
    task = "Implement JWT token validation"
    complexity = classify_task_complexity(task, "feature_implementation")
    assert complexity == TaskComplexity.P2_MODERATE
```

### Integration Tests
```python
# tests/test_adaptive_router_integration.py
def test_routing_with_cost_tracking(agent_context):
    router = AdaptiveModelRouter(context=agent_context)

    decision = router.route(
        task_description="Fix typo in README",
        task_type="documentation",
        agent_key="coder"
    )

    # P3 task should route to local model
    assert decision.complexity == TaskComplexity.P3_SIMPLE
    assert decision.selected_model == "ollama/qwen3-coder:30b"
    assert decision.estimated_cost_usd == 0.0

    # Verify telemetry logged
    events = telemetry.get_events(session_id=agent_context.session_id)
    assert any(e.event_type == EventType.LLM_CALL for e in events)

def test_routing_pattern_learning(agent_context):
    router = AdaptiveModelRouter(context=agent_context)

    # Route and complete task successfully
    decision = router.route(
        task_description="Implement user signup endpoint",
        task_type="feature_implementation",
        agent_key="coder"
    )

    # Simulate task completion
    router.record_completion(
        decision=decision,
        success=True,
        actual_tokens=500,
        duration_ms=2500.0
    )

    # Verify pattern stored in VectorStore (Article IV)
    memories = agent_context.search_memories(
        tags=["routing_pattern", "adaptive_router"]
    )
    assert len(memories) > 0
    assert memories[0]["content"]["classified_complexity"] == "P2_MODERATE"
```

### Performance Tests
```python
# tests/benchmarks/test_routing_performance.py
def test_routing_latency_p99():
    router = AdaptiveModelRouter()
    latencies = []

    for i in range(1000):
        start = time.perf_counter()
        router.route(
            task_description=f"Task {i}",
            task_type="general",
            agent_key="coder"
        )
        latencies.append((time.perf_counter() - start) * 1000)

    p99 = np.percentile(latencies, 99)
    assert p99 < 50.0  # <50ms p99 latency (NFR-1)
```

---

## 9. Constitutional Alignment

### Article I: Complete Context Before Action
**Compliance**:
- VectorStore query with retry on timeout (2x, 3x, up to 10x)
- AST analysis completes fully before routing decision
- Never proceed with partial classification data
- Classification confidence tracked and validated

**Implementation**:
```python
def vectorstore_match_with_retry(
    task_description: str,
    max_retries: int = 3
) -> list[dict]:
    """Article I: Retry VectorStore query on timeout."""
    timeout_ms = 100

    for attempt in range(max_retries):
        try:
            result = vector_store.search(
                query=task_description,
                namespace="task_classification",
                timeout_ms=timeout_ms
            )
            return result
        except TimeoutError:
            timeout_ms *= 2  # Double timeout
            logger.warning(
                f"VectorStore query timeout (attempt {attempt+1}), "
                f"retrying with {timeout_ms}ms timeout"
            )

    raise Exception("Unable to obtain complete VectorStore context")
```

### Article II: 100% Verification and Stability
**Compliance**:
- All routing decisions logged to telemetry (100% audit trail)
- Cost calculation verified against actual token usage
- Result pattern for all operations (no exceptions)
- Classification accuracy tracked and validated

**Implementation**:
```python
from shared.type_definitions.result import Result, Ok, Err

def classify_task_complexity(
    task_description: str,
    task_type: str
) -> Result[TaskComplexity, str]:
    """Article II: Result pattern for error handling."""
    try:
        # Method 1: Keyword detection
        keyword_result = keyword_detect(task_description)
        if keyword_result.is_ok():
            return keyword_result

        # Method 2: AST analysis
        if task_type == "code_modification":
            ast_result = ast_analyze(task_description)
            if ast_result.is_ok():
                return ast_result

        # Method 3: VectorStore
        vs_result = vectorstore_match(task_description)
        if vs_result.is_ok():
            return vs_result

        # Fallback: P2 moderate
        return Ok(TaskComplexity.P2_MODERATE)

    except Exception as e:
        return Err(f"Classification failed: {e}")
```

### Article III: Automated Merge Enforcement
**Compliance**:
- Routing logic automated (no manual model selection in production)
- Environment overrides permitted for testing/debugging only
- Pre-commit validation: linter, type checks, 100% test pass
- Git hooks enforce constitutional compliance

**Implementation**:
```python
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: constitutional-validation
      name: Constitutional Compliance Check
      entry: python scripts/validate_constitution.py
      language: system
      files: 'shared/adaptive_model_router.py'

# scripts/validate_constitution.py
def validate_adaptive_router():
    # Check VectorStore integration (Article IV)
    assert "vector_store.search" in router_code

    # Check Result pattern (Article II)
    assert "Result[" in router_code

    # Check retry logic (Article I)
    assert "max_retries" in router_code
```

### Article IV: Continuous Learning and Improvement
**Compliance** (CRITICAL - MANDATORY):
- **VectorStore integration is constitutionally required**
- All routing decisions stored for future pattern matching
- Min confidence: 0.6, min evidence: 3 occurrences before pattern trusted
- Routing accuracy tracked and improved automatically
- Cross-session learning from historical classifications

**Implementation**:
```python
class LearningStore:
    """Article IV: MANDATORY VectorStore integration."""

    def __init__(self, vector_store: VectorStore):
        assert vector_store is not None, "Article IV violation: VectorStore required"
        self.vector_store = vector_store

    def store_routing_pattern(
        self,
        decision: RoutingDecision,
        actual_complexity: TaskComplexity | None,
        success: bool
    ) -> None:
        """Store routing pattern for future learning."""

        # Calculate confidence based on success
        confidence = 0.9 if success else 0.5

        # Adjust if misclassification detected
        if actual_complexity and actual_complexity != decision.complexity:
            confidence = 0.3  # Low confidence for misclassification

        pattern = {
            "task_description": decision.task_description,
            "task_type": decision.task_type,
            "classified_complexity": decision.complexity.value,
            "actual_complexity": actual_complexity.value if actual_complexity else None,
            "success": success,
            "confidence": confidence,
            "evidence_count": 1,
            "timestamp": decision.timestamp.isoformat()
        }

        self.vector_store.add_memory(
            f"routing_{decision.task_id}",
            pattern
        )

    def query_similar_tasks(
        self,
        task_description: str,
        min_confidence: float = 0.6
    ) -> list[dict]:
        """Query VectorStore for similar task classifications."""

        # Article I: Retry on timeout
        return vectorstore_match_with_retry(task_description)
```

### Article V: Spec-Driven Development
**Compliance**:
- This spec document precedes all implementation
- Plan.md will be created from this spec
- TodoWrite tasks generated from plan
- Implementation follows spec → plan → code workflow

---

## 10. Metrics and Monitoring

### Cost Metrics Dashboard
```python
# Daily cost summary
{
    "period": "2025-10-10",
    "total_tasks": 327,
    "total_cost_usd": 14.23,
    "baseline_cost_usd": 65.40,  # All gpt-5
    "cost_savings_usd": 51.17,
    "cost_reduction_percent": 78.2,
    "breakdown": {
        "P1_tasks": 33,   "P1_cost_usd": 5.28,   # gpt-5
        "P2_tasks": 98,   "P2_cost_usd": 8.95,   # gpt-4o
        "P3_tasks": 196,  "P3_cost_usd": 0.00    # local
    }
}
```

### Accuracy Metrics
```python
# Weekly accuracy report
{
    "period": "2025-10-03 to 2025-10-10",
    "total_classifications": 2,156,
    "correct_classifications": 1,940,
    "misclassifications": 216,
    "accuracy_percent": 90.0,
    "breakdown": {
        "P1_accuracy": 95.2,  # High-stakes tasks have high accuracy
        "P2_accuracy": 88.7,  # Moderate tasks harder to classify
        "P3_accuracy": 91.3   # Simple tasks easy to classify
    },
    "top_misclassification_patterns": [
        "Feature impl classified as P3 (should be P2)",
        "Refactoring classified as P2 (should be P1)"
    ]
}
```

### Performance Metrics
```python
# Hourly performance summary
{
    "hour": "2025-10-10T14:00:00Z",
    "routing_decisions": 47,
    "latency_stats_ms": {
        "p50": 12.3,
        "p95": 31.2,
        "p99": 48.7,
        "max": 62.1
    },
    "vectorstore_query_stats_ms": {
        "p50": 23.4,
        "p95": 87.2,
        "p99": 95.1
    },
    "classification_method_distribution": {
        "keyword": 28,       # 59.6%
        "vectorstore": 15,   # 31.9%
        "ast": 4             # 8.5%
    }
}
```

---

## 11. Future Enhancements

### Phase 2: Sub-Classification
**Goal**: Further optimize P2 tier by splitting into P2A (upper) and P2B (lower)
- P2A → gpt-4o ($1.50/1M)
- P2B → gpt-4o-mini ($0.10/1M)
- **Estimated Additional Savings**: 15% (P2B is 50% of P2 tasks)

### Phase 3: Dynamic Pricing
**Goal**: Adjust routing based on real-time model pricing
- Monitor OpenAI/Anthropic pricing changes
- Automatically re-route if pricing shifts dramatically
- **Estimated Additional Savings**: 5-10% (opportunistic cost optimization)

### Phase 4: Quality Feedback Loop
**Goal**: Automatically detect misclassifications via quality metrics
- Track task retries (indication of incorrect model)
- Track user feedback on output quality
- Auto-adjust classification rules based on feedback
- **Estimated Accuracy Improvement**: 95% → 98%

---

## 12. References

### ADRs
- **ADR-001**: Complete Context Before Action (retry logic, VectorStore queries)
- **ADR-002**: 100% Verification and Stability (Result pattern, telemetry logging)
- **ADR-003**: Automated Merge Enforcement (no manual overrides in production)
- **ADR-004**: Continuous Learning and Improvement (VectorStore integration MANDATORY)
- **ADR-005**: Per-Agent Model Policy (existing baseline to enhance)

### Technical Dependencies
- **shared/model_policy.py**: Existing static model selection logic
- **shared/agent_context.py**: AgentContext for memory and VectorStore access
- **agency_memory/vector_store.py**: VectorStore for pattern storage/retrieval
- **shared/models/telemetry.py**: TelemetryEvent for cost/performance logging
- **constitution.md**: 5 Articles (all must be followed)

### External References
- **OpenAI Pricing**: https://openai.com/pricing (as of 2025-10)
- **Ollama Models**: https://ollama.com/library/qwen3-coder (local Q8_0 quantization)
- **AST Analysis**: Python `ast` module for code complexity estimation

---

## Appendix A: Classification Examples

### P3 (Simple) Examples
```python
EXAMPLES_P3 = [
    "Fix typo in README: 'recieve' → 'receive'",
    "Remove unused import statement from utils.py",
    "Add docstring to calculate_total function",
    "Rename variable 'x' to 'user_count' for clarity",
    "Format code with black formatter",
    "Update copyright year to 2025",
    "Clean up whitespace in config.yaml"
]
```

### P2 (Moderate) Examples
```python
EXAMPLES_P2 = [
    "Implement user authentication with JWT tokens",
    "Fix bug: division by zero in calculate_average",
    "Refactor UserService to use dependency injection",
    "Add unit tests for PaymentProcessor class",
    "Migrate database schema: add 'created_at' column",
    "Optimize SQL query with index on user_id",
    "Add error handling for network timeouts"
]
```

### P1 (Complex) Examples
```python
EXAMPLES_P1 = [
    "Design distributed consensus algorithm for multi-agent coordination",
    "Create ADR: Database selection (PostgreSQL vs MongoDB)",
    "Implement autonomous self-healing for NoneType errors",
    "Architect multi-tier model routing system (this spec!)",
    "Design constitutional compliance validation framework",
    "Implement critical security: SQL injection prevention",
    "Design agent orchestration framework with DAG execution"
]
```

---

## Appendix B: Cost Calculation Examples

### Scenario 1: All P3 (Best Case)
```
100 tasks/day × 30 days = 3,000 tasks/month
100% P3 (local model) = $0/month
Baseline (all gpt-5) = 3,000 × 500 tokens × $4/1M = $6,000/month
Savings: $6,000 (100% reduction)
```

### Scenario 2: Realistic Distribution
```
60% P3, 30% P2, 10% P1 (3,000 tasks/month)
- P3: 1,800 tasks × $0 = $0
- P2: 900 tasks × 500 tokens × $1.50/1M = $675
- P1: 300 tasks × 500 tokens × $4.00/1M = $600
Total: $1,275/month
Baseline: $6,000/month
Savings: $4,725 (78.75% reduction)
```

### Scenario 3: Target (90% Reduction)
```
65% P3, 25% P2, 10% P1 (3,000 tasks/month)
+ P2 sub-classification (50% to gpt-4o-mini)
- P3: 1,950 tasks × $0 = $0
- P2A (upper): 375 tasks × 500 tokens × $1.50/1M = $281.25
- P2B (lower): 375 tasks × 500 tokens × $0.10/1M = $18.75
- P1: 300 tasks × 500 tokens × $4.00/1M = $600
Total: $900/month
Baseline: $6,000/month (all gpt-5)
Savings: $5,100 (85% reduction, approaching 90% target)
```

---

**End of Specification**

**Next Steps**:
1. Create `plan_adaptive_model_router.md` from this spec
2. Generate TodoWrite tasks from plan
3. Implement Phase 1-5 per plan
4. Validate against acceptance criteria
5. Deploy to production with A/B testing

**Constitutional Validation**: ✅ PASS
- Article I: Complete context (VectorStore retry logic) ✅
- Article II: Result pattern, 100% telemetry logging ✅
- Article III: Automated routing, no manual overrides ✅
- Article IV: VectorStore integration MANDATORY ✅
- Article V: Spec-driven (this document precedes code) ✅
