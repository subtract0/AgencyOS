"""
TDDGraphGenerator Example - Demonstration of Test-First Task Graph Generation.

Shows how ApprovedSpec → TaskGraph with automatic Test task generation.

Constitutional Compliance:
- Article II: Test tasks auto-created for every Code task
- Article IV: VectorStore query before generation
- Article V: Spec-driven development (TaskGraph is executable spec)

Usage:
    python tools/orchestrator/tdd_graph_generator_example.py
"""

import logging
from datetime import UTC, datetime

from shared.agent_context import create_agent_context
from tools.orchestrator.approval_checkpoint import ApprovalDecision, ApprovedSpec, Spec
from tools.orchestrator.tdd_graph_generator import TDDGraphGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_simple_spec():
    """Example: Generate task graph from simple spec."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Simple Spec → TaskGraph")
    print("=" * 80 + "\n")

    # Create context with memory
    context = create_agent_context(session_id="example_simple")

    # Store a VectorStore pattern (Article IV)
    context.store_memory(
        "pattern_auth_implementation",
        {
            "pattern_type": "authentication",
            "approach": "jwt_tokens",
            "confidence": 0.85,
            "tasks": ["spec_auth", "code_jwt", "test_jwt"],
        },
        ["task_graph", "pattern", "auth"],
    )

    # Create approved spec
    spec = Spec(
        title="JWT Authentication",
        content="Add JWT-based authentication to API endpoints with token validation and refresh",
        created_at=datetime.now(UTC).isoformat(),
        version=1,
    )
    decision = ApprovalDecision(action="approve", timestamp=datetime.now(UTC).isoformat())
    approved_spec = ApprovedSpec(spec=spec, decision=decision, edit_count=0)

    # Generate task graph
    generator = TDDGraphGenerator(context=context)
    result = generator.generate(approved_spec)

    if result.is_ok():
        graph = result.unwrap()

        print("✅ Task Graph Generated Successfully!\n")
        print(f"Mission: {graph.mission}")
        print(f"Phases: {len(graph.phases)}")
        print(f"Total Tasks: {len(graph.all_tasks())}")
        print(f"Patterns Used: {graph.metadata.get('patterns_used', 0)}\n")

        # Show ASCII tree
        print(graph.to_ascii_tree())
        print()

        # Verify Article II compliance
        all_tasks = graph.all_tasks()
        code_tasks = [t for t in all_tasks if t.type.value == "Code"]
        test_tasks = [t for t in all_tasks if t.type.value == "Test"]

        print("\n" + "-" * 80)
        print("ARTICLE II COMPLIANCE CHECK:")
        print("-" * 80)
        print(f"Code tasks: {len(code_tasks)}")
        print(f"Test tasks: {len(test_tasks)}")

        for code_task in code_tasks:
            matching_tests = [t for t in test_tasks if t.verification_target == code_task.id]
            if matching_tests:
                print(
                    f"✅ {code_task.id} → {matching_tests[0].id} "
                    f"(verification_target set, dependencies correct)"
                )
            else:
                print(f"❌ {code_task.id} → NO TEST TASK (Article II violation)")

        print()

    else:
        print(f"❌ Generation failed: {result.unwrap_err()}")


def example_complex_spec():
    """Example: Generate task graph from complex multi-component spec."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Complex Multi-Component Spec → TaskGraph")
    print("=" * 80 + "\n")

    # Create context
    context = create_agent_context(session_id="example_complex")

    # Create complex spec with multiple components
    spec = Spec(
        title="Complete Authentication System",
        content="""
Implement complete authentication system with the following components:

1. JWT token generation with RSA-256 encryption
2. Token validation middleware for API endpoints
3. User session management with Redis cache
4. Refresh token rotation with blacklist
5. Rate limiting per endpoint (100 req/min)
6. OAuth2 integration (Google, GitHub)
        """,
        created_at=datetime.now(UTC).isoformat(),
        version=1,
    )
    decision = ApprovalDecision(action="approve", timestamp=datetime.now(UTC).isoformat())
    approved_spec = ApprovedSpec(spec=spec, decision=decision, edit_count=0)

    # Generate task graph
    generator = TDDGraphGenerator(context=context)
    result = generator.generate(approved_spec)

    if result.is_ok():
        graph = result.unwrap()

        print("✅ Complex Task Graph Generated!\n")
        print(f"Mission: {graph.mission}")
        print(f"Total Tasks: {len(graph.all_tasks())}")
        print(f"Components Parsed: {graph.metadata.get('components_count', 0)}\n")

        # Show topological sort (execution order)
        print("EXECUTION ORDER (Topological Sort):")
        print("-" * 80)
        layers = graph.topological_sort()
        for layer_idx, layer in enumerate(layers):
            print(f"Layer {layer_idx}: {len(layer)} tasks")
            for task in layer:
                print(f"  - {task.id} ({task.type.value}, {task.agent})")

        print()

        # Show cost estimate
        estimated_cost = graph.estimate_cost()
        print(f"Estimated Cost: ${estimated_cost:.2f} USD")
        print("  (Tier 1 tasks: gpt-5 @ $4/1M tokens)")
        print("  (Tier 2 tasks: 60% local + 40% gpt-4o @ $1.5/1M tokens)")

    else:
        print(f"❌ Generation failed: {result.unwrap_err()}")


def main():
    """Run all examples."""
    print("\n🚀 TDDGraphGenerator Examples")
    print("=" * 80)
    print("Demonstrating Test-First Task Graph Generation (Article II)")
    print("=" * 80)

    # Run examples
    example_simple_spec()
    example_complex_spec()

    print("\n" + "=" * 80)
    print("✅ Examples Complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
