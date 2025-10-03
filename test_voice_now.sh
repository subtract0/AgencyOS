#!/bin/bash
# Voice Transcription Test Runner
# Tests the improvements with your voice and provides immediate feedback

echo "============================================================"
echo "🎤 VOICE TRANSCRIPTION TEST - Ready to Capture Your Voice"
echo "============================================================"
echo ""
echo "📋 IMPROVEMENTS ACTIVE:"
echo "  ✅ Whisper accuracy parameters (15-25% boost expected)"
echo "  ✅ RMS threshold tuned (0.015 - reduces empty results)"
echo "  ✅ Min text length validation (3 chars)"
echo "  ✅ Duration fallback (fixes validation errors)"
echo ""
echo "============================================================"
echo "📝 TEST INSTRUCTIONS"
echo "============================================================"
echo ""
echo "1. Press ENTER to start voice capture"
echo "2. Speak clearly these test phrases (one at a time):"
echo "   - 'Hello, this is a test of the voice transcription system'"
echo "   - 'The quick brown fox jumps over the lazy dog'"
echo "   - 'I want to test the ambient listener improvements'"
echo "   - 'Agency OS is helping me improve voice transcription'"
echo "   - 'This should have higher accuracy than before'"
echo ""
echo "3. Wait for each transcription to complete (~5-10 seconds)"
echo "4. Press Ctrl+C when done (after 5+ test phrases)"
echo ""
echo "============================================================"
echo ""
read -p "Press ENTER to start capturing... "

echo ""
echo "🎙️  STARTING VOICE CAPTURE..."
echo "💡 SPEAK CLEARLY AND LOUDLY for best results"
echo ""

# Run the voice capture script
python simple_voice_capture.py

echo ""
echo "============================================================"
echo "✅ VOICE CAPTURE COMPLETE"
echo "============================================================"
echo ""
echo "📄 Reviewing results..."
echo ""

# Check if transcription file exists
if [ -f "logs/trinity_ambient/voice_transcriptions.txt" ]; then
    echo "Recent transcriptions:"
    echo "----------------------------------------"
    tail -20 logs/trinity_ambient/voice_transcriptions.txt
    echo "----------------------------------------"
    echo ""

    # Count transcriptions
    TOTAL=$(wc -l < logs/trinity_ambient/voice_transcriptions.txt | tr -d ' ')
    EMPTY=$(grep -c "RMS:[0-9.]* Conf:0.00 | $" logs/trinity_ambient/voice_transcriptions.txt 2>/dev/null || echo 0)
    NON_EMPTY=$((TOTAL - EMPTY))

    if [ $TOTAL -gt 0 ]; then
        EMPTY_RATE=$((EMPTY * 100 / TOTAL))
        SUCCESS_RATE=$((NON_EMPTY * 100 / TOTAL))

        echo "📊 QUICK STATS:"
        echo "  Total transcriptions: $TOTAL"
        echo "  Non-empty results: $NON_EMPTY"
        echo "  Empty results: $EMPTY"
        echo "  Success rate: $SUCCESS_RATE%"
        echo "  Empty rate: $EMPTY_RATE%"
        echo ""

        if [ $EMPTY_RATE -lt 30 ]; then
            echo "✅ SUCCESS: Empty rate ($EMPTY_RATE%) is below target (30%)"
            echo "   Improvement #2 is WORKING! 🎉"
        else
            echo "⚠️  NOTICE: Empty rate ($EMPTY_RATE%) still above target (30%)"
            echo "   May need further RMS threshold tuning"
        fi
    fi
    echo ""
    echo "Full log: logs/trinity_ambient/voice_transcriptions.txt"
else
    echo "⚠️  No transcription file found at:"
    echo "   logs/trinity_ambient/voice_transcriptions.txt"
fi

echo ""
echo "============================================================"
echo "NEXT: Provide feedback to Claude about the results"
echo "============================================================"
