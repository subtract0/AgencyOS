#!/bin/bash
# Trinity Protocol - Shutdown Script

echo "🛑 Stopping Trinity Protocol..."

if [ -f /tmp/trinity_listener.pid ]; then
    LISTENER_PID=$(cat /tmp/trinity_listener.pid)
    kill $LISTENER_PID 2>/dev/null && echo "   ✅ Stopped listener (PID: $LISTENER_PID)"
    rm /tmp/trinity_listener.pid
fi

if [ -f /tmp/trinity_dashboard.pid ]; then
    DASHBOARD_PID=$(cat /tmp/trinity_dashboard.pid)
    kill $DASHBOARD_PID 2>/dev/null && echo "   ✅ Stopped dashboard (PID: $DASHBOARD_PID)"
    rm /tmp/trinity_dashboard.pid
fi

echo ""
echo "✅ Trinity stopped. Sleep well! 💤"
