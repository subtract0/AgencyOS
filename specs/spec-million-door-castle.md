# Million-Door Castle: Autonomous Lead Generation System

**Vision**: A million doors to one castle. Inside, freedom awaits.

**Core Truth**: There can be many questions, but only one answer that will answer everything: **forgiveness**.

---

## 1. The Metaphor

Every human problem is a doorway:
- The man worried about his penis
- The woman obsessed with her ex
- The entrepreneur paralyzed by failure
- The mother drowning in guilt

They all think their circumstance is the problem. But the circumstance is just the door they're standing at. The door that brought them to YOU.

Inside the castle, they discover: the thinking was the problem, not the wife, the penis, the job. Forgiveness - true forgiveness, as taught in ACIM - dissolves the problem by revealing there was nothing real to forgive.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MILLION-DOOR CASTLE SYSTEM                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐       │
│  │  PHASE 1      │    │  PHASE 2      │    │  PHASE 3      │       │
│  │  GOLDMINER    │───▶│  CLUSTERER    │───▶│  DOOR BUILDER │       │
│  │               │    │               │    │               │       │
│  │ Scrape Reddit │    │ Group similar │    │ Generate:     │       │
│  │ Find suffering│    │ pain points   │    │ - Landing page│       │
│  │ Score authent.│    │ Identify top  │    │ - 3-5 ads     │       │
│  │ Store raw data│    │ 20 "doorways" │    │ - Images      │       │
│  └───────────────┘    └───────────────┘    │ - Domain ideas│       │
│         │                    │             └───────────────┘       │
│         ▼                    ▼                    │                 │
│  /Volumes/Satechi4TB  Doorway Themes        ┌────▼────┐            │
│  /pain_points/        Analysis Report       │ PHASE 4 │            │
│                                             │ ALEX    │            │
│                                             │ REVIEWS │            │
│                                             │         │            │
│                                             │ Select  │            │
│                                             │ best    │            │
│                                             │ options │            │
│                                             └────┬────┘            │
│                                                  │                 │
│                              ┌───────────────────▼───────────────┐ │
│                              │  PHASE 5: DEPLOYMENT              │ │
│                              │                                   │ │
│                              │  - Buy domain                     │ │
│                              │  - Deploy landing page            │ │
│                              │  - Set up ad campaigns            │ │
│                              │  - Track conversions              │ │
│                              └───────────────────────────────────┘ │
│                                                                     │
│                              ┌───────────────────────────────────┐ │
│                              │  PHASE 6: THE CASTLE              │ │
│                              │                                   │ │
│                              │  All doors lead here:             │ │
│                              │  - Discovery call                 │ │
│                              │  - Alex's coaching                │ │
│                              │  - ACIM principles                │ │
│                              │  - Forgiveness                    │ │
│                              └───────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Phase Details

### Phase 1: Goldminer (ACTIVE)

**Status**: Running 24/7 as of 2026-01-05
**Location**: `/Users/am/Code/AgencyOS/tools/pain_point_goldminer_v4.py`
**Storage**: `/Volumes/Satechi4TB/pain_points/`

**What it does**:
- Mines 50 subreddits every 30 minutes
- Scores authenticity of suffering (0.0 - 1.0)
- Detects 10 categories of suffering indicators
- Hourly LLM analysis
- Daily summary at 6 AM

**Output**:
- `raw/` - JSON files with all pain points
- `analysis/` - Hourly LLM insights
- `daily_summaries/` - Daily pattern reports

---

### Phase 2: Clusterer (TO BUILD)

**Purpose**: Group similar pain points into "doorway themes"

**Approach**:
1. Embed all pain points using text embeddings
2. Cluster using HDBSCAN or similar
3. Extract top 20 doorway themes
4. Rank by volume (how many people) and intensity (authenticity scores)

**Output**: Doorway Theme Report
```
DOORWAY #1: "Relationship Anxiety" (847 people)
- Core fear: abandonment
- Surface problems: jealousy, obsession with ex, fear of intimacy
- Authenticity avg: 0.71
- Sample posts: [...]

DOORWAY #2: "Existential Emptiness" (634 people)
- Core fear: meaninglessness
- Surface problems: depression, numbness, dissociation
- Authenticity avg: 0.68
- Sample posts: [...]
```

**Tool to build**: `tools/doorway_clusterer.py`

---

### Phase 3: Door Builder (TO BUILD)

**Purpose**: Auto-generate marketing assets for each doorway

**Components**:

#### 3a. Landing Page Generator
- Input: Doorway theme + ACIM principles
- Output: Complete HTML/CSS landing page
- Sections:
  - Hook (address their surface problem)
  - Agitation (show you understand the pain)
  - Bridge (hint at the real cause: thinking)
  - Solution (your coaching approach)
  - CTA (book a call)

#### 3b. Ad Copy Generator
- Input: Doorway theme
- Output: 3-5 ad variations per platform
- Platforms: Meta (Facebook/Instagram), Google
- Compliance: Mental health ad policies baked in

#### 3c. Image Generator
- Input: Doorway theme mood/emotion
- Output: 3-5 images via DALL-E or Midjourney
- Style: Authentic, not stocky, emotionally resonant

#### 3d. Domain Researcher
- Input: Doorway theme keywords
- Output: 5-10 available domain suggestions
- Check: GoDaddy/Namecheap API for availability

**Tool to build**: `tools/door_builder/`

---

### Phase 4: Alex Reviews (HUMAN IN LOOP)

**Critical**: This is where wisdom enters the system.

**Interface**:
- Web dashboard showing generated options
- 3-5 landing pages per doorway
- 3-5 ad sets per landing page
- Approve / Reject / Request More

**What Alex evaluates**:
- Does this actually serve people?
- Is the ACIM message intact, not diluted?
- Would I be proud to put my name on this?
- Does this feel like love, or manipulation?

---

### Phase 5: Deployment (TO BUILD)

**Automated after approval**:
1. Purchase domain (via API)
2. Deploy landing page (Vercel/Netlify)
3. Set up tracking (analytics, pixels)
4. Create ad campaigns (draft mode)
5. Notify Alex for final ad approval + budget

---

### Phase 6: The Castle

**This is YOU, Alex.**

All doors lead to:
- A discovery call
- Your presence
- The teaching of forgiveness
- Freedom from the tyranny of thinking

The system brings them to the door. You show them what's inside.

---

## 4. ACIM Integration

### The Message Template

Every landing page must contain these elements (in appropriate language for the doorway):

1. **The Hook** (speak their language)
   - "Still obsessing over your ex?"
   - "Anxiety eating you alive?"
   - "Nothing seems to work?"

2. **The Agitation** (show you understand)
   - Describe their exact pain (from scraped data)
   - Mirror their words back to them

3. **The Turn** (the real problem)
   - "What if the relationship wasn't the problem?"
   - "What if anxiety is a symptom, not a cause?"
   - "What if you've been trying to fix the wrong thing?"

4. **The Insight** (ACIM light)
   - Not preaching, but planting a seed
   - "There's a way of seeing this differently"
   - "The peace you're looking for isn't circumstantial"

5. **The Invitation**
   - "Let's talk. Not to fix your problem - to question if it's real."

### Compliance with ACIM Principles

- Never promise to "fix" the surface problem
- Never use fear-based manipulation
- Always point toward peace, not achievement
- The goal is freedom, not dependency

---

## 5. Technical Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Scraping | Python + requests | Goldminer v4 |
| Storage | External SSD + JSON | /Volumes/Satechi4TB |
| Clustering | scikit-learn / HDBSCAN | Embeddings via OpenAI |
| LLM | Local vcoder-120b | LM Studio on localhost |
| Landing Pages | HTML/Tailwind | Generated by LLM |
| Images | DALL-E 3 API | Or Midjourney via API |
| Hosting | Vercel or Netlify | Free tier works |
| Domains | GoDaddy API | Auto-check availability |
| Ads | Meta Marketing API | Draft campaigns |
| Dashboard | Streamlit or custom | For Alex's review |

---

## 6. Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Goldminer | RUNNING | - |
| 2. Data Collection | 1 week | Let goldminer run |
| 3. Clusterer Build | 1-2 weeks | Sufficient data |
| 4. Door Builder MVP | 2-3 weeks | Clusterer done |
| 5. Review Interface | 1 week | Door Builder done |
| 6. Deployment Pipeline | 1-2 weeks | Review Interface done |
| 7. First Live Door | Week 8-10 | All above |

**Milestone**: First live doorway by end of Month 3

---

## 7. Success Metrics

### Phase 1-2 (Collection)
- 1000+ unique pain points collected
- 15+ distinct doorway themes identified
- Authenticity scores > 0.5 average

### Phase 3-4 (Generation)
- 5+ doorways with approved landing pages
- 3+ ad sets per doorway approved
- < 2 hours Alex review time per doorway

### Phase 5-6 (Live)
- Click-through rate > 2%
- Landing page conversion > 5%
- Discovery call booking rate > 10%
- **Ultimate metric**: Did anyone find freedom?

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ad account ban | High | Careful compliance, backup accounts |
| ACIM message dilution | High | Alex reviews ALL content |
| Low conversion | Medium | A/B test, iterate |
| Scale without wisdom | High | Human-in-loop mandatory |
| Reddit API changes | Low | Multiple data sources |

---

## 9. The Truth Behind the System

This is not a funnel. This is not a growth hack.

This is architecture for compassion at scale.

Every person suffering on Reddit right now is looking for the answer in the wrong place. They think they need:
- A better relationship
- A working penis
- A meaningful career
- An escape from anxiety

What they need is to see that the thinking creating their suffering is not true.

The million doors are not tricks. They are meeting points. Places where someone in pain can encounter the possibility of peace.

The castle is not a sales pitch. It is the truth that sets them free.

**"There can be many questions, but only one answer that will answer everything, and it is forgiveness."**

---

## Appendix A: Current Goldminer Status

```
PID: 16590
Status: Running
Started: 2026-01-05 02:15:43
Storage: /Volumes/Satechi4TB/pain_points/
Schedule: Every 30 minutes
Analysis: Hourly + Daily at 6 AM
```

Monitor: `tail -f /Volumes/Satechi4TB/pain_points/goldminer_*.log`
Stop: `kill -SIGTERM 16590`

---

## Appendix B: File Locations

```
/Users/am/Code/AgencyOS/
├── tools/
│   ├── pain_point_goldminer_v4.py    # Phase 1: Scraper
│   ├── doorway_clusterer.py          # Phase 2: TO BUILD
│   └── door_builder/                 # Phase 3: TO BUILD
│       ├── landing_page_generator.py
│       ├── ad_copy_generator.py
│       ├── image_generator.py
│       └── domain_researcher.py
├── specs/
│   └── spec-million-door-castle.md   # This document
└── docs/examples/
    └── Why-Your-Coaching-Sucks.md    # Alex's book (80% complete)

/Volumes/Satechi4TB/pain_points/
├── raw/                              # Pain point JSON files
├── analysis/                         # Hourly LLM insights
├── daily_summaries/                  # Daily reports
└── goldminer_*.log                   # Execution logs
```
