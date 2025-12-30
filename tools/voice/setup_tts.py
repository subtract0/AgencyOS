
import os
import requests
from pathlib import Path

# Config
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.json"
MODEL_DIR = "experiments/models/kokoro"

def download_file(url, dest_path):
    if os.path.exists(dest_path):
        print(f"✅ Exists: {dest_path}")
        return

    print(f"⬇️ Downloading {url}...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    
    with open(dest_path, 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)
    print(f"✅ Downloaded: {dest_path}")

def setup_tts():
    print("🔊 Setting up Kokoro TTS...")
    
    # Create directory
    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
    
    # Download Model
    download_file(MODEL_URL, os.path.join(MODEL_DIR, "kokoro-v0_19.onnx"))
    
    # Download Voices
    download_file(VOICES_URL, os.path.join(MODEL_DIR, "voices.json"))
    
    print("✨ TTS Setup Complete.")

if __name__ == "__main__":
    setup_tts()
