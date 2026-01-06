
import os
import sys
from shared.env_loader import load_agency_env

# Ensure we can import from the root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from life_agent.life_agent import create_life_agent



# Configuration
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "alexander.monas@gmail.com")

def run_daily_briefing():
    print(f"🌅 Starting Daily Briefing for {OWNER_EMAIL}...")
    
    try:
        # 1. Initialize Dependencies (Bypassing Agency class)
        from shared.agent_context import create_agent_context
        from shared.cost_tracker import CostTracker, MemoryStorage
        
        context = create_agent_context(session_id="daily_briefing")
        cost_tracker = CostTracker(storage=MemoryStorage())
        
        # 2. Initialize Life Agent
        # Detect model (default to llama if available, or fallbacks)
        model = os.getenv("AGENCY_MODEL", "ollama/llama3.1:70b")
        life_agent = create_life_agent(model=model, agent_context=context, cost_tracker=cost_tracker)
        
        # 3. Define the Mission
        mission_prompt = f"""
        It is currently morning.
        
        **MISSION:**
        You are my Executive Secretary. Your job is to prepare my "Morning Briefing".
        
        **INSTRUCTIONS:**
        1. Check my **Calendar** for events in the next 24 hours.
        2. Check my **Email** for the top 5 unread messages.
        3. Synthesize this information into a concise, professional "Morning Briefing" email.
        4. Use the `Email` tool to **DRAFT** this email to {OWNER_EMAIL}.
           - Subject: "🌅 Morning Briefing: [Date]"
           - Body: Use HTML formatting. Highlight urgent items.
        
        **Execute now.** Do not ask for clarification.
        """
        
        print(f"🤖 Agent ({model}) is working...")
        response = life_agent.run(mission_prompt)
        
        print("\n✅ Briefing Task Complete!")
        print(f"Agent Response: {response}")
        
    except ImportError as e:
        print(f"❌ Dependency Error: {e}")
        print("Ensure you are running from the project root.")
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_agency_env()
    run_daily_briefing()
