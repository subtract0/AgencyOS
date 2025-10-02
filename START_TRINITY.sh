#!/bin/bash
# Trinity Protocol - Quick Start
# Run this before sleep, wake up to ambient intelligence!

set -e

echo "🎤 TRINITY PROTOCOL - Starting Ambient Intelligence"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Whisper is available (skip for now - can install later)
if python -c "import whisper" 2>/dev/null; then
    echo "✅ Whisper AI ready"
    if [ ! -f "$HOME/.cache/whisper/base.en.pt" ]; then
        echo "📥 Downloading Whisper model (one-time, ~150MB)..."
        python -c "import whisper; whisper.load_model('base.en')"
    fi
else
    echo "⚠️  Whisper not installed (pip install openai-whisper)"
    echo "   Skipping for now - Trinity will run in demo mode"
fi

# Create log directory
mkdir -p logs/trinity_ambient

# Start ambient listener in background
echo "🎧 Starting ambient listener..."
nohup python trinity_protocol/ambient_listener_service.py \
    --model base.en \
    --min-confidence 0.6 \
    > logs/trinity_ambient/listener.log 2>&1 &
LISTENER_PID=$!
echo "   ✅ Listener PID: $LISTENER_PID"

# Start pattern dashboard in another terminal (optional)
echo "📊 Starting pattern dashboard..."
nohup python trinity_protocol/pattern_dashboard.py --live \
    > logs/trinity_ambient/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "   ✅ Dashboard PID: $DASHBOARD_PID"

# Save PIDs for later shutdown
echo "$LISTENER_PID" > /tmp/trinity_listener.pid
echo "$DASHBOARD_PID" > /tmp/trinity_dashboard.pid

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ TRINITY IS LIVE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 What to do:"
echo "   1. Talk about a project you want to build"
echo "   2. Wait ~30 seconds for pattern detection"
echo "   3. Trinity will ask if you want help (YES/NO)"
echo "   4. Answer 5-10 questions (one-time setup)"
echo "   5. Get 1-3 daily check-ins to move forward"
echo ""
echo "📊 View dashboard:"
echo "   tail -f logs/trinity_ambient/dashboard.log"
echo ""
echo "🛑 Stop Trinity:"
echo "   ./STOP_TRINITY.sh"
echo ""
echo "💤 Goodnight! Trinity will listen while you sleep..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
