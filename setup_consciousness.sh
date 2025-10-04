#!/bin/bash
# Constitutional Consciousness - Automatic Setup Script
# For MacBook Pro M4 (48GB RAM)
# User-friendly, zero configuration required

set -e  # Exit on any error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     Constitutional Consciousness v1.0.0                  ║"
echo "║     Automatic Setup for MacBook Pro                      ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo -e "${YELLOW}This will install:${NC}"
echo "  ✓ Ollama (AI model engine)"
echo "  ✓ 3 AI models (~20GB total)"
echo "  ✓ Python dependencies"
echo "  ✓ Constitutional Consciousness system"
echo ""
echo -e "${YELLOW}Time required: ~15 minutes${NC}"
echo -e "${YELLOW}Disk space needed: ~25GB${NC}\n"

# Check disk space
echo -e "${BLUE}[1/6] Checking disk space...${NC}"
AVAILABLE=$(df -g ~ | awk 'NR==2 {print $4}')
if [ "$AVAILABLE" -lt 25 ]; then
    echo -e "${RED}❌ Not enough disk space. Need 25GB, have ${AVAILABLE}GB${NC}"
    echo -e "${YELLOW}Free up some space and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Disk space OK (${AVAILABLE}GB available)${NC}\n"

# Install Ollama
echo -e "${BLUE}[2/6] Installing Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    echo -e "${GREEN}✓ Ollama installed${NC}\n"
else
    echo -e "${GREEN}✓ Ollama already installed${NC}\n"
fi

# Start Ollama service
echo -e "${BLUE}[3/6] Starting Ollama service...${NC}"
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi
echo -e "${GREEN}✓ Ollama running${NC}\n"

# Download models
echo -e "${BLUE}[4/6] Downloading AI models...${NC}"
echo -e "${YELLOW}This will take 10-15 minutes. Please be patient...${NC}\n"

if ! ollama list | grep -q "codestral.*22b"; then
    echo -e "  Downloading Codestral-22B (Architect)..."
    ollama pull codestral:22b-v0.1-q4_K_M || {
        echo -e "${YELLOW}  Trying alternative: codestral:latest${NC}"
        ollama pull codestral:latest
    }
fi

if ! ollama list | grep -q "qwen2.5-coder.*7b"; then
    echo -e "  Downloading Qwen2.5-Coder-7B (Builder)..."
    ollama pull qwen2.5-coder:7b-instruct-q4_K_M || {
        echo -e "${YELLOW}  Trying alternative: qwen2.5-coder:7b${NC}"
        ollama pull qwen2.5-coder:7b
    }
fi

if ! ollama list | grep -q "qwen2.5-coder.*1.5b"; then
    echo -e "  Downloading Qwen2.5-Coder-1.5B (Controller)..."
    ollama pull qwen2.5-coder:1.5b-instruct-q4_K_M || {
        echo -e "${YELLOW}  Trying alternative: qwen2.5-coder:1.5b${NC}"
        ollama pull qwen2.5-coder:1.5b
    }
fi

echo -e "${GREEN}✓ All models downloaded${NC}\n"

# Install Python dependencies
echo -e "${BLUE}[5/6] Installing Python dependencies...${NC}"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.10+ first.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate venv and install
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q sentence-transformers pydantic litellm

echo -e "${GREEN}✓ Python dependencies installed${NC}\n"

# Create configuration
echo -e "${BLUE}[6/6] Configuring Constitutional Consciousness...${NC}"

cat > .env.local <<EOF
# Constitutional Consciousness - Local-Only Configuration
AGENCY_MODE=local_only
ENABLE_GPT5_ESCALATION=false
USE_OPENAI_FALLBACK=false

# Ollama Models (Hybrid Trinity Architecture)
PLANNER_MODEL=codestral:22b-v0.1-q4_K_M
CODER_MODEL=qwen2.5-coder:7b-instruct-q4_K_M
SCANNER_MODEL=qwen2.5-coder:1.5b-instruct-q4_K_M

# Local Embeddings (No API)
EMBEDDING_PROVIDER=sentence-transformers

# Constitutional Consciousness
ENABLE_CONSCIOUSNESS=true
AUTONOMOUS_NIGHT_RUN=true
EOF

# Create reports directory
mkdir -p reports
mkdir -p logs/consciousness_night_runs

echo -e "${GREEN}✓ Configuration complete${NC}\n"

# Quick test
echo -e "${BLUE}Testing setup...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    MODELS=$(ollama list 2>/dev/null | wc -l)
    if [ "$MODELS" -gt 3 ]; then
        echo -e "${GREEN}✓ Setup test passed${NC}\n"
    else
        echo -e "${YELLOW}⚠ Models may still be downloading. Check with: ollama list${NC}\n"
    fi
else
    echo -e "${RED}❌ Ollama not responding. Try: ollama serve${NC}\n"
    exit 1
fi

# Success summary
echo -e "${GREEN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     ✓ Setup Complete!                                    ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo -e "${BOLD}Next Steps:${NC}"
echo -e "  1. Start night run: ${BLUE}bash start_night_run.sh${NC}"
echo -e "  2. Check status:     ${BLUE}cat reports/latest.txt${NC}"
echo -e "  3. Stop anytime:     ${BLUE}bash stop_night_run.sh${NC}\n"

echo -e "${YELLOW}Models installed:${NC}"
ollama list | head -5

echo -e "\n${GREEN}Ready for autonomous operation! 🚀${NC}\n"
