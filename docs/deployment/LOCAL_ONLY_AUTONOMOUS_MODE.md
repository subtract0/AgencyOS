# Local-Only Autonomous Execution Mode

**Purpose**: Run Constitutional Consciousness autonomously overnight using only local models (Ollama)
**Target**: MacBook Pro M4 (48GB RAM) - Hybrid Trinity Architecture
**Mode**: `--local-only` (no GPT-5 API escalation)

---

## 🎯 Architecture (Hybrid Trinity)

Per `A-Strategic-Framework-for-a-Hybrid-Autonomous-Trinity-on-Apple-Silicon.md`:

### Model Allocation (24GB budget)

1. **Architect (Planner)**: Codestral-22B-Q4_K_M (~13.4GB)
   - High-level planning, task decomposition
   - Local, privacy-sensitive

2. **Builder (Executor)**: Qwen 2.5 Coder 7B-Q4_K_M (~4.7GB)
   - Code execution, file operations
   - Local for routine tasks

3. **Controller (Scanner)**: Qwen 2.5 Coder 1.5B-Q4_K_M (~1.5GB)
   - File monitoring, log parsing, quality checks
   - Lightweight, continuous operation

**Total**: 19.6GB models + 20.4GB KV cache + 8GB macOS = 48GB

---

## 🚀 Deployment Steps (MacBook Pro)

### 1. Install Ollama
```bash
# On MacBook Pro
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull Models
```bash
# Architect (Planner)
ollama pull codestral:22b-v0.1-q4_K_M

# Builder (Executor)
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Controller (Scanner)
ollama pull qwen2.5-coder:1.5b-instruct-q4_K_M
```

### 3. Configure Environment
```bash
# .env on MacBook Pro
AGENCY_MODE=local_only
OLLAMA_HOST=http://localhost:11434

# Model assignments
PLANNER_MODEL=codestral:22b-v0.1-q4_K_M
CODER_MODEL=qwen2.5-coder:7b-instruct-q4_K_M
SCANNER_MODEL=qwen2.5-coder:1.5b-instruct-q4_K_M

# Disable API escalation
ENABLE_GPT5_ESCALATION=false
USE_OPENAI_FALLBACK=false

# Enable Constitutional Consciousness
ENABLE_CONSCIOUSNESS=true
AUTONOMOUS_NIGHT_RUN=true
```

### 4. Sync Codebase
```bash
# From MacBook Air (development)
rsync -avz --exclude .venv --exclude __pycache__ \
  /Users/am/Code/Agency/ \
  macbook-pro:/Users/am/Code/Agency/
```

---

## 🌙 Autonomous Night Run Workflow

### What it does:
1. **Observe**: Read constitutional_violations.jsonl (159 violations)
2. **Analyze**: Detect patterns (create_mock_agent: 150 violations)
3. **Predict**: Forecast violations (95% probability, 180 expected)
4. **Evolve**: Propose agent improvements (test_infrastructure: 95% confidence)
5. **Learn**: Store patterns to VectorStore
6. **Report**: Generate cycle report + evolution proposals

### Command:
```bash
# On MacBook Pro
cd /Users/am/Code/Agency

# Run Constitutional Consciousness autonomously
python -m tools.constitutional_consciousness.feedback_loop \
  --days 7 \
  --json > logs/consciousness_night_run_$(date +%Y%m%d).json

# Or continuous monitoring (runs every hour)
while true; do
  python -m tools.constitutional_consciousness.feedback_loop --days 7
  sleep 3600  # 1 hour
done
```

---

## 🛡️ Safety Mechanisms

### 1. Local-Only Mode
- ✅ All inference via Ollama (no API calls)
- ✅ Data never leaves MacBook Pro
- ✅ Zero API costs

### 2. Human-in-Loop
- ✅ Evolution proposals require approval (Article III)
- ✅ No auto-merge to agent deltas
- ✅ Git audit trail for all changes

### 3. Resource Management
- ✅ 20.4GB KV cache buffer (large context windows)
- ✅ 8GB reserved for macOS (no swapping)
- ✅ Memory monitoring via `vm_stat`

---

## 📊 Expected Performance

### Context Windows (with 20.4GB KV cache)
- **Codestral-22B**: ~25,000 tokens (~0.8GB per 10k tokens)
- **Qwen 2.5 Coder 7B**: ~60,000 tokens (~0.34GB per 10k tokens)
- **Qwen 2.5 Coder 1.5B**: ~136,000 tokens (~0.15GB per 10k tokens)

### Inference Speed (M4 Pro)
- **Codestral-22B**: ~15-20 tokens/sec
- **Qwen 2.5 Coder 7B**: ~30-40 tokens/sec
- **Qwen 2.5 Coder 1.5B**: ~60-80 tokens/sec

### Night Run Estimate
- **Single cycle**: ~5 minutes (analyze 159 violations)
- **Hourly cycles**: 12 cycles overnight (8 hours)
- **Cost**: $0 (local-only)

---

## 🔧 Integration with Constitutional Consciousness

### Existing Implementation (Days 1-4 ✅)
```python
# tools/constitutional_consciousness/feedback_loop.py
class ConstitutionalFeedbackLoop:
    def __init__(self, enable_vectorstore=True):
        # Day 1: Observer + Analyzer
        self.log_path = Path("logs/autonomous_healing/constitutional_violations.jsonl")

        # Day 2: VectorStore
        self.vector_store = create_enhanced_memory_store(
            embedding_provider="openai"  # ← CHANGE to "sentence-transformers" for local
        )

        # Day 3: Prediction
        self.prediction_engine = PredictionEngine(enable_vectorstore=True)

        # Day 4: Agent Evolution
        self.evolution_engine = AgentEvolutionEngine(enable_vectorstore=True)
```

### Local-Only Modifications
```python
# Change 1: Use local embeddings
self.vector_store = create_enhanced_memory_store(
    embedding_provider="sentence-transformers"  # Local, no API
)

# Change 2: Use Ollama for predictions (if LLM needed)
from langchain_community.llms import Ollama

self.local_llm = Ollama(
    model="qwen2.5-coder:7b-instruct-q4_K_M",
    base_url="http://localhost:11434"
)
```

---

## 📈 Metrics to Track

### Constitutional Consciousness Metrics
- Violations analyzed per cycle
- Patterns detected (3+ occurrences)
- Prediction accuracy (probability vs actual)
- Evolution proposals generated
- VectorStore size growth

### System Metrics
- Memory usage (`vm_stat`)
- Model load times
- Inference latency
- Context window utilization

---

## 🚨 Fallback Strategy

If Ollama models struggle with complex reasoning:

1. **Hybrid Mode**: Use GPT-5 API for Architect (Planner) only
2. **Local Execution**: Keep Builder + Controller local
3. **Cost Control**: Cap API usage at $X/night

But for Constitutional Consciousness (pattern analysis):
- **No LLM needed** for detection/prediction (rule-based)
- **VectorStore queries** are local (sentence-transformers)
- **Agent evolution proposals** are template-based

**Result**: Can run 100% local-only without quality loss.

---

## ✅ Deployment Checklist

### MacBook Pro Setup
- [ ] Install Ollama
- [ ] Pull Codestral-22B, Qwen2.5-Coder-7B, Qwen2.5-Coder-1.5B
- [ ] Install sentence-transformers (`pip install sentence-transformers`)
- [ ] Sync Agency codebase from MacBook Air
- [ ] Configure `.env` with `AGENCY_MODE=local_only`
- [ ] Test Ollama connectivity (`ollama list`)

### Constitutional Consciousness Setup
- [ ] Update VectorStore to use sentence-transformers
- [ ] Test feedback loop locally (`python -m tools.constitutional_consciousness.feedback_loop`)
- [ ] Verify VectorStore storage (check memory growth)
- [ ] Set up cron job for hourly cycles (optional)

### Validation
- [ ] Run one full cycle (should take ~5 min)
- [ ] Check memory usage (`vm_stat | grep "Pages active"`)
- [ ] Verify evolution proposals generated
- [ ] Confirm zero API calls (`grep "openai" logs/*.json` → empty)

---

## 🎯 Success Criteria

**Tonight's Goal**: Run Constitutional Consciousness autonomously for 8 hours

**Expected Outcome**:
- 12 consciousness cycles completed
- 2-3 agent evolution proposals (high confidence)
- 159 violations analyzed, patterns learned
- VectorStore enriched with historical data
- Zero API costs
- MacBook Pro stable (no memory pressure)

**Morning Report**:
```
Constitutional Consciousness Night Run Summary
Cycles: 12/12 ✅
Patterns: 2 (create_mock_agent, create_planner_agent)
Predictions: 95% accuracy
Evolution Proposals: 1 (test_infrastructure agent)
API Calls: 0 ✅
Cost: $0 ✅
```

---

**Status**: Ready to deploy
**ETA**: <1 hour setup + overnight autonomous run
**Next**: Install Ollama on MacBook Pro → Sync codebase → Start autonomous cycle
