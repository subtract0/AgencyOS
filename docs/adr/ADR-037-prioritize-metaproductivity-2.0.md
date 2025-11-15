# ADR-037: Prioritize Metaproductivity 2.0 Over Skills/Revenue Path

**Date**: 2025-11-12
**Status**: Accepted
**Deciders**: User + Code (OpenAI) + Claude (Anthropic)

---

## Context

We evaluated two strategic paths for AgencyOS development:

### Path A: Skills + Opportunity Report (Revenue-Focused)
- **Goal**: Generate revenue in 48 hours
- **Approach**:
  - Create 3 Claude Skills (Pain Point Goldminer, Offer Architect, Web Forge)
  - Package 322 collected opportunities as PDF report
  - Sell for $299 each
- **Projected Timeline**: 2 days
- **Projected Revenue**: $299 × 10 sales = $2,990

### Path B: Metaproductivity 2.0 (Infrastructure-Focused)
- **Goal**: Build autonomous agent system with meta-learning
- **Approach**:
  - Mission 0-1: CMP scaffolding + foundation (2 weeks)
  - Missions 2-5: Self-healing, backlog execution, 24/7 operation (4-8 weeks total)
- **Projected Timeline**: 4-8 weeks
- **Projected Revenue**: $0 (infrastructure investment)

---

## Decision

**We choose Path B: Metaproductivity 2.0**

Focus all resources on Missions 0-1 (CMP scaffolding and foundation). Park the Skills/revenue path until after Mission 2.

---

## Rationale

### Path A Failed Critical Evaluation

**1. Marketability Issues**
- ❌ No validated distribution channel
- ❌ No pricing validation data
- ❌ Revenue projection ($2,990) is wishful math
- ❌ Customers can gather Reddit notes themselves for free
- **Reality**: <10% probability of even one $299 sale without audience/promotion

**2. Execution Gap**
- **Claimed**: "2 days to revenue"
- **Reality**: Multi-week project
- **What exists**:
  - ✅ `tools/pain_point_goldminer.py` (partial Reddit miner)
  - ✅ `config/knowledge_ingest/reddit_pain_point_patterns.yaml` (proven patterns)
  - ✅ `docs/rubric-landing-page-evaluation.md` (5-dimension framework)
  - ✅ 322 collected opportunities
- **What's missing**:
  - ❌ Quora scraper (Selenium implementation)
  - ❌ Offer generator (Alex Hormozi framework)
  - ❌ Copywriting engine (BAB framework)
  - ❌ Rubric scorer (ensemble judging)
  - ❌ Next.js template + components
  - ❌ Deployment pipeline
  - ❌ 50-opportunity report packaging
  - ❌ Checkout/payment system
  - ❌ Promotion/distribution plan

**3. Quality Not Met**
- **Claimed**: Sample landing page scored 8.8/10
- **Reality**: Independent review scored it 6/10
- **Issues** (from `logs/baseline_experiments/spiritual_guidance_baseline_20251112_012342/full_pages/sonnet45_variant_01.html`):
  - No concrete proof for claims ("Join 10,000+ seekers")
  - Repetitive pain point quotes (feels canned)
  - Vague product features ("AI-powered pattern recognition")
  - **Scores**:
    - Believability: <6
    - Emotional Resonance: 5-6
    - Specificity: 6
    - Overall: 6/10 (not 8.8/10)
- **Problem**: Using this as portfolio piece would undermine "grand slam offer" promise

**4. Opportunity Cost**
- Path A consumes 2+ weeks for uncertain revenue
- Path B makes AgencyOS itself better, compounds over time
- Path B utilizes Mac Studio M4 Max 128GB 24/7 productively
- Path B aligns with long-term autonomous vision

### Path B Advantages

**1. Compounds Over Time**
- Every autonomous PR is an experiment
- Every merge/reject trains the CMP bandit
- Clades evolve based on real performance
- AgencyOS gets smarter with each iteration

**2. Makes Core Product Better**
- Self-healing agents fix failing tests automatically
- Backlog execution ships features while you sleep
- 24/7 operation utilizes local compute efficiently
- Institutional learning accumulates in VectorStore

**3. Proven Infrastructure**
- CMP types build on existing AgencyOS patterns (Result<T,E>, Pydantic, VectorStore)
- Constitutional compliance from day 1 (Articles I-V)
- TDD workflow ensures quality

**4. Clear Milestones**
- Mission 0: CMP scaffolding (1-2 days)
- Mission 1: Foundation + M4 calibration (3-5 days)
- Mission 2: Learning Coach + CMP pipeline (5-7 days)
- Each mission independently valuable

---

## Consequences

### Immediate Actions
1. ✅ **Archive Skills work**: Created `docs/skills/pain-point-offer-web-skill-suite.md`
2. ✅ **Document decision**: This ADR
3. 🔄 **Start Mission 0**: CMP scaffolding implementation

### What We Keep
- `tools/pain_point_goldminer.py` - Reusable for future data mining
- `tools/knowledge_ingest.py` - Production-ready VectorStore pipeline
- `tools/opportunity_validator.py` - 322 opportunities collected
- `config/knowledge_ingest/reddit_pain_point_patterns.yaml` - Proven extraction patterns
- `docs/rubric-landing-page-evaluation.md` - Valuable copywriting framework

### What We Park (Revisit After Mission 2)
- Skills implementation (3-skill pipeline)
- Opportunity Report packaging
- Landing page generation
- Revenue initiatives

### Conditions for Revisiting Path A
1. **Quality Bar Met**: 10+ landing pages scoring ≥8.0 with independent judges
2. **Distribution Validated**: Proven channel (newsletter, community, ads) with reach
3. **Pricing Validated**: Test willingness to pay with small audience
4. **Execution Plan**: Broken into 2-week sprints with clear milestones

---

## Mission 0 Goals (Next Steps)

### Deliverables
1. `docs/cmp_schema.md` - CMP event and score schema documentation
2. `agency_memory/learning.py` - CMP types:
   - `CmpEvent` dataclass
   - `CmpScore` dataclass
   - `CmpStore` (JSONL to `data/cmp_events.jsonl`)
   - `compute_clade_score()` function
   - `CladeSelector` (epsilon-greedy bandit)
3. `shared/agent_context.py` - Extend with `agent_id`, `clade_id`, `task_type`, `provenance_id`
4. `agency_memory/enhanced_memory_store.py` - Extend with CMP fields + `set_reinforcement()`
5. `tools/cmp_console.py` - CLI for CMP inspection
6. Unit tests for all CMP components

### Timeline
- Estimated: 1-2 days
- Done when: `from agency_memory.learning import CmpEvent, CmpScore, CmpStore, CladeSelector` works

---

## References

- **Metaproductivity 2.0 Roadmap**: See original mission plan (5 missions, 4-8 weeks)
- **Parked Skills Work**: `docs/skills/pain-point-offer-web-skill-suite.md`
- **Constitutional Compliance**: Articles I-V (complete context, 100% verification, automated enforcement, continuous learning, spec-driven)
- **VectorStore Architecture**: `agency_memory/enhanced_memory_store.py`, ADR-006

---

## Lessons Learned

1. **Optimism Bias**: Self-evaluation (8.8/10) vs. independent review (6/10) - always validate externally
2. **Execution Realism**: "2 days to revenue" was wishful thinking; reality is multi-week with uncertain outcome
3. **Infrastructure First**: Building tools that compound > chasing quick revenue
4. **Distribution Matters**: Great product without audience = $0 revenue
5. **Quality Bar**: 6/10 output undermines brand; need ≥8/10 before monetizing

---

**Last Updated**: 2025-11-12
**Next Review**: After Mission 2 completion (estimated 2-3 weeks)
