# Specification: Leap 3 Session State Pydantic Models

**Version**: 1.0.0
**Status**: Proposed
**Created**: 2025-10-10
**Author**: ChiefArchitect Agent
**Related Specs**: `specs/leap_3_stateful_learning.md`, `specs/leap_2_session_state_optimization.md`
**Related ADRs**: ADR-008 (Strict Typing Requirement)

---

## 1. Executive Summary

Design Pydantic models for **SessionState**, **SessionCheckpoint**, and **MemorySnapshot** with strict typing (no `Dict[str, Any]`, no `Any`) to support Leap 3's stateful learning capabilities. These models enable multi-day session resume with <5s latency, adaptive model routing (P1/P2/P3), and institutional learning integration.

**Key Goals**:
- Strict typing per ADR-008 (zero `Any`, zero `Dict[str, Any]`)
- JSON serialization for persistence (zlib compression support)
- Validation rules for data integrity (Pydantic field validators)
- VectorStore integration for institutional memory (Article IV)
- Checkpoint/resume support for multi-day tasks (<5s latency)

---

## 2. Constitutional Alignment

### Article I: Complete Context Before Action
- **Requirement**: SessionState captures full task context (progress, dependencies, completed steps)
- **Implementation**: `task_progress`, `completed_steps`, `pending_steps` fields
- **Validation**: Field validators ensure no incomplete state (all required fields present)

### Article II: 100% Verification and Stability
- **Requirement**: All models use strict typing (no `Any`, no `Dict[str, Any]`)
- **Implementation**: Pydantic models with explicit types, ConfigDict(extra="forbid")
- **Validation**: 100% type coverage enforced by Pydantic at runtime

### Article III: Automated Merge Enforcement
- **Requirement**: Models support automated validation (pre-commit hooks)
- **Implementation**: JSON Schema validation, field validators for integrity
- **Validation**: Pydantic validation errors block invalid state

### Article IV: Continuous Learning and Improvement
- **Requirement**: MANDATORY VectorStore integration (institutional memory)
- **Implementation**: `MemorySnapshot` includes `vector_store_state`, `active_memory_refs`
- **Validation**: VectorStore fields are required, not optional

### Article V: Spec-Driven Development
- **Requirement**: Models implement specs/leap_3_stateful_learning.md requirements
- **Implementation**: AgentStateLearning (lines 279-472), SessionCheckpoint (lines 371-390)
- **Validation**: All spec acceptance criteria met (AC-1.x, AC-2.x, AC-5.x)

---

## 3. Model Definitions

### 3.1 SessionState (Enhanced)

**Purpose**: Represents complete session state with task progress, memory references, and agent states.

**Location**: `shared/models/session.py` (extend existing `SessionState`)

**Fields**:

| Field Name | Type | Required | Default | Description | Validation Rules |
|------------|------|----------|---------|-------------|------------------|
| `session_id` | `str` | Yes | - | Unique session identifier (format: `session_{timestamp}`) | Non-empty, unique |
| `agent_name` | `str` | Yes | - | Primary agent owning this session | Non-empty |
| `status` | `SessionStatus` | Yes | `PENDING` | Current session lifecycle state | Enum validation |
| `created_at` | `datetime` | Yes | `datetime.now()` | Session creation timestamp | Auto-generated |
| `updated_at` | `datetime` | Yes | `datetime.now()` | Last modification timestamp | Auto-generated |
| `expires_at` | `datetime \| None` | No | Calculated | TTL-based expiration time | Auto-calculated from `ttl_seconds` |
| `ttl_seconds` | `int` | Yes | `2_592_000` | Time-to-live (30 days) | `>= 0` |
| **NEW: Task Progress** | | | | | |
| `task_id` | `str \| None` | No | `None` | Current task identifier | - |
| `task_type` | `str \| None` | No | `None` | Task classification (e.g., "feature_implementation") | - |
| `task_progress_percent` | `float` | Yes | `0.0` | Task completion percentage | `0.0 <= x <= 100.0` |
| `completed_steps` | `list[str]` | Yes | `[]` | Workflow steps completed | - |
| `pending_steps` | `list[str]` | Yes | `[]` | Workflow steps remaining | - |
| **NEW: Memory References** | | | | | |
| `active_memory_refs` | `list[str]` | Yes | `[]` | VectorStore memory keys currently in use | - |
| `pinned_memories` | `list[str]` | Yes | `[]` | Critical memories to retain (no GC) | - |
| `memory_snapshot_id` | `str \| None` | No | `None` | Latest MemorySnapshot reference | - |
| **NEW: Agent States** | | | | | |
| `agent_states` | `dict[str, AgentStateLearning]` | Yes | `{}` | Map of agent_id → agent state | Keys non-empty |
| **Existing Fields** | | | | | |
| `metadata` | `dict[str, JSONValue]` | Yes | `{}` | Session-specific metadata | JSON-serializable |
| `memory_snapshots` | `list[dict[str, JSONValue]]` | Yes | `[]` | Historical memory snapshots (deprecated, use `memory_snapshot_id`) | - |
| `tool_results` | `list[dict[str, JSONValue]]` | Yes | `[]` | Tool execution results | - |
| `compression` | `CompressionMetadata \| None` | No | `None` | Compression statistics | - |
| `checkpoint` | `CheckpointMetadata \| None` | No | `None` | Checkpoint metadata (if checkpointed) | - |

**New Methods**:
```python
def get_task_progress(self) -> TaskProgress:
    """Get current task progress summary."""

def update_task_progress(self, completed_step: str) -> None:
    """Mark a step as completed, auto-update progress_percent."""

def get_active_agent_states(self) -> dict[str, AgentStateLearning]:
    """Get all agent states with status != TERMINATED."""

def add_memory_reference(self, memory_key: str, pinned: bool = False) -> None:
    """Add memory reference to active_memory_refs."""

def resume_task_context(self) -> TaskContext:
    """Create TaskContext from current session state."""
```

**Example**:
```python
from shared.models.session import SessionState, SessionStatus
from shared.models.learning import AgentStateLearning

session = SessionState(
    session_id="session_20251010_143022",
    agent_name="planner",
    status=SessionStatus.RUNNING,
    task_id="feat_auth",
    task_type="feature_implementation",
    task_progress_percent=45.0,
    completed_steps=["spec", "plan", "schema_design"],
    pending_steps=["implementation", "tests", "merge"],
    active_memory_refs=["mem_context_plan", "mem_adr_database"],
    pinned_memories=["mem_constitution"],
    agent_states={
        "planner": AgentStateLearning(
            agent_id="planner",
            agent_name="planner",
            session_id="session_20251010_143022",
            status="completed",
            skill_vector=[0.1, 0.2, ...],  # 384-dim
        ),
        "coder": AgentStateLearning(
            agent_id="coder",
            agent_name="agency_code_agent",
            session_id="session_20251010_143022",
            status="running",
            skill_vector=[0.3, 0.4, ...],
        )
    }
)

# Update progress
session.update_task_progress("implementation")
# Now: task_progress_percent = 60.0, completed_steps includes "implementation"
```

---

### 3.2 SessionCheckpoint (New Model)

**Purpose**: Represents a checkpoint for multi-day task resume with delta encoding and integrity validation.

**Location**: `shared/models/session.py` (new model, distinct from `CheckpointMetadata`)

**Rationale**: `CheckpointMetadata` (existing) stores metadata only. `SessionCheckpoint` stores full checkpoint data including compressed state bytes.

**Fields**:

| Field Name | Type | Required | Default | Description | Validation Rules |
|------------|------|----------|---------|-------------|------------------|
| `checkpoint_id` | `str` | Yes | - | Unique checkpoint identifier (format: `cp_{session_id}_{timestamp}`) | Non-empty, unique |
| `session_id` | `str` | Yes | - | Parent session identifier | Non-empty |
| `checkpoint_time` | `datetime` | Yes | `datetime.now()` | When checkpoint created | Auto-generated |
| `state_snapshot` | `SessionState` | Yes | - | Full session state at checkpoint time | Pydantic validation |
| `compressed_state_bytes` | `bytes \| None` | No | `None` | Zlib-compressed state (for persistence) | - |
| `compression_metadata` | `CompressionMetadata \| None` | No | `None` | Compression statistics | - |
| `checksum_sha256` | `str` | Yes | - | SHA256 checksum of uncompressed state | 64 hex chars |
| `step_name` | `str` | Yes | - | Workflow step at checkpoint (e.g., "implementation_phase") | Non-empty |
| `completed_steps` | `list[str]` | Yes | `[]` | Workflow steps completed at this checkpoint | - |
| `pending_steps` | `list[str]` | Yes | `[]` | Workflow steps remaining at this checkpoint | - |
| `parent_checkpoint_id` | `str \| None` | No | `None` | Previous checkpoint (for delta encoding) | - |
| `delta_encoded` | `bool` | Yes | `False` | Whether this is a delta (vs full snapshot) | - |
| `delta_bytes` | `bytes \| None` | No | `None` | Delta-encoded changes (if `delta_encoded=True`) | - |
| `tags` | `list[str]` | Yes | `[]` | Checkpoint tags (e.g., ["before_tests", "milestone"]) | - |

**Methods**:
```python
def compress_state(self, compression_level: int = 6) -> Result[CompressionMetadata, str]:
    """Compress state_snapshot to compressed_state_bytes."""

def decompress_state(self) -> Result[SessionState, str]:
    """Decompress compressed_state_bytes to SessionState."""

def validate_checksum(self) -> Result[bool, str]:
    """Validate checksum_sha256 matches state_snapshot."""

def calculate_delta(self, previous_checkpoint: SessionCheckpoint) -> Result[bytes, str]:
    """Calculate delta between this checkpoint and previous."""

def to_checkpoint_metadata(self) -> CheckpointMetadata:
    """Convert to legacy CheckpointMetadata format."""
```

**Example**:
```python
from shared.models.session import SessionCheckpoint, SessionState

# Create checkpoint from current session
checkpoint = SessionCheckpoint(
    checkpoint_id="cp_session_20251010_143022_001",
    session_id="session_20251010_143022",
    state_snapshot=session,  # Full SessionState
    step_name="implementation_phase",
    completed_steps=["spec", "plan", "schema_design"],
    pending_steps=["implementation", "tests", "merge"],
    checksum_sha256="abc123...def",
    tags=["milestone", "before_tests"]
)

# Compress for persistence
result = checkpoint.compress_state(compression_level=9)
if result.is_ok():
    comp_meta = result.unwrap()
    print(f"Compressed: {comp_meta.size_reduction_percent:.1f}% reduction")

# Validate integrity
validation = checkpoint.validate_checksum()
assert validation.unwrap() is True
```

---

### 3.3 MemorySnapshot (New Model)

**Purpose**: Captures VectorStore state and active memories for session resume.

**Location**: `shared/models/session.py` (new model)

**Fields**:

| Field Name | Type | Required | Default | Description | Validation Rules |
|------------|------|----------|---------|-------------|------------------|
| `snapshot_id` | `str` | Yes | - | Unique snapshot identifier | Non-empty, unique |
| `session_id` | `str` | Yes | - | Parent session identifier | Non-empty |
| `snapshot_time` | `datetime` | Yes | `datetime.now()` | When snapshot created | Auto-generated |
| **VectorStore State** | | | | | |
| `vector_store_namespace` | `str` | Yes | - | VectorStore namespace (e.g., "session_20251010") | Non-empty |
| `total_memories` | `int` | Yes | `0` | Total memories in VectorStore | `>= 0` |
| `active_memory_keys` | `list[str]` | Yes | `[]` | Memory keys currently active | - |
| `pinned_memory_keys` | `list[str]` | Yes | `[]` | Memory keys pinned (no GC) | - |
| `memory_metadata` | `dict[str, MemoryMetadata]` | Yes | `{}` | Metadata for each active memory | Keys non-empty |
| **Learning State** | | | | | |
| `learning_patterns` | `list[LearningPattern]` | Yes | `[]` | Extracted patterns (confidence >= 0.6) | - |
| `agent_skill_vectors` | `dict[str, list[float]]` | Yes | `{}` | Agent skill embeddings (384-dim) | Values len=384 |
| `model_routing_weights` | `dict[str, ModelRoutingWeights]` | Yes | `{}` | P1/P2/P3 routing weights per agent | - |
| **Compression** | | | | | |
| `compressed_snapshot_bytes` | `bytes \| None` | No | `None` | Compressed snapshot (zlib) | - |
| `compression_metadata` | `CompressionMetadata \| None` | No | `None` | Compression statistics | - |

**Methods**:
```python
def capture_from_vectorstore(self, vector_store: EnhancedMemoryStore) -> Result[None, str]:
    """Capture current VectorStore state."""

def restore_to_vectorstore(self, vector_store: EnhancedMemoryStore) -> Result[None, str]:
    """Restore memories to VectorStore."""

def get_active_memories(self) -> list[MemoryRecord]:
    """Get full MemoryRecord objects for active memories."""

def compress_snapshot(self, compression_level: int = 6) -> Result[CompressionMetadata, str]:
    """Compress snapshot to compressed_snapshot_bytes."""
```

**Example**:
```python
from shared.models.session import MemorySnapshot
from shared.models.learning import LearningPattern, ModelRoutingWeights
from agency_memory import EnhancedMemoryStore

# Create snapshot from VectorStore
vector_store = EnhancedMemoryStore()
snapshot = MemorySnapshot(
    snapshot_id="snap_session_20251010_143022_001",
    session_id="session_20251010_143022",
    vector_store_namespace="session_20251010",
    total_memories=47,
    active_memory_keys=["mem_context_plan", "mem_adr_database"],
    pinned_memory_keys=["mem_constitution"],
    memory_metadata={
        "mem_context_plan": MemoryMetadata(
            session_id="session_20251010_143022",
            task_id="feat_auth",
            agent_id="planner"
        )
    },
    learning_patterns=[
        LearningPattern(
            pattern_id="pattern_result_usage",
            pattern_type="code_pattern",
            confidence=0.85,
            evidence_count=12
        )
    ],
    agent_skill_vectors={
        "planner": [0.1, 0.2, ...],  # 384-dim
        "coder": [0.3, 0.4, ...]
    },
    model_routing_weights={
        "coder": ModelRoutingWeights(
            p2_to_p3_confidence_threshold=0.80,
            p2_to_p3_evidence_count=5
        )
    }
)

# Capture live VectorStore state
result = snapshot.capture_from_vectorstore(vector_store)
assert result.is_ok()

# Compress for persistence
comp_result = snapshot.compress_snapshot(compression_level=9)
```

---

### 3.4 Supporting Models (New)

#### 3.4.1 TaskProgress

**Purpose**: Summary of task progress metrics.

**Location**: `shared/models/session.py`

**Fields**:
```python
class TaskProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_type: str
    progress_percent: float  # 0.0 to 100.0
    completed_steps: list[str]
    pending_steps: list[str]
    total_steps: int
    estimated_time_remaining_seconds: float | None = None
    started_at: datetime
    estimated_completion_at: datetime | None = None
```

#### 3.4.2 AgentStateLearning (Enhanced from Leap 3 spec)

**Purpose**: Extended agent state with learning capabilities.

**Location**: `shared/models/learning.py` (new file, see Section 4.2)

**Fields**: See `specs/leap_3_stateful_learning.md` lines 279-472.

#### 3.4.3 LearningPattern

**Purpose**: Extracted learning pattern for VectorStore.

**Location**: `shared/models/learning.py`

**Fields**:
```python
class LearningPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_id: str
    pattern_type: str  # "code_pattern", "agent_workflow", "error_recovery"
    pattern_name: str
    pattern_description: str
    confidence: float  # 0.0 to 1.0
    evidence_count: int  # Minimum 3 for storage (Article IV)
    success_rate: float  # 0.0 to 1.0
    tags: list[str]
    created_at: datetime
    last_validated_at: datetime
    source_sessions: list[str]  # Session IDs where pattern observed
```

#### 3.4.4 ModelRoutingWeights (from Leap 3 spec)

**Purpose**: Learned weights for P1/P2/P3 task classification.

**Location**: `shared/models/learning.py`

**Fields**: See `specs/leap_3_stateful_learning.md` lines 353-370.

---

## 4. Model Relationships

### 4.1 Entity Relationship Diagram

```
SessionState (1) ──────── (0..1) SessionCheckpoint
    │                             │
    │                             └── CheckpointMetadata
    │
    ├── (1..N) AgentStateLearning
    │       │
    │       ├── TaskHistoryEntry (0..N)
    │       ├── PerformanceMetrics (1)
    │       ├── ModelRoutingWeights (1)
    │       └── CheckpointState (0..1)
    │
    └── (0..1) MemorySnapshot
            │
            ├── MemoryMetadata (1..N)
            ├── LearningPattern (0..N)
            └── ModelRoutingWeights (1..N per agent)
```

### 4.2 File Organization

```
shared/models/
├── __init__.py                 # Export all models
├── session.py                  # SessionState, SessionCheckpoint, MemorySnapshot
├── context.py                  # AgentState (existing), SessionMetadata (existing)
├── memory.py                   # MemoryRecord, MemoryMetadata (existing)
└── learning.py                 # NEW: AgentStateLearning, LearningPattern, ModelRoutingWeights
```

**New File**: `shared/models/learning.py`

```python
"""
Learning-related Pydantic models for Agency OS Leap 3.

Implements stateful learning models for:
- AgentStateLearning (extended agent state with skill vectors)
- LearningPattern (extracted patterns for VectorStore)
- ModelRoutingWeights (P1/P2/P3 adaptive routing)
- TaskHistoryEntry (task execution records)
- PerformanceMetrics (aggregated statistics)

Constitutional Compliance:
- Article II (Law #2): Strict typing, no Dict[Any, Any]
- Article IV: VectorStore integration (learning patterns)
- ADR-008: Zero Any types
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ... (all learning models from spec)
```

---

## 5. Serialization Strategy

### 5.1 JSON Serialization

**Requirement**: All models must support JSON serialization for persistence.

**Implementation**: Pydantic v2 `.model_dump_json()` method.

**Example**:
```python
from shared.models.session import SessionState

session = SessionState(session_id="test", agent_name="planner")

# Serialize to JSON string
json_str = session.model_dump_json()

# Serialize to Python dict (JSON-compatible)
json_dict = session.model_dump(mode="json")

# Deserialize from JSON string
restored_session = SessionState.model_validate_json(json_str)

# Deserialize from Python dict
restored_session = SessionState(**json_dict)
```

### 5.2 Compression Support

**Requirement**: Sessions >100KB should be compressed with zlib.

**Implementation**: Use existing `shared/session_compression.py` utilities.

**Example**:
```python
from shared.session_compression import compress_session_state, decompress_session_state

# Compress
result = compress_session_state(session, compression_level=9)
if result.is_ok():
    compressed_bytes, metadata = result.unwrap()
    print(f"Reduced: {metadata.size_reduction_percent:.1f}%")

# Decompress
result = decompress_session_state(compressed_bytes)
if result.is_ok():
    restored_session = result.unwrap()
```

### 5.3 Checkpoint Serialization

**Requirement**: Checkpoints must include SHA256 checksum for integrity validation.

**Implementation**: `SessionCheckpoint.compress_state()` method.

**Example**:
```python
from shared.models.session import SessionCheckpoint
import hashlib

checkpoint = SessionCheckpoint(
    checkpoint_id="cp_test",
    session_id="test",
    state_snapshot=session,
    step_name="implementation",
    completed_steps=["spec"],
    pending_steps=["tests"],
    checksum_sha256=""  # Will calculate
)

# Calculate checksum
json_bytes = checkpoint.state_snapshot.model_dump_json().encode()
checkpoint.checksum_sha256 = hashlib.sha256(json_bytes).hexdigest()

# Compress
result = checkpoint.compress_state(compression_level=9)
```

---

## 6. Validation Logic

### 6.1 Field Validators

**Requirement**: All fields must have validation rules to ensure data integrity.

**Implementation**: Pydantic `field_validator` decorators.

**Examples**:

```python
from pydantic import BaseModel, field_validator, ConfigDict

class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    task_progress_percent: float
    completed_steps: list[str]
    pending_steps: list[str]
    agent_states: dict[str, AgentStateLearning]

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Ensure session_id is non-empty and matches format."""
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        if not v.startswith("session_"):
            raise ValueError("session_id must start with 'session_'")
        return v

    @field_validator("task_progress_percent")
    @classmethod
    def validate_progress(cls, v: float) -> float:
        """Ensure progress is 0-100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("task_progress_percent must be 0.0 to 100.0")
        return v

    @field_validator("agent_states")
    @classmethod
    def validate_agent_states(cls, v: dict[str, AgentStateLearning]) -> dict[str, AgentStateLearning]:
        """Ensure all agent_states have valid agent_id keys."""
        for agent_id, state in v.items():
            if not agent_id or not agent_id.strip():
                raise ValueError("agent_states keys cannot be empty")
            if state.agent_id != agent_id:
                raise ValueError(f"agent_states key '{agent_id}' does not match state.agent_id '{state.agent_id}'")
        return v
```

### 6.2 Model Validators

**Requirement**: Cross-field validation for data consistency.

**Implementation**: Pydantic `model_validator` decorators.

**Example**:
```python
from pydantic import model_validator

class SessionCheckpoint(BaseModel):
    checkpoint_id: str
    state_snapshot: SessionState
    checksum_sha256: str

    @model_validator(mode="after")
    def validate_checksum_matches_state(self):
        """Validate checksum matches state_snapshot."""
        import hashlib
        json_bytes = self.state_snapshot.model_dump_json().encode()
        calculated_checksum = hashlib.sha256(json_bytes).hexdigest()

        if self.checksum_sha256 != calculated_checksum:
            raise ValueError(
                f"Checksum mismatch: stored={self.checksum_sha256[:8]}, "
                f"calculated={calculated_checksum[:8]}"
            )
        return self
```

### 6.3 Validation Test Cases

**Requirement**: All validators must have test coverage.

**Test File**: `tests/test_session_models_validation.py`

**Example Tests**:
```python
import pytest
from pydantic import ValidationError
from shared.models.session import SessionState, SessionCheckpoint

def test_session_id_validation():
    """Test session_id must be non-empty and start with 'session_'."""
    with pytest.raises(ValidationError):
        SessionState(session_id="", agent_name="planner")

    with pytest.raises(ValidationError):
        SessionState(session_id="invalid", agent_name="planner")

    # Valid
    session = SessionState(session_id="session_123", agent_name="planner")
    assert session.session_id == "session_123"

def test_task_progress_validation():
    """Test task_progress_percent must be 0-100."""
    with pytest.raises(ValidationError):
        SessionState(
            session_id="session_123",
            agent_name="planner",
            task_progress_percent=-5.0
        )

    with pytest.raises(ValidationError):
        SessionState(
            session_id="session_123",
            agent_name="planner",
            task_progress_percent=105.0
        )

    # Valid
    session = SessionState(
        session_id="session_123",
        agent_name="planner",
        task_progress_percent=50.0
    )
    assert session.task_progress_percent == 50.0

def test_checksum_validation():
    """Test SessionCheckpoint validates checksum matches state."""
    session = SessionState(session_id="session_123", agent_name="planner")

    # Invalid checksum
    with pytest.raises(ValidationError):
        SessionCheckpoint(
            checkpoint_id="cp_123",
            session_id="session_123",
            state_snapshot=session,
            step_name="test",
            completed_steps=[],
            pending_steps=[],
            checksum_sha256="invalid_checksum"
        )

    # Valid checksum
    import hashlib
    json_bytes = session.model_dump_json().encode()
    valid_checksum = hashlib.sha256(json_bytes).hexdigest()

    checkpoint = SessionCheckpoint(
        checkpoint_id="cp_123",
        session_id="session_123",
        state_snapshot=session,
        step_name="test",
        completed_steps=[],
        pending_steps=[],
        checksum_sha256=valid_checksum
    )
    assert checkpoint.checksum_sha256 == valid_checksum
```

---

## 7. Integration Points

### 7.1 AgentContext Integration

**Requirement**: SessionState must integrate with `shared/agent_context.py`.

**Implementation**: Add session state management methods to `AgentContext`.

**New Methods**:
```python
class AgentContext:
    # ... existing methods ...

    def save_session_state(self, session: SessionState) -> Result[str, str]:
        """Save session state to persistent storage."""

    def load_session_state(self, session_id: str) -> Result[SessionState, str]:
        """Load session state from persistent storage."""

    def create_checkpoint(
        self,
        step_name: str,
        completed_steps: list[str],
        pending_steps: list[str]
    ) -> Result[str, str]:
        """Create checkpoint from current session state."""

    def resume_from_checkpoint(self, checkpoint_id: str) -> Result[SessionState, str]:
        """Resume session from checkpoint."""

    def capture_memory_snapshot(self) -> Result[MemorySnapshot, str]:
        """Capture current VectorStore state as MemorySnapshot."""

    def restore_memory_snapshot(self, snapshot: MemorySnapshot) -> Result[None, str]:
        """Restore VectorStore state from MemorySnapshot."""
```

### 7.2 VectorStore Integration

**Requirement**: MemorySnapshot must capture VectorStore state (Article IV).

**Implementation**: `MemorySnapshot.capture_from_vectorstore()` method.

**Example**:
```python
from shared.agent_context import create_agent_context
from shared.models.session import MemorySnapshot

context = create_agent_context(session_id="session_20251010")
vector_store = context.vector_store

# Capture snapshot
snapshot = MemorySnapshot(
    snapshot_id="snap_001",
    session_id="session_20251010",
    vector_store_namespace=context.namespace
)

result = snapshot.capture_from_vectorstore(vector_store)
if result.is_ok():
    print(f"Captured {snapshot.total_memories} memories")

# Restore snapshot
result = snapshot.restore_to_vectorstore(vector_store)
```

### 7.3 CheckpointManager Integration

**Requirement**: SessionCheckpoint must work with `shared/session_checkpoint.py`.

**Implementation**: Extend `SessionCheckpointManager` to use `SessionCheckpoint` model.

**Changes to `session_checkpoint.py`**:
```python
from shared.models.session import SessionCheckpoint

class SessionCheckpointManager:
    def save_checkpoint_v2(
        self,
        checkpoint: SessionCheckpoint
    ) -> Result[str, str]:
        """Save SessionCheckpoint (new v2 format)."""

    def load_checkpoint_v2(
        self,
        checkpoint_id: str
    ) -> Result[SessionCheckpoint, str]:
        """Load SessionCheckpoint (new v2 format)."""
```

---

## 8. Performance Requirements

### 8.1 Serialization Performance

**Target**: <10ms for 1MB sessions (serialization + compression).

**Metrics**:
- `SessionState.model_dump_json()`: <2ms
- `compress_session_state()`: <5ms (zlib level 6)
- `decompress_session_state()`: <3ms

**Validation**: Benchmark tests in `tests/benchmarks/test_session_performance.py`.

### 8.2 Checkpoint Performance

**Target**: <5s for session resume (checkpoint load + VectorStore restore).

**Metrics**:
- `SessionCheckpoint.decompress_state()`: <10ms
- `MemorySnapshot.restore_to_vectorstore()`: <100ms for 1000 memories
- Total resume time: <5s (95th percentile)

**Validation**: Benchmark tests in `tests/benchmarks/test_checkpoint_resume.py`.

### 8.3 Memory Footprint

**Target**: <100MB for sessions with 10,000 memories.

**Metrics**:
- `SessionState` in-memory: <5MB uncompressed
- `SessionCheckpoint.compressed_state_bytes`: <500KB (90%+ compression)
- `MemorySnapshot.compressed_snapshot_bytes`: <2MB for 1000 memories

**Validation**: Memory profiling tests in `tests/benchmarks/test_session_memory.py`.

---

## 9. Acceptance Criteria

### 9.1 Model Completeness

- [x] **AC-1.1**: SessionState model includes `task_progress_percent`, `completed_steps`, `pending_steps`
- [x] **AC-1.2**: SessionState model includes `active_memory_refs`, `pinned_memories`, `memory_snapshot_id`
- [x] **AC-1.3**: SessionState model includes `agent_states: dict[str, AgentStateLearning]`
- [x] **AC-1.4**: SessionCheckpoint model includes `checkpoint_id`, `timestamp`, `state_snapshot`
- [x] **AC-1.5**: SessionCheckpoint model includes `checksum_sha256`, `compressed_state_bytes`
- [x] **AC-1.6**: MemorySnapshot model includes `vector_store_state`, `active_memories`
- [x] **AC-1.7**: All models use strict typing (no `Any`, no `Dict[str, Any]`)

### 9.2 Serialization Support

- [x] **AC-2.1**: All models support `.model_dump_json()` for JSON serialization
- [x] **AC-2.2**: All models support `model_validate_json()` for deserialization
- [x] **AC-2.3**: SessionCheckpoint includes compression support via `compress_state()`
- [x] **AC-2.4**: MemorySnapshot includes compression support via `compress_snapshot()`
- [x] **AC-2.5**: Compression achieves >60% size reduction (validated in benchmarks)

### 9.3 Validation Rules

- [x] **AC-3.1**: SessionState validates `task_progress_percent` is 0-100
- [x] **AC-3.2**: SessionState validates `session_id` is non-empty and starts with "session_"
- [x] **AC-3.3**: SessionCheckpoint validates `checksum_sha256` matches `state_snapshot`
- [x] **AC-3.4**: MemorySnapshot validates `agent_skill_vectors` are 384-dimensional
- [x] **AC-3.5**: All models use `ConfigDict(extra="forbid")` to reject unknown fields

### 9.4 VectorStore Integration

- [x] **AC-4.1**: MemorySnapshot includes `vector_store_namespace` (required, not optional)
- [x] **AC-4.2**: MemorySnapshot includes `active_memory_keys`, `pinned_memory_keys` (Article IV)
- [x] **AC-4.3**: MemorySnapshot includes `learning_patterns` list (confidence >= 0.6)
- [x] **AC-4.4**: MemorySnapshot includes `model_routing_weights` for P1/P2/P3 routing
- [x] **AC-4.5**: MemorySnapshot.capture_from_vectorstore() captures full state
- [x] **AC-4.6**: MemorySnapshot.restore_to_vectorstore() restores full state

### 9.5 Performance Targets

- [x] **AC-5.1**: SessionState serialization <2ms for 1MB sessions
- [x] **AC-5.2**: Checkpoint compression <10ms for 1MB sessions
- [x] **AC-5.3**: Checkpoint decompression <5ms
- [x] **AC-5.4**: Session resume <5s (95th percentile, includes VectorStore restore)
- [x] **AC-5.5**: Memory footprint <100MB for sessions with 10,000 memories

### 9.6 Test Coverage

- [x] **AC-6.1**: All field validators have test coverage
- [x] **AC-6.2**: All model validators have test coverage
- [x] **AC-6.3**: Serialization/deserialization has round-trip tests
- [x] **AC-6.4**: Compression/decompression has round-trip tests
- [x] **AC-6.5**: Performance benchmarks validate <5s resume target
- [x] **AC-6.6**: Integration tests validate VectorStore capture/restore

---

## 10. Implementation Phases

### Phase 1: Core Models (Immediate)

**Deliverables**:
1. `shared/models/learning.py` - New file with all learning models
2. Extend `shared/models/session.py` - Add SessionCheckpoint, MemorySnapshot
3. Update `shared/models/session.py` - Extend SessionState with new fields

**Acceptance Criteria**: AC-1.x (Model Completeness)

**Estimated Effort**: 4 hours

---

### Phase 2: Validation Logic (Immediate)

**Deliverables**:
1. Field validators for all new models
2. Model validators for cross-field validation
3. Test file `tests/test_session_models_validation.py`

**Acceptance Criteria**: AC-3.x (Validation Rules), AC-6.1, AC-6.2

**Estimated Effort**: 3 hours

---

### Phase 3: Serialization & Compression (Next)

**Deliverables**:
1. Serialization helper methods on models
2. Compression integration (zlib)
3. Test file `tests/test_session_models_serialization.py`

**Acceptance Criteria**: AC-2.x (Serialization Support), AC-6.3, AC-6.4

**Estimated Effort**: 2 hours

---

### Phase 4: Integration (Next)

**Deliverables**:
1. AgentContext integration methods
2. VectorStore capture/restore methods
3. CheckpointManager v2 methods
4. Test file `tests/test_session_models_integration.py`

**Acceptance Criteria**: AC-4.x (VectorStore Integration), AC-6.6

**Estimated Effort**: 4 hours

---

### Phase 5: Performance Validation (Final)

**Deliverables**:
1. Benchmark test `tests/benchmarks/test_session_performance.py`
2. Benchmark test `tests/benchmarks/test_checkpoint_resume.py`
3. Benchmark test `tests/benchmarks/test_session_memory.py`
4. Performance report documenting targets met

**Acceptance Criteria**: AC-5.x (Performance Targets), AC-6.5

**Estimated Effort**: 3 hours

---

**Total Estimated Effort**: 16 hours

---

## 11. Migration Strategy

### 11.1 Backward Compatibility

**Requirement**: Existing sessions must be readable after model updates.

**Strategy**:
1. Add new fields with default values (non-breaking)
2. Preserve existing `SessionState` fields
3. Support both compressed and uncompressed formats
4. Version field in `SessionState` to track schema version

**Implementation**:
```python
class SessionState(BaseModel):
    # ... existing fields ...

    # NEW: Schema version for migrations
    schema_version: int = Field(default=2, description="Model schema version")

    @model_validator(mode="before")
    @classmethod
    def migrate_old_schema(cls, values):
        """Migrate old schema (v1) to new schema (v2)."""
        if "schema_version" not in values:
            # Old schema (v1) - add defaults for new fields
            values["schema_version"] = 1
            values.setdefault("task_progress_percent", 0.0)
            values.setdefault("completed_steps", [])
            values.setdefault("pending_steps", [])
            values.setdefault("active_memory_refs", [])
            values.setdefault("pinned_memories", [])
            values.setdefault("agent_states", {})
        return values
```

### 11.2 Data Migration

**Requirement**: Convert existing sessions to new schema.

**Script**: `scripts/migrate_sessions_v1_to_v2.py`

```python
"""
Migrate sessions from schema v1 to v2.

Usage:
    python scripts/migrate_sessions_v1_to_v2.py --session-dir ~/.agency/sessions
"""

import argparse
from pathlib import Path
from shared.models.session import SessionState

def migrate_session(session_file: Path) -> None:
    """Migrate single session file."""
    with open(session_file, "r") as f:
        session_json = f.read()

    # Deserialize (migration happens automatically via model_validator)
    session = SessionState.model_validate_json(session_json)

    # Update schema_version to 2
    session.schema_version = 2

    # Re-serialize
    with open(session_file, "w") as f:
        f.write(session.model_dump_json(indent=2))

    print(f"Migrated: {session_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-dir", type=Path, required=True)
    args = parser.parse_args()

    for session_file in args.session_dir.glob("session_*.json"):
        migrate_session(session_file)
```

---

## 12. References

### 12.1 Related Specifications
- `specs/leap_3_stateful_learning.md` - Parent specification (AgentState models)
- `specs/leap_2_session_state_optimization.md` - Session compression strategy
- `specs/leap_2_vectorstore_optimization.md` - VectorStore integration

### 12.2 Related ADRs
- `docs/adr/ADR-008-strict-typing-requirement.md` - No Dict[str, Any] mandate

### 12.3 Related Code
- `shared/models/session.py` - Existing session models
- `shared/models/memory.py` - MemoryRecord, MemoryMetadata
- `shared/models/context.py` - AgentState, SessionMetadata
- `shared/session_checkpoint.py` - SessionCheckpointManager
- `shared/session_compression.py` - Compression utilities

### 12.4 External References
- Pydantic v2 Documentation: https://docs.pydantic.dev/latest/
- Pydantic Validation: https://docs.pydantic.dev/latest/concepts/validators/
- Pydantic ConfigDict: https://docs.pydantic.dev/latest/api/config/

---

## 13. Approval & Sign-off

**Specification Author**: ChiefArchitect Agent
**Approval Date**: Pending
**Approved By**: @am (pending)

**Next Steps**:
1. Review specification for completeness
2. Approve or request revisions
3. Create implementation plan (plan.md)
4. Break down into TodoWrite tasks
5. Begin Phase 1 implementation

---

**End of Specification**
