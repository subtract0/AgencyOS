# Hybrid TRM Training Plan

⚠️ **STATUS: PIVOT COMPLETE - See Esper3.1 QLoRA Training Instead**

**Original Plan**: Router + Delegation + Fine-tuned 13B TRM executor
**Reality Check**: TRM is for grid puzzles (ARC-AGI), not coding/DevOps tasks
**New Strategy**: Train Esper3.1 QLoRA adapters on 1,102 algorithm examples

📖 **See**:
- `docs/TRM_REALITY_CHECK.md` - Why TRM doesn't fit
- `docs/ESPER31_TRAINING_COMPLETE_GUIDE.md` - Complete training guide
- `docs/ESPER31_ALGORITHM_TRAINING.md` - Original rationale

🚀 **Quick Start**: `bash scripts/run_esper31_training_pipeline.sh`

---

## Original TRM Plan (Archived)

**Timeline**: 6-8 weeks
**Goal**: Router + Delegation + Fine-tuned 13B TRM executor
**Constraints**: M4 Pro 48GB, local-first, <$50 total cost
**Status**: ⛔ CANCELED - TRM unsuitable for coding domain

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ User Task: "Find shortest path from A to C in graph..."    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ Router (Binary Classifier + Task Type Classifier)          │
│ - Input: instruction + input                                │
│ - Output: {use_trm: 1, task_type: "GRAPH", confidence: 0.9}│
│ - Model: GPT-5 few-shot OR fine-tuned 7M classifier        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├─ use_trm = 0 ──> Generalist (GPT-5)
                  │
                  └─ use_trm = 1 ──> Delegation Layer
                                      │
                                      ▼
                  ┌───────────────────────────────────────────┐
                  │ Delegation Layer                          │
                  │ - Generalist formats task using template  │
                  │ - Output: canonical TRM JSON              │
                  └─────────────┬─────────────────────────────┘
                                │
                                ▼
                  ┌───────────────────────────────────────────┐
                  │ TRM Executor (Qwen3-Coder-13B Q4 + QLoRA) │
                  │ - Processes canonical TRM task            │
                  │ - Outputs: structured response + proof    │
                  └─────────────┬─────────────────────────────┘
                                │
                                ▼
                  ┌───────────────────────────────────────────┐
                  │ Verification Layer                        │
                  │ - Runs local_checks                       │
                  │ - Pass → return; Fail → fallback          │
                  └───────────────────────────────────────────┘
```

---

## Phase 1: Router Training (Week 1-2)

### Objective
Train binary classifier: task → {use_trm: 0/1, task_type, confidence}

### Data Requirements

**Positive Examples** (TRM-suitable):
- 200 GRAPH tasks (shortest path, cycle detection, topological sort)
- 100 SAT tasks (2-SAT, 3-SAT, small instances)
- 100 CSP tasks (graph coloring, scheduling, N-queens)
- 50 INDUCTIVE_PROOF tasks (loop invariants, termination)
- 50 ALG tasks (knapsack, scheduling, optimization)

**Negative Examples** (Generalist-suitable):
- 250 file I/O tasks (read, write, format)
- 100 API calls (HTTP, REST, GraphQL)
- 100 text processing (summarization, translation)
- 50 code generation (non-formal, heuristic)

**Total**: 1,000 labeled examples (50/50 balance)

### Labeling Strategy

**Option A**: GPT-5 auto-labeling (our existing approach)
- Cost: $1.50 for 1,000 samples (gpt-5 pricing)
- Prompt: "Classify this task. TRM-suitable = formal reasoning, deterministic, verifiable. Generalist-suitable = heuristic, creative, I/O."

**Option B**: Rule-based heuristics + manual review
- Heuristics: keyword detection (graph, SAT, CSP, proof)
- Manual review: 200 samples for calibration
- Cost: 3-4 hours human time

**Recommendation**: Option A (faster, cheaper than human time)

### Training Approach

**Model Choice**:
1. **GPT-5 few-shot** (zero training cost, baseline)
   - Provide 10 positive + 10 negative examples in prompt
   - Evaluate on 200-sample test set
   - Expected accuracy: 85-90%

2. **Fine-tuned 7M classifier** (if few-shot insufficient)
   - Base: DistilBERT or small T5 (7M params)
   - Training: 800 samples, validation: 200
   - Hardware: CPU-only, <1 hour on M4 Pro
   - Expected accuracy: 92-95%

**Start with Option 1**, upgrade to Option 2 if needed.

### Success Criteria
- **Precision**: >90% (low false positive rate for TRM usage)
- **Recall**: >85% (catch most TRM-suitable tasks)
- **Task Type Accuracy**: >90% (correct classification into 6 types)

### Deliverables
- `data/router_train_1000.jsonl` (labeled dataset)
- `scripts/train_router.py` (training script if fine-tuning)
- `learning/router_evaluation_report.json` (metrics)

---

## Phase 2: Delegation Layer Training (Week 2-3)

### Objective
Train Generalist to produce canonical TRM task format

### Data Requirements

**Format**: Instruction-following dataset
```jsonl
{"messages": [
  {"role": "system", "content": "Convert tasks to TRM canonical format."},
  {"role": "user", "content": "Find shortest path A→C. Graph: A-B:3, B-C:2, A-C:8."},
  {"role": "assistant", "content": "{\"task_id\":\"...\",\"task_type\":\"GRAPH\",...}"}
]}
```

**Samples needed**: 200 examples (covering all 6 task types)
- 60 GRAPH delegation examples
- 40 SAT delegation examples
- 40 CSP delegation examples
- 20 INDUCTIVE_PROOF delegation examples
- 20 ALG delegation examples
- 20 VERIFICATION delegation examples

### Data Generation Strategy

**Synthetic Generation** (GPT-5 with template):
```python
# Prompt GPT-5:
# "Generate 60 examples of natural language graph tasks and their canonical TRM format.
# Use the delegation template from learning/trm_delegation_template.txt.
# Ensure diverse task types: shortest path, cycle detection, topological sort, etc."
```

**Cost**: ~$0.50 for 200 synthetic examples

### Training Approach

**No fine-tuning needed** - use few-shot prompting:
- Store 200 examples in VectorStore
- At runtime: retrieve 3-5 most similar examples
- Generalist uses examples + template to format task

**Alternative** (if quality insufficient):
- Fine-tune GPT-5-mini with QLoRA adapters (~50MB)
- Training time: 2-3 hours on M4 Pro
- Cost: $0 (local fine-tuning)

### Success Criteria
- **Schema Validity**: >98% of outputs parse as valid JSON
- **Field Completeness**: >95% include all required fields
- **Canonical Encoding**: >90% use correct canonical format (sorted nodes, etc.)

### Deliverables
- `data/delegation_train_200.jsonl` (synthetic dataset)
- `learning/delegation_few_shot_examples.json` (for retrieval)
- `scripts/validate_delegation.py` (schema validator)

---

## Phase 3: TRM Executor Fine-Tuning (Week 3-5)

### Objective
Fine-tune Qwen3-Coder-13B Q4 with QLoRA adapters for TRM task execution

### Base Model Setup

**Model**: `Qwen3-Coder-13B-Instruct-Q4_K_M`
- Size: ~8GB (Q4 quantization)
- Framework: MLX or llama.cpp (Metal-optimized)
- Memory: 8GB (model) + 4GB (KV cache) + 2GB (overhead) = 14GB
- **Fits comfortably** in 48GB M4 Pro

### QLoRA Configuration

```yaml
# qlora_config.yaml
base_model: "Qwen/Qwen3-Coder-13B-Instruct"
quantization: "4bit"
lora_config:
  r: 16                    # LoRA rank
  lora_alpha: 32           # Scaling factor
  lora_dropout: 0.05
  target_modules:
    - q_proj
    - v_proj
    - k_proj
    - o_proj
  bias: "none"

training:
  batch_size: 1            # Gradient accumulation = 8 for effective batch 8
  gradient_accumulation: 8
  learning_rate: 2e-4
  epochs: 3
  warmup_steps: 100
  save_steps: 500
  eval_steps: 200

hardware:
  device: "mps"            # Metal Performance Shaders (M4 Pro)
  mixed_precision: "fp16"
  max_memory_mb: 16000     # 16GB allocation
```

**Adapter Size**: ~100-200MB (vs 8GB base model)

### Training Data

**Curriculum-Based Approach** (inspired by GPT-5 blueprint):

**Stage 0: Foundation (500 examples, 3 days)**
- Deterministic micro-tasks
- GRAPH: shortest path on 4-6 nodes
- SAT: 2-SAT, 3-SAT with ≤5 variables
- CSP: graph coloring with ≤5 nodes, 3 colors
- Expected: Model learns canonical input/output format

**Stage 1: Structural Encoding (200 examples, 2 days)**
- Teach canonical encodings
- Node/edge serialization
- Variable ordering (lexicographic)
- Constraint normalization

**Stage 2: Memoization Patterns (100 examples, 2 days)**
- Repeated subproblems
- Example: Fibonacci with memo vs naive
- Example: Dynamic programming (knapsack subproblems)

**Stage 3: Verification (80 examples, 2 days)**
- Include proof artifacts in output
- Loop invariants with base case + inductive step
- Graph proofs with path validation

**Total Training Data**: ~880 examples across 4 stages

### Data Generation

**Hybrid approach**:

1. **30 seed examples** (from GPT-5 blueprint):
   - `learning/trm_curriculum_seed_30.jsonl` (C1-C30)

2. **Permutation generator** (auto-generate variants):
   ```python
   # For each seed task, generate 10-20 variants
   # Example: "Shortest path A→C" → generate with B→D, X→Y, etc.
   # Script: scripts/generate_trm_curriculum_variants.py
   ```

3. **Synthetic augmentation** (GPT-5):
   - Generate 200 additional complex examples
   - Cost: ~$1.00

**Total Cost**: ~$1.00 for data generation

### Training Time

- **Stage 0**: 500 examples × 3 epochs = 1,500 steps @ ~2s/step = **50 minutes**
- **Stage 1-3**: 380 examples × 3 epochs = 1,140 steps @ ~2s/step = **40 minutes**
- **Total**: ~90 minutes per full curriculum pass
- **With 3 curriculum passes**: ~4.5 hours

### Success Criteria

- **Output Schema Compliance**: >95%
- **Local Checks Pass Rate**: >90%
- **Memoization Hit Rate**: >30% (on recursive subproblems)
- **Latency**: <1s per task (local inference)

### Deliverables

- `data/trm_curriculum_880.jsonl` (full training dataset)
- `models/qwen3-coder-13b-trm-qlora/` (adapter weights ~200MB)
- `scripts/train_trm_qlora.py` (training script)
- `learning/trm_training_report.json` (loss curves, metrics)

---

## Phase 4: Verification Layer (Week 5-6)

### Objective
Implement local_checks executor with sandboxing

### Components

1. **Schema Validator**
   ```python
   def validate_output_schema(output: str, expected_schema: str) -> bool:
       """Parse JSON, check against expected schema."""
       try:
           parsed = json.loads(output)
           schema = json.loads(expected_schema)
           # Validate keys, types
           return True
       except:
           return False
   ```

2. **Local Checks Executor**
   ```python
   def execute_local_checks(
       output: Dict,
       checks: List[str],
       timeout: int = 5
   ) -> Tuple[bool, List[str]]:
       """Execute checks with sandboxing (restricted builtins)."""
       restricted_globals = {
           "__builtins__": {
               "len": len,
               "sum": sum,
               "all": all,
               "any": any,
               "range": range,
           }
       }

       passed_checks = []
       for check in checks:
           try:
               result = eval(check, restricted_globals, {"output": output})
               if result:
                   passed_checks.append(check)
           except Exception as e:
               # Check failed or unsafe
               return False, passed_checks

       return len(passed_checks) == len(checks), passed_checks
   ```

3. **Fallback Strategy**
   ```python
   def execute_with_fallback(task, trm_executor, generalist):
       """Try TRM, fallback to Generalist if verification fails."""
       trm_output = trm_executor(task)

       valid_schema = validate_output_schema(
           trm_output, task["expected_output_schema"]
       )

       if not valid_schema:
           logger.warning(f"TRM schema invalid for {task['task_id']}")
           return generalist(task["original_instruction"])

       checks_pass, passed = execute_local_checks(
           trm_output, task["local_checks"]
       )

       if not checks_pass:
           logger.warning(f"TRM checks failed: {passed}/{len(task['local_checks'])}")
           return generalist(task["original_instruction"])

       return trm_output
   ```

### Testing

**Unit Tests** (50 tests):
- Schema validation (valid/invalid JSON)
- Local checks execution (safe/unsafe code)
- Sandboxing (prevent file access, network, imports)
- Fallback logic (TRM fail → Generalist success)

**Integration Tests** (20 tests):
- End-to-end: Router → Delegation → TRM → Verification
- Memoization cache hits
- Performance (latency <1s)

### Success Criteria

- **Unit Test Pass**: 50/50 (100%)
- **Integration Test Pass**: 20/20 (100%)
- **Verification Safety**: 0 sandbox escapes
- **Fallback Rate**: <10% (most TRM outputs valid)

### Deliverables

- `tools/trm_verification.py` (verification layer)
- `tests/test_trm_verification.py` (50 unit tests)
- `tests/test_trm_integration.py` (20 integration tests)

---

## Phase 5: Integration & Shadow Mode (Week 6-8)

### Objective
Deploy TRM in shadow mode, measure agreement with Generalist

### Shadow Mode Design

```python
def shadow_mode_execute(task):
    """Run both TRM and Generalist, log agreement."""

    # Production: Use Generalist
    generalist_output = generalist(task)

    # Shadow: Try TRM (non-blocking)
    router_decision = router(task)
    if router_decision["use_trm"] == 1:
        delegated_task = delegation_layer(task, router_decision["task_type"])
        trm_output = trm_executor(delegated_task)

        # Log agreement
        agreement = compare_outputs(generalist_output, trm_output)
        log_telemetry({
            "task_id": task["id"],
            "router_decision": router_decision,
            "trm_output": trm_output,
            "generalist_output": generalist_output,
            "agreement": agreement,
            "timestamp": datetime.utcnow().isoformat()
        })

    return generalist_output  # Always return Generalist (safe)
```

### Metrics Tracking

**Key Metrics**:
- **Agreement Rate**: % of tasks where TRM == Generalist
- **TRM Latency**: Time from delegation → verification
- **Memoization Hit Rate**: % of subproblems cached
- **Verification Pass Rate**: % passing local_checks
- **Cost Savings** (projected): TRM usage × $0 vs Generalist cost

**Dashboard** (learning_dashboard.py):
```
TRM Shadow Mode Telemetry (Last 7 Days)
==========================================
Total Tasks: 1,247
Router Decisions: 342 TRM (27.4%), 905 Generalist (72.6%)
Agreement Rate: 312/342 (91.2%) ✅
Verification Pass Rate: 324/342 (94.7%) ✅
Avg TRM Latency: 0.7s
Memoization Hits: 89/342 (26.0%)
Projected Cost Savings: $47.20/week
```

### Success Criteria (Production Cutover)

- **Agreement Rate**: >85% (TRM outputs match Generalist)
- **Verification Pass**: >90%
- **Latency**: <1s median, <2s p95
- **Memoization Hit Rate**: >20%
- **Zero Regressions**: No task failures caused by TRM

### Deliverables

- `tools/trm_shadow_mode.py` (shadow execution)
- `tools/trm_telemetry_dashboard.py` (metrics dashboard)
- `logs/trm_shadow_mode/` (telemetry logs)
- `docs/TRM_SHADOW_MODE_REPORT.md` (7-day analysis)

---

## Phase 6: Production Deployment (Week 8)

### Cutover Decision

**Required**:
- ✅ Agreement rate >85%
- ✅ Verification pass >90%
- ✅ Zero regressions in shadow mode
- ✅ User approval for production deployment

**Deployment**:
```python
def production_execute(task):
    """Production: Use TRM if router decides, else Generalist."""

    router_decision = router(task)

    if router_decision["use_trm"] == 1 and router_decision["confidence"] > 0.8:
        delegated_task = delegation_layer(task, router_decision["task_type"])
        trm_output = trm_executor(delegated_task)

        # Verify
        if verify(trm_output, delegated_task["local_checks"]):
            log_telemetry({"source": "TRM", "task_id": task["id"]})
            return trm_output
        else:
            # Fallback
            log_telemetry({"source": "Generalist", "reason": "verification_failed"})
            return generalist(task)
    else:
        log_telemetry({"source": "Generalist", "reason": "router_decision"})
        return generalist(task)
```

### Monitoring (Post-Deployment)

- **Daily metrics review**: Agreement, latency, cost savings
- **Weekly retraining**: Add new TRM-successful tasks to training set
- **Monthly calibration**: Update router thresholds, delegation templates

### Deliverables

- `tools/trm_production.py` (production executor)
- `docs/TRM_DEPLOYMENT_GUIDE.md` (deployment runbook)
- `docs/TRM_MONITORING_PLAYBOOK.md` (SRE playbook)

---

## Cost Analysis

### One-Time Costs

| Phase | Item | Cost |
|-------|------|------|
| Phase 1 | Router data labeling (GPT-5) | $1.50 |
| Phase 2 | Delegation data generation (GPT-5) | $0.50 |
| Phase 3 | TRM curriculum augmentation (GPT-5) | $1.00 |
| **Total** | | **$3.00** |

### Ongoing Costs

- **TRM Training** (QLoRA): $0 (local on M4 Pro, ~4.5 hours)
- **TRM Inference**: $0 (local on M4 Pro, <1s per task)
- **Electricity** (M4 Pro @ 30W for 100 hours): ~$0.30

### Total Project Cost: **~$5**

### ROI

**Current** (100% Generalist @ $4.00/1M tokens):
- 10,000 tasks/month × 500 tokens avg = 5M tokens
- Cost: $20/month

**With TRM** (30% TRM usage @ $0, 70% Generalist):
- TRM: 3,000 tasks × $0 = $0
- Generalist: 7,000 tasks × 500 tokens × $4.00/1M = $14
- **Cost: $14/month**
- **Savings: $6/month (30% reduction)**

**Payback Period**: ~1 month

---

## Risk Mitigation

### Risk 1: Agreement Rate <85%

**Mitigation**:
- Expand training data (Stage 0 → 1,000 examples)
- Fine-tune delegation layer (QLoRA adapters)
- Lower confidence threshold (0.8 → 0.6)

### Risk 2: M4 Pro Memory Constraints

**Mitigation**:
- Use Q4 quantization (8GB vs 13GB for Q8)
- Reduce batch size (1 → gradient accumulation 16)
- Offload KV cache to RAM if needed

### Risk 3: Latency >1s

**Mitigation**:
- Use Metal-optimized inference (MLX framework)
- Enable memoization caching (Redis or local dict)
- Profile hot paths (llama.cpp profiler)

### Risk 4: Low Memoization Hit Rate

**Mitigation**:
- Improve canonical encoding (stricter sorting)
- Expand cache TTL (1 hour → 24 hours)
- Pre-warm cache with common subproblems

---

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Router Training | `data/router_train_1000.jsonl`, `learning/router_evaluation_report.json` |
| 2-3 | Delegation Layer | `data/delegation_train_200.jsonl`, `scripts/validate_delegation.py` |
| 3-5 | TRM Fine-Tuning | `data/trm_curriculum_880.jsonl`, `models/qwen3-coder-13b-trm-qlora/` |
| 5-6 | Verification Layer | `tools/trm_verification.py`, `tests/test_trm_verification.py` (50 tests) |
| 6-8 | Shadow Mode | `tools/trm_shadow_mode.py`, `docs/TRM_SHADOW_MODE_REPORT.md` |
| 8 | Production Deploy | `tools/trm_production.py`, `docs/TRM_DEPLOYMENT_GUIDE.md` |

**Total Duration**: 6-8 weeks (depending on shadow mode validation)

---

## Next Steps

1. **Review this plan** with user for approval
2. **Generate router training data** (1,000 samples via GPT-5)
3. **Create delegation synthetic dataset** (200 samples)
4. **Set up QLoRA training environment** (MLX or llama.cpp on M4 Pro)
5. **Implement verification layer** with sandboxing
6. **Begin Phase 1** (Router Training)

**Ready to proceed?** User feedback requested on:
- Timeline feasibility (6-8 weeks realistic?)
- Cost budget ($5 one-time acceptable?)
- Any missing components or concerns?
