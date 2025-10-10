"""
Skill Dashboard Visualization (M4.3)

Displays agent skill vectors in a readable format with visual progress bars.

Usage:
    python tools/skill_dashboard.py [--agent AGENT_NAME] [--format text|json]

Features:
    - ASCII progress bars for skill metrics
    - Color-coded skill levels (Red <50%, Yellow 50-75%, Green >75%)
    - Historical trend tracking (if available in VectorStore)
    - Comparison across multiple agents
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.agent_context import create_agent_context
from shared.skill_vector import SkillVector

# ============================================================================
# ASCII Progress Bar
# ============================================================================


def progress_bar(value: float, width: int = 40, show_percentage: bool = True) -> str:
    """
    Generate ASCII progress bar.

    Args:
        value: Float between 0.0 and 1.0
        width: Width of progress bar in characters
        show_percentage: Whether to show percentage text

    Returns:
        ASCII progress bar string
    """
    # Clamp value
    value = max(0.0, min(1.0, value))

    # Calculate filled width
    filled_width = int(value * width)
    empty_width = width - filled_width

    # Color codes (if terminal supports)
    if value < 0.5:
        color = "\033[91m"  # Red
    elif value < 0.75:
        color = "\033[93m"  # Yellow
    else:
        color = "\033[92m"  # Green

    reset = "\033[0m"

    # Build bar
    bar = f"{color}{'█' * filled_width}{'░' * empty_width}{reset}"

    if show_percentage:
        percentage = f"{value * 100:5.1f}%"
        return f"{bar} {percentage}"
    else:
        return bar


# ============================================================================
# Skill Dashboard Display
# ============================================================================


def format_skill_category(
    category_name: str,
    skills: Dict[str, float],
    indent: int = 2
) -> str:
    """Format a skill category with progress bars."""
    lines = []
    indent_str = " " * indent

    # Category header
    avg_score = sum(skills.values()) / len(skills) if skills else 0.0
    lines.append(f"\n{indent_str}📊 {category_name.replace('_', ' ').title()}")
    lines.append(f"{indent_str}{'─' * 60}")
    lines.append(f"{indent_str}Average: {progress_bar(avg_score)}")
    lines.append("")

    # Individual skills
    for skill_name, skill_value in sorted(skills.items()):
        display_name = skill_name.replace('_', ' ').title()
        bar = progress_bar(skill_value)
        lines.append(f"{indent_str}  {display_name:30s} {bar}")

    return "\n".join(lines)


def display_agent_dashboard(
    agent_name: str,
    skill_vector: SkillVector,
    context: Any
) -> str:
    """
    Display comprehensive skill dashboard for an agent.

    Args:
        agent_name: Agent identifier
        skill_vector: SkillVector instance
        context: AgentContext for VectorStore queries

    Returns:
        Formatted dashboard string
    """
    skills_dict = skill_vector.to_dict()

    # Header
    dashboard = f"""
{'='*70}
🚀 AGENT SKILL DASHBOARD: {agent_name.upper()}
{'='*70}

Agent: {agent_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Updates: {skills_dict['update_count']} skill updates recorded
Last Updated: {skills_dict['last_updated']}

Overall Skill Level: {progress_bar(skills_dict['overall_skill_level'])}

"""

    # Aggregate Categories
    dashboard += "  📊 Skill Categories (Aggregates)\n"
    dashboard += f"  {'─' * 60}\n\n"

    categories = [
        ("Technical Skills", skills_dict['technical_skill']),
        ("Strategic Skills", skills_dict['strategic_skill']),
        ("Collaboration Skills", skills_dict['collaboration_skill']),
        ("Quality Skills", skills_dict['quality_skill']),
    ]

    for cat_name, cat_value in categories:
        dashboard += f"  {cat_name:25s} {progress_bar(cat_value)}\n"

    # Top 10 Skills
    dashboard += "\n  🏆 Top 10 Skills (Individual Dimensions)\n"
    dashboard += f"  {'─' * 60}\n\n"

    top_skills = skill_vector.get_top_skills(n=10)
    for skill_name, skill_value in top_skills:
        display_name = skill_name.replace('_', ' ').title()
        dashboard += f"  {display_name:30s} {progress_bar(skill_value)}\n"

    # Weakest 5 Skills (improvement areas)
    dashboard += "\n  ⚠️  Areas for Improvement (Weakest 5 Skills)\n"
    dashboard += f"  {'─' * 60}\n\n"

    weak_skills = skill_vector.get_weakest_skills(n=5)
    for skill_name, skill_value in weak_skills:
        display_name = skill_name.replace('_', ' ').title()
        dashboard += f"  {display_name:30s} {progress_bar(skill_value)}\n"

    # Query VectorStore for historical trend
    historical_skills = context.search_memories(
        tags=["skill_vector", agent_name],
        include_session=True
    )

    if len(historical_skills) > 1:
        # Calculate trend (current vs first)
        first_skills = historical_skills[-1]  # Oldest
        current_avg = skills_dict['overall_skill_level']
        first_avg = first_skills.get("overall_skill_level", 0.5)

        trend = current_avg - first_avg
        trend_symbol = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"

        dashboard += f"\n  {trend_symbol} Skill Trend (vs first measurement)\n"
        dashboard += f"  {'─' * 60}\n"
        dashboard += f"  Change: {trend:+.1%} ({first_avg:.1%} → {current_avg:.1%})\n"
        dashboard += f"  Historical Data Points: {len(historical_skills)}\n"

    # Footer
    dashboard += f"\n{'='*70}\n"
    dashboard += "✅ Dashboard generated successfully\n"
    dashboard += f"{'='*70}\n"

    return dashboard


# ============================================================================
# Multi-Agent Comparison
# ============================================================================


def compare_agents(agent_names: List[str], context: Any) -> str:
    """
    Compare skill levels across multiple agents.

    Args:
        agent_names: List of agent identifiers
        context: AgentContext for queries

    Returns:
        Formatted comparison table
    """
    comparison = f"""
{'='*70}
🔀 MULTI-AGENT SKILL COMPARISON
{'='*70}

Agents: {', '.join(agent_names)}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

    # Collect skills for each agent
    agent_skills = {}
    for agent_name in agent_names:
        skill_vector = SkillVector(
            agent_name=agent_name,
            session_id=f"compare_{datetime.now().timestamp()}"
        )
        skills_dict = skill_vector.to_dict()
        agent_skills[agent_name] = skills_dict

    # Compare key metrics
    comparison += "📊 Skill Category Comparison:\n"
    comparison += f"{'─' * 70}\n\n"

    metrics = [
        ("Overall Skill Level", lambda s: s.get("overall_skill_level", 0.5)),
        ("Technical Skills", lambda s: s.get("technical_skill", 0.5)),
        ("Strategic Skills", lambda s: s.get("strategic_skill", 0.5)),
        ("Collaboration Skills", lambda s: s.get("collaboration_skill", 0.5)),
        ("Quality Skills", lambda s: s.get("quality_skill", 0.5)),
    ]

    for metric_name, metric_getter in metrics:
        comparison += f"\n{metric_name}:\n"

        for agent_name in agent_names:
            try:
                value = metric_getter(agent_skills[agent_name])
                comparison += f"  {agent_name:20s} {progress_bar(value)}\n"
            except (KeyError, TypeError):
                comparison += f"  {agent_name:20s} N/A\n"

    # Update counts
    comparison += f"\n{'─' * 70}\n"
    comparison += "Update Counts (skill evolution activity):\n\n"

    for agent_name in agent_names:
        skills = agent_skills[agent_name]
        update_count = skills.get("update_count", 0)
        comparison += f"  {agent_name:20s} {update_count} updates\n"

    comparison += f"\n{'='*70}\n"

    return comparison


# ============================================================================
# JSON Export
# ============================================================================


def export_json(agent_name: str, skill_vector: SkillVector) -> str:
    """Export skill data as JSON."""
    skills_dict = skill_vector.to_dict()

    # Add metadata
    output = {
        "agent_name": agent_name,
        "generated_at": datetime.now().isoformat(),
        "skills": skills_dict,
    }

    return json.dumps(output, indent=2)


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Display agent skill dashboard (M4.3)"
    )
    parser.add_argument(
        "--agent",
        type=str,
        default="coder",
        help="Agent name to display (default: coder)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--compare",
        type=str,
        nargs="+",
        help="Compare multiple agents (e.g., --compare coder planner auditor)"
    )
    parser.add_argument(
        "--save",
        type=Path,
        help="Save output to file"
    )

    args = parser.parse_args()

    # Initialize context
    context = create_agent_context(
        session_id=f"skill_dashboard_{datetime.now().timestamp()}"
    )

    # Generate output
    if args.compare:
        # Multi-agent comparison
        output = compare_agents(args.compare, context)
    else:
        # Single agent dashboard
        skill_vector = SkillVector(
            agent_name=args.agent,
            session_id=f"dashboard_{datetime.now().timestamp()}"
        )

        if args.format == "json":
            output = export_json(args.agent, skill_vector)
        else:
            output = display_agent_dashboard(args.agent, skill_vector, context)

    # Display or save
    if args.save:
        with open(args.save, 'w') as f:
            f.write(output)
        print(f"✅ Dashboard saved to: {args.save}")
    else:
        print(output)


if __name__ == "__main__":
    main()
