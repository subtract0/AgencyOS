from pathlib import Path

from tools.todo_write import TodoItem, TodoWrite


def test_todo_write_no_emojis_and_summary(tmp_path: Path):
    todos = [
        TodoItem(task="Do A", status="pending"),
        TodoItem(task="Do B", status="completed", priority="low"),
    ]
    tool = TodoWrite(todos=todos)
    out = tool.run()
    assert "Todo List Updated" in out
    assert "Summary:" in out
    # Ensure no emoji characters in the output
    assert "🚧" not in out and "✅" not in out and "💡" not in out


def test_todo_write_minimal_format():
    todos = [
        TodoItem(task="A", status="in_progress"),
        TodoItem(task="B", status="pending", priority="low"),
    ]
    out = TodoWrite(todos=todos).run()
    assert "IN PROGRESS:" in out
    assert "PENDING:" in out
    assert "COMPLETED" not in out or "COMPLETED (showing last" in out
