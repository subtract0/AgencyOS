#!/bin/bash

# Agency OS Development Environment Setup Script
# This script sets up a complete development environment for Agency OS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================${NC}"
echo -e "${BLUE}  Agency OS Development Setup${NC}"
echo -e "${BLUE}===================================${NC}"

# Function to print colored messages
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check Python version
info "Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
REQUIRED_VERSION="3.12"
if [[ ! "$PYTHON_VERSION" =~ ^3\.(12|13) ]]; then
    error "Python 3.12 or 3.13 required. Found: $PYTHON_VERSION"
    exit 1
fi
info "Python $PYTHON_VERSION ✓"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    info "Creating virtual environment..."
    python3 -m venv .venv
else
    info "Virtual environment already exists ✓"
fi

# Activate virtual environment
info "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
info "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
info "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    info "Requirements installed ✓"
fi

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt --quiet
    info "Dev requirements installed ✓"
fi

# Install package in editable mode
info "Installing Agency OS in editable mode..."
pip install -e . --quiet 2>/dev/null || true

# Install additional testing dependencies
info "Installing test dependencies..."
pip install pytest pytest-asyncio pytest-xdist pytest-timeout pytest-cov --quiet

# Install pre-commit hooks
info "Installing pre-commit hooks..."
pip install pre-commit --quiet
pre-commit install
info "Pre-commit hooks installed ✓"

# Create .env file from template if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        info "Creating .env file from template..."
        cp .env.example .env
        warn "Please edit .env and add your API keys"
    else
        warn ".env.example not found, skipping .env creation"
    fi
else
    info ".env file already exists ✓"
fi

# Create necessary directories
info "Creating necessary directories..."
mkdir -p logs/sessions
mkdir -p logs/telemetry
mkdir -p logs/autonomous_healing
mkdir -p logs/archive
mkdir -p logs/snapshots
mkdir -p specs
mkdir -p plans
info "Directories created ✓"

# Run type checking
info "Running type checking..."
if command -v mypy &> /dev/null; then
    pip install mypy --quiet
    mypy . --ignore-missing-imports --no-error-summary 2>/dev/null && info "Type checking passed ✓" || warn "Some type errors found (non-blocking)"
fi

# Run constitutional check if available
if [ -f "scripts/constitutional_check.py" ]; then
    info "Running constitutional compliance check..."
    python scripts/constitutional_check.py && info "Constitutional compliance ✓" || warn "Constitutional check failed (non-blocking)"
fi

# Run quick test to verify setup
info "Running quick test to verify setup..."
python -m pytest tests/ -x --maxfail=1 -q --tb=no 2>/dev/null && info "Quick test passed ✓" || warn "Some tests failed (non-blocking)"

# Display summary
echo ""
echo -e "${GREEN}===================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}===================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'source .venv/bin/activate' to activate the environment"
echo "3. Run 'python run_tests.py --run-all' to verify all tests pass"
echo "4. Run 'python agency.py' to start the Agency"
echo ""
echo "For autonomous development:"
echo "- Always start with a /prime command"
echo "- Maintain 100% test compliance (constitutional requirement)"
echo "- Use 'pre-commit run --all-files' to check before committing"
echo ""
info "Happy coding with Agency OS! 🚀"