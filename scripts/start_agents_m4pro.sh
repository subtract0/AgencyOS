#!/bin/bash
# Quick start script for M4 Pro agents
# Opens 2 terminal windows with autonomous agents

echo "🚀 Starting M4 Pro Autonomous Agents"
echo "===================================="
echo ""
echo "Opening 2 terminal windows..."
echo ""

# Terminal 1
osascript -e 'tell application "Terminal"
    do script "cd ~/Code/Agency && python scripts/autonomous_worker.py --agent-id m4pro-agent1"
    set custom title of front window to "M4 Pro Agent 1"
end tell'

sleep 1

# Terminal 2
osascript -e 'tell application "Terminal"
    do script "cd ~/Code/Agency && python scripts/autonomous_worker.py --agent-id m4pro-agent2"
    set custom title of front window to "M4 Pro Agent 2"
end tell'

echo "✅ Agents started in separate terminal windows"
echo ""
echo "Monitor progress:"
echo "  watch -n 5 'python meta_learning/task_queue.py status'"
