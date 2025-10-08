# Multi-Agent Coordination on Single Machine

**Status:** Critical Design Document
**Author:** Claude (PrimeCCC architectural analysis)
**Date:** 2025-10-08

---

## Problem Statement

Multiple `/primeccc` instances (different terminals, tmux panes, or Claude Code sessions) running on the same machine need to coordinate without colliding.

**Use Cases:**
1. Developer runs `/primeccc` in 2+ terminals for parallel work
2. CI runs `/primeccc` while dev is also running it locally
3. Multiple team members pair-programming on same machine

---

## Current Design (SAFE)

### Lock Acquisition Flow
```
Instance A starts → Read backlog → Acquire lock (priority_1) ✅ → User confirms → Execute
Instance B starts → Read backlog → Try lock (priority_1) ❌ → Skip to priority_2 → Acquire ✅
```

**Timeline:**
```
T+0s:   Instance A reads backlog
T+0.5s: Instance B reads backlog
T+1s:   Instance A acquires lock priority_1 ✅
T+2s:   Instance B tries lock priority_1 → LOCKED, skip
T+2s:   Instance B acquires lock priority_2 ✅
```

**Result:** Zero collisions ✅

### Why It Works
1. **Locks acquired BEFORE confirmation** (line 128 in primeccc.md)
2. **File-based locks** (atomic on same filesystem)
3. **Skip to next on conflict** (line 129-130)

---

## Improvements Needed

### 1. Lock Status Visibility

**Problem:** Can't see what other instances are doing

**Solution:** Add lock metadata
```python
# Current lock file:
primeccc_20251008_170747  # Session ID
2025-10-08T17:07:47       # Timestamp

# Improved lock file:
primeccc_20251008_170747  # Session ID
2025-10-08T17:07:47       # Timestamp
terminal_1                # Terminal identifier
@am                       # User
Priority #1: Ollama Docker Compose  # Task description
```

**Usage:**
```bash
# List active work
python scripts/release_task_lock.py list

# Output:
🔒 Active locks (2):
  - priority_1_ollama_docker
    Session: primeccc_20251008_170747
    Terminal: terminal_1
    User: @am
    Task: Ollama Docker Compose Setup
    Since: 2025-10-08T17:07:47 (5 minutes ago)

  - priority_2_messagebus_cleanup
    Session: primeccc_20251008_180512
    Terminal: terminal_2
    User: @am
    Task: MessageBus Subscriber Cleanup
    Since: 2025-10-08T18:05:12 (30 seconds ago)
```

### 2. Heartbeat Mechanism

**Problem:** Stale locks from crashed instances (4-hour cleanup is too long)

**Solution:** Heartbeat every 60 seconds
```python
# Lock file format:
primeccc_20251008_170747
2025-10-08T17:07:47
2025-10-08T17:12:30  # Last heartbeat (updated every 60s)

# Stale detection:
if datetime.now() - last_heartbeat > timedelta(minutes=5):
    # Instance crashed/killed
    remove_stale_lock()
```

**Background thread:**
```python
def heartbeat_loop(lock_file: Path, session_id: str):
    """Update lock heartbeat every 60 seconds."""
    while True:
        time.sleep(60)
        if lock_file.exists():
            # Verify we still own the lock
            with lock_file.open() as f:
                holder = f.readline().strip()

            if holder == session_id:
                # Update heartbeat timestamp
                update_lock_heartbeat(lock_file)
        else:
            # Lock was released, exit thread
            break
```

### 3. Priority Queue Expansion

**Problem:** TOP 5 exhausted quickly with parallel execution

**Current:** TOP 5 PRIORITY QUEUE
**Proposed:** TOP 20 PRIORITY QUEUE

**Benefits:**
- 4 parallel agents can work simultaneously (20 / 5 = 4)
- Reduces "No Ready tasks" scenarios
- Better work distribution

---

## Recommended Rules

### Rule 1: One Agent Per Priority Tier
**Guideline:** Run max 4 parallel `/primeccc` instances
- Instance 1: Priority #1-5
- Instance 2: Priority #6-10
- Instance 3: Priority #11-15
- Instance 4: Priority #16-20

**Why:** Prevents lock contention, maximizes throughput

### Rule 2: Check Locks Before Starting
```bash
# Before starting new instance
python scripts/release_task_lock.py list

# If 4+ locks active, wait or manually select task
/primeccc "Specific task not in top 20"
```

### Rule 3: Manual Priority Override
```bash
# Skip auto-selection if needed
/primeccc "Implement feature X" --priority high

# This bypasses backlog selection entirely
```

### Rule 4: Session Isolation
```bash
# Use different session IDs for different contexts
export PRIMECCC_SESSION_PREFIX="dev"  # → dev_20251008_170747
export PRIMECCC_SESSION_PREFIX="ci"   # → ci_20251008_170747

# Helps identify which instance is which
```

---

## Auto-Update Mechanism

### Problem: Backlog Goes Stale

**Scenario:**
```
Day 1: Create TOP 20 backlog
Day 2: 10 tasks completed, new issues found
Day 3: Backlog has 10 completed + 5 stale, missing 10 new issues
```

**Current:** Manual update (error-prone)

### Solution: Auto-Update Hooks

#### Option A: Git Pre-Commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Auto-update backlog before each commit

python scripts/update_backlog.py --scan-skipped-tests

# Updates:
# - Completed tasks (grep for "✅ DONE")
# - New skipped tests (pytest --collect-only -m skip)
# - Priority recalculation (ROI = Value / Effort)
```

#### Option B: Scheduled Background Process
```bash
# crontab -e
# Update backlog every 3 hours
0 */3 * * * cd /Users/am/Code/Agency && python scripts/update_backlog.py

# Updates:
# - Scan codebase for @pytest.mark.skip with reason
# - Compare with current backlog
# - Add new items, mark completed items
# - Recalculate priorities
```

#### Option C: CI Integration
```yaml
# .github/workflows/backlog-update.yml
name: Update Backlog
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for backlog updates
        run: python scripts/update_backlog.py
      - name: Commit changes
        run: |
          git config user.name "AgencyOS Bot"
          git commit -am "chore: Auto-update backlog" || true
          git push
```

**Recommended:** **Option C (CI Integration)**
- Always up-to-date
- No local cron setup needed
- Runs after every merge

---

## Implementation Plan

### Phase 1: Enhanced Lock Metadata (1 hour)
- Add terminal, user, task description to lock files
- Update `scripts/release_task_lock.py list` command
- Test with 2 parallel instances

### Phase 2: Heartbeat Mechanism (2 hours)
- Add background thread for heartbeat
- Reduce stale timeout: 4 hours → 5 minutes
- Add heartbeat status to lock list

### Phase 3: TOP 20 Backlog (1 hour)
- Expand backlog from TOP 5 → TOP 20
- Categorize by complexity: Simple (1-2h), Medium (3-6h), Complex (7-20h)
- Add "Recommended Parallelism" field

### Phase 4: Auto-Update (3 hours)
- Create `scripts/update_backlog.py`
- Scan for skipped tests
- Detect completed tasks
- Recalculate priorities
- Integrate with CI

---

## Testing Checklist

### Multi-Agent Tests
- [ ] Start 2 instances simultaneously → Both acquire different tasks
- [ ] Start 4 instances → All work on different priorities
- [ ] Start 21st instance → Waits or prompts for manual selection
- [ ] Kill instance mid-execution → Lock becomes stale in 5 min
- [ ] Complete task in terminal 1 → Lock released, terminal 2 picks it up

### Backlog Tests
- [ ] Complete Priority #1 → Auto-marked DONE in next update
- [ ] Add new skip marker in code → Appears in backlog within 6 hours
- [ ] Manually add high-priority item → Preserved during auto-update
- [ ] Delete obsolete task → Removed from backlog

---

## FAQ

### Q: What if all TOP 20 tasks are locked?
**A:** Agent waits and prompts:
```
⚠️ All 20 priority tasks are currently in progress by other agents.

Options:
1. Wait for a task to complete (press W)
2. Manually specify a task outside TOP 20 (press M)
3. Exit and try later (press Q)

Choice: _
```

### Q: Can remote agents coordinate?
**A:** NO - File-based locks only work on same filesystem.

**For remote coordination, use:**
- Redis locks (distributed)
- Database locks (PostgreSQL advisory locks)
- API-based coordination (centralized queue)

### Q: Should I run `/primeccc` in CI?
**A:** YES, but with constraints:
```yaml
# Only allow 1 CI instance at a time
concurrency:
  group: primeccc
  cancel-in-progress: false  # Wait, don't cancel
```

---

## Conclusion

**Current Design:**
- ✅ Safe for multi-agent execution (file-based locks)
- ✅ Zero collisions (lock before confirmation)
- ⚠️ Limited visibility (can't see other agents' work)
- ⚠️ Slow stale cleanup (4 hours)
- ⚠️ Small queue (TOP 5 exhausts quickly)

**After Improvements:**
- ✅ Full visibility (`list` shows all active work)
- ✅ Fast stale cleanup (5 minutes via heartbeat)
- ✅ Large queue (TOP 20 supports 4 parallel agents)
- ✅ Auto-updated (CI refreshes every 6 hours)

**Ready for production-scale parallel execution.**

---

**Next Steps:** Approve Phase 1-4 implementation?
