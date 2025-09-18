from typing import Optional

from agents import AgentHooks, RunContextWrapper


class SystemReminderHook(AgentHooks):
    """
    System reminder hook for Agency Code to inject periodic reminders about important instructions.

    Triggers reminders:
    - Every 15 tool calls
    - After every user message

    Reminders include:
    - Important instruction reminders
    - Current TODO list status
    """

    def __init__(self):
        self.tool_call_count = 0

    async def on_start(self, context: RunContextWrapper, agent) -> None:
        """Called when agent starts processing a user message or is activated."""
        # Inject reminder after every user message
        self._inject_reminder(context, "user_message")
        filter_duplicates(context)

    async def on_end(self, context: RunContextWrapper, agent, output) -> None:
        """Called when the agent finishes processing a user message."""
        filter_duplicates(context)
        return None

    async def on_handoff(self, context: RunContextWrapper, agent, source) -> None:
        """Called when the agent is being handed off to. The `source` is the agent that is handing
        off to this agent."""
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


class MessageFilterHook(AgentHooks):
    """
    Message filter hook for Agency Code to filter duplicates and reorder messages.

    Used to remove duplicating tool call messages created when using anthropic models
    and reorder message order to make them compatible with the anthropic model.
    """

    async def on_start(self, context: RunContextWrapper, agent) -> None:
        """Called when agent starts processing a user message or is activated."""
        filter_duplicates(context)

    async def on_end(self, context: RunContextWrapper, agent, output) -> None:
        """Called when the agent finishes processing a user message."""
        filter_duplicates(context)


def filter_duplicates(context) -> None:
    """Filter duplicates and reorder messages."""

    thread_manager = context.context.thread_manager

    # Access the message store directly
    messages = thread_manager._store.messages

    # Step 1: Filter duplicates based on call_id for function calls
    call_ids_seen = set()
    deduplicated_messages = []

    for message in messages:
        call_id = message.get("call_id")

        if call_id and message.get("type") == "function_call":
            if call_id in call_ids_seen:
                continue
            else:
                call_ids_seen.add(call_id)
                deduplicated_messages.append(message)
        else:
            # Messages without call_id or non-function calls are always included
            deduplicated_messages.append(message)

    # Step 2: Reorder messages so function_call is immediately followed by function_call_output
    reordered_messages = []
    function_calls = {}  # call_id -> function_call message
    function_outputs = {}  # call_id -> function_call_output message

    # Separate messages by type
    for message in deduplicated_messages:
        msg_type = message.get("type")
        call_id = message.get("call_id")

        if msg_type == "function_call" and call_id:
            function_calls[call_id] = message
        elif msg_type == "function_call_output" and call_id:
            function_outputs[call_id] = message

    # Build the reordered list: keep function_call_outputs in place, move function_calls to come before their outputs
    processed_call_ids = set()

    for message in deduplicated_messages:
        msg_type = message.get("type")
        call_id = message.get("call_id")

        # If it's a function output, add the corresponding call before it
        if (
            msg_type == "function_call_output"
            and call_id
            and call_id not in processed_call_ids
        ):
            processed_call_ids.add(call_id)

            if call_id in function_calls:
                function_call_msg = function_calls[call_id]
                # Adjust timestamps to avoid collisions with same-timestamp reasoning
                output_ts_raw = message.get("timestamp")
                if isinstance(output_ts_raw, (int, float)):
                    try:
                        new_output_ts = float(output_ts_raw) + 2
                        message["timestamp"] = new_output_ts
                        function_call_msg["timestamp"] = new_output_ts - 1
                    except Exception:
                        pass
                reordered_messages.append(function_call_msg)
            else:
                print(f"[WARNING] No function_call found for call_id: {call_id}")

            reordered_messages.append(
                message
            )  # Keep function_call_output in its position

        # If it's not a function call or output, add it as-is
        elif msg_type not in ["function_call", "function_call_output"]:
            reordered_messages.append(message)

        # Preserve standalone function_call (no matching output or missing call_id)
        elif msg_type == "function_call" and (
            not call_id or call_id not in function_outputs
        ):
            reordered_messages.append(message)

        # Function calls with matching outputs are handled when we process their corresponding outputs

    # Update the message store directly
    if len(reordered_messages) != len(messages) or any(
        orig != new for orig, new in zip(messages, reordered_messages)
    ):
        thread_manager._store.messages = reordered_messages


# Factory function to create the hook
def create_system_reminder_hook():
    """Create and return a SystemReminderHook instance."""
    return SystemReminderHook()


def create_message_filter_hook():
    """Create and return a MessageFilterHook instance."""
    return MessageFilterHook()


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
