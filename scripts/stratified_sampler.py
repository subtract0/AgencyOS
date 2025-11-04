#!/usr/bin/env python3
"""
Stratified sampling for maximum diversity + difficulty in training data.

Unlike simple top-N by keyword score, this ensures representation across:
- Task types (graph, SAT, scheduling, regex, etc.)
- Instruction length (short, medium, long)
- Keyword density (multiple keywords vs single keyword)

Usage:
    python scripts/stratified_sampler.py data/seed.dedup.jsonl data/sample_300.jsonl 300

Outputs:
    - data/sample_300.jsonl: Stratified sample
    - data/sampling_report.json: Distribution analysis
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import random


# Reasoning keywords (from GPT-5's list + additions)
REASONING_KEYWORDS = [
    "graph", "dag", "csp", "sat", "knapsack", "schedule", "invariant",
    "recurs", "prove", "edge", "dependency", "constraint", "shortest",
    "optimal", "induct", "contradiction", "cycle", "path", "tree",
    "heap", "sort", "search", "dynamic programming", "greedy",
    "backtrack", "branch and bound", "nondeterministic", "np-complete"
]


def classify_task_type(obj: dict) -> str:
    """
    Classify task into primary type based on keywords.

    Types: graph, constraint, optimization, proof, algorithm, regex, other
    """
    instruction = (obj.get("instruction") or obj.get("prompt") or "").lower()

    if any(kw in instruction for kw in ["graph", "dag", "tree", "node", "edge", "cycle"]):
        return "graph"
    elif any(kw in instruction for kw in ["sat", "csp", "constraint", "satisf"]):
        return "constraint"
    elif any(kw in instruction for kw in ["optim", "minim", "maxim", "knapsack", "schedule"]):
        return "optimization"
    elif any(kw in instruction for kw in ["prove", "induct", "invariant", "contradiction"]):
        return "proof"
    elif any(kw in instruction for kw in ["algorithm", "complex", "sort", "search", "dynamic"]):
        return "algorithm"
    elif any(kw in instruction for kw in ["regex", "pattern", "match", "parse"]):
        return "regex"
    else:
        return "other"


def compute_complexity_score(obj: dict) -> float:
    """
    Multi-dimensional complexity score for prioritization.

    Factors:
    - Instruction length (longer = more complex)
    - Keyword count (multiple reasoning keywords = higher complexity)
    - Rare task types (less common = prioritize for diversity)
    """
    instruction = (obj.get("instruction") or obj.get("prompt") or "").lower()

    # Length score (normalized to 0-1 range, cap at 200 words)
    word_count = len(instruction.split())
    length_score = min(word_count / 200.0, 1.0)

    # Keyword count (bonus for multiple reasoning keywords)
    keyword_count = sum(1 for kw in REASONING_KEYWORDS if kw in instruction)
    keyword_score = min(keyword_count / 5.0, 1.0)  # Cap at 5 keywords

    # Composite score
    return (length_score * 0.4) + (keyword_score * 0.6)


def stratified_sample(
    objects: List[dict],
    target_count: int,
    strata_proportions: Dict[str, float] = None
) -> Tuple[List[dict], Dict]:
    """
    Perform stratified sampling across task types and complexity levels.

    Args:
        objects: List of JSON objects to sample from
        target_count: Total number of samples to select
        strata_proportions: Optional dict of task_type -> proportion (defaults to equal representation)

    Returns:
        (sampled_objects, sampling_report)
    """
    # Classify all objects by task type
    strata: Dict[str, List[Tuple[float, dict]]] = defaultdict(list)

    for obj in objects:
        task_type = classify_task_type(obj)
        complexity = compute_complexity_score(obj)
        strata[task_type].append((complexity, obj))

    # Sort each stratum by complexity (descending)
    for task_type in strata:
        strata[task_type].sort(reverse=True, key=lambda x: x[0])

    # Determine sampling proportions
    if strata_proportions is None:
        # Equal representation across all task types
        num_types = len(strata)
        strata_proportions = {task_type: 1.0 / num_types for task_type in strata}

    # Calculate samples per stratum
    samples_per_stratum = {
        task_type: max(1, int(target_count * proportion))
        for task_type, proportion in strata_proportions.items()
    }

    # Adjust for rounding errors (ensure total = target_count)
    total_allocated = sum(samples_per_stratum.values())
    if total_allocated < target_count:
        # Add remaining samples to largest stratum
        largest_stratum = max(strata.keys(), key=lambda t: len(strata[t]))
        samples_per_stratum[largest_stratum] += (target_count - total_allocated)
    elif total_allocated > target_count:
        # Remove excess from largest stratum
        largest_stratum = max(strata.keys(), key=lambda t: len(strata[t]))
        samples_per_stratum[largest_stratum] -= (total_allocated - target_count)

    # Sample from each stratum (top-N by complexity within each type)
    sampled = []
    sampling_details = {}

    for task_type, count in samples_per_stratum.items():
        available = strata[task_type]
        selected = available[:count]  # Top-N by complexity

        sampled.extend([obj for _, obj in selected])

        sampling_details[task_type] = {
            "available": len(available),
            "sampled": len(selected),
            "avg_complexity": sum(c for c, _ in selected) / len(selected) if selected else 0.0
        }

    # Shuffle to avoid task-type clustering
    random.shuffle(sampled)

    # Generate sampling report
    sampling_report = {
        "target_count": target_count,
        "actual_count": len(sampled),
        "strata_details": sampling_details,
        "keyword_coverage": compute_keyword_coverage(sampled),
        "length_distribution": compute_length_distribution(sampled)
    }

    return sampled, sampling_report


def compute_keyword_coverage(objects: List[dict]) -> Dict[str, int]:
    """Count how many samples contain each reasoning keyword."""
    coverage = {kw: 0 for kw in REASONING_KEYWORDS}

    for obj in objects:
        instruction = (obj.get("instruction") or obj.get("prompt") or "").lower()
        for kw in REASONING_KEYWORDS:
            if kw in instruction:
                coverage[kw] += 1

    return coverage


def compute_length_distribution(objects: List[dict]) -> Dict[str, int]:
    """Bin samples by instruction length."""
    bins = {"short (<50 words)": 0, "medium (50-150 words)": 0, "long (>150 words)": 0}

    for obj in objects:
        instruction = obj.get("instruction") or obj.get("prompt") or ""
        word_count = len(instruction.split())

        if word_count < 50:
            bins["short (<50 words)"] += 1
        elif word_count <= 150:
            bins["medium (50-150 words)"] += 1
        else:
            bins["long (>150 words)"] += 1

    return bins


def main():
    if len(sys.argv) < 4:
        print("Usage: python stratified_sampler.py seed.jsonl output.jsonl target_count")
        sys.exit(2)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    target_count = int(sys.argv[3])

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load objects
    objects = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                objects.append(json.loads(line))

    print(f"Loaded {len(objects)} objects from {input_path}")

    # Perform stratified sampling
    sampled, report = stratified_sample(objects, target_count)

    # Write sampled objects
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for obj in sampled:
            json.dump(obj, f, ensure_ascii=False)
            f.write('\n')

    # Write sampling report
    report_path = output_path.parent / "sampling_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Stratified sampling complete:")
    print(f"   Input: {len(objects)} objects")
    print(f"   Sampled: {len(sampled)} objects")
    print(f"   Report: {report_path}")
    print(f"\n📊 Task Type Distribution:")
    for task_type, details in report["strata_details"].items():
        print(f"   {task_type}: {details['sampled']} samples (avg complexity: {details['avg_complexity']:.2f})")

    print(f"\n📏 Length Distribution:")
    for bin_name, count in report["length_distribution"].items():
        print(f"   {bin_name}: {count}")


if __name__ == "__main__":
    main()
