
import os
import sys
import json
from shared.env_loader import load_agency_env

# Ensure imports work from root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.life.email_tool import EmailTool
from shared.agent_context import create_agent_context
from shared.cost_tracker import CostTracker, MemoryStorage
from shared.lean_agent import LeanAgent, AgentConfig, Tool

def run_inbox_cleaner():
    print("🧹 Starting Inbox Zero Agent...")
    
    # 1. Setup
    email = EmailTool()
    context = create_agent_context(session_id="inbox_cleaner")
    cost_tracker = CostTracker(storage=MemoryStorage())
    model = os.getenv("AGENCY_MODEL", "ollama/llama3.1:70b")
    
    # 2. Fetch Inbox
    print("📥 Fetching recent emails from Inbox...")
    fetch_result = email.fetch_recent_threads(limit=20, query='in:inbox') # Start with 20 for safety
    
    if not fetch_result.success or not fetch_result.data:
        print("✅ Inbox is empty (or error fetching).")
        return

    emails = fetch_result.data
    email_text = "\n".join([f"ID: {e['threadId']} | From: {e['sender']} | Subject: {e['subject']} | Snippet: {e['snippet']}" for e in emails])
    
    # 3. Classify (The "Brain")
    print(f"🧠 Analyzing {len(emails)} emails with {model}...")
    
    classification_prompt = f"""
    You are an expert Email Triage Assistant.
    Your goal is to help me reach Inbox Zero.
    
    **Instructions:**
    1. Analyze the following list of emails.
    2. Classify each email into one of these categories:
       - **ARCHIVE**: Newsletters, Notifications, receipts, old updates (No action needed).
       - **TRASH**: Spam, junk, cold outreach.
       - **KEEP**: Personal emails, urgent tasks, work items, or anything requiring a reply/action.
    
    **Output Format:**
    Return ONLY a valid JSON object with three lists of Thread IDs:
    {{
      "archive": ["id1", "id2"],
      "trash": ["id3"],
      "keep": ["id4"]
    }}
    
    **Email List:**
    {email_text}
    """
    
    # We use a temporary agent for just this reasoning step
    classifier = LeanAgent(AgentConfig(name="Classifier", model=model, instructions="You are a JSON-only response bot."))
    
    try:
        response = classifier.run(classification_prompt)
        # Naive extraction of JSON
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
            
        plan = json.loads(json_str)
        
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        print(f"Raw Response: {response}")
        return

    # 4. Present Plan
    to_archive = plan.get('archive', [])
    to_trash = plan.get('trash', [])
    to_keep = plan.get('keep', [])
    
    print("\n📋 **Cleanup Plan:**")
    print(f"   - Archive: {len(to_archive)} threads")
    print(f"   - Trash:   {len(to_trash)} threads")
    print(f"   - Keep:    {len(to_keep)} threads")
    
    # Show snippet of what is being removed
    if to_archive:
        print("\n📂 **To Archive:**")
        for tid in to_archive[:5]:
             subj = next((e['subject'] for e in emails if e['threadId'] == tid), "Unknown")
             print(f"   - {subj}")
        if len(to_archive) > 5: print(f"   ... and {len(to_archive)-5} more.")

    if to_trash:
        print("\n🗑️ **To Trash:**")
        for tid in to_trash[:5]:
             subj = next((e['subject'] for e in emails if e['threadId'] == tid), "Unknown")
             print(f"   - {subj}")
    
    # 5. User Decision
    choice = input("\n👉 Execute this plan? [y/N] ").strip().lower()
    
    if choice == 'y':
        if to_archive:
            print("📦 Archiving...")
            email.archive_threads(to_archive)
        if to_trash:
            print("🚮 Trashing...")
            email.trash_threads(to_trash)
        print("✨ Done!")
    else:
        print("❌ Aborted.")

if __name__ == "__main__":
    load_agency_env()
    run_inbox_cleaner()
