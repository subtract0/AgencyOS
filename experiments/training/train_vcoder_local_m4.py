
import argparse
import sys
import os
from pathlib import Path

# Ensure we can import mlx
try:
    import mlx.core as mx
    from mlx_lm import load, lora
except ImportError:
    print("❌ mlx-lm not installed. Run: pip install mlx-lm")
    sys.exit(1)

def run_training(
    model_path: str,
    data_path: str,
    adapter_path: str,
    iters: int = 100,
    batch_size: int = 4
):
    """
    Run LoRA fine-tuning on M4 Max using MLX.
    """
    print(f"🚀 Starting Local Fine-Tuning on M4 Max")
    print(f"   Model: {model_path}")
    print(f"   Data:  {data_path}")
    print(f"   Steps: {iters}")
    
    # 1. Load Model
    print("📥 Loading model...")
    model, tokenizer = load(model_path)
    
    # 2. Freeze Model & Enable LoRA
    # Using mlx_lm's built-in fine-tuning logic would be simpler, 
    # but here we'll use a subprocess to call the robust mlx_lm.lora CLI 
    # if we want to avoid re-implementing the trainer.
    # HOWEVER, for "Autonomous" integration, let's wrap the library calls.
    
    # Actually, mlx_lm provides a 'train' function in recent versions.
    # Let's fallback to invoking the CLI command which is very stable.
    # This allows us to benefit from upstream improvements to lora.py easily.
    
    cmd = [
        sys.executable, "-m", "mlx_lm.lora",
        "--model", model_path,
        "--data", data_path,
        "--train",
        "--iters", str(iters),
        "--batch-size", str(batch_size),
        "--adapter-path", adapter_path,
        "--save-every", str(iters), # Save at end
        "--seed", "42"
    ]
    
    # print(f"🔧 param_count: {sum(x.size for x in model.parameters().values())}")
    
    # Execute
    print(f"▶️ Executing: {' '.join(cmd)}")
    result = os.system(' '.join(cmd))
    
    if result == 0:
        print(f"✅ Training Complete. Adapter saved to: {adapter_path}")
    else:
        print(f"❌ Training Failed with exit code {result}")
        sys.exit(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgencyOS Autonomous Trainer (M4 Max)")
    parser.add_argument("--model", type=str, default="mlx-community/Llama-3.2-3B-Instruct")
    parser.add_argument("--data", type=str, required=True, help="Path to data directory (train.jsonl, etc)")
    parser.add_argument("--adapter-out", type=str, default="adapters/agency_os_v1")
    parser.add_argument("--iters", type=int, default=100)
    
    args = parser.parse_args()
    
    # Ensure full path for adapter to avoid losing it
    adapter_full_path = str(Path(args.adapter_out).resolve())
    
    run_training(
        model_path=args.model,
        data_path=args.data,
        adapter_path=adapter_full_path,
        iters=args.iters
    )
