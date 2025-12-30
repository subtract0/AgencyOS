
import numpy as np
import mlx_whisper
import logging
from typing import AsyncGenerator

from pipecat.frames.frames import Frame, TextFrame, TranscriptionFrame
from pipecat.services.stt_service import SegmentedSTTService

class MLXWhisperService(SegmentedSTTService):
    def __init__(self, model_path: str = "mlx-community/whisper-turbo", **kwargs):
        super().__init__(**kwargs)
        self.model_path = model_path
        self._model_loaded = False
        logging.info(f"MLXWhisperService initialized with model: {model_path}")

    async def _handle_user_stopped_speaking(self, frame):
        """Override to pass raw PCM instead of WAV."""
        if frame.emulated:
            return
        self._user_speaking = False
        
        # Pass raw PCM bytes to run_stt
        if len(self._audio_buffer) > 0:
            await self.process_generator(self.run_stt(bytes(self._audio_buffer)))
        
        self._audio_buffer.clear()

    async def run_stt(self, audio: bytes) -> AsyncGenerator[Frame, None]:
        if not self._model_loaded:
             self._model_loaded = True
        
        if not audio:
            return

        # Convert raw bytes (16-bit PCM) to float32 numpy array
        # Assuming 16kHz mono as configured in Transport
        audio_data = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        
        try:
            logging.debug(f"Transcribing {len(audio_data)} samples...")
            # Use mlx_whisper to transcribe
            result = mlx_whisper.transcribe(audio_data, path_or_hf_repo=self.model_path)
            text = result.get("text", "").strip()
            
            if text:
                logging.info(f"Transcribed: '{text}'")
                yield TranscriptionFrame(text, "", 0) # Use TranscriptionFrame for STT results usually
                # Or TextFrame? Pipecat LLM implementation usually expects one or the other.
                # Standard LLMService often expects TextFrame OR TranscriptionFrame.
                # TranscriptionFrame is richer (includes timestamp etc).
                # But LLMService often handles TextFrame more natively for "User Input".
                # Let's verify what standard services use. Deepgram yields TranscriptionFrame.
                
                # Update: In V2, we want to yield TextFrame for the User input if we want it to be added to context?
                # Actually, standard pipecat pipeline: STT -> Aggregator -> Context -> LLM.
                # We will check how we wire it up later, but TranscriptionFrame is safer for STT.
                
        except Exception as e:
            logging.error(f"Error in MLX Whisper: {e}")

