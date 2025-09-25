from tools.kanban.hints import LearningHintRegistry, Hint

def test_learning_hint_registry_roundtrip(tmp_path):
    path = tmp_path / "hints.json"
    reg = LearningHintRegistry(path=str(path))
    reg.ensure_default_hints()

    # Register a custom hint
    h = Hint(match={"error_type": "ModuleNotFoundError"}, action={"note": "install pkg"}, confidence=0.7)
    reg.register(h)

    # Reload and match
    reg2 = LearningHintRegistry(path=str(path))
    m = reg2.match_for_error("ModuleNotFoundError", "ModuleNotFoundError: bar")
    assert m is not None
    assert m.action.get("note") in {"install pkg", "Consider ensuring dependency is installed or extras enabled."}
