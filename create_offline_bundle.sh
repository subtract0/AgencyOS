#!/bin/bash
# Create Offline Bundle for Constitutional Consciousness
# No internet required after this bundle is created

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

VERSION="v1.0.0"
BUNDLE_NAME="agency_offline_${VERSION}"

clear
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     Creating Offline Bundle                              ║"
echo "║     Version: $VERSION                                   ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo -e "${YELLOW}This will create a fully offline-capable bundle (~21GB)${NC}"
echo -e "${YELLOW}No internet will be needed after deployment${NC}\n"

# Check disk space
echo -e "${BLUE}[1/7] Checking disk space...${NC}"
AVAILABLE=$(df -g . | awk 'NR==2 {print $4}')
if [ "$AVAILABLE" -lt 30 ]; then
    echo -e "${RED}❌ Not enough disk space. Need 30GB, have ${AVAILABLE}GB${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Disk space OK (${AVAILABLE}GB available)${NC}\n"

# Create bundle directory
echo -e "${BLUE}[2/7] Creating bundle structure...${NC}"
mkdir -p "$BUNDLE_NAME"/{ollama_models,.vendor,.cache/sentence_transformers,tools,docs,logs,reports}
echo -e "${GREEN}✓ Structure created${NC}\n"

# Download Ollama models
echo -e "${BLUE}[3/7] Downloading Ollama models...${NC}"
echo -e "${YELLOW}This will take 10-15 minutes (20GB download)${NC}\n"

if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Ollama not installed. Run: curl -fsSL https://ollama.com/install.sh | sh${NC}"
    exit 1
fi

# Ensure Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Pull and export models
MODELS=(
    "codestral:22b-v0.1-q4_K_M"
    "qwen2.5-coder:7b-instruct-q4_K_M"
    "qwen2.5-coder:1.5b-instruct-q4_K_M"
)

for model in "${MODELS[@]}"; do
    echo -e "  Pulling $model..."
    ollama pull "$model" || {
        # Try without version suffix
        BASE_MODEL=$(echo "$model" | cut -d':' -f1)
        echo -e "${YELLOW}  Trying $BASE_MODEL:latest${NC}"
        ollama pull "$BASE_MODEL:latest"
    }
done

# Copy Ollama model files
echo -e "  Copying model files..."
if [ -d "$HOME/.ollama/models" ]; then
    cp -r "$HOME/.ollama/models/"* "$BUNDLE_NAME/ollama_models/" 2>/dev/null || true
fi

echo -e "${GREEN}✓ Ollama models ready${NC}\n"

# Download Python dependencies
echo -e "${BLUE}[4/7] Downloading Python dependencies...${NC}"
pip download sentence-transformers pydantic litellm -d "$BUNDLE_NAME/.vendor/" --quiet
echo -e "${GREEN}✓ Python packages downloaded${NC}\n"

# Download sentence-transformer model
echo -e "${BLUE}[5/7] Caching sentence-transformer embeddings...${NC}"
python3 << EOF
from sentence_transformers import SentenceTransformer
import os

model_name = "all-MiniLM-L6-v2"
cache_dir = "$BUNDLE_NAME/.cache/sentence_transformers"

print(f"  Downloading {model_name}...")
model = SentenceTransformer(model_name)
model.save(os.path.join(cache_dir, model_name))
print("  ✓ Embeddings cached")
EOF
echo -e "${GREEN}✓ Embeddings cached${NC}\n"

# Copy Constitutional Consciousness source
echo -e "${BLUE}[6/7] Copying source code...${NC}"
cp -r tools/constitutional_consciousness "$BUNDLE_NAME/tools/"
cp -r docs/deployment "$BUNDLE_NAME/docs/"
cp setup_consciousness.sh start_night_run.sh stop_night_run.sh "$BUNDLE_NAME/"
cp QUICK_START.md DEPLOY_NIGHT_RUN.md README_v1.0.0.md "$BUNDLE_NAME/"
echo -e "${GREEN}✓ Source copied${NC}\n"

# Create offline installer
echo -e "${BLUE}[7/7] Creating offline installer...${NC}"

cat > "$BUNDLE_NAME/install_offline.sh" <<'INSTALLER_EOF'
#!/bin/bash
# Offline Installer - No Internet Required

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Installing Constitutional Consciousness (Offline Mode)${NC}\n"

# Install Python dependencies from vendor
echo -e "${BLUE}[1/4] Installing Python dependencies...${NC}"
python3 -m venv .venv
source .venv/bin/activate
pip install --no-index --find-links=.vendor/ sentence-transformers pydantic litellm --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}\n"

# Install Ollama if needed
echo -e "${BLUE}[2/4] Checking Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama not found. Please install manually:${NC}"
    echo -e "${YELLOW}  curl -fsSL https://ollama.com/install.sh | sh${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Ollama installed${NC}\n"

# Copy models to Ollama directory
echo -e "${BLUE}[3/4] Installing Ollama models...${NC}"
mkdir -p "$HOME/.ollama/models"
cp -r ollama_models/* "$HOME/.ollama/models/" 2>/dev/null || true
echo -e "${GREEN}✓ Models installed${NC}\n"

# Create offline configuration
echo -e "${BLUE}[4/4] Creating offline configuration...${NC}"
cat > .env.offline <<'ENV_EOF'
# Offline Mode Configuration
AGENCY_MODE=offline
OFFLINE_MODE=true

# No external services
ENABLE_GPT5_ESCALATION=false
USE_OPENAI_FALLBACK=false
OLLAMA_AUTO_PULL=false

# Local-only paths
SENTENCE_TRANSFORMERS_CACHE=.cache/sentence_transformers

# Ollama models
PLANNER_MODEL=codestral:22b-v0.1-q4_K_M
CODER_MODEL=qwen2.5-coder:7b-instruct-q4_K_M
SCANNER_MODEL=qwen2.5-coder:1.5b-instruct-q4_K_M

# Constitutional Consciousness
ENABLE_CONSCIOUSNESS=true
AUTONOMOUS_NIGHT_RUN=true
ENV_EOF

echo -e "${GREEN}✓ Configuration created${NC}\n"

echo -e "${GREEN}${BOLD}Installation Complete!${NC}\n"
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Start Ollama: ${YELLOW}ollama serve &${NC}"
echo -e "  2. Run offline:  ${YELLOW}bash start_night_run.sh --offline${NC}"
echo -e "  3. Check results: ${YELLOW}cat reports/latest.txt${NC}\n"
INSTALLER_EOF

chmod +x "$BUNDLE_NAME/install_offline.sh"

# Update start script for offline mode
cat >> "$BUNDLE_NAME/start_night_run.sh" <<'OFFLINE_PATCH'

# Offline mode detection
if [ "$1" == "--offline" ]; then
    export OFFLINE_MODE=true
    export SENTENCE_TRANSFORMERS_CACHE=.cache/sentence_transformers
    export OLLAMA_AUTO_PULL=false
    echo -e "${BLUE}🔒 Offline Mode Enabled${NC}"
    echo -e "${YELLOW}No network access required${NC}\n"
fi
OFFLINE_PATCH

echo -e "${GREEN}✓ Offline installer created${NC}\n"

# Create tarball
echo -e "${BLUE}Creating compressed bundle...${NC}"
tar -czf "${BUNDLE_NAME}.tar.gz" "$BUNDLE_NAME"
BUNDLE_SIZE=$(du -h "${BUNDLE_NAME}.tar.gz" | cut -f1)

# Create checksum
echo -e "${BLUE}Creating checksum...${NC}"
shasum -a 256 "${BUNDLE_NAME}.tar.gz" > "${BUNDLE_NAME}.sha256"

# Cleanup
rm -rf "$BUNDLE_NAME"

echo -e "${GREEN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     ✓ Offline Bundle Created!                            ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo -e "${BOLD}Bundle Details:${NC}"
echo -e "  File: ${BLUE}${BUNDLE_NAME}.tar.gz${NC}"
echo -e "  Size: ${BLUE}${BUNDLE_SIZE}${NC}"
echo -e "  SHA256: ${BLUE}${BUNDLE_NAME}.sha256${NC}\n"

echo -e "${BOLD}Offline Deployment:${NC}"
echo -e "  1. Transfer bundle to offline machine (USB/etc.)"
echo -e "  2. Extract: ${YELLOW}tar -xzf ${BUNDLE_NAME}.tar.gz${NC}"
echo -e "  3. Install: ${YELLOW}cd ${BUNDLE_NAME} && bash install_offline.sh${NC}"
echo -e "  4. Run:     ${YELLOW}bash start_night_run.sh --offline${NC}\n"

echo -e "${GREEN}✓ No internet required after deployment!${NC}\n"
