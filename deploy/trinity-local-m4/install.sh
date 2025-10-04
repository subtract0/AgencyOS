#!/bin/bash
#
# Trinity Local M4 Deployment - One-Command Installer
#
# Deploys self-contained 3-LLM Trinity loop on M4 MacBook (48GB)
# - WITNESS: qwen2.5-coder:1.5b (pattern detection)
# - ARCHITECT: qwen2.5-coder:7b (strategic planning)
# - EXECUTOR: codestral:22b (code execution)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/subtract0/AgencyOS/main/deploy/trinity-local-m4/install.sh | bash
#
# Or local:
#   ./install.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_RAM_GB=48
REQUIRED_DISK_GB=50
MODELS=(
    "qwen2.5-coder:1.5b"
    "qwen2.5-coder:7b"
    "codestral:22b"
)
TRINITY_DIR="${HOME}/.trinity-local"
VENV_DIR="${TRINITY_DIR}/.venv"

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# System verification
check_macos_version() {
    log_info "Checking macOS version..."

    if [[ "$(uname)" != "Darwin" ]]; then
        log_error "This installer is for macOS only"
        exit 1
    fi

    macos_version=$(sw_vers -productVersion)
    major_version=$(echo "$macos_version" | cut -d. -f1)

    if [[ $major_version -lt 14 ]]; then
        log_error "macOS 14+ required (you have $macos_version)"
        exit 1
    fi

    log_success "macOS $macos_version detected"
}

check_m4_chip() {
    log_info "Checking for M4 chip..."

    chip=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "unknown")

    if [[ "$chip" =~ "Apple M4" ]]; then
        log_success "M4 chip detected: $chip"
    elif [[ "$chip" =~ "Apple M" ]]; then
        log_warning "Non-M4 Apple Silicon detected: $chip"
        log_warning "Trinity will work but performance may vary"
    else
        log_error "Apple Silicon not detected. M4 MacBook required."
        exit 1
    fi
}

check_ram() {
    log_info "Checking RAM..."

    ram_bytes=$(sysctl -n hw.memsize)
    ram_gb=$((ram_bytes / 1024 / 1024 / 1024))

    if [[ $ram_gb -lt $REQUIRED_RAM_GB ]]; then
        log_error "Insufficient RAM: ${ram_gb}GB (${REQUIRED_RAM_GB}GB required)"
        exit 1
    fi

    log_success "${ram_gb}GB RAM available (${REQUIRED_RAM_GB}GB required)"
}

check_disk_space() {
    log_info "Checking disk space..."

    available_gb=$(df -g . | tail -1 | awk '{print $4}')

    if [[ $available_gb -lt $REQUIRED_DISK_GB ]]; then
        log_error "Insufficient disk space: ${available_gb}GB (${REQUIRED_DISK_GB}GB required)"
        exit 1
    fi

    log_success "${available_gb}GB disk space available (${REQUIRED_DISK_GB}GB required)"
}

# Ollama installation
install_ollama() {
    log_info "Checking Ollama installation..."

    if command -v ollama &> /dev/null; then
        log_success "Ollama already installed: $(ollama --version)"
        return
    fi

    log_info "Installing Ollama..."

    if ! curl -fsSL https://ollama.com/install.sh | sh; then
        log_error "Ollama installation failed"
        exit 1
    fi

    log_success "Ollama installed successfully"
}

start_ollama_service() {
    log_info "Starting Ollama service..."

    # Check if already running
    if pgrep -x "ollama" > /dev/null; then
        log_success "Ollama service already running"
        return
    fi

    # Start Ollama in background
    ollama serve &> /dev/null &

    # Wait for service to be ready
    max_wait=30
    waited=0
    while ! curl -s http://localhost:11434/api/tags &> /dev/null; do
        if [[ $waited -ge $max_wait ]]; then
            log_error "Ollama service failed to start"
            exit 1
        fi
        sleep 1
        ((waited++))
    done

    log_success "Ollama service started"
}

pull_models() {
    log_info "Pulling Trinity models (this may take 10-20 minutes)..."

    for model in "${MODELS[@]}"; do
        log_info "Pulling $model..."

        if ! ollama pull "$model"; then
            log_error "Failed to pull $model"
            exit 1
        fi

        log_success "$model pulled successfully"
    done

    log_success "All models downloaded"
}

verify_models() {
    log_info "Verifying model availability..."

    available_models=$(ollama list | awk 'NR>1 {print $1}')

    for model in "${MODELS[@]}"; do
        if echo "$available_models" | grep -q "$model"; then
            log_success "$model verified"
        else
            log_error "$model not found in Ollama"
            exit 1
        fi
    done
}

# Python environment setup
setup_python_env() {
    log_info "Setting up Python environment..."

    mkdir -p "$TRINITY_DIR"
    cd "$TRINITY_DIR"

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3.12+"
        exit 1
    fi

    python_version=$(python3 --version | awk '{print $2}')
    log_info "Python $python_version detected"

    # Create virtualenv
    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi

    # Activate virtualenv
    source "$VENV_DIR/bin/activate"

    log_success "Python environment ready"
}

install_trinity_dependencies() {
    log_info "Installing Trinity dependencies..."

    source "$VENV_DIR/bin/activate"

    # Create requirements.txt
    cat > "${TRINITY_DIR}/requirements.txt" << 'EOF'
# Trinity Local Dependencies (Minimal)
httpx>=0.27.0          # Ollama API client
pydantic>=2.0.0        # Data models
sqlalchemy>=2.0.0      # PersistentStore
sentence-transformers>=2.2.0  # VectorStore (Article IV)
PyYAML>=6.0            # Config parsing

# Optional but recommended
pytest>=7.0.0          # Testing infrastructure
EOF

    pip install --upgrade pip
    pip install -r "${TRINITY_DIR}/requirements.txt"

    log_success "Dependencies installed"
}

copy_trinity_code() {
    log_info "Copying Trinity Protocol code..."

    # Determine source directory
    if [[ -d "trinity_protocol" ]]; then
        # Running from Agency repo root
        source_dir="."
    elif [[ -d "../trinity_protocol" ]]; then
        # Running from deploy/trinity-local-m4
        source_dir=".."
    else
        log_error "Cannot find Trinity Protocol source code"
        log_info "Please run from Agency repository root or deploy/trinity-local-m4/"
        exit 1
    fi

    # Copy core Trinity modules
    cp -r "${source_dir}/trinity_protocol" "${TRINITY_DIR}/"
    cp -r "${source_dir}/shared" "${TRINITY_DIR}/"

    # Copy scripts
    cp "${source_dir}/deploy/trinity-local-m4/start_trinity.sh" "${TRINITY_DIR}/" || true
    cp "${source_dir}/deploy/trinity-local-m4/stop_trinity.sh" "${TRINITY_DIR}/" || true
    cp "${source_dir}/deploy/trinity-local-m4/monitor_trinity.sh" "${TRINITY_DIR}/" || true

    chmod +x "${TRINITY_DIR}"/*.sh || true

    log_success "Trinity code copied to ${TRINITY_DIR}"
}

create_trinity_config() {
    log_info "Creating Trinity configuration..."

    cat > "${TRINITY_DIR}/trinity_config.yaml" << 'EOF'
# Trinity Local Configuration for M4 MacBook (48GB)

models:
  witness:
    name: "qwen2.5-coder:1.5b"
    context_length: 2048
    temperature: 0.3
    timeout: 30

  architect:
    name: "qwen2.5-coder:7b"
    context_length: 4096
    temperature: 0.5
    timeout: 120

  executor:
    name: "codestral:22b"
    context_length: 8192
    temperature: 0.3
    timeout: 300

  sub_agents:
    code_writer: "codestral:22b"
    test_architect: "codestral:22b"
    tool_developer: "codestral:22b"
    immunity_enforcer: "qwen2.5-coder:7b"
    release_manager: "qwen2.5-coder:7b"
    task_summarizer: "qwen2.5-coder:1.5b"

memory:
  max_total_mb: 34000
  ollama_num_ctx: 8192
  sequential_execution: true

telemetry:
  log_dir: "logs/trinity_local/"
  enable_metrics: true
  enable_cost_tracker: true

constitutional:
  enable_learning: true
  enforce_tests: true
  max_autonomous_commits: 10
EOF

    log_success "Configuration created: ${TRINITY_DIR}/trinity_config.yaml"
}

initialize_databases() {
    log_info "Initializing Trinity databases..."

    mkdir -p "${TRINITY_DIR}/db"
    mkdir -p "${TRINITY_DIR}/logs/trinity_local"

    source "$VENV_DIR/bin/activate"

    # Create empty SQLite databases
    python3 << 'PYTHON'
import sqlite3
import os

db_dir = os.path.expanduser("~/.trinity-local/db")
os.makedirs(db_dir, exist_ok=True)

# Message bus database
conn = sqlite3.connect(f"{db_dir}/message_bus.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
conn.close()

# Persistent store database
conn = sqlite3.connect(f"{db_dir}/patterns.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS patterns (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
conn.close()

print("✓ Databases initialized")
PYTHON

    log_success "Databases initialized"
}

run_health_check() {
    log_info "Running health check..."

    source "$VENV_DIR/bin/activate"

    # Test Ollama connectivity
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        log_error "Ollama service not accessible"
        exit 1
    fi

    # Test model availability
    for model in "${MODELS[@]}"; do
        if ! ollama list | grep -q "$model"; then
            log_error "Model $model not available"
            exit 1
        fi
    done

    # Test Python imports
    python3 << 'PYTHON'
try:
    import httpx
    import pydantic
    import sqlalchemy
    import yaml
    print("✓ Python dependencies verified")
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    exit(1)
PYTHON

    log_success "Health check passed"
}

create_launcher_alias() {
    log_info "Creating launcher alias..."

    shell_rc=""
    if [[ -f "$HOME/.zshrc" ]]; then
        shell_rc="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        shell_rc="$HOME/.bashrc"
    fi

    if [[ -n "$shell_rc" ]]; then
        if ! grep -q "trinity-local" "$shell_rc"; then
            echo "" >> "$shell_rc"
            echo "# Trinity Local M4" >> "$shell_rc"
            echo "alias trinity='cd ${TRINITY_DIR} && ./start_trinity.sh'" >> "$shell_rc"
            echo "alias trinity-stop='cd ${TRINITY_DIR} && ./stop_trinity.sh'" >> "$shell_rc"
            echo "alias trinity-monitor='cd ${TRINITY_DIR} && ./monitor_trinity.sh'" >> "$shell_rc"

            log_success "Aliases added to $shell_rc"
            log_info "Restart your shell or run: source $shell_rc"
        fi
    fi
}

print_success_banner() {
    cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║   🎉  Trinity Local M4 Installation Complete!  🎉              ║
║                                                                ║
║   3 Local LLMs Running Autonomous Trinity Loop                 ║
║   - WITNESS:    qwen2.5-coder:1.5b (pattern detection)        ║
║   - ARCHITECT:  qwen2.5-coder:7b   (strategic planning)       ║
║   - EXECUTOR:   codestral:22b      (code execution)           ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

EOF

    log_info "Installation directory: ${TRINITY_DIR}"
    log_info ""
    log_info "Quick Start Commands:"
    echo ""
    echo "  Start Trinity:    cd ${TRINITY_DIR} && ./start_trinity.sh"
    echo "  Stop Trinity:     cd ${TRINITY_DIR} && ./stop_trinity.sh"
    echo "  Monitor Status:   cd ${TRINITY_DIR} && ./monitor_trinity.sh"
    echo ""
    echo "Or use aliases (after restarting shell):"
    echo ""
    echo "  trinity          # Start Trinity loop"
    echo "  trinity-stop     # Stop Trinity loop"
    echo "  trinity-monitor  # Monitor real-time status"
    echo ""

    log_success "Ready for 100% offline autonomous development!"
}

# Main installation flow
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Trinity Local M4 Installer                                    ║"
    echo "║  Deploy 3-LLM autonomous coding loop on M4 MacBook             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # Phase 1: System Verification
    log_info "Phase 1: System Verification"
    check_macos_version
    check_m4_chip
    check_ram
    check_disk_space
    echo ""

    # Phase 2: Ollama Setup
    log_info "Phase 2: Ollama Setup"
    install_ollama
    start_ollama_service
    pull_models
    verify_models
    echo ""

    # Phase 3: Python Environment
    log_info "Phase 3: Python Environment"
    setup_python_env
    install_trinity_dependencies
    echo ""

    # Phase 4: Trinity Installation
    log_info "Phase 4: Trinity Installation"
    copy_trinity_code
    create_trinity_config
    initialize_databases
    echo ""

    # Phase 5: Validation
    log_info "Phase 5: Final Validation"
    run_health_check
    create_launcher_alias
    echo ""

    print_success_banner
}

main "$@"
