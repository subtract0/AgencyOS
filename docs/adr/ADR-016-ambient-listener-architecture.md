# ADR-016: Ambient Listener Architecture for Trinity Life Assistant

## Status
**Proposed**

## Context

Trinity Life Assistant requires proactive awareness of user context to deliver truly intelligent assistance. Currently, the system relies on explicit user input (text, tasks, calendar events) but lacks understanding of ambient verbal context - conversations, meetings, brainstorming sessions where users naturally express intent, problems, and goals.

### Problem Statement

**Current Gap**: Trinity cannot perceive or respond to verbal context. If a user says "I need to refactor the authentication module before Friday" during a meeting, Trinity has no awareness unless the user manually creates a task.

**User Need**: Privacy-conscious professionals (engineers, healthcare workers, legal professionals) want proactive assistance based on ambient context WITHOUT compromising privacy by sending audio to cloud services (Alexa, Siri, Google Assistant).

**Technical Challenge**: Build an always-on ambient listener that:
1. Captures audio continuously on MacBook Pro M4
2. Transcribes locally using Whisper AI (no cloud)
3. Feeds transcription stream to WITNESS agent for pattern detection
4. Maintains <5% battery impact during 8-hour operation
5. Provides instant mute and clear privacy guarantees

### Requirements

**Functional**:
- Continuous audio capture from macOS microphone (16kHz mono)
- Local transcription using Whisper.cpp (on-device, zero cloud transmission)
- Publish transcriptions to Trinity Message Bus (`personal_context_stream`)
- WITNESS agent consumes transcriptions, detects user intent patterns
- Visual indicators (menu bar) showing active/muted/processing state

**Non-Functional**:
- Privacy: 100% on-device processing, no cloud APIs, no raw audio storage
- Performance: <2s transcription latency, <5% battery drain, <200MB memory
- Reliability: 99.9% uptime, graceful error handling
- User Control: Instant mute (<100ms), panic delete, configurable retention

**Constitutional**:
- Article I: Complete context (no partial transcriptions published)
- Article II: 100% verification (comprehensive privacy/functionality tests)
- Article IV: Continuous learning (improve from WITNESS pattern feedback)
- Article V: Spec-driven (formal specification created)

## Decision

We will implement a **Privacy-First Ambient Intelligence System** with the following architecture:

### 1. Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ambient Intelligence System                   │
│                     (ambient_intelligence/)                       │
└─────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
   ┌──────────────────┐ ┌──────────────┐ ┌────────────────┐
   │  Audio Capture   │ │   Whisper    │ │ Privacy Control│
   │    Manager       │ │  Transcriber │ │    Manager     │
   │ (audio_capture)  │ │(whisper_trans│ │(privacy_mgr)   │
   └──────────────────┘ └──────────────┘ └────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌────────────────────┐
                    │  Message Bus Client│
                    │ (publish to        │
                    │ personal_context_  │
                    │ stream)            │
                    └────────────────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │   WITNESS Agent    │
                    │ (Pattern Detector) │
                    └────────────────────┘
```

### 2. Technology Stack

**Audio Processing**:
- **Library**: PyAudio or sounddevice (Python audio capture)
- **Sample Rate**: 16kHz mono (Whisper-optimized)
- **Buffer**: Rolling 30-second in-memory buffer (no disk writes)
- **Segmentation**: Silence detection (>2s below -40dB)

**Transcription Engine**:
- **Technology**: Whisper.cpp (C++ port of OpenAI Whisper)
- **Model**: ggml-medium.en (769MB, WER <10%) or ggml-small.en (466MB, faster)
- **Acceleration**: Metal (M4 Pro GPU) with CPU fallback
- **Integration**: Python ctypes/cffi bindings to Whisper.cpp C library
- **Quantization**: INT8 quantized models for speed/memory efficiency

**Message Bus Integration**:
- **Queue**: `personal_context_stream` (existing Trinity queue)
- **Message Format**: Pydantic model `AmbientTranscription` (strict typing)
- **Priority**: NORMAL (0) - ambient context not urgent
- **Correlation**: correlation_id for multi-turn context tracking

**Privacy Controls**:
- **Mute Mechanism**: Keyboard shortcut (Fn+M) or menu bar click
- **Visual Indicator**: macOS NSStatusItem (menu bar icon: green/red/yellow)
- **Privacy Dashboard**: Web UI showing recent transcriptions, network monitor
- **Data Retention**: Configurable TTL (1h, 8h, 24h, session-only)
- **Panic Delete**: Immediate purge of all transcription history

### 3. Data Flow

**Normal Operation**:
```
1. Microphone → PyAudio → Rolling Buffer (30s max, in-memory)
2. Silence detected (>2s) → Segment audio chunk
3. Audio chunk → Whisper.cpp (Metal GPU) → Transcription + confidence
4. Transcription → Pydantic validation → AmbientTranscription object
5. AmbientTranscription → Message Bus → personal_context_stream queue
6. WITNESS agent → Subscribe to queue → Classify transcription
7. WITNESS → Detect pattern (user_intent, feature_request, etc.)
8. WITNESS → Publish signal → improvement_queue
9. ARCHITECT → Receive signal → Generate proactive task suggestion
10. User → Notification → "I noticed you mentioned X. Add to tasks?"
```

**Mute Operation**:
```
1. User presses Fn+M (or menu bar click)
2. Privacy Manager → Stop audio capture (<100ms)
3. Privacy Manager → Clear rolling buffer from memory
4. Privacy Manager → Update menu bar icon (red, muted)
5. Privacy Manager → Log audit event (mute triggered)
6. No transcriptions published while muted
7. User unmutes → Resume normal operation
```

### 4. File Structure

```
ambient_intelligence/
├── __init__.py
├── audio_capture.py          # Audio capture manager (PyAudio wrapper)
├── whisper_transcriber.py    # Whisper.cpp integration (ctypes bindings)
├── privacy_manager.py         # Mute, buffer clear, audit logging
├── message_bus_client.py     # Publish to personal_context_stream
├── menu_bar_ui.py            # macOS NSStatusItem integration
├── models.py                 # Pydantic models (AmbientTranscription, etc.)
├── config.py                 # Configuration (model path, retention policy)
└── main.py                   # Main orchestration (start/stop system)

tests/ambient_intelligence/
├── test_audio_capture.py     # Unit tests for audio capture
├── test_whisper_transcriber.py
├── test_privacy_manager.py
├── test_integration.py       # End-to-end pipeline tests
└── test_privacy_compliance.py # CRITICAL: verify no network, no disk writes

models/whisper/
├── ggml-medium.en.bin        # Whisper model (769MB, bundled or downloaded)
└── ggml-small.en.bin         # Optional smaller model (466MB)
```

### 5. Privacy Guarantees (Non-Negotiable)

- **Raw Audio**: NEVER written to disk (memory-only rolling buffer)
- **Cloud Transmission**: ZERO network calls for audio/transcription processing
- **User Control**: Instant mute (<100ms response), panic delete (purge all data)
- **Transparency**: Open source code, privacy dashboard shows network activity
- **Encryption**: Stored transcriptions encrypted at rest (macOS Keychain)
- **Retention**: User-configurable TTL, automatic purge after expiration
- **Audit Trail**: All privacy events logged (mute/unmute, purges)

### 6. Performance Targets

- **Latency**: <2 seconds from speech end to WITNESS ingestion
- **Battery**: <5% additional drain during 8-hour continuous operation
- **Memory**: <200MB total (buffer + Whisper model + overhead)
- **CPU**: <10% average on M4 Pro during active transcription
- **Accuracy**: <10% WER (Word Error Rate) on conversational English
- **Uptime**: 99.9% during MacBook active hours (no crashes)

## Rationale

### Why Whisper.cpp (not cloud APIs)?

**Privacy Imperative**: Cloud-based transcription (OpenAI Whisper API, Google Speech, AWS Transcribe) requires sending raw audio to external servers, which is:
- A privacy violation for sensitive conversations (healthcare, legal, engineering)
- A GDPR/HIPAA compliance risk
- A trust breach (users cannot verify what happens to their audio)

**Whisper.cpp Advantages**:
- ✅ 100% on-device processing (zero network calls)
- ✅ Open source (users can audit code for privacy)
- ✅ Optimized for Apple Silicon (Metal GPU acceleration)
- ✅ Quantized models (GGML) for speed/efficiency
- ✅ Proven accuracy (WER <10% on benchmark datasets)
- ✅ Active community, regular updates

**Trade-offs Accepted**:
- ❌ Larger binary size (769MB model vs API call)
- ❌ Higher local compute (transcription on-device vs cloud)
- ❌ Slower than cloud APIs (2s vs <1s for cloud)

**Verdict**: Privacy is non-negotiable. Local processing mandatory.

### Why Rolling Buffer (not recording to disk)?

**Privacy Risk**: Writing audio to disk creates permanent records that:
- Can be leaked (backup to cloud, forensic recovery)
- Violate user trust ("I thought it was ephemeral")
- Require complex deletion (filesystem remnants)

**Rolling Buffer Benefits**:
- ✅ Ephemeral by design (memory cleared on mute/shutdown)
- ✅ No forensic recovery risk
- ✅ Fast mute response (clear memory < disk deletion)
- ✅ No storage management complexity

**Trade-offs Accepted**:
- ❌ Limited buffer size (30s max vs unlimited recording)
- ❌ Lost on crash (no recovery of in-progress audio)

**Verdict**: Ephemeral memory buffer aligns with privacy-first design.

### Why Message Bus Integration (not direct WITNESS call)?

**Architecture Consistency**: Trinity Protocol uses message bus for all agent communication:
- ✅ Decoupled components (ambient listener independent of WITNESS)
- ✅ Persistent queue (messages survive process restarts)
- ✅ Asynchronous processing (no blocking)
- ✅ Multi-subscriber support (future agents can consume stream)

**Alternative Considered**: Direct function call to WITNESS agent
- ❌ Tight coupling (changes to WITNESS break ambient listener)
- ❌ No persistence (lost if WITNESS crashes)
- ❌ Synchronous (blocks transcription pipeline)

**Verdict**: Message bus aligns with Trinity architecture, provides reliability.

### Why Pydantic Models (not Dict[str, Any])?

**Constitutional Mandate**: Article II requires strict typing. `Dict[str, Any]` defeats type checking and enables runtime errors.

**Pydantic Benefits**:
- ✅ Compile-time type validation (catch errors before runtime)
- ✅ Automatic JSON serialization (no manual dict construction)
- ✅ Schema documentation (self-documenting API)
- ✅ Validation rules (enforce confidence ∈ [0.0, 1.0])

**Verdict**: Pydantic models mandatory for constitutional compliance.

## Consequences

### Positive

1. **Proactive Assistance**: Trinity gains ambient awareness, can detect user intent from verbal context without manual input
2. **Privacy Preservation**: 100% local processing builds user trust, enables use in sensitive environments (healthcare, legal)
3. **Constitutional Compliance**: Strict typing, complete context, comprehensive testing align with all articles
4. **Extensibility**: Message bus architecture allows future agents to consume ambient stream (e.g., SUMMARY agent for meeting notes)
5. **User Empowerment**: Instant mute, panic delete, privacy dashboard give users full control

### Negative

1. **Implementation Complexity**: Building audio capture, Whisper integration, privacy controls is substantial engineering effort (6 weeks estimated)
2. **Model Size**: 769MB Whisper model increases installation size, requires download/bundling strategy
3. **Battery Impact**: Even optimized, continuous audio capture and transcription will drain battery faster than no ambient listening
4. **Accuracy Limitations**: Whisper not perfect; transcription errors will propagate to WITNESS (mitigated by confidence thresholding)
5. **MacBook-Only**: Initial implementation excludes iOS, limiting use cases (future enhancement)

### Risks

1. **Privacy Violation via Bug**: Accidental network call or disk write would catastrophically breach user trust
   - **Mitigation**: Comprehensive privacy compliance test suite (verify zero network calls, zero disk writes), manual code review, open source transparency

2. **Whisper Performance Insufficient**: Transcription latency >2s or battery drain >5% makes system unusable
   - **Mitigation**: Benchmark multiple models (small, medium), use quantized GGML, Metal acceleration, fallback to smaller model if needed

3. **User Distrust**: Even with privacy guarantees, users may distrust ambient listening
   - **Mitigation**: Open source code, clear privacy dashboard, user education, instant mute capability

4. **Constitutional Violation (Article I)**: Publishing partial transcriptions (mid-sentence) leads to incorrect WITNESS patterns
   - **Mitigation**: Silence detection ensures complete utterances, validation before publishing

## Alternatives Considered

### Alternative 1: Cloud-Based Transcription (OpenAI Whisper API)

**Description**: Use OpenAI Whisper API for transcription (send audio to cloud, receive text)

**Pros**:
- ✅ Faster transcription (<1s vs 2s local)
- ✅ No local model storage (saves 769MB)
- ✅ Better accuracy (cloud models larger/more capable)
- ✅ Simpler implementation (REST API vs C library integration)

**Cons**:
- ❌ **PRIVACY VIOLATION**: Raw audio sent to OpenAI servers (dealbreaker)
- ❌ Requires internet connectivity (fails offline)
- ❌ Usage costs (per-second billing)
- ❌ Latency from network round-trip

**Why Rejected**: Privacy is non-negotiable. Cloud transcription fundamentally incompatible with privacy-first design. This alternative violates user trust and constitutional principles.

### Alternative 2: Browser-Based Speech Recognition (Web Speech API)

**Description**: Use browser's built-in speech recognition (Chrome Web Speech API)

**Pros**:
- ✅ No local model required (browser handles it)
- ✅ Simple JavaScript integration
- ✅ Real-time results (streaming transcription)

**Cons**:
- ❌ **CLOUD-DEPENDENT**: Web Speech API sends audio to Google servers
- ❌ Browser-locked (requires Chrome/Edge running)
- ❌ Limited control (no confidence scores, poor error handling)
- ❌ Privacy concerns (Google's terms of service)

**Why Rejected**: Same privacy violation as cloud APIs. Browser APIs not designed for privacy-first use cases.

### Alternative 3: Manual Transcription (User Types Context)

**Description**: No ambient listening; user manually types context into Trinity

**Pros**:
- ✅ Zero privacy risk (user controls all data)
- ✅ Zero implementation complexity
- ✅ Zero battery impact

**Cons**:
- ❌ **DEFEATS PROACTIVE ASSISTANCE**: User must manually log every intent, breaking workflow
- ❌ Missed context (users forget to log, lose ideas)
- ❌ High friction (typing interrupts focus)

**Why Rejected**: Does not solve the core problem (proactive assistance from ambient context). This is the status quo we're improving upon.

### Alternative 4: Lightweight Keyword Detection (not Full Transcription)

**Description**: Use lightweight keyword spotting (e.g., Porcupine) to detect trigger phrases, only transcribe when activated

**Pros**:
- ✅ Lower battery impact (keyword detection cheaper than full transcription)
- ✅ Smaller model size (keyword models <10MB)
- ✅ Privacy-friendly (only transcribe when triggered)

**Cons**:
- ❌ **MISSES CONTEXT**: User must say trigger phrase ("Hey Trinity") before ambient listening starts
- ❌ Requires training (custom keywords for user's workflow)
- ❌ False negatives (user forgets trigger phrase, context lost)

**Why Rejected**: Trigger-based activation defeats ambient awareness. We want continuous context, not reactive activation.

## Implementation Notes

### Key Implementation Considerations

1. **Whisper.cpp Integration**: Use `ctypes` or `cffi` for Python bindings. Whisper.cpp exposes C API:
   ```c
   struct whisper_context* whisper_init_from_file(const char* path_model);
   int whisper_full(struct whisper_context* ctx, struct whisper_full_params params, const float* samples, int n_samples);
   const char* whisper_full_get_segment_text(struct whisper_context* ctx, int i_segment);
   ```

2. **Metal Acceleration**: Enable GPU inference on M4 Pro:
   ```python
   # In whisper_transcriber.py
   params = whisper_full_default_params(WHISPER_SAMPLING_GREEDY)
   params.use_gpu = True  # Enable Metal backend
   ```

3. **Silence Detection**: Implement using RMS (Root Mean Square) audio analysis:
   ```python
   def detect_silence(audio_chunk, threshold_db=-40, min_duration_s=2.0):
       rms = np.sqrt(np.mean(audio_chunk ** 2))
       db = 20 * np.log10(rms) if rms > 0 else -100
       return db < threshold_db  # True if silence
   ```

4. **Message Bus Publishing**:
   ```python
   from trinity_protocol.message_bus import MessageBus
   from ambient_intelligence.models import AmbientTranscription

   async def publish_transcription(bus: MessageBus, text: str, confidence: float):
       transcription = AmbientTranscription(
           content=text,
           confidence=confidence,
           metadata=TranscriptionMetadata(
               audio_duration_ms=1500,
               chunk_id=str(uuid.uuid4()),
               silence_detected=True,
               model_name="ggml-medium.en"
           )
       )
       await bus.publish(
           queue_name="personal_context_stream",
           message=transcription.dict(),
           priority=0  # NORMAL
       )
   ```

5. **Privacy Compliance Testing**:
   ```python
   # tests/ambient_intelligence/test_privacy_compliance.py
   import psutil
   import subprocess

   def test_no_network_calls_during_transcription():
       # Start ambient listener
       process = start_ambient_listener()

       # Monitor network I/O for 60 seconds
       net_before = psutil.net_io_counters()
       time.sleep(60)
       net_after = psutil.net_io_counters()

       # Assert zero bytes sent (allow received for OS background traffic)
       bytes_sent = net_after.bytes_sent - net_before.bytes_sent
       assert bytes_sent == 0, f"Privacy violation: {bytes_sent} bytes sent to network"
   ```

### Dependencies Required

**Python Libraries** (add to `pyproject.toml`):
```toml
[tool.poetry.dependencies]
pyaudio = "^0.2.13"  # or sounddevice as alternative
numpy = "^1.26.0"
pydantic = "^2.4.0"
```

**System Dependencies** (install via Homebrew):
```bash
brew install portaudio  # Required for PyAudio
brew install ffmpeg     # Whisper.cpp dependency
```

**Whisper.cpp** (build from source):
```bash
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make  # Compiles libwhisper.so (or .dylib on macOS)
./models/download-ggml-model.sh medium.en  # Download model
```

### Migration Path

**Phase 1 (Week 1-2)**: Foundation
- Implement audio capture, Whisper.cpp integration
- Unit tests for transcription accuracy, latency
- Local testing only (no Trinity integration yet)

**Phase 2 (Week 3)**: Trinity Integration
- Message bus client, publish to `personal_context_stream`
- WITNESS agent receives transcriptions
- End-to-end pipeline verified

**Phase 3 (Week 4)**: Privacy Controls
- Mute functionality, menu bar UI
- Privacy compliance tests (zero network, zero disk)
- Privacy dashboard

**Phase 4 (Week 5-6)**: Optimization & Beta
- Battery benchmarks, model selection
- User documentation, beta testing
- Final constitutional compliance audit

### Timeline Estimates

- **Research & Prototyping**: 1 week
- **Core Implementation**: 3 weeks
- **Privacy & Testing**: 1 week
- **Optimization & Documentation**: 1 week
- **Total**: 6 weeks for production-ready system

## References

### Technical Documentation
- **Whisper.cpp**: https://github.com/ggerganov/whisper.cpp
- **OpenAI Whisper**: https://github.com/openai/whisper (original model)
- **GGML Quantization**: https://github.com/ggerganov/ggml
- **macOS CoreAudio**: https://developer.apple.com/documentation/coreaudio
- **PyAudio**: https://people.csail.mit.edu/hubert/pyaudio/

### Related ADRs
- **ADR-004**: Continuous Learning and Improvement (learning from ambient context)
- **ADR-007**: Spec-Driven Development (process followed for this ADR)
- **ADR-001**: Complete Context Before Action (no partial transcriptions)
- **ADR-002**: 100% Verification and Stability (comprehensive testing)

### Related Specifications
- **Spec-017**: Ambient Intelligence System (full specification)
- **WITNESS Agent**: `docs/trinity_protocol/WITNESS.md`
- **Trinity Protocol**: `docs/trinity_protocol_implementation.md`

### Privacy & Compliance
- **GDPR Article 6**: Lawfulness of processing (user consent required)
- **HIPAA Privacy Rule**: Protected health information (PHI) safeguards
- **California Consumer Privacy Act**: Right to deletion (panic delete feature)

---

## Approval

**Proposed by**: ChiefArchitectAgent
**Date**: 2025-10-01
**Status**: Awaiting stakeholder review

**Review Checklist**:
- [x] Privacy-first design (100% local processing)
- [x] Constitutional compliance (Articles I, II, IV, V)
- [x] Technical feasibility (Whisper.cpp proven, M4 Pro capable)
- [x] User control (mute, panic delete, transparency)
- [x] Performance targets (latency, battery, memory)
- [x] Comprehensive testing strategy (privacy compliance tests)
- [x] Clear implementation plan (6-week timeline)

**Next Steps**:
1. Stakeholder review (@am approval)
2. Technical review (AuditorAgent, QualityEnforcerAgent)
3. Privacy audit (external privacy review recommended)
4. Upon approval: Create technical plan (`plan-017-ambient-listener.md`)
5. Implementation begins (Phase 1: Foundation)

---

*"Privacy is not a feature you add at the end. It is a principle you design from the beginning."*
