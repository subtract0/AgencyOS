# Doorway Clusterer - Technical Specification

**Purpose**: Group pain points into "doorway themes" - the entry points people use to find their way to freedom.

**Philosophy**: Every cluster is a door. The content of the suffering varies (relationship, health, career), but the cause is the same: identification with thought.

---

## 1. Input

```
/Volumes/Satechi4TB/pain_points/raw/*.json
```

Each file contains:
```json
{
  "content": "Full post text",
  "source_url": "https://reddit.com/...",
  "source_platform": "reddit",
  "topic": "depression",
  "authenticity_score": 0.73,
  "suffering_indicators": ["i'm lost", "nothing works", ...],
  "created_at": 1704412800,
  "metadata": {
    "subreddit": "depression",
    "upvotes": 45,
    "num_comments": 23
  }
}
```

---

## 2. Output

### Doorway Theme Report

```json
{
  "generated_at": "2026-01-12T06:00:00Z",
  "total_pain_points_analyzed": 2847,
  "doorways": [
    {
      "id": "doorway-001",
      "name": "Relationship Anxiety & Obsession",
      "volume": 847,
      "avg_authenticity": 0.71,
      "core_fear": "Abandonment - belief that love is conditional and can be lost",
      "surface_problems": [
        "Can't stop thinking about ex",
        "Jealousy consuming the relationship",
        "Fear of intimacy/commitment",
        "Obsessive checking partner's phone"
      ],
      "dominant_subreddits": ["BreakUps", "relationship_advice", "ExNoContact"],
      "suffering_indicators": ["i can't let go", "obsessed", "what if they leave"],
      "representative_posts": [
        {
          "excerpt": "I check his location 50 times a day...",
          "authenticity": 0.78,
          "url": "https://..."
        }
      ],
      "acim_angle": "The ego's need for special love - using another to complete yourself",
      "potential_doorway_message": "What if the obsession isn't about them?"
    }
  ]
}
```

### Human-Readable Summary

```markdown
# Doorway Analysis Report - Week of 2026-01-12

## Top 10 Doorways (by volume)

### 1. Relationship Anxiety (847 people)
**They think**: "If I can just fix this relationship / get them back / stop being jealous..."
**The truth**: They're trying to find peace through another person
**Door opener**: "What if the obsession isn't about them?"

### 2. Existential Emptiness (634 people)
...
```

---

## 3. Algorithm

### Step 1: Load & Filter

```python
# Load all pain points from raw files
pain_points = load_all_pain_points("/Volumes/Satechi4TB/pain_points/raw/")

# Filter by minimum authenticity
pain_points = [p for p in pain_points if p.authenticity_score >= 0.3]

# Deduplicate by content similarity (>0.95 cosine = duplicate)
pain_points = deduplicate(pain_points, threshold=0.95)
```

### Step 2: Generate Embeddings

```python
from openai import OpenAI

client = OpenAI()  # Uses OPENAI_API_KEY

embeddings = []
for pp in pain_points:
    # Use title + first 500 chars of content
    text = pp.content[:500]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    embeddings.append(response.data[0].embedding)
```

**Alternative (local)**: Use `nomic-embed-text` via LM Studio for $0 cost.

### Step 3: Cluster

```python
import hdbscan
import numpy as np

# HDBSCAN - finds natural clusters without specifying count
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=50,      # Minimum 50 posts per doorway
    min_samples=10,
    metric='euclidean',
    cluster_selection_method='eom'
)

cluster_labels = clusterer.fit_predict(np.array(embeddings))
```

### Step 4: Analyze Each Cluster

For each cluster, use LLM to extract:

```python
prompt = f"""Analyze these {len(cluster_posts)} posts from people suffering.

Posts:
{cluster_samples}

Extract:
1. DOORWAY NAME: A 2-4 word name for this type of suffering
2. CORE FEAR: What are they really afraid of? (not the surface issue)
3. SURFACE PROBLEMS: What do they THINK the problem is? (list 3-5)
4. ACIM ANGLE: How would A Course in Miracles see this suffering?
5. DOOR OPENER: One question or statement that could crack their thinking open

Be direct. No fluff. Speak like someone who sees through the illusion."""
```

### Step 5: Rank Doorways

```python
# Score = volume * avg_authenticity * engagement_factor
for doorway in doorways:
    doorway.score = (
        doorway.volume * 0.4 +
        doorway.avg_authenticity * 100 * 0.3 +
        doorway.avg_engagement * 0.3
    )

doorways.sort(key=lambda x: x.score, reverse=True)
```

---

## 4. Implementation

### File: `tools/doorway_clusterer.py`

```python
#!/usr/bin/env python3
"""
Doorway Clusterer - Group pain points into entry door themes.

Usage:
  python tools/doorway_clusterer.py --input /Volumes/Satechi4TB/pain_points/raw
  python tools/doorway_clusterer.py --min-points 500  # Wait for more data
"""

import argparse
import json
import hdbscan
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
from openai import OpenAI

@dataclass
class Doorway:
    id: str
    name: str
    volume: int
    avg_authenticity: float
    core_fear: str
    surface_problems: List[str]
    dominant_subreddits: List[str]
    suffering_indicators: List[str]
    representative_posts: List[Dict]
    acim_angle: str
    door_opener: str
    score: float = 0.0

class DoorwayClusterer:
    def __init__(self, input_path: str, min_cluster_size: int = 50):
        self.input_path = Path(input_path)
        self.min_cluster_size = min_cluster_size
        self.client = OpenAI(
            api_key="not-needed",
            base_url="http://localhost:1234/v1"
        )

    def load_pain_points(self) -> List[Dict]:
        """Load all pain points from raw JSON files."""
        points = []
        for f in self.input_path.glob("*.json"):
            with open(f) as fp:
                data = json.load(fp)
                points.extend(data)
        return points

    def generate_embeddings(self, points: List[Dict]) -> np.ndarray:
        """Generate embeddings for all pain points."""
        # Use local embedding model
        embeddings = []
        for p in points:
            text = p['content'][:500]
            response = self.client.embeddings.create(
                model="text-embedding-nomic-embed-text-v1.5",
                input=text
            )
            embeddings.append(response.data[0].embedding)
        return np.array(embeddings)

    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings using HDBSCAN."""
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=10,
            metric='euclidean'
        )
        return clusterer.fit_predict(embeddings)

    def analyze_cluster(self, posts: List[Dict]) -> Doorway:
        """Use LLM to analyze a cluster and extract doorway info."""
        # Implementation here
        pass

    def run(self) -> List[Doorway]:
        """Run the full clustering pipeline."""
        points = self.load_pain_points()
        embeddings = self.generate_embeddings(points)
        labels = self.cluster(embeddings)
        # ... etc
        pass
```

---

## 5. Schedule

Run clustering:
- **Weekly**: Every Sunday at midnight
- **Trigger**: When total pain points > 1000 AND new data since last run

```bash
# Cron entry
0 0 * * 0 cd /Users/am/Code/AgencyOS && python tools/doorway_clusterer.py
```

---

## 6. Output Location

```
/Volumes/Satechi4TB/pain_points/
├── raw/                          # Input: pain points
├── analysis/                     # Hourly goldminer analysis
├── daily_summaries/              # Daily goldminer summaries
└── doorway_reports/              # NEW: Clusterer output
    ├── doorways_20260112.json    # Machine-readable
    └── doorways_20260112.md      # Human-readable
```

---

## 7. Dependencies

```bash
pip install hdbscan numpy scikit-learn openai
```

---

## 8. Success Criteria

| Metric | Target |
|--------|--------|
| Clusters identified | 10-30 doorways |
| Noise ratio | < 20% unclustered |
| Cluster coherence | Posts in same cluster discuss similar suffering |
| Actionable output | Each doorway has clear "door opener" message |

---

## 9. Next Steps After Clustering

1. **Human Review**: Alex reviews top 10 doorways
2. **Door Selection**: Pick 1-3 to build first
3. **Door Builder**: Generate landing pages + ads for selected doorways
4. **Test**: Run one campaign, measure conversion
5. **Iterate**: Refine based on real-world data
