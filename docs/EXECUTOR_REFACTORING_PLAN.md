# Executor Refactoring Plan: TRM → Adaptive Esper3.1

**Status:** Draft - Ready for implementation
**Date:** 2025-10-25
**Related:** `docs/TRM_PIVOT.md`, ADR-034 Amendment

---

## Objective

Refactor `tools/esper31_trm_executor.py` from **TRM delegation model** to **adaptive complexity routing** using Esper3.1 with dynamic parameters.

**Before:** Esper3.1 → TRM (for complex tasks)
**After:** Esper3.1 → Esper3.1 (with adjusted params based on complexity)

---

## Changes Overview

### File Renaming

```bash
tools/esper31_trm_executor.py → tools/adaptive_executor.py
```

**Rationale:** Generic name for future multi-model support (Option B: Qwen3-Coder)

### Class Refactoring

**Old:**
```python
class Esper31TRMExecutor:
    def __init__(self, esper31_model, trm_checkpoint, use_trm):
        self.trm_executor = TRMExecutor(...)
```

**New:**
```python
class AdaptiveExecutor:
    def __init__(
        self,
        primary_model: str = "gpt-oss:20b",  # Esper3.1
        fallback_model: Optional[str] = None,  # Future: Qwen3-Coder
        use_complexity_routing: bool = True
    ):
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.complexity_detector = ComplexityDetector()
```

### New Component: ComplexityDetector

**Location:** `tools/complexity_detector.py`

**Heuristics:**
```python
class ComplexityDetector:
    """
    Classify task complexity using heuristics.

    P3 (Simple): Format code, fix typos, simple refactors
    P2 (Moderate): Feature impl, bug fixes, testing
    P1 (Complex): Architecture, ADRs, complex algorithms
    """

    def classify(self, instruction: str, input_data: str) -> str:
        """
        Returns: "P3_simple" | "P2_moderate" | "P1_complex"
        """
        score = 0

        # Heuristic 1: Instruction length
        if len(instruction) > 500:
            score += 2
        elif len(instruction) > 200:
            score += 1

        # Heuristic 2: Complexity keywords
        complex_keywords = [
            "architecture", "design", "refactor", "optimize",
            "algorithm", "recursive", "graph", "constraint",
            "performance", "scalability", "async", "parallel"
        ]
        score += sum(1 for kw in complex_keywords if kw in instruction.lower())

        # Heuristic 3: Code structure keywords
        structure_keywords = [
            "class", "async def", "yield", "decorator",
            "metaclass", "generator", "context manager"
        ]
        score += sum(1 for kw in structure_keywords if kw in instruction.lower())

        # Heuristic 4: Multi-step indicators
        multi_step_keywords = [
            "first", "then", "next", "finally",
            "step 1", "step 2", "phase"
        ]
        if sum(1 for kw in multi_step_keywords if kw in instruction.lower()) >= 2:
            score += 2

        # Heuristic 5: VectorStore lookup (learn from past)
        # TODO: Query VectorStore for similar tasks
        # If past task with similar embedding was P1, bias upward

        # Classification
        if score >= 6:
            return "P1_complex"
        elif score >= 3:
            return "P2_moderate"
        else:
            return "P3_simple"

    def get_params(self, complexity: str) -> dict:
        """
        Return execution parameters for complexity level.
        """
        if complexity == "P3_simple":
            return {
                "max_tokens": 512,
                "temperature": 0.3,
                "top_p": 0.9,
                "reasoning_steps": 1
            }
        elif complexity == "P2_moderate":
            return {
                "max_tokens": 2048,
                "temperature": 0.5,
                "top_p": 0.95,
                "reasoning_steps": 3
            }
        else:  # P1_complex
            return {
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.95,
                "reasoning_steps": 5
            }
```

---

## Implementation Steps

### Phase 1: Create ComplexityDetector (1-2 hours)

1. **Create file:** `tools/complexity_detector.py`
2. **Implement heuristics:**
   - Instruction length
   - Keyword matching (complex_keywords, structure_keywords)
   - Multi-step detection
3. **Add tests:** `tests/test_complexity_detector.py`
   ```python
   def test_simple_task():
       detector = ComplexityDetector()
       result = detector.classify("Fix typo in README", "")
       assert result == "P3_simple"

   def test_complex_task():
       detector = ComplexityDetector()
       result = detector.classify(
           "Design a scalable architecture for async job processing with graph-based dependencies",
           ""
       )
       assert result == "P1_complex"
   ```

### Phase 2: Refactor Executor (2-3 hours)

1. **Rename file:**
   ```bash
   git mv tools/esper31_trm_executor.py tools/adaptive_executor.py
   ```

2. **Update imports:**
   ```python
   # Remove TRM imports
   # from tools.trm_executor import TRMExecutor

   # Add new imports
   from tools.complexity_detector import ComplexityDetector
   ```

3. **Refactor `__init__`:**
   ```python
   def __init__(
       self,
       primary_model: str = "gpt-oss:20b",
       fallback_model: Optional[str] = None,
       use_complexity_routing: bool = True
   ):
       self.primary_model = primary_model
       self.fallback_model = fallback_model
       self.use_complexity_routing = use_complexity_routing

       if use_complexity_routing:
           self.complexity_detector = ComplexityDetector()

       print(f"✅ AdaptiveExecutor ready")
       print(f"   Primary model: {self.primary_model}")
       print(f"   Fallback model: {self.fallback_model or 'None'}")
       print(f"   Complexity routing: {self.use_complexity_routing}")
   ```

4. **Refactor `execute()`:**
   ```python
   def execute(
       self,
       instruction: str,
       input_data: str = "",
       override_complexity: Optional[str] = None
   ) -> Dict[str, Any]:
       """
       Execute task with adaptive complexity routing.

       Args:
           instruction: Task description
           input_data: Optional input data
           override_complexity: Manual override ("P1_complex", "P2_moderate", "P3_simple")

       Returns:
           {
               "executor": "esper31" | "qwen3-coder",
               "complexity": "P1_complex" | "P2_moderate" | "P3_simple",
               "output": <solution>,
               "reasoning": <optional reasoning trace>,
               "metadata": <execution metadata>
           }
       """
       # Step 1: Determine complexity
       if override_complexity:
           complexity = override_complexity
       elif self.use_complexity_routing:
           complexity = self.complexity_detector.classify(instruction, input_data)
       else:
           complexity = "P2_moderate"  # Default

       # Step 2: Get execution parameters
       params = self.complexity_detector.get_params(complexity)

       # Step 3: Choose model
       # For Option A: Always use primary_model (Esper3.1)
       # For Option B: Use fallback_model for P1_complex if available
       model = self.primary_model
       if complexity == "P1_complex" and self.fallback_model:
           model = self.fallback_model

       # Step 4: Execute
       print(f"🚀 Executing with {model} (complexity: {complexity})")
       result = self._execute_with_params(
           model=model,
           instruction=instruction,
           input_data=input_data,
           params=params
       )

       return {
           "executor": model,
           "complexity": complexity,
           "output": result["output"],
           "reasoning": result.get("reasoning", ""),
           "metadata": {
               "model": model,
               "complexity": complexity,
               "params": params
           }
       }
   ```

5. **Add `_execute_with_params()`:**
   ```python
   def _execute_with_params(
       self,
       model: str,
       instruction: str,
       input_data: str,
       params: dict
   ) -> Dict[str, Any]:
       """
       Execute with Ollama using specified parameters.
       """
       prompt = f"""<|system|>
You are {model}, a coding and architecture specialist.
Reasoning level: {params.get('reasoning_steps', 1)} steps
<|user|>
{instruction}
{f"Input: {input_data}" if input_data else ""}
<|assistant|>
"""

       result = subprocess.run(
           [
               "ollama", "run", model,
               "--",
               prompt
           ],
           capture_output=True,
           text=True,
           timeout=120
       )

       return {
           "output": result.stdout.strip(),
           "reasoning": f"Executed with {params['reasoning_steps']} reasoning steps"
       }
   ```

6. **Remove TRM-specific methods:**
   - Delete `_get_routing_decision()` (was for TRM delegation)
   - Delete `_execute_solo_fallback()` (replaced by `_execute_with_params()`)

### Phase 3: Update Tests (1 hour)

1. **Rename test file:**
   ```bash
   git mv tests/test_esper31_trm_executor.py tests/test_adaptive_executor.py
   ```

2. **Update test cases:**
   ```python
   def test_simple_task_routing():
       executor = AdaptiveExecutor()
       result = executor.execute("Fix typo in README")
       assert result["complexity"] == "P3_simple"
       assert result["metadata"]["params"]["max_tokens"] == 512

   def test_complex_task_routing():
       executor = AdaptiveExecutor()
       result = executor.execute(
           "Design a distributed system for processing 1M events/sec"
       )
       assert result["complexity"] == "P1_complex"
       assert result["metadata"]["params"]["max_tokens"] == 4096

   def test_override_complexity():
       executor = AdaptiveExecutor()
       result = executor.execute(
           "Simple task",
           override_complexity="P1_complex"
       )
       assert result["complexity"] == "P1_complex"

   def test_multi_model_routing():
       # For Option B (future)
       executor = AdaptiveExecutor(
           primary_model="gpt-oss:20b",
           fallback_model="qwen3-coder:30b"
       )
       result = executor.execute("Complex architecture design...")
       assert result["executor"] == "qwen3-coder:30b"
   ```

### Phase 4: Integration (1 hour)

1. **Update imports in agents:**
   ```python
   # OLD
   from tools.esper31_trm_executor import Esper31TRMExecutor

   # NEW
   from tools.adaptive_executor import AdaptiveExecutor
   ```

2. **Update usage:**
   ```python
   # OLD
   executor = Esper31TRMExecutor(use_trm=True)

   # NEW
   executor = AdaptiveExecutor(use_complexity_routing=True)
   ```

3. **Update configuration:**
   - Add `USE_ADAPTIVE_ROUTING=true` to `.env`
   - Add `FALLBACK_MODEL=qwen3-coder:30b` (for Option B, optional)

---

## Future Enhancements (Option B)

### Multi-Model Routing

When ready to implement Option B (Esper3.1 + Qwen3-Coder):

1. **Set fallback model:**
   ```python
   executor = AdaptiveExecutor(
       primary_model="gpt-oss:20b",
       fallback_model="qwen3-coder:30b"
   )
   ```

2. **Routing logic (already in `execute()`):**
   ```python
   if complexity == "P1_complex" and self.fallback_model:
       model = self.fallback_model
   ```

3. **Benchmark:**
   - Run 50 P1 tasks with Esper3.1 vs Qwen3-Coder
   - Measure accuracy, latency, quality
   - Decide if complexity justifies two models

### VectorStore Integration

Add learning from past classifications:

```python
class ComplexityDetector:
    def classify(self, instruction: str, input_data: str) -> str:
        # Existing heuristics...

        # Query VectorStore for similar tasks
        from shared.agent_context import AgentContext
        context = AgentContext()

        similar = context.search_memories(
            tags=["complexity_classification"],
            query=instruction,
            limit=5
        )

        # If past tasks with high similarity were P1, bias upward
        if similar:
            avg_complexity = sum(
                s["metadata"]["complexity_score"]
                for s in similar
            ) / len(similar)

            if avg_complexity > 6:
                score += 1  # Bias toward P1

        # Store this classification for learning
        context.store_memory(
            key=f"complexity_classification_{hash(instruction)}",
            content={
                "instruction": instruction,
                "complexity": result,
                "score": score
            },
            tags=["complexity_classification"]
        )

        return result
```

---

## Testing Strategy

### Unit Tests (TDD)

1. **ComplexityDetector:**
   - Test each heuristic independently
   - Test edge cases (empty instruction, very long instruction)
   - Test keyword matching
   - Test parameter generation

2. **AdaptiveExecutor:**
   - Test routing logic
   - Test parameter application
   - Test fallback model selection
   - Test error handling

### Integration Tests

1. **End-to-end:**
   - Run 20 sample tasks (P1/P2/P3 mix)
   - Verify correct classification
   - Verify correct model selection
   - Verify output quality

2. **Performance:**
   - Benchmark classification speed (<100ms)
   - Benchmark execution latency
   - Compare to old TRM routing

### Shadow Mode (Optional)

Run in parallel with current system:

```python
# Run both old and new executor
old_result = old_executor.execute(task)
new_result = new_executor.execute(task)

# Log differences
if old_result["complexity"] != new_result["complexity"]:
    log_discrepancy(task, old_result, new_result)
```

---

## Rollout Plan

### Week 1: Development

- [x] Day 1: Create `ComplexityDetector` + tests
- [ ] Day 2-3: Refactor executor + tests
- [ ] Day 4: Integration + end-to-end tests
- [ ] Day 5: Documentation + review

### Week 2: Validation

- [ ] Day 1-2: Shadow mode testing (optional)
- [ ] Day 3: Benchmark vs old system
- [ ] Day 4-5: Tune heuristics based on results

### Week 3: Deployment

- [ ] Day 1: Production cutover
- [ ] Day 2-5: Monitor classification accuracy
- [ ] Week 4+: Iterate based on feedback

---

## Success Metrics

### Immediate (Week 1)

- ✅ All unit tests passing (100% coverage)
- ✅ Classification speed <100ms
- ✅ Zero regressions in existing tests

### Short-Term (Week 2-3)

- 🎯 85%+ classification accuracy (vs manual review)
- 🎯 <5% misrouted tasks (wrong complexity)
- 🎯 Latency parity with old system

### Long-Term (Month 1)

- 🎯 90%+ classification accuracy (with VectorStore learning)
- 🎯 Zero cost increase (still local-only)
- 🎯 Improved task quality (appropriate params)

---

## Salvaged TRM Components

### Keep (for future use)

- `tools/trm_executor.py` → Archived, may be useful for grid puzzles
- `models/trm-checkpoints/` → Keep, usable for ARC-AGI experiments
- `label_trm_delegation.py` → Refactor to `label_complexity.py` (heuristic tuning)

### Archive

- TRM training scripts (keep for reference)
- TRM-specific prompts (may inspire future routing)

---

## Questions to Resolve

1. **Threshold tuning:** How to empirically validate score thresholds (3, 6)?
   - **Answer:** Shadow mode + manual review of 100 tasks

2. **VectorStore integration:** When to add learning loop?
   - **Answer:** Week 3-4, after heuristics validated

3. **Option B timing:** When to add Qwen3-Coder fallback?
   - **Answer:** Only if Esper3.1 consistently fails on P1 tasks

4. **Constitutional integration:** How to integrate with `/primeA`?
   - **Answer:** Replace TRM checkpoints with adaptive params

---

## Conclusion

This refactoring:
- ✅ Removes TRM dependency (domain mismatch)
- ✅ Keeps routing architecture (valid design)
- ✅ Adds adaptive complexity (immediate value)
- ✅ Enables future multi-model support (Option B)
- ✅ Integrates with VectorStore (learning loop)

**Estimated effort:** 5-7 days
**Risk:** Low (no breaking changes, graceful fallback)
**Value:** High (immediate cost savings, better task handling)

---

**Next Steps:**
1. Review this plan with team
2. Create Phase 1 tasks in TodoWrite
3. Implement `ComplexityDetector` (TDD)
4. Begin executor refactoring

**Related:**
- `docs/TRM_PIVOT.md` (strategic context)
- ADR-034 Amendment (decision record)
- `tools/esper31_trm_executor.py` (current state)
