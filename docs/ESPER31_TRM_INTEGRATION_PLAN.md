# Esper 3.1 + TRM Integration Plan
**Timeline**: 2-3 weeks
**Cost**: ~$2 (minimal GPT-5 labeling)
**Architecture**: gpt-oss-20b-Esper3.1 (Router + Generalist) → trm:7m (Recursive Specialist)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ gpt-oss-20b-Esper3.1 (Dual Role)                                │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ Base: OpenAI gpt-oss-20b (21B params, 3.6B active)             │
│ Fine-tuning: ValiantLabs Esper3.1 (DevOps + coding specialist) │
│ Additional Training: QLoRA on 1,100 TRM delegation examples     │
│                                                                  │
│ Capabilities:                                                    │
│ 1. Router: Detect tasks needing recursive reasoning             │
│ 2. Generalist: Handle simple coding/architecture tasks solo     │
│ 3. Translator: Format complex tasks for TRM input               │
└─────────────┬────────────────────────────────────────────────────┘
              │
              ├─ Decision: use_trm = 0
              │   ↓
              │   Solo Execution (coding, DevOps, architecture)
              │
              └─ Decision: use_trm = 1
                  ↓
                  Translation → trm:7m format
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ trm:7m (Samsung Tiny Recursive Model)                           │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ Architecture: 7M params, 2-layer network                        │
│ Approach: Recursive refinement (up to 16 iterations)            │
│ Strengths: ARC-AGI (45%), optimization, logical puzzles         │
│                                                                  │
│ Use Cases:                                                       │
│ - Complex architecture optimization                             │
│ - Graph/constraint satisfaction problems                        │
│ - Recursive algorithm design                                    │
│ - Training data generation (synthetic examples)                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Why This Architecture Works

### Esper3.1's Strengths
- **Coding Specialist**: Pre-trained on DevOps, architecture, code reasoning
- **MoE Architecture**: 3.6B active params → fast, efficient
- **Agentic Capabilities**: Native function calling, reasoning effort control
- **Fine-tunable**: Can add QLoRA adapters for TRM delegation

### TRM's Strengths
- **Recursive Reasoning**: Iteratively refines solutions (16 iterations)
- **Tiny but Mighty**: 7M params, beats models 10,000x larger on puzzles
- **Optimization**: Excels at constraint satisfaction, graph problems
- **Fast**: 2-layer network, <1s inference

### Synergy
- **Esper3.1** handles 70-80% of tasks (coding, DevOps, architecture)
- **TRM** handles 20-30% of tasks (complex optimization, recursive reasoning)
- **Cost Savings**: Both local ($0), vs GPT-5 remote ($4/1M tokens)
- **Latency**: Both <2s, vs GPT-5 remote (3-5s)

---

## Training Data

### Existing Dataset: `data/training_examples_final.jsonl` (1,102 examples)

**Current Format**:
```jsonl
{"instruction": "Solve this graph problem...", "input": "...", "output": "..."}
```

**Updated Format** (for Esper3.1 + TRM training):
```jsonl
{
  "instruction": "Solve this graph problem...",
  "input": "Graph: nodes A,B,C; edges A-B:3, B-C:2, A-C:8. Find shortest path A→C.",
  "output": "Path: A→B→C, Distance: 5",
  "use_trm": 1,
  "trm_translation": {
    "task_type": "GRAPH",
    "input": "nodes:[A,B,C];edges:[A-B:3,B-C:2,A-C:8];source:A;dest:C",
    "max_iterations": 16,
    "expected_output": "{\"path\":[\"A\",\"B\",\"C\"],\"distance\":5}"
  }
}
```

### Labeling Strategy

**Phase 1**: Auto-label with GPT-5 ($1.50 for 1,102 examples)
- Prompt: "Classify if this task needs recursive reasoning (TRM) or can be solved directly (Esper3.1)"
- Add `use_trm` field (0 or 1)
- Add `trm_translation` field (for use_trm=1 cases)

**Expected Distribution**:
- `use_trm = 0`: ~30% (simple coding, straightforward logic)
- `use_trm = 1`: ~70% (complex graphs, optimization, recursion)

**Balanced Training**:
- Add 500 simple coding examples (`use_trm = 0`) from existing Agency codebase
- Final: 600 simple (use_trm=0) + 1,100 complex (use_trm=1) = 1,700 total
- Ratio: 35% simple, 65% complex (reflects production distribution)

---

## Phase 1: Data Preparation (Week 1)

### 1.1 Label Existing Data

**Script**: `scripts/label_trm_delegation.py`
```python
#!/usr/bin/env python3
"""
Label existing 1,102 examples with use_trm and trm_translation fields.
Uses GPT-5 for automatic labeling.
"""
import json
from pathlib import Path
from openai import OpenAI

LABELING_PROMPT = """
You are an expert at classifying coding/reasoning tasks.

Classify if this task requires:
- **TRM (use_trm=1)**: Recursive reasoning, optimization, graph problems, constraint satisfaction
- **Esper3.1 Solo (use_trm=0)**: Straightforward coding, DevOps, architecture (no recursion)

For use_trm=1 cases, also provide a TRM translation in this format:
{
  "task_type": "GRAPH|CSP|OPTIMIZATION|RECURSION",
  "input": "<canonical format for TRM>",
  "max_iterations": <int 1-16>,
  "expected_output": "<structured output format>"
}

Task:
Instruction: {instruction}
Input: {input}

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
        input=example.get("input", "")
    )

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

def main():
    client = OpenAI()

    # Load existing data
    input_path = Path("data/training_examples_final.jsonl")
    output_path = Path("data/trm_delegation_labeled.jsonl")

    examples = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"Labeling {len(examples)} examples with GPT-5...")

    labeled = []
    for i, example in enumerate(examples):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(examples)}")

        labeled_example = label_example(example, client)
        labeled.append(labeled_example)

    # Write labeled data
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

if __name__ == "__main__":
    main()
```

**Cost**: 1,102 examples × ~300 tokens/example × $4/1M tokens = **$1.50**

### 1.2 Generate Simple Examples (Optional Balancing)

If auto-labeling shows >80% use_trm=1, generate 500 simple examples:

**Script**: `scripts/generate_simple_examples.py`
```python
#!/usr/bin/env python3
"""
Generate simple coding examples (use_trm=0) for balance.
Extract from Agency codebase + synthetic generation.
"""
import json
from pathlib import Path
from openai import OpenAI

def generate_from_agency_code():
    """Extract simple coding examples from Agency codebase."""
    examples = []

    # Example: file I/O tasks
    examples.append({
        "instruction": "Read a JSON file and return its contents",
        "input": "File path: data/config.json",
        "output": "Use `json.load(open(path))` to read and parse",
        "use_trm": 0,
        "trm_translation": None
    })

    # Example: string formatting
    examples.append({
        "instruction": "Format a log message with timestamp",
        "input": "Level: INFO, Message: Task completed",
        "output": f"[{datetime.now().isoformat()}] INFO: Task completed",
        "use_trm": 0,
        "trm_translation": None
    })

    # ... generate 500 similar examples

    return examples

def main():
    examples = generate_from_agency_code()

    output_path = Path("data/simple_coding_examples.jsonl")
    with open(output_path, 'w') as f:
        for ex in examples:
            json.dump(ex, f, ensure_ascii=False)
            f.write('\n')

    print(f"✅ Generated {len(examples)} simple examples → {output_path}")

if __name__ == "__main__":
    main()
```

---

## Phase 2: Fine-Tune Esper3.1 with QLoRA (Week 1-2)

### 2.1 Setup TRM in Ollama (If Not Already)

**Check if TRM exists**:
```bash
ollama list | grep -i trm
```

**If not found**, convert Samsung's TRM to Ollama format:

1. **Download Samsung TRM weights** (from GitHub repo):
```bash
git clone https://github.com/SamsungSAILMontreal/TinyRecursiveModels
cd TinyRecursiveModels
# Follow their instructions to get pre-trained weights
```

2. **Convert to GGUF** (for Ollama):
```bash
# Using llama.cpp converter
python convert-hf-to-gguf.py TinyRecursiveModels/trm-7m \
  --outfile trm-7m.gguf \
  --outtype q8_0
```

3. **Import to Ollama**:
```bash
# Create Modelfile
cat > Modelfile <<EOF
FROM ./trm-7m.gguf
PARAMETER temperature 0.0
PARAMETER num_ctx 2048
EOF

# Import
ollama create trm:7m -f Modelfile
```

4. **Verify**:
```bash
ollama list | grep trm
# Should show: trm:7m

ollama run trm:7m "Test query"
```

### 2.2 Download Esper3.1 from HuggingFace

```bash
# Download model weights
huggingface-cli download ValiantLabs/gpt-oss-20b-Esper3.1 \
  --local-dir models/gpt-oss-20b-esper31

# Convert to Ollama format (if needed)
ollama create esper31:20b -f models/gpt-oss-20b-esper31
```

**Or use existing `gpt-oss:20b` as base** and fine-tune with Esper3.1's approach.

### 2.3 QLoRA Fine-Tuning

**Config**: `qlora_esper31_trm.yaml`
```yaml
# QLoRA config for Esper3.1 + TRM delegation training
base_model: "ValiantLabs/gpt-oss-20b-Esper3.1"
quantization: "4bit"
lora_config:
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules:
    - q_proj
    - v_proj
    - k_proj
    - o_proj
  bias: "none"

training:
  batch_size: 1
  gradient_accumulation: 8
  learning_rate: 2e-4
  epochs: 3
  warmup_steps: 100
  save_steps: 200

hardware:
  device: "mps"  # Metal Performance Shaders (M4 Pro)
  mixed_precision: "fp16"
  max_memory_mb: 20000  # 20GB allocation (Esper3.1 ~13GB + overhead)
```

**Training Script**: `scripts/train_esper31_qlora.py`
```python
#!/usr/bin/env python3
"""
Fine-tune Esper3.1 with QLoRA for TRM delegation.
Uses MLX framework (Metal-optimized for M4 Pro).
"""
from mlx_lm import load, generate
from mlx_lm.tuner import train as mlx_train
from pathlib import Path
import json

def format_training_example(example: dict) -> dict:
    """Format example for Esper3.1 + TRM training."""

    # If use_trm=0: Solo execution
    if example["use_trm"] == 0:
        return {
            "text": f"""<|system|>
You are Esper3.1, a coding and architecture specialist. Handle this task directly.
<|user|>
{example['instruction']}
Input: {example.get('input', '')}
<|assistant|>
{{\"action\": \"solo\", \"output\": \"{example['output']}\"}}"""
        }

    # If use_trm=1: Delegate to TRM
    else:
        return {
            "text": f"""<|system|>
You are Esper3.1, a coding and architecture specialist. This task requires recursive reasoning. Delegate to TRM.
<|user|>
{example['instruction']}
Input: {example.get('input', '')}
<|assistant|>
{{\"action\": \"delegate_trm\", \"trm_input\": {json.dumps(example['trm_translation'])}}}"""
        }

def main():
    config = {
        "model": "models/gpt-oss-20b-esper31",
        "train_data": "data/trm_delegation_labeled.jsonl",
        "output_dir": "models/esper31-trm-qlora",
        "lora_rank": 16,
        "lora_alpha": 32,
        "learning_rate": 2e-4,
        "batch_size": 1,
        "gradient_accumulation": 8,
        "epochs": 3,
    }

    # Load base model
    print(f"Loading Esper3.1: {config['model']}")
    model, tokenizer = load(config['model'])

    # Load training data
    raw_data = []
    with open(config['train_data']) as f:
        for line in f:
            if line.strip():
                raw_data.append(json.loads(line))

    formatted_data = [format_training_example(ex) for ex in raw_data]

    # Split train/val (90/10)
    split_idx = int(len(formatted_data) * 0.9)
    train_data = formatted_data[:split_idx]
    val_data = formatted_data[split_idx:]

    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")

    # Train with QLoRA
    print("Starting QLoRA fine-tuning...")
    mlx_train(
        model=model,
        tokenizer=tokenizer,
        train_data=train_data,
        val_data=val_data,
        adapter_file=f"{config['output_dir']}/adapters.safetensors",
        lora_rank=config['lora_rank'],
        lora_alpha=config['lora_alpha'],
        learning_rate=config['learning_rate'],
        batch_size=config['batch_size'],
        gradient_accumulation_steps=config['gradient_accumulation'],
        num_epochs=config['epochs'],
    )

    print(f"✅ Training complete! Adapters saved to {config['output_dir']}")

if __name__ == "__main__":
    main()
```

**Training Time**: ~2-3 hours on M4 Pro 14-core (1,700 examples × 3 epochs)

**Memory**: 13GB (model) + 4GB (optimizer) + 2GB (overhead) = **19GB** (fits in 48GB)

---

## Phase 3: TRM Integration (Week 2)

### 3.1 TRM Executor Wrapper

**Tool**: `tools/trm_executor.py`
```python
#!/usr/bin/env python3
"""
Execute TRM (Tiny Recursive Model) for recursive reasoning tasks.
"""
import subprocess
import json
from typing import Dict, Optional

def execute_trm(
    trm_input: Dict,
    max_iterations: int = 16,
    timeout: int = 30
) -> Dict:
    """
    Execute TRM with given input.

    Args:
        trm_input: TRM task specification
        max_iterations: Max recursive iterations (1-16)
        timeout: Timeout in seconds

    Returns:
        TRM output with solution
    """
    # Format input for TRM
    trm_prompt = format_trm_input(trm_input)

    # Call TRM via Ollama
    result = subprocess.run(
        [
            "ollama", "run", "trm:7m",
            "--max-iterations", str(max_iterations),
            trm_prompt
        ],
        capture_output=True,
        text=True,
        timeout=timeout
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr,
            "iterations": 0
        }

    # Parse TRM output
    output = parse_trm_output(result.stdout)

    return {
        "success": True,
        "output": output,
        "iterations": output.get("iterations_used", max_iterations)
    }

def format_trm_input(trm_input: Dict) -> str:
    """Format input for TRM's expected format."""
    # TRM expects puzzle-like inputs
    # Convert our canonical format to TRM format

    task_type = trm_input.get("task_type", "")
    input_data = trm_input.get("input", "")

    if task_type == "GRAPH":
        # Convert graph format to TRM puzzle format
        return format_graph_for_trm(input_data)

    elif task_type == "CSP":
        return format_csp_for_trm(input_data)

    else:
        # Generic format
        return json.dumps(trm_input, indent=2)

def parse_trm_output(raw_output: str) -> Dict:
    """Parse TRM's output."""
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        # TRM might output in custom format
        return {"raw": raw_output}

# Format converters for different task types
def format_graph_for_trm(graph_input: str) -> str:
    """Convert canonical graph format to TRM puzzle format."""
    # Example: "nodes:[A,B,C];edges:[A-B:3,B-C:2];source:A;dest:C"
    # → TRM grid-based representation

    # Parse canonical format
    parts = graph_input.split(';')
    nodes = parts[0].replace('nodes:[', '').replace(']', '').split(',')
    edges = parts[1].replace('edges:[', '').replace(']', '').split(',')
    source = parts[2].split(':')[1]
    dest = parts[3].split(':')[1]

    # Convert to TRM grid/matrix format
    grid = create_adjacency_matrix(nodes, edges)

    return json.dumps({
        "puzzle_type": "shortest_path",
        "grid": grid,
        "start": source,
        "goal": dest
    })

def format_csp_for_trm(csp_input: str) -> str:
    """Convert CSP to TRM puzzle format."""
    # Similar conversion logic
    pass
```

### 3.2 Integration with Esper3.1

**Tool**: `tools/esper31_trm_executor.py`
```python
#!/usr/bin/env python3
"""
Execute tasks using Esper3.1 + TRM integration.
"""
from mlx_lm import load, generate
import json
from tools.trm_executor import execute_trm

class Esper31TRMExecutor:
    def __init__(self, model_path: str, adapter_path: str):
        """Load Esper3.1 with TRM delegation adapters."""
        self.model, self.tokenizer = load(
            model_path,
            adapter_path=adapter_path
        )

    def execute(self, instruction: str, input_data: str = "") -> Dict:
        """Execute task with Esper3.1 + TRM."""

        # Prompt Esper3.1 to decide + translate
        prompt = f"""<|system|>
You are Esper3.1 with TRM delegation capability. Decide if this task needs TRM.
<|user|>
{instruction}
Input: {input_data}
<|assistant|>
"""

        # Get Esper3.1's decision
        response = generate(
            model=self.model,
            tokenizer=self.tokenizer,
            prompt=prompt,
            max_tokens=512,
            temp=0.0
        )

        decision = json.loads(response)

        # Route based on decision
        if decision["action"] == "solo":
            # Esper3.1 handles directly
            return {
                "executor": "esper31",
                "output": decision["output"]
            }

        elif decision["action"] == "delegate_trm":
            # Delegate to TRM
            trm_result = execute_trm(
                trm_input=decision["trm_input"],
                max_iterations=16
            )

            if trm_result["success"]:
                return {
                    "executor": "trm",
                    "output": trm_result["output"],
                    "iterations": trm_result["iterations"]
                }
            else:
                # Fallback to Esper3.1 if TRM fails
                return self.execute_solo_fallback(instruction, input_data)

        else:
            raise ValueError(f"Unknown action: {decision['action']}")

    def execute_solo_fallback(self, instruction: str, input_data: str) -> Dict:
        """Fallback to Esper3.1 solo execution."""
        prompt = f"""<|system|>
You are Esper3.1. Handle this task directly (TRM unavailable).
<|user|>
{instruction}
Input: {input_data}
<|assistant|>
"""

        response = generate(
            model=self.model,
            tokenizer=self.tokenizer,
            prompt=prompt,
            max_tokens=1024,
            temp=0.0
        )

        return {
            "executor": "esper31_fallback",
            "output": response
        }
```

---

## Phase 4: Testing & Validation (Week 3)

### 4.1 Unit Tests

**File**: `tests/test_esper31_trm.py`
```python
def test_solo_execution():
    """Test Esper3.1 solo execution (use_trm=0)."""
    executor = Esper31TRMExecutor(
        "models/gpt-oss-20b-esper31",
        "models/esper31-trm-qlora/adapters.safetensors"
    )

    result = executor.execute(
        "Read a JSON file and return its contents",
        "File: data/config.json"
    )

    assert result["executor"] == "esper31"
    assert "json.load" in result["output"]

def test_trm_delegation():
    """Test TRM delegation (use_trm=1)."""
    executor = Esper31TRMExecutor(...)

    result = executor.execute(
        "Find shortest path from A to C",
        "Graph: nodes A,B,C; edges A-B:3, B-C:2, A-C:8"
    )

    assert result["executor"] == "trm"
    assert result["iterations"] <= 16
    assert "path" in result["output"]

def test_trm_fallback():
    """Test fallback when TRM fails."""
    # ... test fallback logic
```

### 4.2 Integration Tests

**Benchmark**: Run on 200-example test set
- Expected delegation accuracy: >90%
- Expected TRM success rate: >85%
- Expected overall accuracy: >92%

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Delegation Accuracy** | >90% | % correct use_trm decisions |
| **TRM Success Rate** | >85% | % TRM executions completing successfully |
| **Overall Accuracy** | >92% | % tasks solved correctly (Esper31 or TRM) |
| **Latency** | <2s | Median task completion time |
| **Cost Savings** | >95% | vs GPT-5 remote (both models local) |

---

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Data Prep | `data/trm_delegation_labeled.jsonl` (1,700 examples) |
| 1-2 | Fine-Tuning | `models/esper31-trm-qlora/adapters.safetensors` (~200MB) |
| 2 | TRM Integration | `tools/trm_executor.py`, `tools/esper31_trm_executor.py` |
| 3 | Testing | `tests/test_esper31_trm.py` (100% pass), benchmark report |

**Total**: 2-3 weeks

---

## Cost Analysis

| Item | Cost |
|------|------|
| Data labeling (GPT-5, 1,102 examples) | $1.50 |
| Simple example generation (GPT-5, 500 examples) | $0.50 |
| Electricity (M4 Pro training, ~5 hours @ 30W) | $0.02 |
| **Total** | **~$2.00** |

**Monthly Savings** (after deployment):
- Before: 10K tasks × $4/1M tokens = $20/month (GPT-5 remote)
- After: 10K tasks × $0 = $0/month (both local)
- **Savings**: $20/month (100% reduction!)

**Payback**: Immediate (first month)

---

## Next Steps

1. ✅ Verify `trm:7m` is installed in Ollama
2. ✅ Run `scripts/label_trm_delegation.py` (cost: $1.50)
3. ✅ Fine-tune Esper3.1 with QLoRA (~2-3 hours)
4. ✅ Integrate TRM executor
5. ✅ Test and validate (benchmark report)

**Ready to proceed?**
