import subprocess
import time
from typing import Mapping, Optional

from .errors import BashCommandError, BashTimeoutError
from .types import BashResult
from .result import Result


def run(
    cmd: str,
    *,
    timeout: Optional[float] = None,
    cwd: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Result[BashResult, BashCommandError | BashTimeoutError]:
    """Execute a shell command and return a typed Result.

    Args:
        cmd: Command line to execute.
        timeout: Optional timeout in seconds.
        cwd: Optional working directory.
        env: Optional environment mapping.

    Returns:
        Result containing ``BashResult`` on success or a structured error on failure.
    """
    start = time.monotonic()
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            text=True,
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        exit_code = proc.returncode
        runtime = time.monotonic() - start

        if exit_code != 0:
            err = BashCommandError(
                message=f"Command exited with {exit_code}",
                cmd=cmd,
                exit_code=exit_code,
                stderr=stderr,
            )
            return Result(error=err)

        res = BashResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            runtime=runtime,
        )
        return Result(value=res)

    except subprocess.TimeoutExpired:
        proc.kill()
        _, stderr = proc.communicate()
        err = BashTimeoutError(
            message="Command timed out",
            cmd=cmd,
            timeout=timeout or float("inf"),
        )
        return Result(error=err)

    except OSError as exc:
        # Unexpected OS error – wrap as BashCommandError for simplicity
        err = BashCommandError(
            message=str(exc),
            cmd=cmd,
            exit_code=-1,
            stderr=str(exc),
        )
        return Result(error=err)
