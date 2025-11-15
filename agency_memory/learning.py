"""
Simple learning consolidation module.
Provides deterministic summarization of memory tag frequencies and patterns.

Also implements CMP (Clade Metaproductivity) types for tracking autonomous PR experiments
and computing clade performance scores.
"""

import json
import logging
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from shared.models.learning import (
    ContentTypeBreakdown,
    LearningConsolidation,
    LearningInsight,
    PatternAnalysis,
    TimeDistribution,
)
from shared.type_definitions.json import JSONValue

logger = logging.getLogger(__name__)


def consolidate_learnings(memories: list[dict[str, JSONValue]]) -> dict[str, JSONValue]:
    """
    Consolidate learnings from memory records into structured summary.

    Provides deterministic analysis of:
    - Tag frequency distribution
    - Memory patterns over time
    - Content type analysis
    - Usage insights

    Args:
        memories: List of memory records with tags, timestamps, and content

    Returns:
        Structured summary with learning insights
    """
    if not memories:
        # Return simple dict for backward compatibility
        return {
            "summary": "No memories to analyze",
            "total_memories": 0,
            "tag_frequencies": {},
            "patterns": {},
            "generated_at": datetime.now().isoformat(),
        }

    # Initialize counters and analyzers
    tag_counter: Counter[str] = Counter()
    content_types: Counter[str] = Counter()
    hourly_distribution: defaultdict[int, int] = defaultdict(int)
    daily_distribution: defaultdict[str, int] = defaultdict(int)

    # Process each memory
    for memory in memories:
        # Count tags
        tags = memory.get("tags", [])
        if isinstance(tags, list):
            # Filter to only string tags
            string_tags = [str(tag) for tag in tags if isinstance(tag, str)]
            tag_counter.update(string_tags)

        # Analyze content types
        content = memory.get("content", "")
        content_type = _categorize_content(content)
        content_types[content_type] += 1

        # Time pattern analysis
        timestamp_str = memory.get("timestamp", "")
        if isinstance(timestamp_str, str) and timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                hour = timestamp.hour
                day = timestamp.strftime("%A")
                hourly_distribution[hour] += 1
                daily_distribution[day] += 1
            except (ValueError, AttributeError):
                logger.debug(f"Could not parse timestamp: {timestamp_str}")

    # Generate insights
    total_memories = len(memories)
    top_tags = tag_counter.most_common(10)

    # Calculate tag usage patterns
    tag_frequencies = dict(tag_counter)
    unique_tags = len(tag_frequencies)
    # Calculate average tags per memory with type safety
    total_tags = 0
    for m in memories:
        tags = m.get("tags", [])
        if isinstance(tags, list):
            total_tags += len(tags)
    avg_tags_per_memory = total_tags / total_memories if total_memories > 0 else 0

    # Find peak usage times
    peak_hour = (
        max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else None
    )
    peak_day = (
        max(daily_distribution.items(), key=lambda x: x[1])[0] if daily_distribution else None
    )

    # Content analysis
    content_breakdown = dict(content_types)

    # Build content type breakdown
    # Add any missing types to 'other' for backward compatibility
    structured_count = content_breakdown.get("structured", 0)
    numeric_count = content_breakdown.get("numeric", 0)
    other_count = content_breakdown.get("other", 0) + structured_count + numeric_count

    content_type_breakdown = ContentTypeBreakdown(
        text=content_breakdown.get("text", 0),
        error=content_breakdown.get("error", 0),
        success=content_breakdown.get("success", 0),
        command=content_breakdown.get("command", 0),
        url=content_breakdown.get("url", 0),
        long_text=content_breakdown.get("long_text", 0),
        code=content_breakdown.get("code", 0),
        empty=content_breakdown.get("empty", 0),
        other=other_count,
    )

    # Build time distribution
    time_distribution = TimeDistribution(
        hourly=dict(hourly_distribution),
        daily=dict(daily_distribution),
        peak_hour=peak_hour,
        peak_day=peak_day,
    )

    # Build pattern analysis
    patterns = PatternAnalysis(
        content_types=content_type_breakdown, time_distribution=time_distribution
    )

    # Build learning insights
    insights = _generate_insights_models(
        total_memories,
        unique_tags,
        top_tags,
        content_breakdown,
        peak_hour if peak_hour is not None else 0,
        peak_day if peak_day is not None else "",
    )

    # Build structured summary with Pydantic model
    consolidation = LearningConsolidation(
        summary=f"Analyzed {total_memories} memories with {unique_tags} unique tags",
        total_memories=total_memories,
        unique_tags=unique_tags,
        avg_tags_per_memory=round(avg_tags_per_memory, 2),
        tag_frequencies=tag_frequencies,
        top_tags=[{"tag": tag, "count": count} for tag, count in top_tags],
        patterns=patterns,
        insights=insights,
        generated_at=datetime.now(),
    )

    logger.info(f"Learning consolidation completed: {total_memories} memories analyzed")
    # Return as dict for backward compatibility with flat structure
    result = consolidation.to_dict()

    # Flatten patterns for backward compatibility
    if "patterns" in result and isinstance(result["patterns"], dict):
        patterns_dict = result["patterns"]
        patterns_result = patterns_dict.copy()  # Work with a copy

        if "time_distribution" in patterns_result and isinstance(
            patterns_result["time_distribution"], dict
        ):
            # Hoist time distribution fields to patterns level
            time_dist = patterns_result["time_distribution"]

            # Fix hourly distribution keys - convert string keys back to integers
            hourly_dist_raw = time_dist.get("hourly", {})
            processed_hourly_dist = {}
            if isinstance(hourly_dist_raw, dict) and hourly_dist_raw:
                for k, v in hourly_dist_raw.items():
                    if isinstance(v, int):
                        try:
                            processed_hourly_dist[int(str(k))] = v
                        except (ValueError, TypeError):
                            pass

            patterns_result["hourly_distribution"] = cast(JSONValue, processed_hourly_dist)
            patterns_result["daily_distribution"] = time_dist.get("daily", {})
            patterns_result["peak_hour"] = time_dist.get("peak_hour")
            patterns_result["peak_day"] = time_dist.get("peak_day")
            del patterns_result["time_distribution"]
            result["patterns"] = patterns_result

        if "content_types" in patterns_result and isinstance(
            patterns_result["content_types"], dict
        ):
            # Flatten content types and restore any missing legacy types
            content_dict = patterns_result["content_types"]
            flat_content = {}
            if isinstance(content_dict, dict):
                for k, v in content_dict.items():
                    if k != "total" and k != "get_dominant_type":  # Skip methods
                        flat_content[k] = v

                # Add back legacy types for backward compatibility
                if "structured" not in flat_content:
                    flat_content["structured"] = content_breakdown.get("structured", 0)
                if "numeric" not in flat_content:
                    flat_content["numeric"] = content_breakdown.get("numeric", 0)

                patterns_result["content_types"] = flat_content
                result["patterns"] = patterns_result

    # Convert insights from list of objects to list of strings for backward compat
    if "insights" in result and isinstance(result["insights"], list):
        insights_list = result["insights"]
        if insights_list and isinstance(insights_list[0], dict):
            result["insights"] = [
                i.get("description", "") for i in insights_list if isinstance(i, dict)
            ]

    return result


def _categorize_content(content: Any) -> str:
    """
    Categorize content type for analysis.

    Args:
        content: Memory content of any type

    Returns:
        Content category string
    """
    if content is None or content == "":
        return "empty"

    if isinstance(content, str):
        content_lower = content.lower().strip()

        # Check for common patterns
        if content_lower.startswith(("error", "exception", "failed")):
            return "error"
        elif content_lower.startswith(("success", "completed", "finished")):
            return "success"
        elif any(cmd in content_lower for cmd in ["git", "npm", "pip", "docker"]):
            return "command"
        elif content_lower.startswith(("http", "https", "www")):
            return "url"
        elif len(content) > 200:
            return "long_text"
        else:
            return "text"

    elif isinstance(content, (dict, list)):
        return "structured"
    elif isinstance(content, (int, float)):
        return "numeric"
    else:
        return "other"


def _generate_insights_models(
    total_memories: int,
    unique_tags: int,
    top_tags: list[tuple],
    content_breakdown: dict[str, int],
    peak_hour: int,
    peak_day: str,
) -> list[LearningInsight]:
    """
    Generate human-readable insights from analysis.

    Returns:
        List of insight strings
    """
    insights = []

    # Memory volume insights
    if total_memories > 100:
        insights.append(
            LearningInsight(
                category="volume",
                description=f"High memory activity with {total_memories} records",
                importance="high",
                confidence=0.9,
            )
        )
    elif total_memories > 50:
        insights.append(
            LearningInsight(
                category="volume",
                description=f"Moderate memory activity with {total_memories} records",
                importance="medium",
                confidence=0.9,
            )
        )
    else:
        insights.append(
            LearningInsight(
                category="volume",
                description=f"Light memory activity with {total_memories} records",
                importance="low",
                confidence=0.9,
            )
        )

    # Tag usage insights
    if unique_tags > total_memories * 0.8:
        insights.append(
            LearningInsight(
                category="diversity",
                description="High tag diversity - most memories have unique tags",
                importance="medium",
                confidence=0.85,
            )
        )
    elif unique_tags < total_memories * 0.3:
        insights.append(
            LearningInsight(
                category="diversity",
                description="Low tag diversity - tags are reused frequently",
                importance="medium",
                confidence=0.85,
            )
        )

    # Popular tags
    if top_tags:
        most_used_tag, count = top_tags[0]
        percentage = (count / total_memories) * 100
        insights.append(
            LearningInsight(
                category="tags",
                description=f"Most used tag: '{most_used_tag}' ({percentage:.1f}% of memories)",
                importance="medium",
                confidence=0.95,
                supporting_data={"tag": most_used_tag, "count": count, "percentage": percentage},
            )
        )

    # Content type insights
    if content_breakdown:
        dominant_type = max(content_breakdown.keys(), key=lambda k: content_breakdown[k])
        insights.append(
            LearningInsight(
                category="content",
                description=f"Dominant content type: {dominant_type}",
                importance="low",
                confidence=0.9,
            )
        )

    # Time pattern insights
    if peak_hour is not None:
        time_label = (
            "morning"
            if 6 <= peak_hour < 12
            else "afternoon"
            if 12 <= peak_hour < 18
            else "evening"
            if 18 <= peak_hour < 22
            else "night"
        )
        insights.append(
            LearningInsight(
                category="temporal",
                description=f"Peak usage time: {time_label} (hour {peak_hour})",
                importance="low",
                confidence=0.8,
            )
        )

    if peak_day:
        insights.append(
            LearningInsight(
                category="temporal",
                description=f"Most active day: {peak_day}",
                importance="low",
                confidence=0.8,
            )
        )

    return insights


def generate_learning_report(memories: list[dict[str, JSONValue]], session_id: str = None) -> str:
    """
    Generate a formatted learning report from consolidated analysis.

    Args:
        memories: List of memory records
        session_id: Optional session identifier

    Returns:
        Formatted markdown report string
    """
    analysis = consolidate_learnings(memories)

    report = "# Learning Consolidation Report\n\n"

    if session_id:
        report += f"**Session:** {session_id}\n"

    report += f"**Generated:** {analysis['generated_at']}\n"
    # Plain summary line for simple string checks in tests
    report += f"Total Memories: {analysis['total_memories']}\n"
    report += f"**Summary:** {analysis['summary']}\n\n"

    # Statistics
    report += "## Statistics\n\n"
    report += f"- **Total Memories:** {analysis['total_memories']}\n"
    report += f"- **Unique Tags:** {analysis['unique_tags']}\n"
    report += f"- **Average Tags per Memory:** {analysis['avg_tags_per_memory']}\n\n"

    # Top tags
    top_tags = analysis.get("top_tags", [])
    if isinstance(top_tags, list) and top_tags:
        report += "## Most Used Tags\n\n"
        for tag_info in top_tags[:5]:
            if isinstance(tag_info, dict):
                tag_name = tag_info.get("tag", "unknown")
                tag_count = tag_info.get("count", 0)
                report += f"- **{tag_name}:** {tag_count} times\n"
        report += "\n"

    # Insights
    insights = analysis.get("insights", [])
    if isinstance(insights, list) and insights:
        report += "## Key Insights\n\n"
        for insight in insights:
            if isinstance(insight, str):
                report += f"- {insight}\n"
        report += "\n"

    # Content analysis
    patterns = analysis.get("patterns", {})
    content_types: dict[str, int] = {}
    if isinstance(patterns, dict):
        patterns_content_types = patterns.get("content_types", {})
        if isinstance(patterns_content_types, dict):
            # Ensure all values are integers
            for k, v in patterns_content_types.items():
                if isinstance(v, int):
                    content_types[str(k)] = v

    if isinstance(content_types, dict) and content_types:
        report += "## Content Analysis\n\n"
        for content_type, count in sorted(
            content_types.items(), key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True
        ):
            if isinstance(count, int):
                report += f"- **{str(content_type).replace('_', ' ').title()}:** {count}\n"

    return report


# ============================================================================
# CMP (Clade Metaproductivity) Types
# ============================================================================
# Tracks autonomous PR experiments and clade performance scores for
# evolutionary agent selection via epsilon-greedy bandit.
# See docs/cmp_schema.md for specification.


@dataclass
class CmpEvent:
    """
    Records a single autonomous PR experiment.

    A clade is a specific configuration of agent+model+prompt+strategy.
    Each PR created by an autonomous agent generates one CmpEvent.

    Format: clade_id = "<agent_id>::<model_name>::<prompt_profile>::<strategy>"
    Example: "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"
    """

    id: str  # Unique event ID (UUID or timestamp-based)
    pr_id: int  # GitHub PR number
    branch_name: str  # Git branch (format: autogen/{agent}-{model}-{prompt}-{strategy}-{short_id})
    agent_id: str  # Agent that created the PR (e.g., "self_healer_v1", "backlog_v1")
    clade_id: str  # Full clade identifier (format: agent::model::prompt::strategy)
    task_type: str  # Type of task (e.g., "self_heal", "backlog", "refactor")
    created_at: int  # PR creation timestamp (Unix epoch seconds)
    closed_at: int  # PR close/merge timestamp (Unix epoch seconds)
    reinforcement_signal: str  # Outcome: "approved" (merged) or "rejected" (closed without merge)
    reverted: bool  # Was this PR later reverted due to smoke test failure?
    size_loc_delta: int  # Lines of code changed (additions + deletions)
    files_touched: list[str]  # List of file paths modified
    test_status: str  # Test outcome: "pass", "fail", "skip", "timeout"
    test_suites: list[str] = field(default_factory=list)  # Test suites run (e.g., ["unit", "integration"])
    human_review_time_sec: int | None = None  # Time from creation to human approval (seconds)
    extra_metadata: dict[str, Any] = field(default_factory=dict)  # Flexible field for additional context

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "pr_id": self.pr_id,
            "branch_name": self.branch_name,
            "agent_id": self.agent_id,
            "clade_id": self.clade_id,
            "task_type": self.task_type,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "reinforcement_signal": self.reinforcement_signal,
            "reverted": self.reverted,
            "size_loc_delta": self.size_loc_delta,
            "files_touched": self.files_touched,
            "test_status": self.test_status,
            "test_suites": self.test_suites,
            "human_review_time_sec": self.human_review_time_sec,
            "extra_metadata": self.extra_metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CmpEvent":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            id=data["id"],
            pr_id=data["pr_id"],
            branch_name=data["branch_name"],
            agent_id=data["agent_id"],
            clade_id=data["clade_id"],
            task_type=data["task_type"],
            created_at=data["created_at"],
            closed_at=data["closed_at"],
            reinforcement_signal=data["reinforcement_signal"],
            reverted=data["reverted"],
            size_loc_delta=data["size_loc_delta"],
            files_touched=data["files_touched"],
            test_status=data["test_status"],
            test_suites=data.get("test_suites", []),
            human_review_time_sec=data.get("human_review_time_sec"),
            extra_metadata=data.get("extra_metadata", {}),
        )


@dataclass
class CmpScore:
    """
    Aggregates performance metrics for a single clade.

    Score formula: approval_rate - 2*revert_rate - 0.5*(avg_loc_delta_rejected/500)

    Rationale:
    - High approval_rate: Clade's PRs get merged frequently (good)
    - Low revert_rate: Merged PRs rarely break things (very good)
    - Low avg_loc_delta_rejected: Rejections are small, targeted fixes (acceptable)

    Score range: Approximately -2.0 to 1.0
    - > 0.8: Excellent (most PRs approved, few reverts, small rejection deltas)
    - 0.5 to 0.8: Good
    - 0.0 to 0.5: Acceptable
    - < 0.0: Poor (high rejection or revert rate)
    """

    clade_id: str  # Clade identifier
    total_events: int  # Total number of CmpEvents for this clade
    approvals: int  # Number of merged PRs (reinforcement_signal == "approved")
    rejections: int  # Number of rejected PRs (reinforcement_signal == "rejected")
    reverts: int  # Number of merged PRs later reverted (reverted == True)
    approval_rate: float  # approvals / total_events (0.0 to 1.0)
    revert_rate: float  # reverts / approvals (0.0 to 1.0, or 0.0 if no approvals)
    avg_loc_delta_rejected: float  # Average LOC changed for rejected PRs
    score: float  # Composite score (see formula above)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "clade_id": self.clade_id,
            "total_events": self.total_events,
            "approvals": self.approvals,
            "rejections": self.rejections,
            "reverts": self.reverts,
            "approval_rate": self.approval_rate,
            "revert_rate": self.revert_rate,
            "avg_loc_delta_rejected": self.avg_loc_delta_rejected,
            "score": self.score,
        }


def compute_clade_score(events: list[CmpEvent], clade_id: str) -> CmpScore:
    """
    Compute performance score for a single clade from its events.

    Args:
        events: List of all CmpEvents for this clade
        clade_id: Clade identifier to compute score for

    Returns:
        CmpScore with aggregated metrics
    """
    # Filter events for this clade
    clade_events = [e for e in events if e.clade_id == clade_id]

    if not clade_events:
        # No events for this clade
        return CmpScore(
            clade_id=clade_id,
            total_events=0,
            approvals=0,
            rejections=0,
            reverts=0,
            approval_rate=0.0,
            revert_rate=0.0,
            avg_loc_delta_rejected=0.0,
            score=0.0,
        )

    # Count outcomes
    total_events = len(clade_events)
    approvals = sum(1 for e in clade_events if e.reinforcement_signal == "approved")
    rejections = sum(1 for e in clade_events if e.reinforcement_signal == "rejected")
    reverts = sum(1 for e in clade_events if e.reverted)

    # Calculate rates
    approval_rate = approvals / total_events if total_events > 0 else 0.0
    revert_rate = reverts / approvals if approvals > 0 else 0.0

    # Calculate average LOC delta for rejected PRs
    rejected_events = [e for e in clade_events if e.reinforcement_signal == "rejected"]
    if rejected_events:
        avg_loc_delta_rejected = sum(e.size_loc_delta for e in rejected_events) / len(rejected_events)
    else:
        avg_loc_delta_rejected = 0.0

    # Compute composite score
    # Formula: approval_rate - 2*revert_rate - 0.5*(avg_loc_delta_rejected/500)
    score = approval_rate - 2 * revert_rate - 0.5 * (avg_loc_delta_rejected / 500)

    return CmpScore(
        clade_id=clade_id,
        total_events=total_events,
        approvals=approvals,
        rejections=rejections,
        reverts=reverts,
        approval_rate=approval_rate,
        revert_rate=revert_rate,
        avg_loc_delta_rejected=avg_loc_delta_rejected,
        score=score,
    )


class CmpStore:
    """
    Persistent storage for CmpEvents in JSONL format.

    Events are stored in data/cmp_events.jsonl (newline-delimited JSON).
    Operations are append-only for safety and auditability.

    Example usage:
        store = CmpStore()
        store.record_event(event)
        events = store.load_events()
    """

    def __init__(self, data_dir: Path | str = Path("data")):
        """
        Initialize CmpStore.

        Args:
            data_dir: Directory to store cmp_events.jsonl (default: "data")
        """
        self.data_dir = Path(data_dir)
        self.events_file = self.data_dir / "cmp_events.jsonl"

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def record_event(self, event: CmpEvent) -> None:
        """
        Record a CmpEvent to persistent storage (append-only).

        Args:
            event: CmpEvent to record
        """
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

        logger.info(f"Recorded CmpEvent: {event.id} (clade: {event.clade_id}, signal: {event.reinforcement_signal})")

    def load_events(self, task_type: str | None = None) -> list[CmpEvent]:
        """
        Load all CmpEvents from persistent storage.

        Args:
            task_type: Optional filter by task type (e.g., "self_heal", "backlog")

        Returns:
            List of CmpEvents
        """
        if not self.events_file.exists():
            logger.info(f"No CmpEvents file found at {self.events_file}")
            return []

        events = []
        with open(self.events_file, "r") as f:
            for line in f:
                try:
                    event_dict = json.loads(line)
                    event = CmpEvent.from_dict(event_dict)

                    # Filter by task type if specified
                    if task_type is None or event.task_type == task_type:
                        events.append(event)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Failed to parse CmpEvent from line: {line[:100]}... ({e})")
                    continue

        logger.info(f"Loaded {len(events)} CmpEvents" + (f" (task_type={task_type})" if task_type else ""))
        return events

    def get_all_clade_ids(self, task_type: str | None = None) -> list[str]:
        """
        Get list of all unique clade IDs.

        Args:
            task_type: Optional filter by task type

        Returns:
            List of unique clade IDs
        """
        events = self.load_events(task_type=task_type)
        return list(set(e.clade_id for e in events))


class CladeSelector:
    """
    Epsilon-greedy bandit algorithm for selecting which clade to use.

    - With probability ε (default 0.1): explore (choose random clade)
    - With probability 1-ε (default 0.9): exploit (choose highest-scoring clade)

    Example usage:
        selector = CladeSelector(store)
        clade_id = selector.select_clade(
            task_type="self_heal",
            available_clades=[
                "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal",
                "self_healer_v1::gpt-5::prompt_full_context::strategy_careful"
            ],
            epsilon=0.1
        )
    """

    def __init__(self, store: CmpStore):
        """
        Initialize CladeSelector.

        Args:
            store: CmpStore instance for loading events
        """
        self.store = store

    def select_clade(
        self,
        task_type: str,
        available_clades: list[str],
        epsilon: float = 0.1
    ) -> str:
        """
        Select a clade using epsilon-greedy bandit algorithm.

        Args:
            task_type: Task type to filter events (e.g., "self_heal", "backlog")
            available_clades: List of clade IDs to choose from
            epsilon: Exploration probability (default 0.1 = 10% explore, 90% exploit)

        Returns:
            Selected clade ID
        """
        if not available_clades:
            raise ValueError("available_clades must not be empty")

        # Epsilon-greedy decision
        if random.random() < epsilon:
            # Explore: random selection
            selected = random.choice(available_clades)
            logger.info(f"CMP: Explore - randomly selected clade: {selected}")
            return selected
        else:
            # Exploit: choose best clade by score
            events = self.store.load_events(task_type=task_type)

            # Compute scores for all available clades
            scores: dict[str, float] = {}
            for clade_id in available_clades:
                clade_score = compute_clade_score(events, clade_id)
                scores[clade_id] = clade_score.score

            # Select clade with highest score
            if not scores:
                # No events yet, fallback to random
                selected = random.choice(available_clades)
                logger.info(f"CMP: No events yet, randomly selected clade: {selected}")
                return selected

            selected = max(scores, key=scores.get)  # type: ignore
            logger.info(f"CMP: Exploit - selected highest-scoring clade: {selected} (score: {scores[selected]:.3f})")
            return selected
