#!/usr/bin/env python3
"""
Grand Slam Offer Miner - Hormozi-Style Opportunity Discovery

This is a PARALLEL system to the suffering database.
While the suffering DB captures victim language for copywriting,
this system finds actual business opportunities where people WILL PAY.

Philosophy (from $100M Offers):
- Find starving crowds with purchasing power
- Identify what they've tried that failed
- Discover their dream outcomes
- Build offers they feel dumb saying no to

Value Equation:
Value = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort)

Storage: /Volumes/Satechi4TB/pain_points/grand_slam/
"""

import json
import time
import logging
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict, field
from collections import Counter, defaultdict

import requests

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
class OfferSignal:
    """A signal indicating offer potential"""
    id: str
    content: str
    subreddit: str
    signal_type: str  # purchase_intent, failed_solution, dream_outcome, etc.
    url: str
    score: int
    created_utc: float
    extracted_at: str

    # Extracted elements
    dream_outcome: str = ""
    failed_solutions: List[str] = field(default_factory=list)
    willingness_to_pay: str = ""
    urgency_level: str = ""


@dataclass
class GrandSlamOffer:
    """A potential Grand Slam Offer"""
    id: str

    # The Offer
    headline: str
    target_market: str
    dream_outcome: str
    mechanism: str  # How it works (perceived likelihood)
    time_to_result: str
    effort_required: str

    # Value Stack
    core_offer: str
    bonuses: List[str] = field(default_factory=list)
    guarantee: str = ""
    scarcity: str = ""
    urgency: str = ""

    # Evidence
    signal_count: int = 0
    sample_signals: List[str] = field(default_factory=list)
    failed_solutions_mentioned: List[str] = field(default_factory=list)
    subreddits: List[str] = field(default_factory=list)

    # Hormozi Value Equation Scores (1-10)
    dream_outcome_score: float = 0.0
    perceived_likelihood_score: float = 0.0
    time_delay_score: float = 0.0  # Lower is better, inverted for final calc
    effort_score: float = 0.0  # Lower is better, inverted for final calc

    # Final evaluation
    value_score: float = 0.0  # Calculated from equation
    is_grand_slam: bool = False
    evaluation_notes: str = ""
    generated_at: str = ""


class GrandSlamMiner:
    """
    Mines Reddit for Grand Slam Offer opportunities.

    Different from the suffering miner - this looks for:
    - Purchase intent signals
    - Failed solution mentions
    - Dream outcome descriptions
    - Markets with proven spending
    """

    # HORMOZI MARKETS - where people actually spend money
    SUBREDDITS = [
        # B2B & Business (high WTP, clear ROI)
        "Entrepreneur", "startups", "smallbusiness", "freelance",
        "consulting", "agency", "SaaS", "ecommerce", "dropship",
        "juststart", "EntrepreneurRideAlong", "sweatystartup",

        # Wealth & Finance (proven spending)
        "Fire", "financialindependence", "fatFIRE", "leanfire",
        "realestateinvesting", "personalfinance", "sidehustle",
        "passive_income", "Bogleheads", "dividends",

        # Career & Skills (high income earners)
        "cscareerquestions", "ExperiencedDevs", "learnprogramming",
        "ProductManagement", "salesforce", "aws", "devops",
        "careerguidance", "jobs", "resumes", "interviews",

        # Health & Fitness (transformation market)
        "loseit", "Fitness", "bodybuilding", "running", "CrossFit",
        "nutrition", "MealPrepSunday", "intermittentfasting",
        "gainit", "StrongerByScience", "naturalbodybuilding",

        # Relationships (non-crisis, solution-seeking)
        "Marriage", "datingoverthirty", "datingoverforty",
        "Parenting", "Mommit", "daddit", "toddlers", "NewParents",

        # Skills & Learning (education market)
        "languagelearning", "writing", "graphic_design",
        "photography", "videography", "podcasting",

        # Home & DIY (proven purchasers)
        "HomeImprovement", "homeowners", "DIY", "woodworking",
        "gardening", "lawncare", "homeautomation",

        # Hobbies with High Spending
        "golf", "audiophile", "homelab", "MechanicalKeyboards",
        "espresso", "Watches", "churning",
    ]

    # Signals that indicate offer potential
    OFFER_SIGNALS = {
        "purchase_intent": [
            "would pay", "take my money", "worth the investment",
            "where can i buy", "is it worth it", "roi",
            "worth paying for", "happy to pay", "invest in",
            "best money i spent", "worth every penny",
        ],
        "failed_solutions": [
            "tried everything", "nothing works", "wasted money on",
            "disappointed with", "doesn't work", "gave up on",
            "failed with", "can't figure out", "struggling with",
            "been trying for years", "still can't",
        ],
        "dream_outcome": [
            "i just want to", "if only i could", "my goal is",
            "dream of", "wish i could", "finally be able to",
            "all i want is", "hoping to", "would love to",
            "ultimate goal", "end goal is",
        ],
        "urgency": [
            "need this now", "can't wait", "running out of time",
            "deadline", "asap", "urgent", "immediately",
            "before it's too late", "this week", "this month",
        ],
        "success_evidence": [
            "changed my life", "game changer", "finally works",
            "best decision", "life changing", "transformed",
            "breakthrough", "finally figured out", "cracked the code",
        ],
        "specific_problem": [
            "how do i", "what's the best way to", "anyone know how",
            "looking for advice on", "need help with",
            "can someone explain", "what am i doing wrong",
        ],
    }

    # Minimum thresholds for Grand Slam
    MIN_SIGNALS = 20
    MIN_VALUE_SCORE = 70.0  # Out of 100

    def __init__(
        self,
        storage_path: str = "/Volumes/Satechi4TB/pain_points",
        model_base_url: str = "http://localhost:1234/v1",
    ):
        self.storage_path = Path(storage_path)
        self.grand_slam_path = self.storage_path / "grand_slam"
        self.model_base_url = model_base_url

        # Create directories
        self.grand_slam_path.mkdir(parents=True, exist_ok=True)
        (self.grand_slam_path / "signals").mkdir(exist_ok=True)
        (self.grand_slam_path / "offers").mkdir(exist_ok=True)
        (self.grand_slam_path / "golden").mkdir(exist_ok=True)
        (self.grand_slam_path / "rejected").mkdir(exist_ok=True)

        # ChromaDB for offer signals (separate from suffering DB)
        self.chroma_path = self.grand_slam_path / "chromadb_offers"

        # Setup logging
        log_file = self.grand_slam_path / f"miner_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Load existing signal URLs to avoid duplicates
        self.indexed_urls = self._load_indexed_urls()

        self.logger.info("=" * 60)
        self.logger.info("GRAND SLAM OFFER MINER")
        self.logger.info("Hormozi-Style Opportunity Discovery")
        self.logger.info("=" * 60)
        self.logger.info(f"Subreddits: {len(self.SUBREDDITS)}")
        self.logger.info(f"Already indexed: {len(self.indexed_urls)} signals")

    def _load_indexed_urls(self) -> Set[str]:
        """Load URLs already indexed"""
        urls = set()
        if CHROMADB_AVAILABLE and self.chroma_path.exists():
            try:
                client = chromadb.PersistentClient(
                    path=str(self.chroma_path),
                    settings=Settings(anonymized_telemetry=False)
                )
                collection = client.get_or_create_collection("offer_signals")
                results = collection.get(include=["metadatas"], limit=50000)
                for meta in results.get("metadatas", []):
                    if meta and meta.get("url"):
                        urls.add(meta["url"])
            except Exception as e:
                self.logger.debug(f"Error loading indexed URLs: {e}")
        return urls

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
        """Remove thinking tags and markdown from LLM response"""
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        # Remove markdown code blocks
        if "```json" in text:
            text = text.replace("```json", "").replace("```", "")
        elif "```" in text:
            text = text.replace("```", "")
        return text.strip()

    def _has_offer_signal(self, text: str) -> tuple[bool, str, float]:
        """
        Check if text contains offer signals.
        Returns (has_signal, signal_type, strength)
        """
        text_lower = text.lower()

        for signal_type, markers in self.OFFER_SIGNALS.items():
            matches = sum(1 for m in markers if m in text_lower)
            if matches > 0:
                strength = min(matches / 3, 1.0)  # Normalize to 0-1
                return True, signal_type, strength

        return False, "", 0.0

    def fetch_subreddit_signals(
        self,
        subreddit: str,
        days_back: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch posts with offer signals from a subreddit.
        Uses Reddit's public JSON API.
        """
        signals = []

        try:
            # Use Reddit's public JSON endpoint
            url = f"https://www.reddit.com/r/{subreddit}/new.json"
            headers = {"User-Agent": "GrandSlamMiner/1.0"}
            params = {"limit": min(limit, 100), "t": "month"}

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])

                cutoff = datetime.now().timestamp() - (days_back * 86400)

                for post in posts:
                    post_data = post.get("data", {})
                    created = post_data.get("created_utc", 0)

                    if created < cutoff:
                        continue

                    # Combine title and selftext
                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")
                    full_text = f"{title}\n\n{selftext}"

                    # Check for offer signals
                    has_signal, signal_type, strength = self._has_offer_signal(full_text)

                    if has_signal and strength >= 0.3:
                        url = f"https://reddit.com{post_data.get('permalink', '')}"

                        if url not in self.indexed_urls:
                            signals.append({
                                "content": full_text[:2000],
                                "subreddit": subreddit,
                                "signal_type": signal_type,
                                "strength": strength,
                                "url": url,
                                "score": post_data.get("score", 0),
                                "created_utc": created,
                                "num_comments": post_data.get("num_comments", 0),
                            })

            elif response.status_code == 429:
                self.logger.warning(f"Rate limited on r/{subreddit}")
                time.sleep(60)
            else:
                self.logger.debug(f"Error fetching r/{subreddit}: {response.status_code}")

        except Exception as e:
            self.logger.debug(f"Error fetching r/{subreddit}: {e}")

        return signals

    def enrich_signal(self, signal: Dict) -> OfferSignal:
        """
        Use LLM to extract offer components from a signal.
        """
        signal_id = hashlib.md5(signal["url"].encode()).hexdigest()[:12]

        offer_signal = OfferSignal(
            id=signal_id,
            content=signal["content"],
            subreddit=signal["subreddit"],
            signal_type=signal["signal_type"],
            url=signal["url"],
            score=signal["score"],
            created_utc=signal["created_utc"],
            extracted_at=datetime.now().isoformat(),
        )

        client = self._get_llm_client()
        if not client:
            return offer_signal

        prompt = f"""Analyze this Reddit post for Grand Slam Offer potential.

POST FROM r/{signal['subreddit']}:
{signal['content'][:1500]}

Extract (respond in JSON):
{{
    "dream_outcome": "What does this person REALLY want? (their ideal end state)",
    "failed_solutions": ["List any solutions they've tried that didn't work"],
    "willingness_to_pay": "Any signals about what they'd pay or invest?",
    "urgency_level": "low/medium/high - how urgent is their need?",
    "specific_problem": "The concrete problem they're trying to solve"
}}

Be specific. Extract their actual words where possible."""

        try:
            response = client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )

            result = self._clean_llm_response(response.choices[0].message.content)

            # Parse JSON
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(result[start:end])
                offer_signal.dream_outcome = data.get("dream_outcome", "")
                offer_signal.failed_solutions = data.get("failed_solutions", [])
                offer_signal.willingness_to_pay = data.get("willingness_to_pay", "")
                offer_signal.urgency_level = data.get("urgency_level", "")

        except Exception as e:
            self.logger.debug(f"Error enriching signal: {e}")

        return offer_signal

    def index_signal(self, signal: OfferSignal):
        """Index signal in ChromaDB"""
        if not CHROMADB_AVAILABLE:
            return

        try:
            client = chromadb.PersistentClient(
                path=str(self.chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            collection = client.get_or_create_collection("offer_signals")

            collection.add(
                ids=[signal.id],
                documents=[signal.content],
                metadatas=[{
                    "subreddit": signal.subreddit,
                    "signal_type": signal.signal_type,
                    "url": signal.url,
                    "score": signal.score,
                    "dream_outcome": signal.dream_outcome,
                    "urgency": signal.urgency_level,
                    "created_utc": signal.created_utc,
                }]
            )

            self.indexed_urls.add(signal.url)

        except Exception as e:
            self.logger.debug(f"Error indexing signal: {e}")

    def find_offer_clusters(self) -> List[Dict]:
        """
        Analyze indexed signals to find clusters of related opportunities.
        """
        if not CHROMADB_AVAILABLE:
            return []

        clusters = []

        try:
            client = chromadb.PersistentClient(
                path=str(self.chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            collection = client.get_or_create_collection("offer_signals")

            total = collection.count()
            if total < 10:
                return []

            # Get all signals grouped by subreddit and signal type
            results = collection.get(
                include=["documents", "metadatas"],
                limit=5000
            )

            # Group by market (subreddit category)
            market_signals = defaultdict(list)

            for doc, meta in zip(results["documents"], results["metadatas"]):
                subreddit = meta.get("subreddit", "")

                # Categorize into markets
                if subreddit in ["Entrepreneur", "startups", "smallbusiness", "freelance", "consulting", "agency", "SaaS"]:
                    market = "business"
                elif subreddit in ["Fire", "financialindependence", "fatFIRE", "realestateinvesting", "personalfinance"]:
                    market = "wealth"
                elif subreddit in ["cscareerquestions", "ExperiencedDevs", "learnprogramming", "ProductManagement"]:
                    market = "tech_career"
                elif subreddit in ["loseit", "Fitness", "bodybuilding", "nutrition", "intermittentfasting"]:
                    market = "fitness"
                elif subreddit in ["Marriage", "datingoverthirty", "Parenting", "Mommit", "daddit"]:
                    market = "relationships"
                else:
                    market = "other"

                market_signals[market].append({
                    "content": doc,
                    "meta": meta,
                    "subreddit": subreddit,
                })

            # Build clusters for markets with enough signals
            for market, signals in market_signals.items():
                if len(signals) >= 10:
                    # Extract common themes
                    dream_outcomes = [s["meta"].get("dream_outcome", "") for s in signals if s["meta"].get("dream_outcome")]

                    clusters.append({
                        "market": market,
                        "signal_count": len(signals),
                        "subreddits": list(set(s["subreddit"] for s in signals)),
                        "samples": [s["content"][:500] for s in signals[:10]],
                        "dream_outcomes": dream_outcomes[:10],
                    })

            clusters.sort(key=lambda x: x["signal_count"], reverse=True)

        except Exception as e:
            self.logger.error(f"Error finding clusters: {e}")

        return clusters

    def generate_grand_slam_offer(self, cluster: Dict) -> Optional[GrandSlamOffer]:
        """
        Generate a Grand Slam Offer from a cluster of signals.
        Uses Hormozi's Value Equation.
        """
        client = self._get_llm_client()
        if not client:
            return None

        offer_id = hashlib.md5(f"{cluster['market']}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        samples_text = "\n---\n".join(cluster["samples"][:5])
        dreams_text = "\n- ".join(cluster["dream_outcomes"][:5]) if cluster["dream_outcomes"] else "Not extracted"

        prompt = f"""You are Alex Hormozi creating a Grand Slam Offer.

MARKET: {cluster['market']}
SIGNAL COUNT: {cluster['signal_count']} people expressing this need
SUBREDDITS: {', '.join(cluster['subreddits'])}

SAMPLE POSTS (what people are saying):
{samples_text}

DREAM OUTCOMES EXTRACTED:
- {dreams_text}

Create a Grand Slam Offer using the Value Equation:
Value = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort)

Respond in JSON:
{{
    "headline": "A headline that makes them feel dumb saying no",
    "target_market": "Specific person this is for (age, situation, pain)",
    "dream_outcome": "The BIG result they get (not features, OUTCOMES)",
    "mechanism": "WHY this works when other things haven't (the secret/system)",
    "time_to_result": "How fast they see results (be specific)",
    "effort_required": "How easy you make it (done-for-you, templates, etc.)",
    "core_offer": "The main thing they're buying",
    "bonuses": ["Bonus 1 that removes obstacle", "Bonus 2 that speeds up result", "Bonus 3 that reduces effort"],
    "guarantee": "Risk reversal that makes saying no feel dumb",
    "scarcity": "Why they can't get this anywhere else",
    "urgency": "Why they should act now"
}}

Make the offer SO GOOD they feel stupid saying no. Stack value until it's a no-brainer."""

        try:
            response = client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000  # Increased for full offer generation
            )

            result = self._clean_llm_response(response.choices[0].message.content)

            # Parse JSON
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(result[start:end])

                offer = GrandSlamOffer(
                    id=offer_id,
                    headline=data.get("headline", ""),
                    target_market=data.get("target_market", ""),
                    dream_outcome=data.get("dream_outcome", ""),
                    mechanism=data.get("mechanism", ""),
                    time_to_result=data.get("time_to_result", ""),
                    effort_required=data.get("effort_required", ""),
                    core_offer=data.get("core_offer", ""),
                    bonuses=data.get("bonuses", []),
                    guarantee=data.get("guarantee", ""),
                    scarcity=data.get("scarcity", ""),
                    urgency=data.get("urgency", ""),
                    signal_count=cluster["signal_count"],
                    sample_signals=cluster["samples"][:3],
                    subreddits=cluster["subreddits"],
                    generated_at=datetime.now().isoformat(),
                )

                return offer

        except Exception as e:
            self.logger.error(f"Error generating offer: {e}")

        return None

    def evaluate_offer(self, offer: GrandSlamOffer) -> GrandSlamOffer:
        """
        Evaluate offer using Hormozi's Value Equation.
        Score each component and calculate total value.
        """
        client = self._get_llm_client()
        if not client:
            return offer

        prompt = f"""Evaluate this offer using Hormozi's Value Equation.

HEADLINE: {offer.headline}
TARGET: {offer.target_market}
DREAM OUTCOME: {offer.dream_outcome}
MECHANISM: {offer.mechanism}
TIME TO RESULT: {offer.time_to_result}
EFFORT REQUIRED: {offer.effort_required}
GUARANTEE: {offer.guarantee}
EVIDENCE: {offer.signal_count} signals from r/{', r/'.join(offer.subreddits[:3])}

Score each component (1-10) and explain:

Value = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort)

Respond in JSON:
{{
    "dream_outcome_score": 1-10 (how desirable is this outcome?),
    "perceived_likelihood_score": 1-10 (how believable that it'll work?),
    "time_delay_score": 1-10 (10=instant, 1=takes forever),
    "effort_score": 1-10 (10=zero effort, 1=extremely hard),
    "is_grand_slam": true/false (would people feel dumb saying no?),
    "fatal_flaws": ["any deal-breakers"],
    "improvements": ["how to make it better"],
    "evaluation_notes": "Overall assessment"
}}

Be critical but fair. A Grand Slam makes people feel DUMB saying no."""

        try:
            response = client.chat.completions.create(
                model="vcoder-120b-1.0-hi-mlx",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1200  # Increased for full JSON response
            )

            result = self._clean_llm_response(response.choices[0].message.content)

            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(result[start:end])

                offer.dream_outcome_score = float(data.get("dream_outcome_score", 5))
                offer.perceived_likelihood_score = float(data.get("perceived_likelihood_score", 5))
                offer.time_delay_score = float(data.get("time_delay_score", 5))
                offer.effort_score = float(data.get("effort_score", 5))
                offer.is_grand_slam = data.get("is_grand_slam", False)
                offer.evaluation_notes = data.get("evaluation_notes", "")

                # Calculate value score (normalized to 100)
                # Value = (Dream × Likelihood) / (TimeDelay × Effort)
                # We invert time and effort so higher is better
                numerator = offer.dream_outcome_score * offer.perceived_likelihood_score
                denominator = ((11 - offer.time_delay_score) * (11 - offer.effort_score)) / 100 + 0.1
                offer.value_score = min((numerator / denominator) * 10, 100)

                # Override if value score is high enough
                if offer.value_score >= self.MIN_VALUE_SCORE and offer.signal_count >= self.MIN_SIGNALS:
                    offer.is_grand_slam = True

        except Exception as e:
            self.logger.debug(f"Error evaluating offer: {e}")

        return offer

    def save_offer(self, offer: GrandSlamOffer):
        """Save offer to appropriate folder"""
        if offer.is_grand_slam:
            folder = self.grand_slam_path / "golden"
            self.logger.info(f"GRAND SLAM: {offer.headline[:50]}...")
        else:
            folder = self.grand_slam_path / "rejected"

        filepath = folder / f"{offer.id}.json"
        with open(filepath, 'w') as f:
            json.dump(asdict(offer), f, indent=2)

    def run_mining_cycle(self, days_back: int = 30) -> int:
        """
        Run one cycle of signal mining.
        Returns count of new signals found.
        """
        self.logger.info("Starting mining cycle...")

        new_signals = 0

        for subreddit in self.SUBREDDITS:
            self.logger.info(f"Mining r/{subreddit}...")

            signals = self.fetch_subreddit_signals(subreddit, days_back=days_back)

            for signal_data in signals:
                signal = self.enrich_signal(signal_data)
                self.index_signal(signal)
                new_signals += 1

            if signals:
                self.logger.info(f"  Found {len(signals)} signals")

            time.sleep(2)  # Rate limiting

        self.logger.info(f"Mining complete: {new_signals} new signals")
        return new_signals

    def run_offer_generation(self) -> List[GrandSlamOffer]:
        """
        Run offer generation from accumulated signals.
        """
        self.logger.info("Generating offers from signal clusters...")

        clusters = self.find_offer_clusters()
        self.logger.info(f"Found {len(clusters)} market clusters")

        grand_slams = []

        for cluster in clusters:
            self.logger.info(f"Processing {cluster['market']} ({cluster['signal_count']} signals)...")

            offer = self.generate_grand_slam_offer(cluster)
            if offer:
                offer = self.evaluate_offer(offer)
                self.save_offer(offer)

                if offer.is_grand_slam:
                    grand_slams.append(offer)
                    self.logger.info(f"  GRAND SLAM! Value score: {offer.value_score:.1f}")
                else:
                    self.logger.info(f"  Rejected. Value score: {offer.value_score:.1f}")

            time.sleep(1)

        return grand_slams

    def run_once(self, days_back: int = 30) -> List[GrandSlamOffer]:
        """Run complete cycle: mine signals, then generate offers"""
        self.run_mining_cycle(days_back=days_back)
        return self.run_offer_generation()

    def run_continuous(self, mining_interval_hours: int = 4, offer_interval_hours: int = 12):
        """
        Run continuously:
        - Mine signals every N hours
        - Generate offers every M hours
        """
        self.logger.info(f"Starting continuous mode")
        self.logger.info(f"  Mining interval: {mining_interval_hours}h")
        self.logger.info(f"  Offer generation: {offer_interval_hours}h")

        last_mining = datetime.min
        last_offers = datetime.min

        while True:
            try:
                now = datetime.now()

                # Check if mining is due
                if (now - last_mining).total_seconds() >= mining_interval_hours * 3600:
                    self.run_mining_cycle(days_back=30)
                    last_mining = now

                # Check if offer generation is due
                if (now - last_offers).total_seconds() >= offer_interval_hours * 3600:
                    grand_slams = self.run_offer_generation()

                    if grand_slams:
                        self.logger.info(f"Found {len(grand_slams)} Grand Slam offers!")
                        for offer in grand_slams:
                            print("\n" + "=" * 60)
                            print("GRAND SLAM OFFER FOUND")
                            print("=" * 60)
                            print(f"\nHEADLINE: {offer.headline}")
                            print(f"TARGET: {offer.target_market}")
                            print(f"VALUE SCORE: {offer.value_score:.1f}/100")
                            print(f"SIGNALS: {offer.signal_count}")
                            print("=" * 60)

                    last_offers = now

                # Sleep before next check
                time.sleep(60)

            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in cycle: {e}")
                time.sleep(300)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Grand Slam Offer Miner")
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--mine-only', action='store_true', help='Only mine signals, skip offer generation')
    parser.add_argument('--offers-only', action='store_true', help='Only generate offers from existing signals')
    parser.add_argument('--days', type=int, default=30, help='Days back to mine (default: 30)')
    parser.add_argument('--mining-interval', type=int, default=4, help='Hours between mining (default: 4)')
    parser.add_argument('--offer-interval', type=int, default=12, help='Hours between offer generation (default: 12)')

    args = parser.parse_args()

    miner = GrandSlamMiner()

    if args.once:
        if args.mine_only:
            miner.run_mining_cycle(days_back=args.days)
        elif args.offers_only:
            miner.run_offer_generation()
        else:
            miner.run_once(days_back=args.days)
    else:
        miner.run_continuous(
            mining_interval_hours=args.mining_interval,
            offer_interval_hours=args.offer_interval
        )


if __name__ == "__main__":
    main()
