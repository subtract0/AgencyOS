#!/bin/bash
# AgencyOS Development Environment Starter for M4 Max

set -e

PYTHON=/opt/homebrew/bin/python3.13
POETRY=/opt/homebrew/bin/poetry
OLLAMA=/opt/homebrew/opt/ollama/bin/ollama

echo "🚀 Starting AgencyOS Development Environment"
echo "============================================"

# 1. Ensure Ollama is running
echo "1️⃣ Checking Ollama service..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "   ⚙️  Starting Ollama..."
    brew services start ollama
    sleep 2
else
    echo "   ✅ Ollama already running"
fi

# 2. Check Poetry environment
echo "2️⃣ Checking Poetry environment..."
cd "$(dirname "$0")"
$POETRY env info > /dev/null 2>&1 && echo "   ✅ Poetry environment ready" || echo "   ⚠️  Setting up Poetry..."

# 3. Quick dependency check
echo "3️⃣ Verifying dependencies..."
$PYTHON -c "import dotenv; print('   ✅ Dependencies OK')" 2>/dev/null || {
    echo "   ⚠️  Installing dependencies..."
    $POETRY run pip install -r requirements.txt > /dev/null 2>&1
    echo "   ✅ Dependencies installed"
}

# 4. List available Ollama models
echo "4️⃣ Available Ollama models:"
curl -s http://localhost:11434/api/tags | $PYTHON -m json.tool 2>/dev/null | grep -i "name" | head -10

echo ""
echo "✅ Environment Ready!"
echo ""
echo "Quick commands:"
echo "  📚 Run tests:     $POETRY run pytest tests/ -v"
echo "  🔍 Type check:    $POETRY run mypy shared/"
echo "  🎨 Format code:   $POETRY run ruff format ."
echo "  ✨ Lint:          $POETRY run ruff check ."
echo "  🚀 Run agency:    $POETRY run python -m agency"
echo ""
echo "📖 Full setup guide: README.md SETUP_M4_MAX.md"
echo ""
