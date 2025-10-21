# Specification: Gemini Computer Use with Browser Tab Isolation

**ID**: SPEC-20251015-034-gemini-browser-isolation
**Status**: Draft
**Created**: 2025-10-15
**Updated**: 2025-10-15
**Owner**: SpecGenerator Agent
**Related**: ADR-008 (Strict Typing), ADR-010 (Result Pattern), ADR-023 (Memory-Aware Execution)

---

## Executive Summary

This specification defines a **defensive security-first** integration of Gemini's computer use capabilities with strict browser tab isolation using Brave browser. The system enables AI-assisted web automation while enforcing zero-trust principles: tab-level sandboxing, explicit user consent, comprehensive audit trails, and no access beyond browser boundaries.

**Critical Constraint**: This is a **defensive security tool only**. No credential harvesting, no malicious automation, explicit consent UI for user trust. Follows principle of least privilege and constitutional security policy.

---

## Goals

### Primary Objectives

**What We're Building**:
- **Goal 1**: Safe Gemini computer use integration with tab-level browser isolation (Brave only)
- **Goal 2**: Explicit user consent workflow for every computer use action category (mouse/keyboard/screenshot)
- **Goal 3**: HMAC-signed audit trail for all actions (tamper detection, forensic analysis)
- **Goal 4**: Rate limiting and resource constraints (max 10 actions/min, 100 actions/session, 30-minute timeout)
- **Goal 5**: Zero access outside browser sandbox (no filesystem, clipboard, other tabs, system-wide actions)

### Success Metrics

- **Security Isolation**: 100% of actions confined to single browser tab (verified by automated tests)
- **User Consent**: 100% of action categories require explicit opt-in (no assumed permissions)
- **Audit Completeness**: 100% of actions logged with HMAC-SHA256 signatures (tamper detection works)
- **Rate Limit Enforcement**: 0 violations (all limit exceeded attempts blocked with clear errors)
- **Graceful Degradation**: 100% of error scenarios handled without crashes (Brave not installed, network timeout, etc.)

---

## Non-Goals

**Explicitly out of scope for this specification**:

- **Non-Goal 1**: System-wide computer use (clipboard, file system, other applications) - Deferred indefinitely (security risk)
  - **Rationale**: Violates principle of least privilege, excessive attack surface
- **Non-Goal 2**: Multi-tab or multi-window automation - Deferred to future iteration after single-tab proven safe
  - **Rationale**: Increased complexity, cross-tab data leakage risks
- **Non-Goal 3**: Browser plugins or extensions in isolated session - Rejected (security vulnerability)
  - **Rationale**: Extensions can bypass tab isolation, steal credentials
- **Non-Goal 4**: Credential storage or password autofill - Rejected permanently (malicious automation risk)
  - **Rationale**: Constitutional security policy forbids credential harvesting

**Why These Are Non-Goals**:
This specification prioritizes **defensive security** over feature completeness. Each non-goal was evaluated against the constitutional security policy and principle of least privilege. Only browser tab automation is in scope because it provides value (web research, form filling) while maintaining strong isolation boundaries.

---

## Personas

### Persona 1: Research Agent (Primary User)

- **Context**: AI agent performing web research for technical specifications, documentation scraping, competitor analysis
- **Need**: Automate browser interactions without manual clicking (save time, improve accuracy)
- **Current Pain Point**: Manual web scraping is slow, error-prone; existing tools lack safety guarantees
- **Desired Outcome**: Trusted, auditable browser automation with clear isolation boundaries
- **Interaction Pattern**: Invoke `GeminiComputerUse.execute_action()` with screenshot, action description; review audit logs after session

### Persona 2: Development Engineer (System Operator)

- **Context**: Developer integrating Gemini computer use into autonomous workflows (e.g., `/primeA` research phase)
- **Need**: Safe, sandboxed browser automation library with defensive security built-in
- **Current Pain Point**: Existing browser automation tools (Selenium, Playwright) lack AI integration and safety-first design
- **Desired Outcome**: Drop-in library with Pydantic models, Result pattern, HMAC audit trails (constitutional compliance)
- **Interaction Pattern**: Import `GeminiComputerUse`, configure rate limits, handle `Result<T, E>` errors, review audit trail files

### Persona 3: Security Auditor (Compliance Reviewer)

- **Context**: Reviewing autonomous systems for security vulnerabilities, constitutional compliance
- **Need**: Verifiable isolation guarantees, tamper-proof audit trails, explicit consent workflows
- **Current Pain Point**: Black-box AI systems lack transparency, audit trails are easily tampered
- **Desired Outcome**: HMAC-signed audit logs, test coverage proving isolation (no filesystem access, no cross-tab leakage)
- **Interaction Pattern**: Run security test suite (NECESSARY pattern), verify HMAC signatures, audit consent UI flow

---

## Acceptance Criteria

### Functional Criteria (MUST HAVE)

- [ ] **FC-01**: Brave browser launches in isolated profile with unique session ID
  - **Given**: User invokes `GeminiComputerUse.initialize()`
  - **When**: Playwright launches Brave with `--user-data-dir=/tmp/agency-gemini-{session_id}`
  - **Then**: Browser starts with no extensions, empty cache, isolated profile (verified by checking profile directory)

- [ ] **FC-02**: Computer use actions limited to single active tab only
  - **Given**: Browser session active with tab A focused
  - **When**: Action executed (mouse click, keyboard input, screenshot)
  - **Then**: Action applies ONLY to tab A (no cross-tab effects verified by tests)

- [ ] **FC-03**: All actions logged to HMAC-signed audit trail
  - **Given**: Action completed (success or failure)
  - **When**: Audit entry created with timestamp, action type, parameters, result
  - **Then**: Entry signed with HMAC-SHA256 using `GEMINI_AUDIT_HMAC_KEY` (signature verification passes)

- [ ] **FC-04**: User consent prompt before each computer use action category
  - **Given**: First mouse/keyboard/screenshot action in session
  - **When**: Action requested via `execute_action()`
  - **Then**: Console prompt displays: "Allow [category]? (y/N)" (no execution until consent granted)

- [ ] **FC-05**: Rate limiting enforces 10 actions/minute, 100 actions/session
  - **Given**: 10 actions executed within 60 seconds
  - **When**: 11th action requested within same 60-second window
  - **Then**: `Result::Err(RateLimitExceeded)` returned (no execution, clear error message)

- [ ] **FC-06**: Automatic session termination after 30 minutes or user command
  - **Given**: Session started at T=0
  - **When**: T=30 minutes (or user calls `terminate()`)
  - **Then**: Browser process killed, profile directory deleted, audit trail finalized

- [ ] **FC-07**: Zero access to filesystem outside browser sandbox
  - **Given**: Browser session active
  - **When**: Attempt to read/write files via Gemini action
  - **Then**: Playwright sandbox blocks filesystem access (verified by tests attempting file operations)

- [ ] **FC-08**: Zero access to other browser tabs or windows
  - **Given**: Multiple tabs open (tab A active, tab B background)
  - **When**: Action executed in tab A context
  - **Then**: Tab B state unchanged (verified by screenshot comparison before/after)

- [ ] **FC-09**: Clear visual indicator when computer use active
  - **Given**: Computer use session initialized
  - **When**: Actions being executed
  - **Then**: Browser displays banner: "⚠️ AI Automation Active - Session {session_id}" (injected via JavaScript)

- [ ] **FC-10**: Graceful degradation if Brave not installed
  - **Given**: Brave browser not in PATH
  - **When**: `GeminiComputerUse.initialize()` called
  - **Then**: `Result::Err(BraveNotInstalled)` with error message: "Install Brave browser (brew install brave-browser)" (no fallback to Chrome/Firefox)

### Non-Functional Criteria (MUST HAVE)

- [ ] **NF-01**: Performance - Screenshot capture <500ms p95 (tab-level screenshot via Playwright)
- [ ] **NF-02**: Performance - Action execution latency <2 seconds p95 (Gemini API call + browser interaction)
- [ ] **NF-03**: Reliability - Session cleanup 100% success rate (no orphaned browser processes or temp directories)
- [ ] **NF-04**: Security - All audit entries signed with HMAC-SHA256 (tamper detection via signature verification)
- [ ] **NF-05**: Type Safety - 100% Pydantic model coverage (no `Dict[Any, Any]`, strict typing via ADR-008)
- [ ] **NF-06**: Scalability - Handles 100 actions/session without memory leaks (verified by memory profiling)

### Quality Criteria (Constitutional Compliance - MUST HAVE)

- [ ] **QC-01**: Test Coverage >95% (Article II) - All critical paths tested
- [ ] **QC-02**: All 5 constitutional articles enforced:
  - **Article I**: Complete context (full audit trail, no partial execution)
  - **Article II**: 100% test pass rate (NECESSARY pattern validation)
  - **Article III**: Automated enforcement (rate limits, consent, no manual override)
  - **Article IV**: VectorStore learning (successful isolation patterns stored)
  - **Article V**: Spec-driven (traceable to this specification)
- [ ] **QC-03**: Documentation - Public APIs documented with Result pattern examples
- [ ] **QC-04**: Code Quality - Zero linting errors, functions <50 lines (Law #8)
- [ ] **QC-05**: TDD - Tests written BEFORE implementation (Law #1)

### User Experience Criteria

- [ ] **UX-01**: Error messages actionable ("Rate limit exceeded. Wait 45s or use --force flag")
- [ ] **UX-02**: Consent prompts clear ("Allow screenshot capture? (y/N) - Required for AI vision")
- [ ] **UX-03**: Audit trail human-readable (JSON Lines with timestamps, action summaries)

---

## Functional Requirements

### FR-01: Browser Session Management

**Description**: Isolated Brave browser session with unique profile per execution
**Priority**: Critical
**Complexity**: Medium

**Details**:
- Behavior 1: Launch Brave via Playwright with `--user-data-dir=/tmp/agency-gemini-{session_id}`
- Behavior 2: Disable extensions (`--disable-extensions`), plugins (`--disable-plugins`)
- Behavior 3: Inject visual banner via JavaScript: `document.body.prepend("<div>⚠️ AI Automation Active</div>")`
- Constraint: Session ID must be unique (UUID4), profile directory deleted on cleanup

**Test Strategy**:
- Normal: Launch browser, verify profile directory exists, visual banner present
- Edge: Concurrent sessions with different IDs (no profile collision)
- Security: Attempt to access other profiles (isolation verified)
- Resilience: Brave crash mid-session triggers cleanup (no orphaned processes)

### FR-02: Computer Use Action Execution

**Description**: Execute Gemini-generated actions using official Computer Use API within tab boundaries
**Priority**: Critical
**Complexity**: High

**Details**:
- Behavior 1: Call Gemini API with `gemini-2.5-computer-use-preview-10-2025` model
- Behavior 2: Parse function calls from response (official action types: click_at, type_text_at, navigate, etc.)
- Behavior 3: Convert normalized coordinates (0-999 grid) to actual pixel coordinates for 1440x900 viewport
- Behavior 4: Execute via Playwright page context with safety confirmation for high-risk actions
- Behavior 5: Capture screenshot after each action for next iteration
- Constraint: All actions scoped to `page` object (single tab context), leverage built-in Gemini safety system

**Test Strategy**:
- Normal: Send screenshot to Gemini → receive click_at action → execute → verify success
- Normal: Navigate action changes page URL within same tab
- Edge: Gemini returns unsupported action → Pydantic validation fails gracefully
- Security: High-risk action (e.g., navigate to external domain) → user confirmation prompt
- Security: Attempt to access `browser.contexts()` (multiple tabs) → blocked
- Spec: Normalized coordinate conversion accurate (999 → 1440px width, 900px height)

### FR-03: User Consent Workflow

**Description**: Explicit opt-in for high-risk actions (leverages Gemini's built-in safety decision system)
**Priority**: Critical
**Complexity**: Medium

**Details**:
- Behavior 1: Leverage Gemini's built-in safety decision system for high-risk actions
- Behavior 2: Add custom safety instructions to Gemini API calls (e.g., "Never navigate to external domains")
- Behavior 3: Track consent per action category in `ConsentTracker` (Pydantic model)
- Behavior 4: Prompt user for high-risk actions (navigate, key_combination): `input("Allow [action]? (y/N): ")`
- Behavior 5: Cache consent for session (no re-prompt for same low-risk category)
- Constraint: Case-insensitive "y" or "yes" grants consent, all else denies

**Test Strategy**:
- Normal: Low-risk action (click_at, scroll_document) → executes without prompt
- Normal: High-risk action (navigate to external URL) → user confirmation required
- Normal: User grants consent → action executes
- Normal: User denies consent → `Result::Err(ConsentDenied)`
- Edge: Empty input (press Enter) → defaults to deny
- Security: Custom safety instructions prevent credential harvesting prompts
- Security: Gemini safety system blocks inherently dangerous actions

### FR-04: Rate Limiting and Resource Constraints

**Description**: Enforce action limits to prevent abuse and runaway execution
**Priority**: High
**Complexity**: Medium

**Details**:
- Behavior 1: Track actions per minute via sliding window (deque of timestamps)
- Behavior 2: Reject action if window contains ≥10 timestamps (rate limit)
- Behavior 3: Reject session if total actions ≥100 (session limit)
- Behavior 4: Auto-terminate session after 30 minutes (time limit)
- Constraint: Limits configurable via environment variables (`GEMINI_RATE_LIMIT_ACTIONS_PER_MIN`, `GEMINI_MAX_ACTIONS_PER_SESSION`)

**Test Strategy**:
- Normal: 9 actions/min → all succeed
- Edge: 10th action within 60s → rate limit error
- Edge: 100th action in session → session limit error
- Resilience: Session timeout at 30 min → auto-cleanup

### FR-05: HMAC-Signed Audit Trail

**Description**: Tamper-proof logging of all actions with cryptographic signatures
**Priority**: High
**Complexity**: Low

**Details**:
- Behavior 1: Append each action to JSONL file (`~/.agency/audit/gemini_computer_use/{session_id}.jsonl`)
- Behavior 2: Sign entry with HMAC-SHA256 using `GEMINI_AUDIT_HMAC_KEY` secret
- Behavior 3: Include: timestamp, session_id, action_type, parameters, result, duration_ms, signature
- Constraint: Append-only (no edits to audit trail), signature verifiable by external tools

**Test Strategy**:
- Normal: Action executed → audit entry created with valid signature
- Security: Tamper with entry → signature verification fails
- Resilience: Disk full during append → error logged, graceful degradation

---

## Non-Functional Requirements

### NFR-01: Performance

- **Target**: Screenshot capture <500ms p95, action execution <2s p95
- **Measurement**: Timer wrapper around Playwright calls, percentile calculation in tests
- **Acceptance**: 95% of actions meet latency targets (logged to telemetry)

### NFR-02: Security

- **Authentication**: No authentication (defensive tool, no user accounts)
- **Authorization**: User consent per action category (explicit opt-in)
- **Data Protection**: Audit trail encrypted at rest (OS-level encryption), HMAC-signed for integrity

### NFR-03: Type Safety (Constitutional Law #2)

- **Strict Typing**: No `Any` or `Dict[Any, Any]` (Pydantic models for all data structures)
- **Pydantic Models**: `BrowserSession`, `ComputerUseAction`, `AuditEntry`, `ConsentTracker`, `RateLimiter`
- **Validation**: Runtime validation via Pydantic, compile-time via mypy strict mode

### NFR-04: Error Handling (Constitutional Law #5)

- **Result Pattern**: All operations return `Result<T, E>` (no exceptions for control flow)
- **Typed Errors**: `BraveNotInstalled`, `ConsentDenied`, `RateLimitExceeded`, `TabIsolationViolation`, `AuditSigningFailed`
- **Error Messages**: Actionable guidance ("Install Brave: brew install brave-browser")

---

## Dependencies

### Internal Dependencies

- **SPEC-006**: Slop Immunity Protocol (audit trail patterns, HMAC signing)
- **ADR-008**: Strict Typing (Pydantic model enforcement)
- **ADR-010**: Result Pattern (error handling standard)
- **tools/orchestrator/audit_signing.py**: HMAC signature utilities (reuse existing patterns)
- **shared/type_definitions/result.py**: Result<T, E> implementation

### External Dependencies

- **Library**: `playwright>=1.40.0` - Browser automation with Chromium support (Brave is Chromium-based)
- **Library**: `google-generativeai>=0.3.0` - Gemini API integration
- **Library**: `pydantic>=2.0.0` - Data validation and type enforcement
- **Service**: Gemini Computer Use API (`gemini-2.5-computer-use-preview-10-2025` model)
- **Service**: Gemini API key (requires `GEMINI_API_KEY` environment variable from Google AI Studio)
- **Infrastructure**: Brave browser installed (`brew install brave-browser` on macOS)
- **Configuration**: Recommended screen size 1440x900 for optimal coordinate system accuracy

### Dependency Impact Analysis

- **Breaking Changes**: None (new feature, no existing Gemini computer use integration)
- **Integration Points**:
  - Playwright session management (isolated profiles, tab context)
  - Gemini API action parsing (JSON schema validation)
  - Audit trail system (JSONL append, HMAC signing)
- **Migration Path**: N/A (greenfield implementation)

---

## Risks and Mitigations

| ID   | Risk                                  | Impact | Probability | Mitigation Strategy                                                     | Owner              |
| ---- | ------------------------------------- | ------ | ----------- | ----------------------------------------------------------------------- | ------------------ |
| R-01 | Gemini generates malicious actions    | High   | Medium      | Action whitelist (only mouse/keyboard/screenshot), consent per category | QualityEnforcer    |
| R-02 | Tab isolation bypassed via JS exploit | High   | Low         | Playwright sandbox enforcement, security test suite (NECESSARY pattern) | SecurityAuditor    |
| R-03 | Rate limit bypass via concurrency     | Medium | Medium      | Thread-safe rate limiter (mutex/lock), atomic counter                  | CodeAgent          |
| R-04 | Audit trail tampering                 | Medium | Low         | HMAC-SHA256 signatures, signature verification in tests                | ConstitutionalGate |
| R-05 | Brave browser unavailable             | Low    | High        | Clear error message, graceful degradation (no fallback browser)        | ErrorHandler       |

### Risk Mitigation Plan

**High-Risk Items (R-01, R-02)**:
- **Detailed Mitigation (R-01)**:
  - Action whitelist enforced in `ComputerUseAction` Pydantic validator
  - Unsupported actions (filesystem, clipboard) raise `ValueError` before execution
  - User consent required for all supported categories (mouse, keyboard, screenshot)
- **Detailed Mitigation (R-02)**:
  - Playwright context isolation (`browser.new_context()` per session)
  - JavaScript execution scoped to page (`page.evaluate()` not `browser.evaluate()`)
  - Security test: Attempt to access `window.localStorage` of other tabs → blocked
- **Contingency Plan**: If isolation violated in production, kill session immediately, escalate to security audit
- **Early Warning Indicators**: Audit trail shows cross-tab actions, test failures in isolation suite

---

## Edge Cases and Error Scenarios

### Edge Case 1: Action at Exact Rate Limit Boundary

- **Scenario**: 10th action requested at T=59.9s (within 60s window)
- **Expected Behavior**: Action succeeds (window size ≥60s), 11th action at T=60.1s fails
- **Test Case**: Sleep-based timing test with sliding window verification

### Edge Case 2: Session Timeout Mid-Action

- **Scenario**: Action started at T=29:58, timeout at T=30:00
- **Expected Behavior**: Action completes (grace period), next action rejected with `SessionExpired` error
- **Test Case**: Mock timer, verify cleanup triggered after 30 min

### Error Scenario 1: Invalid Action JSON from Gemini

- **Trigger**: Gemini API returns malformed JSON (`{"action": "clck", "target": "button"}` - typo)
- **Error Response**: `Result::Err(InvalidAction)` with Pydantic validation error details
- **User Experience**: Error message: "Invalid action from Gemini API: 'clck' is not a valid action type. Expected: click, type, screenshot"
- **Recovery**: Log error to audit trail, skip action, continue session

### Error Scenario 2: Browser Process Crash

- **Trigger**: Playwright browser process killed externally (OOM, manual `kill -9`)
- **Fallback**: Session cleanup triggered by process monitor (polling or signal handler)
- **Monitoring**: Audit trail logs `browser_crash` event with exit code
- **Recovery**: Raise `Result::Err(BrowserCrashed)`, delete orphaned profile directory

### Error Scenario 3: Network Timeout During Gemini API Call

- **Trigger**: Gemini API request exceeds 10s timeout
- **Fallback**: Retry with exponential backoff (2x, 4x, 8s) per Article I
- **Monitoring**: Log retry attempts to telemetry
- **Recovery**: After 3 retries, raise `Result::Err(GeminiAPITimeout)` with actionable message

---

## Performance Requirements

### Latency Targets

- **P50**: Screenshot capture <200ms, action execution <1s
- **P95**: Screenshot capture <500ms, action execution <2s
- **P99**: Screenshot capture <1s, action execution <5s

### Throughput Targets

- **Requests/Second**: N/A (rate limited to 10 actions/min)
- **Concurrent Sessions**: 1 session per system (isolated profile prevents concurrency)

### Resource Constraints

- **Memory**: <500MB per session (Playwright + Brave browser overhead)
- **CPU**: <20% sustained CPU utilization (screenshot capture spikes to 50%)
- **Storage**: <10MB per session (profile + audit trail), auto-cleanup on termination

---

## Security Considerations

### Authentication & Authorization

- **Auth Mechanism**: No user authentication (local system tool)
- **Permission Model**: User consent per action category (mouse, keyboard, screenshot)
- **Token Management**: N/A (Gemini API key in environment variable, not session-based)

### Input Validation (Constitutional Law #3)

- **Validation Layer**: Pydantic `ComputerUseAction` model with strict schema
  ```python
  class ComputerUseAction(BaseModel):
      action_type: Literal["click", "type", "screenshot"]  # Whitelist
      target: str | None = None  # CSS selector for click/type
      text: str | None = None    # Text for type action

      @field_validator("action_type")
      @classmethod
      def validate_action_whitelist(cls, v: str) -> str:
          if v not in ["click", "type", "screenshot"]:
              raise ValueError(f"Unsupported action: {v}")
          return v
  ```
- **Sanitization**: CSS selectors escaped to prevent XSS (`page.locator(sanitize_selector(target))`)
- **Rate Limiting**: Sliding window enforces 10 actions/min (DDoS protection)

### Data Protection

- **Encryption**: Audit trail encrypted at rest (OS-level file encryption)
- **PII Handling**: Screenshots may contain PII → stored in secure directory (`~/.agency/audit/`), user-deleted after session
- **Audit Logging**: All actions logged with HMAC signatures (tamper detection)

---

## Testing Strategy

### Unit Tests (TDD - Law #1)

- **Coverage Target**: >95%
- **Test Framework**: pytest (Python)
- **Patterns**: AAA (Arrange-Act-Assert), Result pattern unwrapping
- **Mocking**: Playwright browser API (mock `page.click()`, `page.screenshot()`), Gemini API responses

### Integration Tests

- **Scope**: Full workflow (browser launch → action execution → cleanup)
- **Environment**: Real Brave browser + Playwright, mocked Gemini API
- **Data**: Sample action JSONs (valid and invalid)

### End-to-End Tests

- **User Flows**:
  1. Initialize session → execute screenshot → verify audit trail signed
  2. Rate limit test: Execute 11 actions in 60s → 11th fails
  3. Session timeout: Wait 30 min → auto-cleanup triggered
- **Performance**: Action latency <2s p95 (verified with timers)

### NECESSARY Pattern (Comprehensive Coverage)

- **N**ormal operation tests:
  - `test_normal_browser_launch_with_isolated_profile()`
  - `test_normal_screenshot_capture_succeeds()`
  - `test_normal_mouse_click_on_button()`
- **E**dge case tests:
  - `test_edge_rate_limit_boundary_at_10th_action()`
  - `test_edge_session_timeout_at_30_minutes()`
  - `test_edge_concurrent_sessions_with_different_ids()`
- **C**orner case tests:
  - `test_corner_empty_page_screenshot()`
  - `test_corner_action_on_nonexistent_element()`
- **E**rror condition tests:
  - `test_error_brave_not_installed_returns_err()`
  - `test_error_invalid_action_json_from_gemini()`
  - `test_error_browser_crash_triggers_cleanup()`
- **S**ecurity tests:
  - `test_security_cross_tab_access_blocked()`
  - `test_security_filesystem_access_blocked()`
  - `test_security_audit_trail_tamper_detection()`
- **S**tress/performance tests:
  - `test_stress_100_actions_per_session_no_memory_leak()`
  - `test_performance_screenshot_latency_p95_under_500ms()`
- **A**ccessibility tests:
  - `test_accessibility_visual_banner_present()` (N/A for browser automation)
- **R**egression tests:
  - `test_regression_rate_limiter_sliding_window()` (prevent past bugs)
- **Y**ield (output validation) tests:
  - `test_yield_audit_entry_contains_all_required_fields()`
  - `test_yield_hmac_signature_verification_succeeds()`

---

## Documentation Requirements

### User Documentation

- [ ] README with usage examples (Result pattern, consent workflow)
- [ ] API reference (`GeminiComputerUse` class, Pydantic models)
- [ ] Configuration guide (environment variables: `GEMINI_API_KEY`, `GEMINI_AUDIT_HMAC_KEY`, rate limits)

### Developer Documentation

- [ ] Architecture overview (browser isolation, audit trail, rate limiting)
- [ ] Code examples with Result pattern (`match result { Ok(session) => ..., Err(e) => ... }`)
- [ ] Security model (threat analysis, mitigation strategies)

### Operational Documentation

- [ ] Installation guide (`brew install brave-browser`, `pip install playwright`, `playwright install chromium`)
- [ ] Monitoring guide (audit trail review, HMAC signature verification)
- [ ] Troubleshooting guide (common errors: BraveNotInstalled, ConsentDenied, RateLimitExceeded)

---

## Implementation Guidance

### Recommended Approach

1. **Phase 1**: Pydantic models + Result pattern (foundation - 2 hours)
   - Define `BrowserSession`, `ComputerUseAction`, `AuditEntry`, `ConsentTracker`, `RateLimiter`
   - Implement `Result<T, E>` error types (BraveNotInstalled, ConsentDenied, etc.)
   - Write unit tests for Pydantic validation (TDD)

2. **Phase 2**: Browser session management (Playwright integration - 3 hours)
   - Implement `GeminiComputerUse.initialize()` (launch Brave with isolated profile)
   - Visual banner injection via JavaScript
   - Cleanup logic (profile deletion, process termination)
   - Write integration tests (browser launch, cleanup verification)

3. **Phase 3**: Action execution + consent workflow (core logic - 4 hours)
   - Parse Gemini action JSON (Pydantic validation)
   - Execute via Playwright (`page.click()`, `page.type()`, `page.screenshot()`)
   - User consent prompts (ConsentTracker state management)
   - Write end-to-end tests (full workflow with real browser)

4. **Phase 4**: Rate limiting + audit trail (security hardening - 3 hours)
   - Sliding window rate limiter (deque of timestamps)
   - HMAC-signed audit trail (reuse `tools/orchestrator/audit_signing.py` patterns)
   - Session timeout logic (30-minute auto-termination)
   - Write security tests (NECESSARY pattern - cross-tab isolation, tamper detection)

### Key Design Decisions

- **Architecture Pattern**: Repository pattern for audit trail (append-only JSONL), Command pattern for actions
- **Error Handling**: Result<T, E> pattern (Constitutional Law #5) - all errors typed and actionable
- **Type Safety**: Pydantic models with strict validation (Constitutional Law #2) - no `Dict[Any, Any]`
- **Validation**: Input validation at Gemini API boundary (sanitize CSS selectors, whitelist actions)

### Constitutional Compliance Checklist

- [ ] **Article I**: Complete context - full audit trail, no partial execution (retry on timeout)
- [ ] **Article II**: 100% test success rate - NECESSARY pattern coverage >95%
- [ ] **Article III**: Automated enforcement - rate limits, consent, no manual override paths
- [ ] **Article IV**: VectorStore learnings - store successful isolation patterns after validation
- [ ] **Article V**: Spec-driven development - all code traceable to this specification

---

## References

### Related Specifications

- **SPEC-006**: Slop Immunity Protocol (HMAC audit trail patterns)
- **SPEC-030**: Foundation Automation Test Coverage (NECESSARY pattern validation)

### Architecture Decision Records

- **ADR-008**: Strict Typing (no `Dict[Any, Any]`, Pydantic enforcement)
- **ADR-010**: Result Pattern (error handling standard)
- **ADR-023**: Memory-Aware Execution (resource constraints, cleanup)

### External Documentation

- [Playwright Python Documentation](https://playwright.dev/python/docs/intro)
- [Gemini API Reference](https://ai.google.dev/docs)
- [Brave Browser CLI Flags](https://peter.sh/experiments/chromium-command-line-switches/)

---

## Technical Architecture

### Component Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  GeminiComputerUse (Main Orchestrator)                           │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Session Manager│  │ Action Executor │  │ Audit Logger     │  │
│  │ - Brave launch │  │ - Parse Gemini  │  │ - HMAC signing   │  │
│  │ - Profile mgmt │  │ - Playwright API│  │ - JSONL append   │  │
│  │ - Cleanup      │  │ - Result<T,E>   │  │ - Tamper detect  │  │
│  └────────┬───────┘  └────────┬────────┘  └────────┬─────────┘  │
│           │                   │                     │            │
│           ▼                   ▼                     ▼            │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ ConsentTracker │  │ RateLimiter     │  │ SecurityGuard    │  │
│  │ - Per-category │  │ - Sliding window│  │ - Action whitelist│ │
│  │ - Session cache│  │ - 10/min limit  │  │ - Tab isolation  │  │
│  └────────────────┘  └─────────────────┘  └──────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                             │
                             ▼
               ┌──────────────────────────────┐
               │  Playwright + Brave Browser   │
               │  - Isolated profile           │
               │  - Single tab context         │
               │  - No extensions/plugins      │
               └──────────────────────────────┘
```

### Data Flow (Official Gemini Computer Use API)

```
1. User Intent + Task Description
   ↓
2. GeminiComputerUse.initialize()
   ↓ (Brave launch with isolated profile, 1440x900 viewport)
3. Capture screenshot (Playwright page.screenshot())
   ↓
4. Send to Gemini API:
   - Model: gemini-2.5-computer-use-preview-10-2025
   - Input: [screenshot_image, task_prompt]
   - Config: custom safety instructions
   ↓
5. Parse function calls from Gemini response
   ↓ (Pydantic ComputerUseAction validation)
6. Convert normalized coordinates (0-999) → pixels (1440x900)
   ↓
7. ConsentTracker.check(action_type)
   ↓ (User prompt if high-risk: navigate, key_combination)
8. RateLimiter.check()
   ↓ (Sliding window validation)
9. ActionExecutor.execute(action)
   ↓ (Playwright API: page.mouse.click(x, y), page.keyboard.type(), etc.)
10. Capture new screenshot for next iteration
   ↓
11. AuditLogger.append(entry)
   ↓ (HMAC signature)
12. Result<T, E> → User
   ↓
13. Loop back to step 4 until task complete or session timeout
```

### Gemini Computer Use API Integration

```python
import google.generativeai as genai
from PIL import Image

# Configure API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create model with computer use capabilities
model = genai.GenerativeModel(
    model_name="gemini-2.5-computer-use-preview-10-2025",
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    ],
    system_instruction="""You are a browser automation assistant.
    STRICT RULES:
    - NEVER navigate to external domains without user confirmation
    - NEVER attempt to access credentials or passwords
    - ONLY interact with the current active tab
    - Use normalized coordinates (0-999 grid) for all actions
    """
)

# Agent loop pseudocode
def computer_use_agent_loop(task: str, max_iterations: int = 20):
    """Execute task using Gemini Computer Use API with safety controls."""
    session = initialize_browser_session()  # Brave with isolated profile

    for iteration in range(max_iterations):
        # Capture current state
        screenshot = session.page.screenshot()

        # Send to Gemini
        response = model.generate_content(
            contents=[Image.open(screenshot), task],
            generation_config={"temperature": 0.7, "max_output_tokens": 4096}
        )

        # Parse function calls
        if not response.candidates[0].function_calls:
            break  # Task complete

        for function_call in response.candidates[0].function_calls:
            # Validate and execute
            action = ComputerUseAction.model_validate(function_call.args)
            result = execute_action_with_safety(session, action)

            if result.is_err():
                logger.error(f"Action failed: {result.unwrap_err()}")
                break

    return session.cleanup()
```

### Pydantic Models

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import datetime, UTC

class BrowserSession(BaseModel):
    """Isolated browser session metadata."""
    session_id: str = Field(..., description="Unique session ID (UUID4)")
    profile_dir: str = Field(..., description="Temp profile directory path")
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    max_actions: int = Field(default=100, ge=1, le=1000)
    timeout_minutes: int = Field(default=30, ge=1, le=120)

class ComputerUseAction(BaseModel):
    """Gemini computer use action with validation (official API actions)."""
    action_type: Literal[
        "click_at",        # Click at normalized coordinates (0-999 grid)
        "type_text_at",    # Type text at coordinates
        "navigate",        # Navigate to URL
        "scroll_document", # Scroll page
        "key_combination", # Keyboard shortcuts
        "hover_at",        # Hover at coordinates
        "drag_and_drop"    # Drag from source to target
    ]
    # Normalized coordinates (0-999 grid, converted from 1440x900 screen)
    x: int | None = Field(None, ge=0, le=999, description="X coordinate (0-999)")
    y: int | None = Field(None, ge=0, le=999, description="Y coordinate (0-999)")
    text: str | None = Field(None, description="Text for type_text_at")
    url: str | None = Field(None, description="URL for navigate action")
    keys: list[str] | None = Field(None, description="Keys for key_combination")

    @field_validator("action_type")
    @classmethod
    def validate_whitelist(cls, v: str) -> str:
        allowed = ["click_at", "type_text_at", "navigate", "scroll_document",
                   "key_combination", "hover_at", "drag_and_drop"]
        if v not in allowed:
            raise ValueError(f"Unsupported action: {v}. Allowed: {allowed}")
        return v

class AuditEntry(BaseModel):
    """Tamper-proof audit trail entry."""
    timestamp: str = Field(..., description="ISO 8601 timestamp (UTC)")
    session_id: str
    action_type: str
    parameters: dict[str, str]
    result: Literal["success", "error"]
    error_message: str | None = None
    duration_ms: int = Field(..., ge=0)
    signature: str = Field(..., description="HMAC-SHA256 signature (hex)")

class ConsentTracker(BaseModel):
    """User consent per action category."""
    mouse_consent: bool = False
    keyboard_consent: bool = False
    screenshot_consent: bool = False

class RateLimiter(BaseModel):
    """Sliding window rate limiter."""
    window_seconds: int = 60
    max_actions: int = 10
    action_timestamps: list[float] = Field(default_factory=list)
```

### Error Types (Result Pattern)

```python
from shared.type_definitions.result import Result, Ok, Err

class BraveNotInstalled(Exception):
    """Brave browser not found in PATH."""
    def __init__(self):
        super().__init__(
            "Brave browser not installed. "
            "Install via: brew install brave-browser"
        )

class ConsentDenied(Exception):
    """User denied consent for action category."""
    def __init__(self, category: str):
        super().__init__(
            f"User denied consent for {category} actions. "
            "Grant consent or terminate session."
        )

class RateLimitExceeded(Exception):
    """Action rate limit exceeded."""
    def __init__(self, wait_seconds: int):
        super().__init__(
            f"Rate limit exceeded (10 actions/min). "
            f"Wait {wait_seconds}s or use --force flag."
        )

class TabIsolationViolation(Exception):
    """Attempted cross-tab action."""
    def __init__(self, details: str):
        super().__init__(
            f"Tab isolation violated: {details}. "
            "Actions limited to single active tab."
        )

class AuditSigningFailed(Exception):
    """HMAC signature generation failed."""
    def __init__(self, reason: str):
        super().__init__(
            f"Audit signing failed: {reason}. "
            "Set GEMINI_AUDIT_HMAC_KEY environment variable."
        )
```

---

## Security Model

### Threat Model

| Threat                                    | Attack Vector                                  | Mitigation                                         | Verification                           |
| ----------------------------------------- | ---------------------------------------------- | -------------------------------------------------- | -------------------------------------- |
| **T1: Cross-tab data leakage**            | Access other tabs via `browser.contexts()`     | Playwright page-scoped API only, security tests    | `test_security_cross_tab_blocked()`    |
| **T2: Filesystem access**                 | Gemini generates file read/write actions       | Action whitelist (click/type/screenshot only)      | `test_security_filesystem_blocked()`   |
| **T3: Clipboard credential theft**        | Access clipboard via `navigator.clipboard`     | No clipboard API access, browser sandbox enforced  | `test_security_clipboard_blocked()`    |
| **T4: Rate limit bypass**                 | Concurrent requests or timestamp manipulation  | Thread-safe sliding window, atomic operations      | `test_stress_concurrent_actions()`     |
| **T5: Audit trail tampering**             | Modify JSONL file or inject false entries      | HMAC-SHA256 signatures, signature verification API | `test_security_tamper_detection()`     |
| **T6: Unauthorized browser control**      | External process hijacks Playwright session    | Unique session ID, profile isolation               | `test_security_session_hijack()`       |
| **T7: Malicious action injection**        | Gemini API compromised or returns XSS payload  | CSS selector sanitization, Pydantic validation     | `test_security_xss_injection_blocked()`|

### Defense in Depth

1. **Browser Isolation** (Layer 1):
   - Isolated profile per session (`--user-data-dir`)
   - Single tab context (Playwright `page` object scope)
   - No extensions or plugins (`--disable-extensions`)

2. **Input Validation** (Layer 2):
   - Pydantic schema validation (action whitelist)
   - CSS selector sanitization (escape special chars)
   - Rate limiting (sliding window)

3. **User Consent** (Layer 3):
   - Explicit opt-in per action category
   - Session-scoped consent (no persistent permissions)

4. **Audit Trail** (Layer 4):
   - HMAC-SHA256 signatures (tamper detection)
   - Append-only JSONL (no edits)
   - Signature verification API (external audit)

5. **Resource Constraints** (Layer 5):
   - 10 actions/min, 100 actions/session
   - 30-minute timeout (auto-cleanup)
   - Memory limits (<500MB per session)

---

## Approval and Sign-Off

**Created By**: SpecGenerator Agent
**Reviewed By**: Planner, ChiefArchitect (pending)
**Approved By**: User/Product Owner (pending)

**Approval Criteria**:
- [ ] All sections complete (Goals, Personas, Acceptance Criteria, Architecture, Security, Tests)
- [ ] Acceptance criteria verifiable (100% testable with NECESSARY pattern)
- [ ] Risks identified and mitigated (threat model with defense in depth)
- [ ] Constitutional compliance validated (Articles I-V enforced)
- [ ] Stakeholder agreement on scope (defensive security only, no malicious automation)

**Approval Date**: Pending
**Approver Signature**: Pending

---

**Living Document**: This specification will be updated during implementation to reflect learnings and refinements.

---

**Constitutional Compliance Statement**:
This specification adheres to all 5 constitutional articles:
- **Article I**: Complete context via full audit trail, retry on Gemini API timeout
- **Article II**: 100% test coverage (NECESSARY pattern), TDD enforcement
- **Article III**: Automated enforcement (rate limits, consent, no manual override)
- **Article IV**: VectorStore learning (isolation patterns stored after validation)
- **Article V**: Spec-driven development (this document is authoritative source)

**Security Policy Compliance**:
This is a **defensive security tool only**. No credential harvesting, no malicious automation. Explicit consent UI for user trust. Open source for transparency. Follows principle of least privilege.
