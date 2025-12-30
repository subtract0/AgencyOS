
import logging
import asyncio
import subprocess
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import Frame, SystemFrame, TextFrame

class ThermalWatchdogService(FrameProcessor):
    """
    Monitors system temperature and throttles or warns if too hot.
    Uses 'powermetrics' (requires sudo) or 'sysctl' for thermal pressure.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._monitoring = False
        self._check_interval = 30 # seconds
        self._warned = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)

    async def start(self, frame: Frame):
        self._monitoring = True
        asyncio.create_task(self._monitor_loop())
        await super().start(frame)

    async def _monitor_loop(self):
        logging.info("ThermalWatchdog: Guard active.")
        while self._monitoring:
            try:
                # Check thermal pressure level (0=Normal, 1=Moderate, 2=Heavy, 3=Trapped)
                # This works on Apple Silicon without sudo
                cmd = ["sysctl", "-n", "machdep.xcpm.cpu_thermal_level"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                level = int(result.stdout.strip())
                
                if level >= 2: # Significant heat
                    logging.warning(f"ThermalWatchdog: High Thermal Pressure! Level {level}")
                    if not self._warned:
                        await self.push_frame(TextFrame("Warning: My core temperature is rising. I may throttle deep thought tasks."))
                        self._warned = True
                elif level == 0 and self._warned:
                    logging.info("ThermalWatchdog: Temperature normalized.")
                    await self.push_frame(TextFrame("Core temperature stabilized."))
                    self._warned = False
                    
            except Exception as e:
                logging.error(f"ThermalWatchdog error: {e}")
            
            await asyncio.sleep(self._check_interval)

    async def stop(self, frame: Frame):
        self._monitoring = False
        await super().stop(frame)
