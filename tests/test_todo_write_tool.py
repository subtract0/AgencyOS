from pathlib import Path

from agency_code_agent.tools.todo_complete import TodoComplete
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


def test_todo_complete_next_and_specific():
    # Seed context via TodoWrite
    initial = [
        TodoItem(content="Task A", status="pending", priority="high", id="a1"),
        TodoItem(content="Task B", status="in_progress", priority="medium", id="b1"),
        TodoItem(content="Task C", status="pending", priority="low", id="c1"),
    ]
    write_tool = TodoWrite(todos=initial)
    write_tool.run()

    # Complete next (should pick first pending: Task A)
    complete_tool1 = TodoComplete()
    res1 = complete_tool1.run()
    assert "Todo updated: marked one item as completed" in res1
    assert "Remaining:" in res1

    # Complete specific by number (2 -> now should target current list order)
    complete_tool2 = TodoComplete(number=2)
    res2 = complete_tool2.run()
    assert "Todo updated: marked one item as completed" in res2
