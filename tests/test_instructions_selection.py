import os

import pytest

from agency import render_instructions
from agency_code_agent.agency_code_agent import select_instructions_file as code_select
from planner_agent.planner_agent import select_instructions_file as planner_select


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
