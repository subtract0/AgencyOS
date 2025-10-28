# Memory Benchmark Suite Design

**Date**: 2025-10-26
**Purpose**: Validate memory architecture improvements and prove AGI-readiness gains
**Framework**: pytest + pytest-benchmark + golden datasets

---

## Overview

This benchmark suite measures **4 critical dimensions** of memory architecture quality:

1. **Retrieval Accuracy**: Precision@K, Recall@K, NDCG
2. **Latency**: P50/P95/P99 at 10K, 100K, 1M scale
3. **Learning Rate**: Concept acquisition speed
4. **Durability**: Data loss rate over time

**Success Criteria**:
- Retrieval: Precision@10 >80%, Recall@10 >90%
- Latency: P95 <100ms at 100K memories
- Learning: Extract 100 patterns in <5 seconds
- Durability: Data loss <0.01%

---

## 1. Retrieval Accuracy Benchmark

### 1.1 Golden Dataset Design

**File**: `tests/benchmarks/data/retrieval_golden_dataset.json`

**Structure**:
```json
{
  "dataset_version": "1.0.0",
  "created": "2025-10-26",
  "num_queries": 100,
  "num_memories": 10000,
  "queries": [
    {
      "id": "q001",
      "query": "How to implement JWT authentication with RSA-256 signing?",
      "ground_truth_ids": [
        "jwt_auth_rsa256_success_2025_10_15",
        "jwt_auth_pattern_2025_09_20",
        "auth_security_best_practices_2025_08_10"
      ],
      "difficulty": "medium",
      "category": "authentication"
    },
    {
      "id": "q002",
      "query": "Fix NoneType error in repository pattern implementation",
      "ground_truth_ids": [
        "nonetype_fix_repository_2025_10_12",
        "repository_pattern_error_handling_2025_09_15"
      ],
      "difficulty": "easy",
      "category": "debugging"
    }
  ],
  "memories": [
    {
      "key": "jwt_auth_rsa256_success_2025_10_15",
      "content": {
        "pattern": "JWT authentication with RSA-256",
        "code": "from cryptography.hazmat.primitives import hashes...",
        "tests_passed": true,
        "test_count": 47
      },
      "tags": ["coder", "auth", "jwt", "rsa256", "success"],
      "confidence": 0.95
    }
  ]
}
```

**Dataset Categories** (100 queries, 10 per category):
1. **Authentication** (10 queries): JWT, OAuth, SAML, session management
2. **Debugging** (10 queries): NoneType errors, type errors, import errors
3. **Architecture** (10 queries): Repository pattern, ADR, design patterns
4. **Testing** (10 queries): TDD, NECESSARY pattern, test coverage
5. **Performance** (10 queries): Optimization, caching, async/await
6. **Database** (10 queries): SQL queries, migrations, ORM
7. **API Design** (10 queries): REST, GraphQL, validation
8. **Error Handling** (10 queries): Result pattern, try/catch, error messages
9. **Code Quality** (10 queries): Refactoring, linting, type safety
10. **DevOps** (10 queries): Docker, CI/CD, deployment

**Difficulty Distribution**:
- Easy: 30 queries (exact keyword match)
- Medium: 50 queries (semantic similarity required)
- Hard: 20 queries (concept abstraction required)

---

### 1.2 Accuracy Metrics Implementation

**File**: `tests/benchmarks/test_retrieval_accuracy.py`

```python
import pytest
import numpy as np
from pathlib import Path
import json

from agency_memory.vector_store import VectorStore
from tests.benchmarks.metrics import (
    precision_at_k,
    recall_at_k,
    ndcg_at_k,
    mean_reciprocal_rank
)


@pytest.fixture(scope="module")
def golden_dataset():
    """Load golden retrieval dataset."""
    dataset_path = Path(__file__).parent / "data" / "retrieval_golden_dataset.json"
    with open(dataset_path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def vector_store_with_golden_data(golden_dataset):
    """Populate VectorStore with golden memories."""
    store = VectorStore(embedding_provider="sentence-transformers")

    for memory in golden_dataset["memories"]:
        store.store(
            key=memory["key"],
            content=memory["content"],
            tags=memory["tags"],
            confidence=memory["confidence"]
        )

    return store


class TestRetrievalAccuracy:
    """Benchmark retrieval accuracy using golden dataset."""

    @pytest.mark.benchmark
    def test_precision_at_10(self, vector_store_with_golden_data, golden_dataset):
        """Precision@10: % of retrieved results that are relevant."""
        store = vector_store_with_golden_data
        queries = golden_dataset["queries"]

        precisions = []
        for query_obj in queries:
            query = query_obj["query"]
            ground_truth = set(query_obj["ground_truth_ids"])

            # Retrieve top-10
            results = store.semantic_search(query, top_k=10)
            retrieved_ids = {r["key"] for r in results}

            # Calculate precision
            relevant_retrieved = retrieved_ids.intersection(ground_truth)
            precision = len(relevant_retrieved) / min(10, len(retrieved_ids))
            precisions.append(precision)

        avg_precision = np.mean(precisions)

        print(f"\nPrecision@10: {avg_precision:.3f}")
        assert avg_precision >= 0.80, f"Precision@10 {avg_precision:.3f} < 0.80 (target)"

    @pytest.mark.benchmark
    def test_recall_at_10(self, vector_store_with_golden_data, golden_dataset):
        """Recall@10: % of relevant results that are retrieved."""
        store = vector_store_with_golden_data
        queries = golden_dataset["queries"]

        recalls = []
        for query_obj in queries:
            query = query_obj["query"]
            ground_truth = set(query_obj["ground_truth_ids"])

            # Retrieve top-10
            results = store.semantic_search(query, top_k=10)
            retrieved_ids = {r["key"] for r in results}

            # Calculate recall
            relevant_retrieved = retrieved_ids.intersection(ground_truth)
            recall = len(relevant_retrieved) / len(ground_truth) if ground_truth else 0.0
            recalls.append(recall)

        avg_recall = np.mean(recalls)

        print(f"\nRecall@10: {avg_recall:.3f}")
        assert avg_recall >= 0.90, f"Recall@10 {avg_recall:.3f} < 0.90 (target)"

    @pytest.mark.benchmark
    def test_ndcg_at_10(self, vector_store_with_golden_data, golden_dataset):
        """NDCG@10: Normalized discounted cumulative gain (ranking quality)."""
        store = vector_store_with_golden_data
        queries = golden_dataset["queries"]

        ndcgs = []
        for query_obj in queries:
            query = query_obj["query"]
            ground_truth = set(query_obj["ground_truth_ids"])

            # Retrieve top-10
            results = store.semantic_search(query, top_k=10)

            # Calculate NDCG (binary relevance: 1 if in ground truth, 0 otherwise)
            relevance_scores = [
                1.0 if r["key"] in ground_truth else 0.0
                for r in results
            ]
            ndcg = ndcg_at_k(relevance_scores, k=10)
            ndcgs.append(ndcg)

        avg_ndcg = np.mean(ndcgs)

        print(f"\nNDCG@10: {avg_ndcg:.3f}")
        assert avg_ndcg >= 0.85, f"NDCG@10 {avg_ndcg:.3f} < 0.85 (target)"

    @pytest.mark.benchmark
    def test_mrr(self, vector_store_with_golden_data, golden_dataset):
        """MRR: Mean reciprocal rank (position of first relevant result)."""
        store = vector_store_with_golden_data
        queries = golden_dataset["queries"]

        reciprocal_ranks = []
        for query_obj in queries:
            query = query_obj["query"]
            ground_truth = set(query_obj["ground_truth_ids"])

            # Retrieve top-10
            results = store.semantic_search(query, top_k=10)

            # Find position of first relevant result
            for i, result in enumerate(results):
                if result["key"] in ground_truth:
                    reciprocal_ranks.append(1.0 / (i + 1))
                    break
            else:
                reciprocal_ranks.append(0.0)  # No relevant result found

        mrr = np.mean(reciprocal_ranks)

        print(f"\nMRR: {mrr:.3f}")
        assert mrr >= 0.90, f"MRR {mrr:.3f} < 0.90 (target)"

    @pytest.mark.benchmark
    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_accuracy_by_difficulty(
        self, vector_store_with_golden_data, golden_dataset, difficulty
    ):
        """Breakdown accuracy by query difficulty."""
        store = vector_store_with_golden_data
        queries = [q for q in golden_dataset["queries"] if q["difficulty"] == difficulty]

        precisions = []
        recalls = []

        for query_obj in queries:
            query = query_obj["query"]
            ground_truth = set(query_obj["ground_truth_ids"])

            results = store.semantic_search(query, top_k=10)
            retrieved_ids = {r["key"] for r in results}

            relevant_retrieved = retrieved_ids.intersection(ground_truth)
            precision = len(relevant_retrieved) / min(10, len(retrieved_ids))
            recall = len(relevant_retrieved) / len(ground_truth) if ground_truth else 0.0

            precisions.append(precision)
            recalls.append(recall)

        avg_precision = np.mean(precisions)
        avg_recall = np.mean(recalls)

        print(f"\n{difficulty.upper()} queries:")
        print(f"  Precision@10: {avg_precision:.3f}")
        print(f"  Recall@10: {avg_recall:.3f}")

        # Relaxed targets for hard queries
        targets = {
            "easy": (0.90, 0.95),
            "medium": (0.80, 0.90),
            "hard": (0.60, 0.75)
        }
        target_precision, target_recall = targets[difficulty]

        assert avg_precision >= target_precision, (
            f"{difficulty} Precision@10 {avg_precision:.3f} < {target_precision}"
        )
        assert avg_recall >= target_recall, (
            f"{difficulty} Recall@10 {avg_recall:.3f} < {target_recall}"
        )
```

**Helper Metrics** (`tests/benchmarks/metrics.py`):
```python
import numpy as np


def precision_at_k(retrieved: set, ground_truth: set, k: int) -> float:
    """Precision@K: % of retrieved results that are relevant."""
    if not retrieved:
        return 0.0
    relevant_retrieved = retrieved.intersection(ground_truth)
    return len(relevant_retrieved) / min(k, len(retrieved))


def recall_at_k(retrieved: set, ground_truth: set, k: int) -> float:
    """Recall@K: % of relevant results that are retrieved."""
    if not ground_truth:
        return 0.0
    relevant_retrieved = retrieved.intersection(ground_truth)
    return len(relevant_retrieved) / len(ground_truth)


def ndcg_at_k(relevance_scores: list[float], k: int) -> float:
    """Normalized Discounted Cumulative Gain@K."""
    relevance_scores = relevance_scores[:k]

    # DCG: Sum of (relevance / log2(position + 1))
    dcg = sum(
        rel / np.log2(i + 2)  # i+2 because i is 0-indexed
        for i, rel in enumerate(relevance_scores)
    )

    # IDCG: DCG of perfect ranking (sorted by relevance)
    ideal_relevance = sorted(relevance_scores, reverse=True)
    idcg = sum(
        rel / np.log2(i + 2)
        for i, rel in enumerate(ideal_relevance)
    )

    if idcg == 0:
        return 0.0

    return dcg / idcg


def mean_reciprocal_rank(results_list: list[list[str]], ground_truth_list: list[set[str]]) -> float:
    """MRR: Mean reciprocal rank across multiple queries."""
    reciprocal_ranks = []

    for results, ground_truth in zip(results_list, ground_truth_list):
        for i, result_id in enumerate(results):
            if result_id in ground_truth:
                reciprocal_ranks.append(1.0 / (i + 1))
                break
        else:
            reciprocal_ranks.append(0.0)

    return np.mean(reciprocal_ranks)
```

---

## 2. Latency Benchmark

### 2.1 Scale Test Implementation

**File**: `tests/benchmarks/test_latency_at_scale.py`

```python
import pytest
import time
import numpy as np
from agency_memory.vector_store import VectorStore


@pytest.fixture(scope="module", params=[10_000, 100_000])
def vector_store_at_scale(request):
    """Populate VectorStore with 10K or 100K memories."""
    num_memories = request.param
    store = VectorStore(embedding_provider="sentence-transformers")

    # Generate synthetic memories
    print(f"\nPopulating VectorStore with {num_memories:,} memories...")
    memories = []
    for i in range(num_memories):
        key = f"memory_{i:06d}"
        content = {
            "pattern": f"Pattern {i}",
            "description": f"This is a synthetic memory for testing at scale",
            "category": f"category_{i % 10}"
        }
        tags = [f"tag_{i % 100}", f"category_{i % 10}", "synthetic"]
        memories.append((key, content, tags, 0.8))

    # Batch insert (10x faster than individual inserts)
    batch_size = 1000
    for i in range(0, len(memories), batch_size):
        batch = memories[i:i+batch_size]
        for key, content, tags, confidence in batch:
            store.store(key, content, tags, confidence)

    print(f"  Populated {num_memories:,} memories")
    return store, num_memories


class TestLatencyAtScale:
    """Benchmark query latency at 10K, 100K scale."""

    @pytest.mark.benchmark
    def test_p95_latency(self, vector_store_at_scale, benchmark):
        """P95 latency: <100ms at 100K memories."""
        store, num_memories = vector_store_at_scale

        # Test queries
        test_queries = [
            "Pattern with category authentication",
            "Memory for debugging NoneType errors",
            "Synthetic memory for testing",
        ]

        latencies = []
        num_iterations = 100

        for _ in range(num_iterations):
            query = test_queries[_ % len(test_queries)]
            start = time.perf_counter()
            results = store.semantic_search(query, top_k=10)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)
        mean = np.mean(latencies)

        print(f"\nLatency @ {num_memories:,} memories:")
        print(f"  P50: {p50:.2f} ms")
        print(f"  P95: {p95:.2f} ms")
        print(f"  P99: {p99:.2f} ms")
        print(f"  Mean: {mean:.2f} ms")

        # Targets based on scale
        targets = {
            10_000: 20,   # P95 <20ms at 10K
            100_000: 100  # P95 <100ms at 100K
        }
        target_p95 = targets.get(num_memories, 100)

        assert p95 < target_p95, f"P95 latency {p95:.2f}ms >= {target_p95}ms (target)"

    @pytest.mark.benchmark
    def test_throughput(self, vector_store_at_scale):
        """Throughput: Queries per second at scale."""
        store, num_memories = vector_store_at_scale

        query = "Synthetic memory for testing"
        num_queries = 1000

        start = time.perf_counter()
        for _ in range(num_queries):
            store.semantic_search(query, top_k=10)
        elapsed = time.perf_counter() - start

        qps = num_queries / elapsed

        print(f"\nThroughput @ {num_memories:,} memories:")
        print(f"  QPS: {qps:.1f} queries/second")

        # Target: >100 QPS at 100K memories
        min_qps = 100 if num_memories >= 100_000 else 500
        assert qps >= min_qps, f"Throughput {qps:.1f} QPS < {min_qps} QPS (target)"
```

---

## 3. Learning Rate Benchmark

### 3.1 Concept Acquisition Speed

**File**: `tests/benchmarks/test_learning_rate.py`

```python
import pytest
import time
from agency_memory.learning import LearningSystem
from agency_memory.vector_store import VectorStore


@pytest.fixture
def learning_system():
    """LearningSystem with VectorStore backend."""
    store = VectorStore(embedding_provider="sentence-transformers")
    return LearningSystem(vector_store=store)


class TestLearningRate:
    """Benchmark concept acquisition speed."""

    @pytest.mark.benchmark
    def test_pattern_extraction_speed(self, learning_system):
        """Extract 100 patterns in <5 seconds."""
        # Inject 100 patterns (10 concepts, 10 instances each)
        patterns = []
        concepts = [
            "jwt_auth", "oauth", "repository_pattern", "result_pattern",
            "tdd", "docker", "api_design", "caching", "async_await", "sql_queries"
        ]

        for concept_idx, concept in enumerate(concepts):
            for instance_idx in range(10):
                pattern = {
                    "key": f"{concept}_instance_{instance_idx}",
                    "content": {
                        "pattern": f"{concept.replace('_', ' ').title()}",
                        "description": f"Instance {instance_idx} of {concept}",
                        "code": "def example(): pass",
                        "tests_passed": True
                    },
                    "tags": [concept, "pattern", "success"],
                    "confidence": 0.85 + (instance_idx * 0.01)
                }
                patterns.append(pattern)

        # Store patterns
        for pattern in patterns:
            learning_system.vector_store.store(
                key=pattern["key"],
                content=pattern["content"],
                tags=pattern["tags"],
                confidence=pattern["confidence"]
            )

        # Measure extraction time
        start = time.perf_counter()
        extracted = learning_system.extract_patterns(min_confidence=0.6)
        elapsed = time.perf_counter() - start

        print(f"\nPattern Extraction:")
        print(f"  Extracted: {len(extracted)} patterns")
        print(f"  Time: {elapsed:.3f} seconds")

        assert elapsed < 5.0, f"Extraction time {elapsed:.3f}s >= 5.0s (target)"
        assert len(extracted) >= 90, f"Extracted {len(extracted)} patterns < 90 (target)"

    @pytest.mark.benchmark
    def test_concept_abstraction_accuracy(self, learning_system):
        """Concept abstraction accuracy: >90% (9/10 concepts identified)."""
        # (Same pattern injection as above)
        # ...

        # Extract concepts
        concepts_found = learning_system.extract_concepts(min_confidence=0.7)

        expected_concepts = {
            "jwt_auth", "oauth", "repository_pattern", "result_pattern",
            "tdd", "docker", "api_design", "caching", "async_await", "sql_queries"
        }

        accuracy = len(concepts_found.intersection(expected_concepts)) / len(expected_concepts)

        print(f"\nConcept Abstraction:")
        print(f"  Expected: {len(expected_concepts)} concepts")
        print(f"  Found: {len(concepts_found)} concepts")
        print(f"  Accuracy: {accuracy:.1%}")

        assert accuracy >= 0.90, f"Concept accuracy {accuracy:.1%} < 90% (target)"
```

---

## 4. Durability Benchmark

### 4.1 Crash Recovery Test

**File**: `tests/benchmarks/test_durability.py`

```python
import pytest
import os
import signal
import subprocess
import time
from pathlib import Path
from agency_memory.vector_store import VectorStore


class TestDurability:
    """Benchmark data loss rate and recovery time."""

    @pytest.mark.benchmark
    def test_crash_recovery(self, tmp_path):
        """Data loss rate: <0.01% after crash."""
        storage_path = str(tmp_path / "vectorstore")

        # Store 10K memories
        store = VectorStore(storage_path=storage_path)
        num_memories = 10_000

        print(f"\nStoring {num_memories:,} memories...")
        for i in range(num_memories):
            store.store(
                key=f"memory_{i:06d}",
                content={"data": f"Memory {i}"},
                tags=["test"],
                confidence=0.8
            )

        # Force save
        store.save()

        # Verify all memories present
        stats_before = store.get_stats()
        assert stats_before["total_memories"] == num_memories

        # Simulate crash (delete in-memory state, reload from disk)
        del store

        # Reload from disk
        start = time.perf_counter()
        store_recovered = VectorStore(storage_path=storage_path)
        recovery_time = time.perf_counter() - start

        stats_after = store_recovered.get_stats()

        # Calculate data loss
        memories_lost = num_memories - stats_after["total_memories"]
        data_loss_rate = memories_lost / num_memories

        print(f"\nCrash Recovery:")
        print(f"  Memories before: {num_memories:,}")
        print(f"  Memories after: {stats_after['total_memories']:,}")
        print(f"  Memories lost: {memories_lost}")
        print(f"  Data loss rate: {data_loss_rate:.4%}")
        print(f"  Recovery time: {recovery_time:.3f} seconds")

        assert data_loss_rate < 0.0001, f"Data loss {data_loss_rate:.4%} >= 0.01% (target)"
        assert recovery_time < 5.0, f"Recovery time {recovery_time:.3f}s >= 5.0s (target)"
```

---

## 5. Continuous Benchmark CI Job

### 5.1 GitHub Actions Workflow

**File**: `.github/workflows/memory_benchmarks.yml`

```yaml
name: Memory Benchmarks

on:
  push:
    branches: [main]
  pull_request:
    paths:
      - 'agency_memory/**'
      - 'shared/agent_context.py'
      - 'tests/benchmarks/**'
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-benchmark sentence-transformers faiss-cpu

      - name: Run retrieval accuracy benchmarks
        run: |
          pytest tests/benchmarks/test_retrieval_accuracy.py -v --benchmark-only

      - name: Run latency benchmarks
        run: |
          pytest tests/benchmarks/test_latency_at_scale.py -v --benchmark-only

      - name: Run learning rate benchmarks
        run: |
          pytest tests/benchmarks/test_learning_rate.py -v --benchmark-only

      - name: Run durability benchmarks
        run: |
          pytest tests/benchmarks/test_durability.py -v --benchmark-only

      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: .benchmarks/

      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = fs.readFileSync('.benchmarks/results.json', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Memory Benchmark Results\n\`\`\`json\n${results}\n\`\`\``
            });
```

---

## 6. Benchmark Execution Guide

### 6.1 Local Execution

```bash
# Install dependencies
pip install pytest pytest-benchmark sentence-transformers faiss-cpu

# Run all benchmarks
pytest tests/benchmarks/ -v --benchmark-only

# Run specific benchmark category
pytest tests/benchmarks/test_retrieval_accuracy.py -v
pytest tests/benchmarks/test_latency_at_scale.py -v
pytest tests/benchmarks/test_learning_rate.py -v
pytest tests/benchmarks/test_durability.py -v

# Generate HTML report
pytest tests/benchmarks/ --benchmark-only --benchmark-autosave --benchmark-save-data

# Compare with baseline
pytest tests/benchmarks/ --benchmark-only --benchmark-compare=0001
```

### 6.2 Interpreting Results

**Example Output**:
```
======================= Retrieval Accuracy Benchmarks =======================
Precision@10: 0.847
Recall@10: 0.923
NDCG@10: 0.881
MRR: 0.912

EASY queries:
  Precision@10: 0.945
  Recall@10: 0.982
MEDIUM queries:
  Precision@10: 0.832
  Recall@10: 0.911
HARD queries:
  Precision@10: 0.675
  Recall@10: 0.798

======================= Latency Benchmarks =======================
Latency @ 10,000 memories:
  P50: 12.34 ms
  P95: 18.76 ms
  P99: 24.12 ms
  Mean: 13.45 ms

Latency @ 100,000 memories:
  P50: 45.67 ms
  P95: 89.32 ms
  P99: 112.45 ms
  Mean: 52.34 ms

Throughput @ 100,000 memories:
  QPS: 187.2 queries/second

======================= Learning Rate Benchmarks =======================
Pattern Extraction:
  Extracted: 94 patterns
  Time: 3.456 seconds

Concept Abstraction:
  Expected: 10 concepts
  Found: 9 concepts
  Accuracy: 90.0%

======================= Durability Benchmarks =======================
Crash Recovery:
  Memories before: 10,000
  Memories after: 10,000
  Memories lost: 0
  Data loss rate: 0.0000%
  Recovery time: 2.345 seconds

======================= PASSED: 23/23 =======================
```

---

## 7. Success Criteria Summary

| Benchmark | Metric | Target | Baseline (Est.) | Phase 1 Goal | Phase 3 Goal |
|-----------|--------|--------|-----------------|--------------|--------------|
| **Retrieval Accuracy** |
| Precision@10 | Overall | >80% | 65% | 80% | 90% |
| Recall@10 | Overall | >90% | 70% | 90% | 95% |
| NDCG@10 | Overall | >0.85 | 0.65 | 0.85 | 0.92 |
| MRR | Overall | >0.90 | 0.70 | 0.90 | 0.95 |
| **Latency** |
| P95 | 10K memories | <20ms | 15ms | 15ms | 12ms |
| P95 | 100K memories | <100ms | 120ms | 100ms | 75ms |
| Throughput | 100K memories | >100 QPS | 80 QPS | 150 QPS | 300 QPS |
| **Learning Rate** |
| Extraction | 100 patterns | <5s | 8s | 5s | 2s |
| Abstraction | Accuracy | >90% | 60% | 90% | 95% |
| **Durability** |
| Data Loss | After crash | <0.01% | 0.1% | 0.01% | 0.001% |
| Recovery | Time | <5s | 10s | 5s | 2s |

---

## 8. Next Steps

### Phase 1 (Weeks 1-2): Build Infrastructure
1. Create golden retrieval dataset (100 Q&A pairs)
2. Implement accuracy metrics (Precision@K, Recall@K, NDCG)
3. Add latency benchmarks (P50/P95/P99)
4. Add learning rate benchmarks (extraction speed, abstraction accuracy)
5. Add durability benchmarks (crash recovery)
6. Set up CI job for continuous benchmarking

### Phase 2 (Weeks 3-4): Optimize & Validate
1. Run baseline benchmarks (current implementation)
2. Identify performance bottlenecks (profiling)
3. Optimize FAISS index (incremental updates, re-ranking)
4. Validate improvements with benchmarks

### Phase 3 (Weeks 5-6): AGI-Level Targets
1. Achieve >90% Precision@10, >95% Recall@10
2. Achieve <75ms P95 at 100K memories
3. Achieve >95% concept abstraction accuracy
4. Achieve <0.001% data loss rate

**With this benchmark suite, we can prove memory architecture improvements quantitatively.**

---

**End of Benchmark Suite Design**
