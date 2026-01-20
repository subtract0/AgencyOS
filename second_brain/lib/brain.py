"""Second Brain Orchestrator.

The core loop that makes thoughts become actionable:
1. CAPTURE - Frictionless input
2. CLASSIFY - AI routing (local LLM)
3. FILE - Store in the right bucket
4. LOG - Audit trail (receipts)
5. SURFACE - Daily/weekly digests
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
import httpx

from .types import (
    Category, Person, Project, Idea, AdminTask, InboxEntry, ClassificationResult
)
from .classifier import classify_thought, needs_review, CONFIDENCE_THRESHOLD
from .storage import SecondBrainStorage


class SecondBrain:
    """Your Second Brain - an always-on system that works while you sleep.

    Principles:
    - Human does ONE thing: capture
    - AI does classification and routing
    - System does filing, logging, surfacing
    - Trust comes from receipts and easy corrections
    """

    def __init__(self, storage: Optional[SecondBrainStorage] = None):
        self.storage = storage or SecondBrainStorage()

    def capture(self, thought: str) -> dict:
        """Capture a raw thought and process it.

        This is the ONE behavior the human needs to do.
        Everything else is automated.

        Returns a receipt with what happened.
        """
        # 1. Create inbox entry (audit trail starts here)
        entry = InboxEntry(raw_text=thought)
        self.storage.log_capture(entry)

        # 2. Classify with AI
        result = classify_thought(thought)

        # 3. Route based on confidence (bouncer pattern)
        if needs_review(result):
            entry.status = "needs_review"
            entry.confidence = result.confidence
            entry.filed_to = result.category.value
            self.storage.log_capture(entry)

            return {
                "status": "needs_review",
                "entry_id": entry.id,
                "confidence": result.confidence,
                "suggested_category": result.category.value,
                "message": f"I'm {int(result.confidence * 100)}% confident this is {result.category.value}. "
                          f"Reply 'fix:{entry.id}:category' to correct.",
                "reasoning": result.reasoning
            }

        # 4. File to the right bucket
        record_id = self._file_to_category(result)

        # 5. Update inbox entry (receipt)
        entry.status = "filed"
        entry.filed_to = result.category.value
        entry.record_id = record_id
        entry.confidence = result.confidence
        self.storage.log_capture(entry)

        return {
            "status": "filed",
            "entry_id": entry.id,
            "category": result.category.value,
            "record_id": record_id,
            "confidence": result.confidence,
            "message": f"Filed to {result.category.value}: {record_id}. "
                      f"Confidence: {int(result.confidence * 100)}%. "
                      f"Reply 'fix:{entry.id}:category' if wrong.",
            "extracted": result.extracted_data
        }

    def _file_to_category(self, result: ClassificationResult) -> str:
        """Create a record in the appropriate category."""
        data = result.extracted_data

        if result.category == Category.PEOPLE:
            person = Person(
                name=data.get("name", "Unknown"),
                context=data.get("context", ""),
                follow_ups=data.get("follow_ups", []),
                tags=data.get("tags", [])
            )
            return self.storage.save_person(person)

        elif result.category == Category.PROJECTS:
            project = Project(
                name=data.get("name", "Untitled Project"),
                status=data.get("status", "active"),
                next_action=data.get("next_action", ""),
                notes=data.get("notes", ""),
                tags=data.get("tags", [])
            )
            return self.storage.save_project(project)

        elif result.category == Category.IDEAS:
            idea = Idea(
                title=data.get("title", "Untitled Idea"),
                oneliner=data.get("oneliner", ""),
                notes=data.get("notes", ""),
                tags=data.get("tags", [])
            )
            return self.storage.save_idea(idea)

        elif result.category == Category.ADMIN:
            task = AdminTask(
                name=data.get("name", "Untitled Task"),
                due_date=data.get("due_date"),
                notes=data.get("notes", "")
            )
            return self.storage.save_admin(task)

        else:
            # Unknown - create as idea by default
            idea = Idea(
                title="Unclassified",
                oneliner=result.extracted_data.get("raw_text", "")[:100],
                notes=str(result.extracted_data)
            )
            return self.storage.save_idea(idea)

    def fix(self, entry_id: str, correct_category: str) -> dict:
        """Fix a misclassified entry (the fix button).

        Usage: fix("abc123", "projects")
        """
        entry = self.storage.get_inbox_entry(entry_id)
        if not entry:
            return {"status": "error", "message": f"Entry {entry_id} not found"}

        # Re-classify with hint
        result = classify_thought(f"[CATEGORY: {correct_category}] {entry.raw_text}")
        result.category = Category(correct_category)
        result.confidence = 1.0  # Human corrected = full confidence

        # File to correct category
        record_id = self._file_to_category(result)

        # Update entry
        entry.status = "filed"
        entry.filed_to = correct_category
        entry.record_id = record_id
        entry.confidence = 1.0
        self.storage.log_capture(entry)

        return {
            "status": "fixed",
            "entry_id": entry_id,
            "new_category": correct_category,
            "record_id": record_id,
            "message": f"Fixed! Now filed as {correct_category}: {record_id}"
        }

    def daily_digest(self) -> str:
        """Generate a daily digest (tap on the shoulder).

        Designed to fit on a phone screen (<150 words).
        Top 3 actions + 1 stuck thing + 1 small win.
        """
        active_projects = self.storage.get_active_projects()[:5]
        pending_admin = self.storage.list_admin()[:3]
        needs_review = self.storage.get_needs_review()[:3]

        # Build digest
        lines = [
            f"📅 **Daily Digest** - {datetime.now().strftime('%A, %B %d')}",
            "",
            "**🎯 Top Actions Today:**"
        ]

        # Get top 3 next actions from projects
        action_count = 0
        for p in active_projects:
            if p.next_action and action_count < 3:
                lines.append(f"• {p.next_action} ({p.name})")
                action_count += 1

        # Add pending admin if space
        for t in pending_admin:
            if action_count < 3:
                due = f" (due {t.due_date})" if t.due_date else ""
                lines.append(f"• {t.name}{due}")
                action_count += 1

        if action_count == 0:
            lines.append("• No urgent actions - review your projects")

        # Stuck indicator
        blocked = [p for p in self.storage.list_projects() if p.status == "blocked"]
        if blocked:
            lines.extend(["", "**⚠️ Possibly Stuck:**"])
            lines.append(f"• {blocked[0].name}: {blocked[0].notes[:50]}...")

        # Needs review
        if needs_review:
            lines.extend(["", f"**📥 {len(needs_review)} items need review**"])

        # Stats
        stats = self.storage.get_stats()
        lines.extend([
            "",
            f"_Brain: {stats['projects']} projects, {stats['people']} people, {stats['ideas']} ideas_"
        ])

        return "\n".join(lines)

    def weekly_review(self) -> str:
        """Generate a weekly review.

        What happened, biggest open loops, suggestions, recurring themes.
        """
        # Get recent activity
        recent_inbox = self.storage.list_inbox(limit=50)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        this_week = [e for e in recent_inbox if e.captured_at >= week_ago]

        # Count by category
        category_counts = {}
        for entry in this_week:
            cat = entry.filed_to or "unclassified"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        active_projects = self.storage.get_active_projects()
        blocked_projects = [p for p in self.storage.list_projects() if p.status == "blocked"]
        waiting_projects = [p for p in self.storage.list_projects() if p.status == "waiting"]

        lines = [
            f"📊 **Weekly Review** - Week of {datetime.now().strftime('%B %d, %Y')}",
            "",
            "**📈 This Week:**",
            f"• {len(this_week)} thoughts captured"
        ]

        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  - {cat}: {count}")

        lines.extend([
            "",
            "**🚀 Active Projects:**"
        ])
        for p in active_projects[:5]:
            next_act = f" → {p.next_action}" if p.next_action else ""
            lines.append(f"• {p.name}{next_act}")

        if blocked_projects:
            lines.extend(["", "**🚧 Blocked:**"])
            for p in blocked_projects[:3]:
                lines.append(f"• {p.name}")

        if waiting_projects:
            lines.extend(["", "**⏳ Waiting:**"])
            for p in waiting_projects[:3]:
                lines.append(f"• {p.name}")

        # Suggestions
        lines.extend([
            "",
            "**💡 Suggested Focus for Next Week:**",
            f"• Review {len(blocked_projects)} blocked projects",
            f"• Clear {len(self.storage.get_needs_review())} items needing review"
        ])

        if active_projects:
            lines.append(f"• Ship next action on: {active_projects[0].name}")

        return "\n".join(lines)

    def search(self, query: str) -> list[dict]:
        """Simple search across all categories."""
        results = []
        query_lower = query.lower()

        # Search people
        for person in self.storage.list_people():
            if query_lower in person.name.lower() or query_lower in person.context.lower():
                results.append({
                    "type": "person",
                    "id": person.id,
                    "name": person.name,
                    "preview": person.context[:100]
                })

        # Search projects
        for project in self.storage.list_projects():
            if query_lower in project.name.lower() or query_lower in project.notes.lower():
                results.append({
                    "type": "project",
                    "id": project.id,
                    "name": project.name,
                    "preview": project.next_action or project.notes[:100]
                })

        # Search ideas
        for idea in self.storage.list_ideas():
            if query_lower in idea.title.lower() or query_lower in idea.oneliner.lower():
                results.append({
                    "type": "idea",
                    "id": idea.id,
                    "name": idea.title,
                    "preview": idea.oneliner
                })

        return results[:20]  # Limit results

    def get_status(self) -> dict:
        """Get current brain status."""
        stats = self.storage.get_stats()
        needs_review = len(self.storage.get_needs_review())

        return {
            "stats": stats,
            "needs_review": needs_review,
            "active_projects": len(self.storage.get_active_projects()),
            "confidence_threshold": CONFIDENCE_THRESHOLD
        }
