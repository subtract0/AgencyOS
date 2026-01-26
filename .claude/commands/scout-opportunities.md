---
description: Scout Opportunities - AI Business Opportunity Discovery
argument-hint: [niche] [--deep]
---

# Purpose

Discover unique business opportunities where AI can deliver 95%+ of customer value, with strong purchase intent signals and zero/low competition.

# Variables

- `niche` (optional): Specific niche to focus on (e.g., "legal documents", "e-commerce", "freelancer tools")
- `--deep`: Run comprehensive search with additional manual niche exploration

# Workflow

## Phase 1: Run Market Signal Radar

Execute the Market Signal Radar to collect purchase intent signals:

```bash
cd /Volumes/Satechi4TB/pain_points && python3 market_signal_radar.py --once 2>&1 | tail -100
```

This will:
1. Scrape HackerNews for purchase intent signals (2000+ signals)
2. Scrape Gumroad for products with prices
3. Scrape AppSumo for validated products
4. Analyze patterns and synthesize opportunities
5. Validate competition for each opportunity

## Phase 2: Deep Niche Exploration (if --deep or niche specified)

If a specific niche is provided or --deep flag is used, perform manual HN searches:

```bash
# Search for specific niche pain points
curl -s "https://hn.algolia.com/api/v1/search?query=[NICHE]%20pain%20frustrating&tags=story&hitsPerPage=30" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for h in sorted(data.get('hits', []), key=lambda x: x.get('points', 0), reverse=True)[:10]:
    print(f'[{h.get(\"points\", 0)} pts] {h.get(\"title\", \"\")[:70]}')"
```

## Phase 3: Competition Verification

For each promising opportunity, verify competition is ZERO or LOW:

```bash
# Check for existing solutions
curl -s "https://hn.algolia.com/api/v1/search?query=[OPPORTUNITY]%20generator%20AI%20tool&tags=show_hn&hitsPerPage=10" | python3 -c "
import json, sys
data = json.load(sys.stdin)
hits = [h for h in data.get('hits', []) if h.get('points', 0) > 5]
print(f'Found {len(hits)} competitors')"
```

## Phase 4: Report Generation

Generate the final opportunity report:

```bash
cat /Volumes/Satechi4TB/pain_points/market_radar/UNIQUE_OPPORTUNITY_REPORT.md
```

# Criteria for UNIQUE Opportunity

| Criteria | Requirement |
|----------|-------------|
| AI Value Delivery | 95%+ (text generation, transformation, analysis) |
| Purchase Intent | Strong signals (complaints, price mentions, 50+ pts) |
| Competition | ZERO or LOW (< 3 Show HN results with >5 pts) |
| Price Willingness | $25+ validated |

# Output Format

```markdown
## UNIQUE OPPORTUNITY: [Name]

**Problem**: [What pain are people experiencing]
**Validation Signals**:
- [X pts] "[HN discussion title]"
- [Y pts] "[Another discussion]"

**Competition Check**: [ZERO/LOW/MEDIUM/HIGH]
- Existing solutions found: [N]

**Why AI Delivers 95%+**: [Explanation]

**Product Concept**:
- Input: [What user provides]
- Output: [What AI generates]
- Price: $[X] (vs $[Y] consultant alternative)

**First Validation Step**: [Concrete 1-week action]

**Recommendation**: [BUILD / SKIP]
```

# Example Usage

## Full scan:
```
/scout-opportunities
```

## Niche-specific:
```
/scout-opportunities "teacher tools"
/scout-opportunities "legal documents" --deep
```

# Data Sources

- **HackerNews** (Algolia API) - Pain points, complaints, purchase intent
- **Gumroad Discover** - Products with validated prices
- **AppSumo Browse** - B2B tools with prices

# Files

- **Radar**: `/Volumes/Satechi4TB/pain_points/market_signal_radar.py`
- **Output**: `/Volumes/Satechi4TB/pain_points/market_radar/`
- **Reports**: `UNIQUE_OPPORTUNITY_REPORT.md`

---

**Remember**: The goal is to find opportunities that are:
1. HIGH PAIN (people losing money, time, livelihoods)
2. AI-SOLVABLE (95%+ text/content generation)
3. UNCROWDED (zero existing AI tools)
4. VALUABLE ($50+ willingness to pay)
