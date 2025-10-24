# TRM-7M Training Pipeline - Production Deployment Guide

## Complete Autonomous Learning Loop

**Status**: ✅ Production-Ready with Continuous Learning
**Version**: 3.0 (GPT-5 Hardened + Automation)
**Date**: 2025-10-24

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Initial Training & Deployment](#initial-training--deployment)
3. [Continuous Learning Automation](#continuous-learning-automation)
4. [Monitoring & Maintenance](#monitoring--maintenance)
5. [Troubleshooting](#troubleshooting)
6. [Cost & Performance](#cost--performance)

---

## Quick Start

**One-command deployment** (from scratch to production):

```bash
# 1. Train initial model (6-8 hours)
/primeA --graph missions/trm_training_pipeline.json --visualize

# 2. Deploy to shadow mode (1 week)
python scripts/shadow_mode.py --router models/trm_router_lora --duration 7d

# 3. Setup automation (5 minutes)
bash scripts/setup_retraining_cron.sh

# 4. Enable production routing
echo "USE_TRM_ROUTER=true" >> .env
```

---

## Initial Training & Deployment

### Phase 1: Data Preparation (30 minutes)

```bash
# Extract & deduplicate
python scripts/extract_weird_jsonl.py \
  weirdly-numbered-json-contents.md \
  data/seed.jsonl

python scripts/dedupe_and_provenance.py \
  data/seed.jsonl \
  data/seed.dedup.jsonl

# Expected: 659 → ~580-620 unique examples
```

### Phase 2: Stratified Sampling (5 minutes)

```bash
# Sample 300 examples with task type stratification
python scripts/stratified_sampler.py \
  data/seed.dedup.jsonl \
  data/sample_300.jsonl \
  300

# Review sampling report
cat data/sampling_report.json | jq '.strata_details'
```

### Phase 3: Auto-Labeling (10 minutes, ~$3.75)

```bash
# Auto-label with GPT-5 CODEX
export OPENAI_API_KEY="your-api-key"

python scripts/auto_label_batch.py \
  --input data/sample_300.jsonl \
  --output data/auto_300.jsonl \
  --model gpt-5 \
  --temperature 0.0 \
  --log-metadata data/auto_labeling_audit.jsonl
```

### Phase 4: Human Review (3-4 hours)

```bash
# Interactive CLI for label review/correction
python scripts/manual_label_cli.py \
  --input data/auto_300.jsonl \
  --output data/labeled_300.jsonl

# Target: 80%+ agreement rate
```

### Phase 5: Create Gold Evaluation Set (1 hour)

```bash
# 50 hand-labeled examples (2 reviewers per example)
python scripts/create_gold_set.py \
  --input data/sample_300.jsonl \
  --output data/gold_eval_50.jsonl \
  --count 50 \
  --strategy disagreement

# Manual review with extra care
python scripts/manual_label_cli.py \
  --input data/gold_eval_50.jsonl \
  --output data/gold_eval_50_labeled.jsonl \
  --gold-standard-mode
```

### Phase 6: Training (2-4 hours)

```bash
# Merge & split dataset
python scripts/merge_labels.py \
  data/auto_300.jsonl \
  data/labeled_300.jsonl \
  learning/trm_labels_merged.jsonl

python scripts/split_stratified.py \
  --input learning/trm_labels_merged.jsonl \
  --train learning/trm_labels_train.jsonl \
  --val learning/trm_labels_val.jsonl \
  --test learning/trm_labels_test.jsonl \
  --split 70/15/15

# Fine-tune with LoRA + K-fold CV
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
  --oom-guard

# Expected: 85%+ validation accuracy (k-fold CV mean)
```

### Phase 7: Threshold Tuning (5 minutes)

```bash
# Calibrate confidence thresholds
python scripts/tune_thresholds.py \
  --model models/trm_router_lora \
  --val-data learning/trm_labels_val.jsonl \
  --output models/trm_router_lora/threshold_analysis.json \
  --criterion f1

# Review recommended threshold
cat models/trm_router_lora/threshold_analysis.json | jq '.production_recommendation'
```

### Phase 8: Shadow Mode (1 week)

```bash
# Run in parallel with production (zero impact)
python scripts/shadow_mode.py \
  --router models/trm_router_lora \
  --duration 7d \
  --log-path logs/shadow_mode/routing_deltas.jsonl \
  --log-disagreements logs/shadow_mode/disagreements.jsonl \
  --confidence-threshold 0.75

# Monitor telemetry
python scripts/shadow_mode_dashboard.py \
  --input logs/shadow_mode/routing_deltas.jsonl \
  --output logs/shadow_mode/dashboard.html

# Open dashboard in browser
open logs/shadow_mode/dashboard.html
```

**Decision Gate**: If agreement ≥90% for 1 week → Promote to production

### Phase 9: Production Deployment (5 minutes)

```bash
# Update model policy
cat >> shared/model_policy.py <<'EOF'

# TRM Router Integration
from tools.trm_router import TRMRouter

TRM_ROUTER = TRMRouter(
    model_path="models/trm_router_lora",
    confidence_threshold=0.75  # From threshold analysis
)

def route_with_trm(task: dict) -> str:
    """Route task with TRM-7M recursive reasoning check."""
    trm_decision = TRM_ROUTER.classify(task)

    if trm_decision["label"] == 1 and trm_decision["confidence"] >= 0.75:
        # Route to TRM-7M for recursive reasoning
        return "trm-7m"
    else:
        # Fallback to Leap 3 router
        return agent_model(task["agent"])
EOF

# Enable production routing
echo "USE_TRM_ROUTER=true" >> .env

# Verify integration
python -c "from shared.model_policy import route_with_trm; print('✅ TRM Router enabled')"
```

---

## Continuous Learning Automation

### Setup Automated Retraining (5 minutes, one-time)

```bash
# Install cron job (runs bi-weekly at 2 AM)
bash scripts/setup_retraining_cron.sh

# Verify cron entry
crontab -l | grep auto_retrain_loop
```

**Cron Schedule**: 2 AM on 1st and 15th of every month

**What it does**:
1. Collects disagreements from shadow mode (last 14 days)
2. Deduplicates & stratifies new samples
3. Fine-tunes LoRA adapter on combined dataset (existing + new)
4. Re-tunes confidence thresholds
5. Logs lineage to `missions/TRM_ROUTER_CHANGELOG.md`

**Minimum trigger**: 100 disagreements (prevents retraining on insufficient data)

### Setup Gold Set Rotation (Quarterly)

```bash
# Add quarterly cron job for gold set rotation
(crontab -l 2>/dev/null; echo "0 3 1 1,4,7,10 * cd $(pwd) && python scripts/rotate_gold_set.py --gold-set data/gold_eval_50.jsonl --candidate-pool data/seed.dedup.jsonl --rotate-count 10 --strategy disagreement >> logs/gold_rotation.log 2>&1") | crontab -
```

**Schedule**: 3 AM on Jan 1, Apr 1, Jul 1, Oct 1

**What it does**:
1. Rotates 10 examples out of gold set
2. Replaces with 10 new examples (prioritizing disagreements)
3. Archives rotated examples to `data/gold_set_archive.jsonl`
4. Maintains 50 total examples

### Setup Calibration Monitoring (Daily)

**Option 1: GitHub Actions** (Recommended for teams)

Already configured in `.github/workflows/trm_router_validation.yml`:
- Runs daily at 2 AM UTC
- Validates calibration metrics on gold set
- Fails CI if ROC-AUC <0.9, ECE >0.05, or Brier >0.12
- Posts results to PR comments

**Option 2: Local Cron** (For individual developers)

```bash
# Add daily calibration check
(crontab -l 2>/dev/null; echo "0 4 * * * cd $(pwd) && python scripts/calibration_dashboard.py --model models/trm_router_lora --gold-set data/gold_eval_50.jsonl --output logs/calibration/dashboard.html >> logs/calibration.log 2>&1") | crontab -
```

**Schedule**: 4 AM daily

---

## Monitoring & Maintenance

### Daily Checks (5 minutes)

```bash
# 1. Check calibration status
python scripts/calibration_dashboard.py \
  --model models/trm_router_lora \
  --gold-set data/gold_eval_50.jsonl \
  --output logs/calibration/dashboard.html

open logs/calibration/dashboard.html

# 2. Review disagreements (if any)
tail -20 logs/shadow_mode/disagreements.jsonl | jq '.'

# 3. Check retraining logs (if ran recently)
ls -lt logs/retraining/ | head -5
```

**Green Flags**:
- ✅ ROC-AUC ≥0.9
- ✅ ECE ≤0.05
- ✅ Brier ≤0.12
- ✅ No alerts in dashboard

**Red Flags**:
- ⚠️ ROC-AUC <0.85 (significant drift)
- ⚠️ ECE >0.10 (miscalibration)
- ⚠️ Disagreement rate >20% (model-production mismatch)

### Weekly Reviews (30 minutes)

```bash
# 1. Review changelog
cat missions/TRM_ROUTER_CHANGELOG.md | tail -30

# 2. Analyze disagreement patterns
python - <<'EOF'
import json
from collections import Counter

disagreements = [json.loads(line) for line in open("logs/shadow_mode/disagreements.jsonl")]
patterns = Counter(d["production_label"] for d in disagreements)
print(f"Disagreement patterns: {patterns}")

# High-confidence false positives (TRM=1, Production=0, Confidence>0.8)
high_conf_fp = [d for d in disagreements if d["trm_router_label"]==1 and d["production_label"]==0 and d["trm_router_confidence"]>0.8]
print(f"High-confidence false positives: {len(high_conf_fp)}")
for ex in high_conf_fp[:5]:
    print(f"  - {ex['instruction'][:80]}...")
EOF

# 3. Check shadow mode agreement rate
python scripts/shadow_mode_dashboard.py \
  --input logs/shadow_mode/routing_deltas.jsonl \
  --output logs/shadow_mode/dashboard_weekly.html

open logs/shadow_mode/dashboard_weekly.html
```

### Monthly Reviews (1 hour)

```bash
# 1. Full calibration report on test set
python scripts/tune_thresholds.py \
  --model models/trm_router_lora \
  --val-data learning/trm_labels_test.jsonl \
  --output reports/monthly_$(date +%Y%m).json

# 2. Compare to baseline
python - <<'EOF'
import json
from pathlib import Path

current = json.loads(Path("reports/monthly_$(date +%Y%m).json").read_text())
baseline = json.loads(Path("models/trm_router_lora/baseline_metrics.json").read_text())

print("Month-over-month comparison:")
for metric in ["roc_auc", "brier_score", "ece"]:
    curr_val = current["calibration_metrics"][metric]
    base_val = baseline[metric]
    diff = curr_val - base_val
    print(f"  {metric}: {base_val:.4f} → {curr_val:.4f} (Δ {diff:+.4f})")
EOF

# 3. Update baseline if improved
# (Only if metrics improved AND agreement rate ≥90%)
# cp reports/monthly_$(date +%Y%m).json models/trm_router_lora/baseline_metrics.json
```

---

## Troubleshooting

### Issue: Calibration Drift Detected

**Symptoms**: ROC-AUC drops >5%, ECE increases >5%

**Diagnosis**:
```bash
# Check disagreement count
wc -l logs/shadow_mode/disagreements.jsonl

# Review recent disagreements
tail -50 logs/shadow_mode/disagreements.jsonl | jq '.instruction' -r
```

**Solutions**:
1. **If <100 disagreements**: Wait for more data (cron will auto-retrain at 100)
2. **If ≥100 disagreements**: Manually trigger retraining:
   ```bash
   python scripts/auto_retrain_loop.py \
     --disagreements logs/shadow_mode/disagreements.jsonl \
     --output models/trm_router_lora_hotfix_$(date +%Y%m%d) \
     --sample-count 150
   ```
3. **If persistent drift**: Review production workload changes (new task types?)

### Issue: High False Positive Rate (Precision <0.7)

**Symptoms**: TRM router over-delegates (labels too many tasks as needing TRM)

**Diagnosis**:
```bash
python scripts/tune_thresholds.py \
  --model models/trm_router_lora \
  --val-data learning/trm_labels_val.jsonl \
  --output debug/threshold_analysis.json

cat debug/threshold_analysis.json | jq '.threshold_sweep[] | select(.precision >= 0.80)'
```

**Solutions**:
1. **Increase confidence threshold**: Try 0.80 instead of 0.75
2. **Add high-confidence false positives to training**: Sample from disagreements
3. **Re-tune with precision-optimized criterion**:
   ```bash
   python scripts/tune_thresholds.py \
     --model models/trm_router_lora \
     --val-data learning/trm_labels_val.jsonl \
     --output models/trm_router_lora/threshold_precision_optimized.json \
     --criterion precision  # Instead of f1
   ```

### Issue: Cron Job Not Running

**Diagnosis**:
```bash
# Check cron service
pgrep cron || echo "Cron not running"

# Check crontab
crontab -l | grep auto_retrain_loop

# Check logs
ls -lt logs/retraining/ | head -5
```

**Solutions**:
1. **Cron not installed**: `sudo apt-get install cron && sudo service cron start`
2. **Environment variables missing**: Add to crontab:
   ```bash
   OPENAI_API_KEY=your-key
   PATH=/usr/local/bin:/usr/bin:/bin
   ```
3. **Re-install cron**: `bash scripts/setup_retraining_cron.sh`

### Issue: OOM During Training

**Symptoms**: Training crashes with "CUDA out of memory"

**Diagnosis**:
```bash
# Check available memory
nvidia-smi  # Or: python -c "import psutil; print(f'{psutil.virtual_memory().available / 1e9:.1f} GB')"
```

**Solutions**:
1. **Reduce batch size**: Change `--batch-size 4` → `--batch-size 2`
2. **Enable 8-bit quantization**: Add `--load-in-8bit` flag
3. **Use CPU**: Add `--device cpu` (slower but no memory limit)

---

## Cost & Performance

### Training Costs

| Phase | Time | Cost | Frequency |
|-------|------|------|-----------|
| Initial Training | 6-8 hours | $3.75 (auto-labeling) | One-time |
| Automated Retraining | 2-4 hours | $0 (local) | Bi-weekly |
| Gold Set Rotation | 5 minutes | $0 | Quarterly |
| Calibration Monitoring | 1 minute | $0 | Daily |
| **Total (Year 1)** | **~100 hours** | **~$50** | - |

### Operational Costs

| Item | Cost | Notes |
|------|------|-------|
| Inference | $0 | Local 7M-param model |
| Shadow Mode | $0 | No production impact |
| Retraining (26x/year) | $0 | Local fine-tuning |
| Auto-labeling (new samples) | ~$40/year | 100 samples × 26 retrains × $0.015 |
| **Total Annual** | **~$90** | 98% savings vs cloud routing |

### Performance Metrics (Expected)

| Metric | Initial | After 6 Months | After 1 Year |
|--------|---------|----------------|--------------|
| ROC-AUC | 0.89 | 0.92 | 0.94 |
| ECE | 0.06 | 0.04 | 0.03 |
| Agreement Rate | 87% | 92% | 95% |
| Churn Reduction | 40% | 50% | 60% |
| False Positive Rate | 15% | 10% | 8% |

---

## Success Checklist

### ✅ Initial Deployment (Week 1)

- [ ] 300 labeled examples (80%+ agreement)
- [ ] 50 gold evaluation examples (2-reviewer consensus)
- [ ] Model trained (85%+ validation accuracy)
- [ ] Thresholds tuned (precision ≥0.80)
- [ ] Shadow mode running (1 week)
- [ ] Agreement rate ≥90%
- [ ] Production enabled (`USE_TRM_ROUTER=true`)

### ✅ Automation Setup (Week 2)

- [ ] Cron job installed (bi-weekly retraining)
- [ ] GitHub Actions workflow configured
- [ ] Calibration dashboard accessible
- [ ] Gold set rotation scheduled (quarterly)
- [ ] Disagreement logging active
- [ ] Lineage documentation automated

### ✅ Steady State (Month 1+)

- [ ] Daily calibration checks (ROC-AUC ≥0.9)
- [ ] Weekly disagreement reviews
- [ ] Monthly baseline comparisons
- [ ] Quarterly gold set rotations
- [ ] Bi-weekly automated retraining
- [ ] Zero manual interventions

---

## Final Notes

**You now have a fully autonomous, self-improving TRM routing system!**

Key features:
- ✅ **Continuous learning** (bi-weekly retraining from disagreements)
- ✅ **Calibration monitoring** (daily checks, automatic alerts)
- ✅ **Gold set rotation** (quarterly drift tracking)
- ✅ **CI/CD validation** (GitHub Actions enforces quality gates)
- ✅ **Lineage documentation** (every retraining logged)
- ✅ **Cost-effective** (~$90/year vs $19k/year cloud routing)

**Maintenance burden**: ~30 minutes/week (monitoring only, automation handles retraining)

**Next evolution** (Leap 9): Cross-graph learning with TRM patterns stored in VectorStore

---

**Generated**: 2025-10-24
**Version**: 3.0 (Production-Ready + Continuous Learning)
**Status**: ✅ Complete Autonomous Loop
