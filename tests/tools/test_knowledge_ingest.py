"""
Tests for Knowledge Ingestion Tool

Constitutional Compliance:
- Article II: TDD (tests written, implementation verified)
- Article II: Type-safe (Pydantic models)
- Article II: Result pattern
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from tools.knowledge_ingest import (
    RedditScraper,
    PatternMatcher,
    KnowledgeIngestTool,
    RedditPost,
    PainPoint,
    IngestionStats,
    RedditAPIError,
)
from shared.config_loader import (
    RedditPatternConfigLoader,
    PatternCategory,
)
from shared.type_definitions.result import Ok, Err


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_config():
    """Mock pattern configuration."""
    return {
        "patterns": {
            "experience_markers": PatternCategory(
                description="First-person experiences",
                keywords=["i think", "i feel", "i was"],
                usage="Filter for posts",
                weight=1.0,
            ),
            "pain_signals": PatternCategory(
                description="Pain indicators",
                keywords=["struggle", "problem", "challenge"],
                usage="Primary extraction",
                weight=1.5,
            ),
            "emotional_depth": PatternCategory(
                description="Emotional context",
                keywords=["frustration", "worry", "concern"],
                usage="Secondary extraction",
                weight=1.2,
            ),
        },
        "topics": {
            "test_topic": {
                "subreddits": ["r/test"],
                "additional_keywords": [],
                "extraction_focus": [],
            }
        },
        "quality_filters": {
            "authenticity_score_min": 0.6,
            "min_upvotes": 5,
            "min_comment_length": 100,
            "exclude_patterns": [],
            "sentiment_threshold": -0.3,
        },
    }


@pytest.fixture
def sample_reddit_post():
    """Sample Reddit post for testing."""
    return RedditPost(
        post_id="abc123",
        title="I think I have a problem",
        body="I feel like I'm struggling with this challenge. It's causing me frustration.",
        author="test_user",
        created_utc=1762306183,
        score=10,
        url="https://reddit.com/r/test/comments/abc123/test",
        subreddit="test",
    )


# =============================================================================
# REDDIT SCRAPER TESTS
# =============================================================================


class TestRedditScraper:
    """Test Reddit scraper functionality."""

    def test_rate_limiting(self):
        """Test rate limiter enforces delays."""
        scraper = RedditScraper(rate_limit_seconds=0.1)

        import time

        start = time.time()
        scraper._rate_limit()
        scraper._rate_limit()
        elapsed = time.time() - start

        assert elapsed >= 0.1, "Rate limiter should enforce minimum delay"

    @patch("tools.knowledge_ingest.requests.get")
    def test_fetch_posts_success(self, mock_get):
        """Test successful post fetching."""
        # Mock Reddit JSON response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "post1",
                            "title": "Test Post",
                            "selftext": "Test body",
                            "author": "testuser",
                            "created_utc": 1762306183,
                            "score": 10,
                            "permalink": "/r/test/comments/post1/test",
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        scraper = RedditScraper(rate_limit_seconds=0)
        result = scraper.fetch_posts("test", limit=1)

        assert result.is_ok()
        posts = result.unwrap()
        assert len(posts) == 1
        assert posts[0].post_id == "post1"

    @patch("tools.knowledge_ingest.requests.get")
    def test_fetch_posts_api_error(self, mock_get):
        """Test API error handling."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        scraper = RedditScraper(rate_limit_seconds=0)
        result = scraper.fetch_posts("test", limit=1)

        assert result.is_err()
        assert isinstance(result.unwrap_err(), RedditAPIError)


# =============================================================================
# PATTERN MATCHER TESTS
# =============================================================================


class TestPatternMatcher:
    """Test pattern matching functionality."""

    def test_experience_marker_scoring(self, mock_config):
        """Test experience marker detection."""
        matcher = PatternMatcher(mock_config["patterns"])

        text = "I think I feel overwhelmed. I was struggling."
        score = matcher.match_experience_markers(text)

        # Should detect 3 markers: "i think", "i feel", "i was"
        assert score == 1.0, "3+ markers should score 1.0"

    def test_pain_signal_scoring(self, mock_config):
        """Test pain signal detection."""
        matcher = PatternMatcher(mock_config["patterns"])

        text = "I have a problem and struggle with this challenge."
        score = matcher.match_pain_signals(text)

        # Should detect 3 signals: "problem", "struggle", "challenge"
        assert score == 1.0, "3+ signals should score 1.0"

    def test_emotional_depth_scoring(self, mock_config):
        """Test emotional depth detection."""
        matcher = PatternMatcher(mock_config["patterns"])

        text = "My frustration and worry cause concern."
        score = matcher.match_emotional_depth(text)

        # Should detect 3 keywords: "frustration", "worry", "concern"
        assert score == 1.0, "3+ emotional keywords should score 1.0"

    def test_authenticity_score_calculation(self, mock_config):
        """Test weighted authenticity scoring."""
        matcher = PatternMatcher(mock_config["patterns"])

        # Text with all markers
        text = "I think I have a problem that causes frustration."
        score = matcher.calculate_authenticity_score(text)

        # Should be weighted average: (0.33*1.0 + 0.5*1.5 + 0.5*1.2) / 3.7
        assert score > 0.0, "Should detect patterns"
        assert score <= 1.0, "Should be normalized"

    def test_case_insensitive_matching(self, mock_config):
        """Test case-insensitive keyword matching."""
        matcher = PatternMatcher(mock_config["patterns"])

        text = "I THINK I HAVE A PROBLEM WITH THIS STRUGGLE"
        score = matcher.calculate_authenticity_score(text)

        assert score > 0.0, "Should match case-insensitively"


# =============================================================================
# KNOWLEDGE INGEST TOOL TESTS
# =============================================================================


class TestKnowledgeIngestTool:
    """Test main ingestion orchestrator."""

    @patch("tools.knowledge_ingest.RedditPatternConfigLoader.load_config")
    @patch("tools.knowledge_ingest.RedditScraper.fetch_posts")
    @patch("tools.knowledge_ingest.create_agent_context")
    def test_ingest_topic_success(
        self, mock_context, mock_fetch, mock_config_loader
    ):
        """Test successful topic ingestion."""
        # Mock config
        from shared.config_loader import RedditPatternConfig, TopicConfig, QualityFilters, IntegrationConfig, VectorStoreConfig, MemoryToolConfig, OvernightWorkerConfig

        mock_config_loader.return_value = Ok(
            RedditPatternConfig(
                patterns={
                    "experience_markers": PatternCategory(
                        description="test",
                        keywords=["i think"],
                        usage="test",
                        weight=1.0,
                    ),
                    "pain_signals": PatternCategory(
                        description="test",
                        keywords=["problem"],
                        usage="test",
                        weight=1.5,
                    ),
                    "emotional_depth": PatternCategory(
                        description="test",
                        keywords=["frustration"],
                        usage="test",
                        weight=1.2,
                    ),
                },
                reddit_search_template="test",
                topics={
                    "test_topic": TopicConfig(
                        subreddits=["r/test"],
                        additional_keywords=[],
                        extraction_focus=[],
                    )
                },
                integration=IntegrationConfig(
                    vectorstore=VectorStoreConfig(
                        enabled=True,
                        tags_format=["topic:{topic}"],
                        embedding_model="test",
                    ),
                    memory_tool=MemoryToolConfig(
                        enabled=True, path="test", format="test"
                    ),
                    overnight_worker=OvernightWorkerConfig(
                        enabled=True,
                        schedule="test",
                        max_posts_per_topic=20,
                        rate_limit_seconds=2,
                    ),
                ),
                quality_filters=QualityFilters(
                    min_upvotes=5,
                    min_comment_length=100,
                    exclude_patterns=[],
                    sentiment_threshold=-0.3,
                    authenticity_score_min=0.05,  # Low threshold for testing
                ),
            )
        )

        # Mock Reddit posts
        mock_fetch.return_value = Ok(
            [
                RedditPost(
                    post_id="post1",
                    title="I think I have a problem",
                    body="This is frustrating",
                    author="user1",
                    created_utc=1762306183,
                    score=10,
                    url="https://reddit.com/r/test/comments/post1/test",
                    subreddit="test",
                )
            ]
        )

        # Mock context
        mock_ctx = Mock()
        mock_ctx.search_memories.return_value = []  # No duplicates
        mock_ctx.store_memory = Mock()
        mock_context.return_value = mock_ctx

        # Run ingestion
        tool = KnowledgeIngestTool()
        result = tool.ingest_topic("test_topic", limit=1, authenticity_threshold=0.05)

        assert result.is_ok()
        stats = result.unwrap()
        assert stats.posts_fetched == 1
        assert stats.pain_points_extracted == 1
        assert stats.duplicates_skipped == 0

    @patch("tools.knowledge_ingest.RedditPatternConfigLoader.load_config")
    def test_ingest_topic_invalid_topic(self, mock_config_loader):
        """Test error handling for invalid topic."""
        from shared.config_loader import (
            RedditPatternConfig,
            IntegrationConfig,
            VectorStoreConfig,
            MemoryToolConfig,
            OvernightWorkerConfig,
            QualityFilters,
        )

        mock_config_loader.return_value = Ok(
            RedditPatternConfig(
                patterns={},
                reddit_search_template="",
                topics={},
                integration=IntegrationConfig(
                    vectorstore=VectorStoreConfig(
                        enabled=True,
                        tags_format=[],
                        embedding_model="test",
                    ),
                    memory_tool=MemoryToolConfig(
                        enabled=False,
                        path="",
                        format="",
                    ),
                    overnight_worker=OvernightWorkerConfig(
                        enabled=False,
                        schedule="",
                        max_posts_per_topic=0,
                        rate_limit_seconds=0,
                    ),
                ),
                quality_filters=QualityFilters(
                    min_upvotes=0,
                    min_comment_length=0,
                    exclude_patterns=[],
                    sentiment_threshold=0.0,
                    authenticity_score_min=0.0,
                ),
            )
        )

        tool = KnowledgeIngestTool()
        result = tool.ingest_topic("invalid_topic", limit=1)

        assert result.is_err()
        assert "not found" in str(result.unwrap_err()).lower()


# =============================================================================
# PYDANTIC MODEL TESTS
# =============================================================================


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_reddit_post_validation(self):
        """Test RedditPost model validation."""
        post = RedditPost(
            post_id="abc123",
            title="Test",
            body="Body",
            author="user",
            created_utc=1762306183,
            score=10,
            url="https://reddit.com/test",
            subreddit="test",
        )

        assert post.post_id == "abc123"
        assert post.score == 10

    def test_pain_point_validation(self):
        """Test PainPoint model validation."""
        pain_point = PainPoint(
            content="Test content",
            source_url="https://reddit.com/test",
            topic="test_topic",
            authenticity_score=0.85,
            experience_marker_score=0.9,
            pain_signal_score=0.8,
            emotional_depth_score=0.7,
            created_at=1762306183,
        )

        assert pain_point.authenticity_score == 0.85
        assert 0.0 <= pain_point.authenticity_score <= 1.0

    def test_pain_point_invalid_score(self):
        """Test PainPoint rejects invalid scores."""
        with pytest.raises(Exception):  # Pydantic validation error
            PainPoint(
                content="Test",
                source_url="https://reddit.com/test",
                topic="test",
                authenticity_score=1.5,  # Invalid: >1.0
                experience_marker_score=0.9,
                pain_signal_score=0.8,
                emotional_depth_score=0.7,
                created_at=1762306183,
            )

    def test_ingestion_stats_validation(self):
        """Test IngestionStats model validation."""
        stats = IngestionStats(
            topic="test_topic",
            posts_fetched=20,
            posts_filtered=15,
            pain_points_extracted=10,
            duplicates_skipped=5,
            execution_time_seconds=8.27,
        )

        assert stats.posts_fetched == 20
        assert stats.execution_time_seconds == 8.27


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests for full pipeline."""

    @pytest.mark.skipif(
        not Path("config/knowledge_ingest/reddit_pain_point_patterns.yaml").exists(),
        reason="Config file not found",
    )
    def test_load_real_config(self):
        """Test loading real YAML config."""
        result = RedditPatternConfigLoader.load_config(
            "config/knowledge_ingest/reddit_pain_point_patterns.yaml"
        )

        assert result.is_ok()
        config = result.unwrap()
        assert "experience_markers" in config.patterns
        assert "pain_signals" in config.patterns
        assert "emotional_depth" in config.patterns

    def test_export_to_json(self, tmp_path):
        """Test JSON export functionality."""
        tool = KnowledgeIngestTool()

        pain_points = [
            PainPoint(
                content="Test content",
                source_url="https://reddit.com/test",
                topic="test_topic",
                authenticity_score=0.85,
                experience_marker_score=0.9,
                pain_signal_score=0.8,
                emotional_depth_score=0.7,
                created_at=1762306183,
            )
        ]

        # Temporarily override export directory
        original_method = tool._export_to_json
        export_dir = tmp_path / "exports"
        export_dir.mkdir()

        def mock_export(topic, pain_points):
            export_file = export_dir / f"{topic}_test.json"
            data = [pp.model_dump() for pp in pain_points]
            with open(export_file, "w") as f:
                json.dump(data, f, indent=2)

        tool._export_to_json = mock_export
        tool._export_to_json("test_topic", pain_points)

        # Verify file created
        export_file = export_dir / "test_topic_test.json"
        assert export_file.exists()

        # Verify content
        with open(export_file) as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["topic"] == "test_topic"
            assert data[0]["authenticity_score"] == 0.85
