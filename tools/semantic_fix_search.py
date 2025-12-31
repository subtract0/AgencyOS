"""
Semantic Fix Search - VectorStore-powered fix pattern retrieval.

Uses semantic embeddings to find similar fixes from the pattern store.
Falls back to trigram similarity when VectorStore is unavailable.

Constitutional Compliance:
- Article IV: Learning integration (VectorStore-powered pattern retrieval)
"""

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


@dataclass
class SemanticSearchResult:
    """A semantic search result for fix patterns."""

    issue_type: str
    original_pattern: str
    fixed_template: str
    confidence: float
    similarity: float
    source: str  # 'vectorstore', 'pattern_store', 'trigram'
    metadata: dict


class SemanticFixSearch:
    """
    Semantic search for fix patterns.

    Uses VectorStore embeddings for semantic similarity when available,
    falls back to pattern store and trigram matching.
    """

    def __init__(self):
        """Initialize semantic fix search."""
        self._vectorstore = None
        self._vectorstore_available: Optional[bool] = None
        self._pattern_store = None

    def _init_vectorstore(self) -> bool:
        """Initialize VectorStore connection."""
        if self._vectorstore_available is not None:
            return self._vectorstore_available

        try:
            from agency_memory import VectorStore

            self._vectorstore = VectorStore()
            stats = self._vectorstore.get_stats()
            self._vectorstore_available = stats.get("embedding_available", False)
        except Exception:
            self._vectorstore_available = False

        return self._vectorstore_available

    def _init_pattern_store(self) -> bool:
        """Initialize pattern store connection."""
        if self._pattern_store is not None:
            return True

        try:
            from tools.fix_pattern_store import FixPatternStore

            self._pattern_store = FixPatternStore()
            return True
        except ImportError:
            return False

    def search(
        self, code: str, issue_type: Optional[str] = None, top_k: int = 5
    ) -> Result[list[SemanticSearchResult], str]:
        """
        Search for similar fix patterns.

        Args:
            code: Code to find similar fixes for
            issue_type: Optional filter by issue type
            top_k: Number of results to return

        Returns:
            Result containing list of search results
        """
        results = []

        # Try VectorStore first (best quality)
        if self._init_vectorstore() and self._vectorstore:
            vectorstore_results = self._search_vectorstore(code, issue_type, top_k)
            results.extend(vectorstore_results)

        # Try pattern store (good quality, always available)
        if self._init_pattern_store() and self._pattern_store:
            pattern_results = self._search_pattern_store(code, issue_type, top_k)
            results.extend(pattern_results)

        # Fall back to trigram similarity (always works)
        if not results:
            trigram_results = self._search_trigram(code, issue_type, top_k)
            results.extend(trigram_results)

        # Deduplicate by original pattern
        seen = set()
        unique_results = []
        for result in results:
            key = (result.issue_type, result.original_pattern)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        # Sort by confidence * similarity
        unique_results.sort(
            key=lambda r: r.confidence * r.similarity, reverse=True
        )

        return Ok(unique_results[:top_k])

    def _search_vectorstore(
        self, code: str, issue_type: Optional[str], top_k: int
    ) -> list[SemanticSearchResult]:
        """Search VectorStore for similar patterns."""
        results = []

        try:
            if not self._vectorstore:
                return results

            # Search for similar memories
            tags = ["fix_pattern"]
            if issue_type:
                tags.append(issue_type)

            memories = self._vectorstore.search(
                query=code,
                tags=tags,
                limit=top_k * 2,  # Get more, then filter
            )

            for memory in memories:
                content = memory.get("content", {})
                if isinstance(content, dict):
                    results.append(
                        SemanticSearchResult(
                            issue_type=content.get("issue_type", "unknown"),
                            original_pattern=content.get("original", ""),
                            fixed_template=content.get("fixed", ""),
                            confidence=content.get("confidence", 0.5),
                            similarity=memory.get("similarity", 0.5),
                            source="vectorstore",
                            metadata={
                                "memory_id": memory.get("id", ""),
                                "timestamp": memory.get("timestamp", ""),
                            },
                        )
                    )

        except Exception:
            pass

        return results

    def _search_pattern_store(
        self, code: str, issue_type: Optional[str], top_k: int
    ) -> list[SemanticSearchResult]:
        """Search pattern store for matching patterns."""
        results = []

        try:
            if not self._pattern_store:
                return results

            # Get patterns by issue type if specified
            if issue_type:
                pattern = self._pattern_store.find_matching_pattern(issue_type, code)
                if pattern:
                    similarity = self._calculate_similarity(code, pattern.original_pattern)
                    results.append(
                        SemanticSearchResult(
                            issue_type=pattern.issue_type,
                            original_pattern=pattern.original_pattern,
                            fixed_template=pattern.fixed_template,
                            confidence=pattern.confidence,
                            similarity=similarity,
                            source="pattern_store",
                            metadata={
                                "success_count": pattern.success_count,
                                "failure_count": pattern.failure_count,
                                "last_used": pattern.last_used.isoformat(),
                            },
                        )
                    )
            else:
                # Search all patterns
                top_patterns = self._pattern_store.get_top_patterns(top_k * 2)
                for pattern in top_patterns:
                    similarity = self._calculate_similarity(code, pattern.original_pattern)
                    if similarity > 0.3:  # Minimum threshold
                        results.append(
                            SemanticSearchResult(
                                issue_type=pattern.issue_type,
                                original_pattern=pattern.original_pattern,
                                fixed_template=pattern.fixed_template,
                                confidence=pattern.confidence,
                                similarity=similarity,
                                source="pattern_store",
                                metadata={
                                    "success_count": pattern.success_count,
                                    "failure_count": pattern.failure_count,
                                    "last_used": pattern.last_used.isoformat(),
                                },
                            )
                        )

        except Exception:
            pass

        return results

    def _search_trigram(
        self, code: str, issue_type: Optional[str], top_k: int
    ) -> list[SemanticSearchResult]:
        """Search using trigram similarity (fallback)."""
        results = []

        # Common fix patterns (hardcoded fallback)
        common_patterns = [
            {
                "issue_type": "bare_except",
                "original": "except:",
                "fixed": "except Exception:",
                "confidence": 0.95,
            },
            {
                "issue_type": "bare_except",
                "original": "except Exception:",
                "fixed": "except Exception as e:",
                "confidence": 0.9,
            },
            {
                "issue_type": "dict_any_any",
                "original": "Dict[Any, Any]",
                "fixed": "dict[str, Any]",
                "confidence": 0.85,
            },
            {
                "issue_type": "missing_return_type",
                "original": "def func():",
                "fixed": "def func() -> None:",
                "confidence": 0.8,
            },
        ]

        for pattern in common_patterns:
            if issue_type and pattern["issue_type"] != issue_type:
                continue

            similarity = self._calculate_similarity(code, pattern["original"])
            if similarity > 0.2:
                results.append(
                    SemanticSearchResult(
                        issue_type=pattern["issue_type"],
                        original_pattern=pattern["original"],
                        fixed_template=pattern["fixed"],
                        confidence=pattern["confidence"],
                        similarity=similarity,
                        source="trigram",
                        metadata={"builtin": True},
                    )
                )

        return results

    def _calculate_similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings using trigrams."""
        if not a or not b:
            return 0.0

        # Normalize
        a = a.lower().strip()
        b = b.lower().strip()

        # Exact match
        if a == b:
            return 1.0

        # Substring match
        if a in b or b in a:
            return 0.8

        # Trigram similarity
        def trigrams(s: str) -> set:
            return {s[i : i + 3] for i in range(max(0, len(s) - 2))}

        a_trigrams = trigrams(a)
        b_trigrams = trigrams(b)

        if not a_trigrams or not b_trigrams:
            return 0.0

        intersection = len(a_trigrams & b_trigrams)
        union = len(a_trigrams | b_trigrams)

        return intersection / union if union > 0 else 0.0

    def store_fix(
        self,
        issue_type: str,
        original: str,
        fixed: str,
        confidence: float = 0.8,
    ) -> Result[str, str]:
        """
        Store a fix pattern for future searches.

        Args:
            issue_type: Type of issue
            original: Original code
            fixed: Fixed code
            confidence: Confidence level

        Returns:
            Result with success message or error
        """
        # Store in pattern store
        if self._init_pattern_store() and self._pattern_store:
            self._pattern_store.record_success(issue_type, original, fixed)

        # Store in VectorStore for semantic search
        if self._init_vectorstore() and self._vectorstore:
            try:
                self._vectorstore.store(
                    key=f"fix_{issue_type}_{hash(original) % 10000}",
                    content={
                        "issue_type": issue_type,
                        "original": original,
                        "fixed": fixed,
                        "confidence": confidence,
                        "timestamp": datetime.now().isoformat(),
                    },
                    tags=["fix_pattern", issue_type],
                )
            except Exception as e:
                return Err(f"Failed to store in VectorStore: {e}")

        return Ok(f"Stored fix pattern for {issue_type}")

    def get_stats(self) -> dict:
        """Get statistics about search capabilities."""
        stats = {
            "vectorstore_available": self._init_vectorstore(),
            "pattern_store_available": self._init_pattern_store(),
            "fallback_available": True,
        }

        if self._init_pattern_store() and self._pattern_store:
            stats["pattern_store_stats"] = self._pattern_store.get_stats()

        if self._init_vectorstore() and self._vectorstore:
            stats["vectorstore_stats"] = self._vectorstore.get_stats()

        return stats


def main():
    """Command-line interface for semantic fix search."""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic fix search")
    parser.add_argument("code", nargs="?", help="Code to search for fixes")
    parser.add_argument("--type", dest="issue_type", help="Issue type filter")
    parser.add_argument("--top", type=int, default=5, help="Number of results")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    args = parser.parse_args()

    search = SemanticFixSearch()

    if args.stats:
        stats = search.get_stats()
        print("\nSemantic Fix Search Statistics:")
        print(f"  VectorStore: {'✅' if stats['vectorstore_available'] else '❌'}")
        print(f"  Pattern Store: {'✅' if stats['pattern_store_available'] else '❌'}")
        print(f"  Fallback: {'✅' if stats['fallback_available'] else '❌'}")
        if "pattern_store_stats" in stats:
            ps = stats["pattern_store_stats"]
            print(f"\nPattern Store: {ps['total_patterns']} patterns")
            print(f"  Issue types: {', '.join(ps['issue_types']) or 'None'}")
        return

    if not args.code:
        parser.print_help()
        return

    result = search.search(args.code, args.issue_type, args.top)

    if result.is_ok():
        results = result.unwrap()
        print(f"\nFound {len(results)} similar patterns:\n")
        for i, r in enumerate(results, 1):
            score = r.confidence * r.similarity
            print(f"{i}. [{r.issue_type}] (score: {score:.2f})")
            print(f"   Original: {r.original_pattern[:60]}...")
            print(f"   Fixed: {r.fixed_template[:60]}...")
            print(f"   Source: {r.source}, Confidence: {r.confidence:.1%}")
            print()
    else:
        print(f"Error: {result.unwrap_err()}")


if __name__ == "__main__":
    main()
