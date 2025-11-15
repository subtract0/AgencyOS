# Phase 00 Baseline Experiment: Spiritual Guidance Landing Page

**Created**: 2025-11-12 01:23:42
**Status**: Ready for manual execution
**Niche**: Life Coaching / Spiritual Guidance
**Model**: Claude Sonnet 4.5

---

## Quick Navigation

### Start Here
1. **PHASE_00_EXECUTION_GUIDE.md** - Complete step-by-step instructions
2. **READY_TO_USE_PROMPT.md** - Full prompt to copy into Sonnet 4.5

### Reference Documents
- `../../docs/rubric-landing-page-evaluation.md` - 5-dimension scoring rubric
- `../../docs/prompt-baseline-sonnet4.5-landing-page.md` - Prompt template (reference)

### Output Directories
- `full_pages/` - Store generated landing pages here
- `hero_variants/` - Store hero section variants here (if testing separately)

### Create After Execution
- `BASELINE_REPORT.md` - Document scores, Lovable test results, Go/No-Go decision

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────┐
│ Phase 00: Manual Baseline Quality Validation           │
└─────────────────────────────────────────────────────────┘

1. GENERATE
   └─> Copy prompt from READY_TO_USE_PROMPT.md
   └─> Paste into Claude Sonnet 4.5 (API or web)
   └─> Save HTML to full_pages/sonnet45_variant_01.html

2. EVALUATE (Ensemble Judges)
   ├─> DeepSeek-R1: Score using rubric
   ├─> o1-mini: Score using rubric
   └─> Human (you): Final decision

3. TEST LOVABLE
   └─> Paste HTML into Lovable.dev
   └─> Check rendering, semantic structure, styles
   └─> Take screenshots, document issues

4. DOCUMENT
   └─> Create BASELINE_REPORT.md with scores and decision

5. GO/NO-GO
   ├─> PASS (≥8/10): Proceed to Phase 1 orchestrator
   ├─> REFINEMENT (6-8/10): Iterate on prompt, re-test
   └─> FAIL (<6/10): Re-evaluate approach
```

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| README.md | This file (navigation) | ✅ Created |
| PHASE_00_EXECUTION_GUIDE.md | Step-by-step instructions | ✅ Created |
| READY_TO_USE_PROMPT.md | Full prompt with pain points | ✅ Created |
| full_pages/ | Landing page outputs | 📁 Empty (waiting for generation) |
| hero_variants/ | Hero section tests | 📁 Empty (optional use) |
| BASELINE_REPORT.md | Evaluation results | ⏳ To be created after execution |

---

## Key Decisions Made

1. **Synthetic Pain Points**: Using realistic examples from prompt template (sufficient for quality validation)
   - Can optionally replace with real Reddit data later
   - For Phase 00, speed > authenticity (we're testing Sonnet 4.5's quality, not data quality)

2. **Ensemble Judging**: DeepSeek-R1 + o1-mini + human
   - Reduces bias, multiple perspectives
   - Human has final override authority

3. **Lovable Integration**: Critical validation step
   - Ensures HTML is actually usable in production
   - Checks semantic structure, no inline styles

4. **Go/No-Go Gate**: Must hit ≥8/10 before building orchestrator
   - De-risks infrastructure investment
   - Validates ChatGPT-5's strategic advice ("vertical slice first")

---

## Estimated Time

**Total**: ~2 hours
- Generation: 5-10 minutes
- Evaluation (3 judges): 40-50 minutes
- Lovable test: 10-15 minutes
- Report creation: 30-45 minutes

**Optional**: +30-60 minutes for real Reddit scrape

---

## Success Criteria

**PASS**:
- ✅ Overall score ≥8.0/10
- ✅ All 5 dimensions ≥7.0/10
- ✅ Lovable integration works
- ✅ HTML is semantic, no inline styles
- → **Result**: Proceed to Phase 1 orchestrator development

**REFINEMENT**:
- ⚠️ Overall score 6.0-7.9/10
- OR any dimension <7.0/10
- → **Result**: Iterate on prompt, re-test

**FAIL**:
- ❌ Overall score <6.0/10
- OR any dimension <5.0/10
- OR Lovable integration broken
- → **Result**: Re-evaluate approach (different model, different framework)

---

## Next Phase (After PASS)

**Phase 1: Generic Orchestrator (Week 1)**
- Convert winning prompt to orchestrator Step 7 template
- Build mission-based orchestrator (not landing-page specific)
- Wire 5 steps: Data collection → Pain extraction → Solution generation → Variant generation → Taste evaluation
- Lovable HTML validation method
- Test with spiritual guidance (existing baseline data)

See full plan in previous conversation context.

---

## Questions?

Check PHASE_00_EXECUTION_GUIDE.md for troubleshooting and detailed instructions.
