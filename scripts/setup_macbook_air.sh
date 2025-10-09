#!/bin/bash
# MacBook Air Setup Script
# Run this on MacBook Air to configure autonomous agent coordination

set -e  # Exit on error

echo "============================================================"
echo "🍎 MacBook Air Setup for Autonomous Agent Coordination"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check current location
echo -e "${BLUE}Step 1: Checking environment...${NC}"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo ""

# Step 2: Check iCloud accessibility
echo -e "${BLUE}Step 2: Verifying iCloud Drive access...${NC}"
ICLOUD_PATH="/Users/am/Library/Mobile Documents/com~apple~CloudDocs/Agency-Shared"

if [ -d "$ICLOUD_PATH" ]; then
    echo -e "${GREEN}✅ iCloud Drive accessible${NC}"
    echo "   Path: $ICLOUD_PATH"
    ls -la "$ICLOUD_PATH"
else
    echo -e "${YELLOW}⚠️  iCloud path not found: $ICLOUD_PATH${NC}"
    echo "   Please ensure:"
    echo "   1. iCloud Drive is enabled (System Settings → Apple ID → iCloud)"
    echo "   2. Same Apple ID as M4 Pro"
    echo "   3. iCloud sync is complete"
    exit 1
fi
echo ""

# Step 3: Check if Agency repo exists
echo -e "${BLUE}Step 3: Checking Agency repository...${NC}"
if [ -d "$HOME/Code/Agency" ]; then
    echo -e "${GREEN}✅ Agency directory exists${NC}"
    cd "$HOME/Code/Agency"
else
    echo -e "${YELLOW}⚠️  Agency directory not found${NC}"
    echo "   Creating ~/Code directory..."
    mkdir -p "$HOME/Code"
    echo ""
    echo "   Please clone the repository:"
    echo "   cd ~/Code"
    echo "   git clone <repository-url> Agency"
    echo ""
    echo "   Or create symlink to iCloud:"
    echo "   ln -s '$ICLOUD_PATH' ~/Code/Agency"
    exit 1
fi
echo ""

# Step 4: Copy configuration file
echo -e "${BLUE}Step 4: Installing configuration...${NC}"
CONFIG_SOURCE="$ICLOUD_PATH/.agency_config.json"
CONFIG_DEST="$HOME/Code/Agency/.agency_config.json"

if [ -f "$CONFIG_SOURCE" ]; then
    cp "$CONFIG_SOURCE" "$CONFIG_DEST"
    echo -e "${GREEN}✅ Configuration file installed${NC}"
    echo "   From: $CONFIG_SOURCE"
    echo "   To:   $CONFIG_DEST"
else
    echo -e "${YELLOW}⚠️  Config file not found in iCloud${NC}"
    echo "   Expected: $CONFIG_SOURCE"
    echo "   Please ensure M4 Pro has synced the file"
    exit 1
fi
echo ""

# Step 5: Test Python environment
echo -e "${BLUE}Step 5: Testing Python environment...${NC}"
cd "$HOME/Code/Agency"

if ! python3 --version > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Python 3 not found${NC}"
    echo "   Please install Python 3"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 available${NC}"
echo "   Version: $(python3 --version)"
echo ""

# Step 6: Test TaskQueue connection
echo -e "${BLUE}Step 6: Testing TaskQueue connection to iCloud...${NC}"
python3 -c "
import sys
sys.path.insert(0, '$HOME/Code/Agency')
from meta_learning.task_queue import TaskQueue

try:
    q = TaskQueue()
    print('✅ Connected to shared task queue!')
    print(f'   Queue file: {q.queue_file}')

    # Get status
    status = q.get_status()
    print(f'   Total tasks: {status[\"total\"]}')
    print(f'   Pending: {status[\"pending\"]}')
    print(f'   In progress: {status[\"in_progress\"]}')
    print(f'   Completed: {status[\"completed\"]}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    sys.exit(1)
" || exit 1

echo ""

# Step 7: Create start script
echo -e "${BLUE}Step 7: Creating agent start script...${NC}"
cat > "$HOME/Code/Agency/scripts/start_agents_mba.sh" << 'SCRIPT_EOF'
#!/bin/bash
# Quick start script for MacBook Air agents

echo "🚀 Starting MacBook Air Autonomous Agents"
echo "=========================================="
echo ""
echo "Opening 2 terminal windows..."
echo ""

# Terminal 1
osascript -e 'tell application "Terminal"
    do script "cd ~/Code/Agency && python scripts/autonomous_worker.py --agent-id mba-agent1"
    set custom title of front window to "MBA Agent 1"
end tell'

sleep 1

# Terminal 2
osascript -e 'tell application "Terminal"
    do script "cd ~/Code/Agency && python scripts/autonomous_worker.py --agent-id mba-agent2"
    set custom title of front window to "MBA Agent 2"
end tell'

echo "✅ Agents started in separate terminal windows"
echo ""
echo "Monitor progress:"
echo "  watch -n 5 'python meta_learning/task_queue.py status'"
SCRIPT_EOF

chmod +x "$HOME/Code/Agency/scripts/start_agents_mba.sh"
echo -e "${GREEN}✅ Start script created${NC}"
echo "   Location: ~/Code/Agency/scripts/start_agents_mba.sh"
echo ""

# Success!
echo "============================================================"
echo -e "${GREEN}✅ MacBook Air Setup Complete!${NC}"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start MacBook Air agents:"
echo "   cd ~/Code/Agency"
echo "   ./scripts/start_agents_mba.sh"
echo ""
echo "2. Or manually (2 terminals):"
echo "   Terminal 1: python scripts/autonomous_worker.py --agent-id mba-agent1"
echo "   Terminal 2: python scripts/autonomous_worker.py --agent-id mba-agent2"
echo ""
echo "3. Monitor from either machine:"
echo "   python meta_learning/task_queue.py status"
echo ""
echo "============================================================"
echo "🎉 Ready for 4-agent autonomous coordination!"
echo "============================================================"
