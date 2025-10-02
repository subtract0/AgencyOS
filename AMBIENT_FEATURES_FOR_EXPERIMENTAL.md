# Ambient Features for Experimental Migration

## Overview
The following features have been identified as **experimental** and should be migrated to `trinity_protocol/experimental/` in Phase 3.

## Ambient-Specific Modules (Already Separated)

### 1. `witness_ambient_mode.py` (Experimental Pattern Detection)
**Location**: `trinity_protocol/witness_ambient_mode.py`
**Size**: ~450 lines
**Purpose**: Ambient-specific pattern detection for conversation transcriptions

**Features**:
- Recurring topic detection (mentioned 3+ times)
- Project mentions tracking
- Frustration detection
- Action item extraction
- Conversation context analysis

**Dependencies**:
- `ConversationContext` (ambient-specific)
- `PersistentStore`
- Pydantic models from `core/models/patterns.py`

**Migration Target**: `trinity_protocol/experimental/ambient_patterns.py`

---

### 2. `ambient_listener_service.py` (Audio Capture Service)
**Location**: `trinity_protocol/ambient_listener_service.py`
**Size**: ~350 lines
**Purpose**: Background audio capture and transcription service

**Features**:
- Continuous audio monitoring
- Whisper transcription integration
- Conversation buffering
- Pattern signal publishing

**Dependencies**:
- `audio_capture.py`
- `whisper_transcriber.py`
- `ConversationContext`
- `WitnessAgent` (for pattern publishing)

**Migration Target**: `trinity_protocol/experimental/audio_service.py`

---

### 3. `audio_capture.py` (Audio Recording)
**Location**: `trinity_protocol/audio_capture.py`
**Size**: ~300 lines
**Purpose**: Low-level audio recording with PyAudio

**Features**:
- Microphone stream management
- Audio buffer recording
- WAV file export
- Resource cleanup

**Migration Target**: `trinity_protocol/experimental/audio_capture.py`

---

### 4. `whisper_transcriber.py` (Speech-to-Text)
**Location**: `trinity_protocol/whisper_transcriber.py`
**Size**: ~330 lines
**Purpose**: OpenAI Whisper transcription wrapper

**Features**:
- Local Whisper model integration
- Audio file transcription
- Batch processing support
- Error handling

**Migration Target**: `trinity_protocol/experimental/transcription.py`

---

### 5. `conversation_context.py` (Ambient Context)
**Location**: `trinity_protocol/conversation_context.py`
**Size**: ~350 lines
**Purpose**: Conversation window management for ambient mode

**Features**:
- Sliding window context (10 min default)
- Transcript buffering
- Topic tracking
- Context persistence

**Migration Target**: `trinity_protocol/experimental/conversation_context.py`

---

### 6. `transcription_service.py` (Transcription Queue)
**Location**: `trinity_protocol/transcription_service.py`
**Size**: ~230 lines
**Purpose**: Async transcription queue management

**Features**:
- Background transcription processing
- Audio file queue
- Result publishing
- Error recovery

**Migration Target**: `trinity_protocol/experimental/transcription_queue.py`

---

## Production Core Modules (Already Migrated ✅)

### 1. `core/witness.py` (Pattern Detection - Production)
**Status**: ✅ Migrated
**Size**: 318 lines
**Purpose**: Stateless pattern detection for telemetry/context streams

**Features** (Production-Ready):
- 8-step processing loop (LISTEN → RESET)
- Pattern classification
- Signal validation
- Telemetry/context stream monitoring
- PersistentStore integration

---

### 2. `core/orchestrator.py` (Trinity Coordination)
**Status**: ✅ Migrated
**Size**: 210 lines
**Purpose**: Token-efficient Trinity Protocol coordination

**Features**:
- JSONL message bus
- Agent coordination (ARCHITECT, EXECUTOR, WITNESS)
- Synchronous workflow
- Minimal state files

---

### 3. `core/executor.py` (Executor Agent)
**Status**: ✅ Migrated (Previous phase)
**Size**: ~550 lines
**Purpose**: Meta-orchestrator for spawning Claude Code agents

---

### 4. `core/architect.py` (Architect Agent)
**Status**: ✅ Migrated (Previous phase)
**Size**: ~500 lines
**Purpose**: Strategic planning and ROI analysis

---

## Migration Plan (Phase 3)

### Step 1: Create Experimental Directory Structure
```
trinity_protocol/experimental/
├── __init__.py
├── ambient_patterns.py      (witness_ambient_mode.py)
├── audio_service.py          (ambient_listener_service.py)
├── audio_capture.py          (audio_capture.py)
├── transcription.py          (whisper_transcriber.py)
├── conversation_context.py   (conversation_context.py)
└── transcription_queue.py    (transcription_service.py)
```

### Step 2: Update Imports
- Change imports to use `trinity_protocol.experimental.*`
- Update any cross-references between ambient modules
- Ensure no production code depends on experimental features

### Step 3: Add Experimental Warnings
```python
import warnings

def __init__():
    warnings.warn(
        "Ambient features are experimental and not production-ready. "
        "Use at your own risk.",
        ExperimentalWarning,
        stacklevel=2
    )
```

### Step 4: Documentation
- Create `trinity_protocol/experimental/README.md`
- Document experimental status and known limitations
- Provide usage examples for ambient mode

---

## Summary

**Production Core (Migrated)**: 4 modules, ~1,578 lines
**Experimental Ambient (To Migrate)**: 6 modules, ~2,010 lines

**Next Session Action**:
```bash
# Create experimental directory
mkdir -p trinity_protocol/experimental

# Move ambient modules
mv trinity_protocol/witness_ambient_mode.py trinity_protocol/experimental/ambient_patterns.py
mv trinity_protocol/ambient_listener_service.py trinity_protocol/experimental/audio_service.py
# ... (continue for other modules)

# Update imports and add experimental warnings
```

**Validation Criteria**:
- ✅ All production code in `core/` has 100% test coverage
- ✅ No production code imports from `experimental/`
- ✅ Experimental modules have clear warnings
- ✅ Documentation clearly separates production vs experimental
