# Pain Point Agents

Autonomous agents for collecting, processing, and analyzing pain points data.

## Agents

### 1. Goldminer V4 (`pain_point_goldminer_v4.py`)
- **Location**: `tools/pain_point_goldminer_v4.py`
- **Purpose**: 24/7 historical archive collection
- **Data**: Reddit posts going back years via PullPush API

### 2. Fresh Crawler (`fresh_pain_crawler.py`)
- **Purpose**: Collect fresh data from last 30 days
- **Features**: Trend detection, spike alerts
- **Mode**: Continuous until exhausted

### 3. Golden Opportunity Scout (`golden_opportunity_scout.py`)
- **Purpose**: Find landing page opportunities
- **Features**: Generates hypotheses, plays devil's advocate, only surfaces truly compelling opportunities
- **Mode**: 24/7 continuous

### 4. Librarian Agent (`librarian_agent.py`)
- **Purpose**: Data quality guardian
- **Features**: Deduplication, quality scoring, metadata enrichment, clustering
- **Mode**: 24/7 continuous

### 5. ChromaDB Indexer (`index_to_chromadb.py`)
- **Purpose**: Index pain points for semantic search
- **Storage**: `/Volumes/Satechi4TB/pain_points/chromadb_index/`

## Data Storage

All data stored on external drive: `/Volumes/Satechi4TB/pain_points/`

```
pain_points/
├── raw/                    # Raw crawled data
├── fresh/                  # Fresh crawler output
├── opportunities/          # Golden opportunity scout output
│   ├── golden/            # Approved opportunities
│   └── rejected/          # Rejected (for learning)
├── librarian/             # Librarian agent output
│   ├── reports/           # Quality reports
│   ├── clusters/          # Story clusters
│   └── quarantine/        # Flagged low-quality
└── chromadb_index/        # Vector search index
```

## Running

```bash
# Check running agents
ps aux | grep -E "goldminer|fresh_pain|golden_opportunity|librarian" | grep python

# Logs
tail -f /Volumes/Satechi4TB/pain_points/fresh/continuous.log
tail -f /Volumes/Satechi4TB/pain_points/opportunities/scout_continuous.log
tail -f /Volumes/Satechi4TB/pain_points/librarian/continuous.log
```
