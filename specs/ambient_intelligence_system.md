# Specification: Ambient Intelligence System for Trinity Life Assistant

**Spec ID**: `spec-017-ambient-intelligence-system`
**Status**: `Draft`
**Author**: ChiefArchitectAgent
**Created**: 2025-10-01
**Last Updated**: 2025-10-01
**Related Plan**: `plan-017-ambient-listener.md` (to be created)
**Related ADR**: `ADR-016-ambient-listener-architecture.md`

---

## Executive Summary

The Ambient Intelligence System enables Trinity Life Assistant to continuously listen to ambient audio on MacBook Pro M4, transcribe locally using Whisper AI, and feed real-time transcription streams to the WITNESS agent for proactive assistance. This system prioritizes privacy through on-device processing, user control, and zero cloud transmission of raw audio.

---

## Goals

### Primary Goals

- **G1: Privacy-First Ambient Listening**: Enable always-on ambient audio capture with 100% local processing, zero cloud transmission of raw audio, and full user control over data retention
- **G2: Efficient M4 Pro Integration**: Optimize for Apple M4 Pro architecture using Whisper.cpp for <5% battery impact during continuous operation
- **G3: Trinity Protocol Integration**: Seamlessly integrate transcription stream with existing WITNESS agent via `personal_context_stream` queue
- **G4: User Safety and Transparency**: Provide clear visual indicators, instant mute capabilities, and comprehensive privacy controls with audit logging

### Success Metrics

- **Performance**: Transcription latency <2 seconds from speech to WITNESS ingestion
- **Privacy**: 100% of raw audio processing happens on-device, zero cloud transmission
- **Battery**: <5% additional battery drain during continuous operation
- **Accuracy**: Transcription WER (Word Error Rate) <10% for conversational English
- **Reliability**: 99.9% uptime during MacBook active hours (no crashes, memory leaks)
- **User Trust**: Clear privacy indicators visible at all times, instant mute response <100ms

---

## Non-Goals

### Explicit Exclusions

- **Cloud-Based Transcription**: No use of external APIs (OpenAI Whisper API, Google Speech, etc.)
- **Audio Recording Storage**: System does NOT store raw audio files; only rolling buffer in memory
- **Multi-Device Support**: Initial version MacBook Pro M4 only (no iPhone, iPad, HomePod)
- **Real-Time Translation**: Only English transcription initially (multilingual future consideration)
- **Speaker Diarization**: No speaker identification or separation in initial version
- **Voice Commands**: Not a voice control system; purely passive listening for context awareness

### Future Considerations

- **Multi-Language Support**: Spanish, French, German, Chinese transcription
- **Speaker Identification**: Distinguish between user and others for privacy filtering
- **Semantic Chunking**: Break transcription into semantic segments for better WITNESS processing
- **iOS Integration**: Extend to iPhone/iPad for full-device ambient awareness
- **Offline Capability**: Ensure system works without internet connectivity

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Privacy-Conscious Knowledge Worker
- **Description**: Software engineer working from home, handles sensitive information, deeply values privacy
- **Goals**: Wants proactive assistance but refuses to send audio to cloud; needs assurance of local processing
- **Pain Points**: Distrusts existing voice assistants (Alexa, Siri) due to privacy concerns; manual context switching between tasks
- **Technical Proficiency**: High - understands encryption, local processing, wants technical transparency

#### Persona 2: Busy Professional with Compliance Requirements
- **Description**: Healthcare/legal professional bound by HIPAA/attorney-client privilege
- **Goals**: Cannot use cloud-based assistants; needs legally defensible local-only processing
- **Pain Points**: Existing assistants violate compliance; manual task tracking is time-consuming
- **Technical Proficiency**: Medium - needs clear privacy guarantees without deep technical knowledge

#### Persona 3: Creative Professional with Context-Rich Workflows
- **Description**: Writer, researcher, or content creator with complex multi-hour workflows
- **Goals**: Wants system to understand ongoing context (research topics, writing themes) without manual logging
- **Pain Points**: Loses track of ideas during deep work; manual note-taking disrupts flow
- **Technical Proficiency**: Medium - values simplicity and transparency

### User Journeys

#### Journey 1: First-Time Setup with Privacy Verification
```
1. User starts with: Fresh Trinity installation, skeptical about ambient listening
2. User needs to: Enable ambient intelligence while verifying privacy guarantees
3. User performs:
   - Opens Trinity settings → Ambient Intelligence
   - Sees clear privacy statement: "100% local processing, zero cloud transmission"
   - Clicks "Show Technical Details" → sees Whisper.cpp location, model path, no network calls
   - Enables ambient listening with hardware mute button location highlighted
4. System responds:
   - Visual indicator appears in menu bar (green microphone icon)
   - First transcription appears in privacy dashboard within 5 seconds
   - "Privacy Verified" checkmark shows no network activity
5. User achieves: Confident that system is privacy-preserving; begins normal work with ambient assistance
```

#### Journey 2: Daily Use with Proactive Assistance
```
1. User starts with: Ambient listening enabled, starting work day
2. User needs to: Receive proactive suggestions based on ambient conversation context
3. User performs:
   - Joins video call, discusses project deadline approaching
   - Verbally mentions "need to refactor authentication module before Friday"
   - Continues working without manual task entry
4. System responds:
   - Whisper transcribes: "need to refactor authentication module before Friday"
   - WITNESS detects pattern: user_intent/feature_request (confidence 0.82)
   - ARCHITECT generates task suggestion: "Add task: Refactor auth module (deadline Friday)"
   - Notification appears: "I noticed you mentioned refactoring auth. Add to task list?"
5. User achieves: Task captured without breaking flow; proactive assistance feels helpful, not intrusive
```

#### Journey 3: Privacy-Sensitive Meeting with Instant Mute
```
1. User starts with: Ambient listening enabled, about to join confidential meeting
2. User needs to: Instantly disable listening without navigating menus
3. User performs:
   - Presses hardware mute button (Fn+M or dedicated key)
   - Visual indicator changes to red "MUTED" in menu bar
4. System responds:
   - Audio capture stops <100ms
   - Rolling buffer is cleared from memory
   - Menu bar shows "MUTED - No transcription active"
   - Meeting proceeds with zero ambient capture
5. User achieves: Confident that sensitive discussion is not processed; unmutes after meeting
```

---

## Acceptance Criteria

### Functional Requirements

#### Component 1: Audio Capture System
- **AC-1.1**: System SHALL capture ambient audio from default microphone at 16kHz mono (Whisper-optimized sample rate)
- **AC-1.2**: System SHALL maintain rolling buffer of max 30 seconds audio in memory, discarding older samples
- **AC-1.3**: System SHALL NOT write raw audio to disk at any time (memory-only processing)
- **AC-1.4**: System SHALL respect macOS microphone permissions (request permission, handle denial gracefully)
- **AC-1.5**: System SHALL detect silence periods (>2 seconds below -40dB) and segment audio for efficient transcription

#### Component 2: Whisper.cpp Transcription Engine
- **AC-2.1**: System SHALL use Whisper.cpp (C++ port) with quantized models (ggml-medium.en or ggml-small.en)
- **AC-2.2**: System SHALL process audio chunks asynchronously without blocking main thread
- **AC-2.3**: Transcription latency SHALL be <2 seconds from speech end to text availability
- **AC-2.4**: System SHALL handle transcription errors gracefully (log error, continue operation)
- **AC-2.5**: System SHALL use Metal acceleration (M4 Pro GPU) for inference if available, fallback to CPU
- **AC-2.6**: System SHALL achieve <10% WER (Word Error Rate) on conversational English benchmark

#### Component 3: Trinity Message Bus Integration
- **AC-3.1**: Transcription output SHALL be published to `personal_context_stream` queue with priority=NORMAL
- **AC-3.2**: Message format SHALL match WITNESS expected schema:
  ```json
  {
    "source": "ambient_listener",
    "timestamp": "ISO8601",
    "content": "transcribed text",
    "confidence": 0.0-1.0,
    "metadata": {
      "audio_duration_ms": 1500,
      "chunk_id": "uuid",
      "silence_detected": true/false
    }
  }
  ```
- **AC-3.3**: System SHALL include Whisper confidence score in metadata
- **AC-3.4**: System SHALL correlate transcription chunks with correlation_id for multi-turn context
- **AC-3.5**: System SHALL NOT publish transcriptions when muted (no messages to bus during mute)

#### Component 4: Privacy and Safety Controls
- **AC-4.1**: System SHALL provide hardware-triggered mute (keyboard shortcut, physical button) with <100ms response
- **AC-4.2**: System SHALL display clear visual indicator in macOS menu bar:
  - Green microphone: Active listening
  - Red microphone with slash: Muted
  - Yellow microphone: Processing (transcription in progress)
- **AC-4.3**: System SHALL provide privacy dashboard showing:
  - Current status (active/muted)
  - Last 10 transcriptions (user can verify accuracy)
  - Network activity monitor (should always show "No network calls")
  - Data retention policy (transcriptions kept for N hours, configurable)
- **AC-4.4**: System SHALL allow user to configure retention period (1 hour, 8 hours, 24 hours, or session-only)
- **AC-4.5**: System SHALL purge transcriptions older than retention period automatically
- **AC-4.6**: System SHALL provide "Panic Delete" button that immediately purges all transcription history
- **AC-4.7**: System SHALL log all privacy-relevant events (mute/unmute, retention purge) to audit log

### Non-Functional Requirements

#### Performance
- **AC-P.1**: Battery impact SHALL be <5% during 8-hour continuous operation
- **AC-P.2**: Memory footprint SHALL be <200MB including Whisper model and rolling buffer
- **AC-P.3**: CPU usage SHALL average <10% on M4 Pro during active transcription
- **AC-P.4**: System SHALL NOT introduce audio latency or interference with other apps (Zoom, Music, etc.)

#### Quality
- **AC-Q.1**: System SHALL achieve 99.9% uptime during MacBook active hours (no crashes)
- **AC-Q.2**: System SHALL gracefully handle microphone device changes (headphones plugged in/out)
- **AC-Q.3**: System SHALL detect and log any Whisper model errors for debugging
- **AC-Q.4**: Code SHALL follow strict typing (no `Dict[Any, Any]`), use Pydantic models for all data structures

#### Security
- **AC-S.1**: Raw audio SHALL NEVER be written to disk (memory-only, cleared on mute/shutdown)
- **AC-S.2**: Transcription data SHALL be encrypted at rest using macOS Keychain for storage
- **AC-S.3**: System SHALL verify Whisper.cpp binary integrity (checksum validation on startup)
- **AC-S.4**: System SHALL NOT make any network calls for audio or transcription processing (verified via network monitor)
- **AC-S.5**: User SHALL be able to inspect open source code for privacy verification

### Constitutional Compliance

#### Article I: Complete Context Before Action
- **AC-CI.1**: System SHALL NOT publish partial transcriptions; wait for complete audio segment (silence-detected)
- **AC-CI.2**: System SHALL retry Whisper transcription on timeout (max 3 retries with exponential backoff)
- **AC-CI.3**: System SHALL NOT introduce broken windows; all audio processing errors logged and handled

#### Article II: 100% Verification and Stability
- **AC-CII.1**: 100% test coverage for audio capture, transcription, message bus integration, privacy controls
- **AC-CII.2**: All tests SHALL pass before feature completion (unit, integration, privacy validation)
- **AC-CII.3**: System SHALL include privacy compliance tests (verify no network calls, no disk writes)

#### Article III: Automated Merge Enforcement
- **AC-CIII.1**: Feature SHALL respect automated enforcement (pre-commit hooks, CI pipeline)
- **AC-CIII.2**: No bypass mechanisms required; all quality gates must pass

#### Article IV: Continuous Learning and Improvement
- **AC-CIV.1**: System SHALL generate learnings from WITNESS pattern detection (e.g., "User often says X during Y context")
- **AC-CIV.2**: System SHALL apply historical learnings (e.g., improve transcription accuracy based on user's vocabulary)

#### Article V: Spec-Driven Development
- **AC-CV.1**: Implementation SHALL strictly follow this specification
- **AC-CV.2**: All changes SHALL be documented and approved via spec amendment process

---

## Dependencies & Constraints

### System Dependencies
- **macOS 14+ (Sonoma)**: Required for modern CoreAudio APIs and Metal acceleration
- **Apple M4 Pro (or M-series)**: Optimized for Apple Silicon; Intel Macs not supported initially
- **Trinity Protocol**: Message bus, WITNESS agent, persistent store
- **Python 3.12+**: Async audio processing, message bus client

### External Dependencies
- **Whisper.cpp**: C++ implementation of OpenAI Whisper (https://github.com/ggerganov/whisper.cpp)
  - Version: 1.5.0+
  - Model: ggml-medium.en (769MB) or ggml-small.en (466MB)
  - License: MIT (compatible)
- **PyAudio or sounddevice**: Python library for audio capture (BSD license)
- **ctypes or cffi**: Python bindings for Whisper.cpp C library

### Technical Constraints
- **Local Processing Only**: No cloud APIs permitted (privacy requirement)
- **Memory Limit**: 200MB total (rolling buffer + Whisper model + overhead)
- **Latency Requirement**: <2 seconds from speech end to WITNESS ingestion
- **Battery Constraint**: <5% additional drain during continuous operation
- **macOS Exclusive**: Initial implementation MacBook only (iOS future consideration)

### Business Constraints
- **Privacy Compliance**: Must satisfy HIPAA, attorney-client privilege, GDPR personal data requirements
- **Open Source Transparency**: All code must be inspectable for privacy verification
- **User Trust**: Any privacy violation is a CRITICAL bug (immediate fix, transparent disclosure)

---

## Risk Assessment

### High Risk Items
- **Risk 1: Whisper.cpp Performance Degradation**
  - *Description*: Whisper transcription too slow, causing latency >2s or high CPU/battery usage
  - *Mitigation*: Benchmark multiple models (small, base, medium), use quantized GGML, Metal GPU acceleration, fallback to smaller model if latency exceeded

- **Risk 2: Privacy Violation via Accidental Cloud Transmission**
  - *Description*: Bug causes raw audio or transcription to be sent to cloud (catastrophic trust breach)
  - *Mitigation*: Network isolation tests, manual code review of all network calls, privacy compliance test suite, open source transparency

- **Risk 3: Microphone Permission Denial or Revocation**
  - *Description*: User denies microphone access or macOS revokes permission, breaking system
  - *Mitigation*: Graceful degradation (show clear error message, link to settings), poll permission status every 30 seconds, user education

### Medium Risk Items
- **Risk 4: Audio Device Compatibility Issues**
  - *Description*: System fails with certain microphones (Bluetooth, USB, headsets)
  - *Mitigation*: Test with multiple audio devices (built-in, AirPods, USB mic), handle device change events gracefully

- **Risk 5: Whisper Model Download Size**
  - *Description*: 769MB model download during installation may fail or frustrate users
  - *Mitigation*: Pre-bundle model with installation, show clear download progress, offer smaller model (small.en 466MB) as option

### Constitutional Risks
- **Constitutional Risk 1: Article I Violation (Incomplete Context)**
  - *Description*: Publishing partial transcriptions (mid-sentence) to WITNESS, leading to incorrect pattern detection
  - *Mitigation*: Use silence detection (>2 seconds) to segment complete utterances, validate transcript completeness before publishing

- **Constitutional Risk 2: Article II Violation (Insufficient Testing)**
  - *Description*: Privacy bugs slip through due to inadequate test coverage
  - *Mitigation*: Mandatory privacy compliance test suite (no network calls, no disk writes), 100% code coverage requirement, manual privacy audit

---

## Integration Points

### Agent Integration
- **WITNESS Agent**: Primary consumer of transcription stream via `personal_context_stream` queue
  - WITNESS classifies transcriptions as user_intent, recurring_topic, feature_request patterns
  - High-confidence patterns (≥0.7) published to `improvement_queue` for ARCHITECT processing

- **ARCHITECT Agent**: Receives WITNESS signals, generates proactive task suggestions
  - Example: "User mentioned refactoring auth module" → Generate task spec for refactoring

- **EXECUTOR Agent**: Executes approved tasks, publishes outcomes to `telemetry_stream` (loop closure)

### System Integration
- **Message Bus (Trinity Protocol)**:
  - Publish transcriptions to `personal_context_stream` (queue_name, message, priority, correlation_id)
  - Message format: `{"source": "ambient_listener", "content": "...", "timestamp": "...", "metadata": {...}}`

- **Persistent Store**:
  - Store transcriptions with TTL (time-to-live) based on user retention policy
  - Automatic purge after retention period (1h, 8h, 24h, session-only)

- **Privacy Dashboard (UI)**:
  - Display real-time transcription stream
  - Show privacy status (active/muted, network activity, retention policy)
  - Provide mute button, panic delete, settings access

### External Integration
- **macOS CoreAudio**: Audio capture from default input device, microphone permission management
- **Whisper.cpp Library**: Load via ctypes/cffi, call transcription functions, receive text output
- **macOS Menu Bar API**: Display visual indicator (NSStatusItem), handle user interactions

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ambient Intelligence System                   │
└─────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
   ┌──────────────────┐ ┌──────────────┐ ┌────────────────┐
   │  Audio Capture   │ │   Whisper    │ │ Privacy Control│
   │    Manager       │ │  Transcriber │ │    Manager     │
   └──────────────────┘ └──────────────┘ └────────────────┘
              │                │                │
              │                │                │
              ▼                ▼                ▼
   ┌──────────────────────────────────────────────────────┐
   │          Trinity Message Bus Integration              │
   │      (personal_context_stream publisher)              │
   └──────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │   WITNESS Agent    │
                    │ (Pattern Detector) │
                    └────────────────────┘
```

### Component Descriptions

#### 1. Audio Capture Manager
**Responsibility**: Capture ambient audio from macOS microphone, manage rolling buffer

**Key Functions**:
- `initialize_audio_device()`: Request microphone permission, select default input device
- `start_capture()`: Begin continuous audio capture at 16kHz mono
- `get_audio_chunk()`: Return next audio segment (silence-detected or 30s max)
- `clear_buffer()`: Immediately clear rolling buffer (on mute)
- `handle_device_change()`: Gracefully switch audio devices

**Data Flow**:
```
Microphone → CoreAudio → Rolling Buffer (30s max) → Audio Chunk → Transcriber
```

**Privacy Guarantees**:
- No disk writes (memory-only)
- Buffer cleared on mute (<100ms)
- Buffer auto-purge on shutdown

#### 2. Whisper Transcriber
**Responsibility**: Transcribe audio chunks using Whisper.cpp, return text with confidence

**Key Functions**:
- `load_whisper_model()`: Load ggml-medium.en or ggml-small.en model into memory
- `transcribe_chunk(audio_data)`: Async transcription, return (text, confidence)
- `verify_model_integrity()`: Checksum validation on startup
- `use_metal_acceleration()`: Detect M4 Pro GPU, enable Metal backend

**Data Flow**:
```
Audio Chunk → Whisper.cpp (Metal GPU) → Transcribed Text + Confidence → Message Bus
```

**Performance Optimization**:
- Quantized GGML models (INT8) for speed
- Metal acceleration (M4 Pro GPU)
- Async processing (non-blocking)
- Batch processing if multiple chunks queued

#### 3. Privacy Control Manager
**Responsibility**: Enforce privacy controls, provide user transparency

**Key Functions**:
- `handle_mute_toggle()`: Instantly stop capture, clear buffer, update visual indicator
- `update_menu_bar_status()`: Change icon (green/red/yellow) based on system state
- `purge_transcriptions()`: Delete all transcriptions (panic delete or retention policy)
- `show_privacy_dashboard()`: Display recent transcriptions, network monitor, settings
- `audit_log_event(event_type)`: Log mute/unmute, retention purge to audit trail

**States**:
- **ACTIVE**: Green microphone, capturing and transcribing
- **MUTED**: Red microphone with slash, no capture, buffer cleared
- **PROCESSING**: Yellow microphone, transcription in progress

#### 4. Trinity Message Bus Integration
**Responsibility**: Publish transcriptions to `personal_context_stream` for WITNESS consumption

**Message Schema** (Pydantic Model):
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AmbientTranscription(BaseModel):
    source: str = Field(default="ambient_listener", const=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str = Field(min_length=1, description="Transcribed text")
    confidence: float = Field(ge=0.0, le=1.0, description="Whisper confidence score")
    metadata: TranscriptionMetadata

class TranscriptionMetadata(BaseModel):
    audio_duration_ms: int = Field(gt=0, description="Audio chunk duration in milliseconds")
    chunk_id: str = Field(description="UUID for this transcription chunk")
    silence_detected: bool = Field(description="Whether silence triggered segmentation")
    model_name: str = Field(description="Whisper model used (e.g., ggml-medium.en)")
    correlation_id: Optional[str] = Field(default=None, description="Correlates multi-turn context")
```

**Publishing**:
```python
async def publish_transcription(bus: MessageBus, transcription: AmbientTranscription):
    await bus.publish(
        queue_name="personal_context_stream",
        message=transcription.dict(),
        priority=0,  # NORMAL priority
        correlation_id=transcription.metadata.correlation_id
    )
```

### Data Flow (End-to-End)

```
1. User speaks: "I need to refactor the authentication module before Friday"
2. Audio Capture Manager: Captures audio, detects 2s silence, segments chunk
3. Whisper Transcriber: Transcribes → "I need to refactor the authentication module before Friday" (confidence: 0.89)
4. Message Bus Integration: Publishes AmbientTranscription to personal_context_stream
5. WITNESS Agent: Receives message, classifies as user_intent/feature_request (confidence: 0.82)
6. WITNESS: Publishes Signal to improvement_queue → {"pattern": "feature_request", "summary": "Refactor auth module deadline Friday"}
7. ARCHITECT Agent: Receives signal, generates task spec: "Refactor authentication module (priority: HIGH, deadline: Friday)"
8. User: Sees notification → "I noticed you mentioned refactoring auth. Add to task list?"
9. User: Approves → Task added to execution queue
```

---

## Testing Strategy

### Test Categories

#### Unit Tests (95% coverage target)
- **Audio Capture Manager**:
  - `test_initialize_audio_device_success()`: Verify microphone permission granted, device initialized
  - `test_initialize_audio_device_permission_denied()`: Handle permission denial gracefully
  - `test_rolling_buffer_max_size()`: Verify buffer never exceeds 30 seconds
  - `test_clear_buffer_on_mute()`: Buffer cleared <100ms after mute trigger
  - `test_silence_detection()`: Correctly segment audio on 2s silence below -40dB

- **Whisper Transcriber**:
  - `test_load_whisper_model_success()`: Load ggml-medium.en model successfully
  - `test_transcribe_chunk_accuracy()`: WER <10% on test audio samples
  - `test_transcribe_chunk_latency()`: Transcription completes <2s
  - `test_metal_acceleration_fallback()`: Falls back to CPU if Metal unavailable
  - `test_model_integrity_check()`: Detects corrupted model file

- **Privacy Control Manager**:
  - `test_mute_toggle_clears_buffer()`: Buffer cleared on mute
  - `test_menu_bar_status_updates()`: Icon changes reflect system state
  - `test_purge_transcriptions()`: All transcriptions deleted
  - `test_retention_policy_enforcement()`: Transcriptions auto-purge after TTL
  - `test_audit_log_events()`: Mute/unmute events logged

#### Integration Tests (End-to-End)
- **test_audio_to_witness_pipeline()**:
  - Play test audio → verify transcription published to personal_context_stream → WITNESS receives
  - Assert: Transcription accuracy, latency <2s, message format correct

- **test_mute_during_transcription()**:
  - Start transcription → trigger mute mid-process → verify transcription aborted, buffer cleared

- **test_device_change_handling()**:
  - Start capture → unplug headphones → verify system switches to built-in mic gracefully

- **test_privacy_compliance_no_network_calls()**:
  - Run system for 1 hour → verify zero network calls (using macOS Activity Monitor or network sniffer)

- **test_privacy_compliance_no_disk_writes()**:
  - Run system for 1 hour → verify no audio files written to disk (scan temp directories)

#### Privacy Compliance Tests (CRITICAL)
- **test_no_network_calls_during_transcription()**: Use network monitor, assert 0 bytes sent/received
- **test_no_audio_files_on_disk()**: Scan `/tmp`, `~/Library/Caches`, assert no `.wav`, `.mp3`, `.m4a` files
- **test_buffer_cleared_on_shutdown()**: Kill process → verify memory buffer not persisted
- **test_panic_delete_purges_all_data()**: Trigger panic delete → verify 0 transcriptions remain in database

#### Constitutional Compliance Tests
- **Article I (Complete Context)**:
  - `test_no_partial_transcriptions_published()`: Assert only complete segments (silence-detected) published
  - `test_retry_on_whisper_timeout()`: Simulate timeout, verify 3 retries with exponential backoff

- **Article II (100% Verification)**:
  - `test_all_unit_tests_pass()`: Run full suite, assert 0 failures
  - `test_privacy_tests_pass()`: Run privacy suite, assert 0 network calls, 0 disk writes

### Test Data Requirements
- **Test Audio Samples**:
  - 10 conversational English samples (5-30s each, diverse accents)
  - 5 samples with background noise (music, typing, traffic)
  - 3 samples with silence periods for segmentation testing

- **Privacy Test Vectors**:
  - Known sensitive phrases (SSN, credit card numbers) to verify no cloud transmission

### Test Environment Requirements
- **Hardware**: MacBook Pro M4 Pro, AirPods Pro, USB microphone
- **Software**: macOS 14 Sonoma, Python 3.12+, Whisper.cpp 1.5.0+
- **Network Monitoring**: Wireshark or macOS Activity Monitor to verify zero network calls

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Scope**: Audio capture, Whisper.cpp integration, basic transcription

**Deliverables**:
- `ambient_intelligence/audio_capture.py`: Audio capture manager
- `ambient_intelligence/whisper_transcriber.py`: Whisper.cpp wrapper
- `ambient_intelligence/models.py`: Pydantic models (AmbientTranscription, TranscriptionMetadata)
- Unit tests for audio capture and transcription
- Whisper model download/bundling script

**Success Criteria**:
- Audio capture works on MacBook Pro M4
- Whisper.cpp transcribes test audio with <10% WER
- Latency <2 seconds demonstrated
- All unit tests pass (Article II)

### Phase 2: Trinity Integration (Week 3)
**Scope**: Message bus integration, WITNESS agent connection

**Deliverables**:
- `ambient_intelligence/message_bus_client.py`: Publish to personal_context_stream
- Integration tests (audio → transcription → WITNESS)
- WITNESS agent updates (if needed) to handle ambient stream

**Success Criteria**:
- Transcriptions successfully published to message bus
- WITNESS receives and classifies ambient transcriptions
- End-to-end pipeline verified (<2s latency)
- Integration tests pass

### Phase 3: Privacy Controls (Week 4)
**Scope**: Mute functionality, visual indicators, privacy dashboard

**Deliverables**:
- `ambient_intelligence/privacy_manager.py`: Mute, buffer clear, audit logging
- `ambient_intelligence/menu_bar_ui.py`: macOS menu bar integration (NSStatusItem)
- Privacy dashboard UI (web view or native)
- Privacy compliance test suite

**Success Criteria**:
- Mute response <100ms verified
- Menu bar indicator accurate
- Privacy tests pass (0 network calls, 0 disk writes)
- Panic delete verified

### Phase 4: Optimization & Polish (Week 5-6)
**Scope**: Battery optimization, model selection, user education

**Deliverables**:
- Battery benchmarks (<5% drain over 8 hours)
- Model selection (medium vs small based on performance)
- User documentation (privacy guarantees, how to verify, mute usage)
- Final constitutional compliance verification

**Success Criteria**:
- Battery impact <5% (measured)
- All acceptance criteria met (functional, non-functional, constitutional)
- User documentation complete
- Ready for beta testing

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: @am (Product Owner)
- **Secondary Stakeholders**: Privacy-conscious beta testers, compliance professionals
- **Technical Reviewers**: ChiefArchitectAgent, QualityEnforcerAgent, AuditorAgent

### Review Criteria
- [x] **Completeness**: All sections filled with appropriate detail
- [x] **Clarity**: Requirements are unambiguous and testable
- [x] **Feasibility**: Technical implementation realistic (Whisper.cpp proven, M4 Pro capable)
- [x] **Constitutional Compliance**: Aligns with all constitutional articles
- [x] **Privacy-First Design**: On-device processing, user control, transparency prioritized
- [x] **Quality Standards**: Meets Agency quality requirements (strict typing, TDD, 100% tests pass)

### Approval Status
- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending technical review
- [ ] **Constitutional Compliance**: Pending QualityEnforcer audit
- [ ] **Privacy Audit**: Pending external privacy review
- [ ] **Final Approval**: Pending all above approvals

---

## Appendices

### Appendix A: Glossary
- **WER (Word Error Rate)**: Percentage of words incorrectly transcribed; lower is better
- **GGML**: Georgi Gerganov Machine Learning format; quantized model format for efficient inference
- **Metal**: Apple's GPU acceleration framework for M-series chips
- **Rolling Buffer**: Fixed-size memory buffer that discards oldest data when full
- **Silence Detection**: Audio processing technique to detect pauses in speech (typically >2s below -40dB)
- **TTL (Time-to-Live)**: Retention period after which data is automatically purged

### Appendix B: References
- **Whisper.cpp**: https://github.com/ggerganov/whisper.cpp
- **OpenAI Whisper**: https://github.com/openai/whisper (original model)
- **GGML Quantization**: https://github.com/ggerganov/ggml
- **macOS CoreAudio**: https://developer.apple.com/documentation/coreaudio
- **Trinity Protocol Implementation**: `docs/trinity_protocol_implementation.md`
- **Constitution**: `constitution.md`

### Appendix C: Related Documents
- **ADR-016**: Ambient Listener Architecture (decision record for this spec)
- **ADR-004**: Continuous Learning and Improvement (learning from ambient context)
- **Spec-001**: Spec-Driven Development (process this spec follows)
- **WITNESS Agent**: `docs/trinity_protocol/WITNESS.md`

### Appendix D: Privacy Compliance Checklist
- [x] Raw audio NEVER written to disk (memory-only)
- [x] No cloud API calls for transcription (Whisper.cpp local)
- [x] User can verify privacy (open source, network monitor)
- [x] Instant mute capability (<100ms)
- [x] Clear visual indicators (menu bar status)
- [x] Configurable retention policy (1h, 8h, 24h, session-only)
- [x] Panic delete (immediate purge of all transcriptions)
- [x] Audit logging (all privacy events recorded)
- [x] Encrypted at rest (macOS Keychain for stored transcriptions)
- [x] Graceful permission handling (clear error messages)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-01 | ChiefArchitectAgent | Initial specification |

---

*"Privacy is not a feature - it is a fundamental right. This system respects that."*
