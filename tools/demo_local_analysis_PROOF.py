#!/usr/bin/env python3
"""
PROOF: Local LLM Analysis with vcoder-120b (LOCALHOST)

This demonstrates ACTUAL local LLM analysis using localhost:1234 endpoint.
No remote servers, no cloud APIs - pure local inference.
"""

import json
import os
from pathlib import Path
from anthropic import Anthropic

def main():
    """Analyze collected pain points with LOCAL LLM - PROOF OF CONCEPT"""

    print("=" * 80)
    print("PROOF: LOCAL LLM ANALYSIS (vcoder-120b on localhost:1234)")
    print("=" * 80)
    print()

    # Load pain points from exports
    exports_dir = Path("logs/knowledge_ingest/exports")

    # Get the most recent conscious_uncoupling file (best quality data)
    files = sorted(exports_dir.glob("conscious_uncoupling_*.json"), reverse=True)
    if not files:
        print("❌ No conscious_uncoupling exports found")
        return

    latest_file = files[0]
    print(f"📂 Loading from: {latest_file.name}")

    with open(latest_file) as f:
        pain_points = json.load(f)

    print(f"   Found {len(pain_points)} pain points")
    print()

    # Show sample
    print("=" * 80)
    print("SAMPLE PAIN POINTS (Top 3 by authenticity)")
    print("=" * 80)

    sorted_points = sorted(pain_points, key=lambda x: x['authenticity_score'], reverse=True)[:3]

    for i, pp in enumerate(sorted_points, 1):
        content = pp.get('content', 'N/A')
        score = pp.get('authenticity_score', 0)
        url = pp.get('source_url', 'N/A')
        print(f"\n{i}. Authenticity: {score:.3f}")
        print(f"   Source: {url}")
        print(f"   Preview: {content[:250]}...")
        print()

    # Prepare analysis request
    pain_text = "\n\n---\n\n".join([
        f"Pain Point {i+1} (Score: {pp.get('authenticity_score', 0):.2f}):\n{pp.get('content', 'N/A')[:800]}"
        for i, pp in enumerate(sorted_points[:3])
    ])

    print("=" * 80)
    print("SENDING TO LOCAL LLM (LOCALHOST)")
    print("=" * 80)
    print(f"Endpoint: http://localhost:1234/v1")
    print(f"Model: vcoder-120b-1.0-hi-mlx")
    print(f"Pain points to analyze: {len(sorted_points[:3])}")
    print()

    # Initialize Anthropic SDK with LOCAL endpoint
    client = Anthropic(
        api_key="not-needed-local",
        base_url="http://localhost:1234/v1"
    )

    try:
        print("⏳ Generating analysis with LOCAL MODEL...")
        print()

        response = client.messages.create(
            model="vcoder-120b-1.0-hi-mlx",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""You are a professional coaching analyst. Analyze these pain points from the "conscious uncoupling" (divorce/breakup) coaching niche.

Pain Points from Reddit:
{pain_text}

Provide:
1. Top 3 common themes across these pain points
2. Key emotional struggles people face
3. Top 3 specific coaching opportunities (what services could help)
4. One surprising insight from the data

Be concise and actionable. Format as numbered lists."""
            }]
        )

        analysis = response.content[0].text

        print("=" * 80)
        print("✅ LOCAL LLM ANALYSIS COMPLETE")
        print("=" * 80)
        print(analysis)
        print()
        print("=" * 80)

        # Proof of local execution
        print()
        print("🎯 PROOF OF LOCAL EXECUTION:")
        print("   ✓ Endpoint: http://localhost:1234/v1 (not remote)")
        print("   ✓ Model: vcoder-120b-1.0-hi-mlx (120B parameter local model)")
        print("   ✓ Analysis generated from Reddit data")
        print("   ✓ Zero cloud API costs")
        print()
        print("=" * 80)

    except Exception as e:
        print(f"❌ Local LLM error: {e}")
        print()
        print("Troubleshooting:")
        print("  - LM Studio must be running on localhost:1234")
        print("  - Model 'vcoder-120b-1.0-hi-mlx' must be loaded")
        print(f"  - Try: curl http://localhost:1234/v1/models")


if __name__ == "__main__":
    main()
