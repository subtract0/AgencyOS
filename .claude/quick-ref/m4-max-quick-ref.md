# M4 MAX Quick Reference - Local-First Agentic Development

**Hardware**: Mac Studio M4 MAX, 128GB RAM, 12-core CPU, 16-core GPU
**Last Updated**: 2025-10-31

---

## 🚀 Hardware Specs (Exact)

```
CPU:              12-core M4 MAX (8P + 4E) ← NOT 16!
GPU:              16-core integrated
Neural Engine:    16-core
Unified Memory:   128GB LPDDR5X
Memory Bandwidth: ~500 GB/s
```

## 💾 Memory Budget (128GB)

```
Component                    Allocation
─────────────────────────────────────────
macOS + Services             10GB
vcoder-120b Model            30GB (120B params)
KV Cache                     16GB
Test Workers (20x)           60GB (3GB each)
Development                  5GB
Safety Margin                7GB
─────────────────────────────────────────
TOTAL                        128GB ✅
```

## 🤖 Local Model

```bash
Model:     vcoder-120b-1.0-qx86-hi-mlx
Location:  http://192.168.0.2:1234 (LM Studio)
Cost:      $0/million tokens (100% local)
Quality:   GPT-4 class
Speed:     30-50 tokens/sec
```

## 🧪 Python Environment

```bash
# Python 3.12 exactly (required for datetime.UTC)
/opt/homebrew/bin/python3.12 --version
# Expected: Python 3.12.12

# Poetry with Python 3.12
/opt/homebrew/bin/poetry env use /opt/homebrew/bin/python3.12

# Verify
/opt/homebrew/bin/poetry run python --version
```

## 🏃 Quick Start Commands

```bash
# Navigate
cd /Users/am/Code/AgencyOS

# Run tests (20 workers)
/opt/homebrew/bin/poetry run pytest -n 20 tests/ -v

# Full test suite (must be 100%)
./run_tests.py --run-all

# Check local model
curl -s http://192.168.0.2:1234/v1/models | jq '.'

# Test local model
/opt/homebrew/bin/poetry run python test_vcoder.py
```

## 📊 Test Performance

```
Workers    Duration    Memory    Pass Rate
───────────────────────────────────────────
1          60 min      40GB      100%
20         <3 min      110GB     100% ✅
```

## 🏛️ Constitution (7 Articles)

```
I    Complete Context (retry 2x, 3x, 10x)
II   100% Verification (CRITICAL)
III  Automated Enforcement (local hooks)
IV   Continuous Learning (VectorStore)
V    Spec-Driven Development
VI   Red-Green-Refactor TDD (HIGHEST)
VII  Value-First Testing (delete score <10)
```

## 🤖 Autonomous Systems

```
autonomous_evolution.py     ✅ Running (12 cycles)
autonomous_worker_v2.py     ⏳ Verify
intelligence_monitor.py     ⏳ Verify
```

## 🔍 Health Checks

```bash
# Memory
vm_stat | awk '/Pages/ {sum+=$3} END {print sum*4096/1024^3 " GB used"}'

# Evolution system
ps aux | grep autonomous_evolution
cat logs/evolution_report_*.json | tail -n 1 | jq '.cycle'

# Test status
./run_tests.py --run-all 2>&1 | tail -5
```

## 📚 Documentation

```
M4_MAX_AUTONOMOUS_DEVELOPMENT_GUIDE.md    ← Complete guide
AUTONOMOUS_SYSTEMS_INVENTORY.md           ← System catalog
CODEBASE_MAP.md                           ← Project structure
constitution.md                           ← 7 Articles (READ THIS)
```

## ⚠️ Common Issues

### Tests fail with ImportError
```bash
# Fix: Use Python 3.12
/opt/homebrew/bin/poetry env use /opt/homebrew/bin/python3.12
```

### OOM during tests
```bash
# Fix: Reduce workers
pytest -n 10 tests/  # Instead of 20
```

### LM Studio unreachable
```bash
# Fix: Check connectivity
ping 192.168.0.2
curl http://192.168.0.2:1234/v1/models
```

---

**Quick Command Reference**:
- Tests: `./run_tests.py --run-all`
- Model: `curl http://192.168.0.2:1234/v1/models`
- Evolution: `ps aux | grep autonomous_evolution`
- Memory: `vm_stat | grep Pages`

**Target**: 1,762 tests, 100% pass, <3 min, $0 cost ✅
