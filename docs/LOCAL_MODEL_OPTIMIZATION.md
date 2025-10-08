# Local Model Optimization for Apple Silicon

**Target Hardware**: M4 Pro 48GB (Agency OS development machine)
**Goal**: Make Qwen3-Coder-30B work efficiently with Metal GPU acceleration

---

## 🎯 The Right Model: Official Ollama Qwen3-Coder

### Current Problem
- ❌ Using: `hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0` (32GB, timing out)
- Issue: Third-party HuggingFace GGUF, not optimized for Ollama

### Solution: Official Ollama Model
```bash
# Pull the official Qwen3-Coder 30B model
ollama pull qwen3-coder:30b

# Available quantizations:
# qwen3-coder:30b              (default Q4_K_M, ~19GB)
# qwen3-coder:30b-a3b-q4_K_M   (19GB, balanced quality/size)
# qwen3-coder:30b-a3b-q8_0     (32GB, higher quality)
```

**Key Advantage**: Official models are optimized for Ollama's runtime and Metal GPU

---

## 🚀 Apple Silicon Metal Optimization (2025 Features)

### 1. KV Cache Quantization (Game Changer)
**New in 2025**: Ollama supports KV cache quantization for massive memory savings

```bash
# Enable Q8_0 KV cache quantization (2x memory reduction)
export OLLAMA_KV_CACHE_TYPE="q8_0"

# Enable Flash Attention (faster inference)
export OLLAMA_FLASH_ATTENTION=1
```

**Impact**:
- **KV Cache Q8_0**: Halves context memory (F16 → Q8_0)
- **KV Cache Q4_0**: Cuts context memory to 1/3 (F16 → Q4_0)
- **Quality loss**: Minimal to none for Q8_0

### 2. Memory Budget with KV Cache Optimization

#### Without KV Cache Optimization (Current)
```
Model Weights (Q4_K_M):     19GB
KV Cache (F16, 256K ctx):   32GB  ← UNOPTIMIZED
Runtime Overhead:            2GB
─────────────────────────────────
Total:                      53GB  ⚠️ (tight on 48GB Mac)
```

#### With KV Cache Q8_0 (Recommended)
```
Model Weights (Q4_K_M):     19GB
KV Cache (Q8_0, 256K ctx):  16GB  ← 50% REDUCTION
Runtime Overhead:            2GB
─────────────────────────────────
Total:                      37GB  ✅ (safe on 48GB Mac)

Available for tests:        11GB → 3 workers (9GB) ✅
```

#### With KV Cache Q4_0 (Maximum Memory Savings)
```
Model Weights (Q4_K_M):     19GB
KV Cache (Q4_0, 256K ctx):  11GB  ← 66% REDUCTION
Runtime Overhead:            2GB
─────────────────────────────────
Total:                      32GB  ✅ (very safe on 48GB Mac)

Available for tests:        16GB → 5 workers (15GB) ✅
```

---

## 🎛️ Recommended Configuration

### Step 1: Pull Official Model
```bash
# Default Q4_K_M (19GB, good quality)
ollama pull qwen3-coder:30b

# OR: Higher quality Q8_0 (32GB, best quality)
ollama pull qwen3-coder:30b-a3b-q8_0
```

### Step 2: Configure Environment
```bash
# Add to ~/.zshrc or ~/.bash_profile
export OLLAMA_KV_CACHE_TYPE="q8_0"          # KV cache quantization (2x memory savings)
export OLLAMA_FLASH_ATTENTION=1             # Faster inference
export OLLAMA_NUM_GPU=1                     # Use Metal GPU
export OLLAMA_MAX_LOADED_MODELS=1           # Only keep one model in memory
```

### Step 3: Update Agency .env
```bash
# Use official model with optimizations
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen3-coder:30b            # Official Ollama model (19GB Q4_K_M)
LOCAL_MODEL_TEST_WORKERS=3                  # Safe with KV cache optimization

# Alternative: Higher quality
# LOCAL_MODEL_NAME=qwen3-coder:30b-a3b-q8_0  # 32GB Q8_0 (better quality)
```

### Step 4: Restart Ollama
```bash
# Stop Ollama
pkill ollama

# Start with new environment variables (they're in your shell profile now)
ollama serve &

# Test the model
ollama run qwen3-coder:30b "Fix typo: def calcualte_total():"
```

---

## 📊 Performance Comparison

| Configuration | Model Size | KV Cache | Total RAM | Test Workers | Status |
|--------------|------------|----------|-----------|--------------|--------|
| **Old (broken)** | 32GB (HF) | 32GB (F16) | 68GB | 10 | ❌ Kernel panic |
| **Q4_K_M + F16** | 19GB | 32GB | 53GB | 2 | ⚠️ Tight |
| **Q4_K_M + Q8_0** | 19GB | 16GB | 37GB | 3 | ✅ **Recommended** |
| **Q4_K_M + Q4_0** | 19GB | 11GB | 32GB | 5 | ✅ Maximum savings |
| **Q8_0 + Q8_0** | 32GB | 16GB | 50GB | 2 | ✅ Best quality |

---

## 🧠 Quantization Deep Dive

### Model Weight Quantization
- **Q8_0**: 8-bit, ~32GB, highest quality, slower inference
- **Q4_K_M**: 4-bit K-means medium, ~19GB, best balance (default)
- **Q4_K_S**: 4-bit K-means small, ~17GB, slightly lower quality

### KV Cache Quantization (Context Memory)
- **F16**: Full precision, highest quality, 2x memory vs Q8_0
- **Q8_0**: 8-bit, minimal quality loss, 2x memory savings ← **Recommended**
- **Q4_0**: 4-bit, slight quality loss, 3x memory savings

### Trade-offs
```
Quality:    Q8_0 weights + Q8_0 cache > Q4_K_M weights + Q8_0 cache > Q4_K_M + Q4_0 cache
Memory:     Q4_K_M + Q4_0 cache < Q4_K_M + Q8_0 cache < Q8_0 + Q8_0 cache
Speed:      Q4_K_M (fastest) > Q8_0 (slower due to larger model)
```

---

## 🔬 Testing Your Configuration

### 1. Check Memory Usage
```bash
# Monitor memory during model inference
ollama run qwen3-coder:30b "Write hello world in Python" &
sleep 2
ps aux | grep ollama
```

### 2. Verify KV Cache Settings
```bash
# Check environment
echo "KV Cache Type: $OLLAMA_KV_CACHE_TYPE"
echo "Flash Attention: $OLLAMA_FLASH_ATTENTION"

# Should output:
# KV Cache Type: q8_0
# Flash Attention: 1
```

### 3. Test Inference Speed
```bash
time ollama run qwen3-coder:30b "Fix this typo: def calcualte_sum(a, b): return a + b"

# Expected: 2-5 seconds for first token
# If >10 seconds: Something is wrong
```

### 4. Test with Agency Tests
```bash
# Run tests with local model active
USE_LOCAL_MODEL=true python run_tests.py --run-all

# Should show:
# 🧠 Local model active: using 3 test workers (memory-safe)
```

---

## 🐛 Troubleshooting

### Model Still Timing Out
```bash
# 1. Check Ollama version (need >=0.1.25 for KV cache)
ollama --version

# 2. Verify Metal GPU is being used
ollama show qwen3-coder:30b --verbose

# 3. Try without Flash Attention
unset OLLAMA_FLASH_ATTENTION
```

### Out of Memory Errors
```bash
# Option 1: Reduce KV cache to Q4_0
export OLLAMA_KV_CACHE_TYPE="q4_0"

# Option 2: Reduce context length
export OLLAMA_MAX_CONTEXT_LENGTH=32768  # Default is 256K

# Option 3: Use smaller model
ollama pull qwen3-coder:7b  # 7B model (~5GB)
```

### Slow Inference
```bash
# Check if GPU is actually being used
# Activity Monitor → GPU History → Should show high GPU usage during inference

# If CPU-only:
export OLLAMA_NUM_GPU=1
pkill ollama
ollama serve &
```

---

## 🎯 Final Recommended Setup (48GB M4 Mac)

```bash
# ~/.zshrc
export OLLAMA_KV_CACHE_TYPE="q8_0"
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_NUM_GPU=1
export OLLAMA_MAX_LOADED_MODELS=1

# .env
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen3-coder:30b            # Q4_K_M, 19GB
LOCAL_MODEL_TEST_WORKERS=3                  # Safe with KV optimization

# Install
ollama pull qwen3-coder:30b

# Test
ollama run qwen3-coder:30b "print('hello')"
```

**Memory Budget**: 19GB (model) + 16GB (KV Q8_0) + 2GB (runtime) + 9GB (3 test workers) = **46GB** ✅

**Performance**:
- 60% of tasks FREE (P3 local)
- 2-5s first token latency
- 30-50 tokens/sec throughput
- 256K context (repository-scale understanding)

---

## 📚 References

- [Ollama Qwen3-Coder Official](https://ollama.com/library/qwen3-coder)
- [KV Cache Quantization (2025)](https://smcleod.net/2024/12/bringing-k/v-context-quantisation-to-ollama/)
- [Apple Silicon Optimization Guide](https://markaicode.com/apple-metal-performance-shaders-m1-m2-ollama-optimization/)
- [Ollama Environment Variables](https://github.com/ollama/ollama/blob/main/docs/faq.md#how-do-i-configure-ollama-server)

---

**Status**: Ready for implementation
**Next Step**: Run installation script below
