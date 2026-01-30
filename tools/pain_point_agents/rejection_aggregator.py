#!/usr/bin/env python3
"""
Rejection Aggregator - Find Meta-Patterns in Rejected Opportunities

"Maybe something greater will emerge" - by looking at ALL rejections together,
we might find patterns that individual weak signals miss.

This tool:
1. Loads all rejected opportunities
2. Clusters them by theme/market
3. Finds the intersection of multiple weak signals
4. Generates meta-opportunities from the aggregate
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict
from dataclasses import dataclass, asdict

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@dataclass
class MetaOpportunity:
    """An opportunity that emerges from aggregating multiple rejections"""
    id: str
    theme: str
    combined_evidence_count: int
    rejection_count: int  # How many rejections contributed

    # Aggregated insights
    common_pains: List[str]
    common_audiences: List[str]
    recurring_flaws: List[str]  # What kept getting flagged

    # The meta-insight
    meta_observation: str
    reframed_opportunity: str
    why_aggregate_is_stronger: str

    # Suggested approach
    suggested_headline: str
    suggested_mechanism: str
    suggested_guarantee: str


class RejectionAggregator:
    """
    Aggregate rejected opportunities to find meta-patterns.
    """

    def __init__(
        self,
        storage_path: str = "/Volumes/Satechi4TB/pain_points",
        model_base_url: str = "http://localhost:1234/v1",
    ):
        self.storage_path = Path(storage_path)
        self.rejected_path = self.storage_path / "opportunities" / "rejected"
        self.model_base_url = model_base_url

    def _get_llm_client(self):
        if not OpenAI:
            return None
        try:
            return OpenAI(api_key="not-needed", base_url=self.model_base_url, timeout=120.0)
        except:
            return None

    def _clean_llm_response(self, text: str) -> str:
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        return text

    def load_rejections(self) -> List[Dict]:
        """Load all rejected opportunities"""
        rejections = []
        for f in self.rejected_path.glob("*.json"):
            try:
                with open(f) as fp:
                    rejections.append(json.load(fp))
            except:
                pass
        return rejections

    def cluster_by_theme(self, rejections: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Cluster rejections by common themes.
        Uses simple keyword matching, could be enhanced with embeddings.
        """
        themes = defaultdict(list)

        theme_keywords = {
            "loneliness_connection": ["lonely", "friend", "connection", "isolat", "social"],
            "anxiety_overwhelm": ["anxiety", "stress", "overwhelm", "panic", "worry"],
            "confidence_self_worth": ["confidence", "self-worth", "self-esteem", "insecur"],
            "career_direction": ["career", "job", "work", "profession", "direction"],
            "relationship_dynamics": ["relationship", "partner", "marriage", "dating"],
            "health_transformation": ["health", "weight", "fitness", "energy", "body"],
            "productivity_focus": ["productivity", "focus", "discipline", "procrastin"],
            "trauma_healing": ["trauma", "cptsd", "ptsd", "abuse", "neglect"],
            "life_meaning": ["meaning", "purpose", "direction", "lost", "stuck"],
        }

        for rej in rejections:
            text = f"{rej.get('title', '')} {rej.get('target_audience', '')} {rej.get('core_pain', '')}".lower()

            matched = False
            for theme, keywords in theme_keywords.items():
                if any(kw in text for kw in keywords):
                    themes[theme].append(rej)
                    matched = True
                    break

            if not matched:
                themes["other"].append(rej)

        return dict(themes)

    def analyze_cluster(self, theme: str, rejections: List[Dict]) -> Dict:
        """
        Analyze a cluster of rejections to find patterns.
        """
        # Aggregate data
        all_pains = []
        all_audiences = []
        all_flaws = []
        all_quotes = []
        total_evidence = 0

        for rej in rejections:
            if rej.get("core_pain"):
                all_pains.append(rej["core_pain"])
            if rej.get("target_audience"):
                all_audiences.append(rej["target_audience"])
            all_flaws.extend(rej.get("fatal_flaws", []))
            all_quotes.extend(rej.get("sample_quotes", [])[:2])
            total_evidence += rej.get("evidence_count", 0)

        # Find common elements
        flaw_counter = Counter()
        for flaw in all_flaws:
            flaw_lower = flaw.lower()
            if "evidence" in flaw_lower or "mismatch" in flaw_lower:
                flaw_counter["Evidence mismatch"] += 1
            if "vague" in flaw_lower or "generic" in flaw_lower:
                flaw_counter["Too vague/generic"] += 1
            if "clinical" in flaw_lower or "liability" in flaw_lower:
                flaw_counter["Clinical/legal risk"] += 1
            if "niche" in flaw_lower or "small" in flaw_lower:
                flaw_counter["Too narrow"] += 1
            if "saturated" in flaw_lower or "competition" in flaw_lower:
                flaw_counter["Saturated market"] += 1

        return {
            "theme": theme,
            "rejection_count": len(rejections),
            "total_evidence": total_evidence,
            "sample_pains": all_pains[:5],
            "sample_audiences": all_audiences[:5],
            "common_flaws": flaw_counter.most_common(5),
            "sample_quotes": all_quotes[:5],
        }

    def generate_meta_opportunity(self, analysis: Dict) -> MetaOpportunity:
        """
        Generate a meta-opportunity from aggregated rejection data.
        """
        client = self._get_llm_client()
        if not client:
            return None

        prompt = f"""You're looking at {analysis['rejection_count']} rejected landing page opportunities
that all share the theme: "{analysis['theme']}"

Combined, they represent {analysis['total_evidence']} data points.

SAMPLE PAINS (what people expressed):
{chr(10).join('- ' + p[:200] for p in analysis['sample_pains'])}

SAMPLE AUDIENCES:
{chr(10).join('- ' + a[:150] for a in analysis['sample_audiences'])}

WHY THEY WERE REJECTED (common flaws):
{chr(10).join(f'- {flaw}: {count}x' for flaw, count in analysis['common_flaws'])}

SAMPLE QUOTES:
{chr(10).join('- ' + q[:200] + '...' for q in analysis['sample_quotes'][:3])}

Now, looking at ALL of these together - what META-PATTERN emerges?
What opportunity exists that individual weak signals missed?

Think about:
1. What's the REAL underlying need across all these rejections?
2. How could we reframe this to avoid the common flaws?
3. What would make this a VIABLE business opportunity?

Respond in JSON:
{{
    "meta_observation": "The insight that emerges from looking at all of these together",
    "real_underlying_need": "The actual need these people share (not the surface pain)",
    "why_previous_approaches_failed": "Why the individual attempts were rejected",
    "reframed_opportunity": "How to approach this differently",
    "viable_business_angle": "A legal, ethical, scalable way to serve this need",
    "suggested_headline": "A headline for the reframed opportunity",
    "suggested_mechanism": "The 'why it works' that would be believable",
    "suggested_guarantee": "Risk reversal that makes sense",
    "target_that_works": "A more viable target audience for this"
}}"""

        try:
            response = client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )

            result = self._clean_llm_response(response.choices[0].message.content)

            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(result[start:end])

                import hashlib
                opp_id = hashlib.md5(analysis['theme'].encode()).hexdigest()[:12]

                return MetaOpportunity(
                    id=opp_id,
                    theme=analysis['theme'],
                    combined_evidence_count=analysis['total_evidence'],
                    rejection_count=analysis['rejection_count'],
                    common_pains=analysis['sample_pains'],
                    common_audiences=analysis['sample_audiences'],
                    recurring_flaws=[f"{f}: {c}x" for f, c in analysis['common_flaws']],
                    meta_observation=data.get("meta_observation", ""),
                    reframed_opportunity=data.get("reframed_opportunity", ""),
                    why_aggregate_is_stronger=data.get("why_previous_approaches_failed", ""),
                    suggested_headline=data.get("suggested_headline", ""),
                    suggested_mechanism=data.get("suggested_mechanism", ""),
                    suggested_guarantee=data.get("suggested_guarantee", ""),
                )

        except Exception as e:
            print(f"Error generating meta-opportunity: {e}")

        return None

    def run(self) -> List[MetaOpportunity]:
        """
        Run the full aggregation analysis.
        """
        print("=" * 60)
        print("REJECTION AGGREGATOR")
        print("Finding Meta-Patterns in Rejected Opportunities")
        print("=" * 60)

        # Load rejections
        rejections = self.load_rejections()
        print(f"\nLoaded {len(rejections)} rejected opportunities")

        # Cluster by theme
        clusters = self.cluster_by_theme(rejections)
        print(f"\nFound {len(clusters)} theme clusters:")
        for theme, items in sorted(clusters.items(), key=lambda x: -len(x[1])):
            print(f"  {theme}: {len(items)} rejections")

        # Analyze each cluster and generate meta-opportunities
        meta_opportunities = []

        for theme, items in clusters.items():
            if len(items) >= 5:  # Only analyze clusters with enough data
                print(f"\nAnalyzing: {theme}...")
                analysis = self.analyze_cluster(theme, items)

                meta_opp = self.generate_meta_opportunity(analysis)
                if meta_opp:
                    meta_opportunities.append(meta_opp)
                    print(f"  Meta-observation: {meta_opp.meta_observation[:100]}...")

        # Save results
        output_file = self.storage_path / "opportunities" / "meta_opportunities.json"
        with open(output_file, 'w') as f:
            json.dump([asdict(m) for m in meta_opportunities], f, indent=2)

        print(f"\n{'=' * 60}")
        print(f"Generated {len(meta_opportunities)} meta-opportunities")
        print(f"Saved to: {output_file}")
        print("=" * 60)

        return meta_opportunities


def main():
    aggregator = RejectionAggregator()
    meta_opps = aggregator.run()

    # Print summary
    print("\n" + "=" * 60)
    print("META-OPPORTUNITIES SUMMARY")
    print("=" * 60)

    for opp in meta_opps:
        print(f"\n### {opp.theme.upper()}")
        print(f"Evidence: {opp.combined_evidence_count} data points from {opp.rejection_count} rejections")
        print(f"\nMeta-Observation: {opp.meta_observation}")
        print(f"\nReframed: {opp.reframed_opportunity}")
        print(f"\nSuggested Headline: {opp.suggested_headline}")
        print("-" * 40)


if __name__ == "__main__":
    main()
