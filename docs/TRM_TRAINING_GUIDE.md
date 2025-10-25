# TRM-7M Training Pipeline: User Guide

**Complete guide to training your own TRM routing classifier from scratch**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Commands)](#quick-start)
3. [Phase-by-Phase Walkthrough](#phase-by-phase-walkthrough)
4. [Troubleshooting](#troubleshooting)
5. [Cost Breakdown](#cost-breakdown)
6. [Expected Results](#expected-results)

---

## Prerequisites

### Hardware Requirements
- **Minimum**: 32GB RAM, 8-core CPU
- **Recommended**: M4 Pro 48GB (or equivalent), 10-core CPU, 512GB SSD
- **GPU**: Not required for sampling/labeling, required for fine-tuning (Phase 6)

### Software Requirements
```bash
# Python 3.11 or higher
python --version  # Should be ≥3.11

# Install dependencies
pip install openai anthropic peft transformers torch datasets

# Verify installations
python -c "import openai, peft, transformers; print('✅ All dependencies installed')"
```

### API Keys
```bash
# OpenAI API key (for Phase 3 auto-labeling)
export OPENAI_API_KEY="sk-proj-..."

# Verify API key
python -c "from openai import OpenAI; OpenAI().models.list(); print('✅ API key valid')"
```

### Storage Requirements
- **Data**: 2GB (training examples + intermediate files)
- **Model**: 34GB (Qwen3-Coder-30B Q8_0 base + adapter)
- **Logs**: 500MB (shadow mode telemetry)
- **Total**: ~37GB free space

---

## Quick Start (5 Commands)

If you just want to execute the full pipeline end-to-end:

```bash
# 1. Verify dataset (already complete)
python -c "import json; print(f'{sum(1 for _ in open(\"data/training_examples_final.jsonl\"))} examples ready')"

# 2. Run stratified sampling (already complete)
ls -lh data/sample_500.jsonl  # Should show ~450KB

# 3. Auto-label with GPT-5 CODEX (requires API key, ~$0.15)
python scripts/auto_label_batch.py data/sample_500.jsonl data/auto_500.jsonl
# Wait 24 hours for batch completion

# 4. Human review (1-2 hours of manual work)
python scripts/manual_label_cli.py data/auto_500.jsonl data/labeled_500.jsonl

# 5. Merge and train (2-3 hours)
python scripts/merge_labels.py data/auto_500.jsonl data/labeled_500.jsonl learning/trm_labels.jsonl
python scripts/train_router.py learning/trm_labels.jsonl models/trm_router_lora/
```

**Done!** You now have a trained TRM router at `models/trm_router_lora/`.

---

## Phase-by-Phase Walkthrough

### Phase 1: Data Preparation (Complete ✅)

**What it does**: Verifies you have 1,102 curated training examples with no duplicates.

**Command**:
```bash
# Verify dataset exists
ls -lh data/training_examples_final.jsonl

# Check quality
python -c "
import json
examples = [json.loads(line) for line in open('data/training_examples_final.jsonl')]
print(f'✅ {len(examples)} examples loaded')
print(f'✅ All have instruction: {all(\"instruction\" in e or \"prompt\" in e for e in examples)}')
print(f'✅ All have output: {all(\"output\" in e or \"response\" in e for e in examples)}')
"
```

**Expected Output**:
```
✅ 1102 examples loaded
✅ All have instruction: True
✅ All have output: True
```

**What to do if it fails**: Re-run data extraction from previous sessions (see `scripts/dedupe_and_provenance.py`).

---

### Phase 2: Stratified Sampling (Complete ✅)

**What it does**: Selects 500 diverse examples across 7 task types for efficient labeling.

**Command**:
```bash
# Run stratified sampler
python scripts/stratified_sampler.py data/seed.dedup.jsonl data/sample_500.jsonl 500

# Verify diversity
cat data/sampling_report.json | python -m json.tool | grep -A 5 "strata_details"
```

**Expected Output**:
```
📊 Task Type Distribution:
   graph: 73 samples (14.6%)
   constraint: 70 samples (14.0%)
   optimization: 71 samples (14.2%)
   proof: 105 samples (21.0%)
   algorithm: 66 samples (13.2%)
   regex: 41 samples (8.2%)
   other: 74 samples (14.8%)
```

**Quality Checks**:
- All 7 task types represented (≥5% each)
- No single type >30%
- All 17 complexity keywords present

---

### Phase 3: Auto-labeling with GPT-5 CODEX

**What it does**: Uses OpenAI Batch API to classify 500 samples (TRM=1 vs standard=0).

#### Step 1: Verify API Key
```bash
echo $OPENAI_API_KEY  # Should start with "sk-proj-"
```

#### Step 2: Review Cost Estimate
```bash
python scripts/auto_label_batch.py data/sample_500.jsonl data/auto_500.jsonl

# You'll see:
# 💰 Cost Estimation:
#    Samples: 500
#    Input tokens: ~100,000
#    Output tokens: ~5,000
#    Total cost: $0.1250
#    Per sample: $0.000250
#
# Proceed with batch labeling? [y/N]:
```

#### Step 3: Submit Batch (Type 'y' to confirm)
```bash
# The script will:
# 1. Upload batch file to OpenAI
# 2. Submit batch job (returns batch ID)
# 3. Poll every 60 seconds for completion
# 4. Download results when ready (24 hours max)
```

**Output**:
```
✅ Batch job created: batch_abc123xyz
   Status: validating
   Completion window: 24 hours

⏳ Waiting for batch completion (polling every 60s)...
   Status: in_progress | Completed: 250/500
   Status: in_progress | Completed: 500/500
   Status: completed | Completed: 500/500

✅ Batch completed!
📥 Downloading batch results...
✅ Wrote 500 labeled examples to data/auto_500.jsonl

📊 Label Distribution:
   Label 0 (no TRM): 320 (64.0%)
   Label 1 (use TRM): 180 (36.0%)
```

**What to do if it fails**:
- **"Invalid API key"**: Check `OPENAI_API_KEY` environment variable
- **"Batch failed"**: Check `data/batch_input.jsonl` for malformed requests
- **"Timeout"**: Wait longer (batch API can take up to 24 hours)

---

### Phase 4: Human Review Protocol

**What it does**: Corrects auto-labeling errors via interactive terminal UI.

#### Step 1: Review Labeling Rubric
```bash
cat learning/labeling_rubric.md  # Read decision criteria
```

**Quick Decision Guide**:
- **Label 1 (TRM)**: Graph/DAG, SAT, CSP, proofs, edge case inference
- **Label 0 (Standard)**: File I/O, API calls, formatting, simple conditionals

#### Step 2: Run Interactive CLI
```bash
python scripts/manual_label_cli.py data/auto_500.jsonl data/labeled_500.jsonl

# You'll see:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Review Progress: 0/500 (0.0%)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Instruction: "Detect circular dependencies in this task graph..."
#
# Auto-label: 1 (use TRM)
#
# Options:
#   Y - Confirm (agree with auto-label)
#   N - Flip label (0 → 1 or 1 → 0)
#   S - Skip (uncertain, review later)
#   Q - Quit (saves progress)
#
# Your choice: █
```

#### Step 3: Review in Batches
**Recommended**: Review 50-100 samples per session (prevents fatigue).

```bash
# Auto-save happens every 10 reviews
# Progress saved to data/labeled_500.jsonl.progress
```

#### Step 4: Verify Coverage
```bash
wc -l data/labeled_500.jsonl
# Should show 500 lines (or less if you skipped some)
```

**Time Estimate**: 1-2 hours (15-20 seconds per review)

**What to do if unsure**:
- Press 'S' to skip (can review later)
- Check `learning/labeling_rubric.md` for examples
- When in doubt, prefer **label=0** (false negatives less harmful than false positives)

---

### Phase 5: Training Data Production

**What it does**: Merges auto-labels + human reviews, validates quality.

#### Step 1: Merge Labels
```bash
python scripts/merge_labels.py \
    data/auto_500.jsonl \
    data/labeled_500.jsonl \
    learning/trm_labels.jsonl

# Output:
# ✅ Merged 500 labels
#    Auto-only: 200
#    Human-reviewed: 300
#    Agreement rate: 88.7%
#
# 📊 Final Label Distribution:
#    Label 0 (no TRM): 312 (62.4%)
#    Label 1 (use TRM): 188 (37.6%)
```

#### Step 2: Validate Quality
```bash
python scripts/validate_training_data.py learning/trm_labels.jsonl

# Quality Report:
# ✅ Balance: 62.4% / 37.6% (within 30-70% range)
# ✅ Diversity: All 17 keywords represented
# ✅ Schema: All required fields present
# ✅ No data leakage detected
```

**What to watch for**:
- **Imbalance** (>90% one class): Need more diverse samples
- **Missing keywords**: Low coverage for certain task types
- **Data leakage**: Test data in training set (resampling required)

---

### Phase 6: LoRA Fine-tuning

**What it does**: Fine-tunes Qwen3-Coder-30B with LoRA for TRM routing.

#### Step 1: Download Base Model
```bash
# Option 1: Direct from Ollama (recommended)
ollama pull hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0

# Option 2: HuggingFace (if Ollama unavailable)
python -c "
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('Qwen/Qwen3-Coder-30B', load_in_8bit=True)
print('✅ Model downloaded')
"
```

#### Step 2: Configure Training
```bash
cat << 'EOF' > learning/training_config.json
{
  "base_model": "hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0",
  "lora_rank": 8,
  "lora_alpha": 16,
  "learning_rate": 2e-4,
  "batch_size": 4,
  "epochs": 3,
  "warmup_steps": 50,
  "gradient_accumulation_steps": 2,
  "max_seq_length": 512
}
EOF
```

#### Step 3: Run Training
```bash
python scripts/train_router.py \
    learning/trm_labels.jsonl \
    models/trm_router_lora/ \
    --config learning/training_config.json

# Training Progress:
# Epoch 1/3: 100%|████████| 100/100 [08:32<00:00,  5.12s/it]
# Val Loss: 0.234 | Val Acc: 89.2%
#
# Epoch 2/3: 100%|████████| 100/100 [08:31<00:00,  5.11s/it]
# Val Loss: 0.198 | Val Acc: 91.5%
#
# Epoch 3/3: 100%|████████| 100/100 [08:30<00:00,  5.10s/it]
# Val Loss: 0.182 | Val Acc: 92.8%
#
# ✅ Training complete!
#    Final accuracy: 92.8%
#    Saved to: models/trm_router_lora/
```

**Time Estimate**: 1-2 hours on M4 Pro 48GB

**What to do if it fails**:
- **OOM (Out of Memory)**: Reduce `batch_size` to 2 or 1
- **Slow training**: Increase `gradient_accumulation_steps` to 4
- **Overfitting** (val loss increases): Reduce `epochs` to 2

---

### Phase 7: Shadow Mode Deployment

**What it does**: Runs TRM router in parallel with production for 1 week validation.

#### Step 1: Enable Shadow Mode
```bash
# Update environment
export USE_TRM_ROUTER=true
export TRM_SHADOW_MODE=true  # Logs discrepancies without changing behavior

# Restart Agency
python agency.py
```

#### Step 2: Monitor Telemetry
```bash
# Check agreement rate
python scripts/shadow_mode_dashboard.py

# Dashboard (updates every 24 hours):
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Shadow Mode Week 1 Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tasks evaluated: 1,247
# Agreement rate: 87.3% (1,089/1,247)
# TRM precision: 0.91 (182/200)
# TRM recall: 0.84 (182/217)
#
# Discrepancies by type:
#   False positives: 18 (TRM said 1, production said 0)
#   False negatives: 35 (TRM said 0, production said 1)
```

#### Step 3: Review Discrepancies
```bash
# View detailed discrepancy log
cat logs/shadow_mode/routing_deltas.jsonl | python -m json.tool | less

# Example discrepancy:
# {
#   "task_id": "phase_3_task_5",
#   "instruction": "Parse JSON and format output",
#   "trm_label": 1,
#   "production_label": 0,
#   "trm_confidence": 0.73,
#   "timestamp": "2025-10-25T14:32:00Z"
# }
```

**Target**: 85%+ agreement rate before promotion to production

**What to do if agreement <85%**:
- Collect discrepancies as new training data
- Have human expert review false positives/negatives
- Retrain with augmented dataset (see Phase 6)

---

### Phase 8: Production Integration

**What it does**: Promotes TRM router to production (replaces Leap 3 for reasoning tasks).

#### Step 1: Disable Shadow Mode
```bash
export TRM_SHADOW_MODE=false  # Now affects production routing
```

#### Step 2: Update Model Policy
```python
# shared/model_policy.py already updated by Phase 8 tasks
# Just verify integration:

python -c "
from shared.model_policy import should_use_trm
result = should_use_trm('Detect circular dependencies in task graph')
print(f'TRM routing: {result.label} (confidence: {result.confidence})')
"

# Output:
# TRM routing: 1 (confidence: 0.94)
```

#### Step 3: Monitor Production
```bash
# Check TRM usage in production
grep "trm_router" logs/telemetry/daily_*.jsonl | wc -l

# Track cost savings
python scripts/calculate_savings.py logs/telemetry/daily_*.jsonl

# Cost Comparison (Month 1):
#   Without TRM: $1,600 (Leap 3 only)
#   With TRM: $800 (50% reduction on reasoning tasks)
```

---

## Troubleshooting

### Common Issues

#### Issue: "Script not found: auto_label_batch.py"
**Solution**:
```bash
# Verify you're in Agency root directory
pwd  # Should be /path/to/Agency

# Check script exists
ls scripts/auto_label_batch.py

# If missing, re-run Phase 3 task creation
```

#### Issue: "Batch API returns empty results"
**Solution**:
```bash
# Check batch status manually
python -c "
from openai import OpenAI
client = OpenAI()
batch = client.batches.retrieve('batch_YOUR_ID_HERE')
print(f'Status: {batch.status}')
print(f'Errors: {batch.errors}')
"
```

#### Issue: "Training OOM (Out of Memory)"
**Solution**:
```bash
# Reduce batch size in training config
cat learning/training_config.json | \
  python -c "import sys, json; d=json.load(sys.stdin); d['batch_size']=1; print(json.dumps(d, indent=2))" \
  > learning/training_config.json.tmp && \
  mv learning/training_config.json.tmp learning/training_config.json

# Increase gradient accumulation (maintains effective batch size)
# Set gradient_accumulation_steps=8 (4x batch_size reduction → 8x accumulation)
```

#### Issue: "Agreement rate stuck at 70%"
**Solution**:
```bash
# Collect discrepancies for retraining
python scripts/collect_discrepancies.py \
    logs/shadow_mode/routing_deltas.jsonl \
    learning/discrepancies_for_retraining.jsonl

# Have human expert review
python scripts/manual_label_cli.py \
    learning/discrepancies_for_retraining.jsonl \
    learning/discrepancies_labeled.jsonl

# Merge with original training data
python scripts/merge_labels.py \
    learning/trm_labels.jsonl \
    learning/discrepancies_labeled.jsonl \
    learning/trm_labels_v2.jsonl

# Retrain with augmented dataset
python scripts/train_router.py \
    learning/trm_labels_v2.jsonl \
    models/trm_router_lora_v2/
```

---

## Cost Breakdown

### One-Time Costs

| Phase | Item | Cost |
|-------|------|------|
| Phase 3 | OpenAI Batch API (500 samples) | $0.10-0.15 |
| Phase 4 | Human review time (1-2 hours) | Free (your time) |
| Phase 6 | Electricity (M4 Pro 2 hours @ 40W) | $0.01 |
| **Total** | **One-time setup** | **~$0.15** |

### Recurring Savings

| Scenario | Monthly Cost | Savings vs Leap 3 |
|----------|-------------|-------------------|
| Leap 3 Only (Status Quo) | $1,600 | Baseline |
| Leap 3 + TRM Router (Shadow Mode) | $1,600 | $0 (no impact) |
| Leap 3 + TRM Router (Production) | $800 | $800/month (50% reduction) |

**ROI**: One-time cost of $0.15 pays back in <1 day of production usage.

---

## Expected Results

### After Phase 2 (Stratified Sampling)
- ✅ 500 diverse samples across 7 task types
- ✅ All 17 complexity keywords represented
- ✅ Max task type <22% (good diversity)

### After Phase 3 (Auto-labeling)
- ✅ 500 auto-labeled samples
- ✅ Label distribution: 60-70% standard, 30-40% TRM
- ✅ Cost: ~$0.10-0.15

### After Phase 4 (Human Review)
- ✅ 85-95% agreement with auto-labels (indicates good prompt quality)
- ✅ Human corrections: 5-15% of samples

### After Phase 6 (Fine-tuning)
- ✅ Validation accuracy: 85-95%
- ✅ Precision: 0.85-0.95
- ✅ Recall: 0.80-0.90
- ✅ Training time: 1-2 hours

### After Phase 7 (Shadow Mode Week 1)
- 🎯 Agreement rate: 85-90% (target ≥85%)
- 🎯 False positive rate: <10%
- 🎯 False negative rate: <15%

### After Phase 8 (Production Month 1)
- 🎯 Cost reduction: 50% ($1,600 → $800/month)
- 🎯 Latency improvement: 5s → <1s (10x faster)
- 🎯 Churn reduction: 40-60% (fewer test cycles)

---

## Next Steps

After completing all 9 phases:

1. **Monitor production metrics** (cost, latency, accuracy)
2. **Review shadow mode logs weekly** (look for drift)
3. **Retrain every 3-6 months** (or when agreement <85%)
4. **Contribute improvements** to Agency repo

---

## Support

- **Documentation**: `docs/adr/ADR-034-trm-training-pipeline.md`
- **Issues**: https://github.com/anthropics/Agency/issues
- **Slack**: #agency-trm-training (internal)

---

**Happy Training!** 🎯

*Last Updated: 2025-10-24*
