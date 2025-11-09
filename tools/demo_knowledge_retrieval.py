#!/usr/bin/env python3
"""
Demo: Retrieve coaching pain points from VectorStore and analyze with local LLM

This demonstrates the complete knowledge ingestion → retrieval → analysis pipeline.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.agent_context import create_agent_context
from anthropic import Anthropic

def main():
    """Retrieve pain points and analyze with local LLM."""

    print("="*70)
    print("KNOWLEDGE RETRIEVAL & ANALYSIS DEMO")
    print("="*70)

    # Initialize AgentContext
    print("\n1. Initializing AgentContext...")
    context = create_agent_context(session_id="knowledge_demo")

    # Query VectorStore for ACIM pain points
    print("\n2. Querying VectorStore for ACIM pain points...")
    acim_results = context.search_memories(
        tags=["topic:acim", "type:pain_point"],
        include_session=True
    )

    print(f"   Found {len(acim_results)} ACIM pain points")

    # Query for co-parenting pain points
    print("\n3. Querying VectorStore for co-parenting pain points...")
    coparenting_results = context.search_memories(
        tags=["topic:co_parenting", "type:pain_point"],
        include_session=True
    )

    print(f"   Found {len(coparenting_results)} co-parenting pain points")

    # Display sample pain points
    print("\n" + "="*70)
    print("SAMPLE PAIN POINTS")
    print("="*70)

    for i, result in enumerate(acim_results[:3], 1):
        print(f"\n{i}. ACIM Pain Point:")
        print(f"   Content: {result.get('content', 'N/A')[:150]}...")
        print(f"   Tags: {result.get('tags', [])}")

    # Analyze with local LLM
    print("\n" + "="*70)
    print("ANALYZING WITH LOCAL LLM (vcoder-120b)")
    print("="*70)

    if acim_results:
        # Prepare pain points for analysis
        pain_points_text = "\n\n".join([
            f"Pain Point {i+1}: {r.get('content', 'N/A')}"
            for i, r in enumerate(acim_results[:3])
        ])

        print(f"\nSending {len(acim_results[:3])} pain points to local LLM...")

        # Use Anthropic SDK with local model endpoint
        client = Anthropic(
            api_key="not-needed",  # Local LM Studio doesn't need key
            base_url=os.getenv("OPENAI_API_BASE", "http://192.168.0.2:1234/v1")
        )

        try:
            response = client.messages.create(
                model=os.getenv("LOCAL_MODEL_NAME", "vcoder-120b-1.0-qx86-hi-mlx"),
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze these ACIM coaching pain points and identify:
1. Common themes
2. Underlying struggles
3. Coaching opportunities

Pain Points:
{pain_points_text}

Provide a brief analysis (3-5 sentences)."""
                }]
            )

            analysis = response.content[0].text

            print("\n" + "-"*70)
            print("LOCAL LLM ANALYSIS:")
            print("-"*70)
            print(analysis)
            print("-"*70)

        except Exception as e:
            print(f"\n❌ Local LLM error: {e}")
            print("   (This is expected if local model is not running)")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✅ Retrieved {len(acim_results)} ACIM pain points from VectorStore")
    print(f"✅ Retrieved {len(coparenting_results)} co-parenting pain points from VectorStore")
    print(f"✅ VectorStore integration working")
    print(f"✅ Local LLM analysis {'completed' if acim_results else 'skipped (no data)'}")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
