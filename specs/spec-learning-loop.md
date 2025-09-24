# Technical Specification: Autonomous Learning Loop

**Spec ID**: SPEC-LEARNING-001
**Version**: 1.0
**Date**: 2024-09-24
**Status**: Draft
**Author**: Agency Architecture Team

## Executive Summary

This specification defines the autonomous learning loop system that enables the Agency to detect patterns from operations, learn from successes and failures, and apply learned patterns to similar problems without human intervention.

## Goals

1. **Automatic Pattern Extraction**: Extract reusable patterns from every successful operation
2. **Failure Learning**: Learn from failures to avoid repeating mistakes
3. **Pattern Application**: Automatically apply learned patterns to similar problems
4. **Autonomous Triggering**: Detect and respond to system events without human intervention
5. **Measurable Improvement**: Track improvement metrics over time

## Non-Goals

1. **Not** a general AI system - focused on specific code operations
2. **Not** replacing human judgment on architectural decisions
3. **Not** learning from external codebases (only from Agency's own operations)
4. **Not** modifying core constitutional principles

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Event Detection Layer                    │
├─────────────────────────────────────────────────────────────┤
│  File Watcher │ Error Monitor │ Test Runner │ Git Hook      │
└──────┬────────┴───────┬───────┴──────┬──────┴────────┬──────┘
       │                │               │               │
       ▼                ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Event Router & Classifier                 │
│  - Categorizes events (error, success, change, etc.)        │
│  - Determines if learning opportunity exists                │
└──────────────────────────┬───────────────────────────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Pattern    │ │   Healing    │ │   Learning   │
│  Extractor   │ │   Trigger    │ │   Storage    │
└──────────────┘ └──────────────┘ └──────────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Action Executor                          │
│  - Applies patterns                                         │
│  - Executes healing                                         │
│  - Validates results                                        │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Design

### 1. Event Detection Layer

#### 1.1 File Watcher Component
```python
class FileWatcher:
    """
    Monitors filesystem for changes that might trigger learning.
    """

    watch_patterns = [
        "**/*.py",           # Python source files
        "**/*.md",           # Documentation
        "**/tests/*.py",     # Test files
        ".github/**/*.yml"   # CI/CD configs
    ]

    ignore_patterns = [
        "**/__pycache__/**",
        "**/.git/**",
        "**/logs/**",
        "**/*.pyc"
    ]

    def on_file_modified(self, path: Path) -> Event:
        """Triggered when file is modified."""
        return Event(
            type="file_modified",
            path=str(path),
            timestamp=datetime.now(),
            metadata=self._extract_metadata(path)
        )
```

#### 1.2 Error Monitor Component
```python
class ErrorMonitor:
    """
    Monitors logs and test outputs for errors.
    """

    error_sources = [
        "logs/events/*.jsonl",     # Telemetry events
        "pytest_output.log",       # Test failures
        ".git/hooks/pre-commit.log" # Commit failures
    ]

    error_patterns = {
        "NoneType": r"AttributeError.*NoneType",
        "ImportError": r"ImportError|ModuleNotFoundError",
        "TestFailure": r"FAILED.*test_",
        "SyntaxError": r"SyntaxError.*line \d+",
        "TypeError": r"TypeError.*arguments?"
    }

    def detect_error(self, log_content: str) -> Optional[ErrorEvent]:
        """Extract error information from logs."""
        for error_type, pattern in self.error_patterns.items():
            if match := re.search(pattern, log_content):
                return ErrorEvent(
                    type=error_type,
                    message=match.group(0),
                    context=self._extract_context(log_content, match),
                    timestamp=datetime.now()
                )
```

### 2. Pattern Extraction Logic

#### 2.1 Success Pattern Extraction
```python
class PatternExtractor:
    """
    Extracts reusable patterns from successful operations.
    """

    def extract_from_success(self, operation: Operation) -> Pattern:
        """
        Extract pattern from successful operation.

        Example operation:
        - Task: "Fix ImportError in test_agency.py"
        - Actions: [Read, Edit, Test]
        - Result: Tests passing

        Extracted pattern:
        - Trigger: "ImportError in test file"
        - Solution: "Add missing import statement"
        - Validation: "Run tests"
        """

        pattern = Pattern(
            id=generate_id(),
            trigger=self._identify_trigger(operation),
            preconditions=self._extract_preconditions(operation),
            actions=self._extract_action_sequence(operation),
            postconditions=self._extract_postconditions(operation),
            confidence=0.5,  # Initial confidence
            usage_count=0,
            success_count=0
        )

        return pattern

    def _identify_trigger(self, operation: Operation) -> Trigger:
        """Identify what triggered this operation."""
        # Analyze initial state/error
        if operation.initial_error:
            return ErrorTrigger(
                error_type=operation.initial_error.type,
                error_pattern=operation.initial_error.pattern
            )
        elif operation.task_description:
            return TaskTrigger(
                keywords=extract_keywords(operation.task_description)
            )

    def _extract_action_sequence(self, operation: Operation) -> List[Action]:
        """Extract the sequence of actions that led to success."""
        actions = []
        for tool_call in operation.tool_calls:
            action = Action(
                tool=tool_call.tool_name,
                parameters=self._generalize_parameters(tool_call.parameters),
                output_pattern=self._extract_output_pattern(tool_call.output)
            )
            actions.append(action)
        return actions
```

#### 2.2 Failure Pattern Learning
```python
class FailureLearner:
    """
    Learns from failures to avoid repeating mistakes.
    """

    def learn_from_failure(self, operation: Operation) -> AntiPattern:
        """
        Extract anti-pattern from failed operation.
        """

        anti_pattern = AntiPattern(
            id=generate_id(),
            trigger=self._identify_trigger(operation),
            failed_approach=self._extract_action_sequence(operation),
            failure_reason=self._analyze_failure(operation),
            alternative_approaches=self._suggest_alternatives(operation),
            severity="high" if operation.caused_regression else "medium"
        )

        return anti_pattern

    def _analyze_failure(self, operation: Operation) -> FailureReason:
        """Determine why the operation failed."""
        if operation.test_results and not operation.test_results.passed:
            return TestFailure(
                failed_tests=operation.test_results.failures,
                root_cause=self._analyze_test_failures(operation.test_results)
            )
        elif operation.error:
            return ExecutionError(
                error_type=type(operation.error).__name__,
                error_message=str(operation.error)
            )
```

### 3. Autonomous Trigger System

#### 3.1 Event Router
```python
class EventRouter:
    """
    Routes events to appropriate handlers based on type and context.
    """

    def __init__(self):
        self.handlers = {
            "error_detected": ErrorHandler(),
            "test_failure": TestFailureHandler(),
            "file_modified": ChangeHandler(),
            "pattern_matched": PatternApplicationHandler()
        }

    async def route_event(self, event: Event) -> Response:
        """
        Route event to appropriate handler.

        Decision tree:
        1. Is this an error? → Try healing
        2. Is this a test failure? → Analyze and fix
        3. Is this a change? → Check for improvement opportunity
        4. Does this match a known pattern? → Apply pattern
        """

        # Check for pattern matches first
        if patterns := self.pattern_store.find_matching(event):
            return await self.handlers["pattern_matched"].handle(event, patterns)

        # Route based on event type
        if handler := self.handlers.get(event.type):
            return await handler.handle(event)

        # Log unhandled event for future learning
        self.telemetry.log("unhandled_event", event.to_dict())
```

#### 3.2 Autonomous Healing Trigger
```python
class HealingTrigger:
    """
    Automatically triggers healing when errors are detected.
    """

    def __init__(self):
        self.healing_core = SelfHealingCore()
        self.pattern_store = PatternStore()
        self.cooldown = {}  # Prevent healing loops

    async def handle_error(self, error: ErrorEvent) -> HealingResult:
        """
        Attempt to heal detected error.
        """

        # Check cooldown
        if self._in_cooldown(error):
            return HealingResult(skipped=True, reason="cooldown")

        # Check for known pattern
        if pattern := self.pattern_store.find_pattern_for_error(error):
            result = await self._apply_pattern(pattern, error)
        else:
            # Attempt generic healing
            result = await self._attempt_generic_healing(error)

        # Learn from result
        if result.success:
            self._record_success(error, result)
        else:
            self._record_failure(error, result)
            self._add_cooldown(error)

        return result

    def _in_cooldown(self, error: ErrorEvent) -> bool:
        """Check if this error is in cooldown period."""
        key = f"{error.type}:{error.file}"
        if last_attempt := self.cooldown.get(key):
            return (datetime.now() - last_attempt).seconds < 300  # 5 min cooldown
        return False
```

### 4. Pattern Storage & Retrieval

#### 4.1 Pattern Store Schema
```python
@dataclass
class Pattern:
    id: str
    trigger: Trigger
    preconditions: List[Condition]
    actions: List[Action]
    postconditions: List[Condition]
    metadata: PatternMetadata

@dataclass
class PatternMetadata:
    confidence: float  # 0.0 to 1.0
    usage_count: int
    success_count: int
    failure_count: int
    last_used: datetime
    created_at: datetime
    source: str  # "learned", "manual", "imported"
    tags: List[str]
```

#### 4.2 Pattern Matching Algorithm
```python
class PatternMatcher:
    """
    Matches events to stored patterns using similarity scoring.
    """

    def find_matches(self, event: Event) -> List[PatternMatch]:
        """
        Find patterns that could handle this event.
        """

        candidates = []

        for pattern in self.pattern_store.all():
            # Calculate similarity score
            score = self._calculate_similarity(event, pattern)

            # Apply confidence weighting
            weighted_score = score * pattern.metadata.confidence

            # Filter by minimum threshold
            if weighted_score > self.min_threshold:
                candidates.append(PatternMatch(
                    pattern=pattern,
                    score=weighted_score,
                    confidence=self._calculate_confidence(pattern, event)
                ))

        # Sort by score
        return sorted(candidates, key=lambda x: x.score, reverse=True)

    def _calculate_similarity(self, event: Event, pattern: Pattern) -> float:
        """
        Calculate similarity between event and pattern trigger.

        Factors:
        - Error type match: 0.4
        - File type match: 0.2
        - Context similarity: 0.2
        - Historical success: 0.2
        """

        score = 0.0

        # Error type matching
        if hasattr(event, 'error_type') and hasattr(pattern.trigger, 'error_type'):
            if event.error_type == pattern.trigger.error_type:
                score += 0.4

        # File context matching
        if self._similar_file_context(event, pattern):
            score += 0.2

        # Semantic similarity of context
        if context_similarity := self._semantic_similarity(event, pattern):
            score += 0.2 * context_similarity

        # Historical success rate
        if pattern.metadata.usage_count > 0:
            success_rate = pattern.metadata.success_count / pattern.metadata.usage_count
            score += 0.2 * success_rate

        return score
```

### 5. Metrics & Monitoring

#### 5.1 Learning Metrics
```python
class LearningMetrics:
    """
    Track learning system effectiveness.
    """

    metrics = {
        "patterns_learned": Counter(),
        "patterns_applied": Counter(),
        "healing_attempts": Counter(),
        "healing_successes": Counter(),
        "average_confidence": RollingAverage(window=100),
        "improvement_rate": TrendAnalyzer()
    }

    def record_pattern_application(self, pattern: Pattern, success: bool):
        """Record pattern application result."""
        self.metrics["patterns_applied"].increment()

        if success:
            pattern.metadata.success_count += 1
            # Increase confidence
            pattern.metadata.confidence = min(1.0, pattern.metadata.confidence * 1.1)
        else:
            pattern.metadata.failure_count += 1
            # Decrease confidence
            pattern.metadata.confidence = max(0.1, pattern.metadata.confidence * 0.9)

        pattern.metadata.usage_count += 1
        pattern.metadata.last_used = datetime.now()
```

## Implementation Plan

### Phase 1: Foundation (Day 1)
1. Implement Event Detection Layer
2. Create basic Pattern and Event data structures
3. Set up pattern storage (using existing UnifiedPatternStore)

### Phase 2: Pattern Extraction (Day 2)
1. Implement PatternExtractor for success patterns
2. Implement FailureLearner for anti-patterns
3. Create pattern matching algorithm

### Phase 3: Autonomous Triggers (Day 3)
1. Implement EventRouter
2. Create HealingTrigger with cooldown logic
3. Wire up to existing SelfHealingCore

### Phase 4: Integration & Testing (Day 4)
1. Integration tests for full learning loop
2. Metrics collection and dashboard
3. Documentation and examples

## Success Criteria

1. **Pattern Learning Rate**: Learn at least 1 new pattern per 10 operations
2. **Pattern Application Success**: >70% success rate when applying patterns
3. **Healing Success Rate**: >60% of auto-healing attempts succeed
4. **Improvement Over Time**: Measurable reduction in similar errors
5. **No Human Intervention**: System runs for 24 hours without manual fixes

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Infinite healing loops | Cooldown periods, max retry limits |
| Learning bad patterns | Confidence scoring, human review queue |
| Pattern conflicts | Priority system, specificity ordering |
| Performance overhead | Async processing, event batching |
| False positive matches | Minimum confidence threshold |

## Configuration

```yaml
# learning_config.yaml
learning:
  enabled: true

  triggers:
    file_watch: true
    error_monitor: true
    test_monitor: true
    git_hooks: true

  thresholds:
    min_pattern_confidence: 0.3
    min_match_score: 0.5
    cooldown_minutes: 5
    max_retries: 3

  storage:
    backend: "sqlite"  # or "memory"
    persist_patterns: true
    max_patterns: 1000
    cleanup_days: 30

  monitoring:
    metrics_enabled: true
    dashboard_port: 8080
    alert_on_failure: true
```

## Testing Strategy

### Unit Tests
- Pattern extraction from known operations
- Pattern matching with various inputs
- Cooldown and retry logic

### Integration Tests
- Full loop: error → detection → healing → learning
- Pattern persistence and retrieval
- Multi-pattern conflict resolution

### End-to-End Tests
- Inject known error, verify autonomous fix
- Verify pattern learned and reused
- 24-hour autonomous operation test

## Open Questions

1. Should we allow manual pattern creation/editing?
2. How to handle patterns that become stale over time?
3. Should patterns be versioned?
4. How to share patterns between Agency instances?

## Appendices

### A. Pattern Examples

```json
{
  "id": "fix-import-error-001",
  "trigger": {
    "type": "error",
    "error_type": "ImportError",
    "pattern": "cannot import name '(\\w+)' from '([\\w\\.]+)'"
  },
  "actions": [
    {
      "tool": "grep",
      "params": {"pattern": "{captured_name}", "path": "{captured_module}"}
    },
    {
      "tool": "edit",
      "params": {"old": "from {module} import {old_name}",
                 "new": "from {module} import {new_name}"}
    },
    {
      "tool": "test",
      "params": {"file": "{affected_test}"}
    }
  ],
  "metadata": {
    "confidence": 0.85,
    "usage_count": 12,
    "success_count": 10
  }
}
```

### B. Event Flow Example

```
1. File modified: tests/test_agency.py
2. Test runner triggered automatically
3. Test failure detected: ImportError
4. Pattern matcher finds: "fix-import-error-001" (score: 0.82)
5. Pattern applied: Edit import statement
6. Tests run again: Success
7. Pattern confidence increased: 0.85 → 0.87
8. Event logged for metrics
```