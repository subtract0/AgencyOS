#!/usr/bin/env python3
"""
Automated TRM Router Retraining Loop

Runs every 2 weeks via cron to:
1. Collect disagreement logs from shadow mode
2. Deduplicate and stratify new samples
3. Re-tune thresholds
4. Fine-tune LoRA weights
5. Redeploy with updated calibration

Usage:
    python scripts/auto_retrain_loop.py \
        --disagreements logs/shadow_mode/disagreements.jsonl \
        --output models/trm_router_lora_retrain_$(date +%Y%m%d) \
        --sample-count 150

Environment:
    RETRAIN_MIN_DISAGREEMENTS=100  # Minimum disagreements to trigger retraining
    RETRAIN_MAX_AGE_DAYS=14        # Maximum age of disagreements to include
"""
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def collect_disagreements(
    logs_path: Path,
    max_age_days: int = 14
) -> Tuple[List[dict], int]:
    """
    Collect disagreement examples from shadow mode logs.

    Args:
        logs_path: Path to disagreements.jsonl
        max_age_days: Maximum age of disagreements to include

    Returns:
        (disagreements, skipped_count)
    """
    if not logs_path.exists():
        logger.warning(f"Disagreements log not found: {logs_path}")
        return [], 0

    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    disagreements = []
    skipped = 0

    with open(logs_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            obj = json.loads(line)
            timestamp = datetime.fromisoformat(obj.get("timestamp", "2000-01-01T00:00:00Z").replace('Z', '+00:00'))

            if timestamp < cutoff_date:
                skipped += 1
                continue

            disagreements.append(obj)

    logger.info(f"Collected {len(disagreements)} disagreements (skipped {skipped} older than {max_age_days} days)")
    return disagreements, skipped


def prepare_retraining_data(
    disagreements: List[dict],
    existing_train: Path,
    output_path: Path,
    sample_count: int = 150
) -> Path:
    """
    Prepare retraining dataset from disagreements + existing training data.

    Args:
        disagreements: List of disagreement examples
        existing_train: Path to existing training JSONL
        output_path: Output path for combined dataset
        sample_count: Number of disagreements to sample

    Returns:
        Path to prepared dataset
    """
    # Convert disagreements to training format
    training_examples = []
    for disagreement in disagreements:
        example = {
            "instruction": disagreement.get("instruction", ""),
            "input": disagreement.get("input", ""),
            "label": disagreement.get("production_label"),  # Use production label as ground truth
            "source": "disagreement",
            "confidence": disagreement.get("trm_router_confidence"),
            "timestamp": disagreement.get("timestamp")
        }
        training_examples.append(example)

    logger.info(f"Converted {len(training_examples)} disagreements to training format")

    # Sample disagreements using stratified sampler
    disagreements_path = output_path.parent / "disagreements_temp.jsonl"
    with open(disagreements_path, 'w', encoding='utf-8') as f:
        for ex in training_examples:
            json.dump(ex, f, ensure_ascii=False)
            f.write('\n')

    # Deduplicate
    deduped_path = output_path.parent / "disagreements_dedup.jsonl"
    subprocess.run([
        "python", "scripts/dedupe_and_provenance.py",
        str(disagreements_path),
        str(deduped_path)
    ], check=True)

    # Stratified sampling
    sampled_path = output_path.parent / "disagreements_sampled.jsonl"
    subprocess.run([
        "python", "scripts/stratified_sampler.py",
        str(deduped_path),
        str(sampled_path),
        str(min(sample_count, len(training_examples)))
    ], check=True)

    # Merge with existing training data
    combined = []

    # Load existing training data
    if existing_train.exists():
        with open(existing_train, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    combined.append(json.loads(line))

    # Load sampled disagreements
    with open(sampled_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                combined.append(json.loads(line))

    # Write combined dataset
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for ex in combined:
            json.dump(ex, f, ensure_ascii=False)
            f.write('\n')

    logger.info(f"Combined dataset: {len(combined)} examples ({len(combined) - len(training_examples)} existing + {len(training_examples)} new)")

    # Cleanup temp files
    disagreements_path.unlink(missing_ok=True)
    deduped_path.unlink(missing_ok=True)
    sampled_path.unlink(missing_ok=True)

    return output_path


def retrain_model(
    data_path: Path,
    base_model: str,
    output_path: Path,
    prev_checkpoint: Path = None
) -> Path:
    """
    Fine-tune LoRA adapter on updated dataset.

    Args:
        data_path: Path to training JSONL
        base_model: Base model name (e.g., "qwen3coder-30b")
        output_path: Output directory for new checkpoint
        prev_checkpoint: Path to previous checkpoint (for incremental fine-tuning)

    Returns:
        Path to new checkpoint
    """
    cmd = [
        "python", "scripts/train_router.py",
        "--model", base_model,
        "--data", str(data_path),
        "--output", str(output_path),
        "--lora-rank", "8",
        "--lora-alpha", "16",
        "--batch-size", "4",
        "--epochs", "3",
        "--learning-rate", "2e-4",
        "--k-fold", "5",
        "--early-stopping", "patience=3",
        "--oom-guard"
    ]

    if prev_checkpoint and prev_checkpoint.exists():
        cmd.extend(["--init-from", str(prev_checkpoint)])
        logger.info(f"Incremental fine-tuning from {prev_checkpoint}")

    logger.info(f"Starting retraining: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    return output_path


def recalibrate_thresholds(
    checkpoint_path: Path,
    val_data: Path,
    output_path: Path
) -> Dict:
    """
    Re-tune confidence thresholds on validation set.

    Args:
        checkpoint_path: Path to model checkpoint
        val_data: Path to validation JSONL
        output_path: Output path for threshold analysis

    Returns:
        Dict of calibration metrics
    """
    cmd = [
        "python", "scripts/tune_thresholds.py",
        "--model", str(checkpoint_path),
        "--val-data", str(val_data),
        "--output", str(output_path),
        "--criterion", "f1"
    ]

    logger.info(f"Recalibrating thresholds: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Load results
    with open(output_path, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    return analysis


def log_lineage(
    output_path: Path,
    metrics: Dict,
    sample_count: int,
    disagreement_count: int
):
    """
    Append retraining record to changelog.

    Args:
        output_path: Path to model checkpoint
        metrics: Calibration metrics
        sample_count: Number of samples added
        disagreement_count: Number of disagreements collected
    """
    changelog_path = Path("missions/TRM_ROUTER_CHANGELOG.md")

    # Extract key metrics
    roc_auc = metrics.get("calibration_metrics", {}).get("roc_auc", 0.0)
    ece = metrics.get("calibration_metrics", {}).get("expected_calibration_error", 0.0)
    threshold = metrics.get("production_recommendation", {}).get("recommended_threshold", 0.75)

    # Format entry
    today = datetime.now().strftime("%Y-%m-%d")
    checkpoint_name = output_path.name
    entry = f"[{today}] {checkpoint_name} → +{sample_count} samples ({disagreement_count} disagreements)\n"
    entry += f"ROC-AUC {roc_auc:.4f}, ECE {ece:.4f}, threshold = {threshold:.2f}\n\n"

    # Append to changelog
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    with open(changelog_path, 'a', encoding='utf-8') as f:
        f.write(entry)

    logger.info(f"Logged lineage to {changelog_path}")


def main():
    parser = argparse.ArgumentParser(description="Automated TRM Router Retraining Loop")
    parser.add_argument("--disagreements", type=str, required=True, help="Path to disagreements.jsonl")
    parser.add_argument("--output", type=str, required=True, help="Output directory for new checkpoint")
    parser.add_argument("--sample-count", type=int, default=150, help="Number of disagreements to sample")
    parser.add_argument("--base-model", type=str, default="qwen3coder-30b", help="Base model name")
    parser.add_argument("--existing-train", type=str, default="learning/trm_labels_train.jsonl", help="Existing training data")
    parser.add_argument("--val-data", type=str, default="learning/trm_labels_val.jsonl", help="Validation data")
    parser.add_argument("--prev-checkpoint", type=str, help="Previous checkpoint for incremental fine-tuning")
    parser.add_argument("--min-disagreements", type=int, default=100, help="Minimum disagreements to trigger retraining")
    parser.add_argument("--max-age-days", type=int, default=14, help="Maximum age of disagreements to include")

    args = parser.parse_args()

    disagreements_path = Path(args.disagreements)
    output_path = Path(args.output)
    existing_train = Path(args.existing_train)
    val_data = Path(args.val_data)
    prev_checkpoint = Path(args.prev_checkpoint) if args.prev_checkpoint else None

    logger.info("="*70)
    logger.info("TRM ROUTER AUTOMATED RETRAINING LOOP")
    logger.info("="*70)

    # Step 1: Collect disagreements
    disagreements, skipped = collect_disagreements(disagreements_path, args.max_age_days)

    if len(disagreements) < args.min_disagreements:
        logger.warning(f"Insufficient disagreements ({len(disagreements)} < {args.min_disagreements})")
        logger.info("Retraining skipped. Try again later.")
        sys.exit(0)

    # Step 2: Prepare retraining dataset
    combined_data = output_path.parent / "retrain_combined.jsonl"
    prepare_retraining_data(disagreements, existing_train, combined_data, args.sample_count)

    # Step 3: Retrain model
    retrain_model(combined_data, args.base_model, output_path, prev_checkpoint)

    # Step 4: Recalibrate thresholds
    threshold_analysis = output_path / "threshold_analysis.json"
    metrics = recalibrate_thresholds(output_path, val_data, threshold_analysis)

    # Step 5: Log lineage
    log_lineage(output_path, metrics, args.sample_count, len(disagreements))

    logger.info("="*70)
    logger.info("RETRAINING COMPLETE")
    logger.info(f"New checkpoint: {output_path}")
    logger.info(f"ROC-AUC: {metrics.get('calibration_metrics', {}).get('roc_auc', 0.0):.4f}")
    logger.info(f"ECE: {metrics.get('calibration_metrics', {}).get('expected_calibration_error', 0.0):.4f}")
    logger.info(f"Recommended threshold: {metrics.get('production_recommendation', {}).get('recommended_threshold', 0.75):.2f}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
