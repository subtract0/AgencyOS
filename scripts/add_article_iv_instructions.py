#!/usr/bin/env python3
"""
Add Article IV compliance instructions to all agent instruction files.

This script adds the Article IV compliance section to all agent instruction
files that don't already have it.
"""

import os
from pathlib import Path

# Article IV compliance template (generic version for all agents)
ARTICLE_IV_TEMPLATE = """
# Article IV Compliance (Constitutional Mandate)

**BEFORE any significant operation:**
1. Query VectorStore for relevant patterns using agent context
2. Review similar successful operations from past sessions
3. Apply proven patterns with confidence >= 0.6

**AFTER successful operation:**
1. Store the solution pattern in VectorStore via agent context
2. Tag with agent type, operation type, "success"
3. Include confidence score (0.85+ for proven solutions)

**Implementation Pattern:**
```python
# BEFORE: Query learnings
patterns = context.search_memories(
    tags=["{agent_name}", operation_type, "success"],
    include_session=True,
    min_confidence=0.6
)

# Use patterns to guide operation
# ... your implementation here ...

# AFTER: Store successful outcome
context.store_memory(
    key=f"success_{{operation_type}}_{{timestamp}}",
    content={{"solution": result, "success": True}},
    tags=["{agent_name}", operation_type, "success"],
    confidence=0.85
)
```

**This is MANDATORY per Article IV (ADR-004). Skipping VectorStore query/store is a constitutional violation.**
"""


def has_article_iv_section(content: str) -> bool:
    """Check if file already has Article IV compliance section."""
    return "# Article IV Compliance" in content or "Article IV (ADR-004)" in content


def add_article_iv_to_file(file_path: Path, agent_name: str):
    """Add Article IV compliance section to instruction file."""
    with open(file_path, "r") as f:
        content = f.read()

    # Check if already has Article IV section
    if has_article_iv_section(content):
        print(f"✓ {file_path.name} already has Article IV compliance section")
        return False

    # Customize template for agent
    article_iv = ARTICLE_IV_TEMPLATE.format(agent_name=agent_name.lower())

    # Add section before last heading or at end
    # Try to find good insertion point
    insertion_markers = [
        "Keep outputs direct",
        "# Cross-References",
        "# Success Metrics",
    ]

    for marker in insertion_markers:
        if marker in content:
            content = content.replace(marker, f"{article_iv}\n{marker}")
            break
    else:
        # Add at end
        content = content.rstrip() + "\n" + article_iv + "\n"

    # Write updated content
    with open(file_path, "w") as f:
        f.write(content)

    print(f"✓ Added Article IV compliance to {file_path.name}")
    return True


def main():
    """Add Article IV compliance to all agent instruction files."""
    agency_root = Path("/Users/am/Code/Agency")

    # Agent instruction files to update
    agent_files = [
        ("test_generator_agent", "test_generator"),
        ("auditor_agent", "auditor"),
        ("chief_architect_agent", "architect"),
        ("learning_agent", "learning"),
        ("merger_agent", "merger"),
        ("work_completion_summary_agent", "summary"),
    ]

    updated_count = 0

    for agent_dir, agent_name in agent_files:
        instruction_file = agency_root / agent_dir / "instructions-gpt-5.md"

        if not instruction_file.exists():
            print(f"⚠ {instruction_file.name} not found, skipping")
            continue

        if add_article_iv_to_file(instruction_file, agent_name):
            updated_count += 1

    print(f"\n✅ Updated {updated_count} instruction files with Article IV compliance")


if __name__ == "__main__":
    main()
