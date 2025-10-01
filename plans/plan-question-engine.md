# Implementation Plan: Proactive Question Engine

**Spec**: `specs/proactive_question_engine.md`
**Created**: 2025-10-01
**Timeline**: 2-3 weeks
**Priority**: HIGH
**Complexity**: MEDIUM-HIGH

---

## Executive Summary

This plan transforms the Question Engine specification into a concrete implementation roadmap. The engine will formulate thoughtful, non-intrusive questions from detected patterns, learn from user responses, and continuously improve question quality and timing.

**Core Philosophy**: "NO" is learning data, not failure.

**Architecture Approach**:
- **Module 1**: Question Formulation Engine (templates, classification, evidence)
- **Module 2**: Timing Intelligence (flow detection, scheduling, batching)
- **Module 3**: Learning System (response tracking, metrics, adaptation)
- **Module 4**: Deduplication Service (history, semantic similarity, suppression)

---

## Architecture Overview

### Component Structure

```
trinity_protocol/
├── question_engine/              [NEW - Core module]
│   ├── __init__.py
│   ├── formulator.py             # Question formulation from patterns
│   ├── templates.py              # Question templates by pattern type
│   ├── timing.py                 # Timing intelligence and scheduling
│   ├── learning.py               # Response learning and adaptation
│   ├── deduplication.py          # Duplicate detection and suppression
│   └── models.py                 # Data models (Question, Response, Metrics)
│
├── architect_agent.py            [MODIFY - Integration point]
│   └── + question_engine integration
│
└── message_bus.py                [EXTEND - New queues]
    └── + question_formulation_queue, response_queue
```

### Data Models

```python
# trinity_protocol/question_engine/models.py

from dataclasses import dataclass
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime

QuestionType = Literal["low_stakes", "high_value", "medium"]
AnswerType = Literal["YES", "NO", "LATER"]
SentimentType = Literal["positive", "neutral", "negative"]

@dataclass
class FormulatedQuestion:
    """Formulated question ready for delivery."""
    question_id: str
    pattern_id: str
    pattern_name: str
    question_type: QuestionType
    question_text: str
    value_proposition: Optional[str]
    confidence: float
    evidence: Dict[str, Any]  # times_seen, keywords, timeframe
    timing: "TimingDecision"
    created_at: datetime
    status: Literal["pending", "delivered", "expired", "suppressed"]

@dataclass
class TimingDecision:
    """Timing decision for question delivery."""
    deliver_now: bool
    wait_for_signal: Optional[str]  # "conversation_lull", "admin_time", etc.
    batch_with: List[str]  # Question IDs to batch
    scheduled_for: Optional[datetime]
    expires_at: Optional[datetime]

@dataclass
class UserResponse:
    """User response to question."""
    response_id: str
    question_id: str
    answer: AnswerType
    sentiment: SentimentType
    context: Dict[str, Any]  # time_of_day, recent_activity, etc.
    responded_at: datetime

@dataclass
class QuestionMetrics:
    """Learning metrics for question type/pattern."""
    metric_id: str
    question_type: QuestionType
    pattern_name: str
    total_asked: int
    yes_count: int
    no_count: int
    later_count: int
    acceptance_rate: float
    success_contexts: List[Dict[str, Any]]
    failure_contexts: List[Dict[str, Any]]
    last_updated: datetime
```

### Integration Flow

```
1. WITNESS detects pattern
   ↓ (improvement_queue)

2. ARCHITECT analyzes pattern
   ├→ Generates strategy
   ├→ [NEW] Formulates question via QuestionEngine
   ↓ (question_formulation_queue)

3. QuestionEngine processes
   ├→ Formulate question from template
   ├→ Classify type (low_stakes vs high_value)
   ├→ Decide timing (now vs wait)
   ├→ Check deduplication
   ↓ (human_review_queue)

4. User responds
   ↓ (response_queue)

5. QuestionEngine learns
   ├→ Classify response (YES/NO/LATER)
   ├→ Update metrics (acceptance rate)
   ├→ Adjust thresholds (confidence, evidence)
   ├→ Store in Firestore
```

---

## Task Breakdown

### Phase 1: Core Formulation Engine (Week 1)

#### TASK-001: Data Models and Schema

**Description**: Define core data models and Firestore schema for questions, responses, and metrics.

**Subtasks**:
- [ ] TASK-001.1: Create `trinity_protocol/question_engine/models.py`
  - FormulatedQuestion dataclass
  - TimingDecision dataclass
  - UserResponse dataclass
  - QuestionMetrics dataclass
  - Type definitions (QuestionType, AnswerType, SentimentType)

- [ ] TASK-001.2: Define Firestore collections schema
  - `trinity_questions` collection schema
  - `trinity_question_responses` collection schema
  - `trinity_question_metrics` collection schema
  - Add to `shared/models/` for documentation

- [ ] TASK-001.3: Create SQLite tables for local persistence
  - `question_history` table
  - Indexes (pattern_id, asked_at)
  - Migration script

**Dependencies**: None

**Acceptance Criteria**:
- [ ] All models defined with full typing
- [ ] Firestore schema documented
- [ ] SQLite tables created with indexes
- [ ] Models include to_dict() and from_dict() methods

**Estimated Effort**: 4 hours

---

#### TASK-002: Question Templates System

**Description**: Implement template system for question formulation with evidence substitution.

**Subtasks**:
- [ ] TASK-002.1: Create `trinity_protocol/question_engine/templates.py`
  - QuestionTemplate dataclass (template, max_length, requires_value_prop)
  - Template registry (dict mapping pattern_name to templates)
  - Evidence substitution logic ({topic}, {count}, {action} placeholders)

- [ ] TASK-002.2: Define low-stakes templates (5+ patterns)
  - Recurring topic template
  - Small friction template
  - Quick win template
  - Reminder template
  - Information template

- [ ] TASK-002.3: Define high-value templates (5+ patterns)
  - Project opportunity template
  - Decision support template
  - Workflow optimization template
  - Learning opportunity template
  - Strategic assistance template

- [ ] TASK-002.4: Template validation
  - Grammar validation (basic rules)
  - Character limit enforcement
  - Required placeholder verification
  - Test with sample patterns

**Dependencies**: TASK-001 (models)

**Acceptance Criteria**:
- [ ] 10+ templates covering common patterns
- [ ] All templates produce grammatically correct questions
- [ ] Low-stakes templates under 100 chars
- [ ] High-value templates under 200 chars
- [ ] Evidence substitution works correctly

**Estimated Effort**: 6 hours

---

#### TASK-003: Question Formulator

**Description**: Core formulation engine that transforms patterns into questions.

**Subtasks**:
- [ ] TASK-003.1: Create `trinity_protocol/question_engine/formulator.py`
  - QuestionFormulator class
  - Template selection logic (pattern_name -> template)
  - Evidence extraction from DetectedPattern
  - Value proposition generation for high-value questions

- [ ] TASK-003.2: Implement type classification
  - classify_question_type() method
  - Logic: scope (single_action vs project) + value (minutes vs hours)
  - Return QuestionType (low_stakes, high_value, medium)

- [ ] TASK-003.3: Implement question generation
  - formulate_question() method
  - Input: DetectedPattern from WITNESS
  - Output: FormulatedQuestion
  - Steps: select template, extract evidence, substitute, classify type

- [ ] TASK-003.4: Validation and error handling
  - Validate generated question (grammar, length)
  - Handle missing template (fallback to generic)
  - Handle incomplete evidence (skip question)
  - Log formulation failures

**Dependencies**: TASK-001, TASK-002

**Acceptance Criteria**:
- [ ] Formulate questions from DetectedPattern
- [ ] Type classification works (low_stakes vs high_value)
- [ ] Evidence correctly extracted and substituted
- [ ] High-value questions include value proposition
- [ ] Validation catches malformed questions

**Estimated Effort**: 8 hours

---

### Phase 2: Timing Intelligence (Week 1-2)

#### TASK-004: Flow State Detection

**Description**: Detect when user is in flow state (deep work) and should not be interrupted.

**Subtasks**:
- [ ] TASK-004.1: Create `trinity_protocol/question_engine/timing.py`
  - TimingEngine class
  - UserContext dataclass (in_flow_state, schedule, recent_activity)

- [ ] TASK-004.2: Implement flow state heuristics
  - Long silence indicator (>15 min no conversation)
  - Focused conversation indicator (technical topics, no interruptions)
  - "Don't bother me" phrase detection
  - Flow state scoring (0-1)

- [ ] TASK-004.3: Conversation lull detection
  - Identify natural breaks (>2 min silence after conversation)
  - Task transition detection (topic change)
  - Admin time detection (calendar gaps, routine tasks)

**Dependencies**: TASK-001

**Acceptance Criteria**:
- [ ] Flow state detected from conversation patterns
- [ ] Conversation lulls identified
- [ ] Flow state prevents question delivery
- [ ] Natural breaks trigger pending questions

**Estimated Effort**: 6 hours

---

#### TASK-005: Scheduling and Batching

**Description**: Intelligent scheduling of questions and batching of similar questions.

**Subtasks**:
- [ ] TASK-005.1: Implement timing decision logic
  - decide_timing() method
  - Input: FormulatedQuestion, UserContext
  - Output: TimingDecision
  - Logic: flow state, priority, batch opportunities

- [ ] TASK-005.2: Priority-based delivery
  - Time-sensitive questions (deliver within deadline)
  - Can-wait questions (defer to natural break)
  - Emergency questions (interrupt if critical)
  - Priority scoring algorithm

- [ ] TASK-005.3: Question batching
  - find_similar_pending_questions() method
  - Similarity criteria (same pattern type, related topic)
  - Batch size limit (max 5 questions)
  - Batch presentation format

- [ ] TASK-005.4: Schedule persistence
  - Store scheduled questions in SQLite
  - Scheduled delivery worker (async task)
  - Handle expired questions (>24h pending)

**Dependencies**: TASK-004

**Acceptance Criteria**:
- [ ] Time-sensitive questions delivered within deadline
- [ ] Can-wait questions defer to natural breaks
- [ ] Similar questions batched (2+ similar -> batch)
- [ ] Scheduled delivery works across restarts
- [ ] Expired questions cleaned up

**Estimated Effort**: 8 hours

---

#### TASK-006: Schedule Learning

**Description**: Learn user's schedule patterns (busy times, admin time) to optimize delivery.

**Subtasks**:
- [ ] TASK-006.1: Implement schedule tracking
  - Track question delivery times and outcomes
  - Identify busy times (low acceptance rate)
  - Identify good times (high acceptance rate)
  - Store schedule patterns in Firestore

- [ ] TASK-006.2: Apply schedule learning
  - Prefer delivery during identified good times
  - Avoid delivery during identified busy times
  - Adjust scheduling weights based on history

**Dependencies**: TASK-005

**Acceptance Criteria**:
- [ ] Schedule patterns identified from history
- [ ] Busy times avoided for can-wait questions
- [ ] Good times preferred for delivery
- [ ] Schedule learning persists across sessions

**Estimated Effort**: 4 hours

---

### Phase 3: Learning System (Week 2)

#### TASK-007: Response Collection and Classification

**Description**: Collect and classify user responses (YES/NO/LATER) with sentiment analysis.

**Subtasks**:
- [ ] TASK-007.1: Create `trinity_protocol/question_engine/learning.py`
  - ResponseClassifier class
  - classify_answer() method (YES/NO/LATER detection)
  - analyze_sentiment() method (positive/neutral/negative)

- [ ] TASK-007.2: Implement answer detection
  - YES patterns: "yes", "sure", "go ahead", "sounds good", "do it"
  - NO patterns: "no", "not now", "nah", "skip", "not interested"
  - LATER patterns: "later", "remind me", "ask me tomorrow"
  - Fuzzy matching (handle variations)

- [ ] TASK-007.3: Implement sentiment analysis
  - Positive indicators: "great", "thanks", "love it", enthusiastic tone
  - Negative indicators: "annoying", "stop", frustrated tone
  - Neutral: simple yes/no without emotion
  - Sentiment scoring (simple keyword-based initially)

- [ ] TASK-007.4: Context capture
  - Capture time of day, day of week
  - Capture recent activity (from conversation)
  - Capture active topic (conversation context)
  - Store context with response

**Dependencies**: TASK-001

**Acceptance Criteria**:
- [ ] Answers correctly classified (YES/NO/LATER)
- [ ] Sentiment detected (positive/neutral/negative)
- [ ] Context captured with each response
- [ ] Responses stored in Firestore

**Estimated Effort**: 6 hours

---

#### TASK-008: Metrics Tracking and Updating

**Description**: Track acceptance rates and update metrics based on responses.

**Subtasks**:
- [ ] TASK-008.1: Implement metrics storage
  - QuestionMetrics dataclass (already in TASK-001)
  - get_metrics() method (retrieve from Firestore)
  - create_metrics() method (initialize for new pattern)

- [ ] TASK-008.2: Implement metrics update
  - update_metrics() method
  - Increment counters (yes_count, no_count, later_count)
  - Recalculate acceptance_rate (yes / (yes + no))
  - Store updated metrics in Firestore

- [ ] TASK-008.3: Context correlation
  - store_success_context() method (YES responses)
  - store_failure_context() method (NO responses)
  - Identify common patterns in contexts
  - Use for future timing decisions

**Dependencies**: TASK-007

**Acceptance Criteria**:
- [ ] Metrics tracked per question_type and pattern_name
- [ ] Acceptance rate calculated correctly
- [ ] Success/failure contexts stored
- [ ] Metrics updated in real-time

**Estimated Effort**: 5 hours

---

#### TASK-009: Threshold Adjustment (Adaptive Learning)

**Description**: Adjust confidence/evidence thresholds based on acceptance rates.

**Subtasks**:
- [ ] TASK-009.1: Implement threshold adjustment logic
  - adjust_thresholds() method
  - Input: QuestionMetrics
  - Logic: High acceptance (>70%) -> lower threshold, Low (<30%) -> raise
  - Apply to PatternDetector config

- [ ] TASK-009.2: Pattern configuration management
  - get_pattern_config() method
  - Update min_confidence (multiply by 0.9 or 1.1)
  - Update min_evidence (subtract 1 or add 1)
  - Store updated config in Firestore

- [ ] TASK-009.3: Learning application
  - Apply learned thresholds to future pattern detection
  - Validate threshold changes (min 0.5, max 1.0)
  - Log threshold adjustments for audit

**Dependencies**: TASK-008

**Acceptance Criteria**:
- [ ] Thresholds adjust based on acceptance rate
- [ ] High acceptance (>70%) lowers thresholds
- [ ] Low acceptance (<30%) raises thresholds
- [ ] Threshold changes persist across sessions
- [ ] Measurable improvement in acceptance rate over time

**Estimated Effort**: 6 hours

---

### Phase 4: Deduplication & Integration (Week 2-3)

#### TASK-010: Question Deduplication

**Description**: Prevent duplicate questions and respect user's NO responses.

**Subtasks**:
- [ ] TASK-010.1: Create `trinity_protocol/question_engine/deduplication.py`
  - DeduplicationService class
  - QuestionHistory dataclass (question_id, pattern_id, asked_at, response)

- [ ] TASK-010.2: Implement duplicate detection
  - check_duplicate() method
  - Exact duplicate: same pattern_id
  - Semantic duplicate: similarity >0.85 (FAISS)
  - Time window: 7 days

- [ ] TASK-010.3: Duplicate handling logic
  - NO response: Don't re-ask (unless significant new evidence)
  - LATER response: Re-ask after expiry time
  - YES response: OK to re-ask with new evidence
  - Suppression tracking

- [ ] TASK-010.4: Question history management
  - Store question history in SQLite
  - Cleanup old history (>30 days)
  - Sync with Firestore for cross-device

**Dependencies**: TASK-001, TASK-003

**Acceptance Criteria**:
- [ ] Duplicates within 7 days prevented
- [ ] NO responses respected (no re-ask)
- [ ] LATER responses re-offered after expiry
- [ ] Semantic similarity works (FAISS)
- [ ] History cleaned up (>30 days)

**Estimated Effort**: 7 hours

---

#### TASK-011: Conversation Continuity

**Description**: Maintain conversation context and prevent question fatigue.

**Subtasks**:
- [ ] TASK-011.1: Conversation context tracking
  - ConversationContext dataclass
  - Track recent messages (last 10)
  - Track active topic (from conversation)
  - Track last_question_at (prevent fatigue)

- [ ] TASK-011.2: Contextual phrasing
  - Reference active topic ("Speaking of X...")
  - Add transitions for unrelated ("By the way...")
  - Adjust phrasing based on conversation flow

- [ ] TASK-011.3: Question fatigue prevention
  - Max 1 question per 10 minutes
  - Max 5 questions per day
  - Detect fatigue signals (declining acceptance)
  - Extend wait times when fatigued

**Dependencies**: TASK-010

**Acceptance Criteria**:
- [ ] Questions reference active topic when relevant
- [ ] Transitions used for topic changes
- [ ] Question fatigue prevented (max 1/10min)
- [ ] Daily limit enforced (max 5/day)

**Estimated Effort**: 5 hours

---

#### TASK-012: ARCHITECT Integration

**Description**: Integrate Question Engine into ARCHITECT agent workflow.

**Subtasks**:
- [ ] TASK-012.1: Modify `trinity_protocol/architect_agent.py`
  - Import QuestionFormulator
  - Add question formulation step after strategy generation
  - Publish to question_formulation_queue

- [ ] TASK-012.2: Add message bus queues
  - Add question_formulation_queue to MessageBus
  - Add response_queue for user responses
  - Update queue configuration

- [ ] TASK-012.3: Question delivery worker
  - Subscribe to question_formulation_queue
  - Process questions through timing engine
  - Deliver to human_review_queue when ready

- [ ] TASK-012.4: Response feedback loop
  - Subscribe to response_queue
  - Classify response and update metrics
  - Adjust thresholds based on learning

**Dependencies**: TASK-003, TASK-005, TASK-009, TASK-010

**Acceptance Criteria**:
- [ ] ARCHITECT generates questions from patterns
- [ ] Questions processed through timing engine
- [ ] Delivery respects timing decisions
- [ ] Responses trigger learning updates
- [ ] Full pipeline works end-to-end

**Estimated Effort**: 8 hours

---

### Phase 5: Testing & Refinement (Week 3)

#### TASK-013: Unit Tests

**Description**: Comprehensive unit tests for all components.

**Subtasks**:
- [ ] TASK-013.1: Template system tests
  - Test template selection by pattern
  - Test evidence substitution
  - Test character limit enforcement
  - Test grammar validation

- [ ] TASK-013.2: Formulation tests
  - Test question generation from patterns
  - Test type classification logic
  - Test value proposition generation
  - Test validation (malformed questions)

- [ ] TASK-013.3: Timing tests
  - Test flow state detection
  - Test scheduling logic (time-sensitive vs can-wait)
  - Test batching logic (similar questions)
  - Test schedule persistence

- [ ] TASK-013.4: Learning tests
  - Test response classification (YES/NO/LATER)
  - Test sentiment analysis
  - Test metrics update logic
  - Test threshold adjustment

- [ ] TASK-013.5: Deduplication tests
  - Test exact duplicate detection
  - Test semantic duplicate detection
  - Test NO response respect
  - Test LATER re-offer logic

**Dependencies**: All previous tasks

**Acceptance Criteria**:
- [ ] 100+ unit tests covering all modules
- [ ] 100% test pass rate
- [ ] Edge cases covered (missing data, timeouts)
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)

**Estimated Effort**: 12 hours

---

#### TASK-014: Integration Tests

**Description**: End-to-end integration tests for full pipeline.

**Subtasks**:
- [ ] TASK-014.1: Pattern to question flow
  - Test: DetectedPattern -> FormulatedQuestion
  - Verify: Template selection, evidence extraction
  - Validate: Question quality and type

- [ ] TASK-014.2: Timing and delivery flow
  - Test: FormulatedQuestion -> TimingDecision -> Delivery
  - Verify: Flow state detection, scheduling
  - Validate: Delivery timing (now vs wait)

- [ ] TASK-014.3: Response and learning flow
  - Test: UserResponse -> Metrics update -> Threshold adjustment
  - Verify: Response classification, metrics calculation
  - Validate: Thresholds adjust correctly

- [ ] TASK-014.4: Deduplication flow
  - Test: Duplicate pattern -> Suppression
  - Verify: History check, similarity detection
  - Validate: Suppression logic (NO, LATER, YES)

- [ ] TASK-014.5: Firestore persistence
  - Test: Questions, responses, metrics persist
  - Verify: Data survives restart
  - Validate: Cross-session learning works

**Dependencies**: TASK-013

**Acceptance Criteria**:
- [ ] Full pipeline tested end-to-end
- [ ] Firestore persistence verified
- [ ] Learning effectiveness measured
- [ ] Restart durability proven

**Estimated Effort**: 10 hours

---

#### TASK-015: User Acceptance Testing

**Description**: Real-world testing with Alex for quality validation.

**Subtasks**:
- [ ] TASK-015.1: Question quality review
  - Alex reviews 20 formulated questions
  - Rates quality (1-5 scale)
  - Target: Average >4.0

- [ ] TASK-015.2: One-week trial
  - Alex uses system for 1 week
  - Reports annoyance incidents
  - Target: <2 annoyance incidents

- [ ] TASK-015.3: Value measurement
  - Alex accepts 10 questions
  - Measures time saved or value gained
  - Target: >80% provide measurable value

- [ ] TASK-015.4: Feedback incorporation
  - Collect Alex's feedback
  - Identify improvement areas
  - Implement high-priority refinements

**Dependencies**: TASK-014

**Acceptance Criteria**:
- [ ] Alex satisfaction >4.0/5.0
- [ ] Annoyance rate <10% (2/week)
- [ ] Value delivery >80% (of accepted questions)
- [ ] Feedback implemented (P0 items)

**Estimated Effort**: 8 hours (plus 1 week trial time)

---

#### TASK-016: Documentation and Deployment

**Description**: Complete documentation and production deployment preparation.

**Subtasks**:
- [ ] TASK-016.1: API documentation
  - Docstrings for all public methods
  - Usage examples for QuestionEngine
  - Integration guide for ARCHITECT

- [ ] TASK-016.2: User guide
  - How question engine works (for Alex)
  - User control commands (mute, quiet-hours)
  - Response format and learning

- [ ] TASK-016.3: Operational guide
  - Monitoring metrics (acceptance rate, question count)
  - Troubleshooting common issues
  - Performance tuning (thresholds, timing)

- [ ] TASK-016.4: Deployment checklist
  - Firestore collections created
  - SQLite tables initialized
  - Message bus queues configured
  - Monitoring dashboards setup

**Dependencies**: TASK-015

**Acceptance Criteria**:
- [ ] All public APIs documented
- [ ] User guide complete (for Alex)
- [ ] Operational guide complete (for maintenance)
- [ ] Deployment checklist ready

**Estimated Effort**: 6 hours

---

## Implementation Order

### Week 1: Foundation (40 hours)

**Priority**: P0 (Must Have)

1. **TASK-001**: Data Models and Schema (4h)
2. **TASK-002**: Question Templates System (6h)
3. **TASK-003**: Question Formulator (8h)
4. **TASK-004**: Flow State Detection (6h)
5. **TASK-005**: Scheduling and Batching (8h)
6. **TASK-006**: Schedule Learning (4h)
7. **TASK-007**: Response Collection and Classification (6h) - START

**Deliverable**: Core formulation and timing working

---

### Week 2: Learning and Integration (40 hours)

**Priority**: P0-P1

1. **TASK-007**: Response Collection (complete) (2h)
2. **TASK-008**: Metrics Tracking (5h)
3. **TASK-009**: Threshold Adjustment (6h)
4. **TASK-010**: Question Deduplication (7h)
5. **TASK-011**: Conversation Continuity (5h)
6. **TASK-012**: ARCHITECT Integration (8h)
7. **TASK-013**: Unit Tests (12h) - START

**Deliverable**: Full pipeline working with learning

---

### Week 3: Testing and Deployment (36 hours)

**Priority**: P0 (Quality Assurance)

1. **TASK-013**: Unit Tests (complete) (4h)
2. **TASK-014**: Integration Tests (10h)
3. **TASK-015**: User Acceptance Testing (8h + 1 week trial)
4. **TASK-016**: Documentation and Deployment (6h)
5. **Buffer**: Refinements and bug fixes (8h)

**Deliverable**: Production-ready system with documentation

---

## Testing Strategy

### Unit Test Coverage

**Target**: 100% coverage of core logic

**Files to Test**:
- `formulator.py`: Template selection, evidence extraction, type classification
- `templates.py`: Template rendering, validation, character limits
- `timing.py`: Flow detection, scheduling, batching
- `learning.py`: Response classification, metrics, thresholds
- `deduplication.py`: Duplicate detection, history, suppression

**Test Framework**: pytest with async support

**Mocking Strategy**:
- Mock Firestore (use fakes, not real connection)
- Mock MessageBus (in-memory queue)
- Mock UserContext (predefined states)

---

### Integration Test Scenarios

**Scenario 1: Happy Path (Low-Stakes)**
```
1. WITNESS detects recurring_topic pattern (sushi 3x)
2. ARCHITECT formulates low-stakes question
3. Timing engine delivers immediately (not in flow)
4. User responds YES
5. Metrics updated (acceptance_rate increases)
6. Threshold lowered for recurring_topic
```

**Scenario 2: High-Value with Timing**
```
1. WITNESS detects workflow_bottleneck (podcast editing)
2. ARCHITECT formulates high-value question (2h value prop)
3. Timing engine waits (user in flow state)
4. Flow state ends (conversation lull)
5. Question delivered
6. User responds YES
7. Project starts
```

**Scenario 3: Duplicate Suppression**
```
1. Question asked about sushi (pattern_id: P123)
2. User responds NO
3. Same pattern detected again (sushi 5x)
4. Deduplication detects duplicate (pattern_id: P123)
5. Question suppressed (user already said NO)
6. No duplicate question sent
```

**Scenario 4: Learning Adaptation**
```
1. 10 questions asked about calendar_gaps
2. 2 YES, 8 NO (20% acceptance)
3. Metrics updated (low acceptance)
4. Thresholds raised (min_confidence * 1.1, min_evidence + 1)
5. Future calendar_gap questions require more evidence
6. Next question only if 4+ gaps (vs 2 before)
```

---

## Quality Gates

### Code Quality

- [ ] All functions <50 lines (Constitutional Article II)
- [ ] 100% type coverage (strict typing)
- [ ] No `Dict[Any, Any]` (use Pydantic models)
- [ ] All public APIs documented
- [ ] Lint passes (ruff, mypy)

### Testing

- [ ] 100% unit test coverage
- [ ] All integration tests pass
- [ ] User acceptance >4.0/5.0
- [ ] Annoyance rate <10%
- [ ] Value delivery >80%

### Performance

- [ ] Question formulation <500ms
- [ ] Duplicate check <100ms
- [ ] Learning update <1s
- [ ] Semantic similarity <200ms (FAISS)

### Constitutional Compliance

- [ ] Article I: Complete context (wait for full pattern)
- [ ] Article II: 100% verification (validate questions)
- [ ] Article IV: Continuous learning (all responses learned)
- [ ] Article V: Spec-driven (this plan from spec)

---

## Risk Mitigation

### Risk 1: Question Fatigue (HIGH)

**Mitigation**:
- Hard limits: Max 5 questions/day, 1 question/10min
- Batching: Group similar questions
- Learning: Detect fatigue (declining acceptance)
- Control: User can mute patterns

**Validation**: TASK-015 (UAT) monitors annoyance rate

---

### Risk 2: Poor Timing (MEDIUM)

**Mitigation**:
- Flow detection: Multiple heuristics (silence, topic, phrases)
- Schedule learning: Identify busy times
- LATER option: Always available
- Emergency-only interrupts

**Validation**: TASK-014 (integration tests) verify timing logic

---

### Risk 3: Low Value (MEDIUM)

**Mitigation**:
- Strict thresholds: min_confidence 0.7, min_evidence 3
- Value props: High-value questions articulate benefit
- Learning: Raise thresholds if low acceptance
- User control: Mute low-value patterns

**Validation**: TASK-015 (UAT) measures value delivery >80%

---

### Risk 4: Integration Complexity (MEDIUM)

**Mitigation**:
- Incremental integration: Add to ARCHITECT gradually
- Message bus isolation: New queues, no changes to existing
- Backward compatibility: Question engine optional initially
- Rollback plan: Can disable question formulation

**Validation**: TASK-014 (integration tests) prove pipeline works

---

## Success Metrics

### Primary Metrics (User Experience)

1. **User Satisfaction**: "Would you be sad if Trinity stopped asking?"
   - Target: >80% "Yes"
   - Measure: Quarterly survey (TASK-015)

2. **Acceptance Rate**: % questions answered YES
   - Baseline: Unknown (first run)
   - Target: >50% overall (>60% low-stakes, >40% high-value)
   - Measure: Firestore metrics (TASK-008)

3. **Annoyance Rate**: % questions with negative sentiment
   - Target: <10%
   - Measure: Sentiment analysis (TASK-007)

### Secondary Metrics (System Performance)

1. **Question Quality**: % grammatically correct and contextual
   - Target: 100%
   - Measure: Validation tests (TASK-013)

2. **Timing Accuracy**: % delivered at appropriate time
   - Target: <5% during flow state
   - Measure: User reports (TASK-015)

3. **Learning Effectiveness**: Acceptance rate improvement
   - Target: +10% per month (first 3 months)
   - Measure: Monthly trend analysis

4. **Deduplication Rate**: % duplicates prevented
   - Target: >95%
   - Measure: Suppression logs (TASK-010)

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All tests pass (100% unit, all integration)
- [ ] UAT complete (Alex approval >4.0/5.0)
- [ ] Firestore collections created
- [ ] SQLite tables initialized
- [ ] Message bus queues configured
- [ ] Monitoring dashboards ready
- [ ] Documentation complete
- [ ] Rollback plan documented

### Deployment Steps

1. **Database Setup** (30 min):
   - Create Firestore collections (trinity_questions, trinity_question_responses, trinity_question_metrics)
   - Initialize SQLite tables (question_history)
   - Verify indexes created

2. **Code Deployment** (15 min):
   - Deploy question_engine module
   - Update ARCHITECT integration
   - Add message bus queues
   - Restart Trinity services

3. **Smoke Testing** (1 hour):
   - Trigger test pattern (recurring_topic)
   - Verify question formulated
   - Verify timing decision
   - Verify delivery to human_review_queue
   - Send test response (YES)
   - Verify learning update

4. **Monitoring Setup** (30 min):
   - Configure question count alerts
   - Configure acceptance rate tracking
   - Configure error alerts (formulation failures)
   - Setup daily metrics dashboard

5. **Gradual Rollout** (1 week):
   - Day 1-2: Low-stakes questions only (recurring_topic, small_friction)
   - Day 3-4: Add medium questions
   - Day 5-7: Full rollout (high-value questions)
   - Monitor acceptance rate and adjust thresholds

### Post-Deployment

- **Daily**: Review question count, acceptance rate, errors
- **Weekly**: Analyze learning trends, adjust templates
- **Monthly**: Review user satisfaction, refine strategy

---

## Open Questions & Decisions

### Q1: Question Frequency Cap

**Question**: Max questions per day?

**Options**:
- A) 5 questions/day (conservative)
- B) 10 questions/day (aggressive)
- C) Adaptive (based on acceptance rate)

**Decision**: Start with 5/day (A), adjust to adaptive (C) after 2 weeks based on acceptance rate.

**Owner**: TASK-011 (question fatigue prevention)

---

### Q2: Emergency Override

**Question**: When should questions interrupt flow state?

**Options**:
- A) Never (flow is sacred)
- B) Critical errors only (data loss, deadline miss)
- C) Critical + time-sensitive (meeting in 5 min)

**Decision**: B (critical errors only) - flow state is sacred, emergency = real emergency.

**Owner**: TASK-004 (flow state detection)

---

### Q3: LATER Timing

**Question**: How long to wait before re-offering LATER questions?

**Options**:
- A) Fixed (1 day default)
- B) User-specified (ask user)
- C) Context-based (next relevant moment)

**Decision**: Hybrid A+C - Default 1 day, but re-offer immediately if relevant context appears (e.g., user mentions topic again).

**Owner**: TASK-010 (deduplication)

---

### Q4: User Control UI

**Question**: How should Alex control question preferences?

**Options**:
- A) CLI only (`trinity mute <pattern>`, `trinity quiet-hours`)
- B) Web dashboard (visual controls)
- C) Natural language ("stop asking about X")

**Decision**: A+C - CLI for explicit control, natural language for quick muting. Web dashboard is P2 (future).

**Owner**: TASK-016 (documentation) - document CLI commands

---

## Related Documents

- **Spec**: `specs/proactive_question_engine.md` - Full requirements
- **Architecture**: `specs/trinity_whitepaper_enhancements.md` - Trinity architecture
- **Constitution**: `constitution.md` - Compliance requirements
- **Pattern Detection**: `trinity_protocol/pattern_detector.py` - Input source
- **ARCHITECT**: `trinity_protocol/architect_agent.py` - Integration point

---

## Appendix: Code Examples

### Example 1: Template Selection

```python
# trinity_protocol/question_engine/templates.py

from dataclasses import dataclass
from typing import Dict

@dataclass
class QuestionTemplate:
    template: str
    max_length: int
    requires_value_prop: bool

TEMPLATES: Dict[str, QuestionTemplate] = {
    "recurring_topic": QuestionTemplate(
        template="You mentioned {topic} {count} times. {action}?",
        max_length=100,
        requires_value_prop=False
    ),
    "workflow_bottleneck": QuestionTemplate(
        template="You've mentioned {project} {count} times. I can {outcome} in {timeframe} with {effort}. Want to hear more?",
        max_length=200,
        requires_value_prop=True
    ),
    # ... more templates
}

def select_template(pattern_name: str) -> QuestionTemplate:
    return TEMPLATES.get(pattern_name, TEMPLATES["generic"])
```

### Example 2: Timing Decision

```python
# trinity_protocol/question_engine/timing.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List

@dataclass
class TimingDecision:
    deliver_now: bool
    wait_for_signal: Optional[str]
    batch_with: List[str]
    scheduled_for: Optional[datetime]
    expires_at: Optional[datetime]

def decide_timing(question: FormulatedQuestion, context: UserContext) -> TimingDecision:
    # Flow state - wait
    if context.in_flow_state:
        return TimingDecision(
            deliver_now=False,
            wait_for_signal="conversation_lull",
            batch_with=[],
            scheduled_for=None,
            expires_at=None
        )

    # Time-sensitive - deliver soon
    if question.priority == "time_sensitive":
        return TimingDecision(
            deliver_now=context.schedule_allows_interruption,
            wait_for_signal="next_break" if not context.schedule_allows_interruption else None,
            batch_with=[],
            scheduled_for=None,
            expires_at=question.deadline
        )

    # Can-wait - batch or defer
    pending_similar = find_similar_pending_questions(question)
    if len(pending_similar) >= 2:
        return TimingDecision(
            deliver_now=False,
            wait_for_signal="batch_ready",
            batch_with=[q.id for q in pending_similar],
            scheduled_for=None,
            expires_at=datetime.now() + timedelta(hours=24)
        )

    # Default - wait for natural opportunity
    return TimingDecision(
        deliver_now=False,
        wait_for_signal="admin_time_or_lull",
        batch_with=[],
        scheduled_for=None,
        expires_at=datetime.now() + timedelta(hours=24)
    )
```

### Example 3: Response Learning

```python
# trinity_protocol/question_engine/learning.py

from dataclasses import dataclass
from typing import Literal

AnswerType = Literal["YES", "NO", "LATER"]
SentimentType = Literal["positive", "neutral", "negative"]

@dataclass
class UserResponse:
    question_id: str
    answer: AnswerType
    sentiment: SentimentType
    context: Dict[str, Any]
    responded_at: datetime

async def learn_from_response(response: UserResponse) -> None:
    # Update metrics
    metrics = get_metrics(response.question_type, response.pattern_name)
    metrics.total_asked += 1
    if response.answer == "YES":
        metrics.yes_count += 1
    elif response.answer == "NO":
        metrics.no_count += 1
    else:
        metrics.later_count += 1
    metrics.acceptance_rate = metrics.yes_count / (metrics.yes_count + metrics.no_count)

    # Correlate context
    if response.answer == "YES":
        metrics.success_contexts.append(response.context)
    elif response.answer == "NO" and response.sentiment == "negative":
        metrics.failure_contexts.append(response.context)

    # Adjust thresholds
    if metrics.acceptance_rate > 0.7:
        # Lower threshold (ask sooner)
        pattern_config.min_confidence *= 0.9
        pattern_config.min_evidence = max(2, pattern_config.min_evidence - 1)
    elif metrics.acceptance_rate < 0.3:
        # Raise threshold (be more selective)
        pattern_config.min_confidence *= 1.1
        pattern_config.min_evidence += 1

    # Persist to Firestore
    await agent_context.store_memory(
        key=f"question_response_{response.question_id}",
        value=asdict(response),
        metadata={"type": "question_learning", "pattern": response.pattern_name}
    )
```

---

**Status**: Ready for Implementation
**Next Step**: Begin TASK-001 (Data Models and Schema)
**Timeline**: 2-3 weeks (estimated 116 hours total)
**Success Definition**: Alex says "I'd be sad if Trinity stopped asking these questions"
