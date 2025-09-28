import logging
import os
import warnings


def silence_warnings_and_logs() -> None:
    """Suppress Python warnings and noisy third-party loggers.

    This function should be called as early as possible in the process
    (before importing third-party libraries) to minimize startup noise.
    """
    # Environment-level suppression for Python warnings
    os.environ.setdefault("PYTHONWARNINGS", "ignore")

    # Suppress warnings across common categories
    warnings.filterwarnings("ignore")
    for _category in (
        Warning,
        DeprecationWarning,
        PendingDeprecationWarning,
        ResourceWarning,
        UserWarning,
    ):
        try:
            warnings.filterwarnings("ignore", category=_category)
        except (AttributeError, TypeError) as e:
            # Expected if warnings module doesn't support this category
            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to set warning filter for {_category}: {e}")

    try:
        warnings.simplefilter("ignore")
    except (AttributeError, ValueError) as e:
        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to set simple warning filter: {e}")

    # Route warnings through logging, then quiet noisy loggers
    try:
        logging.captureWarnings(True)
        logging.getLogger().setLevel(logging.ERROR)
        for _name in ("aiohttp", "httpx", "pydantic", "litellm", "agency_swarm"):
            logging.getLogger(_name).setLevel(logging.ERROR)
    except (AttributeError, ValueError) as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to configure logging settings: {e}")

    # Final guard: disable default warning printer
    try:

        def _noop_showwarning(*_args, **_kwargs):
            return None

        warnings.showwarning = _noop_showwarning
    except (AttributeError, TypeError) as e:
        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to override warning display function: {e}")
