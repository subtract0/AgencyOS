#!/usr/bin/env python3
"""
DISTRIBUTED MARATHON COORDINATOR - Multi-Machine Test Audit

Coordinates test analysis across multiple machines (MBP + MBA).
Uses TaskQueue for work distribution and result aggregation.

Architecture:
- Coordinator: Creates test analysis tasks (5,889 total)
- Workers: MBP (Qwen3-Coder-30b) + MBA (GPT-OSS-20b)
- Results: Merged into single comprehensive report

Expected Performance:
- MBP alone: 8 hours
- MBP + MBA: 4-5 hours (2x speedup)
- Cost: $0 (all local models)

Usage:
    # On coordinator machine (MBP):
    python scripts/distributed_marathon_coordinator.py --create-tasks

    # On MBP worker terminal:
    python scripts/distributed_marathon_worker.py --machine mbp --model qwen3-coder:30b

    # On MBA worker terminal:
    python scripts/distributed_marathon_worker.py --machine mba --model gpt-oss:20b

    # Merge results when done:
    python scripts/distributed_marathon_coordinator.py --merge-results
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from meta_learning.task_queue import Task, TaskQueue

# Distributed audit config
DISTRIBUTED_DIR = Path.home() / ".agency" / "marathon_distributed"
RESULTS_DIR = DISTRIBUTED_DIR / "results"
QUEUE_FILE = DISTRIBUTED_DIR / "task_queue.json"

# NECESSARY categories
NECESSARY_CATEGORIES = [
    "Normal", "Edge", "Cascading", "Essential",
    "Security", "Spec", "Accessibility", "Resilience", "Year-round"
]

def extract_all_test_functions() -> List[Tuple[Path, str, int, int]]:
    """Extract ALL test functions from codebase."""
    print("🔍 Extracting ALL test functions...")

    test_files = list(Path("tests").rglob("test_*.py"))
    all_tests = []

    for test_file in test_files:
        try:
            content = test_file.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    end_line = node.lineno
                    if node.body:
                        last_stmt = node.body[-1]
                        end_line = getattr(last_stmt, 'end_lineno', node.lineno + 10)

                    all_tests.append((
                        test_file,
                        node.name,
                        node.lineno,
                        end_line
                    ))
        except Exception as e:
            print(f"  ⚠️  Failed to parse {test_file}: {e}")

    print(f"  ✅ Found {len(all_tests)} test functions across {len(test_files)} files")
    return all_tests

def create_distributed_tasks(max_tests: int = None) -> int:
    """Create test analysis tasks for distributed execution."""
    print("="*80)
    print("🌐 DISTRIBUTED MARATHON COORDINATOR")
    print("="*80)
    print()

    # Setup directories
    DISTRIBUTED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    # Extract all tests
    all_tests = extract_all_test_functions()

    if max_tests:
        all_tests = all_tests[:max_tests]

    total_tests = len(all_tests)

    print(f"📊 Creating {total_tests} test analysis tasks...")
    print()

    # Create TaskQueue
    queue = TaskQueue(queue_file=str(QUEUE_FILE))

    # Create tasks (one per test function)
    tasks = []
    for idx, (test_file, test_name, start_line, end_line) in enumerate(all_tests):
        task = Task(
            task_id=f"test_analysis_{idx}",
            type="test_analysis",
            description=f"Analyze {test_name} in {test_file}:{start_line}",
            files_to_modify=[],
            dependencies=[],
            priority=0,  # All equal priority (FIFO)
            status="pending",
            metadata={
                "test_file": str(test_file),
                "test_name": test_name,
                "start_line": start_line,
                "end_line": end_line,
                "analysis_type": "NECESSARY_pattern"
            }
        )
        tasks.append(task)

    # Add tasks in batch
    queue.add_tasks_batch(tasks)

    print("✅ Task creation complete!")
    print()
    print(f"📋 Total Tasks: {total_tests}")
    print(f"📁 Queue File: {QUEUE_FILE}")
    print(f"📁 Results Dir: {RESULTS_DIR}")
    print()
    print("🚀 Next Steps:")
    print()
    print("  1. On MBP (this machine):")
    print("     python scripts/distributed_marathon_worker.py --machine mbp --model qwen3-coder:30b")
    print()
    print("  2. On MBA (other machine):")
    print("     python scripts/distributed_marathon_worker.py --machine mba --model gpt-oss:20b")
    print()
    print("  3. Monitor progress:")
    print(f"     watch -n 5 'python scripts/distributed_marathon_coordinator.py --status'")
    print()
    print("  4. When complete, merge results:")
    print("     python scripts/distributed_marathon_coordinator.py --merge-results")
    print()
    print("="*80)

    return total_tests

def show_status():
    """Show current distributed audit status."""
    queue = TaskQueue(queue_file=str(QUEUE_FILE))
    status = queue.get_status()

    print("="*80)
    print("📊 DISTRIBUTED MARATHON STATUS")
    print("="*80)
    print()
    print(f"Pending:     {status['pending']:4d}")
    print(f"In Progress: {status['in_progress']:4d}")
    print(f"Completed:   {status['completed']:4d}")
    print(f"Failed:      {status['failed']:4d}")
    print()

    total = sum(status.values())
    if total > 0:
        pct = (status['completed'] / total) * 100
        print(f"Progress: {pct:.1f}% complete")

    # Check results files
    result_files = list(RESULTS_DIR.glob("*.json"))
    print(f"Result Files: {len(result_files)}")
    print()

    # Machine breakdown (from result files)
    machine_counts = defaultdict(int)
    for result_file in result_files:
        try:
            with open(result_file) as f:
                data = json.load(f)
                machine = data.get("machine", "unknown")
                machine_counts[machine] += 1
        except:
            pass

    if machine_counts:
        print("Machine Contributions:")
        for machine, count in sorted(machine_counts.items()):
            print(f"  {machine}: {count} tests")

    print()
    print("="*80)

def merge_results():
    """Merge results from all workers into final report."""
    print("="*80)
    print("🔀 MERGING DISTRIBUTED RESULTS")
    print("="*80)
    print()

    result_files = list(RESULTS_DIR.glob("*.json"))
    print(f"📁 Found {len(result_files)} result files")

    if not result_files:
        print("❌ No results to merge!")
        return

    # Load all results
    all_results = []
    machine_stats = defaultdict(int)

    for result_file in result_files:
        try:
            with open(result_file) as f:
                result = json.load(f)
                all_results.append(result)
                machine = result.get("machine", "unknown")
                machine_stats[machine] += 1
        except Exception as e:
            print(f"  ⚠️  Failed to load {result_file}: {e}")

    print(f"  ✅ Loaded {len(all_results)} results")
    print()

    # Machine breakdown
    print("Machine Contributions:")
    for machine, count in sorted(machine_stats.items()):
        print(f"  {machine}: {count} tests")
    print()

    # Generate combined reports
    output_dir = Path("audit_reports")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON report
    json_path = output_dir / f"distributed_audit_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"✅ JSON Report: {json_path}")

    # Markdown summary
    md_path = output_dir / f"distributed_audit_{timestamp}.md"
    generate_markdown_report(all_results, md_path, machine_stats)
    print(f"✅ Markdown Report: {md_path}")

    # Healing roadmap
    roadmap_path = output_dir / f"distributed_healing_roadmap_{timestamp}.md"
    generate_healing_roadmap(all_results, roadmap_path)
    print(f"✅ Healing Roadmap: {roadmap_path}")

    print()
    print("="*80)
    print("✅ MERGE COMPLETE!")
    print("="*80)

def generate_markdown_report(results: List[Dict], output_path: Path, machine_stats: Dict):
    """Generate markdown summary report."""
    with open(output_path, 'w') as f:
        f.write("# Distributed Marathon Test Audit Report\n\n")
        f.write(f"**Date**: {datetime.now()}\n")
        f.write(f"**Tests Analyzed**: {len(results)}\n")
        f.write(f"**Machines**: {len(machine_stats)}\n")
        f.write(f"**Cost**: $0 (100% local)\n\n")

        f.write("## Machine Contributions\n\n")
        for machine, count in sorted(machine_stats.items()):
            f.write(f"- **{machine}**: {count} tests\n")
        f.write("\n")

        # NECESSARY coverage
        f.write("## NECESSARY Pattern Coverage\n\n")
        all_covered = defaultdict(int)
        for result in results:
            for cat in result.get("necessary_coverage", []):
                all_covered[cat] += 1

        for cat in NECESSARY_CATEGORIES:
            covered = all_covered.get(cat, 0)
            total = len(results)
            pct = (covered / total * 100) if total > 0 else 0
            f.write(f"- **{cat}**: {covered}/{total} tests ({pct:.1f}%)\n")
        f.write("\n")

        # Priority breakdown
        f.write("## Healing Priority Breakdown\n\n")
        priorities = defaultdict(int)
        for result in results:
            priority = result.get("healing_priority", "P2")
            priorities[priority] += 1

        for p in ["P0", "P1", "P2", "P3"]:
            count = priorities.get(p, 0)
            f.write(f"- **{p}**: {count} tests\n")

def generate_healing_roadmap(results: List[Dict], output_path: Path):
    """Generate actionable healing roadmap."""
    with open(output_path, 'w') as f:
        f.write("# Distributed Healing Roadmap\n\n")
        f.write(f"**Generated**: {datetime.now()}\n")
        f.write(f"**Tests Analyzed**: {len(results)}\n\n")

        # P0 issues
        f.write("## Phase 1: Critical Fixes (P0)\n\n")
        p0_tests = [r for r in results if r.get("healing_priority") == "P0"]
        if p0_tests:
            for result in p0_tests[:20]:
                f.write(f"- [ ] Fix `{result['name']}` in `{result['file']}:{result['line_start']}`\n")
        else:
            f.write("✅ No P0 issues found!\n")
        f.write("\n")

        # P1 issues
        f.write("## Phase 2: High Priority (P1)\n\n")
        p1_tests = [r for r in results if r.get("healing_priority") == "P1"]
        f.write(f"- {len(p1_tests)} P1 issues to address\n\n")

        # NECESSARY gaps
        f.write("## Phase 3: NECESSARY Gap Filling\n\n")
        gap_counts = defaultdict(int)
        for result in results:
            for gap in result.get("necessary_gaps", []):
                gap_counts[gap] += 1

        for cat in NECESSARY_CATEGORIES:
            count = gap_counts.get(cat, 0)
            if count > 0:
                f.write(f"### {cat} Gap ({count} tests)\n\n")

def main():
    parser = argparse.ArgumentParser(description="Distributed Marathon Coordinator")
    parser.add_argument("--create-tasks", action="store_true", help="Create test analysis tasks")
    parser.add_argument("--max-tests", type=int, help="Limit number of tests (for testing)")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--merge-results", action="store_true", help="Merge worker results")

    args = parser.parse_args()

    if args.create_tasks:
        create_distributed_tasks(max_tests=args.max_tests)
    elif args.status:
        show_status()
    elif args.merge_results:
        merge_results()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
