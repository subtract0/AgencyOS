#!/usr/bin/env python3
"""
Seed Backlog - Populate initial tasks for Night Shift autonomous operation.

Creates a set of P1 and P2 tasks for Night Shift to autonomously execute.
"""

import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.models.backlog import Task, TaskPriority, TaskType
from tools.backlog_agent import BacklogStorage


def seed_initial_tasks():
    """Seed backlog with initial P1/P2 tasks for autonomous operation."""
    storage = BacklogStorage()

    # Initial task set for Mission 6: Night Shift + primeX autonomous operation
    tasks = [
        # P1 Tasks (Critical - Test Failures)
        Task(
            id=str(uuid.uuid4()),
            title="Fix failing integration test: test_night_shift_cycle_execution",
            description="Integration test for Night Shift cycle execution is failing. Need to investigate and fix.",
            task_type=TaskType.TEST_FAILURE,
            priority=TaskPriority.P1,
            estimated_complexity=3,
            business_value=10,
            clade_tags=["test_failure", "integration_test", "night_shift"],
        ),
        Task(
            id=str(uuid.uuid4()),
            title="Fix failing unit test: test_auto_recovery_snapshot_creation",
            description="AutoRecovery snapshot creation test is failing. Git tag creation may be the issue.",
            task_type=TaskType.TEST_FAILURE,
            priority=TaskPriority.P1,
            estimated_complexity=2,
            business_value=9,
            clade_tags=["test_failure", "unit_test", "auto_recovery"],
        ),
        # P2 Tasks (High Priority - Features & Tech Debt)
        Task(
            id=str(uuid.uuid4()),
            title="Implement retry logic in AutoRecovery for transient failures",
            description="Add exponential backoff retry logic to AutoRecovery system for handling transient failures (timeouts, network errors).",
            task_type=TaskType.FEATURE_REQUEST,
            priority=TaskPriority.P2,
            estimated_complexity=5,
            business_value=8,
            clade_tags=["feature", "auto_recovery", "resilience"],
        ),
        Task(
            id=str(uuid.uuid4()),
            title="Add health monitoring dashboard for Night Shift status",
            description="Create a simple CLI dashboard that shows Night Shift status, task queue, recent completions, and system health.",
            task_type=TaskType.FEATURE_REQUEST,
            priority=TaskPriority.P2,
            estimated_complexity=4,
            business_value=7,
            clade_tags=["feature", "monitoring", "ux"],
        ),
        Task(
            id=str(uuid.uuid4()),
            title="Refactor PrimeXOrchestrator to use Result pattern consistently",
            description="Some methods in PrimeXOrchestrator return dicts instead of Result<T,E>. Refactor for consistency.",
            task_type=TaskType.TECH_DEBT,
            priority=TaskPriority.P2,
            estimated_complexity=3,
            business_value=6,
            clade_tags=["tech_debt", "refactoring", "result_pattern"],
        ),
        Task(
            id=str(uuid.uuid4()),
            title="Add comprehensive logging to CMP event recording",
            description="Enhance CMP event recording with structured logging for better debugging and analysis.",
            task_type=TaskType.TECH_DEBT,
            priority=TaskPriority.P2,
            estimated_complexity=2,
            business_value=5,
            clade_tags=["tech_debt", "logging", "observability"],
        ),
    ]

    # Add all tasks to backlog
    print(f"Seeding {len(tasks)} tasks to backlog...")
    for task in tasks:
        result = storage.add_task(task)
        if result.is_ok():
            print(f"✅ Added: {task.title[:60]}... [{task.priority.value}]")
        else:
            print(f"❌ Failed to add task: {result.unwrap_err()}")

    print(f"\n✅ Backlog seeded with {len(tasks)} tasks!")

    # Show summary
    all_tasks = storage.list_tasks().unwrap()
    print(f"\nBacklog Summary:")
    print(f"  Total tasks: {len(all_tasks)}")
    print(f"  P1 tasks: {sum(1 for t in all_tasks if t.priority == TaskPriority.P1)}")
    print(f"  P2 tasks: {sum(1 for t in all_tasks if t.priority == TaskPriority.P2)}")
    print(f"  Test failures: {sum(1 for t in all_tasks if t.task_type == TaskType.TEST_FAILURE)}")
    print(f"  Features: {sum(1 for t in all_tasks if t.task_type == TaskType.FEATURE_REQUEST)}")
    print(f"  Tech debt: {sum(1 for t in all_tasks if t.task_type == TaskType.TECH_DEBT)}")


if __name__ == "__main__":
    seed_initial_tasks()
