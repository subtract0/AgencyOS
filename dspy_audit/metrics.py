"""
Metrics for DSPy Audit System

Defines metrics for evaluating and optimizing the audit modules.
"""

from typing import Any

from shared.type_definitions.json import JSONValue


def audit_effectiveness_metric(
    example: dict[str, JSONValue], prediction: dict[str, JSONValue], trace: Any | None = None
) -> float:
    """
    Measure the effectiveness of an audit.

    Evaluates:
    - Detection of known violations
    - Correct prioritization
    - Fix success rate
    - Constitutional compliance

    Args:
        example: Ground truth with known issues
        prediction: Model's predictions
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0

    # Check if all constitutional violations were detected (40% weight)
    if "known_violations" in example and "issues" in prediction:
        known_constitutional = [
            v for v in example["known_violations"] if v.get("severity") == "constitutional"
        ]
        detected_constitutional = [
            i for i in prediction["issues"] if i.severity.value == "constitutional"
        ]

        if known_constitutional:
            detection_rate = len(detected_constitutional) / len(known_constitutional)
            score += 0.4 * min(1.0, detection_rate)
        else:
            score += 0.4  # No constitutional violations to detect

    # Check if prioritization is correct (30% weight)
    if "issues" in prediction and len(prediction["issues"]) > 0:
        # Constitutional issues should be prioritized first
        first_issue = prediction["issues"][0]
        if hasattr(first_issue, "severity") and first_issue.severity.value == "constitutional":
            score += 0.3
        elif not any(i.severity.value == "constitutional" for i in prediction["issues"]):
            score += 0.3  # No constitutional issues, any prioritization is acceptable

    # Check if fixes passed tests (30% weight)
    if "verification" in prediction:
        if prediction["verification"].get("success", False):
            score += 0.3
        elif prediction["verification"].get("tests_passed", {}).get("unit_tests", False):
            score += 0.15  # Partial credit for passing some tests

    return score


def refactoring_success_metric(
    example: dict[str, JSONValue], prediction: dict[str, JSONValue], trace: Any | None = None
) -> float:
    """
    Measure the success of refactoring operations.

    Evaluates:
    - Fix application success
    - Test passage rate
    - No regressions introduced
    - Code quality improvement

    Args:
        example: Expected refactoring outcome
        prediction: Actual refactoring results
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0

    # Fix application success (40% weight)
    if "applied_fixes" in prediction and "failed_fixes" in prediction:
        total_fixes = len(prediction["applied_fixes"]) + len(prediction["failed_fixes"])
        if total_fixes > 0:
            success_rate = len(prediction["applied_fixes"]) / total_fixes
            score += 0.4 * success_rate
        else:
            score += 0.4  # No fixes attempted

    # Test passage (30% weight)
    if "verification" in prediction:
        test_results = prediction["verification"].get("test_results", {})
        if all(test_results.values()):
            score += 0.3
        elif len(test_results) > 0:
            passing_rate = sum(1 for v in test_results.values() if v) / len(test_results)
            score += 0.3 * passing_rate

    # No regressions (20% weight)
    if "verification" in prediction:
        if not prediction["verification"].get("rollback_needed", False):
            score += 0.2

    # Code quality improvement (10% weight)
    if "metrics" in prediction:
        qt_improvement = prediction["metrics"].get("qt_score_improvement", 0)
        if qt_improvement > 0:
            score += 0.1 * min(1.0, qt_improvement * 5)  # 0.2 improvement = full credit

    return score


def constitutional_compliance_metric(
    example: dict[str, JSONValue], prediction: dict[str, JSONValue], trace: Any | None = None
) -> float:
    """
    Measure constitutional compliance of the audit and fixes.

    Evaluates adherence to the 5 constitutional articles:
    1. Complete Context Before Action
    2. 100% Verification and Stability
    3. Automated Merge Enforcement
    4. Continuous Learning and Improvement
    5. Spec-Driven Development

    Args:
        example: Expected compliance standards
        prediction: Actual compliance results
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0
    weights = [0.25, 0.30, 0.15, 0.15, 0.15]  # Article weights

    # Article I: Complete Context (25% weight)
    if "audit" in prediction:
        audit = prediction["audit"]
        if hasattr(audit, "historical_patterns"):
            if len(audit.historical_patterns) > 0:
                score += weights[0]  # Used historical context
        elif "historical_patterns" in audit and len(audit.get("historical_patterns", [])) > 0:
            score += weights[0]

    # Article II: 100% Verification (30% weight)
    if "verification" in prediction:
        verification = prediction["verification"]
        test_results = verification.get("test_results", {})
        if all(test_results.values()):
            score += weights[1]  # All tests passed
        elif len(test_results) > 0:
            passing_rate = sum(1 for v in test_results.values() if v) / len(test_results)
            if passing_rate >= 0.95:  # 95% is close enough to 100%
                score += weights[1] * 0.8

    # Article III: Automated Enforcement (15% weight)
    if "applied_fixes" in prediction:
        # Check if fixes were automatically verified
        all_verified = all(fix.get("tests_passed", False) for fix in prediction["applied_fixes"])
        if all_verified:
            score += weights[2]

    # Article IV: Continuous Learning (15% weight)
    if "learning" in prediction and prediction["learning"]:
        learning = prediction["learning"]
        if hasattr(learning, "success_patterns"):
            if len(learning.success_patterns) > 0:
                score += weights[3]
        elif "success_patterns" in learning and len(learning.get("success_patterns", [])) > 0:
            score += weights[3]

    # Article V: Spec-Driven Development (15% weight)
    if "prioritization" in prediction:
        prioritization = prediction["prioritization"]
        if hasattr(prioritization, "rationale"):
            if prioritization.rationale:
                score += weights[4]
        elif "rationale" in prioritization and prioritization.get("rationale"):
            score += weights[4]

    return score


def learning_effectiveness_metric(
    example: dict[str, JSONValue], prediction: dict[str, JSONValue], trace: Any | None = None
) -> float:
    """
    Measure the effectiveness of learning and pattern extraction.

    Evaluates:
    - Pattern quality
    - Pattern reusability
    - Anti-pattern identification
    - Knowledge accumulation

    Args:
        example: Expected learning outcomes
        prediction: Actual learning results
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0

    if "learning" not in prediction or not prediction["learning"]:
        return 0.0

    learning = prediction["learning"]

    # Success pattern extraction (40% weight)
    success_patterns = (
        learning.success_patterns
        if hasattr(learning, "success_patterns")
        else learning.get("success_patterns", [])
    )
    if len(success_patterns) > 0:
        score += 0.4 * min(1.0, len(success_patterns) / 3)  # 3+ patterns = full credit

    # Anti-pattern identification (30% weight)
    failure_patterns = (
        learning.failure_patterns
        if hasattr(learning, "failure_patterns")
        else learning.get("failure_patterns", [])
    )
    if len(failure_patterns) > 0:
        score += 0.3 * min(1.0, len(failure_patterns) / 2)  # 2+ anti-patterns = full credit

    # Pattern reusability (20% weight)
    if "metrics" in prediction:
        reuse_rate = prediction["metrics"].get("learning_pattern_reuse", 0)
        score += 0.2 * reuse_rate

    # Optimization suggestions (10% weight)
    suggestions = (
        learning.optimization_suggestions
        if hasattr(learning, "optimization_suggestions")
        else learning.get("optimization_suggestions", [])
    )
    if len(suggestions) > 0:
        score += 0.1

    return score


def composite_audit_metric(
    example: dict[str, JSONValue], prediction: dict[str, JSONValue], trace: Any | None = None
) -> float:
    """
    Composite metric combining all audit metrics.

    Provides a single score for overall audit quality.

    Args:
        example: Ground truth
        prediction: Model predictions
        trace: Optional execution trace

    Returns:
        Weighted average score between 0.0 and 1.0
    """
    # Calculate individual metrics
    effectiveness = audit_effectiveness_metric(example, prediction, trace)
    refactoring = refactoring_success_metric(example, prediction, trace)
    compliance = constitutional_compliance_metric(example, prediction, trace)
    learning = learning_effectiveness_metric(example, prediction, trace)

    # Weighted average
    weights = {
        "effectiveness": 0.35,
        "refactoring": 0.25,
        "compliance": 0.30,
        "learning": 0.10,
    }

    composite_score = (
        effectiveness * weights["effectiveness"]
        + refactoring * weights["refactoring"]
        + compliance * weights["compliance"]
        + learning * weights["learning"]
    )

    return composite_score


def calculate_improvement_delta(
    before_metrics: dict[str, float], after_metrics: dict[str, float]
) -> dict[str, float]:
    """
    Calculate improvement between before and after states.

    Args:
        before_metrics: Metrics before audit/refactoring
        after_metrics: Metrics after audit/refactoring

    Returns:
        Dictionary of improvements for each metric
    """
    improvements = {}

    for key in after_metrics:
        if key in before_metrics:
            improvements[f"{key}_delta"] = after_metrics[key] - before_metrics[key]
            if before_metrics[key] > 0:
                improvements[f"{key}_pct_change"] = (
                    (after_metrics[key] - before_metrics[key]) / before_metrics[key] * 100
                )

    return improvements
