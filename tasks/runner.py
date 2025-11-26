import logging
from typing import Any, Callable
from nightshift.watchdog import NightShiftWatchdog, TaskTimeoutError

logger = logging.getLogger(__name__)

def run_task(
    task_callable: Callable[..., Any],
    *args: Any,
    timeout_minutes: int = 15,
    **kwargs: Any,
) -> Any:
    """
    Execute ``task_callable`` protected by ``NightShiftWatchdog``.
    Returns the callable's return value or re‑raises ``TaskTimeoutError``.
    """
    try:
        with NightShiftWatchdog(timeout_minutes * 60):
            return task_callable(*args, **kwargs)
    except TaskTimeoutError as toe:
        logger.error(toe)
        raise
