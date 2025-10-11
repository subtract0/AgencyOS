#!/bin/bash
set -e

echo "🐳 Verifying Ollama Docker Setup..."
echo ""

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Install from https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running. Start Docker Desktop."
    exit 1
fi

echo "✅ Docker daemon running"

# Start Ollama service
echo "🚀 Starting Ollama service..."
cd /Users/am/Code/Agency
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for Ollama to be healthy (max 180s)..."
timeout=180
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker inspect --format='{{.State.Health.Status}}' agency-ollama 2>/dev/null | grep -q "healthy"; then
        echo "✅ Ollama service is healthy"
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "  Waiting... ${elapsed}s/${timeout}s"
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ Ollama failed to become healthy within ${timeout}s"
    echo "Logs:"
    docker-compose logs ollama
    exit 1
fi

# Initialize model using init script (Article I & II compliance)
echo "📥 Initializing model using init_ollama_model.sh..."
export OLLAMA_MODEL="hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0"
if bash scripts/init_ollama_model.sh; then
    echo "✅ Model initialization complete"
else
    echo "❌ Model initialization failed"
    exit 1
fi

# Verify memory usage
echo "📊 Memory usage:"
docker stats agency-ollama --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Test model inference
echo "🧪 Testing model inference..."
response=$(docker exec agency-ollama ollama run hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0 "Fix typo: def calcualte_total():" --verbose=false 2>&1 | head -5)
if [ -n "$response" ]; then
    echo "✅ Model inference working"
    echo "Sample response: $response"
else
    echo "❌ Model inference failed"
    exit 1
fi

echo ""
echo "🎉 Ollama Docker setup verified successfully!"
echo ""
echo "📝 Next steps:"
echo "  - Set USE_LOCAL_MODEL=true in .env"
echo "  - Set LOCAL_MODEL_NAME=hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0"
echo "  - Run: python run_tests.py --run-all"
echo ""
echo "🛑 To stop: docker-compose down"
echo "📊 Monitor: docker stats agency-ollama"
