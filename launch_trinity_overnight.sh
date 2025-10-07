#!/bin/bash
#
# Trinity Overnight Daemon Launcher
#
# Launches the autonomous 3-agent system for overnight development:
# - AUDITOR: Continuous codebase scanning (every 30 min)
# - FIXER: Autonomous recommendation application (continuous)
# - LEARNER: Pattern extraction and learning (every 60 min)
#
# Usage:
#   ./launch_trinity_overnight.sh [MAX_HOURS]
#
# Examples:
#   ./launch_trinity_overnight.sh          # Run for 8 hours (default)
#   ./launch_trinity_overnight.sh 12       # Run for 12 hours
#

set -e

# Configuration
MAX_RUNTIME_HOURS=${1:-8}
OUTPUT_DIR=".output/trinity"
LOG_FILE="${OUTPUT_DIR}/overnight.log"
PID_FILE="${OUTPUT_DIR}/trinity.pid"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        🌙 TRINITY OVERNIGHT DAEMON LAUNCHER 🌙           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Check if already running
if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}")
    if ps -p "${OLD_PID}" > /dev/null 2>&1; then
        echo -e "${RED}✗ Trinity Daemon already running (PID: ${OLD_PID})${NC}"
        echo -e "${YELLOW}  Stop it first: kill ${OLD_PID}${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠ Stale PID file found, removing...${NC}"
        rm "${PID_FILE}"
    fi
fi

# Check for qwen2.5-coder models
echo -e "${BLUE}Checking Ollama models...${NC}"
if ! ollama list | grep -q "qwen2.5-coder:32b"; then
    echo -e "${RED}✗ qwen2.5-coder:32b not found${NC}"
    echo -e "${YELLOW}  Pull it first: ollama pull qwen2.5-coder:32b${NC}"
    exit 1
fi
echo -e "${GREEN}✓ qwen2.5-coder:32b ready${NC}"

if ! ollama list | grep -q "qwen2.5-coder:7b"; then
    echo -e "${YELLOW}⚠ qwen2.5-coder:7b not found, using 32b for all agents${NC}"
fi

# Check for audit recommendations
RECS_DIR=".output/audit_recommendations"
if [ ! -d "${RECS_DIR}" ] || [ -z "$(ls -A ${RECS_DIR} 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠ No audit recommendations found in ${RECS_DIR}${NC}"
    echo -e "${BLUE}  Running initial audit...${NC}"
    python scripts/continuous_audit_m4pro.py --mode once --config continuous_audit_config.yaml
    echo -e "${GREEN}✓ Initial audit complete${NC}"
fi

# Display configuration
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Runtime:           ${GREEN}${MAX_RUNTIME_HOURS} hours${NC}"
echo -e "  Audit interval:    ${GREEN}30 minutes${NC}"
echo -e "  Learning interval: ${GREEN}60 minutes${NC}"
echo -e "  Output directory:  ${GREEN}${OUTPUT_DIR}${NC}"
echo -e "  Log file:          ${GREEN}${LOG_FILE}${NC}"
echo ""

# Confirm launch
echo -e "${YELLOW}Press CTRL+C to cancel, or wait 5 seconds to launch...${NC}"
sleep 5

# Launch Trinity daemon
echo ""
echo -e "${GREEN}🚀 Launching Trinity Daemon...${NC}"
nohup python scripts/trinity_daemon.py \
    --max-runtime-hours "${MAX_RUNTIME_HOURS}" \
    --recommendations-dir .output/audit_recommendations \
    --output-dir "${OUTPUT_DIR}" \
    --auto-commit \
    --audit-interval-minutes 30 \
    --learning-interval-minutes 60 \
    > "${LOG_FILE}" 2>&1 &

PID=$!
echo "${PID}" > "${PID_FILE}"

# Verify launch
sleep 2
if ps -p "${PID}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Trinity Daemon launched successfully (PID: ${PID})${NC}"
else
    echo -e "${RED}✗ Trinity Daemon failed to start${NC}"
    echo -e "${YELLOW}  Check log: tail -50 ${LOG_FILE}${NC}"
    exit 1
fi

# Display monitoring info
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    MONITORING COMMANDS                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Watch live progress:${NC}"
echo -e "  tail -f ${LOG_FILE} | grep -E '(AUDITOR|FIXER|LEARNER|Status)'"
echo ""
echo -e "${GREEN}Check statistics:${NC}"
echo -e "  cat ${OUTPUT_DIR}/trinity_state.json | jq"
echo ""
echo -e "${GREEN}View success patterns:${NC}"
echo -e "  cat ${OUTPUT_DIR}/shared_memory.json | jq '.success_patterns | length'"
echo ""
echo -e "${GREEN}Stop daemon:${NC}"
echo -e "  kill ${PID}"
echo -e "  # OR"
echo -e "  kill \$(cat ${PID_FILE})"
echo ""
echo -e "${BLUE}Expected overnight results:${NC}"
echo -e "  - 60-84 autonomous commits"
echo -e "  - 15-25 learned patterns"
echo -e "  - 60-70% success rate (improving over time)"
echo -e "  - \$0.00 cost (100% local execution)"
echo ""
echo -e "${YELLOW}Wake up to an improved codebase! 🌙${NC}"
echo ""
