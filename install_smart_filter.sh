#!/bin/bash
# Install dependencies for Smart Voice Filtering

echo "🔧 Installing Smart Voice Filter Dependencies..."
echo ""

# Install torchaudio
echo "📦 Installing torchaudio..."
pip install torchaudio --quiet

# Install librosa (for speaker identification)
echo "📦 Installing librosa..."
pip install librosa --quiet

# Already have: pyaudio, numpy, torch, openai

echo ""
echo "✅ Installation complete!"
echo ""
echo "Run the smart filter with:"
echo "  python voice_smart_filter.py"
