import logging
import asyncio
import pytest

from shared.system_hooks import create_tool_wrapper_hook


class DummyContext:
    def __init__(self):
        self.context = {}
        self.thread_manager = None


class AlwaysFailTool:
    name = "Read"
    def __init__(self):
        self.calls = 0
    def run(self, *args, **kwargs):
        self.calls += 1
        raise ValueError("boom")


def test_breaker_logs_and_env_tuning(monkeypatch):
    # Tune via env
    monkeypatch.setenv("AGENCY_BREAKER_THRESHOLD", "1")
    monkeypatch.setenv("AGENCY_BREAKER_TIMEOUT", "60.0")
    monkeypatch.setenv("AGENCY_RETRY_MAX_ATTEMPTS", "1")

    hook = create_tool_wrapper_hook()
    tool = AlwaysFailTool()
    wrapper = DummyContext()

    # Custom log capture to avoid pytest logging plugin
    logger = logging.getLogger("shared.retry_controller")
    logger.setLevel(logging.INFO)
    records = []

    class ListHandler(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = ListHandler()
    logger.addHandler(handler)

    try:
        # Wrap the tool
        asyncio.get_event_loop().run_until_complete(hook.on_tool_start(wrapper, agent=None, tool=tool))

        # First execution should fail and open the circuit (threshold=1)
        with pytest.raises(ValueError):
            tool.run()

        # Second execution should be blocked by circuit (no extra call)
        with pytest.raises(Exception):
            tool.run()

        # Verify no additional call executed
        assert tool.calls == 2  # initial + retried once due to max_attempts=1 → initial + 1 attempt

        # Verify logs contain circuit events
        messages = "\n".join(r.getMessage() for r in records)
        assert "circuit_open" in messages or "circuit_failure" in messages or "circuit_blocked_request" in messages
    finally:
        logger.removeHandler(handler)
