"""
Test suite for Memory API implementation.
Tests in-memory store, tag search, timestamps, and fallback behavior.
"""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

from agency_memory import (
    Memory,
    InMemoryStore,
    FirestoreStore,
    consolidate_learnings,
    create_session_transcript,
    generate_learning_report,
)


class TestInMemoryStore:
    """Test InMemoryStore functionality."""

    def test_store_and_retrieve_basic(self):
        """Test basic store and retrieve functionality."""
        store = InMemoryStore()

        # Store a memory
        store.store("test_key", "test content", ["tag1", "tag2"])

        # Retrieve all memories
        memories = store.get_all()
        assert len(memories.records) == 1

        memory = memories.records[0].to_dict()
        assert memory["key"] == "test_key"
        assert memory["content"] == "test content"
        assert memory["tags"] == ["tag1", "tag2"]
        assert "timestamp" in memory

        # Verify timestamp format
        timestamp = memory["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise exception

    def test_search_by_tags(self):
        """Test searching memories by tags."""
        store = InMemoryStore()

        # Store multiple memories with different tags
        store.store("mem1", "content1", ["work", "urgent"])
        store.store("mem2", "content2", ["personal", "urgent"])
        store.store("mem3", "content3", ["work", "later"])

        # Search for "urgent" tag
        urgent_memories = store.search(["urgent"])
        assert len(urgent_memories.records) == 2
        keys = [m.key for m in urgent_memories.records]
        assert "mem1" in keys
        assert "mem2" in keys

        # Search for "work" tag
        work_memories = store.search(["work"])
        assert len(work_memories.records) == 2
        keys = [m.key for m in work_memories.records]
        assert "mem1" in keys
        assert "mem3" in keys

        # Search for multiple tags (OR operation)
        multi_memories = store.search(["work", "personal"])
        assert len(multi_memories.records) == 3  # All memories match at least one tag

    def test_search_empty_tags(self):
        """Test search with empty tag list."""
        store = InMemoryStore()
        store.store("test", "content", ["tag1"])

        result = store.search([])
        assert len(result.records) == 0

    def test_timestamp_presence(self):
        """Test that all stored memories have timestamps."""
        store = InMemoryStore()

        # Store multiple memories
        for i in range(3):
            store.store(f"key_{i}", f"content_{i}", [f"tag_{i}"])

        memories = store.get_all()
        for memory in memories.records:
            assert memory.timestamp is not None
            # Verify it's a valid datetime object
            assert isinstance(memory.timestamp, datetime)

    def test_memory_ordering(self):
        """Test that memories are returned in chronological order (newest first)."""
        store = InMemoryStore()

        # Store memories with slight delays to ensure different timestamps
        import time

        store.store("first", "content1", ["tag1"])
        time.sleep(0.01)
        store.store("second", "content2", ["tag2"])
        time.sleep(0.01)
        store.store("third", "content3", ["tag3"])

        memories = store.get_all()
        assert len(memories.records) == 3

        # Should be ordered newest first
        assert memories.records[0].key == "third"
        assert memories.records[1].key == "second"
        assert memories.records[2].key == "first"


class TestMemoryClass:
    """Test the main Memory class with injectable store."""

    def test_memory_with_default_store(self):
        """Test Memory class with default InMemoryStore."""
        memory = Memory()

        memory.store("test", "content", ["tag1"])
        result = memory.search(["tag1"])

        assert len(result) == 1
        assert result[0]["key"] == "test"

    def test_memory_with_custom_store(self):
        """Test Memory class with custom store injection."""
        custom_store = InMemoryStore()
        memory = Memory(store=custom_store)

        memory.store("test", "content", ["tag1"])

        # Should be able to access directly from custom store
        direct_result = custom_store.get_all()
        assert len(direct_result.records) == 1
        assert direct_result.records[0].key == "test"

        # Also verify through memory interface
        memory_result = memory.get_all()
        assert len(memory_result) == 1
        assert memory_result[0]["key"] == "test"


class TestFirestoreStore:
    """Test FirestoreStore fallback behavior."""

    def test_firestore_fallback_when_disabled(self):
        """Test that FirestoreStore falls back when FRESH_USE_FIRESTORE is not set."""
        with patch.dict(os.environ, {}, clear=True):
            store = FirestoreStore()

            # Should use fallback store
            assert store._fallback_store is not None
            assert store._client is None

            # Basic functionality should work
            store.store("test", "content", ["tag1"])
            memories = store.search(["tag1"])
            assert len(memories.records) == 1

    def test_firestore_fallback_on_import_error(self):
        """Test fallback when google-cloud-firestore is not available."""
        with patch.dict(os.environ, {"FRESH_USE_FIRESTORE": "true"}):
            # Patch the import at the module level
            with patch(
                "builtins.__import__",
                side_effect=lambda name, *args: ImportError()
                if "google.cloud" in name
                else __import__(name, *args),
            ):
                store = FirestoreStore()

                # Should use fallback
                assert store._fallback_store is not None
                assert store._client is None

    def test_firestore_emulator_configuration(self):
        """Test Firestore emulator host configuration."""
        with patch.dict(
            os.environ,
            {
                "FRESH_USE_FIRESTORE": "true",
                "FIRESTORE_EMULATOR_HOST": "localhost:8080",
            },
        ):
            # Mock the firestore module
            mock_firestore = MagicMock()
            mock_client = MagicMock()
            mock_collection = MagicMock()

            mock_firestore.Client.return_value = mock_client
            mock_client.collection.return_value = mock_collection
            mock_collection.limit.return_value.stream.return_value = []

            with patch("agency_memory.firestore_store.firestore", mock_firestore):
                _ = FirestoreStore()

                # Should attempt to use Firestore
                assert mock_firestore.Client.called


class TestLearningConsolidation:
    """Test learning consolidation functionality."""

    def test_consolidate_empty_memories(self):
        """Test consolidation with no memories."""
        result = consolidate_learnings([])

        assert result["total_memories"] == 0
        assert result["tag_frequencies"] == {}
        assert "generated_at" in result

    def test_consolidate_basic_analysis(self):
        """Test basic learning consolidation analysis."""
        memories = [
            {
                "key": "mem1",
                "content": "test content",
                "tags": ["work", "urgent"],
                "timestamp": "2023-01-01T10:00:00",
            },
            {
                "key": "mem2",
                "content": "another test",
                "tags": ["work", "research"],
                "timestamp": "2023-01-01T14:00:00",
            },
            {
                "key": "mem3",
                "content": "personal note",
                "tags": ["personal"],
                "timestamp": "2023-01-01T20:00:00",
            },
        ]

        result = consolidate_learnings(memories)

        assert result["total_memories"] == 3
        assert result["unique_tags"] == 4
        assert result["tag_frequencies"]["work"] == 2
        assert result["tag_frequencies"]["urgent"] == 1
        assert result["tag_frequencies"]["research"] == 1
        assert result["tag_frequencies"]["personal"] == 1

    def test_consolidate_tag_patterns(self):
        """Test tag frequency analysis."""
        memories = [
            {
                "key": "m1",
                "content": "c1",
                "tags": ["common", "rare1"],
                "timestamp": "2023-01-01T10:00:00",
            },
            {
                "key": "m2",
                "content": "c2",
                "tags": ["common", "rare2"],
                "timestamp": "2023-01-01T11:00:00",
            },
            {
                "key": "m3",
                "content": "c3",
                "tags": ["common"],
                "timestamp": "2023-01-01T12:00:00",
            },
        ]

        result = consolidate_learnings(memories)

        # "common" should be the most frequent tag
        top_tags = result["top_tags"]
        assert top_tags[0]["tag"] == "common"
        assert top_tags[0]["count"] == 3

    def test_generate_learning_report(self):
        """Test learning report generation."""
        memories = [
            {
                "key": "m1",
                "content": "test",
                "tags": ["work"],
                "timestamp": "2023-01-01T10:00:00",
            }
        ]

        report = generate_learning_report(memories, "test_session")

        assert "# Learning Consolidation Report" in report
        assert "test_session" in report
        assert "Total Memories: 1" in report


class TestSessionTranscript:
    """Test session transcript functionality."""

    def test_create_session_transcript(self):
        """Test session transcript creation."""
        memories = [
            {
                "key": "test_memory",
                "content": "Test content for transcript",
                "tags": ["test", "transcript"],
                "timestamp": "2023-01-01T10:00:00",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch the hardcoded path in create_session_transcript
            with patch("agency_memory.memory.os.path.join") as mock_join:
                mock_join.return_value = os.path.join(temp_dir, "test_transcript.md")

                filepath = create_session_transcript(memories, "test_session")

                # Check file was created
                assert os.path.exists(filepath)

                # Check content
                with open(filepath, "r") as f:
                    content = f.read()

                assert "Session Transcript: test_session" in content
                assert "test_memory" in content
                assert "Test content for transcript" in content
                assert "test, transcript" in content

    def test_create_empty_session_transcript(self):
        """Test transcript creation with no memories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("agency_memory.memory.os.path.join") as mock_join:
                mock_join.return_value = os.path.join(temp_dir, "empty_transcript.md")

                filepath = create_session_transcript([], "empty_session")

                with open(filepath, "r") as f:
                    content = f.read()

                assert "No memories recorded for this session" in content


class TestEdgeCases:
    """Edge case tests for the Memory API."""

    def test_memory_overflow_handling(self):
        """Test handling of many memories without overflow."""
        store = InMemoryStore()

        # Store a large number of memories
        for i in range(1000):
            store.store(f"mem_{i}", f"content_{i}", [f"tag_{i % 10}"])

        # Should handle large datasets
        all_memories = store.get_all()
        assert len(all_memories.records) == 1000

        # Search should still work efficiently
        tag_memories = store.search(["tag_0"])
        assert len(tag_memories.records) == 100  # 1000/10 = 100 memories per tag

    def test_concurrent_access_simulation(self):
        """Test simulated concurrent access to memory store."""
        store = InMemoryStore()

        # Simulate concurrent writes by rapid successive calls
        for i in range(50):
            store.store(f"concurrent_{i}", f"data_{i}", ["concurrent"])

        # All memories should be preserved
        concurrent_memories = store.search(["concurrent"])
        assert len(concurrent_memories.records) == 50

        # Keys should be unique
        keys = [m.key for m in concurrent_memories.records]
        assert len(set(keys)) == 50

    def test_very_large_content_truncation(self):
        """Test handling of very large content."""
        store = InMemoryStore()

        # Create very large content (10KB)
        large_content = "x" * 10000
        store.store("large_content", large_content, ["large"])

        # Content should be stored as-is in InMemoryStore
        memories = store.get_all()
        assert len(memories.records[0].content) == 10000

    def test_special_characters_in_content(self):
        """Test handling of special characters and unicode."""
        store = InMemoryStore()

        special_content = "测试 🚀 Special chars: !@#$%^&*()[]{}|\\:;\"'<>?,./"
        store.store("special", special_content, ["unicode", "special"])

        memories = store.search(["unicode"])
        assert len(memories.records) == 1
        assert memories.records[0].content == special_content

    def test_empty_and_none_values(self):
        """Test handling of empty and None values."""
        store = InMemoryStore()

        # Empty content
        store.store("empty", "", ["empty"])

        # None content (should be converted to string)
        store.store("none", None, ["none"])

        memories = store.get_all()
        assert len(memories.records) == 2

        empty_mem = next(m for m in memories.records if m.key == "empty")
        assert empty_mem.content == ""

        none_mem = next(m for m in memories.records if m.key == "none")
        assert none_mem.content is None or str(none_mem.content) == "None"


class TestIntegration:
    """Integration tests for the complete memory system."""

    def test_session_transcript_with_no_memories(self):
        """Test session transcript generation with no memories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript_file = os.path.join(temp_dir, "empty_test.md")

            # Use a fixed file path instead of mocking
            with patch(
                "agency_memory.memory.os.path.join", return_value=transcript_file
            ):
                _ = create_session_transcript([], "empty_session")

                # File should be created
                assert os.path.exists(transcript_file)

                # Check content
                with open(transcript_file, "r") as f:
                    content = f.read()

                assert "No memories recorded" in content

    def test_full_workflow(self):
        """Test complete workflow: store, search, analyze, transcript."""
        memory = Memory()

        # Store some test data
        memory.store("task1", "Completed feature X", ["work", "completed"])
        memory.store("task2", "Bug in module Y", ["work", "bug", "urgent"])
        memory.store("note1", "Meeting notes", ["personal", "meeting"])

        # Search functionality
        work_items = memory.search(["work"])
        assert len(work_items) == 2

        urgent_items = memory.search(["urgent"])
        assert len(urgent_items) == 1

        # Learning analysis
        all_memories = memory.get_all()
        analysis = consolidate_learnings(all_memories)

        assert analysis["total_memories"] == 3
        assert "work" in analysis["tag_frequencies"]
        assert analysis["tag_frequencies"]["work"] == 2

        # Session transcript
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript_file = os.path.join(temp_dir, "integration_test.md")

            with patch(
                "agency_memory.memory.os.path.join", return_value=transcript_file
            ):
                _ = create_session_transcript(
                    all_memories, "integration_test"
                )
                assert os.path.exists(transcript_file)

    def test_fallback_messages_logged(self, caplog):
        """Test that fallback messages are properly logged."""
        import logging

        # Clear any previous log records and set up fresh capture
        caplog.clear()

        # Ensure we capture from the right logger
        with caplog.at_level(logging.WARNING, logger="agency_memory.firestore_store"):
            with patch.dict(os.environ, {}, clear=True):
                _ = FirestoreStore()

            # Check that fallback message was logged
            fallback_messages = [
                record.message for record in caplog.records
                if "falling back to inmemorystore" in record.message.lower()
            ]

            # More detailed assertion with debugging info
            if not fallback_messages:
                print(f"Captured {len(caplog.records)} log records:")
                for i, record in enumerate(caplog.records):
                    print(f"  {i}: {record.levelname} - {record.name} - {record.message}")

            assert len(fallback_messages) > 0, f"Expected fallback message not found. Captured {len(caplog.records)} records."


if __name__ == "__main__":
    pytest.main([__file__])
