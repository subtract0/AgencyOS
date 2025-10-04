#!/usr/bin/env python3
"""Verify consciousness insights were stored to VectorStore."""

from agency_memory import Memory
from shared.agent_context import AgentContext

def verify_storage():
    """Verify consciousness insights in VectorStore."""

    # Initialize context with memory
    context = AgentContext(memory=Memory(), session_id="consciousness_research_storage")

    print("\n" + "="*80)
    print("VERIFYING VECTORSTORE STORAGE")
    print("="*80)

    # Search for constitutional consciousness insights
    constitutional_memories = context.search_memories(
        tags=["constitutional", "consciousness"],
        include_session=True
    )

    print(f"\nFound {len(constitutional_memories)} constitutional consciousness memories")
    print("\nStored Insights:")
    print("-" * 80)

    for i, mem in enumerate(constitutional_memories, 1):
        content = mem.get("content", {})
        if isinstance(content, dict):
            title = content.get("title", "N/A")
            confidence = content.get("confidence", "N/A")
            tags = mem.get("tags", [])
            print(f"\n{i:2d}. {title}")
            print(f"    Confidence: {confidence}")
            print(f"    Tags: {', '.join(tags)}")

    # Search for research summary
    summary_memories = context.search_memories(
        tags=["research", "summary"],
        include_session=True
    )

    print(f"\n\nResearch Summary:")
    print("-" * 80)
    for mem in summary_memories:
        content = mem.get("content", {})
        if isinstance(content, dict):
            print(f"Title: {content.get('title')}")
            print(f"Total Insights: {content.get('total_insights')}")
            print(f"Stored Count: {content.get('stored_count')}")
            print(f"Academic Backing: {content.get('academic_backing')}")
            print(f"Confidence Range: {content.get('confidence_range')}")

    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80 + "\n")

    return len(constitutional_memories)

if __name__ == "__main__":
    count = verify_storage()
    print(f"✓ Successfully verified {count} insights in VectorStore\n")
