# Trinity Protocol: Preference Learning System

**Status**: ✅ Complete (All tests passing)

## Overview

The Preference Learning System helps Trinity understand Alex's preferences for proactive assistance by analyzing historical response patterns. This system learns what questions Alex values, when he prefers to be asked, and what topics matter most to him.

**Philosophy**: Optimize for Alex's subjective helpfulness, not arbitrary metrics.

## Architecture

### Core Components

```
trinity_protocol/
├── models/preferences.py          # Pydantic models for preference data
├── alex_preference_learner.py     # Learning algorithm and analysis
├── preference_store.py            # Firestore-backed persistence
├── demo_preference_learning.py    # Working demonstration
└── tests/
    └── test_preference_learning.py  # Comprehensive test suite (28 tests)
```

### Data Flow

```
ARCHITECT asks question → Alex responds (YES/NO/LATER/IGNORED)
                ↓
ResponseRecord created & stored
                ↓
After N responses → AlexPreferenceLearner.analyze_responses()
                ↓
Learned preferences → PreferenceStore
                ↓
Recommendations → ARCHITECT (optimize future questions)
```

## Models

### ResponseRecord
**Purpose**: Atomic unit of learning - single question/response pair

**Key Fields**:
- `question_text`: The question asked
- `question_type`: HIGH_VALUE | LOW_STAKES | TASK_SUGGESTION | CLARIFICATION | PROACTIVE_OFFER
- `topic_category`: BOOK_PROJECT | COACHING | CLIENT_WORK | FOOD | etc.
- `response_type`: YES | NO | LATER | IGNORED
- `response_time_seconds`: How long Alex took to respond
- `context_before`: What was happening before the question
- `day_of_week`: When asked
- `time_of_day`: Time period classification

### AlexPreferences
**Purpose**: Master preference model aggregating all learned insights

**Dimensions**:
1. **Question Type Preferences**: Which question types Alex accepts most
2. **Timing Preferences**: Best times of day to ask
3. **Day of Week Preferences**: Day-of-week patterns
4. **Topic Preferences**: Which topics Alex values
5. **Contextual Patterns**: What context leads to YES responses
6. **Recommendations**: Actionable insights for ARCHITECT

### PreferenceRecommendation
**Purpose**: Actionable suggestions for improving ARCHITECT's behavior

**Types**:
- `increase_frequency`: Ask more of this type
- `decrease_frequency`: Ask less of this type
- `change_timing`: Shift to better time windows
- `change_approach`: Modify how questions are framed
- `new_opportunity`: New pattern discovered

**Priority Levels**: CRITICAL | HIGH | MEDIUM | LOW

## Learning Algorithm

### AlexPreferenceLearner

**Core Method**: `analyze_responses(responses) → AlexPreferences`

**Analysis Pipeline**:

1. **Question Type Analysis**
   - Group responses by question type
   - Calculate acceptance rates
   - Track response times
   - Compute confidence scores

2. **Timing Analysis**
   - Classify questions by time of day (6 periods)
   - Calculate acceptance rates per period
   - Identify best times to ask

3. **Day of Week Analysis**
   - Track Monday vs Friday behavior patterns
   - Calculate daily acceptance rates

4. **Topic Analysis**
   - Group by topic category
   - Detect trends (increasing/stable/decreasing)
   - Track acceptance evolution

5. **Context Pattern Detection**
   - Extract keyword patterns from `context_before`
   - Identify high-correlation contexts
   - Generate contextual rules

6. **Recommendation Generation**
   - Find high-acceptance patterns (>70%) → recommend increase
   - Find low-acceptance patterns (<30%) → recommend decrease
   - Identify best timing windows
   - Surface emerging trends

### Confidence Scoring

```python
def calculate_confidence(sample_size, min_samples=10) -> float:
    """
    Confidence approaches 1.0 as sample size increases beyond min_samples.

    - 0 samples: 0.0 confidence
    - <min_samples: Linear 0.0→0.5
    - min_samples→2x: Linear 0.5→1.0
    - >=2x min_samples: 1.0 confidence
    """
```

**Thresholds**:
- Min sample size: 10 responses (configurable)
- Min confidence for recommendations: 0.6 (60%)
- Trend detection window: 7 days

## Storage (PreferenceStore)

### Backends

**In-Memory** (default for dev/testing):
```python
store = PreferenceStore(use_firestore=False)
```

**Firestore** (production):
```python
store = PreferenceStore(use_firestore=True)
# Uses default Firebase credentials
```

### Collections

**alex_responses**:
- Individual response records
- Queryable by question_type, topic, date range
- Ordered by timestamp

**alex_preferences**:
- Current preference snapshot (document: "current")
- Updated after learning sessions

**alex_preference_history**:
- Historical preference snapshots
- Enables trend analysis over time
- Tracks preference evolution

### API

```python
# Store response
store.store_response(response_record)

# Query responses
recent = store.get_recent_responses(limit=100)
coaching_responses = store.query_responses(
    topic_category="coaching",
    start_date=datetime.now() - timedelta(days=7)
)

# Store preferences
snapshot_id = store.store_preferences(preferences, snapshot_reason="weekly_update")

# Retrieve preferences
current = store.get_current_preferences()
history = store.get_preference_history(limit=10)

# Stats
stats = store.get_stats()
```

## Usage Examples

### Basic Learning Workflow

```python
from trinity_protocol.alex_preference_learner import AlexPreferenceLearner, create_response_record
from trinity_protocol.preference_store import PreferenceStore
from trinity_protocol.models.preferences import QuestionType, TopicCategory, ResponseType
from datetime import datetime

# 1. Create store
store = PreferenceStore(use_firestore=False)

# 2. Record responses
response = create_response_record(
    question_id="q_123",
    question_text="Want to work on coaching framework?",
    question_type=QuestionType.HIGH_VALUE,
    topic_category=TopicCategory.COACHING,
    response_type=ResponseType.YES,
    timestamp=datetime.now(),
    response_time_seconds=5.2,
    context_before="Alex reviewing coaching notes"
)
store.store_response(response)

# 3. Learn preferences
learner = AlexPreferenceLearner(
    min_confidence_threshold=0.6,
    min_sample_size=10
)
responses = store.get_recent_responses(limit=100)
preferences = learner.analyze_responses(responses)

# 4. Store learned preferences
store.store_preferences(preferences, snapshot_reason="hourly_update")

# 5. Use recommendations
for rec in preferences.recommendations:
    if rec.priority in ["high", "critical"]:
        print(f"[{rec.priority}] {rec.title}")
        print(f"  {rec.description}")
        print(f"  Evidence: {', '.join(rec.evidence)}")
```

### Integration with ARCHITECT

```python
# In ARCHITECT's question selection logic:

# 1. Load current preferences
preferences = store.get_current_preferences()

# 2. Check if question should be asked
def should_ask_question(question_type, topic_category, time_of_day):
    # Get preferences for this question type
    q_pref = preferences.question_preferences.get(question_type.value)
    if q_pref and q_pref.confidence >= 0.6:
        # If low acceptance, skip
        if q_pref.acceptance_rate < 0.3:
            return False

    # Check timing
    time_pref = preferences.timing_preferences.get(time_of_day.value)
    if time_pref and time_pref.confidence >= 0.6:
        # Prefer high-acceptance time windows
        if time_pref.acceptance_rate < 0.5:
            return False  # Bad timing

    # Check topic
    topic_pref = preferences.topic_preferences.get(topic_category.value)
    if topic_pref and topic_pref.confidence >= 0.6:
        # If low acceptance and high confidence, skip
        if topic_pref.acceptance_rate < 0.3:
            return False

    return True  # Looks good to ask

# 3. Apply recommendations
for rec in preferences.recommendations:
    if rec.recommendation_type == "increase_frequency":
        # Increase question budget for this type
        pass
    elif rec.recommendation_type == "change_timing":
        # Shift questions to recommended time window
        pass
```

## Testing

### Run Tests

```bash
# All tests (28 passing)
uv run pytest tests/trinity_protocol/test_preference_learning.py -v

# Specific test class
uv run pytest tests/trinity_protocol/test_preference_learning.py::TestAlexPreferenceLearner -v

# Single test
uv run pytest tests/trinity_protocol/test_preference_learning.py::TestPreferenceModels::test_response_record_creation -v
```

### Test Coverage

**Model Tests** (6 tests):
- ✅ ResponseRecord creation
- ✅ QuestionPreference rate calculations
- ✅ TopicPreference with trends
- ✅ ContextualPattern model
- ✅ PreferenceRecommendation

**Utility Tests** (4 tests):
- ✅ Time of day classification
- ✅ Day of week classification
- ✅ Confidence calculation
- ✅ create_response_record helper

**Learner Tests** (8 tests):
- ✅ Analyze empty responses
- ✅ Question type analysis
- ✅ Timing analysis
- ✅ Topic analysis
- ✅ Day of week analysis
- ✅ Trend detection (increasing/stable/decreasing)
- ✅ Recommendation generation
- ✅ Contextual pattern detection

**Store Tests** (8 tests):
- ✅ Store/retrieve responses
- ✅ Store/retrieve preferences
- ✅ Preference history
- ✅ Query by question type
- ✅ Query by date range
- ✅ Storage statistics
- ✅ Cache management
- ✅ Delete operations

**Integration Tests** (2 tests):
- ✅ End-to-end workflow
- ✅ Preference evolution over time

## Demo

### Run Demo

```bash
python -m trinity_protocol.demo_preference_learning
```

### Demo Output

The demo simulates 2 weeks of Trinity asking Alex questions across different categories:

1. **Coaching questions** (85% acceptance)
2. **Book project questions** (80% acceptance)
3. **Client work questions** (60% acceptance)
4. **Food suggestions** (15% acceptance)
5. **System improvements** (75% acceptance, increasing trend)
6. **Entertainment** (20% acceptance)

**Sample Output**:
```
📊 QUESTION TYPE PREFERENCES:

  PROACTIVE OFFER:
    Acceptance Rate: 85.7%
    Total Asked: 7
    YES: 6, NO: 1, LATER: 0, IGNORED: 0
    Confidence: 70.0%

  HIGH VALUE:
    Acceptance Rate: 83.7%
    Total Asked: 49
    YES: 41, NO: 8, LATER: 0, IGNORED: 0
    Confidence: 100.0%

📅 TIMING PREFERENCES:

  EARLY MORNING:
    Acceptance Rate: 85.7%
    Questions Asked: 7
    Confidence: 70.0%

✅ WHAT ALEX VALUES (ask more):
  • Coaching: 86% acceptance
  • Book Project: 86% acceptance
  • System Improvement: 86% acceptance

❌ WHAT ALEX DOESN'T VALUE (ask less):
  • Food: 14% acceptance

📈 EMERGING TRENDS:
  • Book Project: Increasing interest (86% recent)

⏰ BEST TIMES TO ASK:
  • Early Morning: 86% acceptance
  • Late Night: 74% acceptance
```

## Key Insights

### What the System Learns

1. **Question Value Hierarchy**
   - HIGH_VALUE questions (coaching, book, system) → 80-85% acceptance
   - TASK_SUGGESTION → 60% acceptance
   - LOW_STAKES (food, entertainment) → 15-20% acceptance

2. **Optimal Timing**
   - Best: Early morning (5am-8am)
   - Good: Late night work sessions
   - Avoid: During focus time, late evening

3. **Topic Preferences**
   - High value: Coaching, Book Project, System Improvement
   - Medium value: Client work
   - Low value: Food, Entertainment (unless explicitly asked)

4. **Context Patterns**
   - Questions after "coaching" context → 86% acceptance
   - Questions after "book, project" keywords → 86% acceptance
   - Questions during "lunchtime" context → 14% acceptance (food)

5. **Trends Over Time**
   - Book project interest: Increasing
   - System improvement: Stable high interest
   - Food suggestions: Consistently low

### Constitutional Compliance

✅ **Article IV: Continuous Learning**
- System learns from every interaction
- Preferences evolve over time
- Historical snapshots enable trend analysis

✅ **Article II: 100% Verification**
- Strict typing with Pydantic models
- No Dict[Any, Any]
- Comprehensive test coverage (28 tests, 100% passing)

✅ **Article I: Complete Context**
- Analyzes ALL responses before making recommendations
- Min confidence thresholds prevent premature conclusions
- Retry logic and timeouts not applicable (batch processing)

## Production Deployment

### Environment Variables

```bash
# Firebase configuration (if using Firestore)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json

# Learning parameters (optional)
PREFERENCE_MIN_CONFIDENCE=0.6
PREFERENCE_MIN_SAMPLE_SIZE=10
PREFERENCE_TREND_WINDOW_DAYS=7
```

### Update Triggers

**Recommended**:
- After every 5 responses: Quick update
- Hourly: Full re-analysis
- Daily: Generate new recommendations
- Weekly: Deep trend analysis

**Implementation**:
```python
# In Trinity main loop
response_count = 0

async def on_alex_response(response):
    global response_count

    # Store response
    store.store_response(response)
    response_count += 1

    # Trigger learning after every 5 responses
    if response_count % 5 == 0:
        await update_preferences()

async def update_preferences():
    # Get recent responses
    responses = store.get_recent_responses(limit=100)

    # Learn preferences
    learner = AlexPreferenceLearner()
    preferences = learner.analyze_responses(responses)

    # Store updated preferences
    store.store_preferences(preferences, snapshot_reason="periodic_update")

    # Log key recommendations
    for rec in preferences.recommendations[:3]:
        logger.info(f"Preference insight: {rec.title}")
```

## Future Enhancements

1. **Advanced Context Analysis**
   - NLP for semantic context understanding
   - Multi-word phrase detection
   - Sentiment analysis

2. **Response Time Analysis**
   - Fast responses → high interest
   - Slow responses → uncertainty
   - Very slow → should have asked differently

3. **Cross-Dimensional Insights**
   - "Coaching questions work best in morning"
   - "Client work questions better on Monday/Tuesday"
   - "Entertainment only on weekends"

4. **Adaptive Thresholds**
   - Learn optimal confidence thresholds per category
   - Dynamic sample size requirements

5. **Collaborative Filtering**
   - Learn from similar user patterns (anonymized)
   - Accelerate learning for new categories

6. **Explainability**
   - "I'm asking because you accepted 85% of coaching questions this week"
   - Transparency in decision-making

## FAQ

**Q: How many responses needed before reliable patterns?**
A: Minimum 10 responses per category for 50% confidence. 20+ responses for high confidence (>80%).

**Q: How does the system handle changing preferences?**
A: Trend detection analyzes recent vs. historical acceptance rates. Preferences update continuously as new data arrives.

**Q: What if Alex's behavior differs by context?**
A: Contextual patterns capture this. "Questions after 'coaching' context" is tracked separately from general topic preference.

**Q: Can preferences be manually overridden?**
A: Yes. You can manually set preference values or adjust confidence scores. However, the system will continue learning from new responses.

**Q: How to reset learning if Alex's preferences change dramatically?**
A: Use `store.delete_all_responses()` to clear history and start fresh, or weight recent responses higher in the algorithm.

## Summary

The Preference Learning System transforms Trinity from "asking randomly" to "asking intelligently based on what Alex actually values." By analyzing response patterns across multiple dimensions (question type, timing, topic, context), the system generates actionable recommendations that help ARCHITECT optimize proactive assistance.

**Key Metrics**:
- 28 tests passing (100%)
- 5 core models
- 6 time-of-day periods analyzed
- 9 topic categories tracked
- 5 question types classified
- 4 response types handled

**Philosophy in Action**:
> "The data will guide us. We optimize for Alex's subjective helpfulness, not arbitrary metrics."

When the system learns that Alex accepts 85% of coaching questions in the morning but only 15% of food suggestions at lunch, Trinity stops wasting his time and focuses on what matters.

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2025-10-01
