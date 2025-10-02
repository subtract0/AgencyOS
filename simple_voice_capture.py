#!/usr/bin/env python3
"""
Simple Voice Capture - Append Transcriptions to File
No complex dependencies, just: whisper + pyaudio
"""
import os
import sys
import time
from datetime import datetime

# Try to import required packages
try:
    import whisper
    import pyaudio
    import numpy as np
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip3 install openai-whisper pyaudio numpy")
    sys.exit(1)

# Configuration
SAMPLE_RATE = 16000
CHUNK_DURATION = 5.0  # Capture 5 seconds at a time
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
VAD_THRESHOLD = 15.0  # Low threshold for detecting speech
OUTPUT_FILE = "logs/trinity_ambient/voice_transcriptions.txt"

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

def calculate_rms(audio_data):
    """Calculate RMS level of audio"""
    samples = np.frombuffer(audio_data, dtype=np.int16)
    if len(samples) == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))

def append_transcription(text, confidence=0.0, rms_level=0.0):
    """Append transcription to file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"[{timestamp}] RMS:{rms_level:.1f} Conf:{confidence:.2f} | {text}\n")
    print(f"✅ Saved: {text[:50]}...")

def main():
    print("🎤 Simple Voice Capture Starting...")
    print(f"📝 Saving transcriptions to: {OUTPUT_FILE}")
    print(f"🔊 VAD Threshold: {VAD_THRESHOLD}")
    print(f"⏱️  Chunk Duration: {CHUNK_DURATION}s")
    print("=" * 60)

    # Load Whisper model
    print("Loading Whisper 'base' model...")
    model = whisper.load_model("base")
    print("✅ Model loaded")

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    try:
        # Open microphone stream
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )

        print(f"\n🎙️  Listening... (Press Ctrl+C to stop)")
        print("💡 SPEAK CLEARLY AND LOUDLY for best results\n")

        cycle = 0
        while True:
            cycle += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle {cycle}: Capturing {CHUNK_DURATION}s...")

            # Read audio chunk
            audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)

            # Calculate RMS for VAD
            rms = calculate_rms(audio_data)
            print(f"  RMS level: {rms:.1f} (threshold: {VAD_THRESHOLD})")

            if rms > VAD_THRESHOLD:
                print(f"  🗣️  Speech detected! Transcribing...")

                # Convert to float32 numpy array for Whisper
                samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Transcribe
                result = model.transcribe(samples, fp16=False, language=None)
                text = result["text"].strip()
                confidence = result.get("confidence", 0.0)

                if text:
                    print(f"  📝 Transcription: '{text}'")
                    append_transcription(text, confidence, rms)
                else:
                    print(f"  ⚠️  Empty transcription (background noise?)")
            else:
                print(f"  💤 Silence (below threshold)")

            print()  # Blank line between cycles

    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print(f"\n📄 All transcriptions saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
