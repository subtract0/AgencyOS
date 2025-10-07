# M4 Pro Benchmark Quick Reference

**Last Updated**: 2025-10-07

## Quick Start

### 10-Task Benchmark (5 minutes)
```bash
python scripts/benchmark_10task_m4pro.py
```

### 100-Task Stress Test (60 minutes)
```bash
python scripts/benchmark_100task_stress.py
```

## Success Criteria

### 10-Task Targets
- ✓ Duration: <5 minutes
- ✓ Memory: <2GB peak
- ✓ Local: 100% (0 cloud escalations)
- ✓ Cost: $0.00

### 100-Task Targets
- ✓ Duration: <60 minutes
- ✓ Memory: <500MB growth
- ✓ Local: >99% (<1 cloud escalation)
- ✓ Cost: <$1.00

## Files Created

1. **Test Validators**: `/Users/am/Code/Agency/tests/test_benchmarks.py`
   - 30+ test cases for benchmark validation
   - TDD-first approach (tests before implementation)
   - Constitutional compliance checks

2. **10-Task Benchmark**: `/Users/am/Code/Agency/scripts/benchmark_10task_m4pro.py`
   - One task per agent type (10 total)
   - Tracks: duration, memory, cost, tier usage
   - Outputs: JSON results + console summary

3. **100-Task Stress Test**: `/Users/am/Code/Agency/scripts/benchmark_100task_stress.py`
   - Ten tasks per agent type (100 total)
   - Tracks: memory stability, escalation patterns
   - Outputs: JSON results + detailed metrics

4. **User Guide**: `/Users/am/Code/Agency/docs/benchmarks/M4_PRO_BENCHMARK_GUIDE.md`
   - Complete execution instructions
   - Troubleshooting section
   - Constitutional compliance validation

5. **Expected Output**: `/Users/am/Code/Agency/docs/benchmarks/EXPECTED_OUTPUT_EXAMPLES.md`
   - Successful execution examples
   - JSON structure reference
   - Failure scenario examples

## Task Coverage

### 10-Task Benchmark Tasks

| # | Agent Type | Description | Expected Duration |
|---|------------|-------------|-------------------|
| 1 | CODER | Prime number checker | 12-14s |
| 2 | TEST_GENERATOR | Pytest tests for prime checker | 14-16s |
| 3 | AUDITOR | Type safety audit | 10-12s |
| 4 | QUALITY_ENFORCER | Constitutional compliance check | 9-11s |
| 5 | PLANNER | Math utilities plan | 16-19s |
| 6 | CHIEF_ARCHITECT | Functional vs OOP ADR | 15-18s |
| 7 | TOOLSMITH | File hash comparison tool | 13-15s |
| 8 | MERGER | Git changes summary | 9-11s |
| 9 | LEARNING | Extract code patterns | 16-18s |
| 10 | SUMMARY | Benchmark summary | 14-16s |

### 100-Task Stress Test Tasks

**10 tasks per agent type**, covering:
- CODER: Algorithms (factorial, fibonacci, sort, search)
- TEST_GENERATOR: Test generation for algorithms
- AUDITOR: Code quality audits
- QUALITY_ENFORCER: Constitutional checks
- PLANNER: Module planning
- CHIEF_ARCHITECT: ADR creation
- TOOLSMITH: Tool development
- MERGER: Git summarization
- LEARNING: Pattern extraction
- SUMMARY: Status summarization

## Key Metrics

### Performance Baselines (M4 Pro)

**10-Task Benchmark**:
- Total: ~140s (2.3 minutes)
- Average: ~14s per task
- Peak Memory: ~1850 MB
- Cost: $0.00

**100-Task Stress Test**:
- Total: ~2850s (47.5 minutes)
- Average: ~28.5s per task
- Peak Memory: ~2090 MB
- Memory Growth: ~435 MB
- Cost: $0.00

### Model Usage

| Agent | Model | Size |
|-------|-------|------|
| CODER | qwen2.5-coder:32b | 32B |
| TEST_GENERATOR | qwen2.5-coder:32b | 32B |
| TOOLSMITH | qwen2.5-coder:32b | 32B |
| PLANNER | qwen2.5-coder:14b | 14B |
| AUDITOR | qwen2.5-coder:14b | 14B |
| QUALITY_ENFORCER | qwen2.5-coder:14b | 14B |
| LEARNING | qwen2.5-coder:14b | 14B |
| CHIEF_ARCHITECT | qwen2.5-coder:14b | 14B |
| MERGER | qwen2.5-coder:14b | 14B |
| SUMMARY | qwen2.5-coder:1.5b | 1.5B |

## Constitutional Compliance

### Article I: Complete Context Before Action
- Retry logic: LOCAL → LOCAL_PLUS → CLOUD
- Max retries: 2
- No partial results (all tasks must complete)

### Article II: 100% Verification
- Track completion rate (must be 100%)
- Track success rate (target 100%)

### Article IV: Learning Integration
- Store successful patterns in AgentContext
- Store escalation patterns for analysis
- Enable cross-session learning

## Running Tests

### Validate Benchmark Infrastructure
```bash
pytest tests/test_benchmarks.py -v
```

### Expected Test Results
```
tests/test_benchmarks.py::TestTenTaskBenchmark::test_benchmark_has_ten_tasks PASSED
tests/test_benchmarks.py::TestTenTaskBenchmark::test_benchmark_covers_all_agent_types PASSED
tests/test_benchmarks.py::TestTenTaskBenchmark::test_each_task_has_required_fields PASSED
tests/test_benchmarks.py::TestHundredTaskBenchmark::test_benchmark_has_hundred_tasks PASSED
tests/test_benchmarks.py::TestHundredTaskBenchmark::test_stress_tasks_distributed_evenly PASSED
... (30+ tests total)

============================== 30 passed in 2.34s ===============================
```

## Troubleshooting

### Ollama Not Running
```bash
curl http://localhost:11434/api/tags
# If fails: ollama serve
```

### Models Not Downloaded
```bash
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:32b
```

### High Memory Usage
```bash
# Stop unused models
ollama ps
ollama stop <model_name>

# Restart with limits
OLLAMA_MAX_LOADED_MODELS=2 ollama serve
```

## Next Steps After Running Benchmarks

1. **Analyze Results**:
   ```bash
   # View results
   cat benchmark_results/benchmark_10task_*.json | jq '.[] | {agent_type, duration_seconds, actual_tier}'
   ```

2. **Compare with Baselines**:
   - Check if duration matches expected ranges
   - Verify memory usage is within bounds
   - Confirm 100% local execution

3. **Identify Issues**:
   - Escalations: Optimize those agent types
   - Slow tasks: Profile and optimize
   - Memory growth: Check for leaks

4. **Store Learnings**:
   - Results automatically stored in AgentContext
   - Query with: `context.search_memories(['benchmark', 'learning'])`

## Integration with Development Workflow

### Pre-Push Hook
```bash
# .git/hooks/pre-push
python scripts/benchmark_10task_m4pro.py --output-dir /tmp/pre_push_bench
```

### Daily Cron Job
```bash
# crontab -e
0 2 * * * cd /Users/am/Code/Agency && python scripts/benchmark_10task_m4pro.py
```

### CI/CD Integration
```yaml
# .github/workflows/benchmark.yml
- name: Run M4 Pro Benchmark
  run: python scripts/benchmark_10task_m4pro.py
```

## Support

- **Documentation**: `/Users/am/Code/Agency/docs/benchmarks/`
- **Tests**: `/Users/am/Code/Agency/tests/test_benchmarks.py`
- **Issues**: Open GitHub issue with results attached

---

**Quick Links**:
- [Full Guide](M4_PRO_BENCHMARK_GUIDE.md)
- [Expected Output](EXPECTED_OUTPUT_EXAMPLES.md)
- [Benchmark Scripts](../../scripts/)
