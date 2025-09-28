# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Extract actionable insights from session analysis.
"""
from agency_swarm.tools import BaseTool  # type: ignore
from pydantic import Field
from typing import Dict, Any, List, Union, cast, Optional
from shared.type_definitions.json import JSONValue
from shared.models.learning import ExtractedInsight, InsightExtractionResult
import json
import re
from datetime import datetime
from learning_agent.json_utils import (
    is_dict, is_list, safe_get, safe_get_dict, safe_get_list,
    safe_get_str, safe_get_int, safe_get_float, ensure_list,
    json_to_any_dict
)


class ExtractInsights(BaseTool):  # mypy: disable-error-code="misc"
    """
    Extracts structured insights from analyzed session data.

    This tool takes the output from AnalyzeSession and identifies actionable insights
    such as tool optimization opportunities, error prevention strategies, and
    successful workflow patterns that can be learned from.
    """

    session_analysis: str = Field(
        ...,
        description="Analyzed session data with patterns (JSON string from AnalyzeSession)"
    )
    insight_type: str = Field(
        default="auto",
        description="Type of insight to extract: 'tool_pattern', 'error_resolution', 'task_completion', 'optimization', or 'auto' for all types"
    )
    confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence threshold for insights (0.0 to 1.0)"
    )

    def run(self) -> str:
        try:
            # Parse the session analysis
            analysis_data = json.loads(self.session_analysis)

            # Extract insights based on type
            insights_list: List[ExtractedInsight] = []

            if self.insight_type == "auto" or self.insight_type == "tool_pattern":
                insights_list.extend(self._extract_tool_insights(analysis_data))

            if self.insight_type == "auto" or self.insight_type == "error_resolution":
                insights_list.extend(self._extract_error_insights(analysis_data))

            if self.insight_type == "auto" or self.insight_type == "task_completion":
                insights_list.extend(self._extract_workflow_insights(analysis_data))

            if self.insight_type == "auto" or self.insight_type == "optimization":
                insights_list.extend(self._extract_optimization_insights(analysis_data))

            # Filter by confidence threshold
            filtered_insights = [
                insight for insight in insights_list
                if insight.confidence >= self.confidence_threshold
            ]

            result = InsightExtractionResult(
                extraction_timestamp=datetime.now().isoformat(),
                insight_type=self.insight_type,
                confidence_threshold=self.confidence_threshold,
                insights=filtered_insights,
                total_insights=len(filtered_insights)
            )

            return result.model_dump_json(indent=2)

        except Exception as e:
            return f"Error extracting insights: {str(e)}"

    def _extract_tool_insights(self, analysis_data: Dict[str, JSONValue]) -> List[ExtractedInsight]:
        """Extract insights about tool usage patterns."""
        tool_analysis = safe_get_dict(analysis_data, "tool_analysis")
        insights: List[ExtractedInsight] = []

        # High-frequency tool patterns
        tool_counts = safe_get_dict(tool_analysis, "tool_usage_counts")
        most_used = safe_get_list(tool_analysis, "most_used_tools")

        if most_used:
            # Process most_used tools safely
            tools_desc = []
            for item in most_used[:3]:
                if is_list(item) and len(ensure_list(item)) >= 2:
                    tool_list = ensure_list(item)
                    tool_name = safe_get_str(tool_list, "0", "unknown")
                    count = safe_get_int(tool_list, "1", 0)
                    tools_desc.append(f"{tool_name} ({count})")

            if tools_desc:
                insight = ExtractedInsight(
                    type="tool_pattern",
                    category="high_frequency_tools",
                    title="Most Frequently Used Tools",
                    description=f"Tools used most often: {', '.join(tools_desc)}",
                    actionable_insight="Consider optimizing these high-frequency tools for better performance",
                    confidence=0.9,
                    data={"tools": cast(List[JSONValue], most_used[:3])},
                    keywords=["tool_usage", "frequency", "optimization"]
                )
                insights.append(insight)

        # Tool success rate insights
        success_rates = safe_get_dict(tool_analysis, "tool_success_rates")
        low_success_tools: List[tuple[str, float]] = []
        for tool, rate in success_rates.items():
            rate_float = safe_get_float({"rate": rate}, "rate", 1.0)
            if rate_float < 0.8:
                low_success_tools.append((tool, rate_float))

        if low_success_tools:
            tools_desc = [f"{tool} ({rate:.1%})" for tool, rate in low_success_tools]
            low_success_insight = ExtractedInsight(
                type="tool_pattern",
                category="low_success_rate",
                title="Tools with Low Success Rates",
                description=f"Tools with success rates below 80%: {', '.join(tools_desc)}",
                actionable_insight="Investigate error patterns for these tools and improve error handling",
                confidence=0.85,
                data={"low_success_tools": cast(List[JSONValue], [(t, r) for t, r in low_success_tools])},
                keywords=["tool_reliability", "error_handling", "improvement"]
            )
            insights.append(low_success_insight)

        # Tool sequence patterns
        sequence_length = safe_get_int(tool_analysis, "tool_sequence_length", 0)
        if sequence_length > 10:
            sequence_insight = ExtractedInsight(
                type="tool_pattern",
                category="long_sequences",
                title="Long Tool Sequences Detected",
                description=f"Session contained {sequence_length} tool calls",
                actionable_insight="Consider creating composite tools or workflows to reduce tool call overhead",
                confidence=0.75,
                data={"sequence_length": sequence_length},
                keywords=["workflow_optimization", "tool_composition", "efficiency"]
            )
            insights.append(sequence_insight)

        return insights

    def _extract_error_insights(self, analysis_data: Dict[str, JSONValue]) -> List[ExtractedInsight]:
        """Extract insights about error patterns and resolution strategies."""
        error_analysis = safe_get_dict(analysis_data, "error_analysis")
        insights: List[ExtractedInsight] = []

        # High error rate insight
        error_rate = safe_get_float(error_analysis, "error_rate", 0.0)
        if error_rate > 0.1:  # More than 10% error rate
            insight = ExtractedInsight(
                type="error_resolution",
                category="high_error_rate",
                title="High Error Rate Detected",
                description=f"Session had {error_rate:.1%} error rate",
                actionable_insight="Investigate common error patterns and implement preventive measures",
                confidence=0.9,
                data={"error_rate": error_rate},
                keywords=["error_prevention", "reliability", "quality"]
            )
            insights.append(insight)

        # Common error types
        error_types = safe_get_dict(error_analysis, "error_types")
        if error_types:
            most_common_error = max(error_types.items(), key=lambda x: x[1])
            if most_common_error[1] > 2:  # More than 2 occurrences
                insights.append(ExtractedInsight(
                    type="error_resolution",
                    category="common_error_type",
                    title=f"Frequent {most_common_error[0]} Errors",
                    description=f"'{most_common_error[0]}' error occurred {most_common_error[1]} times",
                    actionable_insight=f"Create specific error handling for {most_common_error[0]} errors",
                    confidence=0.85,
                    data={"error_type": most_common_error[0], "count": most_common_error[1]},
                    keywords=["error_handling", most_common_error[0], "prevention"]
                ))

        # Resolution patterns
        resolution_patterns = cast(List[Dict[str, JSONValue]], error_analysis.get("resolution_patterns", []))
        if resolution_patterns:
            avg_resolution_steps = sum(cast(int, p.get("steps_to_resolution", 0)) for p in resolution_patterns) / len(resolution_patterns)
            insights.append(ExtractedInsight(
                type="error_resolution",
                category="resolution_efficiency",
                title="Error Resolution Patterns",
                description=f"Found {len(resolution_patterns)} successful error resolutions with average {avg_resolution_steps:.1f} steps",
                actionable_insight="Document successful resolution patterns for future reference",
                confidence=0.8,
                data={"resolution_patterns": cast(List[JSONValue], resolution_patterns), "avg_steps": avg_resolution_steps},
                keywords=["error_resolution", "documentation", "patterns"]
            ))

        return insights

    def _extract_workflow_insights(self, analysis_data: Dict[str, JSONValue]) -> List[ExtractedInsight]:
        """Extract insights about successful workflow patterns."""
        workflow_analysis = analysis_data.get("workflow_analysis", {})
        insights: List[ExtractedInsight] = []

        # High success rate workflows
        success_rate = cast(float, workflow_analysis.get("success_rate", 0))
        if success_rate > 0.8:
            insights.append(ExtractedInsight(
                type="task_completion",
                category="high_success_rate",
                title="High Workflow Success Rate",
                description=f"Achieved {success_rate:.1%} workflow success rate",
                actionable_insight="Document successful workflow patterns as templates for future tasks",
                confidence=0.9,
                data={"success_rate": success_rate},
                keywords=["workflow_success", "templates", "best_practices"]
            ))

        # Workflow efficiency
        avg_length = cast(float, workflow_analysis.get("average_workflow_length", 0))
        if avg_length > 0:
            if avg_length < 5:
                efficiency_insight = "Workflows are very efficient with short sequences"
                confidence = 0.8
            elif avg_length > 15:
                efficiency_insight = "Workflows may be too complex - consider breaking into smaller tasks"
                confidence = 0.85
            else:
                efficiency_insight = "Workflow length appears optimal"
                confidence = 0.7

            insights.append(ExtractedInsight(
                type="task_completion",
                category="workflow_efficiency",
                title="Workflow Length Analysis",
                description=f"Average workflow length is {avg_length:.1f} steps",
                actionable_insight=efficiency_insight,
                confidence=confidence,
                data={"avg_length": avg_length},
                keywords=["workflow_efficiency", "optimization", "task_size"]
            ))

        return insights

    def _extract_optimization_insights(self, analysis_data: Dict[str, JSONValue]) -> List[ExtractedInsight]:
        """Extract general optimization insights."""
        insights: List[ExtractedInsight] = []

        # Memory usage optimization
        memory_analysis = cast(Dict[str, JSONValue], analysis_data.get("memory_analysis", {}))
        memory_ops = cast(Dict[str, int], memory_analysis.get("memory_operations", {}))

        if memory_ops:
            total_ops = sum(memory_ops.values())
            store_ratio = memory_ops.get("store", 0) / total_ops if total_ops > 0 else 0
            retrieve_ratio = memory_ops.get("retrieve", 0) / total_ops if total_ops > 0 else 0

            if store_ratio > 0.7:  # More storing than retrieving
                insights.append(ExtractedInsight(
                    type="optimization",
                    category="memory_usage",
                    title="High Memory Storage Activity",
                    description=f"{store_ratio:.1%} of memory operations were storage",
                    actionable_insight="Consider implementing memory consolidation to reduce storage overhead",
                    confidence=0.75,
                    data={"store_ratio": store_ratio, "total_ops": total_ops},
                    keywords=["memory_optimization", "storage", "consolidation"]
                ))

            if retrieve_ratio > 0.5:  # Good retrieval usage
                insights.append(ExtractedInsight(
                    type="optimization",
                    category="memory_usage",
                    title="Good Memory Retrieval Usage",
                    description=f"{retrieve_ratio:.1%} of memory operations were retrieval",
                    actionable_insight="Memory retrieval patterns show good reuse of stored knowledge",
                    confidence=0.8,
                    data={"retrieve_ratio": retrieve_ratio, "total_ops": total_ops},
                    keywords=["memory_efficiency", "knowledge_reuse", "patterns"]
                ))

        # Agent interaction optimization
        interaction_analysis = cast(Dict[str, JSONValue], analysis_data.get("interaction_analysis", {}))
        total_interactions = cast(int, interaction_analysis.get("total_interactions", 0))

        if total_interactions > 10:
            insights.append(ExtractedInsight(
                type="optimization",
                category="agent_coordination",
                title="High Agent Interaction Volume",
                description=f"Session had {total_interactions} agent interactions",
                actionable_insight="Consider optimizing agent coordination to reduce communication overhead",
                confidence=0.7,
                data={"total_interactions": total_interactions},
                keywords=["agent_coordination", "communication", "efficiency"]
            ))

        return insights