#!/usr/bin/env python3
"""
Fresh Pain Points Crawler - Real-Time Trend Detection

Companion to Goldminer V4 (historical archive).
This crawler focuses on the LAST 30 DAYS for:
- Fresh content that's happening NOW
- Trend detection (what's rising/falling vs. baseline)
- Spike alerts when topics surge
- Daily enrichment with LLM analysis

Storage: /Volumes/Satechi4TB/pain_points/fresh/
Runs: Daily (cron or manual)
"""

import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
class FreshPainPoint:
    """Pain point from fresh/recent content"""
    content: str
    source_url: str
    source_platform: str
    topic: str
    subreddit: str
    authenticity_score: float
    suffering_score: float  # 1-10 scale for intensity
    suffering_indicators: List[str]
    post_created_utc: int  # When the post was actually created
    crawled_at: int  # When we found it
    metadata: Dict = field(default_factory=dict)
    llm_analysis: Optional[Dict] = None


@dataclass
class TrendAlert:
    """Alert when a topic spikes"""
    topic: str
    spike_factor: float  # How much above baseline (e.g., 2.5x)
    current_count: int
    baseline_count: float
    sample_posts: List[str]
    detected_at: str


class FreshPainCrawler:
    """
    Fresh content crawler with trend detection.

    Philosophy: What's happening NOW that we should pay attention to?
    While Goldminer archives eternal suffering, we track the pulse.
    """

    # Comprehensive subreddit coverage
    SUBREDDITS = [
        # Core mental health
        "depression", "Anxiety", "lonely", "socialanxiety",
        "mentalhealth", "BPD", "ADHD", "OCD", "dpdr", "CPTSD",
        "bipolar", "schizophrenia", "HealthAnxiety", "PanicAttack",
        "AVPD", "ptsd", "autism", "aspergirls",

        # Relationship dynamics
        "relationship_advice", "BreakUps", "Divorce", "survivinginfidelity",
        "DeadBedrooms", "ExNoContact", "Codependency", "NarcissisticSpouses",
        "abusiverelationships", "limerence",

        # Identity and meaning
        "Existential_crisis", "findapath", "quarterlifecrisis", "midlifecrisis",
        "selfimprovement", "DecidingToBeBetter", "getdisciplined",

        # Family and parenting
        "raisedbynarcissists", "emotionalneglect", "regretfulparents",
        "breakingmom", "SingleParents", "infertility", "Miscarriage",

        # Grief and loss
        "grief", "widowers", "ForeverAlone", "babyloss", "lastimages",

        # Addiction and recovery
        "addiction", "stopdrinking", "pornfree", "leaves",

        # Financial and life stability
        "povertyfinance", "homeless", "almosthomeless",

        # Chronic conditions
        "ChronicPain", "ChronicIllness", "Fibromyalgia", "CFS", "migraine",

        # Caregiver experience
        "CaregiverSupport", "dementia", "AgingParents",

        # Life transitions
        "IWantOut", "expats", "GradSchool", "PhD", "residency",
        "careerchange", "RedditForGrownups", "retirement",

        # Faith and worldview shifts
        "exmormon", "exchristian", "exmuslim",

        # Clarity-seeking (open to transformation)
        "Meditation", "spirituality", "awakened", "nonduality",
        "Stoicism", "simpleliving", "minimalism",

        # Emotional expression
        "TrueOffMyChest", "offmychest", "confession", "Vent",
        "unsentletters", "adultsurvivors",
    ]

    SUFFERING_MARKERS = {
        "desperation": [
            "i don't know what to do", "i'm lost", "i feel hopeless",
            "nothing works", "i've tried everything", "i'm stuck",
            "i can't take it anymore", "please help"
        ],
        "self_hatred": [
            "i hate myself", "i'm worthless", "i'm a failure",
            "i'm broken", "what's wrong with me"
        ],
        "isolation": [
            "no one understands", "i'm alone", "i have no one",
            "no friends", "no one cares", "lonely"
        ],
        "trapped_thinking": [
            "can't stop thinking", "overthinking", "stuck in my head",
            "spiraling", "intrusive thoughts"
        ],
        "loss_of_meaning": [
            "what's the point", "meaningless", "why bother",
            "nothing matters", "empty"
        ],
        "crisis": [
            "breaking point", "can't go on", "end it all",
            "give up", "no way out"
        ],
    }

    def __init__(
        self,
        storage_path: str = "/Volumes/Satechi4TB/pain_points",
        days_back: int = 30,
        baseline_days: int = 90,
    ):
        self.storage_path = Path(storage_path)
        self.fresh_path = self.storage_path / "fresh"
        self.days_back = days_back
        self.baseline_days = baseline_days

        # Create directories
        self.fresh_path.mkdir(parents=True, exist_ok=True)
        (self.fresh_path / "daily").mkdir(exist_ok=True)
        (self.fresh_path / "trends").mkdir(exist_ok=True)
        (self.fresh_path / "alerts").mkdir(exist_ok=True)

        # Setup logging
        log_file = self.fresh_path / f"fresh_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Load historical baseline from ChromaDB or enriched data
        self.baseline = self._load_baseline()

        # Deduplication: Load existing URLs from ChromaDB (robust, no separate file)
        self._indexed_urls = self._load_indexed_urls()
        self._session_urls: set = set()  # Track URLs within this session only

        self.logger.info("=" * 70)
        self.logger.info("FRESH PAIN CRAWLER - Real-Time Trend Detection")
        self.logger.info("=" * 70)
        self.logger.info(f"Looking back: {days_back} days")
        self.logger.info(f"Baseline period: {baseline_days} days")
        self.logger.info(f"Subreddits: {len(self.SUBREDDITS)}")
        self.logger.info(f"Baseline loaded: {sum(self.baseline.values())} historical posts")

    def _load_indexed_urls(self) -> set:
        """
        Load URLs already in ChromaDB index.

        This is the robust deduplication - we only skip posts that are
        already indexed, not posts from previous crawler runs.
        """
        indexed = set()

        if not CHROMADB_AVAILABLE:
            return indexed

        try:
            chroma_path = self.storage_path / "chromadb_index"
            if chroma_path.exists():
                client = chromadb.PersistentClient(
                    path=str(chroma_path),
                    settings=Settings(anonymized_telemetry=False)
                )
                collection = client.get_collection("pain_points")

                # Get all URLs from index
                results = collection.get(include=["metadatas"], limit=50000)
                for meta in results["metadatas"]:
                    url = meta.get("source_url", "")
                    if url:
                        indexed.add(url)

                self.logger.info(f"Loaded {len(indexed)} indexed URLs for deduplication")
        except Exception as e:
            self.logger.warning(f"Could not load indexed URLs: {e}")

        return indexed

    def _load_baseline(self) -> Dict[str, int]:
        """
        Load baseline topic counts from historical data.
        Used for trend detection (what's normal vs. what's spiking).
        """
        baseline = defaultdict(int)

        # Try to load from ChromaDB first
        if CHROMADB_AVAILABLE:
            try:
                chroma_path = self.storage_path / "chromadb_index"
                if chroma_path.exists():
                    client = chromadb.PersistentClient(
                        path=str(chroma_path),
                        settings=Settings(anonymized_telemetry=False)
                    )
                    collection = client.get_collection("pain_points")

                    # Get topic distribution
                    results = collection.get(include=["metadatas"], limit=15000)
                    for meta in results["metadatas"]:
                        topic = meta.get("topic", "unknown")
                        baseline[topic] += 1

                    self.logger.info(f"Loaded baseline from ChromaDB: {len(baseline)} topics")
                    return dict(baseline)
            except Exception as e:
                self.logger.warning(f"Could not load ChromaDB baseline: {e}")

        # Fallback: Load from enriched JSON
        enriched_file = self.storage_path / "ENRICHED_pain_points.json"
        if enriched_file.exists():
            try:
                with open(enriched_file) as f:
                    data = json.load(f)
                for record in data:
                    topic = record.get("topic", "unknown")
                    baseline[topic] += 1
                self.logger.info(f"Loaded baseline from JSON: {len(baseline)} topics")
            except Exception as e:
                self.logger.warning(f"Could not load JSON baseline: {e}")

        return dict(baseline)

    def calculate_suffering_score(self, text: str) -> Tuple[float, float, List[str]]:
        """
        Calculate both authenticity and suffering intensity.

        Returns: (authenticity_score, suffering_score, indicators)
        """
        text_lower = text.lower()
        detected = []
        category_hits = {}

        for category, markers in self.SUFFERING_MARKERS.items():
            matches = [m for m in markers if m in text_lower]
            if matches:
                detected.extend(matches)
                category_hits[category] = len(matches)

        if not category_hits:
            return 0.0, 0.0, []

        # Authenticity: breadth and depth of suffering markers
        breadth = len(category_hits) / len(self.SUFFERING_MARKERS)
        depth = sum(category_hits.values()) / sum(len(m) for m in self.SUFFERING_MARKERS.values())

        # Length and first-person bonuses
        length_bonus = min(0.15, len(text) / 5000)
        first_person = text_lower.count(" i ") + text_lower.count("i'm") + text_lower.count("i've")
        fp_bonus = min(0.1, first_person / 30)

        authenticity = min(1.0, breadth * 0.4 + depth * 0.4 + length_bonus + fp_bonus)

        # Suffering intensity (1-10 scale)
        # Based on: crisis markers, number of categories, emotional intensity words
        intensity_markers = ["can't take it", "end it", "breaking point", "give up", "no hope"]
        intensity_hits = sum(1 for m in intensity_markers if m in text_lower)

        base_score = len(category_hits) * 1.5  # Max ~9 from categories
        crisis_bonus = intensity_hits * 1.5    # Bonus for crisis language
        suffering_score = min(10.0, base_score + crisis_bonus)

        return authenticity, suffering_score, detected[:10]

    def fetch_subreddit_fresh(self, subreddit: str, sort: str = "new", limit: int = 100) -> List[FreshPainPoint]:
        """
        Fetch fresh posts from a subreddit.

        Args:
            subreddit: Subreddit name
            sort: "new", "hot", or "rising"
            limit: Max posts to fetch
        """
        points = []
        headers = {'User-Agent': 'FreshPainCrawler/1.0 (Research)'}

        try:
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 429:
                self.logger.warning(f"Rate limited on r/{subreddit}")
                time.sleep(60)
                return []

            if response.status_code != 200:
                return []

            data = response.json()
            posts = data.get('data', {}).get('children', [])

            cutoff_time = datetime.now() - timedelta(days=self.days_back)
            cutoff_ts = cutoff_time.timestamp()

            for post in posts:
                pd = post.get('data', {})

                # Skip old posts
                created_utc = pd.get('created_utc', 0)
                if created_utc < cutoff_ts:
                    continue

                # Skip if already indexed or seen this session
                permalink = pd.get('permalink', '')
                post_url = f"https://reddit.com{permalink}"
                if post_url in self._indexed_urls or post_url in self._session_urls:
                    continue

                # Get content
                title = pd.get('title', '')
                body = pd.get('selftext', '')
                content = f"{title}\n\n{body}".strip()

                # Skip short/removed posts
                if len(content) < 150 or body in ['[removed]', '[deleted]']:
                    continue

                # Calculate scores
                authenticity, suffering, indicators = self.calculate_suffering_score(content)

                # Threshold
                if authenticity < 0.15 or len(indicators) < 1:
                    continue

                self._session_urls.add(post_url)

                points.append(FreshPainPoint(
                    content=content[:5000],
                    source_url=post_url,
                    source_platform="reddit",
                    topic=subreddit,
                    subreddit=subreddit,
                    authenticity_score=authenticity,
                    suffering_score=suffering,
                    suffering_indicators=indicators,
                    post_created_utc=int(created_utc),
                    crawled_at=int(time.time()),
                    metadata={
                        "upvotes": pd.get('ups', 0),
                        "num_comments": pd.get('num_comments', 0),
                        "post_id": pd.get('id', ''),
                        "author": pd.get('author', ''),
                        "sort": sort,
                    }
                ))

        except Exception as e:
            self.logger.error(f"Error fetching r/{subreddit}: {e}")

        return points

    def crawl_all_fresh(self) -> List[FreshPainPoint]:
        """Crawl all subreddits for fresh content"""
        all_points = []

        for subreddit in self.SUBREDDITS:
            self.logger.info(f"Crawling r/{subreddit}...")

            # Fetch from multiple sorts for comprehensive coverage
            for sort in ["new", "hot"]:
                points = self.fetch_subreddit_fresh(subreddit, sort=sort, limit=50)
                all_points.extend(points)
                time.sleep(1)  # Rate limiting

            time.sleep(2)  # Between subreddits

        self.logger.info(f"Total fresh points: {len(all_points)}")
        return all_points

    def detect_trends(self, fresh_points: List[FreshPainPoint]) -> Tuple[Dict, List[TrendAlert]]:
        """
        Detect trends by comparing fresh data to baseline.

        Returns:
            - trend_data: Dict with topic trends
            - alerts: List of TrendAlert for significant spikes
        """
        # Count topics in fresh data
        fresh_counts = Counter(p.topic for p in fresh_points)

        # Calculate baseline average per topic (normalize by time period)
        baseline_factor = self.days_back / self.baseline_days

        trends = {}
        alerts = []

        for topic, fresh_count in fresh_counts.items():
            baseline_count = self.baseline.get(topic, 0)
            expected = baseline_count * baseline_factor

            if expected > 0:
                spike_factor = fresh_count / expected
            else:
                spike_factor = float(fresh_count) if fresh_count > 5 else 1.0

            trends[topic] = {
                "fresh_count": fresh_count,
                "baseline_count": baseline_count,
                "expected_count": round(expected, 1),
                "spike_factor": round(spike_factor, 2),
                "trend": "rising" if spike_factor > 1.5 else "falling" if spike_factor < 0.7 else "stable"
            }

            # Alert on significant spikes (>2x expected)
            if spike_factor >= 2.0 and fresh_count >= 5:
                sample_posts = [
                    p.content[:200] for p in fresh_points
                    if p.topic == topic
                ][:3]

                alerts.append(TrendAlert(
                    topic=topic,
                    spike_factor=round(spike_factor, 2),
                    current_count=fresh_count,
                    baseline_count=round(expected, 1),
                    sample_posts=sample_posts,
                    detected_at=datetime.now().isoformat()
                ))

        # Sort trends by spike factor
        trends = dict(sorted(trends.items(), key=lambda x: x[1]["spike_factor"], reverse=True))

        return trends, alerts

    def enrich_with_llm(self, points: List[FreshPainPoint], batch_size: int = 20) -> List[FreshPainPoint]:
        """
        Enrich pain points with LLM analysis.

        Adds structured analysis: core_issue, emotional_state, intervention_opportunity
        """
        if not OpenAI:
            self.logger.warning("OpenAI not available for enrichment")
            return points

        # Sort by suffering score, enrich top ones
        sorted_points = sorted(points, key=lambda x: x.suffering_score, reverse=True)
        to_enrich = sorted_points[:batch_size]

        try:
            client = OpenAI(
                api_key="not-needed",
                base_url="http://localhost:1234/v1",
                timeout=60.0
            )

            for point in to_enrich:
                prompt = f"""Analyze this pain point post (suffering score: {point.suffering_score}/10):

"{point.content[:1500]}"

Respond in JSON format:
{{
    "core_issue": "The underlying problem (not surface symptoms)",
    "emotional_state": "Primary emotion(s) detected",
    "thinking_pattern": "What thinking trap are they stuck in?",
    "intervention_opportunity": "How could this person be helped?",
    "urgency": "low/medium/high/critical"
}}"""

                try:
                    response = client.chat.completions.create(
                        model="vcoder-120b-1.0-hi-mlx",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=500
                    )

                    result = response.choices[0].message.content

                    # Strip thinking tags if present
                    if "</think>" in result:
                        result = result.split("</think>")[-1].strip()

                    # Parse JSON
                    try:
                        # Find JSON in response
                        start = result.find('{')
                        end = result.rfind('}') + 1
                        if start >= 0 and end > start:
                            analysis = json.loads(result[start:end])
                            point.llm_analysis = analysis
                    except json.JSONDecodeError:
                        point.llm_analysis = {"raw": result[:500]}

                except Exception as e:
                    self.logger.debug(f"LLM enrichment error: {e}")

                time.sleep(0.5)  # Rate limiting

        except Exception as e:
            self.logger.error(f"LLM client error: {e}")

        return points

    def generate_trend_report(self, trends: Dict, alerts: List[TrendAlert], points: List[FreshPainPoint]) -> str:
        """Generate human-readable trend report"""
        report = []
        report.append("# Fresh Pain Points - Trend Report")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**Period:** Last {self.days_back} days")
        report.append(f"**Total Fresh Posts:** {len(points)}")
        report.append("")

        # Alerts
        if alerts:
            report.append("## ALERTS - Significant Spikes")
            report.append("")
            for alert in sorted(alerts, key=lambda x: x.spike_factor, reverse=True):
                report.append(f"### r/{alert.topic} - {alert.spike_factor}x baseline")
                report.append(f"- Current: {alert.current_count} posts")
                report.append(f"- Expected: {alert.baseline_count} posts")
                report.append(f"- Sample: \"{alert.sample_posts[0][:100]}...\"" if alert.sample_posts else "")
                report.append("")

        # Rising topics
        rising = [(t, d) for t, d in trends.items() if d["trend"] == "rising"]
        if rising:
            report.append("## Rising Topics")
            for topic, data in rising[:10]:
                report.append(f"- **r/{topic}**: {data['spike_factor']}x ({data['fresh_count']} posts)")
            report.append("")

        # Stable high-volume
        stable = [(t, d) for t, d in trends.items() if d["trend"] == "stable" and d["fresh_count"] >= 10]
        if stable:
            report.append("## Stable High-Volume")
            for topic, data in sorted(stable, key=lambda x: x[1]["fresh_count"], reverse=True)[:10]:
                report.append(f"- r/{topic}: {data['fresh_count']} posts")
            report.append("")

        # High suffering posts
        high_suffering = [p for p in points if p.suffering_score >= 8]
        if high_suffering:
            report.append("## High Suffering Posts (8+/10)")
            for p in sorted(high_suffering, key=lambda x: x.suffering_score, reverse=True)[:5]:
                report.append(f"### [{p.suffering_score}/10] r/{p.subreddit}")
                report.append(f"> {p.content[:300]}...")
                if p.llm_analysis and isinstance(p.llm_analysis, dict):
                    report.append(f"- **Core Issue:** {p.llm_analysis.get('core_issue', 'N/A')}")
                    report.append(f"- **Urgency:** {p.llm_analysis.get('urgency', 'N/A')}")
                report.append("")

        return "\n".join(report)

    def save_results(self, points: List[FreshPainPoint], trends: Dict, alerts: List[TrendAlert], report: str):
        """Save all results"""
        timestamp = datetime.now().strftime("%Y%m%d")

        # Save fresh points
        points_file = self.fresh_path / "daily" / f"fresh_{timestamp}.json"
        with open(points_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in points], f, indent=2, ensure_ascii=False)

        # Save trends
        trends_file = self.fresh_path / "trends" / f"trends_{timestamp}.json"
        with open(trends_file, 'w') as f:
            json.dump(trends, f, indent=2)

        # Save alerts
        if alerts:
            alerts_file = self.fresh_path / "alerts" / f"alerts_{timestamp}.json"
            with open(alerts_file, 'w') as f:
                json.dump([asdict(a) for a in alerts], f, indent=2)

        # Save report
        report_file = self.fresh_path / f"trend_report_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report)

        # No need to save seen_urls - deduplication is against ChromaDB index

        self.logger.info(f"Results saved:")
        self.logger.info(f"  - {points_file}")
        self.logger.info(f"  - {trends_file}")
        self.logger.info(f"  - {report_file}")

    def add_to_chromadb(self, points: List[FreshPainPoint]):
        """Add fresh points to ChromaDB for unified search"""
        if not CHROMADB_AVAILABLE:
            self.logger.warning("ChromaDB not available")
            return

        try:
            chroma_path = self.storage_path / "chromadb_index"
            client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )

            collection = client.get_collection("pain_points")

            # Prepare batch
            ids = []
            documents = []
            metadatas = []

            for i, p in enumerate(points):
                doc_id = f"fresh_{datetime.now().strftime('%Y%m%d')}_{i}"

                ids.append(doc_id)
                documents.append(p.content[:10000])
                metadatas.append({
                    "source_platform": p.source_platform,
                    "topic": p.topic,
                    "source_url": p.source_url[:500],
                    "authenticity_score": p.authenticity_score,
                    "suffering_score": p.suffering_score,
                    "created_at": p.post_created_utc,
                    "is_fresh": True,
                })

            if ids:
                collection.add(ids=ids, documents=documents, metadatas=metadatas)
                self.logger.info(f"Added {len(ids)} fresh points to ChromaDB")

        except Exception as e:
            self.logger.error(f"ChromaDB error: {e}")

    def run(self, enrich: bool = True, add_to_index: bool = True):
        """
        Main entry point - run the fresh crawler.

        Args:
            enrich: Whether to enrich with LLM analysis
            add_to_index: Whether to add to ChromaDB
        """
        self.logger.info("Starting fresh pain crawl...")

        # 1. Crawl all fresh content
        points = self.crawl_all_fresh()

        if not points:
            self.logger.warning("No fresh points found")
            return

        # 2. Enrich with LLM
        if enrich:
            self.logger.info("Enriching with LLM analysis...")
            points = self.enrich_with_llm(points)

        # 3. Detect trends
        self.logger.info("Detecting trends...")
        trends, alerts = self.detect_trends(points)

        # 4. Generate report
        report = self.generate_trend_report(trends, alerts, points)

        # 5. Save results
        self.save_results(points, trends, alerts, report)

        # 6. Add to ChromaDB
        if add_to_index:
            self.add_to_chromadb(points)

        # 7. Print summary
        self.logger.info("\n" + "=" * 70)
        self.logger.info("CRAWL COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"Fresh points: {len(points)}")
        self.logger.info(f"Alerts: {len(alerts)}")

        if alerts:
            self.logger.info("\nSPIKE ALERTS:")
            for alert in alerts[:5]:
                self.logger.info(f"  - r/{alert.topic}: {alert.spike_factor}x baseline")

        # Print report to console
        print("\n" + report)

        return len(points)

    def run_continuous(self, interval_minutes: int = 30, enrich: bool = True):
        """
        Run continuously until no new content is found for 3 cycles.

        Args:
            interval_minutes: Minutes between cycles
            enrich: Whether to enrich with LLM
        """
        self.logger.info(f"Starting continuous mode (interval: {interval_minutes}min)")
        self.logger.info("Will stop after 3 consecutive cycles with no new data")

        zero_cycles = 0
        total_collected = 0
        cycle = 0

        while zero_cycles < 3:
            cycle += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"CYCLE {cycle}")
            self.logger.info(f"{'='*60}")

            try:
                count = self.run(enrich=enrich, add_to_index=True)

                if count and count > 0:
                    total_collected += count
                    zero_cycles = 0
                    self.logger.info(f"Collected {count} new points (total: {total_collected})")
                else:
                    zero_cycles += 1
                    self.logger.info(f"No new points ({zero_cycles}/3 empty cycles)")

                if zero_cycles < 3:
                    self.logger.info(f"Waiting {interval_minutes} minutes...")
                    time.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                self.logger.info("Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in cycle: {e}")
                time.sleep(60)

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"FARMING COMPLETE")
        self.logger.info(f"Total collected: {total_collected}")
        self.logger.info(f"{'='*60}")


def main():
    """Run the fresh crawler"""
    import argparse

    parser = argparse.ArgumentParser(description="Fresh Pain Points Crawler")
    parser.add_argument('--days', type=int, default=30, help='Days to look back (default: 30)')
    parser.add_argument('--no-enrich', action='store_true', help='Skip LLM enrichment')
    parser.add_argument('--no-index', action='store_true', help='Skip ChromaDB indexing')
    parser.add_argument('--storage', type=str, default="/Volumes/Satechi4TB/pain_points")
    parser.add_argument('--continuous', action='store_true', help='Run continuously until exhausted')
    parser.add_argument('--interval', type=int, default=30, help='Minutes between cycles (default: 30)')

    args = parser.parse_args()

    crawler = FreshPainCrawler(
        storage_path=args.storage,
        days_back=args.days
    )

    if args.continuous:
        crawler.run_continuous(
            interval_minutes=args.interval,
            enrich=not args.no_enrich
        )
    else:
        crawler.run(
            enrich=not args.no_enrich,
            add_to_index=not args.no_index
        )


if __name__ == "__main__":
    main()
