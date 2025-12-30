
import os
import sys
import time
import sounddevice as sd
import numpy as np
import subprocess
from kokoro_onnx import Kokoro

# Config
# Config
MODEL_PATH = "experiments/models/kokoro/kokoro-v0_19.onnx"
VOICES_PATH = "experiments/models/kokoro/voices.bin"
DEFAULT_VOICE = "af_sky"  # American Female Sky (High quality)

class VoiceSpeaker:
    def __init__(self):
        self.use_kokoro = False
        self.kokoro = None
        
        # Try to load Kokoro
        if os.path.exists(MODEL_PATH) and os.path.exists(VOICES_PATH):
            try:
                print(f"🔈 Loading Kokoro TTS ({DEFAULT_VOICE})...")
                self.kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
                self.use_kokoro = True
                print("✅ Kokoro TTS Loaded.")
            except Exception as e:
                print(f"⚠️ Kokoro Load Failed: {e}")
        else:
            print("⚠️ Kokoro model not found. Using Native TTS fallback.")
            
    def speak(self, text: str):
        """Speak the text using the best available engine."""
        text = text.strip()
        if not text:
            return

        if self.use_kokoro and self.kokoro:
            try:
                # Generate audio
                # stream.create_stream returns (samples, sample_rate) generator
                # allow skipping long generation by playing chunks?
                # For simplicity, generate full sentence for now (Kokoro is fast)
                
                # Split roughly by sentences to avoid massive generation delay
                # But Kokoro handles short texts best (max 500 chars recommended)
                chunks = [text] # TODO: Split long text
                
                for chunk in chunks:
                    samples, sample_rate = self.kokoro.create(chunk, voice=DEFAULT_VOICE, speed=1.0, lang="en-us")
                    
                    # Play immediately
                    sd.play(samples, sample_rate)
                    sd.wait() # Block until finished
                    
            except Exception as e:
                print(f"❌ Kokoro Error: {e}")
                self._fallback_speak(text)
        else:
            self._fallback_speak(text)

    def _fallback_speak(self, text: str):
        """Use macOS native 'say' command."""
        try:
            # -v Daniel is a decent British voice, or use System default
            subprocess.run(["say", text])
        except Exception as e:
            print(f"❌ Native TTS Error: {e}")

if __name__ == "__main__":
    # Test
    speaker = VoiceSpeaker()
    speaker.speak("I am completely operational and all my circuits are functioning perfectly.")
