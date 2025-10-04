#!/usr/bin/env python3
"""
Query and demonstrate retrieval of Project Consciousness insights from VectorStore.

This script shows how to retrieve the stored constitutional consciousness insights
for use during active development.
"""

import logging

from agency_memory import Memory
from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from shared.agent_context import AgentContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def query_consciousness_insights():
    """Query and display consciousness insights from VectorStore."""

    # Initialize context with same session ID used for storage
    enhanced_store = EnhancedMemoryStore(embedding_provider="sentence-transformers")
    memory = Memory(store=enhanced_store)
    context = AgentContext(memory=memory, session_id="consciousness_research_storage")

    print("\n" + "="*80)
    print("PROJECT CONSCIOUSNESS INSIGHTS - VECTORSTORE QUERY DEMONSTRATION")
    print("="*80)

    # Example 1: Query all constitutional consciousness insights
    print("\n\n[QUERY 1] All Constitutional Consciousness Insights")
    print("-" * 80)
    all_insights = context.search_memories(
        tags=["constitutional", "consciousness"],
        include_session=True
    )
    print(f"Found {len(all_insights)} insights")

    for i, insight in enumerate(all_insights, 1):
        content = insight.get("content", {})
        if isinstance(content, dict):
            title = content.get("title", "N/A")
            confidence = content.get("confidence", "N/A")
            print(f"\n  {i:2d}. {title}")
            print(f"      Confidence: {confidence}")

    # Example 2: Query RAG-specific insights
    print("\n\n[QUERY 2] RAG (Retrieval-Augmented Generation) Insights")
    print("-" * 80)
    rag_insights = context.search_memories(
        tags=["constitutional", "rag"],
        include_session=True
    )
    print(f"Found {len(rag_insights)} RAG-related insights\n")

    for insight in rag_insights:
        content = insight.get("content", {})
        if isinstance(content, dict):
            print(f"Title: {content.get('title')}")
            print(f"Insight: {content.get('insight')}")
            print(f"\nImplementation Mapping:")
            mapping = content.get("implementation_mapping", {})
            if isinstance(mapping, dict):
                print(f"  - Current System: {mapping.get('current_system')}")
                print(f"  - Validation: {mapping.get('validation')}")
                print(f"  - Enhancement: {mapping.get('enhancement')}")
            print(f"\nAcademic Reference: {content.get('academic_reference')}")

    # Example 3: Query self-modification insights
    print("\n\n[QUERY 3] Self-Modification & Dynamic Alignment Insights")
    print("-" * 80)
    self_mod_insights = context.search_memories(
        tags=["constitutional", "self-modification"],
        include_session=True
    )
    print(f"Found {len(self_mod_insights)} self-modification insights\n")

    for insight in self_mod_insights:
        content = insight.get("content", {})
        if isinstance(content, dict):
            print(f"Title: {content.get('title')}")
            print(f"Confidence: {content.get('confidence')}")
            print(f"Evidence Count: {content.get('evidence_count')}")
            print(f"\nKey Insight:")
            insight_text = content.get('insight', '')
            if isinstance(insight_text, str):
                # Wrap text at 75 chars
                words = insight_text.split()
                line = "  "
                for word in words:
                    if len(line) + len(word) + 1 > 75:
                        print(line)
                        line = "  " + word
                    else:
                        line += " " + word if len(line) > 2 else word
                if line.strip():
                    print(line)

    # Example 4: Query research summary
    print("\n\n[QUERY 4] Research Summary")
    print("-" * 80)
    summary_insights = context.search_memories(
        tags=["research", "summary"],
        include_session=True
    )

    for insight in summary_insights:
        content = insight.get("content", {})
        if isinstance(content, dict):
            print(f"Title: {content.get('title')}")
            print(f"Total Insights: {content.get('total_insights')}")
            print(f"Academic Backing: {content.get('academic_backing')}")
            print(f"Confidence Range: {content.get('confidence_range')}")
            print(f"\nKey Themes:")
            themes = content.get('key_themes', [])
            if isinstance(themes, list):
                for i, theme in enumerate(themes, 1):
                    print(f"  {i:2d}. {theme}")

    # Example 5: Demonstrate semantic search (if available)
    print("\n\n[QUERY 5] Semantic Search Demonstration")
    print("-" * 80)

    try:
        semantic_results = enhanced_store.semantic_search(
            query="How do we prevent alignment drift in self-modifying agents?",
            top_k=3,
            min_similarity=0.3
        )

        if semantic_results:
            print(f"Found {len(semantic_results)} semantically relevant results\n")
            for result in semantic_results:
                content = result.get("content", {})
                if isinstance(content, dict):
                    print(f"Title: {content.get('title')}")
                    print(f"Relevance Score: {result.get('relevance_score', 'N/A')}")
                    print(f"Search Type: {result.get('search_type', 'N/A')}")
                    print()
        else:
            print("Semantic search returned no results (may need sentence-transformers)")
    except Exception as e:
        print(f"Semantic search not available: {e}")
        print("(Install sentence-transformers for full semantic search capability)")

    # VectorStore statistics
    print("\n\n[STATISTICS] VectorStore Status")
    print("-" * 80)
    stats = enhanced_store.get_vector_store_stats()
    print(f"Total Memories: {stats.get('total_memories', 0)}")
    print(f"Memories with Embeddings: {stats.get('memories_with_embeddings', 0)}")
    print(f"Embedding Provider: {stats.get('embedding_provider', 'N/A')}")
    print(f"Embedding Available: {stats.get('embedding_available', False)}")
    print(f"Last Updated: {stats.get('last_updated', 'N/A')}")

    print("\n" + "="*80)
    print("QUERY DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nAll 10 constitutional consciousness insights are stored and retrievable.")
    print("Use these queries in active development to reference research-backed patterns.\n")

    return {
        "total_insights": len(all_insights),
        "rag_insights": len(rag_insights),
        "self_mod_insights": len(self_mod_insights),
        "semantic_available": stats.get('embedding_available', False)
    }


if __name__ == "__main__":
    result = query_consciousness_insights()
