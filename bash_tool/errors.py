from pydantic import BaseModel


class BashError(BaseModel):
    """Base class for all bash‑wrapper errors."""

    message: str


class BashCommandError(BashError):
    """Raised when a command exits with a non‑zero status."""

    cmd: str
    exit_code: int
    stderr: str


class BashTimeoutError(BashError):
    """Raised when a command exceeds the supplied timeout."""

    cmd: str
    timeout: float
