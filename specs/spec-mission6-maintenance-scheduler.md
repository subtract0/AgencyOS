# Mission 6 Spec: Autonomous Maintenance Scheduler

**Owner**: CodingAgent / PlannerAgent  
**Last Updated**: 2025-11-15  
**Status**: Draft (ready for implementation)

## Goal
Run recurring maintenance jobs (tests, audits, learning consolidation) on a configurable cadence without manual triggers, ensuring AgencyOS meets Meta Productivity 2.0 uptime and quality targets.

## Success Criteria
1. CLI `python trinity_protocol/scheduler.py start` runs persistent loop (similar to Night Shift but purpose-built for recurring jobs).
2. Job definitions stored in `config/maintenance_jobs.yaml` (cron syntax + command/function).
3. Default jobs:
   - **Daily @ 02:00**: `python run_tests.py --focused` and store summarized results.
   - **Daily @ 03:00**: Run LearningAgent consolidation and post summary to `logs/learning_reports/`.
   - **Weekly Monday @ 04:00**: Auto cost review (call cost dashboard script) + backlog of optimization tasks.
   - **Weekly Wednesday @ 05:00**: CMP health audit (ensure event success rate >70%).
   - **Monthly 1st @ 06:00**: Dependency check (`poetry check` or `pip list --outdated`).
4. Scheduler persists state to `~/.agency/state/maintenance_scheduler.json` (last run, job status, retries).
5. Supports manual run: `python trinity_protocol/scheduler.py run --job daily_tests`.
6. Integrates with Witness/Auto-Trigger by emitting events for failed jobs.

## Functional Requirements
- Cron parsing via `croniter` (already dependency from Night Shift).
- Job Execution Abstractions:
  - ShellCommandJob (runs bash command)
  - PythonCallableJob (imports function)
  - CompositeJob (sequence of sub-jobs)
- Retry policy per job (default 1 retry, exponential backoff).
- Logging to `~/.agency/logs/maintenance_scheduler/<date>.log`.

## Implementation Outline
- Module `trinity_protocol/scheduler.py` containing:
  - `MaintenanceJob` dataclass (id, cron, type, payload, retries).
  - `MaintenanceScheduler` class with `run_forever()` and `run_job(job)`.
  - YAML loader converting config file into job objects (fallback to built-in defaults if file missing).
- Provide `config/maintenance_jobs.yaml` template with default jobs.
- Hook into Witness/AutoTrigger by writing events on failure (optional v1 but prepare stub).

## Testing
- `tests/test_maintenance_scheduler.py`
  - Cron next-run calculation
  - Job execution success + retry logic
  - State persistence roundtrip
  - CLI argument parsing smoke test

## Metrics & Reporting
- Append JSON lines to log with job_id, status, duration, retries, output snippet path.
- After each job, persist summary to `logs/maintenance_reports/<job_id>/<timestamp>.json` for dashboard ingestion.

## Dependencies / Risks
- Jobs may be resource intensive; schedule windows accordingly.
- Need to avoid conflict with Night Shift (e.g., running tests while Night Shift modifies repo). Provide locking via `.agency/locks/maintenance.lock`.
