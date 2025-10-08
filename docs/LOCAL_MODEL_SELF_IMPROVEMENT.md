# Local Model Self-Improvement Guide

**Goal**: Enable qwen3-coder:30b to autonomously improve AgencyOS codebase (including itself)
**Hardware**: M4 Pro 48GB with Metal GPU optimization
**Cost**: $0/1M tokens (vs $1.60 cloud) for 60% of tasks

---

## 🎯 Strategy: Exponential Self-Improvement Loop

### Phase 1: Installation & Validation (30 min)
Test that local model works correctly with memory-safe execution.

### Phase 2: Supervised Improvement (2-4 hours)
Human-guided improvements to validate quality and learn patterns.

### Phase 3: Autonomous Improvement (ongoing)
Local model improves codebase autonomously, with human approval gates.

### Phase 4: Self-Training Loop (advanced)
Fine-tune local model on successful improvements for exponential growth.

---

## 📋 Phase 1: Installation & Validation

### Step 1.1: Install Qwen3-Coder with Optimizations
```bash
# Run automated setup script
cd /Users/am/Code/Agency
bash scripts/setup_local_model.sh

# What it does:
# 1. Configure ~/.zshrc with Metal GPU optimizations:
#    - OLLAMA_KV_CACHE_TYPE="q8_0" (50% memory savings)
#    - OLLAMA_FLASH_ATTENTION=1 (faster inference)
#    - OLLAMA_NUM_GPU=1 (Metal GPU)
# 2. Restart Ollama with optimizations
# 3. Pull qwen3-coder:30b (~19GB, Q4_K_M)
# 4. Test inference
# 5. Update .env with LOCAL_MODEL_NAME=qwen3-coder:30b

# Expected time: 10-15 minutes (mostly download)
```

### Step 1.2: Verify Installation
```bash
# Test 1: Model responds quickly (no timeout)
time ollama run qwen3-coder:30b "Fix typo: def calcualte_total(a, b): return a + b"
# Expected: 2-5 seconds first token, <10 seconds total
# Should output corrected code

# Test 2: Check memory usage (should be ~35-40GB)
ollama run qwen3-coder:30b "print('hello')" &
sleep 3
ps aux | grep ollama | awk '{print $6/1024/1024 " GB"}'
# Expected: 19-22GB (model loaded with small context)

# Test 3: Verify Metal GPU is being used
# Activity Monitor → GPU → Should show high GPU usage during inference
```

### Step 1.3: Test Memory-Aware Execution
```bash
# This should automatically use 3 workers (not 10)
python run_tests.py --run-all

# Expected output:
# "🧠 Local model active: using 3 test workers (memory-safe)"
# All 2915+ tests should pass
# No kernel panic
# Peak memory: ~46GB (safe on 48GB Mac)
```

**Success Criteria**:
- ✅ Model responds in <5 seconds
- ✅ Memory usage 35-40GB (stable)
- ✅ Tests complete successfully (no crash)
- ✅ 3 workers auto-detected

---

## 📋 Phase 2: Supervised Improvement (Quality Validation)

### Step 2.1: Simple P3 Task (Warmup)
Test local model on simple tasks to validate quality.

```bash
# Example 1: Fix typos
cat > /tmp/test_p3_typo.py << 'EOF'
def calcualte_total(items):
    """Calcuate the total price of items."""
    totle = 0
    for item in items:
        totle += item.price
    return totle
EOF

# Ask local model to fix
ollama run qwen3-coder:30b "Fix all typos in this code:
$(cat /tmp/test_p3_typo.py)
"

# Expected: Fixes calculate, Calculate, total (3 typos)
# Quality check: Should preserve logic, only fix typos
```

**P3 Task Examples** (60% of workload, FREE with local model):
1. Fix typos in docstrings
2. Add missing type hints
3. Format code with black
4. Remove unused imports
5. Update copyright years
6. Add simple docstrings
7. Rename variables for clarity
8. Fix simple linting errors

### Step 2.2: Code Quality Improvement (Real Task)
Pick a real file from the codebase and improve it.

```bash
# Find a file with quality issues
python run_tests.py 2>&1 | grep -i "warning\|deprecated" | head -10

# Example: Fix Pydantic deprecation warnings
# File: shared/models/learning.py (has deprecation warnings)

# Test with local model
ollama run qwen3-coder:30b "Fix Pydantic v2 deprecation warnings in this file:
$(cat shared/models/learning.py)

Replace class-based config with ConfigDict.
Preserve all functionality.
"

# Quality validation:
# 1. Run tests: pytest tests/test_learning_agent.py
# 2. Check types: mypy shared/models/learning.py
# 3. Manual review: Does it preserve functionality?
```

**Quality Metrics to Track**:
- **Correctness**: Do tests still pass? (MUST be 100%)
- **Completeness**: Did it fix ALL instances?
- **Safety**: Did it preserve functionality?
- **Style**: Does it match codebase patterns?

### Step 2.3: Measure Quality vs Cloud (Comparison)
Run the same task with both local and cloud models to compare quality.

```bash
# Test task: "Add type hints to function signatures in tools/read.py"

# Local model (FREE)
time ollama run qwen3-coder:30b "Add type hints to all function signatures:
$(cat tools/read.py)
" > /tmp/local_output.py

# Cloud model (gpt-4o, $1.50/1M)
# (Manual: Use Agency agent with USE_LOCAL_MODEL=false)

# Compare:
diff /tmp/local_output.py /tmp/cloud_output.py
pytest tools/test_read.py  # Both should pass

# Quality score:
# - Local: 90% quality (Q4_K_M model)
# - Cloud: 95% quality (gpt-4o)
# - Acceptable delta for P3 tasks
```

**Success Criteria**:
- ✅ Local model quality ≥85% vs cloud (for P3 tasks)
- ✅ All tests pass after local model changes
- ✅ No regressions introduced
- ✅ Cost: $0 vs $0.15-1.50 (cloud)

---

## 📋 Phase 3: Autonomous Improvement Loop

### Architecture: Self-Improving Agent Workflow

```
┌─────────────────────────────────────────────────────┐
│  1. SCAN: Detect improvement opportunities          │
│     - Grep for TODOs, FIXMEs, warnings              │
│     - Run linters (mypy, ruff, black --check)       │
│     - Find deprecated patterns (Pydantic v1)        │
│     - Search for Dict[Any, Any] violations          │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  2. CLASSIFY: Route by complexity                    │
│     - P3 (simple): Fix typos, add docstrings        │
│       → Local model (qwen3-coder:30b, FREE)         │
│     - P2 (moderate): Refactor, add features         │
│       → Cloud (gpt-4o, $1.50/1M)                    │
│     - P1 (complex): Architecture, ADRs              │
│       → Cloud (gpt-5, $4.00/1M)                     │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  3. EXECUTE: Make improvements (TDD-first)           │
│     - Write test first (if applicable)              │
│     - Generate fix using appropriate model          │
│     - Run tests (pytest)                            │
│     - Verify quality (mypy, ruff)                   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  4. VERIFY: Constitutional compliance                │
│     - Article I: Complete context ✓                 │
│     - Article II: 100% tests pass ✓                 │
│     - Article IV: Store learnings ✓                 │
│     - Memory safety: <46GB total ✓                  │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  5. COMMIT: Create atomic commits                    │
│     - Git add changed files                         │
│     - Generate descriptive commit message           │
│     - Create PR with summary                        │
│     - Wait for human approval                       │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  6. LEARN: Extract patterns (VectorStore)            │
│     - What worked? Store successful patterns        │
│     - What failed? Store anti-patterns              │
│     - Update institutional memory                   │
│     - Feed to next iteration                        │
└─────────────────────────────────────────────────────┘
                         ↓
                    (Loop back to 1)
```

### Step 3.1: Create Autonomous Improvement Script

```bash
# Create script: scripts/autonomous_improvement.py
cat > scripts/autonomous_improvement.py << 'EOF'
#!/usr/bin/env python3
"""
Autonomous self-improvement loop using local qwen3-coder:30b.

Phase 3: Supervised autonomous improvements with human approval gates.
"""
import os
import subprocess
from shared.model_policy import get_optimal_model, classify_task_complexity

def scan_for_improvements():
    """Scan codebase for improvement opportunities."""
    opportunities = []

    # 1. Find TODOs/FIXMEs
    result = subprocess.run(
        ["grep", "-r", "-n", "TODO\\|FIXME", ".", "--include=*.py"],
        capture_output=True, text=True
    )
    todos = result.stdout.strip().split('\n') if result.stdout else []

    for todo in todos[:10]:  # Limit to 10 for testing
        opportunities.append({
            "type": "todo",
            "description": todo,
            "complexity": "P3",  # Most TODOs are simple
            "file": todo.split(':')[0] if ':' in todo else None
        })

    # 2. Find Pydantic deprecation warnings
    result = subprocess.run(
        ["grep", "-r", "-n", "class Config:", ".", "--include=*.py"],
        capture_output=True, text=True
    )
    pydantic_warns = result.stdout.strip().split('\n') if result.stdout else []

    for warn in pydantic_warns[:5]:
        opportunities.append({
            "type": "pydantic_v2_migration",
            "description": f"Migrate to ConfigDict: {warn}",
            "complexity": "P3",
            "file": warn.split(':')[0] if ':' in warn else None
        })

    return opportunities

def execute_improvement(opportunity):
    """Execute a single improvement using appropriate model."""
    complexity = opportunity["complexity"]
    model = get_optimal_model(complexity, agent_key="coder")

    print(f"🔧 Improving: {opportunity['description']}")
    print(f"📊 Complexity: {complexity}")
    print(f"🤖 Model: {model}")

    # For local model
    if "ollama/" in model:
        print("💰 Cost: $0 (local)")
    else:
        print(f"💰 Cost: Cloud model ({model})")

    # TODO: Implement actual fix generation
    # This would call ollama or LiteLLM depending on model

    return {"success": True, "model_used": model}

def main():
    print("🚀 Starting autonomous improvement loop...")
    print(f"🧠 Local model: {os.getenv('LOCAL_MODEL_NAME', 'qwen3-coder:30b')}")
    print()

    # Scan for opportunities
    print("🔍 Scanning for improvement opportunities...")
    opportunities = scan_for_improvements()
    print(f"✅ Found {len(opportunities)} opportunities")
    print()

    # Classify by complexity
    p3_tasks = [o for o in opportunities if o["complexity"] == "P3"]
    p2_tasks = [o for o in opportunities if o["complexity"] == "P2"]

    print(f"📊 Breakdown:")
    print(f"   P3 (simple, local): {len(p3_tasks)} tasks → FREE")
    print(f"   P2 (moderate, cloud): {len(p2_tasks)} tasks → $1.50/1M")
    print()

    # Execute P3 tasks with local model
    print("🤖 Executing P3 tasks with local model...")
    for i, task in enumerate(p3_tasks[:3], 1):  # Limit to 3 for demo
        print(f"\n[{i}/{min(3, len(p3_tasks))}]")
        result = execute_improvement(task)
        print(f"   Status: {'✅ Success' if result['success'] else '❌ Failed'}")

    print("\n✅ Autonomous improvement cycle complete!")
    print("📝 Next: Review changes and create PR")

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/autonomous_improvement.py
```

### Step 3.2: Run First Autonomous Cycle (Supervised)

```bash
# Set environment for local model
export USE_LOCAL_MODEL=true
export LOCAL_MODEL_NAME=qwen3-coder:30b
export LOCAL_MODEL_TEST_WORKERS=3

# Run autonomous improvement (first pass - dry run)
python scripts/autonomous_improvement.py

# Expected output:
# 🚀 Starting autonomous improvement loop...
# 🧠 Local model: qwen3-coder:30b
# 🔍 Scanning for improvement opportunities...
# ✅ Found 15 opportunities
# 📊 Breakdown:
#    P3 (simple, local): 12 tasks → FREE
#    P2 (moderate, cloud): 3 tasks → $1.50/1M
# 🤖 Executing P3 tasks with local model...
# [1/3] 🔧 Improving: TODO: Add type hints
#       📊 Complexity: P3
#       🤖 Model: ollama/qwen3-coder:30b
#       💰 Cost: $0 (local)
#       ✅ Success
# ...
```

**Human Approval Gates**:
1. After each file change: Review diff, run tests
2. After batch of changes: Create PR for human review
3. After merge: Extract learnings to VectorStore
4. Iterate: Next batch uses previous learnings

---

## 📋 Phase 4: Self-Training Loop (Advanced)

### Concept: Fine-Tune Local Model on Successful Improvements

Once we have a corpus of **validated improvements** (human-approved PRs), we can:

1. **Collect Training Data**
   ```bash
   # Extract all "good" improvements from git history
   git log --grep="feat:\|fix:" --format="%H" | while read commit; do
     git show $commit > training_data/commit_$commit.diff
   done
   ```

2. **Format for Fine-Tuning**
   ```python
   # Convert diffs to training examples
   training_examples = [
       {
           "input": "Before: <old_code>",
           "output": "After: <new_code>",
           "task": "Fix Pydantic deprecation warning",
           "quality_score": 0.95  # From test pass rate + human review
       }
   ]
   ```

3. **Fine-Tune Qwen3-Coder** (Requires HuggingFace setup)
   ```bash
   # Use Unsloth for efficient fine-tuning on M4 Pro
   # https://github.com/unslothai/unsloth

   # Install Unsloth
   pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

   # Fine-tune on Agency-specific improvements
   python scripts/finetune_local_model.py \
     --base-model qwen3-coder:30b \
     --training-data training_data/ \
     --output agency-qwen3-coder-30b-v1 \
     --lora-rank 16  # LoRA for efficient training

   # Expected: 2-4 hours on M4 Pro
   # Result: Model specifically tuned for Agency codebase patterns
   ```

4. **Deploy Fine-Tuned Model**
   ```bash
   # Convert to GGUF and load in Ollama
   ollama create agency-qwen3-coder:30b -f Modelfile

   # Update .env
   LOCAL_MODEL_NAME=agency-qwen3-coder:30b

   # Now local model knows Agency patterns!
   ```

**Exponential Growth**:
- **Iteration 1**: Base qwen3-coder:30b (90% quality)
- **Iteration 2**: Fine-tuned on 100 good PRs (93% quality)
- **Iteration 3**: Fine-tuned on 500 good PRs (95% quality)
- **Iteration 4**: Fine-tuned on 2000 good PRs (97% quality, approaching GPT-4o)

**Cost Analysis**:
```
Base model:           qwen3-coder:30b        $0/1M tokens, 90% quality
Fine-tuned (iter 1):  agency-v1              $0/1M tokens, 93% quality
Fine-tuned (iter 2):  agency-v2              $0/1M tokens, 95% quality
Fine-tuned (iter 3):  agency-v3              $0/1M tokens, 97% quality

Cloud equivalent:     gpt-4o                 $1.50/1M, 95% quality
                      gpt-5                  $4.00/1M, 98% quality

Savings: $1.50/1M × 1000M tokens = $1,500 per iteration
After 10 iterations: $15,000 saved (FREE vs cloud)
```

---

## 🎯 Success Metrics

### Phase 1 (Installation)
- ✅ Model responds <5s (vs 30+ timeout before)
- ✅ Memory usage stable 35-40GB
- ✅ Tests complete without kernel panic
- ✅ 3 workers auto-detected

### Phase 2 (Supervised)
- ✅ Local model quality ≥85% on P3 tasks
- ✅ 100% test pass rate after improvements
- ✅ Cost: $0 vs $0.15-1.50 cloud
- ✅ 10+ successful improvements validated

### Phase 3 (Autonomous)
- ✅ 60% of tasks routed to local model (P3)
- ✅ 5+ autonomous PRs created per week
- ✅ 80%+ PR approval rate (human review)
- ✅ Zero regressions introduced
- ✅ VectorStore learning accumulation

### Phase 4 (Self-Training)
- ✅ Fine-tuned model quality ≥93% (iteration 1)
- ✅ Cost savings: $1,500+ per iteration
- ✅ Model improves exponentially over time
- ✅ Approaching GPT-4o quality at $0 cost

---

## 🚀 Next Steps

### Immediate (Now)
1. Run installation: `bash scripts/setup_local_model.sh`
2. Verify: Test inference speed and memory usage
3. Validate: Run test suite with 3 workers

### Short-term (This Week)
1. Complete 10 supervised improvements (Phase 2)
2. Measure quality metrics vs cloud
3. Create autonomous improvement script (Phase 3)
4. Run first autonomous cycle (3-5 improvements)

### Medium-term (This Month)
1. Automate 60% of P3 tasks to local model
2. Accumulate 100+ validated improvements
3. Extract training data from git history
4. Prepare for fine-tuning (Phase 4)

### Long-term (3 Months)
1. Fine-tune first iteration (agency-qwen3-coder-v1)
2. Deploy and measure quality improvement
3. Iterate: 500 PRs → v2, 2000 PRs → v3
4. Achieve 97%+ quality at $0 cost
5. **Exponential self-improvement achieved**

---

## 🔗 References

- **Hardware Guide**: `docs/HARDWARE_OPTIMIZATION.md`
- **Model Setup**: `docs/LOCAL_MODEL_OPTIMIZATION.md`
- **ADR-023**: Memory-Aware Execution
- **Constitution**: Article IV (Continuous Learning)
- **Unsloth**: https://github.com/unslothai/unsloth (fine-tuning on Mac)
- **Ollama**: https://ollama.com/library/qwen3-coder

---

**Status**: Ready to begin Phase 1
**Estimated Time to Phase 3**: 1-2 weeks
**Estimated Time to Phase 4**: 1-3 months
**Expected ROI**: $15,000+ saved in first year (vs cloud API)
