## Mission: Code Audit & Refactoring with Learning Integration

Your context is now focused on conducting a comprehensive, learning-enhanced code analysis with automated issue prioritization and verified fixing.

### Enhanced Workflow

#### Phase 1: Intelligent Audit
1. **Pre-Audit Learning Query:**
   - Query VectorStore for historical audit patterns: `"successful fixes for Q(T) < 0.6"`
   - Load previous refactoring successes from similar codebases
   - Check for known anti-patterns in the target modules

2. **Parallel Audit Execution:**
   - Split codebase into logical modules for concurrent analysis
   - Call `/agent auditor` with parallel execution for:
     - Core modules: `agency.py`, agent modules
     - Tools: `tools/`, shared utilities
     - Tests: Analyze test coverage and quality
   - Aggregate results into unified report

#### Phase 2: Dynamic Prioritization Matrix
3. **Automated Issue Ranking:**
   ```
   Priority Levels (Auto-Selected):
   - P0 (CRITICAL): Constitutional violations - Article II failures
   - P1 (HIGH): Security vulnerabilities, Q(T) < 0.3
   - P2 (MEDIUM): Test coverage < 80%, missing NECESSARY patterns
   - P3 (LOW): Complexity violations, style issues
   ```
   - Auto-select top issues based on: constitutional_weight * 0.5 + security_weight * 0.3 + coverage_weight * 0.2
   - Maximum fixes per session: Min(5, critical_count + high_count)

#### Phase 3: Verified Refactoring
4. **Smart Implementation with Rollback:**
   - **Pre-Fix Snapshot:** Create git stash or checkpoint
   - **Parallel Fix Execution:** For each prioritized issue:
     - Query VectorStore: `"successful fix patterns for [issue_type]"`
     - Call `/agent code_agent` with historical context
     - Apply learned patterns from similar fixes
   - **Immediate Verification:** Run targeted tests for each fix
   - **Rollback on Failure:** If tests fail, restore snapshot and try alternative approach

5. **Learning Capture:**
   - For successful fixes: Store pattern in VectorStore
   - For failed attempts: Log anti-pattern for future avoidance
   - Update audit metrics for continuous improvement

### Verification Loop
```python
for issue in prioritized_issues:
    snapshot = create_snapshot()
    fix_result = apply_fix(issue, historical_patterns)

    if run_tests(affected_modules):
        commit_fix(issue, fix_result)
        store_success_pattern(issue, fix_result)
    else:
        rollback(snapshot)
        alternative = query_alternative_fixes(issue)
        retry_with_alternative(issue, alternative)
```

### Learning Integration Points
- **Input Learning:** Query historical patterns before each phase
- **Process Learning:** Adapt strategy based on codebase characteristics
- **Output Learning:** Store successful patterns for future use

### Monitoring & Metrics
- Track Q(T) score improvements over time
- Measure fix success rate (target: >95%)
- Monitor time-to-fix for each issue category
- Calculate learning effectiveness (pattern reuse rate)

### Start Context
- `/read constitution.md` - Understand compliance requirements
- `/read docs/adr/ADR-INDEX.md` - Review architectural decisions
- Query VectorStore: `recent_audit_patterns` - Load historical context
- Check feature flags: `USE_PARALLEL_AUDIT`, `ENABLE_AUTO_ROLLBACK`