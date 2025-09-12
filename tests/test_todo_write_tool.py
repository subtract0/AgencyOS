from pathlib import Path

from agency_code_agent.tools.todo_write import TodoItem, TodoWrite


def test_todo_write_no_emojis_and_summary(tmp_path: Path):
    todos = [
        TodoItem(content="Do A", status="pending", priority="high", id="1"),
        TodoItem(content="Do B", status="completed", priority="low", id="2"),
    ]
    tool = TodoWrite(todos=todos)
    out = tool.run()
    assert "Todo List Updated" in out
    assert "Summary:" in out
    # Ensure no emoji characters in the output
    assert "🚧" not in out and "✅" not in out and "💡" not in out


def test_todo_write_minimal_format():
    todos = [
        TodoItem(content="A", status="in_progress", priority="high", id="1"),
        TodoItem(content="B", status="pending", priority="low", id="2"),
    ]
    out = TodoWrite(todos=todos).run()
    assert "IN PROGRESS:" in out
    assert "PENDING:" in out
    assert "COMPLETED" not in out or "COMPLETED (showing last" in out
