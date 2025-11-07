#!/bin/bash
# Setup development environment for Agency OS
# Purpose: Enable local testing in <5 minutes from clone
# Solves: ModuleNotFoundError blocking local test runs (Blocker #1 - CRITICAL)

set -e

echo "🔧 Setting up Agency OS development environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$python_version" < "3.10" ]]; then
    echo "❌ Python 3.10+ required (found $python_version)"
    exit 1
fi

# Create/activate virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install git+https://github.com/openai/openai-agents-python.git@main

# Install optional dependencies for full test suite
echo "🧪 Installing test dependencies..."
pip install pytest-timeout pytest-xdist

# Verify installation
echo "✅ Verifying installation..."
python -c "from dotenv import load_dotenv; print('✓ dotenv')"
python -c "import pydantic; print('✓ pydantic')"
python -c "import pytest; print('✓ pytest')"

# Set up environment
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Remember to set OPENAI_API_KEY in .env"
    else
        echo "⚠️  No .env.example found. You'll need to create .env manually."
    fi
fi

# Run quick smoke test
echo "🚀 Running smoke test..."
pytest tests/test_memory_api.py::test_memory_init -v

echo ""
echo "✅ Development environment ready!"
echo ""
echo "Next steps:"
echo "  1. Set OPENAI_API_KEY in .env"
echo "  2. Run tests: pytest tests/"
echo "  3. Run with 6 workers: pytest tests/ -n 6"
echo "  4. Run specific suite: pytest tests/unit/"
echo ""
echo "To activate this environment in future sessions:"
echo "  source .venv/bin/activate"
