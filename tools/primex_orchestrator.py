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

# Import agents for PrimeCCCAgent implementation
try:
    from planner_agent.planner_agent import create_planner_agent
    from coding_agent.coding_agent import create_coding_agent
    from test_generator_agent.test_generator_agent import create_test_generator_agent
    from shared.agent_context import create_agent_context
    from shared.model_policy import agent_model
except ImportError:
    create_planner_agent = None  # type: ignore
    create_coding_agent = None  # type: ignore
    create_test_generator_agent = None  # type: ignore

import subprocess


class PrimeCCCAgent:
    """
    PrimeCCC Agent - Autonomous development agent for Night Shift.

    Orchestrates: Planner → Coder → Test Generator → Smoke Tests → Git Commit

    Methods:
        execute(task): Main workflow execution
    """

    def __init__(self, agent_context: Optional[Any] = None):
        """
        Initialize PrimeCCC agent.

        Args:
            agent_context: Shared agent context for memory/learning
        """
        if agent_context is None and create_agent_context:
            agent_context = create_agent_context(session_id=f"primeccc-{uuid.uuid4().hex[:8]}")

        self.context = agent_context

        # Initialize agents if available
        self.planner = None
        self.coder = None
        self.test_generator = None

        if create_planner_agent and agent_model:
            self.planner = create_planner_agent(
                model=agent_model("planner"),
                reasoning_effort="high",
                agent_context=agent_context
            )

        if create_coding_agent and agent_model:
            self.coder = create_coding_agent(
                model=agent_model("coder"),
                reasoning_effort="medium",
                agent_context=agent_context
            )

        if create_test_generator_agent and agent_model:
            self.test_generator = create_test_generator_agent(
                model=agent_model("test_generator"),
                reasoning_effort="medium",
                agent_context=agent_context
            )

    def execute(self, task: Any) -> dict[str, Any]:
        """
        Execute feature/bug fix workflow.

        Workflow:
            1. Planner: Generate plan from task description
            2. Coder: Implement the plan
            3. Test Generator: Generate tests if needed
            4. Run smoke tests
            5. Git commit to nightshift-auto branch
            6. Return results

        Args:
            task: Task object with title/description

        Returns:
            dict: {"success": bool, "pr_url": str | None, "tests_passed": bool, "commit_sha": str | None, "error": str | None, "files_changed": list[str]}
        """
        try:
            logger.info(f"PrimeCCCAgent executing task: {task.title}")

            # Validate agents are available
            if not all([self.planner, self.coder]):
                return {
                    "success": False,
                    "error": "Required agents not available (planner, coder)",
                    "tests_passed": False,
                    "commit_sha": None,
                    "pr_url": None,
                    "files_changed": []
                }

            # Phase 1: Planning
            logger.info("Phase 1: Generating plan...")
            plan_prompt = f"""Create implementation plan for task:

Title: {task.title}
Description: {task.description}
Type: {task.task_type}

Generate a concise implementation plan including:
1. Files to modify/create
2. Key changes needed
3. Test strategy

Keep the plan focused and actionable."""

            plan_result = self.planner.run(plan_prompt)
            logger.info(f"Plan generated: {len(str(plan_result))} chars")
            plan_text = str(plan_result)

            # Phase 2: Implementation
            logger.info("Phase 2: Implementing solution...")
            code_prompt = f"""Implement the following task BY EDITING ACTUAL SOURCE FILES:

Task: {task.title}
Description: {task.description}

Plan:
{plan_result}

CRITICAL: You have file editing tools (Read, Write, Edit, MultiEdit).
USE THEM to make ACTUAL code changes to the repository.

DO NOT just output code as text - make real file edits.

Output format (repeat for each file you modify):
File: relative/path/to/file.py
```python
<complete file contents>
```

Requirements:
1. Use Read tool to understand existing files
2. Use Write/Edit tools to create/modify files
3. Follow TDD: Write tests FIRST
4. Implement minimal code to pass tests
5. Use Result<T,E> pattern for error handling
6. No Dict[Any, Any] - use Pydantic models
7. Functions < 50 lines

Implement the solution now by EDITING FILES."""

            code_result = self.coder.run(code_prompt)
            logger.info(f"Implementation complete: {len(str(code_result))} chars")
            code_text = str(code_result)

            logger.info("Applying generated file changes...")
            apply_result = self._apply_generated_changes(code_text)
            if not apply_result["success"]:
                logger.error(f"Failed to apply generated changes: {apply_result['error']}")
                return {
                    "success": False,
                    "error": apply_result["error"],
                    "tests_passed": False,
                    "commit_sha": None,
                    "pr_url": None,
                    "files_changed": []
                }
            logger.info(f"Applied files: {apply_result['files_changed']}")

            # Verify that source files were actually modified (not just text output)
            logger.info("Verifying source files were modified...")
            verification = self._verify_source_files_changed()
            if not verification["success"]:
                logger.error(f"Source file verification failed: {verification['error']}")
                return {
                    "success": False,
                    "error": verification["error"],
                    "tests_passed": False,
                    "commit_sha": None,
                    "pr_url": None,
                    "files_changed": []
                }

            logger.info(f"Verified source files modified: {verification['files_changed']}")

            # Phase 3: Run smoke tests
            logger.info("Phase 3: Running smoke tests...")
            test_result = self._run_smoke_tests()

            if not test_result["success"]:
                return {
                    "success": False,
                    "error": f"Smoke tests failed: {test_result['error']}",
                    "tests_passed": False,
                    "commit_sha": None,
                    "pr_url": None,
                    "files_changed": []
                }

            logger.info(f"Smoke tests passed: {test_result['tests_passed']}/{test_result['tests_total']}")

            # Materialize agent output to ensure commits have meaningful content
            materialize_result = self._materialize_changes(task, plan_text, code_text)
            if not materialize_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to write generated output: {materialize_result['error']}",
                    "tests_passed": True,
                    "commit_sha": None,
                    "pr_url": None,
                    "files_changed": []
                }

            # Phase 4: Git commit
            logger.info("Phase 4: Committing changes...")
            commit_result = self._commit_changes(task)

            if not commit_result["success"]:
                return {
                    "success": False,
                    "error": f"Git commit failed: {commit_result['error']}",
                    "tests_passed": True,  # Tests passed, but commit failed
                    "commit_sha": None,
                    "pr_url": None,
                    "files_changed": commit_result.get("files_changed", [])
                }

            logger.info(f"Changes committed: {commit_result['commit_sha']}")

            return {
                "success": True,
                "tests_passed": True,
                "commit_sha": commit_result["commit_sha"],
                "pr_url": None,  # No PRs for now (per user requirement)
                "files_changed": commit_result["files_changed"],
                "error": None
            }

        except Exception as e:
            logger.error(f"PrimeCCCAgent execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tests_passed": False,
                "commit_sha": None,
                "pr_url": None,
                "files_changed": []
            }

    def _run_smoke_tests(self) -> dict[str, Any]:
        """
        Run smoke test suite.

        Returns:
            dict: {"success": bool, "tests_passed": int, "tests_total": int, "error": str | None}
        """
        try:
            # Run smoke tests
            result = subprocess.run(
                ["python", "run_tests.py", "--smoke"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse test results from output
            # Look for pytest summary line like: "=== 42 passed in 12.34s ==="
            output = result.stdout + result.stderr

            if result.returncode == 0:
                # Tests passed
                return {
                    "success": True,
                    "tests_passed": self._extract_test_count(output, "passed"),
                    "tests_total": self._extract_test_count(output, "passed"),
                    "error": None
                }
            else:
                # Tests failed
                return {
                    "success": False,
                    "tests_passed": self._extract_test_count(output, "passed"),
                    "tests_total": self._extract_test_count(output, "passed") + self._extract_test_count(output, "failed"),
                    "error": f"Test failures detected. Exit code: {result.returncode}"
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tests_passed": 0,
                "tests_total": 0,
                "error": "Smoke tests timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "success": False,
                "tests_passed": 0,
                "tests_total": 0,
            "error": str(e)
        }

    def _materialize_changes(self, task: Any, plan_text: str, code_text: str) -> dict[str, Any]:
        """
        Persist generated plan/code to the repository so commits have content.

        In the absence of direct code edits from the agent, we write a trace file
        capturing the plan and code output. This enables autonomous commits while
        preserving what the agents produced for later review.
        """
        try:
            target_dir = Path("autogenerated/primeccc")
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / f"{task.id}.md"
            timestamp = datetime.now().isoformat()

            content = [
                f"# PrimeCCC Artifact for Task: {task.title}",
                f"- Task ID: {task.id}",
                f"- Created: {timestamp}",
                f"- Type: {task.task_type}",
                f"- Priority: {task.priority}",
                "",
                "## Plan",
                plan_text,
                "",
                "## Code",
                code_text,
                "",
            ]
            target_file.write_text("\n".join(content))
            return {"success": True, "files": [str(target_file)]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _apply_generated_changes(self, code_text: str) -> dict[str, Any]:
        """
        Parse coder output and apply file edits in the repo.

        Expects repeated blocks:
        File: path/to/file.py
        ```python
        ... contents ...
        ```
        """
        try:
            repo_root = Path.cwd().resolve()
            files = self._parse_file_blocks(code_text)
            if not files:
                return {
                    "success": False,
                    "error": "Coder output did not include any 'File: <path>' blocks with code fences. Ensure the output follows the required format.",
                    "files_changed": []
                }

            written: list[str] = []
            for rel_path, contents in files:
                target_path = Path(rel_path)
                if not target_path.is_absolute():
                    target_path = (repo_root / target_path).resolve()
                if not str(target_path).startswith(str(repo_root)):
                    return {
                        "success": False,
                        "error": f"Refusing to write outside repository root: {rel_path}",
                        "files_changed": []
                    }
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(contents)
                written.append(str(target_path.relative_to(repo_root)))

            return {"success": True, "files_changed": written}
        except Exception as e:
            return {"success": False, "error": f"Failed to apply generated changes: {e}", "files_changed": []}

    def _parse_file_blocks(self, code_text: str) -> list[tuple[str, str]]:
        """
        Extract (path, contents) tuples from structured coder output.
        """
        lines = code_text.splitlines()
        blocks: list[tuple[str, str]] = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.lower().startswith("file:"):
                rel_path = line.split(":", 1)[1].strip()
                i += 1
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
                if i >= len(lines) or not lines[i].strip().startswith("```"):
                    raise ValueError(f"Missing code fence after File: {rel_path}")
                i += 1
                content_lines = []
                while i < len(lines) and not lines[i].startswith("```"):
                    content_lines.append(lines[i])
                    i += 1
                if i >= len(lines):
                    raise ValueError(f"Unterminated code fence for {rel_path}")
                blocks.append((rel_path, "\n".join(content_lines).rstrip() + "\n"))
                i += 1
            else:
                i += 1
        return blocks

    def _verify_source_files_changed(self) -> dict[str, Any]:
        """
        Verify that source code files (not just artifacts) were modified.

        This prevents artifact-only commits where only markdown files in
        autogenerated/primeccc/ are changed without actual code changes.

        Returns:
            dict with:
                - success: bool (True if source files changed)
                - files_changed: list of source file paths
                - error: str (error message if no source files changed)
        """
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True,
                cwd=Path.cwd()
            )

            # Parse changed files, excluding artifacts and temporary files
            changed_files = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                # Status markers are first 2 chars, then space, then file path
                file_path = line[3:] if len(line) > 3 else ""

                # Skip autogenerated artifacts and temporary files
                if file_path and not any([
                    file_path.startswith('autogenerated/'),
                    file_path.endswith('.pyc'),
                    file_path.endswith('__pycache__'),
                    '.tmp' in file_path
                ]):
                    changed_files.append(file_path)

            if not changed_files:
                return {
                    "success": False,
                    "error": (
                        "Agent did not modify any source files. "
                        "Only text output or autogenerated artifacts were created. "
                        "The agent must use file editing tools (Read, Write, Edit) "
                        "to make actual code changes."
                    ),
                    "files_changed": []
                }

            return {
                "success": True,
                "files_changed": changed_files,
                "error": None
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to verify file changes (git status failed): {e}",
                "files_changed": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to verify file changes: {e}",
                "files_changed": []
            }

    def _extract_test_count(self, output: str, status: str) -> int:
        """
        Extract test count from pytest output.

        Args:
            output: pytest stdout/stderr
            status: "passed" or "failed"

        Returns:
            int: Number of tests with given status
        """
        import re

        # Look for patterns like "42 passed" or "5 failed"
        pattern = rf"(\d+) {status}"
        match = re.search(pattern, output)

        if match:
            return int(match.group(1))
        return 0

    def _commit_changes(self, task: Any) -> dict[str, Any]:
        """
        Commit changes to nightshift-auto branch.

        Args:
            task: Task object

        Returns:
            dict: {"success": bool, "commit_sha": str | None, "files_changed": list[str], "error": str | None}
        """
        try:
            # Ensure we're on nightshift-auto branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10
            )

            current_branch = branch_result.stdout.strip()

            if current_branch != "nightshift-auto":
                # Create or switch to nightshift-auto branch
                subprocess.run(
                    ["git", "checkout", "-B", "nightshift-auto"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=True
                )

            # Get list of changed files
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )

            files_changed = []
            for line in status_result.stdout.strip().split("\n"):
                if line.strip():
                    # Format: " M file.py" or "?? file.py"
                    files_changed.append(line[3:].strip())

            if not files_changed:
                return {
                    "success": True,
                    "commit_sha": "no-changes",
                    "files_changed": [],
                    "error": None
                }

            # Stage all changes
            subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )

            # Commit with task info
            commit_message = f"""feat(nightshift): {task.title}

{task.description[:200]}

Task ID: {task.id}
Task Type: {task.task_type}
Automated by: Night Shift + PrimeCCCAgent"""

            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )

            # Get commit SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )

            commit_sha = sha_result.stdout.strip()

            return {
                "success": True,
                "commit_sha": commit_sha,
                "files_changed": files_changed,
                "error": None
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "commit_sha": None,
                "files_changed": [],
                "error": f"Git command failed: {e.stderr if e.stderr else str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "commit_sha": None,
                "files_changed": [],
                "error": str(e)
            }


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
