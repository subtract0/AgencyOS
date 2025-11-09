#!/bin/bash
#
# Start Pain Point Goldminer - 6-Hour Autonomous Collection
#
# This script launches the goldminer in background and monitors progress.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Check if already running
if pgrep -f "pain_point_goldminer.py" > /dev/null; then
    echo "⚠️  Goldminer already running!"
    echo "   PID: $(pgrep -f 'pain_point_goldminer.py')"
    echo ""
    echo "To stop: pkill -f pain_point_goldminer.py"
    echo "To monitor: tail -f logs/goldminer/*.log"
    exit 1
fi

# Set runtime (default: 6 hours)
HOURS=${1:-6}

echo "========================================"
echo "Pain Point Goldminer Launcher"
echo "========================================"
echo "Runtime: $HOURS hours"
echo "Started: $(date)"
echo "End time: $(date -v+${HOURS}H 2>/dev/null || date -d '+${HOURS} hours')"
echo ""

# Create log directory
mkdir -p logs/goldminer

# Launch in background
export PYTHONPATH="$PROJECT_ROOT"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/goldminer/goldminer_${HOURS}hr_${TIMESTAMP}.log"

nohup python tools/pain_point_goldminer.py --hours "$HOURS" > "$LOG_FILE" 2>&1 &
PID=$!

echo "✅ Goldminer started!"
echo ""
echo "PID: $PID"
echo "Log: $LOG_FILE"
echo ""
echo "📊 Monitor progress:"
echo "   tail -f $LOG_FILE"
echo ""
echo "🛑 Stop:"
echo "   kill $PID"
echo ""
echo "📁 Results will be in:"
echo "   logs/knowledge_ingest/exports/goldminer_*.json"
echo "   logs/goldminer/checkpoints/"
echo ""
echo "========================================"

# Show initial output
sleep 5
echo ""
echo "Initial output:"
echo "----------------------------------------"
tail -20 "$LOG_FILE"
echo "----------------------------------------"
echo ""
echo "Goldminer is running in background."
echo "Check logs for progress!"
