
import os
import sys
import time
from dotenv import load_dotenv

# Ensure imports work from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.voice.listener import VoiceListener
from shared.lean_agent import LeanAgent, AgentConfig
from shared.agent_context import create_agent_context
from tools.life.adapter import LifeToolAdapter
from tools.life.email_tool import EmailTool
from tools.life.calendar_tool import CalendarTool


def run_voice_loop():
    print("🧠 Initializing AgencyOS Voice Interface...")
    
    # 1. Initialize Tools
    life_tools = [EmailTool(), CalendarTool()]
    agent_tools = [LifeToolAdapter.to_tool(t) for t in life_tools]
    
    # 2. Initialize Agent (Jarvis Persona)
    model = os.getenv("AGENCY_MODEL", "ollama/llama3.1:70b")
    print(f"🤖 Brain: {model}")
    
    agent = LeanAgent(
        AgentConfig(
            name="Jarvis",
            model=model,
            instructions="""
            You are J.A.R.V.I.S, an intelligent voice assistant.
            Your goal is to execute the user's voice commands efficiently using your tools.
            
            Guidelines:
            - Keep responses SHORT and spoken-style (no markdown, no bullets).
            - If you perform an action (like drafting an email), confirmn it briefly: "Draft created, sir."
            - If you need more info, ask briefly.
            - You have access to Email and Calendar.
            - To use tools, provide action and JSON data string.
            """,
            tools=agent_tools
        )
    )
    
    # 3. Initialize Ear
    listener = VoiceListener()
    
    print("\n🟢 Voice Loop Active. Speak naturally.")
    print("   (Press Ctrl+C to exit)\n")
    
    try:
        while True:
            # A. Listen
            print("👂 Listening...")
            audio = listener.record_audio(max_duration=10.0)
            
            # B. Transcribe
            text = listener.transcribe(audio)
            
            if not text:
                print("Can you repeat that?")
                continue
                
            if "exit" in text.lower() or "stop" in text.lower():
                print("👋 Goodbye.")
                break
                
            # C. Think & Act
            print(f"🧠 Thinking...")
            response = agent.run(text)
            
            # D. Speak (Text-only for now, TTS in Phase 8)
            print(f"\n🤖 JARVIS: {response}\n")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Voice Loop Terminated.")

if __name__ == "__main__":
    load_dotenv()
    run_voice_loop()
