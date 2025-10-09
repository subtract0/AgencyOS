"""
Priority task models for backlog management.

Constitutional compliance:
- ADR-008: Strict typing enforcement (no Dict[Any, Any])
- Constitutional Law #2: Explicit types always
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PriorityTask(BaseModel):
    """
    Represents a single task in the TOP 20 priority queue.

    Used for parsing and managing tasks in the backlog file.
    """

    rank: int = Field(..., ge=1, le=20, description="Priority rank (1-20)")
    id: str = Field(..., description="Task identifier (slugified)")
    description: str = Field(..., description="Human-readable task name")
    value: int = Field(..., ge=1, le=10, description="Business value (1-10)")
    effort: int = Field(..., ge=1, le=10, description="Implementation effort (1-10)")
    roi: float = Field(..., description="ROI = Value / Effort")
    status: Literal["Ready", "Blocked", "In Progress", "Done"] = Field(
        ..., description="Current task status"
    )
    command: str = Field(..., description="Command to execute task")
    next_step: str = Field(..., description="First action to take")

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def calculate_roi(cls, value: int, effort: int) -> float:
        """
        Calculate ROI (Return on Investment).

        Args:
            value: Business value (1-10)
            effort: Implementation effort (1-10)

        Returns:
            ROI as value/effort ratio
        """
        if effort == 0:
            raise ValueError("Effort cannot be zero")
        return round(value / effort, 2)


class BacklogError(BaseModel):
    """
    Error information for backlog operations.

    Used with Result[T, BacklogError] pattern for functional error handling.
    """

    error_type: str = Field(
        ...,
        description="Error type: ParseError, NotFound, IOError, ValidationError",
    )
    message: str = Field(..., description="Human-readable error message")
    line_number: int | None = Field(
        default=None, description="Line number where error occurred (if applicable)"
    )

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def parse_error(cls, message: str, line_number: int | None = None) -> "BacklogError":
        """Create ParseError."""
        return cls(
            error_type="ParseError",
            message=f"Failed to parse backlog: {message}",
            line_number=line_number,
        )

    @classmethod
    def not_found(cls, message: str) -> "BacklogError":
        """Create NotFound error."""
        return cls(error_type="NotFound", message=message)

    @classmethod
    def io_error(cls, message: str) -> "BacklogError":
        """Create IOError."""
        return cls(error_type="IOError", message=f"Filesystem error: {message}")

    @classmethod
    def validation_error(cls, message: str) -> "BacklogError":
        """Create ValidationError."""
        return cls(error_type="ValidationError", message=message)
