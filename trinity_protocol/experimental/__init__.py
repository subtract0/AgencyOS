"""Trinity Protocol Experimental - Prototypes & Research

⚠️ WARNING: Modules in this directory are EXPERIMENTAL ⚠️

Experimental modules:
- May have incomplete tests or no tests
- May have privacy/security concerns
- May require external dependencies
- May change rapidly without notice
- Are NOT suitable for production use

**Privacy Notice**:
Some experimental modules access sensitive data (audio, ambient listening).
Always obtain explicit user consent before using these modules.

**Upgrade Path**:
See docs/TRINITY_UPGRADE_CHECKLIST.md for steps to promote
experimental modules to production status.

**Production Criteria**:
- ✅ 100% test coverage (all paths tested)
- ✅ Strict Pydantic typing (no Dict[Any, Any])
- ✅ Constitutional compliance (Articles I-V)
- ✅ Result<T,E> error handling
- ✅ Functions <50 lines
- ✅ Comprehensive documentation
"""

# Experimental modules (marked as NOT production-ready)
# Import with caution - these modules have known limitations

__all__ = [
    "AmbientPatternDetector",
    "AmbientListener",
    "AudioCaptureModule",
    "WhisperTranscriber",
    "ConversationContext",
    "TranscriptionService",
    "ResponseHandler",
]

# Note: Imports are deferred to avoid import errors from missing dependencies
# Users must explicitly import: from trinity_protocol.experimental.ambient_patterns import AmbientPatternDetector
