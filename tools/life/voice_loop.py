
import os
import sys
import time
from shared.env_loader import load_agency_env

# Ensure imports work from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.voice.listener import VoiceListener
from shared.lean_agent import LeanAgent, AgentConfig
from shared.agent_context import create_agent_context
from tools.life.adapter import LifeToolAdapter
from tools.life.email_tool import EmailTool
from tools.life.calendar_tool import CalendarTool
from tools.life.clock_tool import ClockTool


import subprocess
import requests
import openai
import httpx
import json

# CONSTANTS
MODEL_ID = "mlx-community/Llama-3.1-Nemotron-8B-UltraLong-4M-Instruct-4bit"
SERVER_PORT = 8081
SERVER_PORT = 8081
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}/v1"

def is_server_ready():
    try:
        resp = requests.get(f"{SERVER_URL}/models", timeout=5)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        return False # Port closed
    except requests.exceptions.ReadTimeout:
        return False # Server busy loading (Good sign)
    except Exception as e:
        # print(f"DEBUG: Server check failed: {e}") 
        return False

def start_model_server():
    if is_server_ready():
        print(f"✅ MLX Server already running on port {SERVER_PORT}")
        return None

    print(f"🚀 Launching Nemotron 8B Server ({MODEL_ID})...")
    # Launch as subprocess
    log_file = open("mlx_server.log", "w")
    # v2: Use updated syntax for mlx_lm
    # python -m mlx_lm server --model ...
    process = subprocess.Popen(
        [sys.executable, "-m", "mlx_lm", "server", "--model", MODEL_ID, "--port", str(SERVER_PORT)],
        stdout=log_file,
        stderr=subprocess.STDOUT
    )
    
    # Wait for readiness
    print("⏳ Waiting for model to load (This may take ~5-10 mins for the first download)...")
    for i in range(300):
        if is_server_ready():
            print("✅ Model Server Ready!")
            return process
        if i % 10 == 0:
            print(f"   ... still loading ({i}s)")
        time.sleep(1)
    
    print("❌ Server failed to start (Timeout). Check mlx_server.log")
    return process # Return anyway so we can try to kill it if needed

def process_manual_tool_call(agent, text):
    """
    Handle case where model outputs JSON tool call directly in text 
    instead of using the API's tool_calls structure.
    """
    clean = text.strip()
    if "<|eot_id|>" in clean:
        clean = clean.split("<|eot_id|>")[0].strip()
    
    if not clean.startswith("{"):
        return None
        
    try:
        data = json.loads(clean)
        if "name" in data and "parameters" in data:
            tool_name = data["name"]
            tool_args = data["parameters"]
            
            print(f"⚙️ Detected Tool Request: {tool_name}...")
            
            tool = next((t for t in agent.config.tools if t.name == tool_name), None)
            if not tool:
                return f"System Error: Tool '{tool_name}' not found."
            
            try:
                # Execute tool
                # LifeToolAdapter tools expect 'action' and 'data' (optional)
                # If model sends other args, we might need to conform them, 
                # but let's try direct kwargs first.
                result = tool.function(**tool_args)
                return str(result), tool_name
            except TypeError as te:
                return f"Tool Argument Error: {te}", tool_name
            except Exception as e:
                return f"Tool Execution Error: {e}", tool_name
    except json.JSONDecodeError:
        pass
    except Exception as e:
        print(f"⚠️ Error parsing manual tool call: {e}")
        
    return None


def run_voice_loop():
    print("🧠 Initializing AgencyOS Voice Interface...")
    
    # 0. Start Brain
    server_process = start_model_server()
    
    # 1. Initialize Tools
    life_tools = [EmailTool(), CalendarTool(), ClockTool()]
    agent_tools = [LifeToolAdapter.to_tool(t) for t in life_tools]
    
    # 2. Initialize Agent (Nemotron Orchestrator)
    # Configure LeanAgent to use local MLX server
    os.environ["OPENAI_API_KEY"] = "mlx" # Dummy key
    os.environ["OPENAI_API_BASE"] = SERVER_URL
    
    print(f"🤖 Brain: {MODEL_ID}")
    
    agent = LeanAgent(
        AgentConfig(
            name="Operator",
            model=MODEL_ID, # MUST match the server's loaded model
            instructions="""
            You are Operator, an AI orchestrator for AgencyOS.
            Capabilities:
            - CLOCK: get_current_time (Use this for date/time questions).
            - EMAIL: list_unread, fetch_recent_threads, trash_threads, archive_threads.
            - CALENDAR: list_events, create_event.
            
            PROTOCOL:
            - User asks -> You call TOOL immediately.
            - If user wants to "clean" inbox -> List unread -> Trash/Archive.
            - Be concise. Speak naturally.
            """,
            tools=agent_tools,
            temperature=0.0, # Precision for tools
            stop=["<|eot_id|>"] # Stop generation cleanly at end of turn
        )
    )
    
    # 3. Initialize Ear & Mouth
    listener = VoiceListener()
    from tools.voice.speaker import VoiceSpeaker
    speaker = VoiceSpeaker()
    
    # State
    conversation_active = False
    last_interaction_time = 0
    CONVERSATION_TIMEOUT = 30.0 
    
    print("\n🟢 Voice Loop Active. Speak naturally.")
    print("   (Press Ctrl+C to exit)\n")
    
    try:
        while True:
            # Check if conversation timed out
            if conversation_active and (time.time() - last_interaction_time > CONVERSATION_TIMEOUT):
                print("💤 Conversation timeout. Waiting for wake word...")
                conversation_active = False
                
            # A. Listen
            prompt_status = "🟢 Active" if conversation_active else "🔴 Idle (Waiting for 'Operator')"
            print(f"👂 Listening ({prompt_status})...")
            
            # Listen longer if active
            duration = 15.0 if conversation_active else 10.0
            audio = listener.record_audio(max_duration=duration)
            
            # B. Transcribe
            text = listener.transcribe(audio)
            
            if not text:
                continue
                
            is_wake_word = "operator" in text.lower()
            
            # Wake Word Check Logic
            if not conversation_active and not is_wake_word:
                print(f"💤 Ignored: '{text}' (No wake word)")
                continue
                
            # If we heard wake word, or are already active, proceed
            conversation_active = True
            last_interaction_time = time.time()
                
            # C. Think & Act
            clean_text = text.replace("Operator", "").replace("operator", "").replace("Operator,", "").replace("operator,", "").strip()
            
            if not clean_text:
                speaker.speak("Yes, I'm listening.")
                continue
                
            print(f"🧠 Thinking...")
            
            # Check for exit commands using the CLEANED text
            # This handles "Operator stop", "Jarvis shutdown", etc.
            clean_lower = clean_text.lower()
            exit_triggers = ["exit", "stop", "goodbye", "bye", "quit", "shutdown", "shut down", "deactivate"]
            
            # Exit if the clean command is exactly one of the triggers
            # OR if it's a short phrase containing an explicit shutdown command
            is_exit = clean_lower in exit_triggers or \
                      (len(clean_lower.split()) <= 3 and any(t in clean_lower for t in ["exit system", "stop voice", "goodbye", "shut down"]))

            if is_exit:
                print("👋 Goodbye.")
                speaker.speak("Goodbye, sir.")
                break

            try:
                response = agent.run(clean_text)
            except (openai.APIConnectionError, httpx.ConnectError, requests.exceptions.ConnectionError):
                print("⚠️ Connection to Brain lost. Restarting server...")
                # Kill old process if it exists and looks alive (though it probably isn't)
                if server_process:
                    if server_process.poll() is None:
                        server_process.terminate()
                        try:
                            server_process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            server_process.kill()
                
                # Restart
                server_process = start_model_server()
                
                # Retry generation
                print("🧠 Thinking (Retry)...")
                response = agent.run(clean_text)
            
            # --- Manual Tool Loop ---
            # If the model returned a raw JSON tool call, execute it and loop
            max_manual_turns = 5
            previous_tool_name = None
            
            for i in range(max_manual_turns):
                tool_data = process_manual_tool_call(agent, response)
                if not tool_data:
                    break # Not a tool call, or done
                
                # Check for loop BEFORE executing
                target_tool_name = tool_data[1] if isinstance(tool_data, tuple) else None
                # Note: process_manual_tool_call returns (result, tool_name) if successful, 
                # but currently it executes inside the function. We need to be careful.
                # Actually, our helper executes it. To do "hard break", we should probably checks inside the helper 
                # or just accept we execute it once, but REFUSE to feed it back the same way if it repeats.
                
                # Let's trust the helper for now, but handle the result.
                tool_result, tool_name = tool_data
                print(f"   ⚙️ Result: {tool_result[:100]}...")
                
                # Loop Detection: If calling same tool twice in a row, FORCE STOP
                if tool_name == previous_tool_name:
                    print("   ⚠️ Loop detected (Same tool called twice). Forcing answer.")
                    # We pretend the tool returned a directive to stop.
                    next_prompt = (
                        f"System Observation: You have already called '{tool_name}' and received the data.\n"
                        f"Instruction: Do NOT call it again. Answer the user's question directly using the information you already have."
                    )
                else:
                    # Feed result back to agent using Observation Pattern
                    next_prompt = (
                        f"Observation from {tool_name}: {tool_result}\n"
                        f"Original Question: {clean_text}\n"
                        f"Instruction: Based on this observation, answer the user's question concisely."
                    )
                
                previous_tool_name = tool_name
                
                print(f"🧠 Thinking (Post-Tool)...")
                try:
                    response = agent.run(next_prompt)
                except Exception:
                    response = "I'm having trouble connecting to my brain again."
                    break

            last_interaction_time = time.time() 
            
            # D. Speak
            # If response is STILL a json after loop, we failed to resolve it or hit max turns
            if response.strip().startswith("{") and "name" in response:
                 # Fallback
                 speaker.speak("I am trying to use a tool but getting stuck.")
            else:
                print(f"\n🤖 Operator: {response}\n")
                speaker.speak(response)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Voice Loop Terminated.")
    finally:
        if server_process:
            print("🛑 Stopping Model Server...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    load_agency_env()
    run_voice_loop()
