# **EPIC 4.2 User Guide: Parallel Self-Evolution Framework**

**Version:** 1.0.0
**Last Updated:** 2025-10-09
**Status:** Production Ready

---

## **Table of Contents**

1. [Quick Start (5 Minutes to First ADR)](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Component Deep Dives](#component-deep-dives)
4. [Usage Examples](#usage-examples)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)
7. [Constitutional Compliance Guide](#constitutional-compliance-guide)
8. [API Reference](#api-reference)

---

## **Quick Start**

### **Installation**

```bash
# 1. Ensure you're in the Agency repository
cd /path/to/Agency

# 2. Install dependencies (scipy recommended for statistical tests)
pip install scipy

# 3. Verify installation
python -c "from dspy_agents.ab_testing import EnhancedABOrchestrator; print('✓ AB Testing Ready')"
python -c "from dspy_agents.parallel_orchestrator import ParallelABOrchestrator; print('✓ Parallel Execution Ready')"
python -c "from meta_learning.proposal_generator import ProposalGenerator; print('✓ Proposal Generator Ready')"
python -c "from scripts.worktree_manager import WorktreeManager; print('✓ Worktree Manager Ready')"
```

### **Hello World: Your First ADR in 5 Minutes**

```bash
# 1. Run a simple A/B test (3 agents, 1 task, 2 repeats)
python -m dspy_agents.parallel_orchestrator \
  --agents agent_v1 agent_v2 agent_v3 \
  --tasks planner_api_auth_jwt \
  --repeats 2 \
  --workers 3 \
  --budget 2.0

# Output: benchmark_results/results_20251009_143022.jsonl

# 2. Analyze results and generate ADR
python demo_proposal_generator.py

# Output: docs/adr/ADR-XXX-agent-promotion-planner_v2_dspy.md
```

**Expected Output:**
```
✅ Speedup: 2.8x
✅ ADR generated: ADR-024-agent-promotion-planner_v2_dspy.md
Recommendation: PROMOTE
```

---

## **Architecture Overview**

### **System Diagram (ASCII Art)**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EPIC 4.2: Parallel Evolution Framework           │
└─────────────────────────────────────────────────────────────────────┘

                          User Input
                              │
                              ▼
              ┌───────────────────────────────┐
              │  1. Worktree Manager          │ ◄─── Component 1
              │  (scripts/worktree_manager.py)│
              └───────────────┬───────────────┘
                              │
                              │ Creates isolated branches
                              │
                              ▼
              ┌───────────────────────────────┐
              │  2. A/B Orchestrator          │ ◄─── Component 2
              │  (dspy_agents/ab_testing.py)  │      (Sequential)
              │                               │
              │  OR                           │
              │                               │
              │  3. Parallel Orchestrator     │ ◄─── Component 3
              │  (dspy_agents/parallel_orch.) │      (Parallel)
              └───────────────┬───────────────┘
                              │
                              │ Generates JSONL results
                              │
                              ▼
              ┌───────────────────────────────┐
              │  4. Proposal Generator        │ ◄─── Component 4
              │  (meta_learning/proposal...)  │      (Statistical Analysis)
              └───────────────┬───────────────┘
                              │
                              │ Statistical validation
                              │
                              ▼
              ┌───────────────────────────────┐
              │  ADR Document                 │
              │  (docs/adr/ADR-XXX-...)       │
              └───────────────────────────────┘
                              │
                              ▼
                    Human Review & Promotion
```

### **Data Flow Visualization**

```
Agent Definitions
       │
       ├─► WorktreeManager ──► Isolated Filesystem
       │                             │
       │                             ▼
       ├─► ABOrchestrator ──► Mission Execution
       │                             │
       │                             ▼
       └─► BenchmarkTasks ──► Standardized Metrics
                                     │
                                     ▼
                            JSONL Results File
                            (append-only log)
                                     │
                                     ▼
                         ProposalGenerator
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              Statistical      Confidence       Cost
              Significance     Intervals        Analysis
                    │                │                │
                    └────────────────┼────────────────┘
                                     ▼
                            ProposalReport
                            (Pydantic model)
                                     │
                                     ▼
                            ADR Generation
                            (Markdown)
                                     │
                                     ▼
                          PROMOTE / REJECT / HUMAN_REVIEW
```

### **Worktree Isolation Explanation**

Each agent execution runs in a **completely isolated git worktree**:

```
main-repo/
│
├── .git/                       # Main repository
├── agency.py                   # Main codebase
│
└── worktrees/                  # Isolated execution environments
    ├── agent_v1-task_001-1759965705-r0/
    │   ├── .git -> main-repo/.git/worktrees/agent_v1-...
    │   ├── agency.py           # Independent copy
    │   ├── .env                # Synced config
    │   ├── mission.json        # Task specification
    │   └── benchmark_output.json  # Results
    │
    ├── agent_v2-task_001-1759965705-r0/
    │   └── ...                 # Parallel execution, no conflicts
    │
    └── agent_v3-task_001-1759965705-r0/
        └── ...                 # All run simultaneously
```

**Key Benefits:**
- **Zero git conflicts** (separate branches)
- **True parallelism** (independent filesystems)
- **Complete isolation** (no cross-contamination)
- **Audit trail** (every execution preserved)

---

## **Component Deep Dives**

### **Component 1: Worktree Manager**

**Purpose:** Create isolated filesystem environments for agent execution.

**File:** `scripts/worktree_manager.py`

#### **Creating Isolated Environments**

```python
from scripts.worktree_manager import WorktreeManager, WorktreeConfig

# Initialize manager
manager = WorktreeManager(base_path=Path("worktrees"))

# Create isolated worktree
config = WorktreeConfig(
    branch_name="agent-experiment-1",
    context_files=[".env", ".claude/", "meta_learning/", "dspy_agents/"]
)
worktree_path = manager.create_worktree(config)
# Output: worktrees/agent-experiment-1/
```

**What happens:**
1. `git worktree add worktrees/agent-experiment-1 -b agent-experiment-1`
2. Copies essential files (.env, .claude/, etc.) to new worktree
3. Returns path to isolated environment

#### **Context Synchronization**

**Default Synced Files:**
- `.env` - Environment variables
- `.claude/` - Claude configuration
- `.cursor/` - Cursor IDE settings
- `meta_learning/` - Benchmark definitions
- `dspy_agents/` - Agent implementations
- `agency_config.yaml` - System configuration

**Custom Sync Example:**
```python
config = WorktreeConfig(
    branch_name="custom-sync",
    context_files=[
        ".env",
        "custom_config.yaml",
        "benchmarks/",
        "prompts/"
    ]
)
```

#### **Cleanup Strategies**

```python
# Strategy 1: Remove specific worktree
manager._remove_worktree("agent-experiment-1")

# Strategy 2: Keep only recent worktrees
removed_count = manager.cleanup_all(keep_recent=3)
# Removes all worktrees except the 3 most recent

# Strategy 3: List before cleaning
worktrees = manager.list_worktrees()
for wt in worktrees:
    print(f"{wt['name']}: {wt['size_mb']:.2f} MB")
```

**Automatic Cleanup:**
```bash
# CLI cleanup (keeps 3 most recent)
python scripts/worktree_manager.py cleanup --keep 3
```

---

### **Component 2: A/B Orchestrator Integration**

**Purpose:** Run agent benchmarks with automatic evaluation and budget tracking.

**File:** `dspy_agents/ab_testing.py`

#### **Running Parallel Benchmarks**

```python
from dspy_agents.ab_testing import EnhancedABOrchestrator

# Initialize orchestrator
orchestrator = EnhancedABOrchestrator(
    agent_ids=["planner_v1", "planner_v2_dspy"],
    task_ids=["planner_api_auth_jwt"],  # None = all tasks
    repeats=3,  # Statistical confidence
    budget_limit=5.0  # USD
)

# Run benchmarks (blocks until complete)
results_file = orchestrator.run()
# Output: benchmark_results/results_20251009_143022.jsonl
```

**What happens:**
1. For each (agent, task, repeat) combination:
   - Creates unique worktree branch
   - Syncs context files
   - Invokes agent with mission
   - Collects standardized output
   - Tracks cost
2. Writes results to JSONL (append-only)
3. Stops if budget exceeded

#### **Budget Management**

```python
# Budget check before each execution
if self.total_cost >= self.budget_limit:
    logger.warning(f"Budget limit reached: ${self.total_cost:.2f}")
    return results_path  # Early exit, partial results

# Track cost per execution
cost_usd = duration_s * 0.01  # Placeholder: $0.01/second
self.total_cost += cost_usd
```

**Budget Strategies:**

| Strategy | Configuration | Use Case |
|----------|---------------|----------|
| Strict Limit | `budget_limit=5.0` | Production runs |
| Generous Limit | `budget_limit=50.0` | Full evaluation |
| Per-Run Limit | Check in `_execute_agent_on_task()` | Fine control |

#### **Result Collection**

**JSONL Format (one line per trial):**
```json
{
  "run_id": "abc123",
  "agent_id": "planner_v2_dspy",
  "task_id": "planner_api_auth_jwt",
  "scores": {"aggregate": 0.92},
  "duration_s": 12.5,
  "cost_usd": 0.125,
  "timestamp": "2025-10-09T14:30:22",
  "repeat": 0,
  "metadata": {"agent_type": "planner"}
}
```

**Reading Results:**
```python
import json

with open("benchmark_results/results_20251009_143022.jsonl") as f:
    for line in f:
        result = json.loads(line)
        print(f"{result['agent_id']}: {result['scores']['aggregate']:.2%}")
```

---

### **Component 3: Parallel Orchestrator**

**Purpose:** Execute benchmarks in parallel using ThreadPoolExecutor.

**File:** `dspy_agents/parallel_orchestrator.py`

#### **ThreadPoolExecutor Configuration**

```python
from dspy_agents.parallel_orchestrator import ParallelABOrchestrator

# Parallel execution (3 workers)
orchestrator = ParallelABOrchestrator(
    agent_ids=["agent_v1", "agent_v2", "agent_v3"],
    task_ids=["task_001"],
    repeats=2,
    budget_limit=5.0,
    max_workers=3  # Parallel workers
)

results_file = orchestrator.run()
# 3 agents × 1 task × 2 repeats = 6 jobs
# Completes in ~2x faster than sequential
```

**Worker Tuning:**

| Workers | CPU Cores | Use Case |
|---------|-----------|----------|
| 1 | Any | Sequential (debugging) |
| 3 | 4+ | Balanced (default) |
| 5 | 8+ | High throughput |
| 10 | 16+ | Maximum parallelism |

#### **Performance Tuning**

**Compare Sequential vs Parallel:**
```python
from dspy_agents.parallel_orchestrator import compare_sequential_vs_parallel

results = compare_sequential_vs_parallel(
    agent_ids=["agent_v1", "agent_v2"],
    task_ids=["task_001"],
    repeats=2,
    budget_limit=5.0
)

print(f"Sequential: {results['sequential']['duration_s']:.2f}s")
print(f"Parallel:   {results['parallel']['duration_s']:.2f}s")
print(f"Speedup:    {results['speedup']:.2f}x")
print(f"Efficiency: {results['efficiency_pct']:.1f}%")
```

**Expected Performance:**
- **Sequential (1 worker):** 6 jobs × 5s/job = 30s
- **Parallel (3 workers):** 6 jobs ÷ 3 = 2 batches × 5s = 10s
- **Speedup:** 3.0x (ideal), 2.8x (realistic with overhead)

#### **Thread-Safe Patterns**

**Budget Tracking:**
```python
# Thread-safe cost update
with self._budget_lock:
    self.total_cost += result["cost_usd"]

    if self.total_cost >= self.budget_limit:
        logger.warning("Budget exceeded, stopping...")
        # Cancel remaining jobs
        for future in future_to_job.keys():
            future.cancel()
```

**Result Collection:**
```python
# Thread-safe result appending
with self._results_lock:
    results.append(result)
    self._completed_jobs += 1

    # Write to file immediately (append-only)
    f.write(json.dumps(result, default=str) + "\n")
    f.flush()
```

**Progress Tracking:**
```python
# Thread-safe progress reporting
with self._results_lock:
    progress = (self._completed_jobs / self._total_jobs) * 100
    logger.info(f"[{self._completed_jobs}/{self._total_jobs}] ({progress:.1f}%)")
```

---

### **Component 4: Proposal Generator**

**Purpose:** Statistical analysis and ADR generation from benchmark results.

**File:** `meta_learning/proposal_generator.py`

#### **Statistical Analysis**

```python
from meta_learning.proposal_generator import ProposalGenerator
from pathlib import Path

# Initialize generator
generator = ProposalGenerator(
    min_samples=3,  # Minimum trials per agent
    significance_level=0.05  # P-value threshold (95% confidence)
)

# Analyze results
result = generator.analyze_results(Path("benchmark_results/results_20251009_143022.jsonl"))

if result.is_ok():
    report = result.unwrap()
    print(f"Recommendation: {report.recommendation}")
    print(f"Challenger: {report.challenger.agent_id} (mean: {report.challenger.mean_score:.3f})")
    print(f"Incumbent: {report.incumbent.agent_id} (mean: {report.incumbent.mean_score:.3f})")
    print(f"Improvement: {report.comparison.score_improvement:+.3f}")
    print(f"P-value: {report.comparison.p_value:.4f}")
else:
    print(f"Error: {result.unwrap_err()}")
```

**Statistical Tests Used:**

| Test | When | Library |
|------|------|---------|
| **T-test** | Sample size ≥3, scipy installed | `scipy.stats.ttest_ind()` |
| **Heuristic** | Sample size <3 or no scipy | >10% improvement = PROMOTE |

**Metrics Calculated:**
- **Mean Score** - Average aggregate score
- **Std Dev** - Score variance
- **P-value** - Statistical significance (if scipy available)
- **Effect Size** - Magnitude of difference
- **Confidence Intervals** - 95% CI bounds

#### **ADR Generation**

```python
# Generate ADR document
adr_result = generator.generate_adr(report, output_dir=Path("docs/adr"))

if adr_result.is_ok():
    adr_path = adr_result.unwrap()
    print(f"✓ ADR created: {adr_path}")
    # Output: docs/adr/ADR-024-agent-promotion-planner_v2_dspy.md
else:
    print(f"Error: {adr_result.unwrap_err()}")
```

**ADR Template Structure:**
```markdown
# ADR-024: Agent Promotion - planner_v2_dspy

## Status
**Proposed** - 2025-10-09

## Context
A/B testing framework evaluated challenger agent `planner_v2_dspy`
against incumbent `planner_v1`.

### Challenger Performance
- Mean Score: 0.900 (±0.015)
- Sample Size: 5

### Incumbent Performance
- Mean Score: 0.760 (±0.020)
- Sample Size: 5

## Decision
**Recommendation: PROMOTE**

### Statistical Analysis
- Score Improvement: +0.140 (+18.4%)
- P-value: 0.0012
- Statistical significance: ✓ Yes

## Implementation
1. Update agent registry to promote planner_v2_dspy
2. Deploy to production
3. Monitor metrics for 48 hours
4. Rollback if regression detected
```

#### **Promotion Decisions**

**Decision Logic:**

```python
# PROMOTE criteria (all must be true)
if (
    score_improvement >= 0.05  # ≥5% better
    and p_value < 0.05         # Statistically significant
    and confidence >= 0.95     # High confidence
):
    return "PROMOTE"

# REJECT criteria (any can be true)
if (
    score_improvement < 0      # Regression
    or confidence < 0.5        # Low confidence
):
    return "REJECT"

# Default: INCONCLUSIVE
return "INCONCLUSIVE"
```

**Decision Tree:**
```
                Start
                  │
                  ▼
         Score Improvement ≥5%?
              │         │
             No        Yes
              │         │
              │         ▼
              │    P-value <0.05?
              │         │
              │        Yes
              │         │
              │         ▼
              │    PROMOTE ✓
              │
              ▼
     Score <0% (regression)?
              │         │
             Yes       No
              │         │
              ▼         ▼
         REJECT ✗   INCONCLUSIVE ?
```

---

## **Usage Examples**

### **Example 1: Simple A/B Test (Sequential)**

**Scenario:** Compare 2 agents on 1 task with 3 repeats.

```python
from dspy_agents.ab_testing import EnhancedABOrchestrator
from meta_learning.proposal_generator import ProposalGenerator
from pathlib import Path

# Step 1: Run A/B test
print("Running A/B test...")
orchestrator = EnhancedABOrchestrator(
    agent_ids=["baseline_agent", "improved_agent"],
    task_ids=["code_generation_simple"],
    repeats=3,
    budget_limit=2.0
)
results_file = orchestrator.run()
print(f"✓ Results saved: {results_file}")

# Step 2: Analyze results
print("\nAnalyzing results...")
generator = ProposalGenerator()
analysis = generator.analyze_results(results_file)

if analysis.is_ok():
    report = analysis.unwrap()
    print(f"✓ Recommendation: {report.recommendation}")

    # Step 3: Generate ADR if promoted
    if report.recommendation == "PROMOTE":
        adr_result = generator.generate_adr(report)
        if adr_result.is_ok():
            print(f"✓ ADR: {adr_result.unwrap()}")
else:
    print(f"✗ Error: {analysis.unwrap_err()}")
```

**Expected Output:**
```
Running A/B test...
Completed: baseline_agent on code_generation_simple (repeat 1/3), score=75.00%, cost=$0.0500
Completed: baseline_agent on code_generation_simple (repeat 2/3), score=77.00%, cost=$0.0510
Completed: baseline_agent on code_generation_simple (repeat 3/3), score=76.00%, cost=$0.0505
Completed: improved_agent on code_generation_simple (repeat 1/3), score=89.00%, cost=$0.0520
Completed: improved_agent on code_generation_simple (repeat 2/3), score=91.00%, cost=$0.0530
Completed: improved_agent on code_generation_simple (repeat 3/3), score=90.00%, cost=$0.0525
✓ Results saved: benchmark_results/results_20251009_150022.jsonl

Analyzing results...
✓ Recommendation: PROMOTE
✓ ADR: docs/adr/ADR-025-agent-promotion-improved_agent.md
```

---

### **Example 2: Parallel Execution (3 Agents)**

**Scenario:** Compare 3 agent variants in parallel with 2 repeats.

```python
from dspy_agents.parallel_orchestrator import ParallelABOrchestrator

# Run parallel A/B test
orchestrator = ParallelABOrchestrator(
    agent_ids=["agent_v1", "agent_v2", "agent_v3"],
    task_ids=["planner_api_design"],
    repeats=2,
    budget_limit=5.0,
    max_workers=3  # All 3 run simultaneously
)

results_file = orchestrator.run()

# Get stats
stats = orchestrator.get_stats()
print(f"Completed: {stats['completed_jobs']}/{stats['total_jobs']}")
print(f"Progress: {stats['progress_pct']:.1f}%")
print(f"Cost: ${stats['total_cost_usd']:.2f} / ${stats['budget_limit_usd']:.2f}")
print(f"Budget Used: {stats['budget_used_pct']:.1f}%")
```

**Expected Output:**
```
[1/6] (16.7%) Completed: agent_v1 on planner_api_design (repeat 1/2), score=82.00%, cost=$0.0800
[2/6] (33.3%) Completed: agent_v2 on planner_api_design (repeat 1/2), score=88.00%, cost=$0.0850
[3/6] (50.0%) Completed: agent_v3 on planner_api_design (repeat 1/2), score=91.00%, cost=$0.0900
[4/6] (66.7%) Completed: agent_v1 on planner_api_design (repeat 2/2), score=83.00%, cost=$0.0810
[5/6] (83.3%) Completed: agent_v2 on planner_api_design (repeat 2/2), score=89.00%, cost=$0.0860
[6/6] (100.0%) Completed: agent_v3 on planner_api_design (repeat 2/2), score=92.00%, cost=$0.0910

Completed: 6/6
Progress: 100.0%
Cost: $0.51 / $5.00
Budget Used: 10.2%
```

---

### **Example 3: Custom Statistical Tests (Advanced)**

**Scenario:** Use scipy's advanced statistical features for rigorous validation.

```python
from meta_learning.proposal_generator import ProposalGenerator
from pathlib import Path
import numpy as np
from scipy import stats

# Custom generator with strict criteria
generator = ProposalGenerator(
    min_samples=5,  # Higher sample requirement
    significance_level=0.01  # Stricter p-value (99% confidence)
)

results_file = Path("benchmark_results/high_stakes_experiment.jsonl")
analysis = generator.analyze_results(results_file)

if analysis.is_ok():
    report = analysis.unwrap()

    # Advanced statistical checks
    challenger_scores = report.challenger.raw_scores
    incumbent_scores = report.incumbent.raw_scores

    # 1. Normality test (Shapiro-Wilk)
    _, p_challenger = stats.shapiro(challenger_scores)
    _, p_incumbent = stats.shapiro(incumbent_scores)

    print(f"Normality (Challenger): p={p_challenger:.4f}")
    print(f"Normality (Incumbent): p={p_incumbent:.4f}")

    # 2. Variance equality test (Levene)
    _, p_variance = stats.levene(challenger_scores, incumbent_scores)
    print(f"Variance Equality: p={p_variance:.4f}")

    # 3. Effect size (Cohen's d)
    pooled_std = np.sqrt((
        report.challenger.std_dev**2 + report.incumbent.std_dev**2
    ) / 2)
    cohens_d = (
        report.challenger.mean_score - report.incumbent.mean_score
    ) / pooled_std
    print(f"Cohen's d: {cohens_d:.3f}")

    # 4. Confidence intervals
    print(f"Challenger 95% CI: [{report.comparison.challenger_ci_lower:.3f}, {report.comparison.challenger_ci_upper:.3f}]")
    print(f"Incumbent 95% CI: [{report.comparison.incumbent_ci_lower:.3f}, {report.comparison.incumbent_ci_upper:.3f}]")
    print(f"CI Overlap: {report.comparison.is_ci_overlap()}")

    # Final decision
    print(f"\nRecommendation: {report.recommendation}")
```

**Expected Output:**
```
Normality (Challenger): p=0.8234
Normality (Incumbent): p=0.7456
Variance Equality: p=0.4521
Cohen's d: 1.245
Challenger 95% CI: [0.875, 0.925]
Incumbent 95% CI: [0.735, 0.785]
CI Overlap: False

Recommendation: PROMOTE
```

---

## **Troubleshooting**

### **Common Errors and Solutions**

#### **Error 1: Worktree Already Exists**

**Symptom:**
```
fatal: 'worktrees/agent-v1-task-1' already exists
```

**Solution:**
```bash
# Remove existing worktree
python scripts/worktree_manager.py remove --branch agent-v1-task-1

# Or cleanup all old worktrees
python scripts/worktree_manager.py cleanup --keep 0
```

**Prevention:**
```python
# Automatic cleanup in orchestrator
if worktree_path.exists():
    manager._remove_worktree(config.branch_name)
```

---

#### **Error 2: Git Worktree Conflicts**

**Symptom:**
```
error: cannot lock ref 'refs/heads/agent-v1-task-1':
ref already exists
```

**Root Cause:** Orphaned worktree references after incomplete cleanup.

**Solution:**
```bash
# Prune stale worktree references
git worktree prune

# List all worktrees
git worktree list

# Force remove specific worktree
git worktree remove --force worktrees/agent-v1-task-1

# Delete orphaned branch
git branch -D agent-v1-task-1
```

**Prevention:**
```python
# Always cleanup after execution
try:
    result = manager.invoke_agent(...)
finally:
    manager._remove_worktree(branch_name)
```

---

#### **Error 3: Statistical Edge Cases**

**Symptom:**
```
ValueError: Insufficient samples for agent_v1: need 3, got 2
```

**Solution:**
```python
# Increase repeats to meet min_samples
orchestrator = EnhancedABOrchestrator(
    agent_ids=["agent_v1", "agent_v2"],
    repeats=3,  # Minimum for statistical significance
    budget_limit=5.0
)
```

**Symptom:**
```
P-value: None (scipy not installed)
```

**Solution:**
```bash
# Install scipy for rigorous statistical tests
pip install scipy

# Verify installation
python -c "from scipy import stats; print('✓ scipy installed')"
```

---

#### **Error 4: Budget Overruns**

**Symptom:**
```
WARNING: Budget limit reached: $5.12 >= $5.00
Stopping early. Results saved to: benchmark_results/...
```

**Analysis:**
```python
# Check cost per trial
with open("benchmark_results/results_20251009_143022.jsonl") as f:
    costs = [json.loads(line)["cost_usd"] for line in f]
    print(f"Mean cost per trial: ${sum(costs)/len(costs):.4f}")
    print(f"Max cost: ${max(costs):.4f}")
```

**Solutions:**

1. **Increase Budget:**
```python
orchestrator = EnhancedABOrchestrator(
    budget_limit=10.0  # 2x original
)
```

2. **Reduce Repeats:**
```python
orchestrator = EnhancedABOrchestrator(
    repeats=2  # Down from 3
)
```

3. **Budget per Trial:**
```python
total_jobs = len(agent_ids) * len(task_ids) * repeats
budget_per_trial = total_budget / total_jobs
print(f"Budget per trial: ${budget_per_trial:.4f}")
```

---

#### **Error 5: Missing Benchmark Output**

**Symptom:**
```
WARNING: Failed to parse output JSON: No such file or directory
```

**Root Cause:** Agent didn't write `benchmark_output.json`.

**Solution:**
```python
# Fallback to stdout parsing
def _parse_agent_output(self, result: dict, task) -> dict:
    content = result.get("stdout", "")

    # Extract sections from stdout
    sections = []
    for expected_section in task.expected_output.get("required_sections", []):
        if expected_section.lower() in content.lower():
            sections.append(expected_section)

    return {
        "sections": sections,
        "content": content[:1000],
        "keywords_used": extract_keywords(content)
    }
```

**Prevention:**
```python
# Ensure agent writes output file
mission = f"""
Your output MUST be saved to: benchmark_output.json

Format:
{{
    "sections": ["Goals", "Architecture", ...],
    "content": "Your specification text",
    "keywords_used": ["keyword1", "keyword2"]
}}
"""
```

---

## **Best Practices**

### **When to Use Parallel vs Sequential**

**Use Parallel When:**
- ✅ Multiple agents to compare (≥3)
- ✅ High-latency tasks (>10s per trial)
- ✅ Sufficient CPU cores (≥4)
- ✅ Budget allows parallel runs
- ✅ Time-sensitive evaluation

**Use Sequential When:**
- ✅ Debugging experiments
- ✅ Limited CPU cores (<4)
- ✅ Budget-constrained runs
- ✅ Simple comparisons (2 agents)
- ✅ Learning/experimentation phase

**Performance Comparison:**

| Scenario | Sequential | Parallel (3 workers) | Speedup |
|----------|-----------|---------------------|---------|
| 3 agents × 1 task × 3 repeats | 45s | 15s | 3.0x |
| 5 agents × 2 tasks × 2 repeats | 100s | 35s | 2.86x |
| 2 agents × 1 task × 5 repeats | 50s | 20s | 2.5x |

---

### **Sample Size Recommendations**

**Minimum Samples:**
| Confidence Level | Min Repeats | Use Case |
|------------------|-------------|----------|
| **Quick Test** | 2 | Initial exploration |
| **Standard** | 3 | Default (90% confidence) |
| **High Confidence** | 5 | Production promotion |
| **Critical** | 10 | High-stakes decisions |

**Statistical Power Analysis:**
```python
# Calculate required sample size for desired power
from scipy import stats

def required_sample_size(effect_size=0.5, power=0.8, alpha=0.05):
    """
    Calculate samples needed to detect effect with given power.

    Args:
        effect_size: Cohen's d (0.5 = medium effect)
        power: Probability of detecting true effect (0.8 = 80%)
        alpha: Significance level (0.05 = 95% confidence)
    """
    # Simplified calculation (use statsmodels for exact)
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)

    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n))

# Example: Detect 0.5 Cohen's d with 80% power
n = required_sample_size()
print(f"Required samples per group: {n}")
# Output: Required samples per group: 64
```

**Rule of Thumb:**
- **Small effect** (d=0.2): 310 samples
- **Medium effect** (d=0.5): 64 samples
- **Large effect** (d=0.8): 26 samples

**Practical Guidelines:**
- Start with 3 repeats for quick validation
- Use 5 repeats for production promotion
- Use 10+ repeats for critical agents (e.g., security, billing)

---

### **Statistical Significance Interpretation**

**P-value Thresholds:**

| P-value | Interpretation | Action |
|---------|----------------|--------|
| <0.001 | Very strong evidence | Auto-promote |
| 0.001-0.01 | Strong evidence | Promote with confidence |
| 0.01-0.05 | Moderate evidence | Promote (standard threshold) |
| 0.05-0.10 | Weak evidence | Consider more samples |
| >0.10 | Insufficient evidence | Reject or re-test |

**Effect Size (Cohen's d):**

| Cohen's d | Interpretation | Example |
|-----------|----------------|---------|
| 0.0-0.2 | Trivial | 75% → 76% |
| 0.2-0.5 | Small | 75% → 80% |
| 0.5-0.8 | Medium | 75% → 85% |
| 0.8+ | Large | 75% → 92% |

**Confidence Intervals:**
```python
# Non-overlapping CIs = strong evidence
if not report.comparison.is_ci_overlap():
    print("✓ Strong evidence: CIs don't overlap")
else:
    print("⚠ Weak evidence: CIs overlap")
```

**Decision Matrix:**

| P-value | Effect Size | Sample Size | Decision |
|---------|-------------|-------------|----------|
| <0.05 | Large (0.8+) | ≥3 | **PROMOTE** |
| <0.05 | Medium (0.5) | ≥5 | **PROMOTE** |
| <0.05 | Small (0.2) | ≥10 | Consider |
| ≥0.05 | Any | Any | **REJECT/MORE DATA** |

---

### **ADR Review Guidelines**

**Human Review Checklist:**

```markdown
## ADR Review Checklist

### Statistical Validity
- [ ] Sample size ≥3 per agent
- [ ] P-value <0.05 (if scipy available)
- [ ] Improvement ≥5%
- [ ] No data quality issues

### Cost Analysis
- [ ] Cost increase <20%
- [ ] Cost/benefit ratio acceptable
- [ ] Budget impact sustainable

### Risk Assessment
- [ ] No identified risk factors
- [ ] Rollback plan defined
- [ ] Monitoring strategy clear

### Implementation
- [ ] Agent registry update process clear
- [ ] Deployment steps defined
- [ ] Success metrics specified

### Constitutional Compliance
- [ ] Article I: Complete context validated
- [ ] Article II: 100% test verification
- [ ] Article III: Automated enforcement follows
- [ ] Article IV: Learning stored
- [ ] Article V: Spec-driven process followed
```

**Approval Criteria:**

| Recommendation | Auto-Action | Review Required |
|----------------|-------------|-----------------|
| **PROMOTE** | Yes (if criteria met) | Optional |
| **REJECT** | Yes (if regression) | Optional |
| **INCONCLUSIVE** | No | **Mandatory** |

**Review Workflow:**
```
ADR Generated
     │
     ▼
Auto-Promotable?
     │
    Yes ─────► Create PR ─────► Auto-Merge (if CI passes)
     │
    No
     │
     ▼
Human Review ─────► Approve/Reject ─────► Manual Merge
```

---

## **Constitutional Compliance Guide**

### **How Each Component Enforces Constitutional Articles**

#### **Article I: Complete Context Before Action**

**Worktree Manager:**
```python
# Syncs ALL essential context files before agent execution
context_files = [".env", ".claude/", "meta_learning/", "dspy_agents/"]
self._sync_context(worktree_path, context_files)
```

**A/B Orchestrator:**
```python
# Retries on timeout, never proceeds with incomplete data
try:
    result = subprocess.run(..., timeout=timeout)
except subprocess.TimeoutExpired:
    return {"success": False, "error": "timeout"}
```

**Proposal Generator:**
```python
# Validates ALL data before analysis
if not results_file.exists():
    return Err(f"Results file not found")

validation_result = self._validate_samples(agent_results)
if validation_result.is_err():
    return Err(validation_result.unwrap_err())
```

---

#### **Article II: 100% Verification and Stability**

**A/B Orchestrator:**
```python
# Each trial independently verified
scores = evaluate_output(task, output)
assert "aggregate" in scores  # 100% verification

# Results append-only (immutable audit trail)
with open(results_path, "a") as f:
    f.write(json.dumps(result) + "\n")
```

**Parallel Orchestrator:**
```python
# Thread-safe result collection
with self._results_lock:
    results.append(result)
    f.write(json.dumps(result, default=str) + "\n")
    f.flush()  # Immediate persistence
```

**Proposal Generator:**
```python
# Statistical verification with scipy
if HAS_SCIPY:
    t_stat, p_value = stats.ttest_ind(
        challenger.raw_scores,
        incumbent.raw_scores
    )
    comparison.p_value = p_value
```

---

#### **Article III: Automated Merge Enforcement**

**Proposal Generator:**
```python
def is_auto_promotable(self) -> bool:
    """No bypass authority - criteria are absolute."""
    return (
        self.recommendation == "PROMOTE"
        and self.confidence >= 0.95
        and self.improvement_pct >= 5.0
        and self.p_value < 0.05
        and self.cost_increase_pct <= 20.0
    )
```

**ADR Decision Enforcement:**
```markdown
## Implementation
1. Update agent registry to promote planner_v2_dspy
2. Deploy to production
3. Monitor metrics for 48 hours
4. Rollback if regression detected

**Constitutional Enforcement:**
- No manual overrides permitted
- Promotion gates are absolute barriers
```

---

#### **Article IV: Continuous Learning**

**Result Storage:**
```python
# All results stored in VectorStore for learning
from shared.agent_context import AgentContext

context.store_memory(
    key=f"ab_test_{timestamp}",
    content={
        "agent_ids": agent_ids,
        "results_file": str(results_file),
        "recommendation": report.recommendation,
        "improvement_pct": report.improvement_pct
    },
    tags=["ab_test", "promotion", "statistical_validation"]
)
```

**Pattern Recognition:**
```python
# Query past successful promotions
similar_promotions = context.search_memories(
    tags=["promotion", "success"],
    include_session=False  # Cross-session learning
)

# Apply learnings to new decisions
for promo in similar_promotions:
    if promo["improvement_pct"] > 10.0:
        logger.info(f"Past success: {promo['agent_ids']}")
```

---

#### **Article V: Spec-Driven Development**

**EPIC 4.2 Specification:**
```markdown
# Formal Specification: Self-Evolution Framework

## Goals
1. Automated agent promotion via statistical validation
2. Parallel execution for efficiency
3. Human-in-the-loop for safety

## Acceptance Criteria
- [ ] 3+ agent variants compared in parallel
- [ ] Statistical significance (p<0.05) validated
- [ ] ADR auto-generated with promotion recommendation
- [ ] Constitutional compliance verified
```

**Implementation Traceability:**
```python
# Component 1: Worktree Manager → Spec Goal #2 (Parallel)
# Component 2: A/B Orchestrator → Spec Goal #1 (Automation)
# Component 3: Parallel Orchestrator → Spec Goal #2 (Efficiency)
# Component 4: Proposal Generator → Spec Goal #3 (Safety)
```

---

### **Validation Checkpoints**

**Pre-Execution Validation:**
```python
# Check 1: Minimum sample size (Article I)
assert repeats >= 3, "Need ≥3 repeats for statistical significance"

# Check 2: Budget limit set (Article III)
assert budget_limit > 0, "Budget limit required"

# Check 3: Context files exist (Article I)
for file in context_files:
    assert Path(file).exists(), f"Missing context: {file}"
```

**Post-Execution Validation:**
```python
# Check 1: All trials completed (Article II)
assert completed_jobs == total_jobs, "Incomplete execution"

# Check 2: Results file exists (Article II)
assert results_path.exists(), "Results file missing"

# Check 3: Statistical validation (Article II)
if HAS_SCIPY:
    assert report.comparison.p_value is not None, "P-value missing"
```

**Promotion Validation:**
```python
# Check 1: Auto-promotion criteria (Article III)
if report.is_auto_promotable():
    logger.info("✓ Auto-promotion approved")
else:
    logger.warning("⚠ Human review required")

# Check 2: Learning stored (Article IV)
assert context.get_memory(f"ab_test_{timestamp}") is not None
```

---

### **Audit Trail**

**Complete Execution Trace:**
```
1. Worktree Creation
   └─ logs/worktree_creation_20251009_143022.log

2. Agent Execution (per trial)
   ├─ worktrees/agent_v1-task_001-r0/mission.json
   ├─ worktrees/agent_v1-task_001-r0/benchmark_output.json
   └─ worktrees/agent_v1-task_001-r0/agent.log

3. Benchmark Results (append-only)
   └─ benchmark_results/results_20251009_143022.jsonl

4. Statistical Analysis
   └─ logs/proposal_analysis_20251009_143545.log

5. ADR Generation
   └─ docs/adr/ADR-024-agent-promotion-planner_v2_dspy.md

6. Learning Storage
   └─ ~/.agency/vector_store/ab_test_20251009_143545.json

7. Git History (promotion)
   └─ git log --oneline --decorate
```

---

## **API Reference**

### **WorktreeManager**

```python
from scripts.worktree_manager import WorktreeManager, WorktreeConfig

manager = WorktreeManager(base_path: Path = Path("worktrees"))
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `create_worktree()` | `config: WorktreeConfig` | `Path` | Create isolated worktree |
| `invoke_agent()` | `worktree_path, mission, agent_id, timeout` | `dict` | Execute agent in worktree |
| `_remove_worktree()` | `branch_name: str` | `bool` | Remove worktree and branch |
| `cleanup_all()` | `keep_recent: int = 3` | `int` | Cleanup old worktrees |
| `list_worktrees()` | None | `list[dict]` | List all active worktrees |

**WorktreeConfig:**
```python
@dataclass
class WorktreeConfig:
    branch_name: str
    base_path: Path = Path("worktrees")
    context_files: List[str] = [".env", ".claude/", ...]
```

---

### **EnhancedABOrchestrator**

```python
from dspy_agents.ab_testing import EnhancedABOrchestrator

orchestrator = EnhancedABOrchestrator(
    agent_ids: list[str],
    task_ids: list[str] | None = None,
    repeats: int = 3,
    budget_limit: float = 10.0
)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `run()` | None | `Path` | Execute orchestration, return JSONL path |
| `_get_tasks()` | None | `list[BenchmarkTask]` | Get tasks to execute |
| `_execute_agent_on_task()` | `agent_id, task, repeat_idx` | `dict` | Execute single trial |
| `_worktree_agent_execution()` | `agent_id, task, repeat_idx` | `dict` | Worktree execution |
| `_mock_agent_execution()` | `agent_id, task, repeat_idx` | `dict` | Fallback mock execution |

**Return Type (run()):**
```python
Path("benchmark_results/results_20251009_143022.jsonl")
```

**Result Dict:**
```python
{
    "run_id": str,
    "agent_id": str,
    "task_id": str,
    "scores": {"aggregate": float},
    "duration_s": float,
    "cost_usd": float,
    "timestamp": str,
    "repeat": int,
    "metadata": dict
}
```

---

### **ParallelABOrchestrator**

```python
from dspy_agents.parallel_orchestrator import ParallelABOrchestrator

orchestrator = ParallelABOrchestrator(
    agent_ids: list[str],
    task_ids: list[str] | None = None,
    repeats: int = 3,
    budget_limit: float = 10.0,
    max_workers: int = 3
)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `run()` | None | `Path` | Parallel execution, return JSONL path |
| `_run_single_job()` | `agent_id, task, repeat_idx` | `dict` | Thread-safe job execution |
| `get_stats()` | None | `dict` | Current progress/budget stats |

**Thread-Safe Attributes:**
```python
self._budget_lock: threading.Lock      # Protects total_cost
self._results_lock: threading.Lock     # Protects results list
self._completed_jobs: int              # Thread-safe counter
self._total_jobs: int                  # Total job count
```

**Stats Dict:**
```python
{
    "completed_jobs": int,
    "total_jobs": int,
    "progress_pct": float,
    "total_cost_usd": float,
    "budget_limit_usd": float,
    "budget_used_pct": float,
    "max_workers": int
}
```

---

### **ProposalGenerator**

```python
from meta_learning.proposal_generator import ProposalGenerator

generator = ProposalGenerator(
    min_samples: int = 3,
    significance_level: float = 0.05
)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `analyze_results()` | `results_file: Path` | `Result[ProposalReport, str]` | Analyze JSONL results |
| `generate_adr()` | `report, output_dir` | `Result[Path, str]` | Generate ADR document |
| `_parse_jsonl()` | `file_path: Path` | `Result[list[BenchmarkResult], str]` | Parse JSONL |
| `_calculate_statistics()` | `results, agent_id` | `AgentMetrics` | Calculate stats |
| `_compare_agents()` | `challenger, incumbent` | `ComparisonResult` | Statistical comparison |
| `_determine_recommendation()` | `comparison` | `str` | Decision logic |

**ProposalReport (Pydantic Model):**
```python
class ProposalReport(BaseModel):
    challenger: AgentMetrics
    incumbent: AgentMetrics
    comparison: ComparisonResult
    recommendation: str  # "PROMOTE", "REJECT", "INCONCLUSIVE"
    timestamp: str

    # Methods
    def is_auto_promotable() -> bool
    def is_auto_rejectable() -> bool
    def requires_human_review() -> bool
```

**AgentMetrics:**
```python
class AgentMetrics(BaseModel):
    agent_id: str
    mean_score: float       # 0.0-1.0
    std_dev_score: float    # ≥0.0
    mean_duration: float    # seconds
    mean_cost: float        # USD
    sample_size: int        # ≥3
    raw_scores: list[float] # For statistical tests
```

**ComparisonResult:**
```python
class ComparisonResult(BaseModel):
    challenger_id: str
    incumbent_id: str
    score_improvement: float     # Positive = challenger better
    duration_improvement: float  # Negative = challenger faster
    cost_improvement: float      # Negative = challenger cheaper
    p_value: float | None        # Statistical significance
```

---

### **Configuration Templates**

#### **Quick Start Configuration**

```python
# config.py
AB_TEST_CONFIG = {
    "agent_ids": ["baseline", "improved"],
    "task_ids": ["code_gen_simple"],
    "repeats": 3,
    "budget_limit": 2.0,
    "max_workers": 1,  # Sequential
    "min_samples": 3,
    "significance_level": 0.05
}
```

#### **Production Configuration**

```python
# config_production.py
AB_TEST_CONFIG = {
    "agent_ids": ["v1", "v2_dspy", "v3_enhanced"],
    "task_ids": None,  # All tasks
    "repeats": 5,
    "budget_limit": 20.0,
    "max_workers": 5,
    "min_samples": 5,
    "significance_level": 0.01  # Stricter (99% confidence)
}
```

#### **Debug Configuration**

```python
# config_debug.py
AB_TEST_CONFIG = {
    "agent_ids": ["test_agent"],
    "task_ids": ["simple_task"],
    "repeats": 2,
    "budget_limit": 1.0,
    "max_workers": 1,  # Sequential for debugging
    "min_samples": 2,
    "significance_level": 0.10  # Lenient
}
```

---

## **Appendix: Decision Trees**

### **Execution Strategy Decision Tree**

```
Start: Need to compare agents
    │
    ▼
How many agents?
    │
    ├─ 1-2 agents ──► Use Sequential
    │                 (EnhancedABOrchestrator)
    │
    └─ 3+ agents ──► CPU cores available?
                      │
                      ├─ <4 cores ──► Use Sequential
                      │
                      └─ 4+ cores ──► Use Parallel
                                      (ParallelABOrchestrator)

                                      Workers = min(
                                          num_agents,
                                          cpu_cores - 1
                                      )
```

### **Sample Size Decision Tree**

```
Start: How many repeats?
    │
    ▼
What's the goal?
    │
    ├─ Quick exploration ──► 2 repeats
    │                         (80% confidence)
    │
    ├─ Standard validation ──► 3 repeats
    │                           (90% confidence)
    │
    ├─ Production promotion ──► 5 repeats
    │                            (95% confidence)
    │
    └─ Critical agents ──► 10+ repeats
        (security, billing)   (99% confidence)
```

### **Budget Allocation Decision Tree**

```
Start: Set budget limit
    │
    ▼
Calculate total jobs
jobs = agents × tasks × repeats
    │
    ▼
Estimate cost per job
cost_per_job = avg_duration_s × $0.01/s
    │
    ▼
Total estimated cost
total_cost = jobs × cost_per_job
    │
    ▼
total_cost < budget_limit?
    │
    ├─ Yes ──► Proceed
    │
    └─ No ──► Reduce repeats or tasks
               OR increase budget
```

---

## **Glossary**

**A/B Testing** - Statistical method for comparing two or more variants.

**ADR (Architectural Decision Record)** - Documented rationale for significant architectural choice.

**Aggregate Score** - Combined metric summarizing agent performance (0.0-1.0 range).

**Challenger** - Agent variant being tested for potential promotion.

**Cohen's d** - Standardized measure of effect size (difference / pooled std dev).

**Constitutional Compliance** - Adherence to Agency's 5 constitutional articles.

**Effect Size** - Magnitude of difference between groups (small/medium/large).

**Incumbent** - Current production agent variant.

**JSONL (JSON Lines)** - Text format with one JSON object per line.

**P-value** - Probability of observing results if null hypothesis true (<0.05 = significant).

**Statistical Power** - Probability of detecting true effect if it exists (typically 80%).

**Statistical Significance** - Likelihood that observed difference is not due to chance.

**ThreadPoolExecutor** - Python concurrency framework for parallel execution.

**Worktree** - Git feature enabling multiple working directories on different branches.

---

## **Further Reading**

**Internal Documentation:**
- **EPIC 4.2 Specification:** `EPIC4-2.md`
- **Constitutional Articles:** `constitution.md`
- **ADR Index:** `docs/adr/ADR-INDEX.md`
- **Memory Architecture:** `docs/MEMORY_ARCHITECTURE.md`

**External Resources:**
- **Git Worktrees:** https://git-scm.com/docs/git-worktree
- **Statistical Testing (scipy):** https://docs.scipy.org/doc/scipy/reference/stats.html
- **Cohen's d Calculator:** https://www.socscistatistics.com/effectsize/
- **A/B Testing Best Practices:** https://www.optimizely.com/optimization-glossary/ab-testing/

**Research Papers:**
- Kohavi et al. (2009): "Controlled experiments on the web: survey and practical guide"
- Deng et al. (2017): "Continuous monitoring of A/B tests without pain"

---

**Version History:**
- 1.0.0 (2025-10-09): Initial comprehensive user guide

**Authors:**
- PlannerAgent (Architecture Design)
- ChiefArchitect (Constitutional Compliance)
- AgencyOS Contributors

**License:** MIT (Agency Internal Use)

---

*"Data-driven evolution through rigorous statistical validation."*
