#!/usr/bin/env python3
"""
Pydantic Refactoring Orchestration Script

Creates autonomous task breakdown for replacing all Dict[Any, Any] with Pydantic models.
Perfect for overnight 4-agent parallel execution (M4 Pro + MacBook Air).

Usage:
    python scripts/orchestrate_pydantic_refactor.py

Creates ~45 tasks organized by module:
- Analysis phase (5 tasks)
- Core modules refactoring (15 tasks)
- Tools refactoring (10 tasks)
- Tests refactoring (10 tasks)
- Integration & validation (5 tasks)

Estimated completion: 8-12 hours with 4 agents
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from meta_learning.task_queue import Task, TaskQueue


def create_pydantic_refactor_tasks():
    """Create comprehensive Pydantic refactoring task breakdown."""

    queue = TaskQueue()
    tasks = []

    print("=" * 70)
    print("🔧 PYDANTIC REFACTORING ORCHESTRATION")
    print("=" * 70)
    print()
    print("Goal: Replace all Dict[Any, Any] with typed Pydantic models")
    print("Scope: ~50-60 core files in main codebase")
    print("Agents: 4 (2 M4 Pro + 2 MacBook Air)")
    print("Est. Time: 8-12 hours (overnight)")
    print()

    # ===================================================================
    # PHASE 1: ANALYSIS & DISCOVERY (Priority 10 - Run First)
    # ===================================================================

    tasks.extend(
        [
            Task(
                task_id="pydantic-refactor-analyze-all-occurrences",
                type="spec",
                description="Analyze all Dict[Any, Any] occurrences in main codebase (exclude worktrees)",
                files_to_modify=["docs/specs/pydantic_refactor_analysis.md"],
                dependencies=[],
                priority=10,
            ),
            Task(
                task_id="pydantic-refactor-categorize-by-module",
                type="spec",
                description="Categorize Dict[Any, Any] by module (shared/, tools/, etc.)",
                files_to_modify=["docs/specs/pydantic_refactor_categories.md"],
                dependencies=["pydantic-refactor-analyze-all-occurrences"],
                priority=10,
            ),
            Task(
                task_id="pydantic-refactor-create-base-models",
                type="code",
                description="Create base Pydantic models for common patterns (Config, Metadata, Result extensions)",
                files_to_modify=["shared/models/base.py"],
                dependencies=["pydantic-refactor-categorize-by-module"],
                priority=10,
            ),
        ]
    )

    # ===================================================================
    # PHASE 2: SHARED MODULE REFACTORING (Priority 9 - Core Infrastructure)
    # ===================================================================

    shared_modules = [
        ("agent_context", "Replace Dict[Any, Any] in AgentContext with typed models"),
        ("model_policy", "Replace config dicts with PolicyConfig Pydantic model"),
        ("pattern_detector", "Replace pattern dicts with PatternMatch Pydantic model"),
        ("prompt_compression", "Replace compression metadata with CompressionResult model"),
        ("cost_tracker", "Replace cost tracking dicts with CostEntry model"),
        ("hitl_protocol", "Replace HITL data structures with HITLRequest/HITLResponse models"),
    ]

    for _idx, (module, desc) in enumerate(shared_modules):
        tasks.append(
            Task(
                task_id=f"pydantic-refactor-shared-{module}",
                type="code",
                description=desc,
                files_to_modify=[f"shared/{module}.py"],
                dependencies=["pydantic-refactor-create-base-models"],
                priority=9,
            )
        )

    # ===================================================================
    # PHASE 3: TOOLS REFACTORING (Priority 8 - Can Run in Parallel with Phase 2)
    # ===================================================================

    tools_modules = [
        ("git_unified", "Replace git operation results with GitOperationResult model"),
        ("document_generator", "Replace doc metadata with DocumentMetadata model"),
        ("property_testing", "Replace test config with PropertyTestConfig model"),
        (
            "constitutional_consciousness/models",
            "Replace consciousness state with TypedState model",
        ),
    ]

    for _idx, (module, desc) in enumerate(tools_modules):
        tasks.append(
            Task(
                task_id=f"pydantic-refactor-tools-{module.replace('/', '-')}",
                type="code",
                description=desc,
                files_to_modify=[f"tools/{module}.py"],
                dependencies=["pydantic-refactor-create-base-models"],
                priority=8,
            )
        )

    # ===================================================================
    # PHASE 4: AGENT MODULES REFACTORING (Priority 7)
    # ===================================================================

    agent_modules = [
        ("quality_enforcer", "Replace quality check results with QualityCheckResult model"),
        ("planner", "Replace plan metadata with PlanMetadata model"),
        ("code_agent", "Replace implementation metadata with CodeMetadata model"),
    ]

    for _idx, (module, desc) in enumerate(agent_modules):
        tasks.append(
            Task(
                task_id=f"pydantic-refactor-agent-{module}",
                type="code",
                description=desc,
                files_to_modify=[f"{module}_agent/{module}_agent.py"],
                dependencies=["pydantic-refactor-shared-agent_context"],
                priority=7,
            )
        )

    # ===================================================================
    # PHASE 5: TESTS GENERATION (Priority 6 - After Implementation)
    # ===================================================================

    test_modules = [
        ("shared/models", "Unit tests for all new Pydantic models (base, config, metadata)"),
        ("shared/agent_context", "Integration tests for AgentContext with typed models"),
        ("tools/git_unified", "Tests for GitOperationResult model"),
        ("tools/document_generator", "Tests for DocumentMetadata model"),
    ]

    for _idx, (module, desc) in enumerate(test_modules):
        tasks.append(
            Task(
                task_id=f"pydantic-refactor-test-{module.replace('/', '-')}",
                type="test",
                description=desc,
                files_to_modify=[f"tests/{module.replace('/', '/test_')}.py"],
                dependencies=[
                    f"pydantic-refactor-{module.split('/')[0]}-{module.split('/')[-1] if '/' in module else module}"
                ],
                priority=6,
            )
        )

    # ===================================================================
    # PHASE 6: TYPE SAFETY VALIDATION (Priority 5)
    # ===================================================================

    tasks.extend(
        [
            Task(
                task_id="pydantic-refactor-mypy-validation",
                type="test",
                description="Run mypy on all refactored modules, ensure 100% type safety",
                files_to_modify=["tests/test_pydantic_type_safety.py"],
                dependencies=[t.task_id for t in tasks if t.type == "code"],
                priority=5,
            ),
            Task(
                task_id="pydantic-refactor-verify-no-any",
                type="test",
                description="Grep verification: ensure no Dict[Any, Any] in main codebase",
                files_to_modify=["tests/test_no_dict_any_any.py"],
                dependencies=["pydantic-refactor-mypy-validation"],
                priority=5,
            ),
        ]
    )

    # ===================================================================
    # PHASE 7: INTEGRATION & DOCUMENTATION (Priority 4-1)
    # ===================================================================

    tasks.extend(
        [
            Task(
                task_id="pydantic-refactor-integration-tests",
                type="test",
                description="End-to-end integration tests: AgentContext → Tools → Agents workflow",
                files_to_modify=["tests/integration/test_pydantic_refactor_e2e.py"],
                dependencies=["pydantic-refactor-verify-no-any"],
                priority=4,
            ),
            Task(
                task_id="pydantic-refactor-docs-migration-guide",
                type="doc",
                description="Create migration guide for developers using old Dict[Any, Any] patterns",
                files_to_modify=["docs/PYDANTIC_MIGRATION_GUIDE.md"],
                dependencies=["pydantic-refactor-integration-tests"],
                priority=3,
            ),
            Task(
                task_id="pydantic-refactor-docs-model-reference",
                type="doc",
                description="Create API reference for all new Pydantic models",
                files_to_modify=["docs/api/pydantic_models.md"],
                dependencies=["pydantic-refactor-docs-migration-guide"],
                priority=2,
            ),
            Task(
                task_id="pydantic-refactor-final-validation",
                type="integrate",
                description="Run full test suite, update README, create summary report",
                files_to_modify=["README.md", "docs/PYDANTIC_REFACTOR_SUMMARY.md"],
                dependencies=["pydantic-refactor-docs-model-reference"],
                priority=1,
            ),
        ]
    )

    # Add all tasks to queue
    print(f"📝 Creating {len(tasks)} tasks...")
    queue.add_tasks_batch(tasks)

    print()
    print("=" * 70)
    print("✅ TASKS CREATED SUCCESSFULLY")
    print("=" * 70)
    print()
    print(f"Total tasks: {len(tasks)}")
    print()
    print("Task breakdown:")
    print("  Phase 1 (Analysis):         3 tasks")
    print(f"  Phase 2 (Shared modules):   {len(shared_modules)} tasks")
    print(f"  Phase 3 (Tools):            {len(tools_modules)} tasks")
    print(f"  Phase 4 (Agents):           {len(agent_modules)} tasks")
    print(f"  Phase 5 (Tests):            {len(test_modules)} tasks")
    print("  Phase 6 (Validation):       2 tasks")
    print("  Phase 7 (Integration):      4 tasks")
    print()
    print("Estimated completion: 8-12 hours with 4 agents")
    print()
    print("=" * 70)
    print("🚀 READY FOR AUTONOMOUS EXECUTION")
    print("=" * 70)
    print()
    print("Next steps:")
    print()
    print("1. Start all 4 agents:")
    print("   On M4 Pro:")
    print("     ./scripts/start_all_agents.sh")
    print()
    print("   On MacBook Air:")
    print("     ./scripts/start_agents_mba.sh")
    print()
    print("2. Monitor progress:")
    print("   python scripts/monitor_agents.py")
    print()
    print("3. Go to sleep! 😴")
    print()
    print("4. Morning: Check results:")
    print("   python scripts/check_status.py")
    print()
    print("=" * 70)


if __name__ == "__main__":
    create_pydantic_refactor_tasks()
