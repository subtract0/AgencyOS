# Next Steps: Test Suite Recovery

## Quick Start

Execute the autonomous recovery mission:

```bash
/primeA --graph missions/test_suite_recovery_mission.json --visualize
```

## What Was Diagnosed

1. **Segfault at socket.py:295** - pytest-rerunfailures plugin + Python 3.13 + async tests
2. **Double Test Execution** - run_tests.py runs pytest twice (causing 51% hang)
3. **Vectorstore Performance Crash** - PyTorch memory issue (segfaults even sequentially)
4. **Checkpoint Manager Hang** - Deadlock at test 9/20
5. **~78 Assertion Failures** - Mix of bugs, outdated tests, broken features

## Mission Plan

- **Location**: `missions/test_suite_recovery_mission.json`
- **Documentation**: `missions/test_suite_recovery_plan.md`
- **Phases**: 5 (Diagnostic → Blockers → Assertions → Config → Verification)
- **Tasks**: 16 total
- **Estimated**: ~65k tokens (~$2.50 USD)

## Success Criteria

- Zero segfaults
- Zero hangs
- 100% test pass rate (excluding documented skips)
- 3 consecutive clean runs
- Execution time <10 minutes
- ADR-030 documenting recovery

## Constitutional Significance

**Article II Compliance**: "100% Verification and Stability"

This mission will restore the test suite to 100% green, re-enabling fully autonomous development.

---

**Ready for autonomous execution. Human-out-of-the-loop after `/primeA` invocation.**
