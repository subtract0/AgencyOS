#!/usr/bin/env python3
"""
Run mutation tests on CRITICAL modules.

This script executes mutation testing on the following CRITICAL functions:
1. agency.py: _cli_event_scope, _cmd_run, _cmd_health, _check_test_status, _cmd_dashboard, _cmd_kanban
2. enhanced_memory_store.py: _check_learning_triggers, optimize_vector_store, export_for_learning
3. vector_store.py: add_memory, search, remove_memory, get_stats

Target: 95%+ mutation score (Mars Rover standard)
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.mutation_testing import MutationConfig, MutationTester


def run_mutation_tests():
    """Execute mutation tests on CRITICAL modules."""

    results = {}

    # Test 1: agency.py (CLI commands)
    print("=" * 80)
    print("MUTATION TEST 1/3: agency.py (CLI Commands)")
    print("=" * 80)

    config_agency = MutationConfig(
        target_files=["agency.py"],
        test_command="pytest tests/test_agency_cli_commands.py -v --tb=short -x",
        mutation_types=["arithmetic", "comparison", "boolean", "constant", "return"],
        timeout_seconds=120,
        parallel=False
    )

    tester_agency = MutationTester(config_agency)
    result_agency = tester_agency.run()

    if result_agency.is_ok():
        score_agency = result_agency.unwrap()
        results["agency.py"] = score_agency
        print(tester_agency.generate_report(score_agency))
    else:
        print(f"ERROR: {result_agency.unwrap_err()}")
        results["agency.py"] = None

    # Test 2: enhanced_memory_store.py (Learning functions)
    print("\n" * 2)
    print("=" * 80)
    print("MUTATION TEST 2/3: enhanced_memory_store.py (Learning Functions)")
    print("=" * 80)

    config_memory = MutationConfig(
        target_files=["agency_memory/enhanced_memory_store.py"],
        test_command="pytest tests/test_enhanced_memory_learning.py -v --tb=short -x",
        mutation_types=["arithmetic", "comparison", "boolean", "constant", "return"],
        timeout_seconds=120,
        parallel=False
    )

    tester_memory = MutationTester(config_memory)
    result_memory = tester_memory.run()

    if result_memory.is_ok():
        score_memory = result_memory.unwrap()
        results["enhanced_memory_store.py"] = score_memory
        print(tester_memory.generate_report(score_memory))
    else:
        print(f"ERROR: {result_memory.unwrap_err()}")
        results["enhanced_memory_store.py"] = None

    # Test 3: vector_store.py (VectorStore lifecycle)
    print("\n" * 2)
    print("=" * 80)
    print("MUTATION TEST 3/3: vector_store.py (VectorStore Lifecycle)")
    print("=" * 80)

    config_vector = MutationConfig(
        target_files=["agency_memory/vector_store.py"],
        test_command="pytest tests/test_vector_store_lifecycle.py -v --tb=short -x",
        mutation_types=["arithmetic", "comparison", "boolean", "constant", "return"],
        timeout_seconds=120,
        parallel=False
    )

    tester_vector = MutationTester(config_vector)
    result_vector = tester_vector.run()

    if result_vector.is_ok():
        score_vector = result_vector.unwrap()
        results["vector_store.py"] = score_vector
        print(tester_vector.generate_report(score_vector))
    else:
        print(f"ERROR: {result_vector.unwrap_err()}")
        results["vector_store.py"] = None

    # Generate overall summary
    print("\n" * 2)
    print("=" * 80)
    print("OVERALL MUTATION TESTING SUMMARY")
    print("=" * 80)
    print()

    total_mutations = 0
    total_caught = 0
    total_survived = 0

    for module, score in results.items():
        if score:
            print(f"{module:40s} | Score: {score.mutation_score:.2%} | Mutations: {score.total_mutations} | Caught: {score.mutations_caught} | Survived: {score.mutations_survived}")
            total_mutations += score.total_mutations
            total_caught += score.mutations_caught
            total_survived += score.mutations_survived
        else:
            print(f"{module:40s} | ERROR: Failed to run mutation tests")

    print()
    print(f"{'TOTAL':40s} | Score: {total_caught/total_mutations:.2%} | Mutations: {total_mutations} | Caught: {total_caught} | Survived: {total_survived}")
    print()

    overall_score = total_caught / total_mutations if total_mutations > 0 else 0.0

    if overall_score >= 0.95:
        print("✅ EXCELLENT - Mars Rover standard achieved (95%+)")
        return 0
    elif overall_score >= 0.80:
        print("✓ GOOD - Strong test coverage, but below Mars Rover standard")
        return 1
    else:
        print("❌ INSUFFICIENT - Test suite inadequate for critical systems")
        return 2


if __name__ == "__main__":
    sys.exit(run_mutation_tests())
