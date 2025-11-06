## Top-Level Suite Manual Verification

- **Date**: 2025-11-06
- **Command**:
  ```bash
  PYTHONMALLOC=malloc \
  .venv/bin/python -m pytest \
    tests/test_leap3_e2e_integration.py \
    tests/test_leap3_m5_validation.py \
    tests/test_leap4_e2e_quality_feedback.py \
    tests/test_leap5_phase1_integration.py \
    tests/test_leap5_phase2_integration.py \
    tests/test_leap5_phase3_e2e.py \
    tests/test_leap5_phase4_e2e.py \
    -m "not slow" --ff --maxfail=1 --timeout=30 --timeout-method=thread -vv
  ```
- **Result**: 65 selected tests passed, 11 deselected, 0 failures.
- **Notes**:
  - Command uses the same flags as the CI top-level shards (timeout + `not slow` marker) to mirror runner behavior.
  - Full console transcript captured locally (available on request) and summarized here to avoid bloating the repository.
  - Re-run this command locally whenever `run_top_level=true` is not used in `workflow_dispatch`. Attach updated timestamp + summary before merging changes that affect Leap suites.

