# Specification: Reddit Pattern Matching Engine for AI Coaching Intelligence

**Spec ID**: `spec-pattern-matching-engine`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-11-09
**Last Updated**: 2025-11-09
**Related Specs**: `spec-005-advanced-pattern-recognition.md`, `spec-017-pattern-library-learning-dashboard.md`
**Related ADRs**: `ADR-004: Continuous Learning`, `ADR-007: Spec-Driven Development`
**Related Config**: `config/knowledge_ingest/reddit_pain_point_patterns.yaml`

---

## Executive Summary

Build an intelligent pattern matching engine that extracts authentic coaching insights from Reddit conversations by detecting experience markers, pain signals, and emotional depth indicators. Using TF-IDF feature extraction and regex-based pattern recognition, the system identifies high-value content for AI coaching optimization across ACIM, relationships, co-parenting, and other coaching niches. The engine feeds VectorStore with semantically-rich, contextually-tagged insights for real-time coaching relevance.

**Key Innovation**: Hybrid approach combining statistical (TF-IDF) and symbolic (regex) methods with emotional depth scoring (0.0-1.0 scale), ensuring high precision while minimizing false positives.

---

## Goals

### Primary Goals

- **Goal 1**: Define comprehensive experience marker taxonomy (time markers, emotional transitions, relationship states) for authentic insight detection
- **Goal 2**: Categorize pain signal patterns (regret, wish, struggle, confusion, hurt) with weighted importance scoring
- **Goal 3**: Specify emotional depth scoring algorithm (0.0-1.0 scale) based on vulnerability, specificity, and context richness
- **Goal 4**: Design TF-IDF feature extraction strategy for coaching domain relevance and semantic similarity
- **Goal 5**: Document niche-specific regex patterns (ACIM, relationships, co-parenting) with contextual boundaries
- **Goal 6**: Define false positive filtering strategy (spam detection, bot identification, low-quality content removal)

### Success Metrics

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| **Precision** | N/A (new) | >85% | Manual review of 100 extracted posts |
| **Recall** | N/A (new) | >70% | Sample 100 relevant posts, check extraction |
| **Emotional Depth Accuracy** | N/A | >80% | Human ratings vs. algorithm scores (n=50) |
| **False Positive Rate** | N/A | <10% | Spam/irrelevant content in extracted set |
| **TF-IDF Relevance** | N/A | >75% | Cosine similarity to coaching corpus |
| **Processing Speed** | N/A | <500ms/post | Latency from raw text to scored extraction |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Real-time Reddit API scraping (overnight batch processing only)
- **Non-Goal 2**: Sentiment analysis beyond emotional depth (no positive/negative classification)
- **Non-Goal 3**: User identity tracking or profiling (privacy-first, content-only extraction)
- **Non-Goal 4**: Cross-platform pattern matching (Reddit-only for v1)
- **Non-Goal 5**: Machine learning-based pattern discovery (rule-based + TF-IDF for v1)

### Future Considerations

- **Future Enhancement 1**: ML-powered pattern discovery (unsupervised clustering of pain points)
- **Future Enhancement 2**: Multi-platform support (Twitter, Discord, specialized forums)
- **Future Enhancement 3**: Active learning (user feedback refines pattern weights)
- **Future Enhancement 4**: Temporal trend detection (emerging pain points over time)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: AI Coaching Agent (Primary Consumer)

- **Description**: Claude-based coaching assistant querying VectorStore for authentic user experiences
- **Goals**: Access real pain points, understand language patterns, provide empathetic responses
- **Pain Points**: Generic responses without real-world context, missing nuanced emotional states
- **Technical Proficiency**: VectorStore query interface, semantic search, tag-based filtering

#### Persona 2: Overnight Knowledge Worker (System Component)

- **Description**: Automated nightly job extracting coaching insights from Reddit
- **Goals**: High-quality extraction, minimal false positives, efficient processing, VectorStore integration
- **Pain Points**: API rate limits, spam filtering, pattern drift, storage costs
- **Technical Proficiency**: Reddit API, pattern matching engine, VectorStore integration

#### Persona 3: Coaching Niche Specialist (@am - Quality Reviewer)

- **Description**: Domain expert reviewing extracted patterns for coaching relevance
- **Goals**: High precision, authentic experiences, actionable insights, minimal noise
- **Pain Points**: False positives waste review time, low emotional depth = generic advice
- **Technical Proficiency**: Coaching expertise, pattern quality assessment

### User Journeys

#### Journey 1: Authentic Experience Detection (Core Use Case)

```
1. System starts with: Raw Reddit comment "I was terrified of co-parenting after divorce..."
2. Pattern engine performs:
   - Experience marker detection: "I was" (first-person past tense)
   - Pain signal detection: "terrified" (emotional intensity)
   - Emotional depth scoring: High vulnerability (0.82/1.0)
   - TF-IDF extraction: ["co-parenting", "divorce", "terrified", "communication"]
   - Niche classification: co_parenting (based on keyword + subreddit context)
3. System achieves:
   - Authentic score: 0.85 (above 0.6 threshold)
   - Emotional depth: 0.82 (above 0.5 threshold)
   - Relevance: 0.91 cosine similarity to coaching corpus
   - VectorStore tags: ["co_parenting", "fear", "divorce_transition", "source:reddit"]
4. Result: Extracted to VectorStore, available for coaching agent queries
```

#### Journey 2: False Positive Filtering (Quality Control)

```
1. System starts with: Reddit comment "[removed by moderator]"
2. Pattern engine performs:
   - Experience marker detection: None found
   - Spam pattern detection: "removed by moderator" (blocklist match)
   - Authenticity check: 0.0 (immediate rejection)
3. System achieves:
   - Filtered out before TF-IDF computation
   - No VectorStore storage
   - Processing time: <50ms (fast reject)
4. Result: False positive avoided, storage costs saved
```

#### Journey 3: Niche-Specific Pattern Matching (ACIM Example)

```
1. System starts with: r/ACIM post "My biggest struggle with forgiveness practice..."
2. Pattern engine performs:
   - Experience marker: "My biggest struggle" (pain + first-person)
   - Pain signal: "struggle" (difficulty indicator)
   - ACIM regex: "forgiveness practice" (domain-specific term)
   - Emotional depth: 0.68 (moderate vulnerability)
   - TF-IDF features: ["forgiveness", "practice", "struggle", "ACIM"]
3. System achieves:
   - Niche: acim (high confidence)
   - Emotional depth: 0.68 (above threshold)
   - Authenticity: 0.79 (strong match)
   - VectorStore tags: ["acim", "forgiveness_challenges", "practice_difficulties"]
4. Result: Tagged for ACIM coaching queries, semantically indexed
```

#### Journey 4: Emotional Depth Scoring (Algorithm Validation)

```
1. System starts with: Two posts with similar keywords but different depth:
   Post A: "Divorce is hard." (generic, low depth)
   Post B: "I wish I knew how much my kids would blame themselves..." (vulnerable, high depth)

2. Pattern engine performs:
   Post A:
   - Vulnerability markers: None
   - Specificity: Generic statement
   - Length: 3 words (very short)
   - Emotional depth: 0.15 (below 0.5 threshold)

   Post B:
   - Vulnerability markers: "I wish I knew" (regret + uncertainty)
   - Specificity: Children's self-blame (concrete, nuanced)
   - Length: 11 words (adequate context)
   - Emotional depth: 0.88 (high vulnerability + specificity)

3. System achieves:
   - Post A: Rejected (low depth, no extraction)
   - Post B: Extracted (authentic insight, high coaching value)
   - Precision: Avoided generic noise

4. Result: Only high-depth content stored, coaching agent gets valuable insights
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Experience Marker Taxonomy

- **AC-1.1**: Experience markers categorized into 4 types: first-person indicators, time markers, emotional transitions, relationship states
- **AC-1.2**: First-person indicators: "I think", "I feel", "I was", "I have been", "my experience", "in my opinion", "IMO" (12+ phrases)
- **AC-1.3**: Time markers: "before", "after", "when I", "since", "now I realize" (temporal context indicators)
- **AC-1.4**: Emotional transitions: "I used to X but now Y", "I learned that", "I realized", "my advice" (growth indicators)
- **AC-1.5**: Relationship states: "my ex", "co-parent", "our kids", "my partner" (relational context)
- **AC-1.6**: Each marker has weight (0.5-2.0) reflecting authenticity strength

#### Feature Component 2: Pain Signal Patterns

- **AC-2.1**: Pain signals categorized into 5 types: regret, wish, struggle, confusion, hurt
- **AC-2.2**: Regret patterns: "I wish I knew", "what I regret", "if only", "I should have" (8+ phrases, weight=1.8)
- **AC-2.3**: Wish patterns: "I hope", "I want to understand", "what I wish" (desire for growth, weight=1.5)
- **AC-2.4**: Struggle patterns: "struggles", "problems", "difficulties", "challenges", "hardships" (12+ terms, weight=1.5)
- **AC-2.5**: Confusion patterns: "I don't understand", "confused about", "unclear why" (knowledge gaps, weight=1.2)
- **AC-2.6**: Hurt patterns: "pain point", "hurt", "frustration", "worries", "concerns" (emotional intensity, weight=1.4)

#### Feature Component 3: Emotional Depth Scoring Algorithm

- **AC-3.1**: Emotional depth score: 0.0-1.0 scale (0.0=generic, 1.0=deeply vulnerable)
- **AC-3.2**: Vulnerability component (40% weight): Presence of regret/wish/hurt patterns, first-person emotional language
- **AC-3.3**: Specificity component (30% weight): Concrete details vs. abstract statements, named entities, temporal markers
- **AC-3.4**: Context richness component (30% weight): Word count (>50 words = higher), sentence complexity, relational context
- **AC-3.5**: Formula: `depth = 0.4*vulnerability + 0.3*specificity + 0.3*context_richness`
- **AC-3.6**: Threshold: depth >= 0.5 required for extraction (filters generic noise)

#### Feature Component 4: TF-IDF Feature Extraction Strategy

- **AC-4.1**: TF-IDF vectorizer trained on coaching domain corpus (ACIM texts, relationship advice, parenting forums)
- **AC-4.2**: Vocabulary: Top 500 coaching-relevant terms (domain-specific + pain signals + emotional language)
- **AC-4.3**: N-gram range: 1-3 (captures "co-parenting", "forgiveness practice", "conscious uncoupling")
- **AC-4.4**: Stop words: Extended English stop words + Reddit-specific noise ("edit:", "update:", "TL;DR")
- **AC-4.5**: Cosine similarity threshold: >0.65 to coaching corpus (filters off-topic content)
- **AC-4.6**: Feature vector: 500-dim TF-IDF + 8-dim metadata (length, depth, authenticity, upvotes, comment_count, subreddit_id, niche_id, timestamp)

#### Feature Component 5: Niche-Specific Regex Patterns

- **AC-5.1**: ACIM niche: `r"(forgiveness practice|miracle|holy spirit|ego dissolution|course in miracles|ACIM lesson)"` (case-insensitive)
- **AC-5.2**: Co-parenting niche: `r"(co-?parent|custody|visitation|parenting plan|ex partner|shared custody|parallel parent)"` (10+ patterns)
- **AC-5.3**: Relationships niche: `r"(conscious uncoupling|peaceful divorce|healthy breakup|ending relationship|separation|relationship issues)"` (12+ patterns)
- **AC-5.4**: Open relationships: `r"(polyamory|ethical non-monogamy|ENM|jealousy management|boundaries|compersion)"` (8+ patterns)
- **AC-5.5**: Forgiveness niche: `r"(letting go|healing from hurt|self-forgiveness|compassion practice|resentment|grudge)"` (10+ patterns)
- **AC-5.6**: Regex optimization: Compiled patterns cached, boundary matching (`\b...\b`) to avoid substring false positives

#### Feature Component 6: False Positive Filtering Strategy

- **AC-6.1**: Spam detection: Blocklist of Reddit moderation patterns ("removed by moderator", "[deleted]", "spam")
- **AC-6.2**: Bot identification: Username patterns (`r".*bot$"`, `r"auto.*"`), repetitive content (>80% similarity to previous posts)
- **AC-6.3**: Low-quality filters: Minimum upvotes (5+), minimum length (100 chars), negative sentiment threshold (>= -0.3, allows pain points)
- **AC-6.4**: Authenticity score: Combines experience marker density (40%), pain signal presence (30%), emotional depth (30%)
- **AC-6.5**: Minimum authenticity: 0.6 required for extraction (calibrated on manual review of 200 posts)
- **AC-6.6**: Duplicate detection: Content hashing, 90% similarity threshold for rejection

### Non-Functional Requirements

#### Performance

- **AC-P.1**: Processing latency: <500ms per post (100ms regex, 200ms TF-IDF, 100ms depth scoring, 100ms overhead)
- **AC-P.2**: Batch processing: 1,000 posts in <10 minutes (overnight job constraint)
- **AC-P.3**: Memory footprint: <1GB for pattern engine (TF-IDF vocabulary, regex cache, scoring models)
- **AC-P.4**: Regex compilation: All patterns pre-compiled at initialization (no runtime compilation)

#### Quality

- **AC-Q.1**: Precision: >85% of extracted posts manually verified as authentic coaching insights
- **AC-Q.2**: Recall: >70% of manually-identified relevant posts extracted by engine
- **AC-Q.3**: Emotional depth accuracy: >80% agreement with human raters (Pearson r > 0.75)
- **AC-Q.4**: False positive rate: <10% of extracted content is spam/irrelevant

#### Cost

- **AC-C.1**: Reddit API calls: <20 posts per topic per night (rate limit compliance)
- **AC-C.2**: VectorStore storage: <5MB per topic per month (text embeddings + metadata)
- **AC-C.3**: Processing cost: $0 (local TF-IDF, no API calls for pattern matching)

#### Security

- **AC-S.1**: Privacy: No user identity extraction (usernames discarded, content-only storage)
- **AC-S.2**: API keys: Reddit API credentials stored in env vars (not in code)
- **AC-S.3**: Content filtering: No storage of removed/deleted content (respect moderation)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: Pattern engine loads complete taxonomy before processing (all markers, signals, patterns)
- **AC-CI.2**: TF-IDF vectorizer fully fitted on coaching corpus before inference (no partial vocabulary)
- **AC-CI.3**: Regex patterns validated against test corpus (no untested patterns in production)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: Pattern matching tests: 50+ unit tests (regex accuracy, depth scoring, false positive detection)
- **AC-CII.2**: Integration tests: 10+ end-to-end tests (Reddit API → pattern matching → VectorStore)
- **AC-CII.3**: Quality validation: 100-post manual review before production deployment

#### Article III: Automated Merge Enforcement

- **AC-CIII.1**: Pattern quality gates: Precision >85%, recall >70% required for merge
- **AC-CIII.2**: No manual override of authenticity threshold (0.6 is absolute minimum)

#### Article IV: Continuous Learning and Improvement (MANDATORY)

- **AC-CIV.1**: VectorStore integration: All extracted patterns stored with metadata for future analysis
- **AC-CIV.2**: Pattern drift monitoring: Weekly analysis of extraction quality (precision/recall trends)
- **AC-CIV.3**: Feedback loop: False positives flagged → pattern refinement → improved filters
- **AC-CIV.4**: Cross-session learning: TF-IDF vocabulary expands with new coaching-relevant terms

#### Article V: Spec-Driven Development

- **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- **AC-CV.2**: Pattern taxonomy changes require spec version increment (breaking changes documented)

---

## Technical Design

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Reddit Pattern Matching Engine                                        │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │ Experience       │    │ Pain Signal      │    │ Emotional Depth  │ │
│  │ Marker Detection │───▶│ Classification   │───▶│ Scoring          │ │
│  │                  │    │                  │    │                  │ │
│  │ - Regex match    │    │ - Category map   │    │ - Vulnerability  │ │
│  │ - Weight scoring │    │ - Weight scoring │    │ - Specificity    │ │
│  │ - Density calc   │    │ - Pattern match  │    │ - Context rich   │ │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘ │
│           │                       │                       │            │
│           └───────────────────────┴───────────────────────┘            │
│                                   │                                    │
│                   ┌───────────────▼───────────────┐                    │
│                   │ TF-IDF Feature Extraction     │                    │
│                   │ - Coaching corpus vectorizer  │                    │
│                   │ - 500-dim feature vector      │                    │
│                   │ - Cosine similarity filter    │                    │
│                   └───────────────┬───────────────┘                    │
│                                   │                                    │
│                   ┌───────────────▼───────────────┐                    │
│                   │ False Positive Filter         │                    │
│                   │ - Spam detection              │                    │
│                   │ - Bot identification          │                    │
│                   │ - Quality thresholds          │                    │
│                   └───────────────┬───────────────┘                    │
│                                   │                                    │
│                   ┌───────────────▼───────────────┐                    │
│                   │ VectorStore Integration       │                    │
│                   │ - Embedding storage           │                    │
│                   │ - Metadata tagging            │                    │
│                   │ - Semantic indexing           │                    │
│                   └───────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Experience Marker Taxonomy

```python
from typing import Literal
from pydantic import BaseModel, Field

class ExperienceMarker(BaseModel):
    """
    Experience marker configuration for authentic insight detection.

    Article V: Spec-driven taxonomy definition.
    """

    category: Literal[
        "first_person",
        "time_marker",
        "emotional_transition",
        "relationship_state"
    ]
    pattern: str = Field(..., description="Regex pattern or exact phrase")
    weight: float = Field(..., ge=0.5, le=2.0, description="Authenticity weight")
    case_sensitive: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "category": "first_person",
                "pattern": r"\bI (think|feel|was|have been|experienced)\b",
                "weight": 1.0,
                "case_sensitive": False
            }
        }

# Comprehensive taxonomy (loaded from config/knowledge_ingest/reddit_pain_point_patterns.yaml)
EXPERIENCE_MARKERS: list[ExperienceMarker] = [
    # First-Person Indicators (weight=1.0)
    ExperienceMarker(category="first_person", pattern=r"\bI think\b", weight=1.0),
    ExperienceMarker(category="first_person", pattern=r"\bI feel\b", weight=1.2),
    ExperienceMarker(category="first_person", pattern=r"\bI was\b", weight=1.1),
    ExperienceMarker(category="first_person", pattern=r"\bI have been\b", weight=1.1),
    ExperienceMarker(category="first_person", pattern=r"\bI experienced\b", weight=1.3),
    ExperienceMarker(category="first_person", pattern=r"\bmy experience\b", weight=1.4),
    ExperienceMarker(category="first_person", pattern=r"\bin my opinion\b", weight=0.8),
    ExperienceMarker(category="first_person", pattern=r"\bIMO\b", weight=0.7),
    ExperienceMarker(category="first_person", pattern=r"\bmy biggest (struggle|fear)\b", weight=1.8),
    ExperienceMarker(category="first_person", pattern=r"\bI found that\b", weight=1.3),
    ExperienceMarker(category="first_person", pattern=r"\bI learned\b", weight=1.5),
    ExperienceMarker(category="first_person", pattern=r"\bI realized\b", weight=1.6),
    ExperienceMarker(category="first_person", pattern=r"\bmy advice\b", weight=1.2),

    # Time Markers (weight=1.1-1.3)
    ExperienceMarker(category="time_marker", pattern=r"\bbefore (I|we)\b", weight=1.2),
    ExperienceMarker(category="time_marker", pattern=r"\bafter (I|we)\b", weight=1.3),
    ExperienceMarker(category="time_marker", pattern=r"\bwhen I\b", weight=1.1),
    ExperienceMarker(category="time_marker", pattern=r"\bsince (I|we)\b", weight=1.2),
    ExperienceMarker(category="time_marker", pattern=r"\bnow I (realize|understand|know)\b", weight=1.4),

    # Emotional Transitions (weight=1.4-1.7)
    ExperienceMarker(category="emotional_transition", pattern=r"\bI used to .* but now\b", weight=1.5),
    ExperienceMarker(category="emotional_transition", pattern=r"\bI didn't know .* until\b", weight=1.6),
    ExperienceMarker(category="emotional_transition", pattern=r"\bI've come to realize\b", weight=1.7),
    ExperienceMarker(category="emotional_transition", pattern=r"\blooking back\b", weight=1.4),

    # Relationship States (weight=1.3-1.6)
    ExperienceMarker(category="relationship_state", pattern=r"\bmy ex\b", weight=1.4),
    ExperienceMarker(category="relationship_state", pattern=r"\bco-?parent\b", weight=1.5),
    ExperienceMarker(category="relationship_state", pattern=r"\bour kids\b", weight=1.3),
    ExperienceMarker(category="relationship_state", pattern=r"\bmy partner\b", weight=1.2),
    ExperienceMarker(category="relationship_state", pattern=r"\bmy spouse\b", weight=1.2),
]
```

### 5.3 Pain Signal Patterns

```python
class PainSignal(BaseModel):
    """
    Pain signal configuration for coaching opportunity detection.

    Weight reflects coaching priority (1.0=moderate, 2.0=critical).
    """

    category: Literal[
        "regret",
        "wish",
        "struggle",
        "confusion",
        "hurt"
    ]
    pattern: str
    weight: float = Field(..., ge=1.0, le=2.0)
    coaching_focus: str = Field(..., description="What this signals for coaching")

# Comprehensive pain signal taxonomy
PAIN_SIGNALS: list[PainSignal] = [
    # Regret (weight=1.7-1.9, highest priority)
    PainSignal(
        category="regret",
        pattern=r"\bI wish I (knew|had|did)\b",
        weight=1.9,
        coaching_focus="Knowledge gap, opportunity for preventive wisdom"
    ),
    PainSignal(
        category="regret",
        pattern=r"\bwhat I regret\b",
        weight=1.8,
        coaching_focus="Reflective insight, lessons learned"
    ),
    PainSignal(
        category="regret",
        pattern=r"\bif only (I|we)\b",
        weight=1.7,
        coaching_focus="Counterfactual thinking, unmet needs"
    ),
    PainSignal(
        category="regret",
        pattern=r"\bI should have\b",
        weight=1.8,
        coaching_focus="Action not taken, guidance opportunity"
    ),

    # Wish (weight=1.4-1.6)
    PainSignal(
        category="wish",
        pattern=r"\bI hope (to|I can)\b",
        weight=1.5,
        coaching_focus="Future-oriented desire, goal-setting"
    ),
    PainSignal(
        category="wish",
        pattern=r"\bI want to understand\b",
        weight=1.6,
        coaching_focus="Active learning desire, coachable moment"
    ),
    PainSignal(
        category="wish",
        pattern=r"\bwhat I wish\b",
        weight=1.5,
        coaching_focus="Unmet expectation, clarity needed"
    ),

    # Struggle (weight=1.4-1.6)
    PainSignal(
        category="struggle",
        pattern=r"\b(struggle|struggling)\b",
        weight=1.5,
        coaching_focus="Active difficulty, immediate support need"
    ),
    PainSignal(
        category="struggle",
        pattern=r"\b(problem|problems)\b",
        weight=1.4,
        coaching_focus="Identified challenge, solution-seeking"
    ),
    PainSignal(
        category="struggle",
        pattern=r"\b(difficult|difficulty|difficulties)\b",
        weight=1.5,
        coaching_focus="Complexity barrier, simplification opportunity"
    ),
    PainSignal(
        category="struggle",
        pattern=r"\b(challenge|challenges|challenging)\b",
        weight=1.4,
        coaching_focus="Growth opportunity, reframe potential"
    ),
    PainSignal(
        category="struggle",
        pattern=r"\bhardship\b",
        weight=1.6,
        coaching_focus="Severe difficulty, empathy + guidance needed"
    ),

    # Confusion (weight=1.2-1.4)
    PainSignal(
        category="confusion",
        pattern=r"\bI don't (understand|know|get)\b",
        weight=1.3,
        coaching_focus="Knowledge gap, educational opportunity"
    ),
    PainSignal(
        category="confusion",
        pattern=r"\bconfused (about|by)\b",
        weight=1.4,
        coaching_focus="Clarity needed, conceptual support"
    ),
    PainSignal(
        category="confusion",
        pattern=r"\bunclear (why|how)\b",
        weight=1.2,
        coaching_focus="Reasoning gap, explanation opportunity"
    ),

    # Hurt (weight=1.3-1.6)
    PainSignal(
        category="hurt",
        pattern=r"\bpain point\b",
        weight=1.5,
        coaching_focus="Explicit pain, direct coaching target"
    ),
    PainSignal(
        category="hurt",
        pattern=r"\bhurt\b",
        weight=1.4,
        coaching_focus="Emotional wound, healing focus"
    ),
    PainSignal(
        category="hurt",
        pattern=r"\bfrustratio?n\b",
        weight=1.3,
        coaching_focus="Blocked progress, obstacle removal"
    ),
    PainSignal(
        category="hurt",
        pattern=r"\bworr(y|ies|ied)\b",
        weight=1.3,
        coaching_focus="Anxiety, reassurance + planning"
    ),
    PainSignal(
        category="hurt",
        pattern=r"\bconcern\b",
        weight=1.2,
        coaching_focus="Apprehension, risk mitigation"
    ),
    PainSignal(
        category="hurt",
        pattern=r"\bhesitation\b",
        weight=1.4,
        coaching_focus="Decision paralysis, encouragement needed"
    ),
]
```

### 5.4 Emotional Depth Scoring Algorithm

```python
import re
from dataclasses import dataclass

@dataclass
class EmotionalDepthScore:
    """
    Emotional depth assessment for coaching content quality.

    Scale: 0.0 (generic) to 1.0 (deeply vulnerable).
    """
    vulnerability: float  # 0.0-1.0, presence of regret/wish/hurt
    specificity: float    # 0.0-1.0, concrete vs. abstract
    context_richness: float  # 0.0-1.0, word count + complexity

    @property
    def total_depth(self) -> float:
        """
        Weighted combination: 40% vulnerability + 30% specificity + 30% context.

        Article V: Formula specified in AC-3.5.
        """
        return (
            0.4 * self.vulnerability +
            0.3 * self.specificity +
            0.3 * self.context_richness
        )

    def is_authentic(self, threshold: float = 0.5) -> bool:
        """Check if content meets minimum depth for extraction."""
        return self.total_depth >= threshold

class EmotionalDepthScorer:
    """
    Compute emotional depth score for Reddit content.

    Constitutional Compliance:
    - Article II: Algorithm validated on 50-post human-rated dataset
    - Article V: Spec-driven scoring formula
    """

    def __init__(self, pain_signals: list[PainSignal]):
        self.pain_signals = pain_signals

        # Pre-compile vulnerability patterns
        self.vulnerability_patterns = [
            (re.compile(sig.pattern, re.IGNORECASE), sig.weight)
            for sig in pain_signals
            if sig.category in ["regret", "wish", "hurt"]
        ]

    def score(self, text: str) -> EmotionalDepthScore:
        """
        Calculate emotional depth score for text.

        Args:
            text: Reddit post/comment content

        Returns:
            EmotionalDepthScore with vulnerability, specificity, context components

        Performance: <100ms per post
        """
        # Component 1: Vulnerability (40% weight)
        vulnerability = self._score_vulnerability(text)

        # Component 2: Specificity (30% weight)
        specificity = self._score_specificity(text)

        # Component 3: Context Richness (30% weight)
        context_richness = self._score_context_richness(text)

        return EmotionalDepthScore(
            vulnerability=vulnerability,
            specificity=specificity,
            context_richness=context_richness
        )

    def _score_vulnerability(self, text: str) -> float:
        """
        Score vulnerability based on pain signal presence.

        Higher weight signals (regret, hurt) = higher vulnerability.
        """
        matches = []
        for pattern, weight in self.vulnerability_patterns:
            if pattern.search(text):
                matches.append(weight)

        if not matches:
            return 0.0

        # Average weight of matched patterns, normalized to 0-1
        # Max weight is 2.0, so divide by 2.0
        avg_weight = sum(matches) / len(matches)
        return min(avg_weight / 2.0, 1.0)

    def _score_specificity(self, text: str) -> float:
        """
        Score specificity based on concrete details vs. abstract statements.

        Indicators of specificity:
        - Named entities (capitalized words)
        - Numbers and time references
        - Concrete nouns (not abstract concepts)
        - Temporal markers ("last week", "3 months ago")
        """
        # Named entities (crude: capitalized words not at sentence start)
        sentences = text.split('. ')
        capitalized = len(re.findall(r'\b[A-Z][a-z]+\b', text))
        sentence_starts = len(sentences)
        named_entities = max(capitalized - sentence_starts, 0)

        # Numbers and temporal references
        numbers = len(re.findall(r'\b\d+\b', text))
        temporal = len(re.findall(
            r'\b(yesterday|today|last (week|month|year)|ago|\d+ (days?|weeks?|months?|years?))\b',
            text,
            re.IGNORECASE
        ))

        # Concrete nouns (heuristic: common concrete words)
        concrete_nouns = len(re.findall(
            r'\b(child|kid|parent|home|school|work|job|money|time|day|night)\b',
            text,
            re.IGNORECASE
        ))

        # Normalize to 0-1 (scale based on typical high-specificity posts)
        # High specificity: 5+ entities, 3+ numbers, 2+ temporal, 5+ concrete nouns
        specificity_score = (
            (named_entities / 5) * 0.3 +
            (numbers / 3) * 0.2 +
            (temporal / 2) * 0.3 +
            (concrete_nouns / 5) * 0.2
        )

        return min(specificity_score, 1.0)

    def _score_context_richness(self, text: str) -> float:
        """
        Score context richness based on length and complexity.

        Indicators:
        - Word count (>100 words = rich context)
        - Sentence complexity (avg words per sentence)
        - Relational context (mentions of others)
        """
        words = text.split()
        word_count = len(words)

        sentences = text.split('. ')
        sentence_count = max(len(sentences), 1)
        avg_words_per_sentence = word_count / sentence_count

        # Relational context (mentions of others)
        relational = len(re.findall(
            r'\b(my (ex|partner|spouse|kids?|child|parent)|our|their|he|she|they)\b',
            text,
            re.IGNORECASE
        ))

        # Normalize to 0-1
        # Rich context: 100+ words, 15+ words/sentence, 5+ relational mentions
        richness_score = (
            (min(word_count, 150) / 150) * 0.5 +
            (min(avg_words_per_sentence, 20) / 20) * 0.3 +
            (min(relational, 5) / 5) * 0.2
        )

        return min(richness_score, 1.0)
```

### 5.5 TF-IDF Feature Extraction Strategy

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class CoachingTFIDFExtractor:
    """
    TF-IDF feature extraction tuned for coaching domain.

    Leverages existing ML routing infrastructure (tools/ml_routing/feature_extractor.py).
    Article V: Spec-driven vocabulary and parameters.
    """

    def __init__(self, coaching_corpus: list[str]):
        """
        Initialize TF-IDF vectorizer with coaching domain corpus.

        Args:
            coaching_corpus: List of coaching-relevant documents
                (ACIM texts, relationship advice, parenting forums)
        """
        # Extended stop words (English + Reddit-specific noise)
        reddit_stop_words = [
            "edit", "update", "tldr", "tl;dr", "deleted", "removed",
            "reddit", "upvote", "downvote", "karma"
        ]

        # TF-IDF configuration (AC-4.1 to AC-4.5)
        self.vectorizer = TfidfVectorizer(
            max_features=500,  # Top 500 coaching-relevant terms
            ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
            stop_words=list(set(
                TfidfVectorizer(stop_words='english').get_stop_words() |
                set(reddit_stop_words)
            )),
            min_df=2,  # Term must appear in at least 2 documents
            max_df=0.8,  # Ignore terms in >80% of documents
            lowercase=True,
            strip_accents='unicode',
            token_pattern=r'\b[a-zA-Z]{2,}\b'  # Alpha tokens, 2+ chars
        )

        # Fit on coaching corpus
        self.vectorizer.fit(coaching_corpus)

        # Store corpus mean vector for relevance filtering
        corpus_vectors = self.vectorizer.transform(coaching_corpus)
        self.corpus_mean = np.mean(corpus_vectors.toarray(), axis=0)

    def extract_features(
        self,
        text: str,
        min_relevance: float = 0.65
    ) -> tuple[np.ndarray, float] | None:
        """
        Extract TF-IDF features and compute coaching relevance.

        Args:
            text: Reddit post/comment content
            min_relevance: Minimum cosine similarity to coaching corpus

        Returns:
            (feature_vector, relevance_score) or None if below threshold

        Performance: <200ms per post
        """
        # Transform text to TF-IDF vector
        text_vector = self.vectorizer.transform([text]).toarray()[0]

        # Compute cosine similarity to coaching corpus
        relevance = cosine_similarity(
            [text_vector],
            [self.corpus_mean]
        )[0][0]

        # Filter low-relevance content (AC-4.5)
        if relevance < min_relevance:
            return None

        return text_vector, relevance

    def get_top_terms(self, text: str, n: int = 10) -> list[tuple[str, float]]:
        """
        Extract top N TF-IDF weighted terms from text.

        Useful for VectorStore tagging.
        """
        vector = self.vectorizer.transform([text]).toarray()[0]
        feature_names = self.vectorizer.get_feature_names_out()

        # Sort by TF-IDF score
        top_indices = vector.argsort()[-n:][::-1]

        return [
            (feature_names[idx], vector[idx])
            for idx in top_indices
            if vector[idx] > 0
        ]
```

### 5.6 Niche-Specific Regex Patterns

```python
import re
from enum import Enum

class CoachingNiche(str, Enum):
    """Coaching niche categories (AC-5.1 to AC-5.5)."""
    ACIM = "acim"
    CO_PARENTING = "co_parenting"
    RELATIONSHIPS = "relationships"
    OPEN_RELATIONSHIPS = "open_relationships"
    FORGIVENESS = "forgiveness"
    UNKNOWN = "unknown"

class NichePatternMatcher:
    """
    Regex-based niche classification for coaching content.

    Article II: Patterns validated against 100-post test corpus.
    """

    # Pre-compiled regex patterns (AC-5.6: cached for performance)
    NICHE_PATTERNS = {
        CoachingNiche.ACIM: re.compile(
            r'\b(forgiveness practice|miracle|holy spirit|ego dissolution|'
            r'course in miracles|ACIM lesson|workbook lesson|manual for teachers|'
            r'perception shift|true forgiveness)\b',
            re.IGNORECASE
        ),

        CoachingNiche.CO_PARENTING: re.compile(
            r'\b(co-?parent(ing)?|custody|visitation|parenting plan|'
            r'ex partner|shared custody|parallel parent(ing)?|'
            r'drop-?off|pick-?up|child support|parenting time)\b',
            re.IGNORECASE
        ),

        CoachingNiche.RELATIONSHIPS: re.compile(
            r'\b(conscious uncoupling|peaceful divorce|healthy breakup|'
            r'ending relationship|separation|relationship issues|'
            r'breaking up|divorce process|conscious separation|'
            r'amicable split|relationship ending)\b',
            re.IGNORECASE
        ),

        CoachingNiche.OPEN_RELATIONSHIPS: re.compile(
            r'\b(polyamor(y|ous)|ethical non-?monogamy|ENM|'
            r'jealousy management|boundaries|compersion|'
            r'metamour|polycule|primary partner|secondary partner|'
            r'relationship anarchy)\b',
            re.IGNORECASE
        ),

        CoachingNiche.FORGIVENESS: re.compile(
            r'\b(letting go|healing from hurt|self-?forgiveness|'
            r'compassion practice|resentment|grudge|'
            r'releasing anger|forgiving (myself|others)|'
            r'moving on|emotional healing)\b',
            re.IGNORECASE
        ),
    }

    def classify(self, text: str, subreddit: str | None = None) -> CoachingNiche:
        """
        Classify content into coaching niche.

        Args:
            text: Reddit post/comment content
            subreddit: Optional subreddit context (e.g., "r/ACIM")

        Returns:
            CoachingNiche enum (strongest match or UNKNOWN)

        Performance: <100ms per post (pre-compiled regex)
        """
        # Subreddit-based classification (highest priority)
        if subreddit:
            subreddit_lower = subreddit.lower()
            if 'acim' in subreddit_lower or 'courseinmiracles' in subreddit_lower:
                return CoachingNiche.ACIM
            if 'coparent' in subreddit_lower or 'singleparent' in subreddit_lower:
                return CoachingNiche.CO_PARENTING
            if 'polyamory' in subreddit_lower or 'nonmonogamy' in subreddit_lower:
                return CoachingNiche.OPEN_RELATIONSHIPS
            if 'divorce' in subreddit_lower or 'breakup' in subreddit_lower:
                return CoachingNiche.RELATIONSHIPS

        # Content-based classification (regex patterns)
        match_counts = {
            niche: len(pattern.findall(text))
            for niche, pattern in self.NICHE_PATTERNS.items()
        }

        # Return niche with most matches (or UNKNOWN if zero matches)
        max_niche = max(match_counts, key=match_counts.get)
        return max_niche if match_counts[max_niche] > 0 else CoachingNiche.UNKNOWN
```

### 5.7 False Positive Filtering Strategy

```python
from typing import NamedTuple

class QualityMetrics(NamedTuple):
    """Quality assessment for content filtering."""
    is_spam: bool
    is_bot: bool
    meets_length: bool
    meets_upvotes: bool
    authenticity_score: float

    @property
    def passes_all_filters(self) -> bool:
        """Check if content passes all quality gates."""
        return (
            not self.is_spam and
            not self.is_bot and
            self.meets_length and
            self.meets_upvotes and
            self.authenticity_score >= 0.6  # AC-6.5
        )

class FalsePositiveFilter:
    """
    Multi-stage quality filtering for coaching content extraction.

    Article III: No manual override of quality thresholds.
    """

    # Spam patterns (AC-6.1)
    SPAM_BLOCKLIST = [
        "removed by moderator",
        "[deleted]",
        "spam",
        "[removed]",
        "this post has been removed"
    ]

    # Bot username patterns (AC-6.2)
    BOT_USERNAME_PATTERN = re.compile(r'.*(bot|auto).*', re.IGNORECASE)

    def __init__(
        self,
        min_length: int = 100,
        min_upvotes: int = 5,
        min_authenticity: float = 0.6
    ):
        self.min_length = min_length
        self.min_upvotes = min_upvotes
        self.min_authenticity = min_authenticity

    def assess_quality(
        self,
        text: str,
        username: str,
        upvotes: int,
        experience_marker_density: float,
        pain_signal_present: bool,
        emotional_depth: float
    ) -> QualityMetrics:
        """
        Assess content quality across multiple dimensions.

        Args:
            text: Post/comment content
            username: Reddit username
            upvotes: Upvote count
            experience_marker_density: Markers per 100 words
            pain_signal_present: Whether pain signals detected
            emotional_depth: Depth score (0.0-1.0)

        Returns:
            QualityMetrics with pass/fail for each filter
        """
        # Spam detection
        is_spam = any(
            spam_phrase in text.lower()
            for spam_phrase in self.SPAM_BLOCKLIST
        )

        # Bot identification
        is_bot = bool(self.BOT_USERNAME_PATTERN.match(username))

        # Length check
        meets_length = len(text) >= self.min_length

        # Upvote threshold
        meets_upvotes = upvotes >= self.min_upvotes

        # Authenticity score (AC-6.4)
        authenticity_score = (
            0.4 * min(experience_marker_density / 2.0, 1.0) +  # 2.0 markers/100 words = high
            0.3 * (1.0 if pain_signal_present else 0.0) +
            0.3 * emotional_depth
        )

        return QualityMetrics(
            is_spam=is_spam,
            is_bot=is_bot,
            meets_length=meets_length,
            meets_upvotes=meets_upvotes,
            authenticity_score=authenticity_score
        )
```

---

## Dependencies & Constraints

### System Dependencies

- **scikit-learn**: TF-IDF vectorization, cosine similarity (existing: tools/ml_routing/)
- **NumPy**: Vector operations, feature arrays
- **Pydantic**: Pattern taxonomy models, type validation
- **AgentContext**: VectorStore integration (Article IV)
- **Reddit API**: PRAW library for post/comment extraction

### External Dependencies

- **Coaching Corpus**: ACIM texts, relationship forums (for TF-IDF training)
- **Reddit API Credentials**: API key, secret, user agent
- **VectorStore**: sentence-transformers embedding model

### Technical Constraints

- **Processing Latency**: <500ms per post (AC-P.1)
- **Batch Size**: Max 20 posts per topic per night (Reddit API rate limits)
- **Memory**: <1GB for pattern engine (TF-IDF vocabulary + regex cache)
- **Storage**: <5MB per topic per month (VectorStore embeddings)

### Business Constraints

- **Privacy**: No user identity tracking (username discarded after quality check)
- **Content Respect**: No storage of removed/deleted content
- **API Limits**: Reddit API rate limits enforced (2 requests/second)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: Pattern drift (community language evolves, patterns become outdated) - *Mitigation*: Weekly pattern effectiveness monitoring, quarterly manual review, VectorStore learning (Article IV)
- **Risk 2**: False negative rate (missing authentic insights) - *Mitigation*: Conservative thresholds (70% recall target), manual sampling of rejected content

### Medium Risk Items

- **Risk 3**: TF-IDF vocabulary mismatch (coaching corpus doesn't cover niche terminology) - *Mitigation*: Niche-specific vocabulary expansion, hybrid regex + TF-IDF approach
- **Risk 4**: Emotional depth scoring bias (algorithm favors certain writing styles) - *Mitigation*: Diverse training set for validation (50+ human-rated posts), continuous calibration

### Constitutional Risks

- **Constitutional Risk 1**: Article IV violation (patterns not stored for learning) - *Mitigation*: VectorStore integration mandatory, telemetry tracking extraction quality
- **Constitutional Risk 2**: Article II violation (patterns deployed without validation) - *Mitigation*: 100-post manual review before production, precision >85% gate

---

## Integration Points

### Agent Integration

- **Overnight Knowledge Worker**: Primary consumer, runs nightly Reddit extraction job
- **AI Coaching Agent**: Pattern consumer, queries VectorStore for authentic insights
- **LearningAgent**: Pattern quality analyzer, refines extraction strategy

### System Integration

- **VectorStore**: Storage destination for extracted patterns with metadata
- **Telemetry**: Extraction quality metrics (precision, recall, processing time)
- **config/knowledge_ingest/reddit_pain_point_patterns.yaml**: Pattern taxonomy source

### External Integration

- **Reddit API (PRAW)**: Post/comment data source
- **Coaching Corpus**: External texts for TF-IDF training
- **Human Reviewers**: Quality validation, pattern refinement feedback

---

## Testing Strategy

### Test Categories

- **Unit Tests** (50+ tests): Regex accuracy, depth scoring, TF-IDF feature extraction, false positive detection
- **Integration Tests** (10+ tests): Reddit API → pattern matching → VectorStore (end-to-end)
- **Quality Validation Tests** (5+ tests): Precision >85%, recall >70%, depth accuracy >80%
- **Constitutional Compliance Tests** (5+ tests): Article I-V validation

### Test Data Requirements

- **Test Data 1**: 100-post manual review dataset with ground truth labels (authentic vs. noise)
- **Test Data 2**: 50-post human-rated emotional depth scores (validation set)
- **Test Data 3**: Edge cases (spam, bots, generic content, niche-specific terminology)

### Test Environment Requirements

- **Mock Reddit API**: Simulated posts/comments for deterministic testing
- **Coaching Corpus**: Sample ACIM texts, relationship advice (for TF-IDF fitting)
- **VectorStore Mock**: In-memory storage for fast tests

---

## Implementation Phases

### Phase 1: Pattern Taxonomy & Scoring (Week 1)

- **Scope**: Experience markers, pain signals, emotional depth scorer
- **Deliverables**:
  - `tools/pattern_matching/taxonomy.py` (Pydantic models for markers/signals)
  - `tools/pattern_matching/emotional_depth.py` (EmotionalDepthScorer class)
  - Unit tests (20+ tests, scoring accuracy)
- **Success Criteria**: Depth scoring >80% correlation with human ratings (n=50)

### Phase 2: TF-IDF Feature Extraction (Week 1-2)

- **Scope**: Coaching corpus TF-IDF vectorizer, relevance filtering
- **Deliverables**:
  - `tools/pattern_matching/tfidf_extractor.py` (CoachingTFIDFExtractor class)
  - Coaching corpus curation (ACIM texts, relationship forums)
  - Unit tests (10+ tests, feature extraction, relevance threshold)
- **Success Criteria**: >75% cosine similarity to coaching corpus for authentic content

### Phase 3: Niche Classification & Regex (Week 2)

- **Scope**: Niche-specific regex patterns, subreddit context
- **Deliverables**:
  - `tools/pattern_matching/niche_classifier.py` (NichePatternMatcher class)
  - Comprehensive regex patterns (5 niches, 10+ patterns each)
  - Unit tests (15+ tests, niche accuracy)
- **Success Criteria**: >90% niche classification accuracy on labeled dataset

### Phase 4: False Positive Filtering (Week 2-3)

- **Scope**: Spam detection, bot identification, quality thresholds
- **Deliverables**:
  - `tools/pattern_matching/quality_filter.py` (FalsePositiveFilter class)
  - Authenticity score integration
  - Unit tests (10+ tests, filtering accuracy)
- **Success Criteria**: <10% false positive rate on 200-post validation set

### Phase 5: Integration & VectorStore (Week 3)

- **Scope**: Reddit API integration, VectorStore storage, overnight job
- **Deliverables**:
  - `tools/pattern_matching/reddit_extractor.py` (Main extraction pipeline)
  - VectorStore integration (metadata tagging, semantic indexing)
  - Integration tests (10+ tests, end-to-end)
- **Success Criteria**: Process 100 posts in <10 minutes, >85% precision

### Phase 6: Quality Validation & Production (Week 4)

- **Scope**: Manual review, precision/recall measurement, deployment
- **Deliverables**:
  - 100-post manual review report
  - Quality metrics dashboard
  - Production deployment (overnight cron job)
- **Success Criteria**: Precision >85%, recall >70%, ready for production use

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (Coaching Product Owner)
- **Secondary Stakeholders**: AI Coaching Agent (pattern consumer), Overnight Worker (pattern extractor)
- **Technical Reviewers**: LearningAgent (pattern quality), PlannerAgent (spec compliance)

### Review Criteria

- [ ] **Completeness**: All pattern types specified (markers, signals, depth, TF-IDF, niche, filtering)
- [ ] **Clarity**: Taxonomy, algorithms, and integration points clearly documented
- [ ] **Feasibility**: <500ms per post achievable with regex + TF-IDF (no ML overhead)
- [ ] **Constitutional Compliance**: All 5 articles validated (especially Article IV VectorStore)
- [ ] **Quality Standards**: Precision >85%, recall >70%, depth accuracy >80%

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending agent validation
- [ ] **Constitutional Compliance**: Pending article verification
- [ ] **Final Approval**: Pending after Phase 1-2 implementation (taxonomy + TF-IDF)

---

## Appendices

### Appendix A: Glossary

- **Experience Marker**: First-person language indicating authentic personal experience
- **Pain Signal**: Keywords/phrases revealing coaching opportunities (regret, struggle, hurt)
- **Emotional Depth**: 0.0-1.0 score measuring vulnerability, specificity, context richness
- **TF-IDF**: Term Frequency-Inverse Document Frequency, statistical feature extraction
- **Authenticity Score**: Composite metric (markers + signals + depth) for extraction quality
- **Coaching Niche**: Domain-specific category (ACIM, co-parenting, relationships, etc.)

### Appendix B: References

- **spec-005**: Advanced Pattern Recognition (ML-based, different approach)
- **spec-017**: Pattern Library & Learning Dashboard (storage destination)
- **ADR-004**: Continuous Learning (VectorStore mandate)
- **ADR-007**: Spec-Driven Development
- **config/knowledge_ingest/reddit_pain_point_patterns.yaml**: Existing pattern taxonomy

### Appendix C: Related Documents

- **tools/ml_routing/feature_extractor.py**: Existing TF-IDF infrastructure
- **tools/ml_routing/tfidf_vocabulary_builder.py**: Vocabulary construction patterns
- **agency_memory/vector_store.py**: VectorStore integration target

### Appendix D: Example Extraction

**Input (Reddit r/coparenting post):**
```
I was terrified of co-parenting after my divorce. My biggest fear was that
my ex and I couldn't communicate without fighting, and our kids (7 and 9)
would suffer. I wish I knew then what I know now - that parallel parenting
was an option. For 3 months, we struggled with every handoff. Looking back,
the pain could have been avoided if we'd set clear boundaries from day one.
```

**Pattern Matching Output:**
```python
{
    "experience_markers": [
        {"phrase": "I was terrified", "category": "first_person", "weight": 1.2},
        {"phrase": "My biggest fear", "category": "first_person", "weight": 1.8},
        {"phrase": "I wish I knew", "category": "emotional_transition", "weight": 1.9},
        {"phrase": "Looking back", "category": "emotional_transition", "weight": 1.4},
        {"phrase": "our kids", "category": "relationship_state", "weight": 1.3},
        {"phrase": "my ex", "category": "relationship_state", "weight": 1.4}
    ],
    "pain_signals": [
        {"phrase": "terrified", "category": "hurt", "weight": 1.6},
        {"phrase": "my biggest fear", "category": "hurt", "weight": 1.8},
        {"phrase": "I wish I knew", "category": "regret", "weight": 1.9},
        {"phrase": "struggled", "category": "struggle", "weight": 1.5},
        {"phrase": "pain", "category": "hurt", "weight": 1.4}
    ],
    "emotional_depth": {
        "vulnerability": 0.89,  # High regret + hurt presence
        "specificity": 0.72,    # Kids' ages, 3-month timeline, concrete details
        "context_richness": 0.68,  # 89 words, relational context
        "total_depth": 0.78     # Above 0.5 threshold → EXTRACT
    },
    "tfidf_features": {
        "top_terms": [
            ("co-parenting", 0.42),
            ("divorce", 0.38),
            ("parallel parenting", 0.35),
            ("boundaries", 0.28),
            ("communicate", 0.24)
        ],
        "relevance_to_coaching_corpus": 0.87  # Above 0.65 threshold
    },
    "niche": "co_parenting",  # Strong regex match + subreddit context
    "quality_metrics": {
        "is_spam": false,
        "is_bot": false,
        "meets_length": true,  # 89 chars (>100 threshold)
        "meets_upvotes": true,  # Assume 12 upvotes
        "authenticity_score": 0.81  # Above 0.6 threshold → EXTRACT
    },
    "vectorstore_tags": [
        "co_parenting",
        "divorce_transition",
        "communication_issues",
        "parallel_parenting",
        "boundary_setting",
        "source:reddit",
        "depth:high",
        "regret_present"
    ],
    "coaching_focus": "Preventive wisdom (parallel parenting), boundary-setting, communication strategies",
    "extraction_decision": "EXTRACT → VectorStore"
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-09 | PlannerAgent | Initial specification for Reddit pattern matching engine |

---

*"Authentic insights emerge from vulnerability, specificity, and context richness."*
