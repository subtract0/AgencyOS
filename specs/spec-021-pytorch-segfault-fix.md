# SPEC-021: Fix PyTorch Segfault During Parallel Testing

**Status**: CRITICAL - Tests crash consistently
**Created**: 2025-10-10
**Author**: Claude Code (Opus)

## 1. Problem Statement

**Critical Issue**: Python crashes with segmentation fault when running tests with multiple workers
- **Impact**: Tests cannot run in parallel (3x slower)
- **Frequency**: Every test run with multiple workers
- **Location**: vector_store.py:82 → sentence_transformers → torch import

**Stack Trace Analysis**:
```
Fatal Python error: Segmentation fault
...
File "/Users/am/Code/Agency/.venv/lib/python3.13/site-packages/torch/__init__.py", line 416 in <module>
...
File "/Users/am/Code/Agency/agency_memory/vector_store.py", line 82 in _init_sentence_transformers
```

## 2. Root Cause

**Primary Cause**: PyTorch/transformers unsafe parallel initialization
- Multiple pytest workers (gw0, gw1, gw2) import torch simultaneously
- PyTorch's C++ extension loader is not thread-safe during first import
- Race condition in torch._C module creation causes segfault

**Secondary Factors**:
1. Python 3.13.7 (newer than tested versions)
2. Apple Silicon (current hardware) Metal Performance Shaders
3. pytest-xdist parallel execution (-n 3)

## 3. Solution Options

### Option A: Force Sequential Import (Quick Fix)
- Import torch/transformers at module level (not in __init__)
- Use import lock around initialization
- **Pros**: Fast fix, minimal changes
- **Cons**: Still fragile with multiprocessing

### Option B: Lazy Import with Singleton (Recommended)
- Create singleton embedder that initializes once
- Use threading.Lock for import safety
- Lazy load only when embeddings needed
- **Pros**: Safe, efficient, production-ready
- **Cons**: Requires refactoring

### Option C: Disable Parallel Testing (Workaround)
- Set PYTEST_ADDOPTS="-n 1"
- **Pros**: Works immediately
- **Cons**: 3x slower tests (unacceptable)

## 4. Implementation Plan

**Phase 1: Immediate Mitigation**
1. Add import guard to vector_store.py
2. Pre-import torch in conftest.py
3. Set environment variables for safety

**Phase 2: Proper Fix**
1. Refactor to singleton embedder
2. Add thread-safe initialization
3. Test with parallel workers

## 5. Acceptance Criteria

- [ ] Tests run with -n 3 without segfault
- [ ] No performance regression
- [ ] Thread-safe initialization verified
- [ ] CI pipeline passes with parallel testing
- [ ] Documentation of known issues

## 6. Testing Strategy

1. Run tests with increasing worker counts (1, 2, 3, 4)
2. Stress test with 100 parallel imports
3. Verify on multiple Python versions (3.11, 3.12, 3.13)
4. Test on both Intel and Apple Silicon

## 7. Risk Mitigation

- Rollback: Revert to sequential testing if fix fails
- Monitoring: Add crash detection to CI
- Documentation: Document in README.md
- Long-term: Consider replacing sentence-transformers