#!/usr/bin/env python3
"""
FIXED Voice Capture - Optimized for Accuracy
- Uses small.en model (better accuracy)
- Forces English language
- Higher VAD threshold
- Real confidence scores
"""

import os
import sys
from datetime import datetime

try:
    import numpy as np
    import pyaudio
    import whisper
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip3 install openai-whisper pyaudio numpy")
    sys.exit(1)

# Configuration - OPTIMIZED
SAMPLE_RATE = 16000
CHUNK_DURATION = 5.0
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
VAD_THRESHOLD = 100.0  # Lower threshold for easier speech detection
OUTPUT_FILE = "logs/trinity_ambient/voice_transcriptions_fixed.txt"

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)


def calculate_rms(audio_data):
    """Calculate RMS level of audio"""
    samples = np.frombuffer(audio_data, dtype=np.int16)
    if len(samples) == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))


def append_transcription(text, confidence, rms_level):
    """Append transcription to file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"[{timestamp}] RMS:{rms_level:.1f} Conf:{confidence:.2f} | {text}\n")
    print(f"✅ Saved: {text[:80]}...")


def main():
    print("🎤 FIXED Voice Capture Starting...")
    print(f"📝 Saving to: {OUTPUT_FILE}")
    print(f"🔊 VAD Threshold: {VAD_THRESHOLD} (speak LOUDLY)")
    print(f"⏱️  Chunk Duration: {CHUNK_DURATION}s")
    print("=" * 60)

    # Load Whisper model - medium.en for best accuracy
    print("📥 Downloading/Loading Whisper 'medium.en' model...")
    print("   (First run: ~1.5GB download, please wait)")
    model = whisper.load_model("medium.en")
    print("✅ Model loaded: medium.en (WER: 3-5%, best accuracy)")
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
        print(f"💡 SPEAK LOUDLY - RMS must be >{VAD_THRESHOLD} to trigger\n")

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
                print("  🗣️  Speech detected! Transcribing...")

                # Convert to float32 for Whisper
                samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Transcribe with OPTIMAL parameters (auto-detect language)
                result = model.transcribe(
                    samples,
                    fp16=False,
                    language=None,  # Auto-detect (German/English/etc)
                    temperature=0.0,  # Deterministic
                    beam_size=5,  # Accuracy
                    best_of=5,  # Multi-pass
                    condition_on_previous_text=False,  # No hallucinations
                )

                text = result["text"].strip()

                # Calculate REAL confidence from segments
                segments = result.get("segments", [])
                if segments:
                    confidence = 1.0 - sum(s.get("no_speech_prob", 0.5) for s in segments) / len(
                        segments
                    )
                else:
                    confidence = 0.0

                if text:
                    print(f"  📝 Transcription: '{text}'")
                    print(f"  🎯 Confidence: {confidence:.2f}")
                    append_transcription(text, confidence, rms)
                else:
                    print("  ⚠️  Empty transcription")
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
