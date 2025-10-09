#!/usr/bin/env python3
"""
Generate compact agent summaries for 27x context efficiency.

Converts full agent definitions (1,340 lines) to concise summaries (50 lines)
for faster agent spawning and reduced token costs.

Article II: TDD - tests written in tests/test_agent_summaries.py
ADR-008: Strict typing throughout
"""

import re
from pathlib import Path


def extract_section(content: str, section_header: str, max_lines: int = 5) -> str:
    """
    Extract first N lines from a markdown section.

    Args:
        content: Full markdown content
        section_header: Section to extract (e.g., "## Role")
        max_lines: Maximum lines to extract

    Returns:
        Extracted section content (truncated)
    """
    pattern = rf"{re.escape(section_header)}\s*\n(.*?)(?=\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return ""

    section_text = match.group(1).strip()
    lines = section_text.split("\n")

    # Take first N non-empty lines
    result_lines = []
    for line in lines:
        if line.strip() and not line.startswith("```"):
            result_lines.append(line.strip())
            if len(result_lines) >= max_lines:
                break

    return " ".join(result_lines)[:300]  # Max 300 chars


def extract_list_items(content: str, section_header: str, max_items: int = 5) -> list[str]:
    """Extract bulleted/numbered list items from a section."""
    section = extract_section(content, section_header, max_lines=20)

    # Match list items (- item or 1. item)
    items = re.findall(r"(?:^|\n)(?:-|\d+\.)\s*\*?\*?([^\n]+)", section, re.MULTILINE)

    return [item.strip().rstrip("*").strip() for item in items[:max_items]]


def generate_summary(agent_file: Path) -> str:
    """
    Generate 50-line summary from full agent definition.

    Args:
        agent_file: Path to full agent markdown file

    Returns:
        Compact summary (50 lines max)
    """
    content = agent_file.read_text()
    agent_name = agent_file.stem.replace("_", " ").title()

    # Extract key sections
    role = extract_section(content, "## Role", max_lines=2)

    # Extract core competencies
    competencies = extract_list_items(content, "## Core Competencies", max_items=3)
    competencies_str = (
        "\n".join(f"- {c}" for c in competencies)
        if competencies
        else "- Implementation and code generation"
    )

    # Extract tools
    tools_section = extract_section(content, "## Tool Permissions", max_lines=10)
    allowed_tools_match = re.search(
        r"\*\*Allowed Tools:\*\*(.*?)(?:\*\*|$)", tools_section, re.DOTALL
    )
    if allowed_tools_match:
        tools_text = allowed_tools_match.group(1)
        tools = re.findall(r"(?:^|\n)(?:-|\*)\s*\*?\*?([^\n:]+)", tools_text, re.MULTILINE)
        tools_list = ", ".join(t.strip().rstrip("*").strip() for t in tools[:7])
    else:
        tools_list = "Read, Write, Edit, Bash"

    # Extract communication patterns
    receives_from = extract_list_items(content, "### Receives From:", max_items=3)
    sends_to = extract_list_items(content, "### Sends To:", max_items=3)

    receives_str = ", ".join(receives_from[:3]) if receives_from else "User, ChiefArchitect"
    sends_str = ", ".join(sends_to[:3]) if sends_to else "QualityEnforcer"

    # Generate summary
    summary = f"""# {agent_name} (Summary)

**Role**: {role if role else f"{agent_name} specialist for Agency OS"}

## Core Competencies

{competencies_str}

## Tools

{tools_list}

## Communication

**Receives From**: {receives_str}

**Sends To**: {sends_str}

## Workflow

1. Query VectorStore for patterns (Article IV)
2. Execute core competency tasks
3. Verify constitutional compliance
4. Store learnings for future reuse

## Constitutional Compliance

- Article I: Complete context before action
- Article II: 100% test success rate required
- Article IV: Query learnings before, store after success

## Full Agent

For complete details, see: `.claude/agents/{agent_file.name}`

---

*This is an auto-generated summary for fast agent spawning.*
*Generated: {agent_file.stat().st_mtime}*
"""

    return summary


def generate_all_summaries(agents_dir: Path = Path(".claude/agents")) -> dict[str, Path]:
    """
    Generate summaries for all agent definitions.

    Args:
        agents_dir: Directory containing agent markdown files

    Returns:
        Dict mapping agent names to summary file paths
    """
    if not agents_dir.exists():
        raise FileNotFoundError(f"Agents directory not found: {agents_dir}")

    summaries = {}
    agent_files = list(agents_dir.glob("*.md"))

    # Exclude existing summaries
    agent_files = [f for f in agent_files if not f.stem.endswith(".summary")]

    print(f"Generating summaries for {len(agent_files)} agents...")

    for agent_file in agent_files:
        try:
            summary = generate_summary(agent_file)
            summary_file = agent_file.with_suffix(".summary.md")
            summary_file.write_text(summary)

            summaries[agent_file.stem] = summary_file

            original_lines = len(agent_file.read_text().split("\n"))
            summary_lines = len(summary.split("\n"))
            ratio = original_lines / summary_lines if summary_lines > 0 else 1

            print(
                f"✅ {agent_file.stem}: {original_lines} → {summary_lines} lines ({ratio:.1f}x smaller)"
            )

        except Exception as e:
            print(f"❌ Failed to generate summary for {agent_file.stem}: {e}")

    print(f"\n✅ Generated {len(summaries)} agent summaries")
    return summaries


if __name__ == "__main__":
    import sys

    try:
        summaries = generate_all_summaries()

        # Print statistics
        total_reduction = sum(
            len(Path(f".claude/agents/{name}.md").read_text().split("\n"))
            for name in summaries.keys()
        )
        total_summary = sum(len(path.read_text().split("\n")) for path in summaries.values())

        avg_ratio = total_reduction / total_summary if total_summary > 0 else 1

        print(
            f"\n📊 Total Reduction: {total_reduction} → {total_summary} lines ({avg_ratio:.1f}x average)"
        )
        print(f"💰 Token Savings: ~{avg_ratio:.1f}x cheaper agent spawns")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
