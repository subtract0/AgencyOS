# Anthropic Memory Tool Integration Plan

**Generated**: 2025-10-05
**Status**: ✅ COMPLETE - All phases implemented and tested
**Actual Time**: ~4 hours (Phase 1-3 complete, Phase 4 CLI command skipped)
**Beta**: `context-management-2025-06-27`

---

## Overview

Integrate Anthropic's **Memory Tool** (beta) into Agency OS to enable Claude to maintain persistent memory across conversations through a file-based directory system.

**Key Benefits**:
- Cross-conversation learning (build knowledge over time)
- Persistent context without bloating context windows
- Client-side control (we manage where/how data is stored)
- Automatic memory management (Claude handles read/write/organize)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Anthropic API (Claude Sonnet 4.5)                      │
│ Beta: context-management-2025-06-27                    │
└────────────────┬────────────────────────────────────────┘
                 │ Memory tool calls (JSON)
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Agency Memory Tool Handler                             │
│ (tools/anthropic_memory_tool.py - NEW)                │
│                                                         │
│ Implements BetaAbstractMemoryTool:                     │
│  - view(path, view_range)                              │
│  - create(path, file_text)                             │
│  - str_replace(path, old_str, new_str)                 │
│  - insert(path, insert_line, insert_text)              │
│  - delete(path)                                        │
│  - rename(old_path, new_path)                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ File-Based Storage Backend                             │
│ (~/.agency/memories/ or configurable path)             │
│                                                         │
│ Security:                                               │
│  ✅ Path validation (restrict to /memories)            │
│  ✅ Traversal attack prevention (../ blocked)         │
│  ✅ Size limits (prevent unbounded growth)             │
│  ✅ Expiration (optional auto-cleanup)                 │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

### ✅ Phase 1: Setup (30 min) - COMPLETE
- [x] Plan approved and documented
- [x] Update `requirements.txt` to `anthropic>=0.42.0`
- [x] Install updated Anthropic SDK (v0.69.0 via uv)
- [x] Test beta access with test script
- [x] Verify beta header works

### ✅ Phase 2: Core Implementation (4 hours) - COMPLETE
- [x] Create `tools/anthropic_memory_tool.py`
- [x] Implement `AgencyMemoryTool` class
- [x] Implement 6 memory commands (view, create, str_replace, insert, delete, rename)
- [x] Add path validation (traversal protection, URL encoding)
- [x] Create SDK integration helper (`tools/anthropic_agent_with_memory.py`)
- [x] Test basic operations

### ✅ Phase 3: Security (2 hours) - COMPLETE
- [x] Create security tests (`tests/test_anthropic_memory_security.py`)
- [x] Test path traversal protection (6 attack vectors)
- [x] Add file size limits (1MB default)
- [x] Verify security tests passing (30/30 tests pass)

### ✅ Phase 4: Integration (3 hours) - COMPLETE (CLI command skipped)
- [x] Update `AgentContext` (enable_anthropic_memory, get_anthropic_memory_tool)
- [ ] Add CLI command (skipped - not essential for core functionality)
- [x] Create demo script (`demo_anthropic_memory.py`)
- [x] Update documentation (CLAUDE.md section added)

---

## File Locations

### New Files to Create
1. `tools/anthropic_memory_tool.py` - Core memory tool implementation
2. `tools/anthropic_agent_with_memory.py` - SDK integration helper
3. `tests/test_anthropic_memory_security.py` - Security tests
4. `scripts/test_anthropic_memory_beta.py` - Beta access test
5. `demo_anthropic_memory.py` - Demo script
6. `docs/ANTHROPIC_MEMORY_TOOL_INTEGRATION_PLAN.md` - This plan

### Files to Modify
1. `requirements.txt` - Update anthropic version
2. `shared/agent_context.py` - Add memory tool enablement
3. `agency.py` - Add memory CLI command
4. `CLAUDE.md` - Add usage documentation

---

## Success Criteria

- ✅ Claude can create/read/edit/delete memory files via API
- ✅ Memory persists across conversation sessions
- ✅ Path traversal attacks blocked (security tests pass)
- ✅ File size limits prevent unbounded growth
- ✅ Integration with AgentContext works
- ✅ Demo script runs successfully

---

## Timeline

| Phase | Time | Cumulative |
|-------|------|------------|
| Phase 1: Setup | 30 min | 30 min |
| Phase 2: Core | 4 hours | 4.5 hours |
| Phase 3: Security | 2 hours | 6.5 hours |
| Phase 4: Integration | 3 hours | 9.5 hours |
| **TOTAL** | **~10 hours** | **1.5 days** |

---

For full implementation details, see this document's planning section.
