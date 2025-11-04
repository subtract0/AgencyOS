#!/usr/bin/env python3
"""
Test Esper3.1 QLoRA adapters directly (without exporting to Ollama).

Usage:
    python scripts/test_esper31_adapters.py

Tests a few algorithm problems to verify adapters work and show improvement.
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from pathlib import Path


def load_models():
    """Load base model and model with adapters."""
    model_name = "ValiantLabs/gpt-oss-20b-Esper3.1"
    adapter_path = "models/esper31-algorithms-qlora"

    print("=" * 70)
    print("LOADING MODELS")
    print("=" * 70)

    # Check if adapters exist
    if not Path(adapter_path).exists():
        print(f"\n❌ ERROR: Adapters not found at {adapter_path}")
        print(f"Run training first: python scripts/train_esper31_qlora.py")
        return None, None, None

    # Load tokenizer
    print(f"\n📝 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model
    print(f"📦 Loading base model (this may take a few minutes)...")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map={"": device},
        trust_remote_code=True
    )

    # Load adapters
    print(f"🔧 Loading adapters from {adapter_path}...")
    model_with_adapters = PeftModel.from_pretrained(base_model, adapter_path)

    print(f"✅ Models loaded on device: {device}\n")
    return base_model, model_with_adapters, tokenizer


def generate_response(model, tokenizer, prompt: str, max_length: int = 512) -> str:
    """Generate response from model."""
    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)

    # Move to same device as model
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove the prompt from response
    response = response[len(prompt):].strip()
    return response


def run_tests(base_model, model_with_adapters, tokenizer):
    """Run test cases."""
    test_cases = [
        {
            "name": "Shortest Path",
            "prompt": "Find the shortest path from A to C in this graph: A-B:3, B-C:2, A-C:8. Explain your reasoning.",
        },
        {
            "name": "Cycle Detection",
            "prompt": "Detect if there's a cycle in this directed graph: A->B, B->C, C->A. Explain your reasoning.",
        },
        {
            "name": "Topological Sort",
            "prompt": "Perform topological sort on this graph: A->B, A->C, B->D, C->D. Explain your reasoning.",
        },
    ]

    print("=" * 70)
    print("TESTING ADAPTERS")
    print("=" * 70)

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'─' * 70}")
        print(f"Prompt: {test['prompt']}\n")

        # Base model
        print("🔵 BASE MODEL:")
        base_response = generate_response(base_model, tokenizer, test["prompt"])
        print(base_response[:300] + "..." if len(base_response) > 300 else base_response)

        print(f"\n🟢 WITH ADAPTERS:")
        adapter_response = generate_response(model_with_adapters, tokenizer, test["prompt"])
        print(adapter_response[:300] + "..." if len(adapter_response) > 300 else adapter_response)

    print(f"\n{'=' * 70}")
    print("TESTING COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review responses above - do adapters show improvement?")
    print("2. If yes, export to Ollama: python scripts/export_to_ollama.py")
    print("3. Run full benchmark: python scripts/benchmark_esper31.py --with-adapters --compare-to-baseline")


def main():
    base_model, model_with_adapters, tokenizer = load_models()

    if base_model is None:
        return

    run_tests(base_model, model_with_adapters, tokenizer)


if __name__ == "__main__":
    main()
