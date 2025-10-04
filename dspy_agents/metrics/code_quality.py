"""
Code Quality Metrics for DSPy Agents

Provides evaluation metrics for measuring agent performance,
focusing on test passage, code quality, and task completion.
"""

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def code_agent_metric(example: Any, prediction: Any, trace: Any | None = None) -> float:
    """
    Evaluate CodeAgent performance across multiple dimensions.

    Scoring breakdown:
    - Test passage (40%): All tests must pass
    - Code quality (30%): No linting errors, follows standards
    - Task completion (30%): All requirements met

    Args:
        example: The input example with expected outcomes
        prediction: The agent's prediction/output
        trace: Optional trace information for debugging

    Returns:
        Float score between 0.0 and 1.0
    """
    score = 0.0

    try:
        # Test passage (40%)
        if hasattr(prediction, "verification_status"):
            if prediction.verification_status.all_tests_pass:
                score += 0.4
                logger.debug("Tests passed: +0.4")
        elif hasattr(prediction, "success") and prediction.success:
            # Fallback for simpler result formats
            score += 0.4
            logger.debug("Operation succeeded: +0.4")

        # Code quality (30%)
        quality_score = 0.0
        if hasattr(prediction, "verification_status"):
            if prediction.verification_status.no_linting_errors:
                quality_score += 0.15
            if prediction.verification_status.constitutional_compliance:
                quality_score += 0.15
        elif hasattr(prediction, "changes") and prediction.changes:
            # Basic quality check: changes were made
            quality_score += 0.3

        score += quality_score
        logger.debug(f"Code quality: +{quality_score}")

        # Task completion (30%)
        completion_score = 0.0
        if hasattr(example, "requirements") and hasattr(prediction, "code_changes"):
            # Check if all requirements are addressed in changes
            requirements_met = all(
                any(req.lower() in str(change).lower() for change in prediction.code_changes)
                for req in example.requirements
            )
            if requirements_met:
                completion_score += 0.3
        elif hasattr(prediction, "changes") and prediction.changes:
            # Basic completion: some changes were made
            completion_score += 0.3

        score += completion_score
        logger.debug(f"Task completion: +{completion_score}")

    except Exception as e:
        logger.error(f"Error calculating code_agent_metric: {e}")
        # Return partial score if we got some results

    return min(score, 1.0)  # Cap at 1.0


def auditor_agent_metric(example: Any, prediction: Any, trace: Any | None = None) -> float:
    """
    Evaluate AuditorAgent performance.

    Scoring breakdown:
    - Finding accuracy (40%): Correct identification of issues
    - Severity assessment (30%): Proper prioritization
    - Recommendation quality (30%): Actionable fixes provided

    Args:
        example: The input example with expected findings
        prediction: The agent's audit results
        trace: Optional trace information

    Returns:
        Float score between 0.0 and 1.0
    """
    score = 0.0

    try:
        # Finding accuracy (40%)
        if hasattr(prediction, "findings") and prediction.findings:
            if hasattr(example, "expected_findings"):
                # Calculate precision/recall if we have expected findings
                found_issues = {f.category for f in prediction.findings}
                expected_issues = set(example.expected_findings)

                if expected_issues:
                    overlap = found_issues & expected_issues
                    precision = len(overlap) / len(found_issues) if found_issues else 0
                    recall = len(overlap) / len(expected_issues)
                    f1_score = (
                        2 * (precision * recall) / (precision + recall)
                        if (precision + recall) > 0
                        else 0
                    )
                    score += 0.4 * f1_score
                else:
                    # No expected findings, reward for finding anything
                    score += 0.4
            else:
                # Basic check: some findings were identified
                score += 0.4

        # Severity assessment (30%)
        if hasattr(prediction, "findings") and prediction.findings:
            # Check if severities are properly assigned
            valid_severities = {"critical", "high", "medium", "low"}
            all_valid = all(
                hasattr(f, "severity") and f.severity in valid_severities
                for f in prediction.findings
            )
            if all_valid:
                score += 0.3

        # Recommendation quality (30%)
        if hasattr(prediction, "findings") and prediction.findings:
            # Check if recommendations are provided and non-empty
            has_recommendations = all(
                hasattr(f, "recommendation") and len(f.recommendation) > 10
                for f in prediction.findings
            )
            if has_recommendations:
                score += 0.3
        elif hasattr(prediction, "recommendations") and prediction.recommendations:
            # Alternative format
            score += 0.3

    except Exception as e:
        logger.error(f"Error calculating auditor_agent_metric: {e}")

    return min(score, 1.0)


def planner_agent_metric(example: Any, prediction: Any, trace: Any | None = None) -> float:
    """
    Evaluate PlannerAgent performance.

    Scoring breakdown:
    - Plan completeness (40%): All necessary steps included
    - Resource allocation (30%): Proper agent assignments
    - Risk assessment (30%): Identified risks and mitigations

    Args:
        example: The input example with planning requirements
        prediction: The agent's plan
        trace: Optional trace information

    Returns:
        Float score between 0.0 and 1.0
    """
    score = 0.0

    try:
        # Plan completeness (40%)
        if hasattr(prediction, "plan") and hasattr(prediction.plan, "steps"):
            if len(prediction.plan.steps) > 0:
                # Basic: has steps
                score += 0.2

                # Advanced: reasonable number of steps
                if 3 <= len(prediction.plan.steps) <= 20:
                    score += 0.2
        elif hasattr(prediction, "tasks") and prediction.tasks:
            # Alternative format
            score += 0.4

        # Resource allocation (30%)
        if hasattr(prediction, "plan") and hasattr(prediction.plan, "agent_assignments"):
            if prediction.plan.agent_assignments:
                score += 0.3
        elif hasattr(prediction, "task_dependencies") and prediction.task_dependencies:
            # Alternative: has dependencies mapped
            score += 0.3

        # Risk assessment (30%)
        if hasattr(prediction, "plan") and hasattr(prediction.plan, "risk_factors"):
            if prediction.plan.risk_factors:
                score += 0.3
        elif hasattr(prediction, "risks") and prediction.risks:
            # Alternative format
            score += 0.3

    except Exception as e:
        logger.error(f"Error calculating planner_agent_metric: {e}")

    return min(score, 1.0)


def learning_agent_metric(example: Any, prediction: Any, trace: Any | None = None) -> float:
    """
    Evaluate LearningAgent performance.

    Scoring breakdown:
    - Pattern extraction (40%): Meaningful patterns identified
    - Confidence calibration (30%): Appropriate confidence scores
    - Knowledge consolidation (30%): Effective learning storage

    Args:
        example: The input example with session data
        prediction: The agent's extracted learnings
        trace: Optional trace information

    Returns:
        Float score between 0.0 and 1.0
    """
    score = 0.0

    try:
        # Pattern extraction (40%)
        if hasattr(prediction, "patterns") and prediction.patterns:
            # Basic: patterns were found
            score += 0.2

            # Advanced: patterns have required fields
            valid_patterns = all(
                isinstance(p, dict) and "type" in p and "description" in p
                for p in prediction.patterns
            )
            if valid_patterns:
                score += 0.2

        # Confidence calibration (30%)
        if hasattr(prediction, "confidence_scores") and prediction.confidence_scores:
            # Check if confidence scores are reasonable (between 0 and 1)
            valid_scores = all(
                0.0 <= score <= 1.0 for score in prediction.confidence_scores.values()
            )
            if valid_scores:
                score += 0.3

        # Knowledge consolidation (30%)
        if hasattr(prediction, "consolidated_learnings") and prediction.consolidated_learnings:
            score += 0.15
        if hasattr(prediction, "storage_confirmation") and prediction.storage_confirmation:
            score += 0.15

    except Exception as e:
        logger.error(f"Error calculating learning_agent_metric: {e}")

    return min(score, 1.0)


def get_agent_metric(agent_name: str) -> Callable:
    """
    Get the appropriate metric function for an agent.

    Args:
        agent_name: Name of the agent

    Returns:
        Metric function for the agent

    Raises:
        ValueError: If agent_name is not recognized
    """
    metrics = {
        "code": code_agent_metric,
        "code_agent": code_agent_metric,
        "auditor": auditor_agent_metric,
        "auditor_agent": auditor_agent_metric,
        "planner": planner_agent_metric,
        "planner_agent": planner_agent_metric,
        "learning": learning_agent_metric,
        "learning_agent": learning_agent_metric,
    }

    agent_name_lower = agent_name.lower()
    if agent_name_lower not in metrics:
        raise ValueError(f"No metric found for agent: {agent_name}")

    return metrics[agent_name_lower]


# Constitutional compliance metric
def constitutional_compliance_metric(prediction: Any, trace: Any | None = None) -> float:
    """
    Measure compliance with Agency constitutional principles.

    Returns a score from 0.0 to 1.0 based on adherence to:
    - TDD practices
    - Type safety
    - Input validation
    - Error handling patterns
    - API standardization

    Args:
        prediction: The agent's output
        trace: Optional trace information

    Returns:
        Float score between 0.0 and 1.0
    """
    score = 0.0
    checks_passed = 0
    total_checks = 5

    try:
        # Check 1: Tests included (TDD)
        if hasattr(prediction, "tests") and prediction.tests:
            checks_passed += 1
        elif hasattr(prediction, "tests_added") and prediction.tests_added:
            checks_passed += 1

        # Check 2: Type safety
        if hasattr(prediction, "__annotations__"):
            # Has type annotations
            checks_passed += 1

        # Check 3: Input validation
        if hasattr(prediction, "verification_status"):
            checks_passed += 1

        # Check 4: Error handling
        if hasattr(prediction, "success"):
            # Uses result pattern
            checks_passed += 1

        # Check 5: API standardization
        standard_fields = {"success", "changes", "tests", "message"}
        if hasattr(prediction, "__dict__"):
            pred_fields = set(prediction.__dict__.keys())
            if pred_fields & standard_fields:
                checks_passed += 1

        score = checks_passed / total_checks

    except Exception as e:
        logger.error(f"Error calculating constitutional_compliance_metric: {e}")

    return score


# Composite metric for overall agent quality
def overall_agent_metric(
    example: Any, prediction: Any, agent_type: str, trace: Any | None = None
) -> float:
    """
    Calculate overall agent quality score combining task-specific and constitutional metrics.

    Args:
        example: The input example
        prediction: The agent's output
        agent_type: Type of agent being evaluated
        trace: Optional trace information

    Returns:
        Float score between 0.0 and 1.0
    """
    # Get task-specific score (70% weight)
    try:
        metric_fn = get_agent_metric(agent_type)
        task_score = metric_fn(example, prediction, trace)
    except Exception as e:
        logger.error(f"Error getting task metric: {e}")
        task_score = 0.0

    # Get constitutional compliance score (30% weight)
    constitutional_score = constitutional_compliance_metric(prediction, trace)

    # Weighted average
    overall_score = (0.7 * task_score) + (0.3 * constitutional_score)

    logger.info(
        f"Overall metric for {agent_type}: task={task_score:.2f}, constitutional={constitutional_score:.2f}, overall={overall_score:.2f}"
    )

    return overall_score
