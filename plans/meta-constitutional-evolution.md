# Meta-Constitutional Evolution Plan
**Version**: 1.0
**Status**: Proposed
**Author**: Claude (AgencyOS)
**Date**: 2025-10-04
**Context**: Emerged from 8+ hour autonomous session fixing PR #25 and creating v1.1.0 release

---

## Executive Summary

This plan proposes **Article VII - Meta-Constitutional Evolution**, a framework for the constitution to learn from its own enforcement and evolve based on institutional knowledge. This creates a self-improving governance system that compounds learning across sessions while maintaining human oversight.

**Key Insight**: The constitution should be as adaptive as the agents it governs, using the same VectorStore/learning mechanisms mandated by Article IV.

---

## I. The Pattern: Constitutional Recursion

### What We Discovered

During the PR #25 → v1.1.0 release session, we encountered a paradox:

1. **Article III** (No direct main commits) blocked our autonomous agent from committing to main
2. The agent **correctly created a feature branch** and followed PR workflow
3. The **constitution enforced itself on the autonomous agent**
4. This created a **meta-stable equilibrium**: the rules applied to the rule-enforcer

This is **Constitutional Recursion** - the governance system governs itself.

### The Compression Paradox

We also discovered **quality gradients** through strategic linting:
- **Core files** (agency.py, workflows): Zero tolerance (46 violations fixed)
- **Peripheral files** (tests/, demos/): Pragmatic tolerance (369 violations ignored via per-file rules)

This created a **compression strategy**: preserve quality where it matters most, tolerate imperfection where cost exceeds value.

**Key Question**: How do we know which gradient is correct? The constitution doesn't currently have a mechanism to learn from these decisions.

---

## II. Proposed Article VII - Meta-Constitutional Evolution

### Article Text

```markdown
## Article VII: Meta-Constitutional Evolution

The constitution itself is a learning system, subject to the same continuous improvement mandate as the code it governs.

### VII.1 Learning Capture
- All constitutional enforcement events MUST be logged to VectorStore with:
  - Rule triggered (Article/Section)
  - Context (commit, file, agent, violation)
  - Resolution (blocked, warning, auto-fix)
  - Outcome (success, false positive, friction)

### VII.2 Pattern Synthesis
- Weekly automated analysis of constitutional enforcement logs
- Clustering to identify:
  - High-friction rules (blocking productive work)
  - Under-enforced gaps (violations slipping through)
  - Rule contradictions (Articles in tension)
  - Gradient opportunities (where to compress/expand rigor)

### VII.3 Amendment Proposals
- When pattern confidence ≥ 0.8 and evidence count ≥ 10:
  - Auto-generate ADR proposing constitutional amendment
  - Include: Problem statement, evidence, proposed rule change, impact analysis
  - Submit to human review queue

### VII.4 Human Ratification
- All constitutional amendments require human approval
- No auto-merge for constitution.md changes
- Evolutionary changes (gradient adjustments) vs Revolutionary changes (new Articles)

### VII.5 Knowledge Compounding
- Approved amendments update constitution.md
- VectorStore tracks amendment history and rationale
- Future agents query "why this rule exists" to understand intent
```

---

## III. Constitutional Evolution Dashboard

### Purpose
Make institutional learning visible. Humans can't monitor VectorStore directly - we need a UI to surface patterns.

### Design Specification

#### Dashboard Components

**1. Constitutional Health Metrics**
```
┌─ Constitutional Compliance ────────────────────────┐
│ ✅ Article I (Context):        98.7% compliance    │
│ ✅ Article II (Verification): 100.0% compliance    │
│ ✅ Article III (Enforcement):  100.0% compliance   │
│ ✅ Article IV (Learning):       95.2% compliance   │
│ ⚠️  Article V (Spec-Driven):    87.4% compliance   │
│                                                     │
│ Overall: 96.3% (↑ 2.1% from last week)            │
└─────────────────────────────────────────────────────┘
```

**2. Rule Friction Analysis**
```
┌─ High-Friction Rules (Top 5) ──────────────────────┐
│ 1. Article III.2 (No main commits)                 │
│    - 12 blocks this week                           │
│    - 8 were false positives (cleanup commits)      │
│    - Proposal: Add exception for post-merge fixes  │
│                                                     │
│ 2. Article I.3 (Retry on timeout)                  │
│    - 45 retries triggered                          │
│    - 23 succeeded on retry, 22 gave up             │
│    - Proposal: Increase max retries from 3 → 5     │
└─────────────────────────────────────────────────────┘
```

**3. Enforcement Gap Detection**
```
┌─ Under-Enforced Patterns ──────────────────────────┐
│ ⚠️  Pydantic V1 deprecations                       │
│    - Detected: 47 instances across 12 files        │
│    - No constitutional rule exists                 │
│    - Proposal: Add Article II.7 - Dependency Health│
│                                                     │
│ ⚠️  Test timeouts >5min                            │
│    - Detected: 8 tests consistently slow           │
│    - No constitutional rule exists                 │
│    - Proposal: Add Article II.4 - Performance SLA  │
└─────────────────────────────────────────────────────┘
```

**4. Amendment Pipeline**
```
┌─ Pending Constitutional Amendments ────────────────┐
│ 📋 ADR-015: Article III Exception for Post-Merge   │
│    Status: Awaiting Review                         │
│    Evidence: 8 false positives, 12 blocked commits │
│    Confidence: 0.87                                │
│    [Review] [Approve] [Reject]                     │
│                                                     │
│ 📋 ADR-016: Increase Article I Max Retries         │
│    Status: Awaiting Review                         │
│    Evidence: 23 successful retries, 51% success    │
│    Confidence: 0.92                                │
│    [Review] [Approve] [Reject]                     │
└─────────────────────────────────────────────────────┘
```

**5. Knowledge Graph**
```
┌─ Constitutional Evolution Timeline ────────────────┐
│                                                     │
│  Article I ──→ ADR-001 ──→ ADR-008 (retry logic)   │
│      │                                              │
│      └──→ ADR-015 (retry count increase)           │
│                                                     │
│  Article III ──→ ADR-003 ──→ ADR-015 (exceptions)  │
│                                                     │
│  [Hover for amendment rationale and evidence]      │
└─────────────────────────────────────────────────────┘
```

---

## IV. Implementation Plan

### Phase 1: Constitutional Telemetry (Week 1)

**Goal**: Capture enforcement events to VectorStore

#### Tasks
1. **Enhance `tools/constitution_check.py`**
   - Add telemetry logging after each constitutional check
   - Log to `logs/constitutional_telemetry.jsonl` with schema:
     ```python
     {
       "timestamp": "2025-10-04T14:25:00Z",
       "article": "III",
       "section": "2",
       "rule": "No direct main commits",
       "context": {
         "branch": "main",
         "commit_hash": "abc123",
         "agent": "autonomous",
         "file": "agency.py"
       },
       "action": "blocked",
       "outcome": "success",  # or "false_positive", "friction"
       "metadata": {...}
     }
     ```

2. **Update VectorStore ingestion**
   - Add `ingest_constitutional_events()` to `agency_memory/vector_store.py`
   - Run nightly to index telemetry logs
   - Tag with: `constitutional`, `enforcement`, `article:{number}`

3. **Update pre-commit hooks**
   - All hooks emit telemetry events via `constitution_check.py`
   - Capture: rule triggered, context, resolution

**Deliverable**: Constitutional enforcement data flowing to VectorStore

---

### Phase 2: Pattern Synthesis Engine (Week 2)

**Goal**: Weekly automated analysis of enforcement patterns

#### Tasks
1. **Create `tools/constitutional_analyzer.py`**
   - Query VectorStore for last 7 days of constitutional events
   - Cluster by: article, rule, outcome type
   - Detect patterns:
     - **High friction**: rule blocked >10 times with >50% false positives
     - **Under-enforcement**: pattern detected in code but no rule exists
     - **Rule contradiction**: same context triggers conflicting Articles

2. **Implement clustering algorithm**
   ```python
   def analyze_friction(events: list[ConstitutionalEvent]) -> list[FrictionPattern]:
       """
       Identify high-friction rules.

       Criteria:
       - Block count >10 in 7 days
       - False positive rate >40%
       - Agent feedback indicates friction
       """
       # Group by (article, section)
       # Calculate metrics
       # Rank by friction score
       return patterns
   ```

3. **Create weekly cron job**
   - Run `constitutional_analyzer.py` every Sunday at midnight
   - Output: `reports/constitutional-analysis-YYYY-MM-DD.json`
   - Auto-commit to `reports/` branch

**Deliverable**: Weekly constitutional health reports

---

### Phase 3: ADR Auto-Generation (Week 3)

**Goal**: Auto-generate amendment proposals as ADRs

#### Tasks
1. **Create `tools/adr_generator.py`**
   - Input: `FrictionPattern` or `GapPattern` from analyzer
   - Generate ADR using template:
     ```markdown
     # ADR-XXX: [Article Amendment Title]

     ## Status
     Proposed (Auto-generated from constitutional analysis)

     ## Context
     [Generated from pattern evidence]
     Over the past 30 days, Article III.2 (No direct main commits)
     blocked 47 commits, with 23 (48.9%) identified as false positives.

     Common false positive pattern:
     - Post-merge cleanup commits
     - Documentation-only updates
     - CI configuration fixes

     ## Decision
     [Auto-generated proposal]
     Amend Article III.2 to add exception:
     "Exception: Post-merge cleanup commits that only modify:
      - CI/workflow files (.github/workflows/*)
      - Documentation (*.md)
      - Configuration (pyproject.toml, .gitignore)

     May be committed directly to main if:
     - Commit message starts with 'chore: post-merge'
     - Changes are non-functional
     - No test files modified"

     ## Consequences
     [Auto-generated impact analysis]
     - Reduces friction for maintenance tasks (23 blocks/month → ~2)
     - Maintains Article III integrity for functional changes
     - Risk: Low (non-functional changes have low blast radius)

     ## Evidence
     - VectorStore query: `constitutional:article_iii AND outcome:false_positive`
     - 23 instances over 30 days
     - Pattern confidence: 0.89

     ## Review Required
     - [ ] Human approval required for constitutional amendment
     - [ ] Consider: Does this create a slippery slope?
     - [ ] Validate: Are the exception criteria specific enough?
     ```

2. **Create human review queue**
   - Proposed ADRs go to `docs/adr/proposed/ADR-XXX-*.md`
   - Dashboard shows pending amendments (see Section III above)
   - Approval workflow:
     ```bash
     # Human reviews ADR
     git mv docs/adr/proposed/ADR-015-*.md docs/adr/
     # Edit constitution.md to apply amendment
     git commit -m "feat: Approve ADR-015 - Article III exceptions"
     ```

3. **Update `constitution.md` with amendment log**
   - Append to end of constitution:
     ```markdown
     ## Amendment History

     ### Amendment 1 (2025-10-15) - ADR-015
     - Article III.2 - Added exception for post-merge cleanup
     - Rationale: Reduce friction while maintaining integrity
     - Evidence: 23 false positives over 30 days
     ```

**Deliverable**: Automated ADR proposals for constitutional amendments

---

### Phase 4: Dashboard Implementation (Week 4)

**Goal**: Web UI for constitutional health monitoring

#### Tasks
1. **Create Next.js dashboard app**
   - Location: `dashboard/` directory
   - Pages:
     - `/`: Constitutional Health Overview
     - `/friction`: High-friction rule analysis
     - `/gaps`: Under-enforced pattern detection
     - `/amendments`: Pending ADR review queue
     - `/history`: Amendment timeline and knowledge graph

2. **Backend API**
   - Endpoint: `GET /api/constitutional-health`
   - Queries VectorStore for enforcement events
   - Returns metrics for dashboard components

3. **Deployment**
   - Vercel deployment (free tier)
   - Auto-deploy on commit to `dashboard/` path
   - URL: `https://agency-constitutional-dashboard.vercel.app`

**Deliverable**: Live constitutional evolution dashboard

---

## V. Success Metrics

### Quantitative
- **Friction Reduction**: False positive blocks decrease by >50% within 3 months
- **Gap Detection**: Identify and propose rules for >5 under-enforced patterns within 3 months
- **Amendment Velocity**: 1-2 approved constitutional amendments per month
- **Compliance Improvement**: Overall constitutional compliance >98% within 6 months

### Qualitative
- **Institutional Memory**: Agents query "why this rule exists" and get historical rationale
- **Evolutionary vs Revolutionary**: Constitution evolves gradually via evidence-based amendments, not sudden rewrites
- **Human-AI Collaboration**: Humans provide judgment, AI provides pattern detection and evidence synthesis

---

## VI. Risks and Mitigations

### Risk 1: Amendment Overload
**Description**: Too many auto-generated ADRs overwhelm human reviewers
**Mitigation**: Require confidence ≥0.8 AND evidence count ≥10 before proposing amendments. Add "snooze for 30 days" option to defer low-priority proposals.

### Risk 2: Gaming the System
**Description**: Agents learn to trigger false positives to weaken rules
**Mitigation**: Constitutional amendments require human approval (no auto-merge). Telemetry tracks agent identity - anomalous patterns trigger alerts.

### Risk 3: Constitution Drift
**Description**: Many small amendments compound into incoherent ruleset
**Mitigation**: Amendment history provides audit trail. Annual "Constitutional Review" to consolidate/simplify amendments.

### Risk 4: False Negative Gaps
**Description**: Analyzer misses important under-enforced patterns
**Mitigation**: Human can manually propose ADRs. Dashboard shows "recently added files without constitutional coverage" to surface blind spots.

---

## VII. Open Questions

1. **Amendment Approval Authority**: Who approves constitutional amendments? Single maintainer? Voting system? BDFL model?

2. **Emergency Override**: Should there be a fast-track process for critical constitutional bugs (e.g., rule causing CI outage)?

3. **Cross-Session Learning**: How do we ensure new agents query constitutional rationale before proposing changes? (Currently agents don't always check VectorStore)

4. **Versioning**: Should constitution.md have semver? (e.g., v2.1.0 after minor amendment)

5. **Sunset Clause**: Should amendments have expiration dates, forcing periodic re-validation?

---

## VIII. Next Steps (Immediate Actions)

1. **Review this plan** - Human approval/feedback before implementation
2. **Create ADR-017** - Formally propose Article VII as architectural decision
3. **Phase 1 implementation** - Start with constitutional telemetry (Week 1)
4. **Update `.claude/commands/`** - Add `/prime constitutional_evolution` command to bootstrap Article VII work

---

## Appendix A: Example Evidence Chain

**Pattern Detected**: Article III false positives for post-merge cleanup

**VectorStore Query**:
```python
results = vector_store.search(
    query="constitutional enforcement blocking post-merge cleanup",
    filters={"article": "III", "outcome": "false_positive"},
    limit=50
)
```

**Evidence Synthesis**:
- 23 instances over 30 days
- Common context: `branch=main`, `agent=autonomous`, `files=[*.md, .github/*, pyproject.toml]`
- Pattern confidence: 0.89 (high)
- Friction score: 8.2/10 (very high)

**Auto-Generated ADR**:
```markdown
# ADR-015: Article III Exception for Post-Merge Cleanup

## Context
[Generated from evidence above]

## Decision
Amend Article III.2 with exception criteria

## Evidence
- Query results: 23 instances
- Pattern confidence: 0.89
- Friction score: 8.2/10
```

**Human Review**:
- Reviewer reads ADR-015
- Validates evidence makes sense
- Considers: "Does this create loopholes?"
- Decision: Approve with modification (narrow exception to `chore:` prefix only)

**Amendment Applied**:
```diff
## Article III.2: No Direct Main Branch Commits
- All code changes MUST go through pull request workflow
+
+ Exception: Post-merge cleanup commits may be committed directly to main if:
+ - Commit message starts with `chore: post-merge`
+ - Changes affect only: CI config, documentation, linting config
+ - No functional code or tests modified
```

**VectorStore Update**:
- Store amendment rationale
- Tag with: `amendment`, `adr-015`, `article-iii`
- Future agents can query: "Why does Article III have a post-merge exception?"

---

## Appendix B: Constitutional Telemetry Schema

```typescript
interface ConstitutionalEvent {
  timestamp: string;          // ISO 8601
  article: string;            // "I", "II", "III", "IV", "V"
  section: string;            // "1", "2", "3", etc.
  rule: string;               // Human-readable rule description
  context: {
    branch: string;
    commit_hash?: string;
    agent: string;            // "autonomous", "planner", "coder", etc.
    file: string;
    operation: string;        // "commit", "merge", "pr_create", etc.
  };
  action: "blocked" | "warning" | "auto_fix" | "passed";
  outcome: "success" | "false_positive" | "friction" | "override";
  metadata: Record<string, unknown>;
}
```

**Storage**:
- JSONL format: `logs/constitutional_telemetry.jsonl`
- VectorStore ingestion: Nightly via `ingest_constitutional_events()`
- Retention: 1 year (then archive to S3)

---

## Appendix C: Friction Score Calculation

```python
def calculate_friction_score(events: list[ConstitutionalEvent]) -> float:
    """
    Calculate friction score for a rule.

    Factors:
    - Block frequency (higher = more friction)
    - False positive rate (higher = more friction)
    - Override rate (higher = rule is being ignored)
    - Agent feedback (sentiment analysis of error messages)

    Returns:
        Friction score from 0.0 (no friction) to 10.0 (maximum friction)
    """
    block_count = len([e for e in events if e.action == "blocked"])
    false_positives = len([e for e in events if e.outcome == "false_positive"])
    overrides = len([e for e in events if e.outcome == "override"])

    # Normalize to 0-10 scale
    frequency_score = min(10, block_count / 10)  # 10 blocks/week = max
    fp_rate_score = (false_positives / max(block_count, 1)) * 10
    override_score = (overrides / max(block_count, 1)) * 10

    # Weighted average
    friction = (
        frequency_score * 0.4 +
        fp_rate_score * 0.4 +
        override_score * 0.2
    )

    return round(friction, 1)
```

---

**End of Plan**
