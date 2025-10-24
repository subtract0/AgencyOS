#!/usr/bin/env python3
"""
Tune confidence thresholds for TRM router deployment.

Evaluates multiple confidence thresholds on validation set and recommends
optimal cutoff for production based on Precision/Recall trade-offs.

Includes calibration analysis (Brier score, ROC-AUC) and Platt scaling.

Usage:
    python scripts/tune_thresholds.py \
        --model models/trm_router_lora \
        --val-data learning/trm_labels_val.jsonl \
        --output models/trm_router_lora/threshold_analysis.json

Outputs:
    - threshold_analysis.json: Metrics for each threshold
    - calibration_plot.png: Calibration curve
    - roc_curve.png: ROC curve with optimal threshold
"""
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    roc_curve, brier_score_loss, precision_recall_curve
)
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


def load_validation_data(val_path: Path) -> Tuple[List[dict], List[int]]:
    """Load validation data and extract labels."""
    examples = []
    labels = []

    with open(val_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                examples.append(obj)
                labels.append(obj.get("label", 0))

    return examples, labels


def simulate_router_predictions(examples: List[dict], seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate router predictions with confidence scores.

    NOTE: Replace this with actual TRM router inference in production.
    This is a placeholder for testing threshold tuning logic.
    """
    np.random.seed(seed)

    # Placeholder: generate random confidence scores (0-1) and predictions
    # In production, replace with: router.predict_proba(examples)
    n = len(examples)
    confidences = np.random.rand(n)
    predictions = (confidences > 0.5).astype(int)

    return predictions, confidences


def evaluate_threshold(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: float
) -> Dict[str, float]:
    """
    Evaluate metrics at a specific confidence threshold.

    Args:
        y_true: Ground truth labels (0 or 1)
        y_pred_proba: Predicted probabilities (0.0 to 1.0)
        threshold: Confidence threshold for positive class

    Returns:
        Dict of metrics: precision, recall, f1, accuracy, etc.
    """
    y_pred = (y_pred_proba >= threshold).astype(int)

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    accuracy = (y_pred == y_true).mean()

    # True positives, false positives, false negatives
    tp = ((y_pred == 1) & (y_true == 1)).sum()
    fp = ((y_pred == 1) & (y_true == 0)).sum()
    fn = ((y_pred == 0) & (y_true == 1)).sum()
    tn = ((y_pred == 0) & (y_true == 0)).sum()

    # Specificity (true negative rate)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return {
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "specificity": specificity,
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn)
    }


def find_optimal_threshold(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    criterion: str = "f1"
) -> Tuple[float, Dict]:
    """
    Find optimal threshold by maximizing a criterion (F1, precision, recall).

    Args:
        y_true: Ground truth labels
        y_pred_proba: Predicted probabilities
        criterion: Metric to optimize ("f1", "precision", "recall")

    Returns:
        (optimal_threshold, metrics_at_optimal)
    """
    thresholds = np.linspace(0.1, 0.9, 41)  # Test 41 thresholds from 0.1 to 0.9
    results = [evaluate_threshold(y_true, y_pred_proba, t) for t in thresholds]

    # Find threshold that maximizes criterion
    best_idx = max(range(len(results)), key=lambda i: results[i][criterion])
    optimal_threshold = results[best_idx]["threshold"]
    optimal_metrics = results[best_idx]

    return optimal_threshold, optimal_metrics


def compute_calibration_metrics(y_true: np.ndarray, y_pred_proba: np.ndarray) -> Dict:
    """
    Compute calibration metrics: Brier score, ROC-AUC, calibration curve.

    Args:
        y_true: Ground truth labels (0 or 1)
        y_pred_proba: Predicted probabilities (0.0 to 1.0)

    Returns:
        Dict of calibration metrics
    """
    brier = brier_score_loss(y_true, y_pred_proba)
    roc_auc = roc_auc_score(y_true, y_pred_proba)

    # Calibration curve (bin predictions into 10 bins)
    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_true, y_pred_proba, n_bins=10, strategy='uniform'
    )

    # Expected Calibration Error (ECE)
    # ECE = sum of |mean_predicted - fraction_positive| weighted by bin size
    bin_counts = np.histogram(y_pred_proba, bins=10, range=(0, 1))[0]
    bin_weights = bin_counts / len(y_pred_proba)
    ece = np.sum(bin_weights * np.abs(mean_predicted_value - fraction_of_positives))

    return {
        "brier_score": brier,
        "roc_auc": roc_auc,
        "expected_calibration_error": ece,
        "calibration_curve": {
            "mean_predicted": mean_predicted_value.tolist(),
            "fraction_positive": fraction_of_positives.tolist()
        }
    }


def plot_roc_curve(y_true: np.ndarray, y_pred_proba: np.ndarray, output_path: Path, optimal_threshold: float):
    """Generate ROC curve plot with optimal threshold marked."""
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    roc_auc = roc_auc_score(y_true, y_pred_proba)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random classifier')

    # Mark optimal threshold
    idx_optimal = np.argmin(np.abs(thresholds - optimal_threshold))
    plt.scatter(fpr[idx_optimal], tpr[idx_optimal], color='red', s=100, zorder=5,
                label=f'Optimal threshold = {optimal_threshold:.2f}')

    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve - TRM Router')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ ROC curve saved: {output_path}")


def plot_calibration_curve(y_true: np.ndarray, y_pred_proba: np.ndarray, output_path: Path):
    """Generate calibration curve plot."""
    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_true, y_pred_proba, n_bins=10, strategy='uniform'
    )

    plt.figure(figsize=(8, 6))
    plt.plot(mean_predicted_value, fraction_of_positives, 's-', color='blue', label='TRM Router')
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')

    plt.xlabel('Mean Predicted Probability')
    plt.ylabel('Fraction of Positives')
    plt.title('Calibration Curve - TRM Router')
    plt.legend(loc="upper left")
    plt.grid(alpha=0.3)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Calibration curve saved: {output_path}")


def recommend_production_threshold(threshold_results: List[Dict]) -> Dict:
    """
    Recommend production threshold based on safety/precision trade-offs.

    Heuristic: Prioritize precision ≥0.80 (avoid false positives),
    while maintaining reasonable recall ≥0.70.
    """
    # Filter thresholds meeting minimum precision
    candidates = [r for r in threshold_results if r["precision"] >= 0.80]

    if not candidates:
        # Fallback: choose threshold with highest F1
        best = max(threshold_results, key=lambda r: r["f1"])
        return {
            "recommended_threshold": best["threshold"],
            "rationale": "No threshold met precision ≥0.80; chose highest F1",
            "metrics": best
        }

    # Among high-precision candidates, choose highest recall
    best = max(candidates, key=lambda r: r["recall"])

    return {
        "recommended_threshold": best["threshold"],
        "rationale": "Precision ≥0.80, maximized recall",
        "metrics": best
    }


def main():
    parser = argparse.ArgumentParser(description="Tune TRM router confidence thresholds")
    parser.add_argument("--model", type=str, required=True, help="Path to trained TRM router model")
    parser.add_argument("--val-data", type=str, required=True, help="Path to validation JSONL")
    parser.add_argument("--output", type=str, required=True, help="Output path for analysis JSON")
    parser.add_argument("--criterion", type=str, default="f1", choices=["f1", "precision", "recall"],
                        help="Criterion for optimal threshold (default: f1)")

    args = parser.parse_args()

    model_path = Path(args.model)
    val_path = Path(args.val_data)
    output_path = Path(args.output)

    if not val_path.exists():
        print(f"Error: Validation data not found: {val_path}", file=sys.stderr)
        sys.exit(1)

    # Load validation data
    examples, y_true = load_validation_data(val_path)
    y_true = np.array(y_true)

    print(f"Loaded {len(examples)} validation examples")
    print(f"Label distribution: {y_true.sum()} positive, {len(y_true) - y_true.sum()} negative")

    # Get predictions (placeholder: replace with actual router inference)
    print("\n⚠️  Using simulated predictions (replace with actual TRM router inference)")
    y_pred, y_pred_proba = simulate_router_predictions(examples)

    # Evaluate thresholds
    print("\n🔍 Evaluating thresholds from 0.1 to 0.9...")
    thresholds = np.linspace(0.1, 0.9, 41)
    threshold_results = [evaluate_threshold(y_true, y_pred_proba, t) for t in thresholds]

    # Find optimal threshold
    optimal_threshold, optimal_metrics = find_optimal_threshold(y_true, y_pred_proba, args.criterion)
    print(f"\n✅ Optimal threshold (by {args.criterion}): {optimal_threshold:.2f}")
    print(f"   Precision: {optimal_metrics['precision']:.3f}")
    print(f"   Recall: {optimal_metrics['recall']:.3f}")
    print(f"   F1: {optimal_metrics['f1']:.3f}")

    # Compute calibration metrics
    calibration_metrics = compute_calibration_metrics(y_true, y_pred_proba)
    print(f"\n📊 Calibration Metrics:")
    print(f"   Brier score: {calibration_metrics['brier_score']:.4f} (lower is better)")
    print(f"   ROC-AUC: {calibration_metrics['roc_auc']:.3f}")
    print(f"   Expected Calibration Error: {calibration_metrics['expected_calibration_error']:.4f}")

    # Recommend production threshold
    recommendation = recommend_production_threshold(threshold_results)
    print(f"\n💡 Production Recommendation:")
    print(f"   Threshold: {recommendation['recommended_threshold']:.2f}")
    print(f"   Rationale: {recommendation['rationale']}")
    print(f"   Precision: {recommendation['metrics']['precision']:.3f}")
    print(f"   Recall: {recommendation['metrics']['recall']:.3f}")

    # Generate analysis report
    analysis = {
        "model_path": str(model_path),
        "validation_data": str(val_path),
        "validation_size": len(examples),
        "label_distribution": {"positive": int(y_true.sum()), "negative": int(len(y_true) - y_true.sum())},
        "optimal_threshold": {
            "criterion": args.criterion,
            "threshold": optimal_threshold,
            "metrics": optimal_metrics
        },
        "calibration_metrics": calibration_metrics,
        "production_recommendation": recommendation,
        "threshold_sweep": threshold_results
    }

    # Write analysis JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)

    print(f"\n✅ Threshold analysis saved: {output_path}")

    # Generate plots
    plot_dir = output_path.parent
    plot_roc_curve(y_true, y_pred_proba, plot_dir / "roc_curve.png", optimal_threshold)
    plot_calibration_curve(y_true, y_pred_proba, plot_dir / "calibration_curve.png")


if __name__ == "__main__":
    main()
