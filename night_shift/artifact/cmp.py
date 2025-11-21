from typing import List
from shared.type_definitions.result import Err, Ok, Result
from night_shift.models import CMPSignal


def get_latest_signals() -> Result[List[CMPSignal], str]:
    """Return the latest CMP signals."""
    try:
        raw = [
            {"signal": "S1", "value": 0.75},
            {"signal": "S2", "value": 0.42},
        ]
        signals = [CMPSignal(**item) for item in raw]
        return Ok(signals)
    except Exception as exc:
        return Err(str(exc))
