#!/bin/bash
# Smart Filter Runner - Loads environment and runs with proper settings

# Load .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded environment from .env"
else
    echo "⚠️  No .env file found - will use local transcription only"
fi

echo ""
echo "🎤 Starting Smart Voice Filter..."
echo "   RMS Threshold: 200 (stricter)"
echo "   VAD Threshold: 0.85 (stricter)"
echo "   Speaker Threshold: 0.80 (stricter)"
echo ""

# Run the smart filter
python voice_smart_filter.py

echo ""
echo "✅ Smart filter stopped"
