# Specification: Tiered Spec Review for Two-Stage Workflow Checkpoint

**Version:** 1.0.0
**Created:** 2025-10-15
**Status:** Draft (Awaiting Approval)
**Priority:** High
**Tags:** orchestrator, two-stage-workflow, ux, checkpoint, article-v

---

## Executive Summary

**Mission:** Enhance TwoStageOrchestrator's spec approval checkpoint with progressive disclosure (Tier 1: 30-second executive summary, Tier 2: 2-minute key decisions, Tier 3: full spec) and auto-approve timeout (30 seconds, configurable) for rapid autonomous iteration while maintaining constitutional oversight.

**Approach:** Create deterministic tier generator that parses SpecGenerator output into 3 progressive tiers using structured templates. Integrate auto-approve countdown with interrupt capability. Use Unicode boxes, color coding, and keyboard shortcuts for professional UX.

**Test Summary:** 14 NECESSARY tests (9 for tier generator: Normal/Edge/Cascading/Essential/Security/Spec/Accuracy/Regression/Yield, 5 for UI: Normal/Edge/Security/Spec/Resilience)

**Deliverables:** 7 files (3 implementation, 2 test, 1 ADR, 1 config)

**Constitutional Status:** Articles I-V satisfied (complete context, 100% tests, automated enforcement, VectorStore integration, spec-driven)

**Effort Estimate:** 6-8 hours (4h implementation, 2h testing, 1-2h validation/PR)

**Risk Level:** 🟢 Low (UX enhancement, no breaking changes, backward compatible)

---

## I. Goals (What We WILL Accomplish)

### Primary Goals
1. **Progressive Disclosure UX:** Present specifications in 3 progressive tiers allowing users to approve in 30 seconds (Tier 1 only), 2 minutes (Tier 1+2), or deep dive (Tier 3) based on complexity/confidence
2. **Auto-Approve Timeout:** Implement 30-second configurable countdown with interrupt capability (any key) to enable rapid autonomous iteration while maintaining oversight
3. **Deterministic Parsing:** Extract Tier 1 (executive summary) and Tier 2 (key decisions) from SpecGenerator output using template-based parsing (<2 seconds generation time)
4. **Professional UI:** Unicode boxes, color coding (✅/⚠️/🔴), keyboard shortcuts [A]pprove/[R]evise/[V]iew/[Q]uit for production-ready experience
5. **Backward Compatibility:** Existing two-stage workflow continues working without modifications (enhancement, not breaking change)

### Secondary Goals
6. **Constitutional Compliance:** Validate Articles I-V throughout (complete context, test coverage, automated enforcement, VectorStore learning, spec-driven)
7. **Configuration Management:** Store settings in `~/.agency/config.yml` (timeout_seconds: 30, default_action: approve, tier_display: progressive)
8. **VectorStore Integration:** Store approval patterns with tier metadata for learning (Article IV)

---

## II. Non-Goals (What We Will NOT Do)

1. **LLM-Based Summarization:** Tier generation is deterministic template-based parsing, not LLM inference (cost, latency, non-determinism)
2. **Interactive Editing:** Tier 1/2 are read-only views; editing requires [R]evise action (full Planner re-generation)
3. **Personalized Tiers:** Tier structure is fixed (not user-configurable layouts)
4. **Terminal Detection:** Assume ANSI color support (modern terminals universal, fallback to plain text acceptable)

---

## III. Personas (Who Uses This & Why)

### Primary Persona: Autonomous Development User
- **Role:** Developer using `/primeA --two-stage` for autonomous feature implementation
- **Goals:**
  - Approve specifications quickly when confident (30-second Tier 1 scan)
  - Review architectural decisions when uncertain (2-minute Tier 1+2)
  - Deep dive when spec quality concerns (full Tier 3 view)
- **Pain Points:**
  - Current approval checkpoint shows full spec (100+ lines) forcing slow review even for simple features
  - No auto-approve option for high-confidence low-risk tasks
  - Cannot quickly assess risk level without reading entire spec

### Secondary Persona: Quality-Conscious Developer
- **Role:** Developer reviewing complex/risky specifications
- **Goals:**
  - Quickly identify architectural decisions requiring scrutiny
  - Assess security implications before approval
  - Understand constitutional compliance status
- **Pain Points:**
  - Important decisions buried in long spec documents
  - No visual indicators for risk level or quality score
  - Cannot differentiate between low-risk (approve quickly) and high-risk (deep review)

---

## IV. Acceptance Criteria (Testable Success Measures)

### Functional Criteria

#### Tier 1: Executive Summary (<25 lines, 30-second read)
1. ✅ **Mission Statement:** One-sentence feature description
2. ✅ **Approach:** High-level strategy (architecture style, key technologies)
3. ✅ **Test Summary:** Test count + NECESSARY coverage status
4. ✅ **Deliverables:** File count (implementation, tests, docs)
5. ✅ **Constitutional Status:** Articles I-V compliance (✅/⚠️/🔴 indicators)
6. ✅ **Effort Estimate:** Hours estimate (implementation + testing + validation)
7. ✅ **Risk Level:** 🟢 Low / 🟡 Medium / 🔴 High (based on complexity, security, dependencies)

#### Tier 2: Key Decisions (<50 lines, 2-minute read)
1. ✅ **Architectural Choices:** 4-6 decisions with rationale and trade-offs
2. ✅ **Security Implications:** Auth, input validation, data handling concerns
3. ✅ **Dependencies:** New libraries, API integrations, infrastructure changes
4. ✅ **Performance Considerations:** Expected latency, memory, scalability

#### Tier 3: Full Spec (reference only, interactive view)
1. ✅ **File Path Display:** Show spec file location and line count
2. ✅ **Interactive View:** [V]iew action opens full spec in terminal pager (less/more)
3. ✅ **Search Capability:** User can search full spec during review

### UX Criteria
4. ✅ **Auto-Approve Countdown:** 30-second timer displays remaining seconds, updates every second
5. ✅ **Interrupt Capability:** Any keystroke (except whitespace) interrupts countdown and presents options
6. ✅ **Color Coding:** ✅ green (compliant), ⚠️ yellow (warnings), 🔴 red (blockers)
7. ✅ **Unicode Boxes:** Clean box drawing characters (─│┌┐└┘) for section separation
8. ✅ **Keyboard Shortcuts:** [A]pprove, [R]evise, [V]iew full spec, [Q]uit (with confirmation)

### Performance Criteria
9. ✅ **Generation Time:** Tier extraction <2 seconds (deterministic parsing, no LLM)
10. ✅ **Rendering Time:** UI display <500ms (template formatting)

### Configuration Criteria
11. ✅ **Timeout Configurable:** `~/.agency/config.yml: two_stage.checkpoint.timeout_seconds` (default 30)
12. ✅ **Default Action Configurable:** `two_stage.checkpoint.default_action: approve|prompt` (auto-approve on timeout vs. prompt again)
13. ✅ **Tier Display Configurable:** `two_stage.checkpoint.tier_display: progressive|full` (show tiers progressively vs. all at once)

### Backward Compatibility Criteria
14. ✅ **Existing Workflow Intact:** TwoStageOrchestrator works without changes if tiered review disabled
15. ✅ **Legacy Approval Format:** Fallback to current approval_checkpoint.py behavior if tier generation fails

### Constitutional Criteria (Articles I-V)
16. ✅ **Article I (Complete Context):** All tier data available before approval prompt (no partial loading)
17. ✅ **Article II (100% Verification):** All tests pass before PR creation (test gate enforced)
18. ✅ **Article III (Automated Enforcement):** Quality gates cannot be manually bypassed (auto-approve is timeout-based, not manual override)
19. ✅ **Article IV (Continuous Learning):** Approval patterns stored with tier metadata (which tier influenced decision)
20. ✅ **Article V (Spec-Driven):** Spec approval checkpoint remains (two-stage workflow preserved)

### Test Coverage Criteria
21. ✅ **NECESSARY Pattern:** 9 categories for tier generator (Normal, Edge, Cascading, Essential, Security, Spec, Accuracy, Regression, Yield)
22. ✅ **NECESSARY Pattern:** 5 categories for UI (Normal, Edge, Security, Spec, Resilience)
23. ✅ **100% Pass Rate:** All 14 tests pass before PR creation (Article II)

---

## V. Technical Specification

### Architecture

#### Component Diagram
```
TwoStageOrchestrator
    ├→ SpecGenerator (existing)
    │   └→ Spec (Pydantic model)
    │
    ├→ SpecTierGenerator (NEW)
    │   ├→ Input: Spec (from SpecGenerator)
    │   ├→ Output: TieredSpec (Pydantic model)
    │   └→ Logic: Deterministic template-based parsing (<2s)
    │
    ├→ CheckpointUI (NEW)
    │   ├→ Input: TieredSpec + Config
    │   ├→ Output: ApprovalDecision
    │   └→ Logic: Render tiers + countdown + keyboard input
    │
    └→ ApprovalCheckpoint (UPDATED)
        ├→ Integrates SpecTierGenerator
        ├→ Integrates CheckpointUI
        └→ Stores tier metadata to VectorStore
```

#### Data Flow
```
Spec (SpecGenerator)
    ↓
SpecTierGenerator.generate(spec: Spec) → Result[TieredSpec, Error]
    ↓
CheckpointUI.render(tiered_spec: TieredSpec, config: CheckpointConfig)
    ↓
    ├→ Auto-Approve Countdown (30s, configurable)
    ├→ User Interrupt → Show Options [A/R/V/Q]
    └→ Timeout → default_action (approve or prompt)
    ↓
ApprovalDecision(action, tier_viewed, response_time)
    ↓
VectorStore.store_memory(pattern with tier metadata)
```

### File Structure

#### Implementation Files (3)
1. **`tools/orchestrator/spec_tier_generator.py`** (NEW, ~300 lines)
   - Class: `SpecTierGenerator`
   - Method: `generate(spec: Spec) -> Result[TieredSpec, str]`
   - Logic: Template-based parsing of Goals/Personas/Success Criteria into tiers
   - Pydantic Models: `Tier1Summary`, `Tier2Summary`, `Tier3Reference`

2. **`tools/orchestrator/checkpoint_ui.py`** (NEW, ~250 lines)
   - Class: `CheckpointUI`
   - Method: `render(tiered_spec: TieredSpec, config: CheckpointConfig) -> Result[ApprovalDecision, str]`
   - Logic: Unicode box rendering, color coding, countdown timer, keyboard input
   - Pydantic Models: `CheckpointConfig`, `ApprovalDecision` (extended with tier metadata)

3. **`shared/models/two_stage_models.py`** (NEW, ~150 lines)
   - Pydantic Models:
     - `Tier1Summary` (mission, approach, test_summary, deliverables, constitutional_status, effort_estimate, risk_level)
     - `Tier2Summary` (architectural_choices, security_implications, dependencies, performance_considerations)
     - `Tier3Reference` (file_path, line_count, view_command)
     - `TieredSpec` (tier1, tier2, tier3, original_spec)
     - `CheckpointConfig` (timeout_seconds, default_action, tier_display)

#### Test Files (2)
4. **`tests/orchestrator/test_spec_tier_generator.py`** (NEW, ~400 lines, 9 tests)
   - `test_normal_tier_generation_success()` - Happy path: valid Spec → TieredSpec
   - `test_edge_minimal_spec()` - Minimal spec (1 goal, 1 persona, 1 criterion)
   - `test_cascading_missing_metadata()` - Missing metadata fields (graceful degradation)
   - `test_essential_parsing_speed()` - Generation time <2 seconds
   - `test_security_sanitization()` - XSS/injection in spec content (escape HTML/unicode)
   - `test_spec_compliance_articles()` - Constitutional status extraction (Articles I-V)
   - `test_accuracy_tier_content()` - Verify Tier 1/2 accurately reflect spec
   - `test_regression_backward_compat()` - Legacy Spec format still works
   - `test_yield_output_format()` - TieredSpec matches expected schema

5. **`tests/orchestrator/test_checkpoint_ui.py`** (NEW, ~300 lines, 5 tests)
   - `test_normal_auto_approve_timeout()` - Countdown expires, auto-approve triggered
   - `test_edge_interrupt_before_timeout()` - User presses key, countdown cancelled
   - `test_security_input_validation()` - Malicious input (SQL/command injection) rejected
   - `test_spec_keyboard_shortcuts()` - [A/R/V/Q] actions work correctly
   - `test_resilience_terminal_resize()` - Handle terminal resize during countdown (graceful)

#### Documentation Files (1)
6. **`docs/adr/ADR-034-tiered-spec-review.md`** (NEW, ~200 lines)
   - Context: Why tiered review solves approval bottleneck
   - Decision: Progressive disclosure + auto-approve with timeout
   - Rationale: UX improvement, no breaking changes, constitutional compliance
   - Alternatives Considered: LLM summarization (rejected: cost/latency), single-tier (rejected: no flexibility)
   - Consequences: Faster approvals, better UX, maintainable code

#### Configuration Files (1)
7. **`~/.agency/config.yml`** (UPDATED, add section)
   ```yaml
   two_stage:
     checkpoint:
       timeout_seconds: 30
       default_action: approve  # approve | prompt
       tier_display: progressive  # progressive | full
       enable_tiered_review: true  # Feature flag (rollout)
   ```

### Key Algorithms

#### Tier 1 Extraction (Deterministic Parsing)
```python
def extract_tier1(spec: Spec) -> Tier1Summary:
    """Extract executive summary from spec (deterministic, <2s)."""

    # Mission: First goal or title
    mission = spec.goals[0] if spec.goals else spec.title

    # Approach: Infer from goals/success_criteria keywords
    approach = infer_approach_from_keywords(spec.goals + spec.success_criteria)
    # Keywords: "REST API" → "API-driven", "React" → "Component-based", "TDD" → "Test-first"

    # Test Summary: Count from success_criteria (search for "test" keyword)
    test_count = sum(1 for c in spec.success_criteria if "test" in c.lower())
    necessary_coverage = "9/9" if test_count >= 9 else f"{test_count}/9"

    # Deliverables: Infer from goals (1 goal ≈ 1-2 files)
    impl_count = len(spec.goals)
    test_count_files = impl_count  # 1:1 ratio
    doc_count = 1  # Always ADR
    deliverables = f"{impl_count + test_count_files + doc_count} files"

    # Constitutional Status: Check success_criteria for Article references
    articles = extract_article_references(spec.success_criteria)
    status = "✅ Articles I-V" if len(articles) >= 5 else f"⚠️ {len(articles)}/5 articles"

    # Effort Estimate: Heuristic (1 goal = 1h impl, 0.5h test, 0.5h validation)
    effort_hours = len(spec.goals) * 2

    # Risk Level: Based on priority + complexity keywords
    risk = calculate_risk_level(spec.metadata.priority, spec.goals)

    return Tier1Summary(...)
```

#### Auto-Approve Countdown UI
```python
async def render_with_countdown(
    tiered_spec: TieredSpec,
    config: CheckpointConfig
) -> Result[ApprovalDecision, str]:
    """Render Tier 1 with countdown timer and interrupt capability."""

    # Display Tier 1
    print(format_tier1_box(tiered_spec.tier1))

    # Countdown loop
    remaining = config.timeout_seconds
    while remaining > 0:
        print(f"\r⏱️  Auto-approving in {remaining}s (press any key to review options)...", end="", flush=True)

        # Non-blocking keyboard check (select() with 1s timeout)
        if await check_keyboard_input(timeout=1.0):
            # User interrupted
            print("\n\n🛑 Countdown interrupted. Choose action:")
            return await prompt_approval_options(tiered_spec, config)

        remaining -= 1

    # Timeout reached, auto-approve
    print(f"\n\n✅ Auto-approved after {config.timeout_seconds}s timeout")
    return Ok(ApprovalDecision(action="approve", tier_viewed=1, response_time=config.timeout_seconds))
```

#### Keyboard Input Handling (Non-Blocking)
```python
import select
import sys

async def check_keyboard_input(timeout: float = 1.0) -> bool:
    """Non-blocking keyboard input check (Unix/Linux/macOS)."""
    # Use select() for non-blocking stdin check
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    return bool(rlist)

async def prompt_approval_options(
    tiered_spec: TieredSpec,
    config: CheckpointConfig
) -> Result[ApprovalDecision, str]:
    """Prompt user with approval options after countdown interrupt."""

    print(BOX_TOP)
    print("ACTION REQUIRED:")
    print("  [A] Approve  - Proceed with this specification")
    print("  [R] Revise   - Request re-generation (Planner agent)")
    print("  [V] View     - Show Tier 2 (key decisions) or Tier 3 (full spec)")
    print("  [Q] Quit     - Cancel orchestration")
    print(BOX_BOTTOM)

    choice = await get_user_input("Enter choice [A/R/V/Q]: ")

    if choice.upper() == "A":
        return Ok(ApprovalDecision(action="approve", tier_viewed=1))
    elif choice.upper() == "R":
        return Ok(ApprovalDecision(action="reject", tier_viewed=1))
    elif choice.upper() == "V":
        return await handle_view_action(tiered_spec, config)
    elif choice.upper() == "Q":
        return Err("User cancelled orchestration")
    else:
        print(f"❌ Invalid choice: {choice}")
        return await prompt_approval_options(tiered_spec, config)  # Retry
```

### Integration Points

#### TwoStageOrchestrator Integration
```python
# In tools/orchestrator/two_stage_orchestrator.py

async def _await_approval(self, spec: Spec) -> Result[ApprovedSpec, OrchestrationError]:
    """
    Await user approval with tiered review (if enabled).

    Workflow:
    1. Generate tiered spec from Spec model
    2. Render Tier 1 with auto-approve countdown
    3. If interrupted, prompt for [A/R/V/Q]
    4. Store approval pattern with tier metadata
    """
    # Check if tiered review enabled
    config = self._load_checkpoint_config()

    if config.enable_tiered_review:
        # NEW: Tiered review workflow
        tier_generator = SpecTierGenerator()
        tier_result = tier_generator.generate(spec)

        if tier_result.is_err():
            # Fallback to legacy approval
            logger.warning(f"Tier generation failed: {tier_result.unwrap_err()}, using legacy approval")
            return await self.approval_checkpoint.await_approval(spec)

        tiered_spec = tier_result.unwrap()

        # Render with countdown UI
        ui = CheckpointUI(config=config)
        decision_result = await ui.render(tiered_spec)

        if decision_result.is_err():
            return Err(OrchestrationError(stage="spec_approval", reason=decision_result.unwrap_err()))

        decision = decision_result.unwrap()

        # Store approval pattern with tier metadata
        self._store_tiered_approval_pattern(spec, decision, tiered_spec)

        # Convert to ApprovedSpec format
        approved = ApprovedSpec(
            spec=spec,
            decision=decision,
            edit_count=0  # TODO: Track edit iterations
        )

        return Ok(approved)

    else:
        # LEGACY: Original approval workflow
        return await self.approval_checkpoint.await_approval(spec)
```

### Error Handling

#### Failure Scenarios & Recovery
1. **Tier Generation Failure:** Fallback to legacy approval_checkpoint.py (backward compatible)
2. **Terminal Size Too Small:** Display warning, use compact layout (minimum 80x24)
3. **Countdown Interrupt Error:** Retry prompt_approval_options() once, then fallback to legacy
4. **Config File Missing:** Use default values (timeout=30s, default_action=approve)
5. **VectorStore Storage Failure:** Log warning, continue (non-blocking)

### Security Considerations

#### Input Validation
1. **XSS in Spec Content:** Escape HTML entities in tier rendering (use `html.escape()`)
2. **Command Injection in View Action:** Validate file paths, use subprocess with shell=False
3. **Terminal Escape Sequences:** Sanitize spec content (strip ANSI codes except our own)

#### Timeout Abuse Prevention
1. **Minimum Timeout:** Enforce 10-second minimum (prevent instant auto-approve abuse)
2. **Maximum Timeout:** Enforce 300-second maximum (prevent indefinite hangs)
3. **Audit Trail:** Log all auto-approvals with timeout duration to telemetry

---

## VI. Implementation Plan

### Phase 1: Data Models & Tier Generator (2 hours)
**Tasks:**
1. Create `shared/models/two_stage_models.py` with Pydantic models (Tier1Summary, Tier2Summary, Tier3Reference, TieredSpec, CheckpointConfig)
2. Implement `tools/orchestrator/spec_tier_generator.py` with deterministic parsing logic
3. Write 9 NECESSARY tests in `tests/orchestrator/test_spec_tier_generator.py`
4. Validate: All tests pass (pytest -xvs tests/orchestrator/test_spec_tier_generator.py)

### Phase 2: Checkpoint UI & Countdown (2 hours)
**Tasks:**
1. Implement `tools/orchestrator/checkpoint_ui.py` with Unicode boxes, color coding, countdown
2. Write 5 NECESSARY tests in `tests/orchestrator/test_checkpoint_ui.py`
3. Validate: All tests pass (pytest -xvs tests/orchestrator/test_checkpoint_ui.py)

### Phase 3: Integration & Configuration (1 hour)
**Tasks:**
1. Update `tools/orchestrator/two_stage_orchestrator.py` to integrate tiered review (feature flag)
2. Create `~/.agency/config.yml` template with default settings
3. Add config loading logic to TwoStageOrchestrator
4. Validate: Integration test with TwoStageOrchestrator.orchestrate() end-to-end

### Phase 4: Documentation & ADR (1 hour)
**Tasks:**
1. Write `docs/adr/ADR-034-tiered-spec-review.md`
2. Update `tools/orchestrator/CLAUDE.md` with tiered review documentation
3. Update this spec with any implementation learnings

### Phase 5: Validation & PR (1-2 hours)
**Tasks:**
1. Run full test suite: `python run_tests.py --run-all` (100% pass rate required)
2. Run constitutional compliance check: `python tools/constitutional_intelligence/constitution_check.py`
3. Create PR with git worktree isolation
4. Store success pattern in VectorStore (Article IV)

---

## VII. Risks & Mitigations

### Risk 1: Terminal Compatibility Issues (🟡 Medium)
**Risk:** Unicode boxes or ANSI colors may not render correctly on all terminals (Windows CMD, older terminals)

**Mitigation:**
- Detect terminal capabilities (check TERM environment variable)
- Fallback to ASCII boxes (+-|) if Unicode unsupported
- Fallback to plain text if colors unsupported
- Test on: macOS Terminal, iTerm2, Windows Terminal, WSL2

### Risk 2: Countdown Interruption Race Condition (🟡 Medium)
**Risk:** Keyboard input may not be detected immediately (select() polling interval 1 second)

**Mitigation:**
- Use 100ms polling interval (not 1 second) for responsive interrupt
- Display "Press any key" prominently above countdown
- Test with manual keyboard mashing during countdown

### Risk 3: False Auto-Approvals (🔴 High if mishandled)
**Risk:** Auto-approve timeout may approve low-quality specs user intended to review

**Mitigation:**
- Display Tier 1 BEFORE countdown starts (user has 30s to scan + decide)
- Require explicit interrupt action (not accidental keypress)
- Log all auto-approvals to audit trail with timestamp
- Make timeout configurable (power users can increase to 60s)

### Risk 4: Tier Generation Accuracy (🟡 Medium)
**Risk:** Deterministic parsing may misclassify approach or risk level

**Mitigation:**
- Use conservative heuristics (default to 🟡 Medium risk, not 🟢 Low)
- Display "Inferred from spec" disclaimer on Tier 1
- Allow [V]iew action to see full spec if user uncertain
- Store tier accuracy feedback to VectorStore for future improvement (Article IV)

---

## VIII. Success Metrics

### Functional Metrics (Article II: 100% Verification)
1. ✅ **Test Pass Rate:** 14/14 tests pass (100%) before PR creation
2. ✅ **Generation Speed:** Tier generation <2 seconds (average across 100 specs)
3. ✅ **Rendering Speed:** UI display <500ms (average across 100 renders)

### UX Metrics
4. ✅ **Auto-Approve Usage:** >50% of approvals use auto-approve timeout (indicates UX success)
5. ✅ **Tier 2 View Rate:** <30% of approvals view Tier 2 (indicates Tier 1 sufficiency)
6. ✅ **Tier 3 View Rate:** <10% of approvals view full spec (indicates Tier 1+2 sufficiency)
7. ✅ **Approval Time Reduction:** Median approval time <30 seconds (vs. current ~2 minutes)

### Quality Metrics (Article III: Automated Enforcement)
8. ✅ **False Approval Rate:** <5% of auto-approved specs later rejected during implementation (measure via edit_count in subsequent iterations)
9. ✅ **Constitutional Compliance:** 100% of approved specs satisfy Articles I-V (no violations)

### Learning Metrics (Article IV: Continuous Learning)
10. ✅ **Pattern Storage:** 100% of approvals stored to VectorStore with tier metadata
11. ✅ **Pattern Application:** Future tier generators query VectorStore for accuracy improvements (confidence ≥ 0.6)

---

## IX. Rollout Plan

### Phase 1: Feature Flag (Default Disabled)
- Deploy with `enable_tiered_review: false` in config
- Manual testing by @am on 5-10 specs
- Collect feedback on tier accuracy, UX, performance

### Phase 2: Opt-In Beta (Week 1-2)
- Enable for @am's sessions only (`ENABLE_TIERED_REVIEW=true` env var)
- Monitor metrics: auto-approve rate, tier view rates, false approvals
- Iterate on tier generation heuristics based on feedback

### Phase 3: Default Enabled (Week 3+)
- Set `enable_tiered_review: true` as default in config
- Legacy approval remains available via feature flag (backward compatibility)
- Monitor long-term metrics: approval time reduction, quality metrics

---

## X. Alternatives Considered

### Alternative 1: LLM-Based Tier Summarization
**Description:** Use LLM (GPT-5-mini) to generate Tier 1/2 summaries from full spec

**Pros:**
- More accurate summaries (natural language understanding)
- Adaptive to spec format variations

**Cons:**
- 🔴 **Cost:** $0.002 per summarization (at scale: $200/month for 100K specs)
- 🔴 **Latency:** 2-5 seconds per call (vs. <2s deterministic parsing)
- 🔴 **Non-Deterministic:** Summaries vary across runs (testing complexity)
- 🔴 **Dependency:** Requires LLM API availability (failure mode)

**Decision:** REJECTED - Cost, latency, and non-determinism outweigh accuracy benefits. Deterministic parsing with heuristics is "good enough" for v1.

### Alternative 2: Single-Tier Approval (No Progressive Disclosure)
**Description:** Show full spec with auto-approve timeout (no Tier 1/2 extraction)

**Pros:**
- Simpler implementation (no tier generator)
- No risk of inaccurate tier extraction

**Cons:**
- 🔴 **UX:** User still forced to scan 100+ line specs to make 30-second decision
- 🔴 **Cognitive Load:** No quick risk assessment (must read everything)

**Decision:** REJECTED - Defeats purpose of UX improvement. Progressive disclosure is core value proposition.

### Alternative 3: No Auto-Approve Timeout
**Description:** Tiered review without auto-approve (always prompt user)

**Pros:**
- Safer (no risk of false auto-approvals)
- Simpler implementation (no countdown logic)

**Cons:**
- 🔴 **Manual Bottleneck:** User must always click [A] (defeats automation)
- 🔴 **Slow Iteration:** Autonomous loop still blocked on manual approval

**Decision:** REJECTED - Auto-approve timeout is essential for rapid iteration. Risk mitigated by displaying Tier 1 before countdown.

---

## XI. Open Questions & Future Work

### Open Questions (Resolve Before Implementation)
1. **Q:** Should auto-approve timeout reset on scroll/mouse movement (not just keypress)?
   **A:** No - too complex, keypress interrupt is sufficient. Mouse events unreliable in terminal.

2. **Q:** Should Tier 2 show inline (expand below Tier 1) or separate screen?
   **A:** Separate screen - cleaner UX, avoids scroll confusion. User presses [V] to toggle.

3. **Q:** Should configuration support per-user overrides (not just global ~/.agency/config.yml)?
   **A:** Not v1 - global config sufficient. Add user overrides in v2 if requested.

### Future Enhancements (v2+)
1. **VectorStore Accuracy Feedback:** Track which tier influenced approval decision, use for ML-based tier generation (Leap 8?)
2. **Custom Tier Templates:** Allow users to define custom Tier 1/2 sections via config (power user feature)
3. **Voice Control Integration:** "Approve spec" voice command triggers auto-approve (accessibility)
4. **Slack/Discord Notifications:** Send Tier 1 to Slack for async team approvals (team workflow)

---

## XII. References

### Constitutional Articles
- **Article I:** Complete Context Before Action (ADR-001) - All tier data available before prompt
- **Article II:** 100% Verification and Stability (ADR-002) - 14 tests pass before PR
- **Article III:** Automated Merge Enforcement (ADR-003) - Quality gates enforced
- **Article IV:** Continuous Learning (ADR-004) - Approval patterns stored with tier metadata
- **Article V:** Spec-Driven Development (ADR-007) - Spec approval checkpoint preserved

### Related ADRs
- **ADR-027:** Two-Stage TDD Orchestration - Base two-stage workflow architecture
- **ADR-032:** Autonomous Completion Protocol - Completion validation patterns
- **ADR-026:** Test-Driven Autonomy (Leap 7) - TDD workflow enforcement

### Related Specs
- **spec-011-two-stage-orchestration.md** - Original two-stage workflow specification
- **spec-027-tdd-graph-generation.md** - TDD task graph design

### Tools & Libraries
- **Pydantic:** Data models with validation (Tier1Summary, Tier2Summary, etc.)
- **asyncio:** Non-blocking countdown and keyboard input
- **select:** Unix keyboard polling (non-blocking stdin check)
- **colorama** (optional): Cross-platform ANSI color support (fallback if needed)

---

## XIII. Appendix: Example Tier 1 Display

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 📋 SPECIFICATION: JWT Authentication Middleware                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 🎯 MISSION:                                                                  │
│    Implement JWT-based authentication for API endpoints with RSA-256        │
│    signing, token refresh, and role-based access control                    │
│                                                                              │
│ 🏗️  APPROACH:                                                                 │
│    Middleware-based architecture with FastAPI dependency injection          │
│                                                                              │
│ 🧪 TEST SUMMARY:                                                             │
│    47 tests (NECESSARY coverage: 9/9) - 100% pass rate required            │
│                                                                              │
│ 📦 DELIVERABLES:                                                             │
│    7 files (3 implementation, 2 test, 1 ADR, 1 config)                      │
│                                                                              │
│ ⚖️  CONSTITUTIONAL STATUS:                                                    │
│    ✅ Articles I-V satisfied (complete context, tests, enforcement, learning) │
│                                                                              │
│ ⏱️  EFFORT ESTIMATE:                                                          │
│    6-8 hours (4h implementation, 2h testing, 1-2h validation/PR)            │
│                                                                              │
│ 🎚️  RISK LEVEL:                                                              │
│    🟡 Medium (security implications, authentication critical path)          │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ ⏱️  Auto-approving in 30s (press any key to review options)...              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

**END OF SPECIFICATION**

**Next Steps (Two-Stage Workflow):**
1. ✅ **Stage 1 Complete:** Specification generated (this document)
2. ⏸️ **Approval Checkpoint:** Awaiting user approval/rejection/revision
3. ⏳ **Stage 2 Pending:** TDD execution (tests first, then implementation)
4. ⏳ **Validation Pending:** 100% test pass rate validation
5. ⏳ **PR Creation Pending:** Autonomous PR with constitutional compliance

**Approval Actions:**
- **[A]pprove:** Proceed to Stage 2 (TDD implementation)
- **[R]evise:** Request specification re-generation with improvements
- **[Q]uit:** Cancel orchestration
