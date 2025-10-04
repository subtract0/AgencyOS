#!/usr/bin/env python3
"""
Smart Voice Filtering Pipeline - v1.0
Reduces 24/7 listening costs from $259/month to ~$15-25/month

Features:
- Silero VAD (ML-based speech detection)
- Speaker identification (filter your voice vs YouTube/others)
- Hybrid local+cloud transcription
- Cost tracking and statistics
"""

import json
import os
import sys
import tempfile
import wave
from datetime import datetime
from pathlib import Path

try:
    import numpy as np
    import pyaudio
    import torch
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip3 install pyaudio numpy torch torchaudio")
    sys.exit(1)

# Configuration
SAMPLE_RATE = 16000
CHUNK_DURATION = 3.0  # Shorter chunks for faster detection
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
RMS_THRESHOLD = 100.0  # Basic noise gate
SPEECH_PROB_THRESHOLD = 0.7  # Silero VAD confidence
SPEAKER_SIMILARITY_THRESHOLD = 0.75  # Speaker matching threshold

OUTPUT_DIR = Path("logs/trinity_ambient")
OUTPUT_FILE = OUTPUT_DIR / "voice_smart_filtered.txt"
STATS_FILE = OUTPUT_DIR / "filtering_stats.json"
SPEAKER_PROFILE = OUTPUT_DIR / "your_voice_profile.npy"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Silero VAD model (will auto-download on first run)
print("Loading Silero VAD model...")
try:
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=False, onnx=False
    )
    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
    print("✅ Silero VAD loaded")
except Exception as e:
    print(f"❌ Failed to load Silero VAD: {e}")
    print("Falling back to simple RMS-based detection")
    model = None


class FilteringStats:
    """Track filtering efficiency and costs"""

    def __init__(self, stats_file):
        self.stats_file = stats_file
        self.stats = self.load_stats()

    def load_stats(self):
        if self.stats_file.exists():
            with open(self.stats_file) as f:
                return json.load(f)
        return {
            "total_chunks": 0,
            "rms_rejected": 0,
            "vad_rejected": 0,
            "speaker_rejected": 0,
            "transcribed": 0,
            "total_audio_seconds": 0,
            "transcribed_seconds": 0,
            "estimated_cost_saved": 0.0,
            "estimated_cost_spent": 0.0,
        }

    def save_stats(self):
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)

    def update(self, chunk_seconds, stage_passed, transcribed=False):
        """Update statistics after processing a chunk"""
        self.stats["total_chunks"] += 1
        self.stats["total_audio_seconds"] += chunk_seconds

        if stage_passed == "rms_rejected":
            self.stats["rms_rejected"] += 1
        elif stage_passed == "vad_rejected":
            self.stats["vad_rejected"] += 1
        elif stage_passed == "speaker_rejected":
            self.stats["speaker_rejected"] += 1
        elif transcribed:
            self.stats["transcribed"] += 1
            self.stats["transcribed_seconds"] += chunk_seconds
            # Cost: $0.006 per minute
            cost = (chunk_seconds / 60) * 0.006
            self.stats["estimated_cost_spent"] += cost

        # Calculate saved cost (what we would have spent without filtering)
        rejected_seconds = self.stats["total_audio_seconds"] - self.stats["transcribed_seconds"]
        self.stats["estimated_cost_saved"] = (rejected_seconds / 60) * 0.006

        self.save_stats()

    def print_summary(self):
        """Print filtering efficiency summary"""
        total = self.stats["total_chunks"]
        if total == 0:
            return

        print("\n" + "=" * 60)
        print("📊 FILTERING STATISTICS")
        print("=" * 60)
        print(f"Total chunks analyzed: {total}")
        print(
            f"  ❌ RMS rejected: {self.stats['rms_rejected']} ({self.stats['rms_rejected'] * 100 // total}%)"
        )
        print(
            f"  ❌ VAD rejected: {self.stats['vad_rejected']} ({self.stats['vad_rejected'] * 100 // total}%)"
        )
        print(
            f"  ❌ Speaker rejected: {self.stats['speaker_rejected']} ({self.stats['speaker_rejected'] * 100 // total}%)"
        )
        print(
            f"  ✅ Transcribed: {self.stats['transcribed']} ({self.stats['transcribed'] * 100 // total}%)"
        )
        print()
        print(f"Audio processed: {self.stats['total_audio_seconds']:.1f}s")
        print(f"Actually transcribed: {self.stats['transcribed_seconds']:.1f}s")
        print(
            f"Filtered out: {self.stats['total_audio_seconds'] - self.stats['transcribed_seconds']:.1f}s"
        )
        print()
        print(f"💰 Estimated cost saved: ${self.stats['estimated_cost_saved']:.4f}")
        print(f"💳 Estimated cost spent: ${self.stats['estimated_cost_spent']:.4f}")

        if self.stats["total_audio_seconds"] > 0:
            hours = self.stats["total_audio_seconds"] / 3600
            monthly_cost = (self.stats["estimated_cost_spent"] / hours) * 24 * 30
            print(f"📈 Projected monthly cost (24/7): ${monthly_cost:.2f}")
        print("=" * 60)


def calculate_rms(audio_data):
    """Calculate RMS level of audio"""
    samples = np.frombuffer(audio_data, dtype=np.int16)
    if len(samples) == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))


def check_speech_silero(audio_data, sample_rate=16000):
    """
    Check if audio contains speech using Silero VAD
    Returns: (has_speech, confidence)
    """
    if model is None:
        # Fallback to RMS if model not loaded
        return True, 1.0

    try:
        # Convert to float32 tensor
        audio_tensor = torch.from_numpy(
            np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        )

        # Get speech probability
        speech_prob = model(audio_tensor, sample_rate).item()

        return speech_prob > SPEECH_PROB_THRESHOLD, speech_prob

    except Exception as e:
        print(f"  ⚠️  VAD error: {e}")
        return True, 0.0


def create_speaker_profile(audio_samples, save_path):
    """
    Create a speaker voice profile from audio samples
    For now, uses simple spectral features (can upgrade to speaker embeddings later)
    """
    # Simple approach: MFCC-based fingerprint
    # In production, use pyannote.audio or speechbrain
    try:
        import librosa

        # Extract MFCC features
        mfccs = []
        for audio in audio_samples:
            samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
            mfcc = librosa.feature.mfcc(y=samples, sr=SAMPLE_RATE, n_mfcc=13)
            mfccs.append(np.mean(mfcc, axis=1))

        # Average features
        profile = np.mean(mfccs, axis=0)
        np.save(save_path, profile)
        print(f"✅ Speaker profile saved to {save_path}")
        return profile

    except ImportError:
        print("⚠️  librosa not installed, speaker filtering disabled")
        print("Install with: pip install librosa")
        return None


def check_speaker_match(audio_data, profile):
    """
    Check if audio matches the speaker profile
    Returns: (is_match, similarity)
    """
    if profile is None:
        # No profile, pass everything through
        return True, 1.0

    try:
        import librosa
        from scipy.spatial.distance import cosine

        # Extract MFCC from current audio
        samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        mfcc = librosa.feature.mfcc(y=samples, sr=SAMPLE_RATE, n_mfcc=13)
        current_features = np.mean(mfcc, axis=1)

        # Calculate similarity (1 - cosine distance)
        similarity = 1 - cosine(profile, current_features)

        return similarity > SPEAKER_SIMILARITY_THRESHOLD, similarity

    except:
        return True, 0.0


def transcribe_local(audio_data):
    """Transcribe using local Whisper model (fallback)"""
    try:
        import whisper

        model = whisper.load_model("base")
        samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        result = model.transcribe(samples, language=None)
        return result["text"].strip(), result.get("language", "unknown")
    except:
        return "", "unknown"


def transcribe_cloud(audio_data):
    """Transcribe using OpenAI Whisper API (best accuracy)"""
    if not os.getenv("OPENAI_API_KEY"):
        print("  ⚠️  OPENAI_API_KEY not set, using local fallback")
        return transcribe_local(audio_data)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Save to temp WAV
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            with wave.open(temp_wav.name, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(audio_data)
            temp_path = temp_wav.name

        try:
            with open(temp_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    temperature=0.0,
                )

            return transcription.text.strip(), transcription.language

        finally:
            os.unlink(temp_path)

    except Exception as e:
        print(f"  ⚠️  Cloud API error: {e}, using local fallback")
        return transcribe_local(audio_data)


def append_transcription(text, language, rms_level, vad_conf, speaker_sim):
    """Save transcription with metadata"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_FILE, "a") as f:
        f.write(
            f"[{timestamp}] Lang:{language} RMS:{rms_level:.1f} "
            f"VAD:{vad_conf:.2f} Speaker:{speaker_sim:.2f} | {text}\n"
        )


def main():
    print("=" * 60)
    print("🎤 SMART VOICE FILTERING PIPELINE v1.0")
    print("=" * 60)
    print(f"📝 Output: {OUTPUT_FILE}")
    print(f"📊 Stats: {STATS_FILE}")
    print(f"🔊 RMS Threshold: {RMS_THRESHOLD}")
    print(f"🎯 VAD Threshold: {SPEECH_PROB_THRESHOLD}")
    print(f"👤 Speaker Threshold: {SPEAKER_SIMILARITY_THRESHOLD}")
    print("=" * 60)

    # Initialize stats tracker
    stats = FilteringStats(STATS_FILE)

    # Load or create speaker profile
    speaker_profile = None
    if SPEAKER_PROFILE.exists():
        speaker_profile = np.load(SPEAKER_PROFILE)
        print(f"✅ Loaded speaker profile from {SPEAKER_PROFILE}")
    else:
        print("⚠️  No speaker profile found")
        print("   Speak 3-5 clear sentences when prompted to create one")
        print("   (This helps filter your voice from YouTube/others)")

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
        print("💡 Multi-stage filtering: RMS → VAD → Speaker → Transcribe\n")

        # Collect samples for speaker profile if needed
        profile_samples = []
        need_profile = not SPEAKER_PROFILE.exists()

        cycle = 0
        while True:
            cycle += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Read audio chunk
            audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)

            # Stage 1: RMS check (basic noise gate)
            rms = calculate_rms(audio_data)

            if rms < RMS_THRESHOLD:
                if cycle % 10 == 0:  # Log every 10th silence
                    print(f"[{timestamp}] 💤 Silence (RMS:{rms:.1f})")
                stats.update(CHUNK_DURATION, "rms_rejected")
                continue

            print(f"[{timestamp}] 🔊 Audio detected (RMS:{rms:.1f})")

            # Stage 2: Silero VAD check (ML-based speech detection)
            has_speech, vad_confidence = check_speech_silero(audio_data, SAMPLE_RATE)

            if not has_speech:
                print(f"  ❌ Not speech (VAD:{vad_confidence:.2f}) - likely noise/music")
                stats.update(CHUNK_DURATION, "vad_rejected")
                continue

            print(f"  ✅ Speech detected (VAD:{vad_confidence:.2f})")

            # Stage 3: Speaker identification (your voice vs others)
            if need_profile and len(profile_samples) < 5:
                print(f"  📝 Recording sample {len(profile_samples) + 1}/5 for speaker profile...")
                profile_samples.append(audio_data)

                if len(profile_samples) == 5:
                    print("  🔨 Creating speaker profile...")
                    speaker_profile = create_speaker_profile(profile_samples, SPEAKER_PROFILE)
                    need_profile = False
                    print("  ✅ Speaker profile created! Now filtering...")
                continue

            is_your_voice, speaker_similarity = check_speaker_match(audio_data, speaker_profile)

            if not is_your_voice:
                print(
                    f"  ❌ Not your voice (similarity:{speaker_similarity:.2f}) - YouTube/other speaker"
                )
                stats.update(CHUNK_DURATION, "speaker_rejected")
                continue

            print(f"  ✅ Your voice detected (similarity:{speaker_similarity:.2f})")

            # Stage 4: Transcribe (hybrid: cloud if API key, else local)
            print("  🌐 Transcribing...")
            text, language = transcribe_cloud(audio_data)

            if text:
                print(f"  📝 [{language}] {text[:80]}...")
                append_transcription(text, language, rms, vad_confidence, speaker_similarity)
                stats.update(CHUNK_DURATION, "transcribed", transcribed=True)
            else:
                print("  ⚠️  Empty transcription")
                stats.update(CHUNK_DURATION, "transcribed", transcribed=False)

            print()

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

        # Print final statistics
        stats.print_summary()
        print(f"\n📄 Transcriptions saved to: {OUTPUT_FILE}")
        print(f"📊 Statistics saved to: {STATS_FILE}")


if __name__ == "__main__":
    main()
