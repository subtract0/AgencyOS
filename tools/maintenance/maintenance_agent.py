
import os
import subprocess
import sys

# Ensure we can import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.lean_agent import LeanAgent, AgentConfig
from shared.budget_manager import BudgetManager
from shared.model_router import ModelRouter

class MaintenanceAgent:
    """
    The Groundskeeper for AgencyOS.
    Responsibilities:
    1. Run Health Checks (skills/test_backend.sh)
    2. If Red: Diagnose & Heal.
    3. If Green: Commit & Sleep.
    """
    
    def __init__(self):
        # Configuration
        self.budget = BudgetManager()
        self.router = ModelRouter(self.budget)
        
        # Setup Local MLX Connection
        os.environ["OPENAI_API_KEY"] = "mlx"
        os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8082/v1"
        
        # We use the Engineer persona for fixing
        self.config = AgentConfig(
            name="MaintenanceEngineer",
            model="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit", # Or Llama 70B
            instructions="""
            You are the Maintenance Engineer for AgencyOS.
            Your goal is to fix broken tests.
            
            PROTOCOL:
            1. Analyze the 'TEST FAILURE LOG'.
            2. Identify the specific file and line causing the error.
            3. Rewrite the File content to fix the bug.
            4. Be surgical. Do not rewrite the whole file if you can locate the error.
            5. ONLY output the corrected code block for the file.
            """,
            temperature=0.2
        )
        self.agent = LeanAgent(self.config)

    def run_skill(self, skill_name: str) -> tuple[int, str]:
        """Runs a bash skill and returns (exit_code, output)."""
        script_path = f"skills/{skill_name}.sh"
        if not os.path.exists(script_path):
            return 1, f"Skill {skill_name} not found."
            
        print(f"🔧 Running Skill: {skill_name}")
        result = subprocess.run([script_path], capture_output=True, text=True)
        return result.returncode, result.stdout + "\n" + result.stderr

    def heal(self):
        print("🚑 Maintenance Agent Triggered.")
        
        # 1. Run Tests
        exit_code, output = self.run_skill("test_backend")
        
        if exit_code == 0:
            print("✅ System is Healthy. No action needed.")
            return

        print("❌ System Unhealthy. Diagnosing...")
        print(f"--- FAILURE LOG ---\n{output[:1000]}...\n-------------------")
        
        # 2. Attempt Fix (Max 3 Loops)
        for attempt in range(1, 4):
            print(f"💉 Healing Attempt {attempt}/3...")
            
            # Context for Agent
            prompt = f"""
            The system failed a health check.
            
            EXIT CODE: {exit_code}
            OUTPUT:
            {output}
            
            Identify the likely file causing this. 
            If you need to read a file, output: READ: <absolute_path>
            If you are ready to fix, output the full file content inside a code block.
            """
            
            # Simple Loop: Mocking the multi-turn for MVP complexity
            # Ideally: Agent requests file -> We give file -> Agent gives fix.
            # For this Class 3 MVP, let's assume the error log has the file path (pytest usually does).
            
            # A smarter agent needs read tools. For MVP, we'll try to guess or ask the agent to identify.
            response = self.agent.run(prompt)
            print(f"🤖 ENTITY: {response}")
            
            # If agent wants to read
            if "READ: " in response:
                target_file = response.split("READ: ")[1].split("\n")[0].strip()
                if os.path.exists(target_file):
                    with open(target_file, "r") as f:
                        file_content = f.read()
                    
                    # Second Turn: Here is the file, fix it.
                    fix_prompt = f"""
                    FILE CONTENT ({target_file}):
                    ```python
                    {file_content}
                    ```
                    
                    ERROR:
                    {output}
                    
                    TASK: Rewrite the file to fix the error. Return the file content.
                    """
                    fix_response = self.agent.run(fix_prompt)
                    
                    # Extract Code Block
                    if "```python" in fix_response:
                        new_content = fix_response.split("```python")[1].split("```")[0].strip()
                        
                        # Apply Fix
                        with open(target_file, "w") as f:
                            f.write(new_content)
                        print(f"🩹 Applied fix to {target_file}")
                        
                        # Verify
                        exit_code, output = self.run_skill("test_backend")
                        if exit_code == 0:
                            print("✅ Fix Verified! System Healthy.")
                            subprocess.run(["git", "commit", "-am", f"fix: auto-healed {target_file}"])
                            return
                        else:
                            print("❌ Fix Failed. Retrying...")
                else:
                    print(f"⚠️ Agent requested non-existent file: {target_file}")
                    # Provide feedback to agent (Future improvement) for now just print.
            
        print("💀 Failed to heal system after 3 attempts.")

if __name__ == "__main__":
    healer = MaintenanceAgent()
    healer.heal()
