from typing import List
from night_shift.utils.result import Result
from night_shift.models import CMPSignal


def get_latest_signals() -> Result[List[CMPSignal], str]:
    """Return the latest CMP signals."""
    try:
        raw = [
            {"signal": "S1", "value": 0.75},
            {"signal": "S2", "value": 0.42},
        ]
        signals = [CMPSignal(**item) for item in raw]
        return Result.Ok(signals)
    except Exception as exc:
        return Result.Err(str(exc))
