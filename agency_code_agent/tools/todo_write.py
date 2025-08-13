from agency_swarm.tools import BaseTool
from pydantic import BaseModel, Field
from typing import List, Literal
import json
import os
from datetime import datetime

class TodoItem(BaseModel):
    content: str = Field(..., min_length=1, description="The todo item content")
    status: Literal["pending", "in_progress", "completed"] = Field(..., description="The status of the todo item")
    priority: Literal["high", "medium", "low"] = Field(..., description="The priority of the todo item")
    id: str = Field(..., description="Unique identifier for the todo item")

class TodoWrite(BaseTool):
    """
    Use this tool to create and manage a structured task list for your current coding session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
    It also helps the user understand the progress of the task and overall progress of their requests.
    
    ## When to Use This Tool
    Use this tool proactively in these scenarios:
    1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
    2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
    3. User explicitly requests todo list - When the user directly asks you to use the todo list
    4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
    5. After receiving new instructions - Immediately capture user requirements as todos
    6. When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you should only have one todo as in_progress at a time
    7. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation
    
    ## When NOT to Use This Tool
    Skip using this tool when:
    1. There is only a single, straightforward task
    2. The task is trivial and tracking it provides no organizational benefit
    3. The task can be completed in less than 3 trivial steps
    4. The task is purely conversational or informational
    
    ## Task States and Management
    1. **Task States**: Use these states to track progress:
       - pending: Task not yet started
       - in_progress: Currently working on (limit to ONE task at a time)
       - completed: Task finished successfully
    
    2. **Task Management**:
       - Update task status in real-time as you work
       - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
       - Only have ONE task in_progress at any time
       - Complete current tasks before starting new ones
       - Remove tasks that are no longer relevant from the list entirely
    
    3. **Task Completion Requirements**:
       - ONLY mark a task as completed when you have FULLY accomplished it
       - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
       - When blocked, create a new task describing what needs to be resolved
       - Never mark a task as completed if:
         - Tests are failing
         - Implementation is partial
         - You encountered unresolved errors
         - You couldn't find necessary files or dependencies
    
    4. **Task Breakdown**:
       - Create specific, actionable items
       - Break complex tasks into smaller, manageable steps
       - Use clear, descriptive task names
    
    When in doubt, use this tool. Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully.
    """
    
    todos: List[TodoItem] = Field(..., description="The updated todo list")
    
    # Class variable to store the todo list across invocations
    _todo_list_file = "/tmp/agency_code_agent_todos.json"
    
    def run(self):
        try:
            # Validate that only one task is in_progress
            in_progress_tasks = [todo for todo in self.todos if todo.status == "in_progress"]
            if len(in_progress_tasks) > 1:
                return f"Error: Only one task can be 'in_progress' at a time. Found {len(in_progress_tasks)} tasks in progress."
            
            # Add timestamp to todos
            current_time = datetime.now().isoformat()
            
            # Convert todos to dict format
            todos_payload = [todo.model_dump() for todo in self.todos]

            # Persist only to JSON file in this version (no shared state/context)
            
            # Save to file for persistence (best-effort)
            try:
                todo_data = {
                    "updated_at": current_time,
                    "todos": todos_payload
                }
                with open(self._todo_list_file, 'w') as f:
                    json.dump(todo_data, f, indent=2)
            except Exception:
                pass
            
            # Format the response
            total_tasks = len(self.todos)
            completed_tasks = len([t for t in self.todos if t.status == "completed"])
            in_progress_tasks = len([t for t in self.todos if t.status == "in_progress"])
            pending_tasks = len([t for t in self.todos if t.status == "pending"])
            
            result = f"Todo List Updated ({current_time[:19]})\n\n"
            result += f"Summary: {total_tasks} total tasks - {completed_tasks} completed, {in_progress_tasks} in progress, {pending_tasks} pending\n\n"
            
            # Group tasks by status
            status_groups = {
                "in_progress": [],
                "pending": [],
                "completed": []
            }
            
            for todo in self.todos:
                status_groups[todo.status].append(todo)
            
            # Display in_progress tasks first
            if status_groups["in_progress"]:
                result += "IN PROGRESS:\n"
                for todo in status_groups["in_progress"]:
                    result += f"  [{todo.priority.upper()}] [{todo.id}] {todo.content}\n"
                result += "\n"
            
            # Display pending tasks
            if status_groups["pending"]:
                result += "PENDING:\n"
                for todo in status_groups["pending"]:
                    result += f"  [{todo.priority.upper()}] [{todo.id}] {todo.content}\n"
                result += "\n"
            
            # Display completed tasks (limit to last 5 to avoid clutter)
            if status_groups["completed"]:
                completed_to_show = status_groups["completed"][-5:]  # Show last 5 completed
                result += f"COMPLETED (showing last {len(completed_to_show)}):\n"
                for todo in completed_to_show:
                    result += f"  [{todo.priority.upper()}] [{todo.id}] {todo.content}\n"
                
                if len(status_groups["completed"]) > 5:
                    result += f"  ... and {len(status_groups['completed']) - 5} more completed tasks\n"
                result += "\n"
            
            # Add usage tips
            result += "Tips:\n"
            result += "  - Keep only ONE task 'in_progress' at a time\n"
            result += "  - Mark tasks 'completed' immediately after finishing\n"
            result += "  - Break complex tasks into smaller, actionable steps\n"
            
            return result.strip()
            
        except Exception as e:
            return f"Error managing todo list: {str(e)}"
    
    @classmethod
    def load_existing_todos(cls):
        """Load existing todos from file."""
        try:
            if os.path.exists(cls._todo_list_file):
                with open(cls._todo_list_file, 'r') as f:
                    data = json.load(f)
                    return data.get("todos", [])
        except Exception:
            pass
        return []



# Create alias for Agency Swarm tool loading (expects class name = file name)
todo_write = TodoWrite

if __name__ == "__main__":
    # Test the tool
    test_todos = [
        TodoItem(
            content="Implement user authentication system",
            status="in_progress",
            priority="high",
            id="auth-001"
        ),
        TodoItem(
            content="Create database schema",
            status="completed",
            priority="high", 
            id="db-001"
        ),
        TodoItem(
            content="Write unit tests for auth module",
            status="pending",
            priority="medium",
            id="test-001"
        ),
        TodoItem(
            content="Update API documentation",
            status="pending",
            priority="low",
            id="docs-001"
        ),
        TodoItem(
            content="Set up CI/CD pipeline",
            status="pending",
            priority="medium",
            id="cicd-001"
        )
    ]
    
    tool = TodoWrite(todos=test_todos)
    result = tool.run()
    print("Todo list example:")
    print(result)
    
    # Test validation - multiple in_progress tasks (should fail)
    invalid_todos = [
        TodoItem(content="Task 1", status="in_progress", priority="high", id="t1"),
        TodoItem(content="Task 2", status="in_progress", priority="high", id="t2")
    ]
    
    invalid_tool = TodoWrite(todos=invalid_todos)
    invalid_result = invalid_tool.run()
    print("\n" + "="*70 + "\n")
    print("Validation test (multiple in_progress - should fail):")
    print(invalid_result)