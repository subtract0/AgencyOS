# Pain Point → Offer → Web Skill Suite (PARKED)

**Status**: Parked - Revisit after Mission 2
**Date Created**: 2025-11-12
**Date Parked**: 2025-11-12
**Reason**: Prioritizing Metaproductivity 2.0 infrastructure over Skills/revenue path

---

## Concept Summary

Three specialized Claude Skills forming an autonomous pipeline:

1. **Pain Point Goldminer** - 24/7 Reddit/Quora scraping with local LLM (vcoder-120b)
2. **Offer Architect** - Pain points → Alex Hormozi "grand slam offers" + landing page copy
3. **Web Forge** - Copy → production Next.js websites (Tailwind, shadcn/ui, Vercel)

**Expected Output**: Reddit pain points → validated business opportunities → deployed landing pages

**Expected Cost**: $0-2 per landing page (100% local possible)

---

## Existing Assets (What We Have)

### Working Tools
- `tools/pain_point_goldminer.py` (lines 1-199)
  - 6-hour Reddit mining loop
  - Local LLM analysis (vcoder-120b @ 192.168.0.2:1234)
  - Checkpoint system (30-min intervals)
  - **Status**: Partially working, no Quora integration

- `tools/knowledge_ingest.py` (full file)
  - Reddit → VectorStore pipeline
  - Pattern-based authenticity scoring
  - Deduplication by URL hash
  - Exports to JSON + VectorStore
  - **Status**: Production-ready

- `tools/opportunity_validator.py` (full file)
  - Deep scraping: 5 subreddits × 3 time filters
  - LLM opportunity extraction
  - Scoring: maintainability (0.6), profitability (0.9), digital (1.0)
  - **Status**: Collected 322 validated opportunities (logs/opportunity_validator/exports/opportunities_20251112_012821.json)

### Configuration
- `config/knowledge_ingest/reddit_pain_point_patterns.yaml` (lines 1-193)
  - Pattern categories: experience_markers, pain_signals, emotional_depth
  - Topic configs: co_parenting, conscious_uncoupling, acim, open_relationships, love_and_forgiveness
  - Quality filters: min_upvotes (5), authenticity_score_min (0.6)
  - **Status**: Production-ready, proven patterns

### Documentation
- `docs/rubric-landing-page-evaluation.md` (lines 1-320)
  - 5-dimension evaluation framework
  - Dimensions: Clarity, Specificity, Emotional Resonance, Believability, Pain-Alignment
  - Scoring guidelines (10/8/6/4/2 levels)
  - Pass threshold: ≥8.0 overall, all dimensions ≥7.0
  - **Status**: Complete, well-structured

### Sample Output
- `logs/baseline_experiments/spiritual_guidance_baseline_20251112_012342/`
  - `full_pages/sonnet45_variant_01.html` (271 lines, 18KB)
  - Landing page for "ZenPath" spiritual journey tracker
  - **Actual Quality**: 6/10 (not 8.8/10 as initially claimed)
  - Issues:
    - No concrete proof for claims ("Join 10,000+ seekers")
    - Repetitive pain point quotes (feels canned)
    - Vague product features ("AI-powered pattern recognition")
    - Believability: <6, Emotional Resonance: 5-6, Specificity: 6

---

## What's Missing (Not Built)

### Skill 1: Pain Point Goldminer
1. **Quora Scraper** - Selenium-based, authenticated scraping (NOT implemented)
2. **Background Scheduler** - launchd/systemd for 24/7 operation (NOT implemented)
3. **Expanded Topic Configs** - 10+ niches beyond current 5 (NOT implemented)

### Skill 2: Offer Architect
1. **Offer Generator** - Alex Hormozi value equation implementation (NOT implemented)
   - Dream Outcome × Perceived Likelihood / (Time Delay × Effort/Sacrifice)
   - 3 offer variants generator
2. **Copywriting Engine** - BAB framework (Before-After-Bridge) (NOT implemented)
   - Hero section generator
   - Before/After section generator
   - Bridge section generator
3. **Rubric Scorer** - Automated evaluation with ensemble judging (NOT implemented)
   - DeepSeek-R1 + o1-mini integration
   - Refinement loop (if <8.0, regenerate)

### Skill 3: Web Forge
1. **Next.js 14 Template** - Modern web stack (NOT implemented)
   - App Router, TypeScript, Tailwind CSS, shadcn/ui
2. **Component Generator** - React/TS code generation (NOT implemented)
3. **Deployment Pipeline** - Vercel CLI integration (NOT implemented)

**Reality Check**: Building all 3 Skills from scratch = multi-week project (not 2 days)

---

## Why Parked (Strategic Decision)

### Issues Identified (2025-11-12)
1. **No Validated Demand**
   - No distribution channel
   - No pricing validation
   - Revenue projections ($299 × 10 sales) are wishful math
   - Marketability unproven

2. **Quality Not Met**
   - Sample landing page is 6/10, not 8.8/10
   - Self-evaluation was overly optimistic
   - No independent validation
   - Would undermine "grand slam offer" promise

3. **Execution Gap**
   - Assumed working scrapers exist (only partial)
   - Assumed tooling exists (most NOT built)
   - Actually: multi-week project, not 48-hour sprint

4. **Revenue Probability**
   - Without audience: <10% chance of single sale
   - Would need: gather 50 opportunities, write 5 quality pages, design checkout, promote
   - Realistically: 1-2 weeks + ad spend or partnerships

5. **Opportunity Cost**
   - Metaproductivity 2.0 compounds with every iteration
   - Makes AgencyOS itself better
   - Aligns with long-term vision
   - Utilizes local compute 24/7 productively

### Decision (See ADR-037)
Focus on Metaproductivity 2.0 (Missions 0-1) instead.

---

## Potential Future (After Mission 2)

If revisiting this concept:

### Prerequisites Before Unpaus

ing
1. **Quality Bar Met**: Generate 10+ landing pages scoring ≥8.0 with independent judges
2. **Distribution Validated**: Identify channel (newsletter, community, ads) with proven reach
3. **Pricing Validated**: Test willingness to pay with small audience
4. **Execution Plan**: Break down into 2-week sprints with clear milestones

### Alternative Approaches
1. **Free Skill for Exposure**: Publish Skill 1 (Goldminer) on GitHub as open-source
2. **Premium Consultation**: Sell 1-on-1 consulting using Skills as demo
3. **SaaS Integration**: Bundle into larger AgencyOS offering

---

## Asset Preservation

### Keep
- `tools/pain_point_goldminer.py` (partial Reddit miner, reusable)
- `tools/knowledge_ingest.py` (production-ready VectorStore pipeline)
- `tools/opportunity_validator.py` (322 opportunities collected)
- `config/knowledge_ingest/reddit_pain_point_patterns.yaml` (proven patterns)
- `docs/rubric-landing-page-evaluation.md` (valuable framework)

### Archive/Delete
- `logs/baseline_experiments/spiritual_guidance_baseline_20251112_012342/` (sample output, low quality)
- `docs/prompt-baseline-sonnet4.5-landing-page.md` (unused prompt template)

---

## References

- **ADR-037**: Prioritize Metaproductivity 2.0 Over Skills/Revenue Path
- **Metaproductivity 2.0 Roadmap**: See original mission plan
- **Skills Documentation**: https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills

---

**Last Updated**: 2025-11-12
**Next Review**: After Mission 2 completion (estimated 4-6 weeks)
