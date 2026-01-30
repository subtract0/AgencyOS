# Pain Point Agents

Autonomous agents for collecting, processing, and analyzing pain points data.

## Two Parallel Systems

We run two systems in parallel for different purposes:

### System 1: Suffering Database (Copywriting Research)
**Purpose**: Capture victim language, emotional expressions, and the exact words people use when in pain. This is gold for copywriting - understanding how people describe their problems.

**Subreddits**: Mental health, loneliness, relationships, trauma, etc.
**Value**: Voice of customer research, emotional resonance in copy

### System 2: Grand Slam Offer Miner (Hormozi-Style)
**Purpose**: Find actual business opportunities where people will PAY. Uses Alex Hormozi's Value Equation to identify offers people would feel dumb saying no to.

**Subreddits**: Entrepreneur, Fitness, Career, Finance, Skills, etc.
**Value**: Viable business opportunities with proven purchase intent

---

## System 1 Agents (Suffering Database)

### 1. Goldminer V4 (`pain_point_goldminer_v4.py`)
- **Location**: `tools/pain_point_goldminer_v4.py`
- **Purpose**: 24/7 historical archive collection
- **Data**: Reddit posts going back years via PullPush API

### 2. Fresh Crawler (`fresh_pain_crawler.py`)
- **Purpose**: Collect fresh data from last 30 days
- **Features**: Trend detection, spike alerts
- **Mode**: Continuous until exhausted

### 3. Golden Opportunity Scout (`golden_opportunity_scout.py`)
- **Purpose**: Find landing page opportunities from suffering data
- **Features**: Generates hypotheses, plays devil's advocate
- **Mode**: 24/7 continuous
- **Note**: Very strict - most get rejected (by design)

### 4. Librarian Agent (`librarian_agent.py`)
- **Purpose**: Data quality guardian
- **Features**: Deduplication, quality scoring, metadata enrichment, clustering
- **Mode**: 24/7 continuous (2-hour cycles)

### 5. ChromaDB Indexer (`index_to_chromadb.py`)
- **Purpose**: Index pain points for semantic search
- **Storage**: `/Volumes/Satechi4TB/pain_points/chromadb_index/`

### 6. Rejection Aggregator (`rejection_aggregator.py`)
- **Purpose**: Find meta-patterns in rejected opportunities
- **Features**: Clusters rejections by theme, generates meta-opportunities
- **Output**: `opportunities/meta_opportunities.json`

---

## System 2 Agents (Grand Slam Offers)

### 1. Grand Slam Miner (`grand_slam_miner.py`)
- **Purpose**: Hormozi-style offer discovery
- **Markets**: B2B, Wealth, Career, Fitness, Relationships (non-crisis)
- **Features**:
  - Mines for offer signals (purchase intent, failed solutions, dream outcomes)
  - Uses Value Equation: (Dream Outcome × Likelihood) / (Time × Effort)
  - Generates stacked offers (bonuses, guarantees, scarcity)
- **Storage**: `/Volumes/Satechi4TB/pain_points/grand_slam/`
- **Mode**: Continuous (4h mining, 12h offer generation)

---

## Data Storage

All data stored on external drive: `/Volumes/Satechi4TB/pain_points/`

```
pain_points/
├── raw/                    # Raw crawled data (Goldminer)
├── fresh/                  # Fresh crawler output
├── opportunities/          # Golden opportunity scout output
│   ├── golden/            # Approved opportunities
│   ├── rejected/          # Rejected (for learning)
│   └── meta_opportunities.json  # Aggregated patterns
├── librarian/             # Librarian agent output
│   ├── reports/           # Quality reports
│   ├── clusters/          # Story clusters
│   └── quarantine/        # Flagged low-quality
├── chromadb_index/        # Vector search (suffering DB)
└── grand_slam/            # Hormozi-style opportunities
    ├── signals/           # Raw offer signals
    ├── chromadb_offers/   # Vector search (offer signals)
    ├── offers/            # Generated offers
    ├── golden/            # Grand Slam offers
    └── rejected/          # Non-grand-slam offers
```

## Running

```bash
# Check all running agents
ps aux | grep -E "goldminer|fresh_pain|golden_opportunity|librarian|grand_slam" | grep python

# System 1 Logs (Suffering DB)
tail -f /Volumes/Satechi4TB/pain_points/fresh/continuous.log
tail -f /Volumes/Satechi4TB/pain_points/opportunities/scout_continuous.log
tail -f /Volumes/Satechi4TB/pain_points/librarian/continuous.log

# System 2 Logs (Grand Slam)
tail -f /Volumes/Satechi4TB/pain_points/grand_slam/miner_*.log

# Start Grand Slam Miner (continuous)
cd /Volumes/Satechi4TB/pain_points
nohup python3 grand_slam_miner.py --mining-interval 4 --offer-interval 12 > grand_slam/continuous.log 2>&1 &

# Run Rejection Aggregator (one-time analysis)
python3 rejection_aggregator.py
```

## Key Insights

### Why Two Systems?

The suffering database is invaluable for copywriting but NOT for finding business opportunities because:
- Mental health markets have legal/clinical liability
- People are venting, not buying
- Evidence doesn't match commercial hypotheses

The Grand Slam system targets markets where people:
- Already spend money (proven purchase intent)
- Want transformation (not just relief)
- Have clear, measurable outcomes

### Hormozi Value Equation

```
Value = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort)
```

Grand Slam offers maximize the numerator (big dreams, high believability) and minimize the denominator (fast results, low effort).
