from agency_swarm.tools import BaseTool
from pydantic import Field


class ExitPlanMode(BaseTool):
    """
    Use this tool when you are in plan mode and have finished presenting your plan and are ready to code. This will prompt the user to exit plan mode.

    IMPORTANT: Only use this tool when the task requires planning the implementation steps of a task that requires writing code. For research tasks where you're gathering information, searching files, reading files or in general trying to understand the codebase - do NOT use this tool.

    Examples:
    1. "Search for and understand the implementation of vim mode in the codebase" - Do not use the exit plan mode tool because you are not planning implementation steps
    2. "Help me implement yank mode for vim" - Use the exit plan mode tool after you have finished planning the implementation steps
    """

    plan: str = Field(
        ...,
        description="The plan you came up with, that you want to run by the user for approval. Supports markdown. The plan should be pretty concise.",
    )

    def run(self):
        try:
            # Format the plan nicely
            formatted_plan = f"""
=== IMPLEMENTATION PLAN ===

{self.plan}

=== READY TO PROCEED ===

The plan above outlines the implementation steps for this task.

Please review the plan and let me know if you'd like to:
- Proceed with the implementation as planned
- Modify any aspects of the plan
- Add or remove steps
- Ask questions about the approach

Once you approve, I'll begin implementing the solution step by step.
"""
            return formatted_plan.strip()

        except Exception as e:
            return f"Error formatting plan: {str(e)}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
exit_plan_mode = ExitPlanMode

if __name__ == "__main__":
    # Test the tool
    test_plan = """
## Implementation Plan for User Authentication

1. **Database Schema Updates**
   - Add users table with email, password_hash, created_at columns
   - Add sessions table for managing user sessions

2. **Authentication Middleware**
   - Create middleware to check session validity
   - Handle login/logout endpoints

3. **Frontend Updates**
   - Add login form component
   - Add registration form component
   - Update navigation to show user state

4. **Testing**
   - Unit tests for auth functions
   - Integration tests for login flow
"""

    tool = ExitPlanMode(plan=test_plan)
    print(tool.run())
