import os
import sys

# Ensure project root is first on sys.path so stdlib `glob` isn't shadowed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import asyncio

from agency_swarm.tools import BaseTool
from pydantic import Field


class Task(BaseTool):
    """
    Launch a new agent that has access to the following tools: Bash, Glob, Grep, LS, exit_plan_mode, Read, Edit, MultiEdit, Write, NotebookRead, NotebookEdit, TodoWrite, WebSearch.

    When to use the this Task Tool:
    - If you are searching for a keyword like "config" or "logger", or for questions like "which file does X?"
    - Open-ended searches that may require multiple rounds of searching

    When NOT to use:
    - Reading specific file paths (use Read or Glob instead)
    - Searching for specific class definitions (use Glob instead)
    - Writing code and running bash commands
    """

    description: str = Field(
        ..., description="A short (3-5 word) description of the task"
    )
    prompt: str = Field(..., description="The task for the agent to perform")

    def run(self):
        try:
            # Construct a fast sub-agency and execute the prompt normally
            from agency_swarm import Agency

            from agency_code_agent.agency_code_agent import create_agency_code_agent

            sub_agent = create_agency_code_agent(
                model="gpt-5-mini", reasoning_effort="low"
            )
            sub_agency = Agency(sub_agent)

            result = asyncio.run(sub_agency.get_response(self.prompt))

            return result.text if hasattr(result, "text") else str(result)

        except Exception as e:
            return f"Error executing task: {str(e)}"


# Create alias for Agency Swarm tool loading (expects class name = file name)
task = Task

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    prompt = (
        "Search the web for the Agency Swarm framework official documentation and the "
        "release date of version 1.0.0. Provide the exact date and one authoritative link."
    )
    print(Task(description="Web research", prompt=prompt).run())
