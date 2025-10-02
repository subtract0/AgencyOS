# Specification: Expanded Autonomous Healing System

**Spec ID**: `spec-016-expanded-autonomous-healing`
**Status**: `Draft`
**Author**: QualityEnforcerAgent
**Created**: 2025-10-02
**Last Updated**: 2025-10-02
**Related Plan**: `plan-016-expanded-autonomous-healing.md`

---

## Executive Summary

Expand Agency OS autonomous healing from NoneType-only coverage (1 error category) to comprehensive healing across 5+ error categories (type errors, import errors, style violations, security issues, performance anti-patterns), add proactive static analysis scanning, build real-time healing dashboard, and auto-extract successful healing patterns to VectorStore. This will improve autonomous healing from 79/100 to 89/100, transforming reactive bug fixing into proactive code quality maintenance.

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Extend autonomous healing from 1 error category (NoneType) to 5+ categories (type, import, style, security, performance)
- [ ] **Goal 2**: Add proactive static analysis scanning (scheduled + on-commit) to detect issues before runtime
- [ ] **Goal 3**: Build real-time healing dashboard displaying live metrics, active healing operations, and success rates
- [ ] **Goal 4**: Auto-extract successful healing patterns to VectorStore for continuous learning and reuse
- [ ] **Goal 5**: Achieve 95%+ healing success rate across all error categories with automated rollback on failure

### Success Metrics
- **Error Category Coverage**: From 1 (NoneType) to 6+ (type, import, style, security, performance, logic)
- **Healing Success Rate**: From >95% (NoneType only) to 95%+ across all categories
- **Proactive Detection**: 80%+ of issues caught before runtime via static analysis
- **Pattern Reuse**: 60%+ of healing operations leverage learned patterns from VectorStore
- **Dashboard Observability**: Real-time visibility into 100% of healing operations
- **Learning Integration**: 100% of successful heals automatically stored in VectorStore

---

## Non-Goals

### Explicit Exclusions
- **Semantic Bug Detection**: Not fixing logic errors requiring domain knowledge (e.g., incorrect business logic)
- **UI/Frontend Healing**: Focus on Python backend healing, not TypeScript/React (defer to future)
- **Distributed Healing**: Not implementing cross-repository healing (single codebase only)
- **Interactive Debugging**: Not building step-through debugger or interactive fix suggestion UI

### Future Considerations
- **AI-Powered Refactoring**: Beyond error fixing to intelligent code optimization
- **Multi-Language Support**: Extend healing to TypeScript, Go, Rust codebases
- **Predictive Healing**: ML models predicting likely errors before they occur
- **Community Pattern Sharing**: Public pattern library for common healing scenarios

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Development Lead (@am - Quality Oversight)
- **Description**: Project owner maintaining code quality and preventing technical debt accumulation
- **Goals**: Proactive issue detection, automated fixing of routine errors, zero manual toil on style/type issues
- **Pain Points**: Manual fixing of repetitive errors, issues discovered at runtime instead of commit-time, no visibility into healing operations
- **Technical Proficiency**: Expert in software quality, expects production-grade autonomous maintenance

#### Persona 2: QualityEnforcerAgent (Healing Orchestrator)
- **Description**: Agent responsible for detecting, analyzing, fixing, and verifying code quality issues
- **Goals**: Comprehensive error coverage, high success rate, pattern reuse, minimal human intervention
- **Pain Points**: Limited to NoneType errors, reactive-only detection, no learning integration, no observability
- **Technical Proficiency**: Expert in autonomous operations, requires healing primitives and pattern library

#### Persona 3: AgencyCodeAgent (Code Producer)
- **Description**: Agent writing code that may introduce errors requiring autonomous healing
- **Goals**: Immediate feedback on code quality issues, automated fixes where possible, clear guidance on complex errors
- **Pain Points**: Errors discovered late in process, manual fixing interrupts flow, no pattern guidance
- **Technical Proficiency**: Expert in code generation, benefits from proactive healing and pattern suggestions

### User Journeys

#### Journey 1: Runtime NoneType Error (Current - Reactive Healing)
```
1. Code executes: Function encounters NoneType error at runtime
2. Error logged: Telemetry captures error trace
3. Healing triggered: QualityEnforcer detects NoneType error in logs
4. LLM analysis: GPT-5 generates fix based on error context
5. Fix applied: Patch applied with test verification
6. Success: Error resolved, but only after runtime failure
7. Gap: Other error types (imports, types, style) remain unhealed
```

#### Journey 2: Multi-Category Error (Future - Proactive Healing)
```
1. Commit staged: Developer commits code with type error + import error + style violation
2. Pre-commit scan: Static analysis detects 3 issues before commit
3. Parallel healing: All 3 errors healed concurrently (type, import, style)
4. Pattern match: Type error matches learned pattern, instant fix
5. Verification: All tests pass, commit proceeds
6. Prevention: Issues never reach runtime, zero manual intervention
7. Learning: Successful fixes stored in VectorStore for future reuse
```

#### Journey 3: Security Issue Detection (Future - Proactive Security)
```
1. Scheduled scan: Daily security analysis runs overnight
2. Vulnerability detected: SQL injection vulnerability in database query
3. Severity assessed: HIGH severity, requires human approval
4. User notified: "Security issue detected: SQL injection in user_repository.py:42"
5. Auto-fix generated: Parameterized query fix proposed
6. User reviews: Approves fix or requests modification
7. Fix applied: Vulnerability patched, security test added
8. Learning: Security pattern stored for preventing similar issues
```

#### Journey 4: Performance Anti-Pattern (Future - Performance Healing)
```
1. Proactive scan: Performance analysis detects N+1 query pattern
2. Context gathered: Database queries in loop, 100x redundant calls
3. Fix generated: Batch query optimization proposed
4. Benchmark: 95% performance improvement estimated
5. Fix applied: Optimized code replaces anti-pattern
6. Verification: Performance tests confirm improvement
7. Learning: N+1 pattern stored for future detection
```

#### Journey 5: Real-Time Dashboard Monitoring (Future - Observability)
```
1. User opens: `agency healing-dashboard` or web UI
2. Dashboard shows:
   - Active healing operations: 3 in progress (2 type errors, 1 import)
   - Success rate (last 24h): 97% (58/60 heals successful)
   - Pattern reuse: 65% (38/58 heals used learned patterns)
   - Error distribution: Type 40%, Import 25%, Style 20%, Security 10%, Perf 5%
3. Drill-down: Click "type errors" → see all type error heals with details
4. Pattern view: Click pattern → see when learned, usage count, success rate
5. Actionable insights: "Import error pattern 'circular dependency' detected 8x, consider architectural refactor"
```

---

## Acceptance Criteria

### Functional Requirements

#### Error Category Expansion
- [ ] **AC-1.1**: Type error healing: mypy violations auto-fixed (missing type annotations, wrong types, generic errors)
- [ ] **AC-1.2**: Import error healing: circular dependencies, missing imports, unused imports auto-fixed
- [ ] **AC-1.3**: Style violation healing: PEP 8, ruff violations auto-fixed (line length, naming, formatting)
- [ ] **AC-1.4**: Security issue healing: SQL injection, XSS, hardcoded secrets detected and fixed (with human approval for HIGH severity)
- [ ] **AC-1.5**: Performance anti-pattern healing: N+1 queries, inefficient loops, redundant operations detected and fixed
- [ ] **AC-1.6**: Logic error detection: basic logic issues flagged for human review (e.g., unreachable code, infinite loops)

#### Proactive Static Analysis
- [ ] **AC-2.1**: Pre-commit hook: runs static analysis before every commit (mypy, ruff, bandit)
- [ ] **AC-2.2**: Scheduled scanning: daily/weekly scans via GitHub Actions or cron
- [ ] **AC-2.3**: On-demand scanning: `agency heal --scan` triggers full codebase analysis
- [ ] **AC-2.4**: Incremental scanning: only scan changed files for fast feedback (<10 seconds)
- [ ] **AC-2.5**: Issue prioritization: P0 (security), P1 (errors), P2 (warnings), P3 (style)

#### Real-Time Healing Dashboard
- [ ] **AC-3.1**: CLI dashboard: `agency healing-dashboard` shows live terminal UI with healing metrics
- [ ] **AC-3.2**: Web dashboard: Optional web UI at `localhost:8080/healing` with real-time updates
- [ ] **AC-3.3**: Metrics displayed: active heals, success rate (1h/24h/7d), error distribution, pattern reuse rate
- [ ] **AC-3.4**: Drill-down views: click error category → see all instances with details (file, line, fix applied)
- [ ] **AC-3.5**: Historical trends: line charts showing healing success rate over time, error frequency trends

#### Pattern Learning & Reuse
- [ ] **AC-4.1**: Successful heals auto-extracted to VectorStore with metadata (error type, fix pattern, context)
- [ ] **AC-4.2**: Pattern matching: before generating new fix, query VectorStore for similar errors (semantic search)
- [ ] **AC-4.3**: Pattern confidence: high-confidence patterns (90%+ success rate) applied automatically, low-confidence prompt user
- [ ] **AC-4.4**: Pattern refinement: patterns updated with new successful heals, failure patterns removed
- [ ] **AC-4.5**: Pattern library: `docs/patterns/healing/` contains human-readable pattern documentation

#### Parallel Healing Integration
- [ ] **AC-5.1**: Multiple errors healed concurrently via parallel execution orchestrator (spec-015)
- [ ] **AC-5.2**: Failure isolation: one heal failure doesn't abort other concurrent heals
- [ ] **AC-5.3**: Dependency detection: dependent fixes executed sequentially (e.g., import before usage)
- [ ] **AC-5.4**: Resource limits: max 5 concurrent heals to avoid API rate limits

### Non-Functional Requirements

#### Performance
- [ ] **AC-P.1**: Static analysis scan: <10 seconds for incremental (changed files), <2 minutes for full codebase
- [ ] **AC-P.2**: Healing latency: <30 seconds per error (detection → fix → verification)
- [ ] **AC-P.3**: Dashboard refresh: real-time updates via WebSocket or 1-second polling
- [ ] **AC-P.4**: Pattern query: <100ms to search VectorStore for matching patterns

#### Reliability
- [ ] **AC-R.1**: Healing success rate: 95%+ across all error categories (measured over 100 heals)
- [ ] **AC-R.2**: Rollback on failure: 100% of failed heals automatically rolled back
- [ ] **AC-R.3**: False positive rate: <5% for security/performance issues (minimize unnecessary fixes)
- [ ] **AC-R.4**: Test verification: 100% of heals verify with full test suite before committing

#### Safety
- [ ] **AC-S.1**: Human approval required: security issues (HIGH severity), performance changes (>10% impact)
- [ ] **AC-S.2**: Audit trail: all heals logged to `logs/autonomous_healing/` with before/after diffs
- [ ] **AC-S.3**: Emergency stop: `agency healing stop` immediately halts all healing operations
- [ ] **AC-S.4**: Dry-run mode: `agency heal --dry-run` shows proposed fixes without applying

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [ ] **AC-CI.1**: Static analysis gathers complete file context before proposing fixes
- [ ] **AC-CI.2**: Pattern matching includes historical context from VectorStore
- [ ] **AC-CI.3**: No healing proceeds without full error analysis and fix validation

#### Article II: 100% Verification and Stability
- [ ] **AC-CII.1**: All heals verified with full test suite (100% pass required)
- [ ] **AC-CII.2**: Healing infrastructure has 100% test coverage
- [ ] **AC-CII.3**: No heal committed without green tests (automatic rollback on failure)

#### Article III: Automated Merge Enforcement
- [ ] **AC-CIII.1**: Pre-commit hook enforces healing before commit (no manual bypass)
- [ ] **AC-CIII.2**: CI pipeline validates healing results (no merge with unhealed errors)

#### Article IV: Continuous Learning and Improvement
- [ ] **AC-CIV.1**: 100% of successful heals stored in VectorStore for learning
- [ ] **AC-CIV.2**: Pattern reuse rate tracked and optimized (target: 60%+)
- [ ] **AC-CIV.3**: Healing effectiveness metrics inform future improvements

#### Article V: Spec-Driven Development
- [ ] **AC-CV.1**: This specification drives all expanded healing implementation
- [ ] **AC-CV.2**: Healing patterns documented in spec-kit format

---

## Dependencies & Constraints

### System Dependencies
- **mypy**: Type checking and error detection
- **ruff**: Style and linting analysis
- **bandit**: Security vulnerability scanning
- **VectorStore**: Pattern storage and semantic search
- **Parallel Executor (spec-015)**: Concurrent healing operations

### External Dependencies
- **OpenAI API**: LLM-powered fix generation for complex errors
- **GitHub Actions**: Scheduled scanning and CI integration
- **Rich (Python)**: Terminal UI for CLI dashboard
- **Flask/FastAPI**: Optional web dashboard backend

### Technical Constraints
- **Pattern Storage**: VectorStore embedding limits (max ~8000 tokens per pattern)
- **API Rate Limits**: Max 5 concurrent LLM calls for healing
- **Scan Performance**: Full codebase scan must complete in <2 minutes
- **Backward Compatibility**: Healing must work with existing NoneType healing infrastructure

### Business Constraints
- **Cost Control**: LLM costs for healing <$10/month (monitor API usage)
- **User Trust**: High severity changes require human approval (security, performance)
- **Incremental Rollout**: New error categories enabled progressively (type → import → style → security → performance)

---

## Risk Assessment

### High Risk Items
- **Risk 1**: False positive heals introduce bugs instead of fixing them - *Mitigation*: High test coverage, pattern confidence thresholds, rollback on test failure
- **Risk 2**: Security fixes applied automatically without review create vulnerabilities - *Mitigation*: Human approval required for HIGH severity security issues, audit trail

### Medium Risk Items
- **Risk 3**: Parallel healing creates merge conflicts or inconsistent state - *Mitigation*: Dependency detection, sequential execution for dependent fixes
- **Risk 4**: Pattern learning creates overfitting (patterns don't generalize) - *Mitigation*: Pattern confidence scoring, periodic pattern pruning, semantic similarity validation

### Constitutional Risks
- **Constitutional Risk 1**: Article II violation if heals bypass test verification - *Mitigation*: 100% test verification before any heal commit
- **Constitutional Risk 2**: Article IV violation if patterns not stored/reused - *Mitigation*: Automated pattern extraction, mandatory VectorStore integration

---

## Integration Points

### Agent Integration
- **QualityEnforcerAgent**: Orchestrates expanded healing across all error categories
- **LearningAgent**: Extracts and refines healing patterns from successful operations
- **AgencyCodeAgent**: Receives proactive healing feedback during code generation
- **AuditorAgent**: Triggers healing based on static analysis findings

### System Integration
- **VectorStore**: Stores and retrieves healing patterns for reuse
- **Telemetry**: Logs all healing operations for observability and metrics
- **Workflow State (spec-015)**: Healing operations checkpointed for resumability
- **CI/CD Pipeline**: Pre-commit hooks and GitHub Actions integration

### External Integration
- **mypy**: Type error detection via command-line invocation
- **ruff**: Style/linting via command-line invocation
- **bandit**: Security scanning via command-line invocation
- **GitHub**: Pre-commit hooks, Actions workflows, PR comments with healing summaries

---

## Testing Strategy

### Test Categories
- **Unit Tests**: Each error category healer tested independently (type, import, style, security, performance)
- **Integration Tests**: End-to-end healing workflow (detect → analyze → fix → verify → commit)
- **Pattern Learning Tests**: Pattern extraction, storage, retrieval, confidence scoring
- **Dashboard Tests**: CLI and web dashboard functionality, real-time updates
- **Constitutional Compliance Tests**: All 5 articles verified in healing operations

### Test Data Requirements
- **Error Fixtures**: Sample files with known errors for each category (type, import, style, security, performance)
- **Pattern Fixtures**: Known healing patterns with success rates for testing pattern matching
- **False Positive Cases**: Intentionally ambiguous errors to test precision

### Test Environment Requirements
- **Mock LLM**: Simulated fix generation for fast, deterministic tests
- **Test Repository**: Isolated git repository for testing healing without affecting production code
- **CI Simulation**: Local GitHub Actions runner for testing CI integration

---

## Implementation Phases

### Phase 1: Type Error Healing (Week 1-2)
- **Scope**: Extend healing to mypy type errors (missing annotations, wrong types)
- **Deliverables**:
  - `tools/auto_fix_type_errors.py` tool
  - Type error pattern library
  - Integration with QualityEnforcerAgent
- **Success Criteria**: 95%+ success rate on type error healing

### Phase 2: Import & Style Healing (Week 3-4)
- **Scope**: Add import error and style violation healing (ruff integration)
- **Deliverables**:
  - `tools/auto_fix_import_errors.py` tool
  - `tools/auto_fix_style_violations.py` tool
  - Pattern extraction for import/style errors
- **Success Criteria**: 95%+ success rate on import and style healing

### Phase 3: Proactive Static Analysis (Week 5)
- **Scope**: Add pre-commit hook and scheduled scanning
- **Deliverables**:
  - `.pre-commit-config.yaml` update with healing hooks
  - `.github/workflows/healing-scan.yml` for scheduled scanning
  - Incremental scan optimization
- **Success Criteria**: 80%+ issues caught before runtime

### Phase 4: Pattern Learning & Dashboard (Week 6-7)
- **Scope**: Build pattern learning system and real-time dashboard
- **Deliverables**:
  - VectorStore pattern extraction automation
  - CLI dashboard (`agency healing-dashboard`)
  - Optional web dashboard
- **Success Criteria**: 60%+ pattern reuse rate, real-time metrics visible

### Phase 5: Security & Performance Healing (Week 8)
- **Scope**: Add security vulnerability and performance anti-pattern healing
- **Deliverables**:
  - `tools/auto_fix_security_issues.py` with bandit integration
  - `tools/auto_fix_performance_issues.py` for N+1 queries, inefficiencies
  - Human approval workflow for HIGH severity changes
- **Success Criteria**: Security/performance issues detected and fixed with 90%+ precision

---

## Review & Approval

### Stakeholders
- **Primary Stakeholder**: @am (Project Owner)
- **Secondary Stakeholders**: QualityEnforcerAgent, AgencyCodeAgent (healing participants)
- **Technical Reviewers**: LearningAgent (pattern validation), AuditorAgent (quality assurance)

### Review Criteria
- [ ] **Completeness**: All 6 error categories addressed with healing strategies
- [ ] **Clarity**: Healing workflows and pattern learning clearly defined
- [ ] **Feasibility**: Proactive scanning and parallel healing technically viable
- [ ] **Constitutional Compliance**: All 5 articles supported by implementation
- [ ] **Quality Standards**: Meets Agency's 95%+ healing success rate requirement

### Approval Status
- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending agent validation
- [ ] **Constitutional Compliance**: Pending article verification
- [ ] **Final Approval**: Pending all above approvals

---

## Appendices

### Appendix A: Glossary
- **Autonomous Healing**: Automated detection, analysis, fixing, and verification of code quality issues
- **Proactive Healing**: Static analysis-based error detection before runtime
- **Pattern Learning**: Extracting successful healing strategies to VectorStore for reuse
- **Healing Dashboard**: Real-time UI displaying healing operations and metrics

### Appendix B: References
- **ADR-002**: 100% Verification and Stability (drives test verification requirement)
- **ADR-004**: Continuous Learning and Improvement (drives pattern learning requirement)
- **spec-015**: Workflow State Persistence (provides parallel execution primitives)
- **Article II**: 100% test verification required for all heals

### Appendix C: Related Documents
- **tools/auto_fix_nonetype.py**: Existing NoneType healing implementation (template for expansion)
- **tools/apply_and_verify_patch.py**: Patch application and rollback infrastructure
- **core/self_healing.py**: Self-healing orchestration logic

### Appendix D: Error Category Definitions

| Category | Detection Tool | Example Errors | Healing Approach | Approval Required |
|----------|---------------|----------------|------------------|-------------------|
| **Type** | mypy | Missing annotations, wrong types | Add type hints, fix type mismatches | No (auto) |
| **Import** | ruff, custom | Circular dependencies, unused imports | Restructure imports, remove unused | No (auto) |
| **Style** | ruff | PEP 8 violations, formatting | Auto-format, fix naming | No (auto) |
| **Security** | bandit | SQL injection, XSS, secrets | Parameterize queries, sanitize inputs | Yes (HIGH) |
| **Performance** | custom | N+1 queries, inefficient loops | Batch operations, optimize algorithms | Yes (>10% impact) |
| **Logic** | custom | Unreachable code, infinite loops | Flag for human review | Yes (always) |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-02 | QualityEnforcerAgent | Initial specification for expanded autonomous healing system |

---

*"A specification is a contract between intention and implementation."*
