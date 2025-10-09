#!/bin/bash
# Quick start script for MacBook Air agents

echo "🚀 Starting MacBook Air Autonomous Agents"
echo "=========================================="
echo ""
echo "Opening 2 terminal windows..."
echo ""

# Terminal 1
osascript -e 'tell application "Terminal"
    do script "cd ~/Code/Agency && source .venv/bin/activate && export PYTHONPATH=\"$PWD:\$PYTHONPATH\" && python scripts/autonomous_worker.py --agent-id mba-agent1"
    set custom title of front window to "MBA Agent 1"
end tell'

sleep 1

# Terminal 2
osascript -e 'tell application "Terminal"
    do script "cd ~/Code/Agency && source .venv/bin/activate && export PYTHONPATH=\"$PWD:\$PYTHONPATH\" && python scripts/autonomous_worker.py --agent-id mba-agent2"
    set custom title of front window to "MBA Agent 2"
end tell'

echo "✅ Agents started in separate terminal windows"
echo ""
echo "Monitor progress (in a new terminal):"
echo "  cd ~/Code/Agency"
echo "  source .venv/bin/activate"
echo "  export PYTHONPATH=\"\$PWD:\$PYTHONPATH\""
echo "  watch -n 5 'python meta_learning/task_queue.py status'"
