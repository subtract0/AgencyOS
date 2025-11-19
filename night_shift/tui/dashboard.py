from dataclasses import dataclass
from time import sleep
from threading import Event
from typing import List

from rich.console import Console
from rich.live import Live
from rich.table import Table

# ----------------------------------------------------------------------
# Data models – Pydantic‑style (no external dependency required for simple cases)
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class CycleSummary:
    current: int
    next: int
    remaining: int


@dataclass(frozen=True)
class BacklogCounts:
    todo: int
    in_progress: int
    blocked: int


@dataclass(frozen=True)
class CMPSignal:
    name: str
    value: str


@dataclass(frozen=True)
class CMPSignals:
    signals: List[CMPSignal]


@dataclass(frozen=True)
class CommitInfo:
    sha: str
    message: str


# ----------------------------------------------------------------------
# Result type for error handling
# ----------------------------------------------------------------------
class Result:
    """Simple Result<T, E> pattern."""

    __slots__ = ("_value", "_error", "_is_ok")

    def __init__(self, value=None, error=None):
        self._value = value
        self._error = error
        self._is_ok = error is None

    @staticmethod
    def Ok(value):
        return Result(value=value)

    @staticmethod
    def Err(error):
        return Result(error=error)

    def is_ok(self):
        return self._is_ok

    def is_err(self):
        return not self._is_ok

    def unwrap(self):
        if self._is_ok:
            return self._value
        raise RuntimeError(f"Unwrapped Err: {self._error}")

    def unwrap_err(self):
        if self._is_ok:
            raise RuntimeError("Unwrapped Ok result")
        return self._error


# ----------------------------------------------------------------------
# Artifact adapters – thin wrappers around existing Night Shift data sources
# ----------------------------------------------------------------------
def get_cycle_summary() -> Result[CycleSummary, str]:
    """Retrieve a simple cycle summary from Night Shift artifacts."""
    try:
        # Placeholder implementation – replace with real artifact access.
        cs = CycleSummary(current=42, next=43, remaining=5)
        return Result.Ok(cs)
    except Exception as exc:
        return Result.Err(str(exc))


def get_backlog_counts() -> Result[BacklogCounts, str]:
    """Retrieve backlog counts from Night Shift artifacts."""
    try:
        bc = BacklogCounts(todo=12, in_progress=7, blocked=2)
        return Result.Ok(bc)
    except Exception as exc:
        return Result.Err(str(exc))


def get_cmp_signals() -> Result[CMPSignals, str]:
    """Retrieve CMP signals from Night Shift artifacts."""
    try:
        signals = [
            CMPSignal(name="CPU", value="45%"),
            CMPSignal(name="MEM", value="68%"),
            CMPSignal(name="IO", value="23%"),
        ]
        return Result.Ok(CMPSignals(signals=signals))
    except Exception as exc:
        return Result.Err(str(exc))


def get_recent_commits(limit: int = 3) -> Result[List[CommitInfo], str]:
    """Retrieve recent git commits – dummy data for demo purposes."""
    try:
        dummy = [
            CommitInfo(sha="a1b2c3d", message="Fix dashboard refresh logic"),
            CommitInfo(sha="d4e5f6g", message="Add backlog count adapters"),
            CommitInfo(sha="h7i8j9k", message="Initial Night Shift TUI commit"),
        ]
        return Result.Ok(dummy[:limit])
    except Exception as exc:
        return Result.Err(str(exc))


# ----------------------------------------------------------------------
# Dashboard construction & run loop
# ----------------------------------------------------------------------
REFRESH_SECONDS = 5


def _build_table() -> Table:
    table = Table(title="Night Shift Status", expand=True)

    # Cycle summary
    cs_res = get_cycle_summary()
    if cs_res.is_ok():
        cs = cs_res.unwrap()
        table.add_column("Cycle", justify="center")
        table.add_row(f"Cur:{cs.current}  Next:{cs.next}  Rem:{cs.remaining}")
    else:
        table.add_column("Cycle", justify="center")
        table.add_row(f"Error: {cs_res.unwrap_err()}")

    # Backlog counts
    bc_res = get_backlog_counts()
    if bc_res.is_ok():
        bc = bc_res.unwrap()
        table.add_column("Backlog", justify="center")
        table.add_row(f"🟦{bc.todo} 🟨{bc.in_progress} 🟥{bc.blocked}")
    else:
        table.add_column("Backlog", justify="center")
        table.add_row(f"Error: {bc_res.unwrap_err()}")

    # CMP signals
    cmp_res = get_cmp_signals()
    if cmp_res.is_ok():
        cmp = cmp_res.unwrap()
        table.add_column("CMP", justify="center")
        table.add_row(" ".join(f"{s.name}:{s.value}" for s in cmp.signals))
    else:
        table.add_column("CMP", justify="center")
        table.add_row(f"Error: {cmp_res.unwrap_err()}")

    # Recent commits
    commit_res = get_recent_commits(limit=3)
    if commit_res.is_ok():
        commits = commit_res.unwrap()
        table.add_column("Commits", justify="left")
        table.add_row("\n".join(f"- {c.sha[:7]} {c.message}" for c in commits))
    else:
        table.add_column("Commits", justify="left")
        table.add_row(f"Error: {commit_res.unwrap_err()}")

    return table


def run_dashboard(stop_event: Event | None = None) -> None:
    """Launch the live-updating dashboard.

    Args:
        stop_event: Optional threading.Event that, when set, stops the loop.
    """
    console = Console()
    with Live(_build_table(), console=console, refresh_per_second=4) as live:
        while not (stop_event and stop_event.is_set()):
            sleep(REFRESH_SECONDS)
            live.update(_build_table())
