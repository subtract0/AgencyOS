#!/bin/bash
#
# Trinity Local M4 - Standalone Installer
# Downloads Agency repo and runs installation
#

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Trinity Local M4 - Standalone Installer                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Agency already exists
if [[ -d "${HOME}/Agency" ]]; then
    echo -e "${GREEN}[INFO]${NC} Agency repo already exists at ~/Agency"
    cd "${HOME}/Agency"

    # Pull latest
    echo -e "${BLUE}[INFO]${NC} Pulling latest changes..."
    git checkout feat/phase-2ab-mars-ready-complete
    git pull origin feat/phase-2ab-mars-ready-complete
else
    # Clone repo
    echo -e "${BLUE}[INFO]${NC} Cloning Agency repo..."
    cd "${HOME}"
    git clone https://github.com/subtract0/AgencyOS.git Agency
    cd Agency
    git checkout feat/phase-2ab-mars-ready-complete
fi

# Run installer
echo ""
echo -e "${BLUE}[INFO]${NC} Running Trinity Local M4 installer..."
./deploy/trinity-local-m4/install.sh
