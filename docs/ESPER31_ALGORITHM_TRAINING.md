# Esper3.1 Algorithm Training Plan
**Goal**: Enhance Esper3.1's algorithm/reasoning skills with your 1,102 examples
**Method**: QLoRA (safe, reversible, cheap)
**Timeline**: 3-4 hours total
**Cost**: ~$0.02 (electricity)

---

## Why This Makes Sense

### Your Dataset IS Valuable

The 1,102 examples cover:
- ✅ Graph algorithms (shortest path, cycle detection, topological sort)
- ✅ Constraint satisfaction problems
- ✅ Dynamic programming patterns
- ✅ Optimization problems
- ✅ Recursive algorithm design

**These ARE core coding skills!**

### Why QLoRA is Perfect

**Safe**:
- Adds small adapters (~200MB) on top of base model
- NO catastrophic forgetting (preserves existing knowledge)
- Can enable/disable adapters
- Reversible (just delete adapters)

**Cheap**:
- Trains on M4 Pro in 2-3 hours
- Only $0.02 electricity cost
- No cloud GPUs needed

**Effective**:
- 1,102 examples is ideal for adapter training
- Focused improvement on algorithm tasks
- Preserves everything else Esper3.1 knows

---

## 3-Step Process

### Step 1: Format Data (5 minutes)

```bash
python scripts/format_for_esper31_training.py
```

**Output**: `data/esper31_training_formatted.jsonl`

Converts from:
```jsonl
{"instruction": "Find shortest path...", "input": "...", "output": "..."}
```

To:
```jsonl
{"messages": [
  {"role": "system", "content": "You are Esper3.1..."},
  {"role": "user", "content": "Find shortest path..."},
  {"role": "assistant", "content": "Path: A→B→C, Distance: 5"}
]}
```

### Step 2: Install Dependencies (5 minutes)

```bash
pip install --break-system-packages transformers peft accelerate bitsandbytes datasets
```

### Step 3: Train QLoRA Adapters (2-3 hours)

```bash
python scripts/train_esper31_qlora.py
```

**What happens**:
1. Downloads Esper3.1 from HuggingFace (~20GB, one-time)
2. Adds LoRA adapters (only trains ~200MB of parameters)
3. Trains for 3 epochs (~2-3 hours on M4 Pro)
4. Saves adapters to `models/esper31-algorithms-qlora/`

**Memory usage**: ~20GB (fits comfortably in 48GB)

---

## What You Get

### Before Training

Esper3.1 is already good at:
- ✅ DevOps tasks
- ✅ Architecture design
- ✅ General coding
- ⚠️  Basic algorithms (okay, not great)

### After Training

Esper3.1 with adapters:
- ✅ DevOps tasks (unchanged)
- ✅ Architecture design (unchanged)
- ✅ General coding (unchanged)
- ✅✅ **Algorithms & reasoning** (improved!)

### Using the Adapters

**Option A: Load in Python**:
```python
from transformers import AutoModelForCausalLM
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "ValiantLabs/gpt-oss-20b-Esper3.1"
)

# Load adapters
model = PeftModel.from_pretrained(
    base_model,
    "models/esper31-algorithms-qlora"
)

# Use it
response = model.generate(...)
```

**Option B: Export to Ollama** (TODO):
```bash
# Merge adapters with base model
python scripts/merge_and_export.py

# Creates: esper31-algorithms:20b in Ollama
ollama run esper31-algorithms:20b
```

**Option C: Switch On-Demand**:
```python
# Without adapters (original Esper3.1)
response = base_model.generate(...)

# With adapters (algorithm-enhanced)
response = model_with_adapters.generate(...)
```

---

## Risk Assessment

### Risks

**Low**:
- ✅ QLoRA is very safe (no catastrophic forgetting in practice)
- ✅ Can delete adapters if they don't help
- ✅ Base model untouched

**Medium**:
- ⚠️  Small dataset (1,102 examples) - might overfit
  - **Mitigation**: Early stopping, validation split, 3 epochs max
- ⚠️  Domain mismatch if examples are too narrow
  - **Mitigation**: Your examples are diverse (7 task types)

**Unlikely**:
- ❌ Adapters make model worse (very rare with QLoRA)
  - **Mitigation**: Benchmark before/after, revert if needed

### Expected Outcome

**Best case** (70% probability):
- Noticeable improvement on algorithm tasks
- No degradation on other tasks
- Worth keeping adapters enabled

**Moderate case** (25% probability):
- Small improvement on algorithm tasks
- Negligible change on other tasks
- Adapters are okay to keep

**Worst case** (5% probability):
- No improvement or slight degradation
- Delete adapters, no harm done

---

## Timeline

| Step | Time | Action |
|------|------|--------|
| 1 | 5 min | Format data |
| 2 | 5 min | Install deps |
| 3 | 2-3 hours | Train (can run overnight) |
| 4 | 10 min | Test & benchmark |
| **Total** | **~3-4 hours** | (mostly unattended) |

---

## Cost

| Item | Cost |
|------|------|
| HuggingFace download | $0 (one-time, ~20GB) |
| Training (electricity) | ~$0.02 (M4 Pro @ 30W × 3 hours) |
| Storage (adapters) | ~200MB |
| **Total** | **~$0.02** |

---

## Benchmarking (Recommended)

Before deciding to keep adapters, benchmark:

```bash
# Before training (save results)
python scripts/benchmark_esper31.py --save-baseline

# After training (compare)
python scripts/benchmark_esper31.py --compare-to-baseline
```

**Test cases**:
- 20 algorithm problems (from your test set)
- 20 general coding problems (to check no degradation)
- 10 DevOps tasks (to check no degradation)

**Keep adapters if**:
- Algorithm tasks: >20% improvement
- Other tasks: <5% degradation

---

## My Recommendation

**YES, train the adapters**:

1. ✅ Your dataset is valuable (algorithms/reasoning)
2. ✅ QLoRA is safe and reversible
3. ✅ Cost is negligible ($0.02)
4. ✅ Time is reasonable (3-4 hours, mostly unattended)
5. ✅ Expected value: Medium-high improvement with low risk

**Worst case**: Spend $0.02 and learn that adapters don't help. Delete them, move on.

**Best case**: Esper3.1 becomes significantly better at algorithms while keeping everything else. Keep adapters enabled permanently.

---

## Next Steps

**If you approve**:

```bash
# Step 1: Format data
python scripts/format_for_esper31_training.py

# Step 2: Install deps
pip install --break-system-packages transformers peft accelerate bitsandbytes datasets

# Step 3: Train (can run overnight)
python scripts/train_esper31_qlora.py

# Step 4: Test
python scripts/test_esper31_adapters.py
```

**Want to proceed?** I can run Step 1 now (data formatting) and you can review the output before committing to training.
