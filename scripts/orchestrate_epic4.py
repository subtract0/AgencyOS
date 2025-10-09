#!/usr/bin/env python3
"""
Master Orchestrator for EPIC 4.2 Implementation

Single command to populate task queue with zero-conflict task breakdown.
This is the ONLY thing you need to run to start autonomous multi-agent execution!

EPIC 4.2 Extension: Autonomous Multi-Agent Orchestration

Usage:
    # Populate queue with EPIC 4.2 tasks
    python scripts/orchestrate_epic4.py --phase epic4.2-complete

    # Then start your agents in separate terminals:
    python scripts/autonomous_worker.py --agent-id m4pro-agent1
    python scripts/autonomous_worker.py --agent-id m4pro-agent2
    python scripts/autonomous_worker.py --agent-id mba-agent1
    python scripts/autonomous_worker.py --agent-id mba-agent2

Constitutional Compliance:
- Article I: Complete dependency graph ensures proper ordering
- Article III: Fully automated (no manual intervention needed)
- Article V: Spec-driven (tasks trace to EPIC 4.2 specification)

Version: 1.0.0
Created: 2025-10-09
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from meta_learning.task_queue import Task, TaskQueue


class MasterOrchestrator:
    """
    Master controller that defines complete task breakdowns.

    This is YOUR control point - one command, entire system works autonomously.

    Tasks are designed to NEVER conflict:
    - Different files per task (no overlap)
    - Clear dependencies (proper ordering)
    - Parallel-safe design (independent tasks can run simultaneously)

    Constitutional Compliance:
        - Article I: Dependency graph ensures complete context
        - Article III: Zero manual intervention
        - Article V: Spec-driven task definitions
    """

    def __init__(self):
        """Initialize orchestrator with task queue."""
        self.queue = TaskQueue()

    def orchestrate_epic4_2(self):
        """
        Define all tasks for EPIC 4.2 Component 4 (Proposal Generator).

        Task breakdown ensures zero conflicts:
        - Spec tasks (parallel): Different files
        - Code tasks (sequential): Depend on specs
        - Test tasks (sequential): Depend on code
        - Integration (final): Depends on all

        Returns:
            Number of tasks added
        """
        print("=" * 60)
        print("🎯 EPIC 4.2 Component 4: Proposal Generator")
        print("=" * 60)
        print()

        tasks = []

        # ===== PHASE 1: SPECIFICATIONS (Parallel-Safe) =====

        tasks.append(
            Task(
                task_id="epic4.2-spec-proposal-generator",
                type="spec",
                description="Create specification for ProposalGenerator with statistical analysis",
                files_to_modify=["docs/specs/proposal_generator_spec.md"],
                dependencies=[],
                priority=10,  # High priority (foundation)
            )
        )

        tasks.append(
            Task(
                task_id="epic4.2-spec-adr-template",
                type="spec",
                description="Create ADR template structure with evidence and rollback sections",
                files_to_modify=["docs/adr/TEMPLATE_v2.md"],
                dependencies=[],
                priority=10,  # High priority (foundation)
            )
        )

        tasks.append(
            Task(
                task_id="epic4.2-spec-integration-workflow",
                type="spec",
                description="Define integration workflow for A/B results → ADR generation",
                files_to_modify=["docs/specs/integration_workflow.md"],
                dependencies=[],
                priority=9,
            )
        )

        # ===== PHASE 2: IMPLEMENTATION (Depends on Specs) =====

        tasks.append(
            Task(
                task_id="epic4.2-code-proposal-models",
                type="code",
                description="Implement Pydantic models (ProposalReport, AgentMetrics, ComparisonResult)",
                files_to_modify=["meta_learning/models.py", "meta_learning/__init__.py"],
                dependencies=["epic4.2-spec-proposal-generator"],
                priority=8,
            )
        )

        tasks.append(
            Task(
                task_id="epic4.2-code-statistical-analysis",
                type="code",
                description="Implement statistical analysis (t-test, confidence intervals, scipy integration)",
                files_to_modify=["meta_learning/statistical_analysis.py"],
                dependencies=["epic4.2-code-proposal-models"],
                priority=7,
            )
        )

        tasks.append(
            Task(
                task_id="epic4.2-code-proposal-generator",
                type="code",
                description="Implement ProposalGenerator class with analyze_results and generate_adr methods",
                files_to_modify=["meta_learning/proposal_generator_v2.py"],
                dependencies=["epic4.2-code-statistical-analysis", "epic4.2-spec-adr-template"],
                priority=6,
            )
        )

        # ===== PHASE 3: TESTING (Depends on Code) =====

        tasks.append(
            Task(
                task_id="epic4.2-test-statistical-analysis",
                type="test",
                description="Write tests for statistical functions (t-test, confidence intervals)",
                files_to_modify=["tests/meta_learning/test_statistical_analysis.py"],
                dependencies=["epic4.2-code-statistical-analysis"],
                priority=5,
            )
        )

        tasks.append(
            Task(
                task_id="epic4.2-test-proposal-generator",
                type="test",
                description="Write comprehensive tests for ProposalGenerator (15+ tests)",
                files_to_modify=["tests/meta_learning/test_proposal_generator_v2.py"],
                dependencies=["epic4.2-code-proposal-generator"],
                priority=5,
            )
        )

        tasks.append(
            Task(
                task_id="epic4.2-test-integration",
                type="test",
                description="Write end-to-end integration tests (A/B results → ADR)",
                files_to_modify=["tests/integration/test_proposal_workflow.py"],
                dependencies=[
                    "epic4.2-test-proposal-generator",
                    "epic4.2-spec-integration-workflow",
                ],
                priority=4,
            )
        )

        # ===== PHASE 4: DOCUMENTATION & DEMO (Parallel with testing) =====

        tasks.append(
            Task(
                task_id="epic4.2-doc-user-guide",
                type="doc",
                description="Create user guide for Proposal Generator (usage examples, API reference)",
                files_to_modify=["docs/proposal_generator_guide.md"],
                dependencies=["epic4.2-code-proposal-generator"],
                priority=3,
            )
        )

        tasks.append(
            Task(
                task_id="epic4.2-demo-proposal-workflow",
                type="code",
                description="Create interactive demo showing complete A/B → Proposal → ADR workflow",
                files_to_modify=["demos/proposal_workflow_demo.py"],
                dependencies=["epic4.2-code-proposal-generator"],
                priority=2,
            )
        )

        # ===== PHASE 5: INTEGRATION (Depends on ALL) =====

        tasks.append(
            Task(
                task_id="epic4.2-integrate-final",
                type="integrate",
                description="Run full test suite, update README, create summary PR",
                files_to_modify=["README.md", "docs/EPIC_4.2_SUMMARY.md"],
                dependencies=[
                    "epic4.2-test-integration",
                    "epic4.2-doc-user-guide",
                    "epic4.2-demo-proposal-workflow",
                ],
                priority=1,
            )
        )

        # Add all tasks in batch (atomic operation)
        self.queue.add_tasks_batch(tasks)

        # Print dependency graph
        print("✅ Task queue populated with", len(tasks), "tasks\n")
        print("Dependency Graph:")
        print("=" * 60)
        print()
        print("PHASE 1: Specifications (Parallel)")
        print("  ├─ epic4.2-spec-proposal-generator")
        print("  ├─ epic4.2-spec-adr-template")
        print("  └─ epic4.2-spec-integration-workflow")
        print()
        print("PHASE 2: Implementation (Sequential)")
        print("  ├─ epic4.2-code-proposal-models")
        print("  │   └─ epic4.2-code-statistical-analysis")
        print("  │       └─ epic4.2-code-proposal-generator")
        print()
        print("PHASE 3: Testing (Sequential)")
        print("  ├─ epic4.2-test-statistical-analysis")
        print("  ├─ epic4.2-test-proposal-generator")
        print("  └─ epic4.2-test-integration")
        print()
        print("PHASE 4: Documentation (Parallel)")
        print("  ├─ epic4.2-doc-user-guide")
        print("  └─ epic4.2-demo-proposal-workflow")
        print()
        print("PHASE 5: Integration (Final)")
        print("  └─ epic4.2-integrate-final")
        print()
        print("=" * 60)

        return len(tasks)

    def orchestrate_medi_pack_v1(self):
        """
        Define tasks for Medi-Pack v1 (Scout/Plan/Build Architecture).

        Returns:
            Number of tasks added
        """
        print("=" * 60)
        print("🎯 Medi-Pack v1: Scout/Plan/Build Architecture")
        print("=" * 60)
        print()

        tasks = []

        # ===== PHASE 1: SCOUT FLEET =====

        tasks.append(
            Task(
                task_id="medi-v1-spec-scout-fleet",
                type="spec",
                description="Create specification for Scout Fleet (parallel context gathering)",
                files_to_modify=["docs/specs/scout_fleet_spec.md"],
                dependencies=[],
                priority=10,
            )
        )

        tasks.append(
            Task(
                task_id="medi-v1-code-scout-fleet",
                type="code",
                description="Implement ScoutFleet class with parallel deployment",
                files_to_modify=["dspy_agents/scout_fleet.py", "dspy_agents/__init__.py"],
                dependencies=["medi-v1-spec-scout-fleet"],
                priority=9,
            )
        )

        tasks.append(
            Task(
                task_id="medi-v1-code-context-consolidator",
                type="code",
                description="Implement ContextConsolidator for merging scout outputs",
                files_to_modify=["dspy_agents/context_consolidator.py"],
                dependencies=["medi-v1-code-scout-fleet"],
                priority=8,
            )
        )

        # ===== PHASE 2: PLANNER PHASE =====

        tasks.append(
            Task(
                task_id="medi-v1-spec-planner-phase",
                type="spec",
                description="Create specification for Planner Phase (execution plan generation)",
                files_to_modify=["docs/specs/planner_phase_spec.md"],
                dependencies=[],
                priority=10,
            )
        )

        tasks.append(
            Task(
                task_id="medi-v1-code-planner-phase",
                type="code",
                description="Implement PlannerPhase class with filtered context",
                files_to_modify=["dspy_agents/planner_phase.py"],
                dependencies=["medi-v1-spec-planner-phase", "medi-v1-code-context-consolidator"],
                priority=7,
            )
        )

        # ===== PHASE 3: BUILDER PHASE =====

        tasks.append(
            Task(
                task_id="medi-v1-spec-builder-phase",
                type="spec",
                description="Create specification for Builder Phase (plan execution)",
                files_to_modify=["docs/specs/builder_phase_spec.md"],
                dependencies=[],
                priority=10,
            )
        )

        tasks.append(
            Task(
                task_id="medi-v1-code-builder-phase",
                type="code",
                description="Implement BuilderPhase class with step validation",
                files_to_modify=["dspy_agents/builder_phase.py"],
                dependencies=["medi-v1-spec-builder-phase"],
                priority=6,
            )
        )

        # ===== PHASE 4: MASTER ORCHESTRATOR =====

        tasks.append(
            Task(
                task_id="medi-v1-code-scout-plan-build-orchestrator",
                type="code",
                description="Implement ScoutPlanBuildOrchestrator (master coordinator)",
                files_to_modify=["dspy_agents/scout_plan_build_orchestrator.py"],
                dependencies=["medi-v1-code-planner-phase", "medi-v1-code-builder-phase"],
                priority=5,
            )
        )

        # ===== PHASE 5: TESTING & INTEGRATION =====

        tasks.append(
            Task(
                task_id="medi-v1-test-complete",
                type="test",
                description="Write comprehensive tests for all Medi-Pack v1 components",
                files_to_modify=[
                    "tests/dspy_agents/test_scout_fleet.py",
                    "tests/dspy_agents/test_planner_phase.py",
                    "tests/dspy_agents/test_builder_phase.py",
                    "tests/dspy_agents/test_scout_plan_build.py",
                ],
                dependencies=["medi-v1-code-scout-plan-build-orchestrator"],
                priority=4,
            )
        )

        tasks.append(
            Task(
                task_id="medi-v1-integrate-final",
                type="integrate",
                description="Run benchmarks, update docs, create Medi-Pack v1 summary",
                files_to_modify=["docs/MEDI_PACK_V1_GUIDE.md", "README.md"],
                dependencies=["medi-v1-test-complete"],
                priority=1,
            )
        )

        # Add all tasks
        self.queue.add_tasks_batch(tasks)

        print("✅ Medi-Pack v1 tasks added:", len(tasks), "tasks\n")

        return len(tasks)

    def show_instructions(self):
        """Print instructions for starting agents."""
        print()
        print("=" * 60)
        print("🚀 NEXT STEPS: Start Your Autonomous Agents")
        print("=" * 60)
        print()
        print("Terminal 1 (M4 Pro):")
        print("  python scripts/autonomous_worker.py --agent-id m4pro-agent1")
        print()
        print("Terminal 2 (M4 Pro):")
        print("  python scripts/autonomous_worker.py --agent-id m4pro-agent2")
        print()
        print("Terminal 3 (MacBook Air):")
        print("  python scripts/autonomous_worker.py --agent-id mba-agent1")
        print()
        print("Terminal 4 (MacBook Air):")
        print("  python scripts/autonomous_worker.py --agent-id mba-agent2")
        print()
        print("=" * 60)
        print("📊 Monitor Progress:")
        print("=" * 60)
        print()
        print("  watch -n 5 'python meta_learning/task_queue.py status'")
        print()
        print("Or manually check:")
        print("  python meta_learning/task_queue.py status")
        print()
        print("=" * 60)
        print("☕ Go make coffee - agents work autonomously!")
        print("=" * 60)
        print()


# CLI Interface
def main():
    """Command-line interface for master orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Master orchestrator for autonomous multi-agent execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # EPIC 4.2 Component 4
  %(prog)s --phase epic4.2-complete

  # Medi-Pack v1
  %(prog)s --phase medi-pack-v1

  # Both phases
  %(prog)s --phase both

After running, start your autonomous agents in separate terminals.
        """,
    )

    parser.add_argument(
        "--phase",
        choices=["epic4.2-complete", "medi-pack-v1", "both"],
        required=True,
        help="Which phase to orchestrate",
    )

    parser.add_argument(
        "--clear", action="store_true", help="Clear existing queue before adding tasks"
    )

    args = parser.parse_args()

    orchestrator = MasterOrchestrator()

    # Clear queue if requested
    if args.clear:
        print("🗑️  Clearing existing task queue...\n")
        orchestrator.queue.clear_queue()

    # Orchestrate selected phase(s)
    total_tasks = 0

    if args.phase in ["epic4.2-complete", "both"]:
        total_tasks += orchestrator.orchestrate_epic4_2()

    if args.phase in ["medi-pack-v1", "both"]:
        total_tasks += orchestrator.orchestrate_medi_pack_v1()

    # Show instructions
    orchestrator.show_instructions()

    print(f"✅ Total tasks queued: {total_tasks}")
    print()


if __name__ == "__main__":
    main()
