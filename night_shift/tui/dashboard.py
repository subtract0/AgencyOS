import time
import threading
from typing import List
from rich.console import Console
from rich.table import Table
from rich.live import Live
from night_shift.util.result import Result, Ok, Err
from night_shift.artifacts.cycle import get_current_cycle_result
from night_shift.artifacts.backlog import backlog_count_result
from night_shift.signals.cmp import latest_cmp_signal_result
from night_shift.vcs.git import recent_commits_result

REFRESH_SEC = 2.0

def _build_table() -> Table:
    table = Table(title="🌙 Night Shift Status", expand=True)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    cycle_res: Result[str, str] = get_current_cycle_result()
    table.add_row("Current Cycle", cycle_res.ok if cycle_res.is_ok() else f"Error: {cycle_res.err}")
    backlog_res: Result[int, str] = backlog_count_result()
    table.add_row("Backlog Items", str(backlog_res.ok) if backlog_res.is_ok() else f"Error: {backlog_res.err}")
    cmp_res: Result[tuple[time.struct_time, float], str] = latest_cmp_signal_result()
    if cmp_res.is_ok():
        ts, val = cmp_res.ok
        table.add_row("Latest CMP", f"{time.strftime('%Y-%m-%d', ts)} → {val:.2f}")
    else:
        table.add_row("Latest CMP", f"Error: {cmp_res.err}")
    commits_res: Result[List[object], str] = recent_commits_result()
    if commits_res.is_ok():
        lines = "\n".join(f"[{c.sha[:7]}] {c.author} {c.date} • {c.message}" for c in commits_res.ok)
    else:
        lines = f"Error: {commits_res.err}"
    table.add_row("Recent Git Commits", lines)
    return table

def run_dashboard(stop_event: threading.Event | None = None) -> None:
    console = Console()
    with Live(_build_table(), console=console, refresh_per_second=4) as live:
        try:
            while True:
                if stop_event and stop_event.is_set():
                    break
                time.sleep(REFRESH_SEC)
                live.update(_build_table())
        except KeyboardInterrupt:
            console.print("\n[bold red]Dashboard stopped.[/]")
