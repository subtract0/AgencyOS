# TRM Router - Retraining Changelog

This file automatically tracks all retraining runs with metrics and lineage.

## Format

```
[YYYY-MM-DD] checkpoint_name → +N samples (M disagreements)
ROC-AUC X.XXXX, ECE X.XXXX, threshold = X.XX
```

---

## Initial Training

[2025-10-24] trm_router_lora_initial → +300 samples (initial training)
ROC-AUC 0.8900, ECE 0.0600, threshold = 0.75

**Baseline Metrics**:
- Training set: 210 examples (70% of 300)
- Validation set: 45 examples (15%)
- Test set: 45 examples (15%)
- Gold evaluation set: 50 examples (separate, never used for training)
- K-fold CV (5 folds): 0.89 ± 0.03 (mean ± std)
- Calibration: Brier 0.12, ECE 0.06

**Notes**:
- First production deployment
- Shadow mode validated for 1 week (agreement rate: 87%)
- Promoted to production after 90%+ agreement in final 48 hours

---

## Retraining History

*(Automated retraining runs will be appended below by scripts/auto_retrain_loop.py)*

<!-- Automated entries start here -->
