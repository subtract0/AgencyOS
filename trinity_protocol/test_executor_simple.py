"""
Simple validation test for EXECUTOR agent core functionality.
"""

import asyncio
from trinity_protocol.message_bus import MessageBus
from trinity_protocol.cost_tracker import CostTracker, ModelTier
from trinity_protocol.executor_agent import ExecutorAgent
from shared.agent_context import create_agent_context


async def main():
    print("=" * 60)
    print("EXECUTOR AGENT - SIMPLE VALIDATION TEST")
    print("=" * 60)

    # Create infrastructure
    message_bus = MessageBus(":memory:")
    cost_tracker = CostTracker(":memory:", budget_usd=10.0)
    agent_context = create_agent_context()

    # Create EXECUTOR
    executor = ExecutorAgent(
        message_bus=message_bus,
        cost_tracker=cost_tracker,
        agent_context=agent_context
    )

    print("\n✓ EXECUTOR agent initialized")

    # Test 1: Task deconstruction
    print("\n[Test 1] Task Deconstruction")
    code_task = {
        "task_id": "test-001",
        "task_type": "code_generation",
        "spec": {"details": "Implement feature X"}
    }
    plan = executor._deconstruct_task(code_task)
    print(f"  Task type: {code_task['task_type']}")
    print(f"  Sub-agents: {[a['type'] for a in plan.sub_agents]}")
    print(f"  Parallel groups: {plan.parallel_groups}")
    assert len(plan.sub_agents) == 2, "Should have CodeWriter + TestArchitect"
    assert len(plan.parallel_groups) == 1, "Should have 1 parallel group"

    # Test 2: Plan externalization
    print("\n[Test 2] Plan Externalization")
    plan_path = executor._externalize_plan(plan)
    print(f"  Plan file: {plan_path}")
    assert executor.plans_dir.exists(), "Plans directory should exist"
    plan_file = executor.plans_dir / f"{plan.task_id}_plan.md"
    assert plan_file.exists(), "Plan file should be created"
    content = plan_file.read_text()
    assert "CodeWriter" in content, "Plan should mention CodeWriter"
    assert "TestArchitect" in content, "Plan should mention TestArchitect"

    # Test 3: Parallel orchestration
    print("\n[Test 3] Parallel Orchestration")
    results = await executor._orchestrate_parallel(plan)
    print(f"  Results: {len(results)} sub-agents completed")
    for result in results:
        print(f"    - {result.agent}: {result.status} (${result.cost_usd:.6f})")
    assert len(results) == 2, "Should have 2 results"
    assert all(r.status == "success" for r in results), "All should succeed"

    # Test 4: Merge delegation
    print("\n[Test 4] Merge Delegation")
    merge_result = await executor._delegate_merge(results, plan.task_id)
    print(f"  Merge agent: {merge_result.agent}")
    print(f"  Status: {merge_result.status}")
    assert merge_result.agent == "ReleaseManager", "Should be ReleaseManager"
    assert merge_result.status == "success", "Merge should succeed"

    # Test 5: Telemetry report creation
    print("\n[Test 5] Telemetry Report Creation")
    report = executor._create_telemetry_report(
        status="success",
        task_id=plan.task_id,
        correlation_id=plan.correlation_id,
        details="Test task completed",
        sub_agent_reports=results + [merge_result],
        verification_result="All tests passed"
    )
    print(f"  Report keys: {list(report.keys())}")
    print(f"  Status: {report['status']}")
    print(f"  Sub-agent count: {len(report['sub_agent_reports'])}")
    assert report["status"] == "success", "Status should be success"
    assert "task_id" in report, "Should have task_id"
    assert "timestamp" in report, "Should have timestamp"
    assert len(report["sub_agent_reports"]) == 3, "Should have 3 sub-agent reports"

    # Test 6: Workspace cleanup
    print("\n[Test 6] Workspace Cleanup")
    executor._cleanup_workspace(plan.task_id)
    assert not plan_file.exists(), "Plan file should be removed"
    print("  ✓ Workspace cleaned")

    # Test 7: Cost tracking
    print("\n[Test 7] Cost Tracking")
    summary = cost_tracker.get_summary()
    print(f"  Total cost: ${summary.total_cost_usd:.6f}")
    print(f"  Total calls: {summary.total_calls}")
    print(f"  Success rate: {summary.success_rate * 100:.1f}%")
    assert summary.total_calls > 0, "Should have tracked LLM calls"
    assert summary.success_rate == 1.0, "All calls should succeed"

    # Test 8: Cost dashboard
    print("\n[Test 8] Cost Dashboard")
    cost_tracker.print_dashboard()

    # Test 9: Full task processing
    print("\n[Test 9] Full Task Processing (End-to-End)")
    test_task = {
        "task_id": "test-e2e-001",
        "correlation_id": "corr-001",
        "task_type": "code_generation",
        "spec": {"details": "End-to-end test task"}
    }

    # Publish task to execution_queue
    await message_bus.publish("execution_queue", test_task)

    # Run EXECUTOR briefly
    executor_task = asyncio.create_task(executor.run())
    await asyncio.sleep(0.5)  # Let it process
    await executor.stop()

    try:
        await asyncio.wait_for(executor_task, timeout=2.0)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        pass

    # Check telemetry
    telemetry_count = await message_bus.get_pending_count("telemetry_stream")
    print(f"  Telemetry reports: {telemetry_count}")
    assert telemetry_count > 0, "Should have telemetry report"

    # Check stats
    stats = executor.get_stats()
    print(f"  Tasks processed: {stats['tasks_processed']}")
    print(f"  Tasks succeeded: {stats['tasks_succeeded']}")
    assert stats["tasks_processed"] == 1, "Should have processed 1 task"
    assert stats["tasks_succeeded"] == 1, "Task should have succeeded"

    # Cleanup
    message_bus.close()
    cost_tracker.close()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nEXECUTOR agent core functionality validated!")
    print("Cost tracking operational!")
    print("Ready for full Trinity integration.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
