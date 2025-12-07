
from tools.life.email_tool import EmailTool
import json

def inspect_draft(draft_id):
    print(f"🧐 Inspecting Draft {draft_id}...")
    email = EmailTool()
    
    try:
        draft = email.service.users().drafts().get(userId='me', id=draft_id).execute()
        message = draft['message']
        snippet = message.get('snippet', '(No Snippet)')
        print(f"Snippet: {snippet}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # ID from previous output
    inspect_draft("r-2207617610426487323")
