"""Local file storage for Second Brain.

Uses JSON files as the filing cabinet (source of truth).
Portable, human-readable, git-friendly.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .types import (
    Person, Project, Idea, AdminTask, InboxEntry, Category
)


class SecondBrainStorage:
    """Local file-based storage for Second Brain data.

    Directory structure:
    data/
    ├── people/      # Person records
    ├── projects/    # Project records
    ├── ideas/       # Idea records
    ├── admin/       # Admin task records
    └── inbox/       # Audit trail (inbox log)
    """

    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data"
            )
        self.base_path = Path(base_path)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create storage directories if they don't exist."""
        for category in ["people", "projects", "ideas", "admin", "inbox"]:
            (self.base_path / category).mkdir(parents=True, exist_ok=True)

    def _get_path(self, category: str, record_id: str) -> Path:
        """Get file path for a record."""
        return self.base_path / category / f"{record_id}.json"

    # === PEOPLE ===

    def save_person(self, person: Person) -> str:
        """Save a person record. Returns the ID."""
        person.last_touched = datetime.now().isoformat()
        path = self._get_path("people", person.id)
        with open(path, "w") as f:
            json.dump(person.to_dict(), f, indent=2)
        return person.id

    def get_person(self, person_id: str) -> Optional[Person]:
        """Get a person by ID."""
        path = self._get_path("people", person_id)
        if not path.exists():
            return None
        with open(path) as f:
            return Person.from_dict(json.load(f))

    def list_people(self) -> list[Person]:
        """List all people."""
        people = []
        for path in (self.base_path / "people").glob("*.json"):
            with open(path) as f:
                people.append(Person.from_dict(json.load(f)))
        return sorted(people, key=lambda p: p.last_touched, reverse=True)

    def find_person_by_name(self, name: str) -> Optional[Person]:
        """Find a person by name (case-insensitive partial match)."""
        name_lower = name.lower()
        for person in self.list_people():
            if name_lower in person.name.lower():
                return person
        return None

    # === PROJECTS ===

    def save_project(self, project: Project) -> str:
        """Save a project record. Returns the ID."""
        project.updated = datetime.now().isoformat()
        path = self._get_path("projects", project.id)
        with open(path, "w") as f:
            json.dump(project.to_dict(), f, indent=2)
        return project.id

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        path = self._get_path("projects", project_id)
        if not path.exists():
            return None
        with open(path) as f:
            return Project.from_dict(json.load(f))

    def list_projects(self, status: Optional[str] = None) -> list[Project]:
        """List projects, optionally filtered by status."""
        projects = []
        for path in (self.base_path / "projects").glob("*.json"):
            with open(path) as f:
                project = Project.from_dict(json.load(f))
                if status is None or project.status == status:
                    projects.append(project)
        return sorted(projects, key=lambda p: p.updated, reverse=True)

    def get_active_projects(self) -> list[Project]:
        """Get all active projects with their next actions."""
        return [p for p in self.list_projects() if p.status == "active"]

    # === IDEAS ===

    def save_idea(self, idea: Idea) -> str:
        """Save an idea record. Returns the ID."""
        path = self._get_path("ideas", idea.id)
        with open(path, "w") as f:
            json.dump(idea.to_dict(), f, indent=2)
        return idea.id

    def get_idea(self, idea_id: str) -> Optional[Idea]:
        """Get an idea by ID."""
        path = self._get_path("ideas", idea_id)
        if not path.exists():
            return None
        with open(path) as f:
            return Idea.from_dict(json.load(f))

    def list_ideas(self) -> list[Idea]:
        """List all ideas."""
        ideas = []
        for path in (self.base_path / "ideas").glob("*.json"):
            with open(path) as f:
                ideas.append(Idea.from_dict(json.load(f)))
        return sorted(ideas, key=lambda i: i.created, reverse=True)

    # === ADMIN ===

    def save_admin(self, task: AdminTask) -> str:
        """Save an admin task. Returns the ID."""
        path = self._get_path("admin", task.id)
        with open(path, "w") as f:
            json.dump(task.to_dict(), f, indent=2)
        return task.id

    def get_admin(self, task_id: str) -> Optional[AdminTask]:
        """Get an admin task by ID."""
        path = self._get_path("admin", task_id)
        if not path.exists():
            return None
        with open(path) as f:
            return AdminTask.from_dict(json.load(f))

    def list_admin(self, include_done: bool = False) -> list[AdminTask]:
        """List admin tasks."""
        tasks = []
        for path in (self.base_path / "admin").glob("*.json"):
            with open(path) as f:
                task = AdminTask.from_dict(json.load(f))
                if include_done or task.status != "done":
                    tasks.append(task)
        return sorted(tasks, key=lambda t: t.due_date or "9999-99-99")

    # === INBOX LOG (Audit Trail) ===

    def log_capture(self, entry: InboxEntry) -> str:
        """Log a captured thought to the inbox log."""
        path = self._get_path("inbox", entry.id)
        with open(path, "w") as f:
            json.dump(entry.to_dict(), f, indent=2)
        return entry.id

    def get_inbox_entry(self, entry_id: str) -> Optional[InboxEntry]:
        """Get an inbox entry by ID."""
        path = self._get_path("inbox", entry_id)
        if not path.exists():
            return None
        with open(path) as f:
            return InboxEntry.from_dict(json.load(f))

    def list_inbox(self, status: Optional[str] = None, limit: int = 100) -> list[InboxEntry]:
        """List inbox entries, most recent first."""
        entries = []
        for path in (self.base_path / "inbox").glob("*.json"):
            with open(path) as f:
                entry = InboxEntry.from_dict(json.load(f))
                if status is None or entry.status == status:
                    entries.append(entry)
        return sorted(entries, key=lambda e: e.captured_at, reverse=True)[:limit]

    def get_needs_review(self) -> list[InboxEntry]:
        """Get all entries that need human review."""
        return self.list_inbox(status="needs_review")

    # === UTILITIES ===

    def update_entry_status(self, entry_id: str, new_category: str, new_record_id: str):
        """Update an inbox entry after manual correction (fix button)."""
        entry = self.get_inbox_entry(entry_id)
        if entry:
            entry.filed_to = new_category
            entry.record_id = new_record_id
            entry.status = "filed"
            self.log_capture(entry)

    def get_stats(self) -> dict:
        """Get storage statistics."""
        return {
            "people": len(list((self.base_path / "people").glob("*.json"))),
            "projects": len(list((self.base_path / "projects").glob("*.json"))),
            "ideas": len(list((self.base_path / "ideas").glob("*.json"))),
            "admin": len(list((self.base_path / "admin").glob("*.json"))),
            "inbox": len(list((self.base_path / "inbox").glob("*.json"))),
        }
