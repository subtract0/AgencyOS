"""
System reminder hook for Agency Code to inject periodic reminders about important instructions.

Triggers reminders:
- Every 15 tool calls
- After every user message

Reminders include:
- Important instruction reminders
- Current TODO list status
"""

from typing import Optional

from agents import AgentHooks, RunContextWrapper


class SystemReminderHook(AgentHooks):
    """
    Hook class to track tool calls and user messages, injecting system reminders
    every 15 tool calls and after each user message.
    """

    def __init__(self):
        self.tool_call_count = 0

    async def on_start(self, context: RunContextWrapper, agent) -> None:
        """Called when agent starts processing a user message or is activated."""
        # Inject reminder after every user message
        self._inject_reminder(context, "user_message")

    async def on_end(self, context: RunContextWrapper, agent, output) -> None:
        """Called when the agent finishes processing a user message."""
        return None

    async def on_handoff(self, context: RunContextWrapper, *args, **kwargs) -> None:
        """Called when a handoff occurs.

        Supports both call styles:
        - RunHooks: on_handoff(context, from_agent=..., to_agent=...)
        - AgentHooks: on_handoff(context, agent=..., source=...)
        """
        return None

    async def on_tool_start(self, context: RunContextWrapper, agent, tool) -> None:
        """Called before each tool execution."""
        return None

    async def on_tool_end(
        self, context: RunContextWrapper, agent, tool, result: str
    ) -> None:
        """Called after each tool execution."""
        self.tool_call_count += 1

        # Check if we should trigger a reminder after 15 tool calls
        if self.tool_call_count >= 15:
            self._inject_reminder(context, "tool_call_limit")
            self.tool_call_count = 0

    async def on_llm_start(
        self,
        context: RunContextWrapper,
        agent,
        system_prompt: Optional[str],
        input_items: list,
    ) -> None:
        """Inject pending system reminder as a system message before the LLM call."""
        try:
            pending = None
            if hasattr(context, "context"):
                pending = context.context.get("pending_system_reminder", None)

            if pending:
                try:
                    # Prepend a system message with the reminder
                    input_items.insert(0, {"role": "system", "content": pending})
                except Exception:
                    # If input items cannot be modified, store for later attempts
                    pass

                # Clear the pending reminder so it's injected only once
                context.context.set("pending_system_reminder", None)
        except Exception:
            # Do not interrupt the flow if injection fails
            return None

    async def on_llm_end(self, context: RunContextWrapper, agent, response) -> None:
        """Called after the LLM returns a response."""
        return None

    # Compatibility wrappers so runner can call run-level names even if this is AgentHooks
    async def on_agent_start(
        self, context: RunContextWrapper, agent, *args, **kwargs
    ) -> None:
        await self.on_start(context, agent)

    async def on_agent_end(
        self, context: RunContextWrapper, agent, output, *args, **kwargs
    ) -> None:
        return None

    def _inject_reminder(self, ctx: RunContextWrapper, trigger_type: str) -> None:
        """
        Inject system reminder into the conversation history.

        Args:
            ctx: The run context wrapper containing threads and agency context
            trigger_type: Either "tool_call_limit" or "user_message"
        """
        try:
            # Get current todos from context
            current_todos = self._get_current_todos(ctx)

            # Create the reminder message
            reminder_message = self._create_reminder_message(
                trigger_type, current_todos
            )

            # Inject the reminder into the conversation history
            self._add_system_reminder_to_thread(ctx, reminder_message)

        except Exception as e:
            # Graceful degradation - don't break the flow if reminder injection fails
            print(f"Warning: Failed to inject system reminder: {e}")

    def _get_current_todos(self, ctx: RunContextWrapper) -> Optional[list]:
        """Get current todos from shared context."""
        try:
            if hasattr(ctx, "context"):
                todos_payload = ctx.context.get("todos", {})
                return todos_payload.get("todos", [])
        except Exception:
            pass
        return None

    def _create_reminder_message(self, trigger_type: str, todos: Optional[list]) -> str:
        """Create the system reminder message."""
        reminder = """<system-reminder>
# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

"""

        # Add current TODO status if available
        if todos:
            reminder += "# Current TODO List Status\n"
            pending_count = sum(1 for todo in todos if todo.get("status") == "pending")
            in_progress_count = sum(
                1 for todo in todos if todo.get("status") == "in_progress"
            )
            completed_count = sum(
                1 for todo in todos if todo.get("status") == "completed"
            )

            reminder += f"- {pending_count} pending tasks\n"
            reminder += f"- {in_progress_count} in-progress tasks\n"
            reminder += f"- {completed_count} completed tasks\n"

            if in_progress_count > 0:
                reminder += "\nCurrent in-progress tasks:\n"
                for todo in todos:
                    if todo.get("status") == "in_progress":
                        reminder += f"- {todo.get('task', 'Unknown task')}\n"
        else:
            reminder += "# TODO List\nConsider using the TodoWrite tool to plan and track your tasks.\n"

        reminder += (
            "\nIMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context or otherwise consider it in your response unless it is highly relevant to your task. Most of the time, it is not relevant.\n</system-reminder>"
            ""
        )

        return reminder

    def _add_system_reminder_to_thread(
        self, ctx: RunContextWrapper, reminder_message: str
    ) -> None:
        """
        Add system reminder message to the conversation thread.

        Note: Based on user conversation, we can mutate conversation history through context.
        """
        try:
            # Store the reminder in the context for the agent to access
            # This will be picked up by the agent and included in responses
            ctx.context.set("pending_system_reminder", reminder_message)

        except Exception as e:
            print(f"Warning: Could not inject reminder into conversation: {e}")


# Factory function to create the hook
def create_system_reminder_hook():
    """Create and return a SystemReminderHook instance."""
    return SystemReminderHook()


if __name__ == "__main__":
    # Test the hook creation
    hook = create_system_reminder_hook()
    print("SystemReminderHook created successfully")
    print(f"Initial tool call count: {hook.tool_call_count}")

    # Test reminder message creation
    test_todos = [
        {"task": "Test task 1", "status": "pending"},
        {"task": "Test task 2", "status": "in_progress"},
        {"task": "Test task 3", "status": "completed"},
    ]

    reminder = hook._create_reminder_message("tool_call_limit", test_todos)
    print("\nSample reminder message:")
    print(reminder)
