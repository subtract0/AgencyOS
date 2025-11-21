#!/usr/bin/env python3
"""
THE LOCAL FOUNDRY: VCoder 120B Fine-Tuner (M4 Max Native)

Leverages the M4 Max's 128GB Unified Memory to fine-tune a 120B Parameter MoE.
Uses MLX for hardware-accelerated LoRA training on Apple Silicon.

Memory Budget:
- Model (4-bit): ~75 GB
- Cache/Grads:   ~30 GB
- OS/System:     ~20 GB
- TOTAL:         ~125 GB (Tight, but possible)

Usage:
    python scripts/train_vcoder_local_m4.py
"""

import sys
import mlx.optimizers as optim
from mlx_lm import load, train
from mlx_lm.tuner import TrainingArgs
from pathlib import Path
import logging

# Configuration
MODEL_PATH = "nightmedia/VCoder-120b-1.0-qx86-hi-mlx" 
DATA_PATH = ".agency/datasets/dpo_nightly_ready.jsonl"
ADAPTER_PATH = "models/adapters/vcoder_120b_local_v1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("M4Foundry")

def run_local_training():
    logger.info("🔥 INITIALIZING M4 MAX FOUNDRY")
    logger.info(f"   Target: {MODEL_PATH}")
    logger.info("   Memory Strategy: 4-bit MoE Quantization")

    # 1. Load the Beast (4-bit quantized)
    logger.info("📦 Loading 120B Model into Unified Memory...")
    model, tokenizer = load(MODEL_PATH)
    
    # 2. Validate Dataset
    data_path = Path(DATA_PATH)
    if not data_path.exists():
        logger.error(f"❌ Dataset not found at {DATA_PATH}")
        logger.info("   Run 'python scripts/compile_dpo_dataset.py' first.")
        sys.exit(1)

    # 3. Configure LoRA for High-RAM Environment
    # We target the 'gate' layers (routers) and experts for maximum steering
    training_args = TrainingArgs(
        batch_size=1,            # Keep low for 120B model
        iters=100,               # Short, potent fine-tuning steps
        learning_rate=1e-5,      # Surgical precision
        adapter_path=ADAPTER_PATH,
        max_seq_length=2048,     # Reasonable context length
        lora_parameters={
            "rank": 8,           # Low rank to save memory on 120B params
            "alpha": 16,
            "dropout": 0.05,
            "scale": 10.0
        },
        # Save memory by aggressive gradient checkpointing if supported
        grad_checkpoint=True 
    )

    logger.info("🚀 ENGAGING NEURAL ENGINE (NPUs)...")
    
    # 4. Execute Training
    # MLX handles the LoRA injection and training loop automatically
    train.train(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        data=data_path, 
    )

    logger.info("✅ TRAINING COMPLETE")
    logger.info(f"   New Brain located at: {ADAPTER_PATH}")
    logger.info("   To activate: Update LOCAL_MODEL_ADAPTER in .env")

if __name__ == "__main__":
    # Ensure we have enough file descriptors for huge models
    import resource
    resource.setrlimit(resource.RLIMIT_NOFILE, (4096, 4096))
    
    run_local_training()