"""
Life Agent Factory
==================

Creates the LifeAssistant agent, equipped with the "Holy Trinity" of Life Tools.
Ensures all tools are wrapped in SafetyGuard for HITL enforcement.
"""

from shared.lean_agent import LeanAgent, AgentConfig
from shared.agent_context import AgentContext
from shared.cost_tracker import CostTracker
from tools.life.calendar_tool import CalendarTool
from tools.life.email_tool import EmailTool
from tools.life.browser_tool import BrowserTool
from shared.safety_guard import SafetyGuard

from tools.life.adapter import LifeToolAdapter

def create_life_agent(model: str, agent_context: AgentContext, cost_tracker: CostTracker) -> LeanAgent:
    """
    Create the LifeAssistant agent.
    
    Args:
        model: LLM model to use.
        agent_context: Shared agent context.
        cost_tracker: Cost tracker instance.
        
    Returns:
        LeanAgent: Configured LifeAssistant.
    """
    # Initialize Tools
    calendar = CalendarTool()
    email = EmailTool()
    browser = BrowserTool()
    
    # Wrap in SafetyGuard (The "Steve Jobs" Safety Layer)
    # We explicitly list sensitive actions that require user confirmation.
    safe_calendar = SafetyGuard(calendar, sensitive_actions=["schedule_event"])
    safe_email = SafetyGuard(email, sensitive_actions=["send_email"])
    # Browser is generally safe (read-only), but we could guard 'visit' if needed.
    # For now, we leave browser unguarded for friction-less research.
    
    # Adapt to LeanAgent Tools (OpenAI Schema)
    tools = [
        LifeToolAdapter.to_tool(safe_calendar),
        LifeToolAdapter.to_tool(safe_email),
        LifeToolAdapter.to_tool(browser)
    ]
    
    instructions = """
    You are the **Life Assistant**.
    Your goal is to manage the user's life by proactively handling their Time (Calendar), Communication (Email), and Knowledge (Browser).
    
    **Philosophy**:
    - **Proactive**: Don't just wait. If you see a meeting, check for conflicts.
    - **Safe**: You have tools that can impact the real world. Use them wisely.
    - **Concise**: The user is busy. Be brief.
    
    **Tools**:
    - **Calendar**: Schedule and check availability.
    - **Email**: Draft and send messages.
    - **Browser**: Research information to inform your actions.
    
    **Workflow**:
    1.  **Understand**: Parse the user's intent.
    2.  **Research**: If needed, use the Browser to find info (e.g., "Find a restaurant").
    3.  **Act**: Use Calendar/Email to execute.
    4.  **Confirm**: The system will automatically prompt the user for dangerous actions.
    """
    
    config = AgentConfig(
        name="LifeAssistant",
        model=model,
        instructions=instructions,
        tools=tools
    )
    
    return LeanAgent(config)
