#!/usr/bin/env python3
"""
Format training_examples_final.jsonl for Esper3.1 QLoRA fine-tuning.

Input: data/training_examples_final.jsonl
Output: data/esper31_training_formatted.jsonl

Format: OpenAI messages format for instruction fine-tuning
"""
import json
from pathlib import Path

SYSTEM_PROMPT = """You are Esper3.1, a coding, architecture, and DevOps reasoning specialist.

You excel at:
- Complex algorithm design and optimization
- Graph algorithms and data structures
- Constraint satisfaction problems
- Recursive problem solving
- System architecture and design patterns

Provide clear, well-reasoned solutions with step-by-step explanations."""

def format_example(example: dict) -> dict:
    """
    Format example for instruction fine-tuning.

    Input example:
    {
        "instruction": "Find shortest path...",
        "input": "Graph: A-B:3, B-C:2, A-C:8",
        "output": "Path: A→B→C, Distance: 5"
    }

    Output:
    {
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """
    instruction = example.get("instruction", "")
    input_data = example.get("input", "")
    output = example.get("output", "")

    # Combine instruction + input for user message
    if input_data:
        user_content = f"{instruction}\n\nInput: {input_data}"
    else:
        user_content = instruction

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output}
        ]
    }

def main():
    input_path = Path("data/training_examples_final.jsonl")
    output_path = Path("data/esper31_training_formatted.jsonl")

    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        return

    print("=" * 70)
    print("FORMATTING DATA FOR ESPER3.1 TRAINING")
    print("=" * 70)

    # Load examples
    examples = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"\n✅ Loaded {len(examples)} examples")

    # Format
    formatted = [format_example(ex) for ex in examples]

    # Write
    with open(output_path, 'w') as f:
        for ex in formatted:
            json.dump(ex, f, ensure_ascii=False)
            f.write('\n')

    print(f"✅ Formatted {len(formatted)} examples")
    print(f"✅ Output: {output_path}")

    # Show sample
    print(f"\n📊 Sample (first example):")
    sample = formatted[0]
    print(f"\nSystem: {sample['messages'][0]['content'][:80]}...")
    print(f"\nUser: {sample['messages'][1]['content'][:100]}...")
    print(f"\nAssistant: {sample['messages'][2]['content'][:100]}...")

    print("\n" + "=" * 70)
    print("NEXT STEP:")
    print("=" * 70)
    print("python scripts/train_esper31_qlora.py")
    print(f"  - Dataset: {output_path}")
    print(f"  - Time: ~2-3 hours on M4 Pro")
    print(f"  - Cost: ~$0.02 (electricity)")
    print(f"  - Output: models/esper31-algorithms-qlora/adapters.safetensors")

if __name__ == "__main__":
    main()
