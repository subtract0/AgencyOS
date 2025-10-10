#!/usr/bin/env bash
################################################################################
# Dashboard Snapshot Monitoring Setup Script
#
# Purpose: Automate hourly dashboard snapshot generation using crontab or systemd
#
# Features:
# - Auto-detect crontab vs systemd
# - Validate Python environment and dependencies
# - Test snapshot generation before installing
# - Install/uninstall/status commands
# - Graceful error handling with informative messages
#
# Constitutional Compliance:
# - Article I: Complete validation before action (env check, test run)
# - Article II: 100% verification (test snapshot before cron install)
# - Article IV: Continuous learning (automated snapshot collection)
#
# Usage:
#   ./scripts/setup_monitoring_cron.sh install    # Install monitoring
#   ./scripts/setup_monitoring_cron.sh uninstall  # Remove monitoring
#   ./scripts/setup_monitoring_cron.sh status     # Check monitoring status
#   ./scripts/setup_monitoring_cron.sh test       # Test snapshot generation
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENCY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${AGENCY_ROOT}/logs/monitoring"
SETUP_LOG="${LOG_DIR}/setup.log"

# Cron configuration
CRON_SCHEDULE="0 * * * *"  # Every hour at minute 0
CRON_MARKER="# Agency Dashboard Snapshot"

# Systemd configuration
SYSTEMD_SERVICE_NAME="monitoring_snapshot"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"

################################################################################
# Logging Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    if [[ -f "${SETUP_LOG}" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "${SETUP_LOG}"
    fi
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    if [[ -f "${SETUP_LOG}" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" >> "${SETUP_LOG}"
    fi
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
    if [[ -f "${SETUP_LOG}" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "${SETUP_LOG}"
    fi
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    if [[ -f "${SETUP_LOG}" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "${SETUP_LOG}"
    fi
}

################################################################################
# Initialization
################################################################################

initialize() {
    # Create log directory first (before any logging)
    mkdir -p "${LOG_DIR}"

    # Create setup log
    touch "${SETUP_LOG}"

    log_info "Initializing monitoring setup..."
    log_success "Log directory created: ${LOG_DIR}"
}

################################################################################
# Validation Functions
################################################################################

validate_python_environment() {
    log_info "Validating Python environment..." >&2

    # Check if we're in Agency root
    if [[ ! -f "${AGENCY_ROOT}/agency.py" ]]; then
        log_error "Not in Agency root directory. Expected: ${AGENCY_ROOT}" >&2
        return 1
    fi

    # Detect virtual environment
    local python_cmd=""

    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        # Already in virtualenv - get the actual path
        python_cmd="$(which python)"
        log_success "Virtual environment detected: ${VIRTUAL_ENV}" >&2
    elif [[ -f "${AGENCY_ROOT}/.venv/bin/python" ]]; then
        # Standard .venv directory
        python_cmd="${AGENCY_ROOT}/.venv/bin/python"
        log_success "Found virtualenv: ${AGENCY_ROOT}/.venv" >&2
    elif [[ -f "${AGENCY_ROOT}/venv/bin/python" ]]; then
        # Alternative venv directory
        python_cmd="${AGENCY_ROOT}/venv/bin/python"
        log_success "Found virtualenv: ${AGENCY_ROOT}/venv" >&2
    else
        log_error "No Python virtual environment found. Please create one:" >&2
        log_error "  python -m venv .venv" >&2
        log_error "  source .venv/bin/activate" >&2
        return 1
    fi

    # Validate Python version
    local python_version
    python_version=$("${python_cmd}" --version 2>&1 | awk '{print $2}')
    log_info "Python version: ${python_version}" >&2

    # Check for required modules
    log_info "Checking required dependencies..." >&2

    if ! "${python_cmd}" -c "import pydantic" 2>/dev/null; then
        log_error "Missing required dependency: pydantic" >&2
        log_error "  pip install pydantic" >&2
        return 1
    fi

    log_success "Python environment validated" >&2

    # Return python command on stdout (for command substitution)
    echo "${python_cmd}"
}

test_snapshot_generation() {
    local python_cmd="$1"

    log_info "Testing snapshot generation..."

    cd "${AGENCY_ROOT}"

    # Run snapshot generator with verbose output
    if "${python_cmd}" -m tools.quality_feedback.dashboard_snapshot --verbose 2>&1 | tee -a "${SETUP_LOG}"; then
        log_success "Snapshot generation test passed"
        return 0
    else
        log_error "Snapshot generation test failed"
        log_error "Check logs at: ${SETUP_LOG}"
        return 1
    fi
}

################################################################################
# Scheduler Detection
################################################################################

detect_scheduler() {
    log_info "Detecting available scheduler..." >&2

    # Check for systemd (user mode)
    if command -v systemctl &>/dev/null && systemctl --user daemon-reload &>/dev/null 2>&1; then
        log_info "systemd user mode available" >&2
        echo "systemd"
        return 0
    fi

    # Check for crontab
    if command -v crontab &>/dev/null; then
        log_info "crontab available" >&2
        echo "crontab"
        return 0
    fi

    log_error "No supported scheduler found (systemd or crontab required)" >&2
    return 1
}

################################################################################
# Crontab Installation
################################################################################

install_crontab() {
    local python_cmd="$1"

    log_info "Installing crontab entry..."

    # Build cron command
    local cron_cmd="cd ${AGENCY_ROOT} && ${python_cmd} -m tools.quality_feedback.dashboard_snapshot >> ${LOG_DIR}/cron.log 2>&1"
    local cron_entry="${CRON_SCHEDULE} ${cron_cmd} ${CRON_MARKER}"

    # Check if entry already exists
    if crontab -l 2>/dev/null | grep -F "${CRON_MARKER}" >/dev/null; then
        log_warning "Crontab entry already exists. Removing old entry..."
        crontab -l 2>/dev/null | grep -v "${CRON_MARKER}" | crontab -
    fi

    # Add new entry
    (crontab -l 2>/dev/null || true; echo "${cron_entry}") | crontab -

    log_success "Crontab installed: ${cron_entry}"
    log_info "Logs will be written to: ${LOG_DIR}/cron.log"
}

uninstall_crontab() {
    log_info "Uninstalling crontab entry..." >&2

    if crontab -l 2>/dev/null | grep -F "${CRON_MARKER}" >/dev/null; then
        crontab -l 2>/dev/null | grep -v "${CRON_MARKER}" | crontab -
        log_success "Crontab entry removed" >&2
    else
        log_warning "No crontab entry found" >&2
    fi
}

status_crontab() {
    log_info "Checking crontab status..."

    if crontab -l 2>/dev/null | grep -F "${CRON_MARKER}" >/dev/null; then
        echo -e "${GREEN}✓${NC} Crontab monitoring is ACTIVE"
        echo "Entry:"
        crontab -l 2>/dev/null | grep -F "${CRON_MARKER}"
    else
        echo -e "${YELLOW}✗${NC} Crontab monitoring is NOT installed"
    fi
}

################################################################################
# Systemd Installation
################################################################################

install_systemd() {
    local python_cmd="$1"

    log_info "Installing systemd units..."

    # Create systemd user directory
    mkdir -p "${SYSTEMD_USER_DIR}"

    # Copy service and timer files
    local service_file="${SCRIPT_DIR}/${SYSTEMD_SERVICE_NAME}.service"
    local timer_file="${SCRIPT_DIR}/${SYSTEMD_SERVICE_NAME}.timer"

    if [[ ! -f "${service_file}" ]]; then
        log_error "Service file not found: ${service_file}"
        return 1
    fi

    if [[ ! -f "${timer_file}" ]]; then
        log_error "Timer file not found: ${timer_file}"
        return 1
    fi

    # Update service file with actual paths
    sed -e "s|{{AGENCY_ROOT}}|${AGENCY_ROOT}|g" \
        -e "s|{{PYTHON_CMD}}|${python_cmd}|g" \
        -e "s|{{LOG_DIR}}|${LOG_DIR}|g" \
        "${service_file}" > "${SYSTEMD_USER_DIR}/${SYSTEMD_SERVICE_NAME}.service"

    cp "${timer_file}" "${SYSTEMD_USER_DIR}/${SYSTEMD_SERVICE_NAME}.timer"

    # Reload systemd daemon
    systemctl --user daemon-reload

    # Enable and start timer
    systemctl --user enable "${SYSTEMD_SERVICE_NAME}.timer"
    systemctl --user start "${SYSTEMD_SERVICE_NAME}.timer"

    log_success "Systemd units installed and enabled"
    log_info "Service: ${SYSTEMD_USER_DIR}/${SYSTEMD_SERVICE_NAME}.service"
    log_info "Timer: ${SYSTEMD_USER_DIR}/${SYSTEMD_SERVICE_NAME}.timer"
}

uninstall_systemd() {
    log_info "Uninstalling systemd units..."

    # Stop and disable timer
    systemctl --user stop "${SYSTEMD_SERVICE_NAME}.timer" 2>/dev/null || true
    systemctl --user disable "${SYSTEMD_SERVICE_NAME}.timer" 2>/dev/null || true

    # Remove unit files
    rm -f "${SYSTEMD_USER_DIR}/${SYSTEMD_SERVICE_NAME}.service"
    rm -f "${SYSTEMD_USER_DIR}/${SYSTEMD_SERVICE_NAME}.timer"

    # Reload daemon
    systemctl --user daemon-reload

    log_success "Systemd units removed"
}

status_systemd() {
    log_info "Checking systemd status..."

    if systemctl --user is-enabled "${SYSTEMD_SERVICE_NAME}.timer" &>/dev/null; then
        echo -e "${GREEN}✓${NC} Systemd monitoring is ACTIVE"
        echo ""
        systemctl --user status "${SYSTEMD_SERVICE_NAME}.timer" --no-pager
    else
        echo -e "${YELLOW}✗${NC} Systemd monitoring is NOT installed"
    fi
}

################################################################################
# Main Commands
################################################################################

cmd_install() {
    log_info "=== Installing Dashboard Snapshot Monitoring ==="

    initialize

    # Validate environment
    local python_cmd
    python_cmd=$(validate_python_environment) || exit 1

    # Test snapshot generation
    test_snapshot_generation "${python_cmd}" || exit 1

    # Detect scheduler
    local scheduler
    scheduler=$(detect_scheduler) || exit 1

    # Install based on scheduler
    case "${scheduler}" in
        systemd)
            install_systemd "${python_cmd}"
            ;;
        crontab)
            install_crontab "${python_cmd}"
            ;;
        *)
            log_error "Unknown scheduler: ${scheduler}"
            exit 1
            ;;
    esac

    log_success "=== Monitoring installation complete ==="
    echo ""
    echo "Dashboard snapshots will be generated hourly at:"
    echo "  ${LOG_DIR}/snapshots/"
    echo ""
    echo "To check status: $0 status"
}

cmd_uninstall() {
    log_info "=== Uninstalling Dashboard Snapshot Monitoring ==="

    initialize

    # Detect scheduler
    local scheduler
    scheduler=$(detect_scheduler) || exit 1

    # Uninstall based on scheduler
    case "${scheduler}" in
        systemd)
            uninstall_systemd
            ;;
        crontab)
            uninstall_crontab
            ;;
        *)
            log_error "Unknown scheduler: ${scheduler}"
            exit 1
            ;;
    esac

    log_success "=== Monitoring uninstallation complete ==="
}

cmd_status() {
    initialize

    # Detect scheduler
    local scheduler
    scheduler=$(detect_scheduler) || exit 1

    # Show status based on scheduler
    case "${scheduler}" in
        systemd)
            status_systemd
            ;;
        crontab)
            status_crontab
            ;;
        *)
            log_error "Unknown scheduler: ${scheduler}"
            exit 1
            ;;
    esac

    # Show recent snapshots
    echo ""
    echo "Recent snapshots:"
    if [[ -d "${LOG_DIR}/snapshots" ]]; then
        ls -lht "${LOG_DIR}/snapshots" | head -n 6
    else
        echo "  (no snapshots yet)"
    fi
}

cmd_test() {
    log_info "=== Testing Snapshot Generation ==="

    initialize

    # Validate environment
    local python_cmd
    python_cmd=$(validate_python_environment) || exit 1

    # Test snapshot generation
    test_snapshot_generation "${python_cmd}" || exit 1

    log_success "=== Test complete ==="
}

cmd_help() {
    cat <<EOF
Dashboard Snapshot Monitoring Setup

Usage:
  $0 <command>

Commands:
  install     Install hourly monitoring (crontab or systemd)
  uninstall   Remove monitoring configuration
  status      Check monitoring status and recent snapshots
  test        Test snapshot generation without installing
  help        Show this help message

Features:
  - Auto-detects crontab vs systemd
  - Validates Python environment before setup
  - Tests snapshot generation before installation
  - Logs to: ${LOG_DIR}/setup.log

Examples:
  $0 install    # Set up automated monitoring
  $0 status     # Check if monitoring is active
  $0 uninstall  # Remove monitoring

Constitutional Compliance:
  - Article I: Complete validation before action
  - Article II: 100% verification (test before install)
  - Article IV: Continuous learning (automated snapshots)
EOF
}

################################################################################
# Entry Point
################################################################################

main() {
    local command="${1:-help}"

    case "${command}" in
        install)
            cmd_install
            ;;
        uninstall)
            cmd_uninstall
            ;;
        status)
            cmd_status
            ;;
        test)
            cmd_test
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            log_error "Unknown command: ${command}"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
