#!/usr/bin/env python3
"""
MetaLearning Agent Registry Demo - Practical usage example.

Demonstrates the value-driven approach to agent performance tracking.
Every line shows measurable benefits.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meta_learning import AgentRegistry
import time
import random


def simulate_agent_learning():
    """Simulate agents learning and improving over time."""
    print("🤖 MetaLearning Agent Registry Demo")
    print("=" * 50)

    # Create registry
    registry = AgentRegistry("data/demo_registry.json")

    # Register different agent types
    agents = {
        "CodeWriter": registry.register_agent("CodeWriterAgent", "1.0.0"),
        "TestGenerator": registry.register_agent("TestGeneratorAgent", "1.2.0"),
        "Debugger": registry.register_agent("DebuggerAgent", "2.1.0"),
    }

    print(f"✅ Registered {len(agents)} agents")

    # Create instances with different configurations
    instances = {}
    for name, agent_id in agents.items():
        config = {
            "learning_rate": random.uniform(0.001, 0.1),
            "context_size": random.choice([1024, 2048, 4096]),
            "model": random.choice(["gpt-4", "claude-3", "local-llm"])
        }
        instance_id = registry.create_instance(agent_id, config)
        instances[name] = instance_id
        print(f"📦 Created {name} instance: {instance_id[:8]}...")

    # Simulate learning progress over time
    print("\n📈 Simulating learning progress...")
    for iteration in range(1, 11):
        print(f"\nIteration {iteration}:")

        for name, instance_id in instances.items():
            # Simulate performance improvement over time
            base_score = 70 + iteration * 2
            variance = random.uniform(-5, 10)
            aiq_score = base_score + variance

            # Add some realistic metrics
            metrics = {
                "success_rate": min(1.0, (aiq_score / 100) + random.uniform(-0.1, 0.1)),
                "avg_response_time": random.uniform(0.5, 3.0),
                "code_quality": random.uniform(0.7, 1.0),
                "test_coverage": random.uniform(0.8, 1.0)
            }

            registry.record_aiq(instance_id, aiq_score, metrics)
            print(f"  {name}: AIQ {aiq_score:.1f} (success: {metrics['success_rate']:.2f})")

        # Show current top performers
        if iteration % 3 == 0:
            print("\n🏆 Current Top Performers:")
            top = registry.get_top_performers(limit=3)
            for i, (agent_name, score) in enumerate(top, 1):
                print(f"  {i}. {agent_name}: {score:.1f}")

        time.sleep(0.5)  # Brief pause for demonstration

    # Final analysis
    print("\n" + "=" * 50)
    print("📊 Final Analysis")
    print("=" * 50)

    for name, agent_id in agents.items():
        history = registry.get_agent_aiq_history(agent_id, limit=10)
        if history:
            scores = [event.aiq_score for event in history]
            improvement = scores[0] - scores[-1]  # Latest - earliest
            print(f"\n{name}:")
            print(f"  Latest AIQ: {scores[0]:.1f}")
            print(f"  Improvement: {improvement:+.1f}")
            print(f"  Total measurements: {len(history)}")

    print(f"\n🎯 Value Delivered:")
    print(f"  • Tracked {len(registry.agents)} agent types")
    print(f"  • Monitored {len(registry.instances)} instances")
    print(f"  • Recorded {len(registry.aiq_events)} performance measurements")
    print(f"  • Identified top performers for optimization")
    print(f"  • Provided quantifiable learning progress")

    # Start API server demo
    print(f"\n🌐 Starting REST API server...")
    print("Try these endpoints:")
    print("  GET  http://localhost:5000/health")
    print("  GET  http://localhost:5000/agents/top-performers")
    print("  POST http://localhost:5000/agents (with JSON: {'name': 'NewAgent'})")

    print(f"\n💡 To start the REST API server, run:")
    print("     python -c \"from meta_learning.registry_api import create_app; create_app().run()\"")
    print("\n👋 Demo completed! Check 'data/demo_registry.json' for persisted data.")


if __name__ == "__main__":
    simulate_agent_learning()