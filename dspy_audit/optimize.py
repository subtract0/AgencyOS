"""
Optimization utilities for DSPy Audit System

Handles compilation, optimization, and persistence of DSPy modules.
"""

import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

# Conditional DSPy import
try:
    import dspy
    from dspy.teleprompt import BootstrapFewShot, BootstrapFewShotWithRandomSearch

    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    print("Warning: DSPy not installed. Optimization features disabled.")

from .metrics import (
    audit_effectiveness_metric,
    composite_audit_metric,
    constitutional_compliance_metric,
)
from .modules import AuditRefactorModule


def load_audit_training_data() -> list[dict[str, Any]]:
    """
    Load historical audit data for training.

    Returns:
        List of training examples with inputs and expected outputs
    """
    training_data = []

    # Load from audit logs
    audit_logs_path = Path("logs/audits")
    if audit_logs_path.exists():
        for audit_file in audit_logs_path.glob("*.json"):
            try:
                with open(audit_file) as f:
                    data = json.load(f)
                    # Convert to training example
                    example = {
                        "input": {
                            "code_path": data.get("target_path", ""),
                            "constitution_rules": ["Article I", "Article II"],
                            "historical_patterns": [],
                        },
                        "output": {
                            "issues": data.get("violations", []),
                            "qt_score": data.get("qt_score", 0.5),
                            "recommendations": data.get("recommendations", []),
                        },
                        "metadata": {
                            "timestamp": data.get("timestamp"),
                            "success": data.get("success", True),
                        },
                    }
                    training_data.append(example)
            except Exception as e:
                print(f"Error loading {audit_file}: {e}")

    # Load from comprehensive audit report
    comprehensive_report = Path("comprehensive_audit_report.json")
    if comprehensive_report.exists():
        try:
            with open(comprehensive_report) as f:
                data = json.load(f)
                # Convert critical issues to training examples
                for issue in data.get("critical_issues", []):
                    example = {
                        "input": {
                            "code_path": issue.get("file", ""),
                            "constitution_rules": ["Article I", "Article II"],
                            "historical_patterns": [],
                        },
                        "output": {
                            "issues": [issue],
                            "qt_score": 0.3,  # Critical issues imply low score
                            "recommendations": [issue.get("recommendation", "")],
                        },
                        "known_violations": [issue],
                    }
                    training_data.append(example)
        except Exception as e:
            print(f"Error loading comprehensive report: {e}")

    # Add synthetic examples for constitutional compliance
    synthetic_examples = [
        {
            "input": {
                "code_path": "test_file.py",
                "constitution_rules": [
                    "Article I: Complete Context Before Action",
                    "Article II: 100% Verification and Stability",
                ],
                "historical_patterns": [
                    {"type": "missing_tests", "fix": "add comprehensive tests"}
                ],
            },
            "output": {
                "issues": [
                    {
                        "file_path": "test_file.py",
                        "line_number": 0,
                        "severity": "constitutional",
                        "category": "missing_tests",
                        "description": "No test coverage",
                        "constitutional_article": 2,
                    }
                ],
                "qt_score": 0.0,
                "recommendations": ["Add comprehensive test coverage"],
            },
            "known_violations": [
                {"severity": "constitutional", "type": "missing_tests"}
            ],
        }
    ]

    training_data.extend(synthetic_examples)
    return training_data


def optimize_audit_module(
    module: AuditRefactorModule | None = None,
    training_data: list[dict] | None = None,
    metric=None,
    num_candidates: int = 8,
    max_bootstrapped_demos: int = 4,
    max_labeled_demos: int = 4,
) -> Any:
    """
    Optimize the audit module using DSPy teleprompters.

    Args:
        module: Module to optimize (creates new if None)
        training_data: Training examples (loads default if None)
        metric: Evaluation metric (uses composite if None)
        num_candidates: Number of candidates for random search
        max_bootstrapped_demos: Max bootstrapped demonstrations
        max_labeled_demos: Max labeled demonstrations

    Returns:
        Optimized module or None if DSPy unavailable
    """
    if not DSPY_AVAILABLE:
        print("DSPy not available. Returning unoptimized module.")
        return module or AuditRefactorModule()

    # Initialize module if not provided
    if module is None:
        module = AuditRefactorModule(use_learning=True)

    # Load training data if not provided
    if training_data is None:
        training_data = load_audit_training_data()

    if not training_data:
        print("No training data available. Returning unoptimized module.")
        return module

    # Use composite metric if not provided
    if metric is None:
        metric = composite_audit_metric

    # Set up the teleprompter
    teleprompter = BootstrapFewShotWithRandomSearch(
        metric=metric,
        num_candidates=num_candidates,
        max_bootstrapped_demos=max_bootstrapped_demos,
        max_labeled_demos=max_labeled_demos,
    )

    print(f"Optimizing with {len(training_data)} training examples...")

    # Compile the module
    try:
        optimized_module = teleprompter.compile(
            student=module,
            trainset=training_data,
        )
        print("Optimization complete!")
        return optimized_module
    except Exception as e:
        print(f"Optimization failed: {e}")
        return module


def save_optimized_module(
    module: Any,
    path: str = "models/audit_refactor_optimized.pkl",
    metadata: dict | None = None,
) -> bool:
    """
    Save an optimized module to disk.

    Args:
        module: Optimized module to save
        path: Save path
        metadata: Optional metadata to save alongside

    Returns:
        True if successful
    """
    try:
        # Create directory if needed
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Save module
        with open(path, "wb") as f:
            pickle.dump(module, f)

        # Save metadata if provided
        if metadata:
            metadata_path = path.replace(".pkl", "_metadata.json")
            metadata["saved_at"] = datetime.now().isoformat()
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

        print(f"Module saved to {path}")
        return True
    except Exception as e:
        print(f"Failed to save module: {e}")
        return False


def load_optimized_module(
    path: str = "models/audit_refactor_optimized.pkl",
) -> Any | None:
    """
    Load an optimized module from disk.

    Args:
        path: Path to load from

    Returns:
        Loaded module or None if failed
    """
    try:
        with open(path, "rb") as f:
            module = pickle.load(f)
        print(f"Module loaded from {path}")

        # Load metadata if available
        metadata_path = path.replace(".pkl", "_metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                metadata = json.load(f)
                print(f"Module metadata: {metadata}")

        return module
    except FileNotFoundError:
        print(f"No saved module found at {path}")
        return None
    except Exception as e:
        print(f"Failed to load module: {e}")
        return None


def evaluate_module_performance(
    module: Any, test_data: list[dict] | None = None
) -> dict[str, float]:
    """
    Evaluate module performance on test data.

    Args:
        module: Module to evaluate
        test_data: Test examples (loads default if None)

    Returns:
        Dictionary of performance metrics
    """
    if test_data is None:
        test_data = load_audit_training_data()[-5:]  # Use last 5 as test

    if not test_data:
        return {"error": "No test data available"}

    results = {
        "total_examples": len(test_data),
        "effectiveness_score": 0.0,
        "compliance_score": 0.0,
        "composite_score": 0.0,
        "successful_runs": 0,
    }

    for example in test_data:
        try:
            # Run module
            prediction = module.forward(
                code_path=example["input"]["code_path"],
                max_fixes=3,
                available_time=30,
            )

            # Calculate metrics
            effectiveness = audit_effectiveness_metric(example, prediction)
            compliance = constitutional_compliance_metric(example, prediction)
            composite = composite_audit_metric(example, prediction)

            results["effectiveness_score"] += effectiveness
            results["compliance_score"] += compliance
            results["composite_score"] += composite
            results["successful_runs"] += 1

        except Exception as e:
            print(f"Evaluation error: {e}")

    # Calculate averages
    if results["successful_runs"] > 0:
        results["effectiveness_score"] /= results["successful_runs"]
        results["compliance_score"] /= results["successful_runs"]
        results["composite_score"] /= results["successful_runs"]

    return results


def compare_modules(
    original_module: Any, optimized_module: Any, test_data: list[dict] | None = None
) -> dict[str, dict[str, float]]:
    """
    Compare performance of original vs optimized module.

    Args:
        original_module: Original unoptimized module
        optimized_module: Optimized module
        test_data: Test examples

    Returns:
        Comparison results
    """
    print("Evaluating original module...")
    original_results = evaluate_module_performance(original_module, test_data)

    print("Evaluating optimized module...")
    optimized_results = evaluate_module_performance(optimized_module, test_data)

    # Calculate improvements
    improvements = {}
    for key in original_results:
        if key != "total_examples" and key != "successful_runs":
            if original_results[key] > 0:
                improvement = (
                    (optimized_results[key] - original_results[key])
                    / original_results[key]
                    * 100
                )
                improvements[f"{key}_improvement_pct"] = improvement

    return {
        "original": original_results,
        "optimized": optimized_results,
        "improvements": improvements,
    }


def continuous_learning_loop(
    module: Any, new_examples: list[dict], reoptimize_threshold: int = 10
) -> Any:
    """
    Continuously improve module with new examples.

    Args:
        module: Current module
        new_examples: New training examples
        reoptimize_threshold: Number of examples before reoptimization

    Returns:
        Updated module
    """
    # Load existing training data
    existing_data = load_audit_training_data()

    # Add new examples
    existing_data.extend(new_examples)

    # Check if reoptimization needed
    if len(new_examples) >= reoptimize_threshold:
        print(f"Reoptimizing with {len(new_examples)} new examples...")
        module = optimize_audit_module(
            module=module,
            training_data=existing_data,
        )

        # Save the updated module
        save_optimized_module(
            module,
            metadata={
                "training_examples": len(existing_data),
                "new_examples": len(new_examples),
            },
        )

    return module
