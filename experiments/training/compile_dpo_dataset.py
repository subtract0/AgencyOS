
import json
import random
import os
from pathlib import Path

def generate_synthetic_data(output_dir: str, num_samples: int = 50):
    """
    Generate synthetic Instruction-Output pairs for AgencyOS self-improvement.
    
    In a real scenario, this would scan:
    - User/Agent logs (agency.log)
    - Git history (good commits)
    - Test files (converting tests to specs)
    """
    print(f"🧬 Compiling 'DPO' Dataset (SFT format for MLX) to {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    data = []
    
    # Synthetic examples showing Agent how to use its own tools
    examples = [
        {
            "instruction": "Schedule a meeting with the team.",
            "output": "I will use the Calendar tool.\n{\"name\": \"Calendar\", \"parameters\": {\"action\": \"schedule_event\", \"data\": \"{\\\"summary\\\": \\\"Team Meeting\\\", \\\"start_date\\\": \\\"2025-10-27T10:00:00Z\\\", \\\"end_date\\\": \\\"2025-10-27T11:00:00Z\\\"}\"}}"
        },
        {
            "instruction": "Check my unread emails.",
            "output": "Checking your inbox now.\n{\"name\": \"Email\", \"parameters\": {\"action\": \"list_unread\", \"data\": \"{\\\"limit\\\": 5}\"}}"
        },
        {
            "instruction": "Draft a report about Q3 metrics.",
            "output": "I'll draft that email for you.\n{\"name\": \"Email\", \"parameters\": {\"action\": \"draft_email\", \"data\": \"{\\\"to\\\": \\\"boss@example.com\\\", \\\"subject\\\": \\\"Q3 Report\\\", \\\"body\\\": \\\"Here are the metrics...\\\"}\"}}"
        }
    ]
    
    for _ in range(num_samples):
        ex = random.choice(examples)
        # Add some variety or noise if needed
        messages = [
            {"role": "user", "content": ex["instruction"]},
            {"role": "assistant", "content": ex["output"]}
        ]
        data.append({"messages": messages})
        
    # Split Train/Valid
    split_idx = int(len(data) * 0.9)
    train_data = data[:split_idx]
    valid_data = data[split_idx:]
    
    with open(os.path.join(output_dir, "train.jsonl"), "w") as f:
        for entry in train_data:
            f.write(json.dumps(entry) + "\n")
            
    with open(os.path.join(output_dir, "valid.jsonl"), "w") as f:
        for entry in valid_data:
            f.write(json.dumps(entry) + "\n")
            
    print(f"✅ Generated {len(train_data)} train and {len(valid_data)} valid samples.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/agency_self_improvement")
    args = parser.parse_args()
    
    generate_synthetic_data(args.out)
