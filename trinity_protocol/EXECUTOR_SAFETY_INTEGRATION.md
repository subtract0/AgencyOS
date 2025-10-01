# EXECUTOR Safety Integration Guide

**CRITICAL INFRASTRUCTURE** - These safety systems MUST be integrated before any autonomous operation.

## Overview

Three safety systems enforce constitutional compliance for autonomous operation:

1. **Foundation Verifier** - Ensures "Green Main" before work begins (Article II)
2. **Budget Enforcer** - Hard daily spending limits with auto-shutdown (Article III)
3. **Message Persistence** - Guarantees work survives restarts (Article IV)

---

## 1. Foundation Verifier Integration

### Purpose
Blocks EXECUTOR startup if foundation is broken (tests failing).

### Article II Compliance
> "A task is complete ONLY when 100% verified and stable."

EXECUTOR must NEVER start work on a broken foundation.

### Integration Pattern

```python
from trinity_protocol.foundation_verifier import (
    FoundationVerifier,
    BrokenFoundationError
)

class ExecutorAgent:
    def __init__(self, ...):
        self.foundation_verifier = FoundationVerifier(
            timeout_seconds=600  # 10 min max for test suite
        )

    async def run(self) -> None:
        """Main loop: verify foundation BEFORE starting work."""

        # STEP 0: VERIFY FOUNDATION (blocking)
        try:
            result = self.foundation_verifier.verify_and_enforce()
            print(f"✓ Foundation healthy: {result.passed_tests} tests passed")
        except BrokenFoundationError as e:
            print(f"❌ BLOCKED: {e}")
            print("Fix all tests before autonomous operation.")
            return  # Do NOT proceed

        # STEP 1-9: Normal EXECUTOR operation
        self._running = True
        async for message in self.message_bus.subscribe("execution_queue"):
            ...
```

### Verification Options

```python
# Option 1: Enforce (raises exception if broken)
verifier.verify_and_enforce()

# Option 2: Check status (returns result)
result = verifier.verify()
if result.status != FoundationStatus.HEALTHY:
    # Handle broken foundation
    pass

# Option 3: Check with caching (avoid redundant runs)
result = verifier.verify(use_cache=True, cache_ttl_seconds=300)
```

### Error Handling

```python
try:
    verifier.verify_and_enforce()
except BrokenFoundationError as e:
    # Log to telemetry
    await message_bus.publish("telemetry_stream", {
        "event": "foundation_check_failed",
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    })

    # Alert operators
    print(f"⚠️  CRITICAL: Foundation broken - EXECUTOR blocked")

    # Do NOT proceed
    sys.exit(1)
```

---

## 2. Budget Enforcer Integration

### Purpose
Hard daily spending limit ($30/day) with auto-shutdown.

### Article III Compliance
> "Quality standards SHALL be technically enforced, not manually governed."

Budget limits are ABSOLUTE. No manual override permitted.

### Integration Pattern

```python
from trinity_protocol.budget_enforcer import (
    BudgetEnforcer,
    BudgetExceededError,
    BudgetStatus
)

class ExecutorAgent:
    def __init__(
        self,
        cost_tracker: CostTracker,
        ...
    ):
        self.budget_enforcer = BudgetEnforcer(
            cost_tracker=cost_tracker,
            daily_limit_usd=30.0,  # HARD LIMIT
            alert_threshold=0.8,   # Alert at 80%
            shutdown_callback=self.emergency_shutdown
        )

    async def _process_task(self, task: Dict[str, Any]) -> None:
        """Process task with budget enforcement."""

        # ENFORCE BUDGET before starting work
        try:
            self.budget_enforcer.enforce()
        except BudgetExceededError as e:
            await self._handle_budget_exceeded(e)
            return  # Do NOT proceed with task

        # Check for alerts
        alerts = self.budget_enforcer.check_alerts()
        for alert in alerts:
            print(alert.message)

        # Proceed with task execution
        ...

    async def emergency_shutdown(self) -> None:
        """Called automatically when budget exceeded."""
        print("🚨 EMERGENCY SHUTDOWN: Budget limit reached")

        # Stop accepting new work
        self._running = False

        # Publish shutdown event
        await self.message_bus.publish("telemetry_stream", {
            "event": "emergency_shutdown",
            "reason": "budget_exceeded",
            "timestamp": datetime.now().isoformat()
        })
```

### Real-Time Monitoring

```python
# Get current budget status
status = budget_enforcer.get_status()

print(f"Spent: ${status.current_spending_usd:.2f}")
print(f"Limit: ${status.daily_limit_usd:.2f}")
print(f"Remaining: ${status.remaining_usd:.2f}")
print(f"Status: {status.status.value}")  # HEALTHY, WARNING, or EXCEEDED
```

### Alert Integration

```python
async def check_budget_alerts(self) -> None:
    """Periodic budget check (every 5 minutes)."""
    alerts = self.budget_enforcer.check_alerts()

    for alert in alerts:
        if alert.alert_type == "threshold_reached":
            # 80% threshold reached
            await self.message_bus.publish("telemetry_stream", {
                "event": "budget_alert",
                "alert_type": alert.alert_type,
                "current_spending": alert.current_spending_usd,
                "remaining": alert.remaining_usd,
                "message": alert.message
            })
```

---

## 3. Message Persistence Integration

### Purpose
Guarantees work survives process crashes and restarts.

### Article IV Compliance
> "The Agency SHALL continuously improve through experiential learning."

Messages must persist for cross-session pattern recognition.

### Already Integrated
Message persistence is built into `MessageBus` via SQLite. No additional code needed!

### Verification
The tests in `test_message_persistence_restart.py` prove:
- ✓ Messages persist after bus close/reopen
- ✓ Messages survive process crashes
- ✓ Correlation tracking persists
- ✓ Processed messages remain processed
- ✓ 24/7 operation supported

### Recovery Scenario

```python
# Session 1: EXECUTOR processes task-1, crashes before task-2
bus = MessageBus(db_path="trinity_messages.db")
async for msg in bus.subscribe("execution_queue"):
    # Process task
    await bus.ack(msg["_message_id"])
    # CRASH (before processing remaining tasks)

# Session 2: EXECUTOR restarts
bus = MessageBus(db_path="trinity_messages.db")  # Same DB!
# Automatically receives pending tasks
async for msg in bus.subscribe("execution_queue"):
    # Continues from where it left off
    ...
```

---

## Integration Checklist

### EXECUTOR Startup Sequence

```python
async def initialize_executor() -> ExecutorAgent:
    """
    Initialize EXECUTOR with all safety systems.

    Constitutional Requirements:
    - Article I: Complete context (all tests must pass)
    - Article II: 100% verification (green main required)
    - Article III: Automated enforcement (budget limits absolute)
    - Article IV: Continuous learning (messages persist)
    """

    # 1. Initialize infrastructure
    message_bus = MessageBus(db_path="trinity_messages.db")
    cost_tracker = CostTracker(db_path="trinity_costs.db", budget_usd=30.0)
    agent_context = create_agent_context()

    # 2. Create EXECUTOR
    executor = ExecutorAgent(
        message_bus=message_bus,
        cost_tracker=cost_tracker,
        agent_context=agent_context
    )

    # 3. VERIFY FOUNDATION (Article II enforcement)
    print("Verifying foundation health...")
    try:
        result = executor.foundation_verifier.verify_and_enforce()
        print(f"✓ Foundation healthy: {result.passed_tests} tests passed")
    except BrokenFoundationError as e:
        print(f"❌ BLOCKED: Foundation broken")
        print(str(e))
        sys.exit(1)

    # 4. CHECK BUDGET STATUS
    print("Checking budget status...")
    status = executor.budget_enforcer.get_status()
    print(f"Budget: ${status.current_spending_usd:.2f} / ${status.daily_limit_usd:.2f}")

    if status.status == BudgetStatus.EXCEEDED:
        print("❌ BLOCKED: Budget exceeded for today")
        sys.exit(1)

    # 5. READY FOR AUTONOMOUS OPERATION
    print("✓ All safety checks passed")
    print("✓ Ready for autonomous operation")

    return executor
```

### EXECUTOR Main Loop

```python
async def run(self) -> None:
    """Main loop with safety enforcement."""

    # Foundation check (already done at startup)
    # Budget enforcement happens per-task

    self._running = True

    try:
        async for message in self.message_bus.subscribe("execution_queue"):
            if not self._running:
                break

            task_id = message.get("task_id")

            # ENFORCE BUDGET before each task
            try:
                self.budget_enforcer.enforce()
            except BudgetExceededError:
                # Auto-shutdown triggered
                break

            # Process task with full safety
            try:
                await self._process_task(message, task_id)
                self._stats["tasks_succeeded"] += 1
            except Exception as e:
                await self._handle_task_failure(task_id, message, e)
                self._stats["tasks_failed"] += 1
            finally:
                # Cleanup
                self._cleanup_workspace(task_id)

            # Acknowledge message
            await self.message_bus.ack(message["_message_id"])

    except asyncio.CancelledError:
        pass  # Expected on shutdown

    finally:
        # Log final stats
        print(f"Tasks processed: {self._stats['tasks_processed']}")
        print(f"Success rate: {self._stats['tasks_succeeded']} / {self._stats['tasks_processed']}")
```

---

## Testing Integration

### Verify Foundation Checks Work

```bash
# 1. Break tests
echo "assert False" >> tests/example_test.py

# 2. Try to start EXECUTOR
python trinity_protocol/executor_agent.py

# Expected: EXECUTOR blocked, prints error message
# BLOCKED: Foundation broken
# Fix all tests before autonomous operation.
```

### Verify Budget Enforcement Works

```python
# 1. Set low budget
executor = ExecutorAgent(
    cost_tracker=CostTracker(budget_usd=1.0),  # $1 limit
    ...
)

# 2. Run expensive tasks
# Expected: EXECUTOR shuts down after ~$1 spending
```

### Verify Message Persistence Works

```bash
# 1. Publish tasks
python -c "
import asyncio
from trinity_protocol.message_bus import MessageBus

async def main():
    bus = MessageBus('trinity_messages.db')
    await bus.publish('execution_queue', {'task_id': 'test-1'})
    await bus.publish('execution_queue', {'task_id': 'test-2'})
    bus.close()

asyncio.run(main())
"

# 2. Kill EXECUTOR mid-task
# 3. Restart EXECUTOR
# Expected: Processes remaining tasks
```

---

## Monitoring & Observability

### Health Check Endpoint

```python
def get_health_status(self) -> Dict[str, Any]:
    """Get EXECUTOR health status."""
    foundation_result = self.foundation_verifier.verify(use_cache=True)
    budget_status = self.budget_enforcer.get_status()

    return {
        "foundation": {
            "status": foundation_result.status.value,
            "tests_passed": foundation_result.passed_tests,
            "tests_failed": foundation_result.failed_tests
        },
        "budget": {
            "status": budget_status.status.value,
            "spent_usd": budget_status.current_spending_usd,
            "limit_usd": budget_status.daily_limit_usd,
            "remaining_usd": budget_status.remaining_usd
        },
        "message_bus": {
            "pending_tasks": await self.message_bus.get_pending_count("execution_queue")
        },
        "executor": {
            "running": self._running,
            "tasks_processed": self._stats["tasks_processed"],
            "tasks_succeeded": self._stats["tasks_succeeded"],
            "tasks_failed": self._stats["tasks_failed"]
        }
    }
```

### Telemetry Events

Key events to publish to `telemetry_stream`:

```python
# 1. Foundation check
{
    "event": "foundation_check",
    "status": "healthy" | "broken",
    "tests_passed": 1562,
    "duration_seconds": 180.5
}

# 2. Budget alert
{
    "event": "budget_alert",
    "threshold_percent": 80,
    "current_spending_usd": 24.0,
    "remaining_usd": 6.0
}

# 3. Emergency shutdown
{
    "event": "emergency_shutdown",
    "reason": "budget_exceeded",
    "final_cost_usd": 30.05
}

# 4. Task completion
{
    "event": "task_completed",
    "task_id": "task-001",
    "duration_seconds": 45.2,
    "cost_usd": 0.15,
    "status": "success" | "failure"
}
```

---

## File References

**Implementation Files:**
- `/Users/am/Code/Agency/trinity_protocol/foundation_verifier.py`
- `/Users/am/Code/Agency/trinity_protocol/budget_enforcer.py`
- `/Users/am/Code/Agency/trinity_protocol/message_bus.py` (already has persistence)

**Test Files:**
- `/Users/am/Code/Agency/tests/trinity_protocol/test_foundation_verifier.py` (20 tests)
- `/Users/am/Code/Agency/tests/trinity_protocol/test_budget_enforcer.py` (3 tests)
- `/Users/am/Code/Agency/tests/trinity_protocol/test_message_persistence_restart.py` (11 tests)

**Integration Target:**
- `/Users/am/Code/Agency/trinity_protocol/executor_agent.py`

**Test Results:**
- ✓ 34/34 tests passing (100%)
- ✓ Constitutional compliance verified
- ✓ Ready for integration

---

## Next Steps

1. **Integrate into EXECUTOR** - Add foundation verification and budget enforcement to `ExecutorAgent.__init__()` and `ExecutorAgent.run()`

2. **Test Integration** - Run full integration test with:
   - Broken foundation scenario
   - Budget exceeded scenario
   - Process crash/restart scenario

3. **Update EXECUTOR Tests** - Add tests verifying safety system integration

4. **Deploy to Production** - Only after all integration tests pass at 100%

---

**Constitutional Mandate**: These safety systems are NOT optional. They enforce Articles I, II, III, and IV. Any attempt to bypass them violates the constitution and must be rejected.

**Status**: ✓ Implementation complete, tested, ready for integration.

**Author**: Claude (Quality Enforcer Agent)
**Date**: 2025-10-01
**Version**: 1.0
