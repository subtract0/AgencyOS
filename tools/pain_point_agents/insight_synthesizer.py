#!/usr/bin/env python3
"""
Insight Synthesizer - Deep Pattern Mining from Pain Point Data

This agent ACTUALLY READS the data and extracts:
1. Specific, non-obvious pain points (not "lonely" but "can't go to barber")
2. Workarounds people have created (signals unmet needs)
3. Exact language and phrases that reveal deep desires
4. Product gaps - things people wish existed
5. Willingness-to-pay signals hidden in the text

Philosophy: Generic insights = worthless. We need SPECIFIC, UNUSUAL patterns
that reveal opportunities nobody else sees.
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict, field

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


@dataclass
class DeepInsight:
    """A specific, non-obvious insight from the data"""
    id: str
    category: str  # workaround, product_gap, language_pattern, hidden_desire, unusual_pain

    # The insight itself
    observation: str  # What we noticed
    evidence: List[str]  # Direct quotes that support this
    frequency: int  # How often this appears

    # Business implications
    product_opportunity: str  # What could be built
    why_not_obvious: str  # Why competitors miss this
    target_specificity: str  # Exactly who this is for

    # Scoring
    uniqueness_score: float  # 1-10, how non-obvious
    evidence_strength: float  # 1-10, how well supported
    monetization_potential: float  # 1-10, could people pay for this

    source_subreddits: List[str] = field(default_factory=list)
    extracted_at: str = ""


class InsightSynthesizer:
    """
    Deep pattern miner that extracts non-obvious insights from pain point data.
    """

    # Patterns to look for
    INSIGHT_PROMPTS = {
        "workarounds": """Look for WORKAROUNDS - things people have created or do themselves
because no good solution exists. Examples:
- "I cut my own hair because..."
- "I made a spreadsheet to track..."
- "I pretend to be on the phone so..."
These reveal unmet needs that could be productized.""",

        "product_gaps": """Look for PRODUCT GAPS - explicit mentions of things people wish existed:
- "Why isn't there a..."
- "I wish someone would make..."
- "If only there was..."
- "I would pay for..."
These are direct product opportunities.""",

        "unusual_pains": """Look for UNUSUAL, SPECIFIC pains that are NOT generic (not just "lonely" or "anxious"):
- Very specific situations (can't go to barber, can't order food on phone)
- Niche life circumstances (remote worker who hasn't left house in months)
- Unexpected combinations (successful career + zero friends)
These reveal underserved niches.""",

        "hidden_desires": """Look for HIDDEN DESIRES buried in complaints - what do they REALLY want?
Not surface desires (want friends) but SPECIFIC outcomes:
- "I just want ONE person who..."
- "All I need is..."
- "If I could just..."
The specificity reveals product features.""",

        "language_patterns": """Look for UNIQUE LANGUAGE and PHRASES people use repeatedly:
- How they describe their situation
- Metaphors they use
- Self-labels they apply
This is copywriting gold - the exact words that resonate.""",

        "failed_solutions": """Look for FAILED SOLUTIONS - what have people tried that didn't work?
- "I tried therapy but..."
- "Apps don't work because..."
- "I've read every book and..."
This reveals what NOT to build and what's missing from existing solutions.""",
    }

    def __init__(
        self,
        storage_path: str = "/Volumes/Satechi4TB/pain_points",
        model_base_url: str = "http://localhost:1234/v1",
    ):
        self.storage_path = Path(storage_path)
        self.insights_path = self.storage_path / "insights"
        self.insights_path.mkdir(parents=True, exist_ok=True)
        self.model_base_url = model_base_url

        print("=" * 70)
        print("INSIGHT SYNTHESIZER")
        print("Deep Pattern Mining for Non-Obvious Opportunities")
        print("=" * 70)

    def _get_llm_client(self) -> Optional[OpenAI]:
        if not OpenAI:
            return None
        try:
            return OpenAI(api_key="not-needed", base_url=self.model_base_url, timeout=180.0)
        except:
            return None

    def _clean_response(self, text: str) -> str:
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        if "```json" in text:
            text = text.replace("```json", "").replace("```", "")
        elif "```" in text:
            text = text.replace("```", "")
        return text.strip()

    def get_random_documents(self, n: int = 100, topic_filter: str = None) -> List[Dict]:
        """Get random documents from the database for analysis."""
        if not CHROMADB_AVAILABLE:
            return []

        try:
            client = chromadb.PersistentClient(
                path=str(self.storage_path / "chromadb_index"),
                settings=Settings(anonymized_telemetry=False)
            )
            collection = client.get_collection("pain_points")
            total = collection.count()

            # Get documents from random offsets
            docs = []
            offsets = random.sample(range(0, total - 100, 100), min(10, total // 100))

            for offset in offsets:
                results = collection.get(
                    include=["documents", "metadatas"],
                    limit=20,
                    offset=offset
                )
                for doc, meta in zip(results["documents"], results["metadatas"]):
                    if topic_filter and meta.get("topic") != topic_filter:
                        continue
                    docs.append({
                        "content": doc,
                        "subreddit": meta.get("topic", "unknown"),
                        "quality": meta.get("quality_score", 0),
                    })

            # Shuffle and return
            random.shuffle(docs)
            return docs[:n]

        except Exception as e:
            print(f"Error getting documents: {e}")
            return []

    def mine_insights(self, category: str, documents: List[Dict]) -> List[DeepInsight]:
        """Mine a specific category of insights from documents."""
        client = self._get_llm_client()
        if not client:
            return []

        prompt_instruction = self.INSIGHT_PROMPTS.get(category, "")
        if not prompt_instruction:
            return []

        # Prepare document batch
        doc_texts = []
        for doc in documents[:50]:  # Analyze 50 at a time
            doc_texts.append(f"[r/{doc['subreddit']}]: {doc['content'][:600]}")

        docs_combined = "\n\n---\n\n".join(doc_texts)

        prompt = f"""You are a pattern-recognition expert analyzing Reddit posts about personal struggles.

{prompt_instruction}

DOCUMENTS TO ANALYZE:
{docs_combined}

Find 3-5 SPECIFIC, NON-OBVIOUS insights. For each, provide:

{{
    "insights": [
        {{
            "observation": "The specific pattern you noticed",
            "evidence": ["Direct quote 1", "Direct quote 2", "Direct quote 3"],
            "frequency_estimate": "How common this seems (rare/occasional/common)",
            "product_opportunity": "What specific product/service could address this",
            "why_not_obvious": "Why most people/companies miss this",
            "target_who": "Exactly who experiences this (be very specific)",
            "uniqueness": 1-10,
            "evidence_strength": 1-10,
            "monetization": 1-10
        }}
    ]
}}

CRITICAL:
- NO generic insights like "people are lonely" or "anxiety is common"
- ONLY specific, unusual patterns that reveal product opportunities
- Include EXACT quotes as evidence
- Be SPECIFIC about who the target is"""

        try:
            response = client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=2500
            )

            result = self._clean_response(response.choices[0].message.content)

            # Parse JSON
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(result[start:end])

                insights = []
                for i, item in enumerate(data.get("insights", [])):
                    import hashlib
                    insight_id = hashlib.md5(
                        f"{category}_{item.get('observation', '')[:50]}".encode()
                    ).hexdigest()[:12]

                    freq_map = {"rare": 1, "occasional": 3, "common": 7}
                    freq = freq_map.get(item.get("frequency_estimate", "").lower(), 2)

                    insight = DeepInsight(
                        id=insight_id,
                        category=category,
                        observation=item.get("observation", ""),
                        evidence=item.get("evidence", [])[:5],
                        frequency=freq,
                        product_opportunity=item.get("product_opportunity", ""),
                        why_not_obvious=item.get("why_not_obvious", ""),
                        target_specificity=item.get("target_who", ""),
                        uniqueness_score=float(item.get("uniqueness", 5)),
                        evidence_strength=float(item.get("evidence_strength", 5)),
                        monetization_potential=float(item.get("monetization", 5)),
                        source_subreddits=list(set(d["subreddit"] for d in documents[:20])),
                        extracted_at=datetime.now().isoformat(),
                    )
                    insights.append(insight)

                return insights

        except Exception as e:
            print(f"Error mining {category}: {e}")

        return []

    def synthesize_product_concept(self, insights: List[DeepInsight]) -> Dict:
        """Synthesize insights into a concrete product concept."""
        client = self._get_llm_client()
        if not client or not insights:
            return {}

        # Prepare insights summary
        insights_text = ""
        for ins in insights[:10]:
            insights_text += f"""
### {ins.category.upper()}: {ins.observation}
Evidence: {'; '.join(ins.evidence[:2])}
Target: {ins.target_specificity}
Opportunity: {ins.product_opportunity}
Scores: Unique={ins.uniqueness_score}, Evidence={ins.evidence_strength}, Monetization={ins.monetization_potential}
"""

        prompt = f"""You have these SPECIFIC, NON-OBVIOUS insights from analyzing thousands of Reddit posts:

{insights_text}

Now synthesize these into ONE concrete product concept that:
1. Addresses a SPECIFIC, underserved niche (not "lonely people" but "remote workers who haven't left their apartment in weeks")
2. Solves a problem that existing solutions miss
3. Uses the exact language these people use
4. Has a clear path to monetization

Respond with:
{{
    "product_name": "Short, memorable name",
    "one_liner": "10-word pitch",
    "specific_target": "Exactly who this is for (very specific)",
    "core_problem_solved": "The specific problem, not generic",
    "why_existing_solutions_fail": "What's wrong with current options",
    "unique_mechanism": "How this works differently",
    "minimum_viable_product": "Simplest version that delivers value",
    "pricing_model": "How to charge and why",
    "first_100_customers": "Where to find them specifically",
    "unfair_advantage": "Why this is hard to copy"
}}

Be SPECIFIC and CONCRETE. No generic startup pitches."""

        try:
            response = client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=1500
            )

            result = self._clean_response(response.choices[0].message.content)

            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])

        except Exception as e:
            print(f"Error synthesizing: {e}")

        return {}

    def run_deep_analysis(self, sample_size: int = 200) -> Dict:
        """Run full deep analysis across all insight categories."""
        print(f"\nLoading {sample_size} random documents...")
        documents = self.get_random_documents(sample_size)
        print(f"Loaded {len(documents)} documents")

        all_insights = []

        for category in self.INSIGHT_PROMPTS.keys():
            print(f"\nMining {category}...")
            insights = self.mine_insights(category, documents)
            print(f"  Found {len(insights)} insights")

            for ins in insights:
                all_insights.append(ins)
                print(f"    - [{ins.uniqueness_score:.0f}] {ins.observation[:60]}...")

        # Save raw insights
        insights_file = self.insights_path / f"insights_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(insights_file, 'w') as f:
            json.dump([asdict(i) for i in all_insights], f, indent=2)
        print(f"\nSaved {len(all_insights)} insights to {insights_file}")

        # Filter top insights
        top_insights = sorted(
            all_insights,
            key=lambda x: (x.uniqueness_score + x.evidence_strength + x.monetization_potential) / 3,
            reverse=True
        )[:10]

        print(f"\n{'='*70}")
        print("TOP INSIGHTS")
        print("="*70)
        for ins in top_insights:
            avg_score = (ins.uniqueness_score + ins.evidence_strength + ins.monetization_potential) / 3
            print(f"\n[{avg_score:.1f}] {ins.category.upper()}")
            print(f"    {ins.observation}")
            print(f"    Target: {ins.target_specificity}")
            print(f"    Opportunity: {ins.product_opportunity[:80]}...")

        # Synthesize product concept
        print(f"\n{'='*70}")
        print("SYNTHESIZING PRODUCT CONCEPT")
        print("="*70)

        product = self.synthesize_product_concept(top_insights)

        if product:
            # Save product concept
            product_file = self.insights_path / f"product_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            product["source_insights"] = [i.id for i in top_insights]
            product["generated_at"] = datetime.now().isoformat()

            with open(product_file, 'w') as f:
                json.dump(product, f, indent=2)

            print(f"\n{product.get('product_name', 'UNNAMED')}")
            print(f"'{product.get('one_liner', '')}'")
            print(f"\nTarget: {product.get('specific_target', '')}")
            print(f"\nProblem: {product.get('core_problem_solved', '')}")
            print(f"\nWhy existing solutions fail: {product.get('why_existing_solutions_fail', '')}")
            print(f"\nMVP: {product.get('minimum_viable_product', '')}")
            print(f"\nFirst 100 customers: {product.get('first_100_customers', '')}")

        return {
            "insights": all_insights,
            "top_insights": top_insights,
            "product_concept": product,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Insight Synthesizer")
    parser.add_argument('--sample-size', type=int, default=200, help='Documents to analyze')
    parser.add_argument('--category', type=str, help='Specific category to mine')

    args = parser.parse_args()

    synthesizer = InsightSynthesizer()
    results = synthesizer.run_deep_analysis(sample_size=args.sample_size)

    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"Total insights: {len(results['insights'])}")
    print(f"Top insights: {len(results['top_insights'])}")
    print(f"Product concept generated: {'Yes' if results['product_concept'] else 'No'}")
    print("="*70)


if __name__ == "__main__":
    main()
