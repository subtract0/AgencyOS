#!/usr/bin/env python3
"""
Cloud-based Voice Transcription using OpenAI Whisper API
Same technology as Blabby.ai - MUCH better accuracy than local models
"""

import os
import sys
import tempfile
from datetime import datetime

try:
    import numpy as np
    import pyaudio
    from openai import OpenAI
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip3 install openai pyaudio numpy")
    sys.exit(1)

# Configuration
SAMPLE_RATE = 16000
CHUNK_DURATION = 5.0
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
VAD_THRESHOLD = 100.0
OUTPUT_FILE = "logs/trinity_ambient/voice_transcriptions_cloud.txt"

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY environment variable not set")
    print("Set it with: export OPENAI_API_KEY='your-key-here'")
    sys.exit(1)

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def calculate_rms(audio_data):
    """Calculate RMS level of audio"""
    samples = np.frombuffer(audio_data, dtype=np.int16)
    if len(samples) == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))


def append_transcription(text, language, rms_level):
    """Append transcription to file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"[{timestamp}] Lang:{language} RMS:{rms_level:.1f} | {text}\n")
    print(f"✅ Saved: [{language}] {text[:80]}...")


def main():
    print("🎤 Cloud-based Voice Capture (OpenAI Whisper API)")
    print(f"📝 Saving to: {OUTPUT_FILE}")
    print(f"🔊 VAD Threshold: {VAD_THRESHOLD}")
    print(f"⏱️  Chunk Duration: {CHUNK_DURATION}s")
    print("🌐 Using: OpenAI Whisper API (same as Blabby.ai)")
    print("=" * 60)

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        print("\n🎙️  Listening... (Press Ctrl+C to stop)")
        print("💡 Speak in ANY language - auto-detected\n")

        cycle = 0
        while True:
            cycle += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Cycle {cycle}: Capturing {CHUNK_DURATION}s...")

            # Read audio chunk
            audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)

            # Calculate RMS for VAD
            rms = calculate_rms(audio_data)
            print(f"  RMS level: {rms:.1f} (threshold: {VAD_THRESHOLD})")

            if rms > VAD_THRESHOLD:
                print("  🗣️  Speech detected! Transcribing via OpenAI API...")

                # Save to temporary WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    import wave

                    with wave.open(temp_wav.name, "wb") as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)  # 16-bit
                        wav_file.setframerate(SAMPLE_RATE)
                        wav_file.writeframes(audio_data)

                    temp_path = temp_wav.name

                try:
                    # Call OpenAI Whisper API
                    with open(temp_path, "rb") as audio_file:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="verbose_json",
                            temperature=0.0,
                        )

                    text = transcription.text.strip()
                    language = transcription.language

                    if text:
                        print(f"  📝 Transcription: '{text}'")
                        print(f"  🌍 Language: {language}")
                        append_transcription(text, language, rms)
                    else:
                        print("  ⚠️  Empty transcription")

                except Exception as e:
                    print(f"  ❌ API Error: {e}")

                finally:
                    # Clean up temp file
                    os.unlink(temp_path)

            else:
                print("  💤 Silence (below threshold)")

            print()  # Blank line

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
