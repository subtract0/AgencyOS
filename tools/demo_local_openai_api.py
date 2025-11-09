#!/usr/bin/env python3
"""
PROOF: Local LLM Analysis using OpenAI-compatible API

LM Studio provides OpenAI-compatible API at localhost:1234.
This script uses the OpenAI SDK with base_url override.
"""

import json
import sys
from pathlib import Path

# Try importing openai
try:
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI SDK not installed")
    print("Install with: pip install openai")
    sys.exit(1)


def main():
    """Analyze pain points with LOCAL LM Studio"""

    print("=" * 80)
    print("PROOF: LOCAL LLM ANALYSIS (vcoder-120b via OpenAI API)")
    print("=" * 80)
    print()

    # Load pain points
    exports_dir = Path("logs/knowledge_ingest/exports")
    files = sorted(exports_dir.glob("conscious_uncoupling_*.json"), reverse=True)

    if not files:
        print("❌ No pain point exports found")
        return

    latest_file = files[0]
    print(f"📂 Loading: {latest_file.name}")

    with open(latest_file) as f:
        pain_points = json.load(f)

    print(f"   Found {len(pain_points)} pain points\n")

    # Get top 3 by authenticity
    sorted_points = sorted(
        pain_points,
        key=lambda x: x['authenticity_score'],
        reverse=True
    )[:3]

    # Display samples
    print("SAMPLE PAIN POINTS:")
    print("-" * 80)
    for i, pp in enumerate(sorted_points, 1):
        score = pp.get('authenticity_score', 0)
        content = pp.get('content', 'N/A')
        print(f"\n{i}. Score: {score:.3f}")
        print(f"   {content[:200]}...")

    # Prepare analysis prompt
    pain_text = "\n\n".join([
        f"PAIN POINT {i+1}:\n{pp.get('content', 'N/A')[:600]}"
        for i, pp in enumerate(sorted_points)
    ])

    print("\n" + "=" * 80)
    print("SENDING TO LOCAL LLM")
    print("=" * 80)
    print("Endpoint: http://localhost:1234/v1")
    print("Model: vcoder-120b-1.0-hi-mlx")
    print()

    # Initialize OpenAI client with LOCAL endpoint
    client = OpenAI(
        api_key="not-needed-local",
        base_url="http://localhost:1234/v1"
    )

    try:
        print("⏳ Analyzing with local 120B parameter model...\n")

        response = client.chat.completions.create(
            model="vcoder-120b-1.0-hi-mlx",
            messages=[{
                "role": "user",
                "content": f"""Analyze these divorce/breakup pain points from Reddit:

{pain_text}

Provide a brief analysis (4-5 sentences) covering:
1. Main emotional themes
2. Common struggles
3. Top coaching opportunity

Be concise and actionable."""
            }],
            temperature=0.7,
            max_tokens=500
        )

        analysis = response.choices[0].message.content

        print("=" * 80)
        print("✅ LOCAL LLM ANALYSIS")
        print("=" * 80)
        print(analysis)
        print()
        print("=" * 80)
        print()
        print("🎯 PROOF OF LOCAL EXECUTION:")
        print("   ✓ Model: vcoder-120b-1.0-hi-mlx (120B params)")
        print("   ✓ Endpoint: localhost:1234 (LOCAL)")
        print("   ✓ Zero cloud costs")
        print("   ✓ Privacy: Data never leaves your machine")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check LM Studio is running")
        print("2. Verify model is loaded")
        print("3. Test: curl http://localhost:1234/v1/models")


if __name__ == "__main__":
    main()
