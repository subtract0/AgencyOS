"""
tests/test_pattern_memory.py
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path

from agency_memory.pattern_memory import PatternMemory, Pattern


@pytest.fixture
def temp_memory():
    """Create PatternMemory with temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield PatternMemory(base_dir=tmpdir)


class TestPatternMemory:
    def test_store_and_query(self, temp_memory):
        """Patterns can be stored and queried."""
        pattern = Pattern(
            id="test_pattern",
            content={"description": "Test pattern"},
            tags=["testing", "unit"],
            confidence=0.9,
        )
        temp_memory.store(pattern)

        results = temp_memory.query(["testing"])
        assert len(results) == 1
        assert results[0].id == "test_pattern"

    def test_persistence(self):
        """Patterns persist across restarts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Store pattern
            memory1 = PatternMemory(base_dir=tmpdir)
            memory1.store(Pattern(
                id="persistent",
                content={"key": "value"},
                tags=["persist"],
                confidence=0.8,
            ))

            # Create new instance (simulates restart)
            memory2 = PatternMemory(base_dir=tmpdir)
            results = memory2.query(["persist"])

            assert len(results) == 1
            assert results[0].id == "persistent"
            assert results[0].content["key"] == "value"

    def test_update_increments_evidence(self, temp_memory):
        """Storing same pattern twice increments evidence."""
        pattern = Pattern(
            id="duplicate",
            content={},
            tags=["test"],
            confidence=0.7,
        )
        temp_memory.store(pattern)
        temp_memory.store(pattern)

        result = temp_memory.get("duplicate")
        assert result.evidence_count == 2
        assert result.confidence > 0.7

    def test_confidence_filter(self, temp_memory):
        """Query respects min_confidence."""
        temp_memory.store(Pattern(id="high", content={}, tags=["a"], confidence=0.9))
        temp_memory.store(Pattern(id="low", content={}, tags=["a"], confidence=0.4))

        results = temp_memory.query(["a"], min_confidence=0.6)
        assert len(results) == 1
        assert results[0].id == "high"

    def test_delete(self, temp_memory):
        """Patterns can be deleted."""
        temp_memory.store(Pattern(id="to_delete", content={}, tags=["x"], confidence=0.8))
        assert temp_memory.count() == 1

        temp_memory.delete("to_delete")
        assert temp_memory.count() == 0
        assert temp_memory.query(["x"]) == []
