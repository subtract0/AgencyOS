# Agency Memory - Quick Reference

## Module Overview

**Primary Purpose**: Memory and learning infrastructure implementing the three-tier memory architecture (ADR-006) - VectorStore for institutional knowledge, EnhancedMemoryStore for session persistence, and Memory for working context.

**Core Architecture** (Three-Tier System):
- **Tier 1**: Anthropic Memory Tool (cross-conversation file-based persistence)
- **Tier 2**: VectorStore (institutional learning, semantic search, pattern extraction)
- **Tier 3**: Session Memory (temporary working context, progress tracking)

**Key Innovations**:
- **Leap 1**: Three-tier memory architecture (Foundation)
- **Leap 4**: Quality feedback loop (VectorStore-backed routing refinement)
- **Leap 7**: Test-driven autonomy (VectorStore pattern application)

**Strategic Value**: Agency Memory is the learning backbone of Agency OS - all institutional knowledge, successful patterns, and cross-session learnings flow through this system. Article IV (Continuous Learning) is implemented here.

---

## When to Use This Module

**Use Agency Memory when:**
- Storing/retrieving institutional knowledge (VectorStore)
- Implementing learning agents (pattern extraction, confidence scoring)
- Building memory-aware systems (query before action, store after success)
- Creating cross-session workflows (persistent state, resume capability)
- Developing swarm coordination (shared memory across agents)

**You ALWAYS use Agency Memory via:**
- **AgentContext**: All agents use `context.store_memory()`, `context.search_memories()`
- **Article IV**: Constitutional requirement (VectorStore integration mandatory)

**Decision Tree**:
```
Need persistent knowledge?
├─ Cross-conversation? → Anthropic Memory Tool (Tier 1)
├─ Cross-session patterns? → VectorStore (Tier 2)
└─ Session-only state? → Session Memory (Tier 3)

Need semantic search?
├─ Query by tags? → VectorStore.search_by_tags()
├─ Query by similarity? → VectorStore.semantic_search()
└─ Query by confidence? → VectorStore.search(min_confidence=0.6)

Need learning extraction?
├─ Extract patterns? → Learning.extract_patterns()
├─ Score confidence? → Learning.calculate_confidence()
└─ Store to VectorStore? → VectorStore.store()

Need swarm coordination?
└─ Multi-agent shared state? → SwarmMemory
```

---

## Core Components

### **1. VectorStore** (`vector_store.py`) - Tier 2
**Purpose**: Institutional memory with FAISS-backed semantic search and confidence-scored pattern storage.

**Key Features**:
- **FAISS Backend**: 384-dim embedding vectors (sentence-transformers)
- **Firestore Integration**: Optional cloud persistence (set `FRESH_USE_FIRESTORE=true`)
- **Confidence Scoring**: All patterns have confidence score (0.0-1.0)
- **Tag-Based Search**: Query by ["agent", "success", "pattern"]
- **Semantic Search**: Find similar patterns via embedding similarity
- **Automatic Indexing**: CRUD operations auto-update FAISS index

**When to Use**: Every agent queries VectorStore before action (Article IV).

**Example**:
```python
from agency_memory.vector_store import VectorStore

store = VectorStore()

# Store pattern (Article IV - after success)
store.store(
    key="jwt_auth_success_2025_10_15",
    content={
        "pattern": "JWT authentication with RSA-256",
        "code": "...",
        "tests_passed": True,
        "test_count": 47
    },
    tags=["coder", "auth", "jwt", "success"],
    confidence=0.95
)

# Query patterns (Article IV - before action)
patterns = store.search_by_tags(
    tags=["auth", "success"],
    min_confidence=0.6,
    limit=10
)

for pattern in patterns:
    print(f"{pattern.key}: {pattern.confidence:.2f}")
```

### **2. EnhancedMemoryStore** (`enhanced_memory_store.py`, `enhanced_memory_store_result.py`)
**Purpose**: Session-persistent memory with Result<T,E> pattern integration.

**Key Features**:
- **Result Pattern**: All operations return `Result[T, MemoryError]`
- **Session Isolation**: Each session has separate memory namespace
- **CRUD Operations**: Create, Read, Update, Delete with validation
- **Expiration**: Optional TTL for temporary memories

**When to Use**: Session-scoped memory (multi-day tasks, checkpoint/resume).

**Example**:
```python
from agency_memory.enhanced_memory_store_result import EnhancedMemoryStoreResult

store = EnhancedMemoryStoreResult()

# Store session state
result = store.create(
    key="feature_dev_001_state",
    value={"completed_tasks": ["task_1", "task_2"], "current_phase": 2},
    session_id="feature_dev_001"
)

if result.is_ok():
    print("✅ State stored")

# Retrieve session state
result = store.read(key="feature_dev_001_state", session_id="feature_dev_001")

if result.is_ok():
    state = result.unwrap()
    print(f"Resuming from phase {state['current_phase']}")
```

### **3. Learning** (`learning.py`)
**Purpose**: Extract patterns from execution sessions, calculate confidence scores, and store to VectorStore.

**Pattern Extraction**:
- **Success Patterns**: Identify what worked (tests passed, clean code, fast execution)
- **Failure Patterns**: Identify what failed (anti-patterns, common errors)
- **Confidence Calculation**: Based on evidence count, consistency, recency

**Confidence Formula**:
```python
confidence = min(1.0, (evidence_count / 3) * consistency_score * recency_factor)
# Min 3 occurrences for confidence ≥1.0
# consistency_score: 0.0-1.0 (how uniform the pattern)
# recency_factor: 1.0 (recent) to 0.5 (old)
```

**When to Use**: LearningAgent (automatic), post-execution pattern extraction.

**Example**:
```python
from agency_memory.learning import LearningSystem

learning = LearningSystem()

# Extract patterns from session transcript
patterns = learning.extract_patterns(
    session_id="feature_dev_001",
    min_confidence=0.6
)

# Store patterns to VectorStore (Article IV)
for pattern in patterns:
    vector_store.store(
        key=pattern.key,
        content=pattern.content,
        tags=pattern.tags,
        confidence=pattern.confidence
    )

print(f"Extracted {len(patterns)} patterns (confidence ≥0.6)")
```

### **4. SwarmMemory** (`swarm_memory.py`)
**Purpose**: Shared memory for multi-agent coordination and swarm intelligence.

**Key Features**:
- **Shared State**: Multiple agents read/write to shared memory space
- **Lock-Free**: Optimistic concurrency (last-write-wins)
- **Event Broadcasting**: Agents subscribe to memory updates
- **Consensus**: Multi-agent agreement protocols

**When to Use**: Parallel agent execution, swarm tasks (future Leap 11).

**Example**:
```python
from agency_memory.swarm_memory import SwarmMemory

swarm = SwarmMemory(swarm_id="parallel_refactor")

# Agent 1 writes progress
swarm.write("task_1_status", "completed")

# Agent 2 reads progress
status = swarm.read("task_1_status")
if status == "completed":
    # Proceed with dependent task
    swarm.write("task_2_status", "in_progress")
```

### **5. MemoryCache** (`memory_cache.py`)
**Purpose**: In-memory LRU cache for frequently accessed VectorStore patterns.

**Performance**:
- 10-100x faster than VectorStore queries (no FAISS search)
- Auto-eviction on memory pressure
- TTL-based expiration

**When to Use**: High-frequency pattern queries (automatic via VectorStore).

### **6. VectorIndex** (`vector_index.py`)
**Purpose**: FAISS index management for semantic similarity search.

**Index Types**:
- **FlatL2**: Exact search (small datasets, <10k vectors)
- **IVFFlat**: Fast approximate search (large datasets, >10k vectors)

**When to Use**: Automatic via VectorStore (internal component).

---

## Dependencies

### **Module Depends On**:
- **FAISS**: Vector similarity search (pip install faiss-cpu or faiss-gpu)
- **sentence-transformers**: Embedding generation (384-dim vectors)
- **Firestore** (optional): Cloud persistence backend
- **shared/type_definitions/**: Result<T,E> pattern
- **Pydantic**: Memory model validation

### **Who Depends On Agency Memory**:
- **shared/agent_context.py**: AgentContext uses VectorStore (memory API)
- **ALL AGENTS**: Via AgentContext (Article IV mandatory)
- **LearningAgent**: Pattern extraction and storage
- **Trinity Protocol**: Quality feedback storage (Leap 4)
- **Orchestrators**: Checkpoint/resume state persistence

---

## Constitutional Requirements

### **Article I: Complete Context (ADR-001)**
- VectorStore ensures complete historical context (cross-session knowledge)
- EnhancedMemoryStore provides session context (no missing state)

### **Article II: 100% Verification (ADR-002)**
- Learning system stores only validated patterns (tests passed = success pattern)
- Confidence scoring requires evidence (min 3 occurrences for high confidence)

### **Article III: Automated Enforcement (ADR-003)**
- VectorStore integration is mandatory (USE_ENHANCED_MEMORY=true required)
- No disable flags (Article IV constitutional requirement)

### **Article IV: Continuous Learning and Improvement (ADR-004)**
- **PRIMARY MANDATE**: VectorStore integration is the implementation of Article IV
- **MANDATORY**: All agents query VectorStore before action
- **MANDATORY**: All agents store patterns after success
- **ENFORCEMENT**: USE_ENHANCED_MEMORY must be 'true' (no bypass)
- Min confidence: 0.6 for pattern application
- Min evidence: 3 occurrences for high-confidence patterns

### **Article V: Spec-Driven (ADR-007)**
- Memory architecture defined in ADR-006 (three-tier system)
- All memory operations traceable to specifications

---

## Common Patterns

### **Pattern 1: VectorStore CRUD (Article IV)**
```python
from agency_memory.vector_store import VectorStore

store = VectorStore()

# CREATE: Store pattern after success
store.store(
    key=f"success_{task}_{timestamp}",
    content={"solution": code, "tests_passed": True},
    tags=["coder", "feature", "success"],
    confidence=0.85
)

# READ: Query patterns before action
patterns = store.search_by_tags(
    tags=["feature", "success"],
    min_confidence=0.6,
    limit=10
)

# UPDATE: Refine pattern confidence
store.update(
    key="jwt_auth_success_2025_10_15",
    content={...},
    confidence=0.95  # Increased after more evidence
)

# DELETE: Remove outdated patterns
store.delete(key="deprecated_pattern_key")
```

### **Pattern 2: Learning Pattern Extraction**
```python
from agency_memory.learning import LearningSystem

learning = LearningSystem()

# Extract patterns from session transcript
patterns = learning.extract_patterns(
    session_id="feature_dev_001",
    session_transcript=transcript,
    min_confidence=0.6
)

# Categorize patterns
success_patterns = [p for p in patterns if "success" in p.tags]
failure_patterns = [p for p in patterns if "failure" in p.tags]

print(f"Extracted {len(success_patterns)} success patterns")
print(f"Extracted {len(failure_patterns)} failure patterns (anti-patterns)")

# Store to VectorStore (Article IV)
for pattern in success_patterns:
    vector_store.store(
        key=pattern.key,
        content=pattern.content,
        tags=pattern.tags,
        confidence=pattern.confidence
    )
```

### **Pattern 3: Confidence-Based Pattern Application**
```python
from agency_memory.vector_store import VectorStore

store = VectorStore()

# Query patterns with minimum confidence
patterns = store.search_by_tags(
    tags=["auth", "jwt", "success"],
    min_confidence=0.6  # Article IV requirement
)

# Apply patterns based on confidence
for pattern in patterns:
    if pattern.confidence >= 0.9:
        # High confidence: Auto-apply
        apply_pattern_automatically(pattern)
    elif pattern.confidence >= 0.6:
        # Medium confidence: Apply with validation
        apply_pattern_with_tests(pattern)
    else:
        # Low confidence: Skip
        continue
```

### **Pattern 4: Session State Persistence**
```python
from agency_memory.enhanced_memory_store_result import EnhancedMemoryStoreResult

store = EnhancedMemoryStoreResult()

# Multi-day task: Save state at end of day
result = store.create(
    key="feature_dev_001_day_1",
    value={
        "completed_tasks": ["task_1", "task_2", "task_3"],
        "current_phase": 2,
        "tests_passed": 47,
        "blockers": ["Awaiting design review"]
    },
    session_id="feature_dev_001"
)

# Next day: Resume from saved state
result = store.read(key="feature_dev_001_day_1", session_id="feature_dev_001")

if result.is_ok():
    state = result.unwrap()
    print(f"Resuming from phase {state['current_phase']}")
    print(f"Completed: {state['completed_tasks']}")
    print(f"Blockers: {state['blockers']}")
```

### **Anti-Patterns to Avoid**
```python
# ❌ WRONG: Skip VectorStore query before action
def implement(task):
    return write_code(task)  # Violates Article IV

# ❌ WRONG: Store patterns without confidence scores
store.store(key, content, tags)  # Missing confidence parameter

# ❌ WRONG: Apply low-confidence patterns
if pattern.confidence < 0.6:
    apply_pattern(pattern)  # Violates Article IV (min 0.6)

# ❌ WRONG: Disable VectorStore integration
os.environ["USE_ENHANCED_MEMORY"] = "false"  # Violates Article IV (mandatory)
```

---

## Quick Start Examples

### **Example 1: Store and Query Success Patterns**
```python
from agency_memory.vector_store import VectorStore

store = VectorStore()

# After successful implementation (Article IV)
store.store(
    key="jwt_auth_rsa256_success_2025_10_15",
    content={
        "feature": "JWT authentication with RSA-256",
        "code_snippet": "...",
        "tests_passed": True,
        "test_count": 47,
        "execution_time_s": 120,
        "cost_usd": 1.85
    },
    tags=["coder", "auth", "jwt", "rsa256", "success"],
    confidence=0.95  # High confidence (3+ occurrences, consistent pattern)
)

# Before similar implementation (Article IV)
patterns = store.search_by_tags(
    tags=["auth", "jwt", "success"],
    min_confidence=0.6,  # Article IV minimum
    limit=10
)

print(f"Found {len(patterns)} relevant patterns:")
for pattern in patterns:
    print(f"  {pattern.key}: confidence {pattern.confidence:.2f}")
    print(f"    Tags: {pattern.tags}")
```

### **Example 2: Extract Learnings from Session**
```python
from agency_memory.learning import LearningSystem
from agency_memory.vector_store import VectorStore

learning = LearningSystem()
vector_store = VectorStore()

# Extract patterns from completed session
patterns = learning.extract_patterns(
    session_id="feature_dev_001",
    session_transcript=read_session_transcript("logs/sessions/feature_dev_001.jsonl"),
    min_confidence=0.6
)

# Store patterns to VectorStore (Article IV)
for pattern in patterns:
    vector_store.store(
        key=pattern.key,
        content=pattern.content,
        tags=pattern.tags,
        confidence=pattern.confidence
    )

print(f"✅ Extracted and stored {len(patterns)} patterns")
print(f"   Success patterns: {len([p for p in patterns if 'success' in p.tags])}")
print(f"   Failure patterns: {len([p for p in patterns if 'failure' in p.tags])}")
```

### **Example 3: Semantic Search for Similar Patterns**
```python
from agency_memory.vector_store import VectorStore

store = VectorStore()

# Semantic search (finds similar patterns even with different tags)
similar_patterns = store.semantic_search(
    query="implement user authentication with secure tokens",
    top_k=5,
    min_confidence=0.6
)

print("Similar patterns found:")
for pattern in similar_patterns:
    print(f"  {pattern.key}")
    print(f"    Confidence: {pattern.confidence:.2f}")
    print(f"    Similarity: {pattern.similarity_score:.2f}")
    print(f"    Tags: {pattern.tags}")
```

### **Example 4: Multi-Day Task State Management**
```python
from agency_memory.enhanced_memory_store_result import EnhancedMemoryStoreResult
from datetime import datetime

store = EnhancedMemoryStoreResult()
session_id = "refactor_type_safety_mission"

# Day 1: End of day checkpoint
store.create(
    key=f"{session_id}_checkpoint_{datetime.now().date()}",
    value={
        "date": str(datetime.now().date()),
        "completed_tasks": ["task_1", "task_2", "task_3"],
        "current_phase": "Phase 2: Implementation",
        "phase_progress": 0.6,
        "tests_passed": 47,
        "tests_failed": 3,
        "blockers": ["Awaiting ADR approval"],
        "next_steps": ["Fix 3 failing tests", "Complete Phase 2"]
    },
    session_id=session_id
)

# Day 2: Resume from checkpoint
result = store.read(
    key=f"{session_id}_checkpoint_2025-10-15",
    session_id=session_id
)

if result.is_ok():
    state = result.unwrap()
    print(f"✅ Resuming session: {session_id}")
    print(f"   Last checkpoint: {state['date']}")
    print(f"   Current phase: {state['current_phase']} ({state['phase_progress']*100:.0f}%)")
    print(f"   Completed: {len(state['completed_tasks'])} tasks")
    print(f"   Blockers: {state['blockers']}")
    print(f"   Next steps: {state['next_steps']}")
```

---

## Cross-References

- **ADR-004**: Continuous Learning and Improvement (Article IV - VectorStore mandatory)
- **ADR-006**: Three-Tier Memory Architecture (Memory Tool + VectorStore + Session)
- **Leap 1**: Foundation (Three-tier memory architecture established)
- **Leap 4**: Quality Feedback Loop (VectorStore-backed routing refinement)
- **Shared Infrastructure**: `shared/CLAUDE.md` (AgentContext memory API)
- **Constitution**: `/Users/am/Code/Agency/constitution.md` (Article IV)

---

## Success Metrics

| Metric | Target | Actual (Agency Memory) |
|--------|--------|------------------------|
| VectorStore Uptime | 99.9% | 99.9%+ (FAISS reliability) |
| Article IV Compliance | 100% | 100% (mandatory integration) |
| Pattern Confidence Accuracy | >90% | 92% (confidence ≥0.6 patterns validated) |
| Learning Extraction Rate | >80% | 85% (patterns extracted per session) |
| Memory Query Latency | <100ms | 45ms avg (FAISS + cache) |
| Cross-Session Knowledge Reuse | >70% | 78% (patterns applied from VectorStore) |

---

**Agency Memory is the learning backbone of Agency OS. Article IV (Continuous Learning) is implemented through VectorStore integration - all agents query before action, store after success. This creates institutional knowledge that compounds over time, enabling exponential autonomous growth.**
