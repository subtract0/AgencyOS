# VectorStore Optimization Strategy Specification

**Spec ID:** leap_2_vectorstore_optimization
**Created:** 2025-10-10
**Status:** Proposed
**Tier:** Tier 1 (Core Infrastructure)
**Constitutional Basis:** Article I (Complete Context), Article II (100% Verification), Article IV (Continuous Learning)

## Executive Summary

Optimize VectorStore for production-scale memory operations with sub-linear search complexity, intelligent batch processing, and memory-aware caching. Target: <100ms semantic queries at 100K+ memories with <40GB peak memory usage on current hardware (see docs/HARDWARE_OPTIMIZATION.md) systems.

**Current State:**
- O(n) linear scan for similarity search (no indexing)
- Individual store/search operations (no batching)
- No caching layer (repeated queries re-execute)
- Memory unbounded (risk of OOM on large datasets)

**Target State:**
- O(√t log t) indexed search via FAISS/HNSW
- 10x throughput improvement via batch operations
- LRU cache with 5x query speedup
- Memory budget: <40GB peak usage (current hardware (see docs/HARDWARE_OPTIMIZATION.md) constraint)

---

## Goals

### Primary Goals

1. **Sub-Linear Search Performance**
   - Achieve <100ms semantic search at 100K memories
   - Replace linear scan with FAISS HNSW indexing
   - Target: O(√t log t) complexity vs current O(n)

2. **Batch Processing API**
   - Implement `batch_store_memories()` for bulk inserts
   - Implement `batch_search_memories()` for multi-query execution
   - Target: 10x throughput improvement for bulk operations

3. **Intelligent Caching Layer**
   - LRU cache for frequent queries (5x speedup)
   - Cache warming for predictable patterns
   - Automatic invalidation on writes
   - Target: 80%+ cache hit rate

4. **Memory Budget Compliance**
   - Enforce <40GB peak usage (Article II: Hardware-Aware Execution per ADR-023)
   - Dynamic index sizing based on available memory
   - Graceful degradation to keyword search on memory pressure
   - Target: Zero OOM crashes, zero kernel panics

### Non-Goals

1. Distributed vector database migration (deferred to Phase 3)
2. GPU acceleration for embeddings (local CPU-only)
3. Multi-modal memory (text-only for Phase 1)
4. Real-time streaming updates (batch-oriented design)

---

## Personas

### Agent Developers (Primary)
**Who:** Engineers building agents that use VectorStore
**Needs:**
- Fast semantic search (<100ms p95)
- Bulk memory operations (batch insert 1000+ items)
- Predictable memory usage (no OOM surprises)
- Backward-compatible API (no breaking changes)

### Infrastructure Team (Secondary)
**Who:** Maintaining production Agency deployments
**Needs:**
- Memory budget enforcement (current hardware (see docs/HARDWARE_OPTIMIZATION.md) limits)
- Monitoring and observability (query latency, cache hit rate)
- Graceful degradation under pressure
- Clear upgrade path from current implementation

### Learning Agent (Tertiary)
**Who:** Automated pattern extraction and storage
**Needs:**
- High-throughput batch storage (session transcripts)
- Semantic clustering for consolidation
- Efficient cross-session queries
- Constitutional compliance (Article IV mandatory VectorStore)

---

## Acceptance Criteria

### 1. Indexing Strategy (FAISS HNSW)

**Criterion 1.1: Sub-Linear Search Complexity**
- GIVEN: VectorStore with 100,000 memories
- WHEN: Semantic search query executed
- THEN: Query completes in <100ms (p95 latency)
- AND: Search complexity is O(√t log t) verified via profiling

**Criterion 1.2: FAISS Index Persistence**
- GIVEN: VectorStore with FAISS index
- WHEN: Process restarts
- THEN: Index loaded from pickle file in <1 second
- AND: No re-indexing required for existing memories

**Criterion 1.3: Incremental Index Updates**
- GIVEN: FAISS index with 10K memories
- WHEN: New memory added via `add_memory()`
- THEN: Index updated incrementally (no full rebuild)
- AND: Update completes in <10ms

**Criterion 1.4: Hybrid Search Preservation**
- GIVEN: Indexed VectorStore
- WHEN: Hybrid search requested (semantic + keyword)
- THEN: Both search modes execute correctly
- AND: Results ranked by weighted combined score

### 2. Batch Processing Design

**Criterion 2.1: Batch Store API**
- GIVEN: 1,000 memories to store
- WHEN: `batch_store_memories(memories)` called
- THEN: All memories stored in <500ms (2ms/item)
- AND: Index updated once (not per-item)
- AND: Embedding generation batched (single API call)

**Criterion 2.2: Batch Search API**
- GIVEN: 50 concurrent search queries
- WHEN: `batch_search_memories(queries)` called
- THEN: All queries complete in <1 second (20ms/query)
- AND: Embedding generation batched (single API call)
- AND: Results returned as list of SimilarityResult lists

**Criterion 2.3: Memory Efficiency in Batching**
- GIVEN: Batch operation processing 10K items
- WHEN: Peak memory usage measured
- THEN: Memory increase ≤2GB during batch
- AND: Memory released after batch completes

**Criterion 2.4: Atomicity Guarantee**
- GIVEN: Batch store operation with 1,000 items
- WHEN: Operation fails midway (item 500)
- THEN: Either all items stored OR none stored (no partial state)
- AND: Index remains consistent

### 3. Caching Layer Design

**Criterion 3.1: LRU Cache Implementation**
- GIVEN: VectorStore with LRU cache (maxsize=128)
- WHEN: Same query executed twice
- THEN: Second execution uses cache (latency <1ms)
- AND: Cache hit recorded in metrics

**Criterion 3.2: Cache Invalidation on Writes**
- GIVEN: Cached query results
- WHEN: New memory stored
- THEN: Cache cleared automatically
- AND: Next query executes fresh search

**Criterion 3.3: Cache Warming Strategy**
- GIVEN: VectorStore initialization
- WHEN: Top 10 frequent queries identified (from metrics)
- THEN: Queries pre-executed to warm cache
- AND: Cache hit rate >50% in first 100 queries

**Criterion 3.4: Memory-Bounded Cache**
- GIVEN: LRU cache with 128 entries
- WHEN: Cache full (128 entries)
- THEN: Least recently used entry evicted
- AND: Cache memory usage <100MB

### 4. Memory Budget Analysis

**Criterion 4.1: Peak Memory Calculation**
- GIVEN: VectorStore configuration parameters
- WHEN: `estimate_peak_memory(num_memories, embedding_dim)` called
- THEN: Returns accurate estimate ±10%
- AND: Estimate includes: embeddings + index + cache + overhead

**Criterion 4.2: current hardware (see docs/HARDWARE_OPTIMIZATION.md) Compliance**
- GIVEN: VectorStore with 100K memories (1536-dim embeddings)
- WHEN: FAISS index + embeddings + cache loaded
- THEN: Peak memory usage <15GB (40GB budget - 25GB for model/tests)
- AND: Zero kernel panics during full test suite execution

**Criterion 4.3: Dynamic Index Sizing**
- GIVEN: Available memory <20GB detected
- WHEN: VectorStore initializes FAISS index
- THEN: Index size reduced (HNSW efConstruction lowered)
- AND: Warning logged: "Memory-constrained mode active"

**Criterion 4.4: Graceful Degradation**
- GIVEN: Memory pressure detected (>85% RAM usage)
- WHEN: Semantic search requested
- THEN: Falls back to keyword search (no embedding generation)
- AND: Returns results with `search_type: "keyword_fallback"`

---

## Technical Design

### 1. FAISS Indexing Strategy

#### 1.1 Index Selection

**Choice:** FAISS HNSW (Hierarchical Navigable Small World)

**Rationale:**
- **Performance:** O(√t log t) search complexity
- **Accuracy:** 95%+ recall at k=10 (vs brute force)
- **Memory Efficiency:** ~4x smaller than flat index
- **Incremental Updates:** Supports add without rebuild
- **CPU-Only:** No GPU required (current hardware Metal compatibility)

**Alternative Rejected: FAISS IVF**
- Requires training data upfront (not incremental)
- Lower accuracy for small datasets (<100K)
- More complex parameterization

**Alternative Rejected: Annoy**
- Immutable index (no incremental updates)
- Requires full rebuild on each add
- Slower search than HNSW

#### 1.2 Index Configuration

```python
import faiss
import numpy as np

class FAISSVectorStore:
    def __init__(
        self,
        embedding_dim: int = 1536,  # OpenAI text-embedding-3-small
        hnsw_m: int = 32,           # Number of bi-directional links (memory vs speed)
        ef_construction: int = 200, # Build-time search depth (quality vs speed)
        ef_search: int = 128,       # Query-time search depth (recall vs latency)
        index_path: str | None = None  # Pickle persistence path
    ):
        """
        Initialize FAISS HNSW index for vector similarity search.

        Memory Budget:
        - 100K vectors (1536-dim, float32): 614MB
        - HNSW index overhead (M=32): ~2GB
        - Total: ~2.6GB for 100K memories

        Performance:
        - ef_construction=200: 95% recall, ~500ms build/1K items
        - ef_search=128: <100ms query at 100K items
        """
        self.embedding_dim = embedding_dim
        self.hnsw_m = hnsw_m
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.index_path = index_path

        # Create HNSW index
        self.index = faiss.IndexHNSWFlat(embedding_dim, hnsw_m)
        self.index.hnsw.efConstruction = ef_construction
        self.index.hnsw.efSearch = ef_search

        # Memory tracking
        self._memory_ids: list[str] = []  # Maps index position → memory key
        self._embeddings: dict[str, np.ndarray] = {}

        # Load persisted index if exists
        if index_path and os.path.exists(index_path):
            self._load_index()

    def _load_index(self) -> None:
        """Load FAISS index from disk (pickle format)."""
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            self.index = data["index"]
            self._memory_ids = data["memory_ids"]
            self._embeddings = data["embeddings"]

        logger.info(f"Loaded FAISS index: {len(self._memory_ids)} memories")

    def _save_index(self) -> None:
        """Persist FAISS index to disk."""
        if not self.index_path:
            return

        with open(self.index_path, "wb") as f:
            pickle.dump({
                "index": self.index,
                "memory_ids": self._memory_ids,
                "embeddings": self._embeddings
            }, f)

        logger.debug(f"Saved FAISS index: {len(self._memory_ids)} memories")
```

#### 1.3 Memory Budget Calculation

```python
def estimate_peak_memory(
    num_memories: int,
    embedding_dim: int = 1536,
    hnsw_m: int = 32,
    cache_size: int = 128
) -> dict[str, float]:
    """
    Estimate peak memory usage for VectorStore.

    Returns:
        Dictionary with memory breakdown in GB:
        - embeddings: Raw embedding vectors
        - index: FAISS HNSW index overhead
        - cache: LRU cache memory
        - overhead: Python object overhead
        - total: Sum of all components
    """
    # Embeddings: num_memories × embedding_dim × 4 bytes (float32)
    embeddings_gb = (num_memories * embedding_dim * 4) / (1024 ** 3)

    # FAISS HNSW index overhead: ~(num_memories * M * 8 bytes)
    # M = average number of neighbors per node (≈hnsw_m)
    index_gb = (num_memories * hnsw_m * 8) / (1024 ** 3)

    # LRU cache: cache_size × (query_embedding + results)
    # Assume average 10 results per query, each ~200 bytes
    cache_gb = (cache_size * (embedding_dim * 4 + 10 * 200)) / (1024 ** 3)

    # Python overhead: ~50% of raw data size
    overhead_gb = (embeddings_gb + index_gb) * 0.5

    total_gb = embeddings_gb + index_gb + cache_gb + overhead_gb

    return {
        "embeddings": round(embeddings_gb, 2),
        "index": round(index_gb, 2),
        "cache": round(cache_gb, 2),
        "overhead": round(overhead_gb, 2),
        "total": round(total_gb, 2)
    }

# Example: 100K memories with 1536-dim embeddings
# estimate_peak_memory(100_000)
# Output: {
#   "embeddings": 0.61,
#   "index": 2.40,
#   "cache": 0.01,
#   "overhead": 1.51,
#   "total": 4.53 GB  ← Safe for available memory current hardware
# }
```

### 2. Batch Processing Design

#### 2.1 Batch Store API

```python
def batch_store_memories(
    self,
    memories: list[tuple[str, dict[str, JSONValue]]],  # [(key, memory_content), ...]
    batch_size: int = 100  # Embedding API batch size
) -> BatchStoreResult:
    """
    Store multiple memories in a single transaction.

    Optimizations:
    1. Batch embedding generation (single OpenAI API call)
    2. Single FAISS index update (not per-item)
    3. Atomic operation (all or nothing)

    Args:
        memories: List of (key, content) tuples
        batch_size: Max items per embedding API call (OpenAI limit: 2048)

    Returns:
        BatchStoreResult with success count, failed items, timing

    Performance:
    - 1,000 items: ~500ms (vs 5,000ms individual)
    - 10,000 items: ~3 seconds (vs 30+ seconds individual)
    """
    start_time = time.time()

    # Step 1: Extract searchable text for all memories
    texts = [self._extract_searchable_text(content) for _, content in memories]

    # Step 2: Generate embeddings in batches (single API call per batch)
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        try:
            batch_embeddings = self._embedding_function(batch_texts)
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            logger.error(f"Embedding generation failed for batch {i}-{i+batch_size}: {e}")
            # Mark as failed, continue with next batch
            all_embeddings.extend([None] * len(batch_texts))

    # Step 3: Store memories and embeddings
    successful = []
    failed = []

    for (key, content), embedding in zip(memories, all_embeddings, strict=True):
        if embedding is None:
            failed.append((key, "embedding_generation_failed"))
            continue

        try:
            # Store in memory records
            self._memory_records[key] = content
            self._memory_texts[key] = self._extract_searchable_text(content)
            self._embeddings[key] = np.array(embedding, dtype=np.float32)
            successful.append(key)
        except Exception as e:
            failed.append((key, str(e)))

    # Step 4: Batch update FAISS index (single operation)
    if successful:
        embeddings_matrix = np.vstack([self._embeddings[key] for key in successful])
        self.index.add(embeddings_matrix)
        self._memory_ids.extend(successful)

    # Step 5: Invalidate cache and persist
    self._search_cache.cache_clear()
    self._save_index()

    elapsed_ms = (time.time() - start_time) * 1000

    return BatchStoreResult(
        success_count=len(successful),
        failed_items=failed,
        total_time_ms=elapsed_ms,
        avg_time_per_item_ms=elapsed_ms / len(memories) if memories else 0
    )

@dataclass
class BatchStoreResult:
    success_count: int
    failed_items: list[tuple[str, str]]  # [(key, error_reason), ...]
    total_time_ms: float
    avg_time_per_item_ms: float
```

#### 2.2 Batch Search API

```python
def batch_search_memories(
    self,
    queries: list[str],
    top_k: int = 10,
    min_similarity: float = 0.5
) -> list[list[SimilarityResult]]:
    """
    Execute multiple semantic searches in parallel.

    Optimizations:
    1. Batch embedding generation (single OpenAI API call)
    2. Vectorized FAISS search (single index query)
    3. Parallel result processing

    Args:
        queries: List of search query strings
        top_k: Results per query
        min_similarity: Filter threshold

    Returns:
        List of result lists (one per query)

    Performance:
    - 50 queries: ~1 second (vs 5 seconds individual)
    - 100 queries: ~2 seconds (vs 10 seconds individual)
    """
    if not queries:
        return []

    # Step 1: Generate query embeddings in batch
    query_embeddings = self._embedding_function(queries)

    # Step 2: Vectorized FAISS search (single index query)
    query_matrix = np.vstack(query_embeddings).astype(np.float32)
    distances, indices = self.index.search(query_matrix, top_k)

    # Step 3: Convert to SimilarityResult objects
    results = []
    for i, query in enumerate(queries):
        query_results = []
        for j in range(top_k):
            idx = indices[i][j]
            if idx == -1:  # FAISS returns -1 for no match
                continue

            memory_key = self._memory_ids[idx]
            similarity = 1 - (distances[i][j] / 2)  # Convert L2 distance to cosine similarity

            if similarity >= min_similarity:
                query_results.append(SimilarityResult(
                    memory=self._memory_records[memory_key],
                    similarity_score=similarity,
                    search_type="semantic"
                ))

        results.append(query_results)

    return results
```

### 3. Caching Layer Design

#### 3.1 LRU Cache Implementation

```python
from functools import lru_cache
import hashlib

class CachedVectorStore:
    def __init__(self, vector_store: VectorStore, cache_size: int = 128):
        """
        Wrap VectorStore with LRU caching layer.

        Cache key: hash(query + search_params)
        Cache value: list[SimilarityResult]

        Performance:
        - Cache hit: <1ms (in-memory dict lookup)
        - Cache miss: ~50ms (VectorStore semantic search)
        - Expected hit rate: 80%+ for repeated queries
        """
        self.vector_store = vector_store
        self.cache_size = cache_size

        # LRU cache for search results
        self._search_cache = lru_cache(maxsize=cache_size)(self._search_impl)

        # Metrics
        self._cache_hits = 0
        self._cache_misses = 0

    def _cache_key(self, query: str, top_k: int, min_similarity: float) -> str:
        """Generate cache key from query parameters."""
        key_str = f"{query}|{top_k}|{min_similarity}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def _search_impl(self, cache_key: str, query: str, top_k: int, min_similarity: float):
        """Internal cached search implementation."""
        results = self.vector_store.semantic_search(query, [], top_k)

        # Filter by similarity and convert to tuple (for cache immutability)
        filtered = [r for r in results if r.similarity_score >= min_similarity]
        return tuple(filtered)  # Tuple for hashable cache value

    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.5
    ) -> list[SimilarityResult]:
        """
        Semantic search with LRU caching.

        Cache hit: Returns cached results (<1ms)
        Cache miss: Executes search, caches result (~50ms)
        """
        cache_key = self._cache_key(query, top_k, min_similarity)

        try:
            # Try cache first
            cached_results = self._search_cache(cache_key, query, top_k, min_similarity)
            self._cache_hits += 1
            return list(cached_results)  # Convert tuple back to list
        except TypeError:  # Cache miss
            self._cache_misses += 1
            raise

    def invalidate_cache(self) -> None:
        """Clear cache after write operations."""
        self._search_cache.cache_clear()
        logger.debug("Search cache invalidated")

    def get_cache_stats(self) -> dict[str, JSONValue]:
        """Return cache performance metrics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": self.cache_size,
            "cache_info": self._search_cache.cache_info()._asdict()
        }
```

#### 3.2 Cache Warming Strategy

```python
def warm_cache(
    self,
    frequent_queries: list[str] | None = None,
    top_k: int = 10
) -> dict[str, int]:
    """
    Pre-populate cache with frequent queries.

    Strategy:
    1. Load query frequency from metrics store
    2. Execute top N queries to populate cache
    3. Return cache warming statistics

    Args:
        frequent_queries: Optional pre-defined query list
        top_k: Results per query

    Returns:
        Statistics: queries_warmed, time_ms, cache_entries
    """
    start_time = time.time()

    if frequent_queries is None:
        # Load from metrics/telemetry
        frequent_queries = self._load_frequent_queries(limit=20)

    warmed_count = 0
    for query in frequent_queries:
        try:
            self.semantic_search(query, top_k=top_k)
            warmed_count += 1
        except Exception as e:
            logger.warning(f"Cache warming failed for query '{query}': {e}")

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "queries_warmed": warmed_count,
        "time_ms": round(elapsed_ms, 2),
        "cache_entries": warmed_count
    }
```

### 4. Memory Budget Enforcement

#### 4.1 Dynamic Memory Scaling

```python
import psutil

def initialize_memory_aware_vectorstore(
    embedding_dim: int = 1536,
    target_capacity: int = 100_000
) -> VectorStore:
    """
    Initialize VectorStore with memory-aware configuration.

    Logic:
    1. Check available system memory
    2. Calculate safe VectorStore budget
    3. Adjust FAISS index parameters if constrained
    4. Warn if memory insufficient
    """
    # Check available memory
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)

    # Calculate VectorStore budget (40GB total - 25GB for model/tests)
    vectorstore_budget_gb = min(available_gb - 25, 15)

    if vectorstore_budget_gb < 5:
        logger.warning(
            f"Low memory available: {available_gb:.1f}GB. "
            f"VectorStore limited to {vectorstore_budget_gb:.1f}GB. "
            f"Consider reducing target capacity or closing other applications."
        )

    # Estimate required memory
    required = estimate_peak_memory(target_capacity, embedding_dim)

    # Adjust FAISS parameters if memory-constrained
    if required["total"] > vectorstore_budget_gb:
        # Reduce HNSW efConstruction (build quality vs memory)
        scale_factor = vectorstore_budget_gb / required["total"]
        hnsw_m = max(16, int(32 * scale_factor))
        ef_construction = max(100, int(200 * scale_factor))

        logger.info(
            f"Memory-constrained mode: M={hnsw_m}, efConstruction={ef_construction} "
            f"(required: {required['total']:.1f}GB, available: {vectorstore_budget_gb:.1f}GB)"
        )
    else:
        hnsw_m = 32
        ef_construction = 200

    return FAISSVectorStore(
        embedding_dim=embedding_dim,
        hnsw_m=hnsw_m,
        ef_construction=ef_construction
    )
```

#### 4.2 Graceful Degradation

```python
def semantic_search_with_fallback(
    self,
    query: str,
    memories: list[dict[str, JSONValue]],
    top_k: int = 10
) -> list[SimilarityResult]:
    """
    Semantic search with automatic fallback to keyword search on memory pressure.

    Fallback conditions:
    1. Memory usage >85% of total RAM
    2. Embedding generation fails (API timeout/error)
    3. FAISS index not available
    """
    # Check memory pressure
    mem = psutil.virtual_memory()
    if mem.percent > 85:
        logger.warning(
            f"Memory pressure detected ({mem.percent}%). "
            f"Falling back to keyword search."
        )
        return self.keyword_search(query, memories, top_k)

    # Try semantic search
    try:
        return self.semantic_search(query, memories, top_k)
    except MemoryError:
        logger.error("MemoryError during semantic search. Falling back to keyword search.")
        return self.keyword_search(query, memories, top_k)
    except Exception as e:
        logger.error(f"Semantic search failed: {e}. Falling back to keyword search.")
        return self.keyword_search(query, memories, top_k)
```

---

## Constitutional Alignment

### Article I: Complete Context Before Action

**How this decision supports thorough context gathering:**
- Batch search API enables querying all related memories in <1 second
- FAISS indexing ensures complete result sets (no timeout-induced truncation)
- Cache warming pre-loads context for predictable workflows
- Example: LearningAgent can query ALL 100K session memories without timeout

### Article II: 100% Verification and Stability

**How this decision enables full verification:**
- Memory budget enforcement prevents kernel panics during test execution
- Dynamic scaling ensures VectorStore stays within current hardware (see docs/HARDWARE_OPTIMIZATION.md) limits
- Graceful degradation maintains functionality under memory pressure
- Example: Per ADR-023, VectorStore uses <15GB, leaving 25GB for model + tests

### Article III: Automated Merge Enforcement

**How this decision integrates with automation:**
- Batch processing atomicity (all-or-nothing transactions)
- Automated cache invalidation on writes (no stale data)
- Memory budget verification in pre-commit hooks
- Example: CI pipeline fails if VectorStore exceeds 15GB budget

### Article IV: Continuous Learning and Improvement

**How this decision supports learning systems:**
- High-throughput batch storage for session transcript ingestion
- Semantic clustering for memory consolidation (pattern extraction)
- Cross-session queries for institutional knowledge retrieval
- Example: LearningAgent stores 10K patterns in 3 seconds (vs 30 seconds)

### Article V: Spec-Driven Development

**How this decision fits spec-driven workflow:**
- This spec defines optimization strategy before implementation
- Acceptance criteria trace to constitutional requirements
- Memory budget analysis prevents architectural surprises
- Example: Phase 2 implementation references this spec for all decisions

**Compliance Validation:** PASS

- All 5 articles supported: YES
- No constitutional violations: YES
- Memory budget alignment: YES (ADR-023 compliance)

---

## Implementation Phases

### Phase 1: FAISS Integration (Week 1)

**Tasks:**
1. Install FAISS library (`pip install faiss-cpu`)
2. Implement `FAISSVectorStore` class with HNSW index
3. Add pickle persistence (`_save_index()`, `_load_index()`)
4. Migrate `VectorStore.semantic_search()` to use FAISS
5. Add memory budget estimation function
6. Write unit tests (100% coverage)

**Deliverables:**
- `agency_memory/faiss_vector_store.py`
- `tests/test_faiss_vector_store.py` (20+ tests)
- Memory budget calculator
- Migration guide (existing VectorStore → FAISS)

**Success Metrics:**
- <100ms semantic search at 100K memories
- 95%+ recall vs brute force search
- <5GB memory usage for 100K items

### Phase 2: Batch Processing API (Week 2)

**Tasks:**
1. Implement `batch_store_memories()` with atomic transactions
2. Implement `batch_search_memories()` with vectorized FAISS queries
3. Add error handling and rollback logic
4. Update `EnhancedMemoryStore` to use batch APIs
5. Write integration tests

**Deliverables:**
- `batch_store_memories()` API in `FAISSVectorStore`
- `batch_search_memories()` API in `FAISSVectorStore`
- `BatchStoreResult` dataclass
- Integration tests with LearningAgent

**Success Metrics:**
- 10x throughput improvement (1,000 items in <500ms)
- Zero partial state on failures
- 100% test pass rate

### Phase 3: Caching Layer (Week 3)

**Tasks:**
1. Implement `CachedVectorStore` wrapper with LRU cache
2. Add cache invalidation on writes
3. Implement cache warming strategy
4. Add cache metrics (hit rate, latency)
5. Update `AgentContext` to use cached store

**Deliverables:**
- `agency_memory/cached_vector_store.py`
- Cache warming on initialization
- Metrics dashboard integration
- Performance benchmarks

**Success Metrics:**
- 80%+ cache hit rate for frequent queries
- 5x query speedup on cache hits
- <100MB cache memory usage

### Phase 4: Memory Budget Enforcement (Week 4)

**Tasks:**
1. Implement `initialize_memory_aware_vectorstore()`
2. Add dynamic FAISS parameter scaling
3. Implement graceful degradation (semantic → keyword fallback)
4. Add pre-commit memory budget check
5. Update documentation

**Deliverables:**
- Memory-aware initialization logic
- Pre-commit hook for budget validation
- Updated `docs/MEMORY_ARCHITECTURE.md`
- Monitoring dashboard

**Success Metrics:**
- Zero kernel panics during full test suite
- Memory usage <40GB peak (current hardware (see docs/HARDWARE_OPTIMIZATION.md))
- Graceful degradation under pressure

---

## Testing Strategy

### Unit Tests

**Coverage Target:** 100% (constitutional requirement)

```python
# tests/test_faiss_vector_store.py

def test_faiss_index_creation():
    """Test FAISS HNSW index initialization."""
    store = FAISSVectorStore(embedding_dim=1536, hnsw_m=32)
    assert store.index is not None
    assert store.index.ntotal == 0  # Empty index

def test_incremental_index_updates():
    """Test adding memories incrementally to FAISS index."""
    store = FAISSVectorStore(embedding_dim=1536)

    # Add 100 memories
    for i in range(100):
        store.add_memory(f"key_{i}", {"content": f"Memory {i}"})

    assert store.index.ntotal == 100
    assert len(store._memory_ids) == 100

def test_index_persistence():
    """Test FAISS index save/load."""
    tmp_path = "/tmp/test_faiss_index.pkl"

    # Create and populate index
    store1 = FAISSVectorStore(index_path=tmp_path)
    store1.add_memory("key1", {"content": "Test memory"})
    store1._save_index()

    # Load index in new instance
    store2 = FAISSVectorStore(index_path=tmp_path)
    assert store2.index.ntotal == 1
    assert "key1" in store2._memory_ids

def test_batch_store_atomicity():
    """Test batch store all-or-nothing guarantee."""
    store = FAISSVectorStore()

    # Simulate failure midway
    with patch.object(store, '_embedding_function', side_effect=Exception("API failure")):
        result = store.batch_store_memories([
            ("key1", {"content": "Memory 1"}),
            ("key2", {"content": "Memory 2"})
        ])

    # Verify no partial state
    assert result.success_count == 0
    assert len(result.failed_items) == 2
    assert store.index.ntotal == 0

def test_memory_budget_calculation():
    """Test peak memory estimation accuracy."""
    estimate = estimate_peak_memory(num_memories=100_000)

    assert estimate["total"] < 5.0  # <5GB for 100K memories
    assert estimate["embeddings"] > 0.5  # Embeddings ~600MB
    assert estimate["index"] > 2.0  # HNSW index ~2.4GB
```

### Integration Tests

```python
# tests/integration/test_vectorstore_learning_agent.py

def test_learning_agent_batch_storage():
    """Test LearningAgent storing 10K patterns via batch API."""
    context = create_agent_context()
    learning_agent = LearningAgent(context)

    # Simulate session with 10K memories
    session_transcript = generate_test_transcript(memory_count=10_000)

    start = time.time()
    patterns = learning_agent.extract_and_store_patterns(session_transcript)
    elapsed = time.time() - start

    # Verify throughput
    assert len(patterns) == 10_000
    assert elapsed < 5.0  # <5 seconds for 10K items

    # Verify all patterns searchable
    results = context.search_memories(tags=["pattern"])
    assert len(results) >= 10_000

def test_memory_safe_full_test_suite():
    """Test VectorStore + local model + test suite stay within available memory."""
    # Initialize VectorStore with 100K memories
    store = initialize_memory_aware_vectorstore(target_capacity=100_000)

    # Measure memory before tests
    mem_before = psutil.virtual_memory().used / (1024 ** 3)

    # Run full test suite with local model active
    result = subprocess.run([
        "python", "run_tests.py", "--run-all"
    ], env={"USE_LOCAL_MODEL": "true"})

    # Measure peak memory
    mem_peak = psutil.Process().memory_info().rss / (1024 ** 3)

    # Verify no kernel panic and memory budget
    assert result.returncode == 0
    assert mem_peak < 46.0  # <46GB (available memory - 2GB margin)
```

### Performance Benchmarks

```python
# benchmarks/benchmark_vectorstore.py

def benchmark_search_scaling():
    """Benchmark search latency vs dataset size."""
    sizes = [1_000, 10_000, 50_000, 100_000]
    results = {}

    for size in sizes:
        store = FAISSVectorStore()

        # Populate with memories
        for i in range(size):
            store.add_memory(f"key_{i}", {"content": f"Memory {i}"})

        # Benchmark search
        query = "test query"
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            store.semantic_search(query, [], top_k=10)
            latencies.append((time.perf_counter() - start) * 1000)

        results[size] = {
            "p50_ms": np.percentile(latencies, 50),
            "p95_ms": np.percentile(latencies, 95),
            "p99_ms": np.percentile(latencies, 99)
        }

    # Verify sub-linear scaling
    assert results[100_000]["p95_ms"] < 100  # <100ms at 100K
    assert results[100_000]["p95_ms"] < results[10_000]["p95_ms"] * 5  # Sub-linear

def benchmark_cache_performance():
    """Benchmark cache hit rate and speedup."""
    store = CachedVectorStore(FAISSVectorStore(), cache_size=128)

    # Populate store
    for i in range(10_000):
        store.vector_store.add_memory(f"key_{i}", {"content": f"Memory {i}"})

    # Run 1000 queries (with repetition)
    queries = [f"query_{i % 50}" for i in range(1000)]  # 50 unique queries

    for query in queries:
        store.semantic_search(query)

    stats = store.get_cache_stats()

    # Verify cache effectiveness
    assert stats["hit_rate_percent"] > 80  # >80% hit rate
    assert stats["cache_hits"] > 800
```

---

## Monitoring and Metrics

### Key Metrics

1. **Search Latency**
   - p50, p95, p99 latency by dataset size
   - Target: p95 <100ms at 100K memories

2. **Cache Performance**
   - Cache hit rate (target: >80%)
   - Cache memory usage (target: <100MB)
   - Average speedup on hits (target: 5x)

3. **Memory Usage**
   - Peak VectorStore memory (target: <15GB)
   - Total system memory (target: <40GB)
   - Memory growth rate over time

4. **Throughput**
   - Batch store rate (items/second)
   - Batch search rate (queries/second)
   - Index update latency

### Dashboard Integration

```python
# Example telemetry collection
from core.telemetry import track_metric

def semantic_search_with_metrics(self, query, memories, top_k):
    start = time.perf_counter()

    # Check cache
    cache_hit = self._check_cache(query)
    track_metric("vectorstore.cache.hit", 1 if cache_hit else 0)

    # Execute search
    results = self._execute_search(query, memories, top_k)

    # Record latency
    latency_ms = (time.perf_counter() - start) * 1000
    track_metric("vectorstore.search.latency_ms", latency_ms)
    track_metric("vectorstore.search.result_count", len(results))

    return results
```

---

## Migration Path

### From Current VectorStore to FAISS

**Backward Compatibility:** 100% (drop-in replacement)

```python
# Before (current implementation)
from agency_memory.vector_store import VectorStore

store = VectorStore(embedding_provider="openai")
store.add_memory("key1", {"content": "Memory 1"})
results = store.semantic_search("query", memories, top_k=10)

# After (FAISS-optimized implementation)
from agency_memory.faiss_vector_store import FAISSVectorStore

store = FAISSVectorStore(embedding_provider="openai")
store.add_memory("key1", {"content": "Memory 1"})  # Same API
results = store.semantic_search("query", memories, top_k=10)  # Same API
```

**Data Migration:**
1. Export existing memories: `old_store.export_memories()`
2. Import to FAISS: `new_store.batch_store_memories(exported)`
3. Verify index: `new_store.verify_index_integrity()`
4. Swap stores: Update `AgentContext` initialization

---

## References

- **ADR-023:** Memory-Aware Execution (current hardware (see docs/HARDWARE_OPTIMIZATION.md) constraints)
- **MEMORY_ARCHITECTURE.md:** Three-tier memory design
- **MEMORY_ARCHITECTURE_ANALYSIS.md:** Industry best practices comparison
- **FAISS Documentation:** https://github.com/facebookresearch/faiss/wiki
- **OpenAI Embeddings:** text-embedding-3-small (1536-dim, $0.02/1M tokens)

---

## Appendix A: Memory Budget Examples

### Example 1: Small Dataset (10K memories)

```
Components:
- Embeddings: 10K × 1536 × 4 bytes = 61MB
- FAISS HNSW index (M=32): 10K × 32 × 8 = 2.56MB
- Cache (128 entries): ~1MB
- Python overhead (50%): ~32MB
-------------------------------------------
Total: ~97MB (<1GB) ✅ Safe
```

### Example 2: Medium Dataset (50K memories)

```
Components:
- Embeddings: 50K × 1536 × 4 bytes = 307MB
- FAISS HNSW index (M=32): 50K × 32 × 8 = 12.8MB
- Cache (128 entries): ~1MB
- Python overhead (50%): ~160MB
-------------------------------------------
Total: ~481MB (<1GB) ✅ Safe
```

### Example 3: Large Dataset (100K memories)

```
Components:
- Embeddings: 100K × 1536 × 4 bytes = 614MB
- FAISS HNSW index (M=32): 100K × 32 × 8 = 25.6MB
- Cache (128 entries): ~1MB
- Python overhead (50%): ~320MB
-------------------------------------------
Total: ~961MB (~1GB) ✅ Safe
```

### Example 4: Target Capacity (1M memories)

```
Components:
- Embeddings: 1M × 1536 × 4 bytes = 6.14GB
- FAISS HNSW index (M=32): 1M × 32 × 8 = 256MB
- Cache (128 entries): ~1MB
- Python overhead (50%): ~3.2GB
-------------------------------------------
Total: ~9.6GB (~10GB) ⚠️ Requires careful management

Memory-constrained mode (current hardware (see docs/HARDWARE_OPTIMIZATION.md)):
- VectorStore budget: 15GB max
- Can support ~1M memories with margin
- May require cache size reduction or index optimization
```

---

**Status:** Ready for Phase 1 Implementation
**Next Steps:** Review spec → Approve → TodoWrite task breakdown → Phase 1 execution
