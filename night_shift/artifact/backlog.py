from night_shift.utils.result import Result
from night_shift.models import BacklogCounts


def get_backlog_counts() -> Result[BacklogCounts, str]:
    """Return backlog counts per priority."""
    try:
        data = {"high": 5, "medium": 12, "low": 20}
        counts = BacklogCounts(**data)
        return Result.Ok(counts)
    except Exception as exc:
        return Result.Err(str(exc))
