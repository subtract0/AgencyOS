#!/usr/bin/env python3
"""
Gold Evaluation Set Rotation

Rotates 10 examples from gold set every quarter to track production drift.
Maintains 50 examples total, never mixes into training data.

Usage:
    python scripts/rotate_gold_set.py \
        --gold-set data/gold_eval_50.jsonl \
        --candidate-pool data/seed.dedup.jsonl \
        --rotate-count 10 \
        --strategy disagreement  # or "random", "high_confidence", "low_confidence"

Rotation strategies:
- disagreement: Select from recent shadow mode disagreements
- random: Random sampling from candidate pool
- high_confidence: High-confidence examples (>0.9) for stability check
- low_confidence: Low-confidence examples (<0.6) for edge case coverage
"""
import sys
import json
import argparse
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_gold_set(gold_path: Path) -> List[dict]:
    """Load current gold evaluation set."""
    examples = []
    with open(gold_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def select_rotation_candidates(
    candidate_pool: List[dict],
    count: int,
    strategy: str = "disagreement"
) -> List[dict]:
    """
    Select candidates for rotation based on strategy.

    Args:
        candidate_pool: List of candidate examples
        count: Number to select
        strategy: Selection strategy

    Returns:
        List of selected candidates
    """
    if strategy == "random":
        return random.sample(candidate_pool, min(count, len(candidate_pool)))

    elif strategy == "disagreement":
        # Prioritize recent disagreements (if available)
        disagreements = [ex for ex in candidate_pool if ex.get("source") == "disagreement"]
        if len(disagreements) >= count:
            return random.sample(disagreements, count)
        else:
            # Fill remaining with random
            remaining = count - len(disagreements)
            non_disagreements = [ex for ex in candidate_pool if ex.get("source") != "disagreement"]
            return disagreements + random.sample(non_disagreements, min(remaining, len(non_disagreements)))

    elif strategy == "high_confidence":
        # Select high-confidence examples (>0.9)
        high_conf = [ex for ex in candidate_pool if ex.get("confidence", 0.5) > 0.9]
        return random.sample(high_conf, min(count, len(high_conf)))

    elif strategy == "low_confidence":
        # Select low-confidence examples (<0.6)
        low_conf = [ex for ex in candidate_pool if ex.get("confidence", 0.5) < 0.6]
        return random.sample(low_conf, min(count, len(low_conf)))

    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def rotate_gold_set(
    gold_set: List[dict],
    rotate_out_count: int,
    new_candidates: List[dict]
) -> tuple[List[dict], List[dict]]:
    """
    Rotate examples out of gold set and replace with new candidates.

    Args:
        gold_set: Current gold set
        rotate_out_count: Number of examples to rotate out
        new_candidates: New candidates to rotate in

    Returns:
        (updated_gold_set, rotated_out_examples)
    """
    # Randomly select examples to rotate out
    rotate_out = random.sample(gold_set, min(rotate_out_count, len(gold_set)))
    remaining = [ex for ex in gold_set if ex not in rotate_out]

    # Add new candidates
    updated = remaining + new_candidates[:rotate_out_count]

    # Add rotation metadata
    today = datetime.now().isoformat()
    for ex in updated:
        if ex in new_candidates:
            ex["_gold_rotation"] = {
                "added": today,
                "rotation_number": ex.get("_gold_rotation", {}).get("rotation_number", 0) + 1
            }

    return updated, rotate_out


def archive_rotated_examples(rotated_out: List[dict], archive_path: Path):
    """Archive rotated-out examples for historical analysis."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    # Append to archive
    with open(archive_path, 'a', encoding='utf-8') as f:
        for ex in rotated_out:
            ex["_archived_date"] = datetime.now().isoformat()
            json.dump(ex, f, ensure_ascii=False)
            f.write('\n')

    logger.info(f"Archived {len(rotated_out)} rotated examples to {archive_path}")


def main():
    parser = argparse.ArgumentParser(description="Rotate Gold Evaluation Set")
    parser.add_argument("--gold-set", type=str, required=True, help="Path to current gold set")
    parser.add_argument("--candidate-pool", type=str, required=True, help="Path to candidate pool JSONL")
    parser.add_argument("--rotate-count", type=int, default=10, help="Number of examples to rotate")
    parser.add_argument("--strategy", type=str, default="disagreement",
                        choices=["disagreement", "random", "high_confidence", "low_confidence"],
                        help="Rotation strategy")
    parser.add_argument("--archive", type=str, default="data/gold_set_archive.jsonl",
                        help="Path to archive rotated examples")

    args = parser.parse_args()

    gold_path = Path(args.gold_set)
    candidate_pool_path = Path(args.candidate_pool)
    archive_path = Path(args.archive)

    logger.info("="*70)
    logger.info("GOLD SET ROTATION")
    logger.info("="*70)

    # Load current gold set
    gold_set = load_gold_set(gold_path)
    logger.info(f"Current gold set: {len(gold_set)} examples")

    # Load candidate pool
    candidate_pool = []
    with open(candidate_pool_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                candidate_pool.append(json.loads(line))
    logger.info(f"Candidate pool: {len(candidate_pool)} examples")

    # Select rotation candidates
    new_candidates = select_rotation_candidates(candidate_pool, args.rotate_count, args.strategy)
    logger.info(f"Selected {len(new_candidates)} candidates ({args.strategy} strategy)")

    # Rotate gold set
    updated_gold, rotated_out = rotate_gold_set(gold_set, args.rotate_count, new_candidates)
    logger.info(f"Rotated {len(rotated_out)} examples out, {len(new_candidates)} in")

    # Archive rotated examples
    archive_rotated_examples(rotated_out, archive_path)

    # Write updated gold set
    backup_path = gold_path.with_suffix('.backup.jsonl')
    gold_path.rename(backup_path)
    logger.info(f"Backed up gold set to {backup_path}")

    with open(gold_path, 'w', encoding='utf-8') as f:
        for ex in updated_gold:
            json.dump(ex, f, ensure_ascii=False)
            f.write('\n')

    logger.info(f"✅ Gold set updated: {gold_path}")
    logger.info(f"   Total examples: {len(updated_gold)}")
    logger.info(f"   Rotation strategy: {args.strategy}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
