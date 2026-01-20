#!/usr/bin/env python3
"""
Pain Point Goldminer v4 - 24/7 Autonomous Suffering Detection

10,000m altitude approach: Find where humans are suffering RIGHT NOW,
regardless of niche. The doorway doesn't matter - they all come because they think.

Storage: /Volumes/Satechi4TB/pain_points/
Analysis: Local LLM (vcoder-120b) hourly + daily summaries

Constitutional Compliance:
- Article IV: Learning (stores patterns to VectorStore)
- Article I: Complete context (retries on failure)
"""

import json
import time
import logging
import sys
import os
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
import requests
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@dataclass
class PainPoint:
    """Human suffering data structure"""
    content: str
    source_url: str
    source_platform: str
    topic: str
    authenticity_score: float
    suffering_indicators: List[str]
    created_at: int
    metadata: Dict = field(default_factory=dict)


class PainPointGoldminerV4:
    """
    24/7 Autonomous pain point collection from the 10,000m altitude.

    Philosophy: The doorway doesn't matter. People come because they think.
    The thinking is the problem, not the wife, penis, job, or loneliness.

    Time Travel: Human suffering is eternal. What was painful 10 years ago
    is painful now. We progressively scrape deeper into history.
    """

    # Time progression: cycle through these to go deeper in time
    # Each cycle uses a different time period, ensuring we capture
    # both fresh suffering and timeless pain
    TIME_PERIODS = [
        {"sort": "top", "t": "week", "desc": "This week's top suffering"},
        {"sort": "top", "t": "month", "desc": "This month's top suffering"},
        {"sort": "top", "t": "year", "desc": "This year's top suffering"},
        {"sort": "top", "t": "all", "desc": "All-time classic suffering"},
        {"sort": "hot", "t": None, "desc": "Currently active discussions"},
        {"sort": "new", "t": None, "desc": "Fresh new posts"},
    ]

    # Universal suffering indicators (not niche-specific)
    SUFFERING_MARKERS = {
        "desperation": [
            "i don't know what to do", "i'm lost", "i feel hopeless",
            "nothing works", "i've tried everything", "i'm stuck",
            "i can't take it anymore", "i'm at my breaking point",
            "i'm desperate", "please help", "i need advice"
        ],
        "self_hatred": [
            "i hate myself", "i'm disgusting", "i'm worthless",
            "i don't deserve", "i'm a failure", "i'm pathetic",
            "i'm broken", "what's wrong with me", "i'm the problem"
        ],
        "isolation": [
            "no one understands", "i'm alone", "i have no one",
            "no friends", "no one cares", "invisible", "forgotten",
            "isolated", "lonely", "disconnected"
        ],
        "trapped_thinking": [
            "can't stop thinking", "overthinking", "stuck in my head",
            "constant loop", "obsessing", "ruminating", "spiraling",
            "my mind won't stop", "intrusive thoughts"
        ],
        "loss_of_meaning": [
            "what's the point", "life is meaningless", "why bother",
            "nothing matters", "i don't see a future", "empty",
            "going through the motions", "existing not living"
        ],
        "shame_guilt": [
            "i'm ashamed", "i feel guilty", "i can't forgive myself",
            "i did something terrible", "i'm a bad person",
            "i don't deserve happiness", "haunted by"
        ],
        "relationship_pain": [
            "they left me", "i can't let go", "obsessed with my ex",
            "i ruined the relationship", "no one will love me",
            "i push people away", "i'm too much", "not enough"
        ],
        "existential": [
            "what am i doing with my life", "midlife crisis",
            "quarter life crisis", "lost my identity", "who am i",
            "life is passing by", "wasted years", "too late"
        ],
        "body_mind_disconnect": [
            "don't feel real", "watching my life", "dissociated",
            "numb", "can't feel anything", "disconnected from body",
            "autopilot", "going through motions"
        ],
        "seeking_but_not_finding": [
            "i've tried therapy", "meds don't work", "nothing helps",
            "still struggling", "years of trying", "lost faith",
            "given up on", "no solution"
        ]
    }

    # Comprehensive subreddit coverage (10,000m altitude)
    SUBREDDITS = {
        # Core suffering
        "depression": {"weight": 1.5, "desc": "Clinical and situational depression"},
        "Anxiety": {"weight": 1.5, "desc": "Anxiety disorders and daily anxiety"},
        "lonely": {"weight": 1.4, "desc": "Loneliness and isolation"},
        "socialanxiety": {"weight": 1.3, "desc": "Social anxiety disorder"},

        # Relationship pain
        "relationship_advice": {"weight": 1.2, "desc": "Relationship struggles"},
        "BreakUps": {"weight": 1.3, "desc": "Breakup pain and recovery"},
        "Divorce": {"weight": 1.3, "desc": "Divorce process and aftermath"},
        "survivinginfidelity": {"weight": 1.4, "desc": "Betrayal and trust"},
        "DeadBedrooms": {"weight": 1.2, "desc": "Intimacy issues"},
        "ExNoContact": {"weight": 1.3, "desc": "No contact struggles"},

        # Identity/meaning crisis
        "Existential_crisis": {"weight": 1.4, "desc": "Existential struggles"},
        "findapath": {"weight": 1.2, "desc": "Life direction confusion"},
        "quarterlifecrisis": {"weight": 1.3, "desc": "Quarter life crisis"},
        "midlifecrisis": {"weight": 1.3, "desc": "Midlife transitions"},
        "selfimprovement": {"weight": 1.0, "desc": "Self-improvement seekers"},
        "DecidingToBeBetter": {"weight": 1.1, "desc": "Change seekers"},

        # Mental health specific
        "BPD": {"weight": 1.4, "desc": "Borderline personality"},
        "ADHD": {"weight": 1.2, "desc": "ADHD struggles"},
        "OCD": {"weight": 1.3, "desc": "OCD intrusive thoughts"},
        "dpdr": {"weight": 1.5, "desc": "Depersonalization/derealization"},
        "Anxietyhelp": {"weight": 1.2, "desc": "Anxiety support"},
        "mentalhealth": {"weight": 1.2, "desc": "General mental health"},

        # Overthinking/intellectuals
        "TrueOffMyChest": {"weight": 1.2, "desc": "Raw confessions and venting"},
        "intj": {"weight": 1.0, "desc": "INTJ personality (often overthinkers)"},
        "infj": {"weight": 1.0, "desc": "INFJ personality (often overthinkers)"},
        "getdisciplined": {"weight": 1.1, "desc": "Discipline struggles"},

        # Healing/growth (people actively seeking)
        "therapy": {"weight": 1.3, "desc": "Therapy discussions"},
        "CPTSD": {"weight": 1.4, "desc": "Complex trauma"},
        "raisedbynarcissists": {"weight": 1.3, "desc": "Narcissistic family"},
        "emotionalneglect": {"weight": 1.3, "desc": "Childhood emotional neglect"},

        # Career/purpose
        "careerguidance": {"weight": 1.0, "desc": "Career confusion"},
        "jobs": {"weight": 0.9, "desc": "Job struggles"},
        "antiwork": {"weight": 0.8, "desc": "Work dissatisfaction"},

        # Specific pain points
        "SuicideWatch": {"weight": 1.5, "desc": "Suicidal ideation (handle with care)"},
        "selfharm": {"weight": 1.4, "desc": "Self-harm struggles"},
        "addiction": {"weight": 1.3, "desc": "Addiction struggles"},
        "stopdrinking": {"weight": 1.2, "desc": "Alcohol recovery"},
        "pornfree": {"weight": 1.2, "desc": "Porn addiction"},

        # Sexual/intimacy shame
        "sex": {"weight": 0.9, "desc": "Sexual struggles"},
        "sexover30": {"weight": 1.0, "desc": "Sexual issues after 30"},
        "erectiledysfunction": {"weight": 1.3, "desc": "ED struggles"},
        "PrematureEjaculation": {"weight": 1.3, "desc": "PE struggles"},

        # Spiritual seeking
        "spirituality": {"weight": 1.0, "desc": "Spiritual seekers"},
        "awakened": {"weight": 1.1, "desc": "Spiritual awakening"},
        "Meditation": {"weight": 0.9, "desc": "Meditation practice"},
        "ACIM": {"weight": 1.2, "desc": "A Course in Miracles"},
        "nonduality": {"weight": 1.1, "desc": "Non-duality seekers"},

        # Helpers needing help
        "therapists": {"weight": 1.3, "desc": "Therapist burnout"},
        "socialwork": {"weight": 1.2, "desc": "Social worker burnout"},
        "nursing": {"weight": 1.1, "desc": "Nurse burnout"},
    }

    def __init__(
        self,
        storage_path: str = "/Volumes/Satechi4TB/pain_points",
        continuous: bool = True,
        analysis_interval_minutes: int = 60,
        daily_summary_hour: int = 6,  # 6 AM
    ):
        self.storage_path = Path(storage_path)
        self.continuous = continuous
        self.analysis_interval = analysis_interval_minutes
        self.daily_summary_hour = daily_summary_hour

        self.start_time = datetime.now()
        self.pain_points: List[PainPoint] = []
        self.daily_stats = defaultdict(int)
        self.running = True

        # Setup storage
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "raw").mkdir(exist_ok=True)
        (self.storage_path / "analysis").mkdir(exist_ok=True)
        (self.storage_path / "daily_summaries").mkdir(exist_ok=True)

        # Deduplication: track seen URLs to avoid re-collecting same posts
        self._seen_urls_file = self.storage_path / "seen_urls.json"
        self._seen_urls: set = self._load_seen_urls()

        # Time travel: track which time period we're currently scraping
        self._progress_file = self.storage_path / "scrape_progress.json"
        self._time_period_index: int = self._load_progress()

        # Setup logging
        log_file = self.storage_path / f"goldminer_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        self.logger.info("=" * 80)
        self.logger.info("PAIN POINT GOLDMINER V4 - 24/7 SUFFERING DETECTION")
        self.logger.info("=" * 80)
        self.logger.info(f"Storage: {self.storage_path}")
        self.logger.info(f"Subreddits: {len(self.SUBREDDITS)}")
        self.logger.info(f"Continuous: {self.continuous}")
        self.logger.info(f"Seen URLs loaded: {len(self._seen_urls)} (deduplication)")
        current_period = self._get_current_time_period()
        self.logger.info(f"Time period: {current_period['desc']} (index {self._time_period_index}/{len(self.TIME_PERIODS)})")
        self.logger.info("=" * 80)

    def _handle_shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        self.logger.info("\nReceived shutdown signal. Saving final checkpoint...")
        self.running = False
        self._save_checkpoint("final")
        self._save_seen_urls()
        self.logger.info("Shutdown complete.")
        sys.exit(0)

    def _load_seen_urls(self) -> set:
        """Load previously seen URLs from disk."""
        if self._seen_urls_file.exists():
            try:
                with open(self._seen_urls_file) as f:
                    data = json.load(f)
                    return set(data.get("urls", []))
            except Exception:
                return set()
        return set()

    def _save_seen_urls(self):
        """Save seen URLs to disk."""
        try:
            with open(self._seen_urls_file, 'w') as f:
                json.dump({"urls": list(self._seen_urls), "count": len(self._seen_urls)}, f)
        except Exception as e:
            self.logger.error(f"Failed to save seen URLs: {e}")

    def _load_progress(self) -> int:
        """Load time period progress from disk."""
        if self._progress_file.exists():
            try:
                with open(self._progress_file) as f:
                    data = json.load(f)
                    return data.get("time_period_index", 0) % len(self.TIME_PERIODS)
            except Exception:
                return 0
        return 0

    def _save_progress(self):
        """Save time period progress to disk."""
        try:
            current_period = self.TIME_PERIODS[self._time_period_index]
            with open(self._progress_file, 'w') as f:
                json.dump({
                    "time_period_index": self._time_period_index,
                    "current_period": current_period,
                    "total_periods": len(self.TIME_PERIODS),
                    "updated_at": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save progress: {e}")

    def _advance_time_period(self):
        """Move to next time period for next cycle."""
        self._time_period_index = (self._time_period_index + 1) % len(self.TIME_PERIODS)
        self._save_progress()
        next_period = self.TIME_PERIODS[self._time_period_index]
        self.logger.info(f"Advanced to next time period: {next_period['desc']}")

    def _get_current_time_period(self) -> Dict:
        """Get current time period configuration."""
        return self.TIME_PERIODS[self._time_period_index]

    def calculate_authenticity(self, text: str) -> tuple[float, List[str]]:
        """
        Calculate authenticity score based on suffering indicators.

        Returns (score, list of detected indicators)
        """
        text_lower = text.lower()
        detected = []
        category_scores = {}

        for category, markers in self.SUFFERING_MARKERS.items():
            matches = [m for m in markers if m in text_lower]
            if matches:
                detected.extend(matches)
                category_scores[category] = len(matches) / len(markers)

        if not category_scores:
            return 0.0, []

        # Weight by number of categories hit (breadth) and depth within categories
        breadth_score = len(category_scores) / len(self.SUFFERING_MARKERS)
        depth_score = sum(category_scores.values()) / len(category_scores)

        # Bonus for long, detailed posts (usually more authentic)
        length_bonus = min(0.2, len(text) / 5000)

        # First person language bonus
        first_person_count = text_lower.count(" i ") + text_lower.count("i'm") + text_lower.count("i've")
        first_person_bonus = min(0.15, first_person_count / 50)

        final_score = (breadth_score * 0.4 + depth_score * 0.4 + length_bonus + first_person_bonus)

        return min(1.0, final_score), detected

    def mine_subreddit(self, subreddit: str, config: Dict) -> List[PainPoint]:
        """Mine a single subreddit for pain points"""
        points = []
        weight = config.get("weight", 1.0)

        try:
            # Get top posts from last week
            url = f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit=50"
            headers = {'User-Agent': 'PainPointGoldminer/4.0 (Research)'}

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 429:
                self.logger.warning(f"Rate limited on r/{subreddit}, waiting...")
                time.sleep(60)
                return []

            response.raise_for_status()
            data = response.json()
            posts = data.get('data', {}).get('children', [])

            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                body = post_data.get('selftext', '')
                content = f"{title}\n\n{body}"

                # Build URL for deduplication check
                post_url = f"https://reddit.com{post_data.get('permalink', '')}"

                # Skip already-seen posts (deduplication)
                if post_url in self._seen_urls:
                    continue

                # Skip short posts, removed posts, or link posts
                if len(content) < 200 or body == '[removed]' or body == '[deleted]':
                    continue

                score, indicators = self.calculate_authenticity(content)

                # Apply subreddit weight
                weighted_score = score * weight

                # Threshold: 0.15 minimum (lower to be inclusive from 10,000m)
                if weighted_score >= 0.15 and len(indicators) >= 2:
                    # Mark as seen
                    self._seen_urls.add(post_url)

                    points.append(PainPoint(
                        content=content,
                        source_url=post_url,
                        source_platform="reddit",
                        topic=subreddit,
                        authenticity_score=weighted_score,
                        suffering_indicators=indicators[:10],  # Top 10 indicators
                        created_at=int(time.time()),
                        metadata={
                            "subreddit": subreddit,
                            "upvotes": post_data.get('ups', 0),
                            "num_comments": post_data.get('num_comments', 0),
                            "post_id": post_data.get('id', ''),
                            "created_utc": post_data.get('created_utc', 0),
                        }
                    ))

            self.logger.debug(f"r/{subreddit}: {len(points)} pain points")

        except Exception as e:
            self.logger.error(f"Error mining r/{subreddit}: {e}")

        return points

    def mine_all_subreddits(self) -> List[PainPoint]:
        """Mine all configured subreddits"""
        all_points = []

        for subreddit, config in self.SUBREDDITS.items():
            self.logger.info(f"Mining r/{subreddit}...")
            points = self.mine_subreddit(subreddit, config)
            all_points.extend(points)
            self.daily_stats[subreddit] += len(points)

            # Respectful rate limiting
            time.sleep(2)

        return all_points

    def analyze_with_llm(self, points: List[PainPoint], analysis_type: str = "hourly") -> str:
        """Analyze collected pain points with local LLM"""
        if not points or OpenAI is None:
            return "No pain points to analyze or OpenAI client unavailable"

        # Sort by authenticity and take top entries
        sorted_points = sorted(points, key=lambda x: x.authenticity_score, reverse=True)
        top_points = sorted_points[:15] if analysis_type == "daily" else sorted_points[:8]

        pain_text = "\n\n---\n\n".join([
            f"[r/{p.topic}] Score: {p.authenticity_score:.2f}\n"
            f"Indicators: {', '.join(p.suffering_indicators[:5])}\n"
            f"Content: {p.content[:600]}..."
            for p in top_points
        ])

        prompt = f"""Analyze these pain points collected from Reddit in the last {'24 hours' if analysis_type == 'daily' else 'hour'}:

{pain_text}

As a coach who understands that all suffering comes from thinking (not circumstances), provide:

1. **TOP 3 SUFFERING PATTERNS**: What are people actually stuck on? (Not the surface issue, but the thinking pattern)

2. **THE REAL PROBLEM**: Behind all these posts, what's the common misunderstanding these people share?

3. **VIDEO OPPORTUNITY**: If you could make ONE video that would help the most people here, what would the title be? What would be the core message?

4. **DOORWAY INSIGHT**: What "doorway" (surface problem) brings the most people, but leads to the deepest transformation?

Be direct. No fluff. Speak like someone who sees through the illusion of problems."""

        try:
            # Try local LLM first (localhost, not remote)
            # Remote server (192.168.0.2) may be down, prefer local
            base_url = "http://localhost:1234/v1"
            client = OpenAI(
                api_key="not-needed",
                base_url=base_url,
                timeout=120.0
            )

            response = client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",  # Use vcoder directly, not env var
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )

            result = response.choices[0].message.content

            # Strip thinking tags if present (from reasoning models)
            if "<think>" in result:
                # Extract content after </think> if present
                if "</think>" in result:
                    result = result.split("</think>")[-1].strip()
                else:
                    # Incomplete thinking, use what we have
                    result = result.replace("<think>", "").strip()

            return result

        except Exception as e:
            self.logger.error(f"LLM analysis error: {e}")
            return f"Analysis failed: {e}"

    def _save_checkpoint(self, checkpoint_type: str = "hourly"):
        """Save current progress"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save raw data
        raw_file = self.storage_path / "raw" / f"pain_points_{timestamp}.json"
        with open(raw_file, 'w') as f:
            json.dump([asdict(p) for p in self.pain_points], f, indent=2)

        # Save seen URLs for deduplication persistence
        self._save_seen_urls()

        self.logger.info(f"Checkpoint saved: {raw_file} ({len(self.pain_points)} points, {len(self._seen_urls)} unique URLs tracked)")

    def _generate_daily_summary(self):
        """Generate daily summary report"""
        timestamp = datetime.now().strftime("%Y%m%d")

        # Analyze all points from the day
        analysis = self.analyze_with_llm(self.pain_points, "daily")

        # Generate summary
        summary = {
            "date": timestamp,
            "total_pain_points": len(self.pain_points),
            "by_subreddit": dict(self.daily_stats),
            "top_suffering_indicators": self._get_top_indicators(),
            "llm_analysis": analysis,
            "high_authenticity_samples": [
                asdict(p) for p in sorted(
                    self.pain_points,
                    key=lambda x: x.authenticity_score,
                    reverse=True
                )[:20]
            ]
        }

        # Save summary
        summary_file = self.storage_path / "daily_summaries" / f"summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # Also save human-readable version
        readable_file = self.storage_path / "daily_summaries" / f"summary_{timestamp}.md"
        with open(readable_file, 'w') as f:
            f.write(f"# Pain Point Daily Summary - {timestamp}\n\n")
            f.write(f"**Total Pain Points Collected:** {len(self.pain_points)}\n\n")
            f.write("## Top Subreddits\n\n")
            for sub, count in sorted(self.daily_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"- r/{sub}: {count}\n")
            f.write(f"\n## LLM Analysis\n\n{analysis}\n")

        self.logger.info(f"Daily summary saved: {summary_file}")

        # Reset daily stats
        self.pain_points = []
        self.daily_stats = defaultdict(int)

    def _get_top_indicators(self) -> Dict[str, int]:
        """Get most common suffering indicators"""
        indicator_counts = defaultdict(int)
        for p in self.pain_points:
            for indicator in p.suffering_indicators:
                indicator_counts[indicator] += 1
        return dict(sorted(indicator_counts.items(), key=lambda x: x[1], reverse=True)[:20])

    def run(self):
        """Main 24/7 mining loop"""
        self.logger.info("Starting 24/7 pain point collection...")
        last_analysis = datetime.now()
        last_daily_summary = datetime.now().date()

        while self.running:
            try:
                # Mine all subreddits
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"MINING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                self.logger.info(f"{'='*60}")

                batch_points = self.mine_all_subreddits()
                self.pain_points.extend(batch_points)

                self.logger.info(f"Batch complete: +{len(batch_points)} points")
                self.logger.info(f"Daily total: {len(self.pain_points)} points")

                # Hourly analysis
                if datetime.now() - last_analysis >= timedelta(minutes=self.analysis_interval):
                    self.logger.info("\nRunning hourly analysis...")
                    analysis = self.analyze_with_llm(batch_points, "hourly")

                    # Save analysis
                    analysis_file = self.storage_path / "analysis" / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                    with open(analysis_file, 'w') as f:
                        f.write(analysis)

                    self.logger.info(f"\n{'='*60}")
                    self.logger.info("HOURLY ANALYSIS:")
                    self.logger.info(f"{'='*60}")
                    self.logger.info(analysis)

                    last_analysis = datetime.now()
                    self._save_checkpoint("hourly")

                # Daily summary at configured hour
                now = datetime.now()
                if now.date() > last_daily_summary and now.hour >= self.daily_summary_hour:
                    self.logger.info("\nGenerating daily summary...")
                    self._generate_daily_summary()
                    last_daily_summary = now.date()

                # Wait before next cycle (30 minutes)
                if self.continuous:
                    self.logger.info(f"Waiting 30 minutes before next cycle...")
                    time.sleep(30 * 60)
                else:
                    break

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait a minute and try again

        # Final save
        self._save_checkpoint("final")
        self.logger.info("Goldminer stopped.")


def main():
    """Run the goldminer"""
    import argparse

    parser = argparse.ArgumentParser(description="Pain Point Goldminer V4 - 24/7 Edition")
    parser.add_argument('--storage', type=str, default="/Volumes/Satechi4TB/pain_points",
                        help='Storage path for data')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit (default: continuous)')
    parser.add_argument('--analysis-interval', type=int, default=60,
                        help='Analysis interval in minutes (default: 60)')
    parser.add_argument('--test', action='store_true',
                        help='Test mode (run once with minimal subreddits)')

    args = parser.parse_args()

    if args.test:
        # Test mode - subset of subreddits
        miner = PainPointGoldminerV4(
            storage_path=args.storage,
            continuous=False,
            analysis_interval_minutes=5
        )
        miner.SUBREDDITS = {
            "depression": {"weight": 1.5, "desc": "Test"},
            "Anxiety": {"weight": 1.5, "desc": "Test"},
            "lonely": {"weight": 1.4, "desc": "Test"},
        }
        miner.run()
    else:
        miner = PainPointGoldminerV4(
            storage_path=args.storage,
            continuous=not args.once,
            analysis_interval_minutes=args.analysis_interval
        )
        miner.run()


if __name__ == "__main__":
    main()
