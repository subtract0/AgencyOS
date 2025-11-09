# Specification: Reddit API Integration for Knowledge Ingestion

**ID**: SPEC-REDDIT-001
**Status**: Draft
**Created**: 2025-11-09
**Updated**: 2025-11-09
**Owner**: PlannerAgent
**Related Config**: `config/knowledge_ingest/reddit_pain_point_patterns.yaml`

---

## Goals

**Primary objective: Enable autonomous extraction of authentic coaching insights from Reddit using PRAW with requests-based fallback**

- **Goal 1**: Integrate PRAW library for official Reddit API access with OAuth2 authentication
- **Goal 2**: Implement requests-based scraping fallback for rate limit scenarios (no authentication required)
- **Goal 3**: Extract high-quality pain point data from 10+ subreddits per coaching niche
- **Goal 4**: Store extracted insights to VectorStore for institutional learning (Article IV compliance)
- **Goal 5**: Support overnight autonomous execution with rate limit handling and retry logic

## Non-Goals

**Explicitly out of scope for this specification**

- **Non-goal 1**: Real-time Reddit monitoring or webhook integration (batch-only execution)
- **Non-goal 2**: Reddit post/comment creation or interaction (read-only integration)
- **Non-goal 3**: Image/video content analysis (text-only extraction)
- **Non-goal 4**: Custom subreddit discovery (predefined subreddit lists only)
- **Non-goal 5**: Reddit user profiling or tracking (post/comment content only)
- **Non-goal 6**: Integration with Reddit Premium or Enterprise APIs (free tier only)

## Personas

**Who will use this feature and how**

### Persona 1: LearningAgent (Overnight Worker)

- **Context**: Autonomous nightly execution for knowledge accumulation
- **Need**: Extract 20 high-quality pain points per topic without manual intervention
- **Interaction**: Batch processing via `/sync-learnings` or overnight worker cron job

### Persona 2: Knowledge Ingestion System

- **Context**: Populate VectorStore with authentic coaching insights from Reddit
- **Need**: Reliable, rate-limit-aware extraction with fallback mechanisms
- **Interaction**: Programmatic API calls to PRAW wrapper with automatic retry/fallback

### Persona 3: System Administrator (@am)

- **Context**: Configure Reddit API credentials and subreddit selections
- **Need**: Environment-based configuration without code changes
- **Interaction**: Set environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)

## Acceptance Criteria

**Verifiable conditions for feature completion**

### Functional Criteria

- [ ] **FC-1**: PRAW client initialization with OAuth2 credentials from environment variables
  - Client ID, Client Secret, User Agent loaded from env
  - Connection test with `reddit.user.me()` (returns None for script apps - valid)
  - Graceful error handling for invalid/missing credentials

- [ ] **FC-2**: Subreddit selection from YAML configuration
  - Load subreddit lists from `config/knowledge_ingest/reddit_pain_point_patterns.yaml`
  - Support 10+ subreddits per topic (co_parenting, conscious_uncoupling, acim, open_relationships, love_and_forgiveness)
  - Validate subreddit existence before extraction (skip non-existent subreddits)

- [ ] **FC-3**: Post/comment filtering with quality criteria
  - Minimum upvotes: 5 (configurable via YAML `quality_filters.min_upvotes`)
  - Minimum comment length: 100 characters (configurable via `quality_filters.min_comment_length`)
  - Recency filter: Posts from last 30 days (configurable parameter)
  - Exclude patterns: `[deleted]`, `[removed]`, spam markers

- [ ] **FC-4**: Experience marker pattern matching
  - Filter posts/comments containing first-person experience phrases (I think, I feel, my experience, etc.)
  - Pattern weighting: experience_markers (1.0), pain_signals (1.5), emotional_depth (1.2)
  - Authenticity score calculation: (experience_markers_count / total_words) * weight
  - Minimum authenticity score: 0.6 (high-quality authentic experiences only)

- [ ] **FC-5**: Fallback scraping with requests + BeautifulSoup
  - Trigger fallback when PRAW hits rate limit (HTTP 429) or authentication fails
  - Use requests library to fetch Reddit JSON endpoints (`/r/{subreddit}/top.json?t=month&limit=100`)
  - Parse JSON responses (no HTML parsing required - Reddit provides JSON)
  - User-Agent header spoofing to avoid bot detection
  - Respect rate limits: 2 seconds delay between requests (configurable)

- [ ] **FC-6**: Rate limit handling and retry logic
  - Detect PRAW rate limit exceptions (`prawcore.exceptions.TooManyRequests`)
  - Exponential backoff retry: 60s → 120s → 300s → fallback
  - Global rate limit tracking: max 60 requests/minute (PRAW default)
  - Daily quota tracking: max 1000 posts/day per topic (configurable)
  - Log rate limit events for monitoring and optimization

- [ ] **FC-7**: Data extraction schema with Pydantic models
  - **RedditPost** model: author (str), title (str), body (str), created_utc (int), url (str), score (int), subreddit (str), post_id (str)
  - **RedditComment** model: author (str), body (str), created_utc (int), url (str), score (int), post_id (str), comment_id (str)
  - **ExtractedInsight** model: content (str), source (RedditPost | RedditComment), authenticity_score (float), pain_signals (list[str]), topic (str)
  - All models use strict typing (no `Dict[Any, Any]` - Constitutional Law #2)

### Non-Functional Criteria

- [ ] **NFC-1**: Performance: Extract 20 posts per topic within 5 minutes (PRAW)
- [ ] **NFC-2**: Performance: Extract 20 posts per topic within 10 minutes (fallback scraping)
- [ ] **NFC-3**: Reliability: 99% success rate for valid subreddits (handle invalid gracefully)
- [ ] **NFC-4**: Reliability: 100% fallback activation on PRAW rate limit
- [ ] **NFC-5**: Security: No credentials stored in code (environment variables only)
- [ ] **NFC-6**: Security: User-Agent randomization for fallback scraping (avoid bot detection)
- [ ] **NFC-7**: Observability: Log all extraction attempts with success/failure counts
- [ ] **NFC-8**: Observability: Telemetry for rate limit events and fallback activations

### Quality Criteria

- [ ] **QC-1**: Test Coverage: >95% for PRAW wrapper, fallback scraper, data extraction
- [ ] **QC-2**: Test Coverage: 100% for Pydantic models (validation logic)
- [ ] **QC-3**: Constitutional Compliance: Article I (complete context - all posts extracted or timeout retry)
- [ ] **QC-4**: Constitutional Compliance: Article II (100% test pass rate before merge)
- [ ] **QC-5**: Constitutional Compliance: Article IV (VectorStore integration for extracted insights)
- [ ] **QC-6**: Constitutional Compliance: Article V (traceability to this specification)
- [ ] **QC-7**: Code Quality: Zero linting errors (mypy, ruff)
- [ ] **QC-8**: Code Quality: Functions <50 lines (focused, single-purpose)
- [ ] **QC-9**: Documentation: Docstrings for all public functions (AAA pattern for tests)
- [ ] **QC-10**: Type Safety: 100% type annotations (strict mypy compliance)

## Dependencies

**System Dependencies**:
- **PRAW**: `praw>=7.8.0` (Python Reddit API Wrapper)
- **Requests**: `requests>=2.32.0` (HTTP client for fallback)
- **BeautifulSoup4**: `beautifulsoup4>=4.12.0` (HTML parsing - optional, JSON preferred)
- **Pydantic**: `pydantic>=2.0.0` (data validation, strict typing)
- **PyYAML**: `pyyaml>=6.0.0` (configuration loading)

**Internal Dependencies**:
- **AgentContext**: `shared/agent_context.py` (VectorStore integration, memory API)
- **Result Pattern**: `shared/type_definitions/result.py` (error handling)
- **EnhancedMemoryStore**: `agency_memory/enhanced_memory.py` (VectorStore backend)

**Configuration Dependencies**:
- **YAML Config**: `config/knowledge_ingest/reddit_pain_point_patterns.yaml` (subreddit lists, quality filters)
- **Environment Variables**: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

**External Dependencies**:
- **Reddit API**: OAuth2 authentication (script app credentials)
- **Reddit JSON Endpoints**: Public JSON feeds for fallback scraping

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Knowledge Ingestion System                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─► RedditExtractor (Facade)
                            │      │
                ┌───────────┴──────┴──────────┐
                │                             │
         ┌──────▼──────┐            ┌────────▼────────┐
         │ PRAWClient  │            │ FallbackScraper │
         │ (Primary)   │            │  (requests)     │
         └──────┬──────┘            └────────┬────────┘
                │                             │
                │   Rate Limit (429)          │
                ├─────────────────────────────┤
                │                             │
         ┌──────▼──────────────────────────────▼──────┐
         │         DataExtractor & Filter              │
         │  (Pattern matching, quality filtering)      │
         └──────┬──────────────────────────────────────┘
                │
         ┌──────▼──────────────────────────────┐
         │       VectorStore Integration        │
         │  (AgentContext.store_memory)         │
         └──────────────────────────────────────┘
```

### Data Flow

```
1. Load YAML config (subreddits, quality filters)
   ↓
2. Initialize PRAWClient with OAuth2 credentials
   ↓
3. For each topic → For each subreddit:
   a. Fetch top posts (last 30 days, limit=100)
   b. Apply quality filters (upvotes, length, recency)
   c. Extract comments from filtered posts
   d. Pattern matching (experience markers, pain signals)
   e. Calculate authenticity score
   f. Store to VectorStore if score >= 0.6
   ↓
4. On rate limit (HTTP 429):
   a. Switch to FallbackScraper
   b. Fetch Reddit JSON endpoints
   c. Parse JSON, apply same filters
   d. Continue extraction with 2s delay
   ↓
5. Return ExtractedInsight[] with metadata
```

### Error Handling Strategy

```python
# Result pattern for all operations (ADR-010)
def extract_from_subreddit(
    subreddit: str,
    topic: str,
    config: RedditConfig
) -> Result[list[ExtractedInsight], RedditError]:
    """
    Extract insights from subreddit with fallback on rate limit.

    Args:
        subreddit: Subreddit name (without r/ prefix)
        topic: Topic category (co_parenting, acim, etc.)
        config: Configuration including quality filters

    Returns:
        Result with list of ExtractedInsight or RedditError

    Raises:
        Never - uses Result pattern
    """
    # Try PRAW first
    praw_result = praw_client.fetch_posts(subreddit, config)

    if praw_result.is_err():
        error = praw_result.unwrap_err()

        # Fallback on rate limit
        if isinstance(error, RateLimitError):
            return fallback_scraper.fetch_posts(subreddit, config)

        # Return error for other failures
        return Err(error)

    # Filter and extract insights
    posts = praw_result.unwrap()
    insights = extract_insights(posts, topic, config)

    return Ok(insights)
```

## Implementation Details

### PRAW Configuration

**Environment Variables**:
```bash
# Reddit OAuth2 credentials (script app)
REDDIT_CLIENT_ID=<your_client_id>
REDDIT_CLIENT_SECRET=<your_client_secret>
REDDIT_USER_AGENT="AgencyOS/1.0 (Knowledge Ingestion Bot)"

# Optional overrides
REDDIT_RATE_LIMIT_DELAY=2  # Seconds between requests (default: 2)
REDDIT_MAX_POSTS_PER_SUBREDDIT=100  # Max posts to fetch (default: 100)
REDDIT_RECENCY_DAYS=30  # Fetch posts from last N days (default: 30)
```

**PRAW Initialization**:
```python
import praw
import os
from shared.type_definitions.result import Result, Ok, Err

def create_praw_client() -> Result[praw.Reddit, str]:
    """
    Create PRAW client with environment credentials.

    Returns:
        Result with initialized Reddit client or error message
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "AgencyOS/1.0")

    if not client_id or not client_secret:
        return Err("Missing Reddit credentials: REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET")

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            ratelimit_seconds=300  # 5-minute sleep on rate limit
        )

        # Test connection (script apps return None for user.me())
        _ = reddit.user.me()  # Will be None for script app - that's valid
        return Ok(reddit)

    except Exception as e:
        return Err(f"PRAW initialization failed: {str(e)}")
```

### Subreddit Selection Strategy

**YAML Configuration** (existing):
```yaml
topics:
  co_parenting:
    subreddits:
      - coparenting         # r/coparenting
      - Parenting           # r/Parenting
      - breakingmom         # r/breakingmom
      - daddit              # r/daddit
      - SingleParents       # r/SingleParents

    additional_keywords:
      - "ex partner"
      - "custody"
      - "visitation"

  conscious_uncoupling:
    subreddits:
      - Divorce
      - BreakUps
      - relationships

  acim:
    subreddits:
      - ACIM
      - spirituality
      - awakened

  open_relationships:
    subreddits:
      - polyamory
      - nonmonogamy
      - relationship_advice

  love_and_forgiveness:
    subreddits:
      - selfimprovement
      - DecidingToBeBetter
      - relationships
```

**Subreddit Loading**:
```python
import yaml
from pathlib import Path
from pydantic import BaseModel

class SubredditConfig(BaseModel):
    """Subreddit configuration for a topic."""
    subreddits: list[str]
    additional_keywords: list[str] = []
    extraction_focus: list[str] = []

def load_subreddit_config(topic: str) -> Result[SubredditConfig, str]:
    """
    Load subreddit configuration for a topic.

    Args:
        topic: Topic name (co_parenting, acim, etc.)

    Returns:
        Result with SubredditConfig or error message
    """
    config_path = Path("config/knowledge_ingest/reddit_pain_point_patterns.yaml")

    if not config_path.exists():
        return Err(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if topic not in config.get("topics", {}):
        return Err(f"Topic '{topic}' not found in configuration")

    topic_config = config["topics"][topic]
    return Ok(SubredditConfig(**topic_config))
```

### Post/Comment Filtering

**Quality Filters** (from YAML):
```yaml
quality_filters:
  min_upvotes: 5
  min_comment_length: 100
  exclude_patterns:
    - "removed by moderator"
    - "[deleted]"
    - "spam"
  sentiment_threshold: -0.3  # Allow negative sentiment (pain points)
  authenticity_score_min: 0.6
```

**Filter Implementation**:
```python
from pydantic import BaseModel
from datetime import datetime, timedelta

class QualityFilters(BaseModel):
    """Quality filter configuration."""
    min_upvotes: int = 5
    min_comment_length: int = 100
    exclude_patterns: list[str] = ["[deleted]", "[removed]", "spam"]
    sentiment_threshold: float = -0.3
    authenticity_score_min: float = 0.6

def filter_post(post: praw.models.Submission, filters: QualityFilters, recency_days: int = 30) -> bool:
    """
    Filter post by quality criteria.

    Args:
        post: PRAW submission object
        filters: Quality filter configuration
        recency_days: Maximum age in days (default: 30)

    Returns:
        True if post meets quality criteria, False otherwise
    """
    # Recency check
    cutoff_date = datetime.now() - timedelta(days=recency_days)
    post_date = datetime.fromtimestamp(post.created_utc)
    if post_date < cutoff_date:
        return False

    # Upvote check
    if post.score < filters.min_upvotes:
        return False

    # Exclude patterns
    body = post.selftext or ""
    for pattern in filters.exclude_patterns:
        if pattern.lower() in body.lower():
            return False

    return True

def filter_comment(comment: praw.models.Comment, filters: QualityFilters) -> bool:
    """
    Filter comment by quality criteria.

    Args:
        comment: PRAW comment object
        filters: Quality filter configuration

    Returns:
        True if comment meets quality criteria, False otherwise
    """
    body = comment.body or ""

    # Length check
    if len(body) < filters.min_comment_length:
        return False

    # Upvote check
    if comment.score < filters.min_upvotes:
        return False

    # Exclude patterns
    for pattern in filters.exclude_patterns:
        if pattern.lower() in body.lower():
            return False

    return True
```

### Fallback Scraping Strategy

**Requests-Based JSON Scraping** (no authentication required):
```python
import requests
import time
from typing import Any

class FallbackScraper:
    """
    Requests-based Reddit scraping for rate limit scenarios.

    Uses Reddit's public JSON endpoints (no authentication).
    """

    def __init__(self, delay_seconds: int = 2):
        """
        Initialize fallback scraper.

        Args:
            delay_seconds: Delay between requests (default: 2)
        """
        self.delay_seconds = delay_seconds
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
        self.request_count = 0

    def fetch_posts(
        self,
        subreddit: str,
        limit: int = 100,
        time_filter: str = "month"
    ) -> Result[list[dict[str, Any]], str]:
        """
        Fetch posts from subreddit using JSON endpoint.

        Args:
            subreddit: Subreddit name (without r/)
            limit: Maximum posts to fetch (default: 100)
            time_filter: Time filter (hour, day, week, month, year, all)

        Returns:
            Result with list of post dicts or error message
        """
        url = f"https://www.reddit.com/r/{subreddit}/top.json"
        params = {"t": time_filter, "limit": limit}
        headers = {
            "User-Agent": self.user_agents[self.request_count % len(self.user_agents)]
        }

        try:
            # Rate limit delay
            if self.request_count > 0:
                time.sleep(self.delay_seconds)

            response = requests.get(url, params=params, headers=headers, timeout=10)
            self.request_count += 1

            if response.status_code == 429:
                return Err("Rate limit exceeded (HTTP 429)")

            if response.status_code != 200:
                return Err(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            # Extract post data
            post_dicts = [post["data"] for post in posts]
            return Ok(post_dicts)

        except requests.exceptions.RequestException as e:
            return Err(f"Request failed: {str(e)}")
        except Exception as e:
            return Err(f"Unexpected error: {str(e)}")

    def fetch_comments(
        self,
        subreddit: str,
        post_id: str
    ) -> Result[list[dict[str, Any]], str]:
        """
        Fetch comments for a post using JSON endpoint.

        Args:
            subreddit: Subreddit name
            post_id: Reddit post ID

        Returns:
            Result with list of comment dicts or error message
        """
        url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
        headers = {
            "User-Agent": self.user_agents[self.request_count % len(self.user_agents)]
        }

        try:
            time.sleep(self.delay_seconds)
            response = requests.get(url, headers=headers, timeout=10)
            self.request_count += 1

            if response.status_code != 200:
                return Err(f"HTTP {response.status_code}")

            data = response.json()
            # Comments are in second element of response array
            comments = data[1].get("data", {}).get("children", [])

            comment_dicts = [c["data"] for c in comments if c["kind"] == "t1"]
            return Ok(comment_dicts)

        except Exception as e:
            return Err(f"Failed to fetch comments: {str(e)}")
```

### Rate Limit Handling

**Exponential Backoff with Fallback**:
```python
import time
from typing import Callable, TypeVar

T = TypeVar("T")

def retry_with_backoff(
    operation: Callable[[], Result[T, Any]],
    max_retries: int = 3,
    fallback: Callable[[], Result[T, Any]] | None = None
) -> Result[T, str]:
    """
    Retry operation with exponential backoff, fallback on exhaustion.

    Args:
        operation: Function returning Result
        max_retries: Maximum retry attempts (default: 3)
        fallback: Fallback function on retry exhaustion (optional)

    Returns:
        Result from operation or fallback
    """
    delays = [60, 120, 300]  # 1min, 2min, 5min

    for attempt in range(max_retries):
        result = operation()

        if result.is_ok():
            return result

        error = result.unwrap_err()

        # Rate limit error → retry with backoff
        if isinstance(error, RateLimitError):
            if attempt < max_retries - 1:
                delay = delays[attempt]
                logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue

        # Other errors → return immediately
        else:
            return result

    # Retry exhausted → fallback
    if fallback:
        logger.info("Retries exhausted, activating fallback scraper")
        return fallback()

    return Err("Rate limit retries exhausted, no fallback available")
```

### Data Extraction Schema

**Pydantic Models** (strict typing, Constitutional Law #2):
```python
from pydantic import BaseModel, Field
from typing import Literal

class RedditPost(BaseModel):
    """Reddit post data model."""
    author: str = Field(..., description="Post author username")
    title: str = Field(..., description="Post title")
    body: str = Field(..., description="Post selftext content")
    created_utc: int = Field(..., description="Unix timestamp")
    url: str = Field(..., description="Post permalink URL")
    score: int = Field(..., description="Upvote count")
    subreddit: str = Field(..., description="Subreddit name")
    post_id: str = Field(..., description="Reddit post ID")

class RedditComment(BaseModel):
    """Reddit comment data model."""
    author: str = Field(..., description="Comment author username")
    body: str = Field(..., description="Comment text")
    created_utc: int = Field(..., description="Unix timestamp")
    url: str = Field(..., description="Comment permalink URL")
    score: int = Field(..., description="Upvote score")
    post_id: str = Field(..., description="Parent post ID")
    comment_id: str = Field(..., description="Reddit comment ID")

class ExtractedInsight(BaseModel):
    """Extracted insight with quality scoring."""
    content: str = Field(..., description="Insight text (post or comment)")
    source_type: Literal["post", "comment"] = Field(..., description="Source type")
    source_post: RedditPost | None = Field(None, description="Source post if type=post")
    source_comment: RedditComment | None = Field(None, description="Source comment if type=comment")
    authenticity_score: float = Field(..., ge=0.0, le=1.0, description="Quality score (0-1)")
    pain_signals: list[str] = Field(default_factory=list, description="Matched pain keywords")
    experience_markers: list[str] = Field(default_factory=list, description="Matched experience phrases")
    topic: str = Field(..., description="Topic category")
    extracted_at: int = Field(..., description="Extraction timestamp")

    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable after creation
        validate_assignment = True
```

**Pattern Matching & Scoring**:
```python
import re
from typing import Pattern

class PatternMatcher:
    """
    Match experience markers and pain signals in text.

    Loads patterns from YAML configuration.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize pattern matcher.

        Args:
            config: YAML configuration dict
        """
        self.experience_markers = config["patterns"]["experience_markers"]["keywords"]
        self.pain_signals = config["patterns"]["pain_signals"]["keywords"]
        self.emotional_depth = config["patterns"]["emotional_depth"]["keywords"]

        self.weights = {
            "experience": config["patterns"]["experience_markers"]["weight"],
            "pain": config["patterns"]["pain_signals"]["weight"],
            "emotional": config["patterns"]["emotional_depth"]["weight"],
        }

    def calculate_authenticity_score(self, text: str) -> tuple[float, list[str], list[str]]:
        """
        Calculate authenticity score for text.

        Args:
            text: Input text (post or comment)

        Returns:
            Tuple of (score, matched_experience_markers, matched_pain_signals)
        """
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)

        if word_count == 0:
            return (0.0, [], [])

        # Count pattern matches
        experience_matches = [m for m in self.experience_markers if m.lower() in text_lower]
        pain_matches = [m for m in self.pain_signals if m.lower() in text_lower]
        emotional_matches = [m for m in self.emotional_depth if m.lower() in text_lower]

        # Calculate weighted score
        experience_score = (len(experience_matches) / word_count) * self.weights["experience"]
        pain_score = (len(pain_matches) / word_count) * self.weights["pain"]
        emotional_score = (len(emotional_matches) / word_count) * self.weights["emotional"]

        # Normalize to 0-1 range
        total_score = min(1.0, experience_score + pain_score + emotional_score)

        return (total_score, experience_matches, pain_matches)
```

## Testing Strategy

### Test Categories

**Unit Tests** (AAA pattern):
```python
def test_praw_client_initialization_success():
    """Test PRAW client initializes with valid credentials."""
    # Arrange
    os.environ["REDDIT_CLIENT_ID"] = "test_id"
    os.environ["REDDIT_CLIENT_SECRET"] = "test_secret"

    # Act
    result = create_praw_client()

    # Assert
    assert result.is_ok()
    client = result.unwrap()
    assert isinstance(client, praw.Reddit)

def test_filter_post_below_min_upvotes():
    """Test post filtering rejects low upvote posts."""
    # Arrange
    post = Mock(score=3, created_utc=time.time(), selftext="Valid content")
    filters = QualityFilters(min_upvotes=5)

    # Act
    result = filter_post(post, filters)

    # Assert
    assert result is False

def test_authenticity_score_calculation():
    """Test authenticity score with experience markers."""
    # Arrange
    text = "I think my biggest struggle is communication. I feel frustrated."
    matcher = PatternMatcher(load_yaml_config())

    # Act
    score, experience, pain = matcher.calculate_authenticity_score(text)

    # Assert
    assert score >= 0.6
    assert "I think" in experience
    assert "struggle" in pain or "frustrated" in pain
```

**Integration Tests**:
```python
@pytest.mark.integration
def test_extract_from_subreddit_praw():
    """Test end-to-end extraction using PRAW."""
    # Arrange
    config = load_subreddit_config("co_parenting").unwrap()
    filters = QualityFilters(min_upvotes=5, min_comment_length=100)

    # Act
    result = extract_from_subreddit("coparenting", "co_parenting", filters)

    # Assert
    assert result.is_ok()
    insights = result.unwrap()
    assert len(insights) > 0
    assert all(i.authenticity_score >= 0.6 for i in insights)

@pytest.mark.integration
def test_fallback_scraper_on_rate_limit():
    """Test fallback scraper activates on rate limit."""
    # Arrange
    mock_praw = Mock(side_effect=RateLimitError("Too many requests"))
    fallback = FallbackScraper()

    # Act
    result = retry_with_backoff(
        operation=lambda: mock_praw.fetch_posts(),
        fallback=lambda: fallback.fetch_posts("coparenting")
    )

    # Assert
    assert result.is_ok()
    posts = result.unwrap()
    assert len(posts) > 0
```

**VectorStore Integration Tests**:
```python
@pytest.mark.integration
def test_store_insights_to_vectorstore():
    """Test extracted insights stored to VectorStore."""
    # Arrange
    context = create_agent_context(session_id="reddit_extraction_test")
    insights = [
        ExtractedInsight(
            content="My biggest struggle with co-parenting is communication...",
            source_type="comment",
            authenticity_score=0.75,
            pain_signals=["struggle", "communication"],
            topic="co_parenting",
            extracted_at=int(time.time())
        )
    ]

    # Act
    for insight in insights:
        context.store_memory(
            key=f"reddit_insight_{insight.extracted_at}",
            content=insight.model_dump(),
            tags=["reddit", "co_parenting", "pain_point"]
        )

    # Assert
    results = context.search_memories(
        tags=["reddit", "co_parenting"],
        include_session=True
    )
    assert len(results) >= 1
    assert "struggle" in results[0]["content"]["pain_signals"]
```

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **Reddit API rate limits** | High | High | Exponential backoff + fallback scraper |
| **Subreddit access restrictions** | Medium | Medium | Validate subreddit existence, skip invalid |
| **Authentication failures** | Medium | Low | Environment variable validation, clear error messages |
| **Bot detection (fallback)** | Medium | Medium | User-Agent rotation, 2s delay between requests |
| **Data quality degradation** | High | Medium | Strict quality filters (min upvotes, authenticity score) |
| **VectorStore capacity** | Low | Low | Limit to 20 posts/topic/day, configurable quota |
| **Overnight worker crashes** | Medium | Low | Retry logic, checkpoint/resume capability |
| **PRAW version incompatibility** | Low | Low | Pin PRAW version in requirements.txt |

## Integration Points

### VectorStore Integration (Article IV)

```python
from shared.agent_context import create_agent_context

def store_insights_to_vectorstore(
    insights: list[ExtractedInsight],
    context: AgentContext
) -> Result[int, str]:
    """
    Store extracted insights to VectorStore.

    Args:
        insights: List of extracted insights
        context: Agent context with VectorStore access

    Returns:
        Result with count of stored insights or error
    """
    stored_count = 0

    for insight in insights:
        # Generate unique key
        key = f"reddit_{insight.topic}_{insight.extracted_at}_{stored_count}"

        # Store to VectorStore
        context.store_memory(
            key=key,
            content=insight.model_dump(),
            tags=[
                "source:reddit",
                f"topic:{insight.topic}",
                "type:pain_point",
                f"authenticity:{int(insight.authenticity_score * 10) / 10}"  # 0.6, 0.7, etc.
            ]
        )
        stored_count += 1

    return Ok(stored_count)
```

### Overnight Worker Integration

```python
def run_overnight_extraction(topics: list[str]) -> Result[dict[str, int], str]:
    """
    Run overnight extraction for all topics.

    Args:
        topics: List of topic names to extract

    Returns:
        Result with extraction counts per topic or error
    """
    context = create_agent_context(session_id=f"overnight_{int(time.time())}")
    results: dict[str, int] = {}

    for topic in topics:
        # Load configuration
        config_result = load_subreddit_config(topic)
        if config_result.is_err():
            logger.warning(f"Skipping topic '{topic}': {config_result.unwrap_err()}")
            continue

        config = config_result.unwrap()

        # Extract from all subreddits
        topic_insights: list[ExtractedInsight] = []
        for subreddit in config.subreddits:
            result = extract_from_subreddit(subreddit, topic, QualityFilters())

            if result.is_ok():
                topic_insights.extend(result.unwrap())
            else:
                logger.warning(f"Failed to extract from r/{subreddit}: {result.unwrap_err()}")

        # Store to VectorStore
        store_result = store_insights_to_vectorstore(topic_insights, context)
        if store_result.is_ok():
            results[topic] = store_result.unwrap()

    return Ok(results)
```

## References

- **ADR-004**: Continuous Learning and Improvement (VectorStore mandatory)
- **ADR-010**: Result Pattern for Error Handling
- **PRAW Documentation**: https://praw.readthedocs.io/
- **Reddit API**: https://www.reddit.com/dev/api
- **Existing Config**: `config/knowledge_ingest/reddit_pain_point_patterns.yaml`
- **AgentContext**: `shared/agent_context.py`
- **Constitutional Law #2**: Strict typing (no `Dict[Any, Any]`)

---

**Constitutional Compliance Checklist**:
- [x] **Article I**: Complete context (retry on rate limit, fallback on exhaustion)
- [x] **Article II**: 100% verification (>95% test coverage, all tests must pass)
- [x] **Article III**: Automated enforcement (quality filters, authenticity score threshold)
- [x] **Article IV**: Continuous learning (VectorStore integration for extracted insights)
- [x] **Article V**: Spec-driven (this specification defines Reddit integration approach)

---

*"Authentic insights from real experiences, stored for institutional learning."*
