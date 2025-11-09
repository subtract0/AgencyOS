#!/usr/bin/env python3
"""
Quora Manual Integration Demo

Since Quora blocks automated scraping (Cloudflare), this demonstrates:
1. How to manually add Quora Q&A content
2. Apply same pattern matching
3. Analyze with local LLM alongside Reddit data

Usage:
1. Copy/paste Quora answers about your topics into quora_samples/
2. Run this script to extract pain points
3. Analyze with local 120B model
"""

import json
import sys
from pathlib import Path
from openai import OpenAI


# Sample Quora content (would come from manual collection)
QUORA_SAMPLES = {
    "conscious_uncoupling": [
        {
            "question": "What is the hardest part about getting divorced?",
            "answer": """I think the hardest part for me was accepting that I failed. My biggest struggle was letting go of the future I had planned - the kids growing up with both parents, the family vacations, growing old together.

The practical problems like dividing assets and custody were painful, but the emotional challenge of seeing your life partner become a stranger is what broke me. I experienced waves of grief that felt like they would never end.

My biggest fear was that my children would be damaged by this, and I still struggle with guilt about that daily.""",
            "url": "https://www.quora.com/What-is-the-hardest-part-about-getting-divorced",
            "upvotes": 1247
        },
        {
            "question": "How do I cope with divorce guilt?",
            "answer": """I was consumed by guilt for months. I felt like I destroyed our family. The frustrations I had in the marriage seemed so small compared to what we're going through now.

What I wish I knew earlier is that guilt is a normal part of grieving a relationship. I learned from my therapist that guilt often masks other emotions - anger, sadness, fear.

My advice: don't rush the process. The barriers I put up to avoid feeling the pain only made it worse. Give yourself permission to feel everything.""",
            "url": "https://www.quora.com/How-do-I-cope-with-divorce-guilt",
            "upvotes": 892
        }
    ]
}


def calculate_authenticity(text: str) -> float:
    """Calculate authenticity score using same patterns as Reddit"""
    experience_markers = ["I think", "I feel", "I was", "my biggest struggle",
                          "I experienced", "my biggest fear", "I learned", "my advice"]
    pain_signals = ["struggles", "problems", "challenge", "difficulties", "painful"]
    emotional_depth = ["frustrations", "guilt", "grief", "fear"]

    text_lower = text.lower()

    exp_score = sum(1 for marker in experience_markers if marker.lower() in text_lower) / len(experience_markers)
    pain_score = sum(1 for signal in pain_signals if signal.lower() in text_lower) / len(pain_signals)
    emotion_score = sum(1 for emotion in emotional_depth if emotion.lower() in text_lower) / len(emotional_depth)

    # Weighted average (same as Reddit system)
    return (exp_score * 1.0 + pain_score * 1.5 + emotion_score * 1.2) / 3.7


def main():
    """Demonstrate Quora + Reddit integration with local LLM"""

    print("=" * 80)
    print("QUORA + REDDIT INTEGRATION DEMO")
    print("=" * 80)
    print()

    # Process Quora samples
    quora_points = []
    for qa in QUORA_SAMPLES["conscious_uncoupling"]:
        combined_text = f"{qa['question']}\n\n{qa['answer']}"
        score = calculate_authenticity(combined_text)

        quora_points.append({
            "content": combined_text,
            "source_url": qa['url'],
            "source_platform": "quora",
            "topic": "conscious_uncoupling",
            "authenticity_score": score,
            "upvotes": qa.get('upvotes', 0)
        })

    print(f"✅ Processed {len(quora_points)} Quora Q&A")
    for qp in quora_points:
        print(f"   - Score: {qp['authenticity_score']:.3f} | {qp['content'][:80]}...")

    # Load Reddit data
    exports_dir = Path("logs/knowledge_ingest/exports")
    reddit_file = sorted(exports_dir.glob("conscious_uncoupling_*.json"), reverse=True)[0]

    with open(reddit_file) as f:
        reddit_points = json.load(f)

    # Add source platform to Reddit data
    for rp in reddit_points:
        rp['source_platform'] = 'reddit'

    print(f"✅ Loaded {len(reddit_points)} Reddit pain points")
    print()

    # Combine and sort by authenticity
    all_points = quora_points + reddit_points
    sorted_points = sorted(all_points, key=lambda x: x['authenticity_score'], reverse=True)[:5]

    print("=" * 80)
    print("TOP 5 PAIN POINTS (QUORA + REDDIT)")
    print("=" * 80)
    for i, pp in enumerate(sorted_points, 1):
        platform = pp['source_platform'].upper()
        score = pp['authenticity_score']
        content = pp['content']
        print(f"\n{i}. [{platform}] Score: {score:.3f}")
        print(f"   {content[:150]}...")

    # Prepare for local LLM analysis
    pain_text = "\n\n---\n\n".join([
        f"[{pp['source_platform'].upper()}] Score {pp['authenticity_score']:.2f}:\n{pp['content'][:600]}"
        for pp in sorted_points
    ])

    print("\n" + "=" * 80)
    print("ANALYZING WITH LOCAL LLM")
    print("=" * 80)
    print(f"Model: vcoder-120b-1.0-hi-mlx")
    print(f"Endpoint: localhost:1234")
    print(f"Pain points: {len(sorted_points)} (from Quora + Reddit)")
    print()

    # Initialize local LLM
    client = OpenAI(
        api_key="not-needed",
        base_url="http://localhost:1234/v1"
    )

    try:
        print("⏳ Generating cross-platform analysis...\n")

        response = client.chat.completions.create(
            model="vcoder-120b-1.0-hi-mlx",
            messages=[{
                "role": "user",
                "content": f"""Analyze these divorce/breakup pain points from BOTH Quora and Reddit:

{pain_text}

Provide:
1. Key differences between Quora vs Reddit pain points
2. Common themes across BOTH platforms
3. Most impactful coaching opportunity revealed by cross-platform data

Be concise (5-6 sentences)."""
            }],
            temperature=0.7,
            max_tokens=600
        )

        analysis = response.choices[0].message.content

        print("=" * 80)
        print("✅ CROSS-PLATFORM LOCAL LLM ANALYSIS")
        print("=" * 80)
        print(analysis)
        print()
        print("=" * 80)
        print()
        print("🎯 PROOF OF MULTI-SOURCE INTEGRATION:")
        print(f"   ✓ {len(quora_points)} Quora Q&A processed")
        print(f"   ✓ {len(reddit_points)} Reddit posts processed")
        print(f"   ✓ Combined authenticity scoring")
        print(f"   ✓ Analyzed locally (localhost:1234)")
        print(f"   ✓ Zero cloud costs")
        print("=" * 80)

        # Save combined export
        export_path = Path("logs/knowledge_ingest/exports/multi_platform_demo.json")
        export_path.parent.mkdir(parents=True, exist_ok=True)

        with open(export_path, 'w') as f:
            json.dump(sorted_points, f, indent=2)

        print(f"\n📁 Saved to: {export_path}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
