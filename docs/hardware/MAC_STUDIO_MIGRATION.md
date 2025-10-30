# Mac Studio M4 MAX Migration Guide

## Overview

This guide provides clean migration steps from M4 Pro MacBook Pro (48GB) to Mac Studio M4 MAX (128GB) for optimal Agency OS performance.

## Current State (M4 Pro 48GB - October 2025)

### Limitations
- **Memory constraints**: 48GB causes test suite to run with reduced parallelism
- **Test execution**: Currently using `-n 3` workers to avoid memory exhaustion
- **Full test suite**: ~25-30 minutes (limited parallelism)
- **Segmentation faults**: Occasional Python crashes under memory pressure (fixed by reducing workers)

### Working Configuration
```ini
# pytest.ini (current M4 Pro config)
[tool:pytest]
addopts = -n 3 --dist loadgroup
```

## Mac Studio M4 MAX Specs (Target)

### Hardware
- **CPU**: M4 MAX (16-core)
- **Memory**: 128GB unified memory
- **Storage**: 2TB+ SSD recommended

### Expected Performance Improvements
- **Test parallelism**: Increase from 3 → 20 workers
- **Full test suite**: <15 minutes (vs 25-30 min on M4 Pro)
- **Memory headroom**: 128GB allows aggressive parallelism + local models
- **Ollama Q8_0**: Run 30B+ models without swapping

## Clean Migration Steps

### DO NOT Use Migration Assistant
Migration Assistant can transfer corrupted virtualenvs, cached packages, and stale configurations. Clean setup is faster and more reliable.

### Step 1: System Setup (30 min)

1. **Install Homebrew**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3.12**
   ```bash
   brew install python@3.12
   python3.12 --version  # Verify: Python 3.12.11+
   ```

3. **Install uv (Python package manager)**
   ```bash
   brew install uv
   uv --version  # Verify: 0.5.0+
   ```

4. **Install Git & Essential Tools**
   ```bash
   brew install git gh tree jq
   gh auth login  # GitHub CLI authentication
   ```

### Step 2: Clone Repository (5 min)

```bash
cd ~/Code  # Or your preferred dev directory
git clone <repository-url>
cd Agency
git checkout feat/memory-learning-phase1  # Or your working branch
```

### Step 3: Virtual Environment Setup (10 min)

```bash
# Create fresh virtualenv
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies via uv (faster than pip)
uv pip install -e .

# Verify installation
python --version  # Should show Python 3.12.11
which python  # Should point to .venv/bin/python
```

### Step 4: Ollama Q8_0 Setup (20 min)

```bash
# Install Ollama
brew install ollama

# Pull Qwen3-Coder Q8_0 (30B params, 32GB)
ollama run hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0

# Verify
ollama list
# Expected output:
# NAME                                                              ID              SIZE
# hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0     112536ee2004    32 GB

# Test local model
ollama run hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0 \
  "Fix typo: def calcualte_total():"
```

### Step 5: pytest.ini Optimization (2 min)

**Update pytest.ini for 128GB:**
```ini
# pytest.ini (Mac Studio M4 MAX config)
[tool:pytest]
addopts = -n 20 --dist loadgroup --maxfail=10
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

**Rationale**:
- **-n 20**: Aggressive parallelism (128GB can handle it)
- **--dist loadgroup**: Balance test distribution across workers
- **--maxfail=10**: Stop after 10 failures (faster feedback)

### Step 6: Environment Variables (3 min)

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env for Mac Studio
nano .env
```

**Recommended .env settings**:
```bash
# Core
OPENAI_API_KEY=<your_key>
AGENCY_MODEL=gpt-5

# Local Model (leveraging 128GB)
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0
LOCAL_MODEL_TEST_WORKERS=20  # Max parallelism for 128GB

# Memory & Learning (MANDATORY)
USE_ENHANCED_MEMORY=true
FRESH_USE_FIRESTORE=false

# Testing
FORCE_RUN_ALL_TESTS=1  # Enable full 6,246 test suite
```

### Step 7: Validate Installation (15 min)

```bash
# 1. Quick unit tests (should be <2 min)
python -m pytest tests/unit/ -v

# 2. Full test suite (should be <15 min on Mac Studio)
python run_tests.py --run-all

# Expected output:
# ====== 6246 passed, 7 skipped, 1 xfailed in XXX seconds ======
#
# Test categories:
# - Unit tests: 1,500+
# - Integration tests: 1,200+
# - E2E tests: 500+
# - Foundation automation: 300+
# - Performance benchmarks: 200+
```

## Performance Comparison

| Metric | M4 Pro 48GB | Mac Studio M4 MAX 128GB | Improvement |
|--------|-------------|-------------------------|-------------|
| Test workers | 3 | 20 | 6.7x |
| Full test suite | 25-30 min | <15 min | ~2x faster |
| Ollama model size | 19GB max | 70B+ models | 3.5x+ |
| Memory headroom | Tight | Abundant | - |
| Segfaults | Occasional | None | Stable |

## Cost Savings with Local Model (128GB)

**M4 Pro 48GB** (limited parallelism):
- **60% P3 tasks**: $0 (local Qwen3-Coder 30B Q8_0)
- **30% P2 tasks**: $1.50/1M tokens (gpt-4o)
- **10% P1 tasks**: $4.00/1M tokens (gpt-5)
- **Total**: ~$1.6K/month (96% reduction vs all-cloud)

**Mac Studio M4 MAX 128GB** (aggressive parallelism + larger models):
- **70% P3 tasks**: $0 (local Qwen3-Coder 70B Q4 or 30B Q8_0)
- **20% P2 tasks**: $1.50/1M tokens (gpt-4o)
- **10% P1 tasks**: $4.00/1M tokens (gpt-5)
- **Total**: ~$1.2K/month (97% reduction, 25% faster execution)

## Troubleshooting

### Issue: Tests still running slowly
**Cause**: pytest.ini not updated
**Fix**: Verify `addopts = -n 20` in pytest.ini

### Issue: Ollama model not loading
**Cause**: Insufficient VRAM allocation
**Fix**: Mac Studio has 128GB unified memory, no VRAM limits

### Issue: Import errors for `peft`, `transformers`
**Cause**: Optional dependencies not installed
**Fix**: These are only needed for QLoRA training (future Phase 4)
```bash
pip install peft transformers torch
```

## Next Steps After Migration

1. **Run full benchmark suite**: `python -m pytest tests/benchmark/ -v`
2. **Verify Article II compliance**: All 6,246 tests should pass
3. **Test local model cost savings**: Track P3 task routing
4. **Update CLAUDE.md**: Document Mac Studio as primary dev environment

## Constitutional Compliance

- **Article I**: Complete context (128GB enables full test suite in <15 min)
- **Article II**: 100% verification (all 6,246 tests must pass)
- **Article III**: Automated enforcement (no manual overrides)
- **Article IV**: VectorStore learning (USE_ENHANCED_MEMORY=true)
- **Article V**: Spec-driven (this migration guide is the spec)

## Revision History

- **2025-10-30**: Initial version (M4 Pro → Mac Studio migration)
- **Source**: Phase 1a test suite recovery work

---

**Estimated Total Migration Time**: 1.5-2 hours (vs 4-6 hours with Migration Assistant debugging)
