#!/usr/bin/env python3
"""
Autonomous Esper3.1 QLoRA Training with Watchdog Monitoring

Bulletproof training with:
- Progress monitoring (detects stuck training >5 min)
- Auto-retry with fallback configs
- Comprehensive logging
- Cloud alternative if all fails

User wakes up to either:
- ✅ Trained adapters
- ❌ Diagnostic report + cloud script
"""
import json
import time
import subprocess
import signal
import sys
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import threading


@dataclass
class TrainingConfig:
    """Training configuration with fallback levels."""
    name: str
    threads: int
    batch_size: int
    gradient_accum: int
    lora_rank: int
    max_seq_length: int
    num_epochs: int
    timeout_first_step_min: int = 15  # Max time for first step
    timeout_step_min: int = 5  # Max time for subsequent steps


# Configurations to try (in order of preference)
CONFIGS = [
    TrainingConfig(
        name="Optimal",
        threads=10,
        batch_size=1,
        gradient_accum=32,
        lora_rank=8,
        max_seq_length=1024,
        num_epochs=3,
    ),
    TrainingConfig(
        name="Moderate",
        threads=6,
        batch_size=1,
        gradient_accum=16,
        lora_rank=6,
        max_seq_length=1024,
        num_epochs=3,
        timeout_first_step_min=20,
    ),
    TrainingConfig(
        name="Conservative",
        threads=4,
        batch_size=1,
        gradient_accum=8,
        lora_rank=4,
        max_seq_length=512,
        num_epochs=3,
        timeout_first_step_min=25,
    ),
]


class WatchdogMonitor:
    """Monitors training progress and kills if stuck."""

    def __init__(self, config: TrainingConfig, log_file: Path):
        self.config = config
        self.log_file = log_file
        self.last_progress = None
        self.last_update_time = time.time()
        self.should_stop = False
        self.process = None

    def monitor(self):
        """Monitor training progress in background thread."""
        while not self.should_stop:
            time.sleep(30)  # Check every 30 seconds

            # Read latest progress from log
            if self.log_file.exists():
                try:
                    with open(self.log_file) as f:
                        lines = f.readlines()

                    # Look for progress indicators
                    for line in reversed(lines[-50:]):  # Last 50 lines
                        if "it/s]" in line or "Step" in line or "loss" in line:
                            current_progress = line.strip()

                            if current_progress != self.last_progress:
                                # Progress detected!
                                self.last_progress = current_progress
                                self.last_update_time = time.time()
                                print(f"\n[Watchdog] Progress detected: {current_progress[:80]}")
                                break
                except Exception as e:
                    print(f"\n[Watchdog] Error reading log: {e}")

            # Check if stuck
            time_since_update = time.time() - self.last_update_time

            # Different timeouts for first step vs subsequent
            if self.last_progress is None:
                timeout = self.config.timeout_first_step_min * 60
            else:
                timeout = self.config.timeout_step_min * 60

            if time_since_update > timeout:
                print(f"\n[Watchdog] ⚠️ STUCK DETECTED!")
                print(f"   No progress for {time_since_update/60:.1f} minutes")
                print(f"   Timeout threshold: {timeout/60} minutes")
                print(f"   Killing training process...")

                if self.process:
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                        time.sleep(2)
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except:
                        pass

                return "STUCK"

        return "STOPPED"


def run_training_with_config(config: TrainingConfig, data_path: str, output_dir: str) -> dict:
    """Run training with specific config and watchdog monitoring."""

    print(f"\n{'='*70}")
    print(f"TRYING CONFIG: {config.name}")
    print(f"{'='*70}")
    print(f"Threads: {config.threads}")
    print(f"Batch size: {config.batch_size}")
    print(f"Gradient accumulation: {config.gradient_accum}")
    print(f"LoRA rank: {config.lora_rank}")
    print(f"Timeout (first step): {config.timeout_first_step_min} min")
    print(f"Timeout (other steps): {config.timeout_step_min} min")
    print(f"{'='*70}\n")

    # Create log file
    log_file = Path(f"data/training_log_{config.name.lower()}.txt")

    # Prepare training command
    training_script = f"""
import os
os.environ["OMP_NUM_THREADS"] = "{config.threads}"
os.environ["MKL_NUM_THREADS"] = "{config.threads}"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
torch.set_num_threads({config.threads})

from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import json

# Load tokenizer
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("ValiantLabs/gpt-oss-20b-Esper3.1")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load model
print("Loading model in FP16...")
model = AutoModelForCausalLM.from_pretrained(
    "ValiantLabs/gpt-oss-20b-Esper3.1",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    device_map=None,
    trust_remote_code=True
)

device = torch.device("cpu")
model = model.to(device)
print("✅ Model loaded")

# Enable gradient checkpointing
if hasattr(model, 'gradient_checkpointing_enable'):
    model.gradient_checkpointing_enable()
    print("✅ Gradient checkpointing enabled")

# Add LoRA
print("Adding LoRA adapters...")
lora_config = LoraConfig(
    r={config.lora_rank},
    lora_alpha={config.lora_rank * 2},
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],
    bias="none",
    task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)
print("✅ LoRA adapters added")

# Load data
print("Loading training data...")
with open("{data_path}") as f:
    data = [json.loads(line) for line in f if line.strip()]

dataset = Dataset.from_list(data)

# Format
def format_messages(ex, tokenizer):
    text = tokenizer.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)
    return {{"text": text}}

dataset = dataset.map(lambda ex: format_messages(ex, tokenizer), remove_columns=dataset.column_names)

# Tokenize
def tokenize(examples):
    result = tokenizer(examples["text"], truncation=True, max_length={config.max_seq_length}, padding="max_length")
    result["labels"] = result["input_ids"].copy()
    return result

dataset = dataset.map(tokenize, batched=True, remove_columns=["text"])

# Split
split = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = split["train"]
eval_dataset = split["test"]

print(f"Training samples: {{len(train_dataset)}}")
print(f"Validation samples: {{len(eval_dataset)}}")

# Training args
args = TrainingArguments(
    output_dir="{output_dir}",
    num_train_epochs={config.num_epochs},
    per_device_train_batch_size={config.batch_size},
    gradient_accumulation_steps={config.gradient_accum},
    learning_rate=2e-4,
    warmup_steps=50,
    logging_steps=1,  # Log every step for monitoring
    save_steps=50,
    eval_steps=50,
    eval_strategy="steps",
    save_total_limit=2,
    load_best_model_at_end=True,
    fp16=False,
    bf16=False,
    optim="adamw_torch",
    report_to="none",
    remove_unused_columns=False,
    gradient_checkpointing=True,
    max_grad_norm=0.3,
    dataloader_num_workers=0,
    ddp_find_unused_parameters=False,
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
print("\\n🚀 Starting training...")
print(f"Config: {config.name}")
print(f"Steps per epoch: {{len(train_dataset) // {config.gradient_accum}}}")
print("")

trainer.train()

# Save
print("\\n💾 Saving adapters...")
model.save_pretrained("{output_dir}")
tokenizer.save_pretrained("{output_dir}")

print("\\n✅ Training complete!")
"""

    # Write training script
    script_path = Path(f"/tmp/train_{config.name.lower()}.py")
    with open(script_path, 'w') as f:
        f.write(training_script)

    # Start watchdog
    monitor = WatchdogMonitor(config, log_file)
    monitor_thread = threading.Thread(target=monitor.monitor, daemon=True)
    monitor_thread.start()

    # Run training
    start_time = time.time()
    try:
        with open(log_file, 'w') as log_f:
            process = subprocess.Popen(
                [".venv-training/bin/python", str(script_path)],
                stdout=log_f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid  # Create new process group for clean kill
            )

            monitor.process = process

            # Wait for completion
            returncode = process.wait()

    except Exception as e:
        print(f"\n❌ Training failed with exception: {e}")
        return {
            "status": "failed",
            "config": config.name,
            "error": str(e),
            "duration_min": (time.time() - start_time) / 60
        }
    finally:
        monitor.should_stop = True

    duration_min = (time.time() - start_time) / 60

    # Check result
    if returncode == 0:
        print(f"\n✅ Training completed successfully!")
        print(f"   Duration: {duration_min:.1f} minutes")
        print(f"   Config: {config.name}")

        return {
            "status": "success",
            "config": config.name,
            "duration_min": duration_min,
            "output_dir": output_dir,
            "log_file": str(log_file)
        }
    else:
        print(f"\n❌ Training failed (exit code {returncode})")
        print(f"   Duration: {duration_min:.1f} minutes")
        print(f"   See log: {log_file}")

        return {
            "status": "failed",
            "config": config.name,
            "error": f"Exit code {returncode}",
            "duration_min": duration_min,
            "log_file": str(log_file)
        }


def main():
    print("\n" + "="*70)
    print("AUTONOMOUS ESPER3.1 QLORA TRAINING")
    print("="*70)
    print("\nBulletproof training with watchdog monitoring")
    print("Will try multiple configs if training gets stuck")
    print("User will wake up to either:")
    print("  ✅ Trained adapters")
    print("  ❌ Diagnostic report + cloud alternative")
    print("\n" + "="*70 + "\n")

    data_path = "data/esper31_training_formatted.jsonl"
    output_dir = "models/esper31-algorithms-qlora"

    # Verify data exists
    if not Path(data_path).exists():
        print(f"❌ Training data not found: {data_path}")
        sys.exit(1)

    print(f"✅ Training data: {data_path}")

    # Count examples
    with open(data_path) as f:
        num_examples = sum(1 for line in f if line.strip())
    print(f"✅ Examples: {num_examples}")

    # Try each config
    results = []
    for i, config in enumerate(CONFIGS, 1):
        print(f"\n{'#'*70}")
        print(f"# ATTEMPT {i}/{len(CONFIGS)}: {config.name} Configuration")
        print(f"{'#'*70}\n")

        result = run_training_with_config(config, data_path, output_dir)
        results.append(result)

        if result["status"] == "success":
            # SUCCESS! Save results and exit
            results_file = Path("data/training_results_autonomous.json")
            with open(results_file, 'w') as f:
                json.dump({
                    "final_status": "success",
                    "successful_config": config.name,
                    "attempts": results,
                    "output_dir": output_dir
                }, f, indent=2)

            print(f"\n{'='*70}")
            print("✅ TRAINING SUCCESSFUL!")
            print(f"{'='*70}")
            print(f"Config used: {config.name}")
            print(f"Duration: {result['duration_min']:.1f} minutes")
            print(f"Adapters saved to: {output_dir}")
            print(f"Full results: {results_file}")
            print(f"{'='*70}\n")

            return 0
        else:
            print(f"\n⚠️ Config {config.name} failed, trying next config...\n")
            time.sleep(5)  # Brief pause before next attempt

    # All configs failed - generate diagnostic report
    print(f"\n{'='*70}")
    print("❌ ALL CONFIGS FAILED")
    print(f"{'='*70}\n")

    # Save diagnostic report
    report = {
        "final_status": "failed",
        "attempts": results,
        "diagnosis": "All training configurations failed. Recommend cloud GPU.",
        "cloud_alternative": {
            "provider": "RunPod",
            "estimated_cost_usd": 1.50,
            "estimated_time_hours": 0.5,
            "command": "# See scripts/train_esper31_runpod.sh"
        }
    }

    report_file = Path("data/training_diagnostic_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"❌ Training failed after {len(CONFIGS)} attempts")
    print(f"📊 Diagnostic report: {report_file}")
    print(f"\n💡 RECOMMENDATION: Use cloud GPU")
    print(f"   Provider: RunPod (A100)")
    print(f"   Cost: ~$1.50")
    print(f"   Time: ~30 minutes")
    print(f"   See: scripts/train_esper31_runpod.sh")
    print(f"\n{'='*70}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
