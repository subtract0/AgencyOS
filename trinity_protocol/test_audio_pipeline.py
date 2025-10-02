#!/usr/bin/env python3
"""
Quick audio pipeline test for Trinity Protocol.

Tests: Mic detection → Audio capture → Whisper transcription
"""

import sys
import os

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_microphone_detection():
    """Test if pyaudio can detect microphones."""
    print("🎤 Testing microphone detection...")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        print(f"✅ Found {device_count} audio devices")

        # List input devices
        for i in range(device_count):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"   Device {i}: {info['name']} (inputs: {info['maxInputChannels']})")

        p.terminate()
        return True
    except ImportError:
        print("❌ pyaudio not installed:")
        print("   brew install portaudio")
        print("   pip install pyaudio")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_whisper_availability():
    """Test if Whisper is available."""
    print("\n🔊 Testing Whisper availability...")

    # Try openai-whisper first
    try:
        import whisper
        print("✅ openai-whisper installed")
        return 'openai-whisper'
    except ImportError:
        pass

    # Try whisper.cpp
    import subprocess
    try:
        result = subprocess.run(['whisper', '--version'],
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            print("✅ whisper.cpp installed")
            return 'whisper.cpp'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print("❌ Whisper not installed:")
    print("   Option 1 (Python - easier): pip install openai-whisper")
    print("   Option 2 (C++ - faster):    brew install whisper-cpp")
    return None


def test_audio_capture(duration_seconds=3):
    """Test 3-second audio capture from default microphone."""
    print(f"\n🎙️  Testing {duration_seconds}s audio capture...")
    try:
        import pyaudio
        import wave
        import tempfile

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000  # Whisper expects 16kHz

        p = pyaudio.PyAudio()

        print("   Recording...")
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)

        frames = []
        for _ in range(0, int(RATE / CHUNK * duration_seconds)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        file_size = os.path.getsize(temp_file.name)
        print(f"✅ Captured {duration_seconds}s audio ({file_size} bytes)")
        print(f"   Temp file: {temp_file.name}")

        return temp_file.name
    except Exception as e:
        print(f"❌ Capture failed: {e}")
        return None


def test_whisper_transcription(audio_file):
    """Test Whisper transcription on audio file."""
    print("\n🎯 Testing Whisper transcription...")

    if not audio_file or not os.path.exists(audio_file):
        print("❌ No audio file to transcribe")
        return False

    try:
        import whisper
        print("   Loading Whisper model (first time may take ~1 min)...")
        model = whisper.load_model("base.en")

        print("   Transcribing...")
        result = model.transcribe(audio_file)

        text = result["text"].strip()
        if text:
            print(f"✅ Transcription successful:")
            print(f"   \"{text}\"")
            return True
        else:
            print("⚠️  Transcription returned empty (audio may be silent)")
            return False

    except ImportError:
        print("❌ openai-whisper not installed")
        return False
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return False


def main():
    """Run complete audio pipeline test."""
    print("━" * 60)
    print("🧪 Trinity Audio Pipeline Test")
    print("━" * 60)

    # Test 1: Microphone detection
    mic_ok = test_microphone_detection()

    # Test 2: Whisper availability
    whisper_backend = test_whisper_availability()

    # Test 3: Audio capture (if mic available)
    audio_file = None
    if mic_ok:
        audio_file = test_audio_capture(duration_seconds=3)

    # Test 4: Transcription (if Whisper + audio available)
    transcription_ok = False
    if whisper_backend == 'openai-whisper' and audio_file:
        transcription_ok = test_whisper_transcription(audio_file)

    # Summary
    print("\n━" * 60)
    print("📊 Test Summary")
    print("━" * 60)
    print(f"Microphone:     {'✅' if mic_ok else '❌'}")
    print(f"Whisper:        {'✅' if whisper_backend else '❌'} ({whisper_backend or 'not installed'})")
    print(f"Audio Capture:  {'✅' if audio_file else '❌'}")
    print(f"Transcription:  {'✅' if transcription_ok else '❌'}")
    print("━" * 60)

    if mic_ok and whisper_backend and transcription_ok:
        print("\n🎉 SUCCESS! Trinity audio pipeline is production-ready!")
        print("\nNext steps:")
        print("  1. ./STOP_TRINITY.sh  (stop current demo processes)")
        print("  2. ./START_TRINITY.sh  (restart with real audio)")
        print("  3. Talk about a project idea near your Mac")
        print("  4. Trinity will detect patterns and offer help")
        return 0
    else:
        print("\n⚠️  Setup incomplete. Install missing dependencies:")
        if not mic_ok:
            print("  brew install portaudio && pip install pyaudio")
        if not whisper_backend:
            print("  pip install openai-whisper")
        print("\nThen re-run: python trinity_protocol/test_audio_pipeline.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
