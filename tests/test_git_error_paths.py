import sys
import types

import pytest

import os
import pytest
from tools.git import Git


@pytest.mark.skipif(os.getenv("AGENCY_SKIP_GIT", "") == "1", reason="Skipping git tests in this CI environment")
def test_git_missing_dulwich_import(monkeypatch):
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("dulwich"):
            raise ModuleNotFoundError("No module named 'dulwich'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    out = Git(cmd="status").run()
    assert "dulwich not installed" in out


@pytest.mark.skipif(os.getenv("AGENCY_SKIP_GIT", "") == "1", reason="Skipping git tests in this CI environment")
def test_git_open_repo_error(monkeypatch):
    # Create a fake dulwich.porcelain module
    dulwich = types.ModuleType("dulwich")
    porcelain = types.ModuleType("dulwich.porcelain")

    class DummyRepo:
        pass

    def open_repo(cwd):
        raise Exception("not a git repository")

    porcelain.open_repo = open_repo
    dulwich.porcelain = porcelain

    monkeypatch.setitem(sys.modules, "dulwich", dulwich)
    monkeypatch.setitem(sys.modules, "dulwich.porcelain", porcelain)

    out = Git(cmd="status").run()
    assert "Error opening git repo" in out


@pytest.mark.skipif(os.getenv("AGENCY_SKIP_GIT", "") == "1", reason="Skipping git tests in this CI environment")
def test_git_diff_error(monkeypatch):
    dulwich = types.ModuleType("dulwich")
    porcelain = types.ModuleType("dulwich.porcelain")

    class DummyRepo:
        pass

    def open_repo(cwd):
        return DummyRepo()

    def diff_tree(repo, *args, **kwargs):
        raise Exception("diff failure")

    porcelain.open_repo = open_repo
    porcelain.diff_tree = diff_tree

    monkeypatch.setitem(sys.modules, "dulwich", dulwich)
    monkeypatch.setitem(sys.modules, "dulwich.porcelain", porcelain)

    out = Git(cmd="diff").run()
    assert "Error in diff" in out


@pytest.mark.skipif(os.getenv("AGENCY_SKIP_GIT", "") == "1", reason="Skipping git tests in this CI environment")
def test_git_show_error(monkeypatch):
    dulwich = types.ModuleType("dulwich")
    porcelain = types.ModuleType("dulwich.porcelain")

    class DummyRepo:
        pass

    def open_repo(cwd):
        return DummyRepo()

    def show(repo, *args, **kwargs):
        raise Exception("show failure")

    porcelain.open_repo = open_repo
    porcelain.show = show

    monkeypatch.setitem(sys.modules, "dulwich", dulwich)
    monkeypatch.setitem(sys.modules, "dulwich.porcelain", porcelain)

    out = Git(cmd="show").run()
    assert "Error in show" in out
