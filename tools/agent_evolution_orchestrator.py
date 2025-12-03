"""
Agent Evolution Orchestrator - Autonomous Agent Self-Improvement

Orchestrates the agent self-improvement pipeline per .claude/commands/agent-self-improve.md:
1. Read agent definitions from .claude/agents/
2. Score against Gold Standard Checklist (10 criteria)
3. Generate improvement proposals
4. Submit to .claude/proposals/ for Architect review
5. Log evolution events to CMP/VectorStore

Constitutional Compliance:
- Article IV: Store improvement patterns in VectorStore after success
- Article III: No bypass of quality gates, proposals require approval

Usage:
    # Run improvement cycle for specific agent
    python tools/agent_evolution_orchestrator.py --agent code_agent

    # Run improvement cycle for all agents
    python tools/agent_evolution_orchestrator.py --all

    # Weekly scheduled run (via Night Shift)
    python tools/agent_evolution_orchestrator.py --scheduled
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)

# Gold Standard Checklist criteria (from agent-self-improve.md)
GOLD_STANDARD_CHECKLIST = [
    "constitutional_articles",      # All 5 articles explicitly enforced
    "agent_tools_integration",      # All 5 agent tools integrated
    "numbered_workflow_steps",      # Minimum 5 numbered workflow steps
    "json_message_formats",         # JSON message format examples
    "agent_context_patterns",       # AgentContext usage with code
    "performance_metrics",          # Performance metrics defined
    "self_assessment_capabilities", # Self-assessment capabilities
    "necessary_pattern_compliance", # NECESSARY pattern (9 categories)
    "communication_protocols",      # Communication with other agents
    "error_handling_patterns",      # Error handling with Result<T,E>
]


@dataclass
class AgentScore:
    """Score for a single agent against Gold Standard."""

    agent_name: str
    scores: dict[str, int] = field(default_factory=dict)  # criterion -> score (0-10)
    total_score: int = 0
    max_score: int = 100
    gaps: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)

    def calculate_total(self) -> None:
        """Calculate total score from individual criteria."""
        self.total_score = sum(self.scores.values())


@dataclass
class ImprovementProposal:
    """Structured improvement proposal."""

    proposal_id: str
    agent_name: str
    title: str
    current_state: str
    gap_impact: dict[str, str]  # performance, alignment, safety, value
    proposed_solution: str
    implementation_diff: str
    expected_benefits: list[str]
    risk_assessment: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    estimated_hours: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentEvolutionOrchestrator:
    """
    Orchestrates agent self-improvement cycles.

    Workflow:
    1. Discover agent definitions
    2. Score each agent against Gold Standard
    3. Identify gaps and generate proposals
    4. Save proposals for Architect review
    5. Log evolution events to VectorStore
    """

    def __init__(
        self,
        agents_dir: Optional[Path] = None,
        proposals_dir: Optional[Path] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            agents_dir: Path to agent definitions (default: .claude/agents/)
            proposals_dir: Path to proposals (default: .claude/proposals/)
        """
        project_root = Path(__file__).parent.parent

        self.agents_dir = agents_dir or (project_root / ".claude" / "agents")
        self.proposals_dir = proposals_dir or (project_root / ".claude" / "proposals")

        # Ensure proposals directory exists
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        (self.proposals_dir / "approved").mkdir(exist_ok=True)
        (self.proposals_dir / "rejected").mkdir(exist_ok=True)

    def discover_agents(self) -> list[str]:
        """
        Discover agent definition files.

        Returns:
            List of agent names (without .md extension)
        """
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return []

        agents = []
        for agent_file in self.agents_dir.glob("*.md"):
            # Skip README and non-agent files
            if agent_file.stem.lower() in ["readme", "index", "template"]:
                continue
            agents.append(agent_file.stem)

        return sorted(agents)

    def read_agent_definition(self, agent_name: str) -> Result[str, str]:
        """
        Read agent definition file.

        Args:
            agent_name: Name of the agent (without .md)

        Returns:
            Result containing definition content or error
        """
        agent_file = self.agents_dir / f"{agent_name}.md"

        if not agent_file.exists():
            return Err(f"Agent definition not found: {agent_file}")

        try:
            content = agent_file.read_text()
            return Ok(content)
        except Exception as e:
            return Err(f"Failed to read agent definition: {e}")

    def score_agent(self, agent_name: str, definition: str) -> AgentScore:
        """
        Score an agent against the Gold Standard Checklist.

        Args:
            agent_name: Name of the agent
            definition: Agent definition content

        Returns:
            AgentScore with criteria scores and gaps
        """
        score = AgentScore(agent_name=agent_name)
        definition_lower = definition.lower()

        # Score each criterion (0-10)
        criteria_checks = {
            "constitutional_articles": [
                "article i", "article ii", "article iii", "article iv", "article v"
            ],
            "agent_tools_integration": [
                "/agent-memory-query", "/agent-memory-store", "/agent-adr-query",
                "/agent-test-verify", "/agent-diff-review"
            ],
            "numbered_workflow_steps": [
                "step 1", "step 2", "step 3", "step 4", "step 5", "## workflow"
            ],
            "json_message_formats": [
                "```json", "{", "message format", "protocol"
            ],
            "agent_context_patterns": [
                "agentcontext", "context.store_memory", "context.search_memories",
                "create_agent_context"
            ],
            "performance_metrics": [
                "metric", "success rate", "performance", "kpi", "target"
            ],
            "self_assessment_capabilities": [
                "self-assess", "evaluate", "introspect", "reflect"
            ],
            "necessary_pattern_compliance": [
                "necessary", "nice-to-have", "requirement", "essential"
            ],
            "communication_protocols": [
                "handoff", "message", "communicate", "protocol", "other agent"
            ],
            "error_handling_patterns": [
                "result<", "ok(", "err(", "error handling", "exception"
            ],
        }

        for criterion, keywords in criteria_checks.items():
            matches = sum(1 for kw in keywords if kw in definition_lower)
            criterion_score = min(10, matches * 2)  # 2 points per match, max 10
            score.scores[criterion] = criterion_score

            if criterion_score >= 8:
                score.strengths.append(criterion)
            elif criterion_score <= 4:
                score.gaps.append(criterion)

        score.calculate_total()
        return score

    def generate_proposals(
        self, agent_name: str, score: AgentScore
    ) -> list[ImprovementProposal]:
        """
        Generate improvement proposals based on gaps.

        Args:
            agent_name: Name of the agent
            score: Agent's current score

        Returns:
            List of improvement proposals
        """
        proposals = []

        # Generate proposal for each gap
        for i, gap in enumerate(score.gaps, 1):
            priority = "CRITICAL" if score.scores.get(gap, 0) <= 2 else "HIGH"

            proposal = ImprovementProposal(
                proposal_id=f"{agent_name}-{gap}-{datetime.now().strftime('%Y%m%d')}",
                agent_name=agent_name,
                title=f"Improve {gap.replace('_', ' ').title()} for {agent_name}",
                current_state=f"Score: {score.scores.get(gap, 0)}/10 on {gap}",
                gap_impact={
                    "performance": f"Reduced effectiveness due to missing {gap}",
                    "alignment": "May not follow best practices",
                    "safety": "No direct safety impact" if gap != "error_handling_patterns" else "Critical for safe operation",
                    "value": "Reduced code quality and maintainability",
                },
                proposed_solution=self._get_solution_for_gap(gap, agent_name),
                implementation_diff=self._get_diff_for_gap(gap, agent_name),
                expected_benefits=[
                    f"+{10 - score.scores.get(gap, 0)} points on {gap}",
                    "Improved constitutional compliance",
                    "Better integration with AgencyOS patterns",
                ],
                risk_assessment="Low risk - additive improvements only",
                priority=priority,
                estimated_hours=2.0 if priority == "CRITICAL" else 4.0,
            )
            proposals.append(proposal)

        return proposals

    def _get_solution_for_gap(self, gap: str, agent_name: str) -> str:
        """Generate solution description for a specific gap."""
        solutions = {
            "constitutional_articles": (
                f"Add explicit sections for Articles I-V in {agent_name}.md with "
                "enforcement workflows and compliance checks."
            ),
            "agent_tools_integration": (
                "Add integration examples for all 5 agent tools: "
                "/agent-memory-query, /agent-memory-store, /agent-adr-query, "
                "/agent-test-verify, /agent-diff-review"
            ),
            "numbered_workflow_steps": (
                "Add a '## Workflow' section with at least 5 numbered steps "
                "documenting the agent's execution flow."
            ),
            "json_message_formats": (
                "Add JSON examples for inter-agent communication protocols "
                "and message schemas."
            ),
            "agent_context_patterns": (
                "Add AgentContext usage examples showing store_memory() and "
                "search_memories() calls for Article IV compliance."
            ),
            "performance_metrics": (
                "Define KPIs and success metrics for the agent's operations "
                "(e.g., success rate, coverage, velocity)."
            ),
            "self_assessment_capabilities": (
                "Add self-assessment section describing how the agent "
                "evaluates its own performance."
            ),
            "necessary_pattern_compliance": (
                "Document which requirements are NECESSARY vs nice-to-have "
                "using the NECESSARY pattern."
            ),
            "communication_protocols": (
                "Add section describing handoff protocols with other agents "
                "in the AgencyOS ecosystem."
            ),
            "error_handling_patterns": (
                "Add Result<T,E> pattern examples and error handling workflows "
                "per ADR-010."
            ),
        }
        return solutions.get(gap, f"Address the {gap} gap with appropriate documentation.")

    def _get_diff_for_gap(self, gap: str, agent_name: str) -> str:
        """Generate implementation diff for a specific gap."""
        return f"""```diff
+ ## {gap.replace('_', ' ').title()}
+
+ [Add content for {gap} in {agent_name}.md]
+
+ ### Example
+
+ [Add practical example demonstrating {gap}]
```"""

    def save_proposal(self, proposal: ImprovementProposal) -> Result[Path, str]:
        """
        Save a proposal to the proposals directory.

        Args:
            proposal: The proposal to save

        Returns:
            Result containing the file path or error
        """
        filename = f"{proposal.proposal_id}.md"
        filepath = self.proposals_dir / filename

        content = f"""# Agent Improvement Proposal: {proposal.title}

**Agent**: {proposal.agent_name}
**Proposal ID**: {proposal.proposal_id}
**Priority**: {proposal.priority}
**Estimated Hours**: {proposal.estimated_hours}
**Created**: {proposal.created_at}

## Current State

{proposal.current_state}

## Gap Impact

| Dimension | Impact |
|-----------|--------|
| Performance | {proposal.gap_impact.get('performance', 'N/A')} |
| Alignment | {proposal.gap_impact.get('alignment', 'N/A')} |
| Safety | {proposal.gap_impact.get('safety', 'N/A')} |
| Value | {proposal.gap_impact.get('value', 'N/A')} |

## Proposed Solution

{proposal.proposed_solution}

## Implementation

{proposal.implementation_diff}

## Expected Benefits

{chr(10).join(f'- {b}' for b in proposal.expected_benefits)}

## Risk Assessment

{proposal.risk_assessment}

---

**Status**: PENDING REVIEW
**Reviewer**: Chief Architect
"""

        try:
            filepath.write_text(content)

            # Update review queue
            queue_file = self.proposals_dir / "review_queue.txt"
            with open(queue_file, "a") as f:
                f.write(f"{datetime.now().isoformat()} - NEW: {proposal.proposal_id}\n")

            return Ok(filepath)
        except Exception as e:
            return Err(f"Failed to save proposal: {e}")

    def run_improvement_cycle(
        self, agent_names: Optional[list[str]] = None
    ) -> Result[dict, str]:
        """
        Run a complete improvement cycle for specified agents.

        Args:
            agent_names: List of agent names (None = all agents)

        Returns:
            Result containing cycle results or error
        """
        if agent_names is None:
            agent_names = self.discover_agents()

        if not agent_names:
            return Err("No agents found to process")

        results = {
            "agents_processed": 0,
            "proposals_generated": 0,
            "total_gaps_found": 0,
            "agent_scores": {},
            "proposals": [],
            "timestamp": datetime.now().isoformat(),
        }

        for agent_name in agent_names:
            logger.info(f"Processing agent: {agent_name}")

            # Read definition
            definition_result = self.read_agent_definition(agent_name)
            if definition_result.is_err():
                logger.warning(f"Skipping {agent_name}: {definition_result.unwrap_err()}")
                continue

            definition = definition_result.unwrap()

            # Score agent
            score = self.score_agent(agent_name, definition)
            results["agent_scores"][agent_name] = {
                "total": score.total_score,
                "gaps": score.gaps,
                "strengths": score.strengths,
            }
            results["total_gaps_found"] += len(score.gaps)

            # Generate proposals for gaps
            if score.gaps:
                proposals = self.generate_proposals(agent_name, score)
                for proposal in proposals:
                    save_result = self.save_proposal(proposal)
                    if save_result.is_ok():
                        results["proposals"].append(proposal.proposal_id)
                        results["proposals_generated"] += 1

            results["agents_processed"] += 1

        # Log to VectorStore (Article IV)
        self._log_to_vectorstore(results)

        return Ok(results)

    def _log_to_vectorstore(self, results: dict) -> None:
        """Log evolution event to VectorStore for Article IV compliance."""
        try:
            # Use AgentContext for VectorStore integration
            from shared.agent_context import create_agent_context

            context = create_agent_context(session_id=f"evolution-{datetime.now().strftime('%Y%m%d')}")
            context.store_memory(
                key=f"evolution_cycle_{datetime.now().isoformat()}",
                content={
                    "type": "agent_evolution_cycle",
                    "results": results,
                    "agents_processed": results["agents_processed"],
                    "proposals_generated": results["proposals_generated"],
                },
                tags=["evolution", "agent_improvement", "cmp"],
            )
            logger.info("Evolution event logged to VectorStore")
        except Exception as e:
            logger.warning(f"Failed to log to VectorStore: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Evolution Orchestrator - Autonomous Self-Improvement"
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Specific agent to process (default: all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all discovered agents",
    )
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Running as scheduled task (Night Shift)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize orchestrator
    orchestrator = AgentEvolutionOrchestrator()

    # Determine agents to process
    agent_names = None
    if args.agent:
        agent_names = [args.agent]

    # Run improvement cycle
    print("\n" + "=" * 60)
    print("AGENT EVOLUTION ORCHESTRATOR")
    print("=" * 60)

    if args.scheduled:
        print("Mode: Scheduled (Night Shift)")
    elif args.agent:
        print(f"Mode: Single Agent ({args.agent})")
    else:
        print("Mode: All Agents")

    print("-" * 60)

    result = orchestrator.run_improvement_cycle(agent_names)

    if result.is_ok():
        data = result.unwrap()
        print(f"\n✅ Evolution cycle complete!")
        print(f"   Agents processed: {data['agents_processed']}")
        print(f"   Gaps found: {data['total_gaps_found']}")
        print(f"   Proposals generated: {data['proposals_generated']}")

        if data["agent_scores"]:
            print("\n📊 Agent Scores:")
            for agent, scores in data["agent_scores"].items():
                status = "✅" if scores["total"] >= 80 else "⚠️" if scores["total"] >= 60 else "❌"
                print(f"   {status} {agent}: {scores['total']}/100")
                if scores["gaps"]:
                    print(f"      Gaps: {', '.join(scores['gaps'][:3])}")

        if data["proposals"]:
            print(f"\n📋 Proposals saved to .claude/proposals/")
            print(f"   Review with: /architect-review-proposals")

        sys.exit(0)
    else:
        print(f"\n❌ Evolution cycle failed: {result.unwrap_err()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
