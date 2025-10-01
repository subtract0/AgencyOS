# Spec: Proactive Question Engine for Trinity Life Assistant

**ID**: spec-proactive-question-engine
**Status**: Draft
**Created**: 2025-10-01
**Priority**: HIGH
**Type**: User Experience Enhancement
**Trinity Component**: ARCHITECT extension

---

## Executive Summary

Trinity Life Assistant currently detects patterns (WITNESS) and generates strategies (ARCHITECT), but lacks the crucial bridge to user value: asking thoughtful, non-intrusive questions that turn ambient intelligence into actionable assistance. This spec defines a question formulation engine that transforms detected patterns into helpful proposals without annoying the user.

**Core Philosophy**: "NO" is fine and is NOT a failure - it's learning data.

**Key Insight**: The difference between helpful and annoying is:
1. **Question quality** (low-stakes vs high-value)
2. **Timing intelligence** (when to ask vs when to wait)
3. **Learning from responses** (adapt to user preferences)

---

## Goal

Build a proactive question engine that:

1. **Formulates thoughtful questions** from detected patterns
2. **Distinguishes between low-stakes and high-value opportunities**
3. **Times questions intelligently** (no interruptions during flow state)
4. **Learns from responses** (YES/NO patterns improve future questions)
5. **Makes Alex feel helped, not annoyed**

### Success Definition

Alex thinks: "I would be sad if Trinity stopped asking these questions" (not "finally it shut up").

---

## Non-Goals

- ❌ **Spam user with every pattern** - Quality over quantity
- ❌ **Interrupt flow state** - Respect deep work time
- ❌ **Generic suggestions** - Must be specific and contextual
- ❌ **Force engagement** - "NO" is a valid and respected response
- ❌ **Ask without context** - All questions reference specific evidence

---

## Current State Analysis

### ✅ What We Have

1. **Pattern Detection (WITNESS)**
   - Detects recurring topics, projects, frustrations
   - Classifies patterns: FAILURE, OPPORTUNITY, USER_INTENT
   - Confidence scoring (0.7-1.0)
   - Evidence tracking (times_seen, keywords_matched)

2. **Strategy Generation (ARCHITECT)**
   - Analyzes patterns and generates plans
   - Complexity estimation
   - Agent orchestration
   - Spec/plan creation

3. **Message Bus Infrastructure**
   - `improvement_queue`: Detected patterns from WITNESS
   - `human_review_queue`: Ready for review
   - SQLite persistence across restarts
   - Priority-based delivery

4. **Learning Infrastructure**
   - Firestore persistence
   - Pattern success tracking
   - VectorStore for semantic search
   - Cross-session memory

### ❌ What's Missing

1. **Question Formulation Logic**
   - No distinction between low-stakes vs high-value
   - No templates for different question types
   - No value proposition articulation

2. **Timing Intelligence**
   - No awareness of user's schedule/state
   - No batching of similar questions
   - No time-sensitive vs can-wait prioritization

3. **Response Learning**
   - No tracking of YES/NO patterns
   - No adaptation based on acceptance rate
   - No context correlation (what makes questions good/bad)

4. **Conversation Context**
   - No awareness of recent interactions
   - No prevention of duplicate questions
   - No follow-up question chains

---

## Personas

### Primary: Alex (Busy Professional)

**Context**:
- Runs coaching business, writes books, records podcasts
- Values efficiency, hates busywork
- Deep work blocks are sacred
- Open to help but not hand-holding

**Needs**:
- Help with tasks I'm avoiding (book writing, admin)
- Proactive reminders for recurring needs (sushi, calendar prep)
- Project assistance (structured approaches to complex work)

**Pain Points**:
- Notifications that interrupt flow
- Generic suggestions that waste time
- Tools that need more input than they provide value
- "Helpful" systems that create work instead of reducing it

**Quote**: "If you ask me something, it better be worth the 5 seconds to read it."

### Secondary: Trinity System

**Context**:
- Observes Alex's patterns through ambient listening
- Detects recurring topics (sushi 3x, book project 5x)
- Has capability to help but uncertain when/how to offer

**Needs**:
- Clear signal on when questions are welcome
- Learning from acceptance/rejection patterns
- Balance between being helpful and annoying

---

## Functional Requirements

### FR1: Question Type Classification

**Requirement**: System MUST classify potential questions into low-stakes vs high-value categories.

**Low-Stakes Questions** (Casual Offers):
- **Definition**: Simple, transactional assistance with minimal commitment
- **Examples**:
  - "You mentioned sushi 3 times this week. Want me to find nearby options?"
  - "Your calendar has 2 gaps tomorrow. Need travel time blocked?"
  - "That PDF you mentioned - should I summarize it?"
- **User Impact**: 5 seconds to say YES/NO
- **Value**: Small time savings (5-15 minutes)
- **Rejection Cost**: Zero - easy to ignore

**High-Value Questions** (Project Proposals):
- **Definition**: Significant assistance requiring multi-step collaboration
- **Examples**:
  - "You've mentioned your coaching book 5 times. I can help finish it in 2 weeks with 1-3 questions per day. Want to hear the plan?"
  - "Your podcast workflow has 4 bottlenecks. I can create automation to save 2 hours per episode. Interested?"
  - "You said 'I need to think about X' 3 times. Want me to structure a decision framework?"
- **User Impact**: 30 seconds to understand value proposition
- **Value**: Large time savings (hours/days) or outcome improvement
- **Rejection Cost**: Low - but question itself is more substantial

**Classification Logic**:
```python
def classify_question_type(pattern: DetectedPattern) -> QuestionType:
    """
    Classify question based on:
    - Impact scope (single action vs multi-step project)
    - Value magnitude (minutes vs hours saved)
    - Commitment level (one-off vs ongoing collaboration)
    """
    if pattern.scope == "single_action" and pattern.value_minutes < 30:
        return QuestionType.LOW_STAKES
    elif pattern.scope == "project" and pattern.value_hours >= 2:
        return QuestionType.HIGH_VALUE
    else:
        return QuestionType.MEDIUM  # Handle case-by-case
```

**Acceptance Criteria**:
- [ ] Every detected pattern assigned question type
- [ ] Low-stakes questions under 20 words
- [ ] High-value questions include value proposition (time/outcome)
- [ ] Question type influences timing (low-stakes can wait, high-value worth interrupting)

---

### FR2: Question Formulation Templates

**Requirement**: System MUST use evidence-based templates to formulate specific, contextual questions.

**Template Structure**:
```python
@dataclass
class QuestionTemplate:
    """Template for question formulation."""
    question_type: QuestionType
    pattern_name: str
    template: str  # String with {evidence}, {value_prop}, {action} placeholders
    max_length: int  # Character limit
    requires_value_prop: bool  # Must articulate value
```

**Low-Stakes Templates**:

1. **Recurring Topic** (e.g., sushi mentions):
   ```
   "You mentioned {topic} {count} times. {action}?"

   Examples:
   - "You mentioned sushi 3 times. Want me to find nearby options?"
   - "You said 'call mom' twice. Add reminder for tomorrow?"
   ```

2. **Small Friction** (e.g., calendar gaps):
   ```
   "{observation}. {simple_action}?"

   Examples:
   - "Your calendar has 2 gaps tomorrow. Block travel time?"
   - "That PDF is 50 pages. Want a 2-page summary?"
   ```

**High-Value Templates**:

1. **Project Opportunity** (e.g., book writing):
   ```
   "You've mentioned {project} {count} times. I can {outcome} in {timeframe} with {effort}. Want to hear more?"

   Examples:
   - "You've mentioned your coaching book 5 times. I can help finish it in 2 weeks with 1-3 questions per day. Want to hear the plan?"
   - "Your podcast workflow has 4 bottlenecks. I can create automation to save 2 hours per episode. Interested in the approach?"
   ```

2. **Decision Support** (e.g., recurring uncertainty):
   ```
   "You said '{phrase}' {count} times. {value_prop}. {action}?"

   Examples:
   - "You said 'I need to think about X' 3 times. I can structure a decision framework with pros/cons. Useful?"
   - "You've mentioned scaling dilemma 4 times. Want me to create a weighted scorecard for options?"
   ```

**Template Selection Logic**:
```python
def select_template(pattern: DetectedPattern) -> QuestionTemplate:
    """
    Select template based on:
    - Pattern type (USER_INTENT, OPPORTUNITY, FAILURE)
    - Pattern name (recurring_topic, feature_request, workflow_bottleneck)
    - Evidence strength (times_seen, confidence)
    """
    if pattern.pattern_type == "user_intent":
        if pattern.pattern_name == "recurring_topic":
            if pattern.times_seen >= 3:
                return RECURRING_TOPIC_TEMPLATE
        elif pattern.pattern_name == "workflow_bottleneck":
            return PROJECT_OPPORTUNITY_TEMPLATE
    # ... additional logic
```

**Acceptance Criteria**:
- [ ] 10+ templates covering common patterns
- [ ] All templates reference specific evidence (count, keywords)
- [ ] High-value templates include clear value proposition
- [ ] Questions under character limit (low-stakes: 100 chars, high-value: 200 chars)
- [ ] Templates produce grammatically correct questions

---

### FR3: Timing Intelligence

**Requirement**: System MUST intelligently time questions to respect user's context and avoid interruptions.

**Timing Dimensions**:

1. **Flow State Detection**:
   - **No interruptions** during deep work
   - Indicators: Long silence, focused conversation, "don't bother me" phrases
   - Wait for natural breaks: conversation lulls, task transitions

2. **Schedule Awareness**:
   - Learn Alex's patterns (busy mornings, free afternoons)
   - Avoid questions during meetings (calendar integration)
   - Prefer questions during admin time or breaks

3. **Question Batching**:
   - Group similar questions together
   - One notification with 3 questions > 3 separate notifications
   - Max 5 questions per batch

4. **Priority-Based Delivery**:
   - **Time-sensitive** (deliver soon): Event-based (meeting prep, deadlines)
   - **Can-wait** (deliver when convenient): Optimization suggestions, project ideas
   - **Emergency** (interrupt if needed): Critical errors, urgent opportunities

**Timing Algorithm**:
```python
@dataclass
class TimingDecision:
    """Timing decision for question delivery."""
    deliver_now: bool
    wait_for_signal: Optional[str]  # "conversation_lull", "admin_time", "next_day"
    batch_with: List[str]  # Other question IDs to batch
    expires_at: Optional[datetime]  # Time-sensitive deadline

def decide_timing(question: FormulatedQuestion, context: UserContext) -> TimingDecision:
    """
    Decide when to deliver question based on:
    - User state (flow/available)
    - Question priority (time-sensitive/can-wait)
    - Batch opportunities (similar pending questions)
    """
    # Flow state - wait for break
    if context.in_flow_state:
        return TimingDecision(
            deliver_now=False,
            wait_for_signal="conversation_lull"
        )

    # Time-sensitive - deliver soon
    if question.priority == "time_sensitive":
        if context.schedule_allows_interruption:
            return TimingDecision(deliver_now=True)
        else:
            return TimingDecision(
                deliver_now=False,
                wait_for_signal="next_break",
                expires_at=question.deadline
            )

    # Can-wait - batch with similar
    pending_similar = find_similar_pending_questions(question)
    if len(pending_similar) >= 2:
        return TimingDecision(
            deliver_now=False,
            wait_for_signal="batch_ready",
            batch_with=[q.id for q in pending_similar]
        )

    # Default - wait for natural opportunity
    return TimingDecision(
        deliver_now=False,
        wait_for_signal="admin_time_or_lull"
    )
```

**Acceptance Criteria**:
- [ ] No questions during detected flow state
- [ ] Questions batched when 2+ similar pending
- [ ] Time-sensitive questions delivered within deadline window
- [ ] Can-wait questions held for natural breaks (max 24h)
- [ ] Emergency questions (critical errors) interrupt appropriately

---

### FR4: Response Learning System

**Requirement**: System MUST learn from user responses (YES/NO/LATER) to improve future question quality and timing.

**Learning Dimensions**:

1. **Acceptance Rate by Question Type**:
   ```python
   @dataclass
   class QuestionMetrics:
       question_type: QuestionType
       pattern_name: str
       total_asked: int
       yes_count: int
       no_count: int
       later_count: int
       acceptance_rate: float  # yes / (yes + no)

   def update_metrics(response: UserResponse) -> None:
       """Track response and update acceptance rate."""
       metrics = get_metrics(response.question_type, response.pattern_name)
       metrics.total_asked += 1
       if response.answer == "YES":
           metrics.yes_count += 1
       elif response.answer == "NO":
           metrics.no_count += 1
       elif response.answer == "LATER":
           metrics.later_count += 1
       metrics.acceptance_rate = metrics.yes_count / (metrics.yes_count + metrics.no_count)
   ```

2. **Context Correlation**:
   - What context leads to YES? (time of day, user state, recent activity)
   - What context leads to NO? (busy times, certain topics, question fatigue)
   - What makes LATER different? (timing issue vs content issue)

3. **Threshold Adjustment**:
   ```python
   def adjust_thresholds(metrics: QuestionMetrics) -> None:
       """
       Adjust confidence/evidence thresholds based on acceptance rate.

       Logic:
       - High acceptance (>70%): Lower threshold (ask sooner)
       - Low acceptance (<30%): Raise threshold (be more selective)
       - Medium (30-70%): Keep threshold, improve timing
       """
       if metrics.acceptance_rate > 0.7:
           # User values these questions - ask sooner
           pattern_config = get_pattern_config(metrics.pattern_name)
           pattern_config.min_confidence *= 0.9  # Lower threshold
           pattern_config.min_evidence = max(2, pattern_config.min_evidence - 1)

       elif metrics.acceptance_rate < 0.3:
           # User doesn't value these - be more selective
           pattern_config = get_pattern_config(metrics.pattern_name)
           pattern_config.min_confidence *= 1.1  # Raise threshold
           pattern_config.min_evidence += 1
   ```

4. **Pattern Quality Signals**:
   - **Strong YES**: User accepts and acts immediately → This pattern/timing is valuable
   - **Soft NO**: User declines politely → Not valuable but not annoying (neutral learning)
   - **Hard NO**: User frustrated/dismissive → This pattern/timing is wrong (strong negative)
   - **LATER**: Timing issue, not content → Re-offer at better time

**Response Collection**:
```python
@dataclass
class UserResponse:
    """User response to question."""
    question_id: str
    question_type: QuestionType
    pattern_name: str
    answer: Literal["YES", "NO", "LATER"]
    sentiment: Literal["positive", "neutral", "negative"]  # Detected from tone
    context: Dict[str, Any]  # Time of day, recent activity, etc.
    timestamp: datetime

def collect_response(question_id: str, user_message: str) -> UserResponse:
    """
    Collect and classify user response.

    YES detection: "yes", "sure", "go ahead", "sounds good", "do it"
    NO detection: "no", "not now", "nah", "skip", "not interested"
    LATER detection: "later", "remind me", "ask me tomorrow", "not right now"

    Sentiment: Analyze tone for frustration vs appreciation
    """
    answer = classify_answer(user_message)
    sentiment = analyze_sentiment(user_message)
    context = capture_current_context()

    return UserResponse(
        question_id=question_id,
        question_type=get_question_type(question_id),
        pattern_name=get_pattern_name(question_id),
        answer=answer,
        sentiment=sentiment,
        context=context,
        timestamp=datetime.now()
    )
```

**Learning Application**:
```python
async def learn_from_response(response: UserResponse) -> None:
    """
    Update system based on user response.

    Steps:
    1. Update metrics (acceptance rate)
    2. Correlate context (what led to YES/NO)
    3. Adjust thresholds (confidence, evidence, timing)
    4. Store in Firestore for cross-session learning
    """
    # Update metrics
    update_metrics(response)

    # Correlate context
    if response.answer == "YES":
        store_success_context(response.pattern_name, response.context)
    elif response.answer == "NO" and response.sentiment == "negative":
        store_failure_context(response.pattern_name, response.context)

    # Adjust thresholds
    metrics = get_metrics(response.question_type, response.pattern_name)
    adjust_thresholds(metrics)

    # Persist to Firestore (Article IV)
    await agent_context.store_memory(
        key=f"question_response_{response.question_id}",
        value=asdict(response),
        metadata={"type": "question_learning", "pattern": response.pattern_name}
    )
```

**Acceptance Criteria**:
- [ ] All responses (YES/NO/LATER) tracked in Firestore
- [ ] Acceptance rate calculated per question type and pattern
- [ ] Thresholds adjust based on acceptance rate (>70% lower, <30% raise)
- [ ] Context correlation identifies success/failure patterns
- [ ] Learning applied to future questions (measurable improvement)

---

### FR5: Question Deduplication and Conversation Continuity

**Requirement**: System MUST prevent duplicate questions and maintain conversation context across interactions.

**Deduplication Logic**:
```python
@dataclass
class QuestionHistory:
    """History of questions asked."""
    question_id: str
    pattern_id: str
    question_text: str
    asked_at: datetime
    response: Optional[UserResponse]
    expires_at: datetime  # When it's OK to ask again

def check_duplicate(new_question: FormulatedQuestion) -> Optional[QuestionHistory]:
    """
    Check if similar question recently asked.

    Similarity criteria:
    - Same pattern_id (exact duplicate)
    - Same topic + similar action (semantic duplicate)
    - Asked within dedup_window (default 7 days)
    """
    recent_questions = get_recent_questions(days=7)

    for hist in recent_questions:
        # Exact duplicate
        if hist.pattern_id == new_question.pattern_id:
            return hist

        # Semantic duplicate
        if semantic_similarity(hist.question_text, new_question.text) > 0.85:
            return hist

    return None  # Not a duplicate

async def handle_duplicate(duplicate: QuestionHistory, new_question: FormulatedQuestion) -> None:
    """
    Handle duplicate question detection.

    Actions:
    - If previous response was NO: Don't ask again (user already declined)
    - If previous response was LATER: Check if enough time passed
    - If previous response was YES: Check if new evidence justifies re-asking
    """
    if duplicate.response and duplicate.response.answer == "NO":
        # User already said no - don't ask again unless significant new evidence
        if new_question.confidence > duplicate.question.confidence + 0.2:
            # Significantly stronger evidence - OK to re-ask
            pass
        else:
            # Suppress duplicate
            return

    elif duplicate.response and duplicate.response.answer == "LATER":
        # User wanted to be reminded - check if enough time passed
        if datetime.now() < duplicate.expires_at:
            # Too soon - wait longer
            return
        else:
            # OK to re-ask now
            pass
```

**Conversation Continuity**:
```python
@dataclass
class ConversationContext:
    """Current conversation context."""
    recent_messages: List[str]  # Last 10 messages
    active_topic: Optional[str]  # Current discussion topic
    pending_questions: List[FormulatedQuestion]  # Questions waiting for timing
    last_question_at: Optional[datetime]  # When we last asked something

def maintain_continuity(question: FormulatedQuestion, context: ConversationContext) -> FormulatedQuestion:
    """
    Adjust question for conversation continuity.

    - If related to active_topic: Reference it ("Speaking of X...")
    - If unrelated to active_topic: Add transition ("By the way...")
    - If multiple questions pending: Present as list ("I have 3 things...")
    """
    if question.topic == context.active_topic:
        question.text = f"Speaking of {context.active_topic}, {question.text}"
    elif context.active_topic:
        question.text = f"By the way, {question.text}"

    # Prevent question fatigue
    if context.last_question_at and (datetime.now() - context.last_question_at) < timedelta(minutes=10):
        # Asked something recently - wait longer
        question.timing.wait_for_signal = "conversation_lull"

    return question
```

**Acceptance Criteria**:
- [ ] Duplicate questions within 7 days prevented (unless significant new evidence)
- [ ] NO responses respected (don't re-ask unless major evidence change)
- [ ] LATER responses re-offered after expiry time
- [ ] Questions reference active conversation topic when relevant
- [ ] Question fatigue prevented (max 1 question per 10 minutes)

---

## Non-Functional Requirements

### NFR1: Performance

- Question formulation: <500ms from pattern detection to formulated question
- Duplicate check: <100ms against last 30 days of questions
- Learning update: <1s to process response and update Firestore
- Semantic similarity: <200ms per comparison (FAISS-accelerated)

### NFR2: Reliability

- All questions persisted to Firestore (survive restarts)
- Response learning survives process crashes
- Graceful degradation if Firestore unavailable (local SQLite fallback)
- No questions lost due to timing delays

### NFR3: Privacy

- All question/response data encrypted at rest (Firestore)
- User can delete question history
- No question data shared across users
- Ambient listening data only used for question formulation (not stored raw)

### NFR4: Constitutional Compliance

- **Article I (Complete Context)**: Wait for full pattern evidence before formulating question
- **Article II (100% Verification)**: Validate question grammar/format before delivery
- **Article IV (Continuous Learning)**: All responses stored and learned from
- **Article V (Spec-Driven)**: This spec drives implementation

---

## Architecture Integration

### Trinity Protocol Integration

```
WITNESS (Pattern Detection)
    ↓ (improvement_queue)
ARCHITECT (Strategy Generation)
    ↓ (NEW: question_formulation_queue)
[QUESTION ENGINE] (This component)
    ├→ Formulate question from pattern
    ├→ Classify type (low-stakes vs high-value)
    ├→ Decide timing (now vs wait)
    ├→ Check deduplication
    ↓ (human_review_queue)
USER (Response)
    ↓ (response_queue)
[QUESTION ENGINE] (Learning)
    ├→ Classify response (YES/NO/LATER)
    ├→ Update metrics
    ├→ Adjust thresholds
    ├→ Store in Firestore
```

### Data Flow

1. **Input**: `DetectedPattern` from WITNESS via `improvement_queue`
2. **Processing**:
   - ARCHITECT analyzes pattern and generates strategy
   - **Question Engine** formulates question from strategy
   - Timing intelligence decides delivery schedule
   - Deduplication check prevents repeats
3. **Output**: `FormulatedQuestion` to `human_review_queue`
4. **Feedback**: `UserResponse` from user triggers learning update

### Storage Schema

**Firestore Collections**:

1. **`trinity_questions`** (formulated questions):
   ```typescript
   {
     question_id: string,
     pattern_id: string,
     question_type: "low_stakes" | "high_value",
     pattern_name: string,
     question_text: string,
     value_proposition: string | null,
     confidence: number,
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

2. **`trinity_question_responses`** (user responses):
   ```typescript
   {
     response_id: string,
     question_id: string,
     answer: "YES" | "NO" | "LATER",
     sentiment: "positive" | "neutral" | "negative",
     context: {
       time_of_day: string,
       day_of_week: string,
       recent_activity: string,
       active_topic: string | null
     },
     responded_at: timestamp
   }
   ```

3. **`trinity_question_metrics`** (learning metrics):
   ```typescript
   {
     metric_id: string,
     question_type: string,
     pattern_name: string,
     total_asked: number,
     yes_count: number,
     no_count: number,
     later_count: number,
     acceptance_rate: number,
     success_contexts: any[],  // Contexts that led to YES
     failure_contexts: any[],  // Contexts that led to NO
     last_updated: timestamp
   }
   ```

**SQLite Tables** (local persistence):

```sql
CREATE TABLE question_history (
    id INTEGER PRIMARY KEY,
    question_id TEXT UNIQUE,
    pattern_id TEXT,
    question_text TEXT,
    question_type TEXT,
    asked_at TEXT,
    response_answer TEXT,
    response_sentiment TEXT,
    expires_at TEXT
);

CREATE INDEX idx_pattern_id ON question_history(pattern_id);
CREATE INDEX idx_asked_at ON question_history(asked_at);
```

---

## Success Metrics

### Primary Metrics (User Experience)

1. **User Satisfaction**: "Would you be sad if Trinity stopped asking questions?"
   - Target: >80% "Yes, I'd be sad" (measured via survey)
   - Measure: Quarterly user feedback

2. **Acceptance Rate**: % of questions answered YES
   - Baseline: Unknown (first implementation)
   - Target: >50% overall (>60% low-stakes, >40% high-value)
   - Measure: YES / (YES + NO) from Firestore

3. **Annoyance Rate**: % of questions with negative sentiment response
   - Target: <10% negative responses
   - Measure: Sentiment analysis of NO responses

### Secondary Metrics (System Performance)

1. **Question Quality**: % questions that are grammatically correct and contextual
   - Target: 100% (automated validation)
   - Measure: Grammar check + template verification

2. **Timing Accuracy**: % questions delivered at appropriate time
   - Target: <5% delivered during flow state (user feedback)
   - Measure: User reports "bad timing" tag

3. **Learning Effectiveness**: Improvement in acceptance rate over time
   - Target: +10% acceptance rate per month (first 3 months)
   - Measure: Monthly acceptance rate trend

4. **Deduplication Effectiveness**: % duplicate questions prevented
   - Target: >95% duplicates prevented
   - Measure: (duplicates_prevented / total_patterns) from logs

---

## Risk Assessment

### Risk 1: Question Fatigue (HIGH)

**Description**: User gets annoyed by too many questions, even if individually good.

**Mitigation**:
- Hard limit: Max 5 questions per day
- Batch similar questions together
- Learn from "question fatigue" signals (declining acceptance rate)
- User control: "Quiet hours" setting

**Success Criteria**: Annoyance rate <10%

### Risk 2: Poor Timing (MEDIUM)

**Description**: Questions interrupt flow state or arrive at bad times.

**Mitigation**:
- Flow state detection (long silence, focused conversation)
- Schedule awareness (learn busy times)
- "LATER" option always available
- Emergency questions only for true emergencies

**Success Criteria**: <5% "bad timing" feedback

### Risk 3: Low Value Questions (MEDIUM)

**Description**: Questions don't provide enough value to justify interruption.

**Mitigation**:
- Strict thresholds (min evidence, confidence)
- High-value questions must articulate value proposition
- Learn from NO responses and raise thresholds
- User can mute specific patterns

**Success Criteria**: Acceptance rate >50%

### Risk 4: Privacy Concerns (LOW)

**Description**: User uncomfortable with ambient listening data usage.

**Mitigation**:
- Transparent about data usage (only for questions)
- User can delete question history
- No raw ambient data stored (only patterns)
- Full control over system (can disable)

**Success Criteria**: Zero privacy complaints

---

## Open Questions

1. **Question Frequency Cap**: Max questions per day?
   - **Proposal**: Start with 5/day, adjust based on acceptance rate
   - **Decision needed**: Week 1 of implementation

2. **Emergency Override**: When should questions interrupt flow state?
   - **Proposal**: Only for critical errors with user impact (data loss, deadline miss)
   - **Decision needed**: During architecture design

3. **LATER Timing**: How long to wait before re-offering LATER questions?
   - **Proposal**: User-specified (default 1 day) or context-based (next relevant moment)
   - **Decision needed**: Week 2 of implementation

4. **User Control UI**: How should Alex control question preferences?
   - **Proposal**: Simple CLI: `trinity mute <pattern>`, `trinity quiet-hours <start> <end>`
   - **Decision needed**: During UI design phase

5. **Multi-User Support**: How to handle question preferences across users?
   - **Proposal**: Per-user metrics/thresholds (if multi-user later)
   - **Decision needed**: Not blocking (future enhancement)

---

## Acceptance Criteria

### Must Have (P0)

- [ ] Question formulation works for 5+ pattern types (recurring_topic, workflow_bottleneck, etc.)
- [ ] Low-stakes vs high-value classification functional
- [ ] Timing intelligence prevents questions during flow state
- [ ] Deduplication prevents repeat questions within 7 days
- [ ] YES/NO/LATER responses tracked in Firestore
- [ ] Acceptance rate calculated and displayed per pattern
- [ ] Thresholds adjust based on acceptance rate (>70% lower, <30% raise)

### Should Have (P1)

- [ ] Question batching groups similar questions
- [ ] Schedule awareness learns busy times
- [ ] Sentiment analysis detects frustration in NO responses
- [ ] "LATER" questions re-offered after expiry
- [ ] User control commands (mute pattern, quiet hours)

### Could Have (P2)

- [ ] Question templates for 10+ pattern types
- [ ] Context correlation identifies success patterns
- [ ] Conversation continuity with active topic reference
- [ ] Multi-language support for questions
- [ ] Voice delivery option (TTS)

---

## Test Strategy

### Unit Tests

1. **Question Formulation**:
   - Template selection for each pattern type
   - Evidence substitution (count, keywords, timeframe)
   - Character limits enforced (low-stakes: 100, high-value: 200)
   - Grammar validation

2. **Timing Intelligence**:
   - Flow state detection logic
   - Batch opportunity detection
   - Priority-based delivery (time-sensitive vs can-wait)
   - Expiry handling

3. **Learning System**:
   - Response classification (YES/NO/LATER)
   - Metrics update logic
   - Threshold adjustment (acceptance rate -> confidence change)
   - Context correlation

4. **Deduplication**:
   - Exact duplicate detection (same pattern_id)
   - Semantic duplicate detection (similar text)
   - NO response respect (don't re-ask)
   - LATER response re-offer

### Integration Tests

1. **End-to-End Flow**:
   - Pattern detected → Question formulated → User response → Learning update
   - Firestore persistence verified
   - Metrics updated correctly

2. **Trinity Integration**:
   - WITNESS → ARCHITECT → Question Engine pipeline
   - Question delivery to `human_review_queue`
   - Response feedback loop

3. **Learning Effectiveness**:
   - Acceptance rate improves over time (simulated responses)
   - Thresholds adjust correctly (high acceptance lowers, low raises)
   - Context correlation identifies patterns

### User Acceptance Tests

1. **User Satisfaction**:
   - Alex reviews 20 formulated questions
   - Rates quality (1-5 scale)
   - Target: Average >4.0

2. **Annoyance Test**:
   - Alex uses system for 1 week
   - Reports annoyance incidents
   - Target: <2 annoyance incidents per week

3. **Value Test**:
   - Alex accepts 10 questions
   - Measures time saved or value gained
   - Target: >80% of accepted questions provide measurable value

---

## Implementation Dependencies

### Required Components

1. **Trinity Protocol** (✅ Already exists):
   - WITNESS agent for pattern detection
   - ARCHITECT agent for strategy generation
   - Message bus (`improvement_queue`, `human_review_queue`)
   - Persistent store (Firestore, SQLite)

2. **Agent Context** (✅ Already exists):
   - `AgentContext` for memory access
   - `store_memory()`, `search_memories()` for Firestore
   - VectorStore for semantic search

3. **Pattern Detection** (✅ Already exists):
   - `PatternDetector` with confidence scoring
   - Pattern types: USER_INTENT, OPPORTUNITY, FAILURE
   - Evidence tracking (times_seen, keywords_matched)

### New Components (To Build)

1. **Question Formulation Engine** (Core):
   - Template system
   - Evidence extraction
   - Value proposition articulation

2. **Timing Intelligence Module**:
   - Flow state detection
   - Schedule learning
   - Batch coordination

3. **Learning System**:
   - Response classification
   - Metrics tracking
   - Threshold adjustment

4. **Deduplication Service**:
   - Question history
   - Semantic similarity (FAISS)
   - Suppression logic

---

## Related Documents

- `specs/trinity_whitepaper_enhancements.md` - Trinity architecture enhancements
- `trinity_protocol/witness_agent.py` - Pattern detection source
- `trinity_protocol/architect_agent.py` - Strategy generation (integration point)
- `trinity_protocol/pattern_detector.py` - Pattern classification logic
- `shared/agent_context.py` - Memory and Firestore access
- `constitution.md` - Constitutional compliance requirements

---

## Glossary

- **Low-Stakes Question**: Simple, transactional assistance (<30 min value, easy to decline)
- **High-Value Question**: Significant multi-step assistance (>2 hour value, worth interrupting)
- **Flow State**: Deep work mode where user should not be interrupted
- **Question Fatigue**: Decline in acceptance rate due to too many questions
- **Acceptance Rate**: Percentage of questions answered YES (success metric)
- **Deduplication**: Preventing repeat questions about same pattern
- **Timing Intelligence**: System's ability to choose appropriate moment for questions
- **Learning System**: Adaptation of thresholds based on user response patterns
- **Value Proposition**: Clear articulation of time/outcome benefit in question

---

**Status**: Draft - Ready for Planning
**Next Step**: Create implementation plan (`plans/plan-question-engine.md`)
**Estimated Effort**: 2-3 weeks (based on scope and integration complexity)
