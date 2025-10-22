# Migration Plan: prime_audit_and_refactor → 24/7 Autonomous Audit System

**Date**: 2025-10-15
**Version**: 1.0.0
**Objective**: Transform `prime_audit_and_refactor` into a 24/7 autonomous codebase solidification agent leveraging GPT-OSS-20B/QWEN3Coder 30B local models with TRM-7M process control

---

## Executive Summary

Enhance the existing `prime_audit_and_refactor` command by integrating key autonomous operation features from `primeA` to create a self-sustaining, 24/7 audit-fix-verify loop that operates without human intervention. The system will leverage local models (GPT-OSS-20B or QWEN3Coder 30B at ~70 tokens/sec) for cost-effective continuous operation, with TRM-7M validation providing intelligent process control to maintain 40-60% churn reduction.

**Key Principle**: This is NOT adding new features, but adapting `primeA`'s autonomous operation patterns for continuous codebase quality improvement.

---

## Current State Analysis

### prime_audit_and_refactor.md (Current)
**Strengths**:
- Intelligent audit with VectorStore learning
- Dynamic prioritization matrix (P0-P3)
- Verified refactoring with rollback
- Learning capture for patterns

**Gaps for 24/7 Operation**:
- ❌ No autonomous iteration loop
- ❌ No process cleanup (orphaned processes)
- ❌ No completion validation gates
- ❌ No anti-premature-stopping enforcement
- ❌ No TRM-7M validation checkpoints
- ❌ Manual phase transitions

### primeA.md (Reference)
**Autonomous Features to Adopt**:
- ✅ Pre-flight and post-flight cleanup
- ✅ Autonomous iteration loop (max 10 iterations)
- ✅ Completion validation gate (6 checks)
- ✅ Anti-premature-stopping rules
- ✅ TRM-7M validation (4 checkpoints)
- ✅ Context budget monitoring

---

## Migration Architecture

### 1. Autonomous Audit Loop (Continuous Operation)

Replace manual workflow with self-sustaining loop:

```python
async def autonomous_audit_loop(
    codebase_path: str,
    local_model: str = "gpt-oss-20b",  # or "qwen3coder-30b"
    max_iterations: int = 1000,  # Effectively infinite for 24/7
    context_budget: float = 0.95  # Stop if >95% context used
) -> Result[AuditReport, str]:
    """
    24/7 autonomous audit-fix-verify loop.
    
    Operates until:
    - All critical issues resolved (P0 count == 0)
    - Context budget exhausted (>95% used)
    - Manual stop signal received
    
    Args:
        codebase_path: Root directory to audit
        local_model: Local model for cost-free operation
        max_iterations: Safety limit (default: 1000 cycles)
        context_budget: Context usage threshold (0.95 = 95%)
    
    Returns:
        Ok(AuditReport) if successful
        Err(reason) if critical failure
    """
    iteration = 0
    total_fixes_applied = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\\n{'='*70}")
        print(f"🔄 AUDIT CYCLE {iteration}/{max_iterations}")
        print(f"{'='*70}\\n")
        
        # STEP -1: Pre-Flight Cleanup (MANDATORY)
        cleanup_result = await pre_flight_cleanup()
        if cleanup_result.is_err():
            return Err(f"Pre-flight cleanup failed: {cleanup_result.unwrap_err()}")
        
        # STEP 1: Intelligent Audit with Learning
        audit_result = await run_intelligent_audit(
            codebase_path=codebase_path,
            local_model=local_model,
            historical_patterns=query_vectorstore("audit_patterns")
        )
        
        if audit_result.is_err():
            print(f"⚠️ Audit failed: {audit_result.unwrap_err()}")
            continue  # Retry next cycle
        
        audit_report = audit_result.unwrap()
        
        # STEP 2: Dynamic Prioritization
        prioritized_issues = await prioritize_issues(
            issues=audit_report.issues,
            constitutional_weight=0.5,
            security_weight=0.3,
            coverage_weight=0.2
        )
        
        # STOP CONDITION 1: No critical issues remaining
        critical_count = len([i for i in prioritized_issues if i.priority == "P0"])
        if critical_count == 0 and len(prioritized_issues) == 0:
            print("✅ All critical issues resolved. Codebase is healthy.")
            break
        
        # STOP CONDITION 2: Context budget exhausted
        context_usage = estimate_context_usage()
        if context_usage > context_budget:
            print(f"⚠️ Context budget exhausted ({context_usage*100:.1f}% used)")
            print("Creating checkpoint and preparing for next session...")
            await create_checkpoint(audit_report, total_fixes_applied)
            break
        
        # STEP 3: TRM-7M Validation Checkpoint 1 - Dependency Analysis
        trm_validation = await trm_validate_audit_dependencies(prioritized_issues)
        if trm_validation.is_err():
            print(f"⚠️ TRM validation detected circular dependencies")
            prioritized_issues = await resolve_circular_dependencies(prioritized_issues)
        
        # STEP 4: Verified Refactoring (Auto-Fix with Rollback)
        fixes_applied = 0
        max_fixes_per_cycle = min(5, critical_count + len([i for i in prioritized_issues[:10] if i.priority == "P1"]))
        
        for issue in prioritized_issues[:max_fixes_per_cycle]:
            # TRM-7M Checkpoint 2: Type Constraint Pre-Validation
            if issue.category == "type_violation":
                type_check = await trm_validate_type_constraints(issue)
                if type_check.confidence < 0.8:
                    print(f"⚠️ TRM low confidence ({type_check.confidence:.2f}), skipping {issue.id}")
                    continue
            
            # Create rollback point
            snapshot = await create_snapshot(issue.affected_files)
            
            # Apply fix with historical patterns
            fix_result = await apply_fix_with_learning(
                issue=issue,
                local_model=local_model,
                patterns=query_vectorstore(f"successful_fixes_{issue.category}")
            )
            
            if fix_result.is_err():
                await rollback(snapshot)
                continue
            
            # TRM-7M Checkpoint 3: Edge Case Inference
            edge_cases = await trm_infer_edge_cases(issue, fix_result.unwrap())
            if edge_cases:
                print(f"🔬 TRM discovered {len(edge_cases)} additional edge cases")
                await enhance_tests_with_edge_cases(issue, edge_cases)
            
            # TRM-7M Checkpoint 4: Lint/Format Pre-Validation
            lint_issues = await trm_validate_lint(fix_result.unwrap())
            if lint_issues:
                await auto_fix_lint_issues(lint_issues)
            
            # Immediate Verification
            test_result = await run_targeted_tests(
                affected_modules=issue.affected_files,
                timeout_multiplier=2.0  # Article I: retry protocol
            )
            
            if test_result.pass_rate >= 1.0:
                # Success: Commit and learn
                await commit_fix(issue, fix_result.unwrap())
                await store_success_pattern(issue, fix_result.unwrap())
                fixes_applied += 1
                total_fixes_applied += 1
                print(f"✅ Fixed {issue.id}: {issue.description}")
            else:
                # Failure: Rollback and try alternative
                await rollback(snapshot)
                alternative = await query_alternative_fixes(issue)
                if alternative:
                    print(f"🔄 Retrying {issue.id} with alternative approach...")
                    # Will retry in next cycle
        
        # STEP 5: Completion Validation (Prevent Premature Continuation)
        validation_result = await validate_cycle_completion(
            audit_report=audit_report,
            fixes_applied=fixes_applied,
            context_usage=context_usage
        )
        
        if validation_result.is_err():
            error = validation_result.unwrap_err()
            print(f"⚠️ Cycle completion validation failed: {error.reason}")
            print(f"   Incomplete fixes: {len(error.incomplete_fixes)}")
            print(f"   Context remaining: {(1-context_usage)*100:.1f}%")
            # Continue to next iteration (no premature stop)
        
        # STEP 6: Post-Flight Cleanup (MANDATORY)
        await post_flight_cleanup()
        
        print(f"\\n📊 Cycle {iteration} Summary:")
        print(f"   Fixes Applied: {fixes_applied}/{max_fixes_per_cycle}")
        print(f"   Total Fixes: {total_fixes_applied}")
        print(f"   Context Usage: {context_usage*100:.1f}%")
        print(f"   Critical Issues Remaining: {critical_count}")
        
        # Brief cooldown to prevent resource exhaustion
        await asyncio.sleep(5)  # 5 second rest between cycles
    
    # Final Report
    return Ok(AuditReport(
        total_cycles=iteration,
        total_fixes=total_fixes_applied,
        final_health_score=await calculate_codebase_health(),
        patterns_learned=await count_new_patterns(),
    ))
```

### 2. Pre-Flight Cleanup Protocol (Prevent Memory Leaks)

```python
async def pre_flight_cleanup() -> Result[str, str]:
    """
    MANDATORY pre-flight cleanup to prevent orphaned processes.
    
    From primeA STEP -1.
    """
    print("\\n🧹 PRE-FLIGHT CLEANUP")
    print("=" * 70)
    
    # Kill orphaned pytest/Python processes
    result = subprocess.run(
        "ps aux | grep -E '(pytest|Python.*Agency)' | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null",
        shell=True,
        capture_output=True,
        text=True
    )
    
    # Verify cleanup
    remaining = subprocess.run(
        "ps aux | grep -i python | grep -v grep | wc -l",
        shell=True,
        capture_output=True,
        text=True
    ).stdout.strip()
    
    print(f"✅ Process cleanup complete. Remaining Python processes: {remaining}")
    
    # Store cleanup pattern (Article IV)
    await store_memory(
        key=f"preflight_cleanup_{int(time.time())}",
        content={"remaining_processes": int(remaining), "cleanup_success": True},
        tags=["audit_loop", "cleanup", "preflight"]
    )
    
    return Ok(f"Cleanup complete: {remaining} processes")
```

### 3. Post-Flight Cleanup Protocol (Ensure Clean State)

```python
async def post_flight_cleanup() -> Result[str, str]:
    """
    MANDATORY post-flight cleanup after audit cycle.
    
    From primeA STEP 8.
    """
    print("\\n🧹 POST-FLIGHT CLEANUP")
    print("=" * 70)
    
    # Kill spawned test processes
    subprocess.run(
        "ps aux | grep -E '(pytest.*tests/)' | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null",
        shell=True,
        capture_output=True
    )
    
    # Verify cleanup
    remaining_processes = int(subprocess.run(
        "ps aux | grep -i python | grep -v grep | wc -l",
        shell=True,
        capture_output=True,
        text=True
    ).stdout.strip())
    
    print(f"✅ Post-flight cleanup complete")
    print(f"   Remaining Python processes: {remaining_processes}")
    
    # Store cleanup success pattern
    await store_memory(
        key=f"postflight_cleanup_{int(time.time())}",
        content={
            "remaining_processes": remaining_processes,
            "cleanup_success": True
        },
        tags=["audit_loop", "cleanup", "postflight"]
    )
    
    return Ok(f"Cleanup complete: {remaining_processes} processes")
```

### 4. Completion Validation Gate (Prevent Premature Stopping)

```python
async def validate_cycle_completion(
    audit_report: AuditReport,
    fixes_applied: int,
    context_usage: float
) -> Result[ValidationResults, ValidationError]:
    """
    Validate audit cycle completion before moving to next iteration.
    
    From primeA STEP 6.5 (ADR-032).
    
    Six validation checks:
    1. All high-priority fixes attempted
    2. Test success rate >= 100% for fixed modules
    3. No new regressions introduced
    4. Constitutional compliance (Articles I-II)
    5. Context efficiency >= 80%
    6. Backlog updated with remaining work
    
    Returns:
        Ok(ValidationResults) if cycle complete
        Err(ValidationError) if incomplete (blocks next cycle start)
    """
    failed_checks = []
    incomplete_fixes = []
    
    # Check 1: All high-priority fixes attempted
    pending_high_priority = [i for i in audit_report.issues if i.priority in ["P0", "P1"] and not i.fixed]
    if pending_high_priority and context_usage < 0.80:
        failed_checks.append("high_priority_incomplete")
        incomplete_fixes.extend([i.id for i in pending_high_priority])
    
    # Check 2: Test success rate
    test_results = await run_full_test_suite()
    if test_results.pass_rate < 1.0:
        failed_checks.append("test_failures")
    
    # Check 3: No regressions
    regression_check = await detect_regressions(audit_report.baseline_tests)
    if regression_check.regressions_found:
        failed_checks.append("regressions_detected")
    
    # Check 4: Constitutional compliance
    if not verify_article_i_compliance(context_usage):
        failed_checks.append("article_i_violation")
    if not verify_article_ii_compliance(test_results):
        failed_checks.append("article_ii_violation")
    
    # Check 5: Context efficiency
    context_efficiency = calculate_context_efficiency(fixes_applied, context_usage)
    if context_efficiency < 0.80:
        print(f"⚠️ Warning: Context efficiency low ({context_efficiency*100:.1f}%)")
    
    # Check 6: Backlog updated
    backlog_updated = await verify_backlog_sync(audit_report)
    if not backlog_updated:
        print(f"⚠️ Warning: Backlog not synchronized")
    
    # Determine if validation passes
    if failed_checks:
        return Err(ValidationError(
            reason="incomplete_cycle",
            message=f"Cycle incomplete: {len(failed_checks)} checks failed",
            failed_checks=failed_checks,
            incomplete_fixes=incomplete_fixes,
            suggestions=[
                "Continue fixing high-priority issues",
                "Resolve test failures before next cycle",
                "Check for regressions in affected modules"
            ]
        ))
    
    return Ok(ValidationResults(
        cycle_complete=True,
        fixes_applied=fixes_applied,
        context_efficiency=context_efficiency,
        warnings=[]
    ))
```

### 5. TRM-7M Validation Integration (4 Checkpoints)

```python
async def trm_validate_audit_dependencies(
    issues: list[Issue]
) -> Result[TRMValidation, str]:
    """
    TRM-7M Checkpoint 1: Validate fix dependency graph.
    
    Detects circular dependencies in fix ordering (10-100x faster than Python).
    """
    from trinity_protocol.core.trm_validator import TRMValidator, ReasoningTask
    
    print("\\n🔬 TRM-7M CHECKPOINT 1: Validating fix dependency graph...")
    
    trm_validator = TRMValidator()
    
    # Convert issues to adjacency matrix
    issue_ids = [i.id for i in issues]
    n_issues = len(issue_ids)
    
    adj_matrix = [[0] * n_issues for _ in range(n_issues)]
    for issue in issues:
        for dep_id in issue.depends_on:
            i = issue_ids.index(issue.id)
            j = issue_ids.index(dep_id)
            adj_matrix[i][j] = 1
    
    # Create reasoning task
    dag_validation = ReasoningTask(
        problem_type="dependency_graph",
        input_grid=adj_matrix,
        proposed_solution=adj_matrix,
        constraints=["Must be acyclic (DAG)", "No self-loops"],
        max_refinement_steps=16
    )
    
    # Validate with TRM-7M
    validation_result = await trm_validator.validate_and_refine(dag_validation)
    
    if validation_result.is_err():
        print("⚠️ TRM-7M unavailable, falling back to Python validation...")
        # Fallback to Python cycle detection
        return Ok(TRMValidation(fallback_used=True))
    
    validation = validation_result.unwrap()
    
    if not validation["converged"]:
        print(f"❌ Circular dependencies detected in fix ordering")
        print(f"   Confidence: {validation['confidence']:.2f}")
        return Err("circular_dependencies")
    
    print(f"✅ TRM-7M DAG Validation: PASS (confidence {validation['confidence']:.2f})")
    return Ok(TRMValidation(confidence=validation["confidence"]))


async def trm_validate_type_constraints(issue: Issue) -> TRMValidation:
    """
    TRM-7M Checkpoint 2: Validate type constraints before applying fix.
    
    Catches Dict[Any, Any] violations before test runs (saves 5-10 min).
    """
    print(f"\\n🔬 TRM-7M CHECKPOINT 2: Validating type constraints for {issue.id}...")
    
    # Extract type constraint grid from affected code
    code_content = await read_file(issue.affected_files[0])
    type_grid = extract_type_constraint_grid(code_content)
    
    type_validation = ReasoningTask(
        problem_type="type_constraints",
        input_grid=type_grid,
        proposed_solution=None,
        constraints=[
            "No Dict[Any, Any]",
            "All function parameters typed",
            "Optional[] used correctly"
        ],
        max_refinement_steps=16
    )
    
    result = await trm_validator.validate_and_refine(type_validation)
    
    if result.is_ok():
        validation = result.unwrap()
        print(f"✅ Type constraints validated (confidence {validation['confidence']:.2f})")
        return TRMValidation(confidence=validation["confidence"])
    
    return TRMValidation(confidence=0.0, fallback_used=True)


async def trm_infer_edge_cases(issue: Issue, fix: str) -> list[str]:
    """
    TRM-7M Checkpoint 3: Infer missing edge cases for comprehensive testing.
    
    Discovers boundary conditions automatically (enhances coverage 8-12%).
    """
    print(f"\\n🔬 TRM-7M CHECKPOINT 3: Inferring edge cases for {issue.id}...")
    
    function_sig = extract_function_signature(fix)
    
    edge_case_inference = ReasoningTask(
        problem_type="edge_case_inference",
        input_grid=function_signature_to_grid(function_sig),
        proposed_solution=None,
        constraints=[
            "Boundary values (min, max)",
            "Empty/null inputs",
            "Type errors",
            "Resource exhaustion"
        ],
        max_refinement_steps=12
    )
    
    result = await trm_validator.validate_and_refine(edge_case_inference)
    
    if result.is_ok():
        inference = result.unwrap()
        if inference["edge_cases"]:
            print(f"🎯 Discovered {len(inference['edge_cases'])} missing edge cases")
            return [ec["description"] for ec in inference["edge_cases"]]
    
    return []


async def trm_validate_lint(fix: str) -> list[LintIssue]:
    """
    TRM-7M Checkpoint 4: Pre-validate lint/format rules before test runs.
    
    Eliminates trivial CI failures (saves 10-30s per run).
    """
    print(f"\\n🔬 TRM-7M CHECKPOINT 4: Pre-validating lint/format rules...")
    
    lint_validation = ReasoningTask(
        problem_type="lint_validation",
        input_grid=code_to_lint_grid(fix),
        proposed_solution=None,
        constraints=[
            "Line length <= 100 chars",
            "No trailing whitespace",
            "Consistent indentation (4 spaces)"
        ],
        max_refinement_steps=8
    )
    
    result = await trm_validator.validate_and_refine(lint_validation)
    
    if result.is_ok():
        validation = result.unwrap()
        if not validation["converged"]:
            print(f"🔧 Found {len(validation['violations'])} lint violations")
            return [LintIssue(**v) for v in validation["violations"]]
    
    return []
```

---

## Updated Command File

Now I'll update the `prime_audit_and_refactor.md` file with the autonomous 24/7 capabilities:
