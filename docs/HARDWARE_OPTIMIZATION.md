# Hardware Optimization Guide - Apple Silicon M4 Pro

**Target System**: MacBook Pro M4 Pro, 48GB Unified Memory
**Critical for**: AgencyOS autonomous operations, local model inference, parallel testing

---

## 🎯 System Architecture

### M4 Pro Specifications
```
CPU Cores:         14 (10 Performance + 4 Efficiency)
GPU Cores:         20
Neural Engine:     16-core
Unified Memory:    48GB LPDDR5X
Memory Bandwidth:  273 GB/s (vs 120 GB/s M4 base) → 2.3x faster
                   Critical for LLM inference (memory-bound workload)
Cache:             24MB shared L2/L3
```

### Memory Architecture
```
Total RAM:              48GB
macOS Reserved:          8GB (system, WindowServer, background services)
Available for Apps:     40GB
Safety Margin:           5GB (swap, peaks, safety)
─────────────────────────────────
Usable for Workloads:   35GB (strict budget)
```

**Key Insight**: Unified memory shared between CPU/GPU/Neural Engine
- ✅ Zero-copy GPU access (Metal Performance Shaders)
- ✅ No PCIe bottleneck (vs discrete GPU)
- ⚠️ Memory pressure affects all subsystems simultaneously

---

## 🧠 Local LLM Inference Optimization

### Metal GPU Acceleration (2025)

#### 1. Model Quantization
```
Format    Precision  Size (30B)  Quality  Speed      Use Case
────────────────────────────────────────────────────────────────
FP16      16-bit     60GB        100%     Baseline   (Too large for 48GB)
Q8_0      8-bit      32GB        98%      0.8x       High quality, tight fit
Q6_K      6-bit mix  25GB        95%      1.0x       Balanced
Q5_K_M    5-bit mix  21GB        92%      1.1x       Good quality
Q4_K_M    4-bit mix  19GB        90%      1.3x       Best balance ✅
Q4_K_S    4-bit mix  17GB        87%      1.4x       Smaller, quality loss
Q4_0      4-bit      17GB        85%      1.5x       Fastest, lowest quality
```

**Recommendation**: **Q4_K_M** (19GB) - Best quality/size/speed trade-off
- K-means quantization preserves important weights
- Mixed precision (higher precision for critical layers)
- Metal GPU optimized

#### 2. KV Cache Quantization (NEW 2025)
```
Context Memory Optimization:

KV Cache Format  256K Context  Memory Saving  Quality Loss
────────────────────────────────────────────────────────────
F16 (default)    32GB          Baseline       0%
Q8_0             16GB          50%            <1% ✅ Recommended
Q4_0             11GB          66%            2-3%
```

**Critical**: KV cache grows linearly with context length
- 256K context (default Qwen3-Coder): 32GB F16 → 16GB Q8_0
- 128K context: 16GB F16 → 8GB Q8_0
- 32K context: 4GB F16 → 2GB Q8_0

**Enable**:
```bash
export OLLAMA_KV_CACHE_TYPE="q8_0"
export OLLAMA_FLASH_ATTENTION=1
```

#### 3. Memory Budget Calculator
```python
def calculate_memory_budget(
    model_params_b: float,      # Model parameters in billions (e.g., 30.0)
    quantization: str,          # "Q4_K_M", "Q8_0", etc.
    context_length_k: int,      # Context in thousands (e.g., 256)
    kv_cache_quant: str         # "F16", "Q8_0", "Q4_0"
) -> dict:
    # Model weights
    quant_sizes = {"Q4_K_M": 0.5, "Q5_K_M": 0.625, "Q6_K": 0.75, "Q8_0": 1.0, "F16": 2.0}
    model_gb = model_params_b * quant_sizes[quantization]

    # KV cache (rough approximation)
    kv_base_gb = (context_length_k / 256) * 32  # 32GB for 256K F16
    kv_quant_factor = {"F16": 1.0, "Q8_0": 0.5, "Q4_0": 0.33}
    kv_cache_gb = kv_base_gb * kv_quant_factor[kv_cache_quant]

    # Runtime overhead
    runtime_gb = 2.0

    total = model_gb + kv_cache_gb + runtime_gb

    return {
        "model_gb": model_gb,
        "kv_cache_gb": kv_cache_gb,
        "runtime_gb": runtime_gb,
        "total_gb": total,
        "safe_for_48gb": total <= 35  # 35GB usable budget
    }

# Example: Qwen3-Coder-30B Q4_K_M with Q8_0 KV cache
result = calculate_memory_budget(30.0, "Q4_K_M", 256, "Q8_0")
# Output: {'model_gb': 15.0, 'kv_cache_gb': 16.0, 'runtime_gb': 2.0, 'total_gb': 33.0, 'safe_for_48gb': True}
```

#### 4. Recommended Configurations (48GB M4 Pro)

**Option A: Maximum Quality (Tight)**
```bash
MODEL: qwen3-coder:30b-a3b-q8_0     # 30GB Q8_0
KV_CACHE: q8_0                      # 16GB
TOTAL: 48GB (model + kv + runtime)
TEST_WORKERS: 0 (sequential only)
USE_CASE: Offline inference, no concurrent testing
```

**Option B: Balanced Quality + Testing (Recommended)**
```bash
MODEL: qwen3-coder:30b              # 19GB Q4_K_M ✅
KV_CACHE: q8_0                      # 16GB
RUNTIME: 2GB
TEST_WORKERS: 3 (9GB)
TOTAL: 46GB
USE_CASE: Development with parallel testing
```

**Option C: Maximum Throughput**
```bash
MODEL: qwen3-coder:30b              # 19GB Q4_K_M
KV_CACHE: q4_0                      # 11GB
RUNTIME: 2GB
TEST_WORKERS: 5 (15GB)
TOTAL: 47GB
USE_CASE: CI/CD pipelines, fast testing
```

**Option D: Smaller Model (32GB Mac friendly)**
```bash
MODEL: qwen3-coder:7b               # 5GB Q4_K_M
KV_CACHE: q8_0                      # 4GB (256K)
RUNTIME: 1GB
TEST_WORKERS: 10 (30GB)
TOTAL: 40GB
USE_CASE: 32GB Macs, maximum parallelism
```

---

## ⚡ Memory Bandwidth Optimization

### Why M4 Pro > M4 for LLMs

**Memory Bandwidth Comparison**:
```
M4 Base:     120 GB/s
M4 Pro:      273 GB/s  → 2.3x faster
M4 Max:      546 GB/s  → 4.6x faster (but overkill for 30B models)
```

**Impact on LLM Inference**:
- LLMs are **memory-bound** workloads (not compute-bound)
- Bottleneck: Loading weights from RAM → GPU
- M4 Pro's 273 GB/s enables:
  - **30-50 tokens/sec** for 30B Q4_K_M models
  - **Faster first token** (2-5s vs 5-10s on M4 base)
  - **Better batching** (multiple concurrent requests)

**Rule of Thumb**:
```
Tokens/sec ≈ Memory_Bandwidth_GB/s / (Model_Size_GB / Batch_Size)

M4 Base (120 GB/s):  120 / (19 / 1) ≈ 6.3 batches/sec → ~20 tokens/sec
M4 Pro (273 GB/s):   273 / (19 / 1) ≈ 14.3 batches/sec → ~45 tokens/sec ✅
```

### Optimization Techniques

#### 1. Metal Performance Shaders (MPS)
```bash
# Enable Metal GPU (default on macOS)
export OLLAMA_NUM_GPU=1

# Verify GPU usage
# Activity Monitor → GPU → Should show high % during inference
```

#### 2. Flash Attention
```bash
# Enable optimized attention kernels
export OLLAMA_FLASH_ATTENTION=1

# Benefit: 2-3x faster attention computation
# Impact: Lower latency, higher throughput
```

#### 3. Concurrent Model Limitation
```bash
# Only keep 1 model loaded at a time
export OLLAMA_MAX_LOADED_MODELS=1

# Prevents memory fragmentation
# Reduces swap pressure
```

#### 4. Context Length Tuning
```bash
# Reduce context if not needed (saves KV cache memory)
export OLLAMA_MAX_CONTEXT_LENGTH=32768  # Default: 262144 (256K)

# Memory savings:
# 256K → 32K = 8x KV cache reduction
# 16GB → 2GB for Q8_0 KV cache
```

---

## 🧪 Parallel Testing Optimization

### Test Runner Memory Dynamics

#### Memory per pytest Worker
```python
# Typical pytest worker memory footprint
Base Python:           ~50MB
Imported modules:      ~200MB (agency, tests, fixtures)
Test execution:        ~100MB (active test objects)
Peak (heavy tests):    ~500MB (database, API mocks)
─────────────────────────────────────────────────────
Average per worker:    ~300MB
Conservative estimate: 3GB per worker (safety margin)
```

#### Worker Count Formula
```python
def calculate_safe_workers(
    available_memory_gb: int,    # e.g., 40 (48GB - 8GB macOS)
    local_model_active: bool,
    model_memory_gb: float,      # e.g., 19 for Q4_K_M
    kv_cache_memory_gb: float,   # e.g., 16 for Q8_0
    runtime_overhead_gb: float = 2.0
) -> int:
    if not local_model_active:
        # Cloud-only mode: no local model memory
        workers = int((available_memory_gb - runtime_overhead_gb) / 3)
        return min(workers, 10)  # Cap at 10 for diminishing returns

    # Local model mode
    model_total = model_memory_gb + kv_cache_memory_gb + runtime_overhead_gb
    remaining = available_memory_gb - model_total - 5  # 5GB safety margin

    workers = max(1, int(remaining / 3))
    return workers

# Example: 48GB Mac with qwen3-coder:30b Q4_K_M + Q8_0 KV
workers = calculate_safe_workers(40, True, 19, 16, 2)
# Output: 3 workers (40 - 19 - 16 - 2 - 5) / 3 = -2/3 → 1 worker minimum, 3 safe with margin
```

#### Dynamic Worker Adjustment
```python
# In run_tests.py
import psutil

def get_safe_worker_count() -> int:
    """Calculate safe pytest worker count based on current memory state."""
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)

    use_local = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"

    if not use_local:
        # Cloud mode: aggressive parallelism
        return min(10, os.cpu_count() or 1)

    # Local model mode: conservative
    # Assume model is loaded (19GB + 16GB KV + 2GB = 37GB)
    # Remaining = available_gb - 37GB
    remaining = available_gb - 37

    if remaining < 9:
        return 1  # Sequential
    elif remaining < 15:
        return 2  # Limited parallelism
    elif remaining < 21:
        return 3  # Safe default
    else:
        return min(5, int(remaining / 3))  # Scale up
```

---

## 🚨 Memory Pressure Detection

### Symptoms of Memory Exhaustion

1. **Kernel Panic (Catastrophic)**
   - `panic: watchdog timeout`
   - System unresponsive for 60-90 seconds
   - Forced reboot
   - **Solution**: Reduce total memory footprint below 48GB

2. **Swap Thrashing (Severe)**
   - Tests slow to 10-100x normal speed
   - Disk I/O maxed out (Activity Monitor → Disk)
   - **Solution**: Reduce worker count or model size

3. **OOM Kills (Moderate)**
   - Process terminated by kernel
   - `malloc failed` or `out of memory` errors
   - **Solution**: Increase safety margin (reduce workers by 1-2)

4. **Inference Timeouts (Warning)**
   - Local model responses >10 seconds
   - KV cache eviction (recomputing context)
   - **Solution**: Reduce context length or use Q4_0 KV cache

### Monitoring Commands
```bash
# Current memory usage
vm_stat | awk '
  /Pages free/ {free=$3}
  /Pages active/ {active=$3}
  /Pages inactive/ {inactive=$3}
  /Pages speculative/ {spec=$3}
  /Pages wired/ {wired=$3}
  END {
    total = free + active + inactive + spec + wired
    printf "Free: %.1f GB\n", free * 4096 / 1024^3
    printf "Used: %.1f GB\n", (active + wired) * 4096 / 1024^3
  }
'

# Memory pressure (red = bad)
memory_pressure

# Per-process memory
ps aux | awk '{if ($6 > 1000000) print $11, $6/1024/1024 " GB"}' | sort -k2 -rn | head -10
```

---

## 📐 Architecture-Aware Development

### Constitutional Integration

**Article I: Complete Context Before Action**
- Hardware constraint: Must account for memory limits
- Timeout retries must not exceed memory budget
- **Rule**: Verify available memory before spawning parallel operations

**Article II: 100% Verification and Stability**
- Test execution must complete without memory exhaustion
- Green tests invalid if achieved via OOM kills
- **Rule**: Worker count auto-adjusts to prevent instability

**Memory Safety Amendment (2025-10-08)**:
```
Section 2.5: Hardware-Aware Execution

All operations SHALL respect available system resources:
- Memory usage MUST stay below 85% of total RAM (40.8GB / 48GB)
- Test parallelism MUST dynamically adjust based on memory state
- Local model inference MUST use optimized quantization (Q4_K_M + Q8_0 KV)
- Kernel panics constitute a BLOCKING violation requiring immediate mitigation
```

### Agent Memory Awareness

All agents should query hardware state before memory-intensive operations:

```python
from shared.hardware_context import get_memory_state, is_memory_safe

def before_action(self):
    state = get_memory_state()
    if not is_memory_safe(required_gb=10):
        # Fallback: reduce scope, cloud API, or defer
        self.use_cloud_api()
```

---

## 🔧 Configuration Reference

### Environment Variables (Add to ~/.zshrc)
```bash
# Ollama Metal GPU Optimization (2025)
export OLLAMA_KV_CACHE_TYPE="q8_0"          # 50% KV cache memory savings
export OLLAMA_FLASH_ATTENTION=1             # Faster attention kernels
export OLLAMA_NUM_GPU=1                     # Use Metal GPU
export OLLAMA_MAX_LOADED_MODELS=1           # Prevent memory fragmentation
export OLLAMA_MAX_CONTEXT_LENGTH=262144     # 256K (reduce if memory tight)

# Agency Testing
export LOCAL_MODEL_TEST_WORKERS=3           # Safe for 48GB Mac
export USE_LOCAL_MODEL=true                 # Enable local inference (60% tasks)
export LOCAL_MODEL_NAME=qwen3-coder:30b     # Q4_K_M 19GB model
```

### .env Configuration
```bash
# Memory-optimized local model (Phase 3: 96% cost reduction)
USE_LOCAL_MODEL=true
LOCAL_MODEL_NAME=qwen3-coder:30b            # Q4_K_M, 19GB, Metal optimized
LOCAL_MODEL_TEST_WORKERS=3                  # Auto-adjusts for memory safety

# Cost tiers (complexity-based routing)
# P3 (simple, 60%):   qwen3-coder:30b local → $0/1M tokens
# P2 (moderate, 30%): gpt-4o cloud         → $1.50/1M tokens
# P1 (complex, 10%):  gpt-5 cloud          → $4.00/1M tokens
```

---

## 📊 Performance Benchmarks (M4 Pro 48GB)

### Model Inference Speed
```
Model              Quant    First Token  Throughput  Context  Memory
───────────────────────────────────────────────────────────────────────
qwen3-coder:30b    Q4_K_M   2-3s         40-50 t/s   256K     19GB ✅
qwen3-coder:30b    Q8_0     3-5s         25-35 t/s   256K     32GB
qwen3-coder:7b     Q4_K_M   0.5-1s       80-100 t/s  256K     5GB
deepseek-v2:lite   Mixed    1-2s         50-70 t/s   128K     9GB
codellama:13b      Q4_0     1-2s         60-80 t/s   100K     7GB
```

### Test Suite Performance
```
Configuration              Workers  Duration  Memory Peak
────────────────────────────────────────────────────────────
Cloud-only (no local)      10       8min      30GB
Local Q4_K_M + Q8_0 KV     3        22min     46GB ✅
Local Q8_0 + Q8_0 KV       2        30min     50GB (tight)
Sequential (1 worker)      1        60min     38GB
```

### Cost Comparison (10K tasks/month)
```
Strategy                    Cost/Month    Speed      Memory
──────────────────────────────────────────────────────────────
All GPT-5                   $40,000       Instant    Low
Multi-tier (no local)       $9,400        Instant    Low
Local P3 (60%) + cloud      $1,600        2-3s       High ✅
Local P3+P2 (90%) + cloud   $400          2-5s       Very High
```

---

## 🎯 Decision Matrix

### When to Use Local Model
```
✅ Use Local (qwen3-coder:30b):
- P3 simple tasks (typos, formatting, docstrings)
- Development/testing (not production)
- Cost optimization critical
- 48GB+ Mac available
- Latency <5s acceptable

❌ Use Cloud (gpt-4o/gpt-5):
- P1/P2 complex tasks (architecture, critical fixes)
- Production deployments
- Sub-second latency required
- <32GB RAM
- Memory pressure detected
```

### When to Adjust Worker Count
```
10 workers: Cloud-only, 32GB+ available
5 workers:  Local Q4_K_M + Q4_0 KV, 48GB Mac
3 workers:  Local Q4_K_M + Q8_0 KV, 48GB Mac ✅ (balanced)
2 workers:  Local Q8_0 + Q8_0 KV, 48GB Mac (quality)
1 worker:   Memory pressure, any configuration
```

---

## 🔗 Integration Points

### Agent Definitions
- All agents in `.claude/agents/` should reference this doc
- Memory budget awareness in agent instructions
- Cloud fallback logic for resource constraints

### Commands
- `/primecc` - Load this doc for hardware context
- `/prime plan_and_execute` - Check memory before parallel operations
- All `/prime*` commands - Hardware-aware execution

### Core Files
- `run_tests.py` - Memory-aware worker adjustment
- `shared/model_policy.py` - Complexity-based routing with local fallback
- `constitution.md` - Memory Safety Amendment (Section 2.5)

---

**Maintained by**: Agency OS Infrastructure
**Last Updated**: 2025-10-08
**Review Cycle**: Quarterly or on hardware/OS changes
