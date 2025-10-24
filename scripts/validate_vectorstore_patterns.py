#!/usr/bin/env python3
"""
VectorStore Pattern Validation Script

Validates the 8 test recovery patterns stored during the test suite recovery mission.
Verifies queryability, metadata structure, confidence scores, and tags.

Constitutional Compliance:
- Article IV: Query VectorStore to validate institutional learning
- Article I: Complete context with retry logic
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.agent_context import create_agent_context


def validate_pattern_structure(pattern: dict[str, Any]) -> list[str]:
    """
    Validate a single pattern's structure and metadata.

    Args:
        pattern: Pattern dictionary from VectorStore

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check required fields
    required_fields = ["content", "tags", "metadata"]
    for field in required_fields:
        if field not in pattern:
            errors.append(f"Missing required field: {field}")

    if not errors:
        # Validate content structure
        content = pattern.get("content", {})
        if not isinstance(content, dict):
            errors.append(f"Content must be dict, got {type(content)}")

        # Validate tags
        tags = pattern.get("tags", [])
        if not isinstance(tags, list):
            errors.append(f"Tags must be list, got {type(tags)}")
        elif "test_recovery" not in tags:
            errors.append("Missing 'test_recovery' tag")
        elif "pattern" not in tags:
            errors.append("Missing 'pattern' tag")

        # Validate metadata
        metadata = pattern.get("metadata", {})
        if not isinstance(metadata, dict):
            errors.append(f"Metadata must be dict, got {type(metadata)}")
        else:
            # Check confidence score
            confidence = metadata.get("confidence")
            if confidence is None:
                errors.append("Missing confidence score in metadata")
            elif not isinstance(confidence, (int, float)):
                errors.append(f"Confidence must be numeric, got {type(confidence)}")
            elif confidence < 0.6:
                errors.append(f"Confidence {confidence} below threshold 0.6")

            # Check timestamp
            timestamp = metadata.get("timestamp")
            if not timestamp:
                errors.append("Missing timestamp in metadata")

    return errors


async def validate_vectorstore_patterns() -> dict[str, Any]:
    """
    Query and validate all test recovery patterns in VectorStore.

    Returns:
        Validation report dictionary
    """
    print("=" * 80)
    print("VectorStore Pattern Validation Script")
    print("=" * 80)
    print()

    # Create agent context for VectorStore access
    context = create_agent_context(
        session_id=f"vectorstore_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    print("Step 1: Query VectorStore for test recovery patterns")
    print("-" * 80)

    # Query patterns with retry logic (Article I: Complete context)
    max_retries = 3
    patterns = []

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}...")
            patterns = context.search_memories(
                tags=["test_recovery", "pattern"],
                include_session=False  # Cross-session patterns
            )
            print(f"✓ Query successful: Found {len(patterns)} patterns")
            break
        except Exception as e:
            print(f"✗ Query failed: {e}")
            if attempt < max_retries - 1:
                print("  Retrying...")
                await asyncio.sleep(1)
            else:
                print("  Max retries reached")
                return {
                    "success": False,
                    "error": str(e),
                    "patterns_found": 0
                }

    print()
    print("Step 2: Validate pattern count")
    print("-" * 80)

    expected_count = 8
    actual_count = len(patterns)
    count_valid = actual_count == expected_count

    print(f"Expected patterns: {expected_count}")
    print(f"Actual patterns:   {actual_count}")
    print(f"Status: {'✓ PASS' if count_valid else '✗ FAIL'}")
    print()

    print("Step 3: Validate individual patterns")
    print("-" * 80)

    validation_results = []
    total_errors = 0

    for idx, pattern in enumerate(patterns, 1):
        print(f"\nPattern {idx}/{actual_count}:")

        # Extract pattern name/description
        content = pattern.get("content", {})
        pattern_name = content.get("pattern_type", "Unknown")
        print(f"  Name: {pattern_name}")

        # Validate structure
        errors = validate_pattern_structure(pattern)

        if not errors:
            print(f"  Status: ✓ VALID")

            # Show metadata details
            metadata = pattern.get("metadata", {})
            confidence = metadata.get("confidence", 0)
            timestamp = metadata.get("timestamp", "N/A")
            tags = pattern.get("tags", [])

            print(f"  Confidence: {confidence:.2f}")
            print(f"  Timestamp: {timestamp}")
            print(f"  Tags: {', '.join(tags)}")

            validation_results.append({
                "pattern_name": pattern_name,
                "valid": True,
                "confidence": confidence,
                "tags": tags
            })
        else:
            print(f"  Status: ✗ INVALID")
            for error in errors:
                print(f"    - {error}")
            total_errors += len(errors)

            validation_results.append({
                "pattern_name": pattern_name,
                "valid": False,
                "errors": errors
            })

    print()
    print("=" * 80)
    print("Validation Summary")
    print("=" * 80)
    print(f"Total patterns queried: {actual_count}")
    print(f"Expected patterns: {expected_count}")
    print(f"Count validation: {'✓ PASS' if count_valid else '✗ FAIL'}")
    print()

    valid_patterns = sum(1 for r in validation_results if r.get("valid", False))
    print(f"Valid patterns: {valid_patterns}/{actual_count}")
    print(f"Invalid patterns: {actual_count - valid_patterns}")
    print(f"Total validation errors: {total_errors}")
    print()

    # Overall status
    overall_success = count_valid and total_errors == 0
    print(f"Overall Status: {'✓ PASS' if overall_success else '✗ FAIL'}")
    print()

    if overall_success:
        print("🎉 All test recovery patterns are properly stored and queryable!")
    else:
        print("⚠️  Issues detected - patterns may need re-extraction")

    # Return detailed report
    return {
        "success": overall_success,
        "patterns_found": actual_count,
        "expected_patterns": expected_count,
        "count_valid": count_valid,
        "valid_patterns": valid_patterns,
        "invalid_patterns": actual_count - valid_patterns,
        "total_errors": total_errors,
        "validation_results": validation_results,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Main entry point."""
    try:
        report = asyncio.run(validate_vectorstore_patterns())

        # Exit with appropriate code
        sys.exit(0 if report.get("success", False) else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
