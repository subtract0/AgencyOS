# Knowledge Ingestion Tool - README

## Overview

Production-ready MVP tool that implements the complete pipeline:

**Reddit → Pattern Matching → VectorStore**

## Features

- ✅ **Reddit Scraper**: No PRAW dependency (uses public JSON API)
- ✅ **Pattern Matcher**: YAML config-based authenticity scoring
- ✅ **VectorStore Integration**: AgentContext memory API (Article IV)
- ✅ **Deduplication**: URL hash-based duplicate prevention
- ✅ **JSON Export**: Demonstration output for verification
- ✅ **Constitutional Compliance**: Result<T,E> pattern, strict typing, functions <50 lines

## Installation

No additional dependencies required beyond Agency OS base requirements:
- `requests` (Reddit API)
- `pyyaml` (config loading)
- `pydantic` (type safety)

## Quick Start

### Basic Usage

```bash
# Ingest ACIM pain points (5 posts per subreddit)
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic acim \
  --limit 5

# Ingest co-parenting pain points with custom threshold
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic co_parenting \
  --limit 10 \
  --threshold 0.05
```

### Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--topic` | ✅ Yes | - | Topic name from config (e.g., `acim`, `co_parenting`) |
| `--limit` | No | 10 | Max posts to fetch per subreddit |
| `--threshold` | No | 0.6 | Authenticity score threshold (0.0-1.0) |
| `--config` | No | `config/knowledge_ingest/reddit_pain_point_patterns.yaml` | Path to config YAML |

### Available Topics

As defined in `config/knowledge_ingest/reddit_pain_point_patterns.yaml`:

- `co_parenting` - Co-parenting challenges (r/coparenting, r/Parenting, etc.)
- `conscious_uncoupling` - Relationship endings (r/Divorce, r/BreakUps)
- `acim` - A Course In Miracles (r/ACIM, r/spirituality)
- `open_relationships` - Non-monogamy (r/polyamory, r/nonmonogamy)
- `love_and_forgiveness` - Self-improvement (r/selfimprovement, r/DecidingToBeBetter)

## Output

### 1. Console Summary

```
============================================================
KNOWLEDGE INGESTION SUMMARY
============================================================
Topic:                 co_parenting
Posts fetched:         12
Posts filtered:        8
Pain points extracted: 8
Duplicates skipped:    0
Execution time:        8.27s
============================================================
✅ Ingestion complete!
```

### 2. Log File

Located in `logs/knowledge_ingest/{topic}_{timestamp}.log`

Example: `logs/knowledge_ingest/co_parenting_20251109_011801.log`

### 3. JSON Export

Located in `logs/knowledge_ingest/exports/{topic}_{timestamp}.json`

Example structure:
```json
[
  {
    "content": "Post title and body combined...",
    "source_url": "https://reddit.com/r/coparenting/comments/...",
    "topic": "co_parenting",
    "authenticity_score": 0.090,
    "experience_marker_score": 0.333,
    "pain_signal_score": 0.0,
    "emotional_depth_score": 0.0,
    "created_at": 1762306183
  }
]
```

### 4. VectorStore

Pain points are stored to VectorStore with tags:
- `topic:{topic}` (e.g., `topic:co_parenting`)
- `source:reddit`
- `type:pain_point`
- `url_hash:{sha256}` (for deduplication)

**Note**: VectorStore is in-memory by default. For persistent storage, configure Firestore backend via `USE_FIRESTORE=true`.

## Architecture

### Pipeline Stages

1. **Config Loader**: Load YAML pattern configuration
2. **Reddit Scraper**: Fetch posts from subreddits (public JSON API)
3. **Pattern Matcher**: Score posts by authenticity (experience markers, pain signals, emotional depth)
4. **Quality Filter**: Filter by authenticity threshold (default: 0.6)
5. **Deduplicator**: Skip duplicate URLs (SHA-256 hash check)
6. **VectorStore**: Store to AgentContext memory
7. **Export**: Write to JSON for demonstration

### Pattern Scoring

**Authenticity Score** = Weighted average of:
- **Experience Markers** (weight: 1.0): First-person language ("I think", "I feel", "my experience")
- **Pain Signals** (weight: 1.5): Explicit pain points ("struggles", "problems", "challenge")
- **Emotional Depth** (weight: 1.2): Emotional context ("frustrations", "worries", "concerns")

**Formula**:
```
authenticity = (exp * 1.0 + pain * 1.5 + emotional * 1.2) / 3.7
```

### Rate Limiting

- **2 seconds** between Reddit API requests
- **User-Agent rotation**: 3 different agents
- **Public API**: No authentication required (Reddit JSON endpoints)

## Configuration

### YAML Pattern Config

Located at: `config/knowledge_ingest/reddit_pain_point_patterns.yaml`

Key sections:
- `patterns`: Experience markers, pain signals, emotional depth keywords
- `topics`: Subreddit lists and additional keywords per topic
- `quality_filters`: Authenticity threshold, min upvotes, exclude patterns
- `integration`: VectorStore and Memory Tool settings

### Adjusting Threshold

The default `authenticity_score_min: 0.6` in the config may be too strict for some topics.

**Options**:

1. **CLI Override** (recommended for testing):
   ```bash
   python tools/knowledge_ingest.py --topic acim --threshold 0.05
   ```

2. **Edit Config** (for permanent change):
   ```yaml
   quality_filters:
     authenticity_score_min: 0.3  # Lower threshold
   ```

### Adding New Topics

Edit `config/knowledge_ingest/reddit_pain_point_patterns.yaml`:

```yaml
topics:
  my_new_topic:
    subreddits:
      - r/MySubreddit1
      - r/MySubreddit2
    additional_keywords:
      - "specific keyword"
      - "another term"
    extraction_focus:
      - theme_1
      - theme_2
```

## Constitutional Compliance

### Article I: Complete Context
- ✅ All posts fetched to completion (no truncation)
- ✅ Rate limiting ensures API reliability

### Article II: Type Safety & Verification
- ✅ Pydantic models: `RedditPost`, `PainPoint`, `IngestionStats`
- ✅ Zero `Dict[Any, Any]` usage
- ✅ Result<T,E> pattern for all operations
- ✅ All functions <50 lines

### Article IV: VectorStore Integration
- ✅ AgentContext memory API (mandatory)
- ✅ `store_memory()` for all pain points
- ✅ URL hash deduplication via VectorStore query
- ✅ Tags: `topic:{topic}`, `source:reddit`, `type:pain_point`

## Troubleshooting

### Issue: 0 pain points extracted

**Cause**: Authenticity threshold too high (default: 0.6)

**Solution**: Lower threshold with `--threshold 0.05`

### Issue: VectorStore memories not persistent

**Expected behavior**: In-memory VectorStore loses data when process ends.

**Solution**: For persistence:
1. Set `USE_FIRESTORE=true` in environment
2. Configure Firestore credentials
3. Or use Anthropic Memory Tool for file-based persistence

### Issue: Reddit API rate limit

**Cause**: Too many requests in short time

**Solution**: Tool automatically enforces 2-second delays. If still hitting limits:
- Reduce `--limit` parameter
- Increase `rate_limit_seconds` in code

## Examples

### Example 1: Test with Small Sample

```bash
PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
  --topic co_parenting \
  --limit 3 \
  --threshold 0.05
```

**Output**:
```
Posts fetched:         12
Pain points extracted: 8
Execution time:        8.27s
```

### Example 2: Production Run (Overnight Worker)

```bash
# Ingest 20 posts per topic (5 topics = 100 total)
for topic in co_parenting conscious_uncoupling acim open_relationships love_and_forgiveness; do
  PYTHONPATH=/Users/am/Code/AgencyOS python tools/knowledge_ingest.py \
    --topic $topic \
    --limit 20 \
    --threshold 0.3
done
```

### Example 3: Verify JSON Export

```bash
# Check exported pain points
cat logs/knowledge_ingest/exports/co_parenting_*.json | jq '.[0] | {
  topic,
  authenticity_score,
  source_url,
  content: .content[:100]
}'
```

**Output**:
```json
{
  "topic": "co_parenting",
  "authenticity_score": 0.09,
  "source_url": "https://reddit.com/r/coparenting/comments/1oopqmi/...",
  "content": "Daughter desperately wants us to do something together..."
}
```

## Metrics

**Expected Performance**:
- **Fetch Rate**: ~2.5 posts/second (rate limiting)
- **Processing**: ~100ms per post (pattern matching)
- **Deduplication**: O(1) URL hash lookup
- **Total Time**: ~10 seconds for 20 posts

## Future Enhancements

**Phase 2** (from spec):
- Sentiment analysis (DistilBERT)
- Content similarity deduplication (cosine similarity ≥0.85)
- Scraping fallback (BeautifulSoup)
- Cron scheduler (overnight execution)

**Phase 3**:
- Multi-platform support (Twitter, Facebook)
- Real-time streaming
- LLM-driven pattern discovery

## Related Documentation

- **Spec**: `specs/spec-036-knowledge-ingestion-system.md`
- **Config**: `config/knowledge_ingest/reddit_pain_point_patterns.yaml`
- **Config Loader**: `shared/config_loader.py`
- **AgentContext**: `shared/agent_context.py`
- **Article IV**: `constitution.md` (VectorStore mandate)

---

**Version**: 1.0 MVP
**Created**: 2025-11-09
**Status**: Production-Ready
