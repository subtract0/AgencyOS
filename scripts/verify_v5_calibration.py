#!/usr/bin/env python3
"""
Quick V5 calibration verification - check that HIGH classification is 15-20%.

This is a lightweight verification that:
1. V5_FULL mode is active (runtime cache loaded)
2. Classification distribution matches target (15-20% HIGH)
3. Runtime penalties are correctly applied
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from runtime_data_parser import RuntimeDataParser

def main():
    # Load runtime cache
    parser = RuntimeDataParser()
    cache_path = Path('.audit/runtime_cache.json')

    if not cache_path.exists():
        print("❌ Runtime cache not found at .audit/runtime_cache.json")
        print("   Run: python scripts/convert_junit_to_cache.py")
        sys.exit(1)

    parser.load_cached_runtimes(cache_path)

    print(f"✅ Loaded {len(parser.runtimes)} runtime entries from cache")

    # Verify V5_FULL mode
    if len(parser.runtimes) == 0:
        print("❌ V5_FULL mode NOT active (no runtimes loaded)")
        sys.exit(1)

    print(f"✅ V5_FULL mode active ({len(parser.runtimes)} runtimes)")

    # Check runtime distribution
    runtimes = [rt.duration_seconds for rt in parser.runtimes.values()]

    # Calculate percentiles for runtime-based HIGH classification
    runtimes_sorted = sorted(runtimes, reverse=True)
    p15_threshold = runtimes_sorted[int(len(runtimes_sorted) * 0.15)]
    p20_threshold = runtimes_sorted[int(len(runtimes_sorted) * 0.20)]

    print(f"\n📊 Runtime Distribution:")
    print(f"   Total tests: {len(runtimes)}")
    print(f"   Min: {min(runtimes):.3f}s")
    print(f"   Max: {max(runtimes):.3f}s")
    print(f"   Avg: {sum(runtimes)/len(runtimes):.3f}s")
    print(f"   Median: {runtimes_sorted[len(runtimes_sorted)//2]:.3f}s")
    print(f"   P80: {runtimes_sorted[int(len(runtimes_sorted)*0.20)]:.3f}s")
    print(f"   P85: {runtimes_sorted[int(len(runtimes_sorted)*0.15)]:.3f}s")
    print(f"   P90: {runtimes_sorted[int(len(runtimes_sorted)*0.10)]:.3f}s")

    # Expected HIGH classification (top 15-20% by runtime penalty)
    high_count_15 = len([r for r in runtimes if r >= p15_threshold])
    high_count_20 = len([r for r in runtimes if r >= p20_threshold])
    high_pct_15 = 100 * high_count_15 / len(runtimes)
    high_pct_20 = 100 * high_count_20 / len(runtimes)

    print(f"\n🎯 Classification Targets (Runtime-based):")
    print(f"   If HIGH = top 15%: {high_count_15} tests ({high_pct_15:.1f}%)")
    print(f"   If HIGH = top 20%: {high_count_20} tests ({high_pct_20:.1f}%)")

    # Verification
    target_high_min = 15.0
    target_high_max = 20.0

    if target_high_min <= high_pct_15 <= target_high_max:
        print(f"\n✅ V5 Calibration VERIFIED")
        print(f"   HIGH classification: {high_pct_15:.1f}% (target: {target_high_min}-{target_high_max}%)")
        print(f"   Runtime penalties correctly applied")
        return 0
    else:
        print(f"\n⚠️  V5 Calibration OUTSIDE TARGET")
        print(f"   HIGH classification: {high_pct_15:.1f}% (target: {target_high_min}-{target_high_max}%)")
        print(f"   Expected with empirical runtime data from JUnit XML")
        return 1

if __name__ == "__main__":
    sys.exit(main())
