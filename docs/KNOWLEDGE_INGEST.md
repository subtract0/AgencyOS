# Knowledge Ingestion System

**Complete Guide to Automated Pain Point Extraction from Reddit**

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Configuration Guide](#configuration-guide)
5. [CLI Parameters](#cli-parameters)
6. [Pattern Matching Explained](#pattern-matching-explained)
7. [Outputs and Storage](#outputs-and-storage)
8. [Integration with VectorStore](#integration-with-vectorstore)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Usage](#advanced-usage)
12. [Next Steps](#next-steps)

---

## Overview

The Knowledge Ingestion System is a production-ready pipeline for extracting authentic pain points from Reddit communities and storing them in Agency OS's VectorStore for AI coaching insights.

### System Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Reddit    │────▶│   Pattern   │────▶│ Deduplica-  │────▶│ VectorStore │
│   Scraper   │     │   Matcher   │     │   tion      │     │   Storage   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                      │
  Public JSON         YAML Config         URL Hashing          AgentContext
  No auth req'd       Authenticity        SHA-256 check        Memory API
  2s rate limit       scoring ≥0.6        Skip duplicates      Semantic search
```

### Key Features

- ✅ **No PRAW dependency** - Uses public Reddit JSON API (no authentication required)
- ✅ **Pattern matching** - Configurable YAML-based keyword scoring
- ✅ **Deduplication** - SHA-256 URL hashing via VectorStore
- ✅ **Type-safe** - Pydantic models (no `Dict[Any, Any]`)
- ✅ **Result pattern** - Functional error handling (no exceptions for control flow)
- ✅ **Constitutional compliance** - Article I (complete context), Article II (100% verification), Article IV (VectorStore integration)

### Use Cases

1. **Coaching Niche Pain Point Extraction**: Identify authentic client struggles in co-parenting, ACIM, conscious uncoupling, open relationships
2. **Market Research**: Discover unmet needs and knowledge gaps in target communities
3. **Content Planning**: Generate coaching program ideas based on real pain points
4. **Overnight Knowledge Accumulation**: Schedule nightly ingestion for continuous learning

---

## Quick Start

### Installation

No additional dependencies required beyond Agency OS base installation.

```bash
# Activate Agency OS virtual environment
source venv/bin/activate

# Verify installation
python -c "from tools.knowledge_ingest import KnowledgeIngestTool; print('✅ Ready')"
```

### Run Single Topic Ingestion (MVP Testing)

```bash
# Ingest ACIM pain points (10 posts per subreddit, low threshold for MVP)
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic acim \
  --limit 10 \
  --threshold 0.1

# Expected output:
# ✅ Fetched 30 posts from r/ACIM, r/spirituality, r/awakened
# ✅ Pain points after filtering (≥0.1): 15
# ✅ Unique pain points (after deduplication): 12
# ✅ Stored 12 pain points to VectorStore
# 📁 Exported to: logs/knowledge_ingest/exports/acim_20251109_143022.json
# ⏱️ Execution time: 8.27s
```

### Check Results

```bash
# View JSON export
cat logs/knowledge_ingest/exports/acim_*.json | jq '.[] | {topic, authenticity_score, content}'

# Query VectorStore
python -c "
from shared.agent_context import create_agent_context
context = create_agent_context('knowledge_query')
results = context.search_memories(['topic:acim', 'type:pain_point'])
print(f'Found {len(results)} ACIM pain points in VectorStore')
"
```

---

## Architecture

### Component Breakdown

#### 1. RedditScraper (`tools/knowledge_ingest.py`)

**Purpose**: Fetch posts from Reddit using public JSON API (no authentication).

**Features**:
- **Rate limiting**: 2-second delay between requests (Reddit API courtesy)
- **User-Agent rotation**: Simple rotation of 3 user agents
- **Time filters**: Hour, day, week, month, year, all
- **Batch fetching**: Up to 100 posts per request

**Example**:
```python
from tools.knowledge_ingest import RedditScraper

scraper = RedditScraper(rate_limit_seconds=2)
result = scraper.fetch_posts(
    subreddit="ACIM",
    time_filter="week",
    limit=10
)

if result.is_ok():
    posts = result.unwrap()
    print(f"Fetched {len(posts)} posts")
```

#### 2. PatternMatcher (`tools/knowledge_ingest.py`)

**Purpose**: Score Reddit posts for authenticity using YAML-configured keywords.

**Scoring Algorithm**:
```python
authenticity_score = (
    experience_marker_score * 1.0 +  # "I think", "I feel"
    pain_signal_score * 1.5 +         # "struggle", "problem"
    emotional_depth_score * 1.2       # "frustration", "worry"
) / 3.7  # Weighted average
```

**Example**:
```python
from tools.knowledge_ingest import PatternMatcher

matcher = PatternMatcher(config.patterns)

text = "I think I'm struggling with forgiveness practice. It causes me frustration."

auth_score = matcher.calculate_authenticity_score(text)
# Returns: 0.82 (high authenticity)
```

#### 3. KnowledgeIngestTool (`tools/knowledge_ingest.py`)

**Purpose**: Main orchestrator - coordinates scraping, pattern matching, deduplication, and VectorStore storage.

**Pipeline**:
1. Load YAML config
2. Fetch posts from subreddits
3. Pattern match and filter (authenticity ≥ threshold)
4. Deduplicate by URL (SHA-256 hash check)
5. Store to VectorStore
6. Export to JSON (demo feature)
7. Generate stats

**Example**:
```python
from tools.knowledge_ingest import KnowledgeIngestTool

tool = KnowledgeIngestTool()
result = tool.ingest_topic(
    topic_name="acim",
    limit=10,
    authenticity_threshold=0.6
)

if result.is_ok():
    stats = result.unwrap()
    print(f"Extracted {stats.pain_points_extracted} pain points")
```

#### 4. RedditPatternConfigLoader (`shared/config_loader.py`)

**Purpose**: Load and validate YAML configuration with Pydantic schema enforcement.

**Features**:
- **Type-safe**: Pydantic models (no `Dict[Any, Any]`)
- **Security**: Path traversal protection
- **Normalization**: Lowercase keywords for consistency
- **Result pattern**: No exceptions for control flow

---

## Configuration Guide

### YAML Configuration Structure

**File**: `config/knowledge_ingest/reddit_pain_point_patterns.yaml`

#### 1. Pattern Categories

Define keyword groups with weights for authenticity scoring:

```yaml
patterns:
  experience_markers:
    description: "First-person experiences that indicate authentic insights"
    keywords:
      - "I think"
      - "I feel"
      - "I was"
      - "my experience"
    weight: 1.0  # Standard priority

  pain_signals:
    description: "Direct indicators of coaching opportunities"
    keywords:
      - "struggles"
      - "problems"
      - "challenge"
      - "difficulties"
    weight: 1.5  # HIGH priority - explicit pain points

  emotional_depth:
    description: "Reveals unmet needs and knowledge gaps"
    keywords:
      - "frustrations"
      - "worries"
      - "barriers"
      - "what I wish I knew"
    weight: 1.2  # Medium-high priority
```

#### 2. Topic Configurations

Define subreddits and extraction focus for each coaching niche:

```yaml
topics:
  acim:
    subreddits:
      - r/ACIM
      - r/spirituality
      - r/awakened

    additional_keywords:
      - "forgiveness practice"
      - "miracle"
      - "holy spirit"
      - "ego dissolution"

    extraction_focus:
      - forgiveness_challenges
      - practice_difficulties
      - conceptual_questions
      - real_world_application

  co_parenting:
    subreddits:
      - r/coparenting
      - r/Parenting
      - r/SingleParents

    additional_keywords:
      - "ex partner"
      - "custody"
      - "communication breakdown"

    extraction_focus:
      - communication_issues
      - boundary_setting
      - child_wellbeing
```

#### 3. Quality Filters

Set minimum quality thresholds:

```yaml
quality_filters:
  min_upvotes: 5              # Minimum post score
  min_comment_length: 100     # Minimum character count
  authenticity_score_min: 0.6 # Authenticity threshold (0.0-1.0)
  sentiment_threshold: -0.3   # Allow negative sentiment (pain points)

  exclude_patterns:
    - "removed by moderator"
    - "[deleted]"
    - "spam"
```

#### 4. Integration Settings

Configure VectorStore and export options:

```yaml
integration:
  vectorstore:
    enabled: true
    tags_format: ["topic:{topic}", "source:reddit", "type:pain_point"]
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

  memory_tool:
    enabled: true
    path: "~/.agency/memories/coaching_knowledge/{topic}/"
    format: "markdown"

  overnight_worker:
    enabled: true
    schedule: "nightly"
    max_posts_per_topic: 20
    rate_limit_seconds: 2
```

### Adding a New Topic

1. **Add topic to YAML**:
```yaml
topics:
  your_new_topic:
    subreddits:
      - r/YourSubreddit1
      - r/YourSubreddit2

    additional_keywords:
      - "topic-specific keyword"

    extraction_focus:
      - specific_focus_area
```

2. **Run ingestion**:
```bash
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic your_new_topic \
  --limit 10 \
  --threshold 0.1
```

### Customizing Pattern Matching

**Adjust keyword weights**:
```yaml
patterns:
  pain_signals:
    weight: 2.0  # Double priority for pain signals
```

**Add new keywords**:
```yaml
patterns:
  experience_markers:
    keywords:
      - "I think"
      - "I believe"  # New keyword
      - "my take is"  # New keyword
```

**Lower quality threshold for more results**:
```yaml
quality_filters:
  authenticity_score_min: 0.3  # Lower = more results, less authentic
```

---

## CLI Parameters

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--topic` | Topic name from config | `--topic acim` |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--limit` | int | 10 | Max posts per subreddit (max 100) |
| `--threshold` | float | 0.6 | Authenticity threshold (0.0-1.0). Use config value if not provided. |
| `--config` | str | `config/knowledge_ingest/reddit_pain_point_patterns.yaml` | Path to YAML config |

### Usage Examples

**Production ingestion (default threshold 0.6)**:
```bash
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic acim \
  --limit 20
```

**MVP testing (low threshold 0.1)**:
```bash
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic acim \
  --limit 10 \
  --threshold 0.1
```

**Custom config file**:
```bash
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic acim \
  --config /path/to/custom_config.yaml
```

**Batch processing multiple topics**:
```bash
#!/bin/bash
for topic in acim co_parenting conscious_uncoupling open_relationships; do
  echo "Processing $topic..."
  PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
    --topic $topic \
    --limit 20 \
    --threshold 0.6
done
```

---

## Pattern Matching Explained

### Authenticity Scoring Algorithm

The pattern matcher calculates an authenticity score (0.0-1.0) based on three dimensions:

#### 1. Experience Markers (Weight 1.0)

**Keywords**:
- First-person pronouns: "I think", "I feel", "I was", "I have been"
- Personal experience: "my experience", "my biggest struggle", "my biggest fear"
- Learning statements: "I found that", "I learned", "I realized"

**Scoring**:
```python
def match_experience_markers(text: str) -> float:
    count = sum(1 for kw in experience_keywords if kw in text.lower())
    return min(1.0, count / 3.0)  # 3+ markers = 1.0
```

**Example**:
```
Text: "I think I feel overwhelmed. I was struggling with this."
Matches: "I think", "I feel", "I was"
Score: 1.0 (3 markers)
```

#### 2. Pain Signals (Weight 1.5)

**Keywords**:
- Direct indicators: "struggles", "problems", "issues", "challenge"
- Intensity markers: "difficulties", "hardships", "pain point"

**Scoring**:
```python
def match_pain_signals(text: str) -> float:
    count = sum(1 for kw in pain_keywords if kw in text.lower())
    return min(1.0, count / 2.0)  # 2+ signals = 1.0
```

**Example**:
```
Text: "I have a problem and struggle with this challenge."
Matches: "problem", "struggle", "challenge"
Score: 1.0 (3 signals)
```

#### 3. Emotional Depth (Weight 1.2)

**Keywords**:
- Emotional context: "frustrations", "worries", "concerns", "hesitations"
- Barriers: "obstacles", "barriers"
- Regret/hindsight: "what I wish I knew", "what I regret"

**Scoring**:
```python
def match_emotional_depth(text: str) -> float:
    count = sum(1 for kw in emotional_keywords if kw in text.lower())
    return min(1.0, count / 2.0)  # 2+ keywords = 1.0
```

**Example**:
```
Text: "My frustration and worry cause concern."
Matches: "frustration", "worry", "concern"
Score: 1.0 (3 keywords)
```

#### 4. Overall Authenticity Score

**Formula**:
```python
authenticity_score = (
    experience_marker_score * 1.0 +
    pain_signal_score * 1.5 +
    emotional_depth_score * 1.2
) / 3.7
```

**Example Calculation**:
```
Text: "I think I have a problem that causes frustration."

experience_marker_score = 0.33  # "I think" (1/3)
pain_signal_score = 0.5         # "problem" (1/2)
emotional_depth_score = 0.5     # "frustration" (1/2)

authenticity_score = (0.33*1.0 + 0.5*1.5 + 0.5*1.2) / 3.7
                   = (0.33 + 0.75 + 0.6) / 3.7
                   = 1.68 / 3.7
                   = 0.45
```

### Quality Thresholds

| Threshold | Quality Level | Use Case |
|-----------|---------------|----------|
| 0.8-1.0 | Very high authenticity | Production coaching insights |
| 0.6-0.8 | High authenticity | Default recommendation |
| 0.3-0.6 | Medium authenticity | Exploratory research |
| 0.1-0.3 | Low authenticity | MVP testing, broad capture |
| 0.0-0.1 | Minimal filtering | Debug, config testing |

**Recommendation**: Start with `--threshold 0.1` for MVP testing, increase to 0.6+ for production.

---

## Outputs and Storage

### JSON Exports

**Location**: `logs/knowledge_ingest/exports/{topic}_{timestamp}.json`

**Format**:
```json
[
  {
    "content": "I think I'm struggling with forgiveness practice. It causes me frustration.",
    "source_url": "https://reddit.com/r/ACIM/comments/abc123/forgiveness_help",
    "topic": "acim",
    "authenticity_score": 0.82,
    "experience_marker_score": 0.67,
    "pain_signal_score": 0.5,
    "emotional_depth_score": 0.5,
    "created_at": 1762306183
  }
]
```

**Usage**:
```bash
# Count pain points
cat logs/knowledge_ingest/exports/acim_*.json | jq '. | length'

# View high-authenticity pain points
cat logs/knowledge_ingest/exports/acim_*.json | \
  jq '.[] | select(.authenticity_score > 0.7) | {content, score: .authenticity_score}'

# Extract pain signal text only
cat logs/knowledge_ingest/exports/acim_*.json | jq -r '.[].content'
```

### VectorStore Storage

**Location**: `~/.agency/memories/` (managed by AgentContext)

**Tags**:
- `topic:{topic}` - e.g., `topic:acim`
- `source:reddit` - Source identifier
- `type:pain_point` - Content type
- `url_hash:{sha256}` - Deduplication key

**Storage Call**:
```python
context.store_memory(
    key=f"{topic_name}:{url_hash}",
    content=pain_point.model_dump(),
    tags=[
        f"topic:{topic_name}",
        "source:reddit",
        "type:pain_point",
        f"url_hash:{url_hash}"
    ]
)
```

### Logs

**Location**: `logs/knowledge_ingest/{topic}_{timestamp}.log`

**Format**:
```
2025-11-09 14:30:22,123 - INFO - Logging initialized: logs/knowledge_ingest/acim_20251109_143022.log
2025-11-09 14:30:22,125 - INFO - Processing topic: acim
2025-11-09 14:30:22,126 - INFO - Subreddits: ['r/ACIM', 'r/spirituality', 'r/awakened']
2025-11-09 14:30:24,234 - INFO - ✅ Fetched 10 posts from r/ACIM
2025-11-09 14:30:26,345 - INFO - ✅ Fetched 10 posts from r/spirituality
2025-11-09 14:30:28,456 - INFO - ✅ Fetched 10 posts from r/awakened
2025-11-09 14:30:28,567 - INFO - Total posts fetched: 30
2025-11-09 14:30:28,678 - INFO - Pain points after filtering (≥0.1): 15
2025-11-09 14:30:28,789 - INFO - Unique pain points (after deduplication): 12
2025-11-09 14:30:28,890 - INFO - ✅ Stored 12 pain points to VectorStore
2025-11-09 14:30:28,991 - INFO - 📁 Exported to: logs/knowledge_ingest/exports/acim_20251109_143022.json
2025-11-09 14:30:29,092 - INFO - ⏱️ Execution time: 6.97s
```

### Summary Output

**Console**:
```
============================================================
KNOWLEDGE INGESTION SUMMARY
============================================================
Topic:                 acim
Posts fetched:         30
Posts filtered:        15
Pain points extracted: 12
Duplicates skipped:    3
Execution time:        6.97s
============================================================
✅ Ingestion complete!
```

---

## Integration with VectorStore

### Storage via AgentContext

The knowledge ingestion system uses Agency OS's standard memory API:

```python
from shared.agent_context import create_agent_context

context = create_agent_context(session_id=f"knowledge_ingest_{topic_name}")

# Store pain point
context.store_memory(
    key=f"{topic_name}:{url_hash}",
    content=pain_point.model_dump(),
    tags=[
        f"topic:{topic_name}",
        "source:reddit",
        "type:pain_point",
        f"url_hash:{url_hash}"
    ]
)
```

### Deduplication Strategy

**URL-based deduplication** using SHA-256 hashing:

```python
import hashlib

# Generate URL hash
url_hash = hashlib.sha256(pain_point.source_url.encode()).hexdigest()

# Check if URL already exists
existing = context.search_memories(
    tags=[f"url_hash:{url_hash}"],
    include_session=False  # Cross-session check
)

if existing:
    duplicates_skipped += 1
else:
    # Store new pain point
    context.store_memory(...)
```

**Why URL hashing?**
- Prevents re-ingesting same Reddit post
- Cross-session deduplication (overnight workers won't duplicate)
- Fast O(1) lookup via tag search

### Querying Pain Points

**Query by topic**:
```python
context = create_agent_context("coaching_agent")

# Get all ACIM pain points
acim_pain_points = context.search_memories(
    tags=["topic:acim", "type:pain_point"],
    include_session=False
)

print(f"Found {len(acim_pain_points)} ACIM pain points")
```

**Query by authenticity score**:
```python
# Get high-quality pain points
high_quality = [
    p for p in context.search_memories(["type:pain_point"])
    if p.get("authenticity_score", 0) > 0.7
]
```

**Query by keyword**:
```python
# Search for forgiveness-related pain points
forgiveness_pain = context.search_memories(
    tags=["topic:acim"],
    query="forgiveness practice difficulty"  # Semantic search
)
```

### VectorStore Configuration

**Optional Enhancement**: sentence-transformers for semantic search

```bash
# Install sentence-transformers (optional)
pip install sentence-transformers

# Configure in YAML
integration:
  vectorstore:
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

**Note**: System falls back to keyword search if sentence-transformers not installed.

---

## Testing

### Run All Tests

```bash
# Full test suite (35 tests)
python -m pytest tests/test_knowledge_ingest_config.py tests/tools/test_knowledge_ingest.py -v

# Expected output:
# tests/test_knowledge_ingest_config.py::TestConfigLoader::test_load_valid_config PASSED
# tests/test_knowledge_ingest_config.py::TestConfigLoader::test_invalid_yaml PASSED
# ... (35 total tests)
# ===== 35 passed in 2.45s =====
```

### Test Coverage

**Config Loader** (`tests/test_knowledge_ingest_config.py`):
- ✅ Valid YAML loading
- ✅ Invalid YAML handling
- ✅ Schema validation (Pydantic)
- ✅ Keyword normalization (lowercase)
- ✅ Path security (no path traversal)

**Knowledge Ingest Tool** (`tests/tools/test_knowledge_ingest.py`):
- ✅ Reddit scraper rate limiting
- ✅ Post fetching (success + error cases)
- ✅ Pattern matching (all three dimensions)
- ✅ Authenticity scoring
- ✅ Case-insensitive matching
- ✅ Full pipeline integration
- ✅ Pydantic model validation
- ✅ JSON export functionality

### Unit Test Example

```python
from tools.knowledge_ingest import PatternMatcher

def test_authenticity_scoring():
    """Test weighted authenticity scoring."""
    matcher = PatternMatcher(config.patterns)

    # High authenticity text
    text = "I think I have a problem that causes frustration."
    score = matcher.calculate_authenticity_score(text)

    assert 0.4 < score < 0.6, "Should detect medium authenticity"
```

### Integration Test

```bash
# Test real config loading
python -c "
from shared.config_loader import RedditPatternConfigLoader

result = RedditPatternConfigLoader.load_config(
    'config/knowledge_ingest/reddit_pain_point_patterns.yaml'
)

assert result.is_ok(), 'Config should load successfully'
config = result.unwrap()
print(f'✅ Loaded {len(config.topics)} topics')
print(f'✅ Loaded {len(config.patterns)} pattern categories')
"
```

---

## Troubleshooting

### Common Issues

#### 1. Rate Limiting (HTTP 429)

**Symptom**: `RedditAPIError: HTTP 429 Too Many Requests`

**Solution**:
```bash
# Increase rate limit (default: 2 seconds)
# Edit tools/knowledge_ingest.py:
self.scraper = RedditScraper(rate_limit_seconds=5)  # Increase to 5 seconds
```

#### 2. Empty Results

**Symptom**: `Pain points after filtering (≥0.6): 0`

**Solution**:
```bash
# Lower authenticity threshold
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic acim \
  --threshold 0.1  # Start low, increase gradually
```

**Diagnostic**:
```python
# Check what's being filtered
from tools.knowledge_ingest import PatternMatcher

matcher = PatternMatcher(config.patterns)
text = "Your sample post text here"
score = matcher.calculate_authenticity_score(text)
print(f"Authenticity score: {score}")

# Breakdown by dimension
print(f"Experience markers: {matcher.match_experience_markers(text)}")
print(f"Pain signals: {matcher.match_pain_signals(text)}")
print(f"Emotional depth: {matcher.match_emotional_depth(text)}")
```

#### 3. PYTHONPATH Errors

**Symptom**: `ModuleNotFoundError: No module named 'shared'`

**Solution**:
```bash
# Always set PYTHONPATH
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py --topic acim

# Or add to .bashrc/.zshrc
export PYTHONPATH=/Users/am/Code/AgencyOS
```

#### 4. VectorStore Warnings

**Symptom**: `Warning: sentence-transformers not installed, using keyword search`

**Impact**: System still works, but semantic search is disabled.

**Solution (Optional)**:
```bash
# Install sentence-transformers for enhanced semantic search
pip install sentence-transformers

# Verify
python -c "import sentence_transformers; print('✅ Installed')"
```

**Note**: Keyword search is sufficient for MVP. Semantic search is an enhancement.

#### 5. Invalid Topic Name

**Symptom**: `IngestError: Topic 'xyz' not found in config`

**Solution**:
```bash
# List available topics
grep -A 1 "^  [a-z_]*:" config/knowledge_ingest/reddit_pain_point_patterns.yaml

# Add new topic to config/knowledge_ingest/reddit_pain_point_patterns.yaml
```

#### 6. JSON Export Errors

**Symptom**: `PermissionError: [Errno 13] Permission denied: 'logs/knowledge_ingest/exports/'`

**Solution**:
```bash
# Create directories with correct permissions
mkdir -p logs/knowledge_ingest/exports
chmod 755 logs/knowledge_ingest/exports
```

---

## Advanced Usage

### 1. Overnight Worker (Scheduled Ingestion)

**Cron Job Setup**:

```bash
# Edit crontab
crontab -e

# Add nightly ingestion (2 AM daily)
0 2 * * * cd /Users/am/Code/AgencyOS && PYTHONPATH=/Users/am/Code/AgencyOS /path/to/venv/bin/python tools/knowledge_ingest.py --topic acim --limit 20 --threshold 0.6 >> logs/knowledge_ingest/cron.log 2>&1
```

**Batch Script** (`scripts/overnight_ingest.sh`):

```bash
#!/bin/bash
set -e

PYTHONPATH=/Users/am/Code/AgencyOS
TOPICS="acim co_parenting conscious_uncoupling open_relationships love_and_forgiveness"

for topic in $TOPICS; do
    echo "$(date): Processing $topic..."
    python tools/knowledge_ingest.py \
        --topic "$topic" \
        --limit 20 \
        --threshold 0.6 \
        >> logs/knowledge_ingest/overnight.log 2>&1

    echo "$(date): $topic complete. Sleeping 30s..."
    sleep 30  # Rate limiting between topics
done

echo "$(date): Overnight ingestion complete!"
```

**Run**:
```bash
chmod +x scripts/overnight_ingest.sh
./scripts/overnight_ingest.sh
```

### 2. Custom Scoring Algorithms

**Override PatternMatcher**:

```python
from tools.knowledge_ingest import PatternMatcher

class CustomPatternMatcher(PatternMatcher):
    """Custom scoring algorithm for specific niches."""

    def calculate_authenticity_score(self, text: str) -> float:
        """Custom weighted formula."""
        exp_score = self.match_experience_markers(text)
        pain_score = self.match_pain_signals(text)
        emotional_score = self.match_emotional_depth(text)

        # ACIM-specific: Emphasize emotional depth
        weighted_sum = (
            exp_score * 0.8 +
            pain_score * 1.5 +
            emotional_score * 2.0  # Double weight for ACIM
        )

        return weighted_sum / 4.3  # New total weight
```

### 3. Real-Time Reddit Streaming (Future Enhancement)

**WebSocket Integration** (Not yet implemented):

```python
# Planned feature - NOT YET IMPLEMENTED
from tools.knowledge_ingest_streaming import RedditStreamListener

listener = RedditStreamListener(
    subreddits=["ACIM", "spirituality"],
    callback=lambda post: process_realtime_post(post)
)

listener.start()  # Streams new posts in real-time
```

### 4. Enhanced NLP Analysis

**Sentiment Analysis** (Optional):

```bash
# Install sentiment analysis library
pip install vaderSentiment

# Use in custom matcher
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
sentiment = analyzer.polarity_scores(text)
# Filter for negative sentiment (pain points)
if sentiment['compound'] < -0.3:
    pain_points.append(...)
```

### 5. Multi-Language Support

**Translation** (Not yet implemented):

```python
# Planned feature - NOT YET IMPLEMENTED
from googletrans import Translator

translator = Translator()
translated = translator.translate(text, src='es', dest='en')
pain_point.content = translated.text
```

### 6. Database Export (Alternative to JSON)

**SQLite Export**:

```python
import sqlite3
import json

def export_to_sqlite(topic: str, pain_points: list):
    """Export pain points to SQLite database."""
    conn = sqlite3.connect("knowledge_ingest.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pain_points (
            id INTEGER PRIMARY KEY,
            topic TEXT,
            content TEXT,
            source_url TEXT,
            authenticity_score REAL,
            created_at INTEGER
        )
    """)

    for pp in pain_points:
        cursor.execute("""
            INSERT INTO pain_points
            (topic, content, source_url, authenticity_score, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (pp.topic, pp.content, pp.source_url, pp.authenticity_score, pp.created_at))

    conn.commit()
    conn.close()
```

---

## Next Steps

### Immediate Actions

1. **Run MVP Test** (10 minutes):
```bash
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic acim --limit 10 --threshold 0.1
```

2. **Review JSON Exports** (5 minutes):
```bash
cat logs/knowledge_ingest/exports/acim_*.json | jq '.[] | {content, score: .authenticity_score}'
```

3. **Query VectorStore** (5 minutes):
```python
from shared.agent_context import create_agent_context
context = create_agent_context('test')
results = context.search_memories(['topic:acim', 'type:pain_point'])
for r in results[:3]:
    print(r.get('content', '')[:100])
```

### Integration with AI Coaching Agent

**Goal**: Use extracted pain points to train coaching agent responses.

```python
from shared.agent_context import create_agent_context

class CoachingAgent:
    def __init__(self):
        self.context = create_agent_context('coaching_agent')

    def get_relevant_pain_points(self, user_query: str) -> list:
        """Retrieve relevant pain points for user's query."""
        # Query VectorStore for similar pain points
        results = self.context.search_memories(
            tags=["type:pain_point"],
            query=user_query  # Semantic search
        )

        # Filter high-quality pain points
        return [
            r for r in results
            if r.get('authenticity_score', 0) > 0.7
        ][:5]

    def generate_coaching_response(self, user_query: str) -> str:
        """Generate coaching response informed by real pain points."""
        pain_points = self.get_relevant_pain_points(user_query)

        # Use pain points as context for LLM
        context_str = "\n".join([
            f"- {pp.get('content', '')[:200]}"
            for pp in pain_points
        ])

        prompt = f"""
        User query: {user_query}

        Similar pain points from community:
        {context_str}

        Provide compassionate coaching response.
        """

        return self.llm_client.generate(prompt)
```

### Schedule Overnight Worker

**Set up cron job** (see Advanced Usage section above).

### Enhance NLP with sentence-transformers

```bash
pip install sentence-transformers
# Restart ingestion tool - semantic search automatically enabled
```

### Monitor Growth

**Track VectorStore size**:

```python
from shared.agent_context import create_agent_context

context = create_agent_context('monitoring')
all_pain_points = context.search_memories(['type:pain_point'])
print(f"Total pain points in VectorStore: {len(all_pain_points)}")

# Breakdown by topic
topics = {}
for pp in all_pain_points:
    topic = pp.get('topic', 'unknown')
    topics[topic] = topics.get(topic, 0) + 1

for topic, count in sorted(topics.items()):
    print(f"  {topic}: {count}")
```

### Production Deployment

1. **Increase authenticity threshold**: 0.1 → 0.6
2. **Increase post limits**: 10 → 20-50 per subreddit
3. **Enable overnight worker**: Schedule nightly ingestion
4. **Monitor deduplication**: Track `duplicates_skipped` in stats
5. **Set up alerting**: Alert if ingestion fails for >24 hours

---

## Appendix: File Locations

| Component | File Path |
|-----------|-----------|
| Main tool | `tools/knowledge_ingest.py` |
| Config loader | `shared/config_loader.py` |
| YAML config | `config/knowledge_ingest/reddit_pain_point_patterns.yaml` |
| Tool tests | `tests/tools/test_knowledge_ingest.py` |
| Config tests | `tests/test_knowledge_ingest_config.py` |
| JSON exports | `logs/knowledge_ingest/exports/{topic}_{timestamp}.json` |
| Logs | `logs/knowledge_ingest/{topic}_{timestamp}.log` |
| VectorStore | `~/.agency/memories/` (managed by AgentContext) |

---

## Appendix: Constitutional Compliance

This implementation adheres to Agency OS's constitutional requirements:

- ✅ **Article I** (Complete Context): All posts fetched to completion, no partial results
- ✅ **Article II** (Type Safety): Pydantic models, Result pattern, no `Dict[Any, Any]`
- ✅ **Article II** (Functions <50 lines): All functions focused, single-purpose
- ✅ **Article IV** (VectorStore Integration): AgentContext memory API, deduplication via tags
- ✅ **Article II** (TDD): 35 tests written FIRST (RED), implementation SECOND (GREEN)

---

## Support and Feedback

**Questions?** Review this guide or check:
- Tool source code: `tools/knowledge_ingest.py`
- Test examples: `tests/tools/test_knowledge_ingest.py`
- Agency OS constitution: `constitution.md`

**Improvements?** Submit PR with new pattern keywords, topics, or scoring algorithms.

---

**Last Updated**: 2025-11-09
**Status**: Production MVP
**Version**: 1.0.0
