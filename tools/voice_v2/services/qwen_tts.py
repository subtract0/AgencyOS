
import asyncio
import logging
import os
import numpy as np
from typing import AsyncGenerator

# Third-party imports for Qwen3-TTS
try:
    import torch
    import soundfile as sf
    from qwen_tts import Qwen3TTSModel
    QWEN_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Qwen3TTSService: Dependencies missing ({e}). Install 'qwen-tts', 'torch', 'soundfile'.")
    QWEN_AVAILABLE = False

from pipecat.frames.frames import Frame, OutputAudioRawFrame, TTSStartedFrame, TTSStoppedFrame, ErrorFrame
from pipecat.services.tts_service import TTSService

class Qwen3TTSService(TTSService):
    """
    Integration for Qwen3-TTS (Base Model for Voice Cloning).
    """
    
    def __init__(self, model_path: str, reference_audio: str = None, device: str = None, **kwargs):
        super().__init__(**kwargs)
        self.model_path = model_path
        self.reference_audio = reference_audio
        self.reference_text = "Standard placeholder text for voice cloning reference." # Should ideally be passed in or loaded
        
        # Determine device
        if not device:
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda:0"
            else:
                self.device = "cpu"
        else:
            self.device = device
            
        self.model = None
        self.voice_clone_prompt = None
        
        if QWEN_AVAILABLE:
            self._load_model()
        else:
            logging.error("Qwen3TTSService: qwen-tts package not available.")

    def _load_model(self):
        try:
            logging.info(f"Qwen3TTSService: Loading model from {self.model_path} on {self.device}...")
            
            # Use local path if exists, otherwise assume HF Hub ID
            # If path implies local but doesn't exist, we might fail, but let's try.
            load_path = self.model_path
            
            self.model = Qwen3TTSModel.from_pretrained(
                load_path,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                attn_implementation="sdpa" # optimized for torch 2.0+
            )
            logging.info("Qwen3TTSService: Model loaded.")
            
            # Pre-compute voice clone prompt if reference provided
            if self.reference_audio and os.path.exists(self.reference_audio):
                logging.info(f"Qwen3TTSService: Pre-computing voice clone prompt from {self.reference_audio}...")
                # We need reference text for high quality clone, or x_vector_only_mode=True
                # For now, we use x_vector_only_mode=True if we don't have text, 
                # OR we assume the user provides specific text.
                # Simplest fallback: x_vector_only_mode=True
                
                self.voice_clone_prompt = self.model.create_voice_clone_prompt(
                    ref_audio=self.reference_audio,
                    x_vector_only_mode=True 
                )
                logging.info("Qwen3TTSService: Voice clone prompt ready.")
            
        except Exception as e:
            logging.error(f"Qwen3TTSService: Failed to load: {e}")

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        if not self.model:
            logging.error("Qwen3TTSService: Model not loaded.")
            yield ErrorFrame("TTS Model not loaded")
            return

        if not text.strip():
            return

        logging.debug(f"Qwen3TTSService: Synthesizing '{text}'")
        yield TTSStartedFrame()
        
        try:
            # Run inference in thread to avoid blocking loop
            # We use pre-computed prompt if available, else standard clone
            
            def _inference():
                if self.voice_clone_prompt:
                    wavs, sr = self.model.generate_voice_clone(
                        text=text,
                        language="English", # Make dynamic?
                        voice_clone_prompt=self.voice_clone_prompt
                    )
                else:
                    # Fallback if no reference audio was loaded at start?
                    # Or use a default speaker if using CustomVoice model?
                    # Assuming Base model requires reference.
                    # We'll try to generate without ref (might fail for Base) or use a temporary one?
                    # Current impl assumes Base model usage as per run_pipecat.
                    # If we don't have reference, we can't clone.
                    raise ValueError("No reference audio provided for Voice Clone model.")
                return wavs, sr

            wavs, sample_rate = await asyncio.to_thread(_inference)
            
            if wavs is not None and len(wavs) > 0:
                audio_float = wavs[0]
                
                # Convert float32 to int16 PCM
                # Clip to prevent overflow
                audio_int16 = (audio_float * 32767).clip(-32768, 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
                
                num_channels = 1 if len(audio_float.shape) == 1 else audio_float.shape[1]

                # Yield OutputAudioRawFrame
                # Since Qwen3 generates full audio (non-streaming in this API), 
                # we yield it as one chunk.
                yield OutputAudioRawFrame(audio=audio_bytes, sample_rate=sample_rate, num_channels=num_channels)
                
        except Exception as e:
            logging.error(f"Qwen3TTSService: Error: {e}")
            yield ErrorFrame(str(e))
            
        yield TTSStoppedFrame()
