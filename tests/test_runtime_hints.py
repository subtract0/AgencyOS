import os
from tools.kanban.hints import LearningHintRegistry, Hint
from tools.kanban.runtime_hints import apply_env_hints_from_registry


def test_apply_env_hints_sets_and_appends(monkeypatch, tmp_path):
    path = tmp_path / "hints.json"
    reg = LearningHintRegistry(path=str(path))
    reg.register(Hint(match={"error_type": "X"}, action={"env": {"FOO": "bar"}}, confidence=0.9))
    reg.register(Hint(match={"error_type": "Y"}, action={"env": {"PYTHONPATH_APPEND": "src"}}, confidence=0.9))

    env = {}
    applied = apply_env_hints_from_registry(reg, env)
    assert any(a["var"] == "FOO" and a["mode"] == "set" for a in applied)
    assert env.get("FOO") == "bar"

    # Apply append
    applied2 = apply_env_hints_from_registry(reg, env)
    # PYTHONPATH was empty; APPEND should set it
    assert any(a["var"] == "PYTHONPATH" for a in applied2)
    assert "src" in env.get("PYTHONPATH", "")


def test_apply_env_hints_threshold(monkeypatch, tmp_path):
    path = tmp_path / "hints.json"
    reg = LearningHintRegistry(path=str(path))
    reg.register(Hint(match={"error_type": "Low"}, action={"env": {"LOW": "x"}}, confidence=0.2))

    monkeypatch.setenv("RUNTIME_HINTS_MIN_CONF", "0.5")
    env = {}
    applied = apply_env_hints_from_registry(reg, env)
    assert applied == []
    assert "LOW" not in env
