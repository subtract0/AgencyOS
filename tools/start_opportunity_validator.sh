#!/bin/bash
#
# Start Opportunity Validator - Autonomous Search for Proven Solutions
#
# Searches internet for historical problems with proven, profitable,
# fully digital solutions.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Check if already running
if pgrep -f "opportunity_validator.py" > /dev/null; then
    echo "⚠️  Validator already running!"
    echo "   PID: $(pgrep -f 'opportunity_validator.py')"
    echo ""
    echo "To stop: pkill -f opportunity_validator.py"
    echo "To monitor: tail -f logs/opportunity_validator/*.log"
    exit 1
fi

# Set runtime (default: 6 hours)
HOURS=${1:-6}

echo "========================================"
echo "Opportunity Validator Launcher"
echo "========================================"
echo "Runtime: $HOURS hours"
echo "Started: $(date)"
echo ""

# Create log directory
mkdir -p logs/opportunity_validator

# Launch in background
export PYTHONPATH="$PROJECT_ROOT"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/opportunity_validator/validator_${HOURS}hr_${TIMESTAMP}.log"

nohup python tools/opportunity_validator.py --hours "$HOURS" > "$LOG_FILE" 2>&1 &
PID=$!

echo "✅ Validator started!"
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
echo "   logs/opportunity_validator/exports/"
echo "   logs/opportunity_validator/checkpoints/"
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
echo "Validator is running in background."
echo "Check logs for progress!"
