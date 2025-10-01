# Proactive Question Engine: Implementation Summary

**Date**: 2025-10-01
**Status**: Specification and Planning Complete
**Timeline**: 2-3 weeks implementation
**Priority**: HIGH

---

## Executive Summary

I've created a comprehensive specification and implementation plan for Trinity's Proactive Question Engine - the critical component that transforms ambient intelligence into helpful, non-intrusive assistance.

**Core Philosophy**: "NO" is fine and is NOT a failure - it's learning data.

**Key Innovation**: The difference between helpful and annoying lies in three dimensions:
1. **Question Quality** (low-stakes casual offers vs high-value project proposals)
2. **Timing Intelligence** (respect flow state, batch similar questions, learn schedule patterns)
3. **Response Learning** (adapt thresholds based on YES/NO patterns)

---

## What Was Created

### 1. Specification Document
**File**: `/Users/am/Code/Agency/specs/proactive_question_engine.md`

**Contents**:
- **5 Functional Requirements** (Question formulation, templates, timing, learning, deduplication)
- **Question Type Classification** (low-stakes vs high-value with clear examples)
- **Template System** (10+ templates for different pattern types)
- **Timing Intelligence** (flow state detection, scheduling, batching)
- **Learning System** (response tracking, metrics, threshold adjustment)
- **Architecture Integration** (Trinity Protocol, Firestore, Message Bus)
- **Success Metrics** (acceptance rate, annoyance rate, value delivery)

**Key Sections**:
- Question Templates: "You mentioned sushi 3 times. Want me to find nearby options?" (low-stakes)
- Value Propositions: "I can help finish it in 2 weeks with 1-3 questions per day" (high-value)
- Timing Rules: Never interrupt flow state, batch similar questions, learn busy times
- Learning Logic: >70% acceptance → lower threshold, <30% acceptance → raise threshold

### 2. Implementation Plan
**File**: `/Users/am/Code/Agency/plans/plan-question-engine.md`

**Contents**:
- **16 Detailed Tasks** with subtasks, dependencies, acceptance criteria
- **3-Week Timeline** (Week 1: Foundation, Week 2: Learning/Integration, Week 3: Testing)
- **Architecture Design** (4 modules: Formulator, Timing, Learning, Deduplication)
- **Data Models** (FormulatedQuestion, UserResponse, QuestionMetrics, TimingDecision)
- **Integration Points** (ARCHITECT agent, Message Bus, Firestore)
- **Testing Strategy** (100+ unit tests, integration scenarios, UAT with Alex)
- **Code Examples** (Template selection, timing decisions, response learning)

**Key Modules**:
- `trinity_protocol/question_engine/formulator.py` - Question generation from patterns
- `trinity_protocol/question_engine/timing.py` - Flow state detection and scheduling
- `trinity_protocol/question_engine/learning.py` - Response classification and adaptation
- `trinity_protocol/question_engine/deduplication.py` - Duplicate prevention and history

---

## Architecture Overview

### Question Pipeline

```
WITNESS (Pattern Detection)
    ↓ (improvement_queue)
    DetectedPattern: recurring_topic, workflow_bottleneck, etc.

ARCHITECT (Strategy Generation)
    ↓ (question_formulation_queue)
    Strategy + Pattern data

QUESTION ENGINE (This component)
    ├→ Formulate: Select template, extract evidence, generate question
    ├→ Classify: Low-stakes (<30 min value) vs High-value (>2 hour value)
    ├→ Time: Detect flow state, schedule delivery, batch similar
    ├→ Deduplicate: Check history, respect NO, re-offer LATER
    ↓ (human_review_queue)
    FormulatedQuestion: "You mentioned X 3 times. Want me to Y?"

USER (Response)
    ↓ (response_queue)
    UserResponse: YES/NO/LATER + sentiment

QUESTION ENGINE (Learning)
    ├→ Classify: YES/NO/LATER detection, sentiment analysis
    ├→ Update: Acceptance rate, success/failure contexts
    ├→ Adjust: Raise/lower thresholds based on acceptance rate
    ├→ Persist: Store in Firestore for cross-session learning
```

### Data Flow Example

**Scenario: Book Writing Assistance**

1. **Pattern Detection** (WITNESS):
   - User mentions "coaching book" 5 times
   - Pattern: workflow_bottleneck, confidence 0.85
   - Evidence: {times_seen: 5, keywords: ["book", "coaching", "writing"]}

2. **Question Formulation**:
   - Template: "You've mentioned {project} {count} times. I can {outcome} in {timeframe} with {effort}. Want to hear more?"
   - Question: "You've mentioned your coaching book 5 times. I can help finish it in 2 weeks with 1-3 questions per day. Want to hear the plan?"
   - Type: high_value (multi-step project, >10 hour value)

3. **Timing Decision**:
   - Check flow state: User in conversation (not in flow)
   - Check schedule: Admin time slot (good for questions)
   - Check duplicates: No recent book questions
   - Decision: Deliver now

4. **User Response**:
   - Answer: "YES, sounds good"
   - Sentiment: positive
   - Context: {time: "2pm", day: "Tuesday", topic: "productivity"}

5. **Learning Update**:
   - Metrics: workflow_bottleneck acceptance_rate → 60% (was 50%)
   - Threshold: min_confidence *= 0.95 (lower threshold, ask sooner)
   - Context: Tuesday 2pm → success context for future questions
   - Firestore: Store response and updated metrics

---

## Key Design Decisions

### 1. Question Type Classification

**Low-Stakes** (Casual Offers):
- **Scope**: Single action, transactional
- **Value**: 5-30 minutes saved
- **Commitment**: None (easy to decline)
- **Length**: Under 100 characters
- **Example**: "You mentioned sushi 3 times. Want me to find nearby options?"

**High-Value** (Project Proposals):
- **Scope**: Multi-step project, collaborative
- **Value**: 2+ hours saved or significant outcome
- **Commitment**: Ongoing engagement (1-3 questions per day)
- **Length**: Under 200 characters (includes value proposition)
- **Example**: "You've mentioned your coaching book 5 times. I can help finish it in 2 weeks with 1-3 questions per day. Want to hear the plan?"

### 2. Timing Intelligence

**Flow State Protection**:
- Indicators: Long silence (>15 min), focused conversation, "don't bother me" phrases
- Action: Wait for conversation lull or task transition
- Override: Emergency only (critical errors with user impact)

**Question Batching**:
- Trigger: 2+ similar pending questions (same pattern type or related topic)
- Limit: Max 5 questions per batch
- Presentation: "I have 3 things: (1) sushi nearby? (2) calendar gaps? (3) PDF summary?"

**Schedule Learning**:
- Track delivery times and outcomes (YES/NO by time of day)
- Identify busy times (low acceptance rate) and good times (high acceptance)
- Prefer delivery during admin time, breaks, or identified good times

### 3. Learning System

**Acceptance Rate Tracking**:
```python
acceptance_rate = yes_count / (yes_count + no_count)
# later_count excluded (timing issue, not content)
```

**Threshold Adjustment**:
- High acceptance (>70%): Lower threshold (confidence *= 0.9, evidence -= 1)
  - Interpretation: User values these questions, ask sooner with less evidence
- Low acceptance (<30%): Raise threshold (confidence *= 1.1, evidence += 1)
  - Interpretation: User doesn't value these, be more selective

**Context Correlation**:
- YES responses: Store context (time, day, recent activity, topic)
- NO responses (negative sentiment): Store as failure context
- Future questions: Prefer success contexts, avoid failure contexts

### 4. Deduplication Logic

**Exact Duplicate** (same pattern_id):
- Previous NO: Don't re-ask (unless significant new evidence, confidence +0.2)
- Previous LATER: Re-ask after expiry time (default 1 day)
- Previous YES: OK to re-ask with new evidence (different aspect)

**Semantic Duplicate** (similarity >0.85):
- Use FAISS for semantic similarity check
- Suppress if too similar within 7-day window
- Exception: Significantly different value proposition

**Question Fatigue Prevention**:
- Hard limit: Max 1 question per 10 minutes
- Daily limit: Max 5 questions per day
- Adaptive: Extend wait times if declining acceptance rate

---

## Implementation Roadmap

### Week 1: Foundation (40 hours)

**Deliverable**: Core formulation and timing working

**Tasks**:
1. Data models and Firestore schema (4h)
2. Question templates system (6h)
3. Question formulator (8h)
4. Flow state detection (6h)
5. Scheduling and batching (8h)
6. Schedule learning (4h)
7. Response collection (start) (4h)

**Validation**: Can formulate questions from patterns, decide timing (now vs wait)

### Week 2: Learning and Integration (40 hours)

**Deliverable**: Full pipeline with learning

**Tasks**:
1. Response collection (complete) (2h)
2. Metrics tracking (5h)
3. Threshold adjustment (6h)
4. Question deduplication (7h)
5. Conversation continuity (5h)
6. ARCHITECT integration (8h)
7. Unit tests (start) (7h)

**Validation**: End-to-end flow works (pattern → question → response → learning)

### Week 3: Testing and Deployment (36 hours)

**Deliverable**: Production-ready system

**Tasks**:
1. Unit tests (complete) (5h)
2. Integration tests (10h)
3. User acceptance testing (8h + 1 week trial)
4. Documentation and deployment (6h)
5. Refinements and bug fixes (7h)

**Validation**: Alex satisfaction >4.0/5.0, annoyance rate <10%, value delivery >80%

---

## Success Metrics

### Primary (User Experience)

1. **User Satisfaction**: "Would you be sad if Trinity stopped asking?"
   - Target: >80% "Yes, I'd be sad"
   - Measure: Quarterly survey after deployment

2. **Acceptance Rate**: % of questions answered YES
   - Baseline: Unknown (first run)
   - Target: >50% overall (>60% low-stakes, >40% high-value)
   - Measure: (yes_count / (yes_count + no_count)) from Firestore

3. **Annoyance Rate**: % of questions with negative sentiment
   - Target: <10%
   - Measure: Sentiment analysis of NO responses

### Secondary (System Performance)

1. **Question Quality**: % grammatically correct and contextual
   - Target: 100%
   - Measure: Automated validation tests

2. **Timing Accuracy**: % delivered at appropriate time
   - Target: <5% during flow state
   - Measure: User feedback "bad timing" tag

3. **Learning Effectiveness**: Improvement in acceptance rate
   - Target: +10% per month (first 3 months)
   - Measure: Monthly trend analysis

4. **Deduplication Rate**: % duplicates prevented
   - Target: >95%
   - Measure: (duplicates_prevented / total_patterns)

---

## Technical Architecture

### Module 1: Question Formulator
**File**: `trinity_protocol/question_engine/formulator.py`

**Responsibilities**:
- Select template based on pattern_name
- Extract evidence from DetectedPattern (times_seen, keywords, timeframe)
- Substitute evidence into template placeholders
- Classify question type (low_stakes vs high_value)
- Generate value proposition for high-value questions
- Validate question (grammar, length, completeness)

**Key Method**:
```python
def formulate_question(pattern: DetectedPattern) -> FormulatedQuestion:
    template = select_template(pattern.pattern_name)
    evidence = extract_evidence(pattern)
    question_text = substitute_evidence(template, evidence)
    question_type = classify_type(pattern)
    value_prop = generate_value_prop(pattern) if question_type == "high_value" else None
    validate_question(question_text, question_type)
    return FormulatedQuestion(...)
```

### Module 2: Timing Intelligence
**File**: `trinity_protocol/question_engine/timing.py`

**Responsibilities**:
- Detect flow state from conversation patterns
- Identify natural breaks (conversation lulls, task transitions)
- Learn user's schedule (busy times, admin time)
- Batch similar pending questions
- Schedule delivery based on priority (time-sensitive vs can-wait)
- Enforce question fatigue limits (1/10min, 5/day)

**Key Method**:
```python
def decide_timing(question: FormulatedQuestion, context: UserContext) -> TimingDecision:
    if context.in_flow_state:
        return wait_for("conversation_lull")
    if question.priority == "time_sensitive":
        return deliver_now() if context.allows_interruption else wait_for("next_break")
    if has_similar_pending(question):
        return batch_and_wait()
    return wait_for("admin_time_or_lull")
```

### Module 3: Learning System
**File**: `trinity_protocol/question_engine/learning.py`

**Responsibilities**:
- Classify user response (YES/NO/LATER)
- Analyze sentiment (positive/neutral/negative)
- Update metrics (acceptance_rate, counts)
- Correlate context (success/failure patterns)
- Adjust thresholds (confidence, evidence)
- Persist learning to Firestore

**Key Method**:
```python
async def learn_from_response(response: UserResponse) -> None:
    metrics = get_metrics(response.question_type, response.pattern_name)
    update_counts(metrics, response.answer)
    correlate_context(metrics, response)
    adjust_thresholds(metrics)
    await persist_to_firestore(metrics)
```

### Module 4: Deduplication Service
**File**: `trinity_protocol/question_engine/deduplication.py`

**Responsibilities**:
- Check exact duplicate (same pattern_id)
- Check semantic duplicate (FAISS similarity >0.85)
- Respect NO responses (don't re-ask within 7 days)
- Re-offer LATER questions after expiry
- Maintain question history (SQLite + Firestore)
- Cleanup old history (>30 days)

**Key Method**:
```python
def check_duplicate(question: FormulatedQuestion) -> Optional[QuestionHistory]:
    exact = find_exact_duplicate(question.pattern_id)
    if exact and exact.response == "NO":
        return exact  # Suppress (user already declined)
    semantic = find_semantic_duplicate(question.text)
    if semantic and semantic.asked_within_days(7):
        return semantic  # Suppress (too similar, too soon)
    return None  # Not a duplicate, OK to ask
```

---

## Storage Schema

### Firestore Collections

**1. trinity_questions** (formulated questions):
```typescript
{
  question_id: string,           // Unique ID
  pattern_id: string,            // Source pattern ID
  question_type: "low_stakes" | "high_value",
  pattern_name: string,          // e.g., "recurring_topic"
  question_text: string,         // "You mentioned sushi 3 times. Want me to find nearby options?"
  value_proposition: string | null,  // For high-value questions
  confidence: number,            // From pattern detection
  evidence: {
    times_seen: number,
    keywords: string[],
    timeframe: string
  },
  timing: {
    created_at: timestamp,
    scheduled_for: timestamp | null,
    delivered_at: timestamp | null,
    expires_at: timestamp | null
  },
  status: "pending" | "delivered" | "expired" | "suppressed"
}
```

**2. trinity_question_responses** (user responses):
```typescript
{
  response_id: string,
  question_id: string,           // References trinity_questions
  answer: "YES" | "NO" | "LATER",
  sentiment: "positive" | "neutral" | "negative",
  context: {
    time_of_day: string,         // "2pm"
    day_of_week: string,         // "Tuesday"
    recent_activity: string,     // "productivity discussion"
    active_topic: string | null
  },
  responded_at: timestamp
}
```

**3. trinity_question_metrics** (learning metrics):
```typescript
{
  metric_id: string,
  question_type: string,         // "low_stakes" | "high_value"
  pattern_name: string,          // "recurring_topic"
  total_asked: number,
  yes_count: number,
  no_count: number,
  later_count: number,
  acceptance_rate: number,       // yes / (yes + no)
  success_contexts: any[],       // Contexts that led to YES
  failure_contexts: any[],       // Contexts that led to NO
  last_updated: timestamp
}
```

### SQLite Tables (local persistence)

```sql
CREATE TABLE question_history (
    id INTEGER PRIMARY KEY,
    question_id TEXT UNIQUE,
    pattern_id TEXT,
    question_text TEXT,
    question_type TEXT,
    asked_at TEXT,
    response_answer TEXT,        -- YES/NO/LATER
    response_sentiment TEXT,     -- positive/neutral/negative
    expires_at TEXT
);

CREATE INDEX idx_pattern_id ON question_history(pattern_id);
CREATE INDEX idx_asked_at ON question_history(asked_at);
```

---

## Risk Assessment & Mitigation

### Risk 1: Question Fatigue (HIGH)

**Symptoms**: User gets annoyed by too many questions, even if individually good.

**Mitigation**:
- Hard limit: Max 5 questions per day
- Rate limit: Max 1 question per 10 minutes
- Batch similar questions (1 notification with 3 questions > 3 separate)
- Learn from declining acceptance rate (extend wait times)
- User control: `trinity mute <pattern>`, `trinity quiet-hours <start> <end>`

**Success Criteria**: Annoyance rate <10%

### Risk 2: Poor Timing (MEDIUM)

**Symptoms**: Questions interrupt flow state or arrive at bad times.

**Mitigation**:
- Flow state detection (silence, focused conversation, explicit phrases)
- Schedule learning (identify busy times from acceptance patterns)
- LATER option always available
- Emergency interrupts only for critical errors (data loss, deadline miss)

**Success Criteria**: <5% "bad timing" feedback

### Risk 3: Low Value Questions (MEDIUM)

**Symptoms**: Questions don't provide enough value to justify interruption.

**Mitigation**:
- Strict thresholds (min_confidence 0.7, min_evidence 3)
- High-value questions must articulate value proposition
- Learn from NO responses and raise thresholds
- User can mute specific patterns

**Success Criteria**: Acceptance rate >50%

### Risk 4: Privacy Concerns (LOW)

**Symptoms**: User uncomfortable with ambient listening data usage.

**Mitigation**:
- Transparent data usage (only for question formulation)
- User can delete question history
- No raw ambient data stored (only patterns)
- Full control (can disable system)

**Success Criteria**: Zero privacy complaints

---

## Constitutional Compliance

### Article I: Complete Context Before Action
- Question formulation waits for full pattern evidence (min_confidence 0.7, min_evidence 3)
- No questions based on incomplete data
- Timeout handling: retry pattern detection if incomplete

### Article II: 100% Verification and Stability
- All questions validated (grammar, length, completeness)
- Test coverage: 100% for formulation, timing, learning
- Quality gate: Questions must pass validation before delivery

### Article IV: Continuous Learning and Improvement
- All responses stored in Firestore for cross-session learning
- Metrics updated in real-time (acceptance rate, context correlation)
- Thresholds adjust based on user feedback (>70% lower, <30% raise)
- Learning applied to future questions (measurable improvement)

### Article V: Spec-Driven Development
- This implementation follows formal specification (`specs/proactive_question_engine.md`)
- All requirements traced to spec sections
- Plan documents architecture, tasks, acceptance criteria
- Implementation blocked until spec/plan approved

---

## Next Steps

### Immediate (Before Implementation)

1. **Review Specification** (`specs/proactive_question_engine.md`):
   - Validate requirements with Alex
   - Confirm question examples (low-stakes vs high-value)
   - Approve success metrics (acceptance rate >50%, annoyance <10%)

2. **Review Implementation Plan** (`plans/plan-question-engine.md`):
   - Validate 3-week timeline
   - Confirm task breakdown (16 tasks, 116 hours)
   - Approve architecture (4 modules: Formulator, Timing, Learning, Deduplication)

3. **Decision on Open Questions**:
   - Q1: Question frequency cap (5/day vs adaptive)
   - Q2: Emergency override (never vs critical errors)
   - Q3: LATER timing (1 day vs context-based)
   - Q4: User control UI (CLI vs natural language)

### Week 1: Foundation

**Start**: TASK-001 (Data Models and Schema)

**Focus**: Core formulation and timing working

**Validation**: Can formulate questions from patterns, decide timing

### Week 2: Learning and Integration

**Start**: TASK-007 (Response Collection) - continue from Week 1

**Focus**: Full pipeline with learning

**Validation**: End-to-end flow (pattern → question → response → learning)

### Week 3: Testing and Deployment

**Start**: TASK-013 (Unit Tests) - complete from Week 2

**Focus**: Production-ready with documentation

**Validation**: Alex satisfaction >4.0/5.0, annoyance <10%, value >80%

---

## Files Created

1. **Specification**: `/Users/am/Code/Agency/specs/proactive_question_engine.md`
   - 500+ lines, comprehensive requirements
   - Question types, templates, timing, learning, deduplication
   - Success metrics, architecture, storage schema

2. **Implementation Plan**: `/Users/am/Code/Agency/plans/plan-question-engine.md`
   - 800+ lines, detailed task breakdown
   - 16 tasks with subtasks, dependencies, acceptance criteria
   - 3-week timeline, code examples, testing strategy

3. **Summary** (this file): `/Users/am/Code/Agency/QUESTION_ENGINE_SUMMARY.md`
   - Executive overview
   - Architecture diagrams
   - Implementation roadmap
   - Next steps

---

## Key Takeaways

### 1. Philosophy: "NO" is Learning Data

User rejection is not failure - it's valuable feedback:
- **NO with positive sentiment**: Question not valuable (raise threshold)
- **NO with negative sentiment**: Question annoying (suppress pattern + raise threshold)
- **LATER**: Timing issue (re-offer at better time)

### 2. Quality Over Quantity

Better to ask 1 great question than 5 mediocre ones:
- Strict thresholds (min_confidence 0.7, min_evidence 3)
- Value proposition required for high-value questions
- Batching similar questions (reduce notification count)
- Question fatigue prevention (max 5/day, 1/10min)

### 3. Timing is Everything

Even great questions fail if timed poorly:
- Flow state is sacred (never interrupt deep work)
- Learn user's schedule (busy mornings, free afternoons)
- Natural breaks preferred (conversation lulls, task transitions)
- LATER option always available (timing issue vs content issue)

### 4. Continuous Improvement

System gets better with every interaction:
- Acceptance rate >70%: Lower threshold (user values these)
- Acceptance rate <30%: Raise threshold (be more selective)
- Context correlation: Identify success/failure patterns
- Cross-session learning: Knowledge accumulates in Firestore

---

## Success Definition

**Alex says**: "I would be sad if Trinity stopped asking these questions."

(Not "finally it shut up" or "this is annoying")

This is the ultimate validation that the question engine is helpful, not intrusive.

---

**Status**: Specification and Planning Complete ✅

**Ready for**: Implementation (Week 1 starts with TASK-001)

**Estimated Completion**: 2-3 weeks (116 hours total effort)

**Next Agent**: Can start implementation immediately from plan
