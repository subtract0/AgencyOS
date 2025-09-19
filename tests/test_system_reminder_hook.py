from typing import Any

import pytest

from shared.system_hooks import create_system_reminder_hook


class MockMessageStore:
    def __init__(self):
        self.messages = []


class MockThreadManager:
    def __init__(self):
        self._store = MockMessageStore()


class MockContext:
    def __init__(self, with_todos: bool = True):
        self._data = {}
        if with_todos:
            self._data["todos"] = {
                "todos": [
                    {"id": "1", "content": "Task A", "status": "pending"},
                    {"id": "2", "content": "Task B", "status": "in_progress"},
                    {"id": "3", "content": "Task C", "status": "completed"},
                ]
            }
        self.thread_manager = MockThreadManager()

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value


class MockRunContextWrapper:
    def __init__(self, context: MockContext):
        self.context = context


class MockAgent:
    pass


@pytest.mark.asyncio
async def test_injects_system_message_and_clears_pending():
    hook = create_system_reminder_hook()
    ctx = MockRunContextWrapper(MockContext())
    agent = MockAgent()

    # Manually inject a pending reminder
    ctx.context.set(
        "pending_system_reminder", "<system-reminder>test</system-reminder>"
    )

    input_items = []
    await hook.on_llm_start(ctx, agent, system_prompt=None, input_items=input_items)

    assert input_items, "Input items should not be empty after injection"
    assert input_items[0]["role"] == "system"
    assert "<system-reminder>" in input_items[0]["content"]
    assert ctx.context.get("pending_system_reminder") is None, (
        "Pending reminder must be cleared"
    )


@pytest.mark.asyncio
async def test_includes_todo_status_when_present():
    hook = create_system_reminder_hook()
    ctx = MockRunContextWrapper(MockContext(with_todos=True))
    agent = MockAgent()

    # Trigger reminder creation and storage
    await hook.on_start(ctx, agent)

    # Now LLM call should receive the system message
    input_items = []
    await hook.on_llm_start(ctx, agent, system_prompt=None, input_items=input_items)

    content = input_items[0]["content"]
    assert "# Current TODO List Status" in content
    assert "pending tasks" in content
    assert "in-progress tasks" in content
    assert "completed tasks" in content


@pytest.mark.asyncio
async def test_fallback_when_todos_absent():
    hook = create_system_reminder_hook()
    ctx = MockRunContextWrapper(MockContext(with_todos=False))
    agent = MockAgent()

    await hook.on_start(ctx, agent)

    input_items = []
    await hook.on_llm_start(ctx, agent, system_prompt=None, input_items=input_items)

    content = input_items[0]["content"]
    assert "# TODO List" in content
    assert "Consider using the TodoWrite tool" in content


@pytest.mark.asyncio
async def test_triggers_after_15_tool_calls():
    hook = create_system_reminder_hook()
    ctx = MockRunContextWrapper(MockContext(with_todos=True))
    agent = MockAgent()

    # 14 tool ends should not inject yet
    for _ in range(14):
        await hook.on_tool_end(ctx, agent, tool=None, result="ok")
        assert ctx.context.get("pending_system_reminder") is None

    # 15th should inject
    await hook.on_tool_end(ctx, agent, tool=None, result="ok")
    assert ctx.context.get("pending_system_reminder") is not None
