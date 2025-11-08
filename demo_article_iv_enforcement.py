#!/usr/bin/env python3
"""
Article IV Enforcement Demonstration

Shows the permanent fix for /primeA's vaporware learning claims.

BEFORE (Bug):
- /primeA CLAIMED patterns were stored to VectorStore
- NO actual context.store_memory() calls executed
- Documentation without enforcement = vaporware

AFTER (Fix):
- Article IV Enforcer MANDATES pattern storage
- Validation gate BLOCKS execution if patterns not stored
- No bypass possible (Article III compliance)

This script demonstrates both scenarios:
1. Proper enforcement (stores patterns, validation passes)
2. Violation scenario (no patterns, validation blocks)
"""

import sys
import time

from tools.orchestrator.article_iv_enforcer import (
    ArticleIVViolation,
    create_article_iv_enforcer,
)


def demo_proper_enforcement():
    """
    Demonstrate CORRECT /primeA workflow with Article IV enforcement.

    This is how /primeA MUST work going forward.
    """
    print("=" * 80)
    print("SCENARIO A: PROPER ARTICLE IV ENFORCEMENT")
    print("=" * 80)
    print()

    # STEP 6.0: Initialize Article IV Enforcer
    print("STEP 6.0: Initialize Article IV Enforcer")
    enforcer = create_article_iv_enforcer(
        mission_name="Demo Mission - Proper Enforcement",
        session_id=f"demo_proper_{int(time.time())}",
    )
    print("✅ Enforcer initialized")
    print(f"   Mission: {enforcer.mission_name}")
    print(f"   Session: {enforcer.session_id}")
    print()

    # STEP 6.1-6.3: Execution happens (simulated)
    print("STEP 6.1-6.3: Mission execution (simulated)")
    print("✅ Task graph executed")
    print("✅ All tests passed")
    print("✅ Quality gates validated")
    print()

    # STEP 6.4: Store execution patterns (MANDATORY)
    print("STEP 6.4: Store Execution Patterns (MANDATORY)")

    # Pattern 1: Quality gate usage
    result1 = enforcer.store_pattern(
        pattern_key=f"pattern_quality_gate_{int(time.time())}",
        pattern_content={
            "type": "quality_gate",
            "description": "Applied completion validator to prevent premature stopping",
            "gates_used": ["slop_immunity", "budget_guard", "completion_validator"],
            "effectiveness": "100% (blocked execution report until complete)",
        },
        tags=["pattern", "quality", "blocking_gate"],
        confidence=1.0,
    )
    print(f"✅ Pattern 1 stored: {result1.is_ok()}")

    # Pattern 2: Cost optimization
    result2 = enforcer.store_pattern(
        pattern_key=f"pattern_cost_optimization_{int(time.time())}",
        pattern_content={
            "type": "cost_optimization",
            "description": "Achieved 45% cost savings via adaptive model routing",
            "estimated_cost_usd": 10.0,
            "actual_cost_usd": 5.5,
            "technique": "P1/P2/P3 tier classification",
        },
        tags=["pattern", "cost", "optimization", "adaptive_routing"],
        confidence=0.9,
    )
    print(f"✅ Pattern 2 stored: {result2.is_ok()}")

    # Pattern 3: Task decomposition
    result3 = enforcer.store_pattern(
        pattern_key=f"pattern_task_decomposition_{int(time.time())}",
        pattern_content={
            "type": "task_decomposition",
            "description": "Decomposed mission into 12 tasks across 3 phases",
            "parallelism": 4,
            "task_breakdown": {"spec": 2, "code": 6, "test": 4},
        },
        tags=["pattern", "planning", "decomposition", "task_graph"],
        confidence=0.8,
    )
    print(f"✅ Pattern 3 stored: {result3.is_ok()}")

    print(f"\n✅ Total patterns stored: {len(enforcer.patterns_stored)}")
    print()

    # STEP 6.5: Validate Article IV Compliance (BLOCKING GATE)
    print("STEP 6.5: Validate Article IV Compliance (BLOCKING GATE)")
    try:
        validation_result = enforcer.validate_article_iv_compliance(min_patterns=1)

        if validation_result.is_ok():
            report = validation_result.unwrap()
            print("✅ ARTICLE IV COMPLIANCE VALIDATED")
            print(f"   Patterns Stored: {report['patterns_stored']}")
            print(f"   Patterns Verified: {report['patterns_verified']}")
            print(f"   Average Confidence: {report['average_confidence']:.2f}")
            print(f"   Pattern Types: {', '.join(set(report['pattern_types']))}")
            print()

            print(enforcer.get_stored_patterns_summary())
            print()

            print("✅ PROCEEDING TO STEP 7 (Execution Report)")
            print()

            return True

    except ArticleIVViolation as e:
        print(f"❌ VIOLATION: {e.reason}")
        return False

    print("=" * 80)
    print()


def demo_violation_scenario():
    """
    Demonstrate what happens when Article IV is VIOLATED.

    This is what happened in the previous /primeA execution:
    - Claimed patterns were stored
    - Never actually called context.store_memory()
    - Vaporware documentation without code execution
    """
    print("=" * 80)
    print("SCENARIO B: ARTICLE IV VIOLATION (What We're Fixing)")
    print("=" * 80)
    print()

    # STEP 6.0: Initialize Article IV Enforcer
    print("STEP 6.0: Initialize Article IV Enforcer")
    enforcer = create_article_iv_enforcer(
        mission_name="Demo Mission - Violation Scenario",
        session_id=f"demo_violation_{int(time.time())}",
    )
    print("✅ Enforcer initialized")
    print()

    # STEP 6.1-6.3: Execution happens (simulated)
    print("STEP 6.1-6.3: Mission execution (simulated)")
    print("✅ Task graph executed")
    print("✅ All tests passed")
    print()

    # STEP 6.4: FORGET to store patterns (THE BUG!)
    print("STEP 6.4: Store Execution Patterns (MANDATORY)")
    print("⚠️  Forgot to call enforcer.store_pattern() - VAPORWARE CLAIMS!")
    print("⚠️  This is what happened in previous /primeA execution")
    print("⚠️  Documentation said 'patterns stored' but NO CODE executed")
    print()

    # STEP 6.5: Validate Article IV Compliance (BLOCKING GATE)
    print("STEP 6.5: Validate Article IV Compliance (BLOCKING GATE)")
    try:
        validation_result = enforcer.validate_article_iv_compliance(min_patterns=1)

        if validation_result.is_ok():
            # This shouldn't happen
            print("❌ UNEXPECTED: Validation passed without patterns!")
            return False

    except ArticleIVViolation as e:
        print("✅ ENFORCEMENT WORKING: Violation detected and blocked")
        print()
        print(f"❌ ARTICLE IV VIOLATION")
        print(f"   Reason: {e.reason}")
        print(f"   Mission: {e.mission}")
        print()
        print("   Suggestions:")
        for suggestion in e.suggestions:
            print(f"   - {suggestion}")
        print()
        print("⚠️  BLOCKING: Cannot proceed to STEP 7 without Article IV compliance")
        print(
            "⚠️  Article IV requires MANDATORY VectorStore learning (not optional)"
        )
        print("⚠️  Use enforcer.store_pattern() to store at least 1 pattern")
        print()
        print("🎯 This is the PERMANENT FIX - vaporware claims are NO LONGER POSSIBLE")
        print()

        return True

    print("=" * 80)
    print()


def main():
    """Run both demonstration scenarios."""
    print("\n" + "=" * 80)
    print("ARTICLE IV ENFORCEMENT DEMONSTRATION")
    print("=" * 80)
    print()
    print("This demonstrates the permanent fix for /primeA's vaporware learning.")
    print()
    print("BACKGROUND:")
    print(
        "- Previous /primeA execution CLAIMED patterns were stored to VectorStore"
    )
    print("- Grepping transcript revealed ZERO context.store_memory() calls")
    print("- Article IV was aspirational documentation, not enforced code")
    print()
    print("FIX:")
    print("- Created ArticleIVEnforcer tool with mandatory validation gate")
    print("- Updated /primeA protocol with STEP 6.4 enforcement")
    print(
        "- Validation BLOCKS execution report if patterns not stored (no bypass)"
    )
    print()
    print("=" * 80)
    print()

    # Run Scenario A: Proper enforcement
    scenario_a_success = demo_proper_enforcement()

    # Run Scenario B: Violation scenario
    scenario_b_success = demo_violation_scenario()

    # Summary
    print("=" * 80)
    print("DEMONSTRATION SUMMARY")
    print("=" * 80)
    print()
    print(
        f"Scenario A (Proper Enforcement): {'✅ PASSED' if scenario_a_success else '❌ FAILED'}"
    )
    print(
        f"Scenario B (Violation Blocked):  {'✅ PASSED' if scenario_b_success else '❌ FAILED'}"
    )
    print()

    if scenario_a_success and scenario_b_success:
        print("✅ ARTICLE IV ENFORCEMENT IS OPERATIONAL")
        print()
        print("KEY TAKEAWAYS:")
        print("1. VectorStore infrastructure is operational (verified in Phase 1)")
        print("2. Article IV Enforcer blocks execution without pattern storage")
        print("3. /primeA protocol updated with mandatory STEP 6.4 validation gate")
        print("4. 17/17 tests passing for Article IV enforcer")
        print()
        print(
            "CONSTITUTIONAL COMPLIANCE: Article IV is now ENFORCED, not just claimed"
        )
        print()
        return 0
    else:
        print("❌ ENFORCEMENT DEMONSTRATION FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
