
import asyncio
import signal
import sys
import logging
import os

# Ensure imports work from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from tools.voice_v2.simple_transport import SimpleTransport # Custom blocking transport
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame

from tools.voice_v2.services.mlx_stt import MLXWhisperService
from tools.voice_v2.services.agency_llm import AgencyLLMService
from tools.voice_v2.services.kokoro_tts import KokoroTTSService
from tools.voice_v2.vad_processor import VADProcessor

from tools.voice_v2.services.thermal_watchdog import ThermalWatchdogService
from tools.voice_v2.services.scheduler import SchedulerService

logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Transport & VAD
    # Use our custom transport that matches debug_audio.py logic
    transport = SimpleTransport(input_device_index=3)
    
    from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
    
    # ...

    # 1. Transport & VAD
    # Use our custom transport that matches debug_audio.py logic
    transport = SimpleTransport(input_device_index=3)
    
    # Increase stop_secs to 2.0 to prevent chopping sentences
    vad_params = VADParams(
        confidence=0.7, 
        start_secs=0.2, 
        stop_secs=2.0,  # CRITICAL FIX: Allow 2s pause before cutting off
        min_volume=0.6
    )
    vad_analyzer = SileroVADAnalyzer(params=vad_params)
    vad_processor = VADProcessor(analyzer=vad_analyzer)
    
    # 2. Services
    stt = MLXWhisperService(model_path="mlx-community/whisper-turbo")
    
    watchdog = ThermalWatchdogService()
    scheduler = SchedulerService()
    
    llm = AgencyLLMService()
    
    # Kokoro paths
    # Assuming running from repo root
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
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True, # The Magic!
            enable_metrics=True,
        ),
        idle_timeout_secs=None, # Disable timeout for always-on assistant
    )
    
    # 5. Runner
    runner = PipelineRunner()
    
    async def shutdown(sig, frame):
        print("Caught interrupt. Stopping...")
        await task.queue_frame(EndFrame())
    
    # Handle Ctrl+C
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
       loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig, None)))
        
    print("🟢 Brain V2 (Pipecat) Starting...")
    print("   Speak comfortably. Interrupt anytime.")
    
    await runner.run(task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
