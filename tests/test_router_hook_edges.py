import asyncio

from shared.system_hooks import create_intent_router_hook


class DummyContext:
    def __init__(self):
        self._data = {}
        self.thread_manager = None
    def get(self, k, d=None):
        return self._data.get(k, d)
    def set(self, k, v):
        self._data[k] = v


class DummyWrapper:
    def __init__(self):
        self.context = DummyContext()


def test_router_no_trigger_no_route():
    hook = create_intent_router_hook()
    w = DummyWrapper()
    w.context.set("latest_user_prompt", "please summarize text")
    asyncio.get_event_loop().run_until_complete(hook.on_start(w, agent=None))
    assert w.context.get("route_to_agent") is None


def test_router_case_insensitive():
    hook = create_intent_router_hook()
    w = DummyWrapper()
    w.context.set("latest_user_prompt", "Please provide an Audio Summary of results")
    asyncio.get_event_loop().run_until_complete(hook.on_start(w, agent=None))
    assert w.context.get("route_to_agent") == "WorkCompletionSummaryAgent"
