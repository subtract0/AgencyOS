
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
SILENCE_THRESHOLD = 0.01  # Amplitude threshold for silence detection
SILENCE_DURATION = 2.0    # Seconds of silence to trigger stop

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
        Record audio from the microphone.
        Args:
            duration: Fixed duration to record (if set).
            max_duration: Maximum duration if using VAD (auto-stop).
        Returns:
            Numpy array of audio data (float32).
        """
        if duration:
            print(f"🔴 Recording for {duration} seconds...")
            audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32')
            sd.wait()
            print("⏹️ Recording stopped.")
            return audio.flatten()
        else:
            print("🔴 Listening (speak now, stops after silence)...")
            frames = []
            silent_chunks = 0
            chunk_size = int(SAMPLE_RATE * 0.5) # 0.5s chunks
            max_chunks = int(max_duration * 2)
            
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32') as stream:
                for _ in range(max_chunks):
                    data, overflowed = stream.read(chunk_size)
                    if overflowed:
                        print("Warning: Audio buffer overflow")
                        
                    frames.append(data)
                    
                    # Simple VAD
                    amplitude = np.max(np.abs(data))
                    if amplitude < SILENCE_THRESHOLD:
                        silent_chunks += 1
                    else:
                        silent_chunks = 0
                        
                    # Stop if silence persists > SILENCE_DURATION
                    if silent_chunks > (SILENCE_DURATION * 2):
                        print("⏹️ Silence detected. Stopping.")
                        break
            
            return np.concatenate(frames).flatten()

    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio data using MLX Whisper.
        """
        print("⚡ Transcribing on M4 Neural Engine...")
        
        # MLX Whisper expects the text or path, but for raw audio we might need to save or pass directly
        # mlx_whisper.transcribe supports numpy array input directly from 0.4.0+
        
        try:
            result = mlx_whisper.transcribe(
                audio_data,
                path_or_hf_repo=self.model_path,
                verbose=False
            )
            text = result['text'].strip()
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
