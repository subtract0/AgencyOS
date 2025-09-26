"""
Consolidate insights into structured learning format.
"""
from agency_swarm.tools import BaseTool
from pydantic import Field
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from shared.types.json import JSONValue
import uuid


class ConsolidateLearning(BaseTool):
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
            insights_data = json.loads(self.insights)
            insights_list = insights_data.get("insights", [])

            if not insights_list:
                return json.dumps({"error": "No insights found to consolidate"}, indent=2)

            # Consolidate insights into learning objects
            learning_objects = []

            for insight in insights_list:
                learning_obj = self._create_learning_object(insight, insights_data)
                if learning_obj:
                    learning_objects.append(learning_obj)

            # Create consolidated result
            result = {
                "consolidation_timestamp": datetime.now().isoformat(),
                "total_learning_objects": len(learning_objects),
                "learning_type": self.learning_type,
                "session_context": self.session_context,
                "learning_objects": learning_objects
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Error consolidating learning: {str(e)}"

    def _create_learning_object(self, insight: Dict[str, JSONValue], context: Dict[str, JSONValue]) -> Dict[str, JSONValue]:
        """Create a standardized learning object from an insight."""
        try:
            # Generate unique learning ID based on content
            content_hash = hashlib.md5(
                f"{insight.get('title', '')}{insight.get('description', '')}{insight.get('actionable_insight', '')}".encode()
            ).hexdigest()[:8]

            learning_id = f"learning_{content_hash}_{int(datetime.now().timestamp())}"

            # Determine learning type if auto
            determined_type = self._determine_learning_type(insight) if self.learning_type == "auto" else self.learning_type

            # Extract patterns based on insight type
            patterns = self._extract_patterns(insight)

            # Create the standardized learning object
            learning_object = {
                "learning_id": learning_id,
                "type": determined_type,
                "category": insight.get("category", "general"),
                "title": insight.get("title", "Untitled Learning"),
                "description": insight.get("description", ""),
                "actionable_insight": insight.get("actionable_insight", ""),
                "confidence": insight.get("confidence", 0.5),
                "keywords": insight.get("keywords", []),
                "patterns": patterns,
                "metadata": {
                    "created_timestamp": datetime.now().isoformat(),
                    "source_session": context.get("session_metadata", {}).get("session_id", "unknown"),
                    "insight_type": insight.get("type", "unknown"),
                    "original_data": insight.get("data", {}),
                    "context": self.session_context
                },
                "application_criteria": self._generate_application_criteria(insight, determined_type),
                "success_metrics": self._generate_success_metrics(insight, determined_type)
            }

            return learning_object

        except Exception as e:
            # Return a basic learning object if there's an error
            return {
                "learning_id": f"error_learning_{uuid.uuid4().hex[:8]}",
                "type": "error",
                "title": "Error Processing Insight",
                "description": f"Failed to process insight: {str(e)}",
                "confidence": 0.1,
                "keywords": ["error", "processing"],
                "metadata": {"error": str(e)}
            }

    def _determine_learning_type(self, insight: Dict[str, JSONValue]) -> str:
        """Automatically determine the learning type from insight characteristics."""
        insight_type = insight.get("type", "")
        category = insight.get("category", "")
        confidence = insight.get("confidence", 0)

        # High confidence insights with tool patterns
        if insight_type == "tool_pattern" and confidence > 0.8:
            return "successful_pattern"

        # Error-related insights
        elif insight_type == "error_resolution":
            if "resolution" in category or "prevention" in insight.get("actionable_insight", "").lower():
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
        patterns = {
            "triggers": [],
            "actions": [],
            "conditions": [],
            "outcomes": []
        }

        insight_type = insight.get("type", "")
        data = insight.get("data", {})
        actionable = insight.get("actionable_insight", "")

        # Extract patterns based on insight type
        if insight_type == "tool_pattern":
            # Tool usage patterns
            if "tools" in data:
                patterns["triggers"] = ["high_frequency_tool_usage"]
                patterns["actions"] = [f"optimize_tool_{tool[0]}" for tool in data["tools"][:2]]

            if "low_success_tools" in data:
                patterns["triggers"] = ["low_tool_success_rate"]
                patterns["actions"] = ["improve_error_handling", "add_validation"]
                patterns["conditions"] = [f"success_rate < 0.8 for {tool[0]}" for tool in data["low_success_tools"][:2]]

        elif insight_type == "error_resolution":
            # Error patterns
            if "error_type" in data:
                patterns["triggers"] = [f"{data['error_type']}_error"]
                patterns["conditions"] = [f"error_count > {data.get('count', 1)}"]

            if "resolution_patterns" in data:
                patterns["actions"] = ["apply_known_resolution", "document_solution"]
                patterns["outcomes"] = ["error_resolved", "pattern_documented"]

        elif insight_type == "task_completion":
            # Workflow patterns
            if "success_rate" in data:
                patterns["triggers"] = ["workflow_completion"]
                patterns["conditions"] = [f"success_rate >= {data['success_rate']:.2f}"]
                patterns["outcomes"] = ["high_success_workflow"]

        # Extract action patterns from actionable insights
        action_keywords = ["optimize", "improve", "consider", "implement", "document", "investigate"]
        for keyword in action_keywords:
            if keyword in actionable.lower():
                patterns["actions"].append(f"{keyword}_based_on_insight")

        return patterns

    def _generate_application_criteria(self, insight: Dict[str, JSONValue], learning_type: str) -> List[str]:
        """Generate criteria for when this learning should be applied."""
        criteria = []

        insight_type = insight.get("type", "")
        category = insight.get("category", "")
        confidence = insight.get("confidence", 0)

        # Base criteria on learning type
        if learning_type == "successful_pattern":
            criteria.extend([
                "Similar task context detected",
                f"Confidence level >= {confidence:.2f}",
                "No conflicting patterns present"
            ])

        elif learning_type == "error_resolution":
            criteria.extend([
                f"Error type matches: {insight.get('data', {}).get('error_type', 'any')}",
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
        metrics = []

        insight_type = insight.get("type", "")
        data = insight.get("data", {})

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
        if "success_rate" in data:
            metrics.append(f"Maintain success rate >= {data['success_rate']:.2f}")

        if "error_rate" in data:
            metrics.append(f"Reduce error rate below {data['error_rate']:.2f}")

        if "tools" in data:
            metrics.append("Tool usage optimization measurable")

        # Default metrics if none specified
        if not metrics:
            metrics = [
                "Objective improvement measured",
                "User feedback positive",
                "No negative side effects"
            ]

        return metrics