#!/usr/bin/env python3
"""
TRM Router Calibration Monitoring Dashboard

Generates real-time calibration metrics and alerts for drift detection.

Usage:
    python scripts/calibration_dashboard.py \
        --model models/trm_router_lora \
        --gold-set data/gold_eval_50.jsonl \
        --output logs/calibration/dashboard.html \
        --alert-thresholds "roc_auc<0.9,ece>0.05,brier>0.12"

Monitors:
- ROC-AUC (target > 0.9)
- Brier score (target < 0.12)
- Expected Calibration Error (ECE, target < 0.05)
- Confidence histogram
- Calibration curve
- Disagreement rate over time
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
import numpy as np
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.calibration import calibration_curve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_gold_set(gold_path: Path) -> Tuple[List[dict], np.ndarray]:
    """Load gold set and extract labels."""
    examples = []
    labels = []

    with open(gold_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                examples.append(obj)
                labels.append(obj.get("label", 0))

    return examples, np.array(labels)


def simulate_predictions(examples: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate router predictions (replace with actual model inference).

    TODO: Replace with actual TRM router inference.
    """
    np.random.seed(42)
    n = len(examples)
    confidences = np.random.rand(n)
    predictions = (confidences > 0.5).astype(int)
    return predictions, confidences


def compute_calibration_metrics(y_true: np.ndarray, y_pred_proba: np.ndarray) -> Dict:
    """Compute all calibration metrics."""
    roc_auc = roc_auc_score(y_true, y_pred_proba)
    brier = brier_score_loss(y_true, y_pred_proba)

    # Calibration curve
    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_true, y_pred_proba, n_bins=10, strategy='uniform'
    )

    # Expected Calibration Error (ECE)
    bin_counts = np.histogram(y_pred_proba, bins=10, range=(0, 1))[0]
    bin_weights = bin_counts / len(y_pred_proba)
    ece = np.sum(bin_weights * np.abs(mean_predicted_value - fraction_of_positives))

    return {
        "roc_auc": roc_auc,
        "brier_score": brier,
        "ece": ece,
        "calibration_curve": {
            "mean_predicted": mean_predicted_value.tolist(),
            "fraction_positive": fraction_of_positives.tolist()
        }
    }


def check_alert_thresholds(metrics: Dict, thresholds: Dict) -> List[str]:
    """Check if any metrics violate alert thresholds."""
    alerts = []

    if "roc_auc" in thresholds and metrics["roc_auc"] < thresholds["roc_auc"]:
        alerts.append(f"⚠️ ROC-AUC below threshold: {metrics['roc_auc']:.4f} < {thresholds['roc_auc']}")

    if "ece" in thresholds and metrics["ece"] > thresholds["ece"]:
        alerts.append(f"⚠️ ECE above threshold: {metrics['ece']:.4f} > {thresholds['ece']}")

    if "brier_score" in thresholds and metrics["brier_score"] > thresholds["brier_score"]:
        alerts.append(f"⚠️ Brier score above threshold: {metrics['brier_score']:.4f} > {thresholds['brier_score']}")

    return alerts


def generate_html_dashboard(
    metrics: Dict,
    alerts: List[str],
    timestamp: str,
    output_path: Path
):
    """Generate HTML dashboard with calibration metrics."""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>TRM Router Calibration Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: #f9f9f9; border-radius: 4px; }}
        .metric-name {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .metric.good {{ background: #d4edda; border-left: 4px solid #28a745; }}
        .metric.warn {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
        .metric.bad {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .alerts {{ background: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #ffc107; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>TRM Router Calibration Dashboard</h1>
        <p class="timestamp">Last updated: {timestamp}</p>

        <h2>Key Metrics</h2>
        <div>
            <div class="metric {get_metric_class(metrics["roc_auc"], 0.9, "above")}">
                <div class="metric-name">ROC-AUC</div>
                <div class="metric-value">{metrics["roc_auc"]:.4f}</div>
                <div class="metric-name">Target: > 0.9</div>
            </div>

            <div class="metric {get_metric_class(metrics["brier_score"], 0.12, "below")}">
                <div class="metric-name">Brier Score</div>
                <div class="metric-value">{metrics["brier_score"]:.4f}</div>
                <div class="metric-name">Target: < 0.12</div>
            </div>

            <div class="metric {get_metric_class(metrics["ece"], 0.05, "below")}">
                <div class="metric-name">ECE</div>
                <div class="metric-value">{metrics["ece"]:.4f}</div>
                <div class="metric-name">Target: < 0.05</div>
            </div>
        </div>

        {"<div class='alerts'><h3>🚨 Alerts</h3>" + "<br>".join(alerts) + "</div>" if alerts else ""}

        <h2>Calibration Status</h2>
        <p>{"✅ All metrics within acceptable range" if not alerts else "⚠️ Some metrics require attention"}</p>

        <h2>Next Steps</h2>
        <ul>
            {"<li>✅ No action required - calibration is healthy</li>" if not alerts else
             "<li>⚠️ Review threshold analysis: scripts/tune_thresholds.py</li><li>Consider retraining if drift persists >2 weeks</li>"}
        </ul>
    </div>
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    logger.info(f"✅ Dashboard generated: {output_path}")


def get_metric_class(value: float, threshold: float, direction: str) -> str:
    """Determine CSS class based on metric value vs threshold."""
    if direction == "above":
        if value >= threshold:
            return "good"
        elif value >= threshold * 0.95:
            return "warn"
        else:
            return "bad"
    else:  # below
        if value <= threshold:
            return "good"
        elif value <= threshold * 1.05:
            return "warn"
        else:
            return "bad"


def main():
    parser = argparse.ArgumentParser(description="TRM Router Calibration Dashboard")
    parser.add_argument("--model", type=str, required=True, help="Path to TRM router model")
    parser.add_argument("--gold-set", type=str, required=True, help="Path to gold evaluation set")
    parser.add_argument("--output", type=str, required=True, help="Output path for HTML dashboard")
    parser.add_argument("--alert-thresholds", type=str, default="roc_auc<0.9,ece>0.05,brier>0.12",
                        help="Alert thresholds (e.g., roc_auc<0.9,ece>0.05)")

    args = parser.parse_args()

    model_path = Path(args.model)
    gold_path = Path(args.gold_set)
    output_path = Path(args.output)

    # Parse thresholds
    thresholds = {}
    for threshold in args.alert_thresholds.split(','):
        metric, condition = threshold.split('<' if '<' in threshold else '>')
        thresholds[metric.strip()] = float(condition.strip())

    logger.info("="*70)
    logger.info("TRM ROUTER CALIBRATION DASHBOARD")
    logger.info("="*70)

    # Load gold set
    examples, y_true = load_gold_set(gold_path)
    logger.info(f"Loaded {len(examples)} gold evaluation examples")

    # Get predictions (replace with actual model inference)
    y_pred, y_pred_proba = simulate_predictions(examples)

    # Compute calibration metrics
    metrics = compute_calibration_metrics(y_true, y_pred_proba)
    logger.info(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"Brier Score: {metrics['brier_score']:.4f}")
    logger.info(f"ECE: {metrics['ece']:.4f}")

    # Check alert thresholds
    alerts = check_alert_thresholds(metrics, thresholds)
    if alerts:
        logger.warning(f"Found {len(alerts)} alert(s):")
        for alert in alerts:
            logger.warning(f"  {alert}")
    else:
        logger.info("✅ All metrics within acceptable range")

    # Generate HTML dashboard
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    generate_html_dashboard(metrics, alerts, timestamp, output_path)

    # Write JSON metrics for programmatic access
    json_output = output_path.with_suffix('.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "metrics": metrics,
            "alerts": alerts,
            "thresholds": thresholds
        }, f, indent=2)

    logger.info(f"✅ JSON metrics: {json_output}")
    logger.info("="*70)

    # Exit with error code if alerts present (for CI/CD)
    if alerts:
        sys.exit(1)


if __name__ == "__main__":
    main()
