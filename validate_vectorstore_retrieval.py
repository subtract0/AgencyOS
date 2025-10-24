#!/usr/bin/env python3
"""
Validate VectorStore Retrieval - Cross-Session Test

Validate that stored test recovery patterns can be retrieved across sessions
(Article IV compliance verification).

Constitutional Requirements:
- Cross-session retrieval must work
- Patterns must maintain confidence scores
- Evidence counts must be preserved
- Tags must be searchable
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.agent_context import create_agent_context


def validate_cross_session_retrieval():
    """
    Validate VectorStore cross-session retrieval (Article IV).

    Tests:
    1. Retrieve all test_recovery patterns
    2. Validate pattern structure
    3. Check confidence scores preserved
    4. Verify evidence counts maintained
    5. Test tag-based filtering
    """
    print("=" * 80)
    print("VectorStore Cross-Session Retrieval Validation (Article IV)")
    print("=" * 80)
    print()

    # Initialize new context (simulating new session)
    context = create_agent_context(session_id="retrieval_validation_new_session")
    print("✅ New session context initialized: retrieval_validation_new_session")
    print()

    # Test 1: Retrieve all test_recovery patterns
    print("Test 1: Retrieve all test_recovery patterns")
    print("-" * 80)
    try:
        all_patterns = context.search_memories(
            tags=["test_recovery"],
            include_session=False  # Cross-session
        )
        print(f"✅ Retrieved {len(all_patterns)} patterns")

        if len(all_patterns) != 8:
            print(f"⚠️  WARNING: Expected 8 patterns, got {len(all_patterns)}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

    print()

    # Test 2: Validate pattern structure
    print("Test 2: Validate pattern structure")
    print("-" * 80)

    required_fields = [
        "id", "name", "type", "description", "pattern",
        "evidence", "confidence", "evidence_count",
        "impact", "reusability", "tags"
    ]

    structure_valid = True
    for pattern in all_patterns:
        missing_fields = [f for f in required_fields if f not in pattern]
        if missing_fields:
            print(f"❌ Pattern '{pattern.get('name', 'Unknown')}' missing fields: {missing_fields}")
            structure_valid = False

    if structure_valid:
        print(f"✅ All {len(all_patterns)} patterns have required fields")
    else:
        print("❌ Some patterns have missing fields")

    print()

    # Test 3: Check confidence scores preserved
    print("Test 3: Check confidence scores preserved (Article IV: ≥0.6)")
    print("-" * 80)

    confidence_valid = True
    for pattern in all_patterns:
        confidence = pattern.get("confidence", 0)
        name = pattern.get("name", "Unknown")

        if confidence < 0.6:
            print(f"❌ Pattern '{name}': confidence {confidence} < 0.6 (Article IV violation)")
            confidence_valid = False
        else:
            print(f"✅ Pattern '{name}': confidence {confidence:.3f}")

    if confidence_valid:
        print("\n✅ All patterns meet Article IV confidence threshold (≥0.6)")
    else:
        print("\n❌ Some patterns violate Article IV confidence requirement")

    print()

    # Test 4: Verify evidence counts maintained
    print("Test 4: Verify evidence counts maintained (Article IV: ≥3)")
    print("-" * 80)

    evidence_valid = True
    for pattern in all_patterns:
        evidence_count = pattern.get("evidence_count", 0)
        name = pattern.get("name", "Unknown")

        if evidence_count < 3:
            print(f"❌ Pattern '{name}': evidence {evidence_count} < 3 (Article IV violation)")
            evidence_valid = False
        else:
            print(f"✅ Pattern '{name}': evidence count {evidence_count}")

    if evidence_valid:
        print("\n✅ All patterns meet Article IV evidence threshold (≥3)")
    else:
        print("\n❌ Some patterns violate Article IV evidence requirement")

    print()

    # Test 5: Test tag-based filtering
    print("Test 5: Test tag-based filtering")
    print("-" * 80)

    test_queries = [
        (["test_recovery", "pydantic"], "Pydantic patterns"),
        (["test_recovery", "e2e"], "E2E patterns"),
        (["test_recovery", "efficiency"], "Efficiency patterns"),
        (["test_recovery", "memory_management"], "Memory-aware patterns"),
    ]

    filtering_valid = True
    for tags, description in test_queries:
        try:
            results = context.search_memories(
                tags=tags,
                include_session=False
            )
            print(f"✅ {description}: {len(results)} results")

            if len(results) == 0:
                print(f"   ⚠️  Warning: No results for {tags}")

        except Exception as e:
            print(f"❌ {description}: Query failed - {e}")
            filtering_valid = False

    if filtering_valid:
        print("\n✅ Tag-based filtering working")
    else:
        print("\n❌ Tag-based filtering has issues")

    print()

    # Summary
    print("=" * 80)
    print("Validation Summary")
    print("=" * 80)
    all_tests_passed = (
        len(all_patterns) == 8 and
        structure_valid and
        confidence_valid and
        evidence_valid and
        filtering_valid
    )

    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
        print()
        print("Article IV Compliance: ✅ VERIFIED")
        print("Cross-Session Retrieval: ✅ WORKING")
        print("Pattern Quality: ✅ MAINTAINED")
        print()
        print("Future agents can safely query:")
        print("  context.search_memories(['test_recovery'])")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Issues detected:")
        if len(all_patterns) != 8:
            print(f"  - Expected 8 patterns, got {len(all_patterns)}")
        if not structure_valid:
            print("  - Some patterns missing required fields")
        if not confidence_valid:
            print("  - Some patterns below confidence threshold")
        if not evidence_valid:
            print("  - Some patterns below evidence threshold")
        if not filtering_valid:
            print("  - Tag-based filtering issues")
        return False


def print_pattern_catalog(context):
    """Print catalog of all available patterns."""
    print()
    print("=" * 80)
    print("Available Pattern Catalog")
    print("=" * 80)
    print()

    patterns = context.search_memories(
        tags=["test_recovery"],
        include_session=False
    )

    for i, pattern in enumerate(patterns, 1):
        name = pattern.get("name", "Unknown")
        pattern_type = pattern.get("type", "Unknown")
        confidence = pattern.get("confidence", 0)
        evidence = pattern.get("evidence_count", 0)
        impact = pattern.get("impact", "Unknown")

        print(f"{i}. {name}")
        print(f"   Type: {pattern_type}")
        print(f"   Confidence: {confidence:.3f}")
        print(f"   Evidence: {evidence} occurrences")
        print(f"   Impact: {impact}")
        print(f"   Tags: {', '.join(pattern.get('tags', []))}")
        print()


def main():
    """Main execution."""
    try:
        success = validate_cross_session_retrieval()

        if success:
            # Print pattern catalog
            context = create_agent_context(session_id="catalog_view")
            print_pattern_catalog(context)
            return 0
        else:
            print("\n⚠️  Validation failed - see issues above")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
