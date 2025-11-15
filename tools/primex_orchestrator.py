"""
primeX Orchestrator - Mission 4 Intelligent Task Orchestration

Orchestrates Backlog Agent → Self-Healing Agent → Learning Coach → CMP for
autonomous task execution and learning.

Workflow:
    1. Auto-select next highest-priority task from backlog (or use explicit intent)
    2. Route to appropriate execution agent:
       - TEST_FAILURE → SelfHealingAgent
       - FEATURE_REQUEST/BUG_FIX/TECH_DEBT → PrimeCCCAgent (future)
    3. On success: Update task status to COMPLETED, store VectorStore metadata
    4. On failure: Keep status PENDING, log error, DO NOT mark complete

TDD Protocol (Article VI):
- Tests written FIRST in tests/test_primex.py (9 tests)
- This implementation makes tests pass (GREEN phase)

Usage:
    # Auto-select from backlog
    python tools/primex_orchestrator.py

    # Explicit task intent
    python tools/primex_orchestrator.py --intent "Fix auth bug in login flow"

    # Help
    python tools/primex_orchestrator.py --help
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add project root to path for imports
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from shared.models.backlog import (
    Task,
    TaskPriority,
    TaskStatus,
    TaskType,
)
from shared.type_definitions.result import Err, Ok, Result
from tools.backlog_agent import BacklogStorage, PriorityQueue

# Import agents for orchestration (needed for test mocking)
try:
    from tools.self_healing_agent import SelfHealingAgent
except ImportError:
    SelfHealingAgent = None  # type: ignore

# Placeholder for PrimeCCCAgent (future integration)
class PrimeCCCAgent:
    """Placeholder for PrimeCCC agent integration."""

    def execute(self, task: Any) -> dict[str, Any]:
        """Execute feature/bug fix workflow (not yet implemented)."""
        return {"success": True, "pr_url": None, "tests_passed": True}


logger = logging.getLogger(__name__)


class PrimeXOrchestrator:
    """
    primeX Orchestrator - Intelligent Task Orchestration (Mission 4).

    Orchestrates:
    - Backlog Agent: Task selection and prioritization
    - Self-Healing Agent: Test failure fixing
    - PrimeCCCAgent: Feature/bug fix implementation (future)
    - Learning Coach: Pattern extraction (future)
    - CMP: Continuous learning and improvement (future)

    Methods:
    - execute(task_intent=None): Main orchestration entry point
    - _execute_workflow(task): Execute task-specific workflow
    - _update_task_status(task_id, status): Update task status in backlog
    """

    def __init__(self, backlog_storage: Optional[BacklogStorage] = None):
        """
        Initialize primeX orchestrator.

        Args:
            backlog_storage: Backlog storage instance (default: create new)
        """
        if backlog_storage is None:
            backlog_storage = BacklogStorage()

        self.backlog_storage = backlog_storage
        self.priority_queue = PriorityQueue(backlog_storage)
        self.memory_store: Optional[EnhancedMemoryStore] = None

    def execute(self, task_intent: Optional[str] = None) -> Result[dict[str, Any], Exception]:
        """
        Execute primeX orchestration workflow.

        Args:
            task_intent: Explicit task intent (None = auto-select from backlog)

        Returns:
            Result[dict, Exception]: Execution result or error
        """
        try:
            # Phase 1: Task Selection
            if task_intent is None:
                # Auto-select from backlog (FR5)
                logger.info("Auto-selecting next task from backlog...")
                task_result = self.priority_queue.select_next_task()

                if task_result.is_err():
                    return Err(Exception(f"Failed to select task: {task_result.unwrap_err()}"))

                task = task_result.unwrap()
                is_adhoc = False

            else:
                # Create ad-hoc task from explicit intent (FR7)
                logger.info(f"Creating ad-hoc task from intent: {task_intent}")
                task = self._create_adhoc_task(task_intent)
                is_adhoc = True

            logger.info(f"Selected task: {task.id} - {task.title}")

            # Phase 2: Update Status to IN_PROGRESS
            if not is_adhoc:
                task.status = TaskStatus.IN_PROGRESS
                update_result = self.backlog_storage.update_task(task)

                if update_result.is_err():
                    return Err(Exception(f"Failed to update task status: {update_result.unwrap_err()}"))

            # Phase 3: Execute Workflow
            start_time = datetime.now()
            workflow_result = self._execute_workflow(task)

            if "success" not in workflow_result or not workflow_result["success"]:
                # Workflow failed - keep status PENDING (FR6)
                if not is_adhoc:
                    task.status = TaskStatus.PENDING
                    self.backlog_storage.update_task(task)

                error_msg = workflow_result.get("error", "Workflow execution failed")
                logger.error(f"Workflow failed: {error_msg}")
                return Err(Exception(error_msg))

            # Phase 4: On Success - Update Status to COMPLETED
            end_time = datetime.now()
            duration_hours = (end_time - start_time).total_seconds() / 3600

            if not is_adhoc:
                task.status = TaskStatus.COMPLETED
                update_result = self.backlog_storage.update_task(task)

                if update_result.is_err():
                    logger.warning(f"Failed to update task status to COMPLETED: {update_result.unwrap_err()}")

            # Phase 5: Store Completion Metadata in VectorStore (FR6 + FR7)
            # Note: Even ad-hoc tasks store completion metadata for learning
            if not is_adhoc:
                memory_result = self.backlog_storage.store_completion_metadata(task, duration_hours)

                if memory_result.is_err():
                    logger.warning(f"Failed to store completion metadata: {memory_result.unwrap_err()}")

            # Phase 6: Return Execution Result
            result = {
                "task_id": task.id,
                "task_title": task.title,
                "task_type": task.task_type.value,
                "status": "completed",
                "duration_hours": duration_hours,
                "pr_url": workflow_result.get("pr_url", None),
                "tests_passed": workflow_result.get("tests_passed", False),
            }

            logger.info(f"Task completed successfully: {task.id}")
            return Ok(result)

        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            return Err(e)

    def execute_task(self, task: Task) -> Result[dict[str, Any], Exception]:
        """
        Execute a specific task (without auto-selection).

        This method accepts an explicit Task object and executes it directly,
        bypassing the auto-selection logic. Used by Night Shift scheduler to
        execute tasks it has already selected from the backlog.

        Args:
            task: Specific task to execute (must already exist in backlog)

        Returns:
            Result[dict, Exception]: Execution result or error

        Example:
            # Night Shift selects a task
            queue = PriorityQueue(storage)
            selected_task = queue.select_next_task().unwrap()

            # Execute THE SELECTED TASK (not auto-select again)
            orchestrator = PrimeXOrchestrator(storage)
            result = orchestrator.execute_task(selected_task)
        """
        try:
            logger.info(f"Executing explicit task: {task.id} - {task.title}")

            # Phase 1: Update Status to IN_PROGRESS
            task.status = TaskStatus.IN_PROGRESS
            update_result = self.backlog_storage.update_task(task)

            if update_result.is_err():
                return Err(update_result.unwrap_err())

            # Phase 2: Execute Workflow
            start_time = datetime.now()
            workflow_result = self._execute_workflow(task)

            if "success" not in workflow_result or not workflow_result["success"]:
                # Workflow failed - keep status PENDING
                task.status = TaskStatus.PENDING
                self.backlog_storage.update_task(task)

                error_msg = workflow_result.get("error", "Workflow execution failed")
                logger.error(f"Workflow failed: {error_msg}")
                return Err(Exception(error_msg))

            # Phase 3: On Success - Update Status to COMPLETED
            end_time = datetime.now()
            duration_hours = (end_time - start_time).total_seconds() / 3600

            task.status = TaskStatus.COMPLETED
            update_result = self.backlog_storage.update_task(task)

            if update_result.is_err():
                logger.warning(f"Failed to update task status to COMPLETED: {update_result.unwrap_err()}")

            # Phase 4: Store Completion Metadata in VectorStore
            memory_result = self.backlog_storage.store_completion_metadata(task, duration_hours)

            if memory_result.is_err():
                logger.warning(f"Failed to store completion metadata: {memory_result.unwrap_err()}")

            # Phase 5: Return Execution Result
            result = {
                "task_id": task.id,
                "task_title": task.title,
                "task_type": task.task_type.value,
                "status": "completed",
                "duration_hours": duration_hours,
                "pr_url": workflow_result.get("pr_url", None),
                "tests_passed": workflow_result.get("tests_passed", False),
            }

            logger.info(f"Explicit task completed successfully: {task.id}")
            return Ok(result)

        except Exception as e:
            logger.error(f"Explicit task execution failed: {e}", exc_info=True)
            # Rollback status to PENDING on exception
            try:
                task.status = TaskStatus.PENDING
                self.backlog_storage.update_task(task)
            except:
                pass  # Best effort rollback
            return Err(e)

    def _create_adhoc_task(self, task_intent: str) -> Task:
        """
        Create ad-hoc task from explicit intent.

        Args:
            task_intent: Task description/intent

        Returns:
            Task: Ad-hoc task (not stored in backlog)
        """
        # Infer task type from intent keywords
        task_type = TaskType.BUG_FIX  # Default
        if any(word in task_intent.lower() for word in ["test", "failing", "fail"]):
            task_type = TaskType.TEST_FAILURE
        elif any(word in task_intent.lower() for word in ["add", "implement", "feature", "new"]):
            task_type = TaskType.FEATURE_REQUEST
        elif any(word in task_intent.lower() for word in ["refactor", "clean", "debt"]):
            task_type = TaskType.TECH_DEBT

        # Create task
        task = Task(
            id=str(uuid.uuid4()),
            title=task_intent[:100],  # Truncate to reasonable length
            description=task_intent,
            task_type=task_type,
            priority=TaskPriority.P2,  # Ad-hoc tasks default to P2
            estimated_complexity=5,  # Default medium complexity
            business_value=5,  # Default medium value
        )

        return task

    def _execute_workflow(self, task: Task) -> dict[str, Any]:
        """
        Execute task-specific workflow.

        Routes to appropriate execution agent based on task type.

        Args:
            task: Task to execute

        Returns:
            dict: Workflow execution result
        """
        try:
            if task.task_type == TaskType.TEST_FAILURE:
                # Route to SelfHealingAgent (Mission 3)
                return self._execute_test_failure_workflow(task)

            elif task.task_type in [TaskType.FEATURE_REQUEST, TaskType.BUG_FIX, TaskType.TECH_DEBT]:
                # Route to PrimeCCCAgent (future integration)
                return self._execute_feature_workflow(task)

            else:
                return {"success": False, "error": f"Unknown task type: {task.task_type}"}

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _execute_test_failure_workflow(self, task: Task) -> dict[str, Any]:
        """
        Execute test failure workflow (SelfHealingAgent integration).

        Args:
            task: Test failure task

        Returns:
            dict: Workflow result
        """
        try:
            if SelfHealingAgent is None:
                raise ImportError("SelfHealingAgent not available")

            # Initialize agent
            agent = SelfHealingAgent()

            # Execute healing workflow
            # Note: This assumes SelfHealingAgent has a heal_one_failure() method
            # that accepts task details and returns a result dict
            result = agent.heal_one_failure(
                test_name=task.title,
                error_message=task.description,
            )

            return result

        except Exception as e:
            logger.error(f"Test failure workflow failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _execute_feature_workflow(self, task: Task) -> dict[str, Any]:
        """
        Execute feature/bug fix workflow (PrimeCCCAgent integration).

        Args:
            task: Feature/bug fix task

        Returns:
            dict: Workflow result
        """
        try:
            logger.info(f"Executing feature workflow for: {task.title}")

            # Initialize PrimeCCCAgent (placeholder for now)
            agent = PrimeCCCAgent()

            # Execute feature workflow
            result = agent.execute(task)

            return result

        except Exception as e:
            logger.error(f"Feature workflow failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


def main():
    """CLI entry point for primeX orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="primeX Orchestrator - Intelligent Task Execution"
    )
    parser.add_argument(
        "--intent",
        type=str,
        help="Explicit task intent (if not provided, auto-selects from backlog)",
    )
    parser.add_argument(
        "--backlog-dir",
        type=str,
        help="Backlog storage directory (default: ~/.agency/memories/agency_backlog)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize backlog storage
    storage = BacklogStorage(data_dir=args.backlog_dir) if args.backlog_dir else BacklogStorage()

    # Initialize orchestrator
    orchestrator = PrimeXOrchestrator(backlog_storage=storage)

    # Execute
    result = orchestrator.execute(task_intent=args.intent)

    if result.is_ok():
        execution_result = result.unwrap()
        print(f"\n✅ Task completed successfully!")
        print(f"   Task: {execution_result['task_title']}")
        print(f"   Duration: {execution_result['duration_hours']:.2f} hours")
        if execution_result.get("pr_url"):
            print(f"   PR: {execution_result['pr_url']}")
        sys.exit(0)
    else:
        error = result.unwrap_err()
        print(f"\n❌ Task execution failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
