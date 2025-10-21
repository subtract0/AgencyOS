# Start Overnight Agents

**Command**: `/start-overnight-agents`

**Purpose**: Launch the Autonomous Night Watch system to execute maintenance and refactoring tasks overnight using distributed parallel workers.

## Overview

The Night Watch system enables continuous codebase improvement by running autonomous agent missions while you sleep. It uses the combined computing power of multiple machines (MacBook Pro M4 Pro + MacBook Air M4) to tackle technical debt, test coverage improvements, documentation updates, and refactoring tasks in parallel.

## Usage

```bash
/start-overnight-agents [--pro-threads N] [--air-threads N] [--mission-set NAME] [--enable-auto-pr] [--dry-run]
```

## Arguments

- `--pro-threads <N>`: Number of parallel workers on M4 Pro (default: 2, range: 1-10)
- `--air-threads <N>`: Number of parallel workers on M4 Air (default: 1, range: 0-5)
- `--mission-set <name>`: Predefined mission set to execute:
  - `refactoring`: Code quality and Pydantic migrations
  - `testing`: Test coverage improvements
  - `docs`: Documentation generation and updates
  - `full`: All enabled missions (default)
- `--enable-auto-pr`: Automatically create PRs for completed tasks
- `--dry-run`: Simulate execution without making changes

## Examples

```bash
# Start with defaults (2 M4 Pro workers, 1 M4 Air worker, full mission set)
/start-overnight-agents

# Focus on testing with 3 workers on M4 Pro
/start-overnight-agents --pro-threads 3 --mission-set testing

# Dry run to see what would execute
/start-overnight-agents --dry-run

# Auto-create PRs for completed tasks
/start-overnight-agents --enable-auto-pr --pro-threads 2
```

## How It Works

### Architecture

1. **Orchestrator** (`scripts/overnight_orchestrator.py`):
   - Loads missions from `overnight_missions.json`
   - Creates central task queue (`task_queue.json`)
   - Starts local worker threads on primary machine
   - Generates command for remote workers on secondary machine
   - Aggregates results and produces final report

2. **Workers** (`scripts/overnight_worker.py`):
   - Claim tasks from queue with atomic file locking
   - Create isolated git branch for each task: `night-watch/{mission-slug}-{timestamp}`
   - Execute `/primeA` command for the mission
   - Verify success criteria (exit code, tests, git status, push)
   - Update task status and log progress
   - Continue to next task until queue exhausted

3. **Task Queue** (`task_queue.json`):
   - Shared between orchestrator and workers
   - Atomic updates via `fcntl.flock()` file locking
   - Tracks task status (PENDING → IN_PROGRESS → COMPLETED/FAILED)

### Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    /start-overnight-agents                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Load missions from overnight_missions.json          │
│              Create task_queue.json (atomic locking)             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
  ┌─────────┐         ┌─────────┐         ┌─────────┐
  │ Worker 1│         │ Worker 2│         │ Worker 3│
  │ (M4 Pro)│         │ (M4 Pro)│         │ (M4 Air)│
  └────┬────┘         └────┬────┘         └────┬────┘
       │                   │                   │
       │ 1. Claim task (atomic lock)           │
       │ 2. Create git branch                  │
       │ 3. Execute /primeA command            │
       │ 4. Verify success criteria            │
       │ 5. Commit & push to branch            │
       │ 6. Update status in queue             │
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Aggregate results from all workers                  │
│              Generate orchestrator report                        │
│              Display summary with next steps                     │
└─────────────────────────────────────────────────────────────────┘
```

### Success Criteria (per task)

Each task must meet all 4 criteria before marking COMPLETED:

1. ✅ `/primeA` command exits with code 0
2. ✅ All tests pass (`python run_tests.py --run-all`)
3. ✅ Git status clean (no uncommitted changes)
4. ✅ Branch pushed to remote successfully

If any criterion fails, task marked as FAILED with error message.

## Morning Review

When you wake up, the orchestrator report shows:

- **Total tasks**: How many missions were in the queue
- **Completed**: Successfully finished tasks with git branches
- **Failed**: Tasks that failed with error messages
- **Conflicts**: Tasks with git merge conflicts
- **Timeouts**: Tasks that exceeded 60-minute limit
- **Branches created**: List of all `night-watch/*` branches ready for review
- **Next steps**: Recommended actions (review PRs, merge branches, investigate failures)

## Configuration

### Mission Definition (`overnight_missions.json`)

```json
{
  "missions": [
    {
      "id": "pydantic_migration",
      "title": "Migrate Dict[Any, Any] to Pydantic Models",
      "description": "Replace all Dict[Any, Any] with properly typed Pydantic models",
      "command": "/primeA 'Migrate all Dict[str, Any] to Pydantic models in agencyos_agent/'",
      "priority": 1,
      "estimated_duration_minutes": 30,
      "tags": ["refactoring", "type-safety"],
      "enabled": true
    },
    {
      "id": "api_docs_generation",
      "title": "Generate API Reference Documentation",
      "description": "Auto-generate API docs for all public agent interfaces",
      "command": "/primeA 'Generate API reference docs for all agent public methods'",
      "priority": 2,
      "estimated_duration_minutes": 20,
      "tags": ["docs"],
      "enabled": true
    }
  ]
}
```

### Remote Worker Setup (MacBook Air)

The orchestrator outputs a command to run on the secondary machine:

```bash
# On MacBook Air, run this command:
cd /path/to/Agency && python scripts/overnight_worker.py \
  --queue-file /path/to/task_queue.json \
  --worker-id worker-m4air-01 \
  --max-duration 60
```

## Constitutional Compliance

### Article I: Complete Context Before Action
- Exponential backoff retry on file lock contention (0.1s, 0.2s, 0.4s)
- Maximum 3 retry attempts before failure
- All 4 success criteria verified before task completion

### Article II: 100% Verification and Stability
- Full test suite run per task (`python run_tests.py --run-all`)
- Git status must be clean (no uncommitted changes)
- Branch push validated before marking complete

### Article III: Automated Merge Enforcement
- No manual overrides in orchestrator or workers
- Quality gates are absolute (all 4 criteria must pass)
- Failed tasks logged but execution continues

### Article IV: Continuous Learning and Improvement
- Task results stored in VectorStore for pattern recognition
- Failed missions analyzed for common issues
- Success patterns shared across future executions

### Article V: Spec-Driven Development
- Implementation traceable to spec-029
- All acceptance criteria from spec validated
- Git branch naming, file locking, status tracking per spec

## Error Handling

- **Git conflict**: Task marked as CONFLICT, logged for manual review
- **Test failure**: Task marked as FAILED with error message
- **Timeout**: Worker killed after 60 minutes, task marked as TIMEOUT
- **Worker crash**: Other workers continue, orchestrator reports crash in final summary
- **Lock contention**: Exponential backoff retry (Article I compliance)

## Logs

- **Worker logs**: `logs/overnight/{worker-id}-{timestamp}.log`
- **Orchestrator log**: Displayed in terminal + saved to `logs/overnight/orchestrator-{timestamp}.log`
- **Task queue**: `task_queue.json` (live status updates)

## Safety Features

- **Dry run mode**: Preview execution without making changes
- **Atomic file locking**: No concurrent queue access (fcntl.flock)
- **Isolated git branches**: No main branch contamination
- **Task timeout**: Maximum 60 minutes per task (configurable)
- **Worker independence**: Single worker failure doesn't affect others

## Future Enhancements (Post-MVP)

- **Redis/PostgreSQL queue**: Replace file-based queue for better scalability
- **Web dashboard**: Real-time monitoring of worker progress
- **Slack/Discord integration**: Notifications when missions complete
- **Auto-PR creation**: Default behavior for completed branches
- **Smart scheduling**: ML-based task duration prediction
- **Cost tracking**: API cost per mission for budget optimization

## See Also

- **Specification**: `specs/spec-029-autonomous-overnight-agents.md`
- **Orchestrator**: `scripts/overnight_orchestrator.py`
- **Worker**: `scripts/overnight_worker.py`
- **Models**: `shared/models/night_watch.py`
- **Tests**: `tests/test_overnight_orchestrator.py`, `tests/test_overnight_worker.py`

## Quick Start

```bash
# 1. Review missions to execute
cat overnight_missions.json

# 2. Start overnight agents
/start-overnight-agents --pro-threads 2 --air-threads 1

# 3. Go to sleep

# 4. Wake up and review orchestrator report

# 5. Review branches created
git branch | grep night-watch

# 6. Merge completed branches
git checkout night-watch/pydantic-migration-20251012-0315
# Review changes, run tests
git checkout main
git merge night-watch/pydantic-migration-20251012-0315
```

---

**Status**: Production-ready (Leap 7 compliant)
**Last Updated**: 2025-10-12
**Constitutional Articles**: I, II, III, IV, V
