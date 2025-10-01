# Trinity Protocol - Production Wiring Checklist

**Purpose**: Step-by-step guide to replace mock implementations with real agent wiring.

**Status**: 🚧 **IN PROGRESS** - Infrastructure ready, wiring pending

---

## Overview

Trinity Protocol is currently operational with complete test coverage (317/317 tests passing) but uses **mock implementations** for sub-agent delegation and verification. This checklist guides the transition from mock to production.

**Critical Path**: Phase 1 MUST be completed before Trinity can execute real improvements autonomously.

---

## Phase 1: Core Wiring (MUST COMPLETE)

### 1.1 EXECUTOR Sub-Agent Wiring

**Status**: ⏳ **PENDING**

**Objective**: Replace mock sub-agent registry with real agent imports and invocations.

#### Current State (Mock)
```python
# trinity_protocol/executor_agent.py (lines 101-108)
self._sub_agent_registry: Dict[str, Any] = {
    "CodeWriter": None,        # TODO: Import AgencyCodeAgent
    "TestArchitect": None,     # TODO: Import TestGeneratorAgent
    "ToolDeveloper": None,     # TODO: Import ToolsmithAgent
    "ImmunityEnforcer": None,  # TODO: Import QualityEnforcerAgent
    "ReleaseManager": None,    # TODO: Import MergerAgent
    "TaskSummarizer": None     # TODO: Import WorkCompletionSummaryAgent
}
```

#### Required Changes

**Step 1**: Add imports at top of `executor_agent.py`
```python
from agency_code_agent.agent import AgencyCodeAgent
from test_generator_agent.agent import TestGeneratorAgent
from toolsmith_agent.agent import ToolsmithAgent
from quality_enforcer_agent.agent import QualityEnforcerAgent
from merger_agent.agent import MergerAgent
from work_completion_summary_agent.agent import WorkCompletionSummaryAgent
from shared.agent_context import AgentContext
```

**Step 2**: Update `__init__` to accept agent factories
```python
def __init__(
    self,
    message_bus: MessageBus,
    cost_tracker: CostTracker,
    agent_context: AgentContext,  # NEW: Shared context
    plans_dir: str = "/tmp/executor_plans",
    verification_timeout: int = 600
):
    self.message_bus = message_bus
    self.cost_tracker = cost_tracker
    self.agent_context = agent_context  # NEW
    self.plans_dir = Path(plans_dir)
    self.verification_timeout = verification_timeout
    self._running = False

    # Real agent registry
    self._sub_agent_registry: Dict[str, Any] = {
        "CodeWriter": AgencyCodeAgent(context=agent_context, cost_tracker=cost_tracker),
        "TestArchitect": TestGeneratorAgent(context=agent_context, cost_tracker=cost_tracker),
        "ToolDeveloper": ToolsmithAgent(context=agent_context, cost_tracker=cost_tracker),
        "ImmunityEnforcer": QualityEnforcerAgent(context=agent_context, cost_tracker=cost_tracker),
        "ReleaseManager": MergerAgent(context=agent_context, cost_tracker=cost_tracker),
        "TaskSummarizer": WorkCompletionSummaryAgent(context=agent_context, cost_tracker=cost_tracker)
    }
```

**Step 3**: Update `_execute_sub_agent()` to invoke real agents
```python
async def _execute_sub_agent(self, agent_spec: Dict[str, Any]) -> SubAgentResult:
    """Execute a sub-agent with real implementation."""
    agent_type = agent_spec["agent"]
    agent = self._sub_agent_registry.get(agent_type)

    if not agent:
        return SubAgentResult(
            agent=agent_type,
            status="failure",
            summary=f"Unknown agent: {agent_type}",
            duration_seconds=0.0,
            error=f"Agent {agent_type} not registered"
        )

    start_time = asyncio.get_event_loop().time()

    try:
        # Execute agent with spec
        result = await agent.execute(agent_spec["spec"])

        duration = asyncio.get_event_loop().time() - start_time

        # Extract cost from result (if available)
        cost = result.get("cost_usd", 0.0)

        return SubAgentResult(
            agent=agent_type,
            status="success" if result.get("success") else "failure",
            summary=result.get("summary", "No summary provided"),
            duration_seconds=duration,
            cost_usd=cost,
            error=result.get("error")
        )
    except Exception as e:
        duration = asyncio.get_event_loop().time() - start_time
        return SubAgentResult(
            agent=agent_type,
            status="failure",
            summary=f"Exception during execution: {str(e)}",
            duration_seconds=duration,
            error=str(e)
        )
```

**Validation**:
- [ ] All 6 agent imports resolve without errors
- [ ] `_sub_agent_registry` contains real agent instances
- [ ] `_execute_sub_agent()` invokes real agent methods
- [ ] Agent context shared across all sub-agents
- [ ] Cost tracker passed to all sub-agents

**Test Command**:
```bash
python -m pytest tests/trinity_protocol/test_executor_agent.py::test_sub_agent_wiring -v
```

---

### 1.2 Test Verification Wiring

**Status**: ⏳ **PENDING**

**Objective**: Replace mock verification with real `run_tests.py --run-all` execution.

#### Current State (Mock)
```python
# trinity_protocol/executor_agent.py (lines 317-324)
async def _run_absolute_verification(self, task_id: str) -> Dict[str, Any]:
    """Run full test suite (Article II enforcement)."""
    # TODO: Replace with real run_tests.py --run-all execution
    return {
        "success": True,  # MOCK
        "total": 1568,
        "passed": 1568,
        "failed": 0,
        "duration_seconds": 185.0,
        "timestamp": datetime.now().isoformat()
    }
```

#### Required Changes

**Step 1**: Update `_run_absolute_verification()` with real subprocess call
```python
async def _run_absolute_verification(self, task_id: str) -> Dict[str, Any]:
    """
    Run full test suite (Article II enforcement).

    CONSTITUTIONAL REQUIREMENT: 100% tests must pass before any merge.
    """
    start_time = asyncio.get_event_loop().time()

    try:
        # Execute real test suite
        process = await asyncio.create_subprocess_exec(
            "python", "run_tests.py", "--run-all",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path(__file__).parent.parent  # Agency root
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=self.verification_timeout
        )

        duration = asyncio.get_event_loop().time() - start_time

        # Parse output to extract test counts
        output = stdout.decode()

        # Extract test counts from pytest output
        # Example: "1568 passed in 185.42s"
        import re
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)

        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        total = passed + failed

        success = (process.returncode == 0 and failed == 0)

        return {
            "success": success,
            "total": total,
            "passed": passed,
            "failed": failed,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat(),
            "stdout": output[:1000],  # First 1000 chars
            "stderr": stderr.decode()[:1000]
        }

    except asyncio.TimeoutError:
        duration = asyncio.get_event_loop().time() - start_time
        return {
            "success": False,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat(),
            "error": f"Verification timeout after {self.verification_timeout}s"
        }

    except Exception as e:
        duration = asyncio.get_event_loop().time() - start_time
        return {
            "success": False,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
```

**Validation**:
- [ ] `run_tests.py --run-all` executes successfully
- [ ] Test counts parsed correctly from output
- [ ] Article II enforcement: `success=False` if any test fails
- [ ] Timeout handling prevents infinite hangs
- [ ] Stdout/stderr captured for debugging

**Test Command**:
```bash
python -m pytest tests/trinity_protocol/test_executor_agent.py::test_verification_real -v
```

---

### 1.3 Constitutional Compliance

**Status**: ⏳ **PENDING**

**Objective**: Eliminate all `Dict[Any, Any]` violations in Trinity codebase.

#### Compliance Check
```bash
# Search for violations
grep -r 'Dict\[Any, Any\]' trinity_protocol/*.py

# Expected: No matches (zero violations)
```

#### Required Actions
- [ ] Replace `Dict[Any, Any]` with Pydantic models
- [ ] Use `JSONValue` from `shared.type_definitions` for truly dynamic data
- [ ] Add type hints to all public methods
- [ ] Run `mypy trinity_protocol/` with zero errors

**Validation**:
```bash
# Type checking
python -m mypy trinity_protocol/ --no-error-summary

# Expected: Success: no issues found
```

---

### 1.4 Cost Tracking Integration

**Status**: ✅ **COMPLETE** (Infrastructure ready)

**Objective**: Ensure all sub-agents report real cost data to `CostTracker`.

#### Current State
- `CostTracker` class implemented with SQLite backend
- EXECUTOR accepts `cost_tracker` parameter
- Sub-agents need `cost_tracker` parameter in constructors

#### Required Changes

**Step 1**: Verify agent constructors accept `cost_tracker`
```python
# Each agent should accept cost_tracker in __init__
class AgencyCodeAgent:
    def __init__(self, context: AgentContext, cost_tracker: CostTracker):
        self.context = context
        self.cost_tracker = cost_tracker
```

**Step 2**: Update agent execution to log costs
```python
async def execute(self, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Execute code generation task."""
    start_time = time.time()

    # ... agent logic ...

    # Log cost after LLM call
    await self.cost_tracker.log_operation(
        agent="CodeWriter",
        operation_type="code_generation",
        model=self.model_name,
        tier=ModelTier.CLOUD_PREMIUM,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        cost_usd=calculated_cost,
        success=True,
        metadata={"file": target_file, "lines": lines_written}
    )

    return {
        "success": True,
        "cost_usd": calculated_cost,
        "summary": "Code generation complete"
    }
```

**Validation**:
- [ ] All 6 agent factories accept `cost_tracker` parameter
- [ ] EXECUTOR passes `cost_tracker` to sub-agents during initialization
- [ ] Real LLM calls logged to cost database
- [ ] Dashboard query returns real cost data

**Test Command**:
```bash
python -m pytest tests/trinity_protocol/test_cost_tracker.py::test_end_to_end_tracking -v
```

---

### 1.5 Test Suite Integration

**Status**: ✅ **COMPLETE** (All tests passing)

**Objective**: Maintain 100% test success rate across Trinity components.

#### Current Status
```bash
# Trinity tests
python -m pytest tests/trinity_protocol/ -o addopts="" -q
# Expected: 317 passed

# ARCHITECT tests
python -m pytest tests/trinity_protocol/test_architect_agent.py -o addopts="" -q
# Expected: 51 passed

# EXECUTOR tests
python -m pytest tests/trinity_protocol/test_executor_agent.py -o addopts="" -q
# Expected: 59 passed
```

**Validation**:
- [x] 51 ARCHITECT tests passing
- [x] 59 EXECUTOR tests passing
- [x] 317/317 Trinity tests passing
- [ ] Full Agency suite: 1,568/1,568 passing (after wiring)

**Test Command**:
```bash
python run_tests.py --run-all
```

---

## Phase 2: Validation (AFTER PHASE 1)

### 2.1 End-to-End Trinity Loop

**Objective**: Verify complete WITNESS → ARCHITECT → EXECUTOR → verification cycle.

**Test Scenario**:
1. Publish test event to `telemetry_stream`
2. WITNESS detects pattern, publishes signal to `improvement_queue`
3. ARCHITECT receives signal, creates task graph, publishes to `execution_queue`
4. EXECUTOR receives task, delegates to sub-agents, runs verification
5. Telemetry published back to `telemetry_stream`

**Validation**:
- [ ] Complete loop executes without errors
- [ ] Real sub-agents invoked (not mocks)
- [ ] Test suite runs and passes
- [ ] Cost tracking captures real data
- [ ] All messages persisted in database

**Test Command**:
```bash
python trinity_protocol/demo_complete_trinity.py --production
```

---

### 2.2 Full Test Suite

**Objective**: 100% test success rate across entire Agency codebase.

**Current Baseline**: 1,562 tests passing (pre-Trinity)

**Post-Wiring Target**: 1,568 tests passing (Trinity adds 6 integration tests)

**Validation**:
- [ ] All existing tests still pass
- [ ] Trinity integration tests pass
- [ ] No regressions introduced
- [ ] Zero broken windows

**Test Command**:
```bash
python run_tests.py --run-all
# Expected: 1568 passed in ~185s
```

---

### 2.3 Cost Dashboard Validation

**Objective**: Verify cost tracking shows real operational data.

**Test Query**:
```python
from trinity_protocol.cost_tracker import CostTracker

tracker = CostTracker("trinity_costs.db")
summary = tracker.get_summary_by_agent()

# Expected: Real cost data for all 6 sub-agents
# CodeWriter: $X.XX
# TestArchitect: $X.XX
# etc.
```

**Validation**:
- [ ] Dashboard shows non-zero costs
- [ ] All 6 sub-agents have entries
- [ ] Token counts match LLM calls
- [ ] Hourly/daily aggregations accurate

---

### 2.4 24-Hour Continuous Operation Test

**Objective**: Verify Trinity can run autonomously for 24 hours without intervention.

**Test Setup**:
```bash
# Start Trinity in background
python trinity_protocol/demo_complete_trinity.py --continuous --duration 86400 &

# Monitor logs
tail -f /tmp/trinity_continuous.log
```

**Success Criteria**:
- [ ] Zero crashes over 24 hours
- [ ] All detected patterns processed
- [ ] Message bus maintains state across restarts
- [ ] Memory usage stable (no leaks)
- [ ] Cost tracking accumulates correctly

**Validation Metrics**:
- Total events processed: >1000
- Signals generated: >100
- Tasks executed: >50
- Average latency: <5 seconds
- Memory usage: <500MB

---

## Phase 3: Enhancements (OPTIONAL)

### 3.1 ADR Search in ARCHITECT

**Objective**: Query existing ADRs before creating new specifications.

**Implementation**:
```python
# In architect_agent.py
async def _gather_context(self, signal: Dict[str, Any]) -> Dict[str, Any]:
    """Gather historical patterns and ADRs."""
    # Query PersistentStore for similar patterns
    patterns = self.pattern_store.search_patterns(
        query=signal["description"],
        min_confidence=0.5,
        limit=10
    )

    # NEW: Search ADRs
    adr_dir = Path(__file__).parent.parent / "docs" / "adr"
    relevant_adrs = []
    for adr_file in adr_dir.glob("*.md"):
        # Simple keyword matching (can upgrade to semantic later)
        content = adr_file.read_text()
        if any(keyword in content.lower() for keyword in signal.get("keywords", [])):
            relevant_adrs.append({
                "file": adr_file.name,
                "title": content.split("\n")[0].replace("# ", "")
            })

    return {
        "patterns": patterns,
        "adrs": relevant_adrs,
        "similar_signals": []  # TODO: Query message bus history
    }
```

**Benefit**: Avoid duplicate specifications, maintain consistency with existing decisions.

---

### 3.2 FAISS Semantic Search

**Objective**: Upgrade PersistentStore to use semantic similarity for pattern search.

**Current**: Keyword-based SQL queries
**Upgrade**: Vector embeddings + FAISS index

**Implementation**:
```python
# Already implemented in persistent_store.py, just needs activation
store = PersistentStore("patterns.db")  # FAISS auto-detected if available

# Semantic search
patterns = store.search_patterns(
    query="authentication error in production",  # Natural language
    min_confidence=0.6,
    limit=5
)
```

**Benefit**: Find conceptually similar patterns even with different wording.

---

### 3.3 Centralized Logging with Correlation IDs

**Objective**: Trace complete execution flow across all 3 agents.

**Implementation**:
```python
import logging
from pythonjsonlogger import jsonlogger

# Structured logging
logger = logging.getLogger("trinity")
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Usage in agents
logger.info("Event detected", extra={
    "agent": "WITNESS",
    "correlation_id": correlation_id,
    "pattern": pattern_name,
    "priority": priority
})
```

**Benefit**: Unified logging across all agents, easy to trace request flow.

---

## Wiring Dependencies

### Agent Constructor Signatures

All agents MUST support this signature for Trinity integration:

```python
class AgentName:
    def __init__(
        self,
        context: AgentContext,
        cost_tracker: CostTracker,
        # Agent-specific params...
    ):
        self.context = context
        self.cost_tracker = cost_tracker

    async def execute(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task.

        Args:
            spec: Task specification from ARCHITECT

        Returns:
            {
                "success": bool,
                "summary": str,
                "cost_usd": float,
                "error": Optional[str]
            }
        """
        pass
```

### Required Agent Methods

Each sub-agent MUST implement:
1. `execute(spec: Dict[str, Any]) -> Dict[str, Any]` - Main entry point
2. Cost logging via `cost_tracker.log_operation()`
3. Context sharing via `self.context.store_memory()` / `search_memories()`

---

## Troubleshooting

### Issue: Sub-agent import fails
**Symptom**: `ModuleNotFoundError` when importing agent
**Solution**: Verify agent module installed and in PYTHONPATH
```bash
python -c "from agency_code_agent.agent import AgencyCodeAgent"
```

### Issue: Test verification times out
**Symptom**: `_run_absolute_verification()` exceeds timeout
**Solution**: Increase `verification_timeout` parameter
```python
executor = ExecutorAgent(
    message_bus=bus,
    cost_tracker=tracker,
    verification_timeout=1200  # 20 minutes
)
```

### Issue: Cost tracking returns zero
**Symptom**: Dashboard shows $0.00 for all agents
**Solution**: Verify agents call `cost_tracker.log_operation()` after LLM calls
```python
# Add this to agent.execute()
await self.cost_tracker.log_operation(
    agent=self.__class__.__name__,
    operation_type="generation",
    model=model_name,
    tier=ModelTier.CLOUD_PREMIUM,
    input_tokens=input_count,
    output_tokens=output_count,
    cost_usd=calculated_cost,
    success=True
)
```

### Issue: Constitutional violations detected
**Symptom**: `mypy` reports `Dict[Any, Any]` errors
**Solution**: Replace with Pydantic models or `JSONValue`
```python
# Before
data: Dict[Any, Any] = {"key": "value"}

# After
from pydantic import BaseModel
class DataModel(BaseModel):
    key: str

data = DataModel(key="value")
```

---

## Validation Checklist

### Phase 1 Complete When:
- [ ] All 6 sub-agents wired with real imports
- [ ] `_execute_sub_agent()` invokes real agent methods
- [ ] `_run_absolute_verification()` executes `run_tests.py --run-all`
- [ ] Zero `Dict[Any, Any]` violations in `trinity_protocol/`
- [ ] `mypy trinity_protocol/` passes with zero errors
- [ ] All 6 agents accept `cost_tracker` parameter
- [ ] 317/317 Trinity tests passing

### Phase 2 Complete When:
- [ ] Complete Trinity loop operational (WITNESS → ARCHITECT → EXECUTOR)
- [ ] Full Agency test suite: 1,568/1,568 passing
- [ ] Cost dashboard shows real operational data
- [ ] 24-hour continuous operation successful

### Phase 3 Complete When:
- [ ] ADR search integrated in ARCHITECT
- [ ] FAISS semantic search operational
- [ ] Centralized logging with correlation IDs

---

## Next Steps

1. **Read** `docs/trinity_protocol/QUICKSTART.md` - Updated with production setup
2. **Review** agent interfaces in `agency_code_agent/`, `test_generator_agent/`, etc.
3. **Start** with Phase 1.1 (sub-agent wiring)
4. **Test** incrementally after each change
5. **Validate** with `python run_tests.py --run-all` before proceeding

---

**Constitutional Mandate**: Article II requires 100% test success before ANY merge. Complete Phase 1 validation before production deployment.

**Status**: 🚧 Infrastructure ready, awaiting wiring completion.
