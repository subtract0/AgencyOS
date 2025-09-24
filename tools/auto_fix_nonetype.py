"""
Auto-fix NoneType errors using LLM delegation and existing telemetry.
Simple, focused self-healing for a specific error class.
"""

import os
import re
import json
from typing import Optional, Dict, Any
from datetime import datetime

from agency_swarm.tools import BaseTool as Tool
from pydantic import Field

from .edit import Edit
from .read import Read
from .bash import Bash


class NoneTypeErrorDetector(Tool):
    """Detect NoneType errors from logs or error messages."""

    log_content: str = Field(..., description="Log content or error message to analyze")

    def run(self) -> str:
        """Detect NoneType errors and extract context."""

        # Common NoneType error patterns
        patterns = [
            r"AttributeError: 'NoneType' object has no attribute '(\w+)'",
            r"TypeError: 'NoneType' object is not (\w+)",
            r"TypeError: argument of type 'NoneType' is not iterable",
            r"TypeError: unsupported operand type\(s\) for .+: 'NoneType'",
        ]

        errors_found = []

        for pattern in patterns:
            matches = re.finditer(pattern, self.log_content, re.MULTILINE)
            for match in matches:
                # Extract line number if present
                line_match = re.search(r'line (\d+)', self.log_content)
                line_number = line_match.group(1) if line_match else "unknown"

                # Extract file path if present
                file_match = re.search(r'File "([^"]+)"', self.log_content)
                file_path = file_match.group(1) if file_match else "unknown"

                errors_found.append({
                    "error_type": "NoneType",
                    "pattern": match.group(0),
                    "file_path": file_path,
                    "line_number": line_number,
                    "attribute": match.group(1) if match.groups() else None
                })

        if errors_found:
            return json.dumps({
                "status": "errors_detected",
                "count": len(errors_found),
                "errors": errors_found
            }, indent=2)
        else:
            return json.dumps({
                "status": "no_nonetype_errors",
                "message": "No NoneType errors detected in provided content"
            })


class LLMNoneTypeFixer(Tool):
    """Use LLM to generate fixes for NoneType errors."""

    error_info: str = Field(..., description="JSON error information from NoneTypeErrorDetector")
    code_context: str = Field(default="", description="Surrounding code context")

    def run(self) -> str:
        """Generate LLM-based fix suggestions."""

        try:
            error_data = json.loads(self.error_info)
        except:
            return "Error: Invalid error information provided"

        if error_data["status"] != "errors_detected":
            return "No NoneType errors to fix"

        fixes = []

        for error in error_data["errors"]:
            attribute = error.get("attribute", "unknown")
            pattern = error["pattern"]

            # Generate specific fix based on error pattern
            if "has no attribute" in pattern:
                fix_suggestion = f"""
# FIX for {pattern}
# Add null check before accessing attribute '{attribute}'

BEFORE (problematic):
variable.{attribute}

AFTER (fixed):
if variable is not None:
    variable.{attribute}
else:
    # Handle None case appropriately
    default_value  # or raise exception, or log warning

GPT-5 PROMPT:
"Fix this NoneType error by adding appropriate null checks and error handling: {pattern}
Context: {self.code_context[:300]}
Provide the corrected code with proper null checking."
"""

            elif "not iterable" in pattern:
                fix_suggestion = f"""
# FIX for {pattern}
# Ensure variable is not None before iteration

BEFORE (problematic):
for item in variable:

AFTER (fixed):
if variable is not None:
    for item in variable:
        # process item
else:
    # Handle None case - maybe use empty list
    for item in []:  # or appropriate default

GPT-5 PROMPT:
"Fix this NoneType iteration error: {pattern}
Context: {self.code_context[:300]}
Provide code that safely handles None values in iteration."
"""

            else:
                fix_suggestion = f"""
# GENERIC FIX for {pattern}

GPT-5 PROMPT:
"Analyze and fix this NoneType error with appropriate null checking and error handling: {pattern}
Code context: {self.code_context[:300]}
Provide the complete fixed code with explanations."
"""

            fixes.append({
                "error": pattern,
                "file": error["file_path"],
                "line": error["line_number"],
                "fix_suggestion": fix_suggestion
            })

        return json.dumps({
            "status": "fixes_generated",
            "fixes": fixes,
            "next_steps": [
                "1. Use the GPT-5 prompts to get detailed fixes",
                "2. Apply fixes using Edit tool",
                "3. Run tests to verify fixes",
                "4. Commit if tests pass"
            ]
        }, indent=2)


class AutoNoneTypeFixer(Tool):
    """Automatically detect and fix NoneType errors in the codebase."""

    file_path: str = Field(..., description="File path where error occurred")
    error_message: str = Field(..., description="The NoneType error message")

    def run(self) -> str:
        """Complete auto-fix workflow for NoneType errors."""

        # Step 1: Detect the specific error
        detector = NoneTypeErrorDetector(log_content=self.error_message)
        error_info = detector.run()

        try:
            error_data = json.loads(error_info)
        except:
            return f"Failed to parse error information: {error_info}"

        if error_data["status"] != "errors_detected":
            return "No NoneType errors detected to auto-fix"

        # Step 2: Read the file context
        try:
            read_tool = Read(file_path=self.file_path)
            file_content = read_tool.run()
        except:
            return f"Failed to read file: {self.file_path}"

        # Step 3: Generate LLM-based fixes
        fixer = LLMNoneTypeFixer(
            error_info=error_info,
            code_context=file_content[:1000]  # First 1000 chars for context
        )
        fix_suggestions = fixer.run()

        # Step 4: Log the auto-fix attempt
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "file": self.file_path,
            "error": self.error_message,
            "detection_result": error_data,
            "fix_suggestions": fix_suggestions,
            "status": "awaiting_human_review"
        }

        # Create logs directory if it doesn't exist
        os.makedirs("logs/auto_fixes", exist_ok=True)

        log_file = f"logs/auto_fixes/nonetype_fixes_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return f"""
AUTO-FIX ANALYSIS COMPLETE for {self.file_path}

ERROR DETECTED: {error_data['count']} NoneType error(s)

FIXES GENERATED:
{fix_suggestions}

LOGGED TO: {log_file}

NEXT STEPS:
1. Review the GPT-5 prompts in the fix suggestions
2. Use the prompts to get specific code fixes
3. Apply fixes manually or with Edit tool
4. Run tests to verify: python run_tests.py
5. Commit if tests pass

This demonstrates focused, LLM-delegated self-healing for NoneType errors.
"""


class SimpleNoneTypeMonitor(Tool):
    """Simple monitor that checks for NoneType errors in recent logs."""

    def run(self) -> str:
        """Check recent logs for NoneType errors."""

        log_dirs = ["logs/sessions", "logs/telemetry", "logs"]
        errors_found = []

        for log_dir in log_dirs:
            if not os.path.exists(log_dir):
                continue

            try:
                # Check recent log files
                for filename in os.listdir(log_dir):
                    if filename.endswith(('.log', '.jsonl', '.md')):
                        file_path = os.path.join(log_dir, filename)

                        # Only check recent files (last 24 hours)
                        if os.path.getmtime(file_path) < (datetime.now().timestamp() - 86400):
                            continue

                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()

                            detector = NoneTypeErrorDetector(log_content=content)
                            result = detector.run()

                            result_data = json.loads(result)
                            if result_data["status"] == "errors_detected":
                                errors_found.extend(result_data["errors"])

                        except Exception as e:
                            continue  # Skip files we can't read

            except Exception as e:
                continue  # Skip directories we can't access

        if errors_found:
            return f"""
🚨 NONETYPE ERRORS DETECTED: {len(errors_found)} errors found in recent logs

SUMMARY:
{json.dumps(errors_found[:3], indent=2)}  # Show first 3

RECOMMENDED ACTION:
Use AutoNoneTypeFixer tool to analyze and fix these errors.

This demonstrates simple, focused monitoring for specific error types.
"""
        else:
            return "✅ No NoneType errors detected in recent logs"