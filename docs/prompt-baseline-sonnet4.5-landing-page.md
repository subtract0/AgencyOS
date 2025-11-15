# Claude Sonnet 4.5 Baseline Prompt: Landing Page Generation

## Purpose
This is the "golden prompt" used in Phase 00 to establish baseline landing page quality (≥8/10 on rubric). Once proven effective, this prompt becomes the template for the orchestrator's Step 7 (full page generation).

## Context
- **Target Model**: Claude Sonnet 4.5
- **Niche**: Life Coaching / Spiritual Guidance
- **Framework**: Before-After-Bridge (BAB) copywriting
- **Output Format**: Lovable-ready HTML (semantic tags, no inline styles)
- **Structural Inspiration**: Ramit Sethi's Earnable, Eben Pagan's Altitude

---

## Full Prompt Template

```
You are an expert landing page copywriter specializing in high-converting pages for digital products in the Health/Wealth/Relationships space. Your task is to create a landing page for a spiritual guidance / life coaching product.

STRUCTURAL INSPIRATION (use for section order and story flow, NOT wording):
- Ramit Sethi's "Earnable" page: Clear hero → Pain (current state) → Vision (desired state) → Solution → Proof → Call to action
- Eben Pagan's "Altitude" page: Emotional hook → Problem agitation → Unique mechanism → Transformation promise → Authority → Offer

CONTEXT: Reddit Research on Spiritual Guidance / Life Coaching

I've analyzed 20-30 Reddit threads from r/spirituality, r/meditation, r/energy_work about people struggling with spiritual practices. Here are the TOP 5 PAIN POINTS extracted:

[PASTE PAIN POINTS HERE - Format:]

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

## Usage Instructions

### Phase 00 Manual Baseline (NOW)
1. Copy this prompt
2. Replace `[PASTE PAIN POINTS HERE]` with actual pain points from Reddit research
3. Send to Claude Sonnet 4.5 via Anthropic API or Claude.ai
4. Evaluate output using `docs/rubric-landing-page-evaluation.md`
5. If <8/10, iterate on prompt and re-test
6. Save winning prompt version for Phase 1

### Phase 1+ Orchestrator Integration (LATER)
1. Orchestrator loads this prompt from `docs/prompt-baseline-sonnet4.5-landing-page.md`
2. Injects variables:
   - `{pain_points}` from Step 3 (pain point extraction)
   - `{solution_concept}` from Step 4 (solution generation)
   - `{winning_hero}` from Step 6 (hero evaluation)
3. Calls Sonnet 4.5 with injected prompt
4. Validates output with `_validate_lovable_html()` method
5. Returns LandingPage object with metadata

---

## Prompt Evolution Log

### Version 1.0 (2025-11-12)
- Initial baseline prompt for Phase 00
- Target: Life Coaching / Spiritual Guidance niche
- Structural references: Earnable, Altitude
- Output format: Lovable-ready HTML
- Rubric alignment: All 5 dimensions (clarity, specificity, resonance, believability, pain-alignment)

### Future Versions (TBD)
- Version 1.1: Adjustments based on Phase 00 results
- Version 2.0: Generalized for other niches (replace spiritual guidance placeholders)
- Version 3.0: Optimized for multi-model league (variations for different models)

---

## Notes
- This prompt is deliberately verbose to ensure Sonnet 4.5 has full context
- The pain point examples are placeholders - real data will come from Reddit research
- HTML output format is critical for Lovable integration (Phase 00 requirement)
- Rubric alignment is baked into the prompt requirements to increase ≥8/10 success rate
