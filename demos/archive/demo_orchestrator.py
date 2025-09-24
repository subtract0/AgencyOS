#!/usr/bin/env python3
"""
Orchestrator System Demo - Showcasing Enterprise-Grade Multi-Agent Coordination

This demo illustrates the power of the orchestrator system extracted from the
enterprise infrastructure branch. It demonstrates:

- Parallel task execution with sophisticated retry policies
- Real-time heartbeat monitoring and telemetry
- Graceful error handling and recovery
- Resource utilization tracking
- Cost accounting and performance metrics

The demo simulates a complex multi-step workflow with intentional failures
to showcase the system's resilience and self-healing capabilities.
"""

import asyncio
import json
import random
import time
from dataclasses import dataclass
from typing import Any, Dict

from shared.agent_context import AgentContext, create_agent_context
from tools.orchestrator.scheduler import (
    OrchestrationPolicy,
    RetryPolicy,
    TaskSpec,
    run_parallel,
)
from tools.telemetry.aggregator import aggregate, list_events


@dataclass
class MockAgent:
    """Mock agent for demonstration purposes."""
    name: str
    failure_rate: float = 0.2
    min_duration: float = 1.0
    max_duration: float = 5.0

    async def run(self, prompt: str, **params) -> Dict[str, Any]:
        """Simulate agent work with realistic timing and occasional failures."""
        duration = random.uniform(self.min_duration, self.max_duration)
        await asyncio.sleep(duration)

        # Simulate occasional failures for resilience testing
        if random.random() < self.failure_rate:
            raise RuntimeError(f"{self.name} encountered a simulated error")

        return {
            "agent": self.name,
            "prompt": prompt,
            "duration": duration,
            "result": f"Completed task: {prompt[:50]}...",
            "usage": {
                "prompt_tokens": random.randint(100, 500),
                "completion_tokens": random.randint(50, 200),
                "total_tokens": random.randint(150, 700),
            },
            "model": random.choice(["gpt-4o", "claude-3-5-sonnet", "gpt-4o-mini"]),
        }


def create_agent_factory(agent_name: str, **kwargs):
    """Factory function to create agents compatible with orchestrator."""
    def factory(ctx: AgentContext) -> MockAgent:
        return MockAgent(name=agent_name, **kwargs)
    factory.__name__ = agent_name
    return factory


async def demonstrate_orchestrator():
    """Main demonstration of orchestrator capabilities."""
    print("🚀 Agency Orchestrator System Demo")
    print("=" * 60)

    # Create shared context for all agents
    ctx = create_agent_context()

    # Define sophisticated orchestration policy
    policy = OrchestrationPolicy(
        max_concurrency=6,  # Run up to 6 agents in parallel
        retry=RetryPolicy(
            max_attempts=3,     # Retry failed tasks up to 3 times
            backoff="exp",      # Exponential backoff strategy
            base_delay_s=0.5,   # Start with 0.5s delay
            jitter=0.2          # Add 20% jitter to prevent thundering herd
        ),
        timeout_s=30.0,         # 30-second timeout per task
        fairness="round_robin", # Fair scheduling across agents
        cancellation="isolated" # Isolated failure handling
    )

    # Create diverse set of tasks with varying complexity
    tasks = [
        TaskSpec(
            id="data_analysis",
            agent_factory=create_agent_factory("DataAnalyst", failure_rate=0.1, max_duration=3.0),
            prompt="Analyze sales data for Q3 trends and anomalies",
            params={"dataset": "sales_q3", "method": "advanced"}
        ),
        TaskSpec(
            id="code_review",
            agent_factory=create_agent_factory("CodeReviewer", failure_rate=0.3, max_duration=4.0),
            prompt="Review pull request #42 for security and performance issues",
            params={"pr_id": 42, "focus": "security"}
        ),
        TaskSpec(
            id="documentation",
            agent_factory=create_agent_factory("TechnicalWriter", failure_rate=0.15, max_duration=2.5),
            prompt="Create API documentation for the new authentication endpoints",
            params={"scope": "auth_api", "format": "openapi"}
        ),
        TaskSpec(
            id="testing",
            agent_factory=create_agent_factory("TestEngineer", failure_rate=0.25, max_duration=5.0),
            prompt="Generate comprehensive test suite for user management module",
            params={"module": "user_mgmt", "coverage": "100%"}
        ),
        TaskSpec(
            id="optimization",
            agent_factory=create_agent_factory("PerformanceOptimizer", failure_rate=0.4, max_duration=6.0),
            prompt="Optimize database queries in the reporting dashboard",
            params={"target": "dashboard", "metrics": ["latency", "throughput"]}
        ),
        TaskSpec(
            id="monitoring",
            agent_factory=create_agent_factory("SystemMonitor", failure_rate=0.2, max_duration=2.0),
            prompt="Set up alerts for critical system metrics and SLA violations",
            params={"sla_threshold": "99.9%", "metrics": ["cpu", "memory", "disk"]}
        ),
    ]

    print(f"📋 Orchestrating {len(tasks)} tasks with {policy.max_concurrency} max concurrency")
    print(f"🔄 Retry policy: {policy.retry.max_attempts} attempts with {policy.retry.backoff} backoff")
    print(f"⏱️  Task timeout: {policy.timeout_s}s")
    print("-" * 60)

    # Execute orchestration
    start_time = time.time()
    result = await run_parallel(ctx, tasks, policy)
    end_time = time.time()

    # Analyze results
    print("\n📊 Orchestration Results")
    print("-" * 60)

    success_count = sum(1 for task in result.tasks if task.status == "success")
    failed_count = sum(1 for task in result.tasks if task.status == "failed")
    timeout_count = sum(1 for task in result.tasks if task.status == "timeout")

    print(f"✅ Successful tasks: {success_count}/{len(tasks)}")
    print(f"❌ Failed tasks: {failed_count}/{len(tasks)}")
    print(f"⏰ Timed out tasks: {timeout_count}/{len(tasks)}")
    print(f"🕒 Total wall time: {end_time - start_time:.2f}s")
    print(f"⚡ Orchestrator overhead: {result.metrics.get('wall_time', 0):.2f}s")

    # Show task details
    print("\n📋 Task Details:")
    for task in result.tasks:
        status_emoji = {"success": "✅", "failed": "❌", "timeout": "⏰"}.get(task.status, "❓")
        duration = task.finished_at - task.started_at
        print(f"  {status_emoji} {task.agent:18} | {duration:5.1f}s | {task.attempts} attempts | {task.id}")
        if task.errors:
            print(f"    ⚠️  Errors: {', '.join(task.errors)}")

    # Display telemetry insights
    await asyncio.sleep(1)  # Allow telemetry to settle
    print("\n📈 Telemetry Analysis (Last 5 minutes):")
    print("-" * 60)

    try:
        telemetry = aggregate(since="5m")

        print(f"🔢 Total events: {telemetry['metrics']['total_events']}")
        print(f"🏃 Tasks started: {telemetry['metrics']['tasks_started']}")
        print(f"🏁 Tasks finished: {telemetry['metrics']['tasks_finished']}")

        if telemetry['agents_active']:
            print(f"🤖 Active agents: {', '.join(telemetry['agents_active'])}")

        if telemetry['costs']['total_tokens'] > 0:
            print(f"💰 Token usage: {telemetry['costs']['total_tokens']:,} tokens")
            print(f"💵 Estimated cost: ${telemetry['costs']['total_usd']:.4f}")

        # Show resource utilization
        resources = telemetry['resources']
        if resources['max_concurrency']:
            util = resources.get('utilization', 0) * 100
            print(f"🎯 Peak utilization: {util:.1f}% ({resources['running']}/{resources['max_concurrency']})")

    except Exception as e:
        print(f"⚠️  Could not retrieve telemetry: {e}")

    # Show some recent events
    print("\n📜 Recent Events (Last 10):")
    print("-" * 60)

    try:
        events = list_events(since="5m", limit=10)
        for event in events[-10:]:  # Show last 10
            event_type = event.get("type", "unknown")
            agent = event.get("agent", "unknown")
            status = event.get("status", "")
            ts = event.get("ts", "")[:19]  # Remove microseconds

            if event_type == "task_started":
                print(f"🟡 {ts} | {agent:15} | Task started (attempt {event.get('attempt', 1)})")
            elif event_type == "task_finished":
                emoji = {"success": "🟢", "failed": "🔴", "timeout": "🟠"}.get(status, "⚪")
                duration = event.get("duration_s", 0)
                print(f"{emoji} {ts} | {agent:15} | Task {status} ({duration:.1f}s)")
            elif event_type == "heartbeat":
                running_time = event.get("running_for_s", 0)
                print(f"💓 {ts} | {agent:15} | Heartbeat ({running_time:.0f}s running)")

    except Exception as e:
        print(f"⚠️  Could not retrieve events: {e}")

    print("\n🎉 Demo completed! The orchestrator system provides:")
    print("  • Sophisticated parallel task execution")
    print("  • Resilient retry mechanisms with exponential backoff")
    print("  • Real-time monitoring and telemetry")
    print("  • Resource utilization tracking")
    print("  • Cost accounting and performance metrics")
    print("  • Graceful error handling and recovery")


if __name__ == "__main__":
    print("Starting Agency Orchestrator Demo...")
    try:
        asyncio.run(demonstrate_orchestrator())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        raise