#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.0",
# ]
# ///

"""
PreToolUse Hook: Test Verification Gate

Blocks git commits/pushes if tests fail (Article II: 100% Verification).

Exit codes:
  0 - Tool use allowed, proceed
  2 - Constitutional violation, block tool use
  1 - Script error
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from constitutional_hooks.common_validators import check_git_status, check_test_results
from constitutional_hooks.config import (
    EXIT_BLOCK,
    EXIT_ERROR,
    EXIT_SUCCESS,
    GIT_COMMANDS_TO_ENFORCE,
)
from constitutional_hooks.models import ToolCall


def main() -> int:
    """
    Validate tool call against Article II and III rules.

    For git commit/push tools, verifies:
    - All tests pass (Article II)
    - Working directory is clean (Article III)
    """
    try:
        # Read JSON from stdin
        input_data = json.load(sys.stdin)

        # Parse into Pydantic model
        tool_call = ToolCall(**input_data)

        # Check if this is a git command that requires enforcement
        if tool_call.tool_name in GIT_COMMANDS_TO_ENFORCE:
            # Article II: Verify all tests pass
            test_result = check_test_results()
            if test_result.is_err():
                error = test_result.unwrap_err()
                sys.stderr.write(
                    f"❌ Constitutional Violation: Cannot {tool_call.tool_name} - {error}\n"
                )
                return EXIT_BLOCK

            # Article III: Verify clean git state
            git_result = check_git_status()
            if git_result.is_err():
                error = git_result.unwrap_err()
                sys.stderr.write(
                    f"❌ Constitutional Violation: Cannot {tool_call.tool_name} - {error}\n"
                )
                return EXIT_BLOCK

        # Tool use is allowed
        return EXIT_SUCCESS

    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: Invalid JSON input: {e}\n")
        return EXIT_ERROR
    except Exception as e:
        sys.stderr.write(f"Error: Hook script failed: {e}\n")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
