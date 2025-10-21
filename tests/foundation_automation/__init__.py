"""Foundation automation workflow test suite.

Tests for /primeA orchestrator covering:
- E2E natural language → PR flow
- Backlog auto-selection mechanism
- Git validation (Phase 0)
- Flag behavior (--two-stage, --no-pr, --plan-only, etc.)
- Constitutional gates (Articles I-V enforcement)
- Graceful fallbacks (VectorStore, TRM, local model, API, pre-commit)

Constitutional Compliance:
- Article I: Complete context (retry logic, no timeouts)
- Article II: 100% verification (test pass rate)
- Article III: Automated enforcement (no manual bypasses)
- Article IV: VectorStore learning integration
- Article V: Spec-driven (SPEC-030 traceability)

NECESSARY Pattern Coverage:
- N: Normal operation paths
- E: Edge cases and boundary conditions
- C: Constraints validation
- E: Error handling and recovery
- S: Security (injection, traversal)
- S: Scale (performance benchmarks)
- A: Asynchronous operations
- R: Retry logic (exponential backoff)
- Y: Yield/generator (if applicable)
"""
