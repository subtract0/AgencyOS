"""
SessionPatternExtractor - Extract patterns from Agency session transcripts.

Analyzes:
- Successful task completion patterns
- Tool combination effectiveness
- Agent handoff strategies
- Problem-solving approaches
- Learning and adaptation patterns
"""

import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, cast

from shared.type_definitions.json import JSONValue

from ..coding_pattern import CodingPattern, EffectivenessMetric, ProblemContext, SolutionApproach
from .base_extractor import BasePatternExtractor

logger = logging.getLogger(__name__)


class SessionPatternExtractor(BasePatternExtractor):
    """Extract coding patterns from Agency session transcripts."""

    def __init__(self, sessions_dir: str = "logs/sessions", confidence_threshold: float = 0.6):
        """
        Initialize session pattern extractor.

        Args:
            sessions_dir: Directory containing session transcripts
            confidence_threshold: Minimum confidence for patterns
        """
        super().__init__("session_analysis", confidence_threshold)
        self.sessions_dir = sessions_dir

    def extract_patterns(self, days_back: int = 30, **kwargs: Any) -> list[CodingPattern]:
        """
        Extract patterns from session transcripts.

        Args:
            days_back: How many days of sessions to analyze

        Returns:
            List of discovered patterns
        """
        patterns: list[CodingPattern] = []

        try:
            # Find session files
            session_files = self._find_session_files(days_back)

            if not session_files:
                logger.info("No session files found for pattern extraction")
                return patterns

            # Extract different types of patterns
            patterns.extend(self._extract_tool_usage_patterns(session_files))
            patterns.extend(self._extract_task_completion_patterns(session_files))
            patterns.extend(self._extract_problem_solving_patterns(session_files))
            patterns.extend(self._extract_agent_handoff_patterns(session_files))

            logger.info(
                f"Extracted {len(patterns)} patterns from {len(session_files)} session files"
            )
            return patterns

        except Exception as e:
            logger.error(f"Failed to extract patterns from sessions: {e}")
            return []

    def _find_session_files(self, days_back: int) -> list[str]:
        """Find session transcript files within the specified time range."""
        session_files: list[str] = []

        if not os.path.exists(self.sessions_dir):
            return session_files

        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)

            for filename in os.listdir(self.sessions_dir):
                if filename.endswith(".md"):
                    file_path = os.path.join(self.sessions_dir, filename)

                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                    if file_mtime >= cutoff_date:
                        session_files.append(file_path)

        except Exception as e:
            logger.warning(f"Failed to find session files: {e}")

        return session_files

    def _extract_tool_usage_patterns(self, session_files: list[str]) -> list[CodingPattern]:
        """Extract patterns from tool usage in sessions."""
        patterns: list[CodingPattern] = []

        try:
            # Aggregate tool usage data
            tool_usage: dict[str, int] = {}
            tool_sequences: list[str] = []
            successful_sessions = 0

            for session_file in session_files:
                session_data = self._parse_session_file(session_file)

                if session_data.get("success", False):
                    successful_sessions += 1

                    # Track individual tool usage
                    tools_used = session_data.get("tools_used", [])
                    if isinstance(tools_used, list):
                        for tool in tools_used:
                            if isinstance(tool, str):
                                tool_usage[tool] = tool_usage.get(tool, 0) + 1

                    # Track tool sequences
                    if isinstance(tools_used, list) and len(tools_used) >= 2:
                        for i in range(len(tools_used) - 1):
                            if isinstance(tools_used[i], str) and isinstance(
                                tools_used[i + 1], str
                            ):
                                sequence = f"{tools_used[i]} -> {tools_used[i + 1]}"
                                tool_sequences.append(sequence)

            # Create patterns for frequently used tools
            if tool_usage:
                most_used_tools = sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:5]

                for tool_name, usage_count in most_used_tools:
                    if usage_count >= 3:  # Used in at least 3 sessions
                        context = ProblemContext(
                            description=f"Frequent need for {tool_name} functionality in development tasks",
                            domain="tool_usage",
                            constraints=["Efficiency", "Reliability", "Integration"],
                            symptoms=[
                                f"Repeated {tool_name} operations",
                                "Development workflow needs",
                            ],
                            scale=f"{usage_count} uses across sessions",
                        )

                        solution = SolutionApproach(
                            approach=f"Systematic use of {tool_name} for development tasks",
                            implementation=f"Integrate {tool_name} into standard workflow",
                            tools=[tool_name, "workflow_automation"],
                            reasoning=f"{tool_name} consistently effective for development tasks",
                        )

                        outcome = EffectivenessMetric(
                            success_rate=successful_sessions / len(session_files)
                            if session_files
                            else 0,
                            maintainability_impact=f"Streamlined workflow with {tool_name}",
                            user_impact="Faster task completion",
                            adoption_rate=usage_count,
                            confidence=0.7,
                        )

                        pattern = self.create_pattern(
                            context,
                            solution,
                            outcome,
                            f"tool_usage_{tool_name}",
                            ["tool_usage", "workflow", tool_name],
                        )
                        patterns.append(pattern)

            # Create patterns for tool sequences
            if tool_sequences:
                sequence_counts: dict[str, int] = {}
                for seq in tool_sequences:
                    sequence_counts[seq] = sequence_counts.get(seq, 0) + 1

                common_sequences = [
                    (seq, count) for seq, count in sequence_counts.items() if count >= 2
                ]

                for sequence, count in common_sequences:
                    context = ProblemContext(
                        description=f"Common tool workflow: {sequence}",
                        domain="workflow",
                        constraints=["Tool integration", "Efficiency", "Reliability"],
                        symptoms=["Multi-step tasks", "Tool coordination needs"],
                        scale=f"{count} occurrences",
                    )

                    solution = SolutionApproach(
                        approach=f"Sequential tool usage pattern: {sequence}",
                        implementation="Execute tools in sequence for optimal results",
                        tools=sequence.split(" -> "),
                        reasoning="Proven effective tool combination",
                    )

                    outcome = EffectivenessMetric(
                        success_rate=0.8,  # Assume sequences that repeat are successful
                        maintainability_impact="Standardized workflow",
                        user_impact="Predictable and efficient task execution",
                        adoption_rate=count,
                        confidence=0.7,
                    )

                    pattern = self.create_pattern(
                        context,
                        solution,
                        outcome,
                        f"tool_sequence_{sequence.replace(' -> ', '_')}",
                        ["workflow", "tool_sequence", "automation"],
                    )
                    patterns.append(pattern)

        except Exception as e:
            logger.warning(f"Tool usage pattern extraction failed: {e}")

        return patterns

    def _extract_task_completion_patterns(self, session_files: list[str]) -> list[CodingPattern]:
        """Extract patterns from successful task completions."""
        patterns: list[CodingPattern] = []

        try:
            successful_tasks: list[dict[str, JSONValue]] = []

            for session_file in session_files:
                session_data = self._parse_session_file(session_file)

                if session_data.get("success", False):
                    successful_tasks.append(session_data)

            if len(successful_tasks) >= 3:  # Need at least 3 successful tasks
                # Analyze common success factors
                common_approaches = self._analyze_success_factors(successful_tasks)

                if common_approaches:
                    context = ProblemContext(
                        description="Complex software engineering tasks requiring systematic approach",
                        domain="task_completion",
                        constraints=["Quality requirements", "Time efficiency", "Maintainability"],
                        symptoms=["Multi-step tasks", "Integration challenges", "Quality needs"],
                        scale=f"{len(successful_tasks)} successful completions",
                    )

                    solution = SolutionApproach(
                        approach="Systematic task breakdown and execution",
                        implementation="Break complex tasks into manageable steps with validation",
                        tools=cast(list[str], common_approaches.get("common_tools", [])),
                        reasoning="Proven approach for complex software engineering tasks",
                        code_examples=cast(list[str], common_approaches.get("examples", [])),
                    )

                    outcome = EffectivenessMetric(
                        success_rate=len(successful_tasks) / len(session_files),
                        maintainability_impact="Structured approach improves outcomes",
                        user_impact="Higher success rate on complex tasks",
                        adoption_rate=len(successful_tasks),
                        confidence=0.8,
                    )

                    pattern = self.create_pattern(
                        context,
                        solution,
                        outcome,
                        f"task_completion_{len(successful_tasks)}",
                        ["task_completion", "methodology", "success"],
                    )
                    patterns.append(pattern)

        except Exception as e:
            logger.warning(f"Task completion pattern extraction failed: {e}")

        return patterns

    def _extract_problem_solving_patterns(self, session_files: list[str]) -> list[CodingPattern]:
        """Extract problem-solving approach patterns."""
        patterns: list[CodingPattern] = []

        try:
            problem_solving_approaches: list[dict[str, JSONValue] | None] = []

            for session_file in session_files:
                session_data = self._parse_session_file(session_file)

                # Look for problem-solving indicators
                content = session_data.get("content", "")
                if isinstance(content, str) and any(
                    keyword in content.lower()
                    for keyword in ["error", "fix", "debug", "solve", "resolve"]
                ):
                    approach = self._extract_problem_solving_approach(session_data)
                    if approach:
                        problem_solving_approaches.append(approach)

            if len(problem_solving_approaches) >= 2:
                # Create pattern for debugging approach
                context = ProblemContext(
                    description="Software errors and issues requiring systematic debugging",
                    domain="debugging",
                    constraints=[
                        "Minimal disruption",
                        "Root cause identification",
                        "Permanent solution",
                    ],
                    symptoms=["Runtime errors", "Test failures", "Unexpected behavior"],
                    scale=f"{len(problem_solving_approaches)} debugging sessions",
                )

                solution = SolutionApproach(
                    approach="Systematic debugging with validation",
                    implementation="Identify issue, analyze root cause, implement fix, validate",
                    tools=["debugging_tools", "testing", "analysis"],
                    reasoning="Structured approach prevents recurring issues",
                )

                outcome = EffectivenessMetric(
                    success_rate=0.85,  # Assume most debugging sessions are successful
                    maintainability_impact="Improved system stability",
                    user_impact="Faster issue resolution",
                    adoption_rate=len(problem_solving_approaches),
                    confidence=0.75,
                )

                pattern = self.create_pattern(
                    context,
                    solution,
                    outcome,
                    f"debugging_approach_{len(problem_solving_approaches)}",
                    ["debugging", "problem_solving", "methodology"],
                )
                patterns.append(pattern)

        except Exception as e:
            logger.warning(f"Problem solving pattern extraction failed: {e}")

        return patterns

    def _extract_agent_handoff_patterns(self, session_files: list[str]) -> list[CodingPattern]:
        """Extract agent communication and handoff patterns."""
        patterns: list[CodingPattern] = []

        try:
            handoff_data: list[dict[str, JSONValue]] = []

            for session_file in session_files:
                session_data = self._parse_session_file(session_file)

                # Look for agent handoff indicators
                content = session_data.get("content", "")
                if isinstance(content, str) and any(
                    keyword in content.lower()
                    for keyword in ["agent", "handoff", "planner", "coder"]
                ):
                    handoffs = self._extract_handoff_info(session_data)
                    handoff_data.extend(handoffs)

            if len(handoff_data) >= 3:
                context = ProblemContext(
                    description="Complex tasks requiring coordination between specialized agents",
                    domain="agent_coordination",
                    constraints=[
                        "Context preservation",
                        "Efficient communication",
                        "Task completion",
                    ],
                    symptoms=[
                        "Multi-step workflows",
                        "Specialization needs",
                        "Coordination overhead",
                    ],
                    scale=f"{len(handoff_data)} agent handoffs",
                )

                solution = SolutionApproach(
                    approach="Structured agent handoffs with context preservation",
                    implementation="Clear handoff protocols with context and task specification",
                    tools=["agent_communication", "context_management", "task_coordination"],
                    reasoning="Specialized agents working together more effective than single agent",
                )

                outcome = EffectivenessMetric(
                    success_rate=0.8,
                    maintainability_impact="Clear responsibilities and improved coordination",
                    user_impact="More effective task completion",
                    adoption_rate=len(handoff_data),
                    confidence=0.7,
                )

                pattern = self.create_pattern(
                    context,
                    solution,
                    outcome,
                    f"agent_handoff_{len(handoff_data)}",
                    ["agent_coordination", "handoff", "multi_agent"],
                )
                patterns.append(pattern)

        except Exception as e:
            logger.warning(f"Agent handoff pattern extraction failed: {e}")

        return patterns

    def _parse_session_file(self, file_path: str) -> dict[str, JSONValue]:
        """Parse a session transcript file."""
        session_data: dict[str, JSONValue] = {
            "file_path": file_path,
            "content": "",
            "tools_used": cast(JSONValue, []),
            "success": False,
            "duration": None,
            "task_type": "unknown",
        }

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                session_data["content"] = content

            # Extract tools used
            tool_patterns = [
                r"Read\(",
                r"Write\(",
                r"Edit\(",
                r"Bash\(",
                r"Grep\(",
                r"Glob\(",
                r"MultiEdit\(",
                r"TodoWrite\(",
                r"Git\(",
            ]

            tools_list = []
            for pattern in tool_patterns:
                if re.search(pattern, content):
                    tool_name = pattern.replace("(", "").replace("\\", "")
                    if tool_name not in tools_list:
                        tools_list.append(tool_name)
            session_data["tools_used"] = cast(JSONValue, tools_list)

            # Determine if session was successful
            success_indicators = [
                "successfully",
                "completed",
                "done",
                "fixed",
                "resolved",
                "implemented",
                "working",
            ]

            session_data["success"] = any(
                indicator in content.lower() for indicator in success_indicators
            )

            # Extract task type
            if "test" in content.lower():
                session_data["task_type"] = "testing"
            elif "fix" in content.lower() or "bug" in content.lower():
                session_data["task_type"] = "debugging"
            elif "implement" in content.lower() or "add" in content.lower():
                session_data["task_type"] = "feature_development"
            elif "refactor" in content.lower():
                session_data["task_type"] = "refactoring"

        except Exception as e:
            logger.debug(f"Failed to parse session file {file_path}: {e}")

        return session_data

    def _analyze_success_factors(
        self, successful_tasks: list[dict[str, JSONValue]]
    ) -> dict[str, JSONValue]:
        """Analyze common factors in successful tasks."""
        factors: dict[str, JSONValue] = {
            "common_tools": cast(JSONValue, []),
            "common_approaches": cast(JSONValue, []),
            "examples": cast(JSONValue, []),
        }

        try:
            # Find most common tools
            all_tools: list[str] = []
            for task in successful_tasks:
                tools_used = task.get("tools_used", [])
                if isinstance(tools_used, list):
                    all_tools.extend([str(tool) for tool in tools_used if isinstance(tool, str)])

            if all_tools:
                tool_counts: dict[str, int] = {}
                for tool in all_tools:
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1

                # Tools used in at least half of successful tasks
                threshold = len(successful_tasks) // 2
                common_tools = [tool for tool, count in tool_counts.items() if count >= threshold]
                factors["common_tools"] = cast(JSONValue, common_tools)

            # Extract approach patterns
            examples_list = []
            for task in successful_tasks[:3]:  # Sample first 3
                content = task.get("content", "")
                if isinstance(content, str) and len(content) > 100:
                    # Extract a representative snippet
                    lines = content.split("\n")
                    for line in lines:
                        if len(line) > 50 and "successfully" in line.lower():
                            examples_list.append(line.strip()[:100] + "...")
                            break
            factors["examples"] = cast(JSONValue, examples_list)

        except Exception as e:
            logger.debug(f"Failed to analyze success factors: {e}")

        return factors

    def _extract_problem_solving_approach(
        self, session_data: dict[str, JSONValue]
    ) -> dict[str, JSONValue] | None:
        """Extract problem-solving approach from session data."""
        content = session_data.get("content", "")

        approach: dict[str, JSONValue] = {
            "type": session_data.get("task_type", "unknown"),
            "tools": session_data.get("tools_used", []),
            "success": session_data.get("success", False),
        }

        # Look for specific problem-solving indicators
        if isinstance(content, str) and ("debug" in content.lower() or "error" in content.lower()):
            approach["type"] = "debugging"
            return approach

        return None

    def _extract_handoff_info(
        self, session_data: dict[str, JSONValue]
    ) -> list[dict[str, JSONValue]]:
        """Extract agent handoff information from session."""
        handoffs: list[dict[str, JSONValue]] = []
        content = session_data.get("content", "")
        if not isinstance(content, str):
            return handoffs

        # Look for agent mentions
        agent_patterns = [
            r"(PlannerAgent|AgencyCodeAgent|LearningAgent|AuditorAgent)",
            r"handoff to (\w+)",
            r"agent (\w+)",
        ]

        for pattern in agent_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]

                handoffs.append(
                    {
                        "agent": match,
                        "context": "task_coordination",
                        "success": session_data.get("success", False),
                    }
                )

        return handoffs
