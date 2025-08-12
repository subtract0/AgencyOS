import os
from claude_code.tools.bash import Bash


def test_bash_default_timeout_and_exit_code():
    tool = Bash(command="echo hello")
    out = tool.run()
    assert "Exit code: 0" in out
    assert "hello" in out


def test_bash_timeout_trigger():
    # Use a sleep shorter than max and a very small timeout to force timeout
    tool = Bash(command="python -c 'import time; time.sleep(5)'", timeout=5000)
    out = tool.run()
    assert "Exit code:" in out
    assert "timed out" in out.lower()

