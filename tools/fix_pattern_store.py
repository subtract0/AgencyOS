"""
Fix pattern store for learning from successful fixes.

Stores patterns of successful code fixes for reuse:
- Pattern matching against original code
- Confidence scoring based on success rate
- LRU caching to prevent memory exhaustion

Constitutional Compliance:
- Article IV: Learning integration (stores patterns, queries past fixes)
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.type_definitions.result import Err, Ok, Result


STORE_PATH = PROJECT_ROOT / "logs" / "fix_patterns.json"
MAX_PATTERNS = 10000  # LRU limit to prevent memory exhaustion


@dataclass
class FixPattern:
    """A learned fix pattern."""

    issue_type: str
    original_pattern: str  # Regex or exact match
    fixed_template: str  # Template with {placeholders}
    confidence: float  # 0.0 to 1.0
    success_count: int
    failure_count: int
    last_used: datetime
    created: datetime
    examples: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "issue_type": self.issue_type,
            "original_pattern": self.original_pattern,
            "fixed_template": self.fixed_template,
            "confidence": self.confidence,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_used": self.last_used.isoformat(),
            "created": self.created.isoformat(),
            "examples": self.examples[-5:],  # Keep last 5 examples
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FixPattern":
        """Create from dictionary."""
        return cls(
            issue_type=data["issue_type"],
            original_pattern=data["original_pattern"],
            fixed_template=data["fixed_template"],
            confidence=data["confidence"],
            success_count=data["success_count"],
            failure_count=data["failure_count"],
            last_used=datetime.fromisoformat(data["last_used"]),
            created=datetime.fromisoformat(data["created"]),
            examples=data.get("examples", []),
        )


class FixPatternStore:
    """Store and retrieve fix patterns.

    Uses file-based persistence with LRU eviction.
    """

    def __init__(self, store_path: Path | None = None):
        """Initialize the pattern store.

        Args:
            store_path: Path to store file (default: logs/fix_patterns.json)
        """
        self.store_path = store_path or STORE_PATH
        self.patterns: dict[str, list[FixPattern]] = {}
        self._load()

    def _load(self) -> None:
        """Load patterns from disk."""
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                for issue_type, patterns in data.items():
                    self.patterns[issue_type] = [
                        FixPattern.from_dict(p) for p in patterns
                    ]
            except Exception:
                self.patterns = {}

    def _save(self) -> None:
        """Save patterns to disk."""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            issue_type: [p.to_dict() for p in patterns]
            for issue_type, patterns in self.patterns.items()
        }
        self.store_path.write_text(json.dumps(data, indent=2))

    def _enforce_limit(self) -> None:
        """Enforce LRU limit on total patterns."""
        total = sum(len(patterns) for patterns in self.patterns.values())

        if total <= MAX_PATTERNS:
            return

        # Collect all patterns with their issue types
        all_patterns = []
        for issue_type, patterns in self.patterns.items():
            for pattern in patterns:
                all_patterns.append((issue_type, pattern))

        # Sort by last_used (oldest first)
        all_patterns.sort(key=lambda x: x[1].last_used)

        # Remove oldest until under limit
        to_remove = total - MAX_PATTERNS
        for issue_type, pattern in all_patterns[:to_remove]:
            self.patterns[issue_type].remove(pattern)

        # Clean empty lists
        self.patterns = {k: v for k, v in self.patterns.items() if v}

    def record_success(
        self, issue_type: str, original: str, fixed: str
    ) -> Result[FixPattern, str]:
        """Record a successful fix.

        Args:
            issue_type: Type of issue (e.g., "bare_except")
            original: Original code that was fixed
            fixed: Fixed code

        Returns:
            Result containing the created/updated pattern
        """
        if issue_type not in self.patterns:
            self.patterns[issue_type] = []

        # Check for existing similar pattern
        existing = self._find_similar_pattern(issue_type, original)

        if existing:
            # Update existing pattern
            existing.success_count += 1
            existing.last_used = datetime.now()
            existing.confidence = existing.success_count / (
                existing.success_count + existing.failure_count
            )
            existing.examples.append(
                {
                    "original": original[:200],
                    "fixed": fixed[:200],
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._save()
            return Ok(existing)

        # Create new pattern
        pattern = FixPattern(
            issue_type=issue_type,
            original_pattern=self._extract_pattern(original),
            fixed_template=fixed,
            confidence=0.8,  # Initial confidence
            success_count=1,
            failure_count=0,
            last_used=datetime.now(),
            created=datetime.now(),
            examples=[
                {
                    "original": original[:200],
                    "fixed": fixed[:200],
                    "timestamp": datetime.now().isoformat(),
                }
            ],
        )

        self.patterns[issue_type].append(pattern)
        self._enforce_limit()
        self._save()

        return Ok(pattern)

    def record_failure(self, issue_type: str, original: str) -> None:
        """Record a failed fix attempt.

        Args:
            issue_type: Type of issue
            original: Original code that failed to fix
        """
        existing = self._find_similar_pattern(issue_type, original)
        if existing:
            existing.failure_count += 1
            existing.confidence = existing.success_count / (
                existing.success_count + existing.failure_count
            )
            self._save()

    def find_matching_pattern(
        self, issue_type: str, code: str
    ) -> Optional[FixPattern]:
        """Find a pattern that matches the given code.

        Args:
            issue_type: Type of issue
            code: Code to match against patterns

        Returns:
            Best matching pattern or None
        """
        import re

        if issue_type not in self.patterns:
            return None

        best_match = None
        best_confidence = 0.0

        for pattern in self.patterns[issue_type]:
            try:
                if re.search(pattern.original_pattern, code):
                    if pattern.confidence > best_confidence:
                        best_match = pattern
                        best_confidence = pattern.confidence
            except re.error:
                # Invalid regex - try exact match
                if pattern.original_pattern in code:
                    if pattern.confidence > best_confidence:
                        best_match = pattern
                        best_confidence = pattern.confidence

        return best_match

    def apply_pattern(self, pattern: FixPattern, code: str) -> str:
        """Apply a pattern to fix code.

        Args:
            pattern: The pattern to apply
            code: Code to fix

        Returns:
            Fixed code
        """
        import re

        # Update last used
        pattern.last_used = datetime.now()
        self._save()

        # Try regex substitution first
        try:
            fixed = re.sub(pattern.original_pattern, pattern.fixed_template, code)
            if fixed != code:
                return fixed
        except re.error:
            pass

        # Fall back to simple replacement
        if pattern.original_pattern in code:
            return code.replace(pattern.original_pattern, pattern.fixed_template)

        # Return template as last resort
        return pattern.fixed_template

    def _find_similar_pattern(
        self, issue_type: str, code: str
    ) -> Optional[FixPattern]:
        """Find a pattern similar to the given code.

        Args:
            issue_type: Type of issue
            code: Code to compare

        Returns:
            Similar pattern or None
        """
        if issue_type not in self.patterns:
            return None

        # Try exact match first (for identical patterns)
        import re
        for pattern in self.patterns[issue_type]:
            if pattern.original_pattern == code:
                return pattern
            # Also check if original is in code or vice versa
            if pattern.original_pattern in code or code in pattern.original_pattern:
                return pattern
            # Try matching via regex (original_pattern may be escaped)
            try:
                if re.search(pattern.original_pattern, code):
                    return pattern
            except re.error:
                pass

        # Fall back to similarity matching
        normalized = self._normalize_code(code)
        for pattern in self.patterns[issue_type]:
            pattern_normalized = self._normalize_code(pattern.original_pattern)
            if self._similarity(normalized, pattern_normalized) > 0.7:
                return pattern

        return None

    def _extract_pattern(self, code: str) -> str:
        """Extract a reusable pattern from code.

        Args:
            code: Code to extract pattern from

        Returns:
            Regex pattern
        """
        import re

        # Escape special regex characters
        pattern = re.escape(code)

        # Replace common variable names with wildcards
        pattern = re.sub(r"\\b[a-z_][a-z0-9_]*\\b", r"\\w+", pattern)

        return pattern

    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison.

        Args:
            code: Code to normalize

        Returns:
            Normalized code
        """
        import re

        # Remove whitespace
        code = re.sub(r"\s+", " ", code)
        # Remove variable names (replace with placeholder)
        code = re.sub(r"\b[a-z_][a-z0-9_]*\b", "_", code)
        return code.strip()

    def _similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings.

        Args:
            a: First string
            b: Second string

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not a or not b:
            return 0.0

        # Simple Jaccard similarity on character trigrams
        def trigrams(s: str) -> set:
            return {s[i : i + 3] for i in range(len(s) - 2)}

        a_trigrams = trigrams(a)
        b_trigrams = trigrams(b)

        if not a_trigrams or not b_trigrams:
            return 0.0

        intersection = len(a_trigrams & b_trigrams)
        union = len(a_trigrams | b_trigrams)

        return intersection / union if union > 0 else 0.0

    def get_stats(self) -> dict:
        """Get statistics about stored patterns.

        Returns:
            Dictionary with statistics
        """
        total_patterns = sum(len(patterns) for patterns in self.patterns.values())
        total_successes = sum(
            p.success_count for patterns in self.patterns.values() for p in patterns
        )
        total_failures = sum(
            p.failure_count for patterns in self.patterns.values() for p in patterns
        )

        avg_confidence = 0.0
        if total_patterns > 0:
            avg_confidence = sum(
                p.confidence for patterns in self.patterns.values() for p in patterns
            ) / total_patterns

        return {
            "total_patterns": total_patterns,
            "issue_types": list(self.patterns.keys()),
            "total_successes": total_successes,
            "total_failures": total_failures,
            "average_confidence": avg_confidence,
            "max_patterns": MAX_PATTERNS,
        }

    def get_top_patterns(self, limit: int = 10) -> list[FixPattern]:
        """Get top patterns by confidence and usage.

        Args:
            limit: Maximum number to return

        Returns:
            List of top patterns
        """
        all_patterns = [
            p for patterns in self.patterns.values() for p in patterns
        ]
        all_patterns.sort(
            key=lambda p: (p.confidence, p.success_count), reverse=True
        )
        return all_patterns[:limit]

    def clear(self) -> None:
        """Clear all patterns."""
        self.patterns = {}
        self._save()


def main():
    """Command-line interface for pattern store."""
    import argparse

    parser = argparse.ArgumentParser(description="Fix pattern store")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--top", type=int, default=10, help="Show top N patterns")
    parser.add_argument("--clear", action="store_true", help="Clear all patterns")
    args = parser.parse_args()

    store = FixPatternStore()

    if args.clear:
        store.clear()
        print("Cleared all patterns")

    elif args.stats:
        stats = store.get_stats()
        print(f"\nPattern Store Statistics:")
        print(f"  Total patterns: {stats['total_patterns']}/{stats['max_patterns']}")
        print(f"  Issue types: {', '.join(stats['issue_types']) or 'None'}")
        print(f"  Total successes: {stats['total_successes']}")
        print(f"  Total failures: {stats['total_failures']}")
        print(f"  Average confidence: {stats['average_confidence']:.1%}")

    else:
        top = store.get_top_patterns(args.top)
        if not top:
            print("No patterns stored yet")
        else:
            print(f"\nTop {len(top)} Patterns:")
            for i, p in enumerate(top, 1):
                print(f"\n{i}. {p.issue_type} (confidence: {p.confidence:.1%})")
                print(f"   Successes: {p.success_count}, Failures: {p.failure_count}")
                print(f"   Pattern: {p.original_pattern[:50]}...")
                print(f"   Template: {p.fixed_template[:50]}...")


if __name__ == "__main__":
    main()
