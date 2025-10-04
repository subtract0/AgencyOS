#!/bin/bash
#
# Monitor Trinity Local M4 - Real-time status
#

set -euo pipefail

TRINITY_DIR="${HOME}/.trinity-local"
PID_FILE="${TRINITY_DIR}/trinity.pid"
LOG_FILE="${TRINITY_DIR}/logs/trinity_local/trinity.log"

clear

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Trinity Local M4 - Status Monitor                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running
if [[ -f "$PID_FILE" ]] && ps -p "$(cat "$PID_FILE")" > /dev/null 2>&1; then
    pid=$(cat "$PID_FILE")
    echo "✅ Status: RUNNING (PID: $pid)"

    # Memory usage
    mem_mb=$(ps -p "$pid" -o rss= | awk '{print int($1/1024)}')
    echo "   Memory: ${mem_mb}MB"

    # Uptime
    start_time=$(ps -p "$pid" -o lstart= | xargs -I {} date -j -f "%a %b %d %T %Y" "{}" "+%s" 2>/dev/null || echo "0")
    now=$(date +%s)
    uptime_sec=$((now - start_time))
    uptime_min=$((uptime_sec / 60))
    echo "   Uptime: ${uptime_min} minutes"
else
    echo "❌ Status: STOPPED"
fi

echo ""
echo "────────────────────────────────────────────────────────────────"
echo "Ollama Models:"
ollama list | head -5

echo ""
echo "────────────────────────────────────────────────────────────────"
echo "Recent Activity (last 10 lines):"
if [[ -f "$LOG_FILE" ]]; then
    tail -10 "$LOG_FILE"
else
    echo "  (no logs yet)"
fi

echo ""
echo "────────────────────────────────────────────────────────────────"
echo "Controls:"
echo "  Start:  ./start_trinity.sh"
echo "  Stop:   ./stop_trinity.sh"
echo "  Logs:   tail -f logs/trinity_local/trinity.log"
