
import os
import sys
import time
import numpy as np
import sounddevice as sd
import mlx_whisper
from typing import Optional, Callable

# Constants
SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHANNELS = 1
SILENCE_THRESHOLD = 0.02  # Increased from 0.01 to avoid noise triggering
SILENCE_DURATION = 2.0    # Seconds of silence to trigger stop

# Known Whisper hallucinations when fed silence/noise
HALLUCINATIONS = [
    "Thank you.", "You", "Let's go.", "I'm going to show you how to use the",
    "MBC News", "Subtitles by", "Thank you for watching", "Start.",
    "Copyright", "All rights reserved", "you", "Okay.", "So, let's go."
]

class VoiceListener:
    def __init__(self, model_path: str = "mlx-community/whisper-turbo"):
        """
        Initialize the Voice Listener using MLX-Whisper.
        Args:
            model_path: The HuggingFace model path for mlx-whisper (default: turbo for speed).
        """
        self.model_path = model_path
        print(f"🎤 VoiceListener initialized. Model: {model_path}")
        print(f"🎤 Audio Device: {sd.query_devices(kind='input')['name']}")

    def record_audio(self, duration: Optional[float] = None, max_duration: float = 30.0) -> np.ndarray:
        """
        Record audio from the microphone. Returns None if mostly silence.
        """
        if duration:
            print(f"🔴 Recording for {duration} seconds...")
            audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32')
            sd.wait()
            print("⏹️ Recording stopped.")
            return audio.flatten()
        else:
            print("🔴 Listening (speak now)...")
            frames = []
            silent_chunks = 0
            chunk_size = int(SAMPLE_RATE * 0.5) # 0.5s chunks
            max_chunks = int(max_duration * 2)
            
            # Track if we actually heard anything significant
            max_amplitude_detected = 0.0
            
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32') as stream:
                for _ in range(max_chunks):
                    data, overflowed = stream.read(chunk_size)
                    if overflowed:
                        print("Warning: Audio buffer overflow")
                    
                    frames.append(data)
                    
                    # Simple VAD
                    amplitude = np.max(np.abs(data))
                    max_amplitude_detected = max(max_amplitude_detected, amplitude)
                    
                    if amplitude < SILENCE_THRESHOLD:
                        silent_chunks += 1
                    else:
                        silent_chunks = 0
                        
                    # Stop if silence persists > SILENCE_DURATION
                    if silent_chunks > (SILENCE_DURATION * 2):
                        # print("⏹️ Silence detected. Stopping.")
                        break
            
            audio_data = np.concatenate(frames).flatten()
            
            # OPTIMIZATION: If audio was mostly silence, don't even transcribe.
            # This saves massive M4 compute and prevents hallucinations.
            if max_amplitude_detected < SILENCE_THRESHOLD:
                print("💤 Ignored (Silence).")
                return None
                
            return audio_data

    def transcribe(self, audio_data: Optional[np.ndarray]) -> str:
        """
        Transcribe audio data using MLX Whisper.
        """
        if audio_data is None or len(audio_data) == 0:
            return ""

        print("⚡ Transcribing on M4 Neural Engine...")
        
        try:
            result = mlx_whisper.transcribe(
                audio_data,
                path_or_hf_repo=self.model_path,
                verbose=False,
                language="en"
            )
            text = result['text'].strip()
            
            # Anti-Hallucination Filter
            if text in HALLUCINATIONS or len(text) < 2:
                print(f"👻 Ignored Hallucination: '{text}'")
                return ""
            
            # Check for repeated hallucinations (e.g. "Thank you. Thank you.")
            if "Thank you." in text and len(text) < 25:
                 print(f"👻 Ignored Hallucination: '{text}'")
                 return ""

            print(f"🗣️ You said: '{text}'")
            return text
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return ""

if __name__ == "__main__":
    # Test run
    listener = VoiceListener()
    try:
        audio = listener.record_audio(max_duration=10.0)
        text = listener.transcribe(audio)
        print(f"📝 Final Transcript: {text}")
    except KeyboardInterrupt:
        print("\n👋 Exiting.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
