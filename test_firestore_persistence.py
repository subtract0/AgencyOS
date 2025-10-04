#!/usr/bin/env python3
"""
Quick Firestore Persistence Test
Tests that patterns persist across process restarts
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_write_pattern():
    """Write a test pattern to Firestore."""
    try:
        from pattern_intelligence.coding_pattern import (
            CodingPattern,
            EffectivenessMetric,
            PatternMetadata,
            ProblemContext,
            SolutionApproach,
        )
        from pattern_intelligence.pattern_store import PatternStore

        print("📝 Creating pattern store...")
        store = PatternStore()

        # Create test pattern
        test_pattern = CodingPattern(
            context=ProblemContext(
                description="Trinity Protocol Foundation Test",
                domain="testing",
                constraints=[],
                symptoms=["foundation_test"],
                scale=None,
                urgency="low",
            ),
            solution=SolutionApproach(
                approach="Store test pattern for Trinity launch validation",
                implementation="test_implementation",
                tools=["PatternStore"],
                reasoning="Verify Firestore persistence before Trinity launch",
                code_examples=[],
                dependencies=[],
                alternatives=[],
            ),
            outcome=EffectivenessMetric(
                success_rate=1.0,
                performance_impact=None,
                maintainability_impact=None,
                user_impact=None,
                technical_debt=None,
                adoption_rate=1,
                longevity=None,
                confidence=0.95,
            ),
            metadata=PatternMetadata(
                pattern_id="trinity_launch_test_2025_09_30",
                discovered_timestamp=datetime.now().isoformat(),
                source="firestore_persistence_test",
                discoverer="Trinity Pre-Flight Check",
                last_applied=None,
                application_count=0,
                validation_status="pending",
                tags=["trinity", "foundation_test", "launch_validation"],
                related_patterns=[],
            ),
        )

        print(f"✍️  Storing pattern: {test_pattern.metadata.pattern_id}")
        store.store_pattern(test_pattern)

        print("✅ Pattern stored successfully!")
        print(f"   Pattern ID: {test_pattern.metadata.pattern_id}")
        print(f"   Timestamp: {test_pattern.metadata.discovered_timestamp}")
        print()
        print("🔄 Now kill this process (Ctrl+C) and run again to verify persistence")
        return True

    except Exception as e:
        print(f"❌ Error storing pattern: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_read_pattern():
    """Read the test pattern from Firestore."""
    try:
        from pattern_intelligence.pattern_store import PatternStore

        print("📖 Reading patterns from store...")
        store = PatternStore()

        # Try to find our test pattern
        test_id = "trinity_launch_test_2025_09_30"
        pattern = store.get_pattern_by_id(test_id)

        if pattern:
            print("✅ PASS: Pattern persisted across restart!")
            print(f"   Pattern ID: {pattern.metadata.pattern_id}")
            print(f"   Description: {pattern.context.description}")
            print(f"   Tags: {pattern.metadata.tags}")
            print()
            print("🎉 Firestore persistence verified!")
            return True
        else:
            print("❌ FAIL: Pattern not found after restart")
            print(f"   Expected ID: {test_id}")
            return False

    except Exception as e:
        print(f"❌ Error reading pattern: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test flow."""
    print("=" * 70)
    print("🧪 Trinity Protocol: Firestore Persistence Test")
    print("=" * 70)
    print()

    # Try to read first (in case this is a restart)
    try:
        from pattern_intelligence.pattern_store import PatternStore

        store = PatternStore()
        test_id = "trinity_launch_test_2025_09_30"
        pattern = store.get_pattern_by_id(test_id)

        if pattern:
            print("🔍 Existing pattern found - testing persistence...")
            success = test_read_pattern()
        else:
            print("📝 No existing pattern - writing test pattern...")
            success = test_write_pattern()
    except Exception:
        print("📝 First run - writing test pattern...")
        success = test_write_pattern()

    print()
    print("=" * 70)
    if success:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed")
    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
