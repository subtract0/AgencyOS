#!/bin/bash
# Start Autonomous Evolution System

cd "$(dirname "$0")"

echo "🚀 Starting AgencyOS Autonomous Evolution"
echo "==========================================="
echo ""
echo "System will:"
echo "  ✓ Scan codebase every 5 minutes"
echo "  ✓ Find improvement opportunities"
echo "  ✓ Learn patterns automatically"
echo "  ✓ Self-evolve when idle"
echo ""
echo "Logs: logs/autonomous_evolution.log"
echo "State: .evolution_state.json"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run with Poetry
/opt/homebrew/bin/poetry run python autonomous_evolution.py
