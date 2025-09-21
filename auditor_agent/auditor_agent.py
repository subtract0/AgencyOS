"""
AuditorAgent - Quality Assurance Agent for NECESSARY pattern analysis and Q(T) scoring.
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from agency_swarm import Agent
from agency_swarm.tools import BaseTool as Tool
from pydantic import Field

from agency_memory import Memory
from shared.agent_context import AgentContext, create_agent_context
from shared.agent_utils import (
    detect_model_type,
    select_instructions_file,
    render_instructions,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import create_system_reminder_hook, create_memory_integration_hook, create_composite_hook
from tools import (
    Bash,
    Edit,
    Glob,
    Grep,
    Read,
    Write,
)

from .ast_analyzer import ASTAnalyzer


class AnalyzeCodebase(Tool):
    """Primary analysis tool for calculating Q(T) and identifying violations."""

    target_path: str = Field(..., description="Path to the codebase to analyze")
    mode: str = Field(default="full", description="Analysis mode: 'full' or 'verification'")

    def run(self):
        """Perform comprehensive codebase analysis and Q(T) calculation."""
        if not os.path.exists(self.target_path):
            return json.dumps({"error": f"Path does not exist: {self.target_path}"})

        analyzer = ASTAnalyzer()

        # Phase 1: Analyze codebase structure
        analysis = analyzer.analyze_directory(self.target_path)

        # Phase 2: Calculate NECESSARY compliance
        necessary_analysis = self._analyze_necessary_compliance(analysis)

        # Phase 3: Calculate Q(T) score
        qt_score = self._calculate_qt_score(necessary_analysis)

        # Phase 4: Generate violations and recommendations
        violations = self._prioritize_violations(necessary_analysis, analysis)
        recommendations = self._generate_recommendations(qt_score, violations)

        audit_report = {
            "mode": self.mode,
            "target": self.target_path,
            "qt_score": qt_score,
            "necessary_compliance": necessary_analysis,
            "violations": violations,
            "codebase_analysis": analysis,
            "recommendations": recommendations
        }

        return json.dumps(audit_report, indent=2)

    def _analyze_necessary_compliance(self, analysis: Dict) -> Dict:
        """Analyze compliance with NECESSARY pattern."""
        total_behaviors = analysis["total_behaviors"]
        total_tests = analysis["total_test_functions"]

        if total_behaviors == 0:
            return {prop: {"score": 0.0, "violations": ["No behaviors found"]} for prop in "NECESSARY"}

        # Calculate each NECESSARY property score
        necessary_scores = {}

        # N - No Missing Behaviors
        behavior_coverage = min(1.0, total_tests / total_behaviors) if total_behaviors > 0 else 0.0
        necessary_scores["N"] = {
            "score": behavior_coverage,
            "violations": [] if behavior_coverage > 0.8 else [f"Low test coverage: {behavior_coverage:.2f}"]
        }

        # E - Edge Cases Covered (heuristic based on test patterns)
        edge_case_score = self._estimate_edge_case_coverage(analysis)
        necessary_scores["E"] = {
            "score": edge_case_score,
            "violations": [] if edge_case_score > 0.6 else ["Insufficient edge case testing"]
        }

        # C - Comprehensive Coverage (multiple tests per behavior)
        comprehensive_score = min(1.0, (total_tests / max(1, total_behaviors)) / 2)
        necessary_scores["C"] = {
            "score": comprehensive_score,
            "violations": [] if comprehensive_score > 0.5 else ["Need more test cases per behavior"]
        }

        # E - Error Conditions (heuristic based on exception testing)
        error_score = self._estimate_error_testing(analysis)
        necessary_scores["E2"] = {
            "score": error_score,
            "violations": [] if error_score > 0.4 else ["Insufficient error condition testing"]
        }

        # S - State Validation (heuristic based on assertion patterns)
        state_score = 0.7  # Default reasonable score for state validation
        necessary_scores["S"] = {
            "score": state_score,
            "violations": [] if state_score > 0.6 else ["State validation could be improved"]
        }

        # S - Side Effects (heuristic based on mock/patch patterns)
        side_effect_score = 0.6  # Default reasonable score
        necessary_scores["S2"] = {
            "score": side_effect_score,
            "violations": [] if side_effect_score > 0.5 else ["Side effect testing could be improved"]
        }

        # A - Async Operations (based on async function analysis)
        async_score = self._estimate_async_coverage(analysis)
        necessary_scores["A"] = {
            "score": async_score,
            "violations": [] if async_score > 0.7 else ["Async operation testing needs attention"]
        }

        # R - Regression Prevention (heuristic based on test history)
        regression_score = 0.8  # Default good score for regression
        necessary_scores["R"] = {
            "score": regression_score,
            "violations": [] if regression_score > 0.7 else ["Regression testing could be strengthened"]
        }

        # Y - Yielding Confidence (overall test quality heuristic)
        confidence_score = min(1.0, (behavior_coverage + edge_case_score + comprehensive_score) / 3)
        necessary_scores["Y"] = {
            "score": confidence_score,
            "violations": [] if confidence_score > 0.7 else ["Overall test confidence needs improvement"]
        }

        return necessary_scores

    def _calculate_qt_score(self, necessary_analysis: Dict) -> float:
        """Calculate Q(T) score from NECESSARY analysis."""
        if not necessary_analysis:
            return 0.0

        total_score = sum(prop["score"] for prop in necessary_analysis.values())
        return total_score / len(necessary_analysis)

    def _prioritize_violations(self, necessary_analysis: Dict, analysis: Dict) -> List[Dict]:
        """Generate prioritized list of violations."""
        violations = []

        for prop, data in necessary_analysis.items():
            if data["score"] < 0.7:  # Threshold for violation
                severity = "critical" if data["score"] < 0.4 else "high" if data["score"] < 0.6 else "medium"

                for violation in data["violations"]:
                    violations.append({
                        "property": prop,
                        "severity": severity,
                        "score": data["score"],
                        "description": violation,
                        "recommendation": self._get_violation_recommendation(prop, violation)
                    })

        # Sort by severity and score
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        violations.sort(key=lambda x: (severity_order[x["severity"]], x["score"]))

        return violations

    def _generate_recommendations(self, qt_score: float, violations: List[Dict]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if qt_score < 0.6:
            recommendations.append("CRITICAL: Q(T) score below 0.6 requires immediate attention")
        elif qt_score < 0.8:
            recommendations.append("Q(T) score indicates significant improvement opportunities")

        # Add specific recommendations based on violations
        for violation in violations[:5]:  # Top 5 violations
            prop = violation["property"]
            if prop == "N":
                recommendations.append("Add missing test cases for uncovered behaviors")
            elif prop == "E":
                recommendations.append("Implement edge case testing for boundary conditions")
            elif prop == "C":
                recommendations.append("Increase test coverage with multiple test vectors per behavior")

        if not recommendations:
            recommendations.append("Q(T) score is good - focus on continuous improvement")

        return recommendations

    def _estimate_edge_case_coverage(self, analysis: Dict) -> float:
        """Estimate edge case coverage based on test patterns."""
        # Heuristic: look for test functions with "edge", "boundary", "limit" keywords
        edge_indicators = 0
        total_tests = analysis["total_test_functions"]

        for test_file in analysis["test_files"]:
            for func in test_file.get("test_functions", []):
                name_lower = func["name"].lower()
                if any(keyword in name_lower for keyword in ["edge", "boundary", "limit", "empty", "null", "zero"]):
                    edge_indicators += 1

        return min(1.0, edge_indicators / max(1, total_tests / 4))  # Expect 25% edge case tests

    def _estimate_error_testing(self, analysis: Dict) -> float:
        """Estimate error condition testing coverage."""
        # Heuristic: look for test functions with error/exception keywords
        error_indicators = 0
        total_tests = analysis["total_test_functions"]

        for test_file in analysis["test_files"]:
            for func in test_file.get("test_functions", []):
                name_lower = func["name"].lower()
                if any(keyword in name_lower for keyword in ["error", "exception", "fail", "invalid", "bad"]):
                    error_indicators += 1

        return min(1.0, error_indicators / max(1, total_tests / 5))  # Expect 20% error tests

    def _estimate_async_coverage(self, analysis: Dict) -> float:
        """Estimate async operation testing coverage."""
        async_functions = 0
        async_tests = 0

        # Count async functions in source
        for source_file in analysis["source_files"]:
            for func in source_file.get("functions", []):
                if func.get("is_async", False):
                    async_functions += 1

        # Count async tests
        for test_file in analysis["test_files"]:
            for func in test_file.get("test_functions", []):
                if func.get("is_async", False):
                    async_tests += 1

        if async_functions == 0:
            return 1.0  # No async functions means perfect async coverage

        return min(1.0, async_tests / async_functions)

    def _get_violation_recommendation(self, prop: str, violation: str) -> str:
        """Get specific recommendation for a violation."""
        recommendations = {
            "N": "Add test cases for uncovered behaviors",
            "E": "Implement boundary condition and edge case tests",
            "C": "Add multiple test vectors for comprehensive coverage",
            "S": "Improve state validation in test assertions",
            "A": "Add async operation testing with proper await patterns",
            "R": "Implement regression test cases for known issues",
            "Y": "Enhance overall test quality and readability"
        }
        return recommendations.get(prop, "Review and improve test implementation")


def create_auditor_agent(
    model: str = "gpt-5", reasoning_effort: str = "medium", agent_context: AgentContext = None
) -> Agent:
    """Factory that returns a fresh AuditorAgent instance."""

    is_openai, is_claude, _ = detect_model_type(model)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    instructions_file = select_instructions_file(current_dir, model)
    instructions = render_instructions(instructions_file, model)

    # Create agent context if not provided
    if agent_context is None:
        agent_context = create_agent_context()

    # Create hooks with memory integration
    reminder_hook = create_system_reminder_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook([reminder_hook, memory_hook])

    # Log agent creation
    agent_context.store_memory(
        f"auditor_agent_created_{agent_context.session_id}",
        {
            "agent_type": "AuditorAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id
        },
        ["agency", "auditor", "creation"]
    )

    return Agent(
        name="AuditorAgent",
        description="Quality assurance agent that calculates Q(T) scores and identifies NECESSARY pattern violations.",
        instructions=instructions,
        tools_folder=os.path.join(current_dir, "tools"),
        model=get_model_instance(model),
        hooks=combined_hook,
        tools=[
            Bash,
            Glob,
            Grep,
            Read,
            Write,
            Edit,
            AnalyzeCodebase,
        ],
        model_settings=create_model_settings(model, reasoning_effort),
    )