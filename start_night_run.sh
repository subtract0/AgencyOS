#!/bin/bash
# Start Constitutional Consciousness Night Run
# Simple wrapper for beginners

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

clear
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     Constitutional Consciousness                         ║"
echo "║     Night Run Starting...                                ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Check if setup was run
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}⚠ Setup not complete. Please run: bash setup_consciousness.sh${NC}"
    exit 1
fi

# Load config
source .env.local

# Activate Python environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠ Virtual environment not found. Run setup_consciousness.sh first${NC}"
    exit 1
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting Ollama...${NC}"
    ollama serve > /dev/null 2>&1 &
    sleep 5
fi

echo -e "${GREEN}✓ Ollama ready${NC}"
echo -e "${GREEN}✓ Python environment active${NC}\n"

# Create log file
LOG_FILE="logs/night_run_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}Night Run Configuration:${NC}"
echo "  • Mode: Local-only (no API calls)"
echo "  • Frequency: Every hour"
echo "  • Models: Codestral-22B + Qwen2.5-Coder-7B + Qwen2.5-Coder-1.5B"
echo "  • Reports: reports/"
echo "  • Logs: $LOG_FILE"
echo ""

echo -e "${YELLOW}Starting continuous operation...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop, or run: bash stop_night_run.sh${NC}\n"

# Save PID for stop script
echo $$ > .night_run.pid

# Run loop
CYCLE=1
while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[Cycle $CYCLE] $TIMESTAMP${NC}" | tee -a "$LOG_FILE"

    # Run Constitutional Consciousness
    python -m tools.constitutional_consciousness.feedback_loop \
        --days 7 \
        > "reports/cycle_${CYCLE}.txt" 2>&1

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Cycle $CYCLE complete${NC}" | tee -a "$LOG_FILE"

        # Update latest report
        cp "reports/cycle_${CYCLE}.txt" reports/latest.txt

        # Extract key metrics
        echo -e "\n${BOLD}Quick Summary:${NC}"
        grep -E "Violations Analyzed|Patterns Detected|Predictions|Evolution" "reports/cycle_${CYCLE}.txt" | head -5
        echo ""
    else
        echo -e "${RED}✗ Cycle $CYCLE failed${NC}" | tee -a "$LOG_FILE"
    fi

    ((CYCLE++))

    echo -e "${YELLOW}Next cycle in 1 hour...${NC}\n"
    sleep 3600
done
