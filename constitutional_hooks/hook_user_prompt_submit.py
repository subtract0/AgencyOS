#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.0",
# ]
# ///

"""
UserPromptSubmit Hook: Constitutional Gatekeeper

Blocks prompts that violate Article I (Complete Context Before Action).

Exit codes:
  0 - Prompt compliant, proceed
  2 - Constitutional violation, block prompt
  1 - Script error
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from constitutional_hooks.common_validators import validate_prompt_content
from constitutional_hooks.config import EXIT_BLOCK, EXIT_ERROR, EXIT_SUCCESS
from constitutional_hooks.models import UserPrompt


def main() -> int:
    """
    Validate user prompt against Article I rules.

    Reads UserPrompt JSON from stdin, validates against constitutional rules,
    and exits with appropriate code.
    """
    try:
        # Read JSON from stdin
        input_data = json.load(sys.stdin)

        # Parse into Pydantic model
        user_prompt = UserPrompt(**input_data)

        # Validate prompt content
        result = validate_prompt_content(user_prompt.prompt)

        if result.is_err():
            error = result.unwrap_err()
            sys.stderr.write(f"❌ Constitutional Violation: {error}\n")
            return EXIT_BLOCK

        # Prompt is compliant
        return EXIT_SUCCESS

    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: Invalid JSON input: {e}\n")
        return EXIT_ERROR
    except Exception as e:
        sys.stderr.write(f"Error: Hook script failed: {e}\n")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
