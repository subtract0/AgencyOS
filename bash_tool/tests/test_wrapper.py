import os
import sys
import time

import pytest

from bash_tool.wrapper import run
from bash_tool.errors import BashCommandError, BashTimeoutError
from bash_tool.types import BashResult


def test_successful_command():
    res = run('printf "ok"')
    assert res.is_ok
    result: BashResult = res.unwrap()
    assert result.stdout == "ok"
    assert result.exit_code == 0


def test_command_failure():
    res = run("cat nonexist_file_12345")
    assert res.is_err
    err = res.unwrap_err()
    assert isinstance(err, BashCommandError)
    assert err.exit_code != 0
    assert "No such file or directory" in err.stderr


def test_timeout():
    res = run("sleep 2", timeout=0.5)
    assert res.is_err
    err = res.unwrap_err()
    assert isinstance(err, BashTimeoutError)
    assert err.timeout == 0.5


def test_custom_cwd(tmp_path):
    script_path = tmp_path / "makefile.txt"
    res = run("touch makefile.txt", cwd=tmp_path)
    assert res.is_ok
    assert script_path.exists()


def test_custom_env():
    res = run('echo "$FOO"', env={"FOO": "bar"})
    assert res.is_ok
    result = res.unwrap()
    # echo adds a trailing newline
    assert result.stdout.strip() == "bar"


def test_unicode_output():
    emoji = "😁"
    res = run(f'printf "{emoji}"')
    assert res.is_ok
    result = res.unwrap()
    assert result.stdout == emoji
