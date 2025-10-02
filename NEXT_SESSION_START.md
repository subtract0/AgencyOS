# Next Session Mission Brief

**Date:** 2025-10-02
**Status:** Test suite has 11 failures - main NOT green
**Priority:** Fix failing tests BEFORE any new features

---

## 🔥 BLOCKER: 11 Test Failures

Test suite timeout after 5min with failures detected in:
1. `tests/dspy_agents/test_toolsmith_agent.py` - 6 failures
2. `tests/test_learning_agent.py` - 4 failures
3. Other scattered failures

**Constitutional Violation:** Article II requires 100% test pass - cannot proceed with new work until green.

---

## ✅ What's Actually Done

1. **PLAN.md Fixed** - Removed misleading "ADR-018 not implemented" claim
2. **Timeout Wrapper Exists** - `shared/timeout_wrapper.py` is production-ready (298 lines)
3. **Background Trinity Simulations Killed** - Cleaned up /tmp processes
4. **Reality Check Complete** - Documented actual vs. aspirational state

---

## 🎯 Immediate Next Steps

### 1. Fix Failing Tests (HIGHEST PRIORITY)
```bash
# Run specific failing test files
python run_tests.py tests/dspy_agents/test_toolsmith_agent.py
python run_tests.py tests/test_learning_agent.py
```

**Root Cause Analysis Needed:**
- Toolsmith failures likely DSPy integration issues
- Learning agent failures may be VectorStore/memory related

### 2. Verify Green Main
```bash
python run_tests.py --run-all  # Must show 100% pass
```

### 3. ONLY THEN: Ambient Listener Implementation

**User Request:** Voice transcription + Gmail Zoom transcript ingestion

**Implementation Plan:**
- **Local Transcription:** whisper.cpp (Metal GPU acceleration, 100% on-device)
- **Gmail Integration:** MCP gmail server for fetching Zoom AI summaries
- **Storage:** Firestore for persistent conversation history
- **Privacy:** Memory-only audio buffer, never written to disk

**Spec Location:** `docs/adr/ADR-016-ambient-listener-architecture.md` (already exists!)

---

## 📋 User's Voice Capture Requirements

**Exact User Request:**
> "I want my voice to be saved and that data to be later used"

**Technical Approach:**
1. **Whisper.cpp** local inference (whisper-1 model, Metal acceleration)
2. **Audio → Text** streaming buffer (never persisted to disk)
3. **Firestore** for text transcripts only
4. **Gmail MCP** for fetching 50+ Zoom AI-generated coaching summaries

**Gmail Access via MCP:**
- User has "50+ emails from Zoom AI-Assistant" with group coaching transcripts
- Use Gmail MCP server to fetch and ingest these for pattern learning
- Feed into VectorStore for cross-session pattern recognition

---

## 🚨 Constitutional Reminder

**Article II:** A task is complete ONLY when 100% verified and stable.

**Current Status:** ❌ NOT STABLE (11 test failures)

**Action:** Fix tests FIRST. No new features until green.

---

## 📊 Metrics (Pre-Fix)

- **Tests Passing:** ~2948/2959 (99.6% - NOT ACCEPTABLE)
- **Failures:** 11 (primarily DSPy toolsmith + learning agent)
- **Article I Compliance:** 90/100 (2/35 tools have timeout wrapper)
- **Main Branch:** ❌ NOT GREEN

---

## 🎬 Session Start Command

```bash
/prime_cc  # Load context
# THEN immediately:
python run_tests.py tests/dspy_agents/test_toolsmith_agent.py -v
# Fix failures one by one
# Verify: python run_tests.py --run-all
```

---

*"In automation we trust, in discipline we excel, in learning we evolve."*

**PRIORITY: DELETE THE FIRE FIRST** (Article II)
