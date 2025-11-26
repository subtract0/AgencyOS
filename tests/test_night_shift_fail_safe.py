import uuid
from unittest.mock import MagicMock

import tools.night_shift_scheduler as ns
from shared.models.backlog import Task, TaskPriority, TaskType
from shared.models.night_shift import NightShiftConfig
from tools.escalation_helper import EscalationResult


def test_handle_task_failure_escalates_when_threshold_reached(monkeypatch, tmp_path):
    config = NightShiftConfig(max_failures_before_block=1)
    scheduler = ns.NightShiftScheduler(config=config, state_dir=str(tmp_path))

    updated_task = Task(
        id=str(uuid.uuid4()),
        title="Failing task",
        description="keeps failing",
        task_type=TaskType.TECH_DEBT,
        priority=TaskPriority.P1,
        estimated_complexity=1,
    )

    scheduler.backlog_storage = MagicMock()
    scheduler.backlog_storage.record_task_failure.return_value = (updated_task, True)

    scheduler.backlog_storage.append_escalation_note = MagicMock()

    monkeypatch.setattr(
        ns,
        "escalate_with_llm",
        lambda *args, **kwargs: EscalationResult(provider="gemini-3.0-pro", analysis="plan"),
    )

    scheduler._handle_task_failure(updated_task, "boom")

    scheduler.backlog_storage.append_escalation_note.assert_called_once_with(
        updated_task.id, "gemini-3.0-pro", "plan"
    )
