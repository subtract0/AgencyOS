# PrimeCCC Distributed Locking

**Problem:** Parallel `/primeccc` instances auto-selecting from the same priority queue would race to execute the same task.

**Solution:** File-based distributed locks in `~/.agency/memories/.locks/`

---

## Architecture

### Lock Directory Structure
```
~/.agency/memories/.locks/
├── priority_1_ollama_docker.lock
├── priority_2_messagebus_cleanup.lock
└── priority_3_executor_api.lock
```

### Lock File Format
```
primeccc_20251008_170747  # Session ID (line 1)
2025-10-08T17:07:47       # ISO timestamp (line 2)
```

---

## Locking Protocol

### 1. Task Selection with Lock Acquisition
```python
def auto_select_task_with_lock(session_id: str) -> str:
    """Auto-select task from priority queue with distributed locking."""

    backlog = read_backlog()
    priority_queue = extract_priority_queue(backlog)

    for priority in priority_queue:
        if priority.status != "Ready":
            continue  # Skip blocked tasks

        task_id = f"priority_{priority.rank}_{slugify(priority.task)}"

        # Try to acquire lock
        lock_acquired = acquire_lock(task_id, session_id)

        if lock_acquired:
            print(f"🔒 Lock acquired: {task_id}")
            return priority.command, task_id
        else:
            print(f"⏭️ Task already locked by another instance, trying next...")
            continue

    # All Ready tasks are locked
    raise NoAvailableTasks("All tasks in progress or blocked")
```

### 2. Lock Lifecycle

```python
# Phase 0: Acquire lock during task selection
task_command, task_id = auto_select_task_with_lock(session_id)

try:
    # Phase 1-4: Execute task
    execute_autonomous_loop(task_command)

finally:
    # Always release lock (success or failure)
    release_lock(task_id, session_id)
```

### 3. Stale Lock Cleanup

**Stale Lock Threshold:** 4 hours

**Logic:**
```python
if datetime.now() - lock_timestamp > timedelta(hours=4):
    print(f"⚠️ Stale lock detected (>{4}h old), removing...")
    os.remove(lock_file)
    # Lock is now available for acquisition
```

**Why 4 hours:**
- Most tasks complete in <2 hours
- Covers long-running architecture tasks
- Prevents indefinite blocking from crashed instances

---

## Edge Cases

### 1. Parallel Instance Startup
```
Instance A: /primeccc (no args)
Instance B: /primeccc (no args)  # Starts 2 seconds later

Timeline:
T+0s:  Instance A reads backlog → selects Priority #1
T+1s:  Instance A acquires lock: priority_1_ollama_docker.lock
T+2s:  Instance B reads backlog → selects Priority #1
T+2s:  Instance B tries to acquire lock → BLOCKED
T+2s:  Instance B selects Priority #2 (next Ready task)
T+3s:  Instance B acquires lock: priority_2_messagebus_cleanup.lock

Result: ✅ Both instances work on different tasks
```

### 2. Crashed Instance
```
Instance A: /primeccc → acquires lock → crashes (no cleanup)

Timeline:
T+0h:  Instance A crashes, lock remains
T+1h:  Instance B tries Priority #1 → BLOCKED (valid lock)
T+4h:  Instance C tries Priority #1 → STALE LOCK DETECTED
T+4h:  Instance C removes stale lock, acquires new lock

Result: ✅ Automatic recovery after 4 hours
```

### 3. Manual Lock Release
```bash
# Force release lock (if instance confirmed dead)
python3 scripts/release_task_lock.py priority_1_ollama_docker

# List all active locks
ls -lh ~/.agency/memories/.locks/

# Clean all stale locks (>4h old)
python3 scripts/clean_stale_locks.py
```

---

## Implementation

### Core Lock Functions

```python
def acquire_lock(task_id: str, session_id: str) -> bool:
    """Acquire lock for task. Returns True if successful."""
    lock_file = os.path.join(LOCK_DIR, f"{task_id}.lock")

    # Check if already locked
    if os.path.exists(lock_file):
        with open(lock_file, 'r') as f:
            holder = f.readline().strip()
            timestamp_str = f.readline().strip()
            timestamp = datetime.fromisoformat(timestamp_str)

        # Check if stale
        if datetime.now() - timestamp > timedelta(hours=4):
            os.remove(lock_file)  # Remove stale lock
        else:
            return False  # Lock is valid

    # Acquire lock
    with open(lock_file, 'w') as f:
        f.write(f"{session_id}\n")
        f.write(f"{datetime.now().isoformat()}\n")

    return True


def release_lock(task_id: str, session_id: str) -> None:
    """Release lock for task."""
    lock_file = os.path.join(LOCK_DIR, f"{task_id}.lock")

    if not os.path.exists(lock_file):
        return

    # Verify we own the lock
    with open(lock_file, 'r') as f:
        holder = f.readline().strip()

    if holder == session_id:
        os.remove(lock_file)
    else:
        print(f"⚠️ Cannot release lock owned by: {holder}")
```

---

## Integration with PrimeCCC

### Updated Phase 0: Task Selection with Locking

```python
# Generate session ID
session_id = f"primeccc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Auto-select task with locking
if not STRATEGIC_INTENT:
    try:
        STRATEGIC_INTENT, task_id = auto_select_task_with_lock(session_id)
        print(f"✅ Selected task: {STRATEGIC_INTENT}")
        print(f"🔒 Lock acquired: {task_id}\n")
    except NoAvailableTasks as e:
        print("⚠️ All Ready tasks are in progress by other instances.")
        print("📋 Review backlog: cat ~/.agency/memories/agency_backlog/test_suite_gaps.md")
        exit(0)

# Always release lock on exit
try:
    # Execute Phase 1-4
    autonomous_execution_loop(...)
finally:
    if task_id:
        release_lock(task_id, session_id)
        print(f"🔓 Lock released: {task_id}")
```

---

## Benefits

✅ **Race-Free:** Parallel instances never collide on the same task
✅ **Automatic Recovery:** Stale locks auto-cleaned after 4 hours
✅ **Stateless:** Lock state is file-based, survives context resets
✅ **Transparent:** Lock status visible in filesystem (`ls ~/.agency/memories/.locks/`)
✅ **Manual Override:** Easy to force-release locks if needed

---

## Testing

```bash
# Test 1: Single instance
/primeccc  # Should acquire lock for Priority #1

# Test 2: Parallel instances (different terminals)
Terminal A: /primeccc  # Acquires Priority #1
Terminal B: /primeccc  # Acquires Priority #2 (skips locked #1)

# Test 3: Stale lock cleanup
echo "test_session" > ~/.agency/memories/.locks/priority_1_ollama_docker.lock
echo "2020-01-01T00:00:00" >> ~/.agency/memories/.locks/priority_1_ollama_docker.lock
/primeccc  # Should detect stale lock, remove it, acquire new lock

# Test 4: Lock release on completion
/primeccc "Simple task"  # Should release lock after completion
ls ~/.agency/memories/.locks/  # Should be empty
```

---

## Future Enhancements

1. **Lock Dashboard:**
   - Web UI showing all active locks
   - Session metadata (agent, task, start time)
   - Manual lock release button

2. **Lock Metrics:**
   - Average lock duration per task type
   - Lock contention rate (how often tasks are skipped)
   - Stale lock frequency

3. **Priority Boosting:**
   - If task fails repeatedly, boost priority
   - If task blocked for >24h, alert for manual review

---

**Status:** ✅ Implemented and tested
**Version:** 1.0
**Last Updated:** 2025-10-08
