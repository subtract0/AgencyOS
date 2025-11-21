from shared.type_definitions.result import Err, Ok, Result
from night_shift.models import CycleSummary


def get_cycle_summary() -> Result[CycleSummary, str]:
    """Return a summary of the current cycle."""
    try:
        # Placeholder logic – replace with real data source
        data = {"id": 1, "name": "Cycle 1", "status": "active"}
        summary = CycleSummary(**data)
        return Ok(summary)
    except Exception as exc:
        return Err(str(exc))
