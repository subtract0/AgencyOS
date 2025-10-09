WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
E0000 00:00:1760046522.286257 3922997 alts_credentials.cc:93] ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.
This plan outlines the implementation of deterministic constitutional enforcement hooks for Agency OS, focusing on the top three priority lifecycle points.

## Agency OS: Claude Code Hooks for Constitutional Enforcement

### 1. High-Level Architecture

The existing `quality_enforcer_agent` provides post-facto, LLM-based enforcement. The new Claude Code Hooks will introduce *pre-facto*, *deterministic*, and *non-LLM* enforcement at critical lifecycle points, effectively acting as an early-exit mechanism to prevent violations before they consume expensive LLM cycles.

**Core Components:**

1.  **Agent Orchestrator:** The central execution loop of Agency OS will be modified to invoke the `HookManager` at the specified lifecycle points.
2.  **Hook Manager:** A central component responsible for registering and executing specific enforcement handlers for each lifecycle point. It will serialize payload data and invoke the appropriate UV single-file script via a subprocess call.
3.  **Enforcement Hooks (UV Scripts):** Lightweight, self-contained Python scripts for each lifecycle point (`UserPromptSubmit`, `PreToolUse`, `Stop`). These scripts will receive JSON payloads, validate them with Pydantic, apply deterministic rules (e.g., regex, file checks, task status), and return an exit code (0 for success, 2 for block).
4.  **Shared Utilities (`hooks/enforcement_rules.py`, `shared/`):** Contains the actual deterministic logic (regex patterns, test runner wrappers, task status checkers) that the UV scripts call.
5.  **Pydantic Models:** Define the structure of data passed to each hook, ensuring strong typing and validation.
6.  **Result Pattern:** A robust way to handle success or error propagation throughout the hook execution and integration.

**Execution Flow:**

`Agent Orchestrator`
  -> `Lifecycle Event Triggered (e.g., UserPromptSubmit)`
    -> `HookManager.execute_hook(lifecycle_point, payload_data)`
      -> `HookManager` serializes `payload_data` to JSON.
      -> `HookManager` spawns a `subprocess` to run the corresponding UV script (e.g., `python hooks/user_prompt_submit.py <json_payload>`).
        -> `UV Script`:
          -> Deserializes JSON to Pydantic model.
          -> Calls deterministic rules from `enforcement_rules.py`.
          -> Returns `exit code 0` (success) or `exit code 2` (block/violation).
      -> `HookManager` interprets the subprocess exit code.
      -> `HookManager` returns `Ok()` or `Err(EnforcementError)` based on the exit code.
    -> `Agent Orchestrator` receives `Result`.
      -> If `Err(EnforcementError)`: Stops agent execution, logs error, and signals the user about the blocked action (e.g., via `sys.exit(2)`).
      -> If `Ok()`: Continues with normal agent processing.

```mermaid
graph TD
    A[Agent Orchestrator] --> B{Lifecycle Event Triggered};
    B -- UserPromptSubmit --> C[HookManager.execute("UserPromptSubmit", payload)];
    B -- PreToolUse --> D[HookManager.execute("PreToolUse", payload)];
    B -- Stop --> E[HookManager.execute("Stop", payload)];

    C --> F{Serialize Payload & Invoke UV Script};
    D --> F;
    E --> F;

    F --> G[UV Script (e.g., user_prompt_submit.py)];
    G --> H[Pydantic Model Validation];
    H --> I[Enforcement Rules (e.g., check_for_banned_patterns)];
    I -- Ok --> J{Exit Code 0};
    I -- Err --> K{Exit Code 2 (Block)};

    J --> L[HookManager Returns Ok];
    K --> M[HookManager Returns Err(EnforcementError)];

    L --> N[Continue Agent Execution];
    M --> O[Block Agent Execution / Signal Error];

    subgraph Hooks
        G -- calls --> hooks_enforcement_rules.py;
    end
    subgraph Shared Infrastructure
        hooks_enforcement_rules.py -- uses --> shared_git_utils.py;
        hooks_enforcement_rules.py -- uses --> shared_task_tracker_utils.py;
    end
```

### 2. File Structure

```
agency_os/
├── core/
│   ├── orchestrator.py                 # MODIFY: Integrate HookManager calls
│   └── ...
├── hooks/
│   ├── __init__.py
│   ├── base.py                         # Defines Result pattern, base EnforcementError
│   ├── models.py                       # Pydantic models for hook payloads
│   ├── enforcement_rules.py            # Centralized deterministic enforcement logic
│   ├── hook_manager.py                 # Manages hook registration and execution
│   │
│   ├── user_prompt_submit.py           # NEW: UV script for UserPromptSubmit hook
│   ├── pre_tool_use.py                 # NEW: UV script for PreToolUse hook
│   └── stop.py                         # NEW: UV script for Stop hook
│
├── shared/
│   ├── __init__.py
│   ├── constants.py                    # Add EXIT_CODE_BLOCK = 2
│   ├── git_utils.py                    # NEW/MODIFY: Utility for running tests, git status
│   └── task_tracker_utils.py           # NEW/MODIFY: Utility for querying task status
│   └── ...
└── tests/
    ├── hooks/                          # NEW: Unit and integration tests for hooks
    │   ├── test_base.py
    │   ├── test_models.py
    │   ├── test_enforcement_rules.py
    │   ├── test_hook_manager.py
    │   ├── test_user_prompt_submit_hook.py
    │   ├── test_pre_tool_use_hook.py
    │   └── test_stop_hook.py
    └── ...
```

### 3. Key Functions/Classes Needed

#### `agency_os/hooks/base.py`

```python
import sys
from typing import TypeVar, Generic, Union, Callable

T = TypeVar("T")
E = TypeVar("E")

class Ok(Generic[T]):
    def __init__(self, value: T):
        self.value = value
    def __repr__(self):
        return f"Ok({self.value!r})"

class Err(Generic[E]):
    def __init__(self, error: E):
        self.error = error
    def __repr__(self):
        return f"Err({self.error!r})"

Result = Union[Ok[T], Err[E]]

class EnforcementError(Exception):
    """Custom exception for constitutional enforcement violations."""
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.message = message
        self.code = code
```

#### `agency_os/hooks/models.py`

```python
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path

class UserPromptSubmitPayload(BaseModel):
    """Payload for UserPromptSubmit hook."""
    prompt: str

class PreToolUsePayload(BaseModel):
    """Payload for PreToolUse hook."""
    tool_name: str
    tool_args: Dict[str, Any]
    current_project_path: Path # Path to the project directory where the tool would operate

class StopPayload(BaseModel):
    """Payload for Stop hook."""
    completed_tasks: List[str]
    remaining_tasks: List[str]
    definition_of_done: str # e.g., "All features implemented and tests pass"
```

#### `agency_os/hooks/enforcement_rules.py`

```python
import re
import subprocess
from pathlib import Path
from typing import List

from agency_os.hooks.base import Result, Ok, Err, EnforcementError
from agency_os.shared.constants import EXIT_CODE_BLOCK # Assume this is defined as 2

# Article I: Complete Context - Block invalid prompt patterns
BANNED_PROMPT_PATTERNS = [
    re.compile(r"skip\s+tests", re.IGNORECASE),
    re.compile(r"Dict\[Any,\s*Any\]", re.IGNORECASE),
    re.compile(r"ignore\s+error", re.IGNORECASE),
    re.compile(r"don't\s+care\s+about\s+quality", re.IGNORECASE),
]

def check_for_banned_patterns(prompt: str) -> Result[None, EnforcementError]:
    """Checks the user prompt against known constitutional violations."""
    for pattern in BANNED_PROMPT_PATTERNS:
        if pattern.search(prompt):
            return Err(EnforcementError(
                f"Prompt violates Article I (Complete Context): '{prompt}' contains a banned pattern: '{pattern.pattern}'"
            ))
    return Ok(None)

# Article II: 100% Verification - Block commits/pushes if tests fail
def is_test_run_successful(project_path: Path) -> Result[None, EnforcementError]:
    """
    Runs project tests and returns success/failure.
    Assumes `pytest` is configured for the project.
    """
    # This would ideally use agency_os.shared.git_utils or similar
    try:
        # Example: running pytest. Adjust command based on project setup.
        result = subprocess.run(
            ["pytest"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False # Do not raise CalledProcessError for non-zero exit codes
        )
        if result.returncode != 0:
            return Err(EnforcementError(
                f"Article II (100% Verification) violated: Tests failed in {project_path}. Output:\n{result.stderr}"
            ))
        return Ok(None)
    except FileNotFoundError:
        return Err(EnforcementError(
            f"Article II (100% Verification) cannot be checked: 'pytest' not found or not in PATH."
        ))
    except Exception as e:
        return Err(EnforcementError(
            f"Article II (100% Verification) test run failed unexpectedly: {e}"
        ))

# Definition of Done - Block session end if tasks incomplete
def are_all_tasks_completed(
    completed_tasks: List[str],
    remaining_tasks: List[str],
    definition_of_done: str
) -> Result[None, EnforcementError]:
    """
    Checks if all tasks are completed based on the Definition of Done.
    This is a simplified check; a real DoD might involve more complex logic.
    """
    if remaining_tasks:
        return Err(EnforcementError(
            f"Definition of Done not met: {len(remaining_tasks)} tasks still remaining. "
            f"Remaining: {', '.join(remaining_tasks[:3])}... DoD: '{definition_of_done}'"
        ))
    # Further checks could be added, e.g., "all tests pass" if not covered by PreToolUse
    return Ok(None)
```

#### `agency_os/hooks/hook_manager.py`

```python
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Callable, Any

from agency_os.hooks.base import Result, Ok, Err, EnforcementError
from agency_os.hooks.models import (
    UserPromptSubmitPayload, PreToolUsePayload, StopPayload
)
from agency_os.shared.constants import EXIT_CODE_BLOCK # Assume this is 2

class HookManager:
    _instance = None
    _hooks: Dict[str, Path] = {} # Map lifecycle_point to path of UV script

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HookManager, cls).__new__(cls)
            cls._instance._hooks = {
                "UserPromptSubmit": Path(__file__).parent / "user_prompt_submit.py",
                "PreToolUse": Path(__file__).parent / "pre_tool_use.py",
                "Stop": Path(__file__).parent / "stop.py",
            }
        return cls._instance

    def execute_hook(self, lifecycle_point: str, payload_data: Any) -> Result[None, EnforcementError]:
        """Executes the registered hook for a given lifecycle point."""
        script_path = self._hooks.get(lifecycle_point)
        if not script_path or not script_path.exists():
            return Err(EnforcementError(f"No hook registered or found for '{lifecycle_point}'", code=1))

        try:
            payload_json = payload_data.model_dump_json() # Use model_dump_json() for Pydantic v2+
        except AttributeError: # Fallback for non-Pydantic models if necessary, or earlier Pydantic versions
            payload_json = json.dumps(payload_data)

        try:
            # Use sys.executable to ensure the current Python interpreter is used
            result = subprocess.run(
                [sys.executable, str(script_path), payload_json],
                capture_output=True,
                text=True,
                check=False # Do not raise CalledProcessError for non-zero exit codes
            )

            if result.returncode == EXIT_CODE_BLOCK:
                error_message = result.stderr.strip() if result.stderr else f"Action blocked by {lifecycle_point} hook."
                return Err(EnforcementError(error_message, code=EXIT_CODE_BLOCK))
            elif result.returncode != 0:
                # Other non-zero exit codes indicate an internal error in the hook script
                error_message = f"Hook '{lifecycle_point}' failed with exit code {result.returncode}. " \
                                f"Stderr: {result.stderr.strip()}"
                return Err(EnforcementError(error_message, code=result.returncode))

            return Ok(None)

        except Exception as e:
            return Err(EnforcementError(f"Failed to execute hook '{lifecycle_point}': {e}", code=1))

# Singleton instance of HookManager
hook_manager = HookManager()
```

#### `agency_os/hooks/user_prompt_submit.py` (UV Single-File Script)

```python
# UV single-file script: python -c "import sys; import json; from pydantic import BaseModel; from pathlib import Path; # ... rest of code"
# For local development and to satisfy UV single-file requirements for embedded dependencies,
# these imports should be directly available or bundled.
# Assuming Pydantic and pathlib are standard or pre-installed in the UV environment.

# Embedded Pydantic models (simplified for brevity, normally imported from hooks.models)
from pydantic import BaseModel
class UserPromptSubmitPayload(BaseModel):
    prompt: str

# Embedded enforcement rules (simplified, normally imported from hooks.enforcement_rules)
import re
import sys
# Simulate Result/EnforcementError if not directly imported or embedded
class EnforcementError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.message = message
        self.code = code
BANNED_PROMPT_PATTERNS = [
    re.compile(r"skip\s+tests", re.IGNORECASE),
    re.compile(r"Dict\[Any,\s*Any\]", re.IGNORECASE),
    re.compile(r"ignore\s+error", re.IGNORECASE),
    re.compile(r"don't\s+care\s+about\s+quality", re.IGNORECASE),
]
def check_for_banned_patterns_embedded(prompt: str) -> bool: # Returns True for violation
    for pattern in BANNED_PROMPT_PATTERNS:
        if pattern.search(prompt):
            sys.stderr.write(f"Prompt violates Article I (Complete Context): '{prompt}' contains a banned pattern: '{pattern.pattern}'\n")
            return True
    return False

# Main entry point for the UV script
def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python user_prompt_submit.py <json_payload>\n")
        sys.exit(1) # General error

    try:
        payload_json = sys.argv[1]
        payload = UserPromptSubmitPayload.model_validate_json(payload_json)

        if check_for_banned_patterns_embedded(payload.prompt):
            sys.exit(2) # Block action
        
        sys.exit(0) # Success

    except Exception as e:
        sys.stderr.write(f"Error in UserPromptSubmit hook: {e}\n")
        sys.exit(1) # General error

if __name__ == "__main__":
    main()
```
*(Similar UV scripts for `pre_tool_use.py` and `stop.py` would follow, embedding their respective Pydantic models and logic, and leveraging `sys.stderr.write` for error messages that `HookManager` can capture.)*

#### `agency_os/hooks/pre_tool_use.py` (UV Single-File Script)

```python
# UV single-file script (abbreviated content for demonstration)
import sys
import json
import subprocess
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any

# Embedded Pydantic models (simplified)
class PreToolUsePayload(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any]
    current_project_path: Path

# Embedded enforcement logic (simplified, from hooks.enforcement_rules)
def is_test_run_successful_embedded(project_path: Path) -> bool: # Returns True for failure
    try:
        result = subprocess.run(["pytest"], cwd=project_path, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            sys.stderr.write(f"Article II (100% Verification) violated: Tests failed in {project_path}. Output:\n{result.stderr}\n")
            return True
        return False
    except FileNotFoundError:
        sys.stderr.write(f"Article II (100% Verification) cannot be checked: 'pytest' not found or not in PATH.\n")
        return True
    except Exception as e:
        sys.stderr.write(f"Article II (100% Verification) test run failed unexpectedly: {e}\n")
        return True

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python pre_tool_use.py <json_payload>\n")
        sys.exit(1)

    try:
        payload_json = sys.argv[1]
        payload = PreToolUsePayload.model_validate_json(payload_json)

        # Only enforce for specific tools (git commit/push)
        if payload.tool_name in ["git commit", "git push"]:
            if is_test_run_successful_embedded(payload.current_project_path):
                sys.exit(2) # Block action

        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Error in PreToolUse hook: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### `agency_os/hooks/stop.py` (UV Single-File Script)

```python
# UV single-file script (abbreviated content for demonstration)
import sys
import json
from pydantic import BaseModel
from typing import List

# Embedded Pydantic models (simplified)
class StopPayload(BaseModel):
    completed_tasks: List[str]
    remaining_tasks: List[str]
    definition_of_done: str

# Embedded enforcement logic (simplified, from hooks.enforcement_rules)
def are_all_tasks_completed_embedded(completed: List[str], remaining: List[str], dod: str) -> bool: # True for incomplete
    if remaining:
        sys.stderr.write(f"Definition of Done not met: {len(remaining)} tasks still remaining. "
                         f"Remaining: {', '.join(remaining[:3])}... DoD: '{dod}'\n")
        return True
    return False

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python stop.py <json_payload>\n")
        sys.exit(1)

    try:
        payload_json = sys.argv[1]
        payload = StopPayload.model_validate_json(payload_json)

        if are_all_tasks_completed_embedded(payload.completed_tasks, payload.remaining_tasks, payload.definition_of_done):
            sys.exit(2) # Block action

        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Error in Stop hook: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### `agency_os/shared/constants.py` (New/Modify)

```python
# ... other constants
EXIT_CODE_SUCCESS = 0
EXIT_CODE_GENERAL_ERROR = 1
EXIT_CODE_BLOCK = 2 # Action blocked by constitutional enforcement
```

#### `agency_os/shared/git_utils.py` (New/Modify)

```python
import subprocess
from pathlib import Path
from typing import Optional

def run_pytest(project_path: Path) -> subprocess.CompletedProcess:
    """Helper to run pytest in a given project directory."""
    return subprocess.run(
        ["pytest"],
        cwd=project_path,
        capture_output=True,
        text=True,
        check=False
    )

# ... other git related utilities
```

#### `agency_os/shared/task_tracker_utils.py` (New/Modify)

```python
from typing import List, Dict, Any

# Placeholder for actual task tracker integration
def get_current_task_status() -> Dict[str, List[str]]:
    """Fetches current task status from the task tracker."""
    # This would interact with the actual task tracking system (e.g., a database, API)
    return {
        "completed": [], # Example: ["Implement feature A", "Write tests for A"]
        "remaining": []  # Example: ["Implement feature B", "Fix bug C"]
    }

def get_definition_of_done() -> str:
    """Fetches the current Definition of Done from configuration."""
    return "All specified features are implemented, all tests pass, and code quality is high."
```

### 4. Testing Strategy

**TDD-First Approach:** For each component, tests will be written *before* implementation.

1.  **Unit Tests:**
    *   **`agency_os/hooks/base.py`:** Test `Result`, `Ok`, `Err` behaviors, and `EnforcementError` instantiation.
    *   **`agency_os/hooks/models.py`:** Test Pydantic model validation (e.g., valid/invalid inputs, serialization/deserialization).
    *   **`agency_os/hooks/enforcement_rules.py`:**
        *   `check_for_banned_patterns`: Test with prompts containing banned patterns (e.g., "skip tests", "Dict[Any, Any]") and valid prompts. Mock `Result` usage.
        *   `is_test_run_successful`: Mock `subprocess.run` to simulate `pytest` passing, failing, or `pytest` not found. Verify correct `Result` is returned.
        *   `are_all_tasks_completed`: Test with empty/non-empty `remaining_tasks` lists.
    *   **UV Script Logic (without subprocess invocation):** Extract the core enforcement logic from each UV script into testable functions within `enforcement_rules.py` or a dedicated test helper. Test these functions in isolation.
    *   **`agency_os/hooks/hook_manager.py`:** Mock `subprocess.run` to simulate various UV script outcomes (exit code 0, 1, 2) and verify `HookManager` returns the correct `Result`.

2.  **Integration Tests:**
    *   **UV Script Execution:** Write tests that *actually* run the UV scripts as subprocesses with sample payloads, ensuring correct exit codes and `stderr` messages are produced. This validates the `subprocess` interaction.
    *   **HookManager End-to-End:** Test `HookManager.execute_hook` for each lifecycle point, feeding it Pydantic models, and verifying it correctly invokes the UV script and interprets its output.
    *   **Orchestrator Integration Simulation:** Create a simplified `agent_orchestrator` mock that simulates an agent's lifecycle (submit prompt, use tool, attempt to stop). Inject the `HookManager` and verify that attempts to violate rules lead to `sys.exit(2)` or similar blocking behavior.

### 5. Integration Points with Existing Code

The primary integration point is the **Agent Orchestrator** (`agency_os/core/orchestrator.py` or similar main execution loop).

1.  **Initialization:**
    *   Import `hook_manager` singleton from `agency_os.hooks.hook_manager`.
    *   `hook_manager` should be ready to use immediately upon import.

2.  **`UserPromptSubmit` Hook:**
    *   **Where:** Immediately after the user's prompt is received, before any agent processing or parsing begins.
    *   **Logic:**
        ```python
        from agency_os.hooks.hook_manager import hook_manager
        from agency_os.hooks.models import UserPromptSubmitPayload
        from agency_os.hooks.base import Err
        import sys

        user_prompt = get_user_prompt_from_interface()
        payload = UserPromptSubmitPayload(prompt=user_prompt)
        result = hook_manager.execute_hook("UserPromptSubmit", payload)

        if isinstance(result, Err):
            print(f"Constitutional Violation: {result.error.message}")
            sys.exit(result.error.code) # Immediately stop the process
        # Proceed with processing the prompt
        ```

3.  **`PreToolUse` Hook:**
    *   **Where:** Just before the `Agent Orchestrator` (or a dedicated `ToolExecutor`) invokes an external tool, specifically `git commit` or `git push`.
    *   **Logic:**
        ```python
        from agency_os.hooks.hook_manager import hook_manager
        from agency_os.hooks.models import PreToolUsePayload
        from agency_os.hooks.base import Err
        from pathlib import Path
        import sys

        tool_name, tool_args = get_agent_decided_tool_action() # e.g., "git commit", {"message": "feat: new feature"}
        current_project_path = Path.cwd() # Or determined from agent context

        # Only trigger for relevant git operations
        if tool_name in ["git commit", "git push"]:
            payload = PreToolUsePayload(tool_name=tool_name, tool_args=tool_args, current_project_path=current_project_path)
            result = hook_manager.execute_hook("PreToolUse", payload)

            if isinstance(result, Err):
                print(f"Action Blocked: {result.error.message}")
                sys.exit(result.error.code)
        # Proceed with executing the tool (e.g., `subprocess.run([tool_name, ...])`)
        ```

4.  **`Stop` Hook:**
    *   **Where:** When the `Agent Orchestrator` (or the `Stop` agent itself) determines that the session should end, but *before* actually terminating.
    *   **Logic:**
        ```python
        from agency_os.hooks.hook_manager import hook_manager
        from agency_os.hooks.models import StopPayload
        from agency_os.hooks.base import Err
        from agency_os.shared.task_tracker_utils import get_current_task_status, get_definition_of_done

        if agent_decides_to_end_session():
            task_status = get_current_task_status()
            definition_of_done = get_definition_of_done()
            payload = StopPayload(
                completed_tasks=task_status["completed"],
                remaining_tasks=task_status["remaining"],
                definition_of_done=definition_of_done
            )
            result = hook_manager.execute_hook("Stop", payload)

            if isinstance(result, Err):
                print(f"Session cannot end: {result.error.message}")
                # Instead of exiting, signal the orchestrator to continue the session
                # and prompt the agent to address the incomplete tasks.
                return "CONTINUE_SESSION_REQUIRED"
        return "SESSION_CAN_END"
        ```

**Interaction with `quality_enforcer_agent`:**
The new deterministic hooks act as a first line of defense. The `quality_enforcer_agent` will still be invoked for more complex, LLM-based, and post-facto quality checks, but only *after* these deterministic checks have passed. This reduces the load on the `quality_enforcer_agent` for common, easily identifiable violations.

### 6. Risk Assessment

*   **False Positives (High):** Deterministic rules (especially regexes) can be overly broad and block legitimate actions.
    *   **Mitigation:** Carefully craft rules with extensive testing against a diverse set of real-world scenarios. Provide clear, actionable error messages. Establish a process for rule refinement and updates.
*   **Performance Overhead (Low-Medium):** Spawning a `subprocess` for each hook invocation has a small overhead.
    *   **Mitigation:** The hooks are designed to be fast and deterministic. They are only invoked at specific, critical points, not continuously. The UV scripts should be kept minimal.
*   **Complexity of UV Single-File Scripts (Medium):** Embedding dependencies like Pydantic can make scripts verbose and harder to manage if not done carefully.
    *   **Mitigation:** Use build tools (if allowed) to bundle, or carefully manage direct imports ensuring target environment has necessary libraries. Keep the actual logic within the UV scripts minimal, delegating to imported `enforcement_rules.py` where possible.
*   **Integration Challenges (Medium):** Ensuring all correct call sites in the `Agent Orchestrator` are identified and properly implement the hook calls and error handling.
    *   **Mitigation:** Thorough code review of the `Agent Orchestrator`. Develop robust integration tests that simulate full agent runs.
*   **Maintainability of Rules (Medium):** Constitutional rules can evolve. Hardcoding them in `enforcement_rules.py` requires code changes.
    *   **Mitigation:** Centralize rules. Consider external configuration (e.g., YAML) if rules become very dynamic, though for deterministic enforcement, embedded code might be preferred for guarantees.
*   **Error Handling (Medium):** Incorrect `subprocess` invocation or parsing of `stderr` could lead to missed blocks or crashes.
    *   **Mitigation:** Robust `try-except` blocks around `subprocess.run` and JSON parsing. Clear distinction between hook's internal error (exit code 1) and constitutional violation (exit code 2).

### 7. Estimated Effort (hours)

This estimation assumes a developer familiar with Python, Pydantic, and `subprocess` interactions.

1.  **Setup & Core Utilities (Result, Pydantic Models, HookManager Skeleton):**
    *   `agency_os/hooks/base.py` (Result pattern, `EnforcementError`): 2 hours
    *   `agency_os/hooks/models.py` (Pydantic payloads): 2 hours
    *   `agency_os/hooks/hook_manager.py` (Initial structure, `execute_hook` without UV script calls): 4 hours
    *   `agency_os/shared/constants.py` (add `EXIT_CODE_BLOCK`): 0.5 hours
    *   **Total: 8.5 hours**

2.  **`UserPromptSubmit` Hook:**
    *   `agency_os/hooks/enforcement_rules.py` (`check_for_banned_patterns`): 3 hours (rule design & implementation)
    *   `agency_os/hooks/user_prompt_submit.py` (UV script, embedding dependencies): 4 hours
    *   Unit Tests (`test_enforcement_rules.py`, `test_user_prompt_submit_hook.py`): 3 hours
    *   **Total: 10 hours**

3.  **`PreToolUse` Hook:**
    *   `agency_os/shared/git_utils.py` (or modify existing for test runner): 2 hours
    *   `agency_os/hooks/enforcement_rules.py` (`is_test_run_successful`): 4 hours (subprocess logic, error handling)
    *   `agency_os/hooks/pre_tool_use.py` (UV script, embedding dependencies): 4 hours
    *   Unit Tests (`test_enforcement_rules.py`, `test_pre_tool_use_hook.py`): 4 hours
    *   **Total: 14 hours**

4.  **`Stop` Hook:**
    *   `agency_os/shared/task_tracker_utils.py` (placeholder for task status/DoD): 2 hours
    *   `agency_os/hooks/enforcement_rules.py` (`are_all_tasks_completed`): 3 hours
    *   `agency_os/hooks/stop.py` (UV script, embedding dependencies): 4 hours
    *   Unit Tests (`test_enforcement_rules.py`, `test_stop_hook.py`): 3 hours
    *   **Total: 12 hours**

5.  **Agent Orchestrator Integration:**
    *   Modifying `agency_os/core/orchestrator.py` at 3 points: 6 hours
    *   **Total: 6 hours**

6.  **Integration & End-to-End Testing, Documentation:**
    *   Full system tests, verifying blocking behavior in simulated agent runs: 8 hours
    *   Refine error messages, logging: 2 hours
    *   Update technical documentation for new hook system: 4 hours
    *   **Total: 14 hours**

**Grand Total Estimated Effort: ~64.5 hours (~1.5-2 weeks)**
