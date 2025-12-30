
import asyncio
import logging
from typing import AsyncGenerator

from pipecat.frames.frames import Frame, TextFrame, TranscriptionFrame, ErrorFrame, StartFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

from shared.lean_agent import LeanAgent, AgentConfig, tool
from tools.life.adapter import LifeToolAdapter
from tools.life.email_tool import EmailTool
from tools.life.calendar_tool import CalendarTool
from tools.life.clock_tool import ClockTool
from tools.life.voice_loop import start_model_server

from shared.budget_manager import BudgetManager
from shared.model_router import ModelRouter

class AgencyLLMService(FrameProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent = None
        self._server_process = None
        
        # Class 2 Governance
        self.budget = BudgetManager()
        self.router = ModelRouter(self.budget)

    async def start(self, frame: Frame):
        """Initialize The Council."""
        logging.info("AgencyLLMService: Summoning The Council...")
        
        # Start Council Servers
        from tools.voice_v2.services.council_manager import council
        self.council = council
        self.council.start_council()
        
        # Give servers a moment to spin up (though LeanAgent retries connection)
        await asyncio.sleep(2)

        # Initialize Agents
        try:
            import os
            # 1. The Executive (Voice/Fast)
            # Port 8081
            os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8081/v1"
            os.environ["OPENAI_API_KEY"] = "mlx"
            
            life_tools = [EmailTool(), CalendarTool(), ClockTool()]
            exec_tools = [LifeToolAdapter.to_tool(t) for t in life_tools]
            
            exec_config = AgentConfig(
                name="Executive",
                model="mlx-community/Llama-3.1-Nemotron-8B-UltraLong-4M-Instruct-4bit",
                instructions="You are the Executive interface (8B). You are a helpful voice assistant. Answer questions directly and concisely in plain text. Do not use JSON.",
                tools=[], # DISABLED TOOLS to stop hallucination loop
                temperature=0.1
            )
            self.agent_exec = LeanAgent(exec_config)
            
            # 2. The Engineer (Coding)
            # Port 8082
            os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8082/v1"
            
            # Future: Add specific coding tools? For now, pure code generation.
            dev_config = AgentConfig(
                name="Engineer",
                model="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
                instructions="You are the Principal Engineer. Write high-quality, bug-free Python code. Explain your logic briefly.",
                temperature=0.2
            )
            self.agent_dev = LeanAgent(dev_config)
            
            # 3. The Architect (Reasoning/Research)
            # Port 8083
            os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8083/v1"
            
            from tools.life.research_tool import ResearchTool
            research_tool = ResearchTool()
            arch_tools = [LifeToolAdapter.to_tool(research_tool)]
            
            arch_config = AgentConfig(
                name="Architect",
                model="mlx-community/Llama-3.3-70B-Instruct-4bit",
                instructions="""
                You are The Architect. A vast superintelligence (70B parameters) running on a 128GB Mac Studio.
                
                PROTOCOL: RECURSIVE DEEP RESEARCH
                1.  **Objective**: When asked to research, do not just answer. EXPLORE.
                2.  **Phase 1: Hone Search Wording**:
                    - Do NOT just search for "X".
                    - Create targeted Google Dorks.
                    - **Market Gap Strategy**: Use this format to find user pain points:
                      `"{Topic}" site:reddit.com (inurl:comments|inurl:thread) ("my biggest struggle"|"pain point"|"what I wish I knew"|"regret"|"frustrations")`
                3.  **Phase 2: Execution Loop**:
                    - Thought: What specific missing info prevents a complete answer?
                    - Action: `search_web` (using honed queries) or `browse_reddit`.
                    - Observation: Analyze. Is it generic? If so, RE-SEARCH with better terms.
                4.  **Phase 3: Synthesis**:
                    - Summarize broadly in voice.
                    - **MANDATORY**: Write a comprehensive `Topic_Analysis_YYYYMMDD.md` report via `write_report`.
                
                You have access to the internet and Reddit.
                Use them proactively. Use the Market Gap strategy for product/sentiment research.
                """,
                tools=arch_tools,
                temperature=0.6
            )
            self.agent_arch = LeanAgent(arch_config)
            
            logging.info("AgencyLLMService: The Council is Seated and Listening.")
            self.agent = True 
            
        except Exception as e:
            logging.error(f"Failed to seat The Council: {e}")
            await self.push_error(ErrorFrame(str(e)))

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            await self.start(frame)
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, (TextFrame, TranscriptionFrame)):
            if not frame.text.strip():
                return
                
            print(f"\n👂 HEARD: '{frame.text}'")
            logging.info(f"Brain received: {frame.text}")
            
            if not self.agent:
                print("❌ Council NOT Ready yet! (Still loading models...)")
                logging.error("Council not ready!")
                return

            try:
                # 0. Complexity Analysis (Heuristic)
                text = frame.text.lower()
                complexity = "low" 
                if any(k in text for k in ["architect", "plan", "design", "deep", "complex", "reason", "analysis"]):
                    complexity = "high"
                
                # 1. Governor Decision
                decision = self.router.route(task_complexity=complexity)
                
                # Check for Provider
                provider = decision["provider"]
                target_model = decision["model"]
                
                selected_agent = self.agent_exec # Default
                agent_name = "Executive (8B)"
                
                if provider == "local":
                    # --- LOCAL ROUTING (Standard) ---
                    if "[system directive: nightly_protocol]" in text:
                        selected_agent = self.agent_arch
                        agent_name = "Architect (70B) [Nightly Override]"
                    elif "dismiss" in text and ("architect" in text or "research" in text):
                         # Manual Dismissal
                        if self.council.is_architect_running():
                            print("📉 Dismissing Architect...")
                            self.council.dismiss_architect()
                            await self.push_frame(TextFrame("Dismissing the Architect to save resources."), direction)
                            return
                        else:
                            await self.push_frame(TextFrame("Architect is already sleeping."), direction)
                            return
                    elif any(k in text for k in ["code", "function", "script", "python", "debug"]):
                        selected_agent = self.agent_dev
                        agent_name = "Engineer (32B)"
                    elif complexity == "high" or any(k in text for k in ["research", "reddit", "search"]):
                        agent_name = f"Architect (70B) [Governed: {decision['reason']}]"
                        selected_agent = self.agent_arch
                        
                        # DYNAMIC LOADING: Wake up Architect if needed
                        if not self.council.is_architect_running():
                            print("⏳ Architect is sleeping. Summoning...")
                            await self.push_frame(TextFrame("Summoning the Architect foundation model..."), direction)
                            await asyncio.to_thread(self.council.summon_architect)
                            print("✅ Architect is awake.")
                            
                elif provider in ["google", "anthropic"]:
                    # --- CLOUD ROUTING (Escalation) ---
                    # For now, we simulate this by using the Architect but logging the cost
                    # In Class 3, we will add actual API calls here.
                    agent_name = f"Cloud ({target_model}) [Simulated by Architect]"
                    selected_agent = self.agent_arch
                    
                    if "estimated_cost" in decision:
                        self.budget.record_spend(decision["estimated_cost"])
                        print(f"💰 RECORDED SPEND: ${decision['estimated_cost']:.2f}")

                    # Summing logic (same as above)
                    if not self.council.is_architect_running():
                        print("⏳ Architect is sleeping. Summoning (Cloud Simulation)...")
                        await self.push_frame(TextFrame("Connecting to Advanced Logic..."), direction)
                        await asyncio.to_thread(self.council.summon_architect)


                print(f"🤔 ROUTING TO: {agent_name}")
                logging.info(f"Router: Selected {agent_name}")

                # Run Agent
                print("⏳ Thinking...")
                response_text = await asyncio.to_thread(selected_agent.run, frame.text)
                
                print(f"🤖 RESPONSE: {response_text[:100]}..." if len(response_text) > 100 else f"🤖 RESPONSE: {response_text}")
                logging.info(f"Brain response: {response_text}")
                await self.push_frame(TextFrame(response_text), direction)
                
                # AUTO-DISMISSAL: Serverless Style
                if selected_agent == self.agent_arch and self.council.is_architect_running():
                    print("📉 Task Complete. Auto-dismissing Architect...")
                    # await self.push_frame(TextFrame("(Auto-Dismissing Architect...)"), direction)
                    self.council.dismiss_architect()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.error(f"Brain Error: {e}")
                await self.push_frame(TextFrame(f"The Council encountered an error: {e}"), direction)
        else:
            await self.push_frame(frame, direction)

    async def stop(self, frame: Frame):
        logging.info("AgencyLLMService: Stopping...")
        if hasattr(self, 'council'):
            self.council.stop_council()
        await super().stop(frame)
