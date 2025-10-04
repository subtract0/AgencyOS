#!/usr/bin/env python3
"""
Constitutional Consciousness - Agent Evolution Engine (Day 4).

Analyzes learnings from VectorStore and proposes agent delta file updates.

Constitutional Compliance:
- Article II: 100% verification (requires human PR approval)
- Article IV: Continuous learning (sourced from VectorStore patterns)
- Article V: Spec-driven (this tool implements consciousness-launch.md spec)

Safety:
- Human-in-loop PR approval (no auto-merge)
- Git audit trail for all changes
- Rollback capability via git
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agency_memory import create_enhanced_memory_store
from tools.constitutional_consciousness.models import ConstitutionalPattern


class AgentEvolutionEngine:
    """
    Proposes agent definition improvements based on constitutional learnings.

    Uses VectorStore to identify patterns that suggest agent behavior improvements.
    """

    def __init__(self, enable_vectorstore: bool = True):
        """Initialize evolution engine."""
        self.enable_vectorstore = enable_vectorstore
        self.agents_dir = Path(".claude/agents")

        if self.enable_vectorstore:
            self.vector_store = create_enhanced_memory_store(
                embedding_provider="openai"
            )
        else:
            self.vector_store = None

    def analyze_agent_patterns(
        self,
        patterns: list[ConstitutionalPattern]
    ) -> dict[str, list[ConstitutionalPattern]]:
        """
        Group patterns by affected agent.

        Args:
            patterns: Detected constitutional patterns

        Returns:
            Dict mapping agent name to list of patterns
        """
        agent_patterns: dict[str, list[ConstitutionalPattern]] = {}

        for pattern in patterns:
            # Infer agent from function name
            # e.g., "create_mock_agent" → "mock" agent (test infrastructure)
            # "create_planner_agent" → "planner" agent
            agent = self._infer_agent(pattern.function_name)

            if agent not in agent_patterns:
                agent_patterns[agent] = []

            agent_patterns[agent].append(pattern)

        return agent_patterns

    def _infer_agent(self, function_name: str) -> str:
        """Infer agent name from function."""
        # Common patterns
        if "mock" in function_name.lower():
            return "test_infrastructure"
        elif "planner" in function_name.lower():
            return "planner"
        elif "code" in function_name.lower():
            return "code_agent"
        elif "quality" in function_name.lower():
            return "quality_enforcer"
        elif "learning" in function_name.lower():
            return "learning"
        else:
            return "general"

    def propose_evolution(
        self,
        agent_name: str,
        patterns: list[ConstitutionalPattern]
    ) -> dict[str, Any]:
        """
        Propose delta file update for agent based on patterns.

        Args:
            agent_name: Name of agent to evolve
            patterns: Patterns suggesting evolution

        Returns:
            Evolution proposal dict with rationale, changes, evidence
        """
        # Query VectorStore for similar historical learnings
        similar_learnings = self._query_learnings(agent_name, patterns) if self.vector_store else []

        # Generate improvement suggestion
        improvement = self._generate_improvement(agent_name, patterns, similar_learnings)

        # Calculate confidence
        confidence = self._calculate_evolution_confidence(patterns, similar_learnings)

        proposal = {
            "agent_name": agent_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "function": p.function_name,
                    "frequency": p.frequency,
                    "trend": p.trend,
                }
                for p in patterns
            ],
            "improvement": improvement,
            "confidence": confidence,
            "evidence_count": len(patterns) + len(similar_learnings),
            "requires_human_approval": True,  # Article III: No bypass
        }

        return proposal

    def _query_learnings(
        self,
        agent_name: str,
        patterns: list[ConstitutionalPattern]
    ) -> list[dict[str, Any]]:
        """Query VectorStore for historical learnings about this agent."""
        if not self.vector_store:
            return []

        # Build query
        pattern_functions = ", ".join([p.function_name for p in patterns])
        query = f"{agent_name} agent improvements for {pattern_functions}"

        results = self.vector_store.combined_search(
            tags=["constitutional", "pattern", agent_name],
            query=query,
            top_k=3,
        )

        return results

    def _generate_improvement(
        self,
        agent_name: str,
        patterns: list[ConstitutionalPattern],
        learnings: list[dict[str, Any]]
    ) -> str:
        """Generate improvement suggestion for agent."""
        # Aggregate evidence
        total_violations = sum(p.frequency for p in patterns)
        articles_violated = set()
        for p in patterns:
            articles_violated.update(p.articles_violated)

        # Generate specific improvement based on violations
        if "Article I" in articles_violated or "Article II" in articles_violated:
            improvement = (
                f"**Context Loading Enhancement** (Article I/II compliance):\n"
                f"- Add explicit context validation before {patterns[0].function_name}\n"
                f"- Query VectorStore for similar successful patterns\n"
                f"- Minimum confidence: 0.6 for pattern reuse\n\n"
                f"**Evidence**: {total_violations} violations across {len(patterns)} patterns"
            )
        elif "Article V" in articles_violated:
            improvement = (
                f"**Spec Coverage Enhancement** (Article V compliance):\n"
                f"- Add spec existence check before implementation\n"
                f"- Generate missing specs for legacy features\n\n"
                f"**Evidence**: {total_violations} spec violations"
            )
        else:
            improvement = (
                f"**General Enhancement**:\n"
                f"- Review {', '.join([p.function_name for p in patterns])}\n"
                f"- {total_violations} violations suggest systematic issue\n"
                f"- Articles violated: {', '.join(articles_violated)}"
            )

        return improvement

    def _calculate_evolution_confidence(
        self,
        patterns: list[ConstitutionalPattern],
        learnings: list[dict[str, Any]]
    ) -> float:
        """Calculate confidence in evolution proposal."""
        # Base confidence from patterns
        base = sum(p.confidence for p in patterns) / len(patterns) if patterns else 0.0

        # Boost from historical learnings
        learning_boost = len(learnings) * 0.1

        # Frequency boost
        total_freq = sum(p.frequency for p in patterns)
        freq_boost = min(total_freq / 100.0, 0.2)

        confidence = min(base + learning_boost + freq_boost, 0.95)

        return round(confidence, 2)

    def generate_evolution_report(
        self,
        proposals: list[dict[str, Any]]
    ) -> str:
        """Generate human-readable evolution report."""
        if not proposals:
            return "No agent evolution proposals (no patterns with high confidence)."

        report_lines = []
        report_lines.append("\n" + "=" * 80)
        report_lines.append("CONSTITUTIONAL CONSCIOUSNESS - AGENT EVOLUTION PROPOSALS")
        report_lines.append("=" * 80)
        report_lines.append(f"\nTimestamp: {datetime.now(UTC).isoformat()}")
        report_lines.append(f"Proposals: {len(proposals)}")

        for i, proposal in enumerate(proposals, 1):
            report_lines.append(f"\n{i}. Agent: {proposal['agent_name']}")
            report_lines.append(f"   Confidence: {proposal['confidence']:.0%}")
            report_lines.append(f"   Evidence: {proposal['evidence_count']} data points")
            report_lines.append(f"   Patterns:")
            for p in proposal['patterns']:
                report_lines.append(f"      - {p['function']} ({p['frequency']} violations, {p['trend']})")
            report_lines.append(f"\n   Improvement:")
            for line in proposal['improvement'].split('\n'):
                report_lines.append(f"   {line}")
            report_lines.append(f"\n   ⚠️  Requires Human Approval (Article III)")

        report_lines.append("\n" + "=" * 80)
        report_lines.append("\nNext Steps:")
        report_lines.append("1. Review proposals above")
        report_lines.append("2. For approved changes: Update .claude/agents/{agent}-delta.md")
        report_lines.append("3. Clear instruction cache: python -c 'from shared.instruction_loader import clear_instruction_cache; clear_instruction_cache()'")
        report_lines.append("4. Test agent behavior with updated definition")
        report_lines.append("=" * 80 + "\n")

        return "\n".join(report_lines)

    def filter_high_confidence_proposals(
        self,
        proposals: list[dict[str, Any]],
        min_confidence: float = 0.8
    ) -> list[dict[str, Any]]:
        """Filter proposals by confidence threshold."""
        return [p for p in proposals if p['confidence'] >= min_confidence]
