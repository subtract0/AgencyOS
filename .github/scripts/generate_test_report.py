#!/usr/bin/env python3
"""
Generate detailed test report from pytest JSON output for PR comments.

Purpose: Velocity Blocker #3 fix - Auto-generated test reports for instant failure diagnosis
Impact: Saves 2-5 min per failure (no manual log diving), better team visibility

Usage:
    pytest tests/ --json-report --json-report-file=test-results.json
    python .github/scripts/generate_test_report.py test-results.json > report.md

Integration with CI:
    # In merge-guardian.yml
    - name: "Run tests with JSON output"
      run: |
        pytest tests/ --json-report --json-report-file=test-results.json

    - name: "Generate test report"
      if: always()
      run: |
        python .github/scripts/generate_test_report.py test-results.json > report.md

    - name: "Post detailed report"
      if: always()
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');
          const report = fs.readFileSync('report.md', 'utf8');
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: report
          });

Constitutional Compliance:
- Article I: Complete context (full error details in PR comment)
- Article II: 100% verification (immediate failure visibility)
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_pytest_json(json_file: Path) -> Dict[str, Any]:
    """
    Parse pytest JSON report and extract key metrics.

    Args:
        json_file: Path to pytest JSON report file

    Returns:
        dict: Parsed report with test counts and failed test details
    """
    with open(json_file) as f:
        data = json.load(f)

    failed_tests = []
    for test in data.get("tests", []):
        if test["outcome"] == "failed":
            # Extract error message from call phase
            error_msg = "Unknown error"
            if "call" in test and "longrepr" in test["call"]:
                error_msg = test["call"]["longrepr"][:500]  # Truncate to 500 chars

            failed_tests.append(
                {
                    "name": test["nodeid"],
                    "file": test["nodeid"].split("::")[0],
                    "lineno": test.get("lineno", "?"),
                    "error": error_msg,
                    "duration": test.get("duration", 0.0),
                }
            )

    summary = data.get("summary", {})
    return {
        "total": summary.get("total", 0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "skipped": summary.get("skipped", 0),
        "duration": data.get("duration", 0.0),
        "failed_tests": failed_tests,
    }


def generate_markdown_report(report: Dict[str, Any]) -> str:
    """
    Generate markdown-formatted PR comment from parsed report.

    Args:
        report: Parsed test report from parse_pytest_json()

    Returns:
        str: Markdown-formatted report for GitHub PR comment
    """
    # Header with overall status
    status_emoji = "✅" if report["failed"] == 0 else "❌"
    md = f"""## {status_emoji} Test Results

**Summary**: {report['passed']}/{report['total']} passed ({report['duration']:.1f}s)

| Metric | Count |
|--------|-------|
| ✅ Passed | {report['passed']} |
| ❌ Failed | {report['failed']} |
| ⏭️ Skipped | {report['skipped']} |
| ⏱️ Duration | {report['duration']:.1f}s |

"""

    # Failed tests section (if any)
    if report["failed"] > 0:
        md += f"""### ❌ {report['failed']} Failed Test{'s' if report['failed'] != 1 else ''}

"""
        for i, test in enumerate(report["failed_tests"], 1):
            # Create clickable link to test file (if on GitHub)
            file_link = f"`{test['file']}`"
            if test["lineno"] != "?":
                file_link = f"`{test['file']}:{test['lineno']}`"

            md += f"""<details>
<summary><strong>{i}. {test['name']}</strong> ({test['duration']:.2f}s)</summary>

**File**: {file_link}

**Error**:
```
{test['error']}
```

</details>

"""
    else:
        md += "### ✅ All Tests Passed!\n\n"
        md += "Great work! All tests are passing. 🎉\n\n"

    # Footer with helpful links
    md += """---

<sub>💡 **Tip**: Click on failed test names to see full error details</sub>
"""

    return md


def main():
    """Main entry point for test report generation."""
    if len(sys.argv) != 2:
        print("Usage: python generate_test_report.py <test-results.json>", file=sys.stderr)
        sys.exit(1)

    json_file = Path(sys.argv[1])

    if not json_file.exists():
        print(f"Error: Test results file not found: {json_file}", file=sys.stderr)
        sys.exit(1)

    try:
        report = parse_pytest_json(json_file)
        markdown = generate_markdown_report(report)
        print(markdown)
    except Exception as e:
        print(f"Error generating test report: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
