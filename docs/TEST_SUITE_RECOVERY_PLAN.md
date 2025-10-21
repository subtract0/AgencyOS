# 🚨 Test Suite Recovery Plan: From RED to GREEN

## Executive Summary

**Current Crisis**: 61 failing tests blocking main branch health
**Root Cause**: Incomplete GREEN phase implementation after TDD RED phase
**Solution**: Systematic implementation of missing components with parallel execution

## 📊 Current State Analysis

### Test Status (Foundation Automation)
- ✅ **19 tests passing** (23%)
- ❌ **61 tests failing** (74%)
- ⚠️ **1 test error** (1%)
- 🎯 **Target: 100% pass rate**

### Failure Categories

| Category | Count | Root Cause | Priority |
|----------|-------|------------|----------|
| Gates Tests | 14 | Missing `foundation_automation_gates.py` module | P1 |
| Fallback Tests | 13 | Missing `FallbackHandler` class | P1 |
| Flag Tests | 20 | Incomplete `_handle_flags()` implementation | P2 |
| Git Validation | 9 | Attribute errors & mock issues | P2 |
| E2E Tests | 5 | Missing methods & mock issues | P3 |

## 🎯 Recovery Strategy

### Phase-by-Phase Execution Plan

#### **Phase 1: Quick Wins (30 minutes)**
Fix simple issues that unblock many tests:
- Fix `GitValidationError.reason` attribute issue
- Add missing imports
- Fix test fixtures

#### **Phase 2: Core Implementations (2 hours)**
Create missing modules with parallel agents:
- `foundation_automation_gates.py` (unblocks 14 tests)
- `fallback_handler.py` (unblocks 13 tests)
- Enhanced `_handle_flags()` (unblocks 20 tests)

#### **Phase 3: Integration (1 hour)**
- Connect all components
- Fix mocking issues
- Verify no regressions

#### **Phase 4: Validation (30 minutes)**
- Run full test suite
- Verify constitutional compliance
- Create PR

## 🔧 Technical Implementation Details

### 1. Gates Module (`tools/orchestrator/foundation_automation_gates.py`)

```python
from typing import Optional
from pydantic import BaseModel
from shared.type_definitions.result import Result, Ok, Err

class FoundationGateError(Exception):
    """Raised when a constitutional gate validation fails."""
    pass

class GateValidationResult(BaseModel):
    """Result of gate validation."""
    gate_id: str
    passed: bool
    message: str
    article: Optional[int]  # Constitutional article (I-V)

# 12 Gate validation functions
def validate_complete_graph(graph) -> Result[None, FoundationGateError]:
    """GATE-001: Article I - Validate graph completeness."""
    # Implementation here

def validate_timeout_retry(timeout_count) -> Result[None, FoundationGateError]:
    """GATE-002: Article I - Validate retry protocol."""
    # Implementation here

# ... 10 more gate functions

def validate_all_gates(context) -> Result[GateValidationResult, FoundationGateError]:
    """Validate all 12 constitutional gates."""
    # Run all validations, early exit on first failure
```

### 2. Fallback Handler (`tools/orchestrator/fallback_handler.py`)

```python
import time
from typing import Any, Optional
from shared.type_definitions.result import Result, Ok, Err

class FallbackHandler:
    """Handles graceful degradation when services unavailable."""

    def __init__(self):
        self.retry_delays = [1, 2, 4, 8]  # Exponential backoff

    def handle_vectorstore_unavailable(self) -> dict:
        """FALLBACK-001: VectorStore unavailable."""
        logger.warning("VectorStore unavailable - using empty memories")
        return {"memories": [], "fallback": True}

    def handle_trm_unavailable(self, graph) -> Result:
        """FALLBACK-002: TRM unavailable - Python validation."""
        logger.warning("TRM unavailable - using Python DAG validation")
        # Python-only validation
        return Ok(None)

    # ... 5 more fallback methods
```

### 3. Flag Routing Enhancements

```python
# In UnifiedPrimeAOrchestrator._handle_flags()

def _handle_flags(self, flags: Optional[Dict]) -> Dict:
    """Enhanced flag handling with all behaviors."""

    if not flags:
        return {}

    normalized = {}

    # FLAG-001: --two-stage routing
    if flags.get("two-stage") or flags.get("two_stage"):
        normalized["route_to"] = "TwoStageOrchestrator"
        normalized["two_stage"] = True

    # FLAG-002: --plan-only
    if flags.get("plan-only") or flags.get("plan_only"):
        normalized["plan_only"] = True
        normalized["skip_execution"] = True

    # FLAG-006: --force with audit logging
    if flags.get("force"):
        self._log_force_override()  # HMAC-signed audit trail
        normalized["force_budget"] = True

    # Detect conflicts
    if normalized.get("plan_only") and normalized.get("auto_pr"):
        raise ValueError("Conflicting flags: --plan-only and --auto-pr")

    return normalized
```

## 🚀 Execution Commands

### Step 1: Create Missing Modules
```bash
# Use parallel agents to create modules
/primeA "Create foundation_automation_gates.py with 12 gate functions"
/primeA "Create fallback_handler.py with 7 fallback methods"
```

### Step 2: Run Targeted Tests
```bash
# Test gates implementation
pytest tests/orchestrator/test_foundation_automation_gates.py -v

# Test fallback handler
pytest tests/orchestrator/test_foundation_automation_fallbacks.py -v

# Test flags
pytest tests/orchestrator/test_foundation_automation_flags.py -v
```

### Step 3: Full Validation
```bash
# All foundation tests
pytest tests/orchestrator/test_foundation_automation_*.py -v

# Full suite
python run_tests.py --run-all
```

## 📈 Success Metrics

| Checkpoint | Target | Command |
|------------|--------|---------|
| Gates Tests | 14/14 passing | `pytest test_foundation_automation_gates.py` |
| Fallback Tests | 13/13 passing | `pytest test_foundation_automation_fallbacks.py` |
| Flag Tests | 20/20 passing | `pytest test_foundation_automation_flags.py` |
| Git Tests | 17/17 passing | `pytest test_foundation_automation_git_validation.py` |
| E2E Tests | 8/8 passing | `pytest test_foundation_automation_e2e.py` |
| **TOTAL** | **82/82 passing** | `pytest test_foundation_automation_*.py` |

## 🎯 Why This Will Work

1. **Root Cause Addressed**: Missing implementations are the primary issue, not logic errors
2. **Parallel Execution**: Multiple agents can work on independent modules simultaneously
3. **Clear Boundaries**: Each module has well-defined interfaces from tests
4. **TDD Guidance**: Tests tell us exactly what to implement
5. **No Guesswork**: Test assertions define expected behavior precisely

## 🔥 Quick Start for Immediate Action

```bash
# 1. Launch the task graph execution
/primeA missions/fix_test_suite_to_green.json

# OR manually with parallel agents:

# 2. Create three parallel agents
/primeccc "Implement foundation_automation_gates.py with 12 validation functions"
/primeccc "Implement FallbackHandler in fallback_handler.py with 7 methods"
/primeccc "Fix _handle_flags() to handle all 8 flag scenarios"

# 3. Monitor progress
watch -n 5 'pytest tests/orchestrator/test_foundation_automation_*.py --tb=no | grep -E "passed|failed"'

# 4. Celebrate when green!
echo "🎉 Test suite is GREEN! Main branch is healthy!"
```

## 🏁 Expected Outcome

After executing this plan:
- ✅ 82/82 foundation automation tests passing
- ✅ No regression in existing 35 orchestrator tests
- ✅ Full test suite (1700+ tests) remains green
- ✅ Main branch ready for production
- ✅ Constitutional compliance maintained

## 💪 Your M4 Pro Can Handle This

With 48GB RAM and 14 CPUs:
- Run 10 parallel pytest workers
- Execute multiple agents simultaneously
- Complete entire recovery in ~4 hours
- Local Ollama model can assist with P3 tasks

---

**This plan is foolproof because:**
1. Tests define the implementation (TDD)
2. Parallel execution maximizes throughput
3. Clear success metrics at each step
4. No ambiguity - tests pass or fail

Let's get your codebase healthy! 🚀