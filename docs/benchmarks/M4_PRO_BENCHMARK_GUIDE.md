# M4 Pro Local Execution Benchmark Guide

**Version**: 1.0
**Target Hardware**: Apple M4 Pro (48GB RAM)
**Purpose**: Validate local Ollama execution performance across all 10 Agency agents

## Overview

This guide provides instructions for running two benchmark suites designed to measure M4 Pro performance with local Ollama models (qwen2.5-coder series).

### Benchmark Suites

1. **10-Task Agent Coverage** (`benchmark_10task_m4pro.py`)
   - Tests ONE task per agent type (10 total)
   - Target: <5 minutes, <2GB memory, 100% local, $0.00 cost
   - Use case: Quick validation after code changes

2. **100-Task Stress Test** (`benchmark_100task_stress.py`)
   - Tests 10 tasks per agent type (100 total)
   - Target: <60 minutes, <500MB memory growth, >99% local, <$1.00 cost
   - Use case: Sustained performance validation, escalation pattern analysis

## Prerequisites

### System Requirements

- **Hardware**: Apple M4 Pro with 48GB RAM (minimum 32GB)
- **OS**: macOS 15.0+ (Darwin 25.0.0+)
- **Python**: 3.11+
- **Disk**: 50GB free space (for Ollama models)

### Software Setup

1. **Install Ollama**:
   ```bash
   # Install Ollama for macOS
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull Required Models**:
   ```bash
   # Pull all qwen2.5-coder variants used by Agency
   ollama pull qwen2.5-coder:1.5b    # SUMMARY agent
   ollama pull qwen2.5-coder:14b     # PLANNER, AUDITOR, QUALITY_ENFORCER, LEARNING, CHIEF_ARCHITECT, MERGER
   ollama pull qwen2.5-coder:32b     # CODER, TEST_GENERATOR, TOOLSMITH
   ```

3. **Verify Ollama is Running**:
   ```bash
   ollama list  # Should show downloaded models
   curl http://localhost:11434/api/tags  # Should return JSON
   ```

4. **Install Python Dependencies**:
   ```bash
   cd /Users/am/Code/Agency
   pip install -e .
   pip install psutil  # For memory profiling
   ```

5. **Set Environment Variables**:
   ```bash
   # Create .env file if not exists
   cat > .env <<EOF
   # Core
   AGENCY_MODEL=ollama/qwen2.5-coder:14b

   # Force local execution (no cloud fallback during benchmarks)
   USE_LOCAL_MODELS=true

   # Memory & Learning (MANDATORY)
   USE_ENHANCED_MEMORY=true

   # Cost tracking
   OPENAI_API_KEY=sk-dummy-for-local  # Not used for local, but required by code
   EOF
   ```

## Running Benchmarks

### 10-Task Agent Coverage Benchmark

**Target Completion Time**: 3-5 minutes

#### Basic Execution

```bash
python scripts/benchmark_10task_m4pro.py
```

#### With Custom Output Directory

```bash
python scripts/benchmark_10task_m4pro.py --output-dir ./my_benchmark_results
```

#### Dry Run (No Actual Execution)

```bash
python scripts/benchmark_10task_m4pro.py --dry-run
```

#### Expected Console Output

```
================================================================================
10-TASK AGENT COVERAGE BENCHMARK (M4 Pro)
================================================================================

📅 Start Time: 2025-10-07T14:30:00.123456
🖥️  Platform: M4 Pro
🎯 Target: 100% local execution, <5min, <2GB, $0.00
📋 Tasks: 10
🔬 Mode: LIVE EXECUTION

================================================================================
TASK 1/10: CODER
================================================================================
✓ CODER: 12.45s (local)

================================================================================
TASK 2/10: TEST_GENERATOR
================================================================================
✓ TEST_GENERATOR: 15.67s (local)

... (8 more tasks) ...

================================================================================
BENCHMARK SUMMARY
================================================================================

📊 Execution Metrics:
   Total Duration: 142.34s
   Average Duration: 14.23s per task
   Peak Memory: 1847.2 MB
   Total Cost: $0.00

✅ Success Metrics:
   Completion Rate: 100.0%
   Success Rate: 100.0%

🖥️  Tier Distribution:
   Local Execution: 10/10
   Cloud Escalation: 0/10
   Escalation Rate: 0.0%

🎯 Target Achievement (M4 Pro):
   ✓ 100% Local
   ✓ <5min Total
   ✓ <2GB Memory
   ✓ $0.00 Cost

================================================================================

📁 Full results: benchmark_results/benchmark_10task_20251007_143000.json
```

### 100-Task Stress Test Benchmark

**Target Completion Time**: 45-60 minutes

#### Basic Execution

```bash
python scripts/benchmark_100task_stress.py
```

#### With Progress Monitoring

```bash
# Terminal 1: Run benchmark
python scripts/benchmark_100task_stress.py

# Terminal 2: Monitor memory
watch -n 5 'ps aux | grep python | grep benchmark'

# Terminal 3: Monitor Ollama
watch -n 5 'curl -s http://localhost:11434/api/ps'
```

#### Expected Console Output

```
================================================================================
100-TASK STRESS TEST BENCHMARK (M4 Pro)
================================================================================

📅 Start Time: 2025-10-07T15:00:00.123456
🖥️  Platform: M4 Pro
🎯 Target: >99% local, <60min, <500MB growth, <$1.00
📋 Tasks: 100 (10 per agent type)
🔬 Mode: LIVE EXECUTION

[████████████████████████████████████████] 100.0% (100/100) | Current: SUMMARY

================================================================================
STRESS TEST SUMMARY (100 TASKS)
================================================================================

⏱️  Execution Metrics:
   Total Duration: 2847.56s
   Average Duration: 28.48s per task (47.5min total)
   Total Cost: $0.00

💾 Memory Stability:
   Baseline Memory: 1654.3 MB
   Peak Memory: 2089.7 MB
   Memory Growth: 435.4 MB
   Growth Rate: 26.3%

✅ Success Metrics:
   Success Rate: 100.0%
   Successful Tasks: 100/100
   Failed Tasks: 0/100
   Tasks with Retries: 2
   Total Retries: 2

🖥️  Tier Distribution:
   Local Execution: 100/100 (100.0%)
   Cloud Escalation: 0/100
   Escalation Rate: 0.0%

📊 Escalation Timeline:
   Early Tasks (1-50): 0 escalations
   Late Tasks (51-100): 0 escalations

🎯 Target Achievement (M4 Pro):
   ✓ >99% Local
   ✓ <60min Total
   ✓ <500MB Growth
   ✓ <$1.00 Cost

================================================================================

📁 Full results: benchmark_results/benchmark_stress_100task_20251007_150000.json
```

## Analyzing Results

### Results File Structure

Benchmarks generate JSON files in `benchmark_results/` with the following structure:

#### 10-Task Results

```json
[
  {
    "task_id": "task_001",
    "agent_type": "CODER",
    "description": "Write a prime number checker function...",
    "expected_tier": "LOCAL",
    "actual_tier": "local",
    "duration_seconds": 12.45,
    "memory_before_mb": 1678.2,
    "memory_after_mb": 1734.8,
    "success": true,
    "error_message": null,
    "cost_usd": 0.0,
    "timestamp": "2025-10-07T14:30:12.123456"
  },
  ...
]
```

#### 100-Task Results

```json
[
  {
    "task_id": "stress_001",
    "task_number": 1,
    "agent_type": "CODER",
    "description": "Write factorial function with type hints",
    "expected_tier": "LOCAL",
    "actual_tier": "local",
    "duration_seconds": 11.23,
    "memory_mb": 1654.3,
    "success": true,
    "error_message": null,
    "cost_usd": 0.0,
    "timestamp": "2025-10-07T15:01:23.456789",
    "retry_count": 0
  },
  ...
]
```

### Key Metrics to Monitor

1. **Local Execution Rate**:
   - 10-task: Must be 100% (0 cloud escalations)
   - 100-task: Must be >99% (<1 cloud escalation)

2. **Duration**:
   - 10-task: <5 minutes (300s)
   - 100-task: <60 minutes (3600s)

3. **Memory Stability**:
   - 10-task: Peak <2GB (2048 MB)
   - 100-task: Growth <500MB from baseline

4. **Cost**:
   - 10-task: Exactly $0.00
   - 100-task: <$1.00 (allows minimal escalation)

### Analyzing Results with Python

```python
import json
from pathlib import Path

# Load results
results_file = Path("benchmark_results/benchmark_10task_20251007_143000.json")
with open(results_file) as f:
    results = json.load(f)

# Calculate metrics
total_duration = sum(r["duration_seconds"] for r in results)
avg_duration = total_duration / len(results)
local_count = sum(1 for r in results if r["actual_tier"] in ["local", "LOCAL", "local_plus"])
escalation_rate = 1 - (local_count / len(results))

print(f"Total Duration: {total_duration:.2f}s ({total_duration / 60:.1f}min)")
print(f"Average Duration: {avg_duration:.2f}s per task")
print(f"Local Execution: {local_count}/{len(results)} ({local_count / len(results) * 100:.1f}%)")
print(f"Escalation Rate: {escalation_rate * 100:.1f}%")

# Find slowest tasks
sorted_results = sorted(results, key=lambda r: r["duration_seconds"], reverse=True)
print("\nTop 5 Slowest Tasks:")
for i, r in enumerate(sorted_results[:5], 1):
    print(f"{i}. {r['agent_type']}: {r['duration_seconds']:.2f}s - {r['description'][:50]}...")
```

## Troubleshooting

### Issue: Benchmarks Fail with "Ollama not running"

**Solution**:
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# If not running, start Ollama
ollama serve

# Verify models are available
ollama list
```

### Issue: High Memory Usage (>3GB)

**Cause**: Multiple Ollama models loaded simultaneously

**Solution**:
```bash
# Clear Ollama cache
ollama ps  # List running models
ollama stop <model_name>  # Stop unused models

# Restart Ollama with memory limits
OLLAMA_MAX_LOADED_MODELS=2 ollama serve
```

### Issue: Slow Execution (>10min for 10-task)

**Potential Causes**:
1. Background processes consuming CPU
2. Disk I/O bottleneck
3. Thermal throttling

**Solution**:
```bash
# Check CPU usage
top -o cpu

# Check thermal state
sudo powermetrics --samplers smc | grep -i temp

# Free up resources
# Close Xcode, Docker, browsers with many tabs
```

### Issue: Escalations to Cloud (actual_tier=CLOUD)

**Cause**: Local model failed or timed out

**Solution**:
1. Check Ollama logs: `tail -f ~/.ollama/logs/server.log`
2. Increase retry timeout in benchmark script
3. Verify model is fully downloaded: `ollama list`
4. Try smaller context window

### Issue: Test Failures

**Run test suite**:
```bash
pytest tests/test_benchmarks.py -v
```

**Common failures**:
- `test_benchmark_has_ten_tasks`: Missing tasks in BENCHMARK_TASKS
- `test_benchmark_covers_all_agent_types`: Agent type mismatch
- `test_memory_profiler_tracks_usage`: psutil not installed

## Constitutional Compliance

Both benchmarks enforce constitutional requirements:

### Article I: Complete Context Before Action
- Retry logic: LOCAL → LOCAL_PLUS → CLOUD (max 2 retries)
- No partial results (all 10/100 tasks must complete)

### Article II: 100% Verification
- Track completion rate (must be 100%)
- Track success rate (target 100%, minimum 95%)

### Article IV: Learning Integration
- Store successful patterns in AgentContext
- Store escalation patterns for analysis
- Enable cross-session learning

**Validation**:
```bash
# Verify Article IV compliance
python -c "
from shared.agent_context import create_agent_context
ctx = create_agent_context(session_id='test')
results = ctx.search_memories(['benchmark', 'learning'])
print(f'Stored learnings: {len(results)}')
"
```

## Continuous Monitoring

### Run Benchmarks Regularly

**Daily**:
```bash
# Quick sanity check (10-task)
python scripts/benchmark_10task_m4pro.py
```

**Weekly**:
```bash
# Full stress test (100-task)
python scripts/benchmark_100task_stress.py
```

**After Code Changes**:
```bash
# Run both benchmarks
python scripts/benchmark_10task_m4pro.py && \
python scripts/benchmark_100task_stress.py
```

### Automated Benchmarking

**Cron Job** (daily at 2 AM):
```cron
0 2 * * * cd /Users/am/Code/Agency && python scripts/benchmark_10task_m4pro.py --output-dir ~/benchmark_history/$(date +\%Y\%m\%d)
```

**Git Hook** (pre-push):
```bash
#!/bin/bash
# .git/hooks/pre-push

echo "Running pre-push benchmark..."
python scripts/benchmark_10task_m4pro.py --output-dir /tmp/pre_push_bench

if [ $? -ne 0 ]; then
    echo "❌ Benchmark failed! Push aborted."
    exit 1
fi

echo "✓ Benchmark passed. Proceeding with push."
exit 0
```

## Next Steps

After running benchmarks:

1. **Analyze Escalation Patterns**:
   - Identify agents that frequently escalate to CLOUD
   - Optimize those agents for local execution

2. **Memory Profiling**:
   - Use `memory_profiler` for detailed analysis
   - Identify memory leaks or inefficient operations

3. **Performance Tuning**:
   - Adjust Ollama model parameters (`temperature`, `num_ctx`)
   - Experiment with different qwen2.5-coder variants

4. **Compare Results**:
   - Track metrics over time
   - Compare before/after code changes
   - Share results with team for collaboration

## Support

**Issues**:
- Open GitHub issue with benchmark results attached
- Include: OS version, Python version, Ollama version, model sizes

**Questions**:
- Slack: #agency-benchmarks channel
- Email: benchmarks@agency.dev

---

**Last Updated**: 2025-10-07
**Maintained By**: TestGeneratorAgent
**Version**: 1.0
