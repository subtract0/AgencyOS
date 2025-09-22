from tools import HandoffWithContext


def test_handoff_with_context_alias_runs():
    tool = HandoffWithContext(
        target_agent="PlannerAgent",
        prompt="Plan feature Y",
        context={"mission": "feature Y"},
        persist=False,
    )
    result = tool.run()
    assert "Prepared handoff" in result
    assert "PlannerAgent" in result
