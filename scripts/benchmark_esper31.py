#!/usr/bin/env python3
"""
Benchmark Esper3.1 with and without QLoRA adapters.

Tests:
1. Algorithm tasks (from test set) - expect improvement
2. General coding tasks - expect no degradation
3. DevOps tasks - expect no degradation

Usage:
    # Before training (save baseline)
    python scripts/benchmark_esper31.py --save-baseline

    # After training (compare)
    python scripts/benchmark_esper31.py --with-adapters --compare-to-baseline
"""
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import argparse


@dataclass
class TestCase:
    """Single test case."""
    category: str  # "algorithm", "coding", "devops"
    prompt: str
    expected_keywords: List[str]  # Keywords we expect in a good response
    difficulty: str  # "easy", "medium", "hard"


@dataclass
class BenchmarkResult:
    """Result from running a test case."""
    test_id: str
    category: str
    difficulty: str
    prompt: str
    response: str
    response_time: float
    contains_expected_keywords: int  # Number of expected keywords found
    total_expected_keywords: int
    score: float  # 0.0 to 1.0


def get_test_cases() -> List[TestCase]:
    """Get benchmark test cases."""
    return [
        # Algorithm tasks (expect improvement with adapters)
        TestCase(
            category="algorithm",
            prompt="Find the shortest path from A to C in graph: A-B:3, B-C:2, A-C:8",
            expected_keywords=["A", "B", "C", "5", "path", "shortest"],
            difficulty="medium"
        ),
        TestCase(
            category="algorithm",
            prompt="Detect if there's a cycle in this directed graph: A->B, B->C, C->A",
            expected_keywords=["cycle", "A", "B", "C", "detected", "exists"],
            difficulty="easy"
        ),
        TestCase(
            category="algorithm",
            prompt="Perform topological sort on: A->B, A->C, B->D, C->D",
            expected_keywords=["topological", "A", "B", "C", "D", "order"],
            difficulty="medium"
        ),
        TestCase(
            category="algorithm",
            prompt="Solve the knapsack problem: items [(5,10), (4,40), (6,30), (3,50)], capacity=10",
            expected_keywords=["knapsack", "90", "value", "items", "optimal"],
            difficulty="hard"
        ),
        TestCase(
            category="algorithm",
            prompt="Check if binary tree is balanced: root=3, left=9, right=20(15,7)",
            expected_keywords=["balanced", "height", "tree", "yes", "true"],
            difficulty="medium"
        ),

        # General coding tasks (expect no degradation)
        TestCase(
            category="coding",
            prompt="Write a Python function to validate email addresses using regex",
            expected_keywords=["import re", "def", "email", "@", "match"],
            difficulty="easy"
        ),
        TestCase(
            category="coding",
            prompt="Implement a simple LRU cache in Python",
            expected_keywords=["class", "LRU", "dict", "get", "put", "capacity"],
            difficulty="medium"
        ),
        TestCase(
            category="coding",
            prompt="Create a decorator that times function execution",
            expected_keywords=["def", "decorator", "time", "import time", "wraps"],
            difficulty="medium"
        ),
        TestCase(
            category="coding",
            prompt="Write a context manager for database connections",
            expected_keywords=["class", "__enter__", "__exit__", "connection", "with"],
            difficulty="medium"
        ),
        TestCase(
            category="coding",
            prompt="Implement async/await pattern for file reading",
            expected_keywords=["async", "await", "async def", "file", "aiofiles"],
            difficulty="hard"
        ),

        # DevOps tasks (expect no degradation)
        TestCase(
            category="devops",
            prompt="Write a Dockerfile for a Python FastAPI application",
            expected_keywords=["FROM", "python", "COPY", "RUN", "CMD", "fastapi"],
            difficulty="easy"
        ),
        TestCase(
            category="devops",
            prompt="Create a docker-compose.yml for app + postgres + redis",
            expected_keywords=["version", "services", "postgres", "redis", "depends_on"],
            difficulty="medium"
        ),
        TestCase(
            category="devops",
            prompt="Write a GitHub Actions workflow for pytest + coverage",
            expected_keywords=["on:", "runs-on", "pytest", "coverage", "steps"],
            difficulty="medium"
        ),
        TestCase(
            category="devops",
            prompt="Create a Kubernetes deployment for 3 replicas with health checks",
            expected_keywords=["apiVersion", "Deployment", "replicas: 3", "livenessProbe", "readinessProbe"],
            difficulty="hard"
        ),
        TestCase(
            category="devops",
            prompt="Write a bash script to monitor disk usage and send alerts",
            expected_keywords=["#!/bin/bash", "df", "disk", "usage", "alert", "if"],
            difficulty="easy"
        ),
    ]


def run_test_ollama(prompt: str, model: str = "gpt-oss:20b") -> tuple[str, float]:
    """
    Run test using Ollama.

    Args:
        prompt: Test prompt
        model: Ollama model name

    Returns:
        (response_text, response_time_seconds)
    """
    import subprocess

    start = time.time()
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        elapsed = time.time() - start
        return result.stdout.strip(), elapsed
    except Exception as e:
        return f"ERROR: {e}", time.time() - start


def score_response(response: str, expected_keywords: List[str]) -> tuple[int, float]:
    """
    Score response based on expected keywords.

    Returns:
        (num_keywords_found, score_0_to_1)
    """
    response_lower = response.lower()
    found = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
    score = found / len(expected_keywords) if expected_keywords else 0.0
    return found, score


def run_benchmark(
    model: str = "gpt-oss:20b",
    save_path: Optional[Path] = None
) -> List[BenchmarkResult]:
    """
    Run full benchmark.

    Args:
        model: Ollama model name
        save_path: If provided, save results to this path

    Returns:
        List of benchmark results
    """
    print(f"\n{'='*70}")
    print(f"BENCHMARKING: {model}")
    print(f"{'='*70}\n")

    test_cases = get_test_cases()
    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {test.category.upper()} - {test.difficulty}")
        print(f"Prompt: {test.prompt[:60]}...")

        response, response_time = run_test_ollama(test.prompt, model)
        found, score = score_response(response, test.expected_keywords)

        result = BenchmarkResult(
            test_id=f"{test.category}_{i}",
            category=test.category,
            difficulty=test.difficulty,
            prompt=test.prompt,
            response=response[:200] + "..." if len(response) > 200 else response,
            response_time=response_time,
            contains_expected_keywords=found,
            total_expected_keywords=len(test.expected_keywords),
            score=score
        )
        results.append(result)

        print(f"Score: {score:.2f} ({found}/{len(test.expected_keywords)} keywords)")
        print(f"Time: {response_time:.2f}s\n")

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}\n")

    for category in ["algorithm", "coding", "devops"]:
        cat_results = [r for r in results if r.category == category]
        if cat_results:
            avg_score = sum(r.score for r in cat_results) / len(cat_results)
            avg_time = sum(r.response_time for r in cat_results) / len(cat_results)
            print(f"{category.upper()}: {avg_score:.2%} avg score, {avg_time:.2f}s avg time")

    overall_score = sum(r.score for r in results) / len(results)
    overall_time = sum(r.response_time for r in results) / len(results)
    print(f"\nOVERALL: {overall_score:.2%} avg score, {overall_time:.2f}s avg time")

    # Save if requested
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        print(f"\n✅ Results saved to: {save_path}")

    return results


def compare_results(baseline_path: Path, current_results: List[BenchmarkResult]):
    """Compare current results to baseline."""
    with open(baseline_path) as f:
        baseline_data = json.load(f)

    baseline_results = [BenchmarkResult(**r) for r in baseline_data]

    print(f"\n{'='*70}")
    print(f"COMPARISON TO BASELINE")
    print(f"{'='*70}\n")

    for category in ["algorithm", "coding", "devops"]:
        baseline_cat = [r for r in baseline_results if r.category == category]
        current_cat = [r for r in current_results if r.category == category]

        if baseline_cat and current_cat:
            baseline_score = sum(r.score for r in baseline_cat) / len(baseline_cat)
            current_score = sum(r.score for r in current_cat) / len(current_cat)
            delta = current_score - baseline_score
            delta_pct = (delta / baseline_score * 100) if baseline_score > 0 else 0

            emoji = "✅" if delta >= 0 else "❌"
            print(f"{category.upper()}:")
            print(f"  Baseline: {baseline_score:.2%}")
            print(f"  Current:  {current_score:.2%}")
            print(f"  Delta:    {emoji} {delta:+.2%} ({delta_pct:+.1f}%)\n")

    # Overall
    baseline_overall = sum(r.score for r in baseline_results) / len(baseline_results)
    current_overall = sum(r.score for r in current_results) / len(current_results)
    delta = current_overall - baseline_overall
    delta_pct = (delta / baseline_overall * 100) if baseline_overall > 0 else 0

    print(f"OVERALL:")
    print(f"  Baseline: {baseline_overall:.2%}")
    print(f"  Current:  {current_overall:.2%}")
    print(f"  Delta:    {delta:+.2%} ({delta_pct:+.1f}%)")

    # Decision
    print(f"\n{'='*70}")
    print(f"RECOMMENDATION")
    print(f"{'='*70}\n")

    algo_baseline = [r for r in baseline_results if r.category == "algorithm"]
    algo_current = [r for r in current_results if r.category == "algorithm"]
    algo_improvement = (sum(r.score for r in algo_current) / len(algo_current) -
                        sum(r.score for r in algo_baseline) / len(algo_baseline))

    other_baseline = [r for r in baseline_results if r.category != "algorithm"]
    other_current = [r for r in current_results if r.category != "algorithm"]
    other_degradation = (sum(r.score for r in other_baseline) / len(other_baseline) -
                         sum(r.score for r in other_current) / len(other_current))

    if algo_improvement > 0.20 and other_degradation < 0.05:
        print("✅ KEEP ADAPTERS:")
        print(f"  - Algorithm tasks improved by {algo_improvement:.1%}")
        print(f"  - Other tasks degraded by only {other_degradation:.1%}")
    elif algo_improvement > 0.10 and other_degradation < 0.10:
        print("⚠️  MAYBE KEEP ADAPTERS:")
        print(f"  - Algorithm tasks improved by {algo_improvement:.1%}")
        print(f"  - Other tasks degraded by {other_degradation:.1%}")
    else:
        print("❌ DON'T KEEP ADAPTERS:")
        print(f"  - Algorithm improvement too small ({algo_improvement:.1%})")
        print(f"  - OR other tasks degraded too much ({other_degradation:.1%})")


def main():
    parser = argparse.ArgumentParser(description="Benchmark Esper3.1")
    parser.add_argument("--model", default="gpt-oss:20b", help="Ollama model name")
    parser.add_argument("--with-adapters", action="store_true", help="Use model with adapters")
    parser.add_argument("--save-baseline", action="store_true", help="Save as baseline")
    parser.add_argument("--compare-to-baseline", action="store_true", help="Compare to baseline")
    parser.add_argument("--baseline-path", type=Path, default=Path("data/esper31_baseline.json"),
                        help="Path to baseline results")

    args = parser.parse_args()

    # Run benchmark
    model = args.model
    if args.with_adapters:
        # TODO: Update this when we know the exported Ollama model name
        model = "esper31-algorithms:20b"

    save_path = None
    if args.save_baseline:
        save_path = args.baseline_path

    results = run_benchmark(model=model, save_path=save_path)

    # Compare if requested
    if args.compare_to_baseline:
        if not args.baseline_path.exists():
            print(f"\n❌ ERROR: Baseline not found at {args.baseline_path}")
            print(f"Run with --save-baseline first")
            return
        compare_results(args.baseline_path, results)


if __name__ == "__main__":
    main()
