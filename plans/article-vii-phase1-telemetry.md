# Article VII Phase 1: Constitutional Telemetry Implementation Plan

**Version**: 1.0
**Status**: Ready for Implementation
**Author**: PlannerAgent (AgencyOS)
**Date**: 2025-10-04
**Parent Plan**: plans/meta-constitutional-evolution.md

---

## Executive Summary

This plan details the technical implementation of Article VII Phase 1: Constitutional Telemetry. The goal is to capture all constitutional enforcement events to VectorStore, enabling the constitution to learn from its own enforcement patterns. This creates the foundation for the meta-constitutional evolution framework.

**Key Deliverable**: Constitutional enforcement data flowing from all enforcement points to VectorStore with structured schema, queryable for pattern analysis.

**Constitutional Alignment**:
- Article I: Complete context gathering via telemetry
- Article II: 100% verification through test coverage
- Article IV: Continuous learning through VectorStore integration (MANDATORY per constitution)
- Article V: Spec-driven development (this plan follows spec-kit format)

---

## I. Goals and Non-Goals

### Goals
1. Capture constitutional enforcement events from all enforcement points
2. Store events in VectorStore for cross-session learning
3. Maintain structured schema for event analysis
4. Enable queryable constitutional compliance history
5. Integrate seamlessly with existing tools/constitution_check.py
6. Support future pattern synthesis and ADR auto-generation

### Non-Goals
1. Pattern analysis/clustering (Phase 2)
2. ADR auto-generation (Phase 3)
3. Dashboard UI (Phase 4)
4. Modification of constitutional rules themselves
5. Real-time enforcement blocking (already exists)

---

## II. Personas and Use Cases

### Persona 1: QualityEnforcerAgent
**Context**: Runs constitutional checks before commits and during CI
**Need**: Record each violation for learning and pattern detection
**User Story**: As QualityEnforcer, I need to log every constitutional check result so the system can identify high-friction rules and false positives over time.

### Persona 2: ChiefArchitectAgent
**Context**: Reviews constitutional effectiveness and proposes amendments
**Need**: Query historical enforcement data to identify patterns
**User Story**: As ChiefArchitect, I need to query "Why does Article III block post-merge cleanup commits?" and get evidence-based answers from historical telemetry.

### Persona 3: LearningAgent
**Context**: Analyzes session data for institutional knowledge
**Need**: Access constitutional events as part of broader learning corpus
**User Story**: As LearningAgent, I need constitutional telemetry integrated into VectorStore so I can detect cross-domain patterns (e.g., "tests fail after Article V spec violations").

### Persona 4: Human Developer (@am)
**Context**: Investigates constitutional compliance issues
**Need**: Trace why a commit was blocked or a rule triggered
**User Story**: As developer, I need to see "What constitutional events occurred in the last 7 days?" to understand enforcement patterns.

---

## III. Acceptance Criteria

### Functional Requirements
1. **Event Capture**
   - [ ] All constitution_check.py violations logged to telemetry
   - [ ] Pre-commit hook constitutional checks logged
   - [ ] CI workflow constitutional checks logged
   - [ ] Git operations (commit, merge, PR) logged with constitutional context

2. **VectorStore Integration**
   - [ ] Constitutional events stored in VectorStore with proper schema
   - [ ] Events tagged with article, section, agent, outcome
   - [ ] Searchable via semantic queries ("false positive Article III")
   - [ ] Retention policy: 1 year of constitutional events

3. **Schema Compliance**
   - [ ] All events follow ConstitutionalEvent Pydantic model
   - [ ] No Dict[str, Any] usage (Article constitutional compliance)
   - [ ] Backwards compatible with existing telemetry.py

4. **Testing**
   - [ ] 100% test coverage for new telemetry functions
   - [ ] Integration test: event flow from constitution_check.py → VectorStore
   - [ ] Test query interface for historical events
   - [ ] Test event schema validation

### Non-Functional Requirements
1. **Performance**: Event logging adds <10ms latency to constitutional checks
2. **Storage**: JSONL format for efficient append-only writes
3. **Privacy**: No sensitive data (tokens, secrets) in telemetry
4. **Reliability**: Telemetry failures never block enforcement

---

## IV. Architecture Design

### 4.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   Constitutional Enforcement Layer               │
├─────────────────────────────────────────────────────────────────┤
│  tools/constitution_check.py                                    │
│  ├─ check_article_i_complete_context()                          │
│  ├─ check_article_ii_verification()                             │
│  ├─ check_article_iii_automated_enforcement()                   │
│  ├─ check_article_iv_continuous_learning()                      │
│  └─ check_article_v_spec_driven()                               │
│         │                                                         │
│         ├──> emit_constitutional_event()  [NEW]                 │
│         │                                                         │
│         └──> ConstitutionalTelemetry      [NEW]                 │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│               Telemetry Storage Layer (Dual Path)               │
├─────────────────────────────────────────────────────────────────┤
│  Path 1: JSONL Logs (Immediate Persistence)                     │
│  ├─ logs/constitutional_telemetry/events_YYYYMMDD.jsonl         │
│  └─ Append-only, secure permissions (0600)                      │
│                                                                   │
│  Path 2: SimpleTelemetry Integration                            │
│  ├─ core/telemetry.py → log()                                   │
│  └─ Unified event sink for all telemetry                        │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   VectorStore Ingestion                          │
├─────────────────────────────────────────────────────────────────┤
│  tools/ingest_constitutional_events.py    [NEW]                 │
│  ├─ Read JSONL logs (daily/on-demand)                           │
│  ├─ Parse and validate ConstitutionalEvent schema               │
│  ├─ Generate embeddings for semantic search                     │
│  └─ Store in agency_memory/vector_store.py                      │
│                                                                   │
│  Trigger: Nightly cron OR post-session manual invocation        │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Query Interface                               │
├─────────────────────────────────────────────────────────────────┤
│  tools/query_constitutional_history.py    [NEW]                 │
│  ├─ search_by_article(article="III", days=7)                    │
│  ├─ search_by_outcome(outcome="false_positive")                 │
│  ├─ semantic_search(query="post-merge cleanup blocks")          │
│  └─ get_compliance_metrics(period="30d")                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow

```
1. Constitutional Check
   └─> ViolationReport created (existing)
       └─> emit_constitutional_event(violation) [NEW]
           ├─> Write to JSONL (immediate)
           └─> Emit to SimpleTelemetry (unified sink)

2. Ingestion (Nightly)
   └─> Read JSONL logs
       └─> Validate schema
           └─> Generate embeddings
               └─> Store in VectorStore with tags

3. Query (On-Demand)
   └─> VectorStore.search(query, filters)
       └─> Returns ConstitutionalEvent records with relevance scores
```

### 4.3 Integration Points

| Component | Integration Type | Modification Required |
|-----------|------------------|----------------------|
| tools/constitution_check.py | Code enhancement | Add telemetry emission after each check |
| core/telemetry.py | Registration | Add ConstitutionalEvent to EventType enum |
| agency_memory/vector_store.py | Schema extension | Add constitutional event indexing |
| shared/models/telemetry.py | New model | Define ConstitutionalEvent Pydantic model |
| .github/workflows/constitutional-ci.yml | CI enhancement | Log constitutional checks during workflow |

---

## V. Schema Design

### 5.1 ConstitutionalEvent Pydantic Model

**Location**: `shared/models/constitutional.py` (NEW FILE)

```python
"""
Constitutional enforcement telemetry models.
Captures enforcement events for learning and pattern analysis.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

from shared.type_definitions.json import JSONValue


class Article(str, Enum):
    """Constitutional articles."""
    ARTICLE_I = "I"
    ARTICLE_II = "II"
    ARTICLE_III = "III"
    ARTICLE_IV = "IV"
    ARTICLE_V = "V"
    ARTICLE_VII = "VII"  # For future meta-constitutional events


class EnforcementAction(str, Enum):
    """Actions taken during constitutional enforcement."""
    BLOCKED = "blocked"           # Operation prevented
    WARNING = "warning"           # Flagged but allowed
    AUTO_FIX = "auto_fix"         # Automatically remediated
    PASSED = "passed"             # Compliance verified


class EnforcementOutcome(str, Enum):
    """Outcome classification for enforcement events."""
    SUCCESS = "success"           # Correct enforcement
    FALSE_POSITIVE = "false_positive"  # Incorrect block
    FRICTION = "friction"         # Valid but high-cost enforcement
    OVERRIDE = "override"         # Rule bypassed (should be rare)


class ConstitutionalEvent(BaseModel):
    """
    Constitutional enforcement telemetry event.

    Captures every instance of constitutional rule application
    for learning and pattern analysis.
    """
    model_config = ConfigDict(extra="forbid")

    # Event identification
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Constitutional context
    article: Article = Field(..., description="Constitutional article triggered")
    section: str | None = Field(None, description="Article section (e.g., '2.1')")
    rule_description: str = Field(..., description="Human-readable rule description")

    # Enforcement context
    context: dict[str, JSONValue] = Field(
        default_factory=dict,
        description="Contextual metadata about enforcement trigger"
    )
    # Context schema (flexible but documented):
    # {
    #   "branch": str,           # Git branch name
    #   "commit_hash": str,      # Git commit hash (if applicable)
    #   "agent_id": str,         # Agent triggering check
    #   "file_path": str,        # File being checked
    #   "operation": str,        # "commit", "merge", "pr_create", "check"
    #   "tool": str,             # Tool invoking check
    # }

    # Enforcement result
    action: EnforcementAction = Field(..., description="Action taken by enforcer")
    outcome: EnforcementOutcome = Field(
        EnforcementOutcome.SUCCESS,
        description="Outcome classification"
    )

    # Metadata
    severity: str = Field(
        "info",
        description="Severity level (info, warning, error, critical)"
    )
    error_message: str | None = Field(
        None,
        description="Error message if action=blocked"
    )
    suggested_fix: str | None = Field(
        None,
        description="Suggested remediation if available"
    )
    metadata: dict[str, JSONValue] = Field(
        default_factory=dict,
        description="Additional metadata for analysis"
    )

    # Learning support
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization and search"
    )
    # Tags examples: ["constitutional", "article_i", "pre-commit", "agent:planner"]

    def to_jsonl(self) -> str:
        """Convert to JSONL format for logging."""
        import json
        return json.dumps(self.model_dump(mode="json"))

    def generate_tags(self) -> list[str]:
        """Generate standard tags for VectorStore indexing."""
        tags = [
            "constitutional",
            f"article_{self.article.value.lower()}",
            f"action_{self.action.value}",
            f"outcome_{self.outcome.value}",
        ]

        if self.context.get("agent_id"):
            tags.append(f"agent:{self.context['agent_id']}")

        if self.context.get("operation"):
            tags.append(f"operation:{self.context['operation']}")

        return tags + self.tags
```

### 5.2 Supporting Types

**Location**: `shared/models/constitutional.py` (same file)

```python
class ComplianceMetrics(BaseModel):
    """Aggregated constitutional compliance metrics."""
    model_config = ConfigDict(extra="forbid")

    period_start: datetime
    period_end: datetime
    total_events: int = 0
    events_by_article: dict[str, int] = Field(default_factory=dict)
    events_by_action: dict[str, int] = Field(default_factory=dict)
    events_by_outcome: dict[str, int] = Field(default_factory=dict)
    compliance_rate: float = Field(0.0, ge=0.0, le=1.0)
    false_positive_rate: float = Field(0.0, ge=0.0, le=1.0)

    def calculate_rates(self) -> None:
        """Calculate compliance and false positive rates."""
        if self.total_events == 0:
            return

        success_count = self.events_by_outcome.get("success", 0)
        fp_count = self.events_by_outcome.get("false_positive", 0)

        self.compliance_rate = success_count / self.total_events
        self.false_positive_rate = fp_count / self.total_events
```

---

## VI. File Structure and Module Responsibilities

### 6.1 New Files

```
shared/models/
  └─ constitutional.py         [NEW] - Pydantic models for constitutional telemetry

tools/
  ├─ constitutional_telemetry.py  [NEW] - Telemetry emission logic
  ├─ ingest_constitutional_events.py  [NEW] - JSONL → VectorStore ingestion
  └─ query_constitutional_history.py  [NEW] - Query interface for events

logs/
  └─ constitutional_telemetry/   [NEW] - JSONL event logs
      ├─ events_20251004.jsonl
      ├─ events_20251005.jsonl
      └─ ...

tests/
  ├─ test_constitutional_telemetry.py  [NEW] - Unit tests for telemetry
  ├─ test_constitutional_ingestion.py  [NEW] - Ingestion pipeline tests
  └─ test_constitutional_queries.py    [NEW] - Query interface tests
```

### 6.2 Modified Files

```
tools/
  └─ constitution_check.py     [MODIFY] - Add telemetry emission

core/
  └─ telemetry.py             [MODIFY] - Register ConstitutionalEvent type

agency_memory/
  └─ vector_store.py          [MODIFY] - Add constitutional event indexing
```

### 6.3 Module Responsibilities

| Module | Responsibility | Key Functions |
|--------|---------------|---------------|
| constitutional_telemetry.py | Emit telemetry events | emit_constitutional_event() |
| constitution_check.py | Constitutional enforcement + telemetry | Enhanced check_article_*() |
| ingest_constitutional_events.py | JSONL → VectorStore | ingest_daily_events(), validate_schema() |
| query_constitutional_history.py | Historical queries | search_by_article(), get_metrics() |
| vector_store.py | Event storage + semantic search | add_constitutional_memory() |

---

## VII. Implementation Plan (TDD-First)

### Phase 1A: Schema and Models (Week 1, Days 1-2)

**Tasks**:
1. Create `shared/models/constitutional.py` with Pydantic models
2. Write comprehensive tests for ConstitutionalEvent validation
3. Test edge cases: missing fields, invalid enums, schema evolution

**Test Cases** (write BEFORE implementation):
```python
# tests/test_constitutional_telemetry.py

def test_constitutional_event_creation():
    """Test creating a valid ConstitutionalEvent."""
    event = ConstitutionalEvent(
        event_id="test-001",
        article=Article.ARTICLE_III,
        section="2",
        rule_description="No direct main commits",
        context={
            "branch": "main",
            "agent_id": "planner",
            "operation": "commit"
        },
        action=EnforcementAction.BLOCKED,
        outcome=EnforcementOutcome.SUCCESS
    )
    assert event.article == Article.ARTICLE_III
    assert "constitutional" in event.generate_tags()

def test_constitutional_event_validation_fails_on_invalid_article():
    """Test that invalid article enum raises validation error."""
    with pytest.raises(ValidationError):
        ConstitutionalEvent(
            event_id="test-002",
            article="INVALID",  # Should fail
            rule_description="Test",
            action=EnforcementAction.PASSED
        )

def test_constitutional_event_to_jsonl():
    """Test JSONL serialization."""
    event = ConstitutionalEvent(...)
    jsonl = event.to_jsonl()
    parsed = json.loads(jsonl)
    assert parsed["article"] == "III"
```

**Deliverable**: Validated Pydantic models with 100% test coverage

---

### Phase 1B: Telemetry Emission (Week 1, Days 3-4)

**Tasks**:
1. Create `tools/constitutional_telemetry.py`
2. Implement `emit_constitutional_event()` function
3. Integrate with `core/telemetry.py` (SimpleTelemetry)
4. Write JSONL to `logs/constitutional_telemetry/`

**Implementation**:

```python
# tools/constitutional_telemetry.py

"""
Constitutional telemetry emission.
Captures constitutional enforcement events to JSONL and VectorStore.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from core.telemetry import get_telemetry
from shared.models.constitutional import (
    ConstitutionalEvent,
    Article,
    EnforcementAction,
    EnforcementOutcome,
)
from shared.type_definitions.json import JSONValue


class ConstitutionalTelemetry:
    """
    Manages constitutional enforcement telemetry.

    Dual-path logging:
    1. JSONL files for dedicated constitutional event storage
    2. SimpleTelemetry for unified telemetry sink
    """

    def __init__(self, log_dir: Path | None = None):
        """Initialize telemetry with log directory."""
        self.log_dir = log_dir or Path.cwd() / "logs" / "constitutional_telemetry"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.telemetry = get_telemetry()

    def emit_event(
        self,
        article: Article,
        rule_description: str,
        action: EnforcementAction,
        context: dict[str, JSONValue] | None = None,
        outcome: EnforcementOutcome = EnforcementOutcome.SUCCESS,
        section: str | None = None,
        error_message: str | None = None,
        suggested_fix: str | None = None,
        **kwargs
    ) -> ConstitutionalEvent:
        """
        Emit a constitutional enforcement event.

        Args:
            article: Constitutional article triggered
            rule_description: Human-readable rule description
            action: Enforcement action taken
            context: Contextual metadata
            outcome: Outcome classification
            section: Article section
            error_message: Error message if blocked
            suggested_fix: Suggested remediation
            **kwargs: Additional metadata

        Returns:
            ConstitutionalEvent: Created event
        """
        # Generate unique event ID
        event_id = f"const_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Create event
        event = ConstitutionalEvent(
            event_id=event_id,
            article=article,
            section=section,
            rule_description=rule_description,
            context=context or {},
            action=action,
            outcome=outcome,
            error_message=error_message,
            suggested_fix=suggested_fix,
            metadata=kwargs,
        )

        # Path 1: Write to dedicated JSONL log
        self._write_jsonl(event)

        # Path 2: Emit to unified telemetry
        self._emit_to_telemetry(event)

        return event

    def _write_jsonl(self, event: ConstitutionalEvent) -> None:
        """Write event to daily JSONL file."""
        date_str = event.timestamp.strftime("%Y%m%d")
        log_file = self.log_dir / f"events_{date_str}.jsonl"

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.to_jsonl() + "\n")
        except Exception as e:
            # Non-fatal: telemetry failures should not block enforcement
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to write constitutional telemetry: {e}")

    def _emit_to_telemetry(self, event: ConstitutionalEvent) -> None:
        """Emit event to unified telemetry system."""
        self.telemetry.log(
            event="constitutional_enforcement",
            data={
                "event_id": event.event_id,
                "article": event.article.value,
                "section": event.section,
                "rule": event.rule_description,
                "action": event.action.value,
                "outcome": event.outcome.value,
                "context": event.context,
            },
            level=self._map_severity(event.action),
        )

    def _map_severity(self, action: EnforcementAction) -> str:
        """Map enforcement action to telemetry severity."""
        mapping = {
            EnforcementAction.BLOCKED: "error",
            EnforcementAction.WARNING: "warning",
            EnforcementAction.AUTO_FIX: "info",
            EnforcementAction.PASSED: "info",
        }
        return mapping.get(action, "info")


# Global singleton
_telemetry_instance: ConstitutionalTelemetry | None = None


def get_constitutional_telemetry() -> ConstitutionalTelemetry:
    """Get global constitutional telemetry instance."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = ConstitutionalTelemetry()
    return _telemetry_instance


def emit_constitutional_event(
    article: Article,
    rule_description: str,
    action: EnforcementAction,
    **kwargs
) -> ConstitutionalEvent:
    """
    Convenience function to emit constitutional event.

    Args:
        article: Constitutional article
        rule_description: Rule description
        action: Enforcement action
        **kwargs: Additional event parameters

    Returns:
        ConstitutionalEvent: Created event
    """
    telemetry = get_constitutional_telemetry()
    return telemetry.emit_event(article, rule_description, action, **kwargs)
```

**Test Cases**:
```python
def test_emit_constitutional_event_creates_jsonl():
    """Test that emitting event creates JSONL file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

        event = telemetry.emit_event(
            article=Article.ARTICLE_III,
            rule_description="No main commits",
            action=EnforcementAction.BLOCKED,
            context={"branch": "main"}
        )

        # Verify JSONL file created
        date_str = datetime.utcnow().strftime("%Y%m%d")
        log_file = Path(tmpdir) / f"events_{date_str}.jsonl"
        assert log_file.exists()

        # Verify content
        with open(log_file) as f:
            line = f.readline()
            parsed = json.loads(line)
            assert parsed["article"] == "III"

def test_telemetry_failure_does_not_raise():
    """Test that telemetry failures are non-fatal."""
    telemetry = ConstitutionalTelemetry(log_dir=Path("/invalid/path"))

    # Should not raise, just log warning
    event = telemetry.emit_event(
        article=Article.ARTICLE_I,
        rule_description="Complete context",
        action=EnforcementAction.PASSED
    )
    assert event is not None
```

**Deliverable**: Working telemetry emission with 100% test coverage

---

### Phase 1C: Integration with constitution_check.py (Week 1, Day 5)

**Tasks**:
1. Modify `tools/constitution_check.py` to emit events
2. Add telemetry after each article check
3. Emit events for both violations AND passes
4. Maintain backward compatibility

**Implementation**:

```python
# tools/constitution_check.py (modifications)

from tools.constitutional_telemetry import emit_constitutional_event
from shared.models.constitutional import (
    Article,
    EnforcementAction,
    EnforcementOutcome
)

class ConstitutionalEnforcer:
    # ... existing code ...

    def check_article_i_complete_context(self) -> bool:
        """Article I: Complete Context - with telemetry."""
        compliant = True

        # ... existing check logic ...

        # NEW: Emit telemetry for each violation
        for violation in self.violations:
            if violation.article == "Article I":
                emit_constitutional_event(
                    article=Article.ARTICLE_I,
                    rule_description=violation.description,
                    action=EnforcementAction.BLOCKED,
                    outcome=EnforcementOutcome.SUCCESS,
                    section="1",  # Infer from violation
                    context={
                        "file_path": violation.file_path,
                        "line_number": violation.line_number,
                        "agent_id": "constitutional_enforcer",
                        "operation": "pre-commit-check",
                    },
                    error_message=violation.description,
                    suggested_fix=violation.suggested_fix,
                )

        # NEW: Emit success event if compliant
        if compliant:
            emit_constitutional_event(
                article=Article.ARTICLE_I,
                rule_description="Complete context verification passed",
                action=EnforcementAction.PASSED,
                outcome=EnforcementOutcome.SUCCESS,
                context={
                    "agent_id": "constitutional_enforcer",
                    "operation": "pre-commit-check",
                },
            )

        return compliant

    # ... similar modifications for check_article_ii, iii, iv, v ...
```

**Test Cases**:
```python
def test_constitution_check_emits_telemetry_on_violation():
    """Test that violations emit telemetry events."""
    enforcer = ConstitutionalEnforcer()

    # Trigger violation
    compliant = enforcer.check_article_ii_verification()

    # Verify telemetry event created
    log_dir = Path("logs/constitutional_telemetry")
    date_str = datetime.utcnow().strftime("%Y%m%d")
    log_file = log_dir / f"events_{date_str}.jsonl"

    assert log_file.exists()
    # Parse and verify event

def test_constitution_check_emits_pass_events():
    """Test that successful checks also emit events."""
    # ... similar test for PASSED events
```

**Deliverable**: Integrated telemetry in constitution_check.py with tests

---

### Phase 1D: VectorStore Ingestion (Week 2, Days 1-3)

**Tasks**:
1. Create `tools/ingest_constitutional_events.py`
2. Read JSONL logs and parse ConstitutionalEvent records
3. Generate embeddings for semantic search
4. Store in VectorStore with proper tags
5. Create ingestion script for nightly cron

**Implementation**:

```python
# tools/ingest_constitutional_events.py

"""
Ingest constitutional telemetry events into VectorStore.
Reads JSONL logs and indexes for semantic search.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from agency_memory.vector_store import VectorStore
from shared.models.constitutional import ConstitutionalEvent


class ConstitutionalEventIngester:
    """
    Ingests constitutional events from JSONL logs to VectorStore.
    """

    def __init__(
        self,
        log_dir: Path | None = None,
        vector_store: VectorStore | None = None,
    ):
        """Initialize ingester."""
        self.log_dir = log_dir or Path.cwd() / "logs" / "constitutional_telemetry"
        self.vector_store = vector_store or VectorStore(embedding_provider="sentence-transformers")

    def ingest_daily_events(self, date: datetime | None = None) -> int:
        """
        Ingest events from a specific day.

        Args:
            date: Date to ingest (defaults to yesterday)

        Returns:
            Number of events ingested
        """
        target_date = date or (datetime.utcnow() - timedelta(days=1))
        date_str = target_date.strftime("%Y%m%d")
        log_file = self.log_dir / f"events_{date_str}.jsonl"

        if not log_file.exists():
            return 0

        ingested_count = 0

        with open(log_file) as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    # Parse and validate
                    event_dict = json.loads(line)
                    event = ConstitutionalEvent(**event_dict)

                    # Add to VectorStore
                    self._add_to_vector_store(event)
                    ingested_count += 1

                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to ingest event: {e}")
                    continue

        return ingested_count

    def _add_to_vector_store(self, event: ConstitutionalEvent) -> None:
        """Add constitutional event to VectorStore."""
        # Generate searchable text
        searchable_text = self._create_searchable_text(event)

        # Generate tags
        tags = event.generate_tags()

        # Create memory record
        memory_key = f"constitutional:{event.event_id}"
        memory_content = {
            "key": memory_key,
            "content": searchable_text,
            "tags": tags,
            "timestamp": event.timestamp.isoformat(),
            "event_data": event.model_dump(mode="json"),
        }

        # Add to VectorStore
        self.vector_store.add_memory(memory_key, memory_content)

    def _create_searchable_text(self, event: ConstitutionalEvent) -> str:
        """Create searchable text for semantic search."""
        parts = [
            f"Constitutional Article {event.article.value}",
            f"Section {event.section}" if event.section else "",
            f"Rule: {event.rule_description}",
            f"Action: {event.action.value}",
            f"Outcome: {event.outcome.value}",
        ]

        # Add context details
        if event.context:
            parts.append(f"Context: {json.dumps(event.context)}")

        # Add error message
        if event.error_message:
            parts.append(f"Error: {event.error_message}")

        return " | ".join(filter(None, parts))

    def ingest_range(self, start_date: datetime, end_date: datetime) -> int:
        """Ingest events from a date range."""
        total_ingested = 0
        current_date = start_date

        while current_date <= end_date:
            count = self.ingest_daily_events(current_date)
            total_ingested += count
            current_date += timedelta(days=1)

        return total_ingested


def main():
    """CLI entry point for ingestion."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest constitutional events")
    parser.add_argument("--date", help="Date to ingest (YYYYMMDD)")
    parser.add_argument("--days", type=int, default=1, help="Number of days to ingest")

    args = parser.parse_args()

    ingester = ConstitutionalEventIngester()

    if args.date:
        date = datetime.strptime(args.date, "%Y%m%d")
        end_date = date + timedelta(days=args.days - 1)
        count = ingester.ingest_range(date, end_date)
    else:
        # Default: ingest yesterday
        count = ingester.ingest_daily_events()

    print(f"Ingested {count} constitutional events")


if __name__ == "__main__":
    main()
```

**Test Cases**:
```python
def test_ingest_daily_events():
    """Test ingesting events from JSONL to VectorStore."""
    # Create test JSONL file
    # Run ingester
    # Verify VectorStore contains events
    pass

def test_searchable_text_generation():
    """Test that searchable text captures key fields."""
    event = ConstitutionalEvent(...)
    ingester = ConstitutionalEventIngester()
    text = ingester._create_searchable_text(event)

    assert "Article III" in text
    assert "blocked" in text
```

**Deliverable**: Working ingestion pipeline with tests

---

### Phase 1E: Query Interface (Week 2, Days 4-5)

**Tasks**:
1. Create `tools/query_constitutional_history.py`
2. Implement query functions for common patterns
3. Integrate with VectorStore semantic search
4. Create CLI for human queries

**Implementation**:

```python
# tools/query_constitutional_history.py

"""
Query interface for constitutional enforcement history.
Enables pattern analysis and evidence gathering.
"""

from datetime import datetime, timedelta
from typing import Literal

from agency_memory.vector_store import VectorStore
from shared.models.constitutional import (
    ConstitutionalEvent,
    ComplianceMetrics,
    Article,
    EnforcementOutcome,
)


class ConstitutionalHistoryQuery:
    """Query constitutional enforcement history."""

    def __init__(self, vector_store: VectorStore | None = None):
        """Initialize query interface."""
        self.vector_store = vector_store or VectorStore(
            embedding_provider="sentence-transformers"
        )

    def search_by_article(
        self,
        article: Article,
        days: int = 7,
        limit: int = 50,
    ) -> list[ConstitutionalEvent]:
        """
        Search events by article.

        Args:
            article: Article to search
            days: Days to look back
            limit: Maximum results

        Returns:
            List of matching events
        """
        tag = f"article_{article.value.lower()}"
        results = self.vector_store.search(
            query=f"Constitutional Article {article.value}",
            namespace="constitutional",
            limit=limit,
        )

        events = []
        for result in results:
            event_data = result.get("event_data")
            if event_data:
                events.append(ConstitutionalEvent(**event_data))

        return events

    def search_by_outcome(
        self,
        outcome: EnforcementOutcome,
        days: int = 30,
        limit: int = 100,
    ) -> list[ConstitutionalEvent]:
        """Search events by outcome (e.g., false positives)."""
        query = f"constitutional enforcement outcome {outcome.value}"
        results = self.vector_store.search(query, limit=limit)

        events = []
        for result in results:
            event_data = result.get("event_data")
            if event_data and event_data.get("outcome") == outcome.value:
                events.append(ConstitutionalEvent(**event_data))

        return events

    def semantic_search(self, query: str, limit: int = 20) -> list[ConstitutionalEvent]:
        """
        Semantic search across constitutional events.

        Args:
            query: Natural language query
            limit: Maximum results

        Returns:
            List of relevant events
        """
        results = self.vector_store.search(query, limit=limit)

        events = []
        for result in results:
            event_data = result.get("event_data")
            if event_data:
                events.append(ConstitutionalEvent(**event_data))

        return events

    def get_compliance_metrics(
        self,
        period_days: int = 30,
    ) -> ComplianceMetrics:
        """
        Calculate compliance metrics for a time period.

        Args:
            period_days: Days to analyze

        Returns:
            ComplianceMetrics with aggregated statistics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # Search all constitutional events in period
        all_events = self.semantic_search(
            query="constitutional enforcement",
            limit=10000,
        )

        # Filter by date
        events_in_period = [
            e for e in all_events
            if start_date <= e.timestamp <= end_date
        ]

        # Calculate metrics
        metrics = ComplianceMetrics(
            period_start=start_date,
            period_end=end_date,
            total_events=len(events_in_period),
        )

        for event in events_in_period:
            # Count by article
            article_key = event.article.value
            metrics.events_by_article[article_key] = (
                metrics.events_by_article.get(article_key, 0) + 1
            )

            # Count by action
            action_key = event.action.value
            metrics.events_by_action[action_key] = (
                metrics.events_by_action.get(action_key, 0) + 1
            )

            # Count by outcome
            outcome_key = event.outcome.value
            metrics.events_by_outcome[outcome_key] = (
                metrics.events_by_outcome.get(outcome_key, 0) + 1
            )

        # Calculate rates
        metrics.calculate_rates()

        return metrics


def main():
    """CLI for querying constitutional history."""
    import argparse

    parser = argparse.ArgumentParser(description="Query constitutional history")
    parser.add_argument("--article", choices=["I", "II", "III", "IV", "V"])
    parser.add_argument("--outcome", choices=["success", "false_positive", "friction"])
    parser.add_argument("--query", help="Semantic search query")
    parser.add_argument("--metrics", action="store_true", help="Show compliance metrics")
    parser.add_argument("--days", type=int, default=7, help="Days to search")

    args = parser.parse_args()

    query_interface = ConstitutionalHistoryQuery()

    if args.metrics:
        metrics = query_interface.get_compliance_metrics(period_days=args.days)
        print(f"Compliance Metrics ({args.days} days)")
        print(f"Total Events: {metrics.total_events}")
        print(f"Compliance Rate: {metrics.compliance_rate:.2%}")
        print(f"False Positive Rate: {metrics.false_positive_rate:.2%}")
        print(f"\nBy Article: {metrics.events_by_article}")

    elif args.article:
        events = query_interface.search_by_article(
            Article(args.article),
            days=args.days,
        )
        print(f"Found {len(events)} events for Article {args.article}")
        for event in events[:10]:
            print(f"  - {event.rule_description} ({event.action.value})")

    elif args.query:
        events = query_interface.semantic_search(args.query)
        print(f"Found {len(events)} events matching '{args.query}'")
        for event in events[:10]:
            print(f"  - {event.rule_description} ({event.action.value})")


if __name__ == "__main__":
    main()
```

**Test Cases**:
```python
def test_search_by_article():
    """Test searching events by article."""
    # Populate VectorStore with test events
    # Search by Article III
    # Verify results filtered correctly
    pass

def test_compliance_metrics_calculation():
    """Test compliance metrics aggregation."""
    # Create test events with known distribution
    # Calculate metrics
    # Verify accuracy of rates
    pass
```

**Deliverable**: Working query interface with CLI and tests

---

## VIII. Testing Strategy

### 8.1 Unit Tests

| Test Suite | Coverage Target | Key Tests |
|------------|----------------|-----------|
| test_constitutional_telemetry.py | 100% | Model validation, emission, JSONL writing |
| test_constitutional_ingestion.py | 100% | JSONL parsing, VectorStore storage |
| test_constitutional_queries.py | 100% | Search filters, semantic search, metrics |

### 8.2 Integration Tests

```python
# tests/integration/test_constitutional_telemetry_integration.py

def test_end_to_end_telemetry_flow():
    """
    Test complete flow: Check → Emit → JSONL → Ingest → Query
    """
    # 1. Run constitutional check (triggers violation)
    enforcer = ConstitutionalEnforcer()
    enforcer.check_article_iii_automated_enforcement()

    # 2. Verify JSONL created
    assert (Path("logs/constitutional_telemetry") / f"events_{date}.jsonl").exists()

    # 3. Run ingestion
    ingester = ConstitutionalEventIngester()
    count = ingester.ingest_daily_events()
    assert count > 0

    # 4. Query VectorStore
    query_interface = ConstitutionalHistoryQuery()
    events = query_interface.search_by_article(Article.ARTICLE_III)
    assert len(events) > 0

    # 5. Verify event data integrity
    event = events[0]
    assert event.article == Article.ARTICLE_III
    assert event.action in [EnforcementAction.BLOCKED, EnforcementAction.PASSED]
```

### 8.3 Performance Tests

```python
def test_telemetry_latency_under_10ms():
    """Test that emission adds <10ms latency."""
    start = time.time()

    emit_constitutional_event(
        article=Article.ARTICLE_I,
        rule_description="Test",
        action=EnforcementAction.PASSED,
    )

    duration_ms = (time.time() - start) * 1000
    assert duration_ms < 10  # Constitutional requirement
```

### 8.4 Edge Case Tests

```python
def test_telemetry_failure_does_not_block_enforcement():
    """Test that telemetry failures are non-fatal."""
    # Simulate disk full / permission error
    # Verify enforcement still completes
    # Verify error logged but not raised
    pass

def test_invalid_event_schema_handled_gracefully():
    """Test that invalid JSONL entries are skipped during ingestion."""
    # Create JSONL with malformed entries
    # Run ingestion
    # Verify valid entries processed, invalid skipped
    pass
```

---

## IX. Success Metrics

### Functional Success Criteria
- [ ] 100% of constitutional checks emit telemetry events
- [ ] All events stored in VectorStore within 24 hours (nightly ingestion)
- [ ] Semantic search returns relevant events (manual spot-checking)
- [ ] CLI query interface functional for all search patterns
- [ ] Zero enforcement operations blocked by telemetry failures

### Non-Functional Success Criteria
- [ ] Telemetry latency <10ms per event
- [ ] Test coverage 100% for new modules
- [ ] All tests pass (Article II compliance)
- [ ] No Dict[str, Any] in new code (strict typing)
- [ ] JSONL files readable and parseable by external tools

### Verification Methods
1. **Manual Testing**: Run constitution checks, verify JSONL created
2. **Automated Tests**: 100% pass rate on test suite
3. **Integration Testing**: Full flow from check → query verified
4. **Performance Testing**: Latency benchmarks under threshold
5. **Code Review**: ChiefArchitect reviews for constitutional compliance

---

## X. Risk Mitigation

### Risk 1: VectorStore Embedding Failures
**Impact**: Events not searchable semantically
**Mitigation**:
- Fallback to keyword search if embeddings fail
- Log embedding errors for debugging
- Test with both sentence-transformers and OpenAI providers

### Risk 2: JSONL File Corruption
**Impact**: Event data loss during ingestion
**Mitigation**:
- Validate JSON syntax during ingestion, skip malformed lines
- Keep JSONL files as append-only (no rewrites)
- Implement checksum validation for critical events

### Risk 3: Telemetry Performance Impact
**Impact**: Slows down constitutional checks
**Mitigation**:
- Async writing to JSONL (non-blocking)
- Benchmark latency, enforce <10ms requirement
- Circuit breaker if telemetry consistently slow

### Risk 4: Storage Growth
**Impact**: JSONL files grow unbounded
**Mitigation**:
- Implement retention policy (1 year of raw JSONL)
- Compress/archive old files after ingestion
- VectorStore serves as long-term indexed storage

---

## XI. Implementation Timeline

### Week 1: Core Implementation
- **Day 1-2**: Schema and models (Phase 1A)
- **Day 3-4**: Telemetry emission (Phase 1B)
- **Day 5**: Integration with constitution_check.py (Phase 1C)

### Week 2: Storage and Query
- **Day 1-3**: VectorStore ingestion (Phase 1D)
- **Day 4-5**: Query interface (Phase 1E)

### Week 3: Testing and Refinement
- **Day 1-2**: Integration tests and performance tests
- **Day 3**: Edge case handling and error scenarios
- **Day 4**: Documentation and CLI polish
- **Day 5**: Code review and constitutional compliance verification

**Total Duration**: 3 weeks (15 working days)

---

## XII. Definition of Done

### Code Complete
- [ ] All modules implemented per specification
- [ ] 100% test coverage on new code
- [ ] All tests passing (Article II compliance)
- [ ] No mypy/ruff violations
- [ ] Code reviewed by ChiefArchitect

### Documentation Complete
- [ ] Module docstrings complete
- [ ] CLI usage documented
- [ ] Schema documented in this plan
- [ ] ADR created for Article VII Phase 1

### Integration Complete
- [ ] constitution_check.py emits events
- [ ] VectorStore ingestion working
- [ ] Query interface functional
- [ ] CI pipeline includes constitutional telemetry tests

### Validation Complete
- [ ] Manual testing: emit event → query event
- [ ] Integration test: full pipeline verified
- [ ] Performance benchmarks met (<10ms)
- [ ] Human review: @am approves plan execution

---

## XIII. Future Work (Out of Scope for Phase 1)

### Phase 2: Pattern Synthesis (Week 4+)
- Clustering algorithm for high-friction rules
- False positive rate analysis
- Automated pattern reports

### Phase 3: ADR Auto-Generation (Week 5+)
- LLM-based ADR drafting from patterns
- Evidence synthesis from VectorStore
- Human review queue integration

### Phase 4: Dashboard UI (Week 6+)
- Constitutional health metrics visualization
- Amendment pipeline tracking
- Knowledge graph rendering

---

## XIV. References

### Related Documents
- `plans/meta-constitutional-evolution.md` - Parent plan for Article VII
- `constitution.md` - The constitution being monitored
- `docs/adr/ADR-004.md` - Continuous Learning mandate
- `tools/constitution_check.py` - Current enforcement implementation

### Constitutional Requirements
- **Article I**: Complete context before action (retry on timeout, all tests complete)
- **Article II**: 100% verification (all tests must pass)
- **Article IV**: VectorStore integration is MANDATORY
- **Article V**: Spec-driven development (this plan follows spec-kit)

### Technical Dependencies
- `agency_memory/vector_store.py` - Semantic search infrastructure
- `core/telemetry.py` - Unified telemetry sink
- `shared/models/telemetry.py` - Base telemetry models

---

## XV. Appendix: Example Queries

### Query 1: Find False Positives for Article III
```bash
python tools/query_constitutional_history.py \
  --article III \
  --outcome false_positive \
  --days 30
```

### Query 2: Semantic Search for Post-Merge Issues
```bash
python tools/query_constitutional_history.py \
  --query "post-merge cleanup blocked by constitutional check" \
  --days 60
```

### Query 3: Compliance Metrics Dashboard
```bash
python tools/query_constitutional_history.py \
  --metrics \
  --days 90
```

**Expected Output**:
```
Compliance Metrics (90 days)
Total Events: 1,247
Compliance Rate: 92.34%
False Positive Rate: 4.12%

By Article:
  I: 123
  II: 456
  III: 234
  IV: 89
  V: 345
```

---

## XVI. Approval and Sign-Off

**Plan Status**: Ready for Implementation
**Constitutional Compliance**: Validated against Articles I-V
**Next Steps**:
1. Human review and approval (@am)
2. Create implementation branch: `feature/article-vii-phase1-telemetry`
3. Begin Phase 1A: Schema and Models
4. Execute TDD workflow: tests first, then implementation

**Prepared by**: PlannerAgent (AgencyOS)
**Date**: 2025-10-04
**Review Required**: @am (Chief Architect)

---

*"The constitution that learns from its enforcement becomes the constitution that perfects itself."*
