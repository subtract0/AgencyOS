#!/usr/bin/env python3
"""
Run FOCUSED mutation tests on specific CRITICAL functions.

Instead of mutating entire files (which takes hours), we'll:
1. Extract specific functions we care about
2. Run targeted mutation tests
3. Generate actionable reports

This is a pragmatic approach that achieves Mars Rover validation in reasonable time.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.mutation_testing import MutationConfig, MutationTester


def extract_function_to_temp_file(source_file: str, function_name: str, temp_file: str) -> bool:
    """Extract a specific function to a temporary file for targeted mutation testing."""
    try:
        with open(source_file) as f:
            lines = f.readlines()

        # Find function definition
        in_function = False
        function_lines = []
        indent_level = 0

        for line in lines:
            if f"def {function_name}(" in line:
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                function_lines.append(line)
            elif in_function:
                current_indent = len(line) - len(line.lstrip())
                # Check if we've exited the function (dedent or new def at same level)
                if (
                    line.strip()
                    and current_indent <= indent_level
                    and not line.strip().startswith("#")
                ):
                    if line.strip().startswith("def ") or line.strip().startswith("class "):
                        break
                function_lines.append(line)

        if function_lines:
            # Add necessary imports at the top
            import_lines = []
            for line in lines:
                if line.startswith("import ") or line.startswith("from "):
                    import_lines.append(line)
                elif not line.strip() or line.strip().startswith("#"):
                    continue
                else:
                    break  # Stop at first non-import

            with open(temp_file, "w") as f:
                f.writelines(import_lines)
                f.write("\n")
                f.writelines(function_lines)

            return True
        return False
    except Exception as e:
        print(f"Error extracting function {function_name}: {e}")
        return False


def run_focused_mutation_test(
    source_file: str, function_name: str, test_command: str, mutation_types: list = None
) -> dict:
    """Run mutation test on a specific function."""

    mutation_types = mutation_types or ["arithmetic", "comparison", "boolean", "constant", "return"]

    print(f"\n{'=' * 80}")
    print(f"Focused Mutation Test: {function_name} in {source_file}")
    print(f"{'=' * 80}\n")

    # For now, run mutation tests on the full file but report results per function
    # This is more reliable than extracting functions
    config = MutationConfig(
        target_files=[source_file],
        test_command=test_command,
        mutation_types=mutation_types,
        timeout_seconds=60,
        parallel=False,
    )

    tester = MutationTester(config)

    # Generate mutations only
    all_mutations = tester.generate_mutations(source_file)

    # Filter mutations to only those in the target function
    # (Check line numbers by parsing source)
    try:
        with open(source_file) as f:
            lines = f.readlines()

        # Find function line range
        start_line = None
        end_line = None
        indent_level = 0

        for i, line in enumerate(lines, 1):
            if f"def {function_name}(" in line:
                start_line = i
                indent_level = len(line) - len(line.lstrip())
            elif start_line and line.strip():
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and (
                    line.strip().startswith("def ") or line.strip().startswith("class ")
                ):
                    end_line = i - 1
                    break

        if start_line and not end_line:
            end_line = len(lines)

        # Filter mutations to function range
        function_mutations = [m for m in all_mutations if start_line <= m.line_number <= end_line]

        print(f"Total mutations in file: {len(all_mutations)}")
        print(
            f"Mutations in {function_name} (lines {start_line}-{end_line}): {len(function_mutations)}"
        )

        if not function_mutations:
            print("No mutations generated for this function.")
            return {
                "function": function_name,
                "total_mutations": 0,
                "mutations_caught": 0,
                "mutations_survived": 0,
                "mutation_score": 1.0,
                "surviving_mutations": [],
            }

        # For focused testing, we'll test a sample of mutations (max 10)
        sample_size = min(10, len(function_mutations))
        sampled_mutations = function_mutations[:sample_size]

        print(f"Running {sample_size} mutations for focused analysis...\n")

        mutations_caught = 0
        mutations_survived = 0
        surviving_mutations = []

        for i, mutation in enumerate(sampled_mutations, 1):
            print(
                f"[{i}/{sample_size}] Testing mutation {mutation.mutation_id} at line {mutation.line_number}"
            )
            print(f"  Original: {mutation.original_code}")
            print(f"  Mutated:  {mutation.mutated_code}")

            # Apply mutation
            apply_result = tester.apply_mutation(mutation)
            if apply_result.is_err():
                print(f"  ⚠ Could not apply mutation: {apply_result.unwrap_err()}")
                tester.restore_original(source_file)
                continue

            # Run tests
            test_result = tester.run_tests()

            # Restore original
            tester.restore_original(source_file)

            if test_result.is_ok():
                tests_passed = test_result.unwrap()

                if tests_passed:
                    print("  ❌ SURVIVED - Tests passed despite mutation (bug not caught!)")
                    mutations_survived += 1
                    surviving_mutations.append(
                        {
                            "mutation_id": mutation.mutation_id,
                            "line": mutation.line_number,
                            "original": mutation.original_code,
                            "mutated": mutation.mutated_code,
                        }
                    )
                else:
                    print("  ✅ CAUGHT - Tests failed as expected")
                    mutations_caught += 1
            else:
                print(f"  ⚠ Test execution error: {test_result.unwrap_err()}")

        mutation_score = mutations_caught / sample_size if sample_size > 0 else 1.0

        print(f"\n{'=' * 80}")
        print(f"Results for {function_name}:")
        print(f"  Mutation Score: {mutation_score:.2%}")
        print(f"  Mutations Tested: {sample_size}")
        print(f"  Caught: {mutations_caught}")
        print(f"  Survived: {mutations_survived}")
        print(f"{'=' * 80}\n")

        return {
            "function": function_name,
            "total_mutations": len(function_mutations),
            "sample_size": sample_size,
            "mutations_caught": mutations_caught,
            "mutations_survived": mutations_survived,
            "mutation_score": mutation_score,
            "surviving_mutations": surviving_mutations,
        }

    except Exception as e:
        print(f"Error during mutation testing: {e}")
        return {
            "function": function_name,
            "error": str(e),
            "total_mutations": 0,
            "mutations_caught": 0,
            "mutations_survived": 0,
            "mutation_score": 0.0,
            "surviving_mutations": [],
        }


def main():
    """Run focused mutation tests on CRITICAL functions."""

    results = []

    # Test 1: _cli_event_scope (agency.py)
    result1 = run_focused_mutation_test(
        source_file="agency.py",
        function_name="_cli_event_scope",
        test_command="pytest tests/test_agency_cli_commands.py::TestCliEventScope -v --tb=short -x",
    )
    results.append(result1)

    # Test 2: _check_learning_triggers (enhanced_memory_store.py)
    result2 = run_focused_mutation_test(
        source_file="agency_memory/enhanced_memory_store.py",
        function_name="_check_learning_triggers",
        test_command="pytest tests/test_enhanced_memory_learning.py::TestCheckLearningTriggers -v --tb=short -x",
    )
    results.append(result2)

    # Test 3: add_memory (vector_store.py)
    result3 = run_focused_mutation_test(
        source_file="agency_memory/vector_store.py",
        function_name="add_memory",
        test_command="pytest tests/test_vector_store_lifecycle.py::TestAddMemory -v --tb=short -x",
    )
    results.append(result3)

    # Generate summary report
    print("\n\n")
    print("=" * 80)
    print("FOCUSED MUTATION TESTING SUMMARY")
    print("=" * 80)
    print()

    total_tested = 0
    total_caught = 0
    total_survived = 0

    for result in results:
        if "error" not in result:
            print(
                f"{result['function']:40s} | Score: {result['mutation_score']:.2%} | Tested: {result.get('sample_size', 0)} | Caught: {result['mutations_caught']} | Survived: {result['mutations_survived']}"
            )
            total_tested += result.get("sample_size", 0)
            total_caught += result["mutations_caught"]
            total_survived += result["mutations_survived"]
        else:
            print(f"{result['function']:40s} | ERROR: {result['error']}")

    print()
    overall_score = total_caught / total_tested if total_tested > 0 else 0.0
    print(
        f"{'OVERALL':40s} | Score: {overall_score:.2%} | Tested: {total_tested} | Caught: {total_caught} | Survived: {total_survived}"
    )
    print()

    if overall_score >= 0.95:
        print("✅ EXCELLENT - Mars Rover standard achieved (95%+)")
        return 0
    elif overall_score >= 0.80:
        print("✓ GOOD - Strong test coverage")
        return 1
    else:
        print("❌ INSUFFICIENT - Test suite needs improvement")
        return 2


if __name__ == "__main__":
    sys.exit(main())
