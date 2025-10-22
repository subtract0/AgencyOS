#!/usr/bin/env python3
"""
Test Failure Classifier

Categorizes test failures by auto-fixability using pattern analysis and LLM evaluation.

Constitutional Compliance:
- Article I: Complete context (full traceback analysis)
- Article IV: VectorStore pattern lookup for proven fixes
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class FailureType(str, Enum):
    """Test failure categories."""

    BLOCKER = "blocker"  # Segfault, hang, import error
    ASSERTION = "assertion"  # Test logic failure (assert statement)
    TIMEOUT = "timeout"  # Test execution timeout
    SKIP = "skip"  # Conditional skip (not a failure)


class FixComplexity(str, Enum):
    """Fix complexity classification."""

    TRIVIAL = "trivial"  # Pure deletion, <5 lines, confidence ≥0.95
    SIMPLE = "simple"  # Single function edit, unit test validation, ≥0.80
    MODERATE = "moderate"  # Multi-function changes, integration tests, ≥0.60
    COMPLEX = "complex"  # Architectural changes, manual fix required, <0.60


@dataclass
class FailurePattern:
    """Pattern matched from VectorStore for proven fixes."""

    pattern_id: str
    description: str
    confidence: float
    evidence_count: int
    fix_strategy: str


class TestFailure(BaseModel):
    """Individual test failure record."""

    test_id: str = Field(
        ..., description="Fully qualified test name (e.g., tests/test_foo.py::test_bar)"
    )
    failure_type: FailureType
    error_message: str = Field(..., description="Error message or assertion output")
    traceback: str = Field(default="", description="Full traceback (if available)")
    file_path: str = Field(..., description="Test file path")
    line_number: int | None = Field(default=None, description="Failure line number")

    # Classification results
    fix_complexity: FixComplexity | None = None
    auto_fixable: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_score: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Risk of regression (0=safe, 1=high risk)"
    )

    # Fix strategy
    fix_strategy: str = ""
    matched_patterns: list[str] = Field(
        default_factory=list, description="VectorStore pattern IDs matched"
    )
    estimated_effort_hours: float = Field(
        default=0.5, ge=0.1, description="Estimated fix time in hours"
    )


class TestFailureCatalog(BaseModel):
    """Complete test failure catalog with classification."""

    total_tests: int = Field(..., description="Total test count")
    passed: int
    failed: int
    errors: int
    skipped: int

    failures: list[TestFailure] = Field(default_factory=list)

    # Summary statistics
    blockers: list[str] = Field(default_factory=list, description="Blocker test IDs")
    assertions: list[str] = Field(default_factory=list, description="Assertion failure test IDs")

    # Priority ranking
    priority_ranking: dict[str, int] = Field(
        default_factory=dict, description="test_id -> priority (1=highest)"
    )
    estimated_effort: dict[str, float] = Field(default_factory=dict, description="test_id -> hours")

    # Execution metadata
    execution_time_seconds: float = 0.0
    timeout_occurred: bool = False
    catalog_timestamp: str = ""


class TestFailureClassifier:
    """Classify test failures by auto-fixability using pattern analysis."""

    def __init__(self):
        """Initialize classifier with VectorStore patterns."""
        self.patterns: list[FailurePattern] = []
        self._load_vectorstore_patterns()

    def _load_vectorstore_patterns(self) -> None:
        """Load proven fix patterns from VectorStore (Article IV).

        Expected patterns:
        - pattern_2_2: Environment variable cleanup (fixture-based isolation)
        - pattern_3_2: Schema mismatch (Pydantic model updates)
        - pattern_fixture_isolation: Test isolation via pytest fixtures
        """
        # TODO: Query VectorStore for patterns with tag="test_fixing"
        # For now, use hardcoded patterns from Leap 8 learnings
        self.patterns = [
            FailurePattern(
                pattern_id="pattern_2_2_env_cleanup",
                description="Environment variable pollution between tests",
                confidence=0.85,
                evidence_count=5,
                fix_strategy="Add cleanup fixtures: @pytest.fixture(autouse=True) to reset env vars",
            ),
            FailurePattern(
                pattern_id="pattern_3_2_schema_mismatch",
                description="Pydantic model validation failures",
                confidence=0.90,
                evidence_count=8,
                fix_strategy="Update Pydantic models with correct field types and validators",
            ),
            FailurePattern(
                pattern_id="pattern_fixture_isolation",
                description="Test isolation failures (shared state)",
                confidence=0.80,
                evidence_count=6,
                fix_strategy="Apply fixture-based isolation with proper scope (function/module)",
            ),
        ]

    def classify_failure(self, failure: TestFailure) -> TestFailure:
        """Classify a single test failure by auto-fixability.

        Args:
            failure: Test failure record with error_message and traceback

        Returns:
            Updated TestFailure with classification fields populated
        """
        # Match against VectorStore patterns
        matched_patterns = self._match_patterns(failure)
        failure.matched_patterns = [p.pattern_id for p in matched_patterns]

        # Calculate confidence from pattern matches
        if matched_patterns:
            # Use highest confidence pattern
            best_pattern = max(matched_patterns, key=lambda p: p.confidence)
            failure.confidence = best_pattern.confidence
            failure.fix_strategy = best_pattern.fix_strategy
        else:
            # No pattern match - use heuristics
            failure.confidence = self._heuristic_confidence(failure)
            failure.fix_strategy = self._suggest_fix_strategy(failure)

        # Classify fix complexity
        failure.fix_complexity = self._classify_complexity(failure)

        # Determine auto-fixability
        failure.auto_fixable = (
            failure.fix_complexity in [FixComplexity.TRIVIAL, FixComplexity.SIMPLE]
            and failure.confidence >= 0.80
        )

        # Calculate risk score
        failure.risk_score = self._calculate_risk(failure)

        # Estimate effort
        failure.estimated_effort_hours = self._estimate_effort(failure)

        return failure

    def _match_patterns(self, failure: TestFailure) -> list[FailurePattern]:
        """Match failure against VectorStore patterns."""
        matched = []

        error_lower = failure.error_message.lower()
        traceback_lower = failure.traceback.lower()

        for pattern in self.patterns:
            # Simple keyword matching (TODO: use embeddings for semantic search)
            keywords = {
                "pattern_2_2_env_cleanup": [
                    "environment",
                    "env",
                    "os.environ",
                    "AGENCY_",
                    "monkeypatch",
                ],
                "pattern_3_2_schema_mismatch": [
                    "pydantic",
                    "validation",
                    "ValidationError",
                    "field required",
                ],
                "pattern_fixture_isolation": [
                    "fixture",
                    "scope",
                    "autouse",
                    "teardown",
                    "shared state",
                ],
            }

            pattern_keywords = keywords.get(pattern.pattern_id, [])
            if any(
                kw.lower() in error_lower or kw.lower() in traceback_lower
                for kw in pattern_keywords
            ):
                matched.append(pattern)

        return matched

    def _heuristic_confidence(self, failure: TestFailure) -> float:
        """Calculate confidence using heuristics when no pattern matches."""
        if failure.failure_type == FailureType.BLOCKER:
            return 0.3  # Blockers are complex

        # Assertion failures with clear messages are easier to fix
        if "assert" in failure.error_message.lower():
            if len(failure.error_message) < 200:  # Clear, concise error
                return 0.70
            return 0.60

        # Import errors are usually simple (missing dependency or typo)
        if "ImportError" in failure.error_message or "ModuleNotFoundError" in failure.error_message:
            return 0.85

        return 0.50  # Default moderate confidence

    def _classify_complexity(self, failure: TestFailure) -> FixComplexity:
        """Classify fix complexity based on confidence and failure type."""
        if failure.confidence >= 0.95 and failure.failure_type != FailureType.BLOCKER:
            # Trivial: High confidence, non-blocker (e.g., import error, simple assertion)
            # Check if fix is likely <5 lines
            if (
                "ImportError" in failure.error_message
                or "ModuleNotFoundError" in failure.error_message
            ):
                return FixComplexity.TRIVIAL

        if failure.confidence >= 0.80 and failure.failure_type == FailureType.ASSERTION:
            # Simple: Single function edit, unit test validation
            return FixComplexity.SIMPLE

        if failure.confidence >= 0.60:
            # Moderate: Multi-function changes, integration tests
            return FixComplexity.MODERATE

        # Complex: Architectural changes, manual fix required
        return FixComplexity.COMPLEX

    def _calculate_risk(self, failure: TestFailure) -> float:
        """Calculate risk score for fix (0=safe, 1=high risk of regression)."""
        risk = 0.5  # Default moderate risk

        # Trivial fixes are low risk
        if failure.fix_complexity == FixComplexity.TRIVIAL:
            risk = 0.2

        # Blockers are high risk
        if failure.failure_type == FailureType.BLOCKER:
            risk = 0.8

        # High confidence = lower risk
        risk = risk * (1 - failure.confidence * 0.3)

        return min(max(risk, 0.0), 1.0)

    def _estimate_effort(self, failure: TestFailure) -> float:
        """Estimate fix effort in hours."""
        effort_map = {
            FixComplexity.TRIVIAL: 0.25,  # 15 minutes
            FixComplexity.SIMPLE: 0.5,  # 30 minutes
            FixComplexity.MODERATE: 2.0,  # 2 hours
            FixComplexity.COMPLEX: 4.0,  # 4+ hours
        }

        base_effort = effort_map.get(failure.fix_complexity, 1.0)

        # Blockers take longer
        if failure.failure_type == FailureType.BLOCKER:
            base_effort *= 2.0

        return base_effort

    def _suggest_fix_strategy(self, failure: TestFailure) -> str:
        """Suggest fix strategy based on failure analysis."""
        if failure.failure_type == FailureType.BLOCKER:
            if "segfault" in failure.error_message.lower() or "SIGSEGV" in failure.error_message:
                return "BLOCKER: Quarantine test with @pytest.mark.skip. Investigate segfault root cause (likely C extension issue)."
            if "timeout" in failure.error_message.lower():
                return "BLOCKER: Test hangs. Add explicit timeout, check for infinite loops or deadlocks."
            if (
                "ImportError" in failure.error_message
                or "ModuleNotFoundError" in failure.error_message
            ):
                return "BLOCKER: Missing dependency or import path issue. Check requirements.txt and PYTHONPATH."

        if failure.failure_type == FailureType.ASSERTION:
            return "ASSERTION: Review test expectations vs actual behavior. Update assertion or fix implementation."

        return "Manual investigation required. No automatic fix strategy available."


def parse_pytest_output(output_text: str) -> TestFailureCatalog:
    """Parse pytest output to extract test failures.

    Args:
        output_text: Raw pytest output text

    Returns:
        TestFailureCatalog with all failures parsed
    """
    catalog = TestFailureCatalog(total_tests=0, passed=0, failed=0, errors=0, skipped=0)

    # Extract summary line (e.g., "1234 passed, 12 failed, 5 errors, 10 skipped in 300.00s")
    summary_pattern = r"(\d+)\s+passed(?:,\s+(\d+)\s+failed)?(?:,\s+(\d+)\s+error(?:s)?)?(?:,\s+(\d+)\s+skipped)?.*?in\s+([\d.]+)s"
    summary_match = re.search(summary_pattern, output_text)

    if summary_match:
        catalog.passed = int(summary_match.group(1))
        catalog.failed = int(summary_match.group(2) or 0)
        catalog.errors = int(summary_match.group(3) or 0)
        catalog.skipped = int(summary_match.group(4) or 0)
        catalog.execution_time_seconds = float(summary_match.group(5))
        catalog.total_tests = catalog.passed + catalog.failed + catalog.errors + catalog.skipped

    # Check for timeout
    if "timed out after" in output_text:
        catalog.timeout_occurred = True

    # Parse individual failures (FAILED tests/...)
    failure_pattern = r"FAILED\s+(tests/[^\s]+)\s+-\s+(.+?)(?=\nFAILED|\nERROR|\n=|$)"
    for match in re.finditer(failure_pattern, output_text, re.DOTALL):
        test_id = match.group(1)
        error_message = match.group(2).strip()

        # Extract file path and line number
        file_match = re.match(r"(tests/[^:]+)::(.+)", test_id)
        if file_match:
            file_path = file_match.group(1)
        else:
            file_path = test_id

        failure = TestFailure(
            test_id=test_id,
            failure_type=FailureType.ASSERTION,
            error_message=error_message[:500],  # Truncate long messages
            file_path=file_path,
        )
        catalog.failures.append(failure)
        catalog.assertions.append(test_id)

    # Parse errors (ERROR tests/...)
    error_pattern = r"ERROR\s+(tests/[^\s]+)\s+-\s+(.+?)(?=\nFAILED|\nERROR|\n=|$)"
    for match in re.finditer(error_pattern, output_text, re.DOTALL):
        test_id = match.group(1)
        error_message = match.group(2).strip()

        file_match = re.match(r"(tests/[^:]+)::(.+)", test_id)
        if file_match:
            file_path = file_match.group(1)
        else:
            file_path = test_id

        failure = TestFailure(
            test_id=test_id,
            failure_type=FailureType.BLOCKER,  # Errors are blockers
            error_message=error_message[:500],
            file_path=file_path,
        )
        catalog.failures.append(failure)
        catalog.blockers.append(test_id)

    return catalog


if __name__ == "__main__":
    # Example usage
    import json
    import sys
    from datetime import UTC, datetime

    if len(sys.argv) < 2:
        print("Usage: python test_failure_classifier.py <pytest_output_file>")
        sys.exit(1)

    output_file = Path(sys.argv[1])
    if not output_file.exists():
        print(f"Error: File not found: {output_file}")
        sys.exit(1)

    # Parse pytest output
    output_text = output_file.read_text()
    catalog = parse_pytest_output(output_text)
    catalog.catalog_timestamp = datetime.now(UTC).isoformat()

    # Classify all failures
    classifier = TestFailureClassifier()
    for i, failure in enumerate(catalog.failures):
        catalog.failures[i] = classifier.classify_failure(failure)

    # Generate priority ranking (blockers first, then by confidence descending)
    sorted_failures = sorted(
        catalog.failures,
        key=lambda f: (
            0 if f.failure_type == FailureType.BLOCKER else 1,  # Blockers first
            -f.confidence,  # High confidence first
        ),
    )

    for rank, failure in enumerate(sorted_failures, 1):
        catalog.priority_ranking[failure.test_id] = rank
        catalog.estimated_effort[failure.test_id] = failure.estimated_effort_hours

    # Save catalog
    output_path = Path("logs/test_failure_catalog.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(catalog.model_dump(), f, indent=2)

    print(f"✅ Test Failure Catalog created: {output_path}")
    print("\n📊 Summary:")
    print(f"  Total tests: {catalog.total_tests}")
    print(f"  Passed: {catalog.passed}")
    print(f"  Failed: {catalog.failed}")
    print(f"  Errors: {catalog.errors}")
    print(f"  Skipped: {catalog.skipped}")
    print("\n🔍 Failures by complexity:")

    complexity_counts = {}
    for failure in catalog.failures:
        if failure.fix_complexity:
            complexity_counts[failure.fix_complexity.value] = (
                complexity_counts.get(failure.fix_complexity.value, 0) + 1
            )

    for complexity, count in sorted(complexity_counts.items()):
        auto_fixable_count = sum(
            1
            for f in catalog.failures
            if f.fix_complexity and f.fix_complexity.value == complexity and f.auto_fixable
        )
        print(f"  {complexity.capitalize()}: {count} ({auto_fixable_count} auto-fixable)")

    print(f"\n⏱️  Total estimated effort: {sum(catalog.estimated_effort.values()):.1f} hours")
