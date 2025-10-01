#!/usr/bin/env python3
"""
Verification script for cost tracking infrastructure.

Tests that all agent factories accept and store cost_tracker parameter.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.cost_tracker import CostTracker, ModelTier
from shared.agent_context import create_agent_context
from agency_code_agent import create_agency_code_agent
from test_generator_agent import create_test_generator_agent
from toolsmith_agent import create_toolsmith_agent
from quality_enforcer_agent import create_quality_enforcer_agent
from merger_agent import create_merger_agent
from work_completion_summary_agent import create_work_completion_summary_agent


def verify_agent_cost_tracker(agent_name: str, factory_func, **kwargs):
    """Verify that an agent factory accepts and stores cost_tracker."""
    print(f"\n{'='*60}")
    print(f"Testing: {agent_name}")
    print(f"{'='*60}")

    # Create cost tracker
    tracker = CostTracker(db_path=":memory:")
    agent_context = create_agent_context()

    # Create agent with cost_tracker
    agent = factory_func(
        agent_context=agent_context,
        cost_tracker=tracker,
        **kwargs
    )

    # Verify cost_tracker is stored in agent_context
    if hasattr(agent_context, 'cost_tracker'):
        if agent_context.cost_tracker is tracker:
            print(f"✅ {agent_name}: cost_tracker stored correctly in agent_context")
            return True
        else:
            print(f"❌ {agent_name}: cost_tracker stored but not the same instance")
            return False
    else:
        print(f"❌ {agent_name}: cost_tracker not stored in agent_context")
        return False


def main():
    """Run verification tests."""
    print("\n" + "="*60)
    print("COST TRACKING INFRASTRUCTURE VERIFICATION")
    print("="*60)

    results = []

    # Test each agent
    agents_to_test = [
        ("AgencyCodeAgent", create_agency_code_agent, {"model": "gpt-5-mini"}),
        ("TestGeneratorAgent", create_test_generator_agent, {"model": "gpt-5"}),
        ("ToolsmithAgent", create_toolsmith_agent, {"model": "gpt-5"}),
        ("QualityEnforcerAgent", create_quality_enforcer_agent, {"model": "gpt-5"}),
        ("MergerAgent", create_merger_agent, {"model": "gpt-5"}),
        ("WorkCompletionSummaryAgent", create_work_completion_summary_agent, {"model": "gpt-5-nano"}),
    ]

    for agent_name, factory_func, kwargs in agents_to_test:
        try:
            result = verify_agent_cost_tracker(agent_name, factory_func, **kwargs)
            results.append((agent_name, result))
        except Exception as e:
            print(f"❌ {agent_name}: Error during verification: {e}")
            results.append((agent_name, False))

    # Print summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed

    for agent_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {agent_name}")

    print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}")

    # Test basic cost tracking functionality
    print("\n" + "="*60)
    print("COST TRACKER BASIC FUNCTIONALITY TEST")
    print("="*60)

    tracker = CostTracker(db_path=":memory:")

    # Track a mock call
    tracker.track_call(
        agent="VerificationAgent",
        model="gpt-5",
        model_tier=ModelTier.CLOUD_PREMIUM,
        input_tokens=1000,
        output_tokens=500,
        duration_seconds=2.5,
        success=True,
        task_id="test-123",
        correlation_id="corr-456"
    )

    summary = tracker.get_summary()

    print(f"Total cost: ${summary.total_cost_usd:.4f}")
    print(f"Total calls: {summary.total_calls}")
    print(f"Cost by agent: {summary.by_agent}")

    if summary.total_cost_usd > 0:
        print("✅ Cost tracking is working correctly")
    else:
        print("❌ Cost tracking failed - total cost is $0")

    # Exit with appropriate code
    if failed == 0:
        print("\n✅ All verification tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} verification test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
