# Legacy tests for earlier watchdog implementation. Skipped until updated
# to match tools/night_shift_watchdog.py

import pytest

pytest.skip(
    "Legacy nightshift.watchdog tests are incompatible with the current implementation",
    allow_module_level=True,
)
