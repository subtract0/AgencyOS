"""
Simple learning consolidation module.
Provides deterministic summarization of memory tag frequencies and patterns.
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def consolidate_learnings(memories: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        return {
            "summary": "No memories to analyze",
            "total_memories": 0,
            "tag_frequencies": {},
            "patterns": {},
            "generated_at": datetime.now().isoformat(),
        }

    # Initialize counters and analyzers
    tag_counter = Counter()
    content_types = Counter()
    hourly_distribution = defaultdict(int)
    daily_distribution = defaultdict(int)

    # Process each memory
    for memory in memories:
        # Count tags
        tags = memory.get("tags", [])
        tag_counter.update(tags)

        # Analyze content types
        content = memory.get("content", "")
        content_type = _categorize_content(content)
        content_types[content_type] += 1

        # Time pattern analysis
        timestamp_str = memory.get("timestamp", "")
        if timestamp_str:
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
    avg_tags_per_memory = sum(len(m.get("tags", [])) for m in memories) / total_memories

    # Find peak usage times
    peak_hour = (
        max(hourly_distribution.items(), key=lambda x: x[1])[0]
        if hourly_distribution
        else None
    )
    peak_day = (
        max(daily_distribution.items(), key=lambda x: x[1])[0]
        if daily_distribution
        else None
    )

    # Content analysis
    content_breakdown = dict(content_types)

    # Build structured summary
    summary = {
        "summary": f"Analyzed {total_memories} memories with {unique_tags} unique tags",
        "total_memories": total_memories,
        "unique_tags": unique_tags,
        "avg_tags_per_memory": round(avg_tags_per_memory, 2),
        "tag_frequencies": tag_frequencies,
        "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
        "patterns": {
            "content_types": content_breakdown,
            "peak_hour": peak_hour,
            "peak_day": peak_day,
            "hourly_distribution": dict(hourly_distribution),
            "daily_distribution": dict(daily_distribution),
        },
        "insights": _generate_insights(
            total_memories,
            unique_tags,
            top_tags,
            content_breakdown,
            peak_hour,
            peak_day,
        ),
        "generated_at": datetime.now().isoformat(),
    }

    logger.info(f"Learning consolidation completed: {total_memories} memories analyzed")
    return summary


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


def _generate_insights(
    total_memories: int,
    unique_tags: int,
    top_tags: List[tuple],
    content_breakdown: Dict[str, int],
    peak_hour: int,
    peak_day: str,
) -> List[str]:
    """
    Generate human-readable insights from analysis.

    Returns:
        List of insight strings
    """
    insights = []

    # Memory volume insights
    if total_memories > 100:
        insights.append(f"High memory activity with {total_memories} records")
    elif total_memories > 50:
        insights.append(f"Moderate memory activity with {total_memories} records")
    else:
        insights.append(f"Light memory activity with {total_memories} records")

    # Tag usage insights
    if unique_tags > total_memories * 0.8:
        insights.append("High tag diversity - most memories have unique tags")
    elif unique_tags < total_memories * 0.3:
        insights.append("Low tag diversity - tags are reused frequently")

    # Popular tags
    if top_tags:
        most_used_tag, count = top_tags[0]
        percentage = (count / total_memories) * 100
        insights.append(
            f"Most used tag: '{most_used_tag}' ({percentage:.1f}% of memories)"
        )

    # Content type insights
    if content_breakdown:
        dominant_type = max(content_breakdown, key=content_breakdown.get)
        insights.append(f"Dominant content type: {dominant_type}")

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
        insights.append(f"Peak usage time: {time_label} (hour {peak_hour})")

    if peak_day:
        insights.append(f"Most active day: {peak_day}")

    return insights


def generate_learning_report(
    memories: List[Dict[str, Any]], session_id: str = None
) -> str:
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
    if analysis["top_tags"]:
        report += "## Most Used Tags\n\n"
        for tag_info in analysis["top_tags"][:5]:
            report += f"- **{tag_info['tag']}:** {tag_info['count']} times\n"
        report += "\n"

    # Insights
    if analysis["insights"]:
        report += "## Key Insights\n\n"
        for insight in analysis["insights"]:
            report += f"- {insight}\n"
        report += "\n"

    # Content analysis
    content_types = analysis["patterns"].get("content_types", {})
    if content_types:
        report += "## Content Analysis\n\n"
        for content_type, count in sorted(
            content_types.items(), key=lambda x: x[1], reverse=True
        ):
            report += f"- **{content_type.replace('_', ' ').title()}:** {count}\n"

    return report
