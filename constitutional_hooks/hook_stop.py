#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.0",
# ]
# ///

"""
Stop Hook: Definition of Done Validator

Blocks session end if tasks incomplete (Article V: Spec-Driven Development).

Exit codes:
  0 - Session can end, Definition of Done met
  2 - Constitutional violation, tasks incomplete
  1 - Script error
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from constitutional_hooks.config import (
    DEFINITION_OF_DONE_THRESHOLD,
    EXIT_BLOCK,
    EXIT_ERROR,
    EXIT_SUCCESS,
)
from constitutional_hooks.errors import ConstitutionalError
from constitutional_hooks.models import SessionState


def main() -> int:
    """
    Validate session completion against Definition of Done.

    Checks if sufficient tasks are completed before allowing session end.
    """
    try:
        # Read JSON from stdin
        input_data = json.load(sys.stdin)

        # Parse into Pydantic model
        session_state = SessionState(**input_data)

        # Calculate completion percentage
        total_tasks = len(session_state.tasks_total)
        completed_tasks = len(session_state.tasks_completed)

        if total_tasks == 0:
            # No tasks defined - allow session end
            return EXIT_SUCCESS

        completion_percentage = completed_tasks / total_tasks

        # Check against Definition of Done threshold
        if completion_percentage < DEFINITION_OF_DONE_THRESHOLD:
            error = ConstitutionalError(
                message=f"Definition of Done not met: {completed_tasks}/{total_tasks} tasks completed ({completion_percentage:.1%}) - threshold is {DEFINITION_OF_DONE_THRESHOLD:.0%}",
                rule_id="Article V",
            )
            sys.stderr.write(f"❌ Constitutional Violation: {error}\n")
            sys.stderr.write(f"\nIncomplete tasks:\n")
            incomplete = set(session_state.tasks_total) - set(
                session_state.tasks_completed
            )
            for task in sorted(incomplete):
                sys.stderr.write(f"  - {task}\n")
            return EXIT_BLOCK

        # Session can end
        return EXIT_SUCCESS

    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: Invalid JSON input: {e}\n")
        return EXIT_ERROR
    except Exception as e:
        sys.stderr.write(f"Error: Hook script failed: {e}\n")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
