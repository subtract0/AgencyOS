# TRM-7M Training Pipeline - Task Graph Visualization

## Mission Overview
**Goal**: Train local models (qwen3coder-30b or gpt-oss-20b) to effectively use TRM-7M for recursive reasoning tasks

**Source**: 659 JSON training examples from `weirdly-numbered-json-contents.md`

**Expected Outcome**:
- 85%+ routing accuracy in shadow mode
- 40-60% churn reduction from TRM validation gates
- $0 inference cost (local model)
- <1s latency per validation

---

## Task Graph (Mermaid DAG)

```mermaid
graph TD
    %% Phase 1: Data Extraction
    A1[create_extraction_script<br/>Tier 2 | Code]
    A2[run_extraction<br/>Tier 2 | Code]
    A3[test_extraction<br/>Tier 2 | Test]

    A1 --> A2
    A1 --> A3

    %% Phase 2: Sampling
    B1[create_sampling_script<br/>Tier 2 | Code]
    B2[run_sampling<br/>Tier 2 | Code]
    B3[test_sampling<br/>Tier 2 | Test]

    A2 --> B1
    B1 --> B2
    B1 --> B3

    %% Phase 3: Auto-Labeling
    C1[create_labeling_prompt<br/>Tier 1 | Spec]
    C2[create_auto_labeler<br/>Tier 1 | Code]
    C3[run_auto_labeling<br/>Tier 1 | Code]
    C4[test_auto_labeler<br/>Tier 2 | Test]

    B2 --> C1
    C1 --> C2
    C2 --> C3
    C2 --> C4

    %% Checkpoint 1
    CKPT1{Human Review<br/>Auto-Label Quality}
    C3 --> CKPT1

    %% Phase 4: Human Review
    D1[create_labeling_rubric<br/>Tier 2 | Spec]
    D2[create_review_cli<br/>Tier 2 | Code]
    D3[test_review_cli<br/>Tier 2 | Test]

    CKPT1 --> D1
    D1 --> D2
    D2 --> D3

    %% Phase 5: Training Data Prep
    E1[create_merge_script<br/>Tier 2 | Code]
    E2[run_merge<br/>Tier 2 | Code]
    E3[create_quality_validator<br/>Tier 2 | Code]
    E4[test_quality_validator<br/>Tier 2 | Test]

    D2 --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4

    %% Checkpoint 2
    CKPT2{Human Review<br/>Dataset Quality}
    E4 --> CKPT2

    %% Phase 6: Model Training
    F1[create_training_config<br/>Tier 1 | Spec]
    F2[create_training_script<br/>Tier 1 | Code]
    F3[create_inference_wrapper<br/>Tier 2 | Code]
    F4[test_training<br/>Tier 2 | Test]

    CKPT2 --> F1
    E2 --> F1
    F1 --> F2
    F2 --> F3
    F2 --> F4

    %% Phase 7: Shadow Mode
    G1[create_shadow_mode<br/>Tier 1 | Code]
    G2[create_telemetry_dashboard<br/>Tier 2 | Code]
    G3[create_retraining_loop<br/>Tier 1 | Code]
    G4[test_shadow_mode<br/>Tier 2 | Test]

    F3 --> G1
    G1 --> G2
    G2 --> G3
    G1 --> G4

    %% Checkpoint 3
    CKPT3{Human Review<br/>Shadow Mode Metrics}
    G3 --> CKPT3

    %% Phase 8: Integration
    H1[update_model_policy<br/>Tier 1 | Code]
    H2[create_trm_agent<br/>Tier 1 | Code]
    H3[update_primea_protocol<br/>Tier 1 | Code]
    H4[test_integration<br/>Tier 1 | Test]

    CKPT3 --> H1
    G1 --> H1
    H1 --> H2
    H2 --> H3
    H3 --> H4

    %% Phase 9: Documentation
    I1[create_adr<br/>Tier 1 | Spec]
    I2[create_user_guide<br/>Tier 2 | Spec]
    I3[update_readme<br/>Tier 2 | Code]

    H4 --> I1
    I1 --> I2
    I2 --> I3

    %% Styling
    classDef tier1 fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef tier2 fill:#4dabf7,stroke:#1971c2,color:#fff
    classDef checkpoint fill:#ffd43b,stroke:#f08c00,color:#000
    classDef spec fill:#a9e34b,stroke:#5c940d,color:#000
    classDef code fill:#74c0fc,stroke:#1864ab,color:#000
    classDef test fill:#ff8787,stroke:#e03131,color:#fff

    class C1,C2,C3,F1,F2,G1,G3,H1,H2,H3,H4,I1 tier1
    class A1,A2,A3,B1,B2,B3,C4,D1,D2,D3,E1,E2,E3,E4,F3,F4,G2,G4,I2,I3 tier2
    class CKPT1,CKPT2,CKPT3 checkpoint
```

---

## Phase Breakdown

### Phase 1: Data Extraction & Quality Assessment (3 tasks)
**Goal**: Extract all 659 JSON objects from messy source file

**Key Tasks**:
- `create_extraction_script`: Robust JSON parsing with Unicode normalization
- `run_extraction`: Execute extraction → `data/seed.jsonl`
- `test_extraction`: Validate 100% extraction rate

**Outputs**: `data/seed.jsonl` (659+ objects)

---

### Phase 2: Heuristic Sampling (3 tasks)
**Goal**: Sample 200 most complex examples for maximum information gain

**Key Tasks**:
- `create_sampling_script`: Complexity scoring (length + keywords)
- `run_sampling`: Top 200 samples → `data/sample_200.jsonl`
- `test_sampling`: Validate scoring + diversity

**Keywords**: graph, dag, csp, sat, knapsack, schedule, invariant, recurs, prove, edge, dependency, constraint, shortest, optimal, induct, contradiction

**Outputs**: `data/sample_200.jsonl` (200 high-complexity objects)

---

### Phase 3: Automated Labeling (4 tasks)
**Goal**: Pre-label 200 samples with GPT-5 CODEX

**Key Tasks**:
- `create_labeling_prompt`: TRM routing decision template
- `create_auto_labeler`: Batch API integration
- `run_auto_labeling`: Execute → `data/auto_200.jsonl`
- `test_auto_labeler`: Validate API usage + output

**Labeling Rules**:
- **1 (YES)**: Deep logical/recursive/constraint tasks (graphs, SAT, proofs, edge-case inference)
- **0 (NO)**: Simple I/O, formatting, trivial unit work

**Outputs**: `data/auto_200.jsonl` (200 auto-labeled objects)

**Checkpoint 1**: Human review of auto-label quality (check balance, sample correctness)

---

### Phase 4: Human Review Protocol (3 tasks)
**Goal**: Build interface for human review/correction of auto-labels

**Key Tasks**:
- `create_labeling_rubric`: One-page guide + 10 gold examples
- `create_review_cli`: Interactive terminal UI for label correction
- `test_review_cli`: Validate CLI functionality

**Review Protocol**:
- Batch size: 50-100 labels per session (prevent fatigue)
- Auto-save every 10 reviews
- Optional notes field for edge cases

**Outputs**: `data/labeled_200.jsonl` (human-reviewed labels)

---

### Phase 5: Training Data Preparation (4 tasks)
**Goal**: Merge auto + human labels, validate quality

**Key Tasks**:
- `create_merge_script`: Human overrides auto, deduplicate
- `run_merge`: Execute → `learning/trm_labels.jsonl`
- `create_quality_validator`: Check balance, diversity, schema
- `test_quality_validator`: Validate quality checks

**Quality Criteria**:
- Label balance: 30-70% for each class (avoid imbalance)
- Keyword diversity: All 17 keywords represented
- No data leakage (test data in training)

**Outputs**: `learning/trm_labels.jsonl` (200+ final labeled objects)

**Checkpoint 2**: Human review of dataset quality before expensive training

---

### Phase 6: Local Model Fine-tuning (4 tasks)
**Goal**: Fine-tune qwen3coder-30b or gpt-oss-20b with LoRA

**Key Tasks**:
- `create_training_config`: LoRA params, learning rate, batch size
- `create_training_script`: Hugging Face + PEFT training
- `create_inference_wrapper`: Lightweight router wrapper
- `test_training`: Validate training correctness

**Training Config**:
- **LoRA**: rank=8, alpha=16 (memory efficient)
- **Batch size**: 4 (fits in 48GB M4 Pro)
- **Epochs**: 3-5 (prevent overfitting on 200 samples)
- **Split**: 80/20 train/val
- **Time**: <2 hours on M4 Pro

**Outputs**: `models/trm_router_lora/` (LoRA adapter)

---

### Phase 7: Shadow Mode Deployment (4 tasks)
**Goal**: Run TRM router in parallel with production, collect telemetry

**Key Tasks**:
- `create_shadow_mode`: Parallel routing without production impact
- `create_telemetry_dashboard`: Visualize agreement rate, confusion matrix
- `create_retraining_loop`: Auto-trigger retraining if agreement <85%
- `test_shadow_mode`: Validate zero production impact

**Metrics Tracked**:
- Agreement rate (7-day rolling window)
- Confusion matrix (TRM vs production)
- Hypothetical cost savings if TRM were live

**Outputs**: `logs/shadow_mode/routing_deltas.jsonl`, `dashboard.html`

**Checkpoint 3**: Human review of shadow mode metrics after 1 week

---

### Phase 8: Agency Orchestrator Integration (4 tasks)
**Goal**: Integrate TRM router into production workflow

**Key Tasks**:
- `update_model_policy`: TRM router before Leap 3 router
- `create_trm_agent`: TRM-7M agent wrapper
- `update_primea_protocol`: Add 4 TRM validation checkpoints
- `test_integration`: End-to-end integration tests

**TRM Validation Gates** (Leap 8):
1. **Checkpoint 1**: DAG validation (circular dependencies)
2. **Checkpoint 2**: Type constraint validation (Dict[Any, Any])
3. **Checkpoint 3**: Edge case inference (test coverage)
4. **Checkpoint 4**: Lint/format pre-validation

**Outputs**: Updated `shared/model_policy.py`, `coding_agent/trm_agent.py`, `.claude/commands/primea.md`

---

### Phase 9: Documentation (3 tasks)
**Goal**: Document entire pipeline for future users

**Key Tasks**:
- `create_adr`: ADR-034 for architectural decisions
- `create_user_guide`: Step-by-step training guide
- `update_readme`: Add TRM training section to CLAUDE.md

**Documentation Outputs**:
- `docs/adr/ADR-034-trm-training-pipeline.md`
- `docs/TRM_TRAINING_GUIDE.md`
- Updated `CLAUDE.md`

---

## Execution Instructions

### Option 1: Execute with /primeA (Recommended)
```bash
/primeA --graph missions/trm_training_pipeline.json --visualize
```

### Option 2: Manual Execution (Step-by-Step)
```bash
# Phase 1: Extraction
python scripts/extract_weird_jsonl.py weirdly-numbered-json-contents.md data/seed.jsonl

# Phase 2: Sampling
python scripts/sample_for_labeling.py data/seed.jsonl data/sample_200.jsonl 200

# Phase 3: Auto-Labeling
python scripts/auto_label_batch.py data/sample_200.jsonl data/auto_200.jsonl

# Phase 4: Human Review
python scripts/manual_label_cli.py data/auto_200.jsonl data/labeled_200.jsonl

# Phase 5: Merge & Validate
python scripts/merge_labels.py data/auto_200.jsonl data/labeled_200.jsonl learning/trm_labels.jsonl
python scripts/validate_training_data.py learning/trm_labels.jsonl

# Phase 6: Training
python scripts/train_router.py --model qwen3coder-30b --data learning/trm_labels.jsonl --output models/trm_router_lora

# Phase 7: Shadow Mode (1 week)
python scripts/shadow_mode.py --router models/trm_router_lora --duration 7d

# Phase 8: Integration
python scripts/deploy_trm_router.py --router models/trm_router_lora --mode production
```

---

## Success Metrics

### Training Phase
- ✅ Extraction: 659+ objects from source file
- ✅ Sampling: 200 high-complexity examples
- ✅ Auto-labeling: 200 labeled objects
- ✅ Human review: 80%+ agreement with auto-labels
- ✅ Quality: 30-70% label balance, all keywords represented
- ✅ Training: 85%+ validation accuracy

### Shadow Mode
- ✅ Agreement rate: 85%+ with production router
- ✅ Precision: 80%+ (true positives / all positives)
- ✅ Recall: 80%+ (true positives / all actual positives)
- ✅ Latency: <500ms inference time

### Production Integration
- ✅ Churn reduction: 40-60% fewer test cycles
- ✅ Cost savings: $0 inference (local model)
- ✅ Validation speed: <1s per checkpoint
- ✅ Zero production impact: No errors, no latency increase

---

## Cost Analysis

### One-Time Costs
- **Auto-labeling** (GPT-5 CODEX): ~$2.50 (200 samples × ~500 tokens × $0.025/1k)
- **Training compute**: $0 (local M4 Pro, 2 hours)
- **Human review**: ~2-3 hours (200 samples @ 50-100/session)

### Ongoing Costs
- **Inference**: $0 (local model, 7M params)
- **Retraining**: ~$2.50 every 2-4 weeks (if needed)

### Cost Savings (vs Cloud API)
- **Before**: $40k/month (all gpt-5) → $1.6k/month (Leap 3 router, 96% savings)
- **After**: $1.6k/month → $1.4k/month (98% savings with TRM router)
- **Additional 2% savings** from TRM routing + 40-60% churn reduction

---

## Constitutional Compliance

### Article I: Complete Context Before Action
- ✅ All 659 examples extracted (no data loss)
- ✅ Human review checkpoints prevent premature training

### Article II: 100% Verification
- ✅ All tests pass before production integration
- ✅ Shadow mode validates accuracy before promotion

### Article III: Automated Enforcement
- ✅ Quality validator blocks imbalanced datasets
- ✅ Shadow mode auto-triggers retraining if agreement <85%

### Article IV: Continuous Learning
- ✅ VectorStore stores TRM routing patterns (confidence ≥0.6)
- ✅ Auto-retraining loop from shadow mode discrepancies

### Article V: Spec-Driven Development
- ✅ Task graph is the specification
- ✅ All tasks trace to acceptance criteria

---

## Next Steps After Completion

1. **Review shadow mode metrics** (1 week of telemetry)
2. **Decide: promote to production or retrain** (based on agreement rate)
3. **If promoted**: Enable `USE_TRM_ROUTER=true` in `.env`
4. **Monitor churn reduction**: Track validation effectiveness over 2 weeks
5. **Propose Leap 9**: Cross-graph learning with TRM patterns

---

**Generated**: 2025-10-24
**Leap**: 8 (TRM-7M Recursive Reasoning Validation)
**Status**: Ready for execution
