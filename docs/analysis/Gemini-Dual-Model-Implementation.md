# Gemini Dual-Model Trinity Implementation

**Date**: 2025-10-07
**Status**: IMPLEMENTING
**Based On**: Gemini Strategic Analysis (docs/A-Strategic-Framework-for-a-Hybrid-Autonomous-Trinity-on-Apple-Silicon.md)

---

## 🎯 Strategy Overview

Gemini's analysis concluded that **specialized dual-model architecture** outperforms single-model approach for M4 Pro (48GB RAM) systems.

### Core Principle

> "No single model excels equally at all three Trinity roles. Different roles require different strengths."

### The Optimal Configuration

| Role | Model | VRAM | Strengths | Score |
|------|-------|------|-----------|-------|
| **FIXER** | DeepSeek-Coder-V2-Lite-Instruct | ~10GB | • 338 programming languages<br>• Specialized coding benchmarks<br>• Superior for code generation/repair | FIXER: 5/5 |
| **AUDITOR** | GPT-OSS-20B | ~11.7GB | • Agentic reasoning architecture<br>• Full Chain-of-Thought transparency<br>• Adjustable reasoning effort | AUDITOR: 5/5 |
| **LEARNER** | GPT-OSS-20B | ~11.7GB | • Knowledge extraction/synthesis<br>• Long-context processing<br>• Excellent summarization | LEARNER: 5/5 |

**Total VRAM**: ~21.7GB (comfortably within 25GB budget)

---

## 📊 Model Specifications

### DeepSeek-Coder-V2-Lite-Instruct

**Architecture**: MoE (16B total, 2.4B active per token)
**GGUF Size**: ~10-12 GB (Q5_K_M quantization)
**Context Window**: 128K tokens
**License**: DeepSeek License
**Ollama**: `deepseek-coder-v2:lite`

**Key Advantages for FIXER Role**:
1. **338 language support** (unmatched in open models)
2. Beats CodeStral-22B on specialized coding benchmarks
3. MoE efficiency: 16B performance at 2.4B activation cost
4. Large context window for understanding full modules

### GPT-OSS-20B

**Architecture**: MoE (21B total, 3.6B active per token)
**GGUF Size**: ~11.7 GB (Q5_K_M quantization)
**Context Window**: 128K tokens
**License**: Apache 2.0 (commercial-friendly)
**Ollama**: `gpt-oss:20b`

**Key Advantages for AUDITOR/LEARNER Roles**:
1. **Explicit agentic reasoning** design (OpenAI-architecture)
2. **Chain-of-Thought transparency** (visible reasoning process)
3. **Adjustable reasoning effort** (low/medium/high modes)
4. Exceptional instruction-following
5. Strong performance on GPQA/MATH reasoning benchmarks

---

## 🔧 Implementation Changes

### 1. Model Policy Update

**File**: `shared/model_policy_enhanced.py`

```python
# BEFORE (single model approach)
TIER_MODELS = {
    ModelTier.LOCAL_STANDARD: "qwen2.5-coder:7b",
    ModelTier.LOCAL_ADVANCED: "codestral-22b",  # or qwen2.5-coder:32b
}

# AFTER (Gemini dual-model strategy)
TIER_MODELS = {
    ModelTier.LOCAL_FAST: "qwen2.5-coder:1.5b",        # Lightweight detection
    ModelTier.LOCAL_STANDARD: "deepseek-coder-v2:lite", # FIXER (code generation)
    ModelTier.LOCAL_ADVANCED: "gpt-oss:20b",            # AUDITOR/LEARNER (analysis)
}
```

### 2. Trinity Agent Mapping

```python
TRINITY_AGENT_TIERS = {
    "fixer": ModelTier.LOCAL_STANDARD,      # deepseek-coder-v2:lite
    "auditor": ModelTier.LOCAL_ADVANCED,    # gpt-oss:20b
    "learner": ModelTier.LOCAL_ADVANCED,    # gpt-oss:20b
    "witness": ModelTier.LOCAL_FAST,        # qwen2.5-coder:1.5b
}
```

### 3. Autonomous Recommendation Fixer

**File**: `scripts/autonomous_recommendation_fixer.py`

Currently uses `default_tier="local"` which maps to qwen2.5-coder:32b.

**Change Required**: Update to use new model policy.

```python
# Current (line ~1158)
registry = create_agent_registry(
    agent_context=context,
    cost_tracker=tracker,
    default_tier="local",  # Generic local
)

# Updated (use MODEL_TIER)
from shared.model_policy_enhanced import ModelTier

registry = create_agent_registry(
    agent_context=context,
    cost_tracker=tracker,
    default_tier=ModelTier.LOCAL_STANDARD,  # DeepSeek for FIXER role
)
```

### 4. Trinity Daemon Update

**File**: `scripts/trinity_daemon.py`

Currently invokes scripts via subprocess without model selection.

**Enhancement**: Pass model parameter to subprocess calls:

```python
# AUDITOR subprocess (gpt-oss:20b)
result = subprocess.run([
    "python", "scripts/continuous_audit_m4pro.py",
    "--model", "gpt-oss:20b",  # AUDITOR model
    "--mode", "once",
    ...
])

# FIXER subprocess (deepseek-coder-v2:lite)
result = subprocess.run([
    "python", "scripts/autonomous_recommendation_fixer.py",
    "--model", "deepseek-coder-v2:lite",  # FIXER model
    ...
])
```

---

## 🧪 Testing Plan

### Phase 1: Individual Model Testing (15 min)

**Test GPT-OSS-20B** (AUDITOR role):
```bash
ollama run gpt-oss:20b "Analyze this Python function for potential bugs:
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)"
```

**Expected**: Detailed analysis with Chain-of-Thought reasoning visible.

**Test DeepSeek-Coder-V2-Lite** (FIXER role):
```bash
ollama run deepseek-coder-v2:lite "Fix this Python function to handle empty lists:
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)"
```

**Expected**: Corrected code with proper error handling.

### Phase 2: Trinity Integration Testing (30 min)

1. **Test FIXER with 1 recommendation**:
   ```bash
   python scripts/autonomous_recommendation_fixer.py \
     --category pruning --priority P3 --limit 1 \
     --auto-commit \
     --recommendations-dir .output/audit_recommendations \
     --output-dir .output/test_gemini_fixer
   ```

2. **Test AUDITOR scan**:
   ```bash
   python scripts/continuous_audit_m4pro.py \
     --mode once --model gpt-oss:20b \
     --output-dir .output/test_gemini_auditor
   ```

3. **Monitor VRAM usage**:
   ```bash
   # Both models running simultaneously
   watch -n 2 'ps aux | grep -E "(ollama|python)" | grep -v grep'
   ```

### Phase 3: 24h Production Run

Launch Trinity daemon with dual-model configuration:
```bash
./launch_trinity_overnight.sh 24  # 24-hour run
```

**Expected Results** (Gemini's prediction):
- **Fixes Applied**: 80-120 commits
- **Success Rate**: 60-70% (improves over time via learning)
- **VRAM Usage**: 21-23GB peak (safe margin)
- **Cost**: $0.00 (100% local)

---

## 📈 Benchmark Integration (Future)

Per Gemini's recommendation, track model performance:

### SWE-Bench Evaluation
- Measure fix quality against real GitHub issues
- Score: 0.0 (doesn't resolve) to 1.0 (fully resolves)
- Target: 0.6-0.7 (60-70% task resolution)

### LiveCodeBench Tracking
- Weekly coding capability assessment
- Prompt adherence metrics
- Code efficiency measurements

### Capability Dashboard
- Track success rate evolution
- Model performance by task type
- Learning rate (patterns/day)

---

## 🚀 Deployment Status

### ✅ Completed
- [x] Gemini strategic analysis documented
- [x] Model downloads initiated (gpt-oss:20b + deepseek-coder-v2:lite)
- [x] Model policy updated (shared/model_policy_enhanced.py)
- [x] Trinity agent tier mapping configured

### 🔄 In Progress
- [ ] Model downloads completing (~3-4 min remaining)
- [ ] Script bug fixes committed

### ⏳ Pending
- [ ] Phase 1: Individual model testing
- [ ] Phase 2: Trinity integration testing
- [ ] Phase 3: 24h production run launch
- [ ] Benchmark integration implementation

---

## 💡 Why This Works

**Problem with Single-Model Approach**:
- Qwen2.5-coder:32b excellent at mainstream coding
- But weaker at deep logical analysis (AUDITOR)
- And weaker at long-context synthesis (LEARNER)
- One model = compromise across all roles

**Gemini's Dual-Model Solution**:
- DeepSeek specialized for code generation (FIXER)
- GPT-OSS specialized for reasoning/analysis (AUDITOR/LEARNER)
- Each model does what it's best at
- Total VRAM still under budget
- No compromises, only strengths

**Expected Impact**:
- **FIXER**: +20% success rate (better language support)
- **AUDITOR**: +30% false positive reduction (better reasoning)
- **LEARNER**: +40% pattern quality (better synthesis)
- **Overall**: 60-70% autonomous fix success vs 0% currently

---

## 📚 References

1. **Gemini's Strategic Framework**: `docs/A-Strategic-Framework-for-a-Hybrid-Autonomous-Trinity-on-Apple-Silicon.md`
2. **Model Downloads**:
   - GPT-OSS: https://ollama.com/library/gpt-oss
   - DeepSeek: https://ollama.com/library/deepseek-coder-v2
3. **Benchmarks**:
   - SWE-Bench: https://www.swebench.com
   - LiveCodeBench: https://livecodebench.github.io

---

**Status**: Models downloading (ETA: 3 min), configuration updated, ready for testing.
