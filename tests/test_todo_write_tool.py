from pathlib import Path
from claude_code.tools.todo_write import TodoWrite, TodoItem


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


