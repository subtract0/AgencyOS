import os

import pytest

from agency_code_agent import agency_code_agent
from agency_code_agent.agency_code_agent import render_instructions
from planner_agent import planner_agent
from shared.agent_utils import select_instructions_file as shared_select

CODE_BASE_DIR = os.path.dirname(os.path.abspath(agency_code_agent.__file__))
PLANNER_BASE_DIR = os.path.dirname(os.path.abspath(planner_agent.__file__))


def code_select(model_name: str) -> str:
    return shared_select(CODE_BASE_DIR, model_name)


def planner_select(model_name: str) -> str:
    return shared_select(PLANNER_BASE_DIR, model_name)


@pytest.mark.parametrize(
    "model_name,expected_filename",
    [
        ("gpt-5-mini", "instructions-gpt-5.md"),
        ("gpt-5", "instructions-gpt-5.md"),
        ("gpt-5-turbo", "instructions-gpt-5.md"),
        ("claude-3-5-sonnet", "instructions.md"),
        ("gpt-4o", "instructions.md"),
        ("gpt-4", "instructions.md"),
    ],
)
def test_code_agent_instructions_path_selection(model_name, expected_filename):
    path = code_select(model_name)
    assert os.path.basename(path) == expected_filename
    assert os.path.exists(path)


@pytest.mark.parametrize(
    "model_name,expected_filename",
    [
        ("gpt-5", "instructions-gpt-5.md"),
        ("gpt-5-mini", "instructions-gpt-5.md"),
        ("claude-3-5-sonnet", "instructions.md"),
    ],
)
def test_planner_instructions_path_selection(model_name, expected_filename):
    path = planner_select(model_name)
    assert os.path.basename(path) == expected_filename
    assert os.path.exists(path)


def test_render_instructions_replaces_model_placeholder():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(current_dir)
    template = os.path.join(repo_root, "agency_code_agent", "instructions.md")
    text = render_instructions(template, "gpt-5-mini")
    assert "Model Name: gpt-5-mini" in text


def test_reasoning_summary_auto_for_agents():
    from agency_code_agent.agency_code_agent import create_agency_code_agent
    from planner_agent.planner_agent import create_planner_agent

    code_agent = create_agency_code_agent(model="gpt-5-mini", reasoning_effort="low")
    planner_agent = create_planner_agent(model="gpt-5", reasoning_effort="high")

    # For OpenAI GPT-5 models, reasoning should be configured and summary set to auto
    assert code_agent.model_settings is not None
    assert getattr(code_agent.model_settings, "reasoning", None) is not None
    assert getattr(code_agent.model_settings.reasoning, "summary", None) == "auto"

    assert planner_agent.model_settings is not None
    # planner may use dict or object depending on implementation; normalize
    reasoning = getattr(planner_agent.model_settings, "reasoning", None)
    if isinstance(reasoning, dict):
        assert reasoning.get("summary") == "auto"
    else:
        assert getattr(reasoning, "summary", None) == "auto"
