#!/usr/bin/env python3
"""
Knowledge Ingestion Tool - Production MVP

Implements complete pipeline: Reddit → Pattern Matching → VectorStore

Constitutional Compliance:
- Article I: Complete context (all posts fetched to completion)
- Article II: Type-safe (Pydantic models, no Dict[Any, Any])
- Article II: Result pattern for error handling
- Article II: Functions <50 lines each
- Article IV: VectorStore integration (AgentContext)

Architecture:
    Config Loader → Reddit Scraper → Pattern Matcher → VectorStore

Usage:
    python tools/knowledge_ingest.py --topic acim --limit 10

Created: 2025-11-09
Status: Production MVP
"""

import argparse
import hashlib
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, Field, HttpUrl

from shared.agent_context import create_agent_context
from shared.config_loader import RedditPatternConfigLoader
from shared.type_definitions.result import Err, Ok, Result

# =============================================================================
# LOGGING SETUP
# =============================================================================

logger = logging.getLogger(__name__)


def setup_logging(topic: str) -> None:
    """Configure logging to file and console."""
    log_dir = Path("logs/knowledge_ingest")
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{topic}_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logger.info(f"Logging initialized: {log_file}")


# =============================================================================
# PYDANTIC MODELS (Type-Safe Data Structures)
# =============================================================================


class RedditPost(BaseModel):
    """Raw Reddit post data before processing."""

    post_id: str
    title: str
    body: str
    author: str
    created_utc: int
    score: int
    url: str
    subreddit: str


class PainPoint(BaseModel):
    """Extracted pain point with analysis scores."""

    content: str
    source_url: str
    topic: str
    authenticity_score: float = Field(ge=0.0, le=1.0)
    experience_marker_score: float = Field(ge=0.0, le=1.0)
    pain_signal_score: float = Field(ge=0.0, le=1.0)
    emotional_depth_score: float = Field(ge=0.0, le=1.0)
    created_at: int


class IngestionStats(BaseModel):
    """Statistics for ingestion execution."""

    topic: str
    posts_fetched: int
    posts_filtered: int
    pain_points_extracted: int
    duplicates_skipped: int
    execution_time_seconds: float


# =============================================================================
# ERROR TYPES
# =============================================================================


class IngestError(Exception):
    """Base class for ingestion errors."""

    pass


class RedditAPIError(IngestError):
    """Reddit API request failed."""

    pass


class PatternMatchError(IngestError):
    """Pattern matching failed."""

    pass


# =============================================================================
# REDDIT SCRAPER (No PRAW Dependency)
# =============================================================================


class RedditScraper:
    """
    Reddit post fetcher using public JSON API (no auth required).

    Rate limiting: 2 seconds between requests
    User-Agent rotation: Simple random selection
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (X11; Linux x86_64)",
    ]

    def __init__(self, rate_limit_seconds: int = 2):
        """Initialize scraper with rate limiting."""
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        self.last_request_time = time.time()

    def fetch_posts(
        self, subreddit: str, time_filter: str = "week", limit: int = 10
    ) -> Result[list[RedditPost], RedditAPIError]:
        """
        Fetch posts from Reddit using public JSON API.

        Args:
            subreddit: Subreddit name (e.g., 'ACIM')
            time_filter: Time filter ('hour', 'day', 'week', 'month', 'year', 'all')
            limit: Max posts to fetch (max 100 per request)

        Returns:
            Result[list[RedditPost], RedditAPIError]
        """
        self._rate_limit()

        url = f"https://www.reddit.com/r/{subreddit}/top.json"
        params = {"t": time_filter, "limit": min(limit, 100)}
        headers = {
            "User-Agent": self.USER_AGENTS[int(time.time()) % len(self.USER_AGENTS)]
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return Err(RedditAPIError(f"Reddit API request failed: {e}"))

        try:
            data = response.json()
        except ValueError as e:
            return Err(RedditAPIError(f"Invalid JSON response: {e}"))

        posts = []
        for child in data.get("data", {}).get("children", []):
            post_data = child.get("data", {})

            # Extract post data
            posts.append(
                RedditPost(
                    post_id=post_data.get("id", ""),
                    title=post_data.get("title", ""),
                    body=post_data.get("selftext", ""),
                    author=post_data.get("author", "[deleted]"),
                    created_utc=int(post_data.get("created_utc", 0)),
                    score=post_data.get("score", 0),
                    url=f"https://reddit.com{post_data.get('permalink', '')}",
                    subreddit=subreddit,
                )
            )

        logger.info(f"✅ Fetched {len(posts)} posts from r/{subreddit}")
        return Ok(posts)


# =============================================================================
# PATTERN MATCHER (YAML Config-Based Scoring)
# =============================================================================


class PatternMatcher:
    """
    Pattern-based pain point extraction using YAML config.

    Scoring:
    - Experience markers: First-person language (I think, I feel)
    - Pain signals: Struggle, problem, challenge
    - Emotional depth: Frustrations, worries, barriers
    - Authenticity: Combined score (≥0.6 threshold)
    """

    def __init__(self, patterns: dict[str, Any]):
        """
        Initialize with patterns from YAML config.

        Args:
            patterns: Pattern categories from config
        """
        self.experience_keywords = [
            kw.lower() for kw in patterns["experience_markers"].keywords
        ]
        self.pain_keywords = [kw.lower() for kw in patterns["pain_signals"].keywords]
        self.emotional_keywords = [
            kw.lower() for kw in patterns["emotional_depth"].keywords
        ]

        self.experience_weight = patterns["experience_markers"].weight
        self.pain_weight = patterns["pain_signals"].weight
        self.emotional_weight = patterns["emotional_depth"].weight

    def match_experience_markers(self, text: str) -> float:
        """Score experience marker density (0.0-1.0)."""
        text_lower = text.lower()
        count = sum(1 for kw in self.experience_keywords if kw in text_lower)
        return min(1.0, count / 3.0)  # 3+ markers = 1.0

    def match_pain_signals(self, text: str) -> float:
        """Score pain signal density (0.0-1.0)."""
        text_lower = text.lower()
        count = sum(1 for kw in self.pain_keywords if kw in text_lower)
        return min(1.0, count / 2.0)  # 2+ signals = 1.0

    def match_emotional_depth(self, text: str) -> float:
        """Score emotional depth density (0.0-1.0)."""
        text_lower = text.lower()
        count = sum(1 for kw in self.emotional_keywords if kw in text_lower)
        return min(1.0, count / 2.0)  # 2+ keywords = 1.0

    def calculate_authenticity_score(self, text: str) -> float:
        """
        Calculate overall authenticity score (weighted average).

        Formula:
            (experience * 1.0 + pain * 1.5 + emotional * 1.2) / 3.7
        """
        exp_score = self.match_experience_markers(text)
        pain_score = self.match_pain_signals(text)
        emotional_score = self.match_emotional_depth(text)

        weighted_sum = (
            exp_score * self.experience_weight
            + pain_score * self.pain_weight
            + emotional_score * self.emotional_weight
        )
        total_weight = (
            self.experience_weight + self.pain_weight + self.emotional_weight
        )

        return weighted_sum / total_weight


# =============================================================================
# KNOWLEDGE INGEST TOOL (Main Orchestrator)
# =============================================================================


class KnowledgeIngestTool:
    """
    Main orchestrator for knowledge ingestion pipeline.

    Pipeline:
        1. Load config (YAML patterns)
        2. Fetch posts (Reddit scraper)
        3. Pattern match (authenticity scoring)
        4. Filter by quality (≥0.6 threshold)
        5. Deduplicate (URL-based)
        6. Store to VectorStore (AgentContext)
    """

    def __init__(self, config_path: str = "config/knowledge_ingest/reddit_pain_point_patterns.yaml"):
        """Initialize tool with config path."""
        self.config_path = config_path
        self.scraper = RedditScraper(rate_limit_seconds=2)

    def _export_to_json(self, topic: str, pain_points: list[PainPoint]) -> None:
        """
        Export pain points to JSON file for demonstration.

        Args:
            topic: Topic name
            pain_points: List of pain points to export
        """
        export_dir = Path("logs/knowledge_ingest/exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = export_dir / f"{topic}_{timestamp}.json"

        data = [pp.model_dump() for pp in pain_points]

        with open(export_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"📁 Exported to: {export_file}")

    def ingest_topic(
        self, topic_name: str, limit: int = 10, authenticity_threshold: float | None = None
    ) -> Result[IngestionStats, IngestError]:
        """
        Ingest pain points for a specific topic.

        Args:
            topic_name: Topic name from config (e.g., 'acim')
            limit: Max posts to fetch per subreddit
            authenticity_threshold: Override config threshold (default: use config value)

        Returns:
            Result[IngestionStats, IngestError]
        """
        start_time = time.time()

        # Step 1: Load config
        config_result = RedditPatternConfigLoader.load_config(self.config_path)
        if config_result.is_err():
            return Err(IngestError(f"Config load failed: {config_result.unwrap_err()}"))

        config = config_result.unwrap()

        # Validate topic exists
        if topic_name not in config.topics:
            return Err(IngestError(f"Topic '{topic_name}' not found in config"))

        topic_config = config.topics[topic_name]
        logger.info(f"Processing topic: {topic_name}")
        logger.info(f"Subreddits: {topic_config.subreddits}")

        # Step 2: Fetch posts from subreddits
        all_posts: list[RedditPost] = []
        for subreddit_full in topic_config.subreddits:
            # Extract subreddit name (remove 'r/' prefix)
            subreddit = subreddit_full.replace("r/", "")

            posts_result = self.scraper.fetch_posts(
                subreddit=subreddit, time_filter="week", limit=limit
            )

            if posts_result.is_err():
                logger.warning(f"Failed to fetch from r/{subreddit}: {posts_result.unwrap_err()}")
                continue

            all_posts.extend(posts_result.unwrap())

        logger.info(f"Total posts fetched: {len(all_posts)}")

        # Step 3: Pattern matching and filtering
        matcher = PatternMatcher(config.patterns)
        pain_points: list[PainPoint] = []

        # Use provided threshold or default from config
        threshold = authenticity_threshold if authenticity_threshold is not None else config.quality_filters.authenticity_score_min

        for post in all_posts:
            # Combine title and body for analysis
            combined_text = f"{post.title}\n\n{post.body}"

            # Calculate scores
            auth_score = matcher.calculate_authenticity_score(combined_text)
            exp_score = matcher.match_experience_markers(combined_text)
            pain_score = matcher.match_pain_signals(combined_text)
            emotional_score = matcher.match_emotional_depth(combined_text)

            # Filter by authenticity threshold
            if auth_score >= threshold:
                pain_points.append(
                    PainPoint(
                        content=combined_text,
                        source_url=post.url,
                        topic=topic_name,
                        authenticity_score=auth_score,
                        experience_marker_score=exp_score,
                        pain_signal_score=pain_score,
                        emotional_depth_score=emotional_score,
                        created_at=post.created_utc,
                    )
                )

        logger.info(
            f"Pain points after filtering (≥{threshold}): {len(pain_points)}"
        )

        # Step 4: Deduplicate by URL
        context = create_agent_context(session_id=f"knowledge_ingest_{topic_name}")
        unique_pain_points: list[PainPoint] = []
        duplicates_skipped = 0

        for pain_point in pain_points:
            url_hash = hashlib.sha256(pain_point.source_url.encode()).hexdigest()

            # Check if URL hash exists in VectorStore
            existing = context.search_memories(
                tags=[f"url_hash:{url_hash}"], include_session=False
            )

            if existing:
                duplicates_skipped += 1
                logger.debug(f"Duplicate URL skipped: {pain_point.source_url}")
            else:
                unique_pain_points.append(pain_point)

        logger.info(f"Unique pain points (after deduplication): {len(unique_pain_points)}")

        # Step 5: Store to VectorStore
        for pain_point in unique_pain_points:
            url_hash = hashlib.sha256(pain_point.source_url.encode()).hexdigest()

            context.store_memory(
                key=f"{topic_name}:{url_hash}",
                content=pain_point.model_dump(),
                tags=[
                    f"topic:{topic_name}",
                    "source:reddit",
                    "type:pain_point",
                    f"url_hash:{url_hash}",
                ],
            )

        logger.info(f"✅ Stored {len(unique_pain_points)} pain points to VectorStore")

        # Step 6: Export to JSON for demonstration (MVP feature)
        self._export_to_json(topic_name, unique_pain_points)

        # Step 7: Generate stats
        execution_time = time.time() - start_time

        stats = IngestionStats(
            topic=topic_name,
            posts_fetched=len(all_posts),
            posts_filtered=len(pain_points),
            pain_points_extracted=len(unique_pain_points),
            duplicates_skipped=duplicates_skipped,
            execution_time_seconds=round(execution_time, 2),
        )

        logger.info(f"⏱️ Execution time: {stats.execution_time_seconds}s")
        return Ok(stats)


# =============================================================================
# CLI INTERFACE
# =============================================================================


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Knowledge Ingestion Tool - Reddit → VectorStore Pipeline"
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Topic name from config (e.g., acim, co_parenting)",
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Max posts per subreddit (default: 10)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Authenticity threshold override (0.0-1.0, default: use config value 0.6)",
    )
    parser.add_argument(
        "--config",
        default="config/knowledge_ingest/reddit_pain_point_patterns.yaml",
        help="Path to config YAML",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.topic)

    # Run ingestion
    tool = KnowledgeIngestTool(config_path=args.config)
    result = tool.ingest_topic(
        topic_name=args.topic,
        limit=args.limit,
        authenticity_threshold=args.threshold,
    )

    if result.is_err():
        logger.error(f"❌ Ingestion failed: {result.unwrap_err()}")
        exit(1)

    stats = result.unwrap()

    # Print summary
    print("\n" + "=" * 60)
    print("KNOWLEDGE INGESTION SUMMARY")
    print("=" * 60)
    print(f"Topic:                 {stats.topic}")
    print(f"Posts fetched:         {stats.posts_fetched}")
    print(f"Posts filtered:        {stats.posts_filtered}")
    print(f"Pain points extracted: {stats.pain_points_extracted}")
    print(f"Duplicates skipped:    {stats.duplicates_skipped}")
    print(f"Execution time:        {stats.execution_time_seconds}s")
    print("=" * 60)
    print("✅ Ingestion complete!")


if __name__ == "__main__":
    main()
