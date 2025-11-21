import pytest
from night_shift.tui.dashboard import run_dashboard

def test_dashboard_runs_briefly():
    # Run the dashboard for a short time; it should exit without errors.
    run_dashboard(max_duration=0.2)
