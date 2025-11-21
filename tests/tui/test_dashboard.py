import importlib.util

import pytest

_rich_available = importlib.util.find_spec("rich") is not None

pytestmark = pytest.mark.skipif(
    not _rich_available,
    reason="Requires 'rich' package for dashboard rendering",
)

if _rich_available:
    from night_shift.tui.dashboard import run_dashboard

def test_dashboard_runs_briefly():
    # Run the dashboard for a short time; it should exit without errors.
    run_dashboard(max_duration=0.2)
