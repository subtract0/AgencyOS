#!/bin/bash
###############################################################################
# Monitor Dual Ollama Instances
#
# Real-time monitoring of two parallel Ollama servers.
#
# Usage:
#   bash scripts/monitor_dual_ollama.sh
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

while true; do
    clear
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}   DUAL OLLAMA MONITOR${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "\n$(date '+%Y-%m-%d %H:%M:%S')\n"

    # System Memory
    echo -e "${CYAN}System Memory:${NC}"
    vm_stat | awk '
        /Pages active/ {printf "  Active:  %.1f GB\n", $3*4096/1024/1024/1024}
        /Pages wired/ {printf "  Wired:   %.1f GB\n", $4*4096/1024/1024/1024}
        /Pages free/ {printf "  Free:    %.1f GB\n", $3*4096/1024/1024/1024}
    '

    # Ollama Processes
    echo -e "\n${CYAN}Ollama Processes:${NC}"
    ollama_pids=$(pgrep -f "ollama serve")
    if [ -z "$ollama_pids" ]; then
        echo -e "  ${RED}No Ollama instances running${NC}"
    else
        ps aux | grep "[o]llama serve" | awk '{
            printf "  PID %s: CPU %.1f%%, Memory %.1f GB\n", $2, $3, $6/1024/1024
        }'
    fi

    # Port Status
    echo -e "\n${CYAN}Port Status:${NC}"
    if lsof -i :11434 >/dev/null 2>&1; then
        pid=$(lsof -ti :11434)
        echo -e "  Port 11434: ${GREEN}LISTENING${NC} (PID: $pid)"

        # Test health
        if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
            models=$(curl -s http://127.0.0.1:11434/api/tags | jq -r '.models[].name' 2>/dev/null | tr '\n' ',' | sed 's/,$//')
            echo -e "    Health:  ${GREEN}OK${NC}"
            echo -e "    Models:  $models"
        else
            echo -e "    Health:  ${RED}ERROR${NC}"
        fi
    else
        echo -e "  Port 11434: ${RED}NOT LISTENING${NC}"
    fi

    if lsof -i :11435 >/dev/null 2>&1; then
        pid=$(lsof -ti :11435)
        echo -e "  Port 11435: ${GREEN}LISTENING${NC} (PID: $pid)"

        # Test health
        if curl -s http://127.0.0.1:11435/api/tags >/dev/null 2>&1; then
            models=$(curl -s http://127.0.0.1:11435/api/tags | jq -r '.models[].name' 2>/dev/null | tr '\n' ',' | sed 's/,$//')
            echo -e "    Health:  ${GREEN}OK${NC}"
            echo -e "    Models:  $models"
        else
            echo -e "    Health:  ${RED}ERROR${NC}"
        fi
    else
        echo -e "  Port 11435: ${RED}NOT LISTENING${NC}"
    fi

    # Logs (last 5 lines from each)
    echo -e "\n${CYAN}Recent Logs:${NC}"
    if [ -f "$HOME/.ollama-instance1.log" ]; then
        echo -e "  ${BLUE}Instance 1 (last 3 lines):${NC}"
        tail -3 "$HOME/.ollama-instance1.log" 2>/dev/null | sed 's/^/    /' || echo "    (no logs)"
    fi

    if [ -f "$HOME/.ollama-instance2.log" ]; then
        echo -e "  ${BLUE}Instance 2 (last 3 lines):${NC}"
        tail -3 "$HOME/.ollama-instance2.log" 2>/dev/null | sed 's/^/    /' || echo "    (no logs)"
    fi

    echo -e "\n${YELLOW}Press Ctrl+C to exit${NC}"
    sleep 2
done
