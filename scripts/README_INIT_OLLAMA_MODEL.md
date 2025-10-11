# Ollama Model Initialization Script

## Overview

`scripts/init_ollama_model.sh` is a production-ready script for initializing Ollama models in Docker containers with full constitutional compliance (Articles I & II, ADR-023).

## Features

- ✅ **Article I Compliance**: Exponential backoff retry (max 10 retries, 2x timeout increase)
- ✅ **Article II Compliance**: 100% verification (service health + model availability)
- ✅ **Idempotent**: No-op if model already exists (safe to run multiple times)
- ✅ **Configurable**: Model name via argument or environment variable
- ✅ **Memory-Aware**: Supports dev (30B), standard (7B), and CI (1.5B) models
- ✅ **Error Handling**: Clear error messages with debug logs on failure
- ✅ **Progress Feedback**: Download time estimates and real-time status

## Usage

### Basic Usage (Default Model)
```bash
# Uses qwen3-coder:30b by default (19GB)
bash scripts/init_ollama_model.sh
```

### Custom Model via Argument
```bash
# Use smaller model for CI/testing
bash scripts/init_ollama_model.sh qwen2.5-coder:1.5b

# Use larger Q8_0 model for higher quality
bash scripts/init_ollama_model.sh hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0
```

### Custom Model via Environment Variable
```bash
# Set model via environment
export OLLAMA_MODEL="qwen3-coder:7b"
bash scripts/init_ollama_model.sh
```

### Custom Container Name
```bash
# Use non-default container name
export OLLAMA_CONTAINER_NAME="my-ollama-container"
bash scripts/init_ollama_model.sh
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_CONTAINER_NAME` | `agency-ollama` | Docker container name |
| `OLLAMA_MODEL` | `qwen3-coder:30b` | Model to pull (if not provided as argument) |
| `MAX_RETRIES` | `10` | Max retry attempts for service readiness |
| `INITIAL_WAIT` | `5` | Initial wait time in seconds (doubles each retry) |
| `HEALTH_CHECK_URL` | `http://localhost:11434/api/tags` | Ollama health check endpoint |

### Retry Logic (Article I Compliance)

The script implements exponential backoff for service readiness:

1. **Attempt 1**: Wait 5 seconds
2. **Attempt 2**: Wait 10 seconds
3. **Attempt 3**: Wait 20 seconds
4. **Attempt 4**: Wait 40 seconds
5. **Attempt 5**: Wait 80 seconds
... up to 10 attempts

**Total max wait**: ~5 + 10 + 20 + 40 + 80 + 160 + 320 + 640 + 1280 + 2560 = ~5115 seconds (~85 minutes)

## Model Size Estimates

| Model | Size | Download Time (estimate) |
|-------|------|--------------------------|
| `qwen3-coder:30b` (Q4_K_M) | 19GB | 10-30 minutes |
| `qwen3-coder:30b` (Q8_0) | 32GB | 15-45 minutes |
| `qwen3-coder:7b` (Q4_K_M) | 5-7GB | 3-10 minutes |
| `qwen2.5-coder:1.5b` | 900MB-1.5GB | 1-5 minutes |

## Integration

### Docker Compose Entrypoint

To run automatically when container starts, add as init container:

```yaml
services:
  ollama-init:
    image: ollama/ollama:latest
    depends_on:
      ollama:
        condition: service_healthy
    volumes:
      - ./scripts:/scripts
    environment:
      - OLLAMA_MODEL=qwen3-coder:30b
    command: ["/scripts/init_ollama_model.sh"]
```

### GitHub Actions CI/CD

```yaml
- name: Initialize Ollama Model
  run: |
    docker-compose up -d
    export OLLAMA_MODEL="qwen2.5-coder:1.5b"  # Small CI model
    bash scripts/init_ollama_model.sh
  timeout-minutes: 15
```

### Programmatic Usage (Python)

```python
import subprocess
import os

def init_ollama_model(model_name: str = "qwen3-coder:30b") -> bool:
    """Initialize Ollama model with constitutional compliance."""
    result = subprocess.run(
        ["bash", "scripts/init_ollama_model.sh", model_name],
        env={**os.environ, "OLLAMA_MODEL": model_name},
        capture_output=True,
        text=True,
        timeout=3600  # 1 hour max
    )
    return result.returncode == 0
```

## Verification (Article II)

The script performs 4 levels of verification:

1. **Container Running**: `docker ps | grep agency-ollama`
2. **Service Health**: `curl -f http://localhost:11434/api/tags`
3. **Model in List**: `docker exec agency-ollama ollama list | grep <model>`
4. **Model in API**: `curl http://localhost:11434/api/tags | grep <model>`

## Error Handling

### Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| `0` | Success (model initialized or already cached) |
| `1` | Container not running after max retries |
| `1` | Service failed to become healthy |
| `$pull_exit_code` | Model pull failed (Ollama exit code) |
| `1` | Model verification failed |

### Debug Logs

On failure, the script automatically displays:
- Last 50 lines of container logs
- Docker container status
- Available models list
- Health check endpoint response

## Testing

### Unit Tests

```bash
# Run all tests for init script
python -m pytest tests/test_init_ollama_model.py -v

# Test specific functionality
python -m pytest tests/test_init_ollama_model.py::TestInitOllamaModelScript::test_exponential_backoff_configuration -v
```

### Integration Tests

```bash
# Test with real Docker container (requires Docker)
python -m pytest tests/test_init_ollama_model.py::TestInitOllamaModelIntegration -v --tb=short
```

### Manual Testing

```bash
# Test with non-existent container (should fail gracefully)
export OLLAMA_CONTAINER_NAME="test-nonexistent"
bash scripts/init_ollama_model.sh

# Test idempotency (run twice, second should be no-op)
bash scripts/init_ollama_model.sh
bash scripts/init_ollama_model.sh  # Should exit quickly with "already available"

# Test with small CI model
bash scripts/init_ollama_model.sh qwen2.5-coder:1.5b
```

## Constitutional Compliance

### Article I: Complete Context Before Action

- ✅ Exponential backoff retry (10 attempts, 2x timeout)
- ✅ Never proceeds without healthy service
- ✅ Service readiness verified before model pull
- ✅ Model availability verified after pull

### Article II: 100% Verification and Stability

- ✅ 100% model availability verification (4 checks)
- ✅ Exit on any verification failure
- ✅ No partial success (all-or-nothing)
- ✅ Tests validate all verification paths (22 tests, 100% pass)

### ADR-023: Memory-Aware Execution

- ✅ Supports multiple model sizes (30B, 7B, 1.5B)
- ✅ Size estimates for memory planning
- ✅ Configurable via environment (dev vs CI)
- ✅ Safe defaults (qwen3-coder:30b for 48GB Macs)

## Troubleshooting

### Issue: "Container not running"

**Cause**: Ollama container not started

**Solution**:
```bash
docker-compose up -d
bash scripts/init_ollama_model.sh
```

### Issue: "Service failed to become healthy"

**Cause**: Ollama service startup failed

**Solution**:
```bash
# Check logs
docker logs agency-ollama

# Restart container
docker-compose restart ollama

# Wait longer (increase start period)
export MAX_RETRIES=15
bash scripts/init_ollama_model.sh
```

### Issue: "Model pull failed"

**Cause**: Network issues, disk space, or invalid model name

**Solution**:
```bash
# Check disk space (need 20-32GB free)
df -h

# Check network connectivity
curl -I https://registry.ollama.ai

# Verify model name
docker exec agency-ollama ollama list

# Try smaller model
bash scripts/init_ollama_model.sh qwen3-coder:7b
```

### Issue: Script hangs indefinitely

**Cause**: Health check never passes

**Solution**:
```bash
# Kill script (Ctrl+C)
# Check health manually
curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama

# Reduce retries for faster failure
export MAX_RETRIES=3
bash scripts/init_ollama_model.sh
```

## Related Documentation

- **Spec**: `specs/spec-023-ollama-docker-integration.md`
- **ADR**: `docs/adr/ADR-023-memory-aware-execution.md`
- **Docker Compose**: `docker-compose.yml`
- **Verification Script**: `scripts/verify_ollama_docker.sh`
- **Health Check Tool**: `tools/ollama_health_check.py`
- **Memory-Aware Runner**: `tools/memory_aware_test_runner.py`

## Version History

- **v1.0.0** (2025-10-11): Initial release with Articles I & II compliance
  - Exponential backoff retry logic
  - 100% verification (4 checks)
  - Idempotent operation
  - Configurable model selection
  - 22 tests (100% pass)
