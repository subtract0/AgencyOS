# Specification: 24/7 Knowledge Ingestion System

**Spec ID**: `spec-036-knowledge-ingestion-system`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-11-09
**Last Updated**: 2025-11-09
**Related Plan**: `plan-036-knowledge-ingestion-system.md` (to be created)
**Related ADRs**: ADR-004 (Continuous Learning), ADR-006 (Memory Architecture)
**Related Config**: `config/knowledge_ingest/reddit_pain_point_patterns.yaml`

---

## Executive Summary

Implement a 24/7 autonomous knowledge ingestion pipeline that continuously mines coaching niche pain points from Reddit, performs emotional analysis, validates authenticity, deduplicates content, and stores insights in VectorStore for semantic retrieval. The system operates overnight, building institutional knowledge through pattern-based extraction with zero manual intervention.

**Key Innovation**: Fully autonomous learning loop that transforms raw social media content into structured, queryable coaching intelligence using proven pattern-matching (config YAML) and VectorStore integration (Article IV compliance).

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Autonomous overnight execution mining 20 posts per topic per night (100 posts/night across 5 topics)
- [ ] **Goal 2**: Pattern-based pain point extraction using proven YAML configuration (experience markers, pain signals, emotional depth)
- [ ] **Goal 3**: VectorStore integration with semantic search enabling coaching niche queries (e.g., "co-parenting communication issues")
- [ ] **Goal 4**: Deduplication strategy preventing redundant storage (URL hash + content similarity threshold ≥0.85)
- [ ] **Goal 5**: Rate limiting compliance for Reddit API (60 req/min with fallback to scraping)
- [ ] **Goal 6**: Emotional analysis pipeline (sentiment, authenticity scoring) for quality filtering

### Success Metrics
- **Ingestion Rate**: 100 high-quality posts/night (20 per topic × 5 topics)
- **Deduplication Accuracy**: ≥95% duplicate detection rate
- **Authenticity Score**: ≥80% posts meet 0.6 authenticity threshold
- **VectorStore Query Performance**: <100ms semantic search latency
- **API Compliance**: Zero Reddit API violations (rate limit adherence)
- **Storage Efficiency**: <10% redundant storage after deduplication
- **Constitutional Compliance**: 100% Article IV adherence (VectorStore integration mandatory)

---

## Non-Goals

### Explicit Exclusions
- **Real-Time Ingestion**: System operates overnight (nightly batch), not real-time streaming
- **Multi-Platform Support**: Reddit-only in Phase 1 (future: Twitter, Facebook, forums)
- **Manual Curation**: 100% autonomous (no human-in-the-loop review)
- **Custom LLM Training**: Uses existing models (sentiment analysis, embeddings)
- **UI Dashboard**: Headless operation (query via VectorStore API, no UI)

### Future Considerations
- **Multi-Platform Ingestion**: Expand to Twitter, Facebook, Quora (Leap 9+)
- **Real-Time Streaming**: Event-driven ingestion for time-sensitive insights
- **Coaching AI Assistant**: Query interface for retrieving insights
- **Pattern Evolution**: LLM-driven pattern discovery (augment YAML config)
- **Quality Feedback Loop**: Store user ratings of retrieved insights

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Coaching Business Owner
- **Description**: Entrepreneur building coaching business needing authentic market insights
- **Goals**: Understand real pain points, validate coaching niche demand, identify underserved topics
- **Pain Points**: Generic market research, expensive surveys, biased focus groups, time-consuming manual research
- **Technical Proficiency**: Non-technical user (queries VectorStore via natural language API)

#### Persona 2: Learning Agent (System Persona)
- **Description**: Agent responsible for continuous knowledge acquisition (Article IV mandate)
- **Goals**: Maximize institutional knowledge growth, maintain data quality, ensure deduplication
- **Pain Points**: API rate limits, duplicate content, low-quality posts, scraping detection
- **Technical Proficiency**: Expert system operating autonomously

#### Persona 3: Coaching Content Creator
- **Description**: Coach creating content (courses, workshops, posts) needing trend insights
- **Goals**: Identify trending pain points, validate content topics, find authentic language patterns
- **Pain Points**: Content ideas disconnected from real struggles, guessing audience needs, generic content
- **Technical Proficiency**: Basic technical user (uses VectorStore query examples)

### User Journeys

#### Journey 1: Overnight Knowledge Acquisition
```
1. System starts with: Scheduled nightly cron job (2 AM daily)
2. System needs to: Acquire 100 high-quality coaching insights
3. System performs:
   - Load config (reddit_pain_point_patterns.yaml)
   - Iterate topics: [co_parenting, conscious_uncoupling, acim, open_relationships, love_and_forgiveness]
   - For each topic:
     - Construct Reddit search query (experience markers + pain signals)
     - Fetch 20 posts (Reddit API with rate limiting)
     - Extract pain points (pattern matching)
     - Analyze emotions (sentiment + authenticity scoring)
     - Deduplicate (URL hash + content similarity)
     - Store to VectorStore (tags: topic, source, type)
4. System concludes: 100 unique insights stored, deduplication stats logged
5. User achieves: Fresh coaching market insights available by morning
```

#### Journey 2: Semantic Query for Coaching Insights
```
1. User starts with: Natural language query "What are common co-parenting communication breakdowns?"
2. User needs to: Retrieve authentic pain points from VectorStore
3. User performs: VectorStore semantic search query
4. System responds:
   - Embed query (sentence-transformers)
   - Search VectorStore (cosine similarity)
   - Rank by relevance (top 10 results)
   - Return insights with metadata (post URL, upvotes, authenticity score)
5. User achieves: 10 real-world examples of co-parenting communication issues with authentic quotes
```

#### Journey 3: Deduplication Prevention
```
1. System starts with: New Reddit post fetched
2. System needs to: Prevent duplicate storage
3. System performs:
   - Generate URL hash (SHA-256)
   - Query VectorStore for matching hash
   - If no match: Calculate content similarity (cosine similarity of embeddings)
   - If similarity <0.85: Store as new insight
   - If similarity ≥0.85: Discard as duplicate, log stats
4. System achieves: Zero duplicate storage, storage efficiency >90%
```

---

## Acceptance Criteria

### Functional Criteria

#### AC-1: Pattern-Based Extraction
- [ ] System loads `reddit_pain_point_patterns.yaml` on startup
- [ ] Reddit search queries constructed from YAML patterns (experience_markers + pain_signals + emotional_depth)
- [ ] Pattern matching filters posts containing ≥1 experience marker AND ≥1 pain signal
- [ ] Extracted posts stored with metadata: `{topic, post_url, title, body, upvotes, author, created_utc}`

#### AC-2: VectorStore Integration
- [ ] All extracted insights stored to VectorStore with tags: `["topic:{topic}", "source:reddit", "type:pain_point"]`
- [ ] Embeddings generated using `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- [ ] Semantic search query returns top-k results (default k=10) in <100ms
- [ ] VectorStore stores metadata: `{post_url, upvotes, authenticity_score, sentiment_score, created_utc}`

#### AC-3: Deduplication Strategy
- [ ] URL hash (SHA-256) generated for all fetched posts
- [ ] VectorStore queried for matching URL hash before storage
- [ ] If URL hash exists: Skip storage, increment duplicate counter
- [ ] If URL hash new: Calculate content similarity (cosine similarity of embeddings)
- [ ] If content similarity ≥0.85: Skip storage, increment near-duplicate counter
- [ ] If content similarity <0.85: Store to VectorStore
- [ ] Deduplication stats logged: `{total_fetched, duplicates_by_url, duplicates_by_content, unique_stored}`

#### AC-4: Rate Limiting Compliance
- [ ] Reddit API rate limit: 60 requests/minute
- [ ] Request pacing: 1 second delay between API calls
- [ ] Exponential backoff on rate limit errors (429): 2s, 4s, 8s, 16s
- [ ] Fallback to scraping if API quota exhausted (BeautifulSoup + requests)
- [ ] Scraping rate limit: 1 request/2 seconds (avoid detection)

#### AC-5: Emotional Analysis Pipeline
- [ ] Sentiment analysis: `-1.0 (negative)` to `1.0 (positive)` using `transformers/distilbert-base-uncased-finetuned-sst-2-english`
- [ ] Authenticity scoring: `0.0` to `1.0` based on experience marker density
  - Formula: `authenticity = min(1.0, experience_marker_count / 3)`
  - Example: 3+ experience markers = 1.0 score
- [ ] Quality filtering: Posts with `authenticity_score ≥0.6` stored
- [ ] Posts with `sentiment_score >0.3` discarded (pain points should be negative/neutral)

#### AC-6: Overnight Worker Execution
- [ ] Cron schedule: Daily at 2 AM local time
- [ ] Execution time budget: 60 minutes max
- [ ] Topics processed: `[co_parenting, conscious_uncoupling, acim, open_relationships, love_and_forgiveness]`
- [ ] Posts per topic: 20 (100 total per night)
- [ ] Error handling: Failed topics logged, execution continues for remaining topics
- [ ] Success notification: Slack webhook or email summary (optional)

### Non-Functional Criteria

#### AC-7: Performance Requirements
- [ ] VectorStore semantic search: <100ms latency (p95)
- [ ] Batch insertion: 100 posts stored in <5 seconds
- [ ] Memory footprint: <512MB during execution
- [ ] Embedding generation: <50ms per post (batch embedding)

#### AC-8: Reliability Requirements
- [ ] Error recovery: Exponential backoff on API failures
- [ ] Partial failure handling: Failed topics logged, execution continues
- [ ] State persistence: Checkpoint after each topic (resume capability)
- [ ] Logging: Structured logs with topic, action, status, duration

#### AC-9: Data Quality Requirements
- [ ] Authenticity filter: ≥80% stored posts have `authenticity_score ≥0.6`
- [ ] Deduplication accuracy: ≥95% duplicate detection rate
- [ ] Pattern matching precision: ≥90% posts contain valid pain points (manual validation sample)
- [ ] Sentiment accuracy: ≥85% posts have negative/neutral sentiment (pain point validation)

### Quality Criteria (Constitutional Compliance)

#### AC-10: Article I (Complete Context)
- [ ] System loads complete YAML config before execution (no partial config)
- [ ] All topics processed to completion (no early termination)
- [ ] VectorStore query returns all results (no pagination truncation)

#### AC-11: Article IV (Continuous Learning)
- [ ] VectorStore integration mandatory (no disable flags)
- [ ] All extracted insights stored to VectorStore
- [ ] System queries VectorStore for duplicates before storage (learning from past data)
- [ ] Deduplication stats stored as learning pattern (trend analysis)

#### AC-12: Article V (Spec-Driven Development)
- [ ] Implementation follows this specification
- [ ] Technical plan created before implementation (plan-036)
- [ ] TodoWrite tasks reference spec acceptance criteria

#### AC-13: Type Safety (ADR-008)
- [ ] All data models defined with Pydantic
- [ ] Pydantic models: `PainPoint`, `ExperienceMarker`, `EmotionalSignal`, `RedditPost`, `DeduplicationStats`
- [ ] Zero `Dict[Any, Any]` usage
- [ ] 100% mypy type checking pass

#### AC-14: Result Pattern (ADR-010)
- [ ] All API calls return `Result[T, E]`
- [ ] Error handling via Result pattern (no try/catch control flow)
- [ ] Example: `fetch_reddit_posts() -> Result[list[RedditPost], RedditAPIError]`

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         24/7 Knowledge Ingestion System                  │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Orchestrator Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Cron Trigger │─▶│ Config Loader│─▶│ Topic Router │                  │
│  │   (2 AM)     │  │  (YAML)      │  │  (5 topics)  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│     Reddit Fetcher Layer    │   │   Scraper Fallback Layer    │
│  ┌────────────────────────┐ │   │  ┌────────────────────────┐ │
│  │ Reddit API Client      │ │   │  │ BeautifulSoup Scraper  │ │
│  │ - Rate Limiter (60/min)│ │   │  │ - Rate Limiter (30/min)│ │
│  │ - Exponential Backoff  │ │   │  │ - User-Agent Rotation  │ │
│  │ - OAuth Token Refresh  │ │   │  │ - Proxy Support        │ │
│  └────────────────────────┘ │   │  └────────────────────────┘ │
└──────────────┬──────────────┘   └──────────────┬──────────────┘
               │                                  │
               └──────────────┬───────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Pattern Matching Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Experience   │  │ Pain Signal  │  │ Emotional    │                  │
│  │ Marker Filter│  │ Detector     │  │ Depth Scanner│                  │
│  │ (YAML config)│  │ (YAML config)│  │ (YAML config)│                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Emotion Analysis Layer                             │
│  ┌──────────────────────────┐  ┌──────────────────────────┐            │
│  │ Sentiment Analyzer       │  │ Authenticity Scorer      │            │
│  │ - DistilBERT (SST-2)     │  │ - Experience Marker Count│            │
│  │ - Range: -1.0 to 1.0     │  │ - Formula: min(1.0, n/3) │            │
│  │ - Filter: sentiment <0.3 │  │ - Threshold: score ≥0.6  │            │
│  └──────────────────────────┘  └──────────────────────────┘            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Deduplication Layer                                │
│  ┌──────────────────────────┐  ┌──────────────────────────┐            │
│  │ URL Hash Generator       │  │ Content Similarity       │            │
│  │ - SHA-256 of post URL    │  │ - Cosine similarity      │            │
│  │ - VectorStore lookup     │  │ - Threshold: 0.85        │            │
│  │ - O(1) duplicate detect  │  │ - Embedding comparison   │            │
│  └──────────────────────────┘  └──────────────────────────┘            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         VectorStore Layer (Article IV)                   │
│  ┌──────────────────────────┐  ┌──────────────────────────┐            │
│  │ Embedding Generator      │  │ FAISS Index              │            │
│  │ - sentence-transformers  │  │ - 384-dim vectors        │            │
│  │ - all-MiniLM-L6-v2       │  │ - Cosine similarity      │            │
│  │ - Batch embedding        │  │ - Semantic search        │            │
│  └──────────────────────────┘  └──────────────────────────┘            │
│  ┌──────────────────────────┐  ┌──────────────────────────┐            │
│  │ Metadata Storage         │  │ Tag Index                │            │
│  │ - post_url, upvotes      │  │ - topic:{topic}          │            │
│  │ - authenticity_score     │  │ - source:reddit          │            │
│  │ - sentiment_score        │  │ - type:pain_point        │            │
│  └──────────────────────────┘  └──────────────────────────┘            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Anthropic Memory Tool (Tier 1)                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ ~/.agency/memories/coaching_knowledge/{topic}/insights.md        │  │
│  │ - Persistent cross-conversation storage                          │  │
│  │ - Manual review/curation capability                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Cron Trigger (2 AM daily)
   ↓
2. Load Config (reddit_pain_point_patterns.yaml)
   ↓
3. For each topic in [co_parenting, conscious_uncoupling, acim, open_relationships, love_and_forgiveness]:
   ↓
4. Construct Search Query (experience markers + pain signals + emotional depth)
   ↓
5. Fetch Posts (Reddit API with rate limiting OR scraping fallback)
   ↓
6. Pattern Matching (filter for experience markers AND pain signals)
   ↓
7. Emotion Analysis (sentiment + authenticity scoring)
   ↓
8. Quality Filter (authenticity ≥0.6, sentiment <0.3)
   ↓
9. Deduplication (URL hash + content similarity)
   ↓
10. Generate Embedding (sentence-transformers)
   ↓
11. Store to VectorStore (tags: topic, source, type)
   ↓
12. Store to Memory Tool (optional manual review)
   ↓
13. Log Stats (total fetched, duplicates, unique stored)
```

---

## Data Models (Pydantic)

### PainPoint
```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Literal

class PainPoint(BaseModel):
    """
    Extracted pain point from Reddit with metadata.

    Article IV: Stored in VectorStore for semantic retrieval.
    """
    post_id: str = Field(..., description="Reddit post ID (unique)")
    post_url: HttpUrl = Field(..., description="Full Reddit post URL")
    topic: Literal["co_parenting", "conscious_uncoupling", "acim", "open_relationships", "love_and_forgiveness"]
    title: str = Field(..., max_length=300)
    body: str = Field(..., max_length=10000)
    author: str = Field(..., max_length=100)
    upvotes: int = Field(..., ge=0)
    created_utc: datetime

    # Analysis scores
    authenticity_score: float = Field(..., ge=0.0, le=1.0, description="Experience marker density")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="DistilBERT sentiment")

    # Extraction metadata
    experience_markers: list[str] = Field(..., description="Matched experience markers")
    pain_signals: list[str] = Field(..., description="Matched pain signals")
    emotional_depth_keywords: list[str] = Field(..., description="Matched emotional keywords")

    # VectorStore metadata
    url_hash: str = Field(..., description="SHA-256 hash of post_url")
    embedding: list[float] | None = Field(None, description="384-dim sentence-transformers embedding")

    class Config:
        json_schema_extra = {
            "example": {
                "post_id": "abc123",
                "post_url": "https://reddit.com/r/coparenting/comments/abc123/...",
                "topic": "co_parenting",
                "title": "Struggling with communication after divorce",
                "body": "I think my biggest struggle is...",
                "author": "throwaway123",
                "upvotes": 47,
                "created_utc": "2025-11-08T14:30:00Z",
                "authenticity_score": 0.85,
                "sentiment_score": -0.42,
                "experience_markers": ["I think", "my biggest struggle"],
                "pain_signals": ["struggle", "issues"],
                "emotional_depth_keywords": ["frustrations"],
                "url_hash": "a3b2c1d4e5f6...",
                "embedding": [0.123, -0.456, ...]
            }
        }
```

### ExperienceMarker
```python
from pydantic import BaseModel, Field

class ExperienceMarker(BaseModel):
    """
    First-person experience phrases indicating authentic insights.

    Loaded from YAML config: patterns.experience_markers
    """
    keywords: list[str] = Field(..., description="Experience marker phrases")
    weight: float = Field(1.0, ge=0.0, le=2.0, description="Priority weight")

    class Config:
        json_schema_extra = {
            "example": {
                "keywords": ["I think", "I feel", "I was", "my experience"],
                "weight": 1.0
            }
        }
```

### EmotionalSignal
```python
from pydantic import BaseModel, Field

class EmotionalSignal(BaseModel):
    """
    Pain signals and emotional depth indicators.

    Loaded from YAML config: patterns.pain_signals, patterns.emotional_depth
    """
    pain_signals: list[str] = Field(..., description="Pain point keywords")
    emotional_depth: list[str] = Field(..., description="Emotional depth keywords")

    class Config:
        json_schema_extra = {
            "example": {
                "pain_signals": ["struggles", "problems", "challenge"],
                "emotional_depth": ["barriers", "frustrations", "worries"]
            }
        }
```

### RedditPost
```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

class RedditPost(BaseModel):
    """
    Raw Reddit post data before processing.

    Fetched from Reddit API or scraping.
    """
    post_id: str
    post_url: HttpUrl
    subreddit: str = Field(..., max_length=100)
    title: str = Field(..., max_length=300)
    body: str = Field(..., max_length=10000)
    author: str = Field(..., max_length=100)
    upvotes: int = Field(..., ge=0)
    num_comments: int = Field(..., ge=0)
    created_utc: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "post_id": "abc123",
                "post_url": "https://reddit.com/r/coparenting/comments/abc123/...",
                "subreddit": "coparenting",
                "title": "Need advice on...",
                "body": "I've been struggling with...",
                "author": "user123",
                "upvotes": 12,
                "num_comments": 8,
                "created_utc": "2025-11-08T14:30:00Z"
            }
        }
```

### DeduplicationStats
```python
from pydantic import BaseModel, Field
from datetime import datetime

class DeduplicationStats(BaseModel):
    """
    Deduplication statistics for monitoring.

    Logged after each overnight execution.
    """
    execution_date: datetime
    topic: str
    total_fetched: int = Field(..., ge=0)
    duplicates_by_url: int = Field(..., ge=0)
    duplicates_by_content: int = Field(..., ge=0)
    unique_stored: int = Field(..., ge=0)
    deduplication_rate: float = Field(..., ge=0.0, le=1.0, description="(total - unique) / total")

    class Config:
        json_schema_extra = {
            "example": {
                "execution_date": "2025-11-09T02:00:00Z",
                "topic": "co_parenting",
                "total_fetched": 20,
                "duplicates_by_url": 2,
                "duplicates_by_content": 1,
                "unique_stored": 17,
                "deduplication_rate": 0.15
            }
        }
```

---

## API Contracts

### Reddit Fetcher API

```python
from shared.type_definitions.result import Result
from typing import Literal

class RedditFetcher:
    """
    Reddit API client with rate limiting and fallback.

    Constitutional compliance:
    - Article I: Complete context (all posts fetched, no truncation)
    - Article IV: VectorStore integration (deduplicate before fetch)
    """

    def fetch_posts(
        self,
        topic: Literal["co_parenting", "conscious_uncoupling", "acim", "open_relationships", "love_and_forgiveness"],
        limit: int = 20,
        min_upvotes: int = 5
    ) -> Result[list[RedditPost], RedditAPIError]:
        """
        Fetch Reddit posts for topic using API with fallback to scraping.

        Rate limiting:
        - API: 60 requests/minute (1 second delay)
        - Scraping: 30 requests/minute (2 second delay)

        Args:
            topic: Coaching topic from YAML config
            limit: Max posts to fetch (default 20)
            min_upvotes: Minimum upvotes filter (default 5)

        Returns:
            Result[list[RedditPost], RedditAPIError]

        Raises:
            Never - uses Result pattern (ADR-010)
        """
```

### Pattern Matcher API

```python
class PatternMatcher:
    """
    Pattern-based pain point extraction.

    Constitutional compliance:
    - Article I: Complete pattern matching (no partial matches)
    - Article V: Spec-driven (YAML config defines patterns)
    """

    def match_pain_points(
        self,
        posts: list[RedditPost],
        patterns: dict[str, Any]
    ) -> Result[list[PainPoint], PatternMatchError]:
        """
        Extract pain points using YAML pattern matching.

        Pattern logic:
        - MUST contain ≥1 experience marker (first-person language)
        - MUST contain ≥1 pain signal (struggle, problem, challenge)
        - SHOULD contain emotional depth keywords (bonus weight)

        Args:
            posts: Raw Reddit posts
            patterns: Loaded from reddit_pain_point_patterns.yaml

        Returns:
            Result[list[PainPoint], PatternMatchError]
            - Only posts matching pattern criteria

        Raises:
            Never - uses Result pattern (ADR-010)
        """
```

### Emotion Analyzer API

```python
class EmotionAnalyzer:
    """
    Sentiment and authenticity analysis.

    Constitutional compliance:
    - Article II: 100% verification (all scores validated)
    - Article IV: VectorStore integration (scores stored as metadata)
    """

    def analyze_emotions(
        self,
        pain_points: list[PainPoint]
    ) -> Result[list[PainPoint], EmotionAnalysisError]:
        """
        Analyze sentiment and authenticity of pain points.

        Analysis pipeline:
        1. Sentiment analysis (DistilBERT SST-2): -1.0 to 1.0
        2. Authenticity scoring: experience_marker_count / 3 (capped at 1.0)
        3. Quality filtering: authenticity ≥0.6, sentiment <0.3

        Args:
            pain_points: Extracted pain points

        Returns:
            Result[list[PainPoint], EmotionAnalysisError]
            - Only pain points passing quality filters

        Raises:
            Never - uses Result pattern (ADR-010)
        """
```

### Deduplicator API

```python
class Deduplicator:
    """
    URL hash and content similarity deduplication.

    Constitutional compliance:
    - Article I: Complete deduplication (no false negatives)
    - Article IV: VectorStore query (check existing hashes)
    """

    def deduplicate(
        self,
        pain_points: list[PainPoint],
        vector_store: VectorStore
    ) -> Result[tuple[list[PainPoint], DeduplicationStats], DeduplicationError]:
        """
        Remove duplicate pain points using URL hash and content similarity.

        Deduplication strategy:
        1. Generate URL hash (SHA-256)
        2. Query VectorStore for matching hash (O(1) lookup)
        3. If no match: Calculate content similarity (cosine similarity)
        4. If similarity <0.85: Store as unique
        5. If similarity ≥0.85: Discard as duplicate

        Args:
            pain_points: Analyzed pain points
            vector_store: VectorStore instance for duplicate lookup

        Returns:
            Result[tuple[list[PainPoint], DeduplicationStats], DeduplicationError]
            - Unique pain points + deduplication statistics

        Raises:
            Never - uses Result pattern (ADR-010)
        """
```

### VectorStore Storage API

```python
class KnowledgeStore:
    """
    VectorStore integration for pain point storage.

    Constitutional compliance:
    - Article IV: Mandatory VectorStore integration
    - Article V: Spec-driven (follows VectorStore schema)
    """

    def store_pain_points(
        self,
        pain_points: list[PainPoint],
        vector_store: VectorStore
    ) -> Result[int, VectorStoreError]:
        """
        Store pain points to VectorStore with embeddings and tags.

        Storage schema:
        - Key: f"{topic}:{post_id}"
        - Content: PainPoint model dict
        - Tags: ["topic:{topic}", "source:reddit", "type:pain_point"]
        - Embedding: 384-dim sentence-transformers vector

        Args:
            pain_points: Unique pain points to store
            vector_store: VectorStore instance

        Returns:
            Result[int, VectorStoreError]
            - Count of successfully stored pain points

        Raises:
            Never - uses Result pattern (ADR-010)
        """

    def query_pain_points(
        self,
        query: str,
        topic: str | None = None,
        top_k: int = 10
    ) -> Result[list[PainPoint], VectorStoreError]:
        """
        Semantic search for pain points.

        Query strategy:
        - Embed query (sentence-transformers)
        - Search VectorStore (cosine similarity)
        - Filter by topic if provided
        - Rank by relevance (top-k)

        Args:
            query: Natural language query
            topic: Optional topic filter
            top_k: Max results (default 10)

        Returns:
            Result[list[PainPoint], VectorStoreError]
            - Top-k pain points ranked by relevance

        Raises:
            Never - uses Result pattern (ADR-010)
        """
```

---

## Deduplication Strategy

### URL Hash Deduplication (Primary)

**Strategy**: Generate SHA-256 hash of `post_url`, query VectorStore for matching hash.

**Advantages**:
- O(1) lookup time
- 100% accuracy (same URL = same post)
- Zero false positives

**Implementation**:
```python
import hashlib

def generate_url_hash(url: str) -> str:
    """Generate SHA-256 hash of URL."""
    return hashlib.sha256(url.encode()).hexdigest()

# Usage
url_hash = generate_url_hash(post.post_url)
existing = vector_store.search_by_tags(tags=["url_hash:" + url_hash])

if existing:
    # Duplicate detected - skip storage
    stats.duplicates_by_url += 1
else:
    # New post - proceed to content similarity check
    ...
```

### Content Similarity Deduplication (Secondary)

**Strategy**: Calculate cosine similarity between embeddings, threshold ≥0.85 = duplicate.

**Advantages**:
- Detects near-duplicates (same pain point, different URL)
- Handles reposts, cross-posts, paraphrased content

**Disadvantages**:
- O(n) comparison time (mitigated by VectorStore FAISS index)
- Potential false positives (adjust threshold 0.80-0.90)

**Implementation**:
```python
from agency_memory.vector_store import VectorStore

def check_content_similarity(
    new_pain_point: PainPoint,
    vector_store: VectorStore,
    threshold: float = 0.85
) -> bool:
    """
    Check if content is similar to existing pain points.

    Returns:
        True if duplicate (similarity ≥ threshold)
        False if unique (similarity < threshold)
    """
    # Embed new pain point
    embedding = vector_store._embedding_function([new_pain_point.body])[0]

    # Query similar pain points (same topic)
    similar = vector_store.semantic_search(
        query=new_pain_point.body,
        memories=vector_store.search_by_tags(tags=[f"topic:{new_pain_point.topic}"]),
        top_k=1
    )

    if similar and similar[0].similarity_score >= threshold:
        # Duplicate detected
        return True

    return False
```

### Deduplication Metrics

| Metric | Target | Monitoring |
|--------|--------|------------|
| URL duplicate rate | <10% | `duplicates_by_url / total_fetched` |
| Content duplicate rate | <5% | `duplicates_by_content / total_fetched` |
| Total deduplication rate | <15% | `(total_fetched - unique_stored) / total_fetched` |
| False negative rate | <1% | Manual review sample (100 posts/week) |
| Storage efficiency | >85% | `unique_stored / total_fetched` |

---

## Rate Limiting Strategy

### Reddit API Rate Limits

**Official Limits** (OAuth authenticated):
- 60 requests per minute
- 600 requests per hour

**Implementation**:
```python
import time
from datetime import datetime, timedelta

class RedditRateLimiter:
    """
    Token bucket rate limiter for Reddit API.

    Constitutional compliance:
    - Article I: Complete context (never truncate due to rate limit)
    - Article III: Automated enforcement (no manual bypass)
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = datetime.now()
        self.min_interval = 60.0 / requests_per_minute  # 1.0 second

    def acquire(self) -> None:
        """
        Acquire rate limit token (blocks if needed).

        Strategy:
        - Refill tokens every minute
        - Block if no tokens available
        - Ensure minimum 1 second between requests
        """
        now = datetime.now()

        # Refill tokens if minute elapsed
        if (now - self.last_refill) > timedelta(minutes=1):
            self.tokens = self.requests_per_minute
            self.last_refill = now

        # Wait if no tokens available
        while self.tokens <= 0:
            time.sleep(1)
            now = datetime.now()
            if (now - self.last_refill) > timedelta(minutes=1):
                self.tokens = self.requests_per_minute
                self.last_refill = now

        # Consume token
        self.tokens -= 1

        # Ensure minimum interval
        time.sleep(self.min_interval)
```

### Exponential Backoff on Errors

**Strategy**: Retry on rate limit (429) with exponential backoff.

**Backoff Schedule**:
- Attempt 1: Immediate
- Attempt 2: 2 seconds
- Attempt 3: 4 seconds
- Attempt 4: 8 seconds
- Attempt 5: 16 seconds
- Max attempts: 5

**Implementation**:
```python
from shared.type_definitions.result import Result, Ok, Err
import time

def fetch_with_backoff(
    url: str,
    max_retries: int = 5
) -> Result[dict, RedditAPIError]:
    """
    Fetch URL with exponential backoff on rate limit.

    Args:
        url: Reddit API endpoint
        max_retries: Max retry attempts (default 5)

    Returns:
        Result[dict, RedditAPIError]

    Raises:
        Never - uses Result pattern (ADR-010)
    """
    for attempt in range(max_retries):
        response = requests.get(url)

        if response.status_code == 200:
            return Ok(response.json())

        if response.status_code == 429:  # Rate limit
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
            continue

        # Other error
        return Err(RedditAPIError(f"Status {response.status_code}"))

    return Err(RedditAPIError("Max retries exceeded"))
```

### Scraping Fallback Rate Limiting

**Strategy**: If API quota exhausted, fallback to scraping with 2-second delays.

**Scraping Rate Limit**:
- 30 requests per minute (2 seconds/request)
- User-Agent rotation (3 agents)
- Respect robots.txt

**Implementation**:
```python
import time
import random

class ScraperRateLimiter:
    """
    Rate limiter for scraping fallback.

    More conservative than API to avoid detection.
    """

    def __init__(self, requests_per_minute: int = 30):
        self.min_interval = 60.0 / requests_per_minute  # 2.0 seconds
        self.last_request = datetime.now()

    def acquire(self) -> None:
        """
        Acquire scraping token with jitter.

        Strategy:
        - 2 second minimum delay
        - Add random jitter (0-500ms) to avoid pattern detection
        """
        now = datetime.now()
        elapsed = (now - self.last_request).total_seconds()

        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            jitter = random.uniform(0, 0.5)  # 0-500ms jitter
            time.sleep(wait_time + jitter)

        self.last_request = datetime.now()
```

---

## VectorStore Schema

### Storage Schema

**Key Format**: `{topic}:{post_id}`

**Example**: `co_parenting:abc123`

**Content**: PainPoint Pydantic model serialized to dict

**Tags**:
- `topic:{topic}` (e.g., `topic:co_parenting`)
- `source:reddit`
- `type:pain_point`
- `url_hash:{hash}` (for URL deduplication)

**Embedding**:
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimensions: 384
- Generation: Batch embedding (100 posts/batch)

### Query Patterns

#### Query by Topic
```python
pain_points = vector_store.search_by_tags(
    tags=["topic:co_parenting", "type:pain_point"],
    limit=20
)
```

#### Semantic Search
```python
results = vector_store.semantic_search(
    query="communication breakdown after divorce",
    memories=all_pain_points,
    top_k=10
)
```

#### Hybrid Search (Tag + Semantic)
```python
# Step 1: Filter by topic
topic_filtered = vector_store.search_by_tags(tags=["topic:co_parenting"])

# Step 2: Semantic search within topic
results = vector_store.semantic_search(
    query="boundaries with ex-partner",
    memories=topic_filtered,
    top_k=10
)
```

### Metadata Schema

**Stored Metadata**:
```json
{
  "post_url": "https://reddit.com/r/coparenting/comments/abc123/...",
  "upvotes": 47,
  "authenticity_score": 0.85,
  "sentiment_score": -0.42,
  "created_utc": "2025-11-08T14:30:00Z",
  "experience_markers": ["I think", "my biggest struggle"],
  "pain_signals": ["struggle", "communication breakdown"],
  "emotional_depth_keywords": ["frustrations", "worries"]
}
```

**Query Metadata Example**:
```python
# Filter by authenticity score
high_quality = [
    p for p in pain_points
    if p.metadata["authenticity_score"] >= 0.8
]

# Filter by upvotes
popular = [
    p for p in pain_points
    if p.metadata["upvotes"] >= 20
]
```

---

## Error Handling Strategy

### Error Categories

#### 1. API Failures
- **Rate Limit (429)**: Exponential backoff, max 5 retries
- **Authentication (401)**: Refresh OAuth token, retry once
- **Server Error (500)**: Wait 10 seconds, retry once
- **Not Found (404)**: Log error, skip post, continue execution

#### 2. Parsing Errors
- **Invalid JSON**: Log error, skip post, continue execution
- **Missing Fields**: Use defaults (e.g., `upvotes=0`), continue execution
- **Invalid URL**: Log error, skip post, continue execution

#### 3. Network Errors
- **Timeout**: Retry with 2x timeout (max 3 retries)
- **Connection Error**: Wait 5 seconds, retry once
- **DNS Error**: Log critical error, fallback to scraping

#### 4. VectorStore Errors
- **Embedding Failure**: Log warning, store without embedding (keyword search only)
- **Storage Failure**: Retry once, if fails log critical error and continue
- **Query Failure**: Return empty result, log error

### Error Handling Implementation

```python
from shared.type_definitions.result import Result, Ok, Err
import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Centralized error handling for knowledge ingestion.

    Constitutional compliance:
    - Article I: Complete context (retry on transient errors)
    - Article III: Automated enforcement (no manual intervention)
    """

    def handle_api_error(
        self,
        error: Exception,
        retry_count: int = 0,
        max_retries: int = 5
    ) -> Result[None, str]:
        """
        Handle API errors with retry logic.

        Strategy:
        - Transient errors (429, 500): Retry with backoff
        - Permanent errors (401, 404): Skip and continue
        - Critical errors (DNS, auth): Fallback to scraping

        Args:
            error: Exception raised
            retry_count: Current retry attempt
            max_retries: Max retry attempts

        Returns:
            Result[None, str]
            - Ok: Continue execution
            - Err: Critical error, halt execution
        """
        if isinstance(error, RateLimitError) and retry_count < max_retries:
            # Exponential backoff
            wait_time = 2 ** retry_count
            time.sleep(wait_time)
            logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
            return Ok(None)

        if isinstance(error, AuthenticationError):
            logger.error("Authentication failed, refresh OAuth token")
            # Trigger token refresh (implementation specific)
            return Ok(None)

        if isinstance(error, NotFoundError):
            logger.warning(f"Post not found: {error}, skipping")
            return Ok(None)

        # Critical error - halt execution
        logger.critical(f"Critical error: {error}")
        return Err(str(error))
```

---

## Dependencies

### External Dependencies
- **praw** (Python Reddit API Wrapper): `pip install praw`
- **requests**: `pip install requests`
- **beautifulsoup4**: `pip install beautifulsoup4` (scraping fallback)
- **sentence-transformers**: `pip install sentence-transformers` (embeddings)
- **transformers**: `pip install transformers` (sentiment analysis)
- **pyyaml**: `pip install pyyaml` (config loading)

### Internal Dependencies
- **agency_memory/vector_store.py**: VectorStore storage and retrieval
- **shared/type_definitions/result.py**: Result pattern
- **shared/agent_context.py**: AgentContext for memory API
- **tools/anthropic_memory_tool.py**: Tier 1 memory storage

### Configuration Dependencies
- **config/knowledge_ingest/reddit_pain_point_patterns.yaml**: Pattern definitions
- **Environment Variables**:
  - `REDDIT_CLIENT_ID`: Reddit app client ID
  - `REDDIT_CLIENT_SECRET`: Reddit app secret
  - `REDDIT_USER_AGENT`: User agent string
  - `USE_ENHANCED_MEMORY=true`: Article IV requirement

---

## Risks and Mitigations

### Risk 1: Reddit API Rate Limit Violations
- **Impact**: HIGH - Account ban, service disruption
- **Probability**: MEDIUM - Without proper rate limiting
- **Mitigation**:
  - Implement token bucket rate limiter (60 req/min)
  - Exponential backoff on 429 errors
  - Fallback to scraping if quota exhausted
  - Monitor API usage in logs

### Risk 2: Duplicate Content Storage
- **Impact**: MEDIUM - Wasted storage, degraded query performance
- **Probability**: MEDIUM - 10-15% duplicate rate expected
- **Mitigation**:
  - URL hash deduplication (primary)
  - Content similarity deduplication (secondary)
  - Target: <15% duplicate rate
  - Monitor deduplication stats daily

### Risk 3: Low-Quality Pain Point Extraction
- **Impact**: MEDIUM - Irrelevant insights, user dissatisfaction
- **Probability**: MEDIUM - Pattern matching false positives
- **Mitigation**:
  - Authenticity scoring (experience marker density)
  - Sentiment filtering (negative/neutral only)
  - Manual review sample (100 posts/week)
  - Iterative pattern refinement

### Risk 4: VectorStore Embedding Failures
- **Impact**: LOW - Fallback to keyword search
- **Probability**: LOW - sentence-transformers reliability
- **Mitigation**:
  - Batch embedding (reduce API calls)
  - Retry on transient failures
  - Fallback to keyword search if embedding fails
  - Monitor embedding success rate

### Risk 5: Overnight Execution Timeout
- **Impact**: MEDIUM - Incomplete ingestion
- **Probability**: LOW - 60-minute budget generous
- **Mitigation**:
  - Checkpoint after each topic (resume capability)
  - Execution time budget: 60 minutes
  - Alert if execution exceeds 45 minutes
  - Parallel topic processing (future optimization)

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Define Pydantic models (PainPoint, RedditPost, DeduplicationStats)
- [ ] Implement Reddit API client with rate limiting
- [ ] Implement scraping fallback (BeautifulSoup)
- [ ] Write tests (AAA pattern, >95% coverage)

### Phase 2: Pattern Matching (Week 2)
- [ ] Load YAML config (reddit_pain_point_patterns.yaml)
- [ ] Implement experience marker filter
- [ ] Implement pain signal detector
- [ ] Implement emotional depth scanner
- [ ] Write tests (pattern matching accuracy >90%)

### Phase 3: Emotion Analysis (Week 3)
- [ ] Integrate DistilBERT sentiment analysis
- [ ] Implement authenticity scoring (experience marker density)
- [ ] Implement quality filtering (authenticity ≥0.6, sentiment <0.3)
- [ ] Write tests (sentiment accuracy >85%)

### Phase 4: Deduplication (Week 4)
- [ ] Implement URL hash generation (SHA-256)
- [ ] Implement VectorStore hash lookup
- [ ] Implement content similarity calculation (cosine)
- [ ] Implement deduplication stats logging
- [ ] Write tests (deduplication accuracy >95%)

### Phase 5: VectorStore Integration (Week 5)
- [ ] Implement batch embedding generation (sentence-transformers)
- [ ] Implement VectorStore storage (tags, metadata)
- [ ] Implement semantic search query API
- [ ] Write tests (query latency <100ms)

### Phase 6: Overnight Worker (Week 6)
- [ ] Implement cron orchestrator (2 AM daily)
- [ ] Implement topic router (5 topics)
- [ ] Implement checkpoint/resume logic
- [ ] Implement error handling and logging
- [ ] Write tests (end-to-end execution)

### Phase 7: Production Deployment (Week 7)
- [ ] Deploy to production environment
- [ ] Configure cron job (2 AM daily)
- [ ] Monitor first week execution (100 posts/night target)
- [ ] Review deduplication stats (target <15%)
- [ ] Review quality metrics (authenticity ≥0.8)

---

## References

### Related ADRs
- **ADR-004**: Continuous Learning and Improvement (Article IV - VectorStore mandate)
- **ADR-006**: Three-Tier Memory Architecture (VectorStore + Memory Tool + Session)
- **ADR-008**: Strict Typing (Pydantic models mandatory)
- **ADR-010**: Result Pattern (error handling via Result<T,E>)

### Related Specifications
- **spec-002-vectorstore-harmonization.md**: VectorStore API design
- **spec-004-quality-feedback-loop.md**: Quality metrics and monitoring

### External References
- **Reddit API Documentation**: https://www.reddit.com/dev/api/
- **PRAW (Python Reddit API Wrapper)**: https://praw.readthedocs.io/
- **sentence-transformers**: https://www.sbert.net/
- **DistilBERT Sentiment**: https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english

---

## Appendix A: Example Execution Flow

### Sample Overnight Execution (2 AM - 2:15 AM)

```
02:00:00 - Cron trigger: Knowledge ingestion started
02:00:01 - Config loaded: reddit_pain_point_patterns.yaml
02:00:02 - Topic router: Processing 5 topics
02:00:03 - [co_parenting] Fetching 20 posts from Reddit API
02:01:15 - [co_parenting] Pattern matching: 18/20 posts matched
02:01:30 - [co_parenting] Emotion analysis: 15/18 passed quality filter
02:01:45 - [co_parenting] Deduplication: 2 URL duplicates, 1 content duplicate
02:02:00 - [co_parenting] VectorStore storage: 12 unique pain points stored
02:02:01 - [co_parenting] Stats: {fetched: 20, matched: 18, quality: 15, unique: 12}
02:02:02 - [conscious_uncoupling] Fetching 20 posts from Reddit API
02:03:14 - [conscious_uncoupling] Pattern matching: 16/20 posts matched
02:03:29 - [conscious_uncoupling] Emotion analysis: 14/16 passed quality filter
02:03:44 - [conscious_uncoupling] Deduplication: 1 URL duplicate, 0 content duplicates
02:03:59 - [conscious_uncoupling] VectorStore storage: 13 unique pain points stored
02:04:00 - [conscious_uncoupling] Stats: {fetched: 20, matched: 16, quality: 14, unique: 13}
... (repeat for acim, open_relationships, love_and_forgiveness)
02:14:30 - Execution complete: 85 unique pain points stored (100 fetched, 15% deduplication rate)
02:14:31 - Stats summary:
            - co_parenting: 12 stored
            - conscious_uncoupling: 13 stored
            - acim: 18 stored
            - open_relationships: 20 stored
            - love_and_forgiveness: 22 stored
02:14:32 - Deduplication summary:
            - URL duplicates: 8
            - Content duplicates: 7
            - Total deduplication rate: 15.0%
02:14:33 - VectorStore stats:
            - Total memories: 1,485 (1,400 previous + 85 new)
            - Embedding coverage: 100%
            - Average authenticity score: 0.78
02:14:34 - Knowledge ingestion completed successfully
```

---

## Appendix B: VectorStore Query Examples

### Example 1: Find Co-Parenting Communication Issues
```python
from agency_memory.vector_store import VectorStore

vector_store = VectorStore()

results = vector_store.semantic_search(
    query="communication breakdown with ex-partner after divorce",
    memories=vector_store.search_by_tags(tags=["topic:co_parenting"]),
    top_k=10
)

for result in results:
    pain_point = PainPoint(**result.memory)
    print(f"Post: {pain_point.title}")
    print(f"Authenticity: {pain_point.authenticity_score:.2f}")
    print(f"Sentiment: {pain_point.sentiment_score:.2f}")
    print(f"Body: {pain_point.body[:200]}...")
    print(f"URL: {pain_point.post_url}")
    print("---")
```

### Example 2: Find High-Quality Insights (Authenticity ≥0.8)
```python
# Query all pain points
all_pain_points = vector_store.search_by_tags(tags=["type:pain_point"])

# Filter by authenticity score
high_quality = [
    p for p in all_pain_points
    if p["authenticity_score"] >= 0.8
]

print(f"Found {len(high_quality)} high-quality pain points (authenticity ≥0.8)")
```

### Example 3: Trend Analysis (Top Pain Signals by Topic)
```python
from collections import Counter

# Query pain points for topic
topic_pain_points = vector_store.search_by_tags(tags=["topic:co_parenting"])

# Extract pain signals
all_pain_signals = []
for p in topic_pain_points:
    all_pain_signals.extend(p["pain_signals"])

# Count frequency
pain_signal_counts = Counter(all_pain_signals)

print("Top 10 pain signals for co-parenting:")
for signal, count in pain_signal_counts.most_common(10):
    print(f"  {signal}: {count}")
```

---

**END OF SPECIFICATION**

---

## Approval Status

**Status**: Draft (Pending PlannerAgent review)
**Next Steps**:
1. Create technical plan (plan-036-knowledge-ingestion-system.md)
2. Generate TodoWrite task breakdown
3. Begin Phase 1 implementation (Foundation)

**Constitutional Compliance Verified**:
- [x] Article I: Complete context (comprehensive architecture)
- [x] Article IV: VectorStore integration (mandatory)
- [x] Article V: Spec-driven (follows spec-kit template)
- [x] ADR-008: Strict typing (Pydantic models defined)
- [x] ADR-010: Result pattern (API contracts specified)
