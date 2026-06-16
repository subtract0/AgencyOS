# Kanban and Worker Protocol

## Worker loop

Each worker repeats:

1. Read current policy.
2. Read Kanban pool.
3. Claim the highest-priority eligible task for its role.
4. Write a claim record.
5. Execute within the task's allowed scope.
6. Write artifacts.
7. Run validation.
8. Update task status with evidence.
9. Release claim.
10. Claim the next eligible task.

## Task status flow

BACKLOG -> READY -> CLAIMED -> IN_PROGRESS -> AWAITING_VALIDATION -> VALIDATED -> DONE

Alternative paths:

- IN_PROGRESS -> NEEDS_REPAIR
- IN_PROGRESS -> NEEDS_TRACE
- IN_PROGRESS -> NEEDS_HUMAN
- IN_PROGRESS -> STUCK
- AWAITING_VALIDATION -> NEEDS_REPAIR

DONE means validated evidence exists. An agent statement is not enough.

## Required task fields

- task_id
- title
- track
- required_role
- priority
- risk_level
- status
- dependencies
- objective
- inputs
- expected_artifacts
- definition_of_done
- validation
- max_runtime_minutes
- max_retries
- stale_after_minutes
- allowed_paths
- forbidden_paths
- escalation_conditions

## WIP limits

Suggested defaults:

- s1 / Qwen3.6: 1 active task plus 1 queued next task
- s2 / Qwopus: 1 active task
- mbp1 / Gemma: 1 active task plus 1 queued next task

## Task creation rule

Workers may create child tasks only when the child task is specific, bounded, and has validation criteria.

Bad: improve benchmark system.

Good: create a validator that rejects gap-matrix rows missing model, domain, pass, failure_type, and artifact_path.
