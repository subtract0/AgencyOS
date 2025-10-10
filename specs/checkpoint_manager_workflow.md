# CheckpointManager Workflow Diagrams

**Spec Reference**: `specs/checkpoint_manager_spec.md`

---

## 1. Auto-Checkpoint Trigger Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     CHECKPOINT TRIGGERS                          │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
   │ Interval     │       │ Task         │       │ User         │
   │ Timer        │       │ Completion   │       │ Interrupt    │
   │ (30 min)     │       │ (every 5)    │       │ (Ctrl+C)     │
   └──────┬───────┘       └──────┬───────┘       └──────┬───────┘
          │                      │                       │
          │                      │                       │
          ▼                      ▼                       ▼
   ┌──────────────────────────────────────────────────────────────┐
   │            CheckpointManager.trigger_checkpoint()            │
   │                                                              │
   │  1. context.get_session_state()                             │
   │  2. save_checkpoint(session_state, session_id)              │
   │  3. Log telemetry: checkpoint_count++, reason, size         │
   └──────────────────────────────────────────────────────────────┘
          │                      │                       │
          ▼                      ▼                       ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  ~/.agency/sessions/{session_id}/checkpoints/                │
   │    └─ checkpoint_20251010_143022.json                        │
   │       (SessionState + SHA256 checksum)                       │
   └──────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Day Resume Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-DAY TASK RESUME                         │
└─────────────────────────────────────────────────────────────────┘

   Friday 3pm                     Weekend                Monday 9am
   ──────────────────────────────────────────────────────────────

   ┌──────────────┐              ┌────────┐            ┌──────────────┐
   │ ChiefArchitect│              │ Laptop │            │ User runs:   │
   │ starts ADR-024│              │ closed │            │ /primeccc    │
   │               │              │        │            │ "Continue    │
   │ 60% complete  │              │        │            │  ADR-024"    │
   └───────┬───────┘              └────────┘            └──────┬───────┘
           │                                                   │
           ▼                                                   ▼
   ┌─────────────────┐                              ┌─────────────────┐
   │ Auto-Checkpoint │                              │ Detect Paused   │
   │ (every 30 min)  │                              │ Session:        │
   │                 │                              │ - Scan checkpts │
   │ checkpoint_001  │                              │ - Find latest   │
   │ checkpoint_002  │                              │ - checkpoint_002│
   │ checkpoint_003  │                              └────────┬────────┘
   └─────────────────┘                                       │
           │                                                 ▼
           │                                         ┌─────────────────┐
           │                                         │ Resume from     │
           │                                         │ Checkpoint:     │
           │                                         │ 1. Load         │
           │◄────────────────────────────────────────│ 2. Validate SHA │
           │                                         │ 3. Restore      │
           │                                         └────────┬────────┘
           ▼                                                  ▼
   ┌─────────────────┐                              ┌─────────────────┐
   │ Checkpoints     │                              │ State Restored: │
   │ Persisted:      │                              │ ✓ 60% progress  │
   │ ~/.agency/      │                              │ ✓ 47 memories   │
   │ sessions/       │                              │ ✓ 12KB metadata │
   │ ADR_024/        │                              │                 │
   │ checkpoints/    │                              │ Resume: 2.1s    │
   └─────────────────┘                              └─────────────────┘
```

---

## 3. Fallback Recovery Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│                CHECKPOINT CORRUPTION RECOVERY                    │
└─────────────────────────────────────────────────────────────────┘

   resume_from_checkpoint(session_id)
           │
           ▼
   ┌─────────────────────────────────────┐
   │ Scan checkpoints directory:          │
   │ - checkpoint_003 (latest)            │
   │ - checkpoint_002                     │
   │ - checkpoint_001                     │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │ Attempt 1: Load checkpoint_003                               │
   │ - Calculate SHA256(session_state_json)                       │
   │ - Compare with stored checksum                               │
   └──────────────┬───────────────────────────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
   ┌─────────┐      ┌───────────────────────────────────────┐
   │ Match?  │      │ Mismatch? (CORRUPTED)                 │
   │ YES     │      │                                       │
   │ ✓       │      │ Log: "Checkpoint 003 corrupted,       │
   └────┬────┘      │       attempting fallback..."         │
        │           └──────────────┬────────────────────────┘
        │                          │
        │                          ▼
        │           ┌──────────────────────────────────────┐
        │           │ Attempt 2: Load checkpoint_002       │
        │           │ - Calculate SHA256                   │
        │           └──────────────┬───────────────────────┘
        │                          │
        │                  ┌───────┴──────┐
        │                  │              │
        │                  ▼              ▼
        │           ┌─────────┐    ┌─────────────────────┐
        │           │ Match?  │    │ Mismatch?           │
        │           │ YES     │    │                     │
        │           │ ✓       │    │ Try checkpoint_001  │
        │           └────┬────┘    └──────────┬──────────┘
        │                │                    │
        │                ▼                    ▼
        │         ┌──────────────────┐  ┌─────────────────────┐
        │         │ Warn: Data loss  │  │ Attempt 3:          │
        │         │ window (T2→T3)   │  │ Load checkpoint_001 │
        │         └──────┬───────────┘  └──────────┬──────────┘
        │                │                         │
        │                │                  ┌──────┴─────┐
        │                │                  │            │
        │                │                  ▼            ▼
        │                │           ┌──────────┐  ┌──────────────┐
        │                │           │ Match?   │  │ Mismatch?    │
        │                │           │ YES ✓    │  │              │
        │                │           └────┬─────┘  │ All checkpts │
        │                │                │        │ CORRUPTED    │
        │                │                │        └──────┬───────┘
        │                │                │               │
        ▼                ▼                ▼               ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ SUCCESS: Restore AgentContext                               │
   │ - Create Memory instance                                    │
   │ - Restore memory snapshots                                  │
   │ - Restore metadata                                          │
   │ - Log resume metrics: checkpoint_id, age, data_loss_window  │
   └─────────────────────────────────────────────────────────────┘
                                                          │
                                                          ▼
                                                 ┌────────────────┐
                                                 │ FULL RESTART   │
                                                 │ (no state)     │
                                                 └────────────────┘
```

---

## 4. Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 CHECKPOINT MANAGER INTEGRATION                   │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────────┐
   │                    PrimeCCC Orchestrator                      │
   │                                                              │
   │  execute_mission(strategic_intent):                          │
   │    1. context = create_agent_context(session_id)            │
   │                      │                                       │
   │                      ▼                                       │
   │    2. checkpoint_manager.detect_paused_session(session_id)  │
   │                      │                                       │
   │              ┌───────┴───────┐                              │
   │              │               │                              │
   │              ▼               ▼                              │
   │       ┌──────────┐    ┌──────────────┐                     │
   │       │ Paused?  │    │ Fresh start  │                     │
   │       │ YES      │    │ NO           │                     │
   │       └────┬─────┘    └──────┬───────┘                     │
   │            │                 │                              │
   │            ▼                 │                              │
   │    ┌───────────────┐         │                             │
   │    │ Resume from   │         │                             │
   │    │ checkpoint    │         │                             │
   │    │ (<5s)         │         │                             │
   │    └───────┬───────┘         │                             │
   │            │                 │                              │
   │            └─────────┬───────┘                             │
   │                      ▼                                      │
   │    3. context.enable_auto_checkpoint(config)               │
   │                      │                                      │
   │                      ▼                                      │
   │    ┌────────────────────────────────────────────┐          │
   │    │ Auto-Checkpoint Active:                    │          │
   │    │ - Interval timer: Every 30 minutes         │          │
   │    │ - Task completion: Every 5 tasks           │          │
   │    │ - Interrupt handler: On Ctrl+C             │          │
   │    └─────────────────┬──────────────────────────┘          │
   │                      ▼                                      │
   │    4. Execute mission workflow:                            │
   │       - Scout files                                        │
   │       - Create plan                                        │
   │       - Execute tasks ◄─────┐                             │
   │         │                   │                             │
   │         └──► on_task_complete() (checkpoint trigger)      │
   │                             │                             │
   │                             ▼                             │
   │    5. Phase completion:                                   │
   │       trigger_checkpoint(reason="phase_complete")         │
   │                                                            │
   │    6. context.disable_auto_checkpoint()                   │
   └────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────────┐
   │                     AgentContext                             │
   │                                                              │
   │  _checkpoint_manager: CheckpointManager | None               │
   │                                                              │
   │  enable_auto_checkpoint(config):                            │
   │    - Create CheckpointManager instance                      │
   │    - Start auto-checkpoint triggers                         │
   │                                                              │
   │  get_checkpoint_manager():                                  │
   │    - Return CheckpointManager instance                      │
   │                                                              │
   │  disable_auto_checkpoint():                                 │
   │    - Stop background timer                                  │
   │    - Restore signal handlers                                │
   └──────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────────┐
   │                   CheckpointManager                          │
   │                                                              │
   │  start_auto_checkpoint(context, task_id):                   │
   │    - Start interval timer (background thread)               │
   │    - Install SIGINT handler                                 │
   │    - Initialize task counter                                │
   │                                                              │
   │  on_task_complete(context):                                 │
   │    - Increment task_count                                   │
   │    - If task_count % interval_tasks == 0:                   │
   │        trigger_checkpoint(reason="task_complete")           │
   │                                                              │
   │  trigger_checkpoint(context, reason):                       │
   │    - save_checkpoint(session_state, session_id)             │
   │    - Log telemetry                                          │
   │                                                              │
   │  resume_from_checkpoint(session_id):                        │
   │    - Fallback recovery (3 attempts)                         │
   │    - Restore AgentContext                                   │
   │    - Log resume metrics                                     │
   └──────────────────────────────────────────────────────────────┘
```

---

## 5. Retention Policy Cleanup

```
┌─────────────────────────────────────────────────────────────────┐
│                   CHECKPOINT CLEANUP WORKFLOW                    │
└─────────────────────────────────────────────────────────────────┘

   Session Start (before new checkpoints)
           │
           ▼
   ┌─────────────────────────────────────┐
   │ cleanup_old_checkpoints(session_id) │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │ Scan checkpoints directory:                                  │
   │ - checkpoint_001 (oldest, 8 days ago)                        │
   │ - checkpoint_002 (7 days ago)                                │
   │ - checkpoint_003 (6 days ago)                                │
   │ - checkpoint_004 (5 days ago)                                │
   │ - checkpoint_005 (4 days ago)                                │
   │ - checkpoint_006 (3 days ago)                                │
   │ - checkpoint_007 (2 days ago)                                │
   │ - checkpoint_008 (1 day ago)                                 │
   │ - checkpoint_009 (12 hours ago)                              │
   │ - checkpoint_010 (6 hours ago) ← LATEST                      │
   └──────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Rule 1: Keep last N checkpoints (N=5)                       │
   │                                                              │
   │ Keep:   006, 007, 008, 009, 010                             │
   │ Delete: 001, 002, 003, 004, 005                             │
   └──────────────┬──────────────────────────────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Rule 2: Delete older than M days (M=7)                      │
   │                                                              │
   │ Cutoff: 7 days ago                                          │
   │ Delete: 001 (8 days), 002 (7.5 days)                        │
   └──────────────┬──────────────────────────────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ Result:                                                      │
   │ - Deleted: 5 checkpoints (001-005)                          │
   │ - Kept: 5 checkpoints (006-010)                             │
   │ - Disk space reclaimed: ~15KB (3KB × 5)                     │
   │ - Log telemetry: deleted_count=5, disk_reclaimed_kb=15      │
   └─────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────┐
   │ Debug Mode: checkpoint_retention_count = -1                 │
   │                                                              │
   │ Keep: ALL checkpoints (no deletion)                         │
   │ Use: Debugging, forensic analysis, long-term audits         │
   └─────────────────────────────────────────────────────────────┘
```

---

## 6. Thread Safety Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREAD-SAFE OPERATIONS                        │
└─────────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────────────┐
   │                    CheckpointManager                          │
   │                                                              │
   │  _lock: threading.Lock                                       │
   │  _timer_thread: threading.Thread                            │
   │  _stop_timer: threading.Event                               │
   └──────────────────────────────────────────────────────────────┘

   Main Thread                    Timer Thread (daemon)
   ────────────                   ──────────────────────

   trigger_checkpoint()           _timer_loop():
         │                              │
         ▼                              ▼
   ┌─────────────┐              ┌─────────────────┐
   │ Acquire     │              │ sleep(30 min)   │
   │ _lock       │              └────────┬────────┘
   └─────┬───────┘                       │
         │                               ▼
         ▼                        ┌─────────────────┐
   ┌─────────────────────┐        │ Acquire _lock   │
   │ save_checkpoint()   │        └────────┬────────┘
   └──────────┬──────────┘                 │
              │                            ▼
              ▼                     ┌─────────────────┐
   ┌──────────────────────┐         │ trigger_       │
   │ Release _lock        │         │ checkpoint()   │
   └──────────────────────┘         └────────┬───────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │ Release _lock   │
                                     └────────┬────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │ Loop until      │
                                     │ _stop_timer set │
                                     └─────────────────┘

   ┌──────────────────────────────────────────────────────────────┐
   │ Atomic File Write (POSIX guarantees):                        │
   │                                                              │
   │ 1. Write to temp file:    checkpoint_123.tmp                │
   │ 2. Atomic rename:         checkpoint_123.tmp → 123.json     │
   │                                                              │
   │ Result: Never partial checkpoint (all or nothing)           │
   └──────────────────────────────────────────────────────────────┘
```

---

## 7. Directory Structure

```
~/.agency/
└── sessions/
    └── {session_id}/
        └── checkpoints/
            ├── checkpoint_20251010_143022_001234.json  # Oldest
            ├── checkpoint_20251010_143522_002345.json
            ├── checkpoint_20251010_144022_003456.json
            ├── checkpoint_20251010_144522_004567.json
            └── checkpoint_20251010_145022_005678.json  # Latest

Each checkpoint file contains:
{
  "checkpoint_id": "checkpoint_20251010_145022_005678",
  "timestamp": "2025-10-10T14:50:22.123456",
  "session_state_json": "{...}",  # Serialized SessionState
  "checksum": "a3f5b2d9..."        # SHA256 hex digest (64 chars)
}

SessionState includes:
- session_id
- agent_name
- status (RUNNING, CHECKPOINTED, etc.)
- metadata (dict[str, JSONValue])
- memory_snapshots (list[dict])
- task_id, task_progress_percent
- completed_steps, pending_steps
- active_memory_refs, pinned_memories
```

---

## 8. Error Recovery Decision Tree (Visual)

```
load_checkpoint(checkpoint_id)
       │
       ▼
┌──────────────────┐
│ Read checkpoint  │
│ file from disk   │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│ Calculate SHA256         │
│ (session_state_json)     │
└────────┬─────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
YES ✓      NO ✗
┌───────┐  ┌────────────────────────┐
│SUCCESS│  │ CHECKSUM MISMATCH      │
│       │  │ (CORRUPTED)            │
│Return │  └──────────┬─────────────┘
│state  │             │
└───────┘             ▼
              ┌────────────────────┐
              │ Find previous      │
              │ checkpoint         │
              └──────────┬─────────┘
                         │
                    ┌────┴────┐
                    │         │
                    ▼         ▼
                 FOUND    NOT FOUND
              ┌────────┐  ┌──────────────────┐
              │ Retry  │  │ ALL CHECKPOINTS  │
              │ (max 3)│  │ CORRUPTED        │
              └────────┘  │                  │
                          │ Return Err(...)  │
                          └──────────────────┘
```

---

**Specification**: `specs/checkpoint_manager_spec.md`
**Summary**: `specs/CHECKPOINT_MANAGER_SUMMARY.md`
