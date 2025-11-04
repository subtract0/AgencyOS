#!/bin/bash
###############################################################################
# Esper3.1 QLoRA Training on RunPod (Cloud GPU Fallback)
#
# Use this if local training fails.
#
# Cost: ~$1.50 (A100 GPU for 30-60 minutes)
# Time: 30-60 minutes
#
# Setup:
#   1. Create RunPod account: https://runpod.io
#   2. Deploy A100 GPU pod with PyTorch template
#   3. Upload this script and training data
#   4. Run: bash train_esper31_runpod.sh
###############################################################################

set -e

echo "=================================================================="
echo "ESPER3.1 QLORA TRAINING ON RUNPOD (CLOUD GPU)"
echo "=================================================================="
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install transformers peft accelerate datasets torch

# Download model (cached after first run)
echo "📦 Downloading Esper3.1 (20GB, one-time)..."
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('ValiantLabs/gpt-oss-20b-Esper3.1', trust_remote_code=True)"

# Train
echo "🚀 Starting training..."
python << 'TRAINING_SCRIPT'
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import json

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("ValiantLabs/gpt-oss-20b-Esper3.1")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load model on GPU
print("Loading model on GPU...")
model = AutoModelForCausalLM.from_pretrained(
    "ValiantLabs/gpt-oss-20b-Esper3.1",
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

# Add LoRA
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],
    bias="none",
    task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)

# Load data
with open("esper31_training_formatted.jsonl") as f:
    data = [json.loads(line) for line in f if line.strip()]

dataset = Dataset.from_list(data)

# Format
def format_messages(ex, tokenizer):
    text = tokenizer.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)
    return {"text": text}

dataset = dataset.map(lambda ex: format_messages(ex, tokenizer), remove_columns=dataset.column_names)

# Tokenize
def tokenize(examples):
    result = tokenizer(examples["text"], truncation=True, max_length=1024, padding="max_length")
    result["labels"] = result["input_ids"].copy()
    return result

dataset = dataset.map(tokenize, batched=True, remove_columns=["text"])

# Split
split = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = split["train"]
eval_dataset = split["test"]

# Training args (GPU optimized)
args = TrainingArguments(
    output_dir="esper31-algorithms-qlora",
    num_train_epochs=3,
    per_device_train_batch_size=4,  # Larger batch on GPU
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    warmup_steps=50,
    logging_steps=10,
    save_steps=100,
    eval_steps=100,
    eval_strategy="steps",
    save_total_limit=2,
    load_best_model_at_end=True,
    fp16=True,  # GPU supports FP16
    optim="adamw_torch",
    report_to="none",
    remove_unused_columns=False,
    max_grad_norm=0.3,
)

# Trainer
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
)

# Train
print("Training...")
trainer.train()

# Save
print("Saving...")
model.save_pretrained("esper31-algorithms-qlora")
tokenizer.save_pretrained("esper31-algorithms-qlora")

print("✅ Training complete!")
TRAINING_SCRIPT

echo ""
echo "=================================================================="
echo "✅ TRAINING COMPLETE"
echo "=================================================================="
echo "Adapters saved to: esper31-algorithms-qlora/"
echo "Download to local machine:"
echo "  scp -r runpod:esper31-algorithms-qlora/ models/"
echo ""
echo "Total cost: ~\$1.50"
echo "=================================================================="
