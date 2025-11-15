# Phase 00 Ready-to-Use Prompt: Claude Sonnet 4.5 Landing Page Generation

**Target**: Spiritual Guidance / Life Coaching niche
**Model**: Claude Sonnet 4.5
**Output**: Lovable-ready HTML landing page
**Expected Quality**: ≥8/10 on rubric (all dimensions ≥7/10)

---

## Instructions for Manual Execution

1. **Copy the full prompt below** (starts at "You are an expert landing page copywriter...")
2. **Paste into Claude Sonnet 4.5** via:
   - Anthropic API (recommended for production)
   - Claude.ai web interface (quick test)
3. **Save the HTML output** to `full_pages/sonnet45_variant_01.html`
4. **Evaluate using ensemble judges**:
   - DeepSeek-R1: Score using rubric (docs/rubric-landing-page-evaluation.md)
   - o1-mini: Score using rubric
   - Human (you): Final decision, can override AI scores
5. **Test Lovable integration**: Copy HTML into Lovable.dev to verify it renders correctly
6. **Document results** in `BASELINE_REPORT.md`

---

## Pain Points Data Source

**IMPORTANT**: The pain points below are **synthetic examples** extracted from the prompt template for Phase 00 baseline testing. They represent realistic spiritual guidance pain points but are NOT from actual Reddit data.

**Optional Enhancement**: You can replace these with real Reddit data by:
- Running `tools/knowledge_ingest.py` with spiritual guidance subreddits (r/spirituality, r/meditation, r/energy_work)
- Using the patterns in `config/knowledge_ingest/reddit_pain_point_patterns.yaml`
- Extracting quotes using the "experience_markers" and "pain_signals" filters

For Phase 00 baseline quality validation, these synthetic examples are **sufficient** to test if Sonnet 4.5 can achieve ≥8/10 landing page quality.

---

## FULL PROMPT (Copy everything below this line)

```
You are an expert landing page copywriter specializing in high-converting pages for digital products in the Health/Wealth/Relationships space. Your task is to create a landing page for a spiritual guidance / life coaching product.

STRUCTURAL INSPIRATION (use for section order and story flow, NOT wording):
- Ramit Sethi's "Earnable" page: Clear hero → Pain (current state) → Vision (desired state) → Solution → Proof → Call to action
- Eben Pagan's "Altitude" page: Emotional hook → Problem agitation → Unique mechanism → Transformation promise → Authority → Offer

CONTEXT: Reddit Research on Spiritual Guidance / Life Coaching

I've analyzed 20-30 Reddit threads from r/spirituality, r/meditation, r/energy_work about people struggling with spiritual practices. Here are the TOP 5 PAIN POINTS extracted:

1. **EMOTIONAL**: Feeling disconnected from spiritual practice due to busy schedule
   - Quotes:
     * "I want to meditate but can't find 30 minutes in my day"
     * "Lost my spiritual routine after moving to a new city"
     * "Used to have a daily practice, now I go weeks without connecting"
   - Priority: 9.2/10 (frequency × intensity × solvability)

2. **PRACTICAL**: Difficulty tracking energy patterns and identifying triggers
   - Quotes:
     * "I have no idea what drains my energy vs. what restores it"
     * "Can't see patterns in my spiritual journey - every day feels random"
     * "Wish I knew what actually helps vs. what I'm just doing out of habit"
   - Priority: 8.5/10

3. **KNOWLEDGE_GAP**: Don't know how to start or what practices to try
   - Quotes:
     * "So many spiritual practices out there, I'm overwhelmed and don't know where to begin"
     * "Tried meditation, crystals, journaling - nothing seems to click"
     * "Need guidance that's personalized to my life, not generic advice"
   - Priority: 8.0/10

4. **EMOTIONAL**: Guilt and shame about inconsistency
   - Quotes:
     * "Feel like a failure when I miss a day of practice"
     * "Can't stick to anything long enough to see results"
     * "Everyone else seems to have it figured out - what's wrong with me?"
   - Priority: 7.8/10

5. **RESOURCE**: Can't afford expensive spiritual retreats or 1:1 coaching
   - Quotes:
     * "Want deep transformation but can't pay $3000 for a retreat"
     * "Spiritual guidance shouldn't only be for wealthy people"
     * "Need something that fits my budget but actually works"
   - Priority: 7.5/10

SOLUTION CONCEPT (based on Product Differentiation framework):

**ZenPath**: An AI-powered spiritual journey tracker that helps busy seekers:
- Track daily energy patterns in 5 minutes
- Identify what drains vs. restores energy
- Get personalized micro-practice recommendations
- Build consistency without guilt or pressure

YOUR TASK:

Generate a complete landing page using the Before-After-Bridge (BAB) framework.

REQUIREMENTS:

1. **OUTPUT FORMAT**: Lovable-ready HTML
   - Use semantic HTML5 tags (<header>, <main>, <section>, <footer>)
   - NO inline styles (class names only)
   - NO <style> tags
   - Clean, copy-pasteable code

2. **COPY REQUIREMENTS** (based on rubric):
   - **Clarity**: Value prop in <10 words, benefit immediately obvious
   - **Specificity**: Use exact timeframes ("5 minutes"), numbers ("10,000+ users"), measurable outcomes
   - **Emotional Resonance**: Use direct quotes from pain points, mirror user language
   - **Believability**: Realistic claims, social proof with context, no hype
   - **Pain-Alignment**: Every feature maps to a specific pain point above

3. **STRUCTURE** (BAB Framework):

   **A. HERO SECTION (Above the Fold)**
   - Headline: Clear value prop (<10 words)
   - Subheadline: Who it's for + what problem it solves (15-20 words)
   - 3-5 bullets: Each addresses a specific pain point using direct quotes or paraphrases
   - Primary CTA: Action-oriented, specific (e.g., "Start Your Free 14-Day Trial")
   - Hero image placeholder: <img src="hero-placeholder.jpg" alt="...">

   **B. BEFORE SECTION (Current Pain State)**
   - Section headline: "When [Pain Point] Becomes Your Daily Reality" or similar
   - 3-4 pain scenarios:
     * Use direct quotes from research
     * Paint vivid scenes (not bullet points - narrative paragraphs)
     * Make reader feel "that's exactly me"
   - Optional: Belief deconstruction paragraph ("Many people think X, but...")

   **C. AFTER SECTION (Desired Future State)**
   - Section headline: "Imagine [Desired Outcome]..."
   - 3-4 outcome descriptions:
     * What life looks like when problem is solved
     * Emotional benefits (not just functional)
     * Specific, believable transformations
   - Bridge teaser: "What if this transformation didn't require [pain point constraint]?"

   **D. BRIDGE SECTION (The Solution)**
   - Product intro:
     * Name: ZenPath
     * One-sentence description
     * Unique mechanism (why this is different)
   - How it works (3 simple steps):
     1. [Step with specific timeframe - e.g., "Track your energy in 5 minutes"]
     2. [Pattern recognition - e.g., "Discover your unique energy patterns"]
     3. [Personalized guidance - e.g., "Get micro-practices tailored to your life"]
   - Key features (3-5):
     * Each feature maps to a pain point
     * Use specific names (not "our tool" but "Energy Pattern Tracker")
     * Include benefit + feature (e.g., "Daily 5-Minute Check-In → Build consistency without overwhelm")

   **E. SOCIAL PROOF / TESTIMONIALS**
   - 2-3 testimonials (fictional but believable):
     * Name + brief context (e.g., "Sarah, busy parent of 3")
     * Specific outcome (e.g., "Built a consistent practice for the first time in 5 years")
     * Quote that addresses a pain point
   - Optional: Social proof stats ("Join 10,000+ spiritual seekers")

   **F. PRICING**
   - 14-day free trial (no credit card required)
   - After trial: $12/month or $99/year (save 31%)
   - What's included (3-5 items)
   - No-commitment message ("Cancel anytime")

   **G. FAQ**
   - 4-6 common objections:
     * "I don't have time for another app" → Answer referencing 5-minute commitment
     * "I've tried spiritual apps before" → Answer about personalization
     * "What if I miss days?" → Answer about guilt-free approach
     * "Do I need any spiritual experience?" → Answer about beginner-friendliness
     * "How is this different from journaling?" → Answer about pattern recognition
     * "Can I cancel if it doesn't work?" → Answer about free trial + cancellation

   **H. FINAL CTA SECTION**
   - Compelling final push:
     * Restate main benefit
     * Address urgency without being pushy (e.g., "Start before your next busy week begins")
     * Primary CTA button
     * Trust signals ("14-day free trial, no credit card, cancel anytime")

4. **TONE & STYLE**:
   - Warm, supportive (not clinical)
   - Honest, not hypey
   - Use "you" language (second person)
   - Avoid spiritual jargon or explain if used
   - Balance emotion with specificity

5. **VALIDATION CHECKLIST** (ensure these before outputting):
   - [ ] Every bullet/feature addresses a specific pain point from research
   - [ ] At least 3 direct quotes or paraphrases from pain points
   - [ ] Specific timeframes mentioned (5 minutes, 14 days, etc.)
   - [ ] Social proof includes context and numbers
   - [ ] No superlatives without proof (no "revolutionary", "miracle", "#1" unless backed)
   - [ ] HTML is semantic, no inline styles
   - [ ] All sections follow BAB structure

OUTPUT:

Provide the full landing page HTML code, ready to paste into Lovable. Include comments indicating each section (<!-- HERO SECTION -->, <!-- BEFORE SECTION -->, etc.) for easy navigation.
```

---

## Next Steps After Generation

1. **Save HTML output** to `full_pages/sonnet45_variant_01.html`
2. **Score with ensemble judges**:
   - Prompt DeepSeek-R1 with rubric + HTML
   - Prompt o1-mini with rubric + HTML
   - Human review using rubric
3. **Test Lovable integration**:
   - Copy HTML into Lovable.dev
   - Verify semantic structure renders correctly
   - Check for any styling issues
4. **Create BASELINE_REPORT.md** with:
   - Ensemble scores (per dimension + overall)
   - Lovable integration test results
   - Go/No-Go decision for Phase 1
   - Recommended improvements (if <8/10)

---

## Success Criteria

**PASS**: Overall ≥8.0/10 AND all dimensions ≥7.0/10
**REFINEMENT**: Overall 6.0-7.9 OR any dimension <7.0
**FAIL**: Overall <6.0 OR any dimension <5.0

If PASS → Proceed to Phase 1 (orchestrator development)
If REFINEMENT → Iterate on prompt, test again
If FAIL → Re-evaluate approach (consider different model or framework)
