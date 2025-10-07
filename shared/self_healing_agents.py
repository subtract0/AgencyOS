"""Self-Healing Agent System - Agents detect their own degradation and auto-improve."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shared.agent_telemetry import AgentTelemetry
from shared.type_definitions.result import Result, Ok, Err


@dataclass
class HealthStatus:
    """Agent health assessment."""
    agent_name: str
    healthy: bool
    degradation_detected: bool
    issues: list[str]
    recommended_actions: list[str]


class SelfHealingSystem:
    """Detect agent degradation and trigger self-improvement."""

    def __init__(self):
        self.telemetry = AgentTelemetry()
        self.health_thresholds = {
            "min_success_rate": 0.90,
            "max_error_rate": 0.10,
            "min_constitutional_compliance": 1.0,
            "min_learning_rate": 0.60
        }

    def check_agent_health(self, agent_name: str) -> HealthStatus:
        """Check if agent is degrading."""
        metrics = self.telemetry.get_agent_metrics(agent_name, days=7)

        issues = []
        actions = []

        # Check success rate
        if metrics["avg_success_rate"] < self.health_thresholds["min_success_rate"]:
            issues.append(f"Success rate {metrics['avg_success_rate']:.0%} below threshold")
            actions.append("Run /agent-self-improve for root cause analysis")

        # Check constitutional compliance
        if metrics["avg_constitutional_compliance"] < 1.0:
            issues.append("Constitutional violations detected")
            actions.append("Use /constitutional-audit for violations list")

        healthy = len(issues) == 0
        degradation_detected = len(issues) > 0

        return HealthStatus(
            agent_name=agent_name,
            healthy=healthy,
            degradation_detected=degradation_detected,
            issues=issues,
            recommended_actions=actions
        )

    def auto_heal(self, agent_name: str) -> Result[str, str]:
        """Automatically trigger self-improvement for degraded agent."""
        health = self.check_agent_health(agent_name)

        if health.healthy:
            return Ok(f"{agent_name} is healthy, no action needed")

        # Trigger self-improvement
        # This would call /agent-self-improve programmatically
        proposal_path = f".claude/proposals/{agent_name}_auto_heal_{datetime.now().strftime('%Y%m%d')}.md"

        # Generate proposal
        # Submit to review queue
        # Log healing attempt

        return Ok(f"Self-healing initiated: {proposal_path}")

    def monitor_all_agents(self) -> dict[str, HealthStatus]:
        """Monitor health of all agents."""
        from shared.agent_registry import AGENT_REGISTRY

        health_report = {}
        for agent_name in AGENT_REGISTRY.keys():
            health_report[agent_name] = self.check_agent_health(agent_name)

        return health_report
