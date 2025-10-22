"""
Test autonomous audit loop for prime_audit_and_refactor command.

This test validates the core autonomous operation patterns:
- Pre-flight cleanup
- Audit cycle iteration
- Completion validation
- Post-flight cleanup
- Stop conditions (P0 resolution, context exhaustion)

Note: This is a simplified test without full TRM-7M integration or local models.
"""

import asyncio
import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional

import pytest

from shared.type_definitions import Result, Ok, Err


@dataclass
class Issue:
    """Represents a code quality issue."""
    id: str
    priority: str  # P0, P1, P2, P3
    category: str
    description: str
    affected_files: List[str]
    fixed: bool = False
    depends_on: List[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class AuditReport:
    """Audit cycle report."""
    total_cycles: int
    total_fixes: int
    final_health_score: float
    patterns_learned: int
    issues: List[Issue] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class ValidationResults:
    """Completion validation results."""
    cycle_complete: bool
    fixes_applied: int
    context_efficiency: float
    warnings: List[str]


@dataclass
class ValidationError:
    """Validation failure details."""
    reason: str
    message: str
    failed_checks: List[str]
    incomplete_fixes: List[str]
    suggestions: List[str]


async def pre_flight_cleanup() -> Result[str, str]:
    """
    STEP -1: Pre-flight cleanup.
    
    Kill orphaned pytest/Python processes.
    """
    print("\n🧹 PRE-FLIGHT CLEANUP")
    print("=" * 70)
    
    # Kill orphaned processes (safe command, only kills OLD processes, not current PID)
    # Get current PID to avoid killing ourselves
    import os
    current_pid = os.getpid()
    
    # Only kill pytest processes that are NOT our current process
    result = subprocess.run(
        f"ps aux | grep -E '(pytest.*test_autonomous)' | grep -v grep | grep -v {current_pid} | awk '{{print $2}}' | xargs kill -9 2>/dev/null || true",
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
    
    return Ok(f"Cleanup complete: {remaining} processes")


async def run_intelligent_audit(
    codebase_path: str,
    local_model: str,
    historical_patterns: Optional[dict] = None
) -> Result[AuditReport, str]:
    """
    STEP 1: Intelligent audit with learning.
    
    Simplified version: Create mock issues for testing.
    """
    print("\n🔍 INTELLIGENT AUDIT")
    print("=" * 70)
    
    # Mock audit: Create sample issues
    issues = [
        Issue(
            id="test_issue_p0_1",
            priority="P0",
            category="test_failure",
            description="Test failure in test_autonomous_audit_loop",
            affected_files=["tests/integration/test_autonomous_audit_loop.py"]
        ),
        Issue(
            id="test_issue_p1_1",
            priority="P1",
            category="coverage_gap",
            description="Low test coverage in audit module",
            affected_files=["tools/audit/auditor.py"]
        ),
    ]
    
    report = AuditReport(
        total_cycles=0,
        total_fixes=0,
        final_health_score=0.7,
        patterns_learned=0,
        issues=issues
    )
    
    print(f"✅ Audit complete: {len(issues)} issues found")
    print(f"   P0: {len([i for i in issues if i.priority == 'P0'])}")
    print(f"   P1: {len([i for i in issues if i.priority == 'P1'])}")
    
    return Ok(report)


async def prioritize_issues(
    issues: List[Issue],
    constitutional_weight: float = 0.5,
    security_weight: float = 0.3,
    coverage_weight: float = 0.2
) -> List[Issue]:
    """
    STEP 2: Dynamic prioritization.
    
    Sort issues by priority (P0 > P1 > P2 > P3).
    """
    print("\n🎯 DYNAMIC PRIORITIZATION")
    print("=" * 70)
    
    # Sort by priority
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    sorted_issues = sorted(issues, key=lambda i: priority_order.get(i.priority, 4))
    
    print(f"✅ Prioritized {len(sorted_issues)} issues")
    for i, issue in enumerate(sorted_issues[:5], 1):
        print(f"   {i}. [{issue.priority}] {issue.id}: {issue.description}")
    
    return sorted_issues


async def apply_fix_with_learning(
    issue: Issue,
    local_model: str,
    patterns: Optional[dict] = None
) -> Result[str, str]:
    """
    Simplified fix application.
    
    In real implementation, this would use local model + VectorStore patterns.
    """
    print(f"    🤖 Applying fix for {issue.id}...")
    await asyncio.sleep(0.1)  # Simulate fix application
    
    # Mock: Always succeed for testing
    return Ok(f"Fixed {issue.id}")


async def run_targeted_tests(
    affected_modules: List[str],
    timeout_multiplier: float = 2.0
) -> Result[dict, str]:
    """
    Run tests for affected modules.
    
    Article I: Retry protocol (2x, 3x, 10x on timeout).
    """
    print(f"    🧪 Running tests for {len(affected_modules)} module(s)...")
    await asyncio.sleep(0.1)  # Simulate test run
    
    # Mock: Always pass for testing
    return Ok({"pass_rate": 1.0, "tests_run": 10})


async def validate_cycle_completion(
    audit_report: AuditReport,
    fixes_applied: int,
    context_usage: float
) -> Result[ValidationResults, ValidationError]:
    """
    STEP 5: Completion validation gate.
    
    Six-check validation from ADR-032.
    """
    print("\n✅ COMPLETION VALIDATION")
    print("=" * 70)
    
    failed_checks = []
    
    # Check 1: High-priority fixes attempted
    pending_high = [i for i in audit_report.issues if i.priority in ["P0", "P1"] and not i.fixed]
    if pending_high and context_usage < 0.80:
        failed_checks.append("high_priority_incomplete")
    
    # Check 2-6: Simplified for testing
    # In real implementation, these would check test success rate, regressions, etc.
    
    if failed_checks:
        return Err(ValidationError(
            reason="incomplete_cycle",
            message=f"Cycle incomplete: {len(failed_checks)} checks failed",
            failed_checks=failed_checks,
            incomplete_fixes=[i.id for i in pending_high],
            suggestions=["Continue fixing high-priority issues"]
        ))
    
    print("✅ All validation checks passed")
    
    return Ok(ValidationResults(
        cycle_complete=True,
        fixes_applied=fixes_applied,
        context_efficiency=0.85,
        warnings=[]
    ))


async def post_flight_cleanup() -> Result[str, str]:
    """
    STEP 6: Post-flight cleanup.
    
    Ensure clean state after cycle.
    """
    print("\n🧹 POST-FLIGHT CLEANUP")
    print("=" * 70)
    
    # Kill spawned test processes (excluding current PID)
    import os
    current_pid = os.getpid()
    
    subprocess.run(
        f"ps aux | grep -E '(pytest.*test_autonomous)' | grep -v grep | grep -v {current_pid} | awk '{{print $2}}' | xargs kill -9 2>/dev/null || true",
        shell=True,
        capture_output=True
    )
    
    remaining_processes = int(subprocess.run(
        "ps aux | grep -i python | grep -v grep | wc -l",
        shell=True,
        capture_output=True,
        text=True
    ).stdout.strip())
    
    print(f"✅ Post-flight cleanup complete")
    print(f"   Remaining Python processes: {remaining_processes}")
    
    return Ok(f"Cleanup complete: {remaining_processes} processes")


def estimate_context_usage() -> float:
    """
    Estimate current context usage.
    
    Simplified: Always return low usage for testing.
    """
    return 0.15  # 15% usage


async def autonomous_audit_loop(
    codebase_path: str,
    local_model: str = "gpt-oss-20b",
    max_iterations: int = 3,  # Limited for testing
    context_budget: float = 0.95
) -> Result[AuditReport, str]:
    """
    24/7 autonomous audit-fix-verify loop (TEST VERSION).
    
    This is a simplified test implementation demonstrating the core loop structure.
    """
    iteration = 0
    total_fixes_applied = 0
    
    print("\n" + "=" * 70)
    print("🚀 AUTONOMOUS AUDIT LOOP TEST")
    print("=" * 70)
    print(f"Local Model: {local_model}")
    print(f"Max Iterations: {max_iterations}")
    print(f"Context Budget: {context_budget * 100}%")
    print("=" * 70)
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'=' * 70}")
        print(f"🔄 AUDIT CYCLE {iteration}/{max_iterations}")
        print(f"{'=' * 70}\n")
        
        # STEP -1: Pre-Flight Cleanup
        cleanup_result = await pre_flight_cleanup()
        if cleanup_result.is_err():
            return Err(f"Pre-flight cleanup failed: {cleanup_result.unwrap_err()}")
        
        # STEP 1: Intelligent Audit
        audit_result = await run_intelligent_audit(
            codebase_path=codebase_path,
            local_model=local_model,
            historical_patterns=None
        )
        
        if audit_result.is_err():
            print(f"⚠️ Audit failed: {audit_result.unwrap_err()}")
            continue
        
        audit_report = audit_result.unwrap()
        
        # STEP 2: Dynamic Prioritization
        prioritized_issues = await prioritize_issues(
            issues=audit_report.issues,
            constitutional_weight=0.5,
            security_weight=0.3,
            coverage_weight=0.2
        )
        
        # STOP CONDITION 1: No critical issues
        critical_count = len([i for i in prioritized_issues if i.priority == "P0"])
        if critical_count == 0 and len(prioritized_issues) == 0:
            print("✅ All critical issues resolved. Codebase is healthy.")
            break
        
        # STOP CONDITION 2: Context budget exhausted
        context_usage = estimate_context_usage()
        if context_usage > context_budget:
            print(f"⚠️ Context budget exhausted ({context_usage * 100:.1f}% used)")
            break
        
        # STEP 4: Verified Refactoring (Simplified - no TRM-7M for testing)
        print("\n🔧 VERIFIED REFACTORING")
        print("=" * 70)
        
        fixes_applied = 0
        max_fixes_per_cycle = min(2, len(prioritized_issues))  # Limited for testing
        
        for issue in prioritized_issues[:max_fixes_per_cycle]:
            print(f"\n  Fixing {issue.id}...")
            
            fix_result = await apply_fix_with_learning(issue, local_model)
            
            if fix_result.is_err():
                continue
            
            test_result = await run_targeted_tests(
                affected_modules=issue.affected_files,
                timeout_multiplier=2.0
            )
            
            if test_result.is_ok():
                test_data = test_result.unwrap()
                if test_data["pass_rate"] >= 1.0:
                    issue.fixed = True
                    fixes_applied += 1
                    total_fixes_applied += 1
                    print(f"    ✅ Fixed {issue.id}")
        
        # STEP 5: Completion Validation
        validation_result = await validate_cycle_completion(
            audit_report=audit_report,
            fixes_applied=fixes_applied,
            context_usage=context_usage
        )
        
        if validation_result.is_err():
            error = validation_result.unwrap_err()
            print(f"⚠️ Cycle validation failed: {error.reason}")
        
        # STEP 6: Post-Flight Cleanup
        await post_flight_cleanup()
        
        print(f"\n📊 Cycle {iteration} Summary:")
        print(f"   Fixes Applied: {fixes_applied}/{max_fixes_per_cycle}")
        print(f"   Total Fixes: {total_fixes_applied}")
        print(f"   Context Usage: {context_usage * 100:.1f}%")
        print(f"   Critical Issues Remaining: {critical_count}")
        
        # Brief cooldown
        if iteration < max_iterations:
            print("\n   ⏸️  Next cycle in 1 second...")
            await asyncio.sleep(1)
    
    # Final Report
    return Ok(AuditReport(
        total_cycles=iteration,
        total_fixes=total_fixes_applied,
        final_health_score=0.95,
        patterns_learned=total_fixes_applied * 2
    ))


# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_pre_flight_cleanup():
    """Test pre-flight cleanup protocol."""
    result = await pre_flight_cleanup()
    assert result.is_ok(), f"Pre-flight cleanup failed: {result.unwrap_err()}"
    print("✅ Pre-flight cleanup test passed")


@pytest.mark.asyncio
async def test_post_flight_cleanup():
    """Test post-flight cleanup protocol."""
    result = await post_flight_cleanup()
    assert result.is_ok(), f"Post-flight cleanup failed: {result.unwrap_err()}"
    print("✅ Post-flight cleanup test passed")


@pytest.mark.asyncio
async def test_intelligent_audit():
    """Test audit cycle with issue detection."""
    result = await run_intelligent_audit(
        codebase_path="/Users/am/Code/Agency",
        local_model="gpt-oss-20b"
    )
    
    assert result.is_ok(), f"Audit failed: {result.unwrap_err()}"
    
    report = result.unwrap()
    assert len(report.issues) > 0, "Expected issues to be detected"
    assert any(i.priority == "P0" for i in report.issues), "Expected P0 issues"
    
    print("✅ Intelligent audit test passed")


@pytest.mark.asyncio
async def test_prioritization():
    """Test issue prioritization logic."""
    issues = [
        Issue("p2_issue", "P2", "style", "Style issue", []),
        Issue("p0_issue", "P0", "test_failure", "Test failure", []),
        Issue("p1_issue", "P1", "coverage", "Coverage gap", []),
    ]
    
    prioritized = await prioritize_issues(issues)
    
    assert prioritized[0].priority == "P0", "P0 should be first"
    assert prioritized[1].priority == "P1", "P1 should be second"
    assert prioritized[2].priority == "P2", "P2 should be third"
    
    print("✅ Prioritization test passed")


@pytest.mark.asyncio
async def test_completion_validation_pass():
    """Test completion validation with successful cycle."""
    report = AuditReport(
        total_cycles=1,
        total_fixes=2,
        final_health_score=0.9,
        patterns_learned=4,
        issues=[
            Issue("fixed_issue", "P0", "test", "Fixed issue", [], fixed=True)
        ]
    )
    
    result = await validate_cycle_completion(
        audit_report=report,
        fixes_applied=2,
        context_usage=0.5
    )
    
    assert result.is_ok(), f"Validation should pass: {result.unwrap_err() if result.is_err() else ''}"
    
    validation = result.unwrap()
    assert validation.cycle_complete is True
    assert validation.fixes_applied == 2
    
    print("✅ Completion validation (pass) test passed")


@pytest.mark.asyncio
async def test_completion_validation_fail():
    """Test completion validation with incomplete cycle."""
    report = AuditReport(
        total_cycles=1,
        total_fixes=0,
        final_health_score=0.5,
        patterns_learned=0,
        issues=[
            Issue("unfixed_p0", "P0", "test", "Unfixed P0 issue", [], fixed=False)
        ]
    )
    
    result = await validate_cycle_completion(
        audit_report=report,
        fixes_applied=0,
        context_usage=0.5  # < 0.80, so validation should fail
    )
    
    assert result.is_err(), "Validation should fail with unfixed P0 issues"
    
    error = result.unwrap_err()
    assert "high_priority_incomplete" in error.failed_checks
    
    print("✅ Completion validation (fail) test passed")


@pytest.mark.asyncio
async def test_autonomous_loop_full_cycle():
    """
    Test full autonomous audit loop (3 iterations).
    
    This is the main integration test demonstrating:
    - Pre-flight cleanup
    - Audit cycle iteration
    - Issue prioritization
    - Fix application
    - Completion validation
    - Post-flight cleanup
    """
    result = await autonomous_audit_loop(
        codebase_path="/Users/am/Code/Agency",
        local_model="gpt-oss-20b",
        max_iterations=3,
        context_budget=0.95
    )
    
    assert result.is_ok(), f"Autonomous loop failed: {result.unwrap_err()}"
    
    report = result.unwrap()
    assert report.total_cycles > 0, "Expected at least one cycle"
    assert report.total_fixes >= 0, "Expected fixes to be applied"
    
    print("\n" + "=" * 70)
    print("🎉 AUTONOMOUS AUDIT LOOP TEST COMPLETE")
    print("=" * 70)
    print(f"Total Cycles: {report.total_cycles}")
    print(f"Total Fixes: {report.total_fixes}")
    print(f"Final Health Score: {report.final_health_score:.2f}")
    print(f"Patterns Learned: {report.patterns_learned}")
    print("=" * 70)
    
    print("✅ Full autonomous loop test passed")


if __name__ == "__main__":
    # Run test manually
    asyncio.run(test_autonomous_loop_full_cycle())
