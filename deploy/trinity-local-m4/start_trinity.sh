#!/bin/bash
#
# Start Trinity Local M4 - Launch 3-LLM autonomous loop
#

set -euo pipefail

TRINITY_DIR="${HOME}/.trinity-local"
VENV_DIR="${TRINITY_DIR}/.venv"
PID_FILE="${TRINITY_DIR}/trinity.pid"

cd "$TRINITY_DIR"
source "$VENV_DIR/bin/activate"

# Check if already running
if [[ -f "$PID_FILE" ]] && ps -p "$(cat "$PID_FILE")" > /dev/null 2>&1; then
    echo "❌ Trinity already running (PID: $(cat "$PID_FILE"))"
    echo "Run ./stop_trinity.sh first"
    exit 1
fi

# Ensure Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "🚀 Starting Ollama service..."
    ollama serve &> /dev/null &
    sleep 3
fi

echo "🚀 Starting Trinity Local M4..."
echo ""
echo "  WITNESS:    qwen2.5-coder:1.5b (pattern detection)"
echo "  ARCHITECT:  qwen2.5-coder:7b   (strategic planning)"
echo "  EXECUTOR:   codestral:22b      (code execution)"
echo ""

# Start Trinity orchestrator in background
nohup python3 -m trinity_protocol.core.orchestrator \
    --config trinity_config.yaml \
    >> logs/trinity_local/trinity.log 2>&1 &

echo $! > "$PID_FILE"

echo "✅ Trinity started (PID: $(cat "$PID_FILE"))"
echo ""
echo "Monitor: ./monitor_trinity.sh"
echo "Stop:    ./stop_trinity.sh"
echo "Logs:    tail -f logs/trinity_local/trinity.log"
