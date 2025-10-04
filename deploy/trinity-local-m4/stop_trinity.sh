#!/bin/bash
#
# Stop Trinity Local M4 - Graceful shutdown
#

set -euo pipefail

TRINITY_DIR="${HOME}/.trinity-local"
PID_FILE="${TRINITY_DIR}/trinity.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "❌ Trinity not running (no PID file)"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "❌ Trinity not running (stale PID file)"
    rm "$PID_FILE"
    exit 1
fi

echo "🛑 Stopping Trinity (PID: $PID)..."

# Graceful shutdown (SIGTERM)
kill -TERM "$PID"

# Wait up to 30 seconds
timeout=30
elapsed=0
while ps -p "$PID" > /dev/null 2>&1; do
    if [[ $elapsed -ge $timeout ]]; then
        echo "⚠️  Graceful shutdown timed out, forcing..."
        kill -KILL "$PID"
        break
    fi
    sleep 1
    ((elapsed++))
done

rm "$PID_FILE"
echo "✅ Trinity stopped"
