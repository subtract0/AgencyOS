# Modellwahl für Trinity-Rollen: Optimierung für M4 Pro

**Datum**: 2025-10-07
**System**: M4 Pro, 48GB Shared RAM, 14 CPU Cores, 16 GPU Cores
**Ziel**: Unbegrenztes Self-Improvement ohne Qualitätsverlust

---

## 🎯 Vision: Full-Circle Self-Improving Machine

### Anforderungen

1. **Keine Obergrenze** für Self-Improvement
2. **Höchste Code-Qualität** (Constitutional compliance)
3. **Benchmark-Tracking**: SWE-Bench, LiveCodeBench, Prompt Adherence
4. **Maximale Ressourcennutzung**: 48GB RAM, 14 CPUs voll ausschöpfen
5. **Autonome agentische Strukturen** mit Qualitätssignalen

### Aktueller Zustand (Phase 4.1)

**❌ PROBLEM**: 0/227 Success Rate (100% Failure)
- **130+ Branches erstellt**, aber KEINE Commits
- **Root Cause**: Script-Regression (3 kritische Bugs kehren zurück)
- **Impact**: Trinity läuft, aber produziert nichts

---

## 📊 Verfügbare Modelle (Ollama Local)

### Installiert

| Modell | Größe | Parameter | Kontext | Speicher | Zweck |
|--------|-------|-----------|---------|----------|-------|
| **qwen2.5-coder:32b** | 19GB | 32B | 128k | ~20GB RAM | Komplexe Implementierung |
| **qwen2.5-coder:14b** | 9.0GB | 14B | 128k | ~10GB RAM | Mittlere Aufgaben |
| **qwen2.5-coder:7b** | 4.7GB | 7B | 128k | ~6GB RAM | Schnelle Analyse |
| **qwen2.5-coder:1.5b** | 986MB | 1.5B | 128k | ~1.5GB RAM | Detection, Classification |

### Empfohlene zusätzliche Modelle

| Modell | Größe | Parameter | Stärken | Trinity-Rolle |
|--------|-------|-----------|---------|---------------|
| **qwen2.5:72b** | 41GB | 72B | Reasoning, Planning | ARCHITECT, AUDITOR |
| **deepseek-coder-v2:236b** | 133GB | 236B | Elite coding | FIXER (P0-P1) |
| **codestral:22b** | 13GB | 22B | Fast, accurate | LEARNER, AUDITOR |
| **llama3.1:70b** | 40GB | 70B | General reasoning | QUALITY_ENFORCER |

**M4 Pro Kapazität**: 48GB RAM - 10GB System = **38GB verfügbar**
- **Gleichzeitig**: 2-3 große Modelle (z.B. 72b + 32b + 14b)
- **Parallel**: 4-5 kleine Modelle (7b, 14b)

---

## 🏗️ Optimierte Trinity-Architektur

### Option A: Quality-First (Empfohlen für Start)

**Ziel**: Maximale Code-Qualität, 60-70% Success Rate

```
ARCHITECT (qwen2.5:72b)     →  Strategic planning, ADR decisions
    ↓
AUDITOR (codestral:22b)     →  Fast, accurate detection (alle 15 min)
    ↓
FIXER (qwen2.5-coder:32b)   →  P2-P3 fixes (90% of work)
FIXER (deepseek-v2:236b)    →  P0-P1 fixes (10%, höchste Qualität)
    ↓
QUALITY_ENFORCER (llama3.1:70b) → Constitutional validation
    ↓
LEARNER (codestral:22b)     →  Pattern extraction (alle 30 min)
```

**RAM-Nutzung**:
- ARCHITECT (72b): 41GB (on-demand)
- AUDITOR (22b): 13GB (persistent)
- FIXER (32b): 19GB (persistent)
- LEARNER (22b): 13GB (shared with AUDITOR)
- **Total Persistent**: 32GB + 10GB System = 42GB ✅

### Option B: Throughput-First

**Ziel**: Maximum Durchsatz, 40-50% Success Rate acceptable

```
ARCHITECT (qwen2.5-coder:32b)     →  Schnelleres Planning
    ↓
AUDITOR (qwen2.5-coder:14b)       →  Scan alle 10 min
    ↓
FIXER-POOL (3x qwen2.5-coder:32b) →  Parallel processing
    ↓
LEARNER (qwen2.5-coder:7b)        →  Continuous learning
```

**RAM-Nutzung**: 3x 19GB + 9GB + 5GB = 62GB **❌ ZU VIEL**

### Option C: Hybrid (Balanced)

**Ziel**: Balance zwischen Qualität und Durchsatz

```
AUDITOR (codestral:22b)           →  Fast detection (alle 15 min)
    ↓
CLASSIFIER (qwen2.5-coder:7b)     →  Priority triage
    ↓
FIXER_FAST (qwen2.5-coder:32b)    →  P3 fixes (parallel 2x)
FIXER_QUALITY (qwen2.5:72b)       →  P0-P2 fixes (sequential)
    ↓
LEARNER (qwen2.5-coder:14b)       →  Pattern extraction
```

**RAM-Nutzung**:
- AUDITOR: 13GB
- CLASSIFIER: 5GB
- 2x FIXER_FAST: 38GB (zu viel für parallel)
- **Alternativ**: 1x FIXER (19GB) + on-demand Quality (72b)
- **Total**: 37GB ✅

---

## 🧪 Benchmark-Integration

### SWE-Bench Integration

**Zweck**: Messen ob Fixes tatsächlich GitHub Issues lösen würden

```python
# scripts/benchmarks/swe_bench_evaluator.py

class SWEBenchEvaluator:
    """Evaluate Trinity fixes against SWE-Bench tasks."""

    def __init__(self, dataset="princeton-nlp/SWE-bench_Lite"):
        self.dataset = load_dataset(dataset)
        self.results = []

    def evaluate_fix(self, fix_result: FixResult) -> SWEBenchScore:
        """
        Map autonomous fix to SWE-Bench task.

        Scoring:
        - 1.0: Fix resolves issue completely
        - 0.5: Fix partially resolves issue
        - 0.0: Fix doesn't resolve or breaks tests
        """
        # Match fix to similar SWE-Bench task
        similar_task = self.find_similar_task(fix_result.recommendation)

        # Run task test suite against fix
        tests_pass = self.run_task_tests(similar_task, fix_result.files_modified)

        # Score based on test results
        score = self.calculate_score(tests_pass, similar_task.acceptance_criteria)

        return SWEBenchScore(
            task_id=similar_task.id,
            fix_id=fix_result.id,
            score=score,
            tests_passed=tests_pass,
            timestamp=datetime.now()
        )
```

### LiveCodeBench Integration

**Zweck**: Real-time coding capability tracking

```python
# scripts/benchmarks/livecode_bench_evaluator.py

class LiveCodeBenchEvaluator:
    """Evaluate Trinity coding quality against LiveCodeBench."""

    def __init__(self):
        self.tasks = self.load_livecode_tasks()
        self.baseline_scores = {}

    def weekly_assessment(self, model: str) -> LiveCodeBenchReport:
        """
        Run weekly LiveCodeBench assessment.

        Tracks:
        - Code generation quality
        - Test case pass rate
        - Prompt adherence score
        - Code efficiency metrics
        """
        results = []

        for task in random.sample(self.tasks, k=50):  # 50 random tasks
            response = self.invoke_model(model, task.prompt)

            score = LiveCodeBenchScore(
                task_id=task.id,
                model=model,
                code_quality=self.assess_quality(response),
                test_pass_rate=self.run_tests(response, task.tests),
                prompt_adherence=self.check_adherence(response, task.requirements),
                efficiency=self.measure_efficiency(response)
            )
            results.append(score)

        return LiveCodeBenchReport(
            model=model,
            timestamp=datetime.now(),
            overall_score=np.mean([s.overall for s in results]),
            trend=self.calculate_trend(model, results)
        )
```

### Prompt Adherence Metrics

**Zweck**: Quantifizieren wie gut Modelle Instructions folgen

```python
# shared/metrics/prompt_adherence.py

class PromptAdherenceScorer:
    """Score how well model output follows instructions."""

    def score(self, prompt: str, output: str, expected_format: dict) -> float:
        """
        Score 0.0-1.0 based on:
        - Format compliance (JSON, markdown, code)
        - Completeness (all required fields present)
        - Accuracy (output matches expected structure)
        - Constitutional compliance (follows Agency rules)
        """
        scores = {
            "format": self.check_format(output, expected_format),
            "completeness": self.check_completeness(output, expected_format),
            "accuracy": self.check_accuracy(output, prompt),
            "constitutional": self.check_constitutional(output)
        }

        # Weighted average
        weights = {"format": 0.2, "completeness": 0.3, "accuracy": 0.3, "constitutional": 0.2}
        return sum(scores[k] * weights[k] for k in scores)
```

---

## 📈 Self-Improvement Tracking

### Capability Evolution Dashboard

```python
# scripts/monitoring/capability_dashboard.py

class CapabilityDashboard:
    """Track Trinity's evolving capabilities over time."""

    metrics = {
        "fix_success_rate": [],  # % of fixes that pass tests
        "swe_bench_score": [],   # SWE-Bench performance
        "livecode_score": [],    # LiveCodeBench performance
        "prompt_adherence": [],  # Instruction-following quality
        "code_quality": [],      # Constitutional compliance
        "velocity": [],          # Fixes per hour
        "learning_rate": []      # New patterns learned per day
    }

    def daily_snapshot(self):
        """Capture daily capability snapshot."""
        snapshot = CapabilitySnapshot(
            date=date.today(),
            metrics={k: v[-1] if v else 0 for k, v in self.metrics.items()},
            model_config=self.get_current_models(),
            recommendation_backlog=self.count_pending_recs()
        )

        # Detect improvement trends
        if len(self.metrics["fix_success_rate"]) > 7:
            trend = self.calculate_weekly_trend()
            if trend > 0.1:  # 10% improvement
                logger.info(f"🚀 Capability improving: +{trend*100:.1f}% this week")

        return snapshot
```

### No-Ceiling Architecture

**Prinzip**: System kann eigene Verbesserungen vorschlagen

```python
# scripts/meta/self_improvement_agent.py

class SelfImprovementAgent:
    """Meta-agent that improves Trinity itself."""

    def analyze_bottlenecks(self) -> list[Improvement]:
        """
        Identify Trinity's own bottlenecks.

        Analyzes:
        - Fix success rate by category
        - Model performance by task type
        - Resource utilization patterns
        - Learning efficiency
        """
        improvements = []

        # Example: Detect if 7b model is bottleneck for AUDITOR
        if self.metrics["audit_false_positive_rate"] > 0.2:
            improvements.append(Improvement(
                component="AUDITOR",
                issue="High false positive rate (20%)",
                recommendation="Upgrade AUDITOR from qwen2.5-coder:7b to codestral:22b",
                expected_impact="+15% accuracy, -5 min per cycle",
                priority=Priority.P1
            ))

        return improvements

    def self_heal(self, improvement: Improvement):
        """
        Apply improvement to Trinity itself.

        Steps:
        1. Create ADR documenting change
        2. Update model_policy_enhanced.py
        3. Run integration tests
        4. Measure impact (A/B test)
        5. Commit if successful
        """
        pass
```

---

## 🎬 Empfohlene Aktion

### Sofort (Nächste 15 Minuten)

1. **Fix Script-Regression** ✅ (bereits erledigt)
2. **Pull größere Modelle**:
   ```bash
   ollama pull qwen2.5:72b        # 41GB, ~20 min
   ollama pull codestral:22b      # 13GB, ~7 min
   ```

3. **Teste FIXER isolated**:
   ```bash
   python scripts/autonomous_recommendation_fixer.py \
     --category pruning --priority P3 --limit 1 \
     --auto-commit \
     --recommendations-dir .output/audit_recommendations \
     --output-dir .output/test_fix
   ```

### Kurzfristig (Nächste 2 Stunden)

4. **Implementiere Option C (Hybrid)**:
   - AUDITOR: codestral:22b
   - FIXER: qwen2.5-coder:32b (P3), qwen2.5:72b (P0-P2)
   - LEARNER: qwen2.5-coder:14b

5. **Integriere SWE-Bench Evaluator** (minimal):
   ```python
   # In FixResult recording
   if fix_result.status == FixStatus.APPLIED:
       swe_score = swe_bench.quick_eval(fix_result)
       telemetry.record("swe_bench_score", swe_score)
   ```

6. **Relaunch Trinity mit fixes**:
   ```bash
   ./launch_trinity_overnight.sh 24  # 24-Stunden-Run
   ```

### Mittelfristig (Nächste Woche)

7. **Full Benchmark Suite**:
   - SWE-Bench weekly evaluation
   - LiveCodeBench daily tracking
   - Prompt adherence metrics per agent

8. **Meta-Self-Improvement Agent**:
   - Analyze Trinity's own performance
   - Propose model upgrades
   - A/B test changes

9. **Multi-Model FIXER Pool**:
   - 2x qwen2.5-coder:32b parallel für P3
   - 1x qwen2.5:72b sequential für P0-P2

---

## 🔬 Experiment: 24h Ultimate Run

### Konfiguration

```yaml
# trinity_ultimate_config.yaml

auditor:
  model: codestral:22b
  interval_minutes: 15
  categories: [pruning, simplification, consolidation, architecture]

fixer:
  fast_pool:
    model: qwen2.5-coder:32b
    parallel: 1  # Start with 1, increase if RAM permits
    priority: [P3]
  quality_pool:
    model: qwen2.5:72b
    parallel: 1
    priority: [P0, P1, P2]

learner:
  model: qwen2.5-coder:14b
  interval_minutes: 30
  min_evidence: 3
  min_confidence: 0.7

benchmarks:
  swe_bench:
    enabled: true
    sample_size: 10  # Eval 10 fixes per hour
  livecode_bench:
    enabled: true
    weekly: true
  prompt_adherence:
    enabled: true
    threshold: 0.8

meta:
  self_improvement:
    enabled: true
    check_interval_hours: 6
    auto_apply: false  # Human approval required
```

### Erwartete Ergebnisse (24h)

**Conservative (Option C - Hybrid)**:
- **Fixes Applied**: 80-120 commits
- **Success Rate**: 60-70% (lernt von Failures)
- **SWE-Bench Score**: 0.6-0.7 (60-70% task resolution)
- **Code Quality**: 95%+ constitutional compliance
- **Patterns Learned**: 30-50 templates
- **Cost**: $0.00 (100% local)

**Optimistic (mit deepseek-v2:236b für P0-P1)**:
- **Fixes Applied**: 100-150 commits
- **Success Rate**: 75-85%
- **SWE-Bench Score**: 0.75-0.85
- **Self-Improvements**: 2-3 Trinity-eigene Optimierungen
- **Cost**: $0.00

---

## 🚀 Nächster Schritt

**Warte auf User-Approval**:

- [ ] Pull qwen2.5:72b + codestral:22b? (~54GB total)
- [ ] Implementiere Hybrid-Architecture (Option C)?
- [ ] Integriere SWE-Bench basic evaluator?
- [ ] Launch 24h Trinity Ultimate Run?

**Oder**:

- [ ] Starte jetzt mit current models (32b/14b/7b) + fixes?
- [ ] Fokus auf Script-Stabilität zuerst?

---

**Zusammenfassung**:
Mit 48GB RAM können wir **gleichzeitig** einen 72b AUDITOR + 32b FIXER + 14b LEARNER laufen lassen = **Elite Quality** + **Unbegrenztes Self-Improvement** + **Benchmark-Tracking** für echte Capability-Evolution-Messung.

Das ist die Grundlage für **No-Ceiling Self-Improvement Machine**. 🚀
