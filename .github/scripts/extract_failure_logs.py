#!/usr/bin/env python3
"""
Extract failure logs from pytest output and format for PR comment.

Purpose: Autonomy Upgrade #1 - Auto-attach failing shard logs to PR comments
Impact: Save 3-5 min per failure, enable autonomous self-diagnosis

Usage:
    pytest tests/ -v | tee pytest_output.txt
    python extract_failure_logs.py pytest_output.txt "test-unit" > failure_report.md

Integration with CI:
    See docs/ci/AUTONOMY_UPGRADES.md for full CI integration instructions

Constitutional Compliance:
- Article I: Complete context (full error details immediately visible)
- Article II: 100% verification (agents verify failures without manual work)
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Any


def extract_failures(pytest_output: str) -> List[Dict[str, Any]]:
    """
    Extract failed test details from pytest output.

    Args:
        pytest_output: Raw pytest console output

    Returns:
        list: [{"test": "test_name", "error": "error_msg", "traceback": "..."}]
    """
    failures = []

    # Split output into sections by "FAILED" markers
    # pytest format: "FAILED tests/path/test_file.py::test_name - Error message"
    lines = pytest_output.split("\n")

    current_failure = None
    capturing_traceback = False
    traceback_lines = []

    for i, line in enumerate(lines):
        # Detect failure line
        if line.startswith("FAILED "):
            # Save previous failure if exists
            if current_failure:
                current_failure["full_traceback"] = "\n".join(traceback_lines)
                failures.append(current_failure)
                traceback_lines = []

            # Parse failure line
            # Format: "FAILED tests/path/test.py::test_name - Error message"
            match = re.match(r"FAILED\s+(.*?)\s+-\s+(.*)", line)
            if match:
                test_path = match.group(1)
                short_error = match.group(2).strip()

                current_failure = {
                    "test": test_path,
                    "short_error": short_error,
                    "full_traceback": "",
                }
                capturing_traceback = True

        # Capture traceback lines after FAILED marker
        elif capturing_traceback:
            # Stop capturing at next FAILED, PASSED, or section marker
            if line.startswith(("FAILED", "PASSED", "=", "_")):
                capturing_traceback = False
            else:
                traceback_lines.append(line)

    # Save last failure
    if current_failure:
        current_failure["full_traceback"] = "\n".join(traceback_lines).strip()[:1000]
        failures.append(current_failure)

    return failures


def format_pr_comment(failures: List[Dict[str, Any]], shard_name: str) -> str:
    """
    Format failures as GitHub PR comment markdown.

    Args:
        failures: List of failure dicts from extract_failures()
        shard_name: Name of test shard (e.g., "test-unit")

    Returns:
        str: Markdown-formatted PR comment
    """
    if not failures:
        return f"✅ **{shard_name}**: All tests passed!"

    md = f"""## ❌ {shard_name} - {len(failures)} Failure(s)

**Auto-generated failure report** (Autonomy Upgrade #1)

<details>
<summary>💡 Click to see failure details</summary>

"""

    for i, failure in enumerate(failures, 1):
        # Extract file path and test name
        test_parts = failure["test"].split("::")
        file_path = test_parts[0] if test_parts else "unknown"
        test_name = test_parts[-1] if len(test_parts) > 1 else failure["test"]

        md += f"""### {i}. `{test_name}`

**File**: `{file_path}`

**Error**: {failure['short_error']}

<details>
<summary>Full traceback</summary>

```
{failure['full_traceback']}
```

</details>

---

"""

    md += """</details>

### 🔧 Next Steps for Agents

1. Read error messages above (no log diving needed)
2. Identify root cause from traceback
3. Apply fix and verify locally: `pytest {file_path}::{test_name}`
4. Push fix and verify CI passes

### 📊 Context
- This report was auto-generated from pytest output
- See `docs/ci/AUTONOMY_UPGRADES.md` for automation details
"""

    return md


def main():
    """Main entry point for failure log extraction."""
    if len(sys.argv) != 3:
        print(
            "Usage: python extract_failure_logs.py <pytest_output.txt> <shard_name>",
            file=sys.stderr,
        )
        print("\nExample:", file=sys.stderr)
        print(
            "  pytest tests/unit -v | tee output.txt && python extract_failure_logs.py output.txt test-unit",
            file=sys.stderr,
        )
        sys.exit(1)

    output_file = Path(sys.argv[1])
    shard_name = sys.argv[2]

    if not output_file.exists():
        print(f"Error: {output_file} not found", file=sys.stderr)
        sys.exit(1)

    pytest_output = output_file.read_text()
    failures = extract_failures(pytest_output)
    comment = format_pr_comment(failures, shard_name)

    print(comment)


if __name__ == "__main__":
    main()
