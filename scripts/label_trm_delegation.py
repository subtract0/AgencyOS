#!/usr/bin/env python3
"""
Label existing 1,102 examples with use_trm and trm_translation fields.
Uses GPT-5 for automatic labeling.

Cost: ~$1.50 for 1,102 examples

Usage:
    python scripts/label_trm_delegation.py
"""
import json
import os
from pathlib import Path
from openai import OpenAI

LABELING_PROMPT = """
You are an expert at classifying coding/reasoning tasks.

Classify if this task requires:
- **TRM (use_trm=1)**: Recursive reasoning, optimization, graph problems, constraint satisfaction, complex algorithms
- **Esper3.1 Solo (use_trm=0)**: Straightforward coding, DevOps, architecture (no heavy recursion or optimization)

For use_trm=1 cases, also provide a TRM translation:
{
  "task_type": "GRAPH|CSP|OPTIMIZATION|RECURSION|ARC_AGI",
  "input": "<canonical format for TRM - grid-based if possible>",
  "max_iterations": <int 1-16, higher for complex tasks>,
  "expected_output": "<structured output format>"
}

Task:
Instruction: {instruction}
Input: {input}
Output: {output}

Respond in JSON:
{
  "use_trm": 0 or 1,
  "reasoning": "<why this decision>",
  "trm_translation": {<translation if use_trm=1>} or null
}
"""

def label_example(example: dict, client: OpenAI) -> dict:
    """Label a single example with GPT-5."""
    prompt = LABELING_PROMPT.format(
        instruction=example.get("instruction", ""),
        input=example.get("input", ""),
        output=example.get("output", "")
    )

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a task classification expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        label = json.loads(response.choices[0].message.content)

        return {
            **example,
            "use_trm": label["use_trm"],
            "trm_translation": label.get("trm_translation"),
            "_labeling_reasoning": label.get("reasoning")
        }
    except Exception as e:
        print(f"   Error labeling example: {e}")
        # Default to use_trm=0 on error (conservative)
        return {
            **example,
            "use_trm": 0,
            "trm_translation": None,
            "_labeling_reasoning": f"Error: {e}"
        }

def main():
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Paths
    input_path = Path("data/training_examples_final.jsonl")
    output_path = Path("data/trm_delegation_labeled.jsonl")

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Load existing data
    print("=" * 70)
    print("TRM DELEGATION LABELING")
    print("=" * 70)

    examples = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"\n✅ Loaded {len(examples)} examples from {input_path}")

    # Estimate cost
    avg_tokens_per_example = 300  # Instruction + input + output + response
    total_tokens = len(examples) * avg_tokens_per_example
    cost_estimate = (total_tokens / 1_000_000) * 4.0  # GPT-5 $4/1M tokens

    print(f"\n💰 Cost Estimation:")
    print(f"   Examples: {len(examples)}")
    print(f"   Avg tokens/example: {avg_tokens_per_example}")
    print(f"   Total tokens: ~{total_tokens:,}")
    print(f"   Estimated cost: ${cost_estimate:.2f}")

    # Confirm
    response = input(f"\nProceed with labeling? [y/N]: ")
    if response.lower() != 'y':
        print("❌ Aborted by user")
        sys.exit(0)

    # Label examples
    print(f"\n🏷️  Labeling {len(examples)} examples with GPT-5...")

    labeled = []
    for i, example in enumerate(examples):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(examples)} ({i/len(examples)*100:.1f}%)")

        labeled_example = label_example(example, client)
        labeled.append(labeled_example)

    # Write labeled data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for example in labeled:
            json.dump(example, f, ensure_ascii=False)
            f.write('\n')

    # Stats
    trm_count = sum(1 for ex in labeled if ex["use_trm"] == 1)
    solo_count = len(labeled) - trm_count

    print(f"\n✅ Labeling complete!")
    print(f"   Total: {len(labeled)}")
    print(f"   use_trm=1 (TRM): {trm_count} ({trm_count/len(labeled)*100:.1f}%)")
    print(f"   use_trm=0 (Solo): {solo_count} ({solo_count/len(labeled)*100:.1f}%)")
    print(f"   Output: {output_path}")

    # Show sample labels
    print(f"\n📊 Sample Labels:")
    for i in range(min(3, len(labeled))):
        ex = labeled[i]
        print(f"\n  Example {i + 1}:")
        print(f"    Instruction: {ex['instruction'][:60]}...")
        print(f"    use_trm: {ex['use_trm']}")
        print(f"    Reasoning: {ex.get('_labeling_reasoning', 'N/A')[:80]}...")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print(f"1. Review labeled data: head -3 {output_path} | python3 -m json.tool")
    print(f"2. If distribution is good (30-70% TRM), proceed to Phase 2 (fine-tuning)")
    print(f"3. If imbalanced (>80% TRM), run scripts/generate_simple_examples.py")

if __name__ == "__main__":
    import sys
    main()
