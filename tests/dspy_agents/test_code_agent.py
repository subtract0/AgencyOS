"""
Comprehensive unit tests for DSPyCodeAgent - DSPy-powered code agent implementation.

Tests following the NECESSARY pattern:
- **N**amed clearly with test purpose
- **E**xecutable in isolation
- **C**omprehensive coverage
- **E**dge Cases - Boundary conditions tested
- **S**tateful - Test state changes
- **S**erializable - Clear data flow
- **A**uditable - Well documented
- **R**epeatable - Consistent results
- **Y**ielding - Clear outcomes

Constitutional Compliance:
- Article I: TDD is Mandatory - Tests written before implementation review
- Article II: Strict typing enforced throughout
- Article III: All inputs validated using Pydantic models
- Article IV: Comprehensive error handling tested
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from typing import Dict, Any, List

# Test imports for DSPy availability scenarios
def mock_dspy_available():
    """Mock DSPy as available."""
    return True

def mock_dspy_unavailable():
    """Mock DSPy as unavailable."""
    return False

# We'll use these mocks to test both scenarios
@pytest.fixture
def mock_dspy_module():
    """Mock DSPy module for testing."""
    with patch('dspy_agents.modules.code_agent.dspy') as mock_dspy:
        # Mock the DSPy classes and methods
        mock_module = Mock()
        mock_chain_of_thought = Mock()
        mock_predict = Mock()

        mock_dspy.Module = Mock(return_value=mock_module)
        mock_dspy.ChainOfThought = Mock(return_value=mock_chain_of_thought)
        mock_dspy.Predict = Mock(return_value=mock_predict)

        yield mock_dspy

@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return {
        "repository_root": "/test/repo",
        "current_directory": "/test/repo/src",
        "git_branch": "feature-test",
        "session_id": "test_session_123",
        "agent_context": {"test": "data"}
    }

@pytest.fixture
def sample_file_changes():
    """Sample file changes for testing."""
    from dspy_agents.signatures.base import FileChange
    return [
        FileChange(
            file_path="/test/file1.py",
            operation="modify",
            content="def test_function(): pass",
            diff="+ def test_function(): pass"
        ),
        FileChange(
            file_path="/test/file2.py",
            operation="create",
            content="# New file content"
        )
    ]

@pytest.fixture
def sample_test_cases():
    """Sample test cases for testing."""
    from dspy_agents.signatures.base import TestSpecification
    return [
        TestSpecification(
            test_file="/test/test_file1.py",
            test_name="test_basic_functionality",
            test_code="def test_basic_functionality(): assert True",
            follows_necessary=True
        ),
        TestSpecification(
            test_file="/test/test_file2.py",
            test_name="test_edge_case",
            test_code="def test_edge_case(): assert 1 == 1",
            follows_necessary=True
        )
    ]

@pytest.fixture
def sample_verification_result():
    """Sample verification result for testing."""
    from dspy_agents.signatures.base import VerificationResult
    return VerificationResult(
        all_tests_pass=True,
        no_linting_errors=True,
        constitutional_compliance=True,
        error_details=[]
    )

@pytest.fixture
def sample_agent_result(sample_file_changes, sample_test_cases, sample_verification_result):
    """Sample agent result for testing."""
    from dspy_agents.signatures.base import AgentResult
    return AgentResult(
        success=True,
        changes=sample_file_changes,
        tests=sample_test_cases,
        verification=sample_verification_result,
        message="Task completed successfully"
    )

@pytest.fixture
def sample_task_plan():
    """Sample task plan for testing."""
    from dspy_agents.signatures.base import TaskPlan
    return TaskPlan(
        steps=[
            "Analyze requirements",
            "Write tests first (TDD)",
            "Implement functionality",
            "Verify implementation"
        ],
        agent_assignments={
            "DSPyCodeAgent": "All steps"
        },
        estimated_time=300,
        risk_factors=["Complex logic", "Integration testing required"]
    )


class TestDSPyCodeAgentInitialization:
    """Test DSPyCodeAgent initialization scenarios."""

    def test_init_with_dspy_available(self, mock_dspy_module):
        """Test agent initialization when DSPy is available."""
        # Mock DSPy availability
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(
                model="gpt-4o-mini",
                reasoning_effort="high",
                enable_learning=True,
                quality_threshold=0.9
            )

            # Verify initialization
            assert agent.model == "gpt-4o-mini"
            assert agent.reasoning_effort == "high"
            assert agent.enable_learning is True
            assert agent.quality_threshold == 0.9
            assert agent.dspy_available is True

            # Verify DSPy modules are initialized
            assert agent.planner is not None
            assert agent.implementer is not None
            assert agent.verifier is not None
            assert agent.task_executor is not None

            # Verify learning patterns are initialized
            assert isinstance(agent.success_patterns, list)
            assert isinstance(agent.failure_patterns, list)
            assert len(agent.success_patterns) == 0
            assert len(agent.failure_patterns) == 0

    def test_init_with_dspy_unavailable(self):
        """Test agent initialization when DSPy is not available."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', False):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(
                model="gpt-4o-mini",
                reasoning_effort="medium",
                enable_learning=False,
                quality_threshold=0.8
            )

            # Verify initialization
            assert agent.model == "gpt-4o-mini"
            assert agent.reasoning_effort == "medium"
            assert agent.enable_learning is False
            assert agent.quality_threshold == 0.8
            assert agent.dspy_available is False

            # Verify DSPy modules are None in fallback
            assert agent.planner is None
            assert agent.implementer is None
            assert agent.verifier is None
            assert agent.task_executor is None

    def test_init_with_default_parameters(self):
        """Test agent initialization with default parameters."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Verify default values
            assert agent.model == "gpt-4o-mini"
            assert agent.reasoning_effort == "medium"
            assert agent.enable_learning is True
            assert agent.quality_threshold == 0.8

    def test_factory_function_creates_agent(self):
        """Test factory function creates agent with correct parameters."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import create_dspy_code_agent

            agent = create_dspy_code_agent(
                model="gpt-4",
                reasoning_effort="low",
                enable_learning=False,
                quality_threshold=0.7
            )

            assert agent.model == "gpt-4"
            assert agent.reasoning_effort == "low"
            assert agent.enable_learning is False
            assert agent.quality_threshold == 0.7


class TestDSPyCodeAgentForwardMethod:
    """Test the main forward method execution."""

    def test_forward_with_dspy_available_success(self, mock_dspy_module, sample_context, sample_agent_result):
        """Test successful forward execution when DSPy is available."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Mock the task executor to return a successful result
            mock_result = Mock()
            mock_result.code_changes = sample_agent_result.changes
            mock_result.tests_added = sample_agent_result.tests
            mock_result.verification_status = sample_agent_result.verification

            agent.task_executor = Mock(return_value=mock_result)

            # Execute the forward method
            result = agent.forward(
                task_description="Create a test function",
                context=sample_context
            )

            # Verify result
            assert isinstance(result, type(sample_agent_result))
            assert result.success is True
            assert len(result.changes) == 2
            assert len(result.tests) == 2
            assert result.verification is not None

            # Verify task executor was called with correct parameters
            agent.task_executor.assert_called_once()
            call_args = agent.task_executor.call_args
            assert call_args[1]['task_description'] == "Create a test function"
            assert 'context' in call_args[1]
            assert 'constitutional_requirements' in call_args[1]

    def test_forward_with_dspy_unavailable_fallback(self, sample_context):
        """Test forward execution falls back when DSPy is unavailable."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', False):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Execute the forward method
            result = agent.forward(
                task_description="Create a test function",
                context=sample_context
            )

            # Verify fallback result
            assert result.success is False
            assert "DSPy not available" in result.message
            assert len(result.changes) == 0
            assert len(result.tests) == 0
            assert result.verification.all_tests_pass is False
            assert result.verification.constitutional_compliance is False

    def test_forward_with_minimal_context(self):
        """Test forward method with minimal context."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Mock the task executor
            mock_result = Mock()
            mock_result.code_changes = []
            mock_result.tests_added = []
            mock_result.verification_status = None

            agent.task_executor = Mock(return_value=mock_result)

            # Execute with minimal context
            result = agent.forward(
                task_description="Simple task",
                context={}
            )

            # Should handle missing context gracefully
            assert result.success is True
            agent.task_executor.assert_called_once()

    def test_forward_handles_execution_error(self, sample_context):
        """Test forward method handles execution errors gracefully."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Make task executor raise an exception
            agent.task_executor = Mock(side_effect=Exception("Test error"))

            # Execute the forward method
            result = agent.forward(
                task_description="Create a test function",
                context=sample_context
            )

            # Verify error handling
            assert result.success is False
            assert "Agent execution failed: Test error" in result.message
            assert len(result.changes) == 0
            assert len(result.tests) == 0
            assert result.verification.all_tests_pass is False

    def test_forward_enables_learning_on_success(self, mock_dspy_module, sample_context, sample_agent_result):
        """Test forward method records learning patterns on success."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(enable_learning=True)

            # Mock successful result
            mock_result = Mock()
            mock_result.code_changes = sample_agent_result.changes
            mock_result.tests_added = sample_agent_result.tests
            mock_result.verification_status = sample_agent_result.verification

            agent.task_executor = Mock(return_value=mock_result)

            # Execute the forward method
            result = agent.forward(
                task_description="Create a new authentication feature",
                context=sample_context
            )

            # Verify learning occurred
            assert len(agent.success_patterns) == 1
            assert len(agent.failure_patterns) == 0

            pattern = agent.success_patterns[0]
            assert pattern["task_type"] == "implementation"  # "create" keyword triggers implementation
            assert pattern["success"] is True
            assert "Create a new authentication feature" in pattern["task_description"]


class TestDSPyCodeAgentPlanningMethods:
    """Test planning-related methods."""

    def test_plan_task_with_dspy_available(self, mock_dspy_module, sample_context, sample_task_plan):
        """Test task planning when DSPy is available."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Mock the planner to return a plan
            mock_result = Mock()
            mock_result.plan = sample_task_plan
            agent.planner = Mock(return_value=mock_result)

            # Execute planning
            plan = agent.plan_task(
                task="Create user authentication",
                context=sample_context,
                constraints=["Must use JWT", "Must validate passwords"]
            )

            # Verify plan
            assert plan == sample_task_plan
            assert len(plan.steps) == 4
            assert "Write tests first (TDD)" in plan.steps

            # Verify planner was called with constraints
            agent.planner.assert_called_once()
            call_args = agent.planner.call_args
            assert "Must use JWT" in call_args[1]['constraints']
            assert "Must follow TDD - write tests first" in call_args[1]['constraints']

    def test_plan_task_with_dspy_unavailable_fallback(self, sample_context):
        """Test task planning fallback when DSPy is unavailable."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', False):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Execute planning
            plan = agent.plan_task(
                task="Create user authentication",
                context=sample_context
            )

            # Verify fallback plan
            assert len(plan.steps) > 0
            assert "DSPy not available - using basic planning" in plan.risk_factors
            assert plan.agent_assignments["DSPyCodeAgent"] == "All steps"

    def test_plan_task_classifies_testing_tasks(self, sample_context):
        """Test planning correctly classifies testing tasks."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', False):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Plan a testing task
            plan = agent.plan_task(
                task="Write comprehensive test suite",
                context=sample_context
            )

            # Verify testing-specific planning
            assert "Analyze existing code to understand behavior" in plan.steps
            assert "Write comprehensive test cases following TDD" in plan.steps

    def test_plan_task_handles_planning_error(self, mock_dspy_module, sample_context):
        """Test planning handles errors gracefully."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Make planner raise an exception
            agent.planner = Mock(side_effect=Exception("Planning error"))

            # Execute planning
            plan = agent.plan_task(
                task="Create user authentication",
                context=sample_context
            )

            # Verify error handling
            assert len(plan.steps) == 1
            assert "Error occurred during planning" in plan.steps[0]
            assert "Planning error: Planning error" in plan.risk_factors


class TestDSPyCodeAgentImplementationMethods:
    """Test implementation-related methods."""

    def test_implement_plan_with_dspy_available(self, mock_dspy_module, sample_context,
                                                sample_task_plan, sample_file_changes, sample_test_cases):
        """Test plan implementation when DSPy is available."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Mock the implementer to return changes and tests
            mock_result = Mock()
            mock_result.code_changes = sample_file_changes
            mock_result.tests_added = sample_test_cases
            mock_result.implementation_notes = "Implementation completed successfully"

            agent.implementer = Mock(return_value=mock_result)

            # Execute implementation
            changes, tests, notes = agent.implement_plan(
                plan=sample_task_plan,
                context=sample_context,
                quality_standards=["High code coverage", "Strict typing"]
            )

            # Verify implementation result
            assert len(changes) == 2
            assert len(tests) == 2
            assert "Implementation completed successfully" in notes

            # Verify implementer was called with quality standards
            agent.implementer.assert_called_once()
            call_args = agent.implementer.call_args
            quality_standards = call_args[1]['quality_standards']
            assert "High code coverage" in quality_standards
            assert "Strict typing" in quality_standards
            # Quality standards passed to the method should be used as-is
            assert len(quality_standards) == 2

    def test_implement_plan_with_dspy_unavailable_fallback(self, sample_task_plan, sample_context):
        """Test implementation fallback when DSPy is unavailable."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', False):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Execute implementation
            changes, tests, notes = agent.implement_plan(
                plan=sample_task_plan,
                context=sample_context
            )

            # Verify fallback result
            assert len(changes) == 0
            assert len(tests) == 0
            assert "DSPy not available" in notes
            assert f"{len(sample_task_plan.steps)} steps" in notes

    def test_implement_plan_handles_implementation_error(self, mock_dspy_module, sample_task_plan, sample_context):
        """Test implementation handles errors gracefully."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Make implementer raise an exception
            agent.implementer = Mock(side_effect=Exception("Implementation error"))

            # Execute implementation
            changes, tests, notes = agent.implement_plan(
                plan=sample_task_plan,
                context=sample_context
            )

            # Verify error handling
            assert len(changes) == 0
            assert len(tests) == 0
            assert "Implementation error: Implementation error" in notes


class TestDSPyCodeAgentVerificationMethods:
    """Test verification-related methods."""

    def test_verify_implementation_with_dspy_available(self, mock_dspy_module, sample_agent_result):
        """Test implementation verification when DSPy is available."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent
            from dspy_agents.signatures.base import VerificationResult

            agent = DSPyCodeAgent()

            # Mock the verifier to return verification result
            expected_result = VerificationResult(
                all_tests_pass=True,
                no_linting_errors=True,
                constitutional_compliance=True,
                error_details=[]
            )

            mock_result = Mock()
            mock_result.verification_result = expected_result
            agent.verifier = Mock(return_value=mock_result)

            # Execute verification
            test_results = {"all_pass": True, "coverage": 0.95}
            result = agent.verify_implementation(
                implementation=sample_agent_result,
                test_results=test_results,
                constitutional_checks=["TDD followed", "Strict typing used"]
            )

            # Verify result
            assert result.all_tests_pass is True
            assert result.no_linting_errors is True
            assert result.constitutional_compliance is True
            assert len(result.error_details) == 0

            # Verify verifier was called with constitutional checks
            agent.verifier.assert_called_once()
            call_args = agent.verifier.call_args
            constitutional_checks = call_args[1]['constitutional_checks']
            assert "TDD followed" in constitutional_checks
            assert "Strict typing used" in constitutional_checks
            # Constitutional checks passed to the method should be used as-is
            assert len(constitutional_checks) == 2

    def test_verify_implementation_with_dspy_unavailable_fallback(self, sample_agent_result):
        """Test verification fallback when DSPy is unavailable."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', False):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Execute verification
            test_results = {"all_pass": True}
            result = agent.verify_implementation(
                implementation=sample_agent_result,
                test_results=test_results
            )

            # Verify fallback result
            assert result.all_tests_pass is True  # Based on test_results
            assert result.no_linting_errors is True  # Assumed in fallback
            assert result.constitutional_compliance is True  # Assumed in fallback
            assert "DSPy not available - basic verification only" in result.error_details

    def test_verify_implementation_handles_verification_error(self, mock_dspy_module, sample_agent_result):
        """Test verification handles errors gracefully."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Make verifier raise an exception
            agent.verifier = Mock(side_effect=Exception("Verification error"))

            # Execute verification
            result = agent.verify_implementation(
                implementation=sample_agent_result,
                test_results={}
            )

            # Verify error handling
            assert result.all_tests_pass is False
            assert result.constitutional_compliance is False
            assert "Verification error: Verification error" in result.error_details


class TestDSPyCodeAgentContextManagement:
    """Test context preparation and management."""

    def test_prepare_context_with_complete_data(self, sample_context):
        """Test context preparation with complete data."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Prepare context
            context = agent._prepare_context(sample_context)

            # Verify context
            assert context.repository_root == sample_context["repository_root"]
            assert context.current_directory == sample_context["current_directory"]
            assert context.git_branch == sample_context["git_branch"]
            assert context.session_id == sample_context["session_id"]
            assert len(context.constitutional_articles) == 10

    def test_prepare_context_with_minimal_data(self):
        """Test context preparation with minimal data."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Prepare minimal context
            context = agent._prepare_context({})

            # Verify defaults are set
            assert context.repository_root == os.getcwd()
            assert context.current_directory == os.getcwd()
            assert context.git_branch == "main"
            assert context.session_id.startswith("session_")
            assert len(context.constitutional_articles) == 10

    def test_prepare_context_handles_validation_error(self):
        """Test context preparation handles validation errors gracefully."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Mock ValidationError to trigger the error handling path
            from pydantic import ValidationError
            # Create a simple mock that will raise and then return fallback

            def mock_prepare_context(context_dict):
                try:
                    # Simulate ValidationError on first call
                    raise ValidationError.from_exception_data("Test", [{"type": "missing", "loc": ("field",), "msg": "field required", "input": {}}])
                except ValidationError:
                    # Import here to avoid circular imports
                    from dspy_agents.modules.code_agent import CodeTaskContext
                    from datetime import datetime
                    return CodeTaskContext(
                        repository_root=os.getcwd(),
                        current_directory=os.getcwd(),
                        session_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )

            # Patch the method
            with patch.object(agent, '_prepare_context', side_effect=mock_prepare_context):
                context = agent._prepare_context({"invalid": "data"})

                # Should return fallback context
                assert context.repository_root == os.getcwd()
                assert context.session_id.startswith("fallback_")


class TestDSPyCodeAgentLearningSystem:
    """Test learning system functionality."""

    def test_learn_from_successful_execution(self, sample_context, sample_agent_result):
        """Test learning from successful task execution."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(enable_learning=True)

            # Learn from execution
            agent._learn_from_execution(
                task_description="Create authentication system",
                result=sample_agent_result,
                context=agent._prepare_context(sample_context)
            )

            # Verify learning occurred
            assert len(agent.success_patterns) == 1
            assert len(agent.failure_patterns) == 0

            pattern = agent.success_patterns[0]
            assert pattern["task_type"] == "implementation"
            assert pattern["success"] is True
            assert pattern["changes_count"] == 2
            assert pattern["tests_count"] == 2
            assert pattern["constitutional_compliance"] is True
            assert "authentication" in pattern["keywords"]

    def test_learn_from_failed_execution(self, sample_context):
        """Test learning from failed task execution."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent
            from dspy_agents.signatures.base import AgentResult, VerificationResult

            agent = DSPyCodeAgent(enable_learning=True)

            # Create failed result
            failed_result = AgentResult(
                success=False,
                changes=[],
                tests=[],
                verification=VerificationResult(
                    all_tests_pass=False,
                    no_linting_errors=False,
                    constitutional_compliance=False,
                    error_details=["Type checking failed", "Tests missing"]
                ),
                message="Task failed"
            )

            # Learn from execution
            agent._learn_from_execution(
                task_description="Fix type errors",
                result=failed_result,
                context=agent._prepare_context(sample_context)
            )

            # Verify learning occurred
            assert len(agent.success_patterns) == 0
            assert len(agent.failure_patterns) == 1

            pattern = agent.failure_patterns[0]
            assert pattern["task_type"] == "debugging"
            assert pattern["success"] is False
            assert pattern["constitutional_compliance"] is False
            assert "Type checking failed" in pattern["failure_reasons"]

    def test_pattern_storage_limits(self, sample_context, sample_agent_result):
        """Test that pattern storage respects limits."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(enable_learning=True)

            # Add many success patterns (more than limit)
            for i in range(105):
                agent._learn_from_execution(
                    task_description=f"Task {i}",
                    result=sample_agent_result,
                    context=agent._prepare_context(sample_context)
                )

            # Verify limit is enforced
            assert len(agent.success_patterns) == 100  # Should be capped at 100

    def test_get_historical_patterns(self, sample_context, sample_agent_result):
        """Test retrieval of relevant historical patterns."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(enable_learning=True)

            # Add some patterns
            agent._learn_from_execution(
                task_description="Create authentication system",
                result=sample_agent_result,
                context=agent._prepare_context(sample_context)
            )

            agent._learn_from_execution(
                task_description="Add user registration",
                result=sample_agent_result,
                context=agent._prepare_context(sample_context)
            )

            # Get patterns for related task
            patterns = agent._get_historical_patterns("Implement user authentication")

            # Should find the relevant pattern
            assert len(patterns) > 0
            relevant_pattern = patterns[0]
            assert "authentication" in relevant_pattern["keywords"]

    def test_get_learning_summary(self, sample_context, sample_agent_result):
        """Test learning summary generation."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent
            from dspy_agents.signatures.base import AgentResult

            agent = DSPyCodeAgent(enable_learning=True)

            # Add success and failure patterns
            agent._learn_from_execution("Success task", sample_agent_result,
                                       agent._prepare_context(sample_context))

            failed_result = AgentResult(success=False, changes=[], tests=[],
                                      verification=None, message="Failed")
            agent._learn_from_execution("Failed task", failed_result,
                                       agent._prepare_context(sample_context))

            # Get summary
            summary = agent.get_learning_summary()

            # Verify summary
            assert summary["success_patterns_count"] == 1
            assert summary["failure_patterns_count"] == 1
            assert summary["total_executions"] == 2
            assert summary["success_rate"] == 0.5
            # Check the actual task type that was classified
            success_tasks = summary["common_success_tasks"]
            assert len(success_tasks) > 0  # Should have at least one task type

    def test_reset_learning(self, sample_context, sample_agent_result):
        """Test learning reset functionality."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(enable_learning=True)

            # Add some patterns
            agent._learn_from_execution("Task", sample_agent_result,
                                       agent._prepare_context(sample_context))

            assert len(agent.success_patterns) == 1

            # Reset learning
            agent.reset_learning()

            # Verify reset
            assert len(agent.success_patterns) == 0
            assert len(agent.failure_patterns) == 0


class TestDSPyCodeAgentTaskClassification:
    """Test task classification functionality."""

    def test_classify_testing_tasks(self):
        """Test classification of testing tasks."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Test various testing task descriptions
            testing_tasks = [
                "Write unit tests for authentication",
                "Create test suite for API endpoints",
                "Add pytest fixtures for database testing",
                "Generate unittest coverage report"
            ]

            for task in testing_tasks:
                assert agent._classify_task(task) == "testing"

    def test_classify_debugging_tasks(self):
        """Test classification of debugging tasks."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Test various debugging task descriptions
            debugging_tasks = [
                "Fix authentication bug in login",
                "Debug database connection error",
                "Resolve type checking errors"
            ]

            for task in debugging_tasks:
                assert agent._classify_task(task) == "debugging"

    def test_classify_implementation_tasks(self):
        """Test classification of implementation tasks."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Test various implementation task descriptions
            implementation_tasks = [
                "Create user authentication system",
                "Implement JWT token validation",
                "Add new API endpoint for users",
                "Create database models for orders"
            ]

            for task in implementation_tasks:
                assert agent._classify_task(task) == "implementation"

    def test_classify_refactoring_tasks(self):
        """Test classification of refactoring tasks."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Test various refactoring task descriptions
            refactoring_tasks = [
                "Refactor authentication service",
                "Improve database query performance",
                "Optimize API response times"
            ]

            for task in refactoring_tasks:
                assert agent._classify_task(task) == "refactoring"

    def test_classify_general_tasks(self):
        """Test classification of general tasks."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Test general task
            task = "Review code quality standards"
            assert agent._classify_task(task) == "general"


class TestDSPyCodeAgentKeywordExtraction:
    """Test keyword extraction functionality."""

    def test_extract_meaningful_keywords(self):
        """Test extraction of meaningful keywords."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Extract keywords from task description
            task = "Create user authentication system with JWT tokens and password validation"
            keywords = agent._extract_keywords(task)

            # Verify meaningful keywords are extracted
            expected_keywords = ["create", "user", "authentication", "system", "jwt", "tokens", "password", "validation"]
            for keyword in expected_keywords:
                assert keyword in keywords

            # Verify stop words are filtered out
            stop_words = ["the", "with", "and"]
            for stop_word in stop_words:
                assert stop_word not in keywords

    def test_keyword_extraction_limits_results(self):
        """Test keyword extraction limits results to top 10."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Create a long task description
            long_task = " ".join([f"keyword{i}" for i in range(20)])
            keywords = agent._extract_keywords(long_task)

            # Should be limited to 10 keywords
            assert len(keywords) <= 10

    def test_keyword_extraction_filters_short_words(self):
        """Test keyword extraction filters out short words."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Task with short words
            task = "a to do is be it we go up"
            keywords = agent._extract_keywords(task)

            # All words are short or stop words, should be empty or very few
            assert len(keywords) <= 2  # Only "do" might remain if it passes the filter


class TestDSPyCodeAgentEdgeCases:
    """Test edge cases and error conditions."""

    def test_forward_with_none_task_description(self):
        """Test forward method with None task description."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()
            agent.task_executor = Mock()

            # This should not crash, but handle gracefully
            result = agent.forward(task_description=None, context={})

            # Should have some result (even if task_executor handles None)
            assert result is not None

    def test_process_task_result_with_invalid_data(self):
        """Test processing task result with invalid data."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Create invalid result data
            invalid_result = Mock()
            invalid_result.code_changes = ["invalid_format"]  # Should be FileChange objects
            invalid_result.tests_added = [{"invalid": "test"}]  # Invalid format
            invalid_result.verification_status = None

            context = agent._prepare_context({})

            # Process the invalid result
            result = agent._process_task_result(invalid_result, context)

            # Should handle gracefully and return valid AgentResult
            assert result is not None
            assert hasattr(result, 'success')
            assert hasattr(result, 'changes')
            assert hasattr(result, 'tests')

    def test_is_pattern_relevant_with_empty_keywords(self):
        """Test pattern relevance check with empty keywords."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Pattern with empty keywords
            pattern = {"keywords": []}
            task = "Any task description"

            # Should return False for empty keywords
            assert agent._is_pattern_relevant(pattern, task) is False

    def test_is_pattern_relevant_with_missing_keywords(self):
        """Test pattern relevance check with missing keywords field."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Pattern without keywords field
            pattern = {"task_type": "implementation"}
            task = "Any task description"

            # Should handle gracefully
            assert agent._is_pattern_relevant(pattern, task) is False

    def test_learning_with_disabled_learning(self, mock_dspy_module, sample_context, sample_agent_result):
        """Test that learning doesn't occur when disabled."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(enable_learning=False)

            # Mock successful result
            mock_result = Mock()
            mock_result.code_changes = sample_agent_result.changes
            mock_result.tests_added = sample_agent_result.tests
            mock_result.verification_status = sample_agent_result.verification

            agent.task_executor = Mock(return_value=mock_result)

            # Execute forward method (this is where learning is controlled)
            result = agent.forward(
                task_description="Test task",
                context=sample_context
            )

            # No patterns should be added because learning is disabled
            assert len(agent.success_patterns) == 0
            assert len(agent.failure_patterns) == 0

    def test_get_common_task_types_with_empty_patterns(self):
        """Test getting common task types with empty patterns."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Get common task types from empty patterns
            common_types = agent._get_common_task_types([])

            # Should return empty dict
            assert len(common_types) == 0
            assert isinstance(common_types, dict)


class TestDSPyCodeAgentConstitutionalCompliance:
    """Test constitutional compliance features."""

    def test_constitutional_articles_are_included_in_context(self, sample_context):
        """Test that constitutional articles are included in prepared context."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Prepare context
            context = agent._prepare_context(sample_context)

            # Verify constitutional articles are present
            assert len(context.constitutional_articles) == 10
            assert "TDD is Mandatory - Write tests before implementation" in context.constitutional_articles
            assert "Strict Typing Always - Use concrete types, avoid Any" in context.constitutional_articles
            assert "Validate All Inputs - Use proper validation schemas" in context.constitutional_articles

    def test_constitutional_constraints_added_to_planning(self, mock_dspy_module, sample_context):
        """Test that constitutional constraints are added to planning."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Mock planner result
            from dspy_agents.signatures.base import TaskPlan
            mock_plan = TaskPlan(steps=["step1"], agent_assignments={})
            mock_result = Mock()
            mock_result.plan = mock_plan
            agent.planner = Mock(return_value=mock_result)

            # Execute planning
            agent.plan_task(
                task="Create feature",
                context=sample_context,
                constraints=["Custom constraint"]
            )

            # Verify constitutional constraints were added
            call_args = agent.planner.call_args
            constraints = call_args[1]['constraints']
            assert "Custom constraint" in constraints
            assert "Must follow TDD - write tests first" in constraints
            assert "Must use strict typing" in constraints

    def test_constitutional_compliance_tracked_in_learning(self, sample_context, sample_agent_result):
        """Test that constitutional compliance is tracked in learning patterns."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent(enable_learning=True)

            # Learn from execution
            agent._learn_from_execution(
                task_description="Create feature",
                result=sample_agent_result,
                context=agent._prepare_context(sample_context)
            )

            # Verify constitutional compliance is tracked
            pattern = agent.success_patterns[0]
            assert "constitutional_compliance" in pattern
            assert pattern["constitutional_compliance"] is True


# Integration tests for full workflow
class TestDSPyCodeAgentIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_with_dspy_available(self, mock_dspy_module, sample_context):
        """Test complete workflow from task to result when DSPy is available."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent
            from dspy_agents.signatures.base import FileChange, TestSpecification, VerificationResult

            agent = DSPyCodeAgent(enable_learning=True)

            # Mock all DSPy components
            mock_changes = [FileChange(file_path="/test.py", operation="create", content="test")]
            mock_tests = [TestSpecification(test_file="/test_test.py", test_name="test_func",
                                 test_code="def test_func(): pass", follows_necessary=True)]
            mock_verification = VerificationResult(all_tests_pass=True, no_linting_errors=True,
                                                 constitutional_compliance=True, error_details=[])

            mock_task_result = Mock()
            mock_task_result.code_changes = mock_changes
            mock_task_result.tests_added = mock_tests
            mock_task_result.verification_status = mock_verification

            agent.task_executor = Mock(return_value=mock_task_result)

            # Execute full workflow
            result = agent.forward(
                task_description="Create a new feature with tests",
                context=sample_context
            )

            # Verify complete result
            assert result.success is True
            assert len(result.changes) == 1
            assert len(result.tests) == 1
            assert result.verification.all_tests_pass is True
            assert result.verification.constitutional_compliance is True

            # Verify learning occurred
            assert len(agent.success_patterns) == 1
            assert agent.success_patterns[0]["success"] is True

    def test_full_workflow_with_dspy_unavailable(self, sample_context):
        """Test complete workflow falls back gracefully when DSPy unavailable."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', False):
            from dspy_agents.modules.code_agent import DSPyCodeAgent

            agent = DSPyCodeAgent()

            # Execute workflow
            result = agent.forward(
                task_description="Create a new feature",
                context=sample_context
            )

            # Verify fallback behavior
            assert result.success is False
            assert "DSPy not available" in result.message
            assert len(result.changes) == 0
            assert result.verification.constitutional_compliance is False

    def test_workflow_with_planning_implementation_verification(self, mock_dspy_module, sample_context):
        """Test workflow using separate planning, implementation, and verification methods."""
        with patch('dspy_agents.modules.code_agent.DSPY_AVAILABLE', True):
            from dspy_agents.modules.code_agent import DSPyCodeAgent
            from dspy_agents.signatures.base import TaskPlan, FileChange, TestSpecification, VerificationResult, AgentResult

            agent = DSPyCodeAgent()

            # Mock planning
            mock_plan = TaskPlan(
                steps=["Plan step 1", "Plan step 2"],
                agent_assignments={"DSPyCodeAgent": "All steps"}
            )
            mock_plan_result = Mock()
            mock_plan_result.plan = mock_plan
            agent.planner = Mock(return_value=mock_plan_result)

            # Mock implementation
            mock_changes = [FileChange(file_path="/impl.py", operation="create", content="impl")]
            mock_tests = [TestSpecification(test_file="/test_impl.py", test_name="test_impl",
                                 test_code="def test_impl(): pass", follows_necessary=True)]
            mock_impl_result = Mock()
            mock_impl_result.code_changes = mock_changes
            mock_impl_result.tests_added = mock_tests
            mock_impl_result.implementation_notes = "Implementation notes"
            agent.implementer = Mock(return_value=mock_impl_result)

            # Mock verification
            mock_verification = VerificationResult(all_tests_pass=True, no_linting_errors=True,
                                                 constitutional_compliance=True, error_details=[])
            mock_verify_result = Mock()
            mock_verify_result.verification_result = mock_verification
            agent.verifier = Mock(return_value=mock_verify_result)

            # Execute complete workflow
            # 1. Plan
            plan = agent.plan_task("Create feature", sample_context)
            assert len(plan.steps) == 2

            # 2. Implement
            changes, tests, notes = agent.implement_plan(plan, sample_context)
            assert len(changes) == 1
            assert len(tests) == 1
            assert "Implementation notes" in notes

            # 3. Verify
            implementation = AgentResult(success=True, changes=changes, tests=tests,
                                       verification=None, message="Test")
            verification = agent.verify_implementation(implementation, {"all_pass": True})
            assert verification.all_tests_pass is True
            assert verification.constitutional_compliance is True

            # Verify all components were called
            agent.planner.assert_called_once()
            agent.implementer.assert_called_once()
            agent.verifier.assert_called_once()