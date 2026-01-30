
import asyncio
import signal
import sys
import logging
import os
import json

# Ensure imports work from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.frames.frames import EndFrame, TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

from cells.voice.simple_transport import SimpleTransport 
from cells.voice.services.mlx_stt import MLXWhisperService
from cells.voice.services.agency_llm import AgencyLLMService
from cells.voice.services.kokoro_tts import KokoroTTSService
from cells.voice.services.qwen_tts import Qwen3TTSService
from cells.voice.vad_processor import VADProcessor
from cells.voice.services.thermal_watchdog import ThermalWatchdogService
from cells.voice.services.scheduler import SchedulerService

from cells.shared.message_bus import MessageBus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceCell")

class VoiceCell:
    """
    Class 19: The Voice.
    A full-duplex voice cell that connects the Audit/Brain (LLM) to the Ear/Mouth (Audio),
    while also subscribing to the central MessageBus for external control.
    """
    def __init__(self, input_device_index=3): # Default to cam link
        self.input_device_index = input_device_index
        self.running = False
        self.task = None
        self.bus = MessageBus() # Persistent connection

    async def run(self):
        self.running = True
        print("🟢 VoiceCell (Class 19) Starting...")
        
        # 1. Transport & VAD
        transport = SimpleTransport(input_device_index=self.input_device_index)
        
        vad_params = VADParams(
            confidence=0.7, 
            start_secs=0.2, 
            stop_secs=2.0,
            min_volume=0.6
        )
        vad_analyzer = SileroVADAnalyzer(params=vad_params)
        vad_processor = VADProcessor(analyzer=vad_analyzer)
        
        # 2. Services
        stt = MLXWhisperService(model_path="mlx-community/whisper-turbo")
        watchdog = ThermalWatchdogService()
        scheduler = SchedulerService()
        llm = AgencyLLMService()
        
        # TTS Selection
        # Qwen3-TTS (The Upgrade)
        qwen_model_path = "experiments/models/qwen3_tts"
        USE_QWEN_TTS = True
        
        if USE_QWEN_TTS:
            tts = Qwen3TTSService(
                model_path=qwen_model_path,
                reference_audio="experiments/voices/klara_reference.wav" 
            )
        else:
            kokoro_model = "experiments/models/kokoro/kokoro-v0_19.onnx"
            kokoro_voices = "experiments/models/kokoro/voices.bin"
            tts = KokoroTTSService(
                model_path=kokoro_model,
                voices_path=kokoro_voices,
                voice="af_sky"
            )
        
        # 3. Pipeline
        # Input -> VAD -> STT -> Watchdog -> Scheduler -> LLM -> TTS -> Output
        pipeline = Pipeline(
            [
                transport.input(),
                vad_processor,
                stt,
                watchdog,
                scheduler,
                llm,
                tts,
                transport.output(),
            ]
        )
        
        # 4. Task
        self.task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
            ),
            idle_timeout_secs=None,
        )
        
        runner = PipelineRunner()
        
        # 5. Bus Subscription (Sidecar)
        asyncio.create_task(self._bus_listener())

        # Handle Shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
        
        print("   Speak comfortably. Interrupt anytime.")
        await runner.run(self.task)

    async def _bus_listener(self):
        """Listens for commands on the 'voice' channel."""
        logger.info("Bus Listener started on channel 'voice'")
        async for msg in self.bus.subscribe("voice"):
            if not self.running: 
                break
                
            try:
                data = msg.get('message_data', {})
                action = data.get('action')
                
                if action == 'speak':
                    text = data.get('text')
                    if text and self.task:
                        print(f"📣 Bus Command: SPEAK '{text[:30]}...'")
                        # Inject directly into pipeline (bypassing LLM if needed, or inject as System message?)
                        # Typically we want TTS to speak it. 
                        # We queue a TextFrame. In our pipeline, LLM produces TextFrames for TTS.
                        # If we inject a TextFrame before TTS, it will be spoken.
                        await self.task.queue_frame(TextFrame(text))
                        
                elif action == 'stop':
                    if self.task:
                         print("🛑 Bus Command: STOP")
                         # How to interrupt? 
                         # Typically sending a UserStartedSpeakingFrame or similar triggers interruption, 
                         # or we manually clear queues?
                         # For now, we can try queuing an EndFrame? No that kills the task.
                         pass

                await self.bus.ack(msg['_message_id'])

            except Exception as e:
                logger.error(f"Bus Error: {e}")

    async def shutdown(self):
        print("Caught interrupt. Stopping...")
        self.running = False
        if self.task:
            await self.task.queue_frame(EndFrame())
        self.bus.close()

if __name__ == "__main__":
    try:
        cell = VoiceCell()
        asyncio.run(cell.run())
    except KeyboardInterrupt:
        pass
