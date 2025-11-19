import threading
import time

from night_shift.tui.dashboard import (
    CycleSummary,
    BacklogCounts,
    CMPSignal,
    CMPSignals,
    CommitInfo,
    Result,
    get_cycle_summary,
    get_backlog_counts,
    get_cmp_signals,
    get_recent_commits,
    run_dashboard,
)


def test_result_pattern() -> None:
    ok = Result.Ok(123)
    err = Result.Err("boom")
    assert ok.is_ok()
    assert not ok.is_err()
    assert ok.unwrap() == 123
    assert err.is_err()
    assert err.unwrap_err() == "boom"


def test_cycle_summary_adapter() -> None:
    res: Result[CycleSummary, str] = get_cycle_summary()
    assert res.is_ok()
    cs = res.unwrap()
    assert isinstance(cs.current, int)
    assert cs.next == cs.current + 1


def test_backlog_counts_adapter() -> None:
    res = get_backlog_counts()
    assert res.is_ok()
    bc = res.unwrap()
    assert bc.todo >= 0 and bc.blocked >= 0


def test_cmp_signals_adapter() -> None:
    res = get_cmp_signals()
    assert res.is_ok()
    cmp = res.unwrap()
    assert isinstance(cmp.signals, list)
    assert all(isinstance(s, CMPSignal) for s in cmp.signals)


def test_recent_commits_adapter() -> None:
    res = get_recent_commits(limit=2)
    assert res.is_ok()
    commits = res.unwrap()
    assert len(commits) == 2
    assert all(isinstance(c, CommitInfo) for c in commits)


def test_dashboard_runs_and_stops() -> None:
    """Run the dashboard in a background thread and stop it quickly."""
    stop_evt = threading.Event()
    thread = threading.Thread(target=run_dashboard, args=(stop_evt,))
    thread.start()
    time.sleep(0.2)  # Let it start and render at least once.
    stop_evt.set()
    thread.join(timeout=2)
    assert not thread.is_alive()
