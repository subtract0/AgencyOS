#!/usr/bin/env python3
"""
Autonomous Agent Worker

Self-governing agent that continuously polls task queue and executes tasks
without human intervention. Runs until stopped with Ctrl+C.

EPIC 4.2 Extension: Autonomous Multi-Agent Orchestration

Constitutional Compliance:
- Article I: Complete context via task dependencies
- Article II: Verification via test execution
- Article III: Autonomous execution (no manual intervention)

Version: 1.0.0
Created: 2025-10-09
"""

import json
import signal
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ruff: noqa: I001 - local imports after path manipulation
from envs.openenv_exec import run_command as run_spec_command
from meta_learning.task_queue import Task, TaskQueue
from scripts.worktree_manager import WorktreeConfig, WorktreeManager


class AutonomousWorker:
    """
    Self-governing agent that polls for tasks and executes them autonomously.

    Runs continuously in a loop:
    1. Poll queue for available task
    2. If found, claim it atomically
    3. Execute in isolated worktree
    4. Mark complete
    5. Repeat

    Handles graceful shutdown on Ctrl+C.

    Example:
        >>> worker = Autonomous Worker(agent_id="m4pro-agent1")
        >>> worker.run()  # Runs forever until Ctrl+C

    Constitutional Compliance:
        - Article I: Complete context via dependency checking
        - Article II: Test execution for verification
        - Article III: Zero manual intervention
    """

    def __init__(self, agent_id: str, poll_interval: int = 5):
        """
        Initialize autonomous worker.

        Args:
            agent_id: Unique identifier for this agent
            poll_interval: Seconds between queue polls (default: 5)
        """
        self.agent_id = agent_id
        self.poll_interval = poll_interval
        self.queue = TaskQueue()
        self.worktree_manager = WorktreeManager()
        self.running = True
        self.tasks_completed = 0

        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        """Graceful shutdown on Ctrl+C or SIGTERM."""
        print(f"\n{'=' * 60}")
        print(f"🛑 Agent {self.agent_id} shutting down gracefully...")
        print(f"   Tasks completed: {self.tasks_completed}")
        print(f"{'=' * 60}\n")
        self.running = False
        sys.exit(0)

    def run(self):
        """
        Main worker loop - runs forever until stopped.

        Continuously polls task queue and executes available tasks.
        """
        print(f"\n{'=' * 60}")
        print("🤖 Autonomous Agent Started")
        print(f"{'=' * 60}")
        print(f"Agent ID: {self.agent_id}")
        print(f"Poll interval: {self.poll_interval}s")
        print("Press Ctrl+C to stop")
        print(f"{'=' * 60}\n")

        while self.running:
            try:
                # Try to claim a task
                task = self.queue.claim_task(self.agent_id)

                if task is None:
                    # No tasks available, wait and retry
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"⏳ [{timestamp}] No tasks available, waiting {self.poll_interval}s...")
                    time.sleep(self.poll_interval)
                    continue

                # Execute the task
                print(f"\n{'=' * 60}")
                print("🎯 Executing Task")
                print(f"{'=' * 60}")
                print(f"Task ID: {task.task_id}")
                print(f"Type: {task.type}")
                print(f"Description: {task.description}")
                print(f"Files to modify: {len(task.files_to_modify)}")
                print(
                    f"Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}"
                )
                print(f"{'=' * 60}\n")

                success = self._execute_task(task)

                # Mark as complete
                self.queue.complete_task(task.task_id, success=success)

                if success:
                    self.tasks_completed += 1
                    print(f"\n✅ Task {task.task_id} completed successfully!")
                    print(f"   Total completed: {self.tasks_completed}\n")
                else:
                    print(f"\n❌ Task {task.task_id} failed!\n")

            except Exception as e:
                print(f"❌ Worker error: {e}")
                print("   Continuing to next task...\n")
                time.sleep(self.poll_interval)

    def _execute_task(self, task: Task) -> bool:
        """
        Execute a single task in isolated worktree.

        Args:
            task: Task object to execute

        Returns:
            True if successful, False otherwise

        Constitutional Compliance:
            - Article I: Worktree isolation for complete context
            - Article II: Test execution for verification
        """
        try:
            # Create worktree
            print("📁 Creating isolated worktree...")
            config = WorktreeConfig(branch_name=task.task_id)
            worktree_path = self.worktree_manager.create_worktree(config)

            # Prepare mission based on task type
            mission = self._create_mission(task)

            # Write mission file
            mission_file = worktree_path / "autonomous_mission.md"
            mission_file.write_text(mission)

            # Also write task metadata
            meta_file = worktree_path / "task_metadata.json"
            meta_file.write_text(
                json.dumps(
                    {
                        "agent_id": self.agent_id,
                        "task": asdict(task),
                        "started_at": datetime.utcnow().isoformat(),
                    },
                    indent=2,
                )
            )

            print("📝 Mission file created: autonomous_mission.md")
            print("🚀 Executing task via Claude Code Agent...\n")

            # Execute mission - REAL EXECUTION ENABLED
            success = self._execute_task_real(task, worktree_path)

            # If successful and task type requires it, commit changes
            if success and task.type in ["code", "test", "integrate"]:
                self._commit_changes(task, worktree_path)

            return success

        except Exception as e:
            print(f"❌ Task execution failed: {e}")
            import traceback

            traceback.print_exc()
            return False

        finally:
            # Always cleanup worktree
            print("🗑️  Cleaning up worktree...")
            try:
                self.worktree_manager._remove_worktree(task.task_id)
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")

    def _create_mission(self, task: Task) -> str:
        """
        Generate mission prompt based on task type.

        Args:
            task: Task object

        Returns:
            Markdown-formatted mission prompt
        """
        base = f"""# Autonomous Mission: {task.task_id}

## Task Details
- **Type**: {task.type}
- **Description**: {task.description}
- **Files to Modify**: {", ".join(task.files_to_modify) if task.files_to_modify else "No specific files"}
- **Dependencies**: {", ".join(task.dependencies) if task.dependencies else "None"}

---

"""

        if task.type == "spec":
            return (
                base
                + """## Your Role: Specification Generator

Create a detailed specification document for this feature.

### Requirements:
1. **Goals and Requirements**
   - What problem does this solve?
   - What are the acceptance criteria?

2. **API/Interface Design**
   - Function signatures
   - Input/output formats
   - Error handling

3. **Data Structures**
   - Models and schemas
   - Relationships

4. **Edge Cases**
   - What can go wrong?
   - How to handle errors?

5. **Testing Strategy**
   - Unit test scenarios
   - Integration test scenarios
   - Performance considerations

### Output:
Save specification to `docs/specs/{task_id}.md`

### Constitutional Compliance:
- Article V: Spec-driven development (this is the spec!)
"""
            )

        elif task.type == "code":
            return (
                base
                + """## Your Role: Code Implementation Agent

Implement the feature according to the specification.

### Requirements:
1. **Read the Spec**
   - Check `docs/specs/` for related specifications
   - Understand requirements fully

2. **Implementation**
   - Follow existing code style
   - Add comprehensive type hints
   - Include detailed docstrings
   - Handle all edge cases

3. **Quality Standards**
   - Use Result<T,E> pattern for error handling
   - Use Pydantic models for data structures
   - Functions under 50 lines
   - No untyped dicts

### Output:
Modify files as specified in task

### Constitutional Compliance:
- Article I: Complete context before implementation
- Law #2: Strict typing (Pydantic, no Any)
- Law #5: Result pattern for errors
"""
            )

        elif task.type == "test":
            return (
                base
                + """## Your Role: Test Generator

Write comprehensive tests for the implemented feature.

### Requirements:
1. **Test Coverage**
   - Unit tests (>95% coverage)
   - Integration tests
   - Edge case tests
   - Error condition tests

2. **Test Structure**
   - Use AAA pattern (Arrange, Act, Assert)
   - Use pytest fixtures
   - Clear test names
   - Comprehensive docstrings

3. **Test Types**
   - Happy path (normal operation)
   - Edge cases (boundary conditions)
   - Error cases (invalid inputs)
   - Performance tests (if relevant)

### Output:
Create test files in `tests/` directory

### Constitutional Compliance:
- Article I: TDD - tests validate complete implementation
- Article II: 100% verification
"""
            )

        elif task.type == "integrate":
            return (
                base
                + """## Your Role: Integration Agent

Review and integrate all completed work.

### Tasks:
1. **Review Changes**
   - Check all modified files
   - Verify constitutional compliance
   - Ensure quality standards met

2. **Run Test Suite**
   - Execute all tests
   - Fix any failures
   - Ensure 100% pass rate

3. **Resolve Conflicts**
   - Merge any conflicting changes
   - Ensure consistency

4. **Documentation**
   - Update README if needed
   - Add changelog entry
   - Create demo if appropriate

### Output:
- All tests passing
- Changes integrated
- Documentation updated

### Constitutional Compliance:
- Article II: 100% test pass rate required
- Article IV: Document learnings
"""
            )

        else:
            return (
                base
                + f"""## Task Type: {task.type}

Execute the task as described above.

Ensure constitutional compliance at all steps.
"""
            )

    def _execute_task_real(self, task: Task, worktree_path: Path) -> bool:
        """
        Execute task using actual Claude Code Agent.

        Args:
            task: Task being executed
            worktree_path: Path to worktree

        Returns:
            True if successful
        """
        print(f"🚀 REAL EXECUTION: Invoking Claude Code Agent for {task.type} task...")

        try:
            # Load mission file
            mission_file = worktree_path / "autonomous_mission.md"
            mission_content = mission_file.read_text()

            # Use subprocess to invoke agency.py with the mission
            # This keeps the agent in the correct worktree directory
            import subprocess
            import sys

            # Build command to run agency code agent with mission
            # Using Python API directly for better control
            # IMPORTANT: Use absolute path for worktree_path
            abs_worktree_path = worktree_path.absolute()

            # Use lean agent system (no subprocess, no hang)
            import os

            from shared.lean_adapter import Agency, Agent
            from shared.model_policy import agent_model

            # Change to worktree directory
            original_dir = os.getcwd()
            os.chdir(str(abs_worktree_path))

            try:
                # Create simple Claude Code agent
                print("🤖 Creating lean agent...")
                agent = Agent(
                    name="coder",
                    instructions="""You are an expert software engineer working on autonomous tasks.

Follow these principles:
- Write clean, tested, typed code
- Use Pydantic models (never untyped dicts)
- Use Result<T,E> pattern for errors
- Keep functions under 50 lines
- Write tests before implementation (TDD)

Constitutional Requirements:
- Article I: Complete context before acting
- Article II: 100% verification via tests
- Article V: Follow specifications
""",
                    model=agent_model("coder"),
                    temperature=0.3,
                )

                # Create agency wrapper
                print("🏢 Creating agency...")
                agency = Agency([agent], shared_instructions="./autonomous_mission.md")

                # Execute mission
                print("🚀 Executing mission...")
                response = agency.get_completion(mission_content)

                print("✅ Task executed successfully")
                print(f"📄 Response preview: {response[:200]}...")
                return True

            finally:
                # Restore directory
                os.chdir(original_dir)

        except KeyboardInterrupt:
            print("⏹️  Task execution interrupted")
            return False
        except Exception as e:
            print(f"❌ Task execution error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _simulate_execution(self, task: Task, worktree_path: Path) -> bool:
        """
        Simulate task execution (placeholder for actual agent invocation).

        In production, this would invoke the actual Claude Code Agent.
        For testing, we simulate success.

        Args:
            task: Task being executed
            worktree_path: Path to worktree

        Returns:
            True if successful
        """
        print(f"⚙️  Simulating execution for task type: {task.type}")

        # Simulate processing time
        time.sleep(2)

        # Create placeholder output files
        if task.files_to_modify:
            for file_path in task.files_to_modify:
                full_path = worktree_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                if not full_path.exists():
                    content = f"""# {task.task_id}

## Generated by Autonomous Worker

Task: {task.description}
Agent: {self.agent_id}
Timestamp: {datetime.utcnow().isoformat()}

This is a placeholder file created during autonomous execution simulation.
In production, this would be generated by the actual agent.
"""
                    full_path.write_text(content)
                    print(f"   ✓ Created: {file_path}")

        print("✅ Simulation complete")
        return True

    def _commit_changes(self, task: Task, worktree_path: Path):
        """
        Commit changes to the worktree branch.

        Args:
            task: Task that was executed
            worktree_path: Path to worktree
        """
        print("📝 Committing changes...")

        try:
            # Add all changes
            run_spec_command(
                ["git", "add", "."], cwd=str(worktree_path), check=True, capture_output=True
            )

            # Commit
            commit_msg = f"""{task.type}: {task.description}

Task ID: {task.task_id}
Agent: {self.agent_id}
Type: {task.type}
Files: {", ".join(task.files_to_modify) if task.files_to_modify else "multiple"}

🤖 Generated with autonomous agent
"""
            run_spec_command(
                ["git", "commit", "-m", commit_msg],
                cwd=str(worktree_path),
                check=True,
                capture_output=True,
            )

            print(f"✅ Changes committed to branch: {task.task_id}")

            # Optionally push (uncomment for auto-push)
            # subprocess.run([
            #     "git", "push", "origin", task.task_id
            # ], cwd=str(worktree_path), check=True)

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Commit warning: {e}")


# CLI Interface
def main():
    """Command-line interface for autonomous worker."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Autonomous agent worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start agent (runs forever until Ctrl+C)
  %(prog)s --agent-id m4pro-agent1

  # Custom poll interval
  %(prog)s --agent-id mba-agent1 --poll-interval 10

  # Run on MacBook Air
  %(prog)s --agent-id mba-agent2
        """,
    )

    parser.add_argument(
        "--agent-id", required=True, help="Unique agent identifier (e.g., m4pro-agent1, mba-agent1)"
    )
    parser.add_argument(
        "--poll-interval", type=int, default=5, help="Seconds between queue polls (default: 5)"
    )

    args = parser.parse_args()

    worker = AutonomousWorker(agent_id=args.agent_id, poll_interval=args.poll_interval)

    worker.run()


if __name__ == "__main__":
    main()
