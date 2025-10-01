# Implementation Plan: Ambient Intelligence System

**Plan ID**: plan-ambient-intelligence-system
**Status**: Draft
**Created**: 2025-10-01
**Priority**: HIGH
**Source**: Next Agent Mission Brief - Phase 1 Autonomous Event Detection
**Estimated Effort**: 32-40 hours (4-5 working days with parallel execution)

---

## 1. Overview

### 1.1 Specification Reference

**Note**: This plan is created proactively based on NEXT_AGENT_MISSION.md requirements. Formal specification and ADR should be created first by Chief Architect:
- **Spec**: `specs/ambient_intelligence_system.md` (to be created)
- **ADR**: `docs/adr/ADR-016-ambient-listener-architecture.md` (to be created)

### 1.2 Goals and Objectives

**Primary Goal**: Enable Trinity Protocol WITNESS agent to monitor ambient audio sources (developer conversations, meetings, voice memos) and extract actionable insights for autonomous system improvement.

**Objectives**:
1. Capture audio from system microphone with privacy controls
2. Convert speech to text using local Whisper.cpp (cost-free, privacy-preserving)
3. Stream text events to Trinity message bus for WITNESS consumption
4. Integrate with existing WITNESS pattern detection for user intent signals
5. Implement comprehensive safety controls (pause, delete, opt-in)

**Key Constraints**:
- **Privacy-first**: All processing local, explicit user consent required
- **Cost-free**: Use local Whisper.cpp model (no API costs)
- **Constitutional compliance**: All 5 articles, especially Article I (complete context)
- **Non-intrusive**: Background operation, minimal CPU/memory impact

### 1.3 Success Criteria

1. **Audio Capture**: Continuous microphone monitoring with configurable silence detection
2. **Speech Recognition**: Real-time transcription with <5 second latency
3. **WITNESS Integration**: Text events flow to `personal_context_stream` queue
4. **Pattern Detection**: WITNESS detects user intent patterns (feature requests, frustrations)
5. **Safety Controls**: User can pause/resume/delete at any time
6. **Performance**: <10% CPU usage, <500MB memory footprint
7. **Constitutional Compliance**: 100% adherence to all 5 articles
8. **Test Coverage**: >90% with integration tests validating full pipeline

---

## 2. Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ambient Intelligence System                   │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ Audio Capture│          │   Whisper    │          │    Text      │
│    Module    │─────────▶│  Transcriber │─────────▶│   Stream     │
│              │          │              │          │   Pipeline   │
└──────────────┘          └──────────────┘          └──────────────┘
        │                                                    │
        │                                                    ▼
        │                                          ┌──────────────┐
        │                                          │   Message    │
        │                                          │     Bus      │
        │                                          │ (personal_   │
        │                                          │  context_    │
        │                                          │  stream)     │
        │                                          └──────────────┘
        │                                                    │
        │                                                    ▼
        │                                          ┌──────────────┐
        │                                          │   WITNESS    │
        │                                          │    Agent     │
        │                                          │  (existing)  │
        │                                          └──────────────┘
        │                                                    │
        │                                                    ▼
        │                                          ┌──────────────┐
        │                                          │ improvement_ │
        │                                          │    queue     │
        │                                          └──────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Safety Controls                              │
│  - Privacy Manager (consent, pause/resume, data deletion)        │
│  - Sensitivity Filter (PII detection, profanity, credentials)    │
│  - Audit Log (what was captured, when, transcription status)     │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

**Phase 1: Audio Capture**
```
Microphone → PyAudio → Audio Buffer → VAD (Voice Activity Detection) → Audio Chunks
                                              │
                                              └─ (silence detected) → Skip chunk
```

**Phase 2: Transcription**
```
Audio Chunks → Whisper.cpp (local) → Text Segments → Confidence Check
                                                            │
                                                            ├─ (low confidence) → Mark uncertain
                                                            └─ (high confidence) → Proceed
```

**Phase 3: Privacy & Safety**
```
Text Segments → PII Detection → Sensitivity Filter → User Consent Check
                      │                  │                    │
                      │                  │                    └─ (no consent) → Drop
                      │                  └─ (sensitive) → Redact or Drop
                      └─ (PII found) → Redact or Flag
```

**Phase 4: Event Publishing**
```
Filtered Text → Event Formatter → Message Bus → personal_context_stream → WITNESS
                                                                              │
                                                                              ▼
                                                                    Pattern Detection
                                                                              │
                                                                              ├─ user_intent: feature_request
                                                                              ├─ user_intent: workflow_bottleneck
                                                                              └─ user_intent: frustration_signal
```

### 2.3 Component Specifications

#### AudioCaptureModule
- **Responsibility**: Capture audio from system microphone
- **Technology**: PyAudio + webrtcvad for VAD
- **Output**: Audio chunks (16kHz, mono, 16-bit PCM)
- **Controls**: Start, stop, pause, resume
- **Configuration**: Device selection, sample rate, chunk size

#### WhisperTranscriber
- **Responsibility**: Convert audio to text
- **Technology**: whisper.cpp Python bindings (local inference)
- **Model**: `base.en` (74MB, 0.15s RTF on CPU)
- **Output**: Text segments with timestamps and confidence scores
- **Fallback**: `tiny.en` if base too slow (39MB, 0.1s RTF)

#### TextStreamPipeline
- **Responsibility**: Process and publish transcriptions
- **Functions**: Batching, deduplication, formatting
- **Output**: Events to message bus
- **Buffering**: 5-second window for sentence completion

#### SafetyControls
- **Responsibility**: Privacy and security enforcement
- **Components**:
  - PrivacyManager: Consent tracking, pause/resume, data deletion
  - SensitivityFilter: PII detection (presidio), keyword blocking
  - AuditLog: Capture log with timestamps and actions

### 2.4 Data Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# Audio Chunk
@dataclass
class AudioChunk:
    """Raw audio data chunk."""
    data: bytes
    sample_rate: int
    timestamp: datetime
    duration_ms: int
    has_speech: bool  # From VAD

# Transcription Segment
class TranscriptionSegment(BaseModel):
    """Whisper transcription output."""
    text: str = Field(..., min_length=1)
    start_time: float
    end_time: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    language: str = "en"

# Ambient Event (for message bus)
class AmbientEvent(BaseModel):
    """Event published to personal_context_stream."""
    event_type: str = "ambient_speech"
    text: str
    timestamp: str  # ISO8601
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    session_id: str
    redacted: bool = False

# Privacy Settings
class PrivacySettings(BaseModel):
    """User privacy configuration."""
    consent_given: bool = False
    recording_enabled: bool = False
    retain_audio: bool = False
    retain_transcriptions: bool = True
    pii_redaction_enabled: bool = True
    blocked_keywords: List[str] = Field(default_factory=list)
    auto_pause_on_keywords: List[str] = Field(default_factory=list)
```

### 2.5 Integration Points

**Trinity Protocol Integration**:
- **Message Bus**: Publish to `personal_context_stream` queue
- **WITNESS Agent**: Consume ambient events (no code changes needed)
- **Pattern Store**: Store detected user intent patterns
- **Cost Tracker**: No LLM costs (local Whisper), track compute time

**Existing Infrastructure**:
- **AgentContext**: Store privacy settings and audit logs
- **EnhancedMemoryStore**: Optional transcription persistence
- **Constitutional Enforcement**: Validate against all 5 articles

---

## 3. Task Breakdown

### Phase 1: Foundation & Setup (8 hours)

#### TASK-001: Environment Setup & Dependencies
**Priority**: CRITICAL
**Complexity**: Low
**Effort**: 2 hours
**Dependencies**: None

**Sub-tasks**:
- [ ] TASK-001.1: Install whisper.cpp with Python bindings
  - Research: Compare whisper.cpp vs OpenAI Whisper Python
  - Install: `pip install whisper-cpp-python` or build from source
  - Verify: Test basic transcription on sample audio
  - **Acceptance**: Whisper model loads and transcribes test audio in <1s

- [ ] TASK-001.2: Install audio capture dependencies
  - Install: `pip install pyaudio webrtcvad`
  - Handle: Platform-specific issues (PortAudio on macOS)
  - Test: Record 5-second audio clip from default mic
  - **Acceptance**: PyAudio can capture audio without errors

- [ ] TASK-001.3: Download Whisper models
  - Download: `base.en` and `tiny.en` models
  - Location: `~/.cache/whisper/` or project directory
  - Validate: Model checksums match official releases
  - **Acceptance**: Both models downloaded and loadable

#### TASK-002: Project Structure & Boilerplate
**Priority**: CRITICAL
**Complexity**: Low
**Effort**: 2 hours
**Dependencies**: TASK-001

**Sub-tasks**:
- [ ] TASK-002.1: Create ambient_intelligence module structure
  ```
  ambient_intelligence/
  ├─ __init__.py
  ├─ audio_capture.py
  ├─ whisper_transcriber.py
  ├─ text_pipeline.py
  ├─ safety_controls.py
  ├─ ambient_agent.py (main orchestrator)
  └─ config.py
  ```
  - **Acceptance**: Module imports successfully

- [ ] TASK-002.2: Define Pydantic models
  - Create: `models.py` with AudioChunk, TranscriptionSegment, AmbientEvent
  - Validate: All models pass mypy strict type checking
  - Test: Instantiate each model with valid/invalid data
  - **Acceptance**: 100% type coverage, validation tests pass

- [ ] TASK-002.3: Create configuration system
  - File: `ambient_intelligence/config.py`
  - Settings: Model selection, audio params, privacy defaults
  - Source: Environment variables + YAML config file
  - **Acceptance**: Config loads from .env and config.yaml

#### TASK-003: Specifications & ADR Creation
**Priority**: HIGH
**Complexity**: Medium
**Effort**: 4 hours
**Dependencies**: None (can run parallel with TASK-001/002)
**Agent**: ChiefArchitectAgent

**Sub-tasks**:
- [ ] TASK-003.1: Create formal specification
  - File: `specs/ambient_intelligence_system.md`
  - Sections: Goals, Non-Goals, Personas, Acceptance Criteria
  - Template: Use `specs/TEMPLATE.md`
  - **Acceptance**: Spec follows spec-kit methodology, approved by user

- [ ] TASK-003.2: Create ADR for architecture decisions
  - File: `docs/adr/ADR-016-ambient-listener-architecture.md`
  - Decisions: Local vs cloud, Whisper.cpp vs API, privacy model
  - Rationale: Cost, privacy, performance, constitutional compliance
  - **Acceptance**: ADR documents key decisions with trade-offs

- [ ] TASK-003.3: Document privacy & security model
  - Section: Privacy-first design principles
  - Analysis: GDPR/CCPA considerations, data retention
  - Controls: Consent mechanism, right to deletion
  - **Acceptance**: Privacy model documented and defensible

---

### Phase 2: Core Components (12 hours)

#### TASK-004: Audio Capture Module (TDD)
**Priority**: CRITICAL
**Complexity**: Medium
**Effort**: 4 hours
**Dependencies**: TASK-001, TASK-002

**Sub-tasks**:
- [ ] TASK-004.1: Write tests for AudioCaptureModule
  - Test: Device enumeration and selection
  - Test: Audio recording start/stop/pause
  - Test: VAD detection (speech vs silence)
  - Test: Chunk size and sample rate configuration
  - **Acceptance**: Tests defined for all public methods

- [ ] TASK-004.2: Implement AudioCaptureModule
  - Class: `AudioCaptureModule(device_index, sample_rate, chunk_duration)`
  - Methods: `start()`, `stop()`, `pause()`, `resume()`, `get_chunk()`
  - VAD: Integrate webrtcvad for speech detection
  - Threading: Use asyncio for non-blocking capture
  - **Acceptance**: All tests pass, captures audio in background

- [ ] TASK-004.3: Add error handling and recovery
  - Handle: Device not found, permission denied, buffer overflow
  - Retry: Automatic reconnection on device disconnect
  - Logging: Debug logs for audio levels and VAD decisions
  - **Acceptance**: Graceful handling of all error scenarios

#### TASK-005: Whisper Transcriber Module (TDD)
**Priority**: CRITICAL
**Complexity**: Medium
**Effort**: 4 hours
**Dependencies**: TASK-001, TASK-002

**Sub-tasks**:
- [ ] TASK-005.1: Write tests for WhisperTranscriber
  - Test: Model loading (base.en, tiny.en)
  - Test: Audio transcription with confidence scores
  - Test: Language detection
  - Test: Timestamp alignment
  - Mock: Use pre-recorded audio samples
  - **Acceptance**: Tests cover happy path and edge cases

- [ ] TASK-005.2: Implement WhisperTranscriber
  - Class: `WhisperTranscriber(model_name, device)`
  - Methods: `transcribe(audio_chunk) -> TranscriptionSegment`
  - Async: Non-blocking transcription with asyncio
  - Performance: Measure RTF (real-time factor)
  - **Acceptance**: All tests pass, transcription accuracy >90%

- [ ] TASK-005.3: Add confidence filtering and quality checks
  - Filter: Drop segments with confidence <0.5
  - Hallucination: Detect repeated phrases (Whisper artifact)
  - Fallback: Switch to tiny model if base too slow
  - **Acceptance**: Quality checks prevent garbage output

#### TASK-006: Text Stream Pipeline (TDD)
**Priority**: HIGH
**Complexity**: Medium
**Effort**: 4 hours
**Dependencies**: TASK-002, TASK-005

**Sub-tasks**:
- [ ] TASK-006.1: Write tests for TextStreamPipeline
  - Test: Sentence batching (combine short segments)
  - Test: Deduplication (remove repeated text)
  - Test: Event formatting for message bus
  - Test: Buffering and flush behavior
  - **Acceptance**: Tests validate text processing logic

- [ ] TASK-006.2: Implement TextStreamPipeline
  - Class: `TextStreamPipeline(buffer_seconds, min_confidence)`
  - Methods: `add_segment()`, `flush()`, `get_events()`
  - Logic: Buffer segments for N seconds, combine, deduplicate
  - Output: `AmbientEvent` objects ready for message bus
  - **Acceptance**: All tests pass, pipeline processes text correctly

- [ ] TASK-006.3: Integrate with Trinity message bus
  - Publish: Send events to `personal_context_stream` queue
  - Format: Match existing WITNESS event schema
  - Correlation: Generate unique session_id per capture session
  - **Acceptance**: Events successfully consumed by WITNESS

---

### Phase 3: Safety & Privacy (8 hours)

#### TASK-007: Privacy Manager (TDD)
**Priority**: CRITICAL
**Complexity**: High
**Effort**: 4 hours
**Dependencies**: TASK-002

**Sub-tasks**:
- [ ] TASK-007.1: Write tests for PrivacyManager
  - Test: Consent workflow (request, grant, revoke)
  - Test: Recording state management (enabled/paused)
  - Test: Data deletion (audio, transcriptions, events)
  - Test: Privacy settings persistence
  - **Acceptance**: Tests cover all privacy operations

- [ ] TASK-007.2: Implement PrivacyManager
  - Class: `PrivacyManager(settings_store)`
  - Methods: `request_consent()`, `grant()`, `revoke()`, `delete_all()`
  - Storage: Persist settings in AgentContext or local file
  - UI: CLI prompts for consent with clear explanations
  - **Acceptance**: All tests pass, consent workflow functional

- [ ] TASK-007.3: Add audit logging
  - Log: All capture sessions (start/stop, duration, word count)
  - Log: Privacy actions (consent granted/revoked, data deleted)
  - Storage: SQLite database or JSON file
  - Query: Retrieve audit log for specific session
  - **Acceptance**: Full audit trail of privacy-related actions

#### TASK-008: Sensitivity Filter (TDD)
**Priority**: HIGH
**Complexity**: High
**Effort**: 4 hours
**Dependencies**: TASK-002, TASK-006

**Sub-tasks**:
- [ ] TASK-008.1: Write tests for SensitivityFilter
  - Test: PII detection (emails, phone numbers, SSN, credit cards)
  - Test: Keyword blocking (passwords, API keys, profanity)
  - Test: Redaction modes (replace, drop, flag)
  - Test: Auto-pause on sensitive keywords
  - **Acceptance**: Tests validate all filter rules

- [ ] TASK-008.2: Implement PII detection
  - Library: Microsoft Presidio or spaCy NER
  - Entities: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD
  - Action: Redact with `[REDACTED]` or drop segment entirely
  - Performance: <100ms per segment
  - **Acceptance**: PII detection accuracy >95% on test cases

- [ ] TASK-008.3: Implement keyword filtering
  - Patterns: Regex for "password", "api key", "secret", etc.
  - Custom: User-defined blocked keywords
  - Action: Auto-pause recording when detected
  - Notification: Alert user of blocked content
  - **Acceptance**: Keyword blocking prevents sensitive data capture

---

### Phase 4: Integration & Orchestration (6 hours)

#### TASK-009: Ambient Agent Orchestrator (TDD)
**Priority**: HIGH
**Complexity**: High
**Effort**: 4 hours
**Dependencies**: TASK-004, TASK-005, TASK-006, TASK-007, TASK-008

**Sub-tasks**:
- [ ] TASK-009.1: Write tests for AmbientAgent
  - Test: End-to-end pipeline (audio → text → message bus)
  - Test: State management (stopped, recording, paused)
  - Test: Privacy enforcement (consent required)
  - Test: Error recovery (device disconnect, model crash)
  - **Acceptance**: Integration tests validate full system

- [ ] TASK-009.2: Implement AmbientAgent orchestrator
  - Class: `AmbientAgent(message_bus, privacy_manager, config)`
  - Methods: `start()`, `stop()`, `pause()`, `resume()`, `get_status()`
  - Flow: AudioCapture → Whisper → Pipeline → Privacy → MessageBus
  - Async: Use asyncio to coordinate all components
  - **Acceptance**: All tests pass, agent runs continuously

- [ ] TASK-009.3: Add monitoring and health checks
  - Metrics: Audio chunks/sec, transcription latency, event rate
  - Health: Check each component status (is_healthy)
  - Dashboard: CLI command to show live stats
  - **Acceptance**: Health checks detect component failures

#### TASK-010: WITNESS Integration Validation
**Priority**: HIGH
**Complexity**: Medium
**Effort**: 2 hours
**Dependencies**: TASK-009

**Sub-tasks**:
- [ ] TASK-010.1: Test WITNESS pattern detection
  - Scenario: Ambient speech contains "I need to automate this task"
  - Expected: WITNESS detects `user_intent: feature_request`
  - Validation: Check improvement_queue for signal
  - **Acceptance**: WITNESS correctly classifies ambient events

- [ ] TASK-010.2: Validate end-to-end flow
  - Test: Speak test phrases → WITNESS → ARCHITECT
  - Verify: Patterns detected and persisted to pattern_store
  - Metrics: Latency from speech to signal (<30 seconds)
  - **Acceptance**: Full Trinity pipeline processes ambient input

- [ ] TASK-010.3: Document integration patterns
  - Guide: How to configure WITNESS for ambient events
  - Examples: Sample ambient events and expected patterns
  - Troubleshooting: Common issues and solutions
  - **Acceptance**: Documentation enables user configuration

---

### Phase 5: CLI & User Experience (4 hours)

#### TASK-011: CLI Commands & Control Interface
**Priority**: MEDIUM
**Complexity**: Low
**Effort**: 2 hours
**Dependencies**: TASK-009

**Sub-tasks**:
- [ ] TASK-011.1: Implement CLI commands
  ```bash
  agency ambient start     # Start ambient listener
  agency ambient stop      # Stop ambient listener
  agency ambient pause     # Pause recording
  agency ambient resume    # Resume recording
  agency ambient status    # Show current status
  agency ambient consent   # Manage consent
  agency ambient logs      # Show audit logs
  agency ambient delete    # Delete all data
  ```
  - Framework: Click or Typer for CLI
  - Output: Rich formatting with status colors
  - **Acceptance**: All commands functional with help text

- [ ] TASK-011.2: Add interactive consent workflow
  - Prompt: Clear explanation of what data is captured
  - Options: Grant, deny, view details, configure settings
  - Confirmation: Require explicit "yes" to enable
  - **Acceptance**: User cannot accidentally enable without consent

- [ ] TASK-011.3: Create status dashboard
  - Display: Current state, session duration, events published
  - Live: Update every second with live metrics
  - Controls: Keyboard shortcuts for pause/resume
  - **Acceptance**: Dashboard provides clear system visibility

#### TASK-012: Documentation & User Guide
**Priority**: MEDIUM
**Complexity**: Low
**Effort**: 2 hours
**Dependencies**: TASK-011

**Sub-tasks**:
- [ ] TASK-012.1: Write user guide
  - File: `docs/AMBIENT_INTELLIGENCE_GUIDE.md`
  - Sections: Setup, Usage, Privacy, Troubleshooting
  - Examples: Common workflows and use cases
  - **Acceptance**: User can set up system from guide alone

- [ ] TASK-012.2: Create privacy FAQ
  - Questions: What data is stored? Where? For how long?
  - Answers: Clear, non-technical explanations
  - Rights: How to view, export, delete data
  - **Acceptance**: Privacy concerns addressed transparently

- [ ] TASK-012.3: Add troubleshooting guide
  - Issues: No audio, poor transcription, high CPU
  - Solutions: Step-by-step debugging procedures
  - Diagnostics: Commands to check system health
  - **Acceptance**: Common problems have documented solutions

---

### Phase 6: Testing & Validation (4 hours)

#### TASK-013: Comprehensive Test Suite
**Priority**: CRITICAL
**Complexity**: Medium
**Effort**: 3 hours
**Dependencies**: All previous tasks

**Sub-tasks**:
- [ ] TASK-013.1: Unit tests for all modules
  - Coverage: AudioCapture, Whisper, Pipeline, Safety, Agent
  - Target: >90% code coverage
  - Mocking: External dependencies (PyAudio, Whisper)
  - **Acceptance**: All unit tests pass, coverage >90%

- [ ] TASK-013.2: Integration tests for full pipeline
  - Test: Audio file → transcription → message bus → WITNESS
  - Test: Privacy enforcement blocks non-consented capture
  - Test: Sensitivity filter redacts PII
  - Test: Error recovery (component crash, restart)
  - **Acceptance**: Integration tests validate real system behavior

- [ ] TASK-013.3: Performance tests
  - Measure: CPU usage, memory footprint, latency
  - Target: <10% CPU, <500MB RAM, <5s latency
  - Load: 1-hour continuous capture test
  - **Acceptance**: Performance within specified limits

#### TASK-014: Constitutional Compliance Validation
**Priority**: CRITICAL
**Complexity**: Low
**Effort**: 1 hour
**Dependencies**: TASK-013

**Sub-tasks**:
- [ ] TASK-014.1: Article I validation (Complete Context)
  - Verify: All audio chunks processed before transcription
  - Verify: No premature termination on errors
  - Test: Timeout handling retries correctly
  - **Acceptance**: No action taken without complete audio context

- [ ] TASK-014.2: Article II validation (100% Verification)
  - Verify: All components have comprehensive tests
  - Verify: Test pass rate 100% before merge
  - CI: Add ambient tests to pipeline
  - **Acceptance**: Zero test failures in CI

- [ ] TASK-014.3: Article IV validation (Continuous Learning)
  - Verify: Detected patterns stored in PersistentStore
  - Verify: Cross-session pattern recognition works
  - Test: Pattern persistence across ambient agent restarts
  - **Acceptance**: Learning persists and improves over time

---

## 4. Testing Strategy

### 4.1 Unit Tests

**Modules to Test**:
- `audio_capture.py`: Device enumeration, recording, VAD
- `whisper_transcriber.py`: Model loading, transcription, confidence
- `text_pipeline.py`: Batching, deduplication, event formatting
- `safety_controls.py`: Privacy manager, PII detection, keyword filtering
- `ambient_agent.py`: State management, component coordination

**Mocking Strategy**:
- PyAudio: Mock audio stream with pre-recorded samples
- Whisper: Mock transcription with deterministic outputs
- Message Bus: Mock publish calls, verify event format

**Coverage Target**: >90% line coverage

### 4.2 Integration Tests

**Test Scenarios**:

1. **End-to-End Happy Path**
   - Input: Pre-recorded audio file with clear speech
   - Expected: Text events published to message bus
   - Validation: WITNESS consumes and detects patterns

2. **Privacy Enforcement**
   - Input: Attempt to start without consent
   - Expected: Recording blocked, error message shown
   - Validation: No audio captured or transcribed

3. **PII Redaction**
   - Input: Speech containing "my email is user@example.com"
   - Expected: Transcription redacted to "my email is [REDACTED]"
   - Validation: No PII reaches message bus

4. **Error Recovery**
   - Input: Disconnect audio device mid-capture
   - Expected: Agent pauses, retries on reconnect
   - Validation: No data loss, graceful degradation

5. **WITNESS Pattern Detection**
   - Input: "I really need to automate this repetitive task"
   - Expected: WITNESS detects `user_intent: workflow_bottleneck`
   - Validation: Signal published to improvement_queue

### 4.3 System Tests

**24-Hour Continuous Operation Test**:
```bash
# Start ambient agent with 24h runtime limit
python trinity_protocol/run_ambient_test.py --duration 24 --budget 0.00

# Monitor
watch -n 5 "python trinity_protocol/cost_dashboard.py --ambient"

# Validate
python trinity_protocol/validate_ambient_session.py
```

**Success Criteria**:
- Zero crashes over 24 hours
- CPU usage stable <10%
- Memory usage stable <500MB
- >100 ambient events published
- >10 user intent patterns detected
- All privacy controls functional

### 4.4 Performance Tests

**Benchmarks**:
- **Audio Capture**: Should handle 16kHz continuous stream without buffer overflow
- **Transcription**: RTF (real-time factor) <0.5 (transcribe 1s audio in <0.5s)
- **End-to-End Latency**: <5 seconds from speech to message bus
- **CPU Usage**: <10% average on modern hardware (M1/M2 Mac, Intel i7)
- **Memory Footprint**: <500MB including Whisper model

**Load Test**:
- Simulate 8-hour workday of ambient capture
- Measure: Peak CPU, peak memory, event throughput
- Validate: No memory leaks, no performance degradation

---

## 5. Implementation Order

### Critical Path (Parallel Execution Opportunities)

**Week 1: Foundation (Days 1-2)**
```
[PARALLEL]
├─ TASK-001: Dependencies (Agent A)
├─ TASK-002: Project Structure (Agent B)
└─ TASK-003: Specs & ADR (ChiefArchitect)

[SEQUENTIAL after Week 1]
└─ Review and approval gate
```

**Week 2: Core Components (Days 3-5)**
```
[PARALLEL]
├─ TASK-004: Audio Capture (Agent A)
├─ TASK-005: Whisper Transcriber (Agent B)
└─ TASK-006: Text Pipeline (Agent C)

[SEQUENTIAL after Week 2]
└─ Integration checkpoint
```

**Week 3: Safety & Integration (Days 6-8)**
```
[PARALLEL]
├─ TASK-007: Privacy Manager (Agent A)
└─ TASK-008: Sensitivity Filter (Agent B)

[SEQUENTIAL after privacy complete]
├─ TASK-009: Ambient Agent Orchestrator
├─ TASK-010: WITNESS Integration
└─ Integration validation gate
```

**Week 4: Polish & Testing (Days 9-10)**
```
[PARALLEL]
├─ TASK-011: CLI Commands (Agent A)
├─ TASK-012: Documentation (Agent B)
└─ TASK-013: Test Suite (TestGenerator + QualityEnforcer)

[SEQUENTIAL after tests]
└─ TASK-014: Constitutional Compliance
```

**Final Gate**: 24-hour continuous operation test

---

## 6. Quality Gates

### Gate 1: Foundation Complete (After Phase 1)

**Checklist**:
- [ ] Whisper models downloaded and functional
- [ ] PyAudio captures audio from microphone
- [ ] Project structure follows Agency conventions
- [ ] Formal spec and ADR created and approved
- [ ] All types defined with Pydantic models
- [ ] Configuration system loads from .env

**Exit Criteria**: All foundation tasks 100% complete, ChiefArchitect approval

### Gate 2: Core Components Complete (After Phase 2)

**Checklist**:
- [ ] AudioCaptureModule tests 100% pass
- [ ] WhisperTranscriber tests 100% pass
- [ ] TextStreamPipeline tests 100% pass
- [ ] All modules have >90% code coverage
- [ ] Integration test: Audio file → text events works
- [ ] No type errors (mypy --strict passes)

**Exit Criteria**: All core component tests pass, QualityEnforcer approval

### Gate 3: Safety Complete (After Phase 3)

**Checklist**:
- [ ] PrivacyManager enforces consent requirement
- [ ] SensitivityFilter redacts PII correctly
- [ ] Audit log tracks all privacy actions
- [ ] Tests validate all privacy scenarios
- [ ] Cannot capture audio without explicit consent
- [ ] Data deletion works for all stored data

**Exit Criteria**: Privacy tests 100% pass, AuditorAgent approval

### Gate 4: Integration Complete (After Phase 4)

**Checklist**:
- [ ] AmbientAgent orchestrates all components
- [ ] Events published to personal_context_stream
- [ ] WITNESS consumes and detects patterns
- [ ] End-to-end test: Speech → WITNESS → signal works
- [ ] Error recovery tests pass
- [ ] Health checks detect component failures

**Exit Criteria**: Integration tests 100% pass, full pipeline functional

### Gate 5: Pre-Merge Validation (After Phase 6)

**Checklist**:
- [ ] All 2,274 existing tests still pass (no regression)
- [ ] New ambient tests pass (>50 new tests added)
- [ ] Code coverage >90% for new modules
- [ ] No type errors (mypy --strict)
- [ ] No constitutional violations (constitution_check passes)
- [ ] Documentation complete and reviewed
- [ ] 24-hour continuous operation test passes
- [ ] Performance within specified limits

**Exit Criteria**: MergerAgent approval, CI pipeline green, ready for PR

---

## 7. Risks & Mitigations

### Risk 1: Privacy Concerns (HIGH IMPACT)

**Risk**: Users uncomfortable with ambient audio capture, even locally

**Impact**: Feature unusable, wasted development effort

**Likelihood**: MEDIUM

**Mitigation**:
1. **Explicit Consent**: Multi-step consent workflow, cannot accidentally enable
2. **Transparency**: Open-source code, clear data handling documentation
3. **Privacy-First**: All processing local, no cloud transmission
4. **User Control**: Easy pause/delete, visible recording indicator
5. **Opt-In Only**: Disabled by default, requires active enablement

**Contingency**: If user adoption low, deprecate feature and focus on other inputs

### Risk 2: Whisper Performance (MEDIUM IMPACT)

**Risk**: Local Whisper.cpp too slow for real-time transcription on older hardware

**Impact**: High latency, poor user experience

**Likelihood**: MEDIUM

**Mitigation**:
1. **Model Selection**: Start with `base.en`, fallback to `tiny.en` if slow
2. **Hardware Detection**: Auto-select model based on CPU/GPU
3. **Batching**: Buffer audio to reduce transcription frequency
4. **Performance Tests**: Validate on target hardware early
5. **GPU Acceleration**: Use Metal (macOS) or CUDA if available

**Contingency**: Add cloud Whisper API option (OpenAI) for users who accept cost/privacy trade-off

### Risk 3: PII Leakage (CRITICAL IMPACT)

**Risk**: Sensitivity filter fails to detect PII, sensitive data reaches message bus

**Impact**: Privacy violation, user trust loss, potential legal issues

**Likelihood**: LOW (with comprehensive testing)

**Mitigation**:
1. **Multiple Layers**: Presidio + regex + keyword blocking
2. **Test Coverage**: Extensive PII detection test suite
3. **Audit Logging**: Track all redactions for review
4. **User Review**: Option to review transcriptions before publishing
5. **Fail-Safe**: Drop segment if filter uncertain

**Contingency**: Implement manual review queue before publishing to WITNESS

### Risk 4: WITNESS Integration Issues (LOW IMPACT)

**Risk**: Ambient events don't match WITNESS pattern expectations, patterns not detected

**Impact**: Feature doesn't generate useful signals

**Likelihood**: LOW (WITNESS already handles personal_context_stream)

**Mitigation**:
1. **Schema Alignment**: Match existing event format exactly
2. **Integration Tests**: Validate WITNESS consumes events correctly
3. **Pattern Tuning**: Adjust pattern heuristics for ambient speech
4. **Feedback Loop**: Monitor detection rate, tune over time
5. **Fallback Patterns**: Add ambient-specific patterns if needed

**Contingency**: Extend WITNESS pattern detector with ambient-optimized rules

### Risk 5: Constitutional Violations (MEDIUM IMPACT)

**Risk**: Ambient system violates Article I (incomplete context) or Article II (quality)

**Impact**: System breaks constitutional compliance, requires redesign

**Likelihood**: LOW (with careful design)

**Mitigation**:
1. **Article I Compliance**: Process all audio chunks before transcription, retry on timeouts
2. **Article II Compliance**: >90% test coverage, 100% test pass rate
3. **Article IV Compliance**: Persist patterns to PersistentStore
4. **Constitution Check**: Run constitutional validation in CI
5. **Quality Gates**: Multi-stage validation before merge

**Contingency**: QualityEnforcer agent reviews and fixes violations automatically

---

## 8. Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage | >90% | pytest-cov |
| Test Pass Rate | 100% | CI pipeline |
| Audio Capture Reliability | >99% uptime | 24h test |
| Transcription Accuracy | >90% WER | Manual evaluation |
| End-to-End Latency | <5 seconds | Timestamp delta |
| CPU Usage | <10% average | Resource monitor |
| Memory Footprint | <500MB | Resource monitor |
| PII Detection Accuracy | >95% | Test suite |

### User Experience Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Consent Workflow Clarity | 100% understand | User survey |
| Privacy Concerns Addressed | >90% comfortable | User survey |
| Feature Adoption Rate | >50% of users | Usage telemetry |
| User-Reported Issues | <5 per month | Issue tracker |

### Business Value Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| User Intent Patterns Detected | >10 per day | Pattern store |
| Actionable Insights Generated | >3 per week | ARCHITECT queue |
| Manual Work Automated | >5 tasks/month | User feedback |
| User Satisfaction | >4/5 | User survey |

---

## 9. Dependencies

### External Dependencies

**Python Packages**:
- `whisper-cpp-python` (Whisper.cpp bindings)
- `pyaudio` (Audio capture)
- `webrtcvad` (Voice activity detection)
- `presidio-analyzer` (PII detection)
- `presidio-anonymizer` (PII redaction)
- `pydantic` (Type validation)
- `click` or `typer` (CLI framework)

**System Dependencies**:
- PortAudio (for PyAudio)
- Whisper models (`base.en`, `tiny.en`)
- Microphone hardware with system permissions

### Internal Dependencies

**Agency Modules**:
- `trinity_protocol.message_bus`: Event publishing
- `trinity_protocol.witness_agent`: Pattern detection
- `trinity_protocol.persistent_store`: Pattern storage
- `shared.agent_context`: Settings and memory
- `shared.models`: Existing Pydantic models
- `tools.constitution_check`: Compliance validation

**Trinity Agents**:
- WITNESS: Consumes ambient events (no changes needed)
- ARCHITECT: Processes detected user intent patterns
- EXECUTOR: May implement suggested improvements

---

## 10. Rollout Plan

### Phase 1: Alpha Release (Internal Testing)

**Scope**: Core functionality only, no CLI polish

**Users**: Developer only (you)

**Duration**: 1 week

**Goals**:
- Validate core pipeline works
- Test privacy controls
- Measure performance
- Identify bugs and edge cases

**Success Criteria**: 7-day continuous operation without crashes

### Phase 2: Beta Release (Limited Users)

**Scope**: Full feature set with CLI and documentation

**Users**: 3-5 early adopters

**Duration**: 2 weeks

**Goals**:
- Gather user feedback
- Test on different hardware
- Validate privacy concerns addressed
- Measure user intent detection rate

**Success Criteria**: >80% user satisfaction, <5 critical bugs

### Phase 3: General Availability

**Scope**: Production-ready, documented, tested

**Users**: All Agency users (opt-in)

**Launch Checklist**:
- [ ] All tests passing (100%)
- [ ] Documentation complete
- [ ] Privacy FAQ reviewed by legal
- [ ] Performance validated on 3+ hardware configs
- [ ] User guide tested with non-technical user
- [ ] Rollback plan defined
- [ ] Support process established

---

## 11. Future Enhancements (Out of Scope)

**Not in V1, but consider for future**:

1. **Multi-Language Support**: Extend beyond English
2. **Speaker Diarization**: Identify who said what in meetings
3. **Emotion Detection**: Detect frustration/excitement in tone
4. **Keyword Spotting**: Trigger on specific phrases ("Hey Agency")
5. **Cloud Whisper Option**: OpenAI Whisper API for faster transcription
6. **Mobile Integration**: Capture from phone conversations
7. **Meeting Summarization**: Auto-generate meeting notes
8. **Action Item Extraction**: Detect TODOs and create tasks automatically

---

## 12. Related Documents

**Specifications**:
- `specs/ambient_intelligence_system.md` (to be created by ChiefArchitect)
- `specs/trinity_whitepaper_enhancements.md` (context for autonomous operation)

**ADRs**:
- `docs/adr/ADR-016-ambient-listener-architecture.md` (to be created)
- `docs/adr/ADR-004-continuous-learning-system.md` (learning integration)

**Implementation Guides**:
- `NEXT_AGENT_MISSION.md` (autonomous operation context)
- `trinity_protocol/README.md` (Trinity Protocol overview)
- `docs/INSIDE_REPORT_SESSION_2025_10_01.md` (recent learnings)

**Code References**:
- `trinity_protocol/witness_agent.py` (integration target)
- `trinity_protocol/message_bus.py` (event publishing)
- `trinity_protocol/pattern_detector.py` (pattern classification)

---

## 13. Constitutional Alignment

### Article I: Complete Context Before Action

**Compliance**:
- Audio chunks processed completely before transcription
- No premature termination on partial data
- Timeout handling with retries (2x, 3x, up to 10x)
- All segments buffered for sentence completion

**Validation**: Integration tests verify no action on incomplete audio

### Article II: 100% Verification and Stability

**Compliance**:
- >90% test coverage for all modules
- 100% test pass rate required for merge
- CI pipeline validates all tests
- 24-hour continuous operation test

**Validation**: QualityEnforcer agent validates before merge

### Article III: Automated Merge Enforcement

**Compliance**:
- Pre-commit hooks run tests
- CI pipeline blocks merge on failure
- No manual override capability
- Quality gates at each phase

**Validation**: MergerAgent enforces constitutional requirements

### Article IV: Continuous Learning and Improvement

**Compliance**:
- Detected patterns stored in PersistentStore
- Cross-session pattern recognition
- Pattern confidence tracking
- Learning accumulated in VectorStore

**Validation**: LearningAgent extracts patterns from ambient sessions

### Article V: Spec-Driven Development

**Compliance**:
- Formal spec created before implementation (TASK-003)
- ADR documents architectural decisions
- Plan breaks down into TodoWrite tasks
- All implementation traces to specification

**Validation**: This plan follows spec-kit methodology

---

## 14. Conclusion

This implementation plan provides a comprehensive roadmap for building the Ambient Intelligence System. The system will enable Trinity Protocol's WITNESS agent to monitor ambient audio sources and extract actionable user intent signals for autonomous improvement.

**Key Highlights**:
- **Privacy-First**: All processing local, explicit consent required
- **Cost-Free**: Whisper.cpp eliminates API costs
- **Trinity Integration**: Seamless WITNESS integration without code changes
- **Constitutional Compliance**: Adheres to all 5 articles
- **Parallel Execution**: 32-40 hours with agent parallelization
- **Comprehensive Testing**: >90% coverage, 24-hour validation

**Next Steps**:
1. ChiefArchitect creates formal spec and ADR (TASK-003)
2. User approves specification
3. AgencyCodeAgent begins implementation (TASK-001)
4. Parallel agent execution across phases
5. Quality gates at each phase
6. Final validation and merge

**Expected Outcome**: A production-ready ambient intelligence system that enables Trinity Protocol to detect user intent from natural speech, creating a foundation for human-out-of-loop autonomous operation.

---

**Status**: Draft - Awaiting Specification
**Next**: Create `specs/ambient_intelligence_system.md` and `docs/adr/ADR-016-ambient-listener-architecture.md`
**Timeline**: 4-5 weeks for full implementation with testing
**Estimated Cost**: $0 (local Whisper.cpp, no API costs)

---

*"Privacy-first ambient intelligence for autonomous learning and improvement."*
