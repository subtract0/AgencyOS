"""
Tests for Semantic Fix Search (Phase 2 completion).

Tests the VectorStore-powered fix pattern retrieval including:
- Pattern matching
- Similarity calculation
- Search with different sources
- Fix storage
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestSemanticSearchResult:
    """Tests for SemanticSearchResult dataclass."""

    def test_result_creation(self):
        """Test creating a search result."""
        from tools.semantic_fix_search import SemanticSearchResult

        result = SemanticSearchResult(
            issue_type="bare_except",
            original_pattern="except:",
            fixed_template="except Exception:",
            confidence=0.95,
            similarity=0.85,
            source="pattern_store",
            metadata={"success_count": 10},
        )

        assert result.issue_type == "bare_except"
        assert result.original_pattern == "except:"
        assert result.confidence == 0.95
        assert result.similarity == 0.85
        assert result.source == "pattern_store"


class TestSemanticFixSearch:
    """Tests for SemanticFixSearch class."""

    @pytest.fixture
    def search(self, tmp_path):
        """Create search instance with test store."""
        from tools.semantic_fix_search import SemanticFixSearch

        # Seed pattern store for testing
        from tools.fix_pattern_store import FixPatternStore

        store = FixPatternStore(store_path=tmp_path / "test_patterns.json")
        store.record_success("bare_except", "except:", "except Exception:")
        store.record_success("dict_any_any", "Dict[Any, Any]", "dict[str, Any]")

        s = SemanticFixSearch()
        # Replace pattern store with test version
        s._pattern_store = store
        return s

    def test_search_finds_matching_patterns(self, search):
        """Test that search finds matching patterns."""
        result = search.search("except:")

        assert result.is_ok()
        results = result.unwrap()

        # Should find at least one result
        assert len(results) >= 1

        # First result should be bare_except
        assert any(r.issue_type == "bare_except" for r in results)

    def test_search_with_issue_type_filter(self, search):
        """Test searching with issue type filter."""
        result = search.search("except:", issue_type="bare_except")

        assert result.is_ok()
        results = result.unwrap()

        # All results should be bare_except type
        for r in results:
            assert r.issue_type == "bare_except"

    def test_search_top_k_limit(self, search):
        """Test that top_k limits results."""
        result = search.search("except:", top_k=2)

        assert result.is_ok()
        results = result.unwrap()

        assert len(results) <= 2

    def test_similarity_calculation(self, search):
        """Test similarity calculation."""
        # Exact match
        sim = search._calculate_similarity("except:", "except:")
        assert sim == 1.0

        # Substring match
        sim = search._calculate_similarity("except:", "    except:")
        assert sim > 0.7

        # No match
        sim = search._calculate_similarity("def foo():", "class Bar:")
        assert sim < 0.5

    def test_search_deduplicates_results(self, search):
        """Test that duplicate results are removed."""
        # Search should not return duplicates
        result = search.search("except:")

        assert result.is_ok()
        results = result.unwrap()

        # Check for duplicates
        seen = set()
        for r in results:
            key = (r.issue_type, r.original_pattern)
            assert key not in seen, f"Duplicate found: {key}"
            seen.add(key)

    def test_search_sorts_by_score(self, search):
        """Test that results are sorted by confidence * similarity."""
        result = search.search("code")

        assert result.is_ok()
        results = result.unwrap()

        if len(results) >= 2:
            # Verify sorted in descending order
            for i in range(len(results) - 1):
                score_i = results[i].confidence * results[i].similarity
                score_j = results[i + 1].confidence * results[i + 1].similarity
                assert score_i >= score_j

    def test_trigram_fallback(self):
        """Test trigram fallback when pattern store has no matches."""
        from tools.semantic_fix_search import SemanticFixSearch

        search = SemanticFixSearch()

        # Search for something that won't match any pattern
        result = search.search("completely_random_unique_code_xyz123")

        assert result.is_ok()
        results = result.unwrap()

        # When no patterns match, should fall back to trigram
        # Trigram may return empty for completely random code
        # Just verify the search completes successfully
        assert isinstance(results, list)

    def test_store_fix(self, search, tmp_path):
        """Test storing a new fix pattern."""
        result = search.store_fix(
            issue_type="new_issue",
            original="old code",
            fixed="new code",
            confidence=0.9,
        )

        assert result.is_ok()
        assert "Stored" in result.unwrap()

    def test_get_stats(self, search):
        """Test getting search statistics."""
        stats = search.get_stats()

        assert "pattern_store_available" in stats
        assert "fallback_available" in stats
        assert stats["fallback_available"] is True


class TestSimilarityCalculation:
    """Tests for similarity calculation methods."""

    @pytest.fixture
    def search(self):
        """Create search instance."""
        from tools.semantic_fix_search import SemanticFixSearch

        return SemanticFixSearch()

    def test_exact_match_similarity(self, search):
        """Test exact match returns 1.0."""
        sim = search._calculate_similarity("test", "test")
        assert sim == 1.0

    def test_empty_string_similarity(self, search):
        """Test empty strings return 0.0."""
        sim = search._calculate_similarity("", "test")
        assert sim == 0.0

        sim = search._calculate_similarity("test", "")
        assert sim == 0.0

    def test_substring_similarity(self, search):
        """Test substring match has high similarity."""
        # After normalization (strip + lowercase), these are equal
        # Test with strings that are substrings but not equal after normalization
        sim = search._calculate_similarity("except", "exception")
        assert sim > 0.5  # Similar due to shared prefix

    def test_case_insensitive(self, search):
        """Test similarity is case insensitive."""
        sim = search._calculate_similarity("EXCEPT:", "except:")
        assert sim == 1.0

    def test_whitespace_handling(self, search):
        """Test whitespace is normalized."""
        sim = search._calculate_similarity("  test  ", "test")
        assert sim == 1.0

    def test_trigram_similarity(self, search):
        """Test trigram similarity for similar strings."""
        # Similar words should have high similarity
        sim = search._calculate_similarity("exception", "exceptions")
        assert sim > 0.6

        # Different words should have low similarity
        sim = search._calculate_similarity("abc", "xyz")
        assert sim < 0.3
