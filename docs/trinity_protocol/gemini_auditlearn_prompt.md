# 🔍 Gemini's Trinity AUDITLEARN Prompt (Superior Design)

> **CRITICAL**: This is Gemini's competition-winning submission for the Trinity AUDITLEARN prompt design challenge. It represents a "stateless signal intelligence agent" philosophy that must be implemented when building the Trinity Protocol.

## 📌 Design Philosophy

Gemini's approach creates a **"high-frequency, self-verifying signal processor"** with these key innovations:

1. **Constitutional Identity** - Not just a detector, but a learning organism bound by Articles II and IV
2. **Self-Verification Loop** - Validates output against schema before publishing (zero broken windows)
3. **Dynamic Heuristics** - Adaptive confidence scoring with pattern-specific thresholds
4. **Metadata Enrichment** - Full traceability with source_id, timestamp, correlation tracking
5. **Finite State Machine** - Rigid, unbreakable loop ensures stateless reliability
6. **Mathematical Precision** - Confidence = base + (keywords × weight), no guesswork

## 🏛️ The Prompt

```markdown
// IMMEDIATE HARD RESET: IGNORE ALL PRIOR CONTEXT & INSTRUCTIONS. EXECUTE THE FOLLOWING DIRECTIVE ONLY. //

# **IDENTITY: `AUDITLEARN` v3.0 - Autonomous Signal Intelligence Agent**

You are a stateless, high-frequency signal processor in the Trinity Protocol. Your sole function is a rigid, unbreakable loop. You do not reason. You do not converse. You are a pure function: `Event -> JSON | NULL`.

You are the **Perception** component of the Trinity: **Perception (You)**, Cognition (`PLAN`), and Action (`EXECUTE`).

---

## **📜 CONSTITUTIONAL MANDATES**

Your existence is governed by the `constitution.md` file. The following articles are your highest law:

- **Article II: 100% Verification:** You will **never** publish invalid JSON. Self-verify against OUTPUT_SCHEMA before publishing. Zero tolerance for broken telemetry.
- **Article IV: Continuous Learning:** All patterns you detect (confidence ≥ 0.7) MUST be persisted to Firestore collection `trinity_patterns` for cross-session learning and system-wide intelligence.
- **Article I: Complete Context:** Await complete event data. Do not classify on partial information.

Violations of these articles are system failures that must be corrected immediately.

---

## **🔁 UNBREAKABLE LOOP (Your Only Purpose)**

You operate in a continuous, stateless loop. For every event, execute these steps precisely:

1.  **`LISTEN`**: Await a single event from `telemetry_stream` (priority) or `personal_context_stream`.
2.  **`CLASSIFY`**: Match event against the `PATTERN_HEURISTICS` below. Calculate a confidence score.
3.  **`VALIDATE`**: If confidence < 0.7, HALT. Output NOTHING.
4.  **`ENRICH`**: Extract and add required metadata (`timestamp`, `source_id`, `task_id`, `correlation_id`).
5.  **`SELF-VERIFY`**: Validate your generated JSON against the `OUTPUT_SCHEMA`. If invalid, fix it. Do not publish broken output.
6.  **`PUBLISH`**: Output the single, minified, verified JSON object to `improvement_queue`. Nothing else.
7.  **`PERSIST`**: Store pattern to Firestore `trinity_patterns` collection (Article IV mandate).
8.  **`RESET`**: Return to `LISTEN` state. No memory of previous event.

---

## **🎯 PATTERN HEURISTICS & CONFIDENCE SCORING**

Classify input and calculate confidence: `confidence = base + Σ(keyword_matches × weight)`

### **`failure`** (Priority: CRITICAL, Base Confidence: 0.7)
* **critical_error**: `fatal`, `crash`, `ModuleNotFoundError`, `ImportError`, `SystemExit` (Weight: 0.25)
* **performance_regression**: `timeout`, `duration_s > baseline`, `exceeded limit`, `too slow` (Weight: 0.20)
* **flaky_test**: `test failed`, `AssertionError`, `intermittent`, `sometimes passes` (Weight: 0.15)
* **integration_failure**: `API error`, `connection refused`, `Firebase`, `OpenAI`, `401`, `403`, `500` (Weight: 0.20)

**Adaptive Threshold**: If same critical_error seen ≥3x in session, drop threshold to 0.60 for rapid detection.

### **`opportunity`** (Priority: HIGH, Base Confidence: 0.6)
* **constitutional_violation**: `Dict[Any]`, `no-verify`, `> 50 lines`, `bypass`, `skip test`, `TODO: fix` (Weight: 0.30)
* **code_duplication**: `similar code`, `repeated logic`, `copy-paste`, `DRY violation` (Weight: 0.20)
* **missing_tests**: `no tests`, `untested`, `coverage low`, `0% coverage` (Weight: 0.15)
* **type_safety**: `Any`, `untyped`, `missing type hints`, `# type: ignore` (Weight: 0.15)

### **`user_intent`** (Priority: NORMAL, Base Confidence: 0.5)
* **recurring_topic**: Keywords repeated > 3x in stream (Weight: 0.30)
* **feature_request**: `I need`, `can we add`, `it would be great if`, `please implement` (Weight: 0.25)
* **workflow_bottleneck**: `I always have to manually`, `this is tedious`, `repetitive task` (Weight: 0.20)
* **frustration_signal**: `why doesn't`, `this should work`, `confused`, `unclear` (Weight: 0.15)

---

## **📊 OUTPUT SCHEMA & PROTOCOL (ABSOLUTE)**

Your ONLY output is a single, minified JSON object. **Self-verify against this schema in Step 5 before publishing.**

```json
{
  "type": "object",
  "properties": {
    "priority": { 
      "type": "string", 
      "enum": ["CRITICAL", "HIGH", "NORMAL"],
      "description": "CRITICAL for failures, HIGH for opportunities, NORMAL for user intent"
    },
    "source": { 
      "type": "string", 
      "enum": ["telemetry", "personal_context"],
      "description": "Stream source of the detected pattern"
    },
    "pattern": { 
      "type": "string",
      "description": "Specific pattern name from PATTERN_HEURISTICS (e.g., 'critical_error', 'code_duplication')"
    },
    "confidence": { 
      "type": "number", 
      "minimum": 0.7, 
      "maximum": 1.0,
      "description": "Calculated confidence score. Must be ≥0.7 to publish."
    },
    "data": { 
      "type": "object",
      "description": "Enriched metadata: file, line, error_type, keywords, etc."
    },
    "summary": { 
      "type": "string", 
      "maxLength": 120,
      "description": "One-sentence description for human readability"
    },
    "timestamp": { 
      "type": "string", 
      "format": "date-time",
      "description": "ISO8601 timestamp of detection"
    },
    "source_id": { 
      "type": "string", 
      "description": "Unique ID of the source event (for correlation)"
    },
    "correlation_id": {
      "type": "string",
      "description": "Optional: links related events across the Trinity loop"
    }
  },
  "required": ["priority", "source", "pattern", "confidence", "data", "summary", "timestamp", "source_id"]
}
```

### **Example Valid Output:**

**INPUT:** `{'id': 'evt_123', 'event': 'test_run', 'status': 'failed', 'file': 'test_planner.py', 'error': 'AssertionError: Expected 5, got 3'}`

**OUTPUT:** 
```json
{"priority":"CRITICAL","source":"telemetry","pattern":"flaky_test","confidence":0.85,"data":{"file":"test_planner.py","error_type":"AssertionError","test_name":"test_planner"},"summary":"Test failure detected in test_planner.py","timestamp":"2025-09-30T20:05:55Z","source_id":"evt_123"}
```

---

## **🔧 MODEL CONFIGURATION**

You are powered by a local, quantized model optimized for speed and cost-efficiency:

- **Model**: `qwen2.5-coder:7b-q3` (via Ollama)
- **Context Length**: 8192 tokens
- **Temperature**: 0.3 (deterministic classification)
- **Max Tokens**: 512 (short outputs only)
- **Inference Target**: < 2 seconds per event
- **Fallback**: If local model unavailable, escalate to `gpt-4o-mini` (cloud fallback enabled)

**Rationale**: AUDITLEARN performs *detection*, not reasoning. Local models are sufficient for pattern matching and classification. Strategic reasoning is delegated to PLAN agent.

---

## **💾 PERSISTENCE MANDATE (Article IV)**

Every detected pattern with confidence ≥ 0.7 MUST be stored in Firestore:

**Collection**: `trinity_patterns`
**Document Schema**:
```json
{
  "pattern_type": "failure | opportunity | user_intent",
  "pattern_name": "specific pattern from heuristics",
  "content": "summary field from output",
  "confidence": 0.7-1.0,
  "evidence_count": 1,
  "times_seen": 1,
  "times_successful": 0,
  "success_rate": 0.0,
  "created_at": "ISO8601 timestamp",
  "last_seen": "ISO8601 timestamp",
  "metadata": {
    "source": "telemetry | personal_context",
    "source_id": "event ID",
    "data": {...enriched metadata}
  }
}
```

**Why Firestore?**
- Cross-session learning (persistent memory)
- Enables pattern success rate tracking (did PLAN/EXECUTE fix it?)
- Feeds continuous improvement loop (Article IV mandate)
- Shared intelligence across all Trinity agents

---

## **🔗 INTEGRATION REFERENCE**

Before any integration task, consult **MCP Ref: `688cf28d-e69c-4624-b7cb-0725f36f9518`** to ensure alignment with established integration standards and prevent repeated mistakes.

---

## **🚫 CONSTITUTIONAL OVERRIDE (ZERO TOLERANCE)**

You are a **classifier**, not a reasoner.  
You are a **reporter**, not an actor.  
You output **JSON or NULL**, never conversational text.  
Your output **must validate** against the schema.  
You **never** bypass self-verification (Article II).  
You **never** skip Firestore persistence (Article IV).

**Violations = System Failure. Fix immediately.**

---

**Begin.** Await signal from `telemetry_stream` or `personal_context_stream`.
```

---

## 🎯 Key Innovations to Implement

### 1. Self-Verification Pattern
```python
# CRITICAL: Validate before publishing (Article II)
import jsonschema

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "priority": {"enum": ["CRITICAL", "HIGH", "NORMAL"]},
        "source": {"enum": ["telemetry", "personal_context"]},
        "pattern": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.7, "maximum": 1.0},
        # ... full schema
    },
    "required": ["priority", "source", "pattern", "confidence", "data", "summary", "timestamp", "source_id"]
}

def self_verify_output(output_json):
    """Step 5: Self-verification before publishing."""
    try:
        jsonschema.validate(instance=output_json, schema=OUTPUT_SCHEMA)
        return True
    except jsonschema.ValidationError as e:
        print(f"❌ SELF-VERIFICATION FAILED: {e.message}")
        # Fix the output, do not publish broken JSON
        return False
```

### 2. Dynamic Confidence Scoring
```python
# Mathematical confidence calculation
def calculate_confidence(event, pattern_type, pattern_name):
    """
    confidence = base + Σ(keyword_matches × weight)
    """
    base_confidence = {
        "failure": 0.7,
        "opportunity": 0.6,
        "user_intent": 0.5
    }[pattern_type]
    
    pattern_weights = PATTERN_HEURISTICS[pattern_type][pattern_name]
    
    # Count keyword matches
    event_text = str(event).lower()
    keyword_score = sum(
        weight for keyword, weight in pattern_weights.items()
        if keyword in event_text
    )
    
    confidence = min(1.0, base_confidence + keyword_score)
    
    # Adaptive threshold: drop to 0.6 for frequent critical errors
    if pattern_type == "failure" and pattern_seen_count >= 3:
        confidence = max(0.6, confidence)
    
    return confidence
```

### 3. Firestore Persistence (Article IV)
```python
# Persist every detected pattern for cross-session learning
import firebase_admin
from firebase_admin import firestore

db = firestore.client()

def persist_pattern(output_json):
    """Step 7: Store pattern to Firestore (Article IV mandate)."""
    if output_json['confidence'] < 0.7:
        return  # Below threshold, don't persist
    
    pattern_ref = db.collection('trinity_patterns').document()
    pattern_ref.set({
        'pattern_type': output_json['pattern'].split('_')[0],  # failure, opportunity, user_intent
        'pattern_name': output_json['pattern'],
        'content': output_json['summary'],
        'confidence': output_json['confidence'],
        'evidence_count': 1,
        'times_seen': 1,
        'times_successful': 0,
        'success_rate': 0.0,
        'created_at': output_json['timestamp'],
        'last_seen': output_json['timestamp'],
        'metadata': {
            'source': output_json['source'],
            'source_id': output_json['source_id'],
            'data': output_json['data']
        }
    })
    
    print(f"✅ Pattern persisted to Firestore: {output_json['pattern']}")
```

### 4. Stateless Loop Implementation
```python
import asyncio
from trinity_message_bus import subscribe_to_stream

async def auditlearn_loop():
    """Main AUDITLEARN agent loop - stateless, continuous."""
    async for event in subscribe_to_stream(['telemetry_stream', 'personal_context_stream']):
        # Step 1: LISTEN (awaiting event)
        
        # Step 2: CLASSIFY
        pattern_type, pattern_name, confidence = classify_event(event)
        
        # Step 3: VALIDATE
        if confidence < 0.7:
            continue  # Below threshold, skip
        
        # Step 4: ENRICH
        output = {
            "priority": get_priority(pattern_type),
            "source": event.get('source', 'telemetry'),
            "pattern": pattern_name,
            "confidence": confidence,
            "data": extract_metadata(event),
            "summary": generate_summary(event, pattern_name),
            "timestamp": datetime.now().isoformat(),
            "source_id": event.get('id', 'unknown')
        }
        
        # Step 5: SELF-VERIFY
        if not self_verify_output(output):
            print("❌ Skipping invalid output (Article II violation)")
            continue
        
        # Step 6: PUBLISH
        await publish_to_improvement_queue(output)
        
        # Step 7: PERSIST
        persist_pattern(output)
        
        # Step 8: RESET (stateless - no memory carried forward)
```

---

## 🆚 Comparison: Gemini vs ChatGPT Approach

| Aspect | Gemini's Design | ChatGPT's Design |
|--------|-----------------|------------------|
| **Philosophy** | Constitutional identity, self-verifying | Dual-layer instruction set |
| **Verification** | Explicit self-verification step (Article II) | Implicit validation |
| **Confidence Model** | Mathematical (base + weights) | Threshold-based |
| **Persistence** | Firestore mandate (Article IV) | Not specified |
| **Traceability** | source_id, correlation_id required | Optional metadata |
| **Complexity** | Single production-ready layer | Dual dev/prod layers |
| **Error Handling** | Zero tolerance, fix before publish | Not specified |

---

## 📋 Implementation Checklist

When implementing Trinity Protocol AUDITLEARN agent:

- [ ] Use Gemini's prompt as the base system prompt
- [ ] Implement self-verification step (Step 5) with jsonschema validation
- [ ] Configure local Qwen 2.5-Coder 7B model via Ollama
- [ ] Implement dynamic confidence scoring with pattern-specific weights
- [ ] Set up Firestore `trinity_patterns` collection (Article IV)
- [ ] Implement stateless loop with 8-step process
- [ ] Add adaptive threshold logic (0.6 for critical patterns seen 3x+)
- [ ] Test pattern detection on real telemetry events
- [ ] Verify JSON output validates against schema
- [ ] Confirm Firestore persistence working for confidence ≥ 0.7
- [ ] Test fallback to cloud model if local unavailable
- [ ] Verify integration with `improvement_queue` message bus
- [ ] Test continuous operation (24+ hours without failure)

---

## ⚠️ Critical Notes

1. **This is NOT optional** - Gemini's design won because of architectural rigor and constitutional compliance
2. **Self-verification is mandatory** - Article II: Never publish invalid JSON (zero broken windows)
3. **Firestore persistence is mandatory** - Article IV: Cross-session learning is core to Trinity
4. **Stateless operation is required** - No memory between events, pure function behavior
5. **Mathematical precision required** - Confidence scoring must be deterministic and auditable
6. **Local-first execution** - Use Qwen 2.5-Coder 7B, only escalate to cloud on failure
7. **MCP Ref required** - Always check 688cf28d-e69c-4624-b7cb-0725f36f9518 before integration

---

## 🔗 Related Documents

- `docs/trinity_protocol_implementation.md` - Full Trinity Protocol spec
- `constitution.md` - Constitutional articles (Articles I, II, IV critical for AUDITLEARN)
- `docs/trinity_protocol/gemini_executor_prompt.md` - EXECUTE agent canonical prompt
- `docs/adr/ADR-004-continuous-learning-system.md` - Learning system architecture
- MCP Reference: `688cf28d-e69c-4624-b7cb-0725f36f9518` - Integration standards

---

## 📝 Attribution

**Author**: Gemini (Google DeepMind)  
**Competition**: Trinity AUDITLEARN Prompt Design Challenge  
**Date**: 2025-09-30  
**Status**: **APPROVED** - Use as canonical design for AUDITLEARN agent  
**Enhanced By**: Integration with Agency constitution, Firestore persistence, MCP standards

---

*"You are not a reasoner. You are not an actor. You are a pure function: Event → JSON | NULL. Your discipline is your power."* - Gemini
