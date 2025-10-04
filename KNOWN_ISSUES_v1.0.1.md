# Known Issues - v1.0.1

## Test Infrastructure Timeout (In Progress)

**Issue**: Full test suite hangs/times out after 10 minutes, even with optimizations applied.

**Status**: Under investigation for v1.0.2

**Details**:
- Individual test files pass quickly (<2s per file)
- Full suite with 2,334 tests times out at 10 minutes
- Applied fixes in v1.0.1:
  - ✅ Changed pytest-xdist workers from 4 to 8
  - ✅ Removed 731 experimental tests (bloat deletion)
- Remaining issue: Test infrastructure (conftest.py, fixtures, or resource contention)

**Workaround**: Run tests by directory or individual files:
```bash
# By directory
python run_tests.py tests/test_agency*.py

# By category
python run_tests.py --fast  # Fast tests only
python run_tests.py tests/unit/

# Individual files
uv run pytest tests/test_agency.py -v
```

**Next Steps** (v1.0.2):
1. Deep debug conftest.py session-scoped fixtures
2. Identify resource-intensive or blocking operations
3. Check for circular dependencies or deadlocks
4. Profile slowest tests with `--durations=0`

**Root Cause Hypothesis**:
- Session-scoped fixtures with external resources (database, network, file locks)
- Async event loop conflicts in parallel execution
- Resource exhaustion with 8 parallel workers

**Priority**: HIGH (blocks full CI validation)

**Assigned**: Test Infrastructure Team (v1.0.2 milestone)

---

## Changes in v1.0.1

### Fixed
- ✅ pytest-xdist worker count optimized (4 → 8 workers)
- ✅ Experimental test bloat removed (731 tests deleted)
- ✅ Test runtime improved (estimated 73s faster with bloat removal)

### Added
- ✅ Phase 2A/2B documentation (13 files)
- ✅ Vital functions catalog (105 functions identified)
- ✅ 3-week Mars compliance roadmap

### Deferred to v1.0.2
- ❌ Full test suite stability (infrastructure debug needed)
- ❌ 100% CI validation (blocked by timeout issue)

---

**Date**: 2025-10-04
**Version**: 1.0.1
**Next Review**: v1.0.2 planning
