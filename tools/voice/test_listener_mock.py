
import sys
import os
import numpy as np
from unittest.mock import MagicMock, patch

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock sounddevice BEFORE importing listener
sys.modules['sounddevice'] = MagicMock()

from tools.voice.listener import VoiceListener

def test_mock_transcription():
    print("🧪 Testing VoiceListener with synthetic audio...")
    
    # Initialize
    listener = VoiceListener(model_path="mlx-community/whisper-turbo")
    
    # Generate synthetic audio (1 second of silence/noise)
    # Whisper expects float32
    duration = 1.0
    samplerate = 16000
    synthetic_audio = np.random.uniform(-0.1, 0.1, int(duration * samplerate)).astype(np.float32)
    
    print(f"🎵 Generated {len(synthetic_audio)} samples of synthetic audio.")
    
    # Transcribe
    # Note: Random noise usually transcribes to hallucinations or empty string.
    # We just want to ensure it doesn't CRASH.
    try:
        text = listener.transcribe(synthetic_audio)
        print(f"✅ Transcription successful (Result: '{text}')")
    except Exception as e:
        print(f"❌ Transcription crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_mock_transcription()
