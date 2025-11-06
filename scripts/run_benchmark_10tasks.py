#!/usr/bin/env python3
"""
10-Task Benchmark for Constitutional Compliance Validation (Week 4 Day 2)

Monitors Articles I, II, V during live benchmark execution.

Article I: Complete Context Before Action
- Validates retry behavior on timeout
- Validates escalation logic (LOCAL → LOCAL_PLUS → CLOUD)
- Ensures no partial results

Article II: 100% Verification and Stability
- Validates all tasks complete (no hanging)
- Validates test execution
- Validates terminal states (success/failure)

Article V: Spec-Driven Development
- Validates benchmark follows documented procedure
- Validates task types are valid (TaskType enum)
- Validates results documented for reproducibility
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from trinity_protocol.core.orchestrator import TrinityBus

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 10 diverse benchmark tasks following TaskType enum
BENCHMARK_TASKS = [
    {
        "task_id": "bench_001",
        "task_type": "CODE_FIX",
        "description": "Fix simple type error in helper function",
        "priority": "MEDIUM",
        "file": "trinity_protocol/core/helper_utils.py",
        "expected_tier": "LOCAL",
    },
    {
        "task_id": "bench_002",
        "task_type": "TEST_GENERATION",
        "description": "Generate unit tests for new OllamaClient module",
        "priority": "HIGH",
        "file": "trinity_protocol/core/ollama_client.py",
        "expected_tier": "LOCAL",
    },
    {
        "task_id": "bench_003",
        "task_type": "REFACTORING",
        "description": "Consolidate duplicate logging functions",
        "priority": "LOW",
        "file": "trinity_protocol/core/logging_utils.py",
        "expected_tier": "LOCAL",
    },
    {
        "task_id": "bench_004",
        "task_type": "ARCHITECTURE",
        "description": "Design API for new agent communication protocol",
        "priority": "HIGH",
        "file": "trinity_protocol/core/message_protocol.py",
        "expected_tier": "LOCAL_PLUS",  # Complex, may need escalation
    },
    {
        "task_id": "bench_005",
        "task_type": "TOOL_CREATION",
        "description": "Create utility for parsing agent responses",
        "priority": "MEDIUM",
        "file": "trinity_protocol/tools/response_parser.py",
        "expected_tier": "LOCAL",
    },
    {
        "task_id": "bench_006",
        "task_type": "VERIFICATION",
        "description": "Verify constitutional compliance in HybridExecutor",
        "priority": "HIGH",
        "file": "trinity_protocol/core/hybrid_executor.py",
        "expected_tier": "LOCAL",
    },
    {
        "task_id": "bench_007",
        "task_type": "CODE_GENERATION",
        "description": "Generate new feature for cost tracking visualization",
        "priority": "MEDIUM",
        "file": "trinity_protocol/core/cost_visualizer.py",
        "expected_tier": "LOCAL",
    },
    {
        "task_id": "bench_008",
        "task_type": "CODE_FIX",
        "description": "Fix complex multi-file dependency issue",
        "priority": "HIGH",
        "file": "trinity_protocol/core/orchestrator.py",
        "expected_tier": "LOCAL_PLUS",  # Complex, may need escalation
    },
    {
        "task_id": "bench_009",
        "task_type": "TEST_GENERATION",
        "description": "Generate integration tests for Trinity message bus",
        "priority": "HIGH",
        "file": "tests/trinity_protocol/core/test_message_bus_integration.py",
        "expected_tier": "LOCAL",
    },
    {
        "task_id": "bench_010",
        "task_type": "GENERAL",
        "description": "Update documentation for Week 4 Day 2 benchmark results",
        "priority": "LOW",
        "file": "archive/legacy-docs-2025-11-05/benchmarks/week4_day2_results.md",  # Archived 2025-11-05
        "expected_tier": "LOCAL",
    },
]


def inject_benchmark_tasks():
    """Inject all 10 benchmark tasks into Trinity message bus."""

    bus = TrinityBus()

    print("=" * 80)
    print("🚀 WEEK 4 DAY 2: 10-TASK CONSTITUTIONAL COMPLIANCE BENCHMARK")
    print("=" * 80)
    print(f"\n📅 Start Time: {datetime.now().isoformat()}")
    print(f"📋 Message Bus: {bus.path}")
    print(f"🎯 Tasks: {len(BENCHMARK_TASKS)}")

    # Read baseline message count
    baseline_count = 0
    if Path(bus.path).exists():
        with open(bus.path) as f:
            baseline_count = sum(1 for _ in f)

    print(f"📊 Baseline Messages: {baseline_count}")
    print("\n" + "=" * 80)
    print("INJECTING BENCHMARK TASKS")
    print("=" * 80)

    # Inject all tasks
    for idx, task in enumerate(BENCHMARK_TASKS, start=1):
        signal_data = {
            "task_id": task["task_id"],
            "pattern": "benchmark_task",
            "priority": task["priority"],
            "source": "benchmark",
            "task_type": task["task_type"],
            "description": task["description"],
            "file": task["file"],
            "expected_tier": task["expected_tier"],
            "injected_at": datetime.now().isoformat(),
        }

        bus.publish("ORCHESTRATOR", "IMPROVEMENT_SIGNAL", signal_data)

        print(f"\n✅ Task {idx}/10: {task['task_id']}")
        print(f"   Type: {task['task_type']}")
        print(f"   Description: {task['description']}")
        print(f"   Expected Tier: {task['expected_tier']}")

        # Small delay between tasks to prevent race conditions
        time.sleep(0.5)

    print("\n" + "=" * 80)
    print("ALL TASKS INJECTED - MONITORING PHASE")
    print("=" * 80)
    print(f"\n📊 Expected Messages: {baseline_count + 10} (baseline + 10 tasks)")
    print("📝 Log File: /tmp/trinity.jsonl")
    print(f"🔍 Trinity Process: PID {get_trinity_pid()}")

    print("\n" + "=" * 80)
    print("MONITORING INSTRUCTIONS")
    print("=" * 80)
    print("\n1. Article I Compliance (Complete Context Before Action):")
    print("   grep -i 'timeout' /tmp/trinity.jsonl | grep -i 'retry'")
    print("   grep -E 'LOCAL.*FAILED|ESCALAT' /tmp/trinity.jsonl")

    print("\n2. Article II Compliance (100% Verification and Stability):")
    print("   grep 'EXECUTOR_COMPLETE\\|EXECUTOR_FAILED' /tmp/trinity.jsonl | tail -20")
    print("   tail -100 /tmp/trinity.jsonl | grep -E 'timestamp|EXECUTOR'")

    print("\n3. Article V Compliance (Spec-Driven Development):")
    print(
        "   grep 'task_type' /tmp/trinity.jsonl | grep -E 'CODE_FIX|TEST_GENERATION|ARCHITECTURE|VERIFICATION|GENERAL'"
    )

    print("\n4. Real-time monitoring:")
    print("   tail -f /tmp/trinity.jsonl")

    print("\n5. Trinity process logs:")
    print("   tail -f ~/.trinity-local/logs/trinity_local/trinity.log")

    print("\n" + "=" * 80)
    print("✅ BENCHMARK INJECTION COMPLETE")
    print("=" * 80)
    print("\nWait 5-10 minutes for Trinity to process all tasks, then run analysis:")
    print("  python scripts/analyze_benchmark_results.py")


def get_trinity_pid():
    """Get Trinity process PID."""
    import subprocess

    try:
        result = subprocess.run(
            ["pgrep", "-f", "trinity_protocol.core.orchestrator"], capture_output=True, text=True
        )
        return result.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


if __name__ == "__main__":
    inject_benchmark_tasks()
