#!/usr/bin/env python3
"""
Parallel A/B Orchestrator for AgencyOS

Leverages worktrees to run multiple agents simultaneously using Python's
concurrent.futures for true parallelization.

EPIC 4.2 Component 3: Parallel Execution Framework

Constitutional Compliance:
- Article I: Complete context (all trials isolated in worktrees)
- Article II: 100% verification (thread-safe result collection)
- Article III: Automated enforcement (parallel safety checks)

Version: 1.0.0
Created: 2025-10-08
"""

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from dspy_agents.ab_testing import EnhancedABOrchestrator

logger = logging.getLogger(__name__)


class ParallelABOrchestrator(EnhancedABOrchestrator):
    """
    A/B Orchestrator with parallel worktree execution.

    Extends EnhancedABOrchestrator to run multiple agent benchmarks
    in parallel using ThreadPoolExecutor and git worktrees for isolation.

    Key Features:
    - Thread-safe budget tracking with Lock
    - Parallel job execution (default: 3 workers)
    - Real-time progress reporting
    - No worktree conflicts (unique branches per job)
    - Automatic result collection as jobs complete

    Example:
        >>> orchestrator = ParallelABOrchestrator(
        ...     agent_ids=["agent_v1", "agent_v2", "agent_v3"],
        ...     task_ids=["planner_api_auth_jwt"],
        ...     repeats=2,
        ...     budget_limit=5.0,
        ...     max_workers=3
        ... )
        >>> results_file = orchestrator.run()
        >>> # 3 agents × 1 task × 2 repeats = 6 jobs
        >>> # Completes in ~2x faster than sequential
    """

    def __init__(
        self,
        agent_ids: list[str],
        task_ids: list[str] | None = None,
        repeats: int = 3,
        budget_limit: float = 10.0,
        max_workers: int = 3,
    ):
        """
        Initialize parallel orchestrator.

        Args:
            agent_ids: List of agent identifiers to test
            task_ids: List of task IDs to run (None = all tasks)
            repeats: Number of repeat trials per agent/task combo
            budget_limit: Maximum cost in USD before stopping
            max_workers: Maximum number of parallel workers (default: 3)

        Constitutional Compliance:
            - Article I: Complete isolation via max_workers limit
            - Article II: Thread-safe verification via Lock
        """
        super().__init__(
            agent_ids=agent_ids,
            task_ids=task_ids,
            repeats=repeats,
            budget_limit=budget_limit,
        )

        self.max_workers = max_workers
        self._budget_lock = threading.Lock()
        self._results_lock = threading.Lock()
        self._completed_jobs = 0
        self._total_jobs = 0

        logger.info(f"ParallelABOrchestrator initialized with {max_workers} workers")

    def run(self) -> Path:
        """
        Execute A/B tests with parallel worktree execution.

        This method:
        1. Generates all job specifications (agent × task × repeat)
        2. Submits jobs to ThreadPoolExecutor for parallel execution
        3. Collects results as they complete
        4. Writes results to JSONL file incrementally

        Returns:
            Path to JSONL results file

        Raises:
            RuntimeError: If budget exceeded or critical error

        Constitutional Compliance:
            - Article I: Complete context (all jobs isolated)
            - Article II: 100% verification (thread-safe tracking)
        """
        # Create results directory
        results_dir = Path("benchmark_results")
        results_dir.mkdir(exist_ok=True)

        # Create timestamped results file with UUID to avoid conflicts in parallel test execution
        import uuid

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # Short UUID suffix
        results_path = results_dir / f"results_{timestamp}_{unique_id}.jsonl"

        # Generate all job specs
        jobs = []
        for agent_id in self.agent_ids:
            for task in self._get_tasks():
                for repeat_idx in range(self.repeats):
                    jobs.append((agent_id, task, repeat_idx))

        self._total_jobs = len(jobs)

        logger.info(
            f"Starting parallel orchestration: {len(self.agent_ids)} agents, "
            f"{len(self._get_tasks())} tasks, {self.repeats} repeats = {self._total_jobs} jobs"
        )
        logger.info(f"Parallel workers: {self.max_workers}")

        # Execute jobs in parallel
        start_time = time.time()
        results = []

        try:
            # Ensure directory exists
            results_path.parent.mkdir(parents=True, exist_ok=True)

            # Open results file for writing
            with open(results_path, "w") as f:
                # Submit all jobs to thread pool
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit jobs and create future-to-job mapping
                    future_to_job = {
                        executor.submit(self._run_single_job, agent_id, task, repeat_idx): (
                            agent_id,
                            task,
                            repeat_idx,
                        )
                        for agent_id, task, repeat_idx in jobs
                    }

                    # Collect results as they complete
                    for future in as_completed(future_to_job):
                        agent_id, task, repeat_idx = future_to_job[future]

                        try:
                            result = future.result()

                            # Thread-safe result collection
                            with self._results_lock:
                                results.append(result)
                                self._completed_jobs += 1

                                # Write result immediately (append-only)
                                f.write(json.dumps(result, default=str) + "\n")
                                f.flush()

                                # Progress reporting
                                progress = (self._completed_jobs / self._total_jobs) * 100
                                logger.info(
                                    f"[{self._completed_jobs}/{self._total_jobs}] "
                                    f"({progress:.1f}%) "
                                    f"Completed: {agent_id} on {task.task_id} "
                                    f"(repeat {repeat_idx + 1}/{self.repeats}), "
                                    f"score={result['scores']['aggregate']:.2%}, "
                                    f"cost=${result['cost_usd']:.4f}"
                                )

                                # Check budget after each result (thread-safe)
                                if self.total_cost >= self.budget_limit:
                                    logger.warning(
                                        f"Budget limit reached: ${self.total_cost:.2f} >= "
                                        f"${self.budget_limit:.2f}"
                                    )
                                    # Cancel remaining futures
                                    for f in future_to_job.keys():
                                        f.cancel()
                                    break

                        except Exception as e:
                            logger.error(f"Job failed: {agent_id} on {task.task_id}: {e}")
                            # Continue with other jobs (graceful degradation)

        except Exception as e:
            logger.error(f"Parallel orchestration failed: {e}")
            raise RuntimeError(f"Parallel orchestration failed: {e}") from e

        # Calculate final stats
        duration_s = time.time() - start_time
        jobs_per_second = self._completed_jobs / duration_s if duration_s > 0 else 0

        logger.info(
            f"Parallel orchestration complete in {duration_s:.1f}s. "
            f"Total cost: ${self.total_cost:.2f}. "
            f"Throughput: {jobs_per_second:.2f} jobs/sec. "
            f"Results: {results_path}"
        )

        return results_path

    def _run_single_job(self, agent_id: str, task, repeat_idx: int) -> dict[str, Any]:
        """
        Run a single agent/task/repeat job (thread-safe).

        This method executes in a worker thread. It:
        1. Checks budget before execution (thread-safe)
        2. Executes agent on task via parent's _execute_agent_on_task()
        3. Updates total_cost (thread-safe)
        4. Returns result dict

        Args:
            agent_id: Agent identifier
            task: BenchmarkTask to execute
            repeat_idx: Repeat trial index

        Returns:
            Result dict with scores, duration, cost, etc.

        Constitutional Compliance:
            - Article I: Complete context (isolated execution)
            - Article II: Thread-safe verification (Lock on budget)
        """
        # Thread-safe budget check before execution
        with self._budget_lock:
            if self.total_cost >= self.budget_limit:
                logger.warning(
                    f"Skipping job (budget limit): {agent_id} on {task.task_id} "
                    f"(repeat {repeat_idx})"
                )
                # Return placeholder result for skipped job
                return {
                    "run_id": "skipped",
                    "agent_id": agent_id,
                    "task_id": task.task_id,
                    "scores": {"aggregate": 0.0},
                    "duration_s": 0.0,
                    "cost_usd": 0.0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "repeat": repeat_idx,
                    "metadata": {"skipped": True, "reason": "budget_limit"},
                }

        # Execute agent on task (this is thread-safe because each worktree is isolated)
        result = self._execute_agent_on_task(agent_id, task, repeat_idx)

        # Thread-safe cost update
        with self._budget_lock:
            self.total_cost += result["cost_usd"]

        return result

    def get_stats(self) -> dict[str, Any]:
        """
        Get current orchestration statistics.

        Returns:
            Dict with progress, throughput, and budget stats

        Thread-safe: Uses locks for consistent reads.
        """
        with self._results_lock:
            completed = self._completed_jobs
            total = self._total_jobs

        with self._budget_lock:
            cost = self.total_cost
            budget = self.budget_limit

        progress = (completed / total * 100) if total > 0 else 0.0
        budget_used = (cost / budget * 100) if budget > 0 else 0.0

        return {
            "completed_jobs": completed,
            "total_jobs": total,
            "progress_pct": round(progress, 1),
            "total_cost_usd": round(cost, 2),
            "budget_limit_usd": round(budget, 2),
            "budget_used_pct": round(budget_used, 1),
            "max_workers": self.max_workers,
        }


def compare_sequential_vs_parallel(
    agent_ids: list[str],
    task_ids: list[str],
    repeats: int = 2,
    budget_limit: float = 5.0,
) -> dict[str, Any]:
    """
    Compare sequential vs parallel execution performance.

    Runs the same benchmark suite twice:
    1. Sequential (max_workers=1)
    2. Parallel (max_workers=3)

    Returns:
        Dict with timing comparison and speedup metrics

    Example:
        >>> results = compare_sequential_vs_parallel(
        ...     agent_ids=["agent_v1", "agent_v2"],
        ...     task_ids=["planner_api_auth_jwt"],
        ...     repeats=2
        ... )
        >>> print(f"Speedup: {results['speedup']:.2f}x")
    """
    logger.info("=" * 60)
    logger.info("SEQUENTIAL VS PARALLEL BENCHMARK")
    logger.info("=" * 60)

    # Sequential execution
    logger.info("\n[1/2] Running SEQUENTIAL execution (max_workers=1)...")
    seq_start = time.time()
    seq_orchestrator = ParallelABOrchestrator(
        agent_ids=agent_ids,
        task_ids=task_ids,
        repeats=repeats,
        budget_limit=budget_limit,
        max_workers=1,  # Sequential
    )
    seq_results = seq_orchestrator.run()
    seq_duration = time.time() - seq_start

    # Parallel execution
    logger.info("\n[2/2] Running PARALLEL execution (max_workers=3)...")
    par_start = time.time()
    par_orchestrator = ParallelABOrchestrator(
        agent_ids=agent_ids,
        task_ids=task_ids,
        repeats=repeats,
        budget_limit=budget_limit,
        max_workers=3,  # Parallel
    )
    par_results = par_orchestrator.run()
    par_duration = time.time() - par_start

    # Calculate speedup
    speedup = seq_duration / par_duration if par_duration > 0 else 0.0

    comparison = {
        "sequential": {
            "duration_s": round(seq_duration, 2),
            "results_file": str(seq_results),
            "total_jobs": seq_orchestrator._total_jobs,
            "completed_jobs": seq_orchestrator._completed_jobs,
        },
        "parallel": {
            "duration_s": round(par_duration, 2),
            "results_file": str(par_results),
            "total_jobs": par_orchestrator._total_jobs,
            "completed_jobs": par_orchestrator._completed_jobs,
        },
        "speedup": round(speedup, 2),
        "time_saved_s": round(seq_duration - par_duration, 2),
        "efficiency_pct": round((speedup / 3.0) * 100, 1),  # vs 3 workers
    }

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK RESULTS")
    logger.info("=" * 60)
    logger.info(f"Sequential: {seq_duration:.2f}s")
    logger.info(f"Parallel:   {par_duration:.2f}s")
    logger.info(f"Speedup:    {speedup:.2f}x")
    logger.info(f"Time saved: {comparison['time_saved_s']:.2f}s")
    logger.info(f"Efficiency: {comparison['efficiency_pct']:.1f}% (vs 3 workers)")
    logger.info("=" * 60)

    return comparison


if __name__ == "__main__":
    # CLI for quick testing
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="Parallel A/B Orchestrator")
    parser.add_argument("--agents", nargs="+", default=["agent_v1", "agent_v2"], help="Agent IDs")
    parser.add_argument("--tasks", nargs="+", default=["planner_api_auth_jwt"], help="Task IDs")
    parser.add_argument("--repeats", type=int, default=2, help="Repeat trials")
    parser.add_argument("--budget", type=float, default=5.0, help="Budget limit (USD)")
    parser.add_argument("--workers", type=int, default=3, help="Max workers")
    parser.add_argument("--compare", action="store_true", help="Compare seq vs parallel")

    args = parser.parse_args()

    if args.compare:
        # Run comparison
        results = compare_sequential_vs_parallel(
            agent_ids=args.agents,
            task_ids=args.tasks,
            repeats=args.repeats,
            budget_limit=args.budget,
        )
        print(f"\n✅ Speedup: {results['speedup']:.2f}x")
    else:
        # Run parallel orchestration
        orchestrator = ParallelABOrchestrator(
            agent_ids=args.agents,
            task_ids=args.tasks,
            repeats=args.repeats,
            budget_limit=args.budget,
            max_workers=args.workers,
        )
        results_file = orchestrator.run()
        print(f"\n✅ Results: {results_file}")
