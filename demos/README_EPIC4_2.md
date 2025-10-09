# EPIC 4.2 Complete Demo

Interactive demonstration of the **Self-Evolution System** with rich terminal formatting and comprehensive scenarios.

## Overview

This demo showcases the end-to-end workflow of EPIC 4.2, from agent registration through statistical analysis to ADR generation. It uses the `rich` library for beautiful terminal output including tables, progress bars, syntax highlighting, and panels.

## Components Demonstrated

### 1. Agent Registry
- Register multiple agent versions
- Track performance over time
- Manage agent lifecycle (active, experimental, deprecated)

### 2. Enhanced A/B Orchestrator
- Run benchmark comparisons between agents
- Collect performance metrics (score, duration, cost)
- Generate JSONL results files

### 3. Parallel Execution Framework
- Sequential vs parallel performance comparison
- Real-time progress tracking
- 2-3x speedup demonstration with worker pools
- Thread-safe budget enforcement

### 4. Proposal Generator
- Statistical analysis (t-tests, confidence intervals)
- Promotion decision logic
- ADR generation with markdown formatting
- Constitutional compliance validation

## Available Demos

### Demo 1: Simple Evolution Cycle
**Duration:** ~10 seconds

Complete workflow demonstration:
1. Register 2 agents (baseline_v1, advanced_v2)
2. Run A/B test with mock data (3 trials each)
3. Generate statistical analysis
4. Create ADR document
5. Show before/after comparison

**Key Features:**
- Agent comparison table
- Statistical significance testing
- ADR preview with syntax highlighting
- Evolution summary

### Demo 2: Parallel Execution
**Duration:** ~5 seconds

Performance comparison:
- Sequential execution (1 worker): 6 jobs
- Parallel execution (3 workers): 6 jobs
- Speedup calculation and visualization
- Efficiency metrics

**Key Features:**
- Progress bars for real-time tracking
- Speedup visualization with bar chart
- Performance metrics table

### Demo 3: Statistical Analysis Deep Dive
**Duration:** ~5 seconds

Detailed statistical breakdown:
1. Raw benchmark scores display
2. Descriptive statistics (mean, std dev)
3. T-test calculation step-by-step
4. 95% confidence intervals
5. Statistical significance explanation

**Key Features:**
- Raw data table
- Statistical calculations breakdown
- Confidence interval visualization
- Significance interpretation

### Demo 4: Promotion Decision
**Duration:** ~10 seconds

Clear winner scenario:
- Decision criteria evaluation
- Promotion logic explanation
- ADR generation and preview
- Auto-promotion workflow instructions

**Key Features:**
- Decision criteria table
- ADR decision section preview
- Promotion instructions panel
- Constitutional compliance check

### Demo 5: Complete Workflow
**Duration:** ~15 seconds

End-to-end integration:
1. Agent Registry (3 agents)
2. A/B Test Execution (mock data)
3. Constitutional compliance verification
4. Statistical analysis
5. Winner determination
6. ADR generation
7. Performance summary

**Key Features:**
- All 4 components in sequence
- Constitutional compliance table
- Winner announcement
- Complete performance summary

## Usage

### Run All Demos (Interactive)

```bash
python demos/epic4_2_complete_demo.py
```

Press Enter between demos to continue. Total runtime: ~45 seconds.

### Run Specific Demo

```bash
# Demo 1: Simple Evolution Cycle
python demos/epic4_2_complete_demo.py 1

# Demo 2: Parallel Execution
python demos/epic4_2_complete_demo.py 2

# Demo 3: Statistical Analysis Deep Dive
python demos/epic4_2_complete_demo.py 3

# Demo 4: Promotion Decision
python demos/epic4_2_complete_demo.py 4

# Demo 5: Complete Workflow
python demos/epic4_2_complete_demo.py 5
```

### Show Help

```bash
python demos/epic4_2_complete_demo.py --help
```

## Requirements

### Python Dependencies

```bash
# Core requirements (in requirements.txt)
rich>=13.0.0              # Terminal formatting
pydantic>=2.0.0           # Data validation
scipy>=1.11.0             # Statistical tests (optional)

# EPIC 4.2 components
meta_learning/            # Agent registry, proposal generator
dspy_agents/              # A/B orchestrator, parallel execution (optional)
shared/                   # Type definitions, Result pattern
```

### Optional Dependencies

- `scipy`: For rigorous statistical tests (t-test, p-values). If not available, uses simplified estimation.
- `dspy_agents`: For real orchestrator demos. Demo 2 simulates parallel execution if not available.

## Output Examples

### Agent Comparison Table

```
                    Agent Comparison
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric        ┃ Challenger ┃ Incumbent ┃ Improvement ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ mean_score    │      0.869 │     0.725 │      +19.7% │
│ mean_duration │       9.90 │      9.33 │       +6.2% │
│ mean_cost     │    $0.0955 │   $0.0960 │       -0.6% │
│ sample_size   │       3.00 │      3.00 │       +0.0% │
│ std_dev       │       0.05 │      0.05 │      +13.6% │
└───────────────┴────────────┴───────────┴─────────────┘
```

### Statistical Tests

```
       Statistical Tests
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Metric            ┃   Value ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Score Improvement │  +0.143 │
│ P-value           │  0.0243 │
│ Recommendation    │ PROMOTE │
└───────────────────┴─────────┘
```

### ADR Preview (Syntax Highlighted)

```markdown
# ADR-001: Agent Promotion - advanced_v2

## Status
**Proposed** - 2025-10-08

## Context
A/B testing framework evaluated challenger agent `advanced_v2` against incumbent `baseline_v1`.

### Challenger Performance (advanced_v2)
- Mean Score: 0.869 (±0.053)
- Mean Duration: 9.90s
- Mean Cost: $0.0955
- Sample Size: 3

## Decision
**Recommendation: PROMOTE**

### Statistical Analysis
- Score Improvement: +0.143 (+14.3%)
- P-value: 0.0243

### Rationale
The challenger demonstrates statistically significant improvement in aggregate score metrics.
```

### Speedup Visualization

```
Speedup Visualization:
████████████████████ 2.89x

✅ EXCELLENT: Achieved > 2x speedup!
```

## File Structure

```
demos/
├── epic4_2_complete_demo.py       # Main demo script (800+ lines)
├── README_EPIC4_2.md              # This file
├── ab_testing_demo.py             # Component 2 demo
├── parallel_execution_demo.py     # Component 3 demo
└── demo_proposal_report.py        # Component 4 demo

Generated Files (temporary):
benchmark_results/
└── demo_*.jsonl                   # Mock benchmark data (auto-deleted)

docs/adr/demos/
└── ADR-*.md                       # Generated ADRs (auto-deleted in demo)

data/
└── demo_*.json                    # Agent registry data (auto-deleted)
```

## Constitutional Compliance

All demos verify compliance with the Agency Constitution:

### Article I: Complete Context Before Action
- ✅ All benchmark data validated before analysis
- ✅ Minimum sample size enforced (3 trials)
- ✅ Data quality checks performed

### Article II: 100% Verification and Stability
- ✅ Statistical tests performed (t-test, confidence intervals)
- ✅ Significance level enforced (p < 0.05)
- ✅ No merge without rigorous validation

### Article III: Automated Merge Enforcement
- ✅ Promotion decisions automated based on criteria
- ✅ No manual overrides permitted
- ✅ Clear decision logic (PROMOTE, REJECT, HUMAN_REVIEW)

### Article IV: Continuous Learning
- ✅ Patterns stored in audit logs
- ✅ Successful evolutions tracked
- ✅ Performance history maintained

## Decision Criteria

### Auto-Promote Thresholds
- Confidence ≥ 0.95
- Score improvement ≥ 5.0%
- P-value < 0.05
- Sample size ≥ 3
- Cost increase ≤ 20%

### Auto-Reject Conditions
- Score improvement < 0% (regression)
- Confidence < 0.5
- Cost increase > 50% AND improvement < 10%

### Human Review Triggers
- Marginal improvements (0-5%)
- High variance in results
- Risk factors detected
- Insufficient statistical power

## Performance Metrics

### Mock Data Generation
- **Deterministic:** Uses seeded random for reproducibility
- **Realistic:** Simulates real benchmark distributions
- **Fast:** Generates data in milliseconds

### Demo Execution Times
- Demo 1: ~10 seconds (registration → ADR)
- Demo 2: ~5 seconds (parallel simulation)
- Demo 3: ~5 seconds (statistical breakdown)
- Demo 4: ~10 seconds (promotion decision)
- Demo 5: ~15 seconds (complete workflow)

**Total Runtime:** ~45 seconds for all 5 demos (interactive mode)

## Troubleshooting

### ModuleNotFoundError: meta_learning
**Solution:** Run from Agency root directory:
```bash
cd /Users/am/Code/Agency
python demos/epic4_2_complete_demo.py
```

### Rich Library Not Available
**Solution:** Install rich:
```bash
pip install rich
```

Demo falls back to plain text if rich is not available.

### SciPy Not Available
**Solution:** Install scipy for rigorous statistical tests:
```bash
pip install scipy
```

Demo uses simplified p-value estimation if scipy is not available.

### Orchestrator Not Available
**Solution:** Demo 2 simulates parallel execution. For real orchestrator:
```bash
# Install dspy_agents components
# (requires worktree_manager and benchmark infrastructure)
```

## Next Steps

After running the demo:

1. **Review Generated ADRs**
   - Check `docs/adr/demos/` for ADR examples
   - Study decision logic and statistical analysis

2. **Run Real Benchmarks**
   - Replace mock data with actual agent benchmarks
   - Use `EnhancedABOrchestrator` for real A/B tests

3. **Integrate with Production**
   - Configure agent registry for production agents
   - Set up automated promotion workflows
   - Enable continuous learning (Article IV)

4. **Enable VectorStore Learning**
   - Store successful patterns in VectorStore
   - Query learnings before agent implementations
   - Track institutional knowledge over time

## Related Documentation

- **EPIC 4.2 Specification:** `docs/EPIC_4_2_SPEC.md`
- **Agent Registry:** `meta_learning/agent_registry.py`
- **Proposal Generator:** `meta_learning/proposal_generator.py`
- **A/B Orchestrator:** `dspy_agents/ab_testing.py`
- **Parallel Orchestrator:** `dspy_agents/parallel_orchestrator.py`
- **Constitution:** `constitution.md` (Articles I-V)

## Contributing

To add new demos:

1. Follow the demo pattern in `epic4_2_complete_demo.py`
2. Use `print_banner()`, `print_section()`, `print_metric_table()` helpers
3. Create mock data with `create_mock_benchmark_data()`
4. Verify constitutional compliance
5. Add to `demos` dictionary in `main()`

## License

Part of Agency OS - See main repository LICENSE.

---

**Generated with EPIC 4.2 Self-Evolution System**
*Constitutional Compliance: Articles I-IV ✅*
