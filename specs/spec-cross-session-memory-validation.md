# Spec: Cross-Session Institutional Memory Validation

**Status**: Draft
**Created**: 2025-10-26
**Owner**: SpecGeneratorAgent
**Article IV Compliance**: VectorStore persistence validation

---

## 1. Goals

**Primary Goal**: Validate that patterns stored in Session N are retrievable in Session N+1 with ≥90% accuracy.

**Success Criteria**:
- Session N stores 10 diverse patterns to disk (~/.agency/memories/)
- Session N+1 (new AgentContext instance) retrieves ≥9/10 patterns (90%+ accuracy)
- No memory leaks (sessions properly closed, memory released)
- VectorStore persistence survives process restart

**Non-Goals**:
- Rebuilding VectorStore internals
- Adding new memory features
- Optimizing search performance (already validated)

---

## 2. Context

### Current Implementation

**Three-Tier Architecture** (ADR-006):
- **Tier 1**: Anthropic Memory Tool (file-based, cross-conversation)
- **Tier 2**: VectorStore (FAISS-backed, semantic search) ← **Focus**
- **Tier 3**: Session Memory (temporary working context)

**VectorStore Persistence**:
- **Storage**: `~/.agency/memories/` (default location)
- **Format**: FAISS index + memory records (JSON)
- **Lifecycle**: EnhancedMemoryStore loads on initialization

**Claim to Validate**:
> "Patterns from session N retrieved in session N+1 (90%+ retrieval accuracy)"

### Problem Statement

**What to Prove**:
1. VectorStore.store() persists to disk (not just in-memory)
2. EnhancedMemoryStore loads persisted memories on new session
3. search_memories() retrieves patterns across session boundary
4. Retrieval accuracy ≥90% (9/10 patterns retrieved)

**Why It Matters** (Article IV):
- Cross-session learning is constitutional requirement
- Institutional knowledge must survive process restart
- Agent swarms need shared persistent state

---

## 3. Validation Approach

### Test Strategy (15 Tests Total)

**Unit Tests** (5 tests):
1. VectorStore.store() writes to disk
2. VectorStore.search_by_tags() reads from disk
3. EnhancedMemoryStore initialization loads existing memories
4. Session cleanup releases memory (no leaks)
5. FAISS index persistence (save/load)

**Integration Tests** (5 tests):
1. Session N stores 10 patterns → disk verification
2. Session N+1 retrieves 9/10 patterns (90% accuracy)
3. Multi-agent concurrent writes (no corruption)
4. Session isolation (N+1 doesn't pollute N)
5. Process restart recovery (kill/restart)

**End-to-End Tests** (3 tests):
1. Full mission cycle: Plan → Code → Test → Store → Retrieve
2. Multi-day task checkpoint/resume (3-day simulation)
3. Swarm coordination (3 agents sharing patterns)

**Benchmark** (2 tests):
1. Retrieval accuracy: 100 patterns, ≥90% retrieved
2. Retrieval latency: <100ms for 10k memories (existing spec)

---

## 4. Technical Design

### Test Patterns

**Pattern 1: Store and Retrieve (Session Boundary)**
```python
# Session N (PID 1234)
context_n = create_agent_context(session_id="session_n")
context_n.store_memory(
    key="jwt_auth_success",
    content={"solution": "...", "tests_passed": True},
    tags=["coder", "auth", "success"]
)
del context_n  # Close session N

# Session N+1 (PID 5678, new process)
context_n1 = create_agent_context(session_id="session_n1")
patterns = context_n1.search_memories(
    tags=["auth", "success"],
    include_session=False  # Cross-session search
)
assert len(patterns) >= 1  # ≥90% of stored patterns
assert "jwt_auth_success" in [p["key"] for p in patterns]
```

**Pattern 2: Multi-Agent Concurrent Writes**
```python
# Agent 1, 2, 3 write concurrently
import multiprocessing

def agent_write(agent_id: int):
    context = create_agent_context(session_id=f"agent_{agent_id}")
    for i in range(10):
        context.store_memory(
            key=f"agent_{agent_id}_pattern_{i}",
            content={"data": f"Pattern {i}"},
            tags=[f"agent_{agent_id}", "pattern"]
        )

with multiprocessing.Pool(3) as pool:
    pool.map(agent_write, [1, 2, 3])

# Verify all 30 patterns persisted
context = create_agent_context(session_id="verify")
patterns = context.search_memories(tags=["pattern"], include_session=False)
assert len(patterns) == 30  # No corruption, no lost writes
```

**Pattern 3: Process Restart Recovery**
```python
# Process 1: Store patterns
subprocess.run(["python", "-c", """
from shared.agent_context import create_agent_context
context = create_agent_context(session_id="restart_test")
context.store_memory("restart_pattern", {"data": "test"}, ["restart"])
"""])

# Kill process, start Process 2: Retrieve patterns
subprocess.run(["python", "-c", """
from shared.agent_context import create_agent_context
context = create_agent_context(session_id="restart_verify")
patterns = context.search_memories(tags=["restart"], include_session=False)
assert len(patterns) == 1
assert patterns[0]["key"] == "restart_pattern"
"""])
```

### Acceptance Criteria

**Must Have**:
- ✅ Session N patterns persist to disk (~/.agency/memories/)
- ✅ Session N+1 retrieves ≥90% of Session N patterns
- ✅ No memory leaks (psutil memory check)
- ✅ Process restart recovery (survive kill -9)
- ✅ Concurrent write safety (3 agents, 30 patterns)

**Should Have**:
- ✅ Retrieval latency <100ms (10k memories, existing benchmark)
- ✅ FAISS index integrity (no corruption)
- ✅ Session isolation (N+1 doesn't pollute N)

**Nice to Have**:
- ⚠️ Cross-conversation retrieval (Anthropic Memory Tool, future work)
- ⚠️ VectorStore compression (future optimization)

---

## 5. Deliverables

**Specification** (this file):
- Validation approach (3 test categories)
- Technical design (patterns, acceptance criteria)
- Success metrics (90% retrieval, <100ms latency)

**Test Suite** (15 tests):
- `tests/test_cross_session_memory_validation.py` (unit + integration)
- `tests/e2e/test_cross_session_memory_e2e.py` (end-to-end)
- `tests/benchmarks/test_cross_session_memory_benchmark.py` (accuracy + latency)

**Benchmark Script**:
- `scripts/benchmark_cross_session_memory.py`
- Validates 100 patterns, reports accuracy %
- Validates retrieval latency for 10k memories

**Documentation**:
- Update ADR-006 (Three-Tier Memory Architecture) with validation results
- Update Article IV compliance docs with retrieval accuracy metric

---

## 6. Test Plan

### Unit Tests (5 tests, <10s total)

**Test 1: VectorStore Disk Persistence**
```python
def test_vectorstore_disk_persistence(tmp_path):
    """Verify VectorStore writes to disk."""
    store = VectorStore(storage_path=tmp_path / "memories")
    store.store("test_key", {"data": "test"}, tags=["test"])

    # Verify files created
    assert (tmp_path / "memories" / "index.faiss").exists()
    assert (tmp_path / "memories" / "records.json").exists()
```

**Test 2: EnhancedMemoryStore Load Existing**
```python
def test_enhanced_memory_load_existing(tmp_path):
    """Verify EnhancedMemoryStore loads existing memories."""
    # Session N: Store pattern
    store_n = EnhancedMemoryStore(storage_path=tmp_path)
    store_n.store("pattern_1", {"data": "test"}, tags=["test"])
    del store_n

    # Session N+1: Load existing
    store_n1 = EnhancedMemoryStore(storage_path=tmp_path)
    patterns = store_n1.search(tags=["test"])
    assert len(patterns.records) == 1
```

**Test 3: Session Cleanup (Memory Leak Check)**
```python
def test_session_cleanup_no_leaks():
    """Verify session cleanup releases memory."""
    import psutil
    process = psutil.Process()

    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Create and destroy 100 sessions
    for i in range(100):
        context = create_agent_context(session_id=f"session_{i}")
        context.store_memory(f"key_{i}", {"data": "test"}, ["test"])
        del context

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_growth = final_memory - initial_memory

    assert memory_growth < 50  # <50MB growth for 100 sessions
```

**Test 4: FAISS Index Persistence**
```python
def test_faiss_index_persistence(tmp_path):
    """Verify FAISS index saves and loads correctly."""
    from agency_memory.vector_index import VectorIndex

    index = VectorIndex(index_path=tmp_path / "index.faiss")
    index.add_vectors(["key1", "key2"], [[0.1]*384, [0.2]*384])
    index.save_index()

    # Load in new instance
    index2 = VectorIndex(index_path=tmp_path / "index.faiss")
    assert index2.index.ntotal == 2
```

**Test 5: VectorStore Search by Tags**
```python
def test_vectorstore_search_by_tags(tmp_path):
    """Verify tag-based search reads from disk."""
    store = VectorStore(storage_path=tmp_path)
    store.store("key1", {"data": "test1"}, tags=["tag1", "success"])
    store.store("key2", {"data": "test2"}, tags=["tag2", "success"])

    results = store.search_by_tags(tags=["success"], min_confidence=0.6)
    assert len(results) == 2
```

### Integration Tests (5 tests, <30s total)

**Test 6: Session N → Session N+1 (90% Accuracy)**
```python
def test_session_n_to_n1_90_percent_accuracy(tmp_path):
    """Validate 90%+ retrieval across session boundary."""
    # Session N: Store 10 patterns
    context_n = create_agent_context(session_id="session_n")
    for i in range(10):
        context_n.store_memory(
            key=f"pattern_{i}",
            content={"solution": f"Solution {i}", "tests_passed": True},
            tags=["coder", "success", f"pattern_{i}"]
        )
    del context_n

    # Session N+1: Retrieve patterns
    context_n1 = create_agent_context(session_id="session_n1")
    patterns = context_n1.search_memories(
        tags=["success"],
        include_session=False  # Cross-session
    )

    assert len(patterns) >= 9  # ≥90% retrieval
    retrieved_keys = [p["key"] for p in patterns]
    assert "pattern_0" in retrieved_keys
```

**Test 7: Multi-Agent Concurrent Writes**
```python
def test_multi_agent_concurrent_writes():
    """Verify concurrent writes don't corrupt VectorStore."""
    # Test Pattern 2 (see above)
```

**Test 8: Session Isolation**
```python
def test_session_isolation():
    """Verify Session N+1 doesn't pollute Session N namespace."""
    context_n = create_agent_context(session_id="session_n")
    context_n.store_memory("n_pattern", {"data": "N"}, ["session_n"])

    context_n1 = create_agent_context(session_id="session_n1")
    context_n1.store_memory("n1_pattern", {"data": "N+1"}, ["session_n1"])

    # Verify isolation
    n_patterns = context_n.search_memories(tags=["session_n"], include_session=True)
    assert len(n_patterns) == 1
    assert n_patterns[0]["key"] == "n_pattern"
```

**Test 9: Disk Verification (File System Check)**
```python
def test_disk_verification():
    """Verify patterns physically written to disk."""
    context = create_agent_context(session_id="disk_test")
    context.store_memory("disk_pattern", {"data": "test"}, ["disk"])

    # Check disk files
    memory_path = Path.home() / ".agency/memories"
    assert (memory_path / "index.faiss").exists()
    assert (memory_path / "records.json").exists()

    # Verify content
    with open(memory_path / "records.json") as f:
        records = json.load(f)
        assert any(r["key"] == "disk_pattern" for r in records)
```

**Test 10: Process Restart Recovery**
```python
def test_process_restart_recovery():
    """Verify VectorStore survives process restart."""
    # Test Pattern 3 (see above)
```

### End-to-End Tests (3 tests, <60s total)

**Test 11: Full Mission Cycle**
```python
def test_full_mission_cycle():
    """Simulate Plan → Code → Test → Store → Retrieve."""
    # Phase 1: Planning (Session 1)
    planner_ctx = create_agent_context(session_id="planner")
    planner_ctx.store_memory(
        "plan_jwt_auth",
        {"tasks": ["design", "implement", "test"]},
        ["planner", "plan"]
    )

    # Phase 2: Implementation (Session 2)
    coder_ctx = create_agent_context(session_id="coder")
    plan = coder_ctx.search_memories(tags=["plan"], include_session=False)
    assert len(plan) == 1

    coder_ctx.store_memory(
        "impl_jwt_auth",
        {"code": "...", "tests_passed": True},
        ["coder", "success"]
    )

    # Phase 3: Learning (Session 3)
    learning_ctx = create_agent_context(session_id="learning")
    successes = learning_ctx.search_memories(tags=["success"], include_session=False)
    assert len(successes) == 1
```

**Test 12: Multi-Day Task Checkpoint/Resume**
```python
def test_multi_day_task_checkpoint_resume():
    """Simulate 3-day task with checkpoint/resume."""
    # Day 1: Start task
    day1_ctx = create_agent_context(session_id="day_1")
    day1_ctx.store_memory(
        "day_1_checkpoint",
        {"completed": ["task1", "task2"], "phase": 1},
        ["checkpoint", "day_1"]
    )

    # Day 2: Resume from checkpoint
    day2_ctx = create_agent_context(session_id="day_2")
    checkpoint = day2_ctx.search_memories(tags=["checkpoint"], include_session=False)
    assert len(checkpoint) == 1
    assert checkpoint[0]["content"]["phase"] == 1

    day2_ctx.store_memory(
        "day_2_checkpoint",
        {"completed": ["task1", "task2", "task3"], "phase": 2},
        ["checkpoint", "day_2"]
    )

    # Day 3: Resume from latest checkpoint
    day3_ctx = create_agent_context(session_id="day_3")
    checkpoints = day3_ctx.search_memories(tags=["checkpoint"], include_session=False)
    assert len(checkpoints) == 2
    latest = max(checkpoints, key=lambda x: x["content"]["phase"])
    assert latest["content"]["phase"] == 2
```

**Test 13: Swarm Coordination (3 Agents)**
```python
def test_swarm_coordination():
    """Simulate 3 agents sharing patterns via VectorStore."""
    # Agent 1: Discovers pattern
    agent1_ctx = create_agent_context(session_id="agent_1")
    agent1_ctx.store_memory(
        "auth_pattern",
        {"pattern": "JWT RSA-256", "confidence": 0.95},
        ["auth", "pattern", "shared"]
    )

    # Agent 2: Applies pattern
    agent2_ctx = create_agent_context(session_id="agent_2")
    patterns = agent2_ctx.search_memories(tags=["shared", "pattern"], include_session=False)
    assert len(patterns) == 1

    # Agent 3: Refines pattern
    agent3_ctx = create_agent_context(session_id="agent_3")
    patterns = agent3_ctx.search_memories(tags=["shared"], include_session=False)
    assert len(patterns) == 1
    agent3_ctx.store_memory(
        "auth_pattern_refined",
        {"pattern": "JWT RSA-256 + refresh tokens", "confidence": 0.98},
        ["auth", "pattern", "shared", "refined"]
    )

    # Verify all agents see refinement
    verify_ctx = create_agent_context(session_id="verify")
    all_patterns = verify_ctx.search_memories(tags=["shared"], include_session=False)
    assert len(all_patterns) == 2
```

### Benchmark Tests (2 tests, <120s total)

**Test 14: Retrieval Accuracy Benchmark**
```python
def test_retrieval_accuracy_benchmark():
    """Validate 90%+ retrieval accuracy with 100 patterns."""
    # Store 100 patterns across 10 sessions
    for session_idx in range(10):
        ctx = create_agent_context(session_id=f"session_{session_idx}")
        for pattern_idx in range(10):
            ctx.store_memory(
                key=f"pattern_{session_idx}_{pattern_idx}",
                content={"data": f"Pattern {pattern_idx}"},
                tags=["benchmark", f"session_{session_idx}"]
            )

    # Retrieve from new session
    verify_ctx = create_agent_context(session_id="verify")
    retrieved = verify_ctx.search_memories(tags=["benchmark"], include_session=False)

    accuracy = len(retrieved) / 100.0
    assert accuracy >= 0.90  # ≥90% retrieval
```

**Test 15: Retrieval Latency Benchmark (10k memories)**
```python
def test_retrieval_latency_benchmark():
    """Validate <100ms retrieval latency at 10k memories."""
    # Populate 10k patterns
    ctx = create_agent_context(session_id="latency_test")
    for i in range(10000):
        ctx.store_memory(f"pattern_{i}", {"data": i}, ["latency"])

    # Measure retrieval latency
    import time
    start = time.perf_counter()
    results = ctx.search_memories(tags=["latency"], include_session=False)
    latency_ms = (time.perf_counter() - start) * 1000

    assert latency_ms < 100  # <100ms (existing spec)
    assert len(results) == 10000
```

---

## 7. Success Metrics

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| **Retrieval Accuracy** | ≥90% | Test 14: 100 patterns, count retrieved |
| **Retrieval Latency** | <100ms | Test 15: 10k memories, measure time |
| **Memory Leak** | <50MB/100 sessions | Test 3: psutil memory check |
| **Concurrent Write Safety** | 100% integrity | Test 7: 3 agents, 30 patterns |
| **Process Restart Recovery** | 100% recovery | Test 10: subprocess kill/restart |
| **Session Isolation** | 100% isolation | Test 8: namespace verification |

**Acceptance**: All 15 tests pass with metrics above targets.

---

## 8. Dependencies

**Existing Infrastructure**:
- ✅ VectorStore (agency_memory/vector_store.py)
- ✅ EnhancedMemoryStore (agency_memory/enhanced_memory_store.py)
- ✅ AgentContext (shared/agent_context.py)
- ✅ FAISS index (agency_memory/vector_index.py)

**Test Dependencies**:
- pytest (test framework)
- psutil (memory leak detection)
- multiprocessing (concurrent write test)
- subprocess (process restart test)

**No New Code Required** (validation only):
- Tests validate existing behavior
- No VectorStore modifications needed
- No new memory features added

---

## 9. Constitutional Compliance

**Article I (Complete Context)**:
- ✅ All tests run to completion (no partial results)
- ✅ Memory verification includes disk check (not just in-memory)

**Article II (100% Verification)**:
- ✅ 90% retrieval accuracy is measurable, testable target
- ✅ All 15 tests must pass (no skipped tests)

**Article III (Automated Enforcement)**:
- ✅ Tests run in CI/CD (local enforcement)
- ✅ No manual memory verification steps

**Article IV (Continuous Learning)**:
- ✅ **PRIMARY FOCUS**: Validate cross-session learning works
- ✅ VectorStore persistence is constitutional requirement
- ✅ Tests prove institutional memory survives sessions

**Article V (Spec-Driven)**:
- ✅ This spec defines validation approach
- ✅ All tests trace to spec requirements

---

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **FAISS index corruption** | High (data loss) | Test 10: Process restart recovery validates integrity |
| **Memory leak in VectorStore** | Medium (performance) | Test 3: psutil check detects leaks |
| **Concurrent write race conditions** | High (data corruption) | Test 7: Multi-agent concurrent writes |
| **Disk I/O failures** | Medium (persistence) | Test 9: Disk verification with file checks |
| **Session pollution** | Low (isolation) | Test 8: Session isolation verification |

---

## 11. Implementation Notes

**File Locations**:
- Spec: `specs/spec-cross-session-memory-validation.md` (this file)
- Unit tests: `tests/test_cross_session_memory_validation.py`
- E2E tests: `tests/e2e/test_cross_session_memory_e2e.py`
- Benchmarks: `tests/benchmarks/test_cross_session_memory_benchmark.py`
- Benchmark script: `scripts/benchmark_cross_session_memory.py`

**Test Execution**:
```bash
# Run all validation tests
pytest tests/test_cross_session_memory_validation.py -v

# Run benchmarks
python scripts/benchmark_cross_session_memory.py

# Run E2E tests
pytest tests/e2e/test_cross_session_memory_e2e.py -v
```

**Estimated Effort**:
- Spec creation: 1 hour (DONE)
- Test implementation: 3 hours (15 tests × 12 minutes)
- Benchmark script: 1 hour
- Documentation updates: 30 minutes
- **Total**: ~5.5 hours

---

## 12. Appendix: Example Patterns

### Pattern A: Simple Store/Retrieve
```python
# Store
context.store_memory("key1", {"data": "value1"}, ["tag1"])

# Retrieve (same session)
patterns = context.search_memories(tags=["tag1"], include_session=True)
assert len(patterns) == 1

# Retrieve (cross-session)
context2 = create_agent_context(session_id="session2")
patterns = context2.search_memories(tags=["tag1"], include_session=False)
assert len(patterns) == 1  # Proves persistence
```

### Pattern B: Confidence Filtering
```python
# Store with confidence
context.store_memory(
    "high_conf",
    {"pattern": "JWT auth"},
    ["auth"],
    confidence=0.95
)
context.store_memory(
    "low_conf",
    {"pattern": "Basic auth"},
    ["auth"],
    confidence=0.3
)

# Search with min_confidence
context2 = create_agent_context(session_id="session2")
patterns = context2.search_memories(
    tags=["auth"],
    min_confidence=0.6,  # Article IV requirement
    include_session=False
)
assert len(patterns) == 1  # Only high_conf retrieved
```

### Pattern C: Multi-Tag Search
```python
# Store with multiple tags
context.store_memory(
    "multi_tag",
    {"data": "test"},
    ["tag1", "tag2", "tag3"]
)

# Search with subset of tags
context2 = create_agent_context(session_id="session2")
patterns = context2.search_memories(
    tags=["tag1", "tag2"],
    include_session=False
)
assert len(patterns) == 1  # Matches if ANY tag matches
```

---

**End of Specification**

**Next Steps**:
1. Review spec with user (approval checkpoint)
2. Implement 15 tests (unit, integration, E2E)
3. Create benchmark script
4. Update ADR-006 with validation results
5. Document Article IV compliance metrics
