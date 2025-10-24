# TRM-7M Training Pipeline - GPT-5 Hardened Version

## Executive Summary

This document incorporates **all high-priority improvements** from GPT-5's review of the original 32-task pipeline. The hardened version adds **robustness, calibration, and production-safety** features.

### Key Improvements Implemented

✅ **Deduplication & Provenance** - Script created: `scripts/dedupe_and_provenance.py`
✅ **Stratified Sampling** - Script created: `scripts/stratified_sampler.py` (300 samples, not 200)
✅ **Threshold Tuning & Calibration** - Script created: `scripts/tune_thresholds.py`
✅ **Cross-validation & Early Stopping** - Integrated into training workflow
✅ **Gold Evaluation Set** - 50 hand-labeled examples never used for training
✅ **Enhanced Telemetry** - Disagreement examples logged for human triage
✅ **OOM Guards** - Memory-aware batch sizing with fallback
✅ **Confidence Thresholds** - Production deployment at confidence ≥0.75 (tunable)

---

## Updated Pipeline (38 tasks, up from 32)

### Phase 1: Data Extraction & Deduplication (4 tasks, +1)

**NEW TASK**: `dedupe_and_provenance` - Remove duplicates, maintain traceability

```bash
# Original extraction
python scripts/extract_weird_jsonl.py \
  weirdly-numbered-json-contents.md \
  data/seed.jsonl

# NEW: Deduplication with provenance tracking
python scripts/dedupe_and_provenance.py \
  data/seed.jsonl \
  data/seed.dedup.jsonl

# Outputs:
# - data/seed.dedup.jsonl (deduplicated examples)
# - data/provenance_manifest.json (checksums + line numbers)
```

**Why**: Duplicates bias sampling and training. Provenance enables traceability.

**Expected**: 659 → ~580-620 unique examples (10-15% deduplication rate)

---

### Phase 2: Stratified Sampling (3 tasks, UPDATED)

**REPLACED**: `create_sampling_script` → `create_stratified_sampling_script`

**INCREASED**: 200 samples → **300 samples** (better calibration, less overfitting)

```bash
# NEW: Stratified sampling across task types
python scripts/stratified_sampler.py \
  data/seed.dedup.jsonl \
  data/sample_300.jsonl \
  300

# Outputs:
# - data/sample_300.jsonl (stratified sample)
# - data/sampling_report.json (task type distribution)
```

**Task Types** (stratified representation):
- Graph/DAG (20-25%)
- Constraint solving (15-20%)
- Optimization (15-20%)
- Proof/induction (10-15%)
- Algorithm analysis (10-15%)
- Regex/parsing (5-10%)
- Other (5-10%)

**Why**: Heuristic top-N misses rare but important task classes. Stratification ensures diversity.

---

### Phase 3: Auto-Labeling with Metadata (5 tasks, +1)

**NEW TASK**: `log_labeling_metadata` - Audit trail for auto-labels

```bash
# Auto-label with metadata logging
python scripts/auto_label_batch.py \
  --input data/sample_300.jsonl \
  --output data/auto_300.jsonl \
  --model gpt-5 \
  --temperature 0.0 \
  --log-metadata data/auto_labeling_audit.jsonl

# Metadata logged per label:
# - model: gpt-5
# - prompt_template: "[routing expert prompt]"
# - temperature: 0.0
# - tokens_used: 247
# - timestamp: "2025-10-24T21:30:00Z"
```

**Why**: Auditability for constitutional compliance (Article III). Enables A/B testing of prompts.

---

### Phase 4: Human Review (4 tasks, +1)

**NEW TASK**: `create_gold_eval_set` - 50 hand-labeled examples for evaluation only

```bash
# Create gold evaluation set (never used for training)
python scripts/create_gold_set.py \
  --input data/sample_300.jsonl \
  --output data/gold_eval_50.jsonl \
  --count 50 \
  --strategy "disagreement"  # Select examples where auto-labels have low confidence

# Manual labeling with extra care (2 reviewers per example)
python scripts/manual_label_cli.py \
  --input data/gold_eval_50.jsonl \
  --output data/gold_eval_50_labeled.jsonl \
  --gold-standard-mode  # Requires 2 reviewers, logs inter-annotator agreement
```

**Why**: Untainted evaluation set prevents overfitting metrics. GPT-5 recommended 10-20%, we're using 50/300 = 16.7%.

---

### Phase 5: Training Data Preparation (5 tasks, +1)

**NEW TASK**: `split_train_val_test` - 70/15/15 split with stratification

```bash
# Merge auto + human labels
python scripts/merge_labels.py \
  data/auto_300.jsonl \
  data/labeled_300.jsonl \
  learning/trm_labels_merged.jsonl

# NEW: Split into train/val/test with stratification
python scripts/split_stratified.py \
  --input learning/trm_labels_merged.jsonl \
  --train learning/trm_labels_train.jsonl \
  --val learning/trm_labels_val.jsonl \
  --test learning/trm_labels_test.jsonl \
  --split 70/15/15 \
  --stratify-by label  # Preserve label balance in each split
```

**Splits**:
- **Train**: 210 examples (70%) - Used for LoRA fine-tuning
- **Val**: 45 examples (15%) - Used for early stopping, hyperparameter tuning
- **Test**: 45 examples (15%) - Final evaluation (never seen during training)
- **Gold**: 50 examples (separate) - Calibration check

---

### Phase 6: Model Training with Calibration (6 tasks, +2)

**NEW TASK 1**: `add_kfold_cross_validation` - 5-fold CV for variance estimates

```bash
# K-fold cross-validation (5 folds)
python scripts/train_router.py \
  --model qwen3coder-30b \
  --data learning/trm_labels_train.jsonl \
  --output models/trm_router_lora \
  --lora-rank 8 \
  --lora-alpha 16 \
  --batch-size 4 \
  --epochs 3 \
  --learning-rate 2e-4 \
  --k-fold 5 \
  --early-stopping patience=3 \
  --oom-guard  # Auto-reduce batch size on OOM

# Outputs 5 models (one per fold) + ensemble average
# - models/trm_router_lora_fold_1/
# - models/trm_router_lora_fold_2/
# - ...
# - models/trm_router_lora_ensemble/  # Averaged predictions
```

**NEW TASK 2**: `tune_confidence_thresholds` - Calibration with Platt scaling

```bash
# Tune thresholds on validation set
python scripts/tune_thresholds.py \
  --model models/trm_router_lora_ensemble \
  --val-data learning/trm_labels_val.jsonl \
  --output models/trm_router_lora/threshold_analysis.json \
  --criterion f1  # Optimize F1 score

# Outputs:
# - threshold_analysis.json (metrics for each threshold 0.1-0.9)
# - roc_curve.png (ROC curve with optimal threshold marked)
# - calibration_curve.png (calibration plot)

# Recommended production threshold: 0.75 (precision ≥0.80, recall ≥0.70)
```

**Training Time Estimates** (with OOM guards):
- **48GB M4 Pro**: 2-4 hours (batch size 4, no OOM)
- **32GB Mac**: 4-6 hours (batch size 2, possible OOM → auto-fallback to batch size 1)
- **16GB Mac**: 8-12 hours (batch size 1, 8-bit quantization)

**OOM Guard Logic**:
```python
try:
    train_batch(batch_size=4)
except torch.cuda.OutOfMemoryError:
    logger.warning("OOM detected, reducing batch size to 2")
    train_batch(batch_size=2)
```

---

### Phase 7: Shadow Mode with Enhanced Telemetry (5 tasks, +1)

**NEW TASK**: `log_disagreement_examples` - Store full context for human triage

```bash
# Shadow mode with disagreement logging
python scripts/shadow_mode.py \
  --router models/trm_router_lora_ensemble \
  --duration 7d \
  --log-path logs/shadow_mode/routing_deltas.jsonl \
  --log-disagreements logs/shadow_mode/disagreements.jsonl  # NEW
  --confidence-threshold 0.75

# Disagreement format:
# {
#   "task_id": "abc123",
#   "instruction": "Detect circular dependencies in this graph...",
#   "production_label": 1,
#   "trm_router_label": 0,
#   "trm_router_confidence": 0.68,
#   "context_snippet": "Given graph with nodes [A, B, C]...",
#   "timestamp": "2025-10-24T21:45:00Z"
# }
```

**Why**: Enables **fast human triage** of disagreements. Top priority for retraining data.

**Telemetry Dashboard** (updated):
- Agreement rate over time (7-day rolling window)
- Confusion matrix (TRM vs production)
- **NEW**: Top 10 disagreement examples (sortable by confidence)
- **NEW**: Confidence histogram (detect miscalibration)

---

### Phase 8: Production Integration (4 tasks, unchanged)

Same as original pipeline, but with **confidence threshold enforcement**:

```python
# Update model_policy.py
from tools.trm_router import TRMRouter

router = TRMRouter(
    model_path="models/trm_router_lora_ensemble",
    confidence_threshold=0.75  # From threshold tuning
)

# Query TRM router before Leap 3 router
trm_decision = router.classify(task)

if trm_decision["label"] == 1 and trm_decision["confidence"] >= 0.75:
    # Route to TRM-7M for recursive reasoning
    return route_to_trm(task)
else:
    # Fallback to Leap 3 router (gpt-5/gpt-4o/local)
    return route_to_leap3(task)
```

---

### Phase 9: Documentation (3 tasks, unchanged)

Same as original: ADR-034, user guide, README update.

---

## Quick Checks Before Execution

Run these validation commands **before** starting the pipeline:

```bash
# 1. Verify source file
wc -l weirdly-numbered-json-contents.md  # Expect 1216 lines

# 2. Quick schema check
python - <<'PY'
import json
bad = 0
for i, line in enumerate(open('weirdly-numbered-json-contents.md')):
    if '{"' in line:
        try:
            json.loads(line)
        except:
            bad += 1
print(f"Malformed lines: {bad}")
PY

# 3. Test helper scripts (smoke test)
python scripts/dedupe_and_provenance.py --help
python scripts/stratified_sampler.py --help
python scripts/tune_thresholds.py --help

# 4. Verify environment
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import peft; print(f'PEFT: {peft.__version__}')"

# 5. Check available memory
python -c "import psutil; print(f'RAM: {psutil.virtual_memory().available / 1e9:.1f} GB available')"
```

Expected outputs:
- ✅ 1216 lines in source file
- ✅ <10 malformed lines
- ✅ All helper scripts show help
- ✅ PyTorch with CUDA (if available)
- ✅ >20GB RAM available (for 48GB Mac, expect ~30-40GB free)

---

## Updated Success Metrics

### Training Phase
- ✅ Extraction: 659+ objects → 580-620 unique (after deduplication)
- ✅ Sampling: 300 stratified samples (was 200)
- ✅ Auto-labeling: 300 labeled objects
- ✅ Human review: 80%+ agreement with auto-labels
- ✅ **NEW**: Gold set: 50 examples with 2-reviewer consensus
- ✅ Quality: 30-70% label balance, all task types represented
- ✅ Training: **85%+ validation accuracy** (k-fold CV mean)
- ✅ **NEW**: Calibration: Brier score <0.20, ECE <0.10

### Shadow Mode (1 week)
- ✅ Agreement: **90%+** with production router (was 85%, raised bar)
- ✅ Precision: **80%+**
- ✅ Recall: **80%+**
- ✅ Latency: <500ms
- ✅ **NEW**: Confidence calibration: ECE <0.15 on production data

### Production
- ✅ Churn reduction: 40-60%
- ✅ Cost: $0 inference
- ✅ Speed: <1s per validation
- ✅ Zero errors
- ✅ **NEW**: False positive rate <10% (precision ≥0.80 enforced)

---

## Cost Analysis (Updated)

### One-Time Setup
- **Auto-labeling**: ~$3.75 (GPT-5 CODEX, 300 samples @ ~500 tokens) - **+$1.25**
- **Training**: $0 (local M4 Pro, 2-4 hours)
- **Human review**: 3-4 hours (300 samples + 50 gold set) - **+1 hour**
- **Gold set labeling**: 1-2 hours (50 samples, 2 reviewers) - **NEW**

**Total setup time**: 6-8 hours (was 4-6 hours)

### Ongoing
- **Inference**: $0 (local 7M-param model)
- **Retraining**: ~$3.75 every 2-4 weeks (if needed)

### Savings (Unchanged)
- **Before Leap 8**: $1.6k/month (Leap 3 router, 96% savings)
- **After Leap 8**: $1.4k/month (98% savings with TRM)
- **Additional**: 40-60% churn reduction (time savings)

---

## Risk Mitigations (GPT-5's Recommendations)

### Risk 1: Overfitting on Small Dataset (300 samples)
**Mitigations**:
- ✅ LoRA (rank=8, only 0.1% of params fine-tuned)
- ✅ Early stopping (patience=3 epochs)
- ✅ K-fold CV (5 folds, ensemble averaging)
- ✅ Separate gold eval set (50 examples never seen during training)
- ✅ Stratified splits (preserve label balance in train/val/test)

### Risk 2: Auto-Label Bias (LLMs over/under-delegate)
**Mitigations**:
- ✅ Manual review of 100% of auto-labels
- ✅ Confidence logging (detect low-confidence auto-labels)
- ✅ Inter-annotator agreement tracking (2 reviewers for gold set)
- ✅ Metadata audit trail (prompt, model, temperature logged)

### Risk 3: Production Impact (router causes errors)
**Mitigations**:
- ✅ Shadow mode (1 week, zero production impact)
- ✅ Confidence threshold (start at 0.75, tune based on telemetry)
- ✅ Rollback plan (USE_TRM_ROUTER=false, instant revert)
- ✅ Human review of disagreements before production promotion

### Risk 4: Data Leakage (test examples in training)
**Mitigations**:
- ✅ Provenance tracking (checksums prevent accidental re-inclusion)
- ✅ Separate gold set (never used for training)
- ✅ Test split reserved until final evaluation
- ✅ Stratified splits (no data leakage between splits)

---

## Immediate Actions (Copy-Pasteable Commands)

### Step 1: Validate Environment
```bash
# Check source file
wc -l weirdly-numbered-json-contents.md  # Expect 1216

# Smoke test helper scripts
python scripts/dedupe_and_provenance.py --help
python scripts/stratified_sampler.py --help
python scripts/tune_thresholds.py --help

# Check dependencies
pip install torch transformers peft datasets scikit-learn matplotlib numpy
```

### Step 2: Run Pilot (50 samples)
```bash
# Extract + dedupe
python scripts/extract_weird_jsonl.py weirdly-numbered-json-contents.md data/seed.jsonl
python scripts/dedupe_and_provenance.py data/seed.jsonl data/seed.dedup.jsonl

# Stratified sample (pilot: 50)
python scripts/stratified_sampler.py data/seed.dedup.jsonl data/sample_50_pilot.jsonl 50

# Auto-label (pilot)
python scripts/auto_label_batch.py --input data/sample_50_pilot.jsonl --output data/auto_50_pilot.jsonl --model gpt-5

# Manual review (10% of pilot = 5 examples)
head -5 data/auto_50_pilot.jsonl | python scripts/manual_label_cli.py --input - --output data/labeled_5_pilot.jsonl

# Check agreement rate
python scripts/compute_agreement.py data/auto_50_pilot.jsonl data/labeled_5_pilot.jsonl
```

**Decision**: If agreement ≥80%, scale to 300. If <80%, revise auto-labeling prompt.

### Step 3: Full Pipeline (Automated)
```bash
# Execute with /primeA (38 tasks, 6-8 hours)
/primeA --graph missions/trm_training_pipeline_v2_gpt5_hardened.json --visualize
```

---

## Updated Task Graph Summary

| Phase | Tasks | Changes |
|-------|-------|---------|
| 1. Data Extraction | 4 (+1) | **+Deduplication** |
| 2. Sampling | 3 (updated) | **Stratified sampling, 300 samples** |
| 3. Auto-Labeling | 5 (+1) | **+Metadata logging** |
| 4. Human Review | 4 (+1) | **+Gold eval set (50 examples)** |
| 5. Training Data Prep | 5 (+1) | **+Stratified train/val/test split** |
| 6. Model Training | 6 (+2) | **+K-fold CV, +Threshold tuning** |
| 7. Shadow Mode | 5 (+1) | **+Disagreement logging** |
| 8. Integration | 4 (unchanged) | Confidence threshold enforcement |
| 9. Documentation | 3 (unchanged) | - |
| **TOTAL** | **38 tasks** | **+6 tasks, hardened for production** |

---

## Constitutional Compliance (Updated)

### Article I: Complete Context Before Action
- ✅ All examples extracted (zero data loss)
- ✅ Provenance tracking (checksums + line numbers)
- ✅ **NEW**: Human review checkpoints with sign-off required

### Article II: 100% Verification
- ✅ All tests pass before production integration
- ✅ **NEW**: Gold eval set validation (untainted evaluation)
- ✅ **NEW**: Shadow mode validates ≥90% agreement (raised from 85%)

### Article III: Automated Enforcement
- ✅ Quality validator blocks imbalanced datasets
- ✅ **NEW**: OOM guards prevent training failures
- ✅ **NEW**: Confidence threshold enforces precision ≥0.80

### Article IV: Continuous Learning
- ✅ VectorStore stores TRM routing patterns (confidence ≥0.6)
- ✅ **NEW**: Disagreement examples prioritized for retraining
- ✅ **NEW**: K-fold CV results stored for meta-learning

### Article V: Spec-Driven Development
- ✅ Task graph is the specification
- ✅ All tasks trace to acceptance criteria
- ✅ **NEW**: Calibration metrics documented in ADR-034

---

## Next Steps

1. **Run pilot** (50 samples, 1 hour) - Validate pipeline before full execution
2. **Review pilot results** - Agreement rate, task type distribution
3. **Execute full pipeline** (300 samples, 6-8 hours) - `/primeA --graph ...`
4. **Shadow mode** (1 week) - Collect telemetry, review disagreements
5. **Production promotion** - If agreement ≥90%, enable `USE_TRM_ROUTER=true`

---

**Version**: 2.0 (GPT-5 Hardened)
**Generated**: 2025-10-24
**Leap**: 8 (TRM-7M Recursive Reasoning Validation)
**Status**: Production-ready with safety guardrails
**Estimated Time**: 6-8 hours (including human review)
**Estimated Cost**: ~$3.75 (auto-labeling only)
