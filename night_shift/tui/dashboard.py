import threading
import time
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

from night_shift.artifact.cycle import get_cycle_summary
from night_shift.artifact.backlog import get_backlog_counts
from night_shift.artifact.cmp import get_latest_signals
from night_shift.artifact.git import get_recent_commits

console = Console()


def _build_cycle_panel() -> Panel:
    res = get_cycle_summary()
    table = Table(title="Cycle")
    table.add_column("Field")
    table.add_column("Value")
    if res.is_ok():
        c = res.unwrap()
        table.add_row("ID", str(c.id))
        table.add_row("Name", c.name)
        table.add_row("Status", c.status)
    else:
        table.add_row("Error", res.unwrap_err())
    return Panel(table)


def _build_backlog_panel() -> Panel:
    res = get_backlog_counts()
    table = Table(title="Backlog")
    table.add_column("Priority")
    table.add_column("Count")
    if res.is_ok():
        b = res.unwrap()
        table.add_row("High", str(b.high))
        table.add_row("Medium", str(b.medium))
        table.add_row("Low", str(b.low))
    else:
        table.add_row("Error", res.unwrap_err())
    return Panel(table)


def _build_cmp_panel() -> Panel:
    res = get_latest_signals()
    table = Table(title="CMP Signals")
    table.add_column("Signal")
    table.add_column("Value", justify="right")
    if res.is_ok():
        for sig in res.unwrap():
            table.add_row(sig.signal, f"{sig.value:.2f}")
    else:
        table.add_row("Error", res.unwrap_err())
    return Panel(table)


def _build_commits_panel() -> Panel:
    res = get_recent_commits(limit=5)
    table = Table(title="Recent Commits")
    table.add_column("SHA")
    table.add_column("Author")
    table.add_column("Message")
    if res.is_ok():
        for com in res.unwrap():
            table.add_row(com.sha, com.author, com.message)
    else:
        table.add_row("Error", res.unwrap_err(), "")
    return Panel(table)


def _render_dashboard() -> Table:
    grid = Table.grid(expand=True)
    grid.add_row(_build_cycle_panel(), _build_backlog_panel(),
                 _build_cmp_panel(), _build_commits_panel())
    return grid


def run_dashboard(max_duration: Optional[float] = None) -> None:
    """Run the TUI dashboard.

    Press ``q`` to quit.  If ``max_duration`` is provided, the dashboard
    will automatically exit after that many seconds (useful for tests).
    """
    stop_event = threading.Event()

    # Input thread only when not in timed test mode
    if max_duration is None:
        def input_thread() -> None:
            while not stop_event.is_set():
                try:
                    ch = console.input("", markup=False)
                    if ch.lower() == "q":
                        stop_event.set()
                except (KeyboardInterrupt, EOFError):
                    stop_event.set()

        threading.Thread(target=input_thread, daemon=True).start()

    start = time.time()
    with Live(_render_dashboard(), refresh_per_second=1, console=console) as live:
        while not stop_event.is_set():
            live.update(_render_dashboard())
            if max_duration is not None and (time.time() - start) >= max_duration:
                stop_event.set()
                break
            time.sleep(0.5)
    console.clear()
