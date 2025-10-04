"""
Analyze session transcripts to extract patterns and insights.
"""

import json
import os
from datetime import datetime
from typing import cast

from agency_swarm.tools import BaseTool
from pydantic import Field

from learning_agent.json_utils import (
    is_dict,
    safe_get,
    safe_get_dict,
    safe_get_list,
    safe_get_str,
)
from shared.type_definitions.json import JSONValue


class AnalyzeSession(BaseTool):  # type: ignore[misc]
    """
    Analyzes a session transcript file to extract patterns, tool usage, and outcomes.

    This tool processes session transcript files from /logs/sessions/ to identify:
    - Tool usage patterns and frequencies
    - Error patterns and resolution strategies
    - Successful workflow sequences
    - Task completion patterns
    - Agent interaction patterns
    """

    session_file: str = Field(
        ...,
        description="Path to the session transcript file in /logs/sessions/ (absolute path or relative to /logs/sessions/)",
    )
    analysis_depth: str = Field(
        default="standard",
        description="Depth of analysis: 'basic' (overview), 'standard' (detailed), or 'comprehensive' (full analysis)",
    )

    def run(self) -> str:
        try:
            # Normalize the session file path
            if not self.session_file.startswith("/"):
                # Relative path, prepend logs/sessions
                session_path = f"/Users/am/Code/Agency/logs/sessions/{self.session_file}"
            else:
                session_path = self.session_file

            # Verify file exists
            if not os.path.exists(session_path):
                return f"Error: Session file not found at {session_path}"

            # Read and parse the session file
            with open(session_path, encoding="utf-8") as f:
                session_data = json.load(f)

            # Extract session metadata
            session_meta = {
                "session_id": session_data.get("session_id", "unknown"),
                "start_time": session_data.get("start_time"),
                "end_time": session_data.get("end_time"),
                "total_entries": len(session_data.get("entries", [])),
            }

            # Analyze based on depth
            analysis = {
                "session_metadata": session_meta,
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_depth": self.analysis_depth,
            }

            if self.analysis_depth in ["standard", "comprehensive"]:
                analysis["tool_analysis"] = self._analyze_tool_usage(session_data)
                analysis["error_analysis"] = self._analyze_error_patterns(session_data)
                analysis["workflow_analysis"] = self._analyze_workflow_patterns(session_data)

            if self.analysis_depth == "comprehensive":
                analysis["agent_interactions"] = self._analyze_agent_interactions(session_data)
                analysis["task_outcomes"] = self._analyze_task_outcomes(session_data)
                analysis["memory_usage"] = self._analyze_memory_usage(session_data)

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing session: {str(e)}"

    def _analyze_tool_usage(self, session_data: dict[str, JSONValue]) -> dict[str, JSONValue]:
        """Analyze tool usage patterns from session data."""
        entries = safe_get_list(session_data, "entries")
        tool_counts: dict[str, int] = {}
        tool_sequences: list[str] = []
        tool_errors: dict[str, int] = {}

        for entry in entries:
            if not is_dict(entry):
                continue
            tags = safe_get_list(entry, "tags")
            content = safe_get_dict(entry, "content")

            # Count tool usage
            if "tool" in tags:
                tool_name = safe_get_str(content, "tool_name", "unknown")
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                tool_sequences.append(tool_name)

                # Track tool errors
                if "error" in tags:
                    tool_errors[tool_name] = tool_errors.get(tool_name, 0) + 1

        # Calculate success rates
        tool_success_rates = {}
        for tool, total_count in tool_counts.items():
            error_count = tool_errors.get(tool, 0)
            success_rate = (total_count - error_count) / total_count if total_count > 0 else 0
            tool_success_rates[tool] = success_rate

        return {
            "tool_usage_counts": cast(dict[str, JSONValue], tool_counts),
            "tool_success_rates": cast(dict[str, JSONValue], tool_success_rates),
            "tool_error_counts": cast(dict[str, JSONValue], tool_errors),
            "most_used_tools": cast(
                list[JSONValue], sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            "tool_sequence_length": len(tool_sequences),
        }

    def _analyze_error_patterns(self, session_data: dict[str, JSONValue]) -> dict[str, JSONValue]:
        """Analyze error patterns and resolution strategies."""
        entries = safe_get_list(session_data, "entries")
        errors: list[dict[str, JSONValue]] = []
        error_types: dict[str, int] = {}
        resolution_patterns: list[dict[str, JSONValue]] = []

        for i, entry in enumerate(entries):
            if not is_dict(entry):
                continue
            tags = safe_get_list(entry, "tags")
            content = safe_get_dict(entry, "content")

            if "error" in tags:
                error_info: dict[str, JSONValue] = {
                    "timestamp": safe_get(entry, "timestamp"),
                    "error_type": safe_get_str(content, "error_type", "unknown"),
                    "tool_name": safe_get(content, "tool_name"),
                    "error_message": safe_get_str(content, "error_message", ""),
                    "entry_index": i,
                }
                errors.append(error_info)

                error_type = safe_get_str(error_info, "error_type", "unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1

                # Look for resolution patterns in next few entries
                resolution = self._find_resolution_pattern(entries, i)
                if resolution:
                    resolution_patterns.append(resolution)

        return {
            "total_errors": len(errors),
            "error_types": cast(dict[str, JSONValue], error_types),
            "error_details": cast(list[JSONValue], errors),
            "resolution_patterns": cast(list[JSONValue], resolution_patterns),
            "error_rate": len(errors) / len(entries) if entries else 0,
        }

    def _analyze_workflow_patterns(
        self, session_data: dict[str, JSONValue]
    ) -> dict[str, JSONValue]:
        """Analyze successful workflow sequences."""
        entries = safe_get_list(session_data, "entries")
        workflows: list[list[JSONValue]] = []

        # Identify workflow sequences by looking for task completion patterns
        current_workflow: list[JSONValue] = []
        for entry in entries:
            if not is_dict(entry):
                continue
            tags = safe_get_list(entry, "tags")
            content = safe_get_dict(entry, "content")

            if "task_start" in tags:
                if current_workflow:
                    workflows.append(current_workflow)
                current_workflow = [entry]
            elif current_workflow:
                current_workflow.append(entry)

                if "task_complete" in tags or "success" in tags:
                    workflows.append(current_workflow)
                    current_workflow = []

        # Analyze successful workflows
        successful_workflows = [
            w
            for w in workflows
            if any("success" in safe_get_list(e, "tags") if is_dict(e) else [] for e in w)
        ]

        return {
            "total_workflows": len(workflows),
            "successful_workflows": len(successful_workflows),
            "success_rate": len(successful_workflows) / len(workflows) if workflows else 0,
            "average_workflow_length": sum(len(w) for w in workflows) / len(workflows)
            if workflows
            else 0,
        }

    def _analyze_agent_interactions(
        self, session_data: dict[str, JSONValue]
    ) -> dict[str, JSONValue]:
        """Analyze patterns in agent-to-agent interactions."""
        entries = safe_get_list(session_data, "entries")
        interactions: dict[str, int] = {}

        for entry in entries:
            if not is_dict(entry):
                continue
            content = safe_get_dict(entry, "content")
            agent_from = safe_get(content, "agent_from")
            agent_to = safe_get(content, "agent_to")
            if agent_from and agent_to:
                interaction_key = f"{agent_from} -> {agent_to}"
                interactions[interaction_key] = interactions.get(interaction_key, 0) + 1

        return {
            "agent_interactions": cast(dict[str, JSONValue], interactions),
            "total_interactions": sum(interactions.values()),
            "most_common_interactions": cast(
                list[JSONValue], sorted(interactions.items(), key=lambda x: x[1], reverse=True)[:3]
            ),
        }

    def _analyze_task_outcomes(self, session_data: dict[str, JSONValue]) -> dict[str, JSONValue]:
        """Analyze task completion outcomes and success factors."""
        entries = safe_get_list(session_data, "entries")
        outcomes: dict[str, int] = {"success": 0, "failure": 0, "partial": 0}

        for entry in entries:
            if not is_dict(entry):
                continue
            tags = safe_get_list(entry, "tags")
            if "task_complete" in tags:
                if "success" in tags:
                    outcomes["success"] += 1
                elif "error" in tags or "failure" in tags:
                    outcomes["failure"] += 1
                else:
                    outcomes["partial"] += 1

        total_tasks = sum(outcomes.values())

        return {
            "task_outcomes": cast(dict[str, JSONValue], outcomes),
            "total_tasks": total_tasks,
            "success_rate": outcomes["success"] / total_tasks if total_tasks > 0 else 0,
        }

    def _analyze_memory_usage(self, session_data: dict[str, JSONValue]) -> dict[str, JSONValue]:
        """Analyze memory storage and retrieval patterns."""
        entries = safe_get_list(session_data, "entries")
        memory_ops: dict[str, int] = {"store": 0, "retrieve": 0, "search": 0}

        for entry in entries:
            if not is_dict(entry):
                continue
            tags = safe_get_list(entry, "tags")
            if "memory" in tags:
                content = safe_get_dict(entry, "content")
                operation = safe_get_str(content, "operation", "unknown")
                if operation in memory_ops:
                    memory_ops[operation] += 1

        return {
            "memory_operations": cast(dict[str, JSONValue], memory_ops),
            "total_memory_ops": sum(memory_ops.values()),
        }

    def _find_resolution_pattern(
        self, entries: list[JSONValue], error_index: int
    ) -> dict[str, JSONValue] | None:
        """Find resolution patterns after an error."""
        # Look at next 3 entries for resolution
        resolution_window = entries[error_index + 1 : error_index + 4]

        for entry in resolution_window:
            if not is_dict(entry):
                continue
            tags = safe_get_list(entry, "tags")
            if "success" in tags or "resolution" in tags:
                content = safe_get_dict(entry, "content")
                return {
                    "resolution_method": safe_get_str(content, "method", "unknown"),
                    "steps_to_resolution": len(resolution_window),
                }

        return None
