#!/bin/bash
# Model Initialization Script for Ollama Docker Container
# Purpose: Wait for Ollama service readiness and pull required model
# Usage: bash scripts/init_ollama_model.sh [model_name]
#
# Constitutional Compliance:
# - Article I: Complete context before action (exponential backoff retry)
# - Article II: 100% verification (validates model availability)
# - ADR-023: Memory-aware execution (supports both dev and CI models)

set -e

# Configuration
CONTAINER_NAME="${OLLAMA_CONTAINER_NAME:-agency-ollama}"
DEFAULT_MODEL="${OLLAMA_MODEL:-qwen3-coder:30b}"
MODEL_NAME="${1:-$DEFAULT_MODEL}"
MAX_RETRIES="${OLLAMA_MAX_RETRIES:-10}"
INITIAL_WAIT="${OLLAMA_INITIAL_WAIT:-5}"
HEALTH_CHECK_URL="http://localhost:11434/api/tags"

echo "🚀 Ollama Model Initialization Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Container: $CONTAINER_NAME"
echo "Model: $MODEL_NAME"
echo ""

# Article I: Complete context before action - wait for Ollama service readiness
echo "📋 Step 1: Wait for Ollama service to be ready (Article I: exponential backoff)"
wait_seconds=$INITIAL_WAIT
retry_count=0

while [ $retry_count -lt $MAX_RETRIES ]; do
    echo "  Attempt $((retry_count + 1))/$MAX_RETRIES (waiting ${wait_seconds}s)..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "  ⚠️  Container $CONTAINER_NAME not running"
        if [ $retry_count -lt $((MAX_RETRIES - 1)) ]; then
            sleep $wait_seconds
            wait_seconds=$((wait_seconds * 2))  # Exponential backoff (Article I)
            retry_count=$((retry_count + 1))
            continue
        else
            echo "❌ FAILED: Container never started after $MAX_RETRIES retries"
            exit 1
        fi
    fi

    # Check if service responds to health check
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo "✅ Ollama service is ready"
        break
    else
        if [ $retry_count -lt $((MAX_RETRIES - 1)) ]; then
            echo "  ⏳ Service not ready yet, waiting ${wait_seconds}s..."
            sleep $wait_seconds
            wait_seconds=$((wait_seconds * 2))  # Article I: exponential backoff
            retry_count=$((retry_count + 1))
        else
            echo "❌ FAILED: Service failed to become healthy after $MAX_RETRIES retries"
            echo "Debug info:"
            docker logs "$CONTAINER_NAME" --tail 50 2>&1 || echo "Could not fetch logs"
            exit 1
        fi
    fi
done

echo ""
echo "📋 Step 2: Check if model already exists (idempotent operation)"

# Query existing models via Ollama CLI
if docker exec "$CONTAINER_NAME" ollama list 2>/dev/null | grep -q "$MODEL_NAME"; then
    echo "✅ Model '$MODEL_NAME' already available (no-op)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 Initialization Complete (model cached)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi

echo "⏳ Model not found, pulling..."
echo ""

# Article II: 100% verification - pull model with error handling
echo "📋 Step 3: Pull model (Article II: full verification required)"
echo "  Model: $MODEL_NAME"

# Estimate download time based on model size
case "$MODEL_NAME" in
    *"30b"*|*"30B"*|*"Q8_0"*)
        echo "  Estimated size: 19-32GB (may take 10-30 minutes)"
        ;;
    *"7b"*|*"7B"*)
        echo "  Estimated size: 5-7GB (may take 3-10 minutes)"
        ;;
    *"1.5b"*|*"1.5B"*)
        echo "  Estimated size: 900MB-1.5GB (may take 1-5 minutes)"
        ;;
    *)
        echo "  Estimated size: Unknown (timing varies)"
        ;;
esac

echo ""
echo "  Starting pull..."

# Execute model pull with real-time output
if docker exec "$CONTAINER_NAME" ollama pull "$MODEL_NAME"; then
    echo "✅ Model pull succeeded"
else
    pull_exit_code=$?
    echo "❌ FAILED: Model pull failed with exit code $pull_exit_code"
    echo "Debug info:"
    docker logs "$CONTAINER_NAME" --tail 50 2>&1 || echo "Could not fetch logs"
    exit $pull_exit_code
fi

echo ""
echo "📋 Step 4: Verify model availability (Article II: 100% verification)"

# Verify model is now in the list
if docker exec "$CONTAINER_NAME" ollama list 2>/dev/null | grep -q "$MODEL_NAME"; then
    echo "✅ Model verified in Ollama list"
else
    echo "❌ FAILED: Model pull succeeded but not found in ollama list"
    echo "Available models:"
    docker exec "$CONTAINER_NAME" ollama list 2>&1 || echo "Could not list models"
    exit 1
fi

# Verify model via health check endpoint (REST API validation)
if curl -f -s "$HEALTH_CHECK_URL" | grep -q "$MODEL_NAME"; then
    echo "✅ Model verified via health check endpoint"
else
    echo "⚠️  WARNING: Model not visible via health check API (may need cache refresh)"
    echo "  This is non-critical - model is available via Ollama CLI"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Initialization Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Summary:"
echo "  Container: $CONTAINER_NAME"
echo "  Model: $MODEL_NAME"
echo "  Status: Ready for inference"
echo ""
echo "🧪 Test inference:"
echo "  docker exec $CONTAINER_NAME ollama run $MODEL_NAME 'print(\"hello\")'"
echo ""
echo "📚 Documentation:"
echo "  See docs/LOCAL_MODEL_OPTIMIZATION.md for usage details"
echo ""
