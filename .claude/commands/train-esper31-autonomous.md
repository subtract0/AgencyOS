# Autonomous Esper3.1 QLoRA Training

**Mission**: Train Esper3.1 with QLoRA adapters on 1,102 algorithm examples. Handle ALL edge cases autonomously.

## Context

**Problem**: Manual training keeps getting stuck/crashing
- Memory issues (80GB → 48GB)
- bitsandbytes requires CUDA (M4 Pro has none)
- Data loader deadlocks
- First step taking forever

**User has**:
- M4 Pro 48GB
- 1,102 formatted training examples in `data/esper31_training_formatted.jsonl`
- `.venv-training/` with dependencies

## Autonomous Mission

Execute the following plan WITHOUT user intervention:

### Phase 1: Diagnosis (5 minutes)

1. **Check environment**:
   - Memory available (need >25GB free)
   - Dependencies installed
   - Training data exists
   - Previous checkpoints (resume if exists)

2. **Determine best approach**:
   - Option A: CPU training with FP16 (current approach)
   - Option B: Use smaller subset first to validate
   - Option C: Recommend cloud GPU if local won't work

3. **Create fallback strategy**:
   - If training stuck >5 min → try smaller batch
   - If OOM → try smaller model rank
   - If deadlock → disable all multiprocessing

### Phase 2: Create Bulletproof Training Script (10 minutes)

Create `scripts/train_esper31_autonomous.py` with:

**Features**:
- ✅ **Progress monitoring**: Detect if stuck (no progress >5 min)
- ✅ **Auto-retry**: If stuck, kill and restart with different config
- ✅ **Memory monitoring**: Check every minute, abort if >45GB
- ✅ **Heartbeat logging**: Print status every 60 seconds even if no progress
- ✅ **Checkpoint safety**: Save every 50 steps
- ✅ **Timeout detection**: If first step >10 min, abort and try different approach

**Configurations to try** (in order):
1. FP16, batch=1, accum=32, workers=0, threads=10
2. FP16, batch=1, accum=16, workers=0, threads=6 (if #1 stuck)
3. FP16, batch=1, accum=8, workers=0, threads=4 (if #2 stuck)
4. Subset 200 examples (if all fail, validate approach)

### Phase 3: Execute with Monitoring (4-8 hours)

1. **Start training with watchdog**:
   - Main process: Training
   - Watchdog process: Monitor progress every 60s
   - If watchdog detects stuck: Kill and retry next config

2. **Real-time monitoring**:
   ```
   [00:00] Starting training (Config 1: FP16, batch=1, accum=32)
   [00:01] Model loaded (20.3GB)
   [00:02] First step starting...
   [02:34] Step 1/93 complete! Loss: 2.45, Time: 154s
   [04:12] Step 2/93 complete! Loss: 2.31, Time: 98s
   [05:45] Step 3/93 complete! Loss: 2.18, Time: 93s
   ...
   ```

3. **Adaptive timing**:
   - First step: 2-5 min acceptable
   - Subsequent steps: 30-90s acceptable
   - If step >10 min: ABORT, try next config

### Phase 4: Validation (15 minutes)

After training completes:

1. **Test adapters load correctly**
2. **Run 3 quick inference tests**
3. **Save results**:
   - `models/esper31-algorithms-qlora/` (adapters)
   - `data/training_log_autonomous.json` (full log)
   - `data/training_metrics.json` (loss curve, timing)

### Phase 5: Report (1 minute)

Generate final report:
```markdown
# Esper3.1 QLoRA Training Complete

## Results
- ✅ Training completed successfully
- Configuration used: FP16, batch=1, accum=32, workers=0
- Total time: 5h 23m
- Final loss: 0.87
- Adapters saved to: models/esper31-algorithms-qlora/

## Training Metrics
- Epoch 1: Avg loss 2.15, Time: 1h 47m
- Epoch 2: Avg loss 1.32, Time: 1h 48m
- Epoch 3: Avg loss 0.87, Time: 1h 48m

## Issues Encountered
- Config 1 (batch=32): Stuck at step 0 for 23min → Aborted
- Config 2 (batch=16): Worked successfully

## Next Steps
1. Test adapters: python scripts/test_esper31_adapters.py
2. Hard benchmark: python scripts/benchmark_esper31_hard.py
3. Compare to baseline
```

## Autonomous Decision Tree

```
START
  ↓
Check memory
  ├─ <25GB free → Close apps or abort
  └─ ≥25GB free → Continue
  ↓
Try Config 1 (optimal)
  ├─ Progress in 5 min? → Continue training
  └─ Stuck >5 min? → Kill, try Config 2
  ↓
Try Config 2 (moderate)
  ├─ Progress in 5 min? → Continue training
  └─ Stuck >5 min? → Kill, try Config 3
  ↓
Try Config 3 (conservative)
  ├─ Progress in 5 min? → Continue training
  └─ Stuck >5 min? → Try subset
  ↓
Try Subset (200 examples)
  ├─ Works? → Report success, recommend cloud for full
  └─ Still fails? → Recommend cloud GPU
  ↓
COMPLETE
```

## Constitutional Compliance

- **Article I**: Complete context (monitor all metrics, retry on timeout)
- **Article II**: 100% verification (test adapters after training)
- **Article III**: Local enforcement (no manual intervention needed)
- **Article IV**: Learning (log all attempts, save metrics for future)
- **Article V**: Spec-driven (this spec guides execution)

## Success Criteria

- [ ] Training completes (all 3 epochs)
- [ ] Adapters saved and loadable
- [ ] Loss decreasing trend
- [ ] Final loss <1.5
- [ ] Inference test passes
- [ ] Full log saved

## Failure Criteria

If ALL configs fail:
- Provide diagnostic report
- Recommend cloud GPU with exact commands
- Estimate cost ($1-2 on RunPod)
- Create ready-to-run cloud script

## Output Deliverables

1. **Code**: `scripts/train_esper31_autonomous.py` (bulletproof trainer)
2. **Adapters**: `models/esper31-algorithms-qlora/` (if successful)
3. **Logs**: `data/training_log_autonomous.json` (detailed log)
4. **Report**: `docs/TRAINING_AUTONOMOUS_REPORT.md` (what happened)
5. **Fallback**: `scripts/train_esper31_runpod.sh` (if local fails)

## Timeline

- Phase 1 (Diagnosis): 5 min
- Phase 2 (Script creation): 10 min
- Phase 3 (Training): 4-8 hours (autonomous, no user intervention)
- Phase 4 (Validation): 15 min
- Phase 5 (Report): 1 min

**Total**: 4-8 hours (fully autonomous)

## Agent Instructions

**You are PrimeA Autonomous Trainer**. Your job:

1. **Create the bulletproof script** with all monitoring/retry logic
2. **Start the training** with watchdog
3. **Monitor autonomously** (don't ask user for help)
4. **Handle failures** by trying next config
5. **Report results** when done (success or failure)

**Critical**: User should be able to run `/primeA "Train Esper3.1"` then go to bed and wake up to either:
- ✅ Trained adapters ready to use
- ❌ Diagnostic report explaining why local training won't work + cloud alternative ready

**No manual intervention. No debugging with user. Handle everything autonomously.**
