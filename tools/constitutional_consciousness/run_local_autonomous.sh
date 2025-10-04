#!/bin/bash
# Constitutional Consciousness - Local-Only Autonomous Night Run
# Runs on MacBook Pro M4 with Ollama models (no API calls)

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Constitutional Consciousness${NC}"
echo -e "${BLUE}Local-Only Autonomous Night Run${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama not running${NC}"
    echo -e "${YELLOW}Starting Ollama...${NC}"
    ollama serve &
    sleep 5
fi

# Verify models are available
echo -e "${BLUE}Checking models...${NC}"
MODELS=$(ollama list 2>/dev/null || echo "")

if ! echo "$MODELS" | grep -q "codestral.*22b"; then
    echo -e "${RED}❌ Codestral-22B not found${NC}"
    echo -e "${YELLOW}Pull with: ollama pull codestral:22b-v0.1-q4_K_M${NC}"
    exit 1
fi

if ! echo "$MODELS" | grep -q "qwen2.5-coder.*7b"; then
    echo -e "${RED}❌ Qwen2.5-Coder-7B not found${NC}"
    echo -e "${YELLOW}Pull with: ollama pull qwen2.5-coder:7b-instruct-q4_K_M${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Models ready${NC}\n"

# Set local-only environment
export AGENCY_MODE=local_only
export ENABLE_GPT5_ESCALATION=false
export USE_OPENAI_FALLBACK=false
export ENABLE_CONSCIOUSNESS=true

# Configure models
export PLANNER_MODEL=codestral:22b-v0.1-q4_K_M
export CODER_MODEL=qwen2.5-coder:7b-instruct-q4_K_M
export SCANNER_MODEL=qwen2.5-coder:1.5b-instruct-q4_K_M

# Ensure sentence-transformers for local embeddings
if ! python -c "import sentence_transformers" 2>/dev/null; then
    echo -e "${YELLOW}Installing sentence-transformers...${NC}"
    pip install sentence-transformers
fi

# Create log directory
mkdir -p logs/consciousness_night_runs

# Determine run mode
MODE="${1:-single}"
DAYS="${2:-7}"

if [ "$MODE" == "continuous" ]; then
    echo -e "${BLUE}🌙 Starting continuous autonomous run...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"

    CYCLE=1
    while true; do
        echo -e "${BLUE}[Cycle $CYCLE] $(date '+%Y-%m-%d %H:%M:%S')${NC}"

        # Run Constitutional Consciousness
        python -m tools.constitutional_consciousness.feedback_loop \
            --days "$DAYS" \
            --json > "logs/consciousness_night_runs/cycle_$(date +%Y%m%d_%H%M%S).json" 2>&1

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Cycle $CYCLE complete${NC}\n"
        else
            echo -e "${RED}❌ Cycle $CYCLE failed${NC}\n"
        fi

        ((CYCLE++))
        sleep 3600  # 1 hour
    done
else
    echo -e "${BLUE}🌙 Running single autonomous cycle...${NC}\n"

    # Run Constitutional Consciousness
    python -m tools.constitutional_consciousness.feedback_loop \
        --days "$DAYS"

    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}✅ Cycle complete${NC}"
        echo -e "${BLUE}Results saved to:${NC}"
        echo -e "  - Terminal output above"
        echo -e "  - VectorStore (Agency memory)"
        echo -e "  - docs/constitutional_consciousness/cycle-$(date +%Y-%m-%d).md"
    else
        echo -e "\n${RED}❌ Cycle failed${NC}"
        exit 1
    fi
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Constitutional Consciousness Complete${NC}"
echo -e "${BLUE}========================================${NC}"
