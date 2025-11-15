# night-shift - Autonomous 24/7 Development (Mission 5)

**Context**: You are executing the `/night-shift` command to manage autonomous 24/7 development operations.

## Mission

Enable continuous autonomous development through:
1. **Scheduled Execution**: Run primeX orchestrator on configurable schedule
2. **Auto-Recovery**: Detect and recover from failures automatically
3. **Health Monitoring**: Monitor system resources before execution
4. **Safety Controls**: Kill switch, rate limits, dry-run mode

## Usage Modes

### Mode 1: Start Night Shift
```
/night-shift start
```

**Behavior**:
- Starts Night Shift scheduler with default configuration
- Schedule: Every 4 hours (0 */4 * * *)
- Max tasks per execution: 3
- Auto-selects highest-priority tasks from backlog
- Logs all operations to `~/.agency/logs/night_shift/`

**Safety Controls**:
- Health check before each cycle (disk, memory, CPU, git status)
- Min interval between executions: 15 minutes
- Resource monitoring: Abort if CPU >90% or memory >80%
- Kill switch: Create `~/.agency/STOP_NIGHT_SHIFT` to stop

### Mode 2: Stop Night Shift
```
/night-shift stop
```

**Behavior**:
- Creates kill switch file (`~/.agency/STOP_NIGHT_SHIFT`)
- Scheduler will stop gracefully on next check
- Current task will complete before shutdown
- State saved for resume

### Mode 3: Status Check
```
/night-shift status
```

**Behavior**:
- Shows last execution time
- Total tasks completed
- Total failures
- Total escalations
- Current health status

### Mode 4: Run One Cycle (Testing)
```
/night-shift run-once
```

**Behavior**:
- Executes one cycle immediately (for testing)
- Respects all safety controls
- Logs to standard location

### Mode 5: Custom Schedule
```
/night-shift start --schedule "0 2 * * *"
```

**Behavior**:
- Starts Night Shift with custom cron schedule
- Example: "0 2 * * *" = 2 AM daily
- Example: "*/30 * * * *" = Every 30 minutes

### Mode 6: Dry Run Mode
```
/night-shift start --dry-run
```

**Behavior**:
- Logs task selection and intent without execution
- Useful for testing schedule and task prioritization
- No actual code changes or PRs created

## Auto-Recovery Features

### Failure Detection
- **Test failures**: pytest exit code != 0
- **Build errors**: SyntaxError, compilation failures
- **Git failures**: merge conflicts, push failures
- **Timeouts**: Task exceeds max duration (60 minutes)
- **Resource exhaustion**: OOM, disk full

### Recovery Actions
1. **Automatic Rollback**: Git reset to last known good state
2. **Retry Logic**: Exponential backoff (0s, 30s, 120s)
3. **Escalation**: User notification when recovery fails

### Escalation
- Creates file: `~/.agency/escalations/<task_id>.json`
- Contains: Task details, failure reason, recovery attempts
- Optional: Email notification (if configured)

## Health Monitoring

### Health Checks
- **Disk space**: >10GB free required
- **Memory**: <80% utilization required
- **CPU**: <90% average utilization required
- **Git repo**: Clean working tree required
- **Dependencies**: All required packages installed

### Abort Conditions
- Health check fails
- Kill switch file exists
- Resource exhaustion detected
- Min interval not met

## Configuration

**Location**: `~/.agency/config/night_shift.yaml`

**Example Configuration**:
```yaml
schedule: "0 */4 * * *"  # Every 4 hours
max_tasks_per_execution: 3
min_interval_minutes: 15
max_task_duration_minutes: 60
dry_run: false
enable_notifications: false
notification_email: null
```

## Logs & State

**Logs**: `~/.agency/logs/night_shift/YYYY-MM-DD.log`
**State**: `~/.agency/state/night_shift_state.json`
**Escalations**: `~/.agency/escalations/`

## Safety Controls

### Kill Switch
- **File**: `~/.agency/STOP_NIGHT_SHIFT`
- **Action**: Immediate graceful shutdown
- **Usage**: `/night-shift stop` or `touch ~/.agency/STOP_NIGHT_SHIFT`

### Rate Limits
- **Max tasks per cycle**: 3 (default)
- **Min interval**: 15 minutes (default)
- **Max concurrent ops**: 1 (sequential only)
- **Max task duration**: 60 minutes (timeout)

### Dry Run Mode
- **Purpose**: Test scheduling without execution
- **Usage**: `--dry-run` flag
- **Logs**: All intent logged, no actual execution

## Integration with Prior Missions

- **Mission 0 (CMP)**: Stores clade performance data
- **Mission 2 (Learning)**: Extracts patterns from completions
- **Mission 3 (Self-Healing)**: Fixes test failures automatically
- **Mission 4 (Backlog)**: Auto-selects tasks from priority queue

## Example Workflow

```
User: /night-shift start --schedule "0 2 * * *"

Claude:
  🌙 Starting Night Shift scheduler...

  Configuration:
  - Schedule: 2 AM daily
  - Max tasks per execution: 3
  - Min interval: 15 minutes
  - Dry run: false

  Health Check:
  ✅ Disk space: 25.3 GB free
  ✅ Memory: 37.2% utilized
  ✅ CPU: 12.1% utilized
  ✅ Git repo: Clean

  Night Shift scheduler started.
  Next execution: 2025-11-16 02:00:00

  To stop: /night-shift stop
  To check status: /night-shift status

  Logs: ~/.agency/logs/night_shift/2025-11-15.log
```

## Monitoring

**Real-time logs**:
```bash
tail -f ~/.agency/logs/night_shift/$(date +%Y-%m-%d).log
```

**Check escalations**:
```bash
ls ~/.agency/escalations/
cat ~/.agency/escalations/<task_id>.json
```

**View state**:
```bash
cat ~/.agency/state/night_shift_state.json
```

## Constitutional Compliance

**Article I**: Complete Context
- Health checks before each execution
- Retry on timeout (complete or abort, no partial work)

**Article II**: 100% Verification
- Tests MUST pass before marking complete
- Auto-recovery verifies green state after rollback

**Article III**: Automated Enforcement
- Safety controls enforced (no manual bypass)
- Kill switch is absolute

**Article IV**: Continuous Learning
- VectorStore query before task selection
- VectorStore store after completion

**Article V**: Spec-Driven
- Implemented per spec-mission-5-night-shift-auto-recovery.md

**Article VI**: TDD Protocol
- 35/35 tests passing (100%)
- Tests written FIRST, implementation SECOND

## References

- **Spec**: `specs/spec-mission-5-night-shift-auto-recovery.md`
- **Implementation**: `tools/night_shift_scheduler.py`, `tools/auto_recovery.py`, `tools/health_monitor.py`
- **Tests**: `tests/test_night_shift_scheduler.py`, `tests/test_auto_recovery.py`
- **Mission 4**: primeX orchestrator (task execution)

---

**Now execute the night-shift operation following the above protocol.**
