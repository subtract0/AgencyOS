# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item"
"""
Consolidate insights into structured learning format.
"""
from agency_swarm.tools import BaseTool
from pydantic import Field
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, cast
from shared.type_definitions.json import JSONValue
import uuid
from learning_agent.json_utils import (
    is_dict, is_list, is_str, is_int, is_float, is_number, is_none,
    safe_get, safe_get_dict, safe_get_list, safe_get_str, safe_get_int, safe_get_float,
    ensure_dict, ensure_list, ensure_str
)


class ConsolidateLearning(BaseTool):  # mypy: disable-error-code="misc"
    """
    Consolidates extracted insights into structured JSON learning objects.

    This tool takes insights from ExtractInsights and converts them into
    standardized learning objects that can be stored in the VectorStore
    for future retrieval and application.
    """

    insights: str = Field(
        ...,
        description="JSON string of extracted insights from ExtractInsights"
    )
    learning_type: str = Field(
        ...,
        description="Type: 'successful_pattern', 'error_resolution', 'optimization', 'interaction_pattern', or 'auto' to detect automatically"
    )
    session_context: str = Field(
        default="",
        description="Optional context about the session (task description, goals, etc.)"
    )

    def run(self) -> str:
        try:
            # Parse the insights
            parsed_insights = json.loads(self.insights)
            insights_data = ensure_dict(parsed_insights)
            insights_list = safe_get_list(insights_data, "insights")

            if not insights_list:
                return json.dumps({"error": "No insights found to consolidate"}, indent=2)

            # Consolidate insights into learning objects
            learning_objects: List[Dict[str, JSONValue]] = []

            for insight_value in insights_list:
                insight = ensure_dict(insight_value)
                learning_obj = self._create_learning_object(insight, insights_data)
                if learning_obj:
                    learning_objects.append(learning_obj)

            # Create consolidated result
            result: Dict[str, JSONValue] = {
                "consolidation_timestamp": datetime.now().isoformat(),
                "total_learning_objects": len(learning_objects),
                "learning_type": self.learning_type,
                "session_context": self.session_context,
                "learning_objects": learning_objects
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Error consolidating learning: {str(e)}"

    def _create_learning_object(self, insight: Dict[str, JSONValue], context: Dict[str, JSONValue]) -> Optional[Dict[str, JSONValue]]:
        """Create a standardized learning object from an insight."""
        try:
            # Generate unique learning ID based on content
            title = safe_get_str(insight, "title")
            description = safe_get_str(insight, "description")
            actionable = safe_get_str(insight, "actionable_insight")

            content_hash = hashlib.md5(
                f"{title}{description}{actionable}".encode()
            ).hexdigest()[:8]

            learning_id = f"learning_{content_hash}_{int(datetime.now().timestamp())}"

            # Determine learning type if auto
            determined_type = self._determine_learning_type(insight) if self.learning_type == "auto" else self.learning_type

            # Extract patterns based on insight type
            patterns = self._extract_patterns(insight)

            # Create the standardized learning object
            session_metadata = safe_get_dict(context, "session_metadata")

            learning_object: Dict[str, JSONValue] = {
                "learning_id": learning_id,
                "type": determined_type,
                "category": safe_get_str(insight, "category", "general"),
                "title": safe_get_str(insight, "title", "Untitled Learning"),
                "description": safe_get_str(insight, "description"),
                "actionable_insight": safe_get_str(insight, "actionable_insight"),
                "confidence": safe_get_float(insight, "confidence", 0.5),
                "keywords": safe_get_list(insight, "keywords"),
                "patterns": patterns,
                "metadata": {
                    "created_timestamp": datetime.now().isoformat(),
                    "source_session": safe_get_str(session_metadata, "session_id", "unknown"),
                    "insight_type": safe_get_str(insight, "type", "unknown"),
                    "original_data": safe_get_dict(insight, "data"),
                    "context": self.session_context
                },
                "application_criteria": self._generate_application_criteria(insight, determined_type),
                "success_metrics": self._generate_success_metrics(insight, determined_type)
            }

            return learning_object

        except Exception as e:
            # Return a basic learning object if there's an error
            error_object: Dict[str, JSONValue] = {
                "learning_id": f"error_learning_{uuid.uuid4().hex[:8]}",
                "type": "error",
                "title": "Error Processing Insight",
                "description": f"Failed to process insight: {str(e)}",
                "confidence": 0.1,
                "keywords": ["error", "processing"],
                "metadata": {"error": str(e)}
            }
            return error_object

    def _determine_learning_type(self, insight: Dict[str, JSONValue]) -> str:
        """Automatically determine the learning type from insight characteristics."""
        insight_type = safe_get_str(insight, "type")
        category = safe_get_str(insight, "category")
        confidence = safe_get_float(insight, "confidence", 0.0)

        # High confidence insights with tool patterns
        if insight_type == "tool_pattern" and confidence > 0.8:
            return "successful_pattern"

        # Error-related insights
        elif insight_type == "error_resolution":
            actionable = safe_get_str(insight, "actionable_insight").lower()
            if "resolution" in category or "prevention" in actionable:
                return "error_resolution"
            else:
                return "optimization"

        # Task completion insights
        elif insight_type == "task_completion":
            if "success" in category:
                return "successful_pattern"
            else:
                return "optimization"

        # Optimization insights
        elif insight_type == "optimization":
            return "optimization"

        # Default fallback
        else:
            return "optimization"

    def _extract_patterns(self, insight: Dict[str, JSONValue]) -> Dict[str, JSONValue]:
        """Extract reusable patterns from the insight."""
        patterns: Dict[str, JSONValue] = {
            "triggers": [],
            "actions": [],
            "conditions": [],
            "outcomes": []
        }

        insight_type = safe_get_str(insight, "type")
        data = safe_get_dict(insight, "data")
        actionable = safe_get_str(insight, "actionable_insight")

        # Extract patterns based on insight type
        if insight_type == "tool_pattern":
            # Tool usage patterns
            tools_data = safe_get_list(data, "tools")
            if tools_data:
                patterns["triggers"] = ["high_frequency_tool_usage"]
                tool_names: List[str] = []
                for tool_item in tools_data[:2]:
                    if is_list(tool_item) and tool_item:
                        tool_names.append(ensure_str(tool_item[0]))
                patterns["actions"] = [f"optimize_tool_{name}" for name in tool_names]

            low_success_tools = safe_get_list(data, "low_success_tools")
            if low_success_tools:
                patterns["triggers"] = ["low_tool_success_rate"]
                patterns["actions"] = ["improve_error_handling", "add_validation"]
                tool_conditions: List[str] = []
                for tool_item in low_success_tools[:2]:
                    if is_list(tool_item) and tool_item:
                        tool_name = ensure_str(tool_item[0])
                        tool_conditions.append(f"success_rate < 0.8 for {tool_name}")
                patterns["conditions"] = tool_conditions

        elif insight_type == "error_resolution":
            # Error patterns
            error_type = safe_get_str(data, "error_type")
            if error_type:
                patterns["triggers"] = [f"{error_type}_error"]
                error_count = safe_get_int(data, "count", 1)
                patterns["conditions"] = [f"error_count > {error_count}"]

            resolution_patterns = safe_get(data, "resolution_patterns")
            if resolution_patterns is not None:
                patterns["actions"] = ["apply_known_resolution", "document_solution"]
                patterns["outcomes"] = ["error_resolved", "pattern_documented"]

        elif insight_type == "task_completion":
            # Workflow patterns
            success_rate = safe_get_float(data, "success_rate")
            if success_rate > 0:
                patterns["triggers"] = ["workflow_completion"]
                patterns["conditions"] = [f"success_rate >= {success_rate:.2f}"]
                patterns["outcomes"] = ["high_success_workflow"]

        # Extract action patterns from actionable insights
        action_keywords = ["optimize", "improve", "consider", "implement", "document", "investigate"]
        for keyword in action_keywords:
            if keyword in actionable.lower():
                patterns["actions"].append(f"{keyword}_based_on_insight")

        return patterns

    def _generate_application_criteria(self, insight: Dict[str, JSONValue], learning_type: str) -> List[str]:
        """Generate criteria for when this learning should be applied."""
        criteria: List[str] = []

        insight_type = safe_get_str(insight, "type")
        category = safe_get_str(insight, "category")
        confidence = safe_get_float(insight, "confidence", 0.0)

        # Base criteria on learning type
        if learning_type == "successful_pattern":
            criteria.extend([
                "Similar task context detected",
                f"Confidence level >= {confidence:.2f}",
                "No conflicting patterns present"
            ])

        elif learning_type == "error_resolution":
            data = safe_get_dict(insight, "data")
            error_type = safe_get_str(data, "error_type", "any")
            criteria.extend([
                f"Error type matches: {error_type}",
                "Error count exceeds threshold",
                "Resolution pattern applicable"
            ])

        elif learning_type == "optimization":
            criteria.extend([
                "Performance metrics below target",
                "Optimization opportunity detected",
                "Resource usage can be improved"
            ])

        elif learning_type == "interaction_pattern":
            criteria.extend([
                "Multi-agent workflow detected",
                "Communication overhead identified",
                "Coordination improvement possible"
            ])

        # Add specific criteria based on insight category
        if category == "high_frequency_tools":
            criteria.append("Tool usage frequency above average")
        elif category == "low_success_rate":
            criteria.append("Tool success rate below 80%")
        elif category == "workflow_efficiency":
            criteria.append("Workflow length analysis needed")

        return criteria

    def _generate_success_metrics(self, insight: Dict[str, JSONValue], learning_type: str) -> List[str]:
        """Generate metrics to measure the success of applying this learning."""
        metrics: List[str] = []

        insight_type = safe_get_str(insight, "type")
        data = safe_get_dict(insight, "data")

        # Base metrics on learning type
        if learning_type == "successful_pattern":
            metrics.extend([
                "Pattern application success rate",
                "Task completion time improvement",
                "Error reduction rate"
            ])

        elif learning_type == "error_resolution":
            metrics.extend([
                "Error recurrence rate",
                "Resolution time improvement",
                "User satisfaction increase"
            ])

        elif learning_type == "optimization":
            metrics.extend([
                "Performance improvement percentage",
                "Resource usage reduction",
                "Efficiency gain measurement"
            ])

        # Add specific metrics based on insight data
        success_rate = safe_get_float(data, "success_rate")
        if success_rate > 0:
            metrics.append(f"Maintain success rate >= {success_rate:.2f}")

        error_rate = safe_get_float(data, "error_rate")
        if error_rate > 0:
            metrics.append(f"Reduce error rate below {error_rate:.2f}")

        tools_data = safe_get_list(data, "tools")
        if tools_data:
            metrics.append("Tool usage optimization measurable")

        # Default metrics if none specified
        if not metrics:
            metrics = [
                "Objective improvement measured",
                "User feedback positive",
                "No negative side effects"
            ]

        return metrics