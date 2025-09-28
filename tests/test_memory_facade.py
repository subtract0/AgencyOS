"""
Comprehensive tests for the UnifiedMemory facade.

Tests the unified memory interface, thread safety, and proper routing
to different backend systems.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from shared.memory_facade import (
    UnifiedMemory, MemoryQuery, SearchResults,
    MemoryStats, MigrationStats, get_unified_memory,
    store_pattern, store_memory, search_all
)
from pattern_intelligence.coding_pattern import (
    CodingPattern, ProblemContext, SolutionApproach,
    EffectivenessMetric, PatternMetadata
)


class TestUnifiedMemory:
    """Test the UnifiedMemory facade."""

    def test_initialization(self):
        """Test UnifiedMemory initialization with all backends."""
        memory = UnifiedMemory()

        assert memory.pattern_store is not None
        assert memory.memory_store is not None
        assert memory.legacy_memory is not None
        assert hasattr(memory, '_lock')

    def test_store_pattern_dict(self):
        """Test storing a pattern from a dictionary."""
        memory = UnifiedMemory()

        # Create a valid pattern dictionary
        pattern_dict = {
            "context": ProblemContext(
                description="Test pattern",
                domain="testing"
            ),
            "solution": SolutionApproach(
                approach="Test approach",
                implementation="Test implementation"
            ),
            "outcome": EffectivenessMetric(
                success_rate=0.95
            ),
            "metadata": PatternMetadata(
                pattern_id="test_pattern_001",
                discovered_timestamp="2024-01-01T00:00:00",
                source="test"
            )
        }

        with patch.object(memory.pattern_store, 'store_pattern', return_value="test_id"):
            result = memory.store_pattern(pattern_dict)
            assert result == "test_id"

    def test_store_pattern_object(self):
        """Test storing a CodingPattern object."""
        memory = UnifiedMemory()

        pattern = CodingPattern(
            context=ProblemContext(
                description="Test pattern",
                domain="testing"
            ),
            solution=SolutionApproach(
                approach="Test approach",
                implementation="Test implementation"
            ),
            outcome=EffectivenessMetric(
                success_rate=0.95
            ),
            metadata=PatternMetadata(
                pattern_id="test_pattern_002",
                discovered_timestamp="2024-01-01T00:00:00",
                source="test"
            )
        )

        with patch.object(memory.pattern_store, 'store_pattern', return_value="test_id"):
            result = memory.store_pattern(pattern)
            assert result == "test_id"

    def test_store_memory(self):
        """Test storing general memory."""
        memory = UnifiedMemory()

        with patch.object(memory.memory_store, 'store_memory') as mock_store:
            memory.store_memory("test_key", {"data": "value"}, ["tag1"], "category1")
            mock_store.assert_called_once_with(
                key="test_key",
                value={"data": "value"},
                tags=["tag1"],
                metadata={"category": "category1"}
            )

    def test_search_unified(self):
        """Test unified search across systems."""
        memory = UnifiedMemory()

        query = MemoryQuery(
            query="test search",
            limit=5,
            include_patterns=True,
            include_memories=True
        )

        with patch.object(memory.pattern_store, 'search_patterns', return_value=["pattern1"]):
            with patch.object(memory.memory_store, 'search_memories', return_value=["memory1"]):
                results = memory.search(query)

                assert isinstance(results, SearchResults)
                assert results.patterns == ["pattern1"]
                assert results.memories == ["memory1"]

    def test_search_patterns_only(self):
        """Test searching only patterns."""
        memory = UnifiedMemory()

        query = MemoryQuery(
            query="test search",
            include_patterns=True,
            include_memories=False
        )

        with patch.object(memory.pattern_store, 'search_patterns', return_value=["pattern1"]):
            with patch.object(memory.memory_store, 'search_memories') as mock_mem:
                results = memory.search(query)

                assert results.patterns == ["pattern1"]
                assert results.memories == []
                mock_mem.assert_not_called()

    def test_get_pattern(self):
        """Test retrieving a specific pattern."""
        memory = UnifiedMemory()

        mock_pattern = Mock(spec=CodingPattern)
        with patch.object(memory.pattern_store, 'get_pattern', return_value=mock_pattern):
            result = memory.get_pattern("test_id")
            assert result == mock_pattern

    def test_get_memory(self):
        """Test retrieving a specific memory."""
        memory = UnifiedMemory()

        with patch.object(memory.memory_store, 'get_memory', return_value={"data": "value"}):
            result = memory.get_memory("test_key")
            assert result == {"data": "value"}

    def test_list_patterns(self):
        """Test listing patterns."""
        memory = UnifiedMemory()

        mock_patterns = [Mock(spec=CodingPattern) for _ in range(3)]
        with patch.object(memory.pattern_store, 'search_patterns', return_value=mock_patterns):
            results = memory.list_patterns(limit=10)
            assert len(results) == 3

    def test_list_patterns_with_category(self):
        """Test listing patterns filtered by category."""
        memory = UnifiedMemory()

        pattern1 = Mock(spec=CodingPattern)
        pattern1.category = "test"
        pattern2 = Mock(spec=CodingPattern)
        pattern2.category = "other"
        pattern3 = Mock(spec=CodingPattern)
        pattern3.category = "test"

        with patch.object(memory.pattern_store, 'search_patterns', return_value=[pattern1, pattern2, pattern3]):
            results = memory.list_patterns(category="test")
            assert len(results) == 2
            assert all(p.category == "test" for p in results)

    def test_clear_patterns(self):
        """Test clearing all patterns."""
        memory = UnifiedMemory()

        with patch.object(memory.pattern_store, 'clear') as mock_clear:
            memory.clear_patterns()
            mock_clear.assert_called_once()

    def test_get_stats(self):
        """Test getting memory statistics."""
        memory = UnifiedMemory()

        with patch.object(memory, 'list_patterns', return_value=[Mock(), Mock()]):
            with patch.object(memory.memory_store, 'get_memory_count', return_value=5):
                stats = memory.get_stats()

                assert isinstance(stats, MemoryStats)
                assert stats.pattern_count == 2
                assert stats.memory_count == 5
                assert stats.backends_active["pattern_store"] is True
                assert "T" in stats.last_updated  # ISO format includes 'T'

    def test_migrate_legacy_data(self):
        """Test legacy data migration."""
        memory = UnifiedMemory()

        stats = memory.migrate_legacy_data()

        assert isinstance(stats, MigrationStats)
        assert stats.patterns == 0
        assert stats.memories == 0


class TestSingleton:
    """Test the singleton pattern and thread safety."""

    def test_singleton_instance(self):
        """Test that get_unified_memory returns the same instance."""
        memory1 = get_unified_memory()
        memory2 = get_unified_memory()

        assert memory1 is memory2

    def test_thread_safety_singleton(self):
        """Test thread-safe singleton creation."""
        instances = []

        def get_instance():
            instances.append(get_unified_memory())

        # Reset singleton for test
        import shared.memory_facade
        shared.memory_facade._unified_memory = None

        # Create multiple threads trying to get the singleton
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_instance)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same
        assert all(inst is instances[0] for inst in instances)

    def test_thread_safety_operations(self):
        """Test thread-safe memory operations."""
        memory = UnifiedMemory()

        # Mock the backends to count calls
        call_count = {'patterns': 0, 'memories': 0}

        def mock_store_pattern(pattern):
            call_count['patterns'] += 1
            time.sleep(0.001)  # Simulate work
            return f"pattern_{call_count['patterns']}"

        def mock_store_memory(key, value, tags, metadata):
            call_count['memories'] += 1
            time.sleep(0.001)  # Simulate work

        with patch.object(memory.pattern_store, 'store_pattern', side_effect=mock_store_pattern):
            with patch.object(memory.memory_store, 'store_memory', side_effect=mock_store_memory):
                # Run concurrent operations
                with ThreadPoolExecutor(max_workers=5) as executor:
                    # Submit pattern storage tasks
                    pattern_futures = []
                    for i in range(10):
                        pattern = CodingPattern(
                            context=ProblemContext(f"Test {i}", "test"),
                            solution=SolutionApproach(f"Solution {i}", f"Impl {i}"),
                            outcome=EffectivenessMetric(0.9),
                            metadata=PatternMetadata(f"test_{i}", "2024-01-01T00:00:00", "test")
                        )
                        future = executor.submit(memory.store_pattern, pattern)
                        pattern_futures.append(future)

                    # Submit memory storage tasks
                    memory_futures = []
                    for i in range(10):
                        future = executor.submit(
                            memory.store_memory,
                            f"key_{i}",
                            {"value": i},
                            [f"tag_{i}"]
                        )
                        memory_futures.append(future)

                    # Wait for all tasks to complete
                    for future in pattern_futures + memory_futures:
                        future.result()

                # Verify all operations completed
                assert call_count['patterns'] == 10
                assert call_count['memories'] == 10


class TestConvenienceFunctions:
    """Test the convenience functions."""

    def test_store_pattern_convenience(self):
        """Test store_pattern convenience function."""
        pattern = CodingPattern(
            context=ProblemContext("Test", "test"),
            solution=SolutionApproach("Solution", "Implementation"),
            outcome=EffectivenessMetric(0.9),
            metadata=PatternMetadata("test_001", "2024-01-01T00:00:00", "test")
        )

        with patch('shared.memory_facade.get_unified_memory') as mock_get:
            mock_memory = Mock()
            mock_memory.store_pattern.return_value = "test_id"
            mock_get.return_value = mock_memory

            result = store_pattern(pattern)

            assert result == "test_id"
            mock_memory.store_pattern.assert_called_once_with(pattern)

    def test_store_memory_convenience(self):
        """Test store_memory convenience function."""
        with patch('shared.memory_facade.get_unified_memory') as mock_get:
            mock_memory = Mock()
            mock_get.return_value = mock_memory

            store_memory("test_key", {"data": "value"}, ["tag1"])

            mock_memory.store_memory.assert_called_once_with(
                "test_key", {"data": "value"}, ["tag1"]
            )

    def test_search_all_convenience(self):
        """Test search_all convenience function."""
        with patch('shared.memory_facade.get_unified_memory') as mock_get:
            mock_memory = Mock()
            mock_results = SearchResults()
            mock_memory.search.return_value = mock_results
            mock_get.return_value = mock_memory

            results = search_all("test query", limit=5)

            assert results == mock_results
            # Verify the query object was created correctly
            call_args = mock_memory.search.call_args[0][0]
            assert call_args.query == "test query"
            assert call_args.limit == 5