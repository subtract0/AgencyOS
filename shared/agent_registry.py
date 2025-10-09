"""Agent Capability Registry - ADR-023 Implementation."""

from enum import Enum
from typing import Literal
from pydantic import BaseModel


class AgentCapability(str, Enum):
    """Agent capabilities for task routing."""

    SPEC_CREATION = "spec_creation"
    PLAN_GENERATION = "plan_generation"
    ARCHITECTURE_DECISION = "architecture_decision"
    CODE_IMPLEMENTATION = "code_implementation"
    TEST_GENERATION = "test_generation"
    TOOL_DEVELOPMENT = "tool_development"
    CODE_AUDIT = "code_audit"
    QUALITY_ENFORCEMENT = "quality_enforcement"
    CONSTITUTIONAL_VALIDATION = "constitutional_validation"
    GIT_WORKFLOW = "git_workflow"
    PR_MANAGEMENT = "pr_management"
    PATTERN_LEARNING = "pattern_learning"
    SESSION_ANALYSIS = "session_analysis"
    E2E_ORCHESTRATION = "e2e_orchestration"
    WORK_SUMMARIZATION = "work_summarization"


class AgentMetadata(BaseModel):
    """Agent capabilities and constraints."""

    name: str
    role: str
    capabilities: list[AgentCapability]
    parallel_safe: bool
    dependencies: list[str]
    preferred_model: Literal["gpt-5", "gpt-5-mini", "local"]
    avg_execution_time_minutes: float
    success_rate: float


AGENT_REGISTRY: dict[str, AgentMetadata] = {
    "spec_generator": AgentMetadata(
        name="spec_generator",
        role="Requirements analyst",
        capabilities=[AgentCapability.SPEC_CREATION],
        parallel_safe=True,
        dependencies=[],
        preferred_model="gpt-5",
        avg_execution_time_minutes=15.0,
        success_rate=0.95,
    ),
    "planner": AgentMetadata(
        name="planner",
        role="Software architect for planning",
        capabilities=[AgentCapability.PLAN_GENERATION],
        parallel_safe=True,
        dependencies=["spec_generator"],
        preferred_model="gpt-5",
        avg_execution_time_minutes=20.0,
        success_rate=0.92,
    ),
    "chief_architect": AgentMetadata(
        name="chief_architect",
        role="System design and ADRs",
        capabilities=[AgentCapability.ARCHITECTURE_DECISION],
        parallel_safe=True,
        dependencies=[],
        preferred_model="gpt-5",
        avg_execution_time_minutes=30.0,
        success_rate=0.90,
    ),
    "code_agent": AgentMetadata(
        name="code_agent",
        role="TDD implementation",
        capabilities=[AgentCapability.CODE_IMPLEMENTATION],
        parallel_safe=False,
        dependencies=["planner", "test_generator"],
        preferred_model="gpt-5",
        avg_execution_time_minutes=45.0,
        success_rate=0.93,
    ),
    "test_generator": AgentMetadata(
        name="test_generator",
        role="Comprehensive test coverage",
        capabilities=[AgentCapability.TEST_GENERATION],
        parallel_safe=True,
        dependencies=["planner"],
        preferred_model="gpt-5",
        avg_execution_time_minutes=25.0,
        success_rate=0.94,
    ),
    "auditor": AgentMetadata(
        name="auditor",
        role="Static code analysis (READ-ONLY)",
        capabilities=[AgentCapability.CODE_AUDIT],
        parallel_safe=True,
        dependencies=[],
        preferred_model="gpt-5",
        avg_execution_time_minutes=20.0,
        success_rate=0.98,
    ),
    "quality_enforcer": AgentMetadata(
        name="quality_enforcer",
        role="Constitutional compliance + healing",
        capabilities=[
            AgentCapability.QUALITY_ENFORCEMENT,
            AgentCapability.CONSTITUTIONAL_VALIDATION,
        ],
        parallel_safe=False,
        dependencies=["auditor"],
        preferred_model="gpt-5",
        avg_execution_time_minutes=30.0,
        success_rate=0.96,
    ),
    "merger": AgentMetadata(
        name="merger",
        role="Git workflow and PR management",
        capabilities=[AgentCapability.GIT_WORKFLOW, AgentCapability.PR_MANAGEMENT],
        parallel_safe=False,
        dependencies=["code_agent", "quality_enforcer"],
        preferred_model="gpt-5",
        avg_execution_time_minutes=15.0,
        success_rate=0.97,
    ),
    "learning_agent": AgentMetadata(
        name="learning_agent",
        role="Pattern extraction and analysis",
        capabilities=[AgentCapability.PATTERN_LEARNING, AgentCapability.SESSION_ANALYSIS],
        parallel_safe=True,
        dependencies=[],
        preferred_model="gpt-5-mini",
        avg_execution_time_minutes=10.0,
        success_rate=0.92,
    ),
    "toolsmith": AgentMetadata(
        name="toolsmith",
        role="Tool development with TDD",
        capabilities=[AgentCapability.TOOL_DEVELOPMENT],
        parallel_safe=True,
        dependencies=["planner", "test_generator"],
        preferred_model="gpt-5",
        avg_execution_time_minutes=60.0,
        success_rate=0.91,
    ),
    "e2e_workflow": AgentMetadata(
        name="e2e_workflow",
        role="End-to-end orchestration",
        capabilities=[AgentCapability.E2E_ORCHESTRATION],
        parallel_safe=False,
        dependencies=[],
        preferred_model="gpt-5",
        avg_execution_time_minutes=120.0,
        success_rate=0.89,
    ),
    "work_completion": AgentMetadata(
        name="work_completion",
        role="Work summarization",
        capabilities=[AgentCapability.WORK_SUMMARIZATION],
        parallel_safe=True,
        dependencies=[],
        preferred_model="gpt-5-mini",
        avg_execution_time_minutes=8.0,
        success_rate=0.94,
    ),
}
