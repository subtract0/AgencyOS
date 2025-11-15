# Phase 00 Execution Guide: Sonnet 4.5 Baseline Quality Validation

**Goal**: Validate if Claude Sonnet 4.5 can generate landing pages with ≥8/10 quality (all dimensions ≥7/10) BEFORE building orchestrator infrastructure.

**Time Required**: 2-3 hours (including evaluation)

**Status**: ✅ READY TO EXECUTE (all infrastructure prepared)

---

## Quick Start (TL;DR)

1. **Open**: `READY_TO_USE_PROMPT.md` in this directory
2. **Copy**: The full prompt (starts at "You are an expert landing page copywriter...")
3. **Paste**: Into Claude Sonnet 4.5 (via API or Claude.ai)
4. **Save**: HTML output to `full_pages/sonnet45_variant_01.html`
5. **Evaluate**: Using ensemble judges (DeepSeek-R1 + o1-mini + you)
6. **Test**: Lovable integration (copy HTML into Lovable.dev)
7. **Document**: Results in `BASELINE_REPORT.md`
8. **Decide**: Go/No-Go for Phase 1 orchestrator development

---

## Files Prepared for You

```
spiritual_guidance_baseline_20251112_012342/
├── PHASE_00_EXECUTION_GUIDE.md    # This file
├── READY_TO_USE_PROMPT.md         # Complete prompt with synthetic pain points
├── hero_variants/                 # (empty) Store hero section tests here
├── full_pages/                    # (empty) Store full landing pages here
└── BASELINE_REPORT.md             # (create after evaluation)

../../docs/
├── rubric-landing-page-evaluation.md        # 5-dimension scoring rubric
└── prompt-baseline-sonnet4.5-landing-page.md  # Template (reference only)
```

---

## Step-by-Step Execution

### Step 1: Access Claude Sonnet 4.5

**Option A: Anthropic API (Recommended for Production)**
```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

with open("READY_TO_USE_PROMPT.md") as f:
    prompt = f.read().split("## FULL PROMPT")[1].strip()

response = client.messages.create(
    model="claude-sonnet-4.5-20250111",
    max_tokens=8000,
    messages=[{"role": "user", "content": prompt}]
)

html_output = response.content[0].text

with open("full_pages/sonnet45_variant_01.html", "w") as f:
    f.write(html_output)
```

**Option B: Claude.ai Web Interface (Quick Test)**
1. Go to https://claude.ai
2. Ensure you're using Claude Sonnet 4.5 (check model selector)
3. Copy the full prompt from `READY_TO_USE_PROMPT.md`
4. Paste and send
5. Copy the HTML output to `full_pages/sonnet45_variant_01.html`

---

### Step 2: Evaluate with Ensemble Judges

**Judge 1: DeepSeek-R1** (via API or web interface)

Prompt:
```
You are evaluating a landing page using a 5-dimension rubric. Please score each dimension 0-10 and provide rationale.

RUBRIC: [Paste content from docs/rubric-landing-page-evaluation.md]

LANDING PAGE HTML: [Paste content from full_pages/sonnet45_variant_01.html]

Please provide:
1. Score for each dimension (Clarity, Specificity, Emotional Resonance, Believability, Pain-Alignment)
2. Specific quotes/examples supporting each score
3. Overall score (average of 5 dimensions)
4. Pass/Fail/Refinement status
5. Top 3 improvement suggestions
```

Save DeepSeek-R1's response to `full_pages/sonnet45_variant_01_r1_scores.json`

---

**Judge 2: o1-mini** (via OpenAI API or web interface)

Use the exact same prompt as DeepSeek-R1.

Save o1-mini's response to `full_pages/sonnet45_variant_01_o1_scores.json`

---

**Judge 3: Human (You)**

1. Read the landing page HTML in a browser (open `full_pages/sonnet45_variant_01.html`)
2. Use the rubric in `docs/rubric-landing-page-evaluation.md`
3. Score each dimension independently
4. Compare your scores with AI judges
5. Make final decision (can override AI scores if you strongly disagree)

Save your scores to `full_pages/sonnet45_variant_01_human_scores.json`

---

### Step 3: Test Lovable Integration

1. **Open Lovable**: https://lovable.dev
2. **Create new project** (or use existing)
3. **Copy HTML**: From `full_pages/sonnet45_variant_01.html`
4. **Paste into Lovable** (replace default content)
5. **Check for issues**:
   - Does it render correctly?
   - Are semantic tags recognized?
   - Any inline style warnings?
   - Does structure make sense?
6. **Take screenshots**: Save to `full_pages/lovable_integration_test.png`
7. **Document issues**: Note any problems in `BASELINE_REPORT.md`

---

### Step 4: Create Baseline Report

Create `BASELINE_REPORT.md` in this directory with the following structure:

```markdown
# Phase 00 Baseline Report: Claude Sonnet 4.5 Landing Page Quality

**Date**: [Current date]
**Niche**: Life Coaching / Spiritual Guidance
**Model**: Claude Sonnet 4.5
**Pain Points**: Synthetic examples (not real Reddit data)

---

## Ensemble Scores

| Dimension | DeepSeek-R1 | o1-mini | Human | Average |
|-----------|-------------|---------|-------|---------|
| Clarity | X.X | X.X | X.X | X.X |
| Specificity | X.X | X.X | X.X | X.X |
| Emotional Resonance | X.X | X.X | X.X | X.X |
| Believability | X.X | X.X | X.X | X.X |
| Pain-Alignment | X.X | X.X | X.X | X.X |
| **OVERALL** | **X.X** | **X.X** | **X.X** | **X.X** |

---

## Evaluation Summary

**Status**: [PASS / REFINEMENT / FAIL]

**Rationale**: [Brief explanation of overall quality]

**Strengths**:
- [Top 3 strengths from evaluations]

**Weaknesses**:
- [Top 3 weaknesses from evaluations]

**Improvement Suggestions**:
1. [From ensemble judges]
2. [...]
3. [...]

---

## Lovable Integration Test

**Status**: [SUCCESS / ISSUES FOUND]

**Findings**:
- [Rendering issues, if any]
- [Semantic structure issues, if any]
- [Style warnings, if any]

**Screenshots**: See `lovable_integration_test.png`

---

## Go/No-Go Decision

**Decision**: [GO / NO-GO / REFINEMENT NEEDED]

**Reasoning**: [Explain decision based on scores and Lovable test]

**Next Steps**:
- If GO: Proceed to Phase 1 orchestrator development (use this prompt as Step 7 template)
- If REFINEMENT: [Specific improvements to make], then re-test
- If NO-GO: [Alternative approach - different model, different framework, etc.]

---

## Notes

**Pain Points Quality**:
- Synthetic examples used for Phase 00 (sufficient for quality validation)
- For production, recommend real Reddit scrape from r/spirituality, r/meditation, r/energy_work
- Use config/knowledge_ingest/reddit_pain_point_patterns.yaml for extraction

**Cost Analysis**:
- Sonnet 4.5 API cost: ~$0.XX per landing page
- Within budget for multi-model league testing

**Reproducibility**:
- Prompt saved in READY_TO_USE_PROMPT.md
- Can re-run anytime to validate consistency
```

---

## Success Criteria (Reminder)

**PASS**:
- Overall score ≥8.0/10
- All 5 dimensions ≥7.0/10
- Lovable integration works without major issues
- → Proceed to Phase 1 orchestrator development

**REFINEMENT NEEDED**:
- Overall score 6.0-7.9/10
- OR any dimension <7.0/10
- → Iterate on prompt, re-test

**FAIL**:
- Overall score <6.0/10
- OR any dimension <5.0/10
- OR Lovable integration broken
- → Re-evaluate approach (different model, different framework)

---

## Optional: Real Reddit Data Collection

If you want to replace synthetic pain points with real Reddit data:

**Quick Scrape (30 minutes)**:
```bash
cd /Users/am/Code/AgencyOS

# Use existing knowledge_ingest.py tool
python tools/knowledge_ingest.py \
  --subreddits r/spirituality,r/meditation,r/energy_work \
  --keywords "I struggle,I can't,feeling disconnected,overwhelmed,lost,stuck" \
  --max-posts 30 \
  --output logs/baseline_experiments/spiritual_guidance_baseline_20251112_012342/reddit_raw_data.json

# Extract pain points using patterns
python tools/pain_point_goldminer.py \
  --input logs/baseline_experiments/spiritual_guidance_baseline_20251112_012342/reddit_raw_data.json \
  --patterns config/knowledge_ingest/reddit_pain_point_patterns.yaml \
  --output logs/baseline_experiments/spiritual_guidance_baseline_20251112_012342/pain_points_extracted.json
```

Then manually format the extracted pain points to match the prompt template structure.

**Note**: For Phase 00 quality validation, synthetic examples are sufficient. Real data is more important for Phase 1+ when building production landing pages.

---

## Troubleshooting

**Issue**: Sonnet 4.5 generates inline styles despite prompt instructions
- **Fix**: Add explicit negative example: "DO NOT: <div style='color: red'>"
- **Fix**: Regenerate with stronger emphasis on semantic HTML only

**Issue**: AI judges give wildly different scores (variance >2 points)
- **Check**: Did you provide the full rubric to both judges?
- **Check**: Are judges using same scoring scale (0-10)?
- **Solution**: Human reviewer makes final call

**Issue**: Lovable integration shows errors
- **Check**: Are all HTML tags closed properly?
- **Check**: Are class names valid CSS identifiers?
- **Fix**: Run HTML through validator (https://validator.w3.org/)

**Issue**: Landing page quality too generic
- **Fix**: Add more specific pain point quotes to prompt
- **Fix**: Emphasize direct quote usage in validation checklist
- **Fix**: Run real Reddit scrape for authentic language

---

## Timeline Estimate

| Task | Time | Cumulative |
|------|------|------------|
| Sonnet 4.5 generation | 5-10 min | 10 min |
| DeepSeek-R1 evaluation | 10-15 min | 25 min |
| o1-mini evaluation | 10-15 min | 40 min |
| Human evaluation | 20-30 min | 70 min |
| Lovable integration test | 10-15 min | 85 min |
| Baseline report creation | 30-45 min | 130 min |
| **TOTAL** | **~2 hours** | **2 hours** |

Add 30-60 minutes if running real Reddit scrape.

---

## Contact / Questions

If you encounter issues or need clarification:
1. Check `docs/rubric-landing-page-evaluation.md` for scoring guidelines
2. Check `docs/prompt-baseline-sonnet4.5-landing-page.md` for prompt template details
3. Check the original plan in previous conversation context
4. Ask me (Claude Code agent) for assistance

---

**Ready to start?** Open `READY_TO_USE_PROMPT.md` and copy the prompt to Sonnet 4.5!
