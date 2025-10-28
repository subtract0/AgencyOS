"""
Tests for E2E test proposal functionality in TestGenerator agent.

Tests complexity detection, E2E test proposal generation, and template selection
for the GenerateTests tool implementation.
"""

import pytest
from test_generator_agent.test_generator_agent import (
    ComplexityLevel,
    E2ETestProposal,
    E2ETestType,
    GenerateTests,
)


class TestComplexityDetection:
    """Test complexity detection for E2E test requirements."""

    def test_detect_simple_feature_single_agent_few_steps(self):
        """Test detection of SIMPLE feature (unit tests sufficient)."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = "Implement a simple validation function for email addresses."

        complexity = tool.detect_feature_complexity(spec)

        assert complexity == ComplexityLevel.SIMPLE

    def test_detect_moderate_feature_two_agents(self):
        """Test detection of MODERATE feature (E2E recommended)."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Implement authentication feature.
        Step 1: PlannerAgent creates specification
        Step 2: CodingAgent implements the code
        Step 3: Run tests and validate
        """

        complexity = tool.detect_feature_complexity(spec)

        assert complexity == ComplexityLevel.MODERATE

    def test_detect_moderate_feature_multiple_steps(self):
        """Test detection of MODERATE feature based on workflow steps."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Refactor the authentication module.
        Then update the database schema.
        After that, migrate existing data.
        Then update the API endpoints.
        Finally, update the documentation.
        """

        complexity = tool.detect_feature_complexity(spec)

        assert complexity == ComplexityLevel.MODERATE

    def test_detect_complex_feature_many_agents(self):
        """Test detection of COMPLEX feature (E2E required)."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Implement full authentication system.
        PlannerAgent creates the specification.
        CodingAgent implements the backend.
        TestGenerator creates comprehensive tests.
        QualityEnforcer validates compliance.
        MergerAgent integrates the changes.
        """

        complexity = tool.detect_feature_complexity(spec)

        assert complexity == ComplexityLevel.COMPLEX

    def test_detect_complex_feature_many_workflow_steps(self):
        """Test detection of COMPLEX feature based on many workflow steps."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Multi-phase authentication implementation:
        Step 1: Design the architecture
        Step 2: Create database models
        Step 3: Implement authentication service
        Step 4: Add JWT token generation
        Step 5: Create API endpoints
        Step 6: Add middleware for auth checking
        Step 7: Write comprehensive tests
        """

        complexity = tool.detect_feature_complexity(spec)

        assert complexity == ComplexityLevel.COMPLEX


class TestE2ETestProposal:
    """Test E2E test proposal generation."""

    def test_propose_no_e2e_tests_for_simple_feature(self):
        """Test no E2E tests proposed for SIMPLE features."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = "Simple validation function"

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.SIMPLE)

        assert len(proposals) == 0

    def test_propose_mission_e2e_test_for_primea_workflow(self):
        """Test Mission E2E test proposal for /primeA workflows."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        PrimeA autonomous mission to implement JWT authentication.
        PlannerAgent creates specification.
        CodingAgent implements with tests.
        QualityEnforcer validates compliance.
        """

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.COMPLEX)

        assert len(proposals) > 0
        mission_proposals = [p for p in proposals if p.test_type == E2ETestType.MISSION]
        assert len(mission_proposals) > 0
        assert mission_proposals[0].test_name == "test_e2e_mission_execution"
        assert "PlannerAgent" in mission_proposals[0].agents_involved
        assert "CodingAgent" in mission_proposals[0].agents_involved

    def test_propose_agent_e2e_test_for_agent_coordination(self):
        """Test Agent E2E test proposal for agent coordination."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Multi-agent coordination workflow.
        TestGenerator creates tests.
        CodingAgent implements features.
        QualityEnforcer validates quality.
        """

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.MODERATE)

        assert len(proposals) > 0
        agent_proposals = [p for p in proposals if p.test_type == E2ETestType.AGENT]
        assert len(agent_proposals) > 0
        assert agent_proposals[0].test_name == "test_e2e_agent_coordination"
        assert agent_proposals[0].complexity == ComplexityLevel.MODERATE

    def test_propose_tool_e2e_test_for_tool_integration(self):
        """Test Tool E2E test proposal for tool integration."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Tool integration workflow.
        Use Read tool to analyze code.
        Use Edit tool to modify files.
        Use Bash tool to run tests.
        """

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.MODERATE)

        assert len(proposals) > 0
        tool_proposals = [p for p in proposals if p.test_type == E2ETestType.TOOL]
        assert len(tool_proposals) > 0
        assert tool_proposals[0].test_name == "test_e2e_tool_integration"

    def test_propose_multiple_e2e_test_types(self):
        """Test proposal of multiple E2E test types for complex features."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Complete autonomous workflow with tool integration.
        PrimeA mission to implement authentication.
        Multiple agents coordinate the implementation.
        Tools are used for file operations and testing.
        """

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.COMPLEX)

        # Should propose multiple test types
        assert len(proposals) >= 2
        test_types = {p.test_type for p in proposals}
        assert E2ETestType.MISSION in test_types or E2ETestType.AGENT in test_types


class TestE2ETestProposalContent:
    """Test E2E test proposal content and structure."""

    def test_proposal_includes_agents_involved(self):
        """Test proposal includes list of agents involved."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Multi-agent workflow.
        PlannerAgent creates plan.
        CodingAgent implements code.
        TestGenerator creates tests.
        """

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.MODERATE)

        assert len(proposals) > 0
        proposal = proposals[0]
        assert len(proposal.agents_involved) > 0
        # Should detect at least some of the mentioned agents
        agent_names = " ".join(proposal.agents_involved)
        assert any(
            agent in agent_names
            for agent in ["PlannerAgent", "CodingAgent", "TestGenerator"]
        )

    def test_proposal_includes_workflow_steps(self):
        """Test proposal includes workflow steps."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Workflow with clear steps:
        Step 1: Create specification
        Step 2: Implement code
        Step 3: Write tests
        Step 4: Validate quality
        """

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.MODERATE)

        assert len(proposals) > 0
        proposal = proposals[0]
        assert len(proposal.workflow_steps) > 0

    def test_proposal_includes_template_path(self):
        """Test proposal includes correct template path."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = "Agent coordination workflow with multiple agents."

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.MODERATE)

        assert len(proposals) > 0
        proposal = proposals[0]
        assert proposal.template_path.endswith(".py")
        assert "e2e" in proposal.template_path.lower()

    def test_proposal_includes_description(self):
        """Test proposal includes meaningful description."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = "Complex mission workflow with multiple agents and tools."

        proposals = tool.propose_e2e_tests(spec, ComplexityLevel.COMPLEX)

        assert len(proposals) > 0
        proposal = proposals[0]
        assert len(proposal.description) > 10
        assert "end-to-end" in proposal.description.lower() or "e2e" in proposal.description.lower()


class TestAgentExtraction:
    """Test agent extraction from specifications."""

    def test_extract_single_agent(self):
        """Test extraction of single agent from spec."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = "CodingAgent implements the feature."

        agents = tool._extract_agents_from_spec(spec)

        assert "CodingAgent" in agents

    def test_extract_multiple_agents(self):
        """Test extraction of multiple agents from spec."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        PlannerAgent creates the plan.
        CodingAgent implements the code.
        QualityEnforcer validates quality.
        """

        agents = tool._extract_agents_from_spec(spec)

        assert "PlannerAgent" in agents
        assert "CodingAgent" in agents
        assert "QualityEnforcer" in agents

    def test_extract_agents_case_insensitive(self):
        """Test agent extraction is case insensitive."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = "planneragent creates the plan. codingagent implements."

        agents = tool._extract_agents_from_spec(spec)

        assert "PlannerAgent" in agents
        assert "CodingAgent" in agents

    def test_extract_agents_returns_default_when_none_found(self):
        """Test default agent returned when none found in spec."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = "Implement a simple function with no agents mentioned."

        agents = tool._extract_agents_from_spec(spec)

        assert len(agents) > 0
        assert "UnspecifiedAgent" in agents


class TestWorkflowStepExtraction:
    """Test workflow step extraction from specifications."""

    def test_extract_numbered_steps(self):
        """Test extraction of numbered workflow steps."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Step 1: Create specification
        Step 2: Implement code
        Step 3: Write tests
        """

        steps = tool._extract_workflow_steps(spec)

        assert len(steps) >= 3

    def test_extract_then_steps(self):
        """Test extraction of 'then' workflow steps."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Create the plan, then implement the code, then validate quality.
        """

        steps = tool._extract_workflow_steps(spec)

        assert len(steps) > 0

    def test_extract_arrow_steps(self):
        """Test extraction of arrow (→) workflow steps."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = """
        Plan → Code → Test → Validate → Merge
        """

        steps = tool._extract_workflow_steps(spec)

        assert len(steps) > 0

    def test_extract_returns_default_when_no_steps_found(self):
        """Test default steps returned when none found in spec."""
        tool = GenerateTests(audit_report="{}", target_file="test.py")
        spec = "Simple feature implementation."

        steps = tool._extract_workflow_steps(spec)

        assert len(steps) > 0
        assert "Execute feature workflow" in steps or "Verify results" in steps
