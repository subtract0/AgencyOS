# 🌐 Distributed Marathon Audit - Quick Start

## What Is This?

Coordinate test analysis across **multiple machines** (MBP + MBA) using local models.
- **M4 Pro (MBP)**: Qwen3-Coder-30b (fast, 32GB)
- **MacBook Air (MBA)**: GPT-OSS-20b (lighter, but still useful!)

**Performance:**
- MBP alone: 8 hours for 5,889 tests
- **MBP + MBA: 4-5 hours** (2x speedup!)
- **Cost: Still $0** (both use local models)

---

## Architecture

```
┌─────────────────────────────────────┐
│  Coordinator (runs on MBP)         │
│  - Creates 5,889 test tasks         │
│  - Manages shared queue             │
│  - Merges results at end            │
└─────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌─────────────┐     ┌─────────────┐
│ Worker 1    │     │ Worker 2    │
│ (MBP)       │     │ (MBA)       │
│             │     │             │
│ Qwen3-Coder │     │ GPT-OSS-20b │
│ Tests 0-N   │     │ Tests N-M   │
└─────────────┘     └─────────────┘
        │                   │
        └─────────┬─────────┘
                  ▼
        ┌─────────────────┐
        │ Shared Results  │
        │ (~/.agency/)    │
        └─────────────────┘
```

---

## Setup (One-Time)

### Prerequisites

**On both machines:**
1. ✅ Ollama installed (`brew install ollama`)
2. ✅ Agency repo cloned to **same path** (e.g., `~/Code/Agency`)
3. ✅ Shared filesystem (iCloud Drive, Dropbox, or NFS)

**Models:**
- **MBP**: `ollama pull qwen3-coder:30b`
- **MBA**: `ollama pull gpt-oss:20b` (or use existing model)

**Network:** None required! Uses shared filesystem (iCloud/Dropbox).

---

## Usage (Step-by-Step)

### Step 1: Create Tasks (On MBP)

```bash
cd ~/Code/Agency

# Create 5,889 test analysis tasks
python scripts/distributed_marathon_coordinator.py --create-tasks

# Or test with smaller batch first:
python scripts/distributed_marathon_coordinator.py --create-tasks --max-tests 100
```

**Output:**
```
🌐 DISTRIBUTED MARATHON COORDINATOR
================================================================================
📊 Creating 5889 test analysis tasks...
✅ Task creation complete!

📋 Total Tasks: 5889
📁 Queue File: ~/.agency/marathon_distributed/task_queue.json
📁 Results Dir: ~/.agency/marathon_distributed/results/
```

---

### Step 2: Start Workers

**Terminal 1 (on MBP):**
```bash
cd ~/Code/Agency
python scripts/distributed_marathon_worker.py --machine mbp --model qwen3-coder:30b
```

**Terminal 2 (on MBA):**
```bash
cd ~/Code/Agency
python scripts/distributed_marathon_worker.py --machine mba --model gpt-oss:20b
```

**Both workers will:**
- ✅ Claim tasks from shared queue (no conflicts!)
- ✅ Analyze tests using their local model
- ✅ Write results to shared directory
- ✅ Show live progress

**Example output:**
```
🤖 DISTRIBUTED MARATHON WORKER
================================================================================
Machine: mbp
Model: qwen3-coder:30b
Agent ID: mbp-worker-1729786543

Waiting for tasks...
(Press Ctrl+C to stop gracefully)
================================================================================

[   0] Analyzing test_hook_initialization                   ✅
[   1] Analyzing test_hook_initialization_without_context   ✅
[   2] Analyzing test_content_truncation                    ✅
...
```

---

### Step 3: Monitor Progress (Optional)

**Terminal 3 (on MBP):**
```bash
# Check status every 5 seconds
watch -n 5 'python scripts/distributed_marathon_coordinator.py --status'
```

**Output:**
```
📊 DISTRIBUTED MARATHON STATUS
================================================================================

Pending:     3245
In Progress:    2
Completed:   2642
Failed:        0

Progress: 44.9% complete
Result Files: 2642

Machine Contributions:
  mba: 1345 tests
  mbp: 1297 tests
```

---

### Step 4: Merge Results (When Complete)

**When workers finish:**
```bash
python scripts/distributed_marathon_coordinator.py --merge-results
```

**Output:**
```
🔀 MERGING DISTRIBUTED RESULTS
================================================================================
📁 Found 5889 result files
  ✅ Loaded 5889 results

Machine Contributions:
  mbp: 3012 tests
  mba: 2877 tests

✅ JSON Report: audit_reports/distributed_audit_20251023_161234.json
✅ Markdown Report: audit_reports/distributed_audit_20251023_161234.md
✅ Healing Roadmap: audit_reports/distributed_healing_roadmap_20251023_161234.md
```

---

## Common Scenarios

### Scenario 1: Test Run (100 tests)

```bash
# 1. Create small batch
python scripts/distributed_marathon_coordinator.py --create-tasks --max-tests 100

# 2. Start MBP worker
python scripts/distributed_marathon_worker.py --machine mbp --model qwen3-coder:30b

# 3. Start MBA worker (in parallel)
python scripts/distributed_marathon_worker.py --machine mba --model gpt-oss:20b

# 4. Merge when done
python scripts/distributed_marathon_coordinator.py --merge-results
```

**Expected time:** ~10 minutes (50 tests per machine)

---

### Scenario 2: Full Audit (5,889 tests)

```bash
# 1. Create all tasks
python scripts/distributed_marathon_coordinator.py --create-tasks

# 2. Start both workers (overnight)
# On MBP:
nohup python scripts/distributed_marathon_worker.py --machine mbp --model qwen3-coder:30b > worker_mbp.log 2>&1 &

# On MBA:
nohup python scripts/distributed_marathon_worker.py --machine mba --model gpt-oss:20b > worker_mba.log 2>&1 &

# 3. Check progress
python scripts/distributed_marathon_coordinator.py --status

# 4. Merge results (next morning)
python scripts/distributed_marathon_coordinator.py --merge-results
```

**Expected time:** ~4-5 hours (2x speedup!)

---

### Scenario 3: Single Machine (MBP Only)

```bash
# If MBA is not available, just run MBP worker
python scripts/distributed_marathon_coordinator.py --create-tasks
python scripts/distributed_marathon_worker.py --machine mbp --model qwen3-coder:30b
python scripts/distributed_marathon_coordinator.py --merge-results
```

**Time:** ~8 hours (still $0 cost!)

---

## Troubleshooting

### Issue: Workers not finding tasks

**Cause:** Queue file path mismatch

**Fix:**
```bash
# Check queue file exists
ls -lh ~/.agency/marathon_distributed/task_queue.json

# If missing, recreate tasks
python scripts/distributed_marathon_coordinator.py --create-tasks
```

---

### Issue: MBA not contributing

**Cause:** Different repo path or model not pulled

**Fix:**
```bash
# On MBA, verify:
cd ~/Code/Agency  # Same path as MBP
ollama list       # Check gpt-oss:20b exists
ollama pull gpt-oss:20b  # If missing
```

---

### Issue: Results not merging

**Cause:** Results in wrong directory

**Fix:**
```bash
# Check results directory
ls ~/.agency/marathon_distributed/results/ | wc -l

# Should show number of completed tests
```

---

## Performance Comparison

| Setup | Time | Cost | Speedup |
|-------|------|------|---------|
| MBP alone (Qwen3-Coder) | 8h | $0 | 1x |
| **MBP + MBA (distributed)** | **4-5h** | **$0** | **2x** |
| Cloud (OpenAI) | 2h | $590 | 4x (but $$!) |

**Winner:** MBP + MBA distributed = 2x faster than solo, $0 cost!

---

## Advanced: Add More Machines

Want to add a 3rd machine?

```bash
# On new machine (e.g., Mac Mini):
cd ~/Code/Agency
ollama pull qwen2.5-coder:7b  # Lighter model
python scripts/distributed_marathon_worker.py --machine mac-mini --model qwen2.5-coder:7b
```

**Each additional machine = ~30-40% speedup!**

---

## File Structure

```
~/.agency/marathon_distributed/
├── task_queue.json          # Shared queue (atomic operations)
└── results/
    ├── test_analysis_0.json
    ├── test_analysis_1.json
    └── ...                  # 5,889 result files

audit_reports/
├── distributed_audit_YYYYMMDD_HHMMSS.json      # Combined JSON
├── distributed_audit_YYYYMMDD_HHMMSS.md        # Summary report
└── distributed_healing_roadmap_YYYYMMDD_HHMMSS.md  # Action plan
```

---

## FAQ

**Q: Do machines need to be on same network?**
A: No! They just need shared filesystem (iCloud, Dropbox, NFS).

**Q: What if one worker crashes?**
A: Other workers continue! Restart crashed worker and it will claim remaining tasks.

**Q: Can I stop/restart workers?**
A: Yes! Ctrl+C for graceful shutdown, restart anytime. Tasks remain in queue.

**Q: What if MBA is slower?**
A: No problem! Faster machine (MBP) will claim more tasks naturally.

**Q: Can I use different models?**
A: Yes! Any Ollama model works. Adjust `--model` parameter.

---

## Summary

**3 Simple Commands:**
```bash
# 1. Create tasks
python scripts/distributed_marathon_coordinator.py --create-tasks

# 2. Start workers (both machines)
python scripts/distributed_marathon_worker.py --machine mbp --model qwen3-coder:30b
python scripts/distributed_marathon_worker.py --machine mba --model gpt-oss:20b

# 3. Merge results
python scripts/distributed_marathon_coordinator.py --merge-results
```

**Result:** 5,889 tests analyzed in 4-5 hours, $0 cost, using idle MBA! 🚀

---

**Ready to distribute?** Start with 100 tests to verify setup, then run full audit overnight!
