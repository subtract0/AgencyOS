import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[2]))

from cells.shared.lean_agent import LeanAgent, AgentConfig, tool, ToolParameter, ToolPropertySchema
from cells.governor.budget import BudgetManager
import os

# Copywriter needs to read the strategy and write the copy
@tool("read_file", "Read strategy documents", ToolParameter(
    type="object", 
    properties={"path": ToolPropertySchema(type="string")}, 
    required=["path"]
))
def read_file(path: str) -> str:
    try:
        if not os.path.exists(path): return "Error: File not found."
        with open(path, "r") as f: return f.read()[:10000]
    except Exception as e: return str(e)

@tool("write_file", "Write markdown/copy", ToolParameter(
    type="object",
    properties={"path": ToolPropertySchema(type="string"), "content": ToolPropertySchema(type="string")},
    required=["path", "content"]
))
def write_file(path: str, content: str) -> str:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f: f.write(content)
        return "Saved."
    except Exception as e: return str(e)

class CopywriterCell:
    """
    The Pen. Specializes in Direct Response Copywriting.
    """
    def __init__(self):
        self.budget = BudgetManager()
        
        # Configure Environment
        os.environ["OPENAI_API_KEY"] = "not-needed"
        os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8082/v1"
        
        config = AgentConfig(
            name="Copywriter",
            instructions="""
            YOU ARE THE PEN. You are a world-class Direct Response Copywriter (Ogilvy, Halbert, Hormozi).
            
            YOUR JOB: Write high-converting sales copy.
            STYLE: Punchy. Emotional. Benefit-driven. No fluff.
            
            PROTOCOL:
            1. READ the strategy: OFFER_STRATEGY.md
            2. WRITE the copy: landing_page_copy.md
            3. DONE.
            """,
            model="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
            max_tokens=3000,
            tools=[read_file, write_file]
        )
        self.agent = LeanAgent(config)

    def write_copy(self):
        print("✍️ The Pen is moving...")
        if not self.budget.check_budget(0.0):
            print("🛑 Budget exceeded.")
            return

        prompt = """
        OBJECTIVE: Read the '/Users/am/.gemini/antigravity/brain/3c22db1a-aec5-4048-a599-39aa5422021a/OFFER_STRATEGY.md'.
        Then write a full Landing Page Copy document saved to 'cells/marketing/landing_page_copy.md'.
        
        STRUCTURE:
        - Headline (H1): The Hook.
        - Subhead (H2): The Promise.
        - The Problem (The Agitation): "The Spiritual Split".
        - The Solution (The Mechanism): "The 3-Step Miracle Trigger".
        - The Offer (Call to Action): "Download the Emergency Peace Kit".
        - Bullets: What's inside.
        """
        
        try:
            self.agent.run(prompt)
            print("✅ Copy written.")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    CopywriterCell().write_copy()
