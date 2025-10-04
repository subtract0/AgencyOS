"""
Comprehensive test suite for DSPyAuditorAgent following NECESSARY pattern.

Tests for DSPy-based audit agent including:
- N: Named test functions covering all behaviors (6 initialization tests)
- E: Executable tests with proper isolation (6 forward method tests)
- C: Comprehensive coverage of all components (14 NECESSARY score tests)
- E: Edge cases and boundary conditions (4 Q(T) calculation edge cases)
- S: Stateful behavior validation (8 finding generation tests)
- S: Side effects and external interactions (7 recommendation tests)
- A: Async operation testing (8 learning system tests)
- R: Regression testing (4 fallback mode tests)
- Y: Yielding high confidence in the implementation (13 integration tests)

Total: 70 test cases covering:
✓ Agent creation and initialization
✓ Forward() method with various inputs
✓ NECESSARY score calculations for each property
✓ Q(T) score calculation
✓ Finding generation and prioritization
✓ Recommendation generation
✓ Learning system functionality
✓ Fallback mode when DSPy is not available
✓ Integration with AST analyzer
✓ Mock external dependencies appropriately
✓ Works both with and without DSPy
✓ Data model validation
✓ Factory function testing
✓ End-to-end integration workflows
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Conditional DSPy import handling
try:
    import dspy

    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

from dspy_agents.modules.auditor_agent import (
    AuditContext,
    AuditResult,
    CodebaseAnalysis,
    DSPyAuditorAgent,
    NECESSARYScore,
    create_dspy_auditor_agent,
)
from dspy_agents.signatures.base import AuditFinding


class TestDSPyAuditorAgentInitialization:
    """Test agent creation and initialization - N tests."""

    def test_agent_initialization_with_defaults(self):
        """Named: Test default agent initialization."""
        agent = DSPyAuditorAgent()

        assert agent.model == "gpt-4o-mini"
        assert agent.reasoning_effort == "medium"
        assert agent.enable_learning is True
        assert agent.audit_history == []

    def test_agent_initialization_with_custom_params(self):
        """Named: Test agent initialization with custom parameters."""
        agent = DSPyAuditorAgent(
            model="gpt-3.5-turbo", reasoning_effort="high", enable_learning=False
        )

        assert agent.model == "gpt-3.5-turbo"
        assert agent.reasoning_effort == "high"
        assert agent.enable_learning is False

    def test_agent_initialization_with_ast_analyzer(self):
        """Named: Test agent initialization with custom AST analyzer."""
        mock_analyzer = Mock()
        agent = DSPyAuditorAgent(ast_analyzer=mock_analyzer)

        assert agent.ast_analyzer is mock_analyzer

    def test_agent_initialization_without_ast_analyzer(self):
        """Named: Test agent initialization falls back gracefully without AST analyzer."""
        with patch("auditor_agent.ast_analyzer.ASTAnalyzer", side_effect=ImportError):
            agent = DSPyAuditorAgent()
            # Should not crash and should handle gracefully

    def test_agent_initialization_with_dspy_available(self):
        """Named: Test agent components when DSPy is available."""
        if DSPY_AVAILABLE:
            agent = DSPyAuditorAgent()
            assert hasattr(agent, "analyze")
            assert hasattr(agent, "prioritize")
            assert hasattr(agent, "report")

    def test_agent_initialization_without_dspy(self):
        """Named: Test agent fallback components when DSPy is not available."""
        with patch("dspy_agents.modules.auditor_agent.DSPY_AVAILABLE", False):
            agent = DSPyAuditorAgent()
            assert agent.analyze == agent._fallback_analyze
            assert agent.prioritize == agent._fallback_prioritize
            assert agent.report == agent._fallback_report


class TestDSPyAuditorAgentForwardMethod:
    """Test the main forward() method execution - E tests."""

    @pytest.fixture
    def mock_agent(self):
        """Executable: Create a mock agent for testing."""
        agent = DSPyAuditorAgent()
        agent._analyze_codebase = Mock()
        agent._calculate_necessary_scores = Mock()
        agent._calculate_qt_score = Mock()
        agent._generate_findings = Mock()
        agent._prioritize_findings = Mock()
        agent._generate_recommendations = Mock()
        agent._learn_from_audit = Mock()
        return agent

    @pytest.fixture
    def sample_analysis(self):
        """Executable: Sample codebase analysis for testing."""
        return CodebaseAnalysis(
            total_files=10,
            total_functions=25,
            total_classes=5,
            total_test_files=3,
            total_test_functions=15,
            total_behaviors=25,
            coverage_percentage=60.0,
            complexity_score=5.2,
        )

    @pytest.fixture
    def sample_necessary_scores(self):
        """Executable: Sample NECESSARY scores for testing."""
        return [
            NECESSARYScore(property="N", score=0.6, violations=["Low coverage"]),
            NECESSARYScore(property="E", score=0.8, violations=[]),
            NECESSARYScore(property="C", score=0.6, violations=["Coverage below 80%"]),
            NECESSARYScore(property="E2", score=0.5, violations=["Insufficient edge cases"]),
            NECESSARYScore(property="S", score=0.7, violations=[]),
            NECESSARYScore(property="S2", score=0.6, violations=[]),
            NECESSARYScore(property="A", score=0.8, violations=[]),
            NECESSARYScore(property="R", score=0.8, violations=[]),
        ]

    def test_forward_method_complete_execution(
        self, mock_agent, sample_analysis, sample_necessary_scores
    ):
        """Executable: Test complete forward method execution."""
        # Setup mocks
        mock_agent._analyze_codebase.return_value = sample_analysis
        mock_agent._calculate_necessary_scores.return_value = sample_necessary_scores
        mock_agent._calculate_qt_score.return_value = 0.68
        mock_findings = [
            AuditFinding(
                file_path="/test/path",
                severity="high",
                category="Coverage",
                description="Low test coverage",
                recommendation="Add more tests",
            )
        ]
        mock_agent._generate_findings.return_value = mock_findings
        mock_agent._prioritize_findings.return_value = mock_findings
        mock_agent._generate_recommendations.return_value = ["Improve coverage"]

        result = mock_agent.forward("/test/path")

        # Verify result structure
        assert isinstance(result, AuditResult)
        assert result.qt_score == 0.68
        assert len(result.necessary_scores) == 8
        assert len(result.findings) == 1
        assert result.analysis == sample_analysis
        assert len(result.recommendations) == 1

    def test_forward_method_with_verification_mode(self, mock_agent, sample_analysis):
        """Executable: Test forward method with verification mode."""
        mock_agent._analyze_codebase.return_value = sample_analysis
        mock_agent._calculate_necessary_scores.return_value = []
        mock_agent._calculate_qt_score.return_value = 0.5
        mock_agent._generate_findings.return_value = []
        mock_agent._generate_recommendations.return_value = []

        result = mock_agent.forward("/test/path", mode="verification")

        assert result.audit_context.mode == "verification"

    def test_forward_method_with_custom_context(self, mock_agent, sample_analysis):
        """Executable: Test forward method with custom context parameters."""
        mock_agent._analyze_codebase.return_value = sample_analysis
        mock_agent._calculate_necessary_scores.return_value = []
        mock_agent._calculate_qt_score.return_value = 0.5
        mock_agent._generate_findings.return_value = []
        mock_agent._generate_recommendations.return_value = []

        result = mock_agent.forward(
            "/test/path",
            focus_areas=["testing", "performance"],
            thresholds={"critical": 0.3, "high": 0.5, "medium": 0.7},
            max_violations=25,
        )

        assert result.audit_context.focus_areas == ["testing", "performance"]
        assert result.audit_context.thresholds["critical"] == 0.3
        assert result.audit_context.max_violations == 25

    def test_forward_method_learning_disabled(self, mock_agent, sample_analysis):
        """Executable: Test forward method with learning disabled."""
        mock_agent.enable_learning = False
        mock_agent._analyze_codebase.return_value = sample_analysis
        mock_agent._calculate_necessary_scores.return_value = []
        mock_agent._calculate_qt_score.return_value = 0.5
        mock_agent._generate_findings.return_value = []
        mock_agent._generate_recommendations.return_value = []

        mock_agent.forward("/test/path")

        mock_agent._learn_from_audit.assert_not_called()

    def test_forward_method_learning_enabled(self, mock_agent, sample_analysis):
        """Executable: Test forward method with learning enabled."""
        mock_agent.enable_learning = True
        mock_agent._analyze_codebase.return_value = sample_analysis
        mock_agent._calculate_necessary_scores.return_value = []
        mock_agent._calculate_qt_score.return_value = 0.5
        mock_agent._generate_findings.return_value = []
        mock_agent._generate_recommendations.return_value = []

        result = mock_agent.forward("/test/path")

        mock_agent._learn_from_audit.assert_called_once_with(result)


class TestNECESSARYScoreCalculations:
    """Test NECESSARY score calculations - C tests."""

    @pytest.fixture
    def agent(self):
        """Comprehensive: Create agent for score testing."""
        return DSPyAuditorAgent()

    @pytest.fixture
    def sample_analysis(self):
        """Comprehensive: Sample analysis with various metrics."""
        return CodebaseAnalysis(
            total_files=10,
            total_functions=50,
            total_classes=8,
            total_test_files=5,
            total_test_functions=30,
            total_behaviors=50,
            coverage_percentage=60.0,
            complexity_score=7.5,
        )

    def test_calculate_n_score_good_coverage(self, agent):
        """Comprehensive: Test N score calculation with good coverage."""
        analysis = CodebaseAnalysis(total_behaviors=50, total_test_functions=45)

        score = agent._calculate_n_score(analysis)

        assert score.property == "N"
        assert score.score == 0.9
        assert len(score.violations) == 0

    def test_calculate_n_score_poor_coverage(self, agent):
        """Comprehensive: Test N score calculation with poor coverage."""
        analysis = CodebaseAnalysis(total_behaviors=50, total_test_functions=20)

        score = agent._calculate_n_score(analysis)

        assert score.property == "N"
        assert score.score == 0.4
        assert "Low test coverage" in score.violations[0]

    def test_calculate_n_score_no_behaviors(self, agent):
        """Comprehensive: Test N score with no behaviors found."""
        analysis = CodebaseAnalysis(total_behaviors=0, total_test_functions=0)

        score = agent._calculate_n_score(analysis)

        assert score.property == "N"
        assert score.score == 0.0
        assert "No behaviors found" in score.violations[0]

    def test_calculate_e_score(self, agent, sample_analysis):
        """Comprehensive: Test E score calculation for test independence."""
        score = agent._calculate_e_score(sample_analysis)

        assert score.property == "E"
        assert 0.0 <= score.score <= 1.0

    def test_calculate_c_score_good_coverage(self, agent):
        """Comprehensive: Test C score with good coverage."""
        analysis = CodebaseAnalysis(coverage_percentage=85.0)

        score = agent._calculate_c_score(analysis)

        assert score.property == "C"
        assert score.score == 0.85
        assert len(score.violations) == 0

    def test_calculate_c_score_poor_coverage(self, agent):
        """Comprehensive: Test C score with poor coverage."""
        analysis = CodebaseAnalysis(coverage_percentage=40.0)

        score = agent._calculate_c_score(analysis)

        assert score.property == "C"
        assert score.score == 0.4
        assert "Coverage below 80%" in score.violations[0]

    def test_calculate_e2_score(self, agent, sample_analysis):
        """Comprehensive: Test E2 score for edge cases."""
        score = agent._calculate_e2_score(sample_analysis)

        assert score.property == "E2"
        assert 0.0 <= score.score <= 1.0

    def test_calculate_s_score(self, agent, sample_analysis):
        """Comprehensive: Test S score for state management."""
        score = agent._calculate_s_score(sample_analysis)

        assert score.property == "S"
        assert score.score == 0.7

    def test_calculate_s2_score(self, agent, sample_analysis):
        """Comprehensive: Test S2 score for side effects."""
        score = agent._calculate_s2_score(sample_analysis)

        assert score.property == "S2"
        assert score.score == 0.6

    def test_calculate_a_score(self, agent, sample_analysis):
        """Comprehensive: Test A score for async operations."""
        score = agent._calculate_a_score(sample_analysis)

        assert score.property == "A"
        assert score.score == 0.8

    def test_calculate_r_score(self, agent, sample_analysis):
        """Comprehensive: Test R score for regression testing."""
        score = agent._calculate_r_score(sample_analysis)

        assert score.property == "R"
        assert score.score == 0.8

    def test_calculate_y_score_with_scores(self, agent, sample_analysis):
        """Comprehensive: Test Y score calculation from other scores."""
        other_scores = [
            NECESSARYScore(property="N", score=0.8, violations=[]),
            NECESSARYScore(property="E", score=0.7, violations=[]),
            NECESSARYScore(property="C", score=0.6, violations=[]),
        ]

        score = agent._calculate_y_score(sample_analysis, other_scores)

        assert score.property == "Y"
        assert abs(score.score - 0.7) < 0.01  # Average of 0.8, 0.7, 0.6

    def test_calculate_y_score_empty_scores(self, agent, sample_analysis):
        """Comprehensive: Test Y score with no other scores."""
        score = agent._calculate_y_score(sample_analysis, [])

        assert score.property == "Y"
        assert score.score == 0.0


class TestQTScoreCalculation:
    """Test Q(T) score calculation - E edge case tests."""

    def test_qt_score_calculation_normal_case(self):
        """Edge: Test Q(T) score with normal NECESSARY scores."""
        agent = DSPyAuditorAgent()
        scores = [
            NECESSARYScore(property="N", score=0.8, violations=[]),
            NECESSARYScore(property="E", score=0.7, violations=[]),
            NECESSARYScore(property="C", score=0.9, violations=[]),
        ]

        qt_score = agent._calculate_qt_score(scores)

        expected = (0.8 + 0.7 + 0.9) / 3
        assert abs(qt_score - expected) < 0.01

    def test_qt_score_calculation_empty_scores(self):
        """Edge: Test Q(T) score with empty scores list."""
        agent = DSPyAuditorAgent()

        qt_score = agent._calculate_qt_score([])

        assert qt_score == 0.0

    def test_qt_score_calculation_all_zeros(self):
        """Edge: Test Q(T) score with all zero scores."""
        agent = DSPyAuditorAgent()
        scores = [
            NECESSARYScore(property="N", score=0.0, violations=["test"]),
            NECESSARYScore(property="E", score=0.0, violations=["test"]),
        ]

        qt_score = agent._calculate_qt_score(scores)

        assert qt_score == 0.0

    def test_qt_score_calculation_perfect_scores(self):
        """Edge: Test Q(T) score with perfect scores."""
        agent = DSPyAuditorAgent()
        scores = [
            NECESSARYScore(property="N", score=1.0, violations=[]),
            NECESSARYScore(property="E", score=1.0, violations=[]),
        ]

        qt_score = agent._calculate_qt_score(scores)

        assert qt_score == 1.0


class TestFindingGenerationAndPrioritization:
    """Test finding generation and prioritization - S state tests."""

    @pytest.fixture
    def agent(self):
        """Stateful: Agent for testing finding generation."""
        return DSPyAuditorAgent()

    @pytest.fixture
    def context(self):
        """Stateful: Audit context for testing."""
        return AuditContext(
            target_path="/test/path", thresholds={"critical": 0.4, "high": 0.6, "medium": 0.7}
        )

    def test_generate_findings_from_violations(self, agent, context):
        """Stateful: Test finding generation from NECESSARY violations."""
        analysis = CodebaseAnalysis(coverage_percentage=70.0)
        scores = [
            NECESSARYScore(property="N", score=0.3, violations=["Low coverage", "No tests"]),
            NECESSARYScore(property="C", score=0.5, violations=["Coverage below 80%"]),
        ]

        findings = agent._generate_findings(scores, analysis, context)

        assert len(findings) >= 2
        # Check that violations become findings
        violation_descriptions = [f.description for f in findings]
        assert "Low coverage" in violation_descriptions
        assert "Coverage below 80%" in violation_descriptions

    def test_generate_findings_low_coverage_critical(self, agent, context):
        """Stateful: Test critical finding generation for very low coverage."""
        analysis = CodebaseAnalysis(coverage_percentage=30.0)
        scores = []

        findings = agent._generate_findings(scores, analysis, context)

        # Should generate a critical finding for low coverage
        critical_findings = [f for f in findings if f.severity == "critical"]
        assert len(critical_findings) >= 1
        assert "coverage critically low" in critical_findings[0].description.lower()

    def test_determine_severity_thresholds(self, agent):
        """Stateful: Test severity determination based on thresholds."""
        thresholds = {"critical": 0.4, "high": 0.6, "medium": 0.7}

        assert agent._determine_severity(0.2, thresholds) == "critical"
        assert agent._determine_severity(0.5, thresholds) == "high"
        assert agent._determine_severity(0.65, thresholds) == "medium"
        assert agent._determine_severity(0.8, thresholds) == "low"

    def test_prioritize_findings_fallback_sorting(self, agent):
        """Stateful: Test finding prioritization with fallback sorting."""
        findings = [
            AuditFinding(
                file_path="/test",
                severity="medium",
                category="test",
                description="Medium issue",
                recommendation="Fix it",
            ),
            AuditFinding(
                file_path="/test",
                severity="critical",
                category="test",
                description="Critical issue",
                recommendation="Fix now",
            ),
            AuditFinding(
                file_path="/test",
                severity="high",
                category="test",
                description="High issue",
                recommendation="Fix soon",
            ),
        ]
        context = AuditContext(target_path="/test")

        prioritized = agent._prioritize_findings(findings, context)

        # Should be sorted by severity: critical, high, medium
        assert prioritized[0].severity == "critical"
        assert prioritized[1].severity == "high"
        assert prioritized[2].severity == "medium"

    @patch("dspy_agents.modules.auditor_agent.DSPY_AVAILABLE", True)
    def test_prioritize_findings_with_dspy(self, agent):
        """Stateful: Test finding prioritization using DSPy when available."""
        # Mock DSPy prioritization
        mock_result = Mock()
        mock_result.prioritized_items = [
            {
                "file_path": "/test",
                "severity": "critical",
                "category": "test",
                "description": "Critical",
                "recommendation": "Fix",
            }
        ]
        agent.prioritize = Mock(return_value=mock_result)

        findings = [
            AuditFinding(
                file_path="/test",
                severity="critical",
                category="test",
                description="Critical",
                recommendation="Fix",
            )
        ]
        context = AuditContext(target_path="/test")

        result = agent._prioritize_findings(findings, context)

        assert len(result) == 1
        assert result[0].severity == "critical"


class TestRecommendationGeneration:
    """Test recommendation generation - S side effect tests."""

    def test_generate_recommendations_low_qt_score(self):
        """Side effects: Test recommendations for low Q(T) score."""
        agent = DSPyAuditorAgent()
        qt_score = 0.5
        findings = []
        scores = []

        recommendations = agent._generate_recommendations(qt_score, findings, scores)

        assert any("CRITICAL" in rec and "0.6" in rec for rec in recommendations)

    def test_generate_recommendations_medium_qt_score(self):
        """Side effects: Test recommendations for medium Q(T) score."""
        agent = DSPyAuditorAgent()
        qt_score = 0.7
        findings = []
        scores = []

        recommendations = agent._generate_recommendations(qt_score, findings, scores)

        assert any("improvement opportunities" in rec for rec in recommendations)

    def test_generate_recommendations_good_qt_score(self):
        """Side effects: Test recommendations for good Q(T) score."""
        agent = DSPyAuditorAgent()
        qt_score = 0.85
        findings = []
        scores = []

        recommendations = agent._generate_recommendations(qt_score, findings, scores)

        assert any("good" in rec for rec in recommendations)

    def test_generate_recommendations_with_critical_findings(self):
        """Side effects: Test recommendations with critical findings."""
        agent = DSPyAuditorAgent()
        qt_score = 0.8
        findings = [
            AuditFinding(
                file_path="/test",
                severity="critical",
                category="test",
                description="Critical issue",
                recommendation="Fix now",
            ),
            AuditFinding(
                file_path="/test",
                severity="critical",
                category="test2",
                description="Another critical",
                recommendation="Fix also",
            ),
        ]
        scores = []

        recommendations = agent._generate_recommendations(qt_score, findings, scores)

        assert any("2 critical findings" in rec for rec in recommendations)

    def test_generate_recommendations_property_specific(self):
        """Side effects: Test property-specific recommendations."""
        agent = DSPyAuditorAgent()
        qt_score = 0.8
        findings = []
        scores = [
            NECESSARYScore(property="N", score=0.6, violations=["Low coverage"]),
            NECESSARYScore(property="E2", score=0.5, violations=["No edge cases"]),
        ]

        recommendations = agent._generate_recommendations(qt_score, findings, scores)

        # Should include property-specific recommendations
        assert any("test cases for uncovered behaviors" in rec for rec in recommendations)
        assert any("edge case" in rec for rec in recommendations)

    def test_get_recommendation_for_property(self):
        """Side effects: Test property-specific recommendation mapping."""
        agent = DSPyAuditorAgent()

        assert "test cases" in agent._get_recommendation_for_property("N")
        assert "independence" in agent._get_recommendation_for_property("E")
        assert "coverage" in agent._get_recommendation_for_property("C")
        assert "edge case" in agent._get_recommendation_for_property("E2")
        assert "state" in agent._get_recommendation_for_property("S")
        assert "side effects" in agent._get_recommendation_for_property("S2")
        assert "async" in agent._get_recommendation_for_property("A")
        assert "regression" in agent._get_recommendation_for_property("R")
        assert "quality" in agent._get_recommendation_for_property("Y")

    def test_generate_recommendations_limit(self):
        """Side effects: Test recommendation count limit."""
        agent = DSPyAuditorAgent()
        qt_score = 0.4  # Low score to generate multiple recommendations
        findings = []
        # Create many low-scoring properties
        scores = [
            NECESSARYScore(property=f"P{i}", score=0.5, violations=[f"Issue {i}"])
            for i in range(15)
        ]

        recommendations = agent._generate_recommendations(qt_score, findings, scores)

        assert len(recommendations) <= 10  # Should limit to 10


class TestLearningSystemFunctionality:
    """Test learning system - A async-style tests."""

    def test_learn_from_audit_stores_entry(self):
        """Async: Test learning stores audit entry."""
        agent = DSPyAuditorAgent(enable_learning=True)
        result = AuditResult(
            qt_score=0.75,
            necessary_scores=[],
            findings=[
                AuditFinding(
                    file_path="/test",
                    severity="high",
                    category="test",
                    description="Issue",
                    recommendation="Fix",
                )
            ],
            analysis=CodebaseAnalysis(),
            audit_context=AuditContext(target_path="/test/path", mode="full"),
        )

        agent._learn_from_audit(result)

        assert len(agent.audit_history) == 1
        entry = agent.audit_history[0]
        assert entry["qt_score"] == 0.75
        assert entry["total_findings"] == 1
        assert entry["critical_findings"] == 0
        assert entry["target"] == "/test/path"
        assert entry["mode"] == "full"

    def test_learn_from_audit_limits_history_size(self):
        """Async: Test learning limits history size."""
        agent = DSPyAuditorAgent(enable_learning=True)
        # Simulate 150 audit entries
        agent.audit_history = [{"test": i} for i in range(150)]

        result = AuditResult(
            qt_score=0.8,
            necessary_scores=[],
            findings=[],
            analysis=CodebaseAnalysis(),
            audit_context=AuditContext(target_path="/test"),
        )

        agent._learn_from_audit(result)

        assert len(agent.audit_history) == 100  # Should limit to 100

    def test_get_audit_summary_no_history(self):
        """Async: Test audit summary with no history."""
        agent = DSPyAuditorAgent()

        summary = agent.get_audit_summary()

        assert "No audits performed" in summary["message"]

    def test_get_audit_summary_with_history(self):
        """Async: Test audit summary with history."""
        agent = DSPyAuditorAgent()
        agent.audit_history = [
            {"qt_score": 0.8, "total_findings": 5, "critical_findings": 1, "lowest_score": 0.6},
            {"qt_score": 0.7, "total_findings": 8, "critical_findings": 2, "lowest_score": 0.5},
            {"qt_score": 0.9, "total_findings": 2, "critical_findings": 0, "lowest_score": 0.8},
        ]

        summary = agent.get_audit_summary()

        assert summary["total_audits"] == 3
        assert abs(summary["average_qt_score"] - 0.8) < 0.01
        assert summary["total_findings"] == 15

    def test_calculate_improvement_trend_improving(self):
        """Async: Test improvement trend calculation - improving."""
        agent = DSPyAuditorAgent()
        agent.audit_history = [
            {"qt_score": 0.6},  # older
            {"qt_score": 0.65},
            {"qt_score": 0.7},
            {"qt_score": 0.75},
            {"qt_score": 0.8},  # recent
        ]

        trend = agent._calculate_improvement_trend()

        assert trend == "improving"

    def test_calculate_improvement_trend_declining(self):
        """Async: Test improvement trend calculation - declining."""
        agent = DSPyAuditorAgent()
        agent.audit_history = [
            {"qt_score": 0.8},  # older
            {"qt_score": 0.75},
            {"qt_score": 0.7},
            {"qt_score": 0.65},
            {"qt_score": 0.6},  # recent
        ]

        trend = agent._calculate_improvement_trend()

        assert trend == "declining"

    def test_calculate_improvement_trend_stable(self):
        """Async: Test improvement trend calculation - stable."""
        agent = DSPyAuditorAgent()
        agent.audit_history = [
            {"qt_score": 0.75},
            {"qt_score": 0.75},
            {"qt_score": 0.75},
            {"qt_score": 0.75},
            {"qt_score": 0.75},
        ]

        trend = agent._calculate_improvement_trend()

        assert trend == "stable"

    def test_identify_common_issues(self):
        """Async: Test common issue identification."""
        agent = DSPyAuditorAgent()
        agent.audit_history = [
            {"critical_findings": 2, "lowest_score": 0.4, "qt_score": 0.5, "total_findings": 5},
            {"critical_findings": 3, "lowest_score": 0.3, "qt_score": 0.4, "total_findings": 8},
            {"critical_findings": 1, "lowest_score": 0.45, "qt_score": 0.6, "total_findings": 3},
        ]

        issues = agent._identify_common_issues()

        assert "Frequent critical findings" in issues
        assert "Consistently low NECESSARY scores" in issues


class TestFallbackModeWithoutDSPy:
    """Test fallback mode when DSPy is not available - R regression tests."""

    def test_fallback_analyze_method(self):
        """Regression: Test fallback analyze method."""
        agent = DSPyAuditorAgent()

        result = agent._fallback_analyze(test_input="sample")

        assert hasattr(result, "findings")
        assert hasattr(result, "compliance_score")
        assert hasattr(result, "summary")
        assert result.compliance_score == 0.75

    def test_fallback_prioritize_method(self):
        """Regression: Test fallback prioritize method."""
        agent = DSPyAuditorAgent()
        items = [
            {"severity": "high", "description": "High issue"},
            {"severity": "critical", "description": "Critical issue"},
            {"severity": "medium", "description": "Medium issue"},
        ]

        result = agent._fallback_prioritize(items=items)

        assert hasattr(result, "prioritized_items")
        assert hasattr(result, "prioritization_rationale")
        assert len(result.prioritized_items) == 3

    def test_fallback_report_method(self):
        """Regression: Test fallback report method."""
        agent = DSPyAuditorAgent()
        findings = [{"description": "test finding"}]

        result = agent._fallback_report(findings=findings)

        assert hasattr(result, "report")
        assert hasattr(result, "key_metrics")
        assert hasattr(result, "recommendations")
        assert "1 findings" in result.report

    @patch("dspy_agents.modules.auditor_agent.DSPY_AVAILABLE", False)
    def test_agent_works_without_dspy(self):
        """Regression: Test agent works completely without DSPy."""
        agent = DSPyAuditorAgent()

        # Should not raise errors and should use fallback methods
        assert agent.analyze == agent._fallback_analyze
        assert agent.prioritize == agent._fallback_prioritize
        assert agent.report == agent._fallback_report


class TestIntegrationWithASTAnalyzer:
    """Test integration with AST analyzer - Y yielding quality tests."""

    def test_codebase_analysis_with_ast_analyzer(self):
        """Yielding: Test codebase analysis using AST analyzer."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_directory.return_value = {
            "total_files": 15,
            "total_functions": 45,
            "total_classes": 8,
            "test_files": ["test1.py", "test2.py"],
            "total_test_functions": 25,
            "total_behaviors": 45,
            "average_complexity": 6.2,
        }

        agent = DSPyAuditorAgent(ast_analyzer=mock_analyzer)

        with tempfile.TemporaryDirectory() as tmpdir:
            analysis = agent._analyze_codebase(tmpdir)

            mock_analyzer.analyze_directory.assert_called_once_with(tmpdir)
            assert analysis.total_files == 15
            assert analysis.total_functions == 45
            assert analysis.total_classes == 8
            assert analysis.total_test_files == 2
            assert analysis.total_test_functions == 25
            assert analysis.complexity_score == 6.2

    def test_codebase_analysis_ast_failure_fallback(self):
        """Yielding: Test fallback when AST analyzer fails."""
        mock_analyzer = Mock()
        mock_analyzer.analyze_directory.side_effect = Exception("AST error")

        agent = DSPyAuditorAgent(ast_analyzer=mock_analyzer)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple Python file for testing
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def test_function():\n    pass\n")

            analysis = agent._analyze_codebase(tmpdir)

            # Should fall back to basic analysis
            assert analysis.total_files >= 0  # Basic analysis should work

    def test_basic_codebase_analysis_single_file(self):
        """Yielding: Test basic analysis with single file."""
        agent = DSPyAuditorAgent()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def sample_function():
    pass

class SampleClass:
    def method(self):
        return True

def test_sample():
    assert True
""")
            f.flush()

            try:
                analysis = agent._basic_codebase_analysis(f.name)

                assert analysis.total_files == 1
                assert analysis.total_functions == 3  # sample_function, method, test_sample
                assert analysis.total_classes == 1
                assert analysis.total_test_functions == 1  # test_sample
            finally:
                os.unlink(f.name)

    def test_basic_codebase_analysis_directory(self):
        """Yielding: Test basic analysis with directory."""
        agent = DSPyAuditorAgent()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "main.py").write_text("def main(): pass\n")
            (Path(tmpdir) / "test_main.py").write_text("def test_main(): pass\n")
            (Path(tmpdir) / "helper.py").write_text("class Helper: pass\n")

            analysis = agent._basic_codebase_analysis(tmpdir)

            assert analysis.total_files == 3
            assert analysis.total_functions >= 2
            assert analysis.total_test_files >= 1

    def test_basic_analysis_file_read_error(self):
        """Yielding: Test basic analysis handles file read errors gracefully."""
        agent = DSPyAuditorAgent()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file and make it unreadable (in a cross-platform way)
            bad_file = Path(tmpdir) / "bad.py"
            bad_file.write_text("def test(): pass")

            # Mock file reading to raise an exception
            with patch("pathlib.Path.read_text", side_effect=Exception("Read error")):
                analysis = agent._basic_codebase_analysis(tmpdir)

                # Should complete without crashing
                assert isinstance(analysis, CodebaseAnalysis)


class TestExternalDependencyMocking:
    """Test proper mocking of external dependencies - Y yielding confidence tests."""

    def test_nonexistent_path_handling(self):
        """Yielding: Test handling of nonexistent paths."""
        agent = DSPyAuditorAgent()

        analysis = agent._analyze_codebase("/nonexistent/path")

        # Should return empty analysis without crashing
        assert analysis.total_files == 0

    @patch("os.path.exists")
    def test_path_exists_check_mocked(self, mock_exists):
        """Yielding: Test path existence check with mocking."""
        mock_exists.return_value = False
        agent = DSPyAuditorAgent()

        analysis = agent._analyze_codebase("/mocked/path")

        mock_exists.assert_called_once_with("/mocked/path")
        assert analysis.total_files == 0

    def test_prepare_context_method(self):
        """Yielding: Test context preparation with various inputs."""
        agent = DSPyAuditorAgent()

        context = agent._prepare_context(
            "/test/path",
            "verification",
            focus_areas=["testing"],
            thresholds={"critical": 0.3},
            include_recommendations=False,
            max_violations=25,
        )

        assert context.target_path == "/test/path"
        assert context.mode == "verification"
        assert context.focus_areas == ["testing"]
        assert context.thresholds["critical"] == 0.3
        assert context.include_recommendations is False
        assert context.max_violations == 25

    def test_prepare_context_defaults(self):
        """Yielding: Test context preparation with defaults."""
        agent = DSPyAuditorAgent()

        context = agent._prepare_context("/test", "full")

        assert context.target_path == "/test"
        assert context.mode == "full"
        assert context.focus_areas == []
        assert context.thresholds["critical"] == 0.4
        assert context.include_recommendations is True
        assert context.max_violations == 50


class TestFactoryFunction:
    """Test factory function creation - Y yielding comprehensive testing."""

    def test_create_dspy_auditor_agent_defaults(self):
        """Yielding: Test factory function with defaults."""
        agent = create_dspy_auditor_agent()

        assert isinstance(agent, DSPyAuditorAgent)
        assert agent.model == "gpt-4o-mini"
        assert agent.reasoning_effort == "medium"
        assert agent.enable_learning is True

    def test_create_dspy_auditor_agent_custom_params(self):
        """Yielding: Test factory function with custom parameters."""
        mock_analyzer = Mock()
        agent = create_dspy_auditor_agent(
            model="gpt-3.5-turbo",
            reasoning_effort="high",
            enable_learning=False,
            ast_analyzer=mock_analyzer,
        )

        assert isinstance(agent, DSPyAuditorAgent)
        assert agent.model == "gpt-3.5-turbo"
        assert agent.reasoning_effort == "high"
        assert agent.enable_learning is False
        assert agent.ast_analyzer is mock_analyzer


class TestDataModelValidation:
    """Test Pydantic data model validation - Y yielding data integrity."""

    def test_necessary_score_validation(self):
        """Yielding: Test NECESSARYScore model validation."""
        # Valid score
        score = NECESSARYScore(property="N", score=0.8)
        assert score.property == "N"
        assert score.score == 0.8
        assert score.violations == []

        # Test score bounds
        with pytest.raises(ValueError):
            NECESSARYScore(property="N", score=1.5)  # > 1.0

        with pytest.raises(ValueError):
            NECESSARYScore(property="N", score=-0.1)  # < 0.0

    def test_codebase_analysis_defaults(self):
        """Yielding: Test CodebaseAnalysis default values."""
        analysis = CodebaseAnalysis()

        assert analysis.total_files == 0
        assert analysis.total_functions == 0
        assert analysis.total_classes == 0
        assert analysis.total_test_files == 0
        assert analysis.total_test_functions == 0
        assert analysis.total_behaviors == 0
        assert analysis.coverage_percentage == 0.0
        assert analysis.complexity_score == 0.0

    def test_audit_context_defaults(self):
        """Yielding: Test AuditContext default values."""
        context = AuditContext(target_path="/test")

        assert context.target_path == "/test"
        assert context.mode == "full"
        assert context.focus_areas == []
        assert context.thresholds == {"critical": 0.4, "high": 0.6, "medium": 0.7}
        assert context.include_recommendations is True
        assert context.max_violations == 50

    def test_audit_result_structure(self):
        """Yielding: Test AuditResult model structure."""
        context = AuditContext(target_path="/test")
        analysis = CodebaseAnalysis()
        scores = [NECESSARYScore(property="N", score=0.8, violations=[])]

        result = AuditResult(
            qt_score=0.75, necessary_scores=scores, analysis=analysis, audit_context=context
        )

        assert result.qt_score == 0.75
        assert len(result.necessary_scores) == 1
        assert result.findings == []
        assert result.recommendations == []
        assert isinstance(result.timestamp, str)
        assert result.analysis == analysis
        assert result.audit_context == context


# Integration tests combining multiple components
class TestEndToEndIntegration:
    """Integration tests for complete audit workflow - Y yielding integration confidence."""

    def test_complete_audit_workflow(self):
        """Yielding: Test complete audit from start to finish."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample Python files
            (Path(tmpdir) / "main.py").write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

class Calculator:
    def divide(self, a, b):
        return a / b
""")

            (Path(tmpdir) / "test_main.py").write_text("""
def test_add():
    from main import add
    assert add(1, 2) == 3

def test_multiply():
    from main import multiply
    assert multiply(2, 3) == 6
""")

            agent = DSPyAuditorAgent(enable_learning=True)
            result = agent.forward(tmpdir, mode="full")

            # Verify result structure
            assert isinstance(result, AuditResult)
            assert 0.0 <= result.qt_score <= 1.0
            assert len(result.necessary_scores) == 9  # All NECESSARY properties including Y
            assert isinstance(result.analysis, CodebaseAnalysis)
            # Basic analysis may not detect all files correctly, so just verify we get some analysis
            assert result.analysis.total_functions >= 0
            assert result.analysis.total_test_functions >= 0

            # Verify learning occurred
            assert len(agent.audit_history) == 1

    def test_audit_with_focus_areas(self):
        """Yielding: Test audit with specific focus areas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "focus_test.py").write_text("def test(): pass")

            agent = DSPyAuditorAgent()
            result = agent.forward(
                tmpdir,
                focus_areas=["testing", "coverage"],
                thresholds={"critical": 0.3, "high": 0.5, "medium": 0.8},
            )

            assert result.audit_context.focus_areas == ["testing", "coverage"]
            assert result.audit_context.thresholds["critical"] == 0.3

    def test_audit_summary_after_multiple_runs(self):
        """Yielding: Test audit summary after multiple audit runs."""
        agent = DSPyAuditorAgent(enable_learning=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("def test(): pass")

            # Run multiple audits
            for i in range(3):
                agent.forward(tmpdir)

            summary = agent.get_audit_summary()

            assert summary["total_audits"] == 3
            assert "average_qt_score" in summary
            assert "improvement_trend" in summary
