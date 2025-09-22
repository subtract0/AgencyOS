"""
Analyze session transcripts to extract patterns and insights.
"""
from agency_swarm.tools import BaseTool
from pydantic import Field
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class AnalyzeSession(BaseTool):
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
        description="Path to the session transcript file in /logs/sessions/ (absolute path or relative to /logs/sessions/)"
    )
    analysis_depth: str = Field(
        default="standard",
        description="Depth of analysis: 'basic' (overview), 'standard' (detailed), or 'comprehensive' (full analysis)"
    )

    def run(self) -> str:
        try:
            # Normalize the session file path
            if not self.session_file.startswith('/'):
                # Relative path, prepend logs/sessions
                session_path = f"/Users/am/Code/Agency/logs/sessions/{self.session_file}"
            else:
                session_path = self.session_file

            # Verify file exists
            if not os.path.exists(session_path):
                return f"Error: Session file not found at {session_path}"

            # Read and parse the session file
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Extract session metadata
            session_meta = {
                "session_id": session_data.get("session_id", "unknown"),
                "start_time": session_data.get("start_time"),
                "end_time": session_data.get("end_time"),
                "total_entries": len(session_data.get("entries", []))
            }

            # Analyze based on depth
            analysis = {
                "session_metadata": session_meta,
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_depth": self.analysis_depth
            }

            if self.analysis_depth in ["standard", "comprehensive"]:
                analysis.update(self._analyze_tool_usage(session_data))
                analysis.update(self._analyze_error_patterns(session_data))
                analysis.update(self._analyze_workflow_patterns(session_data))

            if self.analysis_depth == "comprehensive":
                analysis.update(self._analyze_agent_interactions(session_data))
                analysis.update(self._analyze_task_outcomes(session_data))
                analysis.update(self._analyze_memory_usage(session_data))

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing session: {str(e)}"

    def _analyze_tool_usage(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tool usage patterns from session data."""
        entries = session_data.get("entries", [])
        tool_counts = {}
        tool_sequences = []
        tool_errors = {}

        for entry in entries:
            tags = entry.get("tags", [])
            content = entry.get("content", {})

            # Count tool usage
            if "tool" in tags:
                tool_name = content.get("tool_name", "unknown")
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
            "tool_analysis": {
                "tool_usage_counts": tool_counts,
                "tool_success_rates": tool_success_rates,
                "tool_error_counts": tool_errors,
                "most_used_tools": sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "tool_sequence_length": len(tool_sequences)
            }
        }

    def _analyze_error_patterns(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error patterns and resolution strategies."""
        entries = session_data.get("entries", [])
        errors = []
        error_types = {}
        resolution_patterns = []

        for i, entry in enumerate(entries):
            tags = entry.get("tags", [])
            content = entry.get("content", {})

            if "error" in tags:
                error_info = {
                    "timestamp": entry.get("timestamp"),
                    "error_type": content.get("error_type", "unknown"),
                    "tool_name": content.get("tool_name"),
                    "error_message": content.get("error_message", ""),
                    "entry_index": i
                }
                errors.append(error_info)

                error_type = error_info["error_type"]
                error_types[error_type] = error_types.get(error_type, 0) + 1

                # Look for resolution patterns in next few entries
                resolution = self._find_resolution_pattern(entries, i)
                if resolution:
                    resolution_patterns.append(resolution)

        return {
            "error_analysis": {
                "total_errors": len(errors),
                "error_types": error_types,
                "error_details": errors,
                "resolution_patterns": resolution_patterns,
                "error_rate": len(errors) / len(entries) if entries else 0
            }
        }

    def _analyze_workflow_patterns(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze successful workflow sequences."""
        entries = session_data.get("entries", [])
        workflows = []

        # Identify workflow sequences by looking for task completion patterns
        current_workflow = []
        for entry in entries:
            tags = entry.get("tags", [])
            content = entry.get("content", {})

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
        successful_workflows = [w for w in workflows if any("success" in e.get("tags", []) for e in w)]

        return {
            "workflow_analysis": {
                "total_workflows": len(workflows),
                "successful_workflows": len(successful_workflows),
                "success_rate": len(successful_workflows) / len(workflows) if workflows else 0,
                "average_workflow_length": sum(len(w) for w in workflows) / len(workflows) if workflows else 0
            }
        }

    def _analyze_agent_interactions(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in agent-to-agent interactions."""
        entries = session_data.get("entries", [])
        interactions = {}

        for entry in entries:
            content = entry.get("content", {})
            if "agent_from" in content and "agent_to" in content:
                interaction_key = f"{content['agent_from']} -> {content['agent_to']}"
                interactions[interaction_key] = interactions.get(interaction_key, 0) + 1

        return {
            "interaction_analysis": {
                "agent_interactions": interactions,
                "total_interactions": sum(interactions.values()),
                "most_common_interactions": sorted(interactions.items(), key=lambda x: x[1], reverse=True)[:3]
            }
        }

    def _analyze_task_outcomes(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task completion outcomes and success factors."""
        entries = session_data.get("entries", [])
        outcomes = {"success": 0, "failure": 0, "partial": 0}

        for entry in entries:
            tags = entry.get("tags", [])
            if "task_complete" in tags:
                if "success" in tags:
                    outcomes["success"] += 1
                elif "error" in tags or "failure" in tags:
                    outcomes["failure"] += 1
                else:
                    outcomes["partial"] += 1

        total_tasks = sum(outcomes.values())

        return {
            "outcome_analysis": {
                "task_outcomes": outcomes,
                "total_tasks": total_tasks,
                "success_rate": outcomes["success"] / total_tasks if total_tasks > 0 else 0
            }
        }

    def _analyze_memory_usage(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze memory storage and retrieval patterns."""
        entries = session_data.get("entries", [])
        memory_ops = {"store": 0, "retrieve": 0, "search": 0}

        for entry in entries:
            tags = entry.get("tags", [])
            if "memory" in tags:
                content = entry.get("content", {})
                operation = content.get("operation", "unknown")
                if operation in memory_ops:
                    memory_ops[operation] += 1

        return {
            "memory_analysis": {
                "memory_operations": memory_ops,
                "total_memory_ops": sum(memory_ops.values())
            }
        }

    def _find_resolution_pattern(self, entries: List[Dict[str, Any]], error_index: int) -> Optional[Dict[str, Any]]:
        """Find resolution patterns after an error."""
        # Look at next 3 entries for resolution
        resolution_window = entries[error_index + 1:error_index + 4]

        for entry in resolution_window:
            tags = entry.get("tags", [])
            if "success" in tags or "resolution" in tags:
                return {
                    "resolution_method": entry.get("content", {}).get("method", "unknown"),
                    "steps_to_resolution": len(resolution_window)
                }

        return None