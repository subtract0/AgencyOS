#!/bin/bash
# Setup script for optimized local model on Apple Silicon
# Run: bash scripts/setup_local_model.sh

set -e

echo "🚀 Agency OS - Local Model Optimization Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Detect shell
SHELL_RC="$HOME/.zshrc"
if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

echo "📋 Step 1: Check Ollama installation"
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Installing..."
    brew install ollama
    echo "✅ Ollama installed"
else
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -1)
    echo "✅ Ollama found: $OLLAMA_VERSION"
fi

echo ""
echo "📋 Step 2: Configure environment variables"

# Check if already configured
if grep -q "OLLAMA_KV_CACHE_TYPE" "$SHELL_RC"; then
    echo "⚠️  Environment variables already configured in $SHELL_RC"
    echo "   Skipping..."
else
    echo "   Adding optimizations to $SHELL_RC"
    cat >> "$SHELL_RC" << 'EOF'

# Ollama Apple Silicon Optimizations (Agency OS)
export OLLAMA_KV_CACHE_TYPE="q8_0"          # KV cache quantization (2x memory savings)
export OLLAMA_FLASH_ATTENTION=1             # Faster inference
export OLLAMA_NUM_GPU=1                     # Use Metal GPU
export OLLAMA_MAX_LOADED_MODELS=1           # Only keep one model in memory
EOF
    echo "✅ Environment variables added"
fi

echo ""
echo "📋 Step 3: Load environment variables"
source "$SHELL_RC"
export OLLAMA_KV_CACHE_TYPE="q8_0"
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_NUM_GPU=1
export OLLAMA_MAX_LOADED_MODELS=1

echo "   KV Cache Type: $OLLAMA_KV_CACHE_TYPE"
echo "   Flash Attention: $OLLAMA_FLASH_ATTENTION"
echo "   GPU: $OLLAMA_NUM_GPU"

echo ""
echo "📋 Step 4: Restart Ollama with optimizations"
echo "   Stopping Ollama..."
pkill ollama || true
sleep 2

echo "   Starting Ollama with Metal GPU optimizations..."
nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 3

if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama running with optimizations"
else
    echo "❌ Failed to start Ollama"
    exit 1
fi

echo ""
echo "📋 Step 5: Pull official Qwen3-Coder model"
echo "   This will download ~19GB (Q4_K_M quantization)"
echo ""

# Check if already downloaded
if ollama list | grep -q "qwen3-coder:30b"; then
    echo "✅ Model already downloaded"
else
    echo "   Downloading... (this may take 5-10 minutes)"
    ollama pull qwen3-coder:30b
    echo "✅ Model downloaded"
fi

echo ""
echo "📋 Step 6: Test model inference"
echo "   Running test prompt..."
TEST_OUTPUT=$(ollama run qwen3-coder:30b "Say 'hello world' in one word" 2>&1 | head -5)
if [ $? -eq 0 ]; then
    echo "✅ Model responds:"
    echo "   $TEST_OUTPUT"
else
    echo "❌ Model test failed"
    echo "   Check /tmp/ollama.log for details"
    exit 1
fi

echo ""
echo "📋 Step 7: Update Agency .env configuration"
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  No .env file found, copying from .env.example"
    cp .env.example .env
fi

# Update or add local model configuration
if grep -q "LOCAL_MODEL_NAME" "$ENV_FILE"; then
    echo "   Updating LOCAL_MODEL_NAME in .env"
    sed -i.bak 's|LOCAL_MODEL_NAME=.*|LOCAL_MODEL_NAME=qwen3-coder:30b|' "$ENV_FILE"
else
    echo "   Adding LOCAL_MODEL_NAME to .env"
    echo "LOCAL_MODEL_NAME=qwen3-coder:30b" >> "$ENV_FILE"
fi

if grep -q "USE_LOCAL_MODEL" "$ENV_FILE"; then
    sed -i.bak 's|USE_LOCAL_MODEL=.*|USE_LOCAL_MODEL=true|' "$ENV_FILE"
else
    echo "USE_LOCAL_MODEL=true" >> "$ENV_FILE"
fi

if grep -q "LOCAL_MODEL_TEST_WORKERS" "$ENV_FILE"; then
    sed -i.bak 's|LOCAL_MODEL_TEST_WORKERS=.*|LOCAL_MODEL_TEST_WORKERS=3|' "$ENV_FILE"
else
    echo "LOCAL_MODEL_TEST_WORKERS=3" >> "$ENV_FILE"
fi

rm -f .env.bak

echo "✅ .env updated"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Memory Budget (48GB Mac):"
echo "   Model (Q4_K_M):      19GB"
echo "   KV Cache (Q8_0):     16GB (optimized)"
echo "   Runtime:              2GB"
echo "   Test workers (3):     9GB"
echo "   ────────────────────────"
echo "   Total:               46GB ✅"
echo ""
echo "🚀 Next Steps:"
echo "   1. Restart your terminal to load environment variables"
echo "   2. Run: python run_tests.py --run-all"
echo "   3. Expected output: '🧠 Local model active: using 3 test workers'"
echo ""
echo "📚 Documentation:"
echo "   See docs/LOCAL_MODEL_OPTIMIZATION.md for details"
echo ""
