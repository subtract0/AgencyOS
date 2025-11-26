from pydantic import BaseModel


class BashResult(BaseModel):
    """Successful execution result."""

    stdout: str
    stderr: str
    exit_code: int
    runtime: float
