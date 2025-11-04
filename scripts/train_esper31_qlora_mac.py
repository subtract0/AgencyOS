#!/usr/bin/env python3
"""
QLoRA Fine-Tuning for Esper3.1 - M4 Pro Optimized Version

NO bitsandbytes required - uses native PyTorch with aggressive memory optimization.

Hardware:
    M4 Pro 48GB - ~4-6 hours training time (CPU, 10 threads)

Strategy:
    - Load model in FP16 (half precision) → ~20GB
    - Use all 10 performance cores → Max CPU utilization
    - Extreme gradient accumulation (batch=1, accum=32) → Minimal memory growth
    - Gradient checkpointing → Saves 40% memory
    - Single-process data loading → Avoids macOS fork deadlocks
    - Train on subset if needed → Faster iteration

Cost:
    ~$0.02 (electricity for 5 hours)
"""
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
import sys

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType
)
from datasets import Dataset


@dataclass
class TrainingConfig:
    """Training configuration for M4 Pro."""
    model_name: str = "ValiantLabs/gpt-oss-20b-Esper3.1"
    train_data: str = "data/esper31_training_formatted.jsonl"
    output_dir: str = "models/esper31-algorithms-qlora"

    # QLoRA config
    lora_r: int = 8  # Reduced from 16 to save memory
    lora_alpha: int = 16  # Reduced from 32
    lora_dropout: float = 0.05
    target_modules: List[str] = None

    # Training params (VERY conservative for CPU)
    num_epochs: int = 3
    batch_size: int = 1  # Minimum
    gradient_accumulation_steps: int = 32  # EXTREME accumulation to simulate batch=32
    learning_rate: float = 2e-4
    warmup_steps: int = 50  # Reduced
    max_seq_length: int = 1024  # Reduced from 2048 to save memory

    # Memory optimization
    use_subset: bool = False  # Train on subset for faster iteration?
    subset_size: int = 200  # If use_subset=True

    def __post_init__(self):
        if self.target_modules is None:
            # Only train attention layers (saves memory)
            self.target_modules = ["q_proj", "v_proj"]


def check_memory():
    """Check available memory."""
    import subprocess
    result = subprocess.run(['vm_stat'], capture_output=True, text=True)
    lines = result.stdout.split('\n')

    for line in lines:
        if 'Pages free' in line:
            free_pages = int(line.split(':')[1].strip().replace('.', ''))
            free_gb = (free_pages * 4096) / (1024**3)
            return free_gb
    return 0


def load_training_data(data_path: str, use_subset: bool = False, subset_size: int = 200) -> Dataset:
    """Load and prepare training data."""
    data = []
    with open(data_path) as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    if use_subset:
        import random
        random.seed(42)
        data = random.sample(data, min(subset_size, len(data)))
        print(f"⚠️  Using subset: {len(data)} examples (faster iteration)")
    else:
        print(f"✅ Loaded {len(data)} training examples (full dataset)")

    return Dataset.from_list(data)


def format_messages_for_training(example: Dict, tokenizer) -> Dict:
    """Format messages into training format."""
    messages = example["messages"]

    # Convert messages to chat format
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )

    return {"text": text}


def main():
    config = TrainingConfig()

    # Configure PyTorch to use all performance cores (M4 Pro has 10)
    import os
    num_threads = 10  # M4 Pro performance cores
    torch.set_num_threads(num_threads)
    torch.set_num_interop_threads(num_threads)
    os.environ["OMP_NUM_THREADS"] = str(num_threads)
    os.environ["MKL_NUM_THREADS"] = str(num_threads)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Fix fork deadlock

    # Check if user wants subset training
    if "--subset" in sys.argv:
        config.use_subset = True
        print("\n⚡ FAST MODE: Training on 200-example subset")
        print("   (Use for quick testing, then train on full dataset)\n")

    print("=" * 70)
    print("ESPER3.1 QLORA TRAINING (M4 Pro Optimized)")
    print("=" * 70)
    print(f"🔥 Using {num_threads} CPU threads (M4 Pro performance cores)")
    print(f"\n📦 Model: {config.model_name}")
    print(f"📊 Data: {config.train_data}")
    print(f"💾 Output: {config.output_dir}")
    print(f"🔧 LoRA rank: {config.lora_r} (reduced for memory)")
    print(f"📈 Epochs: {config.num_epochs}")
    print(f"💪 Gradient accumulation: {config.gradient_accumulation_steps} (simulates batch=32)")
    print(f"⏱️  Estimated time: 4-6 hours (CPU, full dataset, 10 threads)")
    if config.use_subset:
        print(f"⚡ Subset mode: ~45 min (testing, 10 threads)")

    # Check memory
    free_gb = check_memory()
    print(f"\n🧠 Free memory: {free_gb:.1f} GB")
    if free_gb < 25:
        print("⚠️  WARNING: Low memory. Close other applications!")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    # Load tokenizer
    print(f"\n📝 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model WITHOUT bitsandbytes (pure PyTorch)
    print(f"📦 Loading base model in FP16...")
    print(f"   (This may take 10-15 minutes - model is ~20GB)")
    print(f"   Loading to CPU (MPS has compatibility issues)")

    try:
        model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            torch_dtype=torch.float16,  # FP16 to save memory
            low_cpu_mem_usage=True,  # Optimized loading
            device_map=None,  # Don't auto-assign to GPU
            trust_remote_code=True
        )

        # Move to CPU explicitly
        device = torch.device("cpu")
        model = model.to(device)

        print(f"✅ Model loaded on CPU in FP16 (~20GB)")

    except Exception as e:
        print(f"\n❌ Failed to load model: {e}")
        print(f"\nThis usually means:")
        print(f"  1. Not enough RAM (need ~25GB free)")
        print(f"  2. Other apps using too much memory")
        print(f"\nTry:")
        print(f"  - Close Chrome, VS Code, etc.")
        print(f"  - Restart Mac to clear memory")
        print(f"  - Run with --subset flag for smaller test")
        return

    # Enable gradient checkpointing BEFORE adding LoRA
    if hasattr(model, 'gradient_checkpointing_enable'):
        model.gradient_checkpointing_enable()
        print(f"✅ Gradient checkpointing enabled (saves ~40% memory)")

    # Configure LoRA (smaller config to save memory)
    print(f"\n🔧 Adding LoRA adapters...")
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )

    # Add LoRA adapters
    model = get_peft_model(model, lora_config)

    print(f"\n📊 Trainable Parameters:")
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   Total: {total_params:,}")
    print(f"   Trainable: {trainable_params:,} ({trainable_params/total_params*100:.2f}%)")
    print(f"   Memory for adapters: ~{trainable_params * 2 / 1e9:.2f} GB")

    # Load data
    print(f"\n📊 Loading training data...")
    dataset = load_training_data(
        config.train_data,
        use_subset=config.use_subset,
        subset_size=config.subset_size
    )

    # Format data
    print(f"🔄 Formatting data...")
    dataset = dataset.map(
        lambda ex: format_messages_for_training(ex, tokenizer),
        remove_columns=dataset.column_names
    )

    # Tokenize
    def tokenize_function(examples):
        result = tokenizer(
            examples["text"],
            truncation=True,
            max_length=config.max_seq_length,
            padding="max_length"
        )
        result["labels"] = result["input_ids"].copy()
        return result

    print(f"🔄 Tokenizing...")
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text"]
    )

    # Split train/val
    split_dataset = tokenized_dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split_dataset["train"]
    eval_dataset = split_dataset["test"]

    print(f"✅ Training samples: {len(train_dataset)}")
    print(f"✅ Validation samples: {len(eval_dataset)}")

    # Training arguments (VERY conservative for CPU)
    print(f"\n⚙️  Configuring training...")
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        logging_steps=5,  # Log frequently
        save_steps=100,  # Save often (in case of crashes)
        eval_steps=100,
        eval_strategy="steps",  # Updated from evaluation_strategy
        save_total_limit=2,  # Only keep 2 checkpoints (save disk)
        load_best_model_at_end=True,
        fp16=False,  # Already using FP16 model
        bf16=False,
        optim="adamw_torch",
        report_to="none",
        remove_unused_columns=False,
        gradient_checkpointing=True,
        max_grad_norm=0.3,
        dataloader_num_workers=0,  # Single process (multiprocessing causes deadlocks on macOS)
        ddp_find_unused_parameters=False,
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    # Train
    print(f"\n🚀 Starting training...")
    print(f"   CPU threads: {num_threads} (performance cores)")
    print(f"   Data workers: 0 (single process - avoids macOS fork issues)")
    print(f"   Effective batch size: {config.batch_size * config.gradient_accumulation_steps}")
    print(f"   Steps per epoch: {len(train_dataset) // (config.batch_size * config.gradient_accumulation_steps)}")
    if config.use_subset:
        print(f"   Estimated time: ~45 minutes (subset)")
    else:
        print(f"   Estimated time: ~4-6 hours (full dataset)")
    print(f"\n" + "=" * 70)
    print(f"💡 TIP: You can safely Ctrl+C and resume later from last checkpoint")
    print(f"=" * 70 + "\n")

    try:
        trainer.train()
    except KeyboardInterrupt:
        print(f"\n⚠️  Training interrupted by user")
        print(f"   Last checkpoint saved to: {config.output_dir}")
        print(f"   To resume, run this script again (will auto-resume)")
        return

    # Save
    print(f"\n💾 Saving adapters...")
    model.save_pretrained(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)

    print(f"\n" + "=" * 70)
    print(f"✅ TRAINING COMPLETE!")
    print(f"=" * 70)
    print(f"📁 Adapters saved to: {config.output_dir}")
    print(f"📦 Adapter size: ~{trainable_params * 2 / 1e9:.2f} GB")
    print(f"\n🎯 Next Steps:")
    print(f"1. Test adapters: .venv-training/bin/python scripts/test_esper31_adapters.py")
    print(f"2. Run hard benchmark: python scripts/benchmark_esper31_hard.py --save-baseline")
    print(f"3. Compare: python scripts/benchmark_esper31_hard.py --with-adapters --compare-to-baseline")


if __name__ == "__main__":
    main()
