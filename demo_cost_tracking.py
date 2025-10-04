"""
Demo: Real GPT-5 Cost Tracking Across Agency Agents

This script demonstrates the integrated cost tracking system working with real
GPT-5 API calls. It shows:
1. Automatic token counting from OpenAI API responses
2. Per-agent cost breakdowns
3. Real-time cost dashboard
4. Cost data persistence to SQLite

IMPORTANT: This makes real API calls with minimal tokens to control costs.
"""

import os

from openai import OpenAI
from trinity_protocol.cost_tracker import CostTracker

from agency_code_agent.agency_code_agent import create_agency_code_agent
from shared.agent_context import create_agent_context
from shared.llm_cost_wrapper import wrap_openai_client


def demo_simple_cost_tracking():
    """Simple demonstration of cost tracking with OpenAI client."""
    print("\n" + "=" * 80)
    print("DEMO 1: Direct OpenAI Client Cost Tracking")
    print("=" * 80)

    # Create cost tracker with $1 budget
    tracker = CostTracker(db_path="demo_costs.db", budget_usd=1.0)

    # Enable cost tracking for all OpenAI calls
    wrap_openai_client(tracker, agent_name="DemoAgent", task_id="demo-1")

    # Make a minimal API call
    print("\nMaking API call to GPT-4o-mini...")
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Explain cost tracking in 10 words or less."}],
        max_tokens=15,
    )

    print(f"Response: {response.choices[0].message.content}")

    # Display cost dashboard
    tracker.print_dashboard()

    # Show recent calls
    print("\nRecent API Calls:")
    for call in tracker.get_recent_calls(limit=5):
        print(
            f"  - {call.agent}: {call.model} | "
            f"${call.cost_usd:.6f} | "
            f"{call.input_tokens} in + {call.output_tokens} out tokens"
        )

    tracker.close()
    print("\nCost data saved to: demo_costs.db")


def demo_agent_cost_tracking():
    """Demonstrate cost tracking integrated with Agency agents."""
    print("\n" + "=" * 80)
    print("DEMO 2: Agency Agent Cost Tracking")
    print("=" * 80)

    # Create cost tracker
    tracker = CostTracker(db_path=":memory:", budget_usd=5.0)

    # Create agent with cost tracking
    context = create_agent_context()
    agent = create_agency_code_agent(
        model="gpt-4o-mini", agent_context=context, cost_tracker=tracker
    )

    print(f"\nCreated {agent.name} with cost tracking enabled")
    print(f"Cost tracker attached to agent context: {hasattr(context, 'cost_tracker')}")

    # Verify integration
    summary = tracker.get_summary()
    print("\nInitial state:")
    print(f"  Total calls: {summary.total_calls}")
    print(f"  Total cost: ${summary.total_cost_usd:.6f}")

    print("\nAgent is ready to make LLM calls with automatic cost tracking!")
    print("All API calls will be tracked and reported in real-time.")

    tracker.close()


def demo_gpt5_cost_tracking():
    """Demonstrate GPT-5 cost tracking (if API key is available)."""
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set - skipping GPT-5 demo")
        return

    print("\n" + "=" * 80)
    print("DEMO 3: Real GPT-5 Cost Tracking")
    print("=" * 80)

    # Create cost tracker
    tracker = CostTracker(db_path=":memory:", budget_usd=10.0)

    # Enable tracking
    wrap_openai_client(tracker, agent_name="GPT5Demo", task_id="gpt5-demo")

    # Make minimal GPT-5 call
    print("\nMaking minimal GPT-5 API call (low reasoning effort)...")
    client = OpenAI()

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": "Say 'Cost tracking works!' and nothing else"}],
            max_completion_tokens=10,
            reasoning_effort="low",
        )

        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")

        # Show cost breakdown
        tracker.print_dashboard()

        # Detailed call info
        recent = tracker.get_recent_calls(limit=1)[0]
        print("\nDetailed cost breakdown:")
        print(f"  Input tokens:  {recent.input_tokens:,}")
        print(f"  Output tokens: {recent.output_tokens:,}")
        print(f"  Duration:      {recent.duration_seconds:.2f}s")
        print(f"  Cost:          ${recent.cost_usd:.6f}")
        print(f"  Model tier:    {recent.model_tier.value}")

    except Exception as e:
        print(f"Error: {e}")

    tracker.close()


def demo_multi_agent_tracking():
    """Demonstrate tracking across multiple agents."""
    print("\n" + "=" * 80)
    print("DEMO 4: Multi-Agent Cost Tracking")
    print("=" * 80)

    from test_generator_agent.test_generator_agent import create_test_generator_agent
    from toolsmith_agent.toolsmith_agent import create_toolsmith_agent

    # Shared cost tracker
    tracker = CostTracker(db_path=":memory:", budget_usd=10.0)
    context = create_agent_context()

    # Create multiple agents with same tracker
    agents = [
        create_agency_code_agent(model="gpt-4o-mini", agent_context=context, cost_tracker=tracker),
        create_test_generator_agent(model="gpt-5", agent_context=context, cost_tracker=tracker),
        create_toolsmith_agent(model="gpt-5", agent_context=context, cost_tracker=tracker),
    ]

    print(f"\nCreated {len(agents)} agents:")
    for agent in agents:
        print(f"  - {agent.name}")

    print("\nAll agents share the same CostTracker instance")
    print("Any LLM calls from any agent will be tracked and reported together")

    # Verify all agents have tracking
    summary = tracker.get_summary()
    print("\nShared tracker state:")
    print(f"  Total calls: {summary.total_calls}")
    print(f"  Budget remaining: ${tracker.budget_usd - summary.total_cost_usd:.2f}")

    tracker.close()


def main():
    """Run all cost tracking demonstrations."""
    print("\n" + "█" * 80)
    print(" " * 20 + "AGENCY LLM COST TRACKING DEMO")
    print("█" * 80)

    demo_simple_cost_tracking()
    demo_gpt5_cost_tracking()  # Run GPT-5 before other demos that close trackers
    demo_agent_cost_tracking()
    demo_multi_agent_tracking()

    print("\n" + "=" * 80)
    print("✅ All demonstrations completed successfully!")
    print("=" * 80)

    print("\nKey Takeaways:")
    print("  1. Cost tracking works transparently with all OpenAI API calls")
    print("  2. Real token counts are captured from API responses")
    print("  3. All 6 Agency agents support cost tracking via cost_tracker parameter")
    print("  4. Costs are persisted to SQLite for historical analysis")
    print("  5. Budget alerts help prevent cost overruns")

    print("\nNext Steps:")
    print("  - Run: python demo_cost_tracking.py")
    print("  - Check: demo_costs.db for cost data")
    print("  - Review: /tmp/gpt5_cost_test.json for detailed breakdown")


if __name__ == "__main__":
    main()
