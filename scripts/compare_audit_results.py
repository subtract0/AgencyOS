#!/usr/bin/env python3
"""
Compare Marathon Audit V1 vs V2 Results

Analyzes improvements from calibration and generates detailed comparison report.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

def load_audit_results(json_path: Path) -> List[Dict]:
    """Load audit results from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)

def analyze_priority_distribution(results: List[Dict]) -> Dict[str, int]:
    """Count tests by priority."""
    counts = defaultdict(int)
    for test in results:
        counts[test['healing_priority']] += 1
    return dict(counts)

def analyze_necessary_gaps(results: List[Dict], version: str) -> Dict[str, int]:
    """Count gap frequency across all tests."""
    gap_counts = defaultdict(int)

    for test in results:
        gaps = test['necessary_gaps']
        for gap in gaps:
            gap_counts[gap] += 1

    return dict(gap_counts)

def find_priority_changes(v1_results: List[Dict], v2_results: List[Dict]) -> List[Dict]:
    """Find tests where priority changed from V1 to V2."""
    changes = []

    # Create lookup by test name
    v1_lookup = {test['name']: test for test in v1_results}
    v2_lookup = {test['name']: test for test in v2_results}

    for test_name in v1_lookup:
        if test_name in v2_lookup:
            v1_priority = v1_lookup[test_name]['healing_priority']
            v2_priority = v2_lookup[test_name]['healing_priority']

            if v1_priority != v2_priority:
                changes.append({
                    'test': test_name,
                    'v1_priority': v1_priority,
                    'v2_priority': v2_priority,
                    'file': v1_lookup[test_name]['file'],
                    'line': v1_lookup[test_name]['line_start'],
                    'v1_gaps': len(v1_lookup[test_name]['necessary_gaps']),
                    'v2_gaps': len(v2_lookup[test_name]['necessary_gaps']),
                    'v2_applicable': len(v2_lookup[test_name].get('applicable_categories', [])),
                })

    return changes

def calculate_false_gap_reduction(v1_results: List[Dict], v2_results: List[Dict]) -> Dict:
    """Calculate reduction in false gaps from applicability filtering."""
    # Focus on Accessibility and Year-round (known false gaps)
    false_gap_categories = ['Accessibility', 'Year-round', 'Cascading', 'Security']

    v1_false_gaps = 0
    v2_false_gaps = 0
    v2_prevented = 0

    v1_lookup = {test['name']: test for test in v1_results}
    v2_lookup = {test['name']: test for test in v2_results}

    for test_name in v1_lookup:
        if test_name in v2_lookup:
            v1_gaps = set(v1_lookup[test_name]['necessary_gaps'])
            v2_gaps = set(v2_lookup[test_name]['necessary_gaps'])
            v2_applicable = set(v2_lookup[test_name].get('applicable_categories', []))

            # V1 false gaps: gaps that were in V1 but not in V2's applicable set
            for cat in false_gap_categories:
                if cat in v1_gaps:
                    v1_false_gaps += 1
                    if cat not in v2_applicable:
                        # This gap was prevented by applicability filter
                        v2_prevented += 1
                    elif cat in v2_gaps:
                        # Still a gap in V2 (actually applicable)
                        v2_false_gaps += 1

    return {
        'v1_false_gaps': v1_false_gaps,
        'v2_false_gaps': v2_false_gaps,
        'prevented': v2_prevented,
        'reduction_pct': ((v1_false_gaps - v2_false_gaps) / v1_false_gaps * 100) if v1_false_gaps > 0 else 0
    }

def generate_comparison_report(v1_path: Path, v2_path: Path, output_path: Path):
    """Generate comprehensive V1 vs V2 comparison report."""

    print(f"Loading V1 results from {v1_path}...")
    v1_results = load_audit_results(v1_path)

    print(f"Loading V2 results from {v2_path}...")
    v2_results = load_audit_results(v2_path)

    # Verify same test count
    if len(v1_results) != len(v2_results):
        print(f"⚠️  Warning: Different test counts (V1: {len(v1_results)}, V2: {len(v2_results)})")

    total = len(v1_results)

    # Analyze distributions
    v1_priorities = analyze_priority_distribution(v1_results)
    v2_priorities = analyze_priority_distribution(v2_results)

    v1_gaps = analyze_necessary_gaps(v1_results, "V1")
    v2_gaps = analyze_necessary_gaps(v2_results, "V2")

    # Find changes
    priority_changes = find_priority_changes(v1_results, v2_results)

    # Calculate false gap reduction
    false_gap_analysis = calculate_false_gap_reduction(v1_results, v2_results)

    # Generate report
    with open(output_path, 'w') as f:
        f.write("# Marathon Audit V1 vs V2 - Detailed Comparison\n\n")
        f.write(f"**V1 Source**: {v1_path.name}\n")
        f.write(f"**V2 Source**: {v2_path.name}\n")
        f.write(f"**Tests Compared**: {total}\n\n")

        # Priority Distribution
        f.write("## 1. Priority Distribution Comparison\n\n")
        f.write("| Priority | V1 Count | V1 % | V2 Count | V2 % | Change | Assessment |\n")
        f.write("|----------|----------|------|----------|------|--------|------------|\n")

        for priority in ['P0', 'P1', 'P2', 'P3']:
            v1_count = v1_priorities.get(priority, 0)
            v2_count = v2_priorities.get(priority, 0)
            v1_pct = (v1_count / total * 100) if total > 0 else 0
            v2_pct = (v2_count / total * 100) if total > 0 else 0
            delta = v2_pct - v1_pct

            if priority == 'P1':
                if v2_pct < 20:
                    assessment = "✅ EXCELLENT"
                elif v2_pct < 30:
                    assessment = "✅ GOOD"
                elif v2_pct < 50:
                    assessment = "⚠️ FAIR"
                else:
                    assessment = "❌ POOR"
            else:
                assessment = "—"

            f.write(f"| {priority} | {v1_count} | {v1_pct:.1f}% | {v2_count} | {v2_pct:.1f}% | {delta:+.1f}% | {assessment} |\n")

        # Key Metrics
        f.write("\n### Key Improvements\n\n")
        p1_reduction_pct = ((v1_priorities.get('P1', 0) - v2_priorities.get('P1', 0)) /
                           v1_priorities.get('P1', 1)) * 100
        f.write(f"- **P1 Reduction**: {v1_priorities.get('P1', 0)} → {v2_priorities.get('P1', 0)} "
               f"({p1_reduction_pct:.1f}% reduction)\n")
        f.write(f"- **P2 Increase**: {v1_priorities.get('P2', 0)} → {v2_priorities.get('P2', 0)} "
               f"(better classification)\n")
        f.write(f"- **P3 Introduced**: {v2_priorities.get('P3', 0)} tests (cosmetic issues)\n\n")

        # False Gap Reduction
        f.write("## 2. False Gap Reduction Analysis\n\n")
        f.write(f"**Total False Gaps Prevented**: {false_gap_analysis['prevented']}\n\n")
        f.write(f"- V1 False Gaps (Accessibility, Year-round, etc.): {false_gap_analysis['v1_false_gaps']}\n")
        f.write(f"- V2 False Gaps (after applicability filter): {false_gap_analysis['v2_false_gaps']}\n")
        f.write(f"- **Reduction**: {false_gap_analysis['reduction_pct']:.1f}%\n\n")

        # NECESSARY Gap Comparison
        f.write("## 3. NECESSARY Gap Frequency Comparison\n\n")
        f.write("| Category | V1 Gaps | V1 % | V2 Gaps | V2 % | Reduction | Impact |\n")
        f.write("|----------|---------|------|---------|------|-----------|--------|\n")

        necessary_categories = ['Normal', 'Edge', 'Cascading', 'Essential', 'Security',
                               'Spec', 'Accessibility', 'Resilience', 'Year-round']

        for cat in necessary_categories:
            v1_count = v1_gaps.get(cat, 0)
            v2_count = v2_gaps.get(cat, 0)
            v1_pct = (v1_count / total * 100) if total > 0 else 0
            v2_pct = (v2_count / total * 100) if total > 0 else 0
            reduction = v1_count - v2_count
            reduction_pct = (reduction / v1_count * 100) if v1_count > 0 else 0

            if cat in ['Accessibility', 'Year-round']:
                impact = "🎯 MAJOR" if reduction_pct > 50 else "✅ Good"
            elif cat in ['Cascading', 'Security']:
                impact = "✅ Good" if reduction_pct > 20 else "⚠️ Minor"
            else:
                impact = "—"

            f.write(f"| {cat} | {v1_count} | {v1_pct:.1f}% | {v2_count} | {v2_pct:.1f}% | "
                   f"{reduction} ({reduction_pct:.1f}%) | {impact} |\n")

        # Priority Changes Detail
        f.write("\n## 4. Individual Test Priority Changes\n\n")
        f.write(f"**Total Tests with Priority Changes**: {len(priority_changes)}\n\n")

        # Group by change type
        p1_to_p2 = [c for c in priority_changes if c['v1_priority'] == 'P1' and c['v2_priority'] == 'P2']
        p1_to_p3 = [c for c in priority_changes if c['v1_priority'] == 'P1' and c['v2_priority'] == 'P3']
        p2_to_p1 = [c for c in priority_changes if c['v1_priority'] == 'P2' and c['v2_priority'] == 'P1']

        f.write(f"### P1 → P2 Recalibrations ({len(p1_to_p2)} tests)\n\n")
        for change in p1_to_p2[:10]:  # Top 10
            f.write(f"- `{change['test']}` ({change['file']}:{change['line']})\n")
            f.write(f"  - V1: {change['v1_gaps']} gaps, V2: {change['v2_gaps']}/{change['v2_applicable']} applicable\n")

        f.write(f"\n### P1 → P3 Recalibrations ({len(p1_to_p3)} tests)\n\n")
        for change in p1_to_p3[:10]:  # Top 10
            f.write(f"- `{change['test']}` ({change['file']}:{change['line']})\n")
            f.write(f"  - V1: {change['v1_gaps']} gaps, V2: {change['v2_gaps']}/{change['v2_applicable']} applicable (cosmetic only)\n")

        f.write(f"\n### P2 → P1 Escalations ({len(p2_to_p1)} tests)\n\n")
        if p2_to_p1:
            for change in p2_to_p1[:10]:
                f.write(f"- `{change['test']}` ({change['file']}:{change['line']})\n")
                f.write(f"  - V2 detected missing core categories from applicable set\n")
        else:
            f.write("✅ No tests escalated (good calibration)\n")

        # Recommendations
        f.write("\n## 5. Recommendations\n\n")
        p1_pct_v2 = (v2_priorities.get('P1', 0) / total * 100) if total > 0 else 0

        if p1_pct_v2 < 20:
            f.write("✅ **V2 calibration is EXCELLENT** (P1: {:.1f}% < 20% target)\n\n".format(p1_pct_v2))
            f.write("**Next Steps**:\n")
            f.write("1. Focus on the {} P1 items (all high-quality gaps)\n".format(v2_priorities.get('P1', 0)))
            f.write("2. Validate top 5 P1 issues manually (spot check)\n")
            f.write("3. Scale V2 to full 5,408 test suite\n")
        elif p1_pct_v2 < 30:
            f.write("✅ **V2 calibration is GOOD** (P1: {:.1f}% < 30%)\n\n".format(p1_pct_v2))
            f.write("**Next Steps**:\n")
            f.write("1. Manual review of P1 items to identify remaining false positives\n")
            f.write("2. Fine-tune applicability filter (may need test-type specific logic)\n")
            f.write("3. Consider running on larger sample (500 tests)\n")
        else:
            f.write("⚠️ **V2 needs further tuning** (P1: {:.1f}% still high)\n\n".format(p1_pct_v2))
            f.write("**Recommendations**:\n")
            f.write("1. Review recalibration logic (may be too lenient)\n")
            f.write("2. Add more specific applicability rules\n")
            f.write("3. Consider test-name pattern matching for test type\n")

        # Summary
        f.write("\n## Summary\n\n")
        f.write(f"V2 improvements successfully reduced:\n")
        f.write(f"- P1 inflation by {p1_reduction_pct:.1f}%\n")
        f.write(f"- False gaps by {false_gap_analysis['reduction_pct']:.1f}%\n")
        f.write(f"- Accessibility gaps by {((v1_gaps.get('Accessibility', 0) - v2_gaps.get('Accessibility', 0)) / v1_gaps.get('Accessibility', 1) * 100):.1f}%\n")
        f.write(f"- Year-round gaps by {((v1_gaps.get('Year-round', 0) - v2_gaps.get('Year-round', 0)) / v1_gaps.get('Year-round', 1) * 100):.1f}%\n\n")

        f.write("**Overall Assessment**: ")
        if p1_pct_v2 < 20 and false_gap_analysis['reduction_pct'] > 50:
            f.write("🎯 **EXCELLENT** - V2 is production-ready\n")
        elif p1_pct_v2 < 30 and false_gap_analysis['reduction_pct'] > 40:
            f.write("✅ **GOOD** - V2 is ready for larger sample validation\n")
        else:
            f.write("⚠️ **NEEDS TUNING** - Further calibration recommended\n")

    print(f"\n✅ Comparison report generated: {output_path}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python compare_audit_results.py <v1.json> <v2.json> <output.md>")
        sys.exit(1)

    v1_path = Path(sys.argv[1])
    v2_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    if not v1_path.exists():
        print(f"Error: V1 file not found: {v1_path}")
        sys.exit(1)

    if not v2_path.exists():
        print(f"Error: V2 file not found: {v2_path}")
        sys.exit(1)

    generate_comparison_report(v1_path, v2_path, output_path)

if __name__ == "__main__":
    main()
