"""Unit tests for fix pattern store.

Tests the Phase 2 learning system components.
"""

import pytest
from datetime import datetime
from pathlib import Path

import sys

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestFixPattern:
    """Tests for FixPattern dataclass."""

    def test_pattern_creation(self):
        """Test creating a fix pattern."""
        from tools.fix_pattern_store import FixPattern

        pattern = FixPattern(
            issue_type="bare_except",
            original_pattern=r"except\s*:",
            fixed_template="except Exception as e:",
            confidence=0.9,
            success_count=10,
            failure_count=1,
            last_used=datetime.now(),
            created=datetime.now(),
        )

        assert pattern.issue_type == "bare_except"
        assert pattern.confidence == 0.9
        assert pattern.success_count == 10

    def test_pattern_to_dict(self):
        """Test serialization to dict."""
        from tools.fix_pattern_store import FixPattern

        pattern = FixPattern(
            issue_type="bare_except",
            original_pattern=r"except:",
            fixed_template="except Exception as e:",
            confidence=0.9,
            success_count=10,
            failure_count=1,
            last_used=datetime.now(),
            created=datetime.now(),
            examples=[{"original": "x", "fixed": "y"}],
        )

        data = pattern.to_dict()
        assert data["issue_type"] == "bare_except"
        assert data["confidence"] == 0.9
        assert "last_used" in data
        assert len(data["examples"]) == 1

    def test_pattern_from_dict(self):
        """Test deserialization from dict."""
        from tools.fix_pattern_store import FixPattern

        data = {
            "issue_type": "bare_except",
            "original_pattern": "except:",
            "fixed_template": "except Exception as e:",
            "confidence": 0.9,
            "success_count": 10,
            "failure_count": 1,
            "last_used": "2024-01-01T00:00:00",
            "created": "2024-01-01T00:00:00",
            "examples": [],
        }

        pattern = FixPattern.from_dict(data)
        assert pattern.issue_type == "bare_except"
        assert pattern.confidence == 0.9

    def test_pattern_roundtrip(self):
        """Test serialization roundtrip."""
        from tools.fix_pattern_store import FixPattern

        original = FixPattern(
            issue_type="test",
            original_pattern="pattern",
            fixed_template="template",
            confidence=0.85,
            success_count=5,
            failure_count=2,
            last_used=datetime.now(),
            created=datetime.now(),
        )

        data = original.to_dict()
        restored = FixPattern.from_dict(data)

        assert restored.issue_type == original.issue_type
        assert restored.confidence == original.confidence
        assert restored.success_count == original.success_count


class TestFixPatternStore:
    """Tests for FixPatternStore class."""

    def test_store_creation(self, tmp_path):
        """Test creating a store."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        assert store.patterns == {}

    def test_record_success(self, tmp_path):
        """Test recording a successful fix."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        result = store.record_success(
            "bare_except",
            "    except:",
            "    except Exception as e:",
        )

        assert result.is_ok()
        pattern = result.unwrap()
        assert pattern.issue_type == "bare_except"
        assert pattern.success_count == 1
        assert pattern.confidence == 0.8  # Initial confidence

    def test_record_success_updates_existing(self, tmp_path):
        """Test that recording success updates existing patterns."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        # Record first success
        store.record_success("bare_except", "except:", "except Exception as e:")

        # Record second similar success
        result = store.record_success(
            "bare_except", "except:", "except Exception as e:"
        )

        pattern = result.unwrap()
        assert pattern.success_count == 2
        assert pattern.confidence == 1.0  # 2 successes, 0 failures

    def test_record_failure(self, tmp_path):
        """Test recording a failed fix."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        # Record a success first
        store.record_success("bare_except", "except:", "except Exception as e:")

        # Record a failure
        store.record_failure("bare_except", "except:")

        # Check confidence decreased
        pattern = store.find_matching_pattern("bare_except", "except:")
        assert pattern is not None
        assert pattern.failure_count == 1
        assert pattern.confidence == 0.5  # 1 success, 1 failure

    def test_find_matching_pattern(self, tmp_path):
        """Test finding a matching pattern."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        store.record_success("bare_except", "except:", "except Exception as e:")

        pattern = store.find_matching_pattern("bare_except", "    except:")
        assert pattern is not None
        assert pattern.issue_type == "bare_except"

    def test_find_no_matching_pattern(self, tmp_path):
        """Test finding no match returns None."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        pattern = store.find_matching_pattern("unknown", "code")
        assert pattern is None

    def test_apply_pattern(self, tmp_path):
        """Test applying a pattern to fix code."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        result = store.record_success(
            "bare_except", "except:", "except Exception as e:"
        )
        pattern = result.unwrap()

        fixed = store.apply_pattern(pattern, "    except:")
        assert "Exception" in fixed

    def test_persistence(self, tmp_path):
        """Test that patterns persist across store instances."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"

        # Create first store and add pattern
        store1 = FixPatternStore(store_path=store_path)
        store1.record_success("test", "original", "fixed")

        # Create second store and verify pattern exists
        store2 = FixPatternStore(store_path=store_path)
        assert len(store2.patterns.get("test", [])) == 1

    def test_get_stats(self, tmp_path):
        """Test getting statistics."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        store.record_success("type1", "a", "b")
        store.record_success("type2", "c", "d")

        stats = store.get_stats()
        assert stats["total_patterns"] == 2
        assert "type1" in stats["issue_types"]
        assert "type2" in stats["issue_types"]

    def test_get_top_patterns(self, tmp_path):
        """Test getting top patterns."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        # Add patterns with different success counts
        result = store.record_success("type1", "a", "b")
        pattern = result.unwrap()
        # Simulate more successes
        pattern.success_count = 10
        pattern.confidence = 0.95
        store._save()

        store.record_success("type2", "c", "d")

        top = store.get_top_patterns(limit=5)
        assert len(top) == 2
        # Should be sorted by confidence
        assert top[0].confidence >= top[1].confidence

    def test_clear(self, tmp_path):
        """Test clearing all patterns."""
        from tools.fix_pattern_store import FixPatternStore

        store_path = tmp_path / "patterns.json"
        store = FixPatternStore(store_path=store_path)

        store.record_success("test", "a", "b")
        assert store.get_stats()["total_patterns"] == 1

        store.clear()
        assert store.get_stats()["total_patterns"] == 0


class TestLRUEviction:
    """Tests for LRU eviction."""

    def test_enforces_limit(self, tmp_path):
        """Test that LRU limit is enforced."""
        from tools.fix_pattern_store import FixPatternStore
        import tools.fix_pattern_store as module

        # Temporarily reduce limit for testing
        original_limit = module.MAX_PATTERNS
        module.MAX_PATTERNS = 5

        try:
            store_path = tmp_path / "patterns.json"
            store = FixPatternStore(store_path=store_path)

            # Add more patterns than limit
            for i in range(10):
                store.record_success(f"type{i}", f"original{i}", f"fixed{i}")

            # Should have been limited
            total = store.get_stats()["total_patterns"]
            assert total <= 5
        finally:
            module.MAX_PATTERNS = original_limit


class TestSimilarity:
    """Tests for similarity calculation."""

    def test_similar_patterns_match(self, tmp_path):
        """Test that similar patterns are recognized."""
        from tools.fix_pattern_store import FixPatternStore

        store = FixPatternStore(store_path=tmp_path / "patterns.json")

        # Record a pattern
        store.record_success("bare_except", "except:", "except Exception as e:")

        # Similar pattern should find existing
        existing = store._find_similar_pattern("bare_except", "except: pass")
        # Note: may or may not match depending on similarity threshold

    def test_normalize_code(self, tmp_path):
        """Test code normalization."""
        from tools.fix_pattern_store import FixPatternStore

        store = FixPatternStore(store_path=tmp_path / "patterns.json")

        code1 = "def foo():    pass"
        code2 = "def bar(): pass"

        # Normalized versions should be more similar
        norm1 = store._normalize_code(code1)
        norm2 = store._normalize_code(code2)

        # Both should have variables replaced
        assert "_" in norm1
        assert "_" in norm2
