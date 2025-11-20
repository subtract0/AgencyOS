import threading
import time
from night_shift.tui.dashboard import run_dashboard
from night_shift.artifacts.cycle import set_current_cycle
from night_shift.artifacts.backlog import add_backlog, remove_backlog
from night_shift.signals.cmp import add_cmp_signal
from datetime import datetime

def test_dashboard_runs_and_stops():
    stop_event = threading.Event()
    def target():
        run_dashboard(stop_event=stop_event)
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    time.sleep(3)
    stop_event.set()
    thread.join(timeout=2)
    assert not thread.is_alive()

def test_data_providers_return_results():
    class MockCycle:
        name = "Sprint 42"
    set_current_cycle(MockCycle())
    add_backlog("Task B")
    remove_backlog("Task A") if "Task A" in [] else None
    add_cmp_signal(datetime.utcnow(), 3.14)
    from night_shift.artifacts.cycle import get_current_cycle_result
    from night_shift.artifacts.backlog import backlog_count_result
    from night_shift.signals.cmp import latest_cmp_signal_result
    cycle_res = get_current_cycle_result()
    backlog_res = backlog_count_result()
    cmp_res = latest_cmp_signal_result()
    assert cycle_res.is_ok() and cycle_res.ok == "Sprint 42"
    assert backlog_res.is_ok() and backlog_res.ok == 1
    assert cmp_res.is_ok()
    ts, val = cmp_res.ok
    assert isinstance(ts, datetime)
    assert isinstance(val, float) and abs(val - 3.14) < 1e-6
