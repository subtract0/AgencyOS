
import asyncio
import numpy as np
import logging
import os
from typing import AsyncGenerator

from pipecat.frames.frames import Frame, OutputAudioRawFrame, TTSStartedFrame, TTSStoppedFrame, ErrorFrame
from pipecat.services.tts_service import TTSService

from kokoro_onnx import Kokoro

class KokoroTTSService(TTSService):
    def __init__(self, model_path: str, voices_path: str, voice: str = "af_sky", **kwargs):
        super().__init__(**kwargs)
        self.model_path = model_path
        self.voices_path = voices_path
        self.voice = voice
        self.kokoro = None
        
        # Load Kokoro
        if os.path.exists(model_path) and os.path.exists(voices_path):
            try:
                logging.info(f"KokoroTTSService: Loading model...")
                self.kokoro = Kokoro(model_path, voices_path)
                logging.info("KokoroTTSService: Loaded.")
            except Exception as e:
                logging.error(f"KokoroTTSService: Failed to load: {e}")
        else:
            logging.error(f"KokoroTTSService: Model/Voices not found at {model_path} / {voices_path}")

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        if not self.kokoro:
            logging.error("KokoroTTSService: Model not loaded.")
            return

        if not text.strip():
            return

        logging.debug(f"KokoroTTSService: Synthesizing '{text}'")
        
        yield TTSStartedFrame()
        
        try:
            # Run blocking synthesis in a thread
            # Kokoro.create returns (samples, sample_rate)
            # samples is np.float32
            output = await asyncio.to_thread(
                self.kokoro.create, 
                text, 
                voice=self.voice, 
                speed=1.0, 
                lang="en-us"
            )
            
            if output:
                samples, sample_rate = output
                # Convert float32 to int16 PCM
                audio_int16 = (samples * 32767).clip(-32768, 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
                
                # Check num_channels. Kokoro usually mono?
                # If samples is 1D, it's mono.
                num_channels = 1 if len(samples.shape) == 1 else samples.shape[1]

                # Yield OutputAudioRawFrame
                # We yield the whole clip as one frame for now, unless we want to chunk it.
                # Pipecat transports handle buffering usually.
                yield OutputAudioRawFrame(audio=audio_bytes, sample_rate=sample_rate, num_channels=num_channels)
                
        except Exception as e:
            logging.error(f"KokoroTTSService: Error: {e}")
            yield ErrorFrame(str(e))
            
        yield TTSStoppedFrame()
