# Performance Benchmark CI Job

**Status:** ✅ Implemented
**Created:** 2025-10-08
**Workflow:** `.github/workflows/benchmarks.yml`

---

## Overview

Dedicated CI job for performance benchmarks with **single-worker isolation** to ensure stable timing measurements without CPU contention.

### Why Separate Job?

**Problem:** Benchmarks with strict timing thresholds (e.g., `<200ms`) fail under parallel test execution due to CPU contention (14 workers competing).

**Solution:** Isolated benchmark job runs tests sequentially (`-n 0`) on dedicated runner for accurate performance measurements.

---

## Benchmark Tests

### Locations
```
tests/benchmarks/test_performance.py         # Core performance benchmarks
tests/fixtures/test_constitutional_test_agents.py  # Agent initialization benchmarks
tests/unit/shared/test_prompt_compression.py      # Prompt compression benchmarks
tests/unit/tools/test_tool_cache.py               # Tool cache benchmarks
```

### Marker
```python
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    def test_health_check_speed(self):
        """Health check must complete in <2 seconds."""
        # ... timing assertions
```

### Current Benchmarks

| Test | Threshold | Purpose |
|------|-----------|---------|
| `test_health_check_speed` | <2s | Fast health check validation |
| `test_constitutional_validator_speed` | <5s | Constitutional validation speed |
| `test_fast_test_tier_performance` | <30s | Fast test tier execution |
| `test_agent_context_initialization` | <200ms | Agent startup time |

---

## Workflow Configuration

### Triggers

1. **Push to main** - Track performance over time
2. **PR with benchmark changes** - Prevent regressions before merge
3. **Manual trigger** - On-demand benchmark runs
4. **Weekly schedule** - Sunday 3 AM UTC for trend analysis

### Key Features

**Single-Worker Isolation:**
```yaml
# No xdist parallelization for stable timing
python -m pytest tests/ -m benchmark -v
```

**Regression Detection:**
- Fails if any benchmark exceeds threshold
- Posts results as PR comment
- Stores baseline for historical comparison

**Artifact Retention:**
- Benchmark results stored for 90 days
- Baselines saved on main branch
- JSON format for programmatic analysis

---

## Usage

### Local Development

```bash
# Run all benchmarks (sequential, accurate timing)
pytest -m benchmark

# Run specific benchmark
pytest tests/benchmarks/test_performance.py::TestPerformanceBenchmarks::test_health_check_speed -v

# Collect benchmark tests without running
pytest -m benchmark --collect-only
```

### CI Integration

**Automatic:**
- Runs on main pushes
- Runs on PR when benchmark files change

**Manual:**
```bash
# Trigger via GitHub Actions UI
# Actions → Performance Benchmarks → Run workflow
```

---

## Adding New Benchmarks

### 1. Mark Test with Benchmark Decorator

```python
import pytest

@pytest.mark.benchmark
class TestMyBenchmarks:
    def test_my_performance(self):
        """My operation must complete in <1 second."""
        import time
        start = time.time()

        # ... operation to benchmark

        duration = time.time() - start
        assert duration < 1.0, f"Operation took {duration:.2f}s, must be <1s"
```

### 2. Verify Locally

```bash
# Test runs successfully
pytest tests/my_module/test_my_benchmarks.py -v

# Not included in standard test runs
pytest tests/  # Skips benchmarks by default
```

### 3. Commit and Push

```bash
git add tests/my_module/test_my_benchmarks.py
git commit -m "test: Add performance benchmark for MyOperation"
git push
```

Workflow runs automatically on PR.

---

## Results Interpretation

### PR Comment Format

```markdown
## 🔬 Performance Benchmark Results

**Status:** ✅ PASSED
**Total Tests:** 6
**Passed:** 6
**Failed:** 0
**Duration:** 12.34s

### ✅ All Benchmarks Passed

No performance regressions detected.
```

### Failure Example

```markdown
## 🔬 Performance Benchmark Results

**Status:** ⚠️ REGRESSION DETECTED
**Total Tests:** 6
**Passed:** 5
**Failed:** 1
**Duration:** 15.67s

### ⚠️ Failed Benchmarks

Performance regressions detected. Review timing thresholds in failing tests.

- `test_health_check_speed`: Expected <2s, took 3.45s
```

---

## Troubleshooting

### Benchmark Failing Locally but Passing in CI

**Cause:** Local CPU contention (other processes).

**Fix:** Close resource-heavy applications and retry:
```bash
pytest -m benchmark -v
```

### Benchmark Passing Locally but Failing in CI

**Cause:** CI runner slower than local machine OR threshold too strict.

**Fix:**
1. Review threshold (is <200ms realistic for CI?)
2. Adjust threshold or mark as `@pytest.mark.skip(reason="Too strict for CI")`

### Adding Benchmark to Existing Test

```python
# Before
def test_my_function():
    result = my_function()
    assert result == expected

# After
import pytest

@pytest.mark.benchmark
def test_my_function_performance():
    import time
    start = time.time()
    result = my_function()
    duration = time.time() - start

    assert result == expected  # Correctness
    assert duration < 0.5, f"Function took {duration:.2f}s, must be <0.5s"  # Performance
```

---

## Maintenance

### Baseline Updates

Baselines are stored on main branch in `.benchmarks/` directory:

```bash
.benchmarks/
├── baseline-20251008-030000.json
├── baseline-20251015-030000.json
└── baseline-20251022-030000.json
```

**Retention:** Manual cleanup (no automated expiry).

### Trend Analysis

Use `scripts/analyze_benchmark_results.py` to compare baselines:

```bash
python scripts/analyze_benchmark_results.py .benchmarks/baseline-20251008-030000.json .benchmarks/baseline-20251015-030000.json
```

---

## Constitutional Compliance

### Article I: Complete Context Before Action
✅ Benchmarks run with full isolation (no partial results from CPU contention)

### Article II: 100% Verification and Stability
✅ Regression detection prevents performance degradation from merging

### Article III: Automated Merge Enforcement
✅ Failed benchmarks block PR merge (quality gate)

### Article IV: Continuous Learning
✅ 90-day retention enables pattern recognition and optimization opportunities

### Article V: Spec-Driven Development
✅ Benchmark thresholds documented in test docstrings

---

## Future Enhancements

1. **Trend Visualization**
   - Grafana dashboard for benchmark history
   - Alert on >20% degradation over 4 weeks

2. **Comparative Analysis**
   - Compare PR benchmarks against main baseline
   - Show % difference in PR comment

3. **Automated Threshold Tuning**
   - Adjust thresholds based on CI runner performance
   - P50/P95/P99 percentiles over 30 days

4. **Benchmark Categories**
   - `@pytest.mark.benchmark_critical` (must pass)
   - `@pytest.mark.benchmark_monitor` (warn only)

---

**Related Files:**
- Workflow: `.github/workflows/benchmarks.yml`
- Config: `pytest.ini` (line 13: `benchmark` marker)
- Tests: `tests/benchmarks/test_performance.py`
- Analysis: `scripts/analyze_benchmark_results.py`

**Next Steps:**
- Run workflow manually to verify: Actions → Performance Benchmarks
- Monitor first main push for baseline creation
- Review weekly runs for performance trends
