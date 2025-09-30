# AUDITLEARN Prompt Design Decision

**Date**: 2025-09-30  
**Decision**: Gemini's submission selected as canonical AUDITLEARN prompt  
**Status**: ✅ APPROVED - Implementation ready

---

## 🏆 Competition Summary

Two competing designs were evaluated for the Trinity Protocol AUDITLEARN agent:

1. **Gemini (Google DeepMind)** - "Self-Verifying Signal Processor"
2. **ChatGPT (OpenAI)** - "Dual-Layer Hybrid Approach"

---

## 📊 Evaluation Criteria

Based on Agency's constitutional requirements and Trinity Protocol architecture:

| Criterion | Gemini | ChatGPT | Winner |
|-----------|--------|---------|--------|
| **Constitutional Alignment** | ✅ Explicit Article II, IV compliance | ⚠️ Implicit compliance | Gemini |
| **Self-Verification** | ✅ Step 5: Schema validation before publish | ❌ No explicit self-verification | Gemini |
| **Confidence Model** | ✅ Mathematical (base + weights) | ⚠️ Threshold-based, no formula | Gemini |
| **Traceability** | ✅ Requires source_id, correlation_id | ⚠️ Optional metadata | Gemini |
| **Firestore Integration** | ✅ Built-in (with enhancement) | ❌ Not specified | Gemini |
| **Complexity** | ✅ Single production layer | ⚠️ Dual dev/prod layers | Gemini |
| **Error Handling** | ✅ Zero tolerance, fix before publish | ⚠️ Not specified | Gemini |

**Final Score**: Gemini 7/7, ChatGPT 2/7

---

## ✨ Gemini's Key Innovations

1. **Self-Verification Loop** - Step 5 validates JSON against schema before publishing
   - Aligns with Article II: 100% Verification mandate
   - Prevents broken windows in telemetry stream

2. **Mathematical Confidence Scoring** - `confidence = base + Σ(keyword_matches × weight)`
   - Deterministic and auditable
   - Adaptive thresholds (0.75 → 0.60 for critical patterns seen 3x+)

3. **Constitutional as Identity** - Not instructions, but core operating principles
   - Article I: Complete Context
   - Article II: 100% Verification
   - Article IV: Continuous Learning

4. **Metadata Enrichment** - Full traceability chain
   - `source_id`: Links back to originating event
   - `correlation_id`: Tracks patterns across Trinity loop
   - `timestamp`: ISO8601 for precise time tracking

5. **Stateless Finite State Machine** - 8-step unbreakable loop
   - LISTEN → CLASSIFY → VALIDATE → ENRICH → SELF-VERIFY → PUBLISH → PERSIST → RESET
   - Pure function behavior: Event → JSON | NULL

---

## 🔧 Enhancements Applied

To integrate Gemini's design with Agency infrastructure:

### 1. Firestore Persistence (Article IV)
- Collection: `trinity_patterns`
- Schema: pattern_type, confidence, evidence_count, success_rate, metadata
- Purpose: Cross-session learning, pattern success tracking

### 2. Local Model Configuration
- Model: `qwen2.5-coder:7b-q3` via Ollama
- Temperature: 0.3 (deterministic classification)
- Max tokens: 512 (short outputs only)
- Fallback: `gpt-4o-mini` cloud escalation

### 3. MCP Integration Reference
- Ref: `688cf28d-e69c-4624-b7cb-0725f36f9518`
- Purpose: Ensure alignment with established integration standards

### 4. Pattern Heuristics Enhancement
- Added `integration_failure` pattern (Firebase, OpenAI, API errors)
- Added `type_safety` opportunity pattern
- Added `frustration_signal` user intent pattern

---

## 📋 Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Set up Firestore `trinity_patterns` collection
- [ ] Configure Ollama with Qwen 2.5-Coder 7B
- [ ] Implement 8-step stateless loop
- [ ] Add jsonschema validation for self-verification

### Phase 2: Pattern Detection (Week 3)
- [ ] Implement mathematical confidence scoring
- [ ] Add adaptive threshold logic
- [ ] Test pattern detection on real telemetry
- [ ] Verify Firestore persistence

### Phase 3: Integration (Week 4)
- [ ] Connect to `telemetry_stream` and `personal_context_stream`
- [ ] Publish to `improvement_queue` message bus
- [ ] Test end-to-end AUDITLEARN → PLAN loop
- [ ] Run 24-hour continuous operation test

---

## ⚠️ Critical Requirements

1. **Self-verification is MANDATORY** - Never publish invalid JSON (Article II)
2. **Firestore persistence is MANDATORY** - Every pattern ≥0.7 confidence (Article IV)
3. **Stateless operation is REQUIRED** - No memory between events
4. **Local-first execution** - Use Qwen 2.5-Coder 7B, only escalate on failure
5. **Mathematical precision** - Confidence scoring must be deterministic

---

## 🔗 Related Files

- **Canonical Prompt**: `docs/trinity_protocol/gemini_auditlearn_prompt.md` (17KB)
- **Executor Prompt**: `docs/trinity_protocol/gemini_executor_prompt.md` (9.1KB)
- **Trinity Spec**: `docs/trinity_protocol_implementation.md`
- **Constitution**: `constitution.md` (Articles I, II, IV)
- **ADR-004**: `docs/adr/ADR-004-continuous-learning-system.md`

---

## 📝 Decision Rationale

Gemini's design was selected because it:

1. **Architecturally superior** - Pure function, stateless, self-verifying
2. **Constitutionally compliant** - Explicit enforcement of Articles I, II, IV
3. **Production-ready** - Single layer, minimal complexity, clear implementation path
4. **Mathematically rigorous** - Deterministic confidence scoring, auditable decisions
5. **Traceable** - Full metadata chain enables debugging and learning loops

ChatGPT's dual-layer approach, while clever, adds unnecessary complexity for a stateless detector and lacks the explicit constitutional enforcement that is core to Agency's governance model.

---

## ✅ Approval

**Approved By**: @am  
**Date**: 2025-09-30  
**Next Step**: Begin Phase 1 implementation  
**Success Criteria**: Pattern detection working with ≥90% precision by Week 4

---

*"You are not a reasoner. You are not an actor. You are a pure function: Event → JSON | NULL. Your discipline is your power."* - Gemini
