# 🚀 AgencyOS M4 MAX Setup Guide

**Status**: ✅ Environment ready for local LLM execution

## ✅ What's Done

### Installed Components
- ✅ Python 3.13.9 (via `brew install python@3.13`)
- ✅ Poetry 2.2.1 (via `brew install poetry`)
- ✅ Ollama 0.12.7 (via `brew install ollama`)
- ✅ All Python dependencies (from `requirements.txt`)
- ✅ Git repository initialized at `/Users/am/Code/AgencyOS`

### Environment Configuration
- **Python**: `/opt/homebrew/bin/python3.13`
- **Poetry**: `/opt/homebrew/bin/poetry`
- **Ollama**: Running as background service via `brew services`
- **Ollama API**: http://localhost:11434

## 🎯 Next Steps: Download Local LLM Model

### Option 1: Qwen3-Coder 30B (RECOMMENDED for M4 Max)
**Specifications**:
- Size: ~20GB (Q4_K_M quantization)
- Download time: 10-15 minutes on M4 Max
- Memory usage: ~19GB + 16GB KV cache = 35GB total
- Performance: Excellent for code generation

**Pull the model**:
```bash
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 \
/opt/homebrew/opt/ollama/bin/ollama pull qwen3-coder:30b
```

### Option 2: Mistral 7B (Lightweight, Fast)
```bash
/opt/homebrew/opt/ollama/bin/ollama pull mistral:latest
```

### Option 3: Llama2 70B (Large, Very Capable)
```bash
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 \
/opt/homebrew/opt/ollama/bin/ollama pull llama2:70b
```

## 🔧 Configuration Files

### `.env` Configuration
Located at `/Users/am/Code/AgencyOS/.env`:
- OpenAI API keys configured
- Firebase/Firestore paths configured
- Memory settings configured

### Local LLM Configuration
Add to `.env` for local execution:
```bash
# Use local Ollama instead of OpenAI
OLLAMA_API_URL=http://localhost:11434
LOCAL_MODEL_NAME=qwen3-coder:30b
USE_LOCAL_MODEL=true
```

## 📚 Running the System

### Option A: With OpenAI (Current)
```bash
cd /Users/am/Code/AgencyOS
/opt/homebrew/bin/poetry run python -m agency
```

### Option B: With Local LLM (After Model Download)
```bash
cd /Users/am/Code/AgencyOS
export USE_LOCAL_MODEL=true
export OLLAMA_API_URL=http://localhost:11434
/opt/homebrew/bin/poetry run python -m agency
```

## ✅ Verification

### Test Setup
```bash
cd /Users/am/Code/AgencyOS
/opt/homebrew/bin/poetry run pytest tests/ -v --tb=short -x
```

### Quick Ollama Test
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test with a model (after pulling)
/opt/homebrew/opt/ollama/bin/ollama run qwen3-coder:30b "Hello, what is 2+2?"
```

## 🛠️ Poetry Commands

### Available Commands
```bash
# Run tests (all)
/opt/homebrew/bin/poetry run pytest tests/

# Run tests (unit only)
/opt/homebrew/bin/poetry run pytest -m "not integration and not e2e"

# Run specific test file
/opt/homebrew/bin/poetry run pytest tests/test_agency.py -v

# Type checking
/opt/homebrew/bin/poetry run mypy shared/

# Code formatting
/opt/homebrew/bin/poetry run ruff format .

# Linting
/opt/homebrew/bin/poetry run ruff check .
```

## 🚀 Full Development Workflow

### 1. Start Ollama Service
```bash
brew services start ollama
```

### 2. Download Model (First Time Only)
```bash
OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 \
/opt/homebrew/opt/ollama/bin/ollama pull qwen3-coder:30b
```

### 3. Verify Everything Works
```bash
cd /Users/am/Code/AgencyOS

# Quick sanity check
/opt/homebrew/bin/poetry run pytest tests/unit/ -v -x --tb=short

# Full test suite
/opt/homebrew/bin/poetry run pytest tests/ -v
```

### 4. Run Agency
```bash
/opt/homebrew/bin/poetry run python -m agency
```

## 💾 Hardware Specifications

**M4 Max Mac Studio**:
- CPU: 12-core M4 Max
- Memory: 128GB shared unified RAM
- Bandwidth: 273 GB/s
- Storage: Sufficient for local models

**Memory Budget**:
- System + Services: ~8GB
- Available for workloads: 120GB
- Safe budget for operations: 100GB+

**Ollama Optimization**:
- Flash attention: `OLLAMA_FLASH_ATTENTION=1`
- KV cache quantization: `OLLAMA_KV_CACHE_TYPE=q8_0`
- Model quantization: Q4_K_M (optimal balance)

## 📖 Documentation

- **Architecture**: `docs/architecture/overview.md`
- **Setup**: `docs/getting-started/README.md`
- **Local Models**: `docs/setup/APPLE_SILICON_AI_SETUP.md`
- **Trinity Protocol**: `trinity_protocol/README.md`

## ⚠️ Known Issues & Fixes

### ImportError: No module named 'X'
**Fix**: Re-run dependencies installation
```bash
cd /Users/am/Code/AgencyOS
/opt/homebrew/bin/poetry run pip install -r requirements.txt
```

### Ollama Connection Failed
**Fix**: Check if service is running
```bash
brew services list | grep ollama
# If not running:
brew services start ollama
```

### Tests Fail with Memory Errors
**Fix**: Reduce parallel test workers in `pytest.ini`
```ini
addopts = [..., "-n", "2"]  # Reduce from 3 to 2 workers
```

## 🎯 Next Session

When you return, simply:
1. `cd /Users/am/Code/AgencyOS`
2. `/opt/homebrew/bin/poetry run pytest tests/` to verify
3. Run your development workflow

---

**Setup Date**: 2025-10-30
**Python**: 3.13.9
**Poetry**: 2.2.1
**Ollama**: 0.12.7
**Status**: ✅ Ready for development
