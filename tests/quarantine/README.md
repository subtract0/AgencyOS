# Quarantined Test Suites

These suites are temporarily excluded from automated runs (see `run_tests.py` ignores)
because they are unstable or hang locally. Track remediation work here so we can restore
them once fixed.

| File | Reason | Status |
|------|--------|--------|
| `tests/benchmarks/test_vectorstore_performance.py` | FAISS-based benchmark leaks native memory and intermittently segfaults even with sequential execution (see `TEST_FAILURE_INVENTORY.md`). | Needs subprocess isolation or mocked benchmarks before re-enabling. |
| `tests/test_checkpoint_manager.py` | Hangs around test 9/20 in macOS Python 3.13 environments; root cause under investigation. | Awaiting repro + fix plan. |

While quarantined, these suites are still available for manual execution (run directly via
`pytest path::test_name`). Document progress in this README and remove entries once the
suite can run reliably inside the standard test runner.
