"""Lightweight vector index tests that no longer require FAISS.

These tests install a minimal FAISS stub so the VectorIndex wrapper can run
without heavy native dependencies or long-lived benchmarks. They focus on the
Python-side logic (ID bookkeeping, error handling, and search formatting).
"""

from __future__ import annotations

import importlib
import sys
import types

import numpy as np
import pytest


class _DummyIndex:
    def __init__(self, dim: int, links: int) -> None:  # noqa: D401 - mimic FAISS
        self.ntotal = 0
        self.dim = dim
        self.hnsw = types.SimpleNamespace(efConstruction=0, efSearch=0)

    def add(self, embeddings: np.ndarray) -> None:
        self.ntotal += embeddings.shape[0]
        self._vectors = embeddings  # type: ignore[attr-defined]

    def search(self, query: np.ndarray, k: int):  # noqa: ANN001 - FAISS signature
        if not hasattr(self, "_vectors") or self.ntotal == 0:
            distances = np.full((1, k), 0.0, dtype=np.float32)
            indices = np.full((1, k), -1, dtype=np.int64)
            return distances, indices

        # Simple dot product for deterministic ordering
        scores = self._vectors @ query.T
        ranked = np.argsort(scores[:, 0])[::-1][:k]
        distances = np.zeros((1, len(ranked)), dtype=np.float32)
        indices = ranked.reshape(1, -1).astype(np.int64)
        return distances, indices


@pytest.fixture(autouse=True)
def install_faiss_stub(monkeypatch):
    stub = types.SimpleNamespace(IndexHNSWFlat=_DummyIndex)
    monkeypatch.setitem(sys.modules, "faiss", stub)
    import agency_memory.vector_index as vector_index

    importlib.reload(vector_index)
    yield vector_index


def test_add_and_search_returns_ids(monkeypatch, install_faiss_stub):
    vector_index = install_faiss_stub.VectorIndex(embedding_dim=3)

    ids = ["a", "b", "c"]
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    vector_index.add_vectors(ids, embeddings)

    results = vector_index.search([1.0, 0.0, 0.0], k=2)

    assert results[0][0] == "a"
    assert vector_index.index.ntotal == 3


def test_add_vectors_validates_dimensions(install_faiss_stub):
    vector_index = install_faiss_stub.VectorIndex(embedding_dim=2)

    with pytest.raises(ValueError):
        vector_index.add_vectors(["id"], [[0.0, 1.0, 2.0]])


def test_search_on_empty_index_returns_empty(install_faiss_stub):
    vector_index = install_faiss_stub.VectorIndex(embedding_dim=2)
    assert vector_index.search([0.0, 0.0], k=1) == []
