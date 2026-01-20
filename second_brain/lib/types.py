"""Second Brain type definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json
import uuid


class Category(Enum):
    """The four buckets for thoughts."""
    PEOPLE = "people"
    PROJECTS = "projects"
    IDEAS = "ideas"
    ADMIN = "admin"
    UNKNOWN = "unknown"


@dataclass
class Person:
    """A person in your network."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    context: str = ""  # How you know them, what matters
    follow_ups: list[str] = field(default_factory=list)
    last_touched: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "context": self.context,
            "follow_ups": self.follow_ups,
            "last_touched": self.last_touched,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Person":
        return cls(**data)


@dataclass
class Project:
    """A project you're working on."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    status: str = "active"  # active, waiting, blocked, someday, done
    next_action: str = ""  # The specific next step
    notes: str = ""
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "next_action": self.next_action,
            "notes": self.notes,
            "created": self.created,
            "updated": self.updated,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(**data)


@dataclass
class Idea:
    """An idea worth remembering."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    oneliner: str = ""  # Core insight in one sentence
    notes: str = ""
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "oneliner": self.oneliner,
            "notes": self.notes,
            "created": self.created,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Idea":
        return cls(**data)


@dataclass
class AdminTask:
    """An administrative task or errand."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    due_date: Optional[str] = None
    status: str = "pending"  # pending, done
    notes: str = ""
    created: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "due_date": self.due_date,
            "status": self.status,
            "notes": self.notes,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AdminTask":
        return cls(**data)


@dataclass
class InboxEntry:
    """Raw captured thought before processing."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    raw_text: str = ""
    captured_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # After classification
    filed_to: Optional[str] = None  # Category
    record_id: Optional[str] = None  # ID in destination database
    confidence: float = 0.0
    status: str = "pending"  # pending, filed, needs_review, failed

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "raw_text": self.raw_text,
            "captured_at": self.captured_at,
            "filed_to": self.filed_to,
            "record_id": self.record_id,
            "confidence": self.confidence,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InboxEntry":
        return cls(**data)


@dataclass
class ClassificationResult:
    """Result from the AI classifier."""
    category: Category
    confidence: float
    extracted_data: dict  # Fields extracted for that category
    reasoning: str = ""
