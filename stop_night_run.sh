#!/bin/bash
# Stop Constitutional Consciousness Night Run

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Stopping Constitutional Consciousness Night Run...${NC}\n"

if [ -f ".night_run.pid" ]; then
    PID=$(cat .night_run.pid)

    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        rm .night_run.pid
        echo -e "${GREEN}✓ Night run stopped (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Process not running (PID: $PID)${NC}"
        rm .night_run.pid
    fi
else
    echo -e "${YELLOW}⚠ No night run PID file found${NC}"
    echo -e "${YELLOW}Checking for running processes...${NC}\n"

    PROCS=$(ps aux | grep "constitutional_consciousness" | grep -v grep | awk '{print $2}')
    if [ -n "$PROCS" ]; then
        echo "$PROCS" | while read pid; do
            kill $pid
            echo -e "${GREEN}✓ Stopped process $pid${NC}"
        done
    else
        echo -e "${YELLOW}No Constitutional Consciousness processes found${NC}"
    fi
fi

echo -e "\n${BLUE}Latest results:${NC}"
if [ -f "reports/latest.txt" ]; then
    tail -20 reports/latest.txt
else
    echo -e "${YELLOW}No reports found${NC}"
fi
