#!/usr/bin/env python3
"""
Golden Opportunity Scout - Autonomous Landing Page Opportunity Generator

This agent continuously:
1. Analyzes the pain points database for patterns
2. Generates potential landing page opportunities
3. Critically evaluates each (plays devil's advocate)
4. Discards most as not good enough
5. Only surfaces truly compelling opportunities

Philosophy: Most ideas are mediocre. We're looking for the ones
where even a harsh critic has nothing bad to say.

Storage: /Volumes/Satechi4TB/pain_points/opportunities/
Runs: Continuously or via cron
"""

import json
import time
import logging
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import Counter, defaultdict

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
class Opportunity:
    """A potential landing page opportunity"""
    id: str
    title: str
    target_audience: str
    core_pain: str
    transformation_promise: str
    evidence_count: int
    sample_quotes: List[str]
    subreddits: List[str]
    generated_at: str

    # Evaluation scores (0-10)
    specificity_score: float = 0.0
    evidence_strength: float = 0.0
    transformation_clarity: float = 0.0
    market_size_indicator: float = 0.0
    competition_gap: float = 0.0

    # Critical evaluation
    devils_advocate: str = ""
    fatal_flaws: List[str] = field(default_factory=list)

    # Final verdict
    is_golden: bool = False
    confidence: float = 0.0


class GoldenOpportunityScout:
    """
    Autonomous agent that finds golden landing page opportunities.

    Most opportunities are discarded. Only the truly compelling
    ones make it through the gauntlet.
    """

    # Minimum thresholds for a "golden" opportunity
    MIN_EVIDENCE_COUNT = 10
    MIN_SPECIFICITY = 7.0
    MIN_EVIDENCE_STRENGTH = 7.0
    MIN_TRANSFORMATION_CLARITY = 8.0
    MIN_OVERALL_CONFIDENCE = 0.75

    def __init__(
        self,
        storage_path: str = "/Volumes/Satechi4TB/pain_points",
        model_base_url: str = "http://localhost:1234/v1",
    ):
        self.storage_path = Path(storage_path)
        self.opportunities_path = self.storage_path / "opportunities"
        self.model_base_url = model_base_url

        # Create directories
        self.opportunities_path.mkdir(parents=True, exist_ok=True)
        (self.opportunities_path / "candidates").mkdir(exist_ok=True)
        (self.opportunities_path / "golden").mkdir(exist_ok=True)
        (self.opportunities_path / "rejected").mkdir(exist_ok=True)

        # Setup logging
        log_file = self.opportunities_path / f"scout_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Load existing golden opportunities to avoid duplicates
        self.existing_ids = self._load_existing_ids()

        self.logger.info("=" * 60)
        self.logger.info("GOLDEN OPPORTUNITY SCOUT")
        self.logger.info("=" * 60)

    def _load_existing_ids(self) -> set:
        """Load IDs of already processed opportunities"""
        ids = set()
        for f in (self.opportunities_path / "golden").glob("*.json"):
            ids.add(f.stem)
        for f in (self.opportunities_path / "rejected").glob("*.json"):
            ids.add(f.stem)
        return ids

    def _get_llm_client(self) -> Optional[OpenAI]:
        """Get LLM client"""
        if not OpenAI:
            return None
        try:
            return OpenAI(
                api_key="not-needed",
                base_url=self.model_base_url,
                timeout=120.0
            )
        except Exception:
            return None

    def _clean_llm_response(self, text: str) -> str:
        """Remove thinking tags from LLM response"""
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        return text

    def find_pain_clusters(self) -> List[Dict]:
        """
        Analyze the database to find clusters of similar pain patterns.
        Returns clusters with high concentration of similar issues.
        """
        if not CHROMADB_AVAILABLE:
            self.logger.warning("ChromaDB not available")
            return []

        clusters = []

        try:
            client = chromadb.PersistentClient(
                path=str(self.storage_path / "chromadb_index"),
                settings=Settings(anonymized_telemetry=False)
            )
            collection = client.get_collection("pain_points")

            # Get sample of high-signal content
            results = collection.get(
                include=["documents", "metadatas"],
                limit=5000
            )

            # Group by topic and find common themes
            topic_docs = defaultdict(list)
            for doc, meta in zip(results["documents"], results["metadatas"]):
                topic = meta.get("topic", "unknown")
                topic_docs[topic].append({
                    "content": doc[:500],
                    "score": meta.get("suffering_score", 0)
                })

            # Find high-volume topics
            for topic, docs in topic_docs.items():
                if len(docs) >= 20:
                    avg_score = sum(d.get("score", 0) or 0 for d in docs) / len(docs)
                    clusters.append({
                        "topic": topic,
                        "count": len(docs),
                        "avg_intensity": avg_score,
                        "samples": [d["content"] for d in docs[:10]]
                    })

            # Sort by count
            clusters.sort(key=lambda x: x["count"], reverse=True)

        except Exception as e:
            self.logger.error(f"Error finding clusters: {e}")

        return clusters[:15]  # Top 15 clusters

    def generate_opportunity_hypotheses(self, clusters: List[Dict]) -> List[Dict]:
        """
        Generate landing page hypotheses from pain clusters.
        Uses LLM to identify specific audience + transformation pairs.
        """
        client = self._get_llm_client()
        if not client:
            return []

        hypotheses = []

        for cluster in clusters[:8]:  # Process top 8 clusters
            samples_text = "\n---\n".join(cluster["samples"][:5])

            prompt = f"""Based on these posts from r/{cluster['topic']} ({cluster['count']} posts in database):

{samples_text}

Generate 2-3 SPECIFIC landing page opportunity hypotheses.

For each, provide (respond in JSON array):
[
  {{
    "target_audience": "Very specific audience (age, situation, mindset)",
    "core_pain": "The specific pain point in their own words",
    "transformation": "What clarity/shift would help them",
    "headline_idea": "A compelling headline for this audience"
  }}
]

Be SPECIFIC. Not "people who are anxious" but "software engineers in their 30s who feel trapped in golden handcuffs".
Focus on audiences who are SEEKING clarity, not just venting."""

            try:
                response = client.chat.completions.create(
                    model="vcoder-120b-1.0-hi-mlx",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000
                )

                result = self._clean_llm_response(response.choices[0].message.content)

                # Parse JSON
                start = result.find('[')
                end = result.rfind(']') + 1
                if start >= 0 and end > start:
                    ideas = json.loads(result[start:end])
                    for idea in ideas:
                        idea["source_topic"] = cluster["topic"]
                        idea["evidence_count"] = cluster["count"]
                        idea["samples"] = cluster["samples"][:5]
                        hypotheses.append(idea)

                time.sleep(1)

            except Exception as e:
                self.logger.debug(f"Error generating hypothesis: {e}")

        return hypotheses

    def evaluate_opportunity(self, hypothesis: Dict) -> Opportunity:
        """
        Critically evaluate an opportunity hypothesis.
        Plays devil's advocate to find fatal flaws.
        """
        opp_id = hashlib.md5(
            f"{hypothesis.get('target_audience', '')}{hypothesis.get('core_pain', '')}".encode()
        ).hexdigest()[:12]

        # Skip if already processed
        if opp_id in self.existing_ids:
            return None

        opportunity = Opportunity(
            id=opp_id,
            title=hypothesis.get("headline_idea", ""),
            target_audience=hypothesis.get("target_audience", ""),
            core_pain=hypothesis.get("core_pain", ""),
            transformation_promise=hypothesis.get("transformation", ""),
            evidence_count=hypothesis.get("evidence_count", 0),
            sample_quotes=hypothesis.get("samples", [])[:5],
            subreddits=[hypothesis.get("source_topic", "")],
            generated_at=datetime.now().isoformat()
        )

        client = self._get_llm_client()
        if not client:
            return opportunity

        # Critical evaluation prompt
        eval_prompt = f"""You are a harsh, skeptical marketing critic. Evaluate this landing page opportunity:

TARGET AUDIENCE: {opportunity.target_audience}
CORE PAIN: {opportunity.core_pain}
TRANSFORMATION PROMISE: {opportunity.transformation_promise}
HEADLINE: {opportunity.title}
EVIDENCE: {opportunity.evidence_count} posts found

Sample quotes from audience:
{chr(10).join(opportunity.sample_quotes[:3])}

EVALUATE (respond in JSON):
{{
    "specificity_score": 0-10 (is the audience specific enough to target?),
    "evidence_strength": 0-10 (do the quotes really support this pain point?),
    "transformation_clarity": 0-10 (is the promised transformation clear and believable?),
    "market_size": 0-10 (is this audience large enough to matter?),
    "competition_gap": 0-10 (is there a gap in the market for this?),
    "devils_advocate": "Your harshest criticism of this opportunity",
    "fatal_flaws": ["List any deal-breakers that would make this fail"],
    "verdict": "GOLDEN" or "REJECT",
    "confidence": 0.0-1.0
}}

Be HARSH. Most opportunities should be rejected. Only truly compelling ones pass."""

        try:
            response = client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=0.3,
                max_tokens=800
            )

            result = self._clean_llm_response(response.choices[0].message.content)

            # Parse evaluation
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                eval_data = json.loads(result[start:end])

                opportunity.specificity_score = float(eval_data.get("specificity_score", 0))
                opportunity.evidence_strength = float(eval_data.get("evidence_strength", 0))
                opportunity.transformation_clarity = float(eval_data.get("transformation_clarity", 0))
                opportunity.market_size_indicator = float(eval_data.get("market_size", 0))
                opportunity.competition_gap = float(eval_data.get("competition_gap", 0))
                opportunity.devils_advocate = eval_data.get("devils_advocate", "")
                opportunity.fatal_flaws = eval_data.get("fatal_flaws", [])
                opportunity.confidence = float(eval_data.get("confidence", 0))

                # Determine if golden
                is_golden = (
                    eval_data.get("verdict") == "GOLDEN" and
                    opportunity.evidence_count >= self.MIN_EVIDENCE_COUNT and
                    opportunity.specificity_score >= self.MIN_SPECIFICITY and
                    opportunity.evidence_strength >= self.MIN_EVIDENCE_STRENGTH and
                    opportunity.transformation_clarity >= self.MIN_TRANSFORMATION_CLARITY and
                    opportunity.confidence >= self.MIN_OVERALL_CONFIDENCE and
                    len(opportunity.fatal_flaws) == 0
                )
                opportunity.is_golden = is_golden

        except Exception as e:
            self.logger.debug(f"Error evaluating: {e}")

        return opportunity

    def save_opportunity(self, opp: Opportunity):
        """Save opportunity to appropriate folder"""
        if opp.is_golden:
            folder = self.opportunities_path / "golden"
        else:
            folder = self.opportunities_path / "rejected"

        filepath = folder / f"{opp.id}.json"
        with open(filepath, 'w') as f:
            json.dump(asdict(opp), f, indent=2)

        self.existing_ids.add(opp.id)

    def generate_alert(self, opp: Opportunity) -> str:
        """Generate alert message for golden opportunity"""
        alert = f"""
{'='*60}
GOLDEN OPPORTUNITY FOUND
{'='*60}

ID: {opp.id}
Found: {opp.generated_at}

HEADLINE: {opp.title}

TARGET: {opp.target_audience}

CORE PAIN: {opp.core_pain}

TRANSFORMATION: {opp.transformation_promise}

EVIDENCE: {opp.evidence_count} posts from r/{', r/'.join(opp.subreddits)}

SCORES:
  Specificity:    {opp.specificity_score}/10
  Evidence:       {opp.evidence_strength}/10
  Transformation: {opp.transformation_clarity}/10
  Market Size:    {opp.market_size_indicator}/10
  Competition Gap:{opp.competition_gap}/10

CONFIDENCE: {opp.confidence:.0%}

{'='*60}
"""
        return alert

    def run_once(self) -> List[Opportunity]:
        """Run one cycle of opportunity scouting"""
        self.logger.info("Starting opportunity scout cycle...")

        # 1. Find pain clusters
        self.logger.info("Analyzing pain clusters...")
        clusters = self.find_pain_clusters()
        self.logger.info(f"Found {len(clusters)} significant clusters")

        if not clusters:
            self.logger.warning("No clusters found")
            return []

        # 2. Generate hypotheses
        self.logger.info("Generating opportunity hypotheses...")
        hypotheses = self.generate_opportunity_hypotheses(clusters)
        self.logger.info(f"Generated {len(hypotheses)} hypotheses")

        # 3. Evaluate each (harshly)
        golden = []
        rejected = 0

        for hyp in hypotheses:
            opp = self.evaluate_opportunity(hyp)
            if opp is None:
                continue  # Already processed

            self.save_opportunity(opp)

            if opp.is_golden:
                golden.append(opp)
                self.logger.info(f"GOLDEN: {opp.title[:50]}...")
                print(self.generate_alert(opp))
            else:
                rejected += 1
                self.logger.debug(f"Rejected: {opp.title[:50]}...")

            time.sleep(0.5)

        self.logger.info(f"Cycle complete: {len(golden)} golden, {rejected} rejected")

        # Save summary
        if golden:
            summary_file = self.opportunities_path / f"golden_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
            with open(summary_file, 'w') as f:
                f.write(f"# Golden Opportunities - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                for opp in golden:
                    f.write(self.generate_alert(opp))
                    f.write("\n\n")

        return golden

    def run_continuous(self, interval_hours: int = 6):
        """Run continuously, checking every N hours"""
        self.logger.info(f"Starting continuous mode (interval: {interval_hours}h)")

        while True:
            try:
                golden = self.run_once()

                if golden:
                    self.logger.info(f"Found {len(golden)} golden opportunities!")
                else:
                    self.logger.info("No golden opportunities this cycle")

                self.logger.info(f"Sleeping {interval_hours} hours...")
                time.sleep(interval_hours * 3600)

            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in cycle: {e}")
                time.sleep(300)  # Wait 5 min on error


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Golden Opportunity Scout")
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=6, help='Hours between cycles (default: 6)')
    parser.add_argument('--storage', type=str, default="/Volumes/Satechi4TB/pain_points")

    args = parser.parse_args()

    scout = GoldenOpportunityScout(storage_path=args.storage)

    if args.once:
        scout.run_once()
    else:
        scout.run_continuous(interval_hours=args.interval)


if __name__ == "__main__":
    main()
