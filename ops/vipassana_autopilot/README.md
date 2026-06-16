# Vipassana Autopilot: AgencyOS Completion Engine v0

This folder is a launch package for running AgencyOS productively during Alex's unattended 10-day+ window.

The system is designed as a **continuous autonomous Kanban worker pool** governed periodically by a **GPT-5.5 Hermes fleet governor**.

Workers should not wait for Hermes to hand them every task. Workers continuously claim bounded tasks from the pool, execute them, validate outputs, write append-only evidence, and claim the next eligible task. Hermes periodically audits, redirects, prunes, repairs, and improves the system.

## Mission

Build and validate AgencyOS Autopilot v0: a continuously running, append-only, self-auditing autonomous worker pool that advances the larger objective of creating an autonomous completion engine for unfinished valuable work.

Target asset classes:

- unfinished books
- unfinished PhDs and research projects
- incomplete software systems
- unfinished courses and programs
- business assets and strategic documents

## Primary deliverables

At the end of the run, the system should produce:

```text
ops/reports/vipassana_autopilot_final/
  01_EXECUTIVE_SUMMARY.md
  02_FLEET_RUN_LOG.md
  03_VALIDATED_ARTIFACTS_INDEX.md
  04_GAP_MATRIX_REPORT.md
  05_COMPLETION_BENCH_V0.md
  06_SYSTEM_FAILURES_AND_FIXES.md
  07_MODEL_STRENGTHS_AND_ROUTING_POLICY.md
  08_NEXT_30_DAY_PLAN.md
  09_HUMAN_REVIEW_QUEUE.md
  10_RAW_LEDGER_EXPORTS/
```

## Operating principle

Optimize for:

```text
reliability > evidence > useful artifacts > scale > cleverness
```

Do not optimize for agent busyness. DONE means validated by reproducible evidence.

## Start files

Read these in order:

1. `LAUNCH_ONE_LINER.txt`
2. `HERMES_GPT55_MASTER_PROMPT.md`
3. `OPERATING_POLICY.md`
4. `KANBAN_AND_WORKER_PROTOCOL.md`
5. `MULTI_MACHINE_TOPOLOGY.md`
6. `SEED_BACKLOG.txt`
7. `SAFE_MODE_BACKLOG.md`
8. `DASHBOARD_TEMPLATE.txt`

## Governance model

- Local workers run continuously.
- Local dispatcher enforces task claiming and WIP limits.
- Watchdog catches stale tasks, broken workers, looping failures, and dangerous states.
- GPT-5.5 Hermes governs every 5 hours or on explicit operator request.
- RED-SAFE freezes only unsafe subsystems and continues safe productive backlog.
- BLACK halt is reserved for security, money, publication, deletion, external upload, credential, destructive, or unrecoverable corruption risks.

## Repository scope

This package is additive. It defines launch policy, worker protocol, topology, seed tasks, and return-report structure. It does not change production code.