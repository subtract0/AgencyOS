from shared.type_definitions.result import Err, Ok, Result
from night_shift.models import BacklogCounts


def get_backlog_counts() -> Result[BacklogCounts, str]:
    """Return backlog counts per priority."""
    try:
        data = {"high": 5, "medium": 12, "low": 20}
        counts = BacklogCounts(**data)
        return Ok(counts)
    except Exception as exc:
        return Err(str(exc))
