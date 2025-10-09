#!/usr/bin/env python3
"""
Test 4-Agent Cross-Machine Coordination
Creates 8 simple tasks to verify all 4 agents work together
"""

import sys
from pathlib import Path

# Add Agency to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from meta_learning.task_queue import Task, TaskQueue


def create_test_tasks():
    """Create 8 simple test tasks for 4-agent coordination"""

    queue = TaskQueue()

    tasks = [
        Task(
            task_id=f"test-task-{i}",
            type="test",
            description=f"Test task {i} - Simple validation",
            files_to_modify=[f"test_output_{i}.txt"],
            dependencies=[],
            priority=10 - i,
            status="pending",
        )
        for i in range(1, 9)
    ]

    print("=" * 60)
    print("🧪 4-Agent Coordination Test")
    print("=" * 60)
    print(f"\nCreating {len(tasks)} test tasks...")
    print("Expected distribution:")
    print("  - M4 Pro: 4 tasks (m4pro-agent1: 2, m4pro-agent2: 2)")
    print("  - MacBook Air: 4 tasks (mba-agent1: 2, mba-agent2: 2)")
    print(f"\nQueue file: {queue.queue_file}")
    print()

    # Add tasks to queue
    queue.add_tasks_batch(tasks)

    print(f"✅ {len(tasks)} tasks added to queue!")
    print()
    print("Watch your agent terminals - they should start claiming tasks!")
    print()
    print("Monitor progress:")
    print(
        '  python -c "import sys; sys.path.insert(0, \'/Users/am/Code/Agency\'); from meta_learning.task_queue import TaskQueue; q = TaskQueue(); s = q.get_status(); print(f\'Pending: {s[\\"pending\\"]}, In Progress: {s[\\"in_progress\\"]}, Completed: {s[\\"completed\\"]}\')"'
    )
    print()
    print("=" * 60)


if __name__ == "__main__":
    create_test_tasks()
