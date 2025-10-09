"""
Demo script for ProposalGenerator - EPIC 4.2 Component 4.

Shows how to:
1. Analyze A/B test results from JSONL
2. Generate statistical comparisons
3. Create ADR proposals for agent promotions

Constitutional compliance: Article IV - Learning from data
"""

import json
import tempfile
from pathlib import Path

from meta_learning import ProposalGenerator


def create_sample_benchmark_data() -> Path:
    """Create sample benchmark JSONL data for demo."""
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)

    # Simulate A/B test results
    # Agent v1 (incumbent): Lower performance
    for i in range(5):
        result = {
            "run_id": f"run_v1_{i}",
            "agent_id": "planner_v1",
            "task_id": "task_001",
            "scores": {"aggregate": 0.72 + i * 0.02},  # 0.72 to 0.80
            "duration_s": 15.0 + i * 0.5,
            "cost_usd": 0.15 + i * 0.01,
            "timestamp": "2025-10-09T12:00:00",
            "metadata": {"agent_type": "planner"},
        }
        temp_file.write(json.dumps(result) + "\n")

    # Agent v2 (challenger): Higher performance
    for i in range(5):
        result = {
            "run_id": f"run_v2_{i}",
            "agent_id": "planner_v2_dspy",
            "task_id": "task_001",
            "scores": {"aggregate": 0.88 + i * 0.01},  # 0.88 to 0.92
            "duration_s": 12.0 + i * 0.3,
            "cost_usd": 0.12 + i * 0.005,
            "timestamp": "2025-10-09T12:00:00",
            "metadata": {"agent_type": "planner", "enhanced": "dspy"},
        }
        temp_file.write(json.dumps(result) + "\n")

    temp_file.close()
    return Path(temp_file.name)


def main():
    """Run ProposalGenerator demo."""
    print("=" * 80)
    print("ProposalGenerator Demo - EPIC 4.2 Component 4")
    print("=" * 80)
    print()

    # Step 1: Create sample data
    print("Step 1: Creating sample benchmark data...")
    benchmark_file = create_sample_benchmark_data()
    print(f"Created: {benchmark_file}")
    print()

    # Step 2: Initialize generator
    print("Step 2: Initializing ProposalGenerator...")
    generator = ProposalGenerator(min_samples=3, significance_level=0.05)
    print("✓ Generator ready")
    print()

    # Step 3: Analyze results
    print("Step 3: Analyzing A/B test results...")
    result = generator.analyze_results(benchmark_file)

    if result.is_err():
        print(f"❌ Analysis failed: {result.unwrap_err()}")
        benchmark_file.unlink()
        return

    report = result.unwrap()
    print("✓ Analysis complete")
    print()

    # Step 4: Display results
    print("Step 4: Statistical Analysis Results")
    print("-" * 80)
    print()

    print(f"Challenger: {report.challenger.agent_id}")
    print(
        f"  Mean Score: {report.challenger.mean_score:.3f} (±{report.challenger.std_dev_score:.3f})"
    )
    print(f"  Mean Duration: {report.challenger.mean_duration:.2f}s")
    print(f"  Mean Cost: ${report.challenger.mean_cost:.4f}")
    print(f"  Sample Size: {report.challenger.sample_size}")
    print()

    print(f"Incumbent: {report.incumbent.agent_id}")
    print(
        f"  Mean Score: {report.incumbent.mean_score:.3f} (±{report.incumbent.std_dev_score:.3f})"
    )
    print(f"  Mean Duration: {report.incumbent.mean_duration:.2f}s")
    print(f"  Mean Cost: ${report.incumbent.mean_cost:.4f}")
    print(f"  Sample Size: {report.incumbent.sample_size}")
    print()

    print("Comparison:")
    print(
        f"  Score Improvement: {report.comparison.score_improvement:+.3f} "
        f"({report.comparison.score_improvement * 100:+.1f}%)"
    )
    print(f"  Duration Change: {report.comparison.duration_improvement:+.2f}s")
    print(f"  Cost Change: ${report.comparison.cost_improvement:+.4f}")
    if report.comparison.p_value is not None:
        print(f"  P-value: {report.comparison.p_value:.4f}")
        significance = "✓ Significant" if report.comparison.p_value < 0.05 else "✗ Not significant"
        print(f"  {significance}")
    else:
        print("  P-value: Not available (scipy not installed)")
    print()

    print(f"Recommendation: {report.recommendation}")
    print()

    # Step 5: Generate ADR
    print("Step 5: Generating ADR document...")
    with tempfile.TemporaryDirectory() as tmpdir:
        adr_result = generator.generate_adr(report, output_dir=Path(tmpdir))

        if adr_result.is_err():
            print(f"❌ ADR generation failed: {adr_result.unwrap_err()}")
        else:
            adr_path = adr_result.unwrap()
            print(f"✓ ADR generated: {adr_path.name}")
            print()

            # Display ADR preview
            print("ADR Preview (first 40 lines):")
            print("-" * 80)
            content = adr_path.read_text()
            lines = content.split("\n")
            for i, line in enumerate(lines[:40], start=1):
                print(f"{i:3d}: {line}")

            if len(lines) > 40:
                print(f"\n... ({len(lines) - 40} more lines)")

    # Cleanup
    benchmark_file.unlink()

    print()
    print("=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
