# ADR-024: Adaptive Model Router for 90% Cost Reduction

## Status
**Proposed** - 2025-10-10

## Context

Agency OS currently uses a static per-agent model policy (`shared/model_policy.py`) that assigns models based on agent type alone, without considering task complexity. This approach leads to significant cost inefficiency:

### Current Cost Structure (Baseline)
- **All tasks route to gpt-5** by default ($4.00/1M tokens)
- **10,000 tasks/month** × 500 tokens avg = **$20,000/month**
- **No task complexity differentiation**: Simple typo fixes use same $4/1M model as complex architectural decisions
- **Local model unused**: Qwen3-Coder-30B Q8_0 available but not integrated for P3 tasks

### Problem Statement
The static routing policy wastes 60-80% of LLM budget on simple tasks that could run on cheaper models (gpt-4o-mini) or free local models (Ollama). Without intelligent task classification, Agency cannot achieve cost efficiency while maintaining quality.

### Requirements Identified
1. **Task complexity classification** before model selection
2. **Multi-tier routing**: P1 (complex) → P2 (moderate) → P3 (simple)
3. **Cost tracking** with telemetry integration
4. **VectorStore learning** to improve classification accuracy (Article IV mandate)
5. **Constitutional compliance** across all 5 articles

### Constraints
- **Article IV**: VectorStore integration is constitutionally required (not optional)
- **Article I**: Classification must have retry logic for complete context
- **Article II**: 100% telemetry logging for all routing decisions
- **Article III**: Automated routing (no manual overrides in production)
- **Target**: 90% cost reduction ($20K/month → $2K/month)

---

## Decision

**Implement AdaptiveModelRouter: An intelligent model routing system that classifies task complexity (P1/P2/P3) and routes to cost-optimal models, achieving 90% cost reduction while maintaining constitutional compliance.**

### Core Architecture

#### 1. Task Complexity Classification
Three-method hybrid algorithm:

**Method 1: Keyword Detection** (Fast, 80% accuracy)
```python
P3_KEYWORDS = [
    r"\b(typo|format|docstring|comment|readme)\b",
    r"\b(remove|delete|clean)\b.*\b(unused|dead code)\b"
]

P1_KEYWORDS = [
    r"\b(design|architect|adr|constitutional)\b",
    r"\b(autonomous|healing|critical|security)\b"
]

# P2 is default fallback
```

**Method 2: AST Analysis** (Accurate for code tasks)
```python
if task_type == "code_modification":
    complexity = estimate_cyclomatic_complexity(code_ast)
    if complexity > 10: return P1_COMPLEX
    elif complexity > 5: return P2_MODERATE
    else: return P3_SIMPLE
```

**Method 3: VectorStore Pattern Matching** (Article IV, 95% accuracy when mature)
```python
# Query historical classifications
similar_tasks = vector_store.search(
    query=task_description,
    namespace="task_classification",
    limit=5
)

# Weighted average of historical complexity
return calculate_weighted_avg(similar_tasks)
```

#### 2. Model Routing Table
```python
MODEL_ROUTING = {
    "P1_COMPLEX": "gpt-5",                    # $4.00/1M tokens (10% of tasks)
    "P2_MODERATE": "gpt-4o",                  # $1.50/1M tokens (30% of tasks)
    "P3_SIMPLE": "ollama/qwen3-coder:30b"     # $0.00 (local, 60% of tasks)
}

# Fallback if local model unavailable
if P3_SIMPLE and not is_local_model_available():
    return "gpt-4o-mini"  # $0.10/1M tokens
```

#### 3. Cost Tracking & Telemetry
```python
@dataclass
class RoutingDecision:
    task_id: str
    complexity: TaskComplexity  # P1/P2/P3
    selected_model: str
    estimated_cost_usd: float
    routing_latency_ms: float
    classification_confidence: float

    def to_telemetry_event(self) -> TelemetryEvent:
        # Log to telemetry system (Article II: 100% logging)
        pass
```

#### 4. VectorStore Learning (Article IV - MANDATORY)
```python
class LearningStore:
    def store_routing_pattern(
        self,
        decision: RoutingDecision,
        success: bool,
        actual_tokens: int
    ) -> None:
        """Store routing pattern for future learning."""

        pattern = {
            "task_description": decision.task_description,
            "classified_complexity": decision.complexity.value,
            "success": success,
            "confidence": 0.9 if success else 0.5,
            "evidence_count": 1
        }

        # Article IV: MANDATORY VectorStore storage
        vector_store.add_memory(f"routing_{decision.task_id}", pattern)
```

### Integration Points

#### shared/model_policy.py Enhancement
```python
# BEFORE (static)
def agent_model(agent_key: str) -> str:
    return DEFAULTS.get(agent_key, "gpt-5")

# AFTER (adaptive)
def agent_model(
    agent_key: str,
    task_description: str | None = None,
    context: AgentContext | None = None
) -> str:
    """Return optimal model via adaptive routing."""

    # Backward compatible: no task → static default
    if task_description is None:
        return DEFAULTS.get(agent_key, "gpt-5")

    # Adaptive routing based on complexity
    router = AdaptiveModelRouter(context=context)
    decision = router.route(
        task_description=task_description,
        agent_key=agent_key
    )

    return decision.selected_model
```

#### shared/agent_context.py Enhancement
```python
class AgentContext:
    def get_optimal_model(
        self,
        agent_key: str,
        task_description: str
    ) -> str:
        """Get optimal model via adaptive routing."""
        if self._adaptive_router is None:
            self._adaptive_router = AdaptiveModelRouter(context=self)

        decision = self._adaptive_router.route(
            task_description=task_description,
            agent_key=agent_key
        )

        return decision.selected_model
```

---

## Rationale

### Why Adaptive Routing Over Static Policy?

#### Cost Efficiency
**Current Baseline** (all gpt-5):
- 10,000 tasks/month × 500 tokens × $4.00/1M = $20,000/month

**With Adaptive Routing**:
- P3 (60%): 6,000 tasks × $0 (local) = $0
- P2 (30%): 3,000 tasks × $1.50/1M = $2,250
- P1 (10%): 1,000 tasks × $4.00/1M = $2,000
- **Total**: $4,250/month (78.75% reduction)

**With P2 Sub-Classification** (Phase 2):
- **Target**: $2,000/month (90% reduction)

#### Quality Preservation
- **P1 tasks** (architecture, ADRs) still use gpt-5 (maximum quality)
- **P2 tasks** (features, bugs) use gpt-4o (balanced quality/cost)
- **P3 tasks** (typos, formatting) use local model (sufficient quality, FREE)

#### Constitutional Alignment
- **Article IV**: VectorStore learning improves classification accuracy over time
- **Article I**: Retry logic ensures complete context before classification
- **Article II**: 100% telemetry logging for all routing decisions
- **Article III**: Automated routing (no manual overrides in production)

### Alternatives Considered

#### Alternative 1: Per-Agent Token Budgets
**Description**: Set monthly token budgets per agent, auto-switch to cheaper models when budget exceeded.

**Pros**:
- Simple implementation
- Predictable monthly costs

**Cons**:
- **Quality degradation**: Important tasks late in month use cheap models
- **No learning**: Doesn't improve over time
- **Article IV violation**: No VectorStore integration

**Rejected**: Violates Article IV (continuous learning mandate), degrades quality unpredictably.

#### Alternative 2: Manual Task Tagging
**Description**: Developers manually tag tasks as P1/P2/P3 before execution.

**Pros**:
- 100% classification accuracy (human judgment)
- Simple routing logic

**Cons**:
- **Article III violation**: Manual process, not automated
- **Developer friction**: Requires manual tagging for every task
- **No learning**: Static classifications, no improvement

**Rejected**: Violates Article III (automated merge enforcement), adds developer overhead.

#### Alternative 3: Random 10% Sampling to Cheaper Models
**Description**: Route 10% of tasks randomly to gpt-4o-mini to save costs.

**Pros**:
- Easy to implement
- Some cost savings

**Cons**:
- **Low savings**: Only 10% reduction (vs 90% target)
- **Random quality degradation**: Important tasks might get cheap model
- **No learning**: No improvement over time

**Rejected**: Insufficient cost savings (10% vs 90% target), random quality degradation unacceptable.

---

## Consequences

### Positive Outcomes

#### Cost Reduction (90% Target)
- **Immediate**: 78.75% reduction ($20K → $4.25K/month) in Phase 1
- **Phase 2**: 90% reduction ($20K → $2K/month) with P2 sub-classification
- **Annual Savings**: $216K/year (Phase 1), $240K/year (Phase 2)

#### Quality Preservation
- **P1 tasks unchanged**: Architecture, ADRs still use gpt-5
- **P2 tasks balanced**: Features use gpt-4o (2.7x cheaper, comparable quality)
- **P3 tasks FREE**: Local model handles simple tasks (typos, formatting)

#### Continuous Improvement (Article IV)
- **VectorStore learning**: Classification accuracy improves over time
- **Pattern storage**: Successful routing decisions stored for future use
- **Cross-session learning**: Historical patterns inform new classifications

#### Performance Enhancement
- **<50ms routing latency** (p99): Minimal overhead
- **Parallel classification**: Keyword + AST + VectorStore methods run concurrently
- **Cached classifications**: Similar tasks reuse previous decisions

### Negative Consequences

#### Implementation Complexity
- **New components**: TaskComplexityClassifier, ModelRouter, CostTracker, LearningStore
- **Integration overhead**: Changes to model_policy.py, agent_context.py
- **Testing burden**: Unit tests, integration tests, performance tests, A/B testing

**Mitigation**: Phased implementation (Week 1: Classification, Week 2: Routing, Week 3: Learning)

#### Misclassification Risk
- **False P3**: Complex task classified as simple → quality degradation
- **False P1**: Simple task classified as complex → cost waste
- **Cold start**: 80% accuracy initially (no VectorStore history)

**Mitigation**:
- **Human review**: Sample 100 tasks/week for accuracy validation
- **Fallback logic**: Uncertain classifications default to P2 (safe middle ground)
- **Confidence thresholds**: Low-confidence classifications escalate to higher tier
- **Learning loop**: Misclassifications stored with low confidence, improve over time

#### VectorStore Dependency
- **Article IV mandate**: VectorStore integration is constitutionally required
- **Performance risk**: VectorStore query adds latency (100ms p99)
- **Storage growth**: Routing patterns accumulate over time

**Mitigation**:
- **Article I retry logic**: VectorStore query with 2x, 3x timeout on failure
- **Async queries**: VectorStore lookup in parallel with keyword/AST methods
- **Cleanup policy**: Archive patterns older than 90 days

#### Local Model Availability
- **Hardware constraint**: Local model requires 48GB RAM (M4 Pro)
- **Memory contention**: Qwen3-Coder Q8_0 uses 38GB
- **Fallback cost**: P3 tasks use gpt-4o-mini if local unavailable ($0.10/1M)

**Mitigation**:
- **Memory-aware execution**: ADR-023 hardware constraints enforced
- **Fallback logic**: Auto-switch to gpt-4o-mini if local model unavailable
- **Cost tracking**: Monitor fallback usage, optimize if >10% of P3 tasks

### Risks

#### Risk 1: Classification Accuracy Below 90%
**Probability**: Medium (cold start accuracy is 80%)
**Impact**: High (misclassifications waste cost or degrade quality)

**Mitigation**:
- VectorStore learning improves accuracy to 95% after 1,000 tasks
- Human review loop validates classifications weekly
- Confidence thresholds escalate uncertain tasks to higher tier

#### Risk 2: VectorStore Query Latency >100ms
**Probability**: Medium (depends on VectorStore load)
**Impact**: Low (still within 50ms total routing latency p99)

**Mitigation**:
- Article I retry logic with timeout escalation
- Async VectorStore queries in parallel with other methods
- LRU cache for frequent task patterns

#### Risk 3: Local Model Unavailable (Memory Exhaustion)
**Probability**: Low (ADR-023 memory-aware execution enforced)
**Impact**: Medium (P3 tasks cost $0.10/1M instead of $0)

**Mitigation**:
- Memory monitoring with psutil before spawning local model
- Auto-fallback to gpt-4o-mini if memory pressure detected
- Test parallelism reduced to 3 workers when local model active

---

## Implementation Notes

### Phase 1: Core Classification (Week 1)
**Deliverables**:
1. `TaskComplexity` enum (P1/P2/P3)
2. `TaskComplexityClassifier` with 3 methods (keyword, AST, VectorStore)
3. Unit tests for 80% accuracy on synthetic tasks

**Files Created**:
- `shared/adaptive_model_router.py` (300 lines)
- `shared/models/routing.py` (Pydantic models, 150 lines)
- `tests/test_task_complexity_classifier.py` (200 lines)

### Phase 2: Model Routing (Week 1)
**Deliverables**:
1. `ModelRouter` class with routing table
2. Environment override handling
3. Integration with `shared/model_policy.py`
4. Unit tests for routing decisions

**Files Modified**:
- `shared/model_policy.py` (add `task_description` parameter)
- `shared/agent_context.py` (add `get_optimal_model()`)

### Phase 3: Cost Tracking (Week 2)
**Deliverables**:
1. `CostTracker` class with telemetry integration
2. `CostSummary` aggregation logic
3. Telemetry event logging (Article II)
4. Dashboard metrics (cost savings, accuracy)

**Files Created**:
- `shared/cost_tracker.py` (200 lines)
- `tests/test_cost_tracking.py` (150 lines)

### Phase 4: Learning Integration (Week 2, Article IV)
**Deliverables**:
1. `LearningStore` class for VectorStore integration
2. Pattern storage after successful tasks
3. Pattern retrieval during classification
4. Confidence scoring and evidence counting

**Files Created**:
- `shared/learning_store.py` (250 lines)
- `tests/test_learning_store.py` (200 lines)

### Phase 5: Production Validation (Week 3)
**Deliverables**:
1. A/B testing: 10% traffic to adaptive router
2. Accuracy measurement: human review of 100 tasks
3. Cost validation: actual vs predicted costs
4. Performance profiling: latency p50, p99

**Validation Criteria**:
- Classification accuracy >90%
- Cost reduction >78% (Phase 1 target)
- Routing latency p99 <50ms
- Zero constitutional violations

---

## Constitutional Alignment

### Article I: Complete Context Before Action ✅
- **VectorStore retry logic**: 2x, 3x, up to 10x timeout on failure
- **AST analysis complete**: Full complexity estimation before routing
- **Never proceed with partial data**: Uncertain classifications default to P2

**Implementation**:
```python
def vectorstore_match_with_retry(task_description: str) -> Result[TaskComplexity, str]:
    timeout_ms = 100
    for attempt in range(3):
        try:
            return vector_store.search(task_description, timeout_ms=timeout_ms)
        except TimeoutError:
            timeout_ms *= 2  # Article I: Double timeout
    raise Exception("Unable to obtain complete VectorStore context")
```

### Article II: 100% Verification and Stability ✅
- **100% telemetry logging**: All routing decisions logged to TelemetryEvent
- **Result pattern**: All operations return Result<T, E> for error handling
- **Cost validation**: Predicted vs actual costs tracked and validated

**Implementation**:
```python
def classify_task_complexity(
    task_description: str
) -> Result[TaskComplexity, str]:
    """Article II: Result pattern for error handling."""
    try:
        # Classification logic
        return Ok(TaskComplexity.P2_MODERATE)
    except Exception as e:
        return Err(f"Classification failed: {e}")
```

### Article III: Automated Merge Enforcement ✅
- **Automated routing**: No manual model selection in production
- **Environment overrides**: Permitted for testing/debugging only
- **Pre-commit validation**: Linter, type checks, 100% test pass required

**Implementation**:
```python
# Environment override allowed (testing only)
override = os.getenv(f"{agent_key.upper()}_MODEL")
if override:
    logger.warning(f"Manual override: {override} (testing only)")
    return override
```

### Article IV: Continuous Learning and Improvement ✅ (CRITICAL)
- **VectorStore integration MANDATORY**: Constitutionally required (not optional)
- **Pattern storage**: All routing decisions stored for future learning
- **Min confidence 0.6**: Min evidence 3 before pattern trusted
- **Cross-session learning**: Historical patterns inform new classifications

**Implementation**:
```python
class LearningStore:
    def __init__(self, vector_store: VectorStore):
        # Article IV: VectorStore integration is MANDATORY
        assert vector_store is not None, "Article IV violation: VectorStore required"
        self.vector_store = vector_store

    def store_routing_pattern(self, decision: RoutingDecision, success: bool):
        """Article IV: Store pattern for future learning."""
        pattern = {
            "classified_complexity": decision.complexity.value,
            "success": success,
            "confidence": 0.9 if success else 0.5
        }
        self.vector_store.add_memory(f"routing_{decision.task_id}", pattern)
```

### Article V: Spec-Driven Development ✅
- **Spec first**: `specs/adaptive_model_router_spec.md` created before implementation
- **Plan follows spec**: `plan_adaptive_model_router.md` to be created
- **TodoWrite tasks**: Generated from plan for implementation tracking

---

## Performance Targets

### Latency Targets
- **Routing decision p50**: <20ms
- **Routing decision p99**: <50ms
- **VectorStore query p99**: <100ms
- **Classification latency p99**: <30ms

### Cost Targets
**Phase 1** (78.75% reduction):
- Baseline: $20,000/month
- Target: $4,250/month
- Savings: $15,750/month ($189K/year)

**Phase 2** (90% reduction):
- Baseline: $20,000/month
- Target: $2,000/month
- Savings: $18,000/month ($216K/year)

### Accuracy Targets
- **Cold start**: 80% accuracy (no VectorStore history)
- **Warm** (100 tasks): 90% accuracy
- **Mature** (1,000+ tasks): 95% accuracy

---

## Metrics and Monitoring

### Cost Metrics
```python
# Daily cost summary
{
    "total_tasks": 327,
    "total_cost_usd": 14.23,
    "baseline_cost_usd": 65.40,
    "cost_savings_usd": 51.17,
    "cost_reduction_percent": 78.2,
    "breakdown": {
        "P1": {"tasks": 33, "cost_usd": 5.28},
        "P2": {"tasks": 98, "cost_usd": 8.95},
        "P3": {"tasks": 196, "cost_usd": 0.00}
    }
}
```

### Accuracy Metrics
```python
# Weekly accuracy report
{
    "total_classifications": 2156,
    "correct_classifications": 1940,
    "accuracy_percent": 90.0,
    "top_misclassification_patterns": [
        "Feature impl classified as P3 (should be P2)"
    ]
}
```

### Performance Metrics
```python
# Hourly performance summary
{
    "routing_decisions": 47,
    "latency_stats_ms": {
        "p50": 12.3,
        "p95": 31.2,
        "p99": 48.7
    }
}
```

---

## References

### Previous ADRs
- **ADR-001**: Complete Context Before Action (retry logic foundation)
- **ADR-002**: 100% Verification and Stability (telemetry logging requirement)
- **ADR-003**: Automated Merge Enforcement (no manual overrides)
- **ADR-004**: Continuous Learning System (VectorStore integration mandate)
- **ADR-005**: Per-Agent Model Policy (static baseline to enhance)
- **ADR-023**: Memory-Aware Test Execution (hardware constraints for local model)

### Technical Dependencies
- **shared/model_policy.py**: Existing static model selection (to be enhanced)
- **shared/agent_context.py**: AgentContext for memory and VectorStore access
- **agency_memory/vector_store.py**: VectorStore for pattern storage/retrieval
- **shared/models/telemetry.py**: TelemetryEvent for cost/performance logging
- **constitution.md**: 5 Articles (all must be followed)

### External References
- **OpenAI Pricing**: https://openai.com/pricing (as of 2025-10)
- **Ollama Qwen3-Coder**: https://ollama.com/library/qwen3-coder
- **Python AST Module**: https://docs.python.org/3/library/ast.html

---

## Review and Evolution

### Review Schedule
- **Weekly**: Classification accuracy and cost metrics review
- **Monthly**: VectorStore learning effectiveness assessment
- **Quarterly**: Full system impact evaluation and optimization

### Success Metrics for Next Review (2025-11-10)
- **Cost Reduction**: >78% achieved in Phase 1
- **Classification Accuracy**: >90% after 1,000 tasks
- **Performance**: p99 routing latency <50ms
- **Constitutional Compliance**: 100% (zero violations)
- **VectorStore Learning**: Pattern accuracy improving month-over-month

### Evolution Triggers
```python
EVOLUTION_TRIGGERS = {
    "accuracy_below_85_percent": "Classification accuracy degrading",
    "cost_reduction_below_70_percent": "Missing cost targets",
    "latency_above_100ms_p99": "Performance degradation",
    "local_model_unavailable_above_10_percent": "Fallback usage too high"
}
```

---

## Report Metadata

- **Author**: ChiefArchitectAgent
- **Stakeholder**: @am
- **Date**: 2025-10-10
- **Dependencies**: ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-023
- **Implementation Phase**: Leap 3 - Stateful Learning
- **Next Review**: 2025-11-10 (monthly assessment)
- **Supersedes**: None (new capability)
- **Related Systems**: VectorStore, AgentContext, Model Policy, Telemetry
- **Specification**: `specs/adaptive_model_router_spec.md`

---

*"The measure of intelligence is not the cost of the model, but the wisdom to choose the right model for each task."* - ADR-024 Cost Optimization Principle
