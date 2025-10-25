#!/usr/bin/env python3
"""
QLoRA Fine-Tuning for Esper3.1 on Algorithm/Reasoning Tasks

Uses PEFT (Parameter-Efficient Fine-Tuning) to add small adapters (~200MB)
without modifying the base model.

Requirements:
    pip install --break-system-packages transformers peft accelerate bitsandbytes

Hardware:
    M4 Pro 48GB - ~2-3 hours training time

Cost:
    ~$0.02 (electricity)

Output:
    models/esper31-algorithms-qlora/
        - adapter_config.json
        - adapter_model.safetensors (~200MB)
"""
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

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
    prepare_model_for_kbit_training,
    TaskType
)
from datasets import Dataset


@dataclass
class TrainingConfig:
    """Training configuration."""
    model_name: str = "ValiantLabs/gpt-oss-20b-Esper3.1"
    train_data: str = "data/esper31_training_formatted.jsonl"
    output_dir: str = "models/esper31-algorithms-qlora"

    # QLoRA config
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = None

    # Training params
    num_epochs: int = 3
    batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    warmup_steps: int = 100
    max_seq_length: int = 2048

    # Hardware
    device: str = "auto"  # Auto-select (will use CPU with 8-bit quantization)
    fp16: bool = False  # Using 8-bit quantization instead
    bf16: bool = False  # Using 8-bit quantization instead

    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]


def load_training_data(data_path: str) -> Dataset:
    """Load and prepare training data."""
    data = []
    with open(data_path) as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    print(f"✅ Loaded {len(data)} training examples")
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

    print("=" * 70)
    print("ESPER3.1 QLORA TRAINING (8-bit Quantized)")
    print("=" * 70)
    print(f"\n📦 Model: {config.model_name}")
    print(f"📊 Data: {config.train_data}")
    print(f"💾 Output: {config.output_dir}")
    print(f"🔧 LoRA rank: {config.lora_r}")
    print(f"📈 Epochs: {config.num_epochs}")
    print(f"⚡ Using 8-bit quantization (fits in 48GB RAM)")
    print(f"⏱️  Estimated time: 4-6 hours (CPU is slower than GPU)")

    # Load tokenizer
    print(f"\n📝 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model with 8-bit quantization
    print(f"📦 Loading base model with 8-bit quantization...")
    print(f"   (This may take a few minutes - model is ~20GB)")
    print(f"   Using CPU + 8-bit quantization to fit in 48GB RAM")

    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        load_in_8bit=True,  # 8-bit quantization (20GB FP32 → ~10GB INT8)
        device_map="auto",  # Let transformers decide best device placement
        trust_remote_code=True,
        torch_dtype=torch.float16,  # Use FP16 for non-quantized layers
    )

    # Prepare for training
    print(f"🔧 Preparing model for QLoRA...")
    model = prepare_model_for_kbit_training(model)

    # Enable gradient checkpointing to save memory
    model.gradient_checkpointing_enable()
    print(f"✅ Gradient checkpointing enabled (saves ~40% memory)")

    # Configure LoRA
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

    # Load data
    print(f"\n📊 Loading training data...")
    dataset = load_training_data(config.train_data)

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

    # Training arguments (optimized for CPU + 8-bit)
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        logging_steps=10,
        save_steps=200,
        eval_steps=200,
        evaluation_strategy="steps",
        save_total_limit=3,
        load_best_model_at_end=True,
        fp16=False,  # Using 8-bit quantization instead
        bf16=False,
        optim="adamw_8bit",  # 8-bit optimizer to match 8-bit model
        report_to="none",  # Disable wandb
        remove_unused_columns=False,
        gradient_checkpointing=True,  # Enable gradient checkpointing
        max_grad_norm=0.3,  # Gradient clipping
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
    print(f"   Estimated time: 2-3 hours on M4 Pro")
    print(f"   Memory usage: ~20GB")
    print(f"\n" + "=" * 70)

    trainer.train()

    # Save
    print(f"\n💾 Saving adapters...")
    model.save_pretrained(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)

    print(f"\n" + "=" * 70)
    print(f"✅ TRAINING COMPLETE!")
    print(f"=" * 70)
    print(f"📁 Adapters saved to: {config.output_dir}")
    print(f"📦 Adapter size: ~200MB")
    print(f"\n🎯 Next Steps:")
    print(f"1. Test adapters: python scripts/test_esper31_adapters.py")
    print(f"2. Export to Ollama: python scripts/export_to_ollama.py")
    print(f"3. Compare: python scripts/benchmark_before_after.py")


if __name__ == "__main__":
    main()
