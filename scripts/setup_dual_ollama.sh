#!/bin/bash
###############################################################################
# Dual Ollama Server Setup
#
# Sets up two parallel Ollama instances for A/B testing and task routing.
#
# Instance 1 (Port 11434): Base model (general tasks)
# Instance 2 (Port 11435): Adapted model (algorithm tasks)
#
# Usage:
#   bash scripts/setup_dual_ollama.sh start
#   bash scripts/setup_dual_ollama.sh stop
#   bash scripts/setup_dual_ollama.sh status
#   bash scripts/setup_dual_ollama.sh restart
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
INSTANCE1_DIR="$HOME/.ollama"
INSTANCE2_DIR="$HOME/.ollama-instance2"
PID_DIR="$HOME/.ollama-pids"

mkdir -p "$PID_DIR"

# Functions
start_instance1() {
    echo -e "${BLUE}Starting Ollama Instance 1 (Base Model, Port 11434)...${NC}"

    if lsof -i :11434 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port 11434 already in use${NC}"
        return
    fi

    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_MODELS="$INSTANCE1_DIR" \
    OLLAMA_NUM_PARALLEL=1 \
    OLLAMA_MAX_LOADED_MODELS=1 \
    ollama serve > "$HOME/.ollama-instance1.log" 2>&1 &

    echo $! > "$PID_DIR/ollama-instance1.pid"

    # Wait for startup
    sleep 2

    if lsof -i :11434 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Instance 1 started on port 11434${NC}"
        echo -e "${BLUE}   Model directory: $INSTANCE1_DIR${NC}"
        echo -e "${BLUE}   Log: $HOME/.ollama-instance1.log${NC}"
    else
        echo -e "${RED}❌ Instance 1 failed to start${NC}"
        cat "$HOME/.ollama-instance1.log"
    fi
}

start_instance2() {
    echo -e "${BLUE}Starting Ollama Instance 2 (Adapted Model, Port 11435)...${NC}"

    if lsof -i :11435 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port 11435 already in use${NC}"
        return
    fi

    mkdir -p "$INSTANCE2_DIR"

    OLLAMA_HOST=127.0.0.1:11435 \
    OLLAMA_MODELS="$INSTANCE2_DIR" \
    OLLAMA_NUM_PARALLEL=1 \
    OLLAMA_MAX_LOADED_MODELS=1 \
    ollama serve > "$HOME/.ollama-instance2.log" 2>&1 &

    echo $! > "$PID_DIR/ollama-instance2.pid"

    # Wait for startup
    sleep 2

    if lsof -i :11435 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Instance 2 started on port 11435${NC}"
        echo -e "${BLUE}   Model directory: $INSTANCE2_DIR${NC}"
        echo -e "${BLUE}   Log: $HOME/.ollama-instance2.log${NC}"
    else
        echo -e "${RED}❌ Instance 2 failed to start${NC}"
        cat "$HOME/.ollama-instance2.log"
    fi
}

stop_instance() {
    local instance=$1
    local pid_file="$PID_DIR/ollama-instance${instance}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping Instance ${instance} (PID $pid)...${NC}"
            kill $pid
            rm "$pid_file"
            echo -e "${GREEN}✅ Instance ${instance} stopped${NC}"
        else
            echo -e "${YELLOW}Instance ${instance} not running (stale PID)${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}No PID file for Instance ${instance}${NC}"
    fi
}

show_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}   DUAL OLLAMA STATUS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════${NC}"

    # Instance 1
    echo -e "\n${GREEN}Instance 1 (Base Model, Port 11434):${NC}"
    if lsof -i :11434 >/dev/null 2>&1; then
        local pid=$(lsof -ti :11434)
        local mem=$(ps -o rss= -p $pid 2>/dev/null | awk '{print $1/1024/1024}')
        echo -e "  Status: ${GREEN}RUNNING${NC}"
        echo -e "  PID: $pid"
        echo -e "  Memory: ${mem} GB"
        echo -e "  Endpoint: http://127.0.0.1:11434"

        # Test connection
        if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
            echo -e "  Health: ${GREEN}OK${NC}"
            local models=$(curl -s http://127.0.0.1:11434/api/tags | jq -r '.models[].name' 2>/dev/null | wc -l)
            echo -e "  Models: $models loaded"
        else
            echo -e "  Health: ${RED}ERROR${NC}"
        fi
    else
        echo -e "  Status: ${RED}NOT RUNNING${NC}"
    fi

    # Instance 2
    echo -e "\n${GREEN}Instance 2 (Adapted Model, Port 11435):${NC}"
    if lsof -i :11435 >/dev/null 2>&1; then
        local pid=$(lsof -ti :11435)
        local mem=$(ps -o rss= -p $pid 2>/dev/null | awk '{print $1/1024/1024}')
        echo -e "  Status: ${GREEN}RUNNING${NC}"
        echo -e "  PID: $pid"
        echo -e "  Memory: ${mem} GB"
        echo -e "  Endpoint: http://127.0.0.1:11435"

        # Test connection
        if curl -s http://127.0.0.1:11435/api/tags >/dev/null 2>&1; then
            echo -e "  Health: ${GREEN}OK${NC}"
            local models=$(curl -s http://127.0.0.1:11435/api/tags | jq -r '.models[].name' 2>/dev/null | wc -l)
            echo -e "  Models: $models loaded"
        else
            echo -e "  Health: ${RED}ERROR${NC}"
        fi
    else
        echo -e "  Status: ${RED}NOT RUNNING${NC}"
    fi

    # System resources
    echo -e "\n${BLUE}System Resources:${NC}"
    vm_stat | awk '
        /Pages active/ {printf "  Active Memory: %.1f GB\n", $3*4096/1024/1024/1024}
        /Pages free/ {printf "  Free Memory:   %.1f GB\n", $3*4096/1024/1024/1024}
    '

    echo ""
}

pull_models() {
    echo -e "${BLUE}Pulling models for both instances...${NC}"

    # Instance 1: Base model
    echo -e "\n${GREEN}Instance 1: Pulling gpt-oss:20b${NC}"
    OLLAMA_HOST=127.0.0.1:11434 ollama pull gpt-oss:20b

    # Instance 2: Check if adapted model exists, otherwise use base
    echo -e "\n${GREEN}Instance 2: Checking for esper31-algorithms:20b${NC}"
    if OLLAMA_HOST=127.0.0.1:11435 ollama list | grep -q "esper31-algorithms"; then
        echo -e "${GREEN}✅ Adapted model already present${NC}"
    else
        echo -e "${YELLOW}⚠️  Adapted model not found, pulling base model${NC}"
        echo -e "${YELLOW}   (Run training to create adapted model)${NC}"
        OLLAMA_HOST=127.0.0.1:11435 ollama pull gpt-oss:20b
    fi
}

# Main
case "$1" in
    start)
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}   STARTING DUAL OLLAMA SERVERS${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════${NC}"
        start_instance1
        start_instance2
        echo ""
        sleep 2
        show_status
        ;;

    stop)
        echo -e "${BLUE}Stopping all Ollama instances...${NC}"
        stop_instance 1
        stop_instance 2
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start
        ;;

    status)
        show_status
        ;;

    pull)
        pull_models
        ;;

    test)
        echo -e "${BLUE}Testing both instances...${NC}\n"

        PROMPT="What is 2+2?"

        echo -e "${GREEN}Instance 1 (Port 11434):${NC}"
        curl -s http://127.0.0.1:11434/api/generate -d "{
            \"model\": \"gpt-oss:20b\",
            \"prompt\": \"$PROMPT\",
            \"stream\": false
        }" | jq -r '.response' || echo "ERROR"

        echo -e "\n${GREEN}Instance 2 (Port 11435):${NC}"
        curl -s http://127.0.0.1:11435/api/generate -d "{
            \"model\": \"gpt-oss:20b\",
            \"prompt\": \"$PROMPT\",
            \"stream\": false
        }" | jq -r '.response' || echo "ERROR"
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|pull|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start both Ollama instances"
        echo "  stop     - Stop both instances"
        echo "  restart  - Restart both instances"
        echo "  status   - Show status and health"
        echo "  pull     - Pull models for both instances"
        echo "  test     - Quick test of both instances"
        exit 1
        ;;
esac
