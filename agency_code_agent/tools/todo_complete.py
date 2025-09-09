from datetime import datetime
from typing import Any, Dict, List, Optional

from agency_swarm.tools import BaseTool
from pydantic import Field


class TodoComplete(BaseTool):
    """
    Marks a todo item as completed and returns the updated remaining items summary.

    - If `number` is provided, completes that item by 1-based index in the current list order
    - If not provided, automatically completes the next actionable todo (first pending, else first in_progress)
    - Updates are persisted in shared context under key "todos"
    - Returns a plain-text summary of remaining todos grouped by status
    """

    number: Optional[int] = Field(
        default=None,
        description="1-based index of the todo to complete. If omitted, completes the next actionable item automatically.",
    )

    def _load_todos(self) -> List[Dict[str, Any]]:
        todos: List[Dict[str, Any]] = []
        if self.context is not None:
            todos = self.context.get("todos", []) or []
        # Fallback: import from write tool's module-level store
        if not todos:
            try:
                from agency_code_agent.tools.todo_write import _GLOBAL_TODOS, TodoWrite

                if _GLOBAL_TODOS:
                    todos = list(_GLOBAL_TODOS)
                if not todos:
                    todos = TodoWrite.load_existing_todos()
            except Exception:
                pass
        return list(todos)

    def _save_todos(self, todos: List[Dict[str, Any]]):
        if self.context is not None:
            self.context.set("todos", todos)
        # Fallback: also persist to write tool's global store
        try:
            import agency_code_agent.tools.todo_write as tw

            tw._GLOBAL_TODOS = list(todos)
        except Exception:
            pass

    def run(self) -> str:
        todos = self._load_todos()
        if not todos:
            return "No todos found."

        idx: Optional[int] = None
        if self.number is not None:
            if self.number < 1 or self.number > len(todos):
                return (
                    f"Invalid todo number: {self.number}. There are {len(todos)} todos."
                )
            idx = self.number - 1
        else:
            for i, t in enumerate(todos):
                if t.get("status") == "pending":
                    idx = i
                    break
            if idx is None:
                for i, t in enumerate(todos):
                    if t.get("status") == "in_progress":
                        idx = i
                        break
            if idx is None:
                return "All todos are already completed."

        todos[idx]["status"] = "completed"
        todos[idx]["completed_at"] = datetime.now().isoformat()
        self._save_todos(todos)

        remaining = [t for t in todos if t.get("status") != "completed"]

        # Build summary of remaining items
        status_groups = {"in_progress": [], "pending": []}
        for t in remaining:
            status = t.get("status")
            if status in status_groups:
                status_groups[status].append(t)

        lines: List[str] = []
        lines.append("Todo updated: marked one item as completed\n")
        lines.append(f"Remaining: {len(remaining)} items\n")

        if status_groups["in_progress"]:
            lines.append("IN PROGRESS:")
            for t in status_groups["in_progress"]:
                lines.append(
                    f"  [{t.get('priority', 'MED').upper()}] {t.get('content', '')}"
                )
            lines.append("")

        if status_groups["pending"]:
            lines.append("PENDING:")
            for t in status_groups["pending"]:
                lines.append(
                    f"  [{t.get('priority', 'MED').upper()}] {t.get('content', '')}"
                )
            lines.append("")

        return "\n".join(l for l in lines if l is not None).strip()


# Create alias for Agency Swarm tool loading (expects class name = file name)
todo_complete = TodoComplete
