"""
Simple validation test for ARCHITECT agent core functionality.
"""

import asyncio
from trinity_protocol.message_bus import MessageBus
from trinity_protocol.persistent_store import PersistentStore
from trinity_protocol.architect_agent import ArchitectAgent


async def main():
    print("=" * 60)
    print("ARCHITECT AGENT - SIMPLE VALIDATION TEST")
    print("=" * 60)

    # Create infrastructure
    message_bus = MessageBus(":memory:")
    pattern_store = PersistentStore(":memory:")

    # Create ARCHITECT
    architect = ArchitectAgent(
        message_bus=message_bus,
        pattern_store=pattern_store,
        min_complexity=0.7
    )

    print("\n✓ ARCHITECT agent initialized")

    # Test 1: Complexity assessment
    print("\n[Test 1] Complexity Assessment")
    simple_signal = {
        'pattern': 'type_error',
        'data': {'keywords': ['bug']},
        'evidence_count': 1
    }
    simple_complexity = architect._assess_complexity(simple_signal)
    print(f"  Simple signal complexity: {simple_complexity:.2f} (expected < 0.3)")
    assert simple_complexity < 0.3, "Simple signal should score < 0.3"

    complex_signal = {
        'pattern': 'architectural_improvement',
        'data': {'keywords': ['architecture', 'refactor']},
        'evidence_count': 5
    }
    complex_complexity = architect._assess_complexity(complex_signal)
    print(f"  Complex signal complexity: {complex_complexity:.2f} (expected > 0.7)")
    assert complex_complexity > 0.7, "Complex signal should score > 0.7"

    # Test 2: Reasoning engine selection
    print("\n[Test 2] Reasoning Engine Selection")
    critical_signal = {'priority': 'CRITICAL', 'data': {}}
    engine = architect._select_reasoning_engine(critical_signal, 0.5)
    print(f"  CRITICAL priority → {engine} (expected: gpt-5)")
    assert engine == "gpt-5", "CRITICAL should select gpt-5"

    high_complex_signal = {'priority': 'HIGH', 'data': {}}
    engine = architect._select_reasoning_engine(high_complex_signal, 0.8)
    print(f"  HIGH + complex → {engine} (expected: claude-4.1)")
    assert engine == "claude-4.1", "HIGH + complex should select claude-4.1"

    normal_signal = {'priority': 'NORMAL', 'data': {}}
    engine = architect._select_reasoning_engine(normal_signal, 0.3)
    print(f"  NORMAL + simple → {engine} (expected: codestral-22b)")
    assert engine == "codestral-22b", "NORMAL should select codestral-22b"

    # Test 3: Context gathering
    print("\n[Test 3] Context Gathering")
    signal = {'pattern': 'test_pattern', 'data': {}}
    context = await architect._gather_context(signal)
    print(f"  Context keys: {list(context.keys())}")
    assert 'historical_patterns' in context, "Context should include historical patterns"
    assert 'relevant_adrs' in context, "Context should include ADRs"

    # Test 4: Spec generation
    print("\n[Test 4] Spec Generation")
    spec = architect._generate_spec(signal, context, "test-123")
    print(f"  Spec length: {len(spec)} chars")
    assert "# Spec:" in spec, "Spec should be markdown format"
    assert "test-123" in spec, "Spec should include correlation ID"

    # Test 5: Task graph generation
    print("\n[Test 5] Task Graph Generation")
    from trinity_protocol.architect_agent import Strategy
    strategy = Strategy(
        priority="HIGH",
        complexity=0.5,
        engine="codestral-22b",
        decision="Test task generation",
        spec_content=None,
        adr_content=None
    )
    tasks = architect._generate_task_graph(strategy, "test-graph-123")
    print(f"  Tasks generated: {len(tasks)}")
    print(f"  Task types: {[t.task_type for t in tasks]}")
    assert len(tasks) == 3, "Should generate 3 tasks (code, test, merge)"

    # Test 6: Self-verification
    print("\n[Test 6] Self-Verification")
    task_dicts = [t.to_dict() for t in tasks]
    try:
        is_valid = architect._self_verify_plan(tasks)
        print(f"  Task graph valid: {is_valid}")
        assert is_valid, "Task graph should be valid"
    except ValueError as e:
        print(f"  ✗ Validation failed: {e}")
        raise

    # Test 7: Signal processing
    print("\n[Test 7] Signal Processing (end-to-end)")
    test_signal = {
        'priority': 'NORMAL',
        'pattern': 'code_duplication',
        'data': {'keywords': []},
        'correlation_id': 'test-e2e-456'
    }
    try:
        await architect._process_signal(test_signal, "test-e2e-456")
        print("  ✓ Signal processed successfully")

        # Check execution queue
        pending = await message_bus.get_pending_count("execution_queue")
        print(f"  Tasks in execution_queue: {pending}")
        assert pending >= 3, f"Should have at least 3 tasks in queue, got {pending}"

    except Exception as e:
        print(f"  ✗ Processing failed: {e}")
        raise

    # Test 8: Statistics
    print("\n[Test 8] Statistics")
    stats = architect.get_stats()
    print(f"  Stats keys: {list(stats.keys())}")
    print(f"  Signals processed: {stats['signals_processed']}")
    print(f"  Tasks created: {stats['tasks_created']}")
    # Note: signals_processed is only incremented in run() loop, not _process_signal()
    assert stats['tasks_created'] == 3, "Should have created 3 tasks"

    # Cleanup
    message_bus.close()
    pattern_store.close()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nARCHITECT agent core functionality validated!")
    print("Ready for integration with WITNESS and EXECUTOR.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
