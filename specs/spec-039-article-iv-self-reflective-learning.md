# Specification: Article IV Self-Reflective Learning Compliance Validation

**ID**: SPEC-20251026-article-iv-self-reflective-learning
**Status**: Draft
**Created**: 2025-10-26
**Updated**: 2025-10-26
**Owner**: SpecGeneratorAgent
**Related**: ADR-004, ADR-006, constitution.md (Article IV)

## Goals

**Primary objectives and success definition**

### What We're Building

This specification defines a comprehensive validation framework to verify that agents comply with Article IV of the Agency Constitution: "Continuous Learning and Improvement." The framework validates that agents query VectorStore patterns before action and store successful patterns after completion, as constitutionally mandated.

- **Goal 1**: Validate agent Article IV compliance - Verify 80%+ query-before-action rate, 100% store-after-success rate
- **Goal 2**: Provide automated compliance enforcement - Pre-commit hooks, telemetry monitoring, quality gates that block constitutional violations
- **Goal 3**: Enable compliance audit capabilities - Git log analysis, VectorStore query/storage tracking, benchmark reporting
- **Goal 4**: Create constitutional test suite - Unit, integration, and E2E tests following NECESSARY pattern

### Success Metrics

- **Metric 1**: 80%+ of agent actions query VectorStore before implementation (benchmark compliance)
- **Metric 2**: 100% of successful operations store learnings to VectorStore (constitutional requirement)
- **Metric 3**: 60%+ of VectorStore queries result in pattern application (learning effectiveness)
- **Metric 4**: 0 constitutional violations in last 30 days (git log audit)
- **Metric 5**: >95% test coverage on Article IV validation logic (TDD compliance)

## Non-Goals

**Explicitly out of scope for this specification**

- **Non-goal 1**: Modifying existing agent implementations - This spec validates compliance, not implements Article IV in agents (agents already have VectorStore integration per ADR-004)
- **Non-goal 2**: Creating new VectorStore infrastructure - Existing `agency_memory/` module provides VectorStore (ADR-006), this spec validates its usage
- **Non-goal 3**: Enforcing query/storage patterns in non-agent code - Constitutional requirement applies to autonomous agents only, not tools or utilities
- **Non-goal 4**: Real-time blocking of non-compliant operations - Validation is pre-commit and post-hoc audit, not runtime interception (performance trade-off)

**Why These Are Non-Goals:**

Article IV infrastructure (VectorStore, AgentContext memory API) already exists per ADR-004 and ADR-006. This specification focuses on *validating* that agents use this infrastructure correctly, not building it. Real-time blocking would add significant performance overhead and complexity; pre-commit hooks and audit reports provide sufficient enforcement with minimal impact.

## Personas

**Who will use this feature and how**

### Persona 1: Quality Enforcer Agent

- **Context**: Autonomous quality validation during development workflows
- **Need**: Automated Article IV compliance checking before merges
- **Current Pain Point**: No systematic validation that agents query/store VectorStore as required - constitutional violations go undetected
- **Desired Outcome**: Pre-commit hook blocks merges when Article IV compliance <80%, telemetry dashboard shows real-time compliance metrics
- **Interaction Pattern**: Runs `validate_article_iv_compliance()` in pre-commit hook, receives pass/fail with detailed violation report

### Persona 2: Agent Developer (Human or Autonomous)

- **Context**: Creating new agents or modifying existing agent workflows
- **Need**: Clear compliance requirements, immediate feedback on violations
- **Current Pain Point**: Article IV requirements are documented but not enforced - easy to accidentally violate by forgetting search_memories() call
- **Desired Outcome**: Unit tests fail if agent skips VectorStore query, integration tests validate full query→action→store flow
- **Interaction Pattern**: Runs pytest test suite, sees failures with actionable error messages: "Agent 'planner' did not query VectorStore before planning (Article IV violation)"

### Persona 3: System Administrator / DevOps

- **Context**: Monitoring constitutional compliance across all agent sessions
- **Need**: Historical compliance metrics, trend analysis, violation alerts
- **Current Pain Point**: No visibility into Article IV compliance rates - can't measure learning effectiveness or detect regression
- **Desired Outcome**: Git log audit script generates monthly compliance report: "Query rate: 87%, Storage rate: 100%, 0 violations"
- **Interaction Pattern**: Runs `python tools/constitutional_intelligence/audit_article_iv.py --since=30d`, reviews JSON report

## Acceptance Criteria

**Verifiable conditions for feature completion**

### Functional Criteria (MUST HAVE)

- [ ] **FC-01**: AgentContext memory API validation (Unit tests)
  - Given: Agent receives AgentContext with memory system
  - When: Agent calls `context.search_memories(tags=["pattern", "task_type"])`
  - Then: Query executes successfully, returns list of matching patterns
  - Edge cases: Empty result set, VectorStore unavailable (graceful fallback)

- [ ] **FC-02**: Query-before-action workflow validation (Integration tests)
  - Given: Agent starting new task (e.g., PlannerAgent.create_plan())
  - When: Agent execution begins
  - Then: `search_memories()` called BEFORE `create_plan_content()`, query logged with timestamp
  - Validation: Telemetry shows query_timestamp < action_timestamp

- [ ] **FC-03**: Store-after-success workflow validation (Integration tests)
  - Given: Agent completes task successfully
  - When: Task completion detected (Result.is_ok() == True)
  - Then: `context.store_memory()` called with task outcome, learnings persisted to VectorStore
  - Error handling: If storage fails, log warning but don't block completion

- [ ] **FC-04**: Git log audit for constitutional compliance
  - Given: Git repository with 30 days of commit history
  - When: `audit_article_iv.py --since=30d` executed
  - Then: Script scans commits for VectorStore query/storage calls, generates compliance report JSON
  - Validation: Report shows query_rate, storage_rate, violations list

- [ ] **FC-05**: Benchmark metrics calculation
  - Given: Telemetry data from agent sessions
  - When: Benchmark calculation runs
  - Then: Calculates query_rate (queries / total_actions), storage_rate (storages / successful_actions), pattern_application_rate (patterns_applied / queries)
  - Threshold validation: query_rate ≥ 0.80, storage_rate == 1.0

- [ ] **FC-06**: Constitutional violation detection and blocking
  - Given: Agent implementation that skips VectorStore query
  - When: Pre-commit hook runs `validate_article_iv_compliance()`
  - Then: Hook detects violation, blocks commit with error message: "Article IV violated: Agent 'X' did not query VectorStore before action Y"
  - Edge cases: Allow skip for non-agent code, simple tools, or test fixtures

### Non-Functional Criteria (MUST HAVE)

- [ ] **NF-01**: Performance: Validation overhead <100ms per agent action (telemetry logging)
- [ ] **NF-02**: Reliability: VectorStore unavailable → graceful fallback, log warning, continue without blocking
- [ ] **NF-03**: Security: Patterns stored to VectorStore must not contain API keys, passwords, or PII
- [ ] **NF-04**: Type Safety: All validation functions use Pydantic models for telemetry data (Article II, Law #2)
- [ ] **NF-05**: Scalability: Git audit script handles repositories with 10,000+ commits (pagination, streaming)

### Quality Criteria (Constitutional Compliance - MUST HAVE)

- [ ] **QC-01**: Test Coverage >95% (Article II) - Unit, integration, E2E tests for all validation logic
- [ ] **QC-02**: All 10 constitutional laws enforced in validation code
- [ ] **QC-03**: All 5 constitutional articles validated (Article IV is focus, but validator checks all)
- [ ] **QC-04**: Documentation: Public APIs documented with docstrings (Law #9)
- [ ] **QC-05**: Code Quality: Zero linting errors, functions <50 lines (Law #8)
- [ ] **QC-06**: TDD: Tests written BEFORE implementation (Law #1, Article VI)

### User Experience Criteria

- [ ] **UX-01**: Error messages are actionable - "Article IV violated: Missing search_memories() call in planner_agent.py:142"
- [ ] **UX-02**: Compliance reports are human-readable JSON with clear metrics
- [ ] **UX-03**: Pre-commit hook provides remediation guidance: "Add context.search_memories(tags=['pattern']) before line 142"

## Functional Requirements

### FR-01: AgentContext Memory API Validation

**Description**: Validate that AgentContext provides VectorStore integration via search_memories() and store_memory()
**Priority**: Critical
**Complexity**: Low

**Details**:

- Behavior 1: `context.search_memories(tags)` returns list of matching patterns
- Behavior 2: `context.store_memory(key, content, tags)` persists to VectorStore
- Constraint: Both methods must be available on all AgentContext instances (Article IV mandate)

**Test Strategy**: Unit tests verify API exists, returns expected types, handles edge cases (empty results, VectorStore unavailable)

### FR-02: Query-Before-Action Timing Validation

**Description**: Verify that agents call search_memories() BEFORE taking action (not after)
**Priority**: Critical
**Complexity**: Medium

**Details**:

- Behavior 1: Telemetry logs query_timestamp when search_memories() called
- Behavior 2: Telemetry logs action_timestamp when agent action begins
- Constraint: query_timestamp MUST be < action_timestamp (constitutional ordering)

**Test Strategy**: Integration tests mock telemetry logger, verify log order, assert query happens first

### FR-03: Store-After-Success Detection

**Description**: Verify that agents call store_memory() after successful task completion (not failures)
**Priority**: Critical
**Complexity**: Medium

**Details**:

- Behavior 1: Monitor task completion via Result<T, E> pattern (is_ok() == True)
- Behavior 2: Expect store_memory() call within 5 seconds of success
- Constraint: Storage MUST occur for successful tasks, SHOULD NOT occur for failures (don't learn from errors without explicit labeling)

**Test Strategy**: Integration tests execute agent task, verify storage call happens after success, does NOT happen after failure

### FR-04: Git Log Constitutional Audit

**Description**: Scan git commit history for Article IV compliance patterns
**Priority**: High
**Complexity**: High

**Details**:

- Behavior 1: Parse git log for commits touching agent files
- Behavior 2: AST-parse Python files to detect search_memories() and store_memory() calls
- Behavior 3: Calculate compliance rates per agent, per time period
- Constraint: Audit must handle large repositories (10K+ commits) without memory exhaustion

**Test Strategy**: Unit tests with mock git log, integration tests with real fixture repository, E2E test with Agency repo

### FR-05: Pre-Commit Hook Enforcement

**Description**: Block commits that introduce Article IV violations
**Priority**: High
**Complexity**: Medium

**Details**:

- Behavior 1: Pre-commit hook runs validate_article_iv_compliance() on staged files
- Behavior 2: If agent code modified without VectorStore query/storage, reject commit
- Constraint: Allow skip for test files, non-agent code, or with explicit override flag
- Error message: "Article IV violation detected in [file:line]. Add context.search_memories() before action."

**Test Strategy**: Pre-commit hook testing framework, mock git staged files, verify blocking behavior

### FR-06: Telemetry Dashboard Metrics

**Description**: Real-time visibility into Article IV compliance rates
**Priority**: Medium
**Complexity**: Medium

**Details**:

- Behavior 1: Telemetry middleware logs query/storage events with agent_name, task_type, timestamp
- Behavior 2: Dashboard calculates rolling metrics: query_rate, storage_rate, pattern_application_rate
- Constraint: Metrics updated every 5 minutes, historical data retained for 90 days

**Test Strategy**: Unit tests for metric calculation, integration tests for telemetry logging, E2E test for dashboard rendering

## Non-Functional Requirements

### NFR-01: Performance

- **Target**: Validation overhead <100ms per agent action (telemetry logging <10ms, compliance check <90ms)
- **Measurement**: Profiling with cProfile, benchmark with 1000 agent actions
- **Acceptance**: 95th percentile latency <100ms

### NFR-02: Reliability

- **Target**: 99.9% uptime for validation infrastructure (VectorStore client, telemetry logger)
- **Fallback**: If VectorStore unavailable, log warning and continue (don't block agent execution)
- **Acceptance**: <0.1% of agent actions blocked by validation infrastructure failure

### NFR-03: Security

- **Validation**: Patterns stored to VectorStore must not contain secrets
- **Sanitization**: Regex scan for API_KEY, PASSWORD, TOKEN patterns before storage
- **Acceptance**: 0 secrets leaked to VectorStore in production (audit scan)

### NFR-04: Type Safety (Constitutional Law #2)

- **Strict Typing**: No `any` or `Dict[Any, Any]` in validation code
- **Pydantic Models**: ArticleIVTelemetry, ComplianceReport, ValidationResult all typed
- **Validation**: Mypy passes with strict mode (--strict flag)

### NFR-05: Error Handling (Constitutional Law #5)

- **Result Pattern**: All validation functions return Result<T, E>
- **No Exceptions**: No try/catch for control flow (use Result for expected errors)
- **Typed Errors**: ValidationError, ComplianceError, AuditError explicit types

## Dependencies

### Internal Dependencies

- **SPEC-035**: VectorStore Validation Criteria (harmonization with VectorStore testing strategy)
- **ADR-004**: Continuous Learning System (defines Article IV requirements)
- **ADR-006**: Three-Tier Memory Architecture (AgentContext memory API spec)
- **constitution.md**: Article IV formal definition (constitutional mandate)

### External Dependencies

- **agency_memory/**: VectorStore backend (EnhancedMemoryStore, Memory API)
- **shared/agent_context.py**: AgentContext with search_memories(), store_memory()
- **shared/constitutional_validator.py**: validate_article_iv() function (existing infrastructure)
- **Git**: Git log parsing for historical audit

### Dependency Impact Analysis

- **Breaking Changes**: None - validation is additive, does not modify existing agent APIs
- **Integration Points**: Pre-commit hooks, telemetry middleware, AgentContext initialization
- **Migration Path**: N/A - new capability, no migration needed

## Risks and Mitigations

| ID   | Risk                                      | Impact | Probability | Mitigation Strategy                                                | Owner           |
| ---- | ----------------------------------------- | ------ | ----------- | ------------------------------------------------------------------ | --------------- |
| R-01 | VectorStore unavailable blocks agents     | High   | Low         | Graceful fallback: log warning, continue without blocking          | QualityEnforcer |
| R-02 | False positives block valid commits       | Medium | Medium      | Explicit override flag: `git commit --no-verify` for emergencies   | Developer       |
| R-03 | Git audit script consumes excessive RAM   | Medium | Medium      | Streaming git log parser, paginate results, limit history to 90d   | Toolsmith       |
| R-04 | Telemetry overhead degrades performance   | Low    | High        | Async logging, batch writes, sampling (log 10% of queries)         | CodeAgent       |
| R-05 | Secrets leaked to VectorStore patterns    | High   | Low         | Pre-storage sanitization, regex scan for common secret patterns    | QualityEnforcer |
| R-06 | Compliance metrics misleading (sampling)  | Medium | Medium      | Document sampling methodology, provide raw counts alongside metrics | Planner         |

### Risk Mitigation Plan

**High-Risk Items (Impact: High, Probability: Medium/High):**

**R-01: VectorStore Unavailable**

- Mitigation: Implement circuit breaker pattern - after 3 consecutive VectorStore failures, switch to fallback mode (no queries/storage) for 5 minutes
- Contingency: Manual override env var `DISABLE_ARTICLE_IV_ENFORCEMENT=true` for production incidents
- Early Warning: VectorStore health check every 60 seconds, alert if down >5 minutes

**R-05: Secrets Leaked**

- Mitigation: Sanitization layer in store_memory() - scan for patterns: `(api_key|password|token|secret)\s*=\s*['"][^'"]+['"]`
- Contingency: VectorStore audit script to scan existing patterns for secrets, purge if found
- Early Warning: Random sampling of 1% of stored patterns, automated secret detection

## Edge Cases and Error Scenarios

### Edge Case 1: VectorStore Returns Empty Results

- **Scenario**: Agent queries VectorStore but no relevant patterns exist (new task type, cold start)
- **Expected Behavior**: Agent proceeds without historical patterns, creates new learning from scratch
- **Test Case**: Unit test with empty VectorStore, verify agent doesn't crash, completes task successfully

### Edge Case 2: Agent Stores Pattern After Partial Success

- **Scenario**: Agent completes task with warnings (e.g., 95% test pass rate, not 100%)
- **Expected Behavior**: Storage decision based on threshold - store if >90% success, don't store if <90%
- **Test Case**: Integration test with partial success scenario, verify storage logic

### Edge Case 3: Multiple Agents Query VectorStore Concurrently

- **Scenario**: 10 agents query VectorStore simultaneously, race condition risk
- **Expected Behavior**: VectorStore handles concurrent reads (read-only operation, no race condition)
- **Test Case**: Load test with 100 concurrent queries, verify no corruption

### Error Scenario 1: Search_Memories() Timeout

- **Trigger**: VectorStore query takes >5 seconds (network latency, large result set)
- **Error Response**: TimeoutError with typed error object
- **User Experience**: Agent logs warning "VectorStore query timed out, proceeding without historical patterns"
- **Recovery**: Fallback to no-pattern mode, continue task execution

### Error Scenario 2: Store_Memory() Fails Due to Invalid Data

- **Trigger**: Pattern contains non-serializable object (e.g., threading.Lock)
- **Error Response**: SerializationError with typed error object
- **User Experience**: Agent logs error "Failed to store pattern: [reason]", task completion NOT blocked
- **Recovery**: Sanitize pattern (remove non-serializable fields), retry once, then skip if still fails

### Error Scenario 3: Git Audit Script Encounters Binary Files

- **Trigger**: Repository contains large binary files in commit history
- **Error Response**: BinaryFileSkipped warning
- **User Experience**: Audit script skips binary files, logs count: "Skipped 47 binary files"
- **Recovery**: Continue audit with text files only, note limitation in report

## Performance Requirements

### Latency Targets

- **P50**: 10ms for search_memories() call (VectorStore query)
- **P95**: 50ms for search_memories() call (network latency, large result sets)
- **P99**: 100ms for search_memories() call (worst case, timeout threshold)

### Throughput Targets

- **Requests/Second**: 1000 VectorStore queries/sec (10 agents × 100 queries/sec each)
- **Concurrent Agents**: 100 simultaneous agents querying VectorStore

### Resource Constraints

- **Memory**: Validation logic <50MB heap (telemetry buffering, metric aggregation)
- **CPU**: <5% CPU for telemetry logging (async, non-blocking)
- **Storage**: Telemetry logs <1GB/day (90-day retention = 90GB)

## Security Considerations

### Authentication & Authorization

- **Auth Mechanism**: VectorStore queries authenticated via AgentContext session_id
- **Permission Model**: All agents can read patterns, only creating agent can update its own patterns
- **Token Management**: No tokens required (local VectorStore, no external API)

### Input Validation (Constitutional Law #3)

- **Validation Layer**: Pydantic models for all telemetry data (ArticleIVTelemetry, ComplianceReport)
- **Sanitization**: Regex-based secret detection before pattern storage
- **Rate Limiting**: 1000 queries/sec per agent (DDoS protection)

### Data Protection

- **Encryption**: VectorStore data encrypted at rest (Firestore backend, AES-256)
- **PII Handling**: Patterns must not contain user emails, names, or personal data (sanitization layer)
- **Audit Logging**: All VectorStore writes logged for compliance audit

## Testing Strategy

### Unit Tests (TDD - Law #1)

- **Coverage Target**: >95%
- **Test Framework**: pytest
- **Patterns**: AAA (Arrange-Act-Assert)
- **Mocking**: Mock VectorStore, AgentContext for fast, isolated tests

**Test Files**:

- `tests/test_article_iv_validation_unit.py` (25 tests)
  - test_search_memories_api_exists
  - test_store_memory_api_exists
  - test_query_before_action_timing
  - test_store_after_success_detection
  - test_compliance_report_generation
  - test_benchmark_calculation
  - test_sanitization_layer_removes_secrets
  - test_fallback_mode_when_vectorstore_unavailable

### Integration Tests

- **Scope**: Full agent workflow (query → action → store) with real VectorStore
- **Environment**: In-memory VectorStore (agency_memory/Memory)
- **Data**: Fixture patterns for reproducibility

**Test Files**:

- `tests/integration/test_article_iv_integration.py` (15 tests)
  - test_planner_agent_queries_before_planning
  - test_coder_agent_stores_after_implementation
  - test_quality_enforcer_validates_article_iv
  - test_git_audit_script_scans_commits
  - test_pre_commit_hook_blocks_violations
  - test_telemetry_logs_query_storage_events

### End-to-End Tests

- **User Flows**: Complete mission with Article IV compliance tracking
- **Performance**: Load test with 100 agents querying VectorStore

**Test Files**:

- `tests/e2e/test_article_iv_compliance_e2e.py` (10 tests)
  - test_mission_compliance_full_workflow
  - test_git_audit_generates_report
  - test_pre_commit_hook_enforcement
  - test_concurrent_agent_vectorstore_access

### NECESSARY Pattern (Comprehensive Coverage)

- **N**ormal operation tests (happy path): Agent queries, finds patterns, applies them, stores new learning
- **E**dge case tests (boundaries, limits): Empty VectorStore, no matching patterns, concurrent queries
- **C**orner case tests (unusual combinations): Query timeout + fallback, storage failure + retry
- **E**rror condition tests (invalid inputs, failures): VectorStore unavailable, serialization error, binary files in git audit
- **S**ecurity tests (injection, auth bypass): Secret detection in patterns, unauthorized pattern modification
- **S**tress/performance tests (load, concurrency): 1000 queries/sec, 100 concurrent agents
- **A**ccessibility tests (if user-facing): N/A - internal validation framework
- **R**egression tests (prevent past bugs): Track past Article IV violations, ensure detection
- **Y**ield (output validation) tests: Compliance report JSON schema validation, benchmark metric ranges

## Documentation Requirements

### User Documentation

- [ ] README with usage examples (validate_article_iv_compliance(), audit script)
- [ ] Compliance report interpretation guide (what do metrics mean?)
- [ ] Troubleshooting guide (common violations, remediation steps)

### Developer Documentation

- [ ] Architecture overview (validation flow, telemetry pipeline, git audit)
- [ ] Code examples with Result pattern (how to add Article IV compliance to new agents)
- [ ] Pre-commit hook setup instructions

### Operational Documentation

- [ ] Git audit script usage (`python tools/constitutional_intelligence/audit_article_iv.py --help`)
- [ ] Telemetry dashboard access (where to view metrics)
- [ ] Incident runbook (VectorStore down, what to do?)

## Implementation Guidance

### Recommended Approach

1. **Phase 1**: Unit tests for AgentContext memory API validation (TDD foundation)
2. **Phase 2**: Integration tests for query-before-action, store-after-success workflows
3. **Phase 3**: Git audit script with AST parsing
4. **Phase 4**: Pre-commit hook enforcement, telemetry dashboard

### Key Design Decisions

- **Architecture Pattern**: Observer pattern for telemetry (agents emit events, middleware logs)
- **Error Handling**: Result<T, E> pattern (Constitutional Law #5)
- **Type Safety**: Pydantic models (Constitutional Law #2)
- **Validation**: Input validation at boundaries (Law #3)

### Constitutional Compliance Checklist

- [ ] **Article I**: Complete context gathered before validation (full git log, all telemetry data)
- [ ] **Article II**: 100% test success rate enforced (TDD, >95% coverage)
- [ ] **Article III**: Automated enforcement via pre-commit hooks (no manual bypass)
- [ ] **Article IV**: VectorStore learnings applied (query existing validation patterns before implementing new tests)
- [ ] **Article V**: Spec-driven development followed (this spec traces to implementation)

## References

### Related Specifications

- **SPEC-035**: VectorStore Validation Criteria (harmonized testing strategy)
- **SPEC-037**: E2E Testing Framework (E2E test infrastructure)
- **SPEC-030**: Foundation Automation Test Coverage (TDD baseline)

### Architecture Decision Records

- **ADR-004**: Continuous Learning System (Article IV definition)
- **ADR-006**: Three-Tier Memory Architecture (AgentContext memory API)
- **ADR-024**: Adaptive Model Router (VectorStore learning integration example)
- **ADR-025**: Quality Feedback Loop (telemetry-driven improvement)

### External Documentation

- [VectorStore API Documentation](../agency_memory/CLAUDE.md)
- [AgentContext Reference](../shared/CLAUDE.md)
- [Constitutional Validator API](../shared/constitutional_validator.py)

## Approval and Sign-Off

**Created By**: SpecGeneratorAgent
**Reviewed By**: Planner, ChiefArchitect (pending)
**Approved By**: User/Product Owner (pending)

**Approval Criteria**:

- [ ] All sections complete
- [ ] Acceptance criteria verifiable (testable with NECESSARY pattern)
- [ ] Risks identified and mitigated (graceful fallback, sanitization)
- [ ] Constitutional compliance validated (Articles I-V checklist)
- [ ] Stakeholder agreement on scope (query/storage validation, not infrastructure changes)

**Approval Date**: TBD
**Approver Signature**: TBD

---

**Living Document**: This specification will be updated during implementation to reflect learnings and refinements.

**Next Steps**:

1. **Review**: Submit spec to Planner for technical feasibility review
2. **Approval**: Get sign-off from ChiefArchitect on architecture decisions
3. **Planning**: Create plan.md with agent assignments, tool development, test strategy
4. **Implementation**: TDD workflow - write tests first (Article VI mandate)
