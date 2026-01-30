
import logging
import asyncio
from datetime import datetime
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import Frame, TextFrame

class SchedulerService(FrameProcessor):
    """
    Triggers automated tasks based on time.
    e.g. Nightly Janitor Cycle at 3 AM.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._monitoring = False
        self._check_interval = 60 # Check every minute
        self._nightly_job_triggered = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)

    async def start(self, frame: Frame):
        self._monitoring = True
        asyncio.create_task(self._clock_loop())
        await super().start(frame)

    async def _clock_loop(self):
        logging.info("Scheduler: Clock ticking.")
        while self._monitoring:
            now = datetime.now()
            
            # Reset trigger if it's not 3 AM anymore
            if now.hour != 3 and self._nightly_job_triggered:
                self._nightly_job_triggered = False
            
            # Trigger at 3:00 AM
            if now.hour == 3 and now.minute == 0 and not self._nightly_job_triggered:
                logging.info("Scheduler: It is 3 AM. Initiating Nightly Console.")
                
                # The Nightly Protocol
                prompt = """
                [SYSTEM DIRECTIVE: NIGHTLY_PROTOCOL]
                Role: The Council (Architect Mode)
                
                Mission:
                1. RESEARCH: Scan r/LocalLLaMA and key HuggingFace spaces for new "SOTA" models, specifically focusing on:
                   - Keywords: "Reasoning", "Knowledge", "128GB", "M4 Max", "Benchmark".
                   - Models of interest: GLM-4.5, GPT-OSS 120B, new Llama variants.
                   - Look for highly upvoted (>50) discussion threads.
                
                2. REPORT: Compile a "Daily Intelligence Briefing" markdown file at `~/AgencyOS/Research/Daily_Briefing_{date}.md`.
                   - Header: Top Findings
                   - Section: Community Sentiment
                   - Section: Recommendations (Should we download something new?)
                
                3. MAINTENANCE: Scan `~/Downloads` for chaos. Organize if needed.
                
                Execute now.
                """
                await self.push_frame(TextFrame(prompt))
                self._nightly_job_triggered = True
            
            await asyncio.sleep(self._check_interval)

    async def stop(self, frame: Frame):
        self._monitoring = False
        await super().stop(frame)
