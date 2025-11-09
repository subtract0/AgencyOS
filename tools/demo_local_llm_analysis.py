#!/usr/bin/env python3
"""
Demo: Analyze collected pain points with local LLM (vcoder-120b)

Reads pain points from JSON exports and sends to local LM Studio for analysis.
"""

import json
import os
from pathlib import Path
from anthropic import Anthropic

def main():
    """Analyze pain points with local LLM."""

    print("="*70)
    print("LOCAL LLM ANALYSIS DEMO (vcoder-120b)")
    print("="*70)

    # Load ACIM pain points from most recent export
    exports_dir = Path("logs/knowledge_ingest/exports")
    acim_files = sorted(exports_dir.glob("acim_*.json"), reverse=True)

    if not acim_files:
        print("\n❌ No ACIM pain point exports found")
        print(f"   Looked in: {exports_dir}")
        return

    latest_file = acim_files[0]
    print(f"\n1. Loading pain points from: {latest_file.name}")

    with open(latest_file) as f:
        pain_points = json.load(f)

    print(f"   Found {len(pain_points)} pain points")

    # Display sample
    print("\n" + "="*70)
    print("SAMPLE PAIN POINTS")
    print("="*70)

    for i, pp in enumerate(pain_points[:3], 1):
        content = pp.get('content', 'N/A')
        score = pp.get('authenticity_score', 0)
        print(f"\n{i}. Authenticity: {score:.2f}")
        print(f"   {content[:200]}...")

    # Prepare for analysis
    pain_text = "\n\n".join([
        f"Pain Point {i+1}: {pp.get('content', 'N/A')}"
        for i, pp in enumerate(pain_points[:5])
    ])

    print("\n" + "="*70)
    print("SENDING TO LOCAL LLM")
    print("="*70)
    print(f"Model: {os.getenv('LOCAL_MODEL_NAME', 'vcoder-120b-1.0-qx86-hi-mlx')}")
    print(f"Endpoint: {os.getenv('OPENAI_API_BASE', 'http://192.168.0.2:1234/v1')}")

    # Analyze with local LLM
    client = Anthropic(
        api_key="not-needed",  # Local doesn't need key
        base_url=os.getenv("OPENAI_API_BASE", "http://192.168.0.2:1234/v1")
    )

    try:
        print("\n⏳ Generating analysis...")
        response = client.messages.create(
            model=os.getenv("LOCAL_MODEL_NAME", "vcoder-120b-1.0-qx86-hi-mlx"),
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Analyze these A Course in Miracles (ACIM) pain points from Reddit and identify:

1. Common themes and patterns
2. Key struggles people face with ACIM practice
3. Top 3 coaching opportunities

Pain Points from Reddit:
{pain_text}

Provide concise analysis (5-7 sentences max)."""
            }]
        )

        analysis = response.content[0].text

        print("\n" + "="*70)
        print("LOCAL LLM ANALYSIS")
        print("="*70)
        print(analysis)
        print("="*70)

        # Summary
        print("\n" + "="*70)
        print("DEMO COMPLETE")
        print("="*70)
        print(f"✅ Loaded {len(pain_points)} pain points from {latest_file.name}")
        print(f"✅ Analyzed with local LLM (vcoder-120b)")
        print(f"✅ Complete pipeline demonstrated:")
        print(f"   Reddit → Pattern Matching → JSON Export → Local LLM Analysis")
        print("\n" + "="*70)

    except Exception as e:
        print(f"\n❌ Local LLM error: {e}")
        print("\n   Troubleshooting:")
        print(f"   - Check LM Studio is running at {os.getenv('OPENAI_API_BASE')}")
        print(f"   - Check model {os.getenv('LOCAL_MODEL_NAME')} is loaded")
        print(f"   - Try: curl {os.getenv('OPENAI_API_BASE', 'http://192.168.0.2:1234/v1')}/models")


if __name__ == "__main__":
    main()
