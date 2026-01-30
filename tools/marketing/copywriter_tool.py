
import sys
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[2]))

from cells.shared.lean_agent import LeanAgent, AgentConfig, tool, ToolParameter, ToolPropertySchema
from cells.shared.model_profiles import MODELS

@tool(
    name="generate_sales_copy",
    description="Use the Expert Copywriter (The Pen) to write high-converting sales copy based on a strategy/brief.",
    parameters=ToolParameter(
        type="object",
        properties={
            "brief": ToolPropertySchema(type="string", description="The strategy, product details, or instructions for the copy."),
            "output_path": ToolPropertySchema(type="string", description="Where to save the markdown copy (default: cells/marketing/generated_copy.md)")
        },
        required=["brief"]
    )
)
def generate_sales_copy(brief: str, output_path: str = "cells/marketing/generated_copy.md") -> str:
    print(f"✍️ Invoking The Pen...")
    
    # 1. Setup Writer Agent
    # Use Qwen-32B or Architect (70B) depending on complexity? 
    # Let's use Qwen-32B (Deep Coder/Writer) profile for speed/quality balance.
    profile = MODELS["deep_coder"]
    
    config = AgentConfig(
        name="Copywriter",
        instructions="""
        YOU ARE THE PEN. You are a world-class Direct Response Copywriter (Ogilvy, Halbert, Hormozi).
        
        YOUR JOB: Write high-converting sales copy based on the USER BRIEF.
        STYLE: Punchy. Emotional. Benefit-driven. No fluff.
        FORMAT: Markdown (H1, H2, Bullets).
        
        DO NOT include conversational filler ("Here is the copy"). Just write the copy.
        """,
        model=profile,
        max_tokens=4000,
        temperature=0.7 # Creativity
    )
    
    agent = LeanAgent(config)
    
    # 2. Run
    prompt = f"BRIEF:\n{brief}\n\nWRITE THE SALES COPY NOW."
    try:
        copy = agent.run(prompt)
        
        # 3. Save
        full_path = Path(output_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(copy)
        
        return f"Copy written successfully to {output_path}."
        
    except Exception as e:
        return f"Error writing copy: {e}"

# For standalone testing
if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = "sk-dummy" # Ensure key exists
    brief = "Sell a pen that never runs out of ink. Target: Students."
    # Direct function call requires unwrapping the Tool object or calling .function
    if hasattr(generate_sales_copy, "function"):
         print(generate_sales_copy.function(brief, "test_copy.md"))
    else:
         print(generate_sales_copy(brief, "test_copy.md"))
