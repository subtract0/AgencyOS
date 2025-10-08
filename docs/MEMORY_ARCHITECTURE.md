# Agency Memory Architecture: State-of-the-Art Design

**Created:** 2025-10-08
**Status:** Production-Ready + Continuous Evolution
**Constitutional Basis:** Article IV (Continuous Learning)

## Executive Summary

Agency employs a **three-tier memory architecture** combining:
1. **Anthropic Memory Tool** - Cross-conversation persistence (file-based)
2. **VectorStore** - Institutional learning (semantic search)
3. **Session Memory** - Working context (in-memory)

This design enables **exponential growth** through:
- Cross-conversation continuity (Memory Tool)
- Automatic pattern extraction (VectorStore)
- Real-time context management (Session Memory)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT CONTEXT                            │
│                  (Unified Interface)                        │
└───────────────┬─────────────┬─────────────────┬─────────────┘
                │             │                 │
       ┌────────▼────┐  ┌─────▼──────┐  ┌──────▼───────┐
       │   Memory    │  │  Vector    │  │   Session    │
       │    Tool     │  │   Store    │  │   Memory     │
       │  (Tier 1)   │  │  (Tier 2)  │  │   (Tier 3)   │
       └─────────────┘  └────────────┘  └──────────────┘
              │                │               │
       ┌──────▼───────┐ ┌─────▼───────┐  ┌───▼────────┐
       │ ~/.agency/   │ │ ChromaDB/   │  │ In-Memory  │
       │  memories/   │ │ Firestore   │  │   Dict     │
       └──────────────┘ └─────────────┘  └────────────┘
```

---

## Tier 1: Cross-Conversation Memory (Anthropic Memory Tool)

### Purpose
**Persistent knowledge that survives context window resets and sessions.**

### Implementation
- **Backend:** File-based storage in `~/.agency/memories/`
- **Tool:** `AgencyMemoryTool(BetaAbstractMemoryTool)`
- **Access:** `context.enable_anthropic_memory()`

### Use Cases

| Category | Example | Persistence |
|----------|---------|-------------|
| **Technical Debt** | Test suite gaps, known issues | Indefinite |
| **Architectural Decisions** | ADRs, design patterns | Indefinite |
| **Coding Standards** | Result pattern, TDD workflow | Indefinite |
| **Feature Backlogs** | Unimplemented features, TODOs | Until resolved |
| **Session Progress** | Multi-day task checkpoints | Until completion |

### Directory Structure

```
~/.agency/memories/
├── agency_backlog/              # Technical debt tracking
│   ├── test_suite_gaps.md      # 191 skipped tests analysis
│   ├── architecture_todo.md     # Planned improvements
│   └── feature_requests.md      # User requests
│
├── patterns/                    # Reusable code patterns
│   ├── result_pattern.md        # Error handling standard
│   ├── pydantic_usage.md        # Model design guide
│   ├── tdd_workflow.md          # Test-first development
│   └── constitutional_checks.md # Compliance patterns
│
├── institutional/               # Cross-session knowledge
│   ├── coding_standards.md      # Agency code style
│   ├── git_workflow.md          # Branch/commit strategy
│   ├── testing_guidelines.md    # Test writing rules
│   └── model_routing_policy.md  # Cost optimization
│
└── sessions/                    # Session-specific context
    ├── session_20251008_auth/   # Feature development
    └── session_20251007_tests/  # Test fixing session
```

### Operations

```python
# Enable for session
context.enable_anthropic_memory()
tool = context.get_anthropic_memory_tool()

# Store backlog item
tool.create(
    "/memories/agency_backlog/test_suite_gaps.md",
    "# Test Suite Gaps\n\n## Ollama Tests (140 skipped)..."
)

# Update progress
tool.str_replace(
    "/memories/agency_backlog/test_suite_gaps.md",
    "Status: Ready to fix",
    "Status: FIXED ✅"
)

# Retrieve institutional knowledge
patterns = tool.view("/memories/patterns/result_pattern.md")
```

### Performance
- **Latency:** ~5ms per file operation (local filesystem)
- **Capacity:** Limited by disk space (typically 100MB quota)
- **Search:** File path-based (O(1) lookup)

---

## Tier 2: Institutional Learning (VectorStore)

### Purpose
**Automatic pattern extraction and semantic search across all sessions.**

### Implementation
- **Backend:** ChromaDB (local) / Firestore (production)
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dims)
- **Access:** `context.store_memory()`, `context.search_memories()`

### Use Cases

| Pattern Type | Auto-Extracted | Example |
|-------------|----------------|---------|
| **Code Patterns** | ✅ | Result<T,E> usage, Pydantic models |
| **Error Solutions** | ✅ | TypeError fixes, API migrations |
| **Test Patterns** | ✅ | AAA pattern, fixture usage |
| **Architectural Decisions** | ✅ | ADR-style decisions |
| **Agent Interactions** | ✅ | Successful workflows |

### Constitutional Mandate (Article IV)

```python
# MANDATORY - No disable flags permitted
USE_ENHANCED_MEMORY=true

# VectorStore integration is constitutional law
# Agents MUST query learnings before decisions
# Agents MUST store successful patterns after operations
```

### Operations

```python
# Store pattern (automatic tagging)
context.store_memory(
    key="result_pattern_success_2025_10_08",
    content={
        "pattern": "Result<T,E>",
        "context": "Fixed CostTracker.track() API",
        "outcome": "100% test pass",
        "confidence": 0.95
    },
    tags=["pattern", "error_handling", "success"]
)

# Search patterns (semantic)
results = context.search_memories(
    tags=["error_handling"],
    include_session=False  # Cross-session search
)

# Query learnings before action (constitutional requirement)
learnings = context.search_memories(
    tags=["cost_tracker", "api_migration"],
    include_session=True
)
```

### Performance
- **Latency:** ~50ms per semantic search (with embeddings)
- **Fallback:** ~5ms keyword search (no embeddings)
- **Capacity:** ~10K memories per agent (current), 1M+ (target with vector DB)
- **Cache:** LRU cache (5x speedup, 128 entries)

### Learning Triggers

```python
# Auto-trigger conditions
if test_suite_passed:
    learning_agent.extract_patterns(session_transcript)

if error_fixed:
    learning_agent.store_solution(error, fix, confidence=0.8)

if adr_created:
    learning_agent.index_decision(adr_content)
```

---

## Tier 3: Session Memory (Working Context)

### Purpose
**Temporary context for current session, cleared on restart.**

### Implementation
- **Backend:** In-memory dictionary
- **Scoping:** Session ID-tagged
- **Access:** `context.set_metadata()`, `context.get_metadata()`

### Use Cases

| Data Type | Example | Lifetime |
|-----------|---------|----------|
| **Current Task** | "Fixing skipped tests" | Session |
| **Progress State** | "3/7 todos complete" | Session |
| **Temporary Flags** | "local_model_enabled" | Session |
| **Agent State** | "coder_active=True" | Session |

### Operations

```python
# Store session metadata
context.set_metadata("current_task", "test_fixing")
context.set_metadata("tests_fixed", 47)

# Retrieve metadata
task = context.get_metadata("current_task", default="unknown")
```

### Performance
- **Latency:** <1μs (in-memory dictionary)
- **Capacity:** Limited by RAM (typically <1MB per session)

---

## Unified Memory Interface (AgentContext)

### Design Philosophy

**Single entry point for all memory operations:**
```python
from shared.agent_context import create_agent_context

context = create_agent_context(session_id="feature_dev")

# Tier 1: Cross-conversation (explicit)
context.enable_anthropic_memory()
tool = context.get_anthropic_memory_tool()
tool.create("/memories/backlog/item.md", "...")

# Tier 2: Institutional learning (automatic)
context.store_memory("key", {"pattern": "..."}, tags=["learning"])
results = context.search_memories(["pattern"])

# Tier 3: Session context (temporary)
context.set_metadata("progress", 75)
```

### Memory Selection Strategy

| Question | Use This Tier | Reason |
|----------|--------------|--------|
| Should survive restarts? | Tier 1 (Memory Tool) | Cross-conversation persistence |
| Should be searchable semantically? | Tier 2 (VectorStore) | Pattern discovery |
| Is it temporary state? | Tier 3 (Session) | No persistence needed |
| Is it curated knowledge? | Tier 1 (Memory Tool) | Manual organization |
| Is it auto-extracted pattern? | Tier 2 (VectorStore) | Continuous learning |

---

## State-of-the-Art Features

### 1. Hybrid Search (Tier 2)

```python
# Semantic search with keyword fallback
results = vector_store.hybrid_search(
    query="Result pattern for error handling",
    tags=["pattern", "error"],
    top_k=5,
    alpha=0.7  # 70% semantic, 30% keyword
)
```

### 2. Priority-Based Retention

```python
class MemoryPriority(Enum):
    CRITICAL = 4  # Never delete (constitutional, ADRs)
    HIGH = 3      # Keep indefinitely (patterns, learnings)
    NORMAL = 2    # Keep until pruning threshold
    LOW = 1       # First to be pruned
```

### 3. Automatic Memory Consolidation

```python
# Triggered at 80% capacity
def consolidate_memories(self):
    # Group related memories by semantic similarity
    clusters = self.cluster_by_similarity(threshold=0.85)

    # Summarize each cluster
    for cluster in clusters:
        summary = self.llm_summarize(cluster)
        self.store(summary, priority=HIGH)
        self.archive(cluster)  # Move to cold storage
```

### 4. Session-Scoped Caching

```python
# 5x performance improvement
@lru_cache(maxsize=128)
def _search_memories_impl(tags_tuple, include_session):
    # Cached search results
    ...

# Cache invalidation on writes
def store_memory(self, key, content, tags):
    self.memory.store(key, content, tags)
    self._search_cache.cache_clear()
```

### 5. Cross-Agent Memory Sharing

```python
# Agent-specific namespace
agent1.store_memory("pattern:result", {...}, tags=["agent1"])

# Shared knowledge store
shared_store.store("pattern:result", {...}, tags=["shared"])

# Query across agents
all_patterns = query_all_agents(tags=["pattern"])
```

---

## Constitutional Compliance

### Article IV: Continuous Learning

```python
# MANDATORY VectorStore integration
assert os.getenv("USE_ENHANCED_MEMORY") == "true", \
    "Article IV violation: VectorStore is constitutionally required"

# Query before action
@require_learning_check
def implement_feature(context, spec):
    learnings = context.search_memories(["similar_feature"])
    if learnings:
        apply_learned_patterns(learnings)
    ...

# Store after success
@auto_store_pattern
def complete_task(context, result):
    if result.is_ok():
        context.store_memory(
            key=f"success_{task_id}",
            content=result.value,
            tags=["success", "pattern"]
        )
```

---

## Memory Lifecycle

```
┌─────────────────┐
│  Agent Action   │
└────────┬────────┘
         │
    ┌────▼─────────────────────────┐
    │ Should persist?              │
    │ - Cross-session? → Tier 1    │
    │ - Pattern? → Tier 2          │
    │ - Temp state? → Tier 3       │
    └────┬─────────────────────────┘
         │
    ┌────▼────────┐
    │   Store     │
    └────┬────────┘
         │
    ┌────▼────────────────────┐
    │  Learning Extraction    │
    │  (if Tier 2)            │
    └────┬────────────────────┘
         │
    ┌────▼────────────────────┐
    │  Consolidation Check    │
    │  (if >80% capacity)     │
    └────┬────────────────────┘
         │
    ┌────▼────────────────────┐
    │  Indexed for Search     │
    └─────────────────────────┘
```

---

## Scalability

### Current Performance

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| **Memories per agent** | ~10K | 1M+ | Vector DB needed |
| **Search complexity** | O(n) | O(√t log t) | Vector indices |
| **Storage per memory** | ~200 bytes | ~100 bytes | Compression |
| **Cross-agent queries** | O(n*agents) | O(log(n*agents)) | Distributed index |

### Optimization Roadmap

**Phase 1: Vector Database Integration** (Medium effort, high value)
- Replace in-memory ChromaDB with Weaviate/Pinecone
- Add vector indices for O(√t log t) search
- Enable distributed queries

**Phase 2: Memory Consolidation** (Low effort, high impact)
- Semantic clustering of related memories
- Hierarchical summarization (daily → weekly → monthly)
- Automatic archive to cold storage

**Phase 3: Distributed Architecture** (High effort, transformative)
- Memory-compute disaggregation
- Specialized memory agents
- Real-time memory streaming

---

## Integration Points

### 1. LearningAgent

```python
from learning_agent import LearningAgent

# Extract patterns from session
learning_agent = LearningAgent(context)
patterns = learning_agent.analyze_session(session_transcript)

# Store in VectorStore
for pattern in patterns:
    context.store_memory(
        key=f"pattern_{pattern.id}",
        content=pattern.dict(),
        tags=["pattern", "auto_extracted"]
    )
```

### 2. QualityEnforcer

```python
# Check against institutional knowledge
def enforce_constitutional_compliance(code):
    # Query memory for similar violations
    past_violations = context.search_memories(
        tags=["constitutional_violation", code.file_path]
    )

    if past_violations:
        # Apply learned fixes
        return apply_past_solutions(code, past_violations)
```

### 3. ChiefArchitect

```python
# Store ADRs in both systems
def create_adr(adr_content):
    # Tier 1: File-based persistence
    tool.create(f"/memories/adrs/ADR-{id}.md", adr_content)

    # Tier 2: Semantic indexing
    context.store_memory(
        key=f"adr_{id}",
        content=adr_content,
        tags=["adr", "architecture"]
    )
```

---

## Best Practices

### 1. Tier Selection

```python
# ✅ GOOD: Cross-conversation knowledge
tool.create("/memories/patterns/result.md", "...")

# ❌ BAD: Session-specific temp state
tool.create("/memories/temp_counter.md", "42")
# → Use: context.set_metadata("counter", 42)

# ✅ GOOD: Auto-extracted patterns
context.store_memory("pattern_x", {...}, tags=["pattern"])

# ❌ BAD: Manual curated docs
context.store_memory("coding_standards", {...})
# → Use: tool.create("/memories/institutional/standards.md", ...)
```

### 2. Tagging Strategy

```python
# Hierarchical tags for better search
tags = [
    "domain:testing",           # Domain
    "type:pattern",             # Type
    "lang:python",              # Language
    "confidence:high",          # Quality
    f"session:{session_id}"     # Session tracking
]
```

### 3. Memory Hygiene

```python
# Periodic cleanup
def cleanup_stale_memories(days=90):
    # Tier 1: Manual review (backlog completed items)
    tool.delete("/memories/agency_backlog/fixed_items/")

    # Tier 2: Automatic pruning (low confidence + old)
    vector_store.prune(
        min_confidence=0.6,
        max_age_days=days,
        preserve_priority=[CRITICAL, HIGH]
    )

    # Tier 3: Cleared on session end automatically
```

---

## Metrics & Monitoring

### Memory Health Dashboard

```python
{
    "tier1_usage": "45MB / 100MB",
    "tier2_records": "8,432 / 10,000",
    "tier3_sessions": 5,
    "search_latency_p95": "52ms",
    "cache_hit_rate": "87%",
    "consolidation_triggered": 12,
    "learning_extraction_rate": "3.2 patterns/hour"
}
```

### Constitutional Compliance Score

```python
compliance_score = {
    "vectorstore_enabled": True,          # Article IV required
    "learning_extraction_active": True,   # Auto-learning
    "pattern_query_before_action": 0.89,  # 89% compliance
    "pattern_store_after_success": 0.95   # 95% compliance
}
```

---

## References

- [Anthropic Memory Tool Docs](./ANTHROPIC_MEMORY_TOOL.md)
- [VectorStore Implementation](../agency_memory/vector_store.py)
- [Memory Architecture Analysis](../agency_memory/MEMORY_ARCHITECTURE_ANALYSIS.md)
- [AgentContext API](../shared/agent_context.py)
- [Constitution Article IV](../constitution.md#article-iv-continuous-learning)

---

## Future Evolution

### 2025 Q4: Advanced Patterns
- Multimodal memory (text + code + diagrams)
- Neural pathway-like reinforcement
- Real-time knowledge graph updates

### 2026 Q1: Distributed Memory
- Memory-compute disaggregation
- Cross-organization memory sharing (privacy-preserving)
- Federated learning from memory stores

### 2026 Q2: Autonomous Memory Management
- Self-optimizing memory consolidation
- Predictive memory pre-loading
- Memory explanation and interpretability

---

**Status:** ✅ Production-Ready with Clear Evolution Path

This architecture balances **immediate usability** with **long-term scalability**, enabling Agency to learn and improve autonomously while maintaining constitutional compliance.
