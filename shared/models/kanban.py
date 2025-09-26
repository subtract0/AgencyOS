from __future__ import annotations

"""
Typed models for Kanban cards and feeds.

These models formalize the structure returned by tools.kanban.adapters while
preserving backward compatibility (adapters may still return plain dicts for now).

Adoption plan:
- Keep adapters returning dict[str, JSONValue] until all consumers are updated
- Optionally switch adapters to return KanbanFeed/KanbanCard later and serialize with model_dump()
"""

from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

from shared.types.json import JSONValue


CardType = Literal["error", "task", "pattern", "antipattern", "discovery"]
CardStatus = Literal["To Investigate", "In Progress", "Learned", "Resolved"]


class KanbanCard(BaseModel):
    """A single card in the Kanban feed summarizing an event, task, or pattern."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Stable card identifier")
    type: CardType = Field(..., description="Card category")
    title: str = Field(..., description="Short, human-readable title")
    summary: str = Field("", description="Brief summary; may be truncated")
    source_ref: str = Field(..., description="Source reference, e.g., event or pattern id")
    status: CardStatus = Field(..., description="Workflow status of the card")
    created_at: str = Field(..., description="ISO-8601 timestamp (UTC)")
    links: List[str] = Field(default_factory=list, description="Optional links related to this card")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering/grouping")

    def to_dict(self) -> dict[str, JSONValue]:
        return self.model_dump(mode="json")  # type: ignore[return-value]


class KanbanFeed(BaseModel):
    """Container for a generated Kanban feed and its cards."""
    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(..., description="ISO-8601 timestamp when feed was generated")
    cards: List[KanbanCard] = Field(default_factory=list, description="Cards included in the feed")

    def to_dict(self) -> dict[str, JSONValue]:
        return self.model_dump(mode="json")  # type: ignore[return-value]


__all__ = [
    "KanbanCard",
    "KanbanFeed",
    "CardType",
    "CardStatus",
]
