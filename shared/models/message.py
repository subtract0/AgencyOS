from __future__ import annotations

"""
Message models for type-safe inter-agent communication.

These models replace untyped dict-based messages with a versioned envelope that
supports validation, routing, and backward-compatible serialization.
"""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field, ConfigDict

from shared.type_definitions.json import JSONValue


class MessageEnvelope(BaseModel):
    """Versioned message envelope used for inter-agent communication."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique message identifier")
    version: int = Field(1, ge=1, description="Envelope version for evolution")
    type: str = Field(..., description="Message type or topic")
    sender: str = Field(..., description="Agent or component sending the message")
    recipient: Optional[str] = Field(None, description="Intended recipient agent (optional for broadcast)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, JSONValue] = Field(default_factory=dict, description="Message payload data")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing requests/replies")

    def to_dict(self) -> Dict[str, JSONValue]:
        """Backward-compatible JSON-serializable representation."""
        # We deliberately keep JSONValue to ensure no Any escapes
        doc = self.model_dump(mode="json")
        # pydantic returns standard types compatible with JSON
        return doc  # type: ignore[return-value]


__all__ = [
    "MessageEnvelope",
]
