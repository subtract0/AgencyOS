from night_shift.utils.result import Result
from night_shift.models import CycleSummary


def get_cycle_summary() -> Result[CycleSummary, str]:
    """Return a summary of the current cycle."""
    try:
        # Placeholder logic – replace with real data source
        data = {"id": 1, "name": "Cycle 1", "status": "active"}
        summary = CycleSummary(**data)
        return Result.Ok(summary)
    except Exception as exc:
        return Result.Err(str(exc))
