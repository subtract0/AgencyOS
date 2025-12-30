
from datetime import datetime
from tools.life.base import LifeTool, ToolResult

class ClockTool(LifeTool):
    """
    A simple tool to get the current date and time.
    """
    def __init__(self):
        super().__init__(
            name="Clock",
            description="Get the current time, date, and day of the week."
        )
        
    def get_capabilities(self) -> list[str]:
        return ["get_current_time"]
        
    def execute(self, action: str, **kwargs) -> ToolResult:
        if action == "get_current_time":
            now = datetime.now()
            # Format: "Monday, December 09, 2025 at 12:15 PM"
            time_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
            return ToolResult(
                success=True,
                message=f"The current time is {time_str}."
            )
            
        return ToolResult(success=False, error="Unknown action")
