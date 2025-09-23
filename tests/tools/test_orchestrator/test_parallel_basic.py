import asyncio
import time
import pytest

from shared.agent_context import AgentContext
from tools.orchestrator import execute_parallel, TaskSpec, OrchestrationPolicy


class StubAgent:
    def __init__(self, delay: float = 0.05, result: dict | None = None):
        self.delay = delay
        self.result = result or {"ok": True}

    async def run(self, prompt: str, **params):
        await asyncio.sleep(self.delay)
        return {"prompt": prompt, **self.result}


def stub_factory(ctx: AgentContext):  # noqa: ARG001
    return StubAgent(delay=0.1)


@pytest.mark.asyncio
async def test_parallel_speedup_basic():
    ctx = AgentContext()
    tasks = [
        TaskSpec(agent_factory=stub_factory, prompt="a"),
        TaskSpec(agent_factory=stub_factory, prompt="b"),
    ]
    policy = OrchestrationPolicy(max_concurrency=2)
    t0 = time.time()
    res = await execute_parallel(ctx, tasks, policy)
    wall = time.time() - t0
    # With two tasks that take 0.1s each, parallel should be < 0.18s comfortably
    assert wall < 0.18, f"expected speedup, got wall={wall}"
    assert len(res.tasks) == 2
    assert all(r.status == "success" for r in res.tasks)


class FlakyOnce:
    def __init__(self):
        self.calls = 0

    async def run(self, prompt: str, **params):  # noqa: ARG002
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("fail-once")
        return {"ok": True}


def flaky_factory(ctx: AgentContext):  # noqa: ARG001
    return FlakyOnce()


@pytest.mark.asyncio
async def test_retry_fixed_backoff_success_on_second_attempt():
    ctx = AgentContext()
    tasks = [TaskSpec(agent_factory=flaky_factory, prompt="x")]
    policy = OrchestrationPolicy(max_concurrency=1)
    policy.retry.max_attempts = 2
    res = await execute_parallel(ctx, tasks, policy)
    assert len(res.tasks) == 1
    r = res.tasks[0]
    assert r.attempts == 2
    assert r.status == "success"
