# Cross-Session Institutional Memory Test Suite - Summary

**Generated**: 2025-10-26
**Specification**: `specs/spec-cross-session-memory-validation.md`
**Constitutional Requirement**: Article IV - Cross-session learning and institutional memory persistence

---

## Test Suite Overview

**Total Tests**: 15 tests across 4 categories
**TDD Protocol**: RED-GREEN-REFACTOR (currently in RED phase)
**Expected Behavior**: Tests FAIL initially (RED) to validate cross-session persistence gaps

| Category | Tests | File | Status |
|----------|-------|------|--------|
| **Unit** | 5 | `tests/agency_memory/test_cross_session_unit.py` | ✅ Created (RED phase) |
| **Integration** | 5 | `tests/agency_memory/test_cross_session_integration.py` | ✅ Created (RED phase) |
| **E2E** | 3 | `tests/e2e/test_cross_session_memory_e2e.py` | ✅ Created (RED phase) |
| **Benchmark** | 2 | `tests/benchmarks/test_cross_session_benchmark.py` | ✅ Created (RED phase) |

---

## TDD Validation Results

### RED Phase Confirmation ✅

**Integration Test**: `test_session_n_to_n_plus_1_retrieval`
```
Session N: Stored 10 patterns
Session N+1: Retrieved 0/10 patterns (0%)
❌ FAIL: Retrieval accuracy 0% below 90% threshold
```

**Benchmark Test**: `test_90_percent_retrieval_accuracy`
```
Stored: 100 patterns
Retrieved: 0 patterns
Accuracy: 0.00%
Target: ≥90.00%
❌ FAIL: Retrieval accuracy benchmark FAILED
```

**Analysis**:
- ✅ Tests correctly fail (RED phase)
- ✅ Failure demonstrates cross-session persistence gap
- ✅ 0% retrieval accuracy proves memories are NOT persisted across sessions
- ✅ TDD protocol validated (tests written BEFORE implementation fixes)

---

## Test Catalog

### Unit Tests (5 tests) - `test_cross_session_unit.py`

| Test | Purpose | Expected RED Behavior | Article IV Validation |
|------|---------|----------------------|----------------------|
| `test_vectorstore_persists_to_disk` | Verify VectorStore writes to disk | Pass (in-memory works) | Partial (no file persistence) |
| `test_vectorstore_loads_from_disk` | Verify VectorStore loads existing memories | Pass (same process) | Partial (cross-process fails) |
| `test_faiss_index_persists` | Verify FAISS index saves/loads | FAISS not installed | Skipped (optional dependency) |
| `test_session_cleanup_no_memory_leak` | Verify no memory leaks (100 sessions) | Pass (good memory mgmt) | ✅ Memory stability |
| `test_memory_deduplication_across_sessions` | Verify duplicate keys handled | Untested (persistence first) | ⚠️ Needs investigation |

**Observations**:
- VectorStore has **in-memory** persistence (same process)
- VectorStore lacks **cross-process** persistence (different sessions)
- Memory management is healthy (no leaks detected)

### Integration Tests (5 tests) - `test_cross_session_integration.py`

| Test | Purpose | RED Result | Article IV Impact |
|------|---------|------------|-------------------|
| `test_session_n_to_n_plus_1_retrieval` | 90% retrieval accuracy | ❌ FAIL (0%) | **CRITICAL** - No cross-session learning |
| `test_concurrent_session_writes` | Concurrent write safety | ❌ FAIL (expected) | Multi-agent swarm broken |
| `test_process_restart_recovery` | Survive process restart | ❌ FAIL (expected) | No institutional memory survival |
| `test_partial_session_failure_recovery` | Partial write resilience | ❌ FAIL (expected) | No graceful degradation |
| `test_multi_day_checkpoint_resume` | Multi-day task resume | ❌ FAIL (expected) | No checkpoint persistence |

**Impact**:
- **HIGH SEVERITY**: 0% cross-session retrieval violates Article IV
- **Mission-Critical**: Agents cannot learn from past sessions
- **Swarm Broken**: Multi-agent coordination impossible without shared memory
- **Long-Running Tasks**: Multi-day tasks cannot checkpoint/resume

### E2E Tests (3 tests) - `test_cross_session_memory_e2e.py`

| Test | Purpose | RED Result | Business Impact |
|------|---------|------------|-----------------|
| `test_full_mission_cross_session` | Mission N → Mission N+1 learning | ❌ FAIL (expected) | No institutional knowledge accumulation |
| `test_agent_swarm_coordination` | 5 agents share patterns | ❌ FAIL (expected) | Swarm intelligence impossible |
| `test_100_session_persistence` | Stress test (100 sessions) | ❌ FAIL (expected) | Scale limitations |

**Strategic Implications**:
- **Autonomous Growth Blocked**: Agents cannot accumulate knowledge over time
- **Cost Optimization Broken**: Cannot reuse successful patterns (Article IV)
- **Quality Feedback Loop Incomplete**: Leap 4 depends on cross-session learning

### Benchmark Tests (2 tests) - `test_cross_session_benchmark.py`

| Benchmark | Target | Current Result | Status |
|-----------|--------|----------------|--------|
| **Retrieval Accuracy** | ≥90% | 0% | ❌ FAIL (critical gap) |
| **Retrieval Latency** | <100ms | Untestable (0 memories retrieved) | ⚠️ Blocked |
| **Query Throughput** | ≥1000 qps | Untestable (0 memories retrieved) | ⚠️ Blocked |

**Performance Baseline**:
- **Accuracy**: 0% (90% below target) - **CRITICAL**
- **Latency**: Cannot benchmark (no data to retrieve)
- **Throughput**: Cannot benchmark (no data to retrieve)

---

## Root Cause Analysis

### Why Tests Fail (RED Phase)

**Primary Issue**: `AgentContext` stores memories in **session-scoped** `Memory` instance
- Each `create_agent_context(session_id)` creates **new** `Memory()` instance
- `Memory()` is in-memory only (no persistence backend)
- When session ends (`del context`), memories are **garbage collected**

**Code Evidence**:
```python
# shared/agent_context.py:37
def __init__(self, memory: Memory | None = None, session_id: str | None = None):
    self.memory = memory or Memory()  # ← NEW instance per session
```

**Memory Flow**:
```
Session N:
  AgentContext(session_id="n") → Memory() → store("pattern_1") → [in-memory dict]
  del AgentContext → Memory garbage collected → ❌ Data lost

Session N+1:
  AgentContext(session_id="n1") → Memory() → search("pattern_1") → ❌ Not found (0%)
```

### Missing Persistence Layer

**Current Architecture** (Session-Scoped):
```
AgentContext → Memory (ephemeral, session-scoped)
```

**Required Architecture** (Cross-Session):
```
AgentContext → Memory (session-scoped) + VectorStore (persistent, shared)
              ↓
         VectorStore (FAISS + disk/Firestore backend)
              ↓
         ~/.agency/memories/ (persistent storage)
```

---

## GREEN Phase Roadmap

### Implementation Requirements

**Option 1: Integrate VectorStore into AgentContext** (Recommended)
```python
# shared/agent_context.py
class AgentContext:
    def __init__(self, memory: Memory | None = None, session_id: str | None = None):
        self.memory = memory or Memory()
        # Add persistent VectorStore (shared across sessions)
        self.vector_store = VectorStore(storage_path="~/.agency/memories/")

    def store_memory(self, key: str, content: Any, tags: list[str]) -> None:
        # Store in BOTH session memory AND VectorStore
        self.memory.store(key, content, tags + [f"session:{self.session_id}"])
        self.vector_store.store(key, content, tags, confidence=0.85)  # Persist to disk

    def search_memories(self, tags: list[str], include_session: bool = True) -> list:
        if include_session:
            # Session-scoped search (current behavior)
            return self.memory.search(tags + [f"session:{self.session_id}"])
        else:
            # Cross-session search (NEW - queries VectorStore)
            return self.vector_store.search_by_tags(tags, min_confidence=0.6)
```

**Option 2: VectorStore Persistence Backend**
```python
# agency_memory/vector_store.py
class VectorStore:
    def __init__(self, storage_path: str = "~/.agency/memories/"):
        self._storage_path = Path(storage_path).expanduser()
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Load existing memories from disk
        self._load_from_disk()

    def store(self, key, content, tags, confidence):
        # Store in-memory
        self._memory_records[key] = {...}

        # Persist to disk immediately
        self._save_to_disk()

    def _save_to_disk(self):
        records_file = self._storage_path / "records.json"
        with open(records_file, "w") as f:
            json.dump(self._memory_records, f)

        # Save FAISS index (if enabled)
        if self.vector_index:
            self.vector_index.save_index()

    def _load_from_disk(self):
        records_file = self._storage_path / "records.json"
        if records_file.exists():
            with open(records_file, "r") as f:
                self._memory_records = json.load(f)

        # Load FAISS index (if enabled)
        if self.vector_index:
            self.vector_index.load_index()
```

---

## Acceptance Criteria (GREEN Phase)

**Unit Tests**:
- ✅ `test_vectorstore_persists_to_disk`: Verify `records.json` file exists
- ✅ `test_vectorstore_loads_from_disk`: Session N+1 loads Session N memories
- ✅ `test_faiss_index_persists`: FAISS index file exists and loads
- ✅ `test_session_cleanup_no_memory_leak`: <50MB growth for 100 sessions
- ✅ `test_memory_deduplication_across_sessions`: Duplicate keys handled

**Integration Tests**:
- ✅ `test_session_n_to_n_plus_1_retrieval`: ≥90% retrieval accuracy (9/10 patterns)
- ✅ `test_concurrent_session_writes`: 30/30 patterns persisted (no corruption)
- ✅ `test_process_restart_recovery`: 5/5 patterns survive process restart
- ✅ `test_partial_session_failure_recovery`: 5/5 patterns recovered
- ✅ `test_multi_day_checkpoint_resume`: 2/2 checkpoints retrieved

**E2E Tests**:
- ✅ `test_full_mission_cross_session`: Mission N+1 retrieves ≥1 Mission N pattern
- ✅ `test_agent_swarm_coordination`: 4/4 agent patterns retrieved by Merger
- ✅ `test_100_session_persistence`: ≥90% retrieval (≥450/500 patterns)

**Benchmarks**:
- ✅ `test_90_percent_retrieval_accuracy`: ≥90% accuracy (≥90/100 patterns)
- ✅ `test_retrieval_latency_at_10k_memories`: <100ms latency (median)
- ✅ `test_multi_query_throughput`: ≥1000 queries/second

---

## Test Execution Commands

```bash
# Unit tests (fast, <10s total)
pytest tests/agency_memory/test_cross_session_unit.py -v

# Integration tests (moderate, <30s total)
pytest tests/agency_memory/test_cross_session_integration.py -v -m integration

# E2E tests (slow, <2min total)
pytest tests/e2e/test_cross_session_memory_e2e.py -v -m e2e

# Benchmarks (slow, <5min total)
pytest tests/benchmarks/test_cross_session_benchmark.py -v -m benchmark

# Full suite (all 15 tests)
pytest tests/agency_memory/test_cross_session_*.py tests/e2e/test_cross_session_*.py tests/benchmarks/test_cross_session_*.py -v

# RED phase validation (expect failures)
pytest tests/agency_memory/test_cross_session_integration.py::test_session_n_to_n_plus_1_retrieval -v
```

---

## Constitutional Compliance Impact

### Article IV Violations (Current State)

| Article IV Requirement | Current Status | Test Validation |
|------------------------|----------------|-----------------|
| **Query before action** | ✅ API exists | `test_agent_context_search_memories_api_exists` |
| **Store after success** | ✅ API exists | `test_agent_context_store_memory_api_exists` |
| **Cross-session retrieval** | ❌ **BROKEN** (0%) | `test_session_n_to_n_plus_1_retrieval` |
| **90% retrieval accuracy** | ❌ **BROKEN** (0%) | `test_90_percent_retrieval_accuracy` |
| **Institutional memory** | ❌ **BROKEN** | `test_full_mission_cross_session` |
| **VectorStore integration** | ⚠️ Partial (in-memory only) | `test_vectorstore_persists_to_disk` |

**Severity**: **HIGH** - Article IV is **NOT ENFORCED** without cross-session persistence

### Leap Evolution Impact

| Leap | Dependency on Cross-Session Memory | Status |
|------|-----------------------------------|--------|
| **Leap 1** (Foundation) | Three-tier memory architecture | ⚠️ Tier 2 (VectorStore) not persistent |
| **Leap 3** (Adaptive Router) | Skill vector evolution across sessions | ❌ **BLOCKED** (no cross-session learning) |
| **Leap 4** (Quality Feedback) | Misclassification refinement storage | ❌ **BLOCKED** (feedback lost per session) |
| **Leap 7** (Test-Driven Autonomy) | Pattern application from past tests | ❌ **BLOCKED** (no pattern accumulation) |
| **Leap 8** (Adaptive Routing) | Training data accumulation | ❌ **BLOCKED** (no cross-session training) |

**Strategic Risk**: **CRITICAL** - All learning-based Leaps depend on cross-session memory

---

## Next Steps (GREEN Phase)

### Phase 1: Implement Persistence (Priority 1)
1. Add `storage_path` parameter to `VectorStore.__init__()`
2. Implement `_save_to_disk()` in `VectorStore.store()`
3. Implement `_load_from_disk()` in `VectorStore.__init__()`
4. Integrate persistent VectorStore into `AgentContext`

### Phase 2: Verify Tests (Priority 1)
1. Run integration test: `test_session_n_to_n_plus_1_retrieval`
   - Expected: ≥90% retrieval accuracy (9/10 patterns)
2. Run benchmark: `test_90_percent_retrieval_accuracy`
   - Expected: ≥90% accuracy (90/100 patterns)
3. Run E2E: `test_full_mission_cross_session`
   - Expected: Mission N+1 retrieves Mission N patterns

### Phase 3: Performance Optimization (Priority 2)
1. Add FAISS index persistence (`test_faiss_index_persists`)
2. Optimize retrieval latency (`test_retrieval_latency_at_10k_memories`)
3. Benchmark query throughput (`test_multi_query_throughput`)

### Phase 4: Production Hardening (Priority 3)
1. Add Firestore backend option (optional cloud persistence)
2. Implement checkpoint compression (multi-day tasks)
3. Add memory quota enforcement (prevent disk bloat)

---

## Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **Article IV non-compliance** | HIGH | 100% (current) | Implement persistence (Phase 1) |
| **Data loss on process restart** | HIGH | 100% (current) | Add disk persistence |
| **Swarm coordination failure** | HIGH | 100% (current) | Shared VectorStore |
| **Performance degradation** | MEDIUM | Low | FAISS indexing (Phase 3) |
| **Disk space bloat** | LOW | Medium | Memory quotas (Phase 4) |

---

## Conclusion

**TDD Validation**: ✅ **SUCCESS**
- Tests correctly fail (RED phase) with 0% retrieval accuracy
- Failure demonstrates critical cross-session persistence gap
- Root cause identified: `AgentContext` uses ephemeral `Memory()` instances

**Article IV Compliance**: ❌ **CRITICAL VIOLATION**
- Cross-session learning is **constitutionally required** but **not enforced**
- 0% retrieval accuracy proves institutional memory does not persist
- All learning-based Leaps (3, 4, 7, 8) are **blocked**

**Recommendation**: **IMMEDIATE IMPLEMENTATION** (GREEN phase)
- Priority 1: Integrate persistent VectorStore into AgentContext
- Priority 1: Verify tests pass (≥90% retrieval accuracy)
- Priority 2: Optimize performance (FAISS, <100ms latency)

**Estimated Effort**:
- Phase 1 (Persistence): 4-6 hours
- Phase 2 (Verification): 1-2 hours
- Phase 3 (Optimization): 2-3 hours
- **Total**: 7-11 hours to GREEN phase

---

**Generated by**: TestGeneratorAgent
**Date**: 2025-10-26
**Spec**: `specs/spec-cross-session-memory-validation.md`
**Article IV**: Continuous Learning and Improvement (ADR-004)
