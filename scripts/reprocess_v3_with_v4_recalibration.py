#!/usr/bin/env python3
"""
Re-process V3 results with V4 recalibration logic.

This is faster than re-running the full audit since we already have
gap detection from qwen3-coder. We just apply V4's improved recalibration.
"""

import json
from pathlib import Path
from datetime import datetime

def v4_recalibrate_priority(test_analysis: dict) -> str:
    """
    V4 recalibration logic (copied from marathon_test_audit_v4.py).

    V4 Changes from V3:
    1. Focused tests: IGNORE all non-focal gaps (P3 if focal category covered)
    2. General tests: STRICTER threshold (1+ missing core → P1, not 2+)
    """
    applicable_gaps = [gap for gap in test_analysis['necessary_gaps']
                      if gap in test_analysis['applicable_categories']]

    # P0: Manual flag only
    if any(keyword in test_analysis['name'].upper() for keyword in ['CRITICAL', 'BROKEN', 'FAILING']):
        return 'P0'

    # V4: Ground truth-aligned logic
    test_purpose = test_analysis.get('test_purpose', 'general')

    if test_purpose.startswith('focused_'):
        # Focused tests: VERY LENIENT (ignore all non-focal gaps)
        focal_map = {
            'focused_security': 'Security',
            'focused_validation': 'Spec',
            'focused_error': 'Resilience',
            'focused_accessibility': 'Accessibility',
            'focused_edge': 'Edge',
            'focused_resilience': 'Resilience',
        }
        focal_category = focal_map.get(test_purpose)

        # P1: Only if missing the FOCAL category it claims to test
        if focal_category and focal_category in applicable_gaps:
            return 'P1'  # Test doesn't test what it says it tests

        # V4 CHANGE: Ignore all non-focal gaps for focused tests
        # Focused tests get P3 if they cover their focal category
        return 'P3'

    else:
        # General tests: STRICTER (V4 change: 1+ missing core → P1)
        core_categories = {'Normal', 'Edge', 'Essential', 'Spec'}
        applicable_core = core_categories & set(test_analysis['applicable_categories'])
        missing_core = set(applicable_gaps) & applicable_core

        # V4 CHANGE: P1 if missing 1+ core categories (was 2+ in V3)
        if len(missing_core) >= 1:
            return 'P1'

        # P2: Missing non-core categories only
        if len(applicable_gaps) > 0:
            return 'P2'

        # P3: No gaps
        return 'P3'

def main():
    # Load V3 results
    v3_path = Path("audit_reports/marathon_audit_v3_20251023_170855.json")
    with open(v3_path, 'r') as f:
        v3_data = json.load(f)

    v3_results = v3_data.get('results', v3_data)
    print(f"Loaded {len(v3_results)} V3 results")

    # Re-process with V4 recalibration
    v4_results = []
    priority_changes = 0

    for test in v3_results:
        v4_priority = v4_recalibrate_priority(test)
        v3_priority = test['healing_priority']

        if v4_priority != v3_priority:
            priority_changes += 1

        # Create V4 result (copy V3 data, update priority)
        v4_test = test.copy()
        v4_test['healing_priority'] = v4_priority
        v4_results.append(v4_test)

    print(f"Priority changes: {priority_changes}/{len(v3_results)} ({priority_changes*100/len(v3_results):.1f}%)")

    # Count V4 priorities
    from collections import Counter
    v4_priorities = Counter(t['healing_priority'] for t in v4_results)
    print(f"\nV4 Priority Distribution:")
    for p in ['P0', 'P1', 'P2', 'P3']:
        count = v4_priorities.get(p, 0)
        pct = count * 100 / len(v4_results)
        print(f"  {p}: {count:3d} ({pct:5.1f}%)")

    # Save V4 results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = Path(f"audit_reports/marathon_audit_v4_reprocessed_{timestamp}.json")

    v4_data = {
        "tests_analyzed": len(v4_results),
        "total_tests": 100,
        "execution_time_minutes": 0.1,  # Instant reprocessing
        "version": "V4-reprocessed",
        "source": "V3 results with V4 recalibration",
        "timestamp": timestamp,
        "results": v4_results
    }

    with open(output_path, 'w') as f:
        json.dump(v4_data, f, indent=2)

    print(f"\n✅ Saved V4 reprocessed results: {output_path}")
    print("\nNext step:")
    print("  python scripts/validate_v3_against_ground_truth.py")
    print("  (Update script to use V4 file)")

if __name__ == "__main__":
    main()
