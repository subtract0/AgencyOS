#!/usr/bin/env python3
"""
HARD Benchmark for Esper3.1 - Tests that actually challenge the model.

The original benchmark was too easy (98.89% accuracy).
These tests require genuine algorithmic understanding and reasoning.

Usage:
    # Save baseline (before training)
    python scripts/benchmark_esper31_hard.py --save-baseline

    # Compare after training
    python scripts/benchmark_esper31_hard.py --with-adapters --compare-to-baseline
"""
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import argparse
import subprocess


@dataclass
class HardTestCase:
    """A genuinely challenging test case."""
    category: str
    prompt: str
    correct_answer: str  # What a correct response should contain
    common_wrong_answers: List[str]  # Common mistakes to check for
    difficulty: str
    explanation: str  # Why this is hard


@dataclass
class BenchmarkResult:
    """Result from running a test case."""
    test_id: str
    category: str
    difficulty: str
    prompt: str
    response: str
    response_time: float
    is_correct: bool
    has_wrong_answer: bool
    score: float  # 0.0, 0.5, or 1.0


def get_hard_test_cases() -> List[HardTestCase]:
    """Get ACTUALLY HARD test cases that will differentiate models."""
    return [
        # ===== HARD ALGORITHM TESTS =====

        HardTestCase(
            category="algorithm",
            prompt="""Given a graph with NEGATIVE weights:
A->B: 4, A->C: 2, B->D: -5, C->B: 1, C->D: 8, B->C: -2

Find shortest path from A to D using Bellman-Ford. Explain why Dijkstra won't work here.""",
            correct_answer="A->B->C->B->D",  # Takes advantage of negative cycle
            common_wrong_answers=["A->C->D", "Dijkstra", "impossible"],
            difficulty="hard",
            explanation="Requires understanding negative weights, negative cycles, and why Bellman-Ford is needed"
        ),

        HardTestCase(
            category="algorithm",
            prompt="""You have an array [3, 1, 4, 1, 5, 9, 2, 6] and need to find the longest increasing subsequence.
What is the LENGTH of the LIS, and give ONE example sequence.
Note: Subsequence, not subarray (doesn't need to be contiguous).""",
            correct_answer="4",  # LIS length is 4, e.g., [1,4,5,9] or [1,4,5,6]
            common_wrong_answers=["5", "6", "[1,5,9]", "subarray"],
            difficulty="hard",
            explanation="Classic DP problem, many models confuse subsequence with subarray"
        ),

        HardTestCase(
            category="algorithm",
            prompt="""Design a data structure for an LRU cache with O(1) get and put operations.
Explain the key insight that makes O(1) possible for BOTH operations.
What two data structures do you combine?""",
            correct_answer="hash map + doubly linked list",
            common_wrong_answers=["array", "single linked list", "just hash map", "O(n)"],
            difficulty="hard",
            explanation="Requires understanding why both structures are needed for O(1)"
        ),

        HardTestCase(
            category="algorithm",
            prompt="""You're doing a DFS on a directed graph to detect cycles.
When do you mark a node as "visited" vs "in current path"?
Give a counterexample where just "visited" fails to detect a cycle.""",
            correct_answer="need both visited AND recursion stack",
            common_wrong_answers=["just visited", "just stack", "doesn't matter"],
            difficulty="hard",
            explanation="Subtle difference between visited set and recursion stack in cycle detection"
        ),

        HardTestCase(
            category="algorithm",
            prompt="""Given intervals [[1,3],[2,6],[8,10],[15,18]], merge overlapping intervals.
Now explain: What if the intervals AREN'T sorted? What changes in your algorithm?""",
            correct_answer="must sort first by start time",
            common_wrong_answers=["doesn't matter", "still works", "use different algorithm"],
            difficulty="hard",
            explanation="Tests understanding of preconditions and algorithm assumptions"
        ),

        # ===== HARD CODING TESTS =====

        HardTestCase(
            category="coding",
            prompt="""Explain the difference between:
```python
def outer():
    x = []
    def inner():
        x.append(1)
    return inner
```
vs
```python
def outer():
    x = 0
    def inner():
        x = x + 1
    return inner
```
Which one works? Which one raises UnboundLocalError? Why?""",
            correct_answer="first works, second raises UnboundLocalError",
            common_wrong_answers=["both work", "second works", "need nonlocal for both"],
            difficulty="hard",
            explanation="Subtle Python scoping: mutating vs reassigning in closures"
        ),

        HardTestCase(
            category="coding",
            prompt="""You have a race condition in this code:
```python
counter = 0

async def increment():
    global counter
    temp = counter
    await asyncio.sleep(0)  # Simulates I/O
    counter = temp + 1
```
If you run increment() 100 times concurrently, counter won't be 100.
What's the CORRECT fix? (Hint: asyncio.Lock is one option, but there's a simpler one)""",
            correct_answer="use asyncio.Lock OR make it atomic with += OR use queue",
            common_wrong_answers=["threading.Lock", "just remove await", "use Thread"],
            difficulty="hard",
            explanation="Tests async concurrency understanding vs threading locks"
        ),

        HardTestCase(
            category="coding",
            prompt="""In Python, what's the difference between `is` and `==` for:
- Small integers (1, 2, 3)
- Large integers (10000, 10001)
- Strings ("hello", "hello")
Explain when `is` returns True even though you created separate objects.""",
            correct_answer="small ints/strings are interned, is checks identity",
            common_wrong_answers=["they're the same", "always use ==", "is faster"],
            difficulty="hard",
            explanation="Tests understanding of object interning and identity vs equality"
        ),

        HardTestCase(
            category="coding",
            prompt="""You're implementing a retry decorator with exponential backoff:
```python
@retry(max_attempts=3, backoff=2)
def flaky_api_call():
    ...
```
What's the tricky part about implementing this as a decorator?
How do you preserve the original function's signature and docstring?""",
            correct_answer="use functools.wraps to preserve metadata",
            common_wrong_answers=["just return wrapper", "copy docstring manually", "doesn't matter"],
            difficulty="hard",
            explanation="Tests decorator best practices and metadata preservation"
        ),

        HardTestCase(
            category="coding",
            prompt="""Explain why this is a memory leak in a long-running server:
```python
cache = {}

def process_request(user_id, data):
    if user_id not in cache:
        cache[user_id] = expensive_computation(data)
    return cache[user_id]
```
What's the fix? (LRU cache, TTL, max size?)""",
            correct_answer="unbounded cache grows forever, need LRU/TTL/max_size",
            common_wrong_answers=["no leak", "use dict.clear()", "restart server"],
            difficulty="hard",
            explanation="Tests understanding of unbounded growth in production systems"
        ),

        # ===== HARD DEVOPS TESTS =====

        HardTestCase(
            category="devops",
            prompt="""Your Docker container works locally but fails in production with "permission denied".
The Dockerfile uses `USER nonroot` for security.
What's likely wrong, and how do you fix file permissions in the Dockerfile?""",
            correct_answer="COPY files as root then chown to nonroot user",
            common_wrong_answers=["run as root", "chmod 777", "disable security"],
            difficulty="hard",
            explanation="Tests understanding of Docker user permissions and security"
        ),

        HardTestCase(
            category="devops",
            prompt="""In Kubernetes, your pod keeps getting OOMKilled but `kubectl top pod` shows it's only using 200MB.
You set memory limit to 512MB. What's happening?
Hint: Look at memory requests vs limits and QoS classes.""",
            correct_answer="memory request != limit, or page cache counted, or limit too low for spikes",
            common_wrong_answers=["increase limit to 1GB", "bug in kubectl", "restart pod"],
            difficulty="hard",
            explanation="Tests deep understanding of K8s memory accounting and QoS"
        ),

        HardTestCase(
            category="devops",
            prompt="""Your GitHub Actions workflow runs tests in parallel with `matrix: [3.9, 3.10, 3.11, 3.12]`.
Tests pass on 3.9-3.11 but fail on 3.12. How do you allow 3.12 to fail without blocking the workflow?
(continue-on-error is wrong - that ignores ALL failures)""",
            correct_answer="use matrix.experimental and allow-failure pattern",
            common_wrong_answers=["continue-on-error: true", "remove 3.12", "if: matrix.version != '3.12'"],
            difficulty="hard",
            explanation="Tests nuanced understanding of GitHub Actions matrix builds"
        ),

        HardTestCase(
            category="devops",
            prompt="""Your Postgres DB has a query that's slow in production but fast in staging.
EXPLAIN ANALYZE shows different query plans. What are 3 likely reasons?
(Hint: Not just "more data")""",
            correct_answer="outdated statistics, missing indexes, different postgres.conf, cache state",
            common_wrong_answers=["just more data", "slower server", "network latency"],
            difficulty="hard",
            explanation="Tests understanding of query planner and environment differences"
        ),

        HardTestCase(
            category="devops",
            prompt="""You set up Redis as a cache with TTL=3600 (1 hour).
After 2 hours, `redis-cli DBSIZE` shows 10M keys (should be ~0).
What's the issue? (Hint: maxmemory-policy)""",
            correct_answer="maxmemory not set or wrong eviction policy (noeviction)",
            common_wrong_answers=["TTL not working", "Redis bug", "need to restart"],
            difficulty="hard",
            explanation="Tests understanding of Redis memory management and eviction policies"
        ),
    ]


def run_test_ollama(
    prompt: str,
    model: str = "gpt-oss:20b",
    port: int = 11434,
    timeout: int = 120
) -> tuple[str, float]:
    """
    Run test using Ollama.

    Args:
        prompt: Test prompt
        model: Ollama model name
        port: Ollama port
        timeout: Timeout in seconds

    Returns:
        (response_text, response_time_seconds)
    """
    start = time.time()
    try:
        result = subprocess.run(
            ["curl", "-s", f"http://127.0.0.1:{port}/api/generate",
             "-d", json.dumps({
                 "model": model,
                 "prompt": prompt,
                 "stream": False,
                 "options": {
                     "temperature": 0.1,  # Low temp for more consistent answers
                     "num_predict": 512
                 }
             })],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start

        if result.returncode == 0:
            response_data = json.loads(result.stdout)
            return response_data.get("response", ""), elapsed
        else:
            return f"ERROR: {result.stderr}", elapsed

    except subprocess.TimeoutExpired:
        return "ERROR: Timeout", time.time() - start
    except Exception as e:
        return f"ERROR: {e}", time.time() - start


def score_response(
    response: str,
    correct_answer: str,
    wrong_answers: List[str]
) -> tuple[bool, bool, float]:
    """
    Score response intelligently.

    Returns:
        (is_correct, has_wrong_answer, score)
        score: 1.0 = fully correct, 0.5 = partial, 0.0 = wrong
    """
    response_lower = response.lower()
    correct_lower = correct_answer.lower()

    # Check if response contains correct answer
    is_correct = correct_lower in response_lower

    # Check if response contains common wrong answers
    has_wrong = any(wrong.lower() in response_lower for wrong in wrong_answers)

    # Scoring
    if is_correct and not has_wrong:
        score = 1.0  # Perfect
    elif is_correct and has_wrong:
        score = 0.5  # Mentioned correct but also wrong answers
    else:
        score = 0.0  # Wrong or no answer

    return is_correct, has_wrong, score


def run_benchmark(
    model: str = "gpt-oss:20b",
    port: int = 11434,
    save_path: Optional[Path] = None
) -> List[BenchmarkResult]:
    """
    Run full HARD benchmark.

    Args:
        model: Ollama model name
        port: Ollama port
        save_path: If provided, save results to this path

    Returns:
        List of benchmark results
    """
    print(f"\n{'='*70}")
    print(f"HARD BENCHMARK: {model} (Port {port})")
    print(f"{'='*70}\n")

    test_cases = get_hard_test_cases()
    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {test.category.upper()} - {test.difficulty}")
        print(f"Test: {test.prompt[:80]}...")

        response, response_time = run_test_ollama(test.prompt, model, port)
        is_correct, has_wrong, score = score_response(
            response,
            test.correct_answer,
            test.common_wrong_answers
        )

        result = BenchmarkResult(
            test_id=f"{test.category}_{i}",
            category=test.category,
            difficulty=test.difficulty,
            prompt=test.prompt,
            response=response[:300] + "..." if len(response) > 300 else response,
            response_time=response_time,
            is_correct=is_correct,
            has_wrong_answer=has_wrong,
            score=score
        )
        results.append(result)

        # Show result
        if score == 1.0:
            emoji = "✅"
        elif score == 0.5:
            emoji = "⚠️"
        else:
            emoji = "❌"

        print(f"Score: {emoji} {score:.1f} (Correct: {is_correct}, HasWrong: {has_wrong})")
        print(f"Time: {response_time:.2f}s")
        print(f"Why hard: {test.explanation}\n")

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}\n")

    for category in ["algorithm", "coding", "devops"]:
        cat_results = [r for r in results if r.category == category]
        if cat_results:
            avg_score = sum(r.score for r in cat_results) / len(cat_results)
            avg_time = sum(r.response_time for r in cat_results) / len(cat_results)
            perfect = sum(1 for r in cat_results if r.score == 1.0)
            print(f"{category.upper()}:")
            print(f"  Avg Score: {avg_score:.2%}")
            print(f"  Perfect: {perfect}/{len(cat_results)}")
            print(f"  Avg Time: {avg_time:.2f}s\n")

    overall_score = sum(r.score for r in results) / len(results)
    perfect_count = sum(1 for r in results if r.score == 1.0)
    print(f"OVERALL:")
    print(f"  Avg Score: {overall_score:.2%}")
    print(f"  Perfect: {perfect_count}/{len(results)}")

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
    print(f"COMPARISON TO BASELINE (HARD TESTS)")
    print(f"{'='*70}\n")

    for category in ["algorithm", "coding", "devops"]:
        baseline_cat = [r for r in baseline_results if r.category == category]
        current_cat = [r for r in current_results if r.category == category]

        if baseline_cat and current_cat:
            baseline_score = sum(r.score for r in baseline_cat) / len(baseline_cat)
            current_score = sum(r.score for r in current_cat) / len(current_cat)
            delta = current_score - baseline_score
            delta_pct = (delta / baseline_score * 100) if baseline_score > 0 else 0

            baseline_perfect = sum(1 for r in baseline_cat if r.score == 1.0)
            current_perfect = sum(1 for r in current_cat if r.score == 1.0)

            emoji = "✅" if delta >= 0 else "❌"
            print(f"{category.upper()}:")
            print(f"  Baseline: {baseline_score:.2%} ({baseline_perfect}/{len(baseline_cat)} perfect)")
            print(f"  Current:  {current_score:.2%} ({current_perfect}/{len(current_cat)} perfect)")
            print(f"  Delta:    {emoji} {delta:+.2%} ({delta_pct:+.1f}%)\n")

    # Overall
    baseline_overall = sum(r.score for r in baseline_results) / len(baseline_results)
    current_overall = sum(r.score for r in current_results) / len(current_results)
    delta = current_overall - baseline_overall

    baseline_perfect = sum(1 for r in baseline_results if r.score == 1.0)
    current_perfect = sum(1 for r in current_results if r.score == 1.0)

    print(f"OVERALL:")
    print(f"  Baseline: {baseline_overall:.2%} ({baseline_perfect}/{len(baseline_results)} perfect)")
    print(f"  Current:  {current_overall:.2%} ({current_perfect}/{len(current_results)} perfect)")
    print(f"  Delta:    {delta:+.2%}")

    # Recommendation
    print(f"\n{'='*70}")
    print(f"RECOMMENDATION")
    print(f"{'='*70}\n")

    algo_improvement = current_overall - baseline_overall

    if algo_improvement > 0.15:
        print("✅ SIGNIFICANT IMPROVEMENT:")
        print(f"  - Overall improvement: {algo_improvement:.1%}")
        print(f"  - Adapters are working!")
    elif algo_improvement > 0.05:
        print("⚠️  MODEST IMPROVEMENT:")
        print(f"  - Overall improvement: {algo_improvement:.1%}")
        print(f"  - Consider more training")
    else:
        print("❌ NO SIGNIFICANT IMPROVEMENT:")
        print(f"  - Overall change: {algo_improvement:.1%}")
        print(f"  - May need different approach")


def main():
    parser = argparse.ArgumentParser(description="HARD Benchmark for Esper3.1")
    parser.add_argument("--model", default="gpt-oss:20b", help="Ollama model name")
    parser.add_argument("--port", type=int, default=11434, help="Ollama port")
    parser.add_argument("--with-adapters", action="store_true", help="Use model with adapters (port 11435)")
    parser.add_argument("--save-baseline", action="store_true", help="Save as baseline")
    parser.add_argument("--compare-to-baseline", action="store_true", help="Compare to baseline")
    parser.add_argument("--baseline-path", type=Path, default=Path("data/esper31_baseline_hard.json"),
                        help="Path to baseline results")

    args = parser.parse_args()

    # Use port 11435 for adapted model
    port = 11435 if args.with_adapters else args.port

    model = args.model
    if args.with_adapters:
        model = "esper31-algorithms:20b"  # Adapted model

    save_path = None
    if args.save_baseline:
        save_path = args.baseline_path

    results = run_benchmark(model=model, port=port, save_path=save_path)

    # Compare if requested
    if args.compare_to_baseline:
        if not args.baseline_path.exists():
            print(f"\n❌ ERROR: Baseline not found at {args.baseline_path}")
            print(f"Run with --save-baseline first")
            return
        compare_results(args.baseline_path, results)


if __name__ == "__main__":
    main()
