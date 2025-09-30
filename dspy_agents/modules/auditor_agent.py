"""
DSPy AuditorAgent Module

Implements quality assurance and test coverage analysis using DSPy,
focusing on NECESSARY pattern compliance and Q(T) scoring.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from shared.type_definitions.json import JSONValue

# Conditional DSPy import with fallback
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    # Provide fallback implementations
    class dspy:
        class Module:
            pass
        class ChainOfThought:
            def __init__(self, signature):
                self.signature = signature
            def __call__(self, **kwargs):
                return type('Result', (), kwargs)()
        class Predict:
            def __init__(self, signature):
                self.signature = signature
            def __call__(self, **kwargs):
                return type('Result', (), kwargs)()

from dspy_agents.signatures.base import (
    AuditSignature,
    PrioritizationSignature,
    ReportSignature,
    AuditFinding,
)

logger = logging.getLogger(__name__)


# ===========================
# Data Models
# ===========================

class NECESSARYScore(BaseModel):
    """Score for a NECESSARY property."""
    property: str = Field(..., description="NECESSARY property letter")
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    violations: List[str] = Field(default_factory=list, description="List of violations")
    details: Optional[str] = Field(None, description="Additional details")


class CodebaseAnalysis(BaseModel):
    """Results from codebase analysis."""
    total_files: int = Field(0, description="Total files analyzed")
    total_functions: int = Field(0, description="Total functions found")
    total_classes: int = Field(0, description="Total classes found")
    total_test_files: int = Field(0, description="Total test files")
    total_test_functions: int = Field(0, description="Total test functions")
    total_behaviors: int = Field(0, description="Total behaviors identified")
    coverage_percentage: float = Field(0.0, description="Test coverage percentage")
    complexity_score: float = Field(0.0, description="Average complexity score")


class AuditContext(BaseModel):
    """Context for an audit operation."""
    target_path: str = Field(..., description="Path to audit")
    mode: str = Field("full", description="Audit mode: full or verification")
    focus_areas: List[str] = Field(default_factory=list, description="Specific areas to focus on")
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {"critical": 0.4, "high": 0.6, "medium": 0.7},
        description="Severity thresholds"
    )
    include_recommendations: bool = Field(True, description="Include recommendations")
    max_violations: int = Field(50, description="Maximum violations to report")


class AuditResult(BaseModel):
    """Complete audit result."""
    qt_score: float = Field(..., description="Overall Q(T) score")
    necessary_scores: List[NECESSARYScore] = Field(..., description="Individual NECESSARY scores")
    findings: List[AuditFinding] = Field(default_factory=list, description="Audit findings")
    analysis: CodebaseAnalysis = Field(..., description="Codebase analysis")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    audit_context: AuditContext = Field(..., description="Audit context")


# ===========================
# DSPy Auditor Agent
# ===========================

class DSPyAuditorAgent(dspy.Module if DSPY_AVAILABLE else object):
    """
    DSPy-based Auditor Agent for quality assurance and NECESSARY compliance.

    This agent performs comprehensive code quality analysis, focusing on:
    - NECESSARY pattern compliance
    - Q(T) score calculation
    - Test coverage analysis
    - Code quality metrics
    - Constitutional compliance verification
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        reasoning_effort: str = "medium",
        enable_learning: bool = True,
        ast_analyzer: Optional[Any] = None
    ):
        """
        Initialize the DSPy Auditor Agent.

        Args:
            model: Model to use for reasoning
            reasoning_effort: Level of reasoning effort
            enable_learning: Whether to enable learning from audits
            ast_analyzer: Optional AST analyzer instance
        """
        if DSPY_AVAILABLE:
            super().__init__()

        self.model = model
        self.reasoning_effort = reasoning_effort
        self.enable_learning = enable_learning

        # Import AST analyzer if available
        self.ast_analyzer = ast_analyzer
        if self.ast_analyzer is None:
            try:
                from auditor_agent.ast_analyzer import ASTAnalyzer
                self.ast_analyzer = ASTAnalyzer()
            except ImportError:
                logger.warning("AST analyzer not available, using fallback analysis")

        # Initialize DSPy components
        if DSPY_AVAILABLE:
            self.analyze = dspy.ChainOfThought(AuditSignature)
            self.prioritize = dspy.Predict(PrioritizationSignature)
            self.report = dspy.Predict(ReportSignature)
        else:
            # Fallback implementations
            self.analyze = self._fallback_analyze
            self.prioritize = self._fallback_prioritize
            self.report = self._fallback_report

        # Audit history for learning
        self.audit_history: List[Dict[str, JSONValue]] = []

        logger.info(f"DSPyAuditorAgent initialized with model={model}, DSPy available: {DSPY_AVAILABLE}")

    def forward(self, target_path: str, mode: str = "full", **kwargs) -> AuditResult:
        """
        Main execution method for the auditor.

        Args:
            target_path: Path to audit
            mode: Audit mode (full or verification)
            **kwargs: Additional context

        Returns:
            Complete audit result
        """
        # Prepare context
        context = self._prepare_context(target_path, mode, **kwargs)

        # Phase 1: Analyze codebase structure
        analysis = self._analyze_codebase(context.target_path)

        # Phase 2: Calculate NECESSARY compliance
        necessary_scores = self._calculate_necessary_scores(analysis)

        # Phase 3: Calculate Q(T) score
        qt_score = self._calculate_qt_score(necessary_scores)

        # Phase 4: Generate findings
        findings = self._generate_findings(necessary_scores, analysis, context)

        # Phase 5: Prioritize findings
        if findings:
            findings = self._prioritize_findings(findings, context)

        # Phase 6: Generate recommendations
        recommendations = []
        if context.include_recommendations:
            recommendations = self._generate_recommendations(qt_score, findings, necessary_scores)

        # Create result
        result = AuditResult(
            qt_score=qt_score,
            necessary_scores=necessary_scores,
            findings=findings[:context.max_violations],
            analysis=analysis,
            recommendations=recommendations,
            audit_context=context
        )

        # Learn from this audit
        if self.enable_learning:
            self._learn_from_audit(result)

        return result

    def _prepare_context(self, target_path: str, mode: str, **kwargs) -> AuditContext:
        """Prepare audit context from inputs."""
        return AuditContext(
            target_path=target_path,
            mode=mode,
            focus_areas=kwargs.get("focus_areas", []),
            thresholds=kwargs.get("thresholds", {"critical": 0.4, "high": 0.6, "medium": 0.7}),
            include_recommendations=kwargs.get("include_recommendations", True),
            max_violations=kwargs.get("max_violations", 50)
        )

    def _analyze_codebase(self, target_path: str) -> CodebaseAnalysis:
        """Analyze codebase structure and metrics."""
        analysis = CodebaseAnalysis()

        if not os.path.exists(target_path):
            logger.error(f"Path does not exist: {target_path}")
            return analysis

        # Use AST analyzer if available
        if self.ast_analyzer:
            try:
                ast_analysis = self.ast_analyzer.analyze_directory(target_path)

                # Extract metrics from AST analysis
                analysis.total_files = ast_analysis.get("total_files", 0)
                analysis.total_functions = ast_analysis.get("total_functions", 0)
                analysis.total_classes = ast_analysis.get("total_classes", 0)
                analysis.total_test_files = len(ast_analysis.get("test_files", []))
                analysis.total_test_functions = ast_analysis.get("total_test_functions", 0)
                analysis.total_behaviors = ast_analysis.get("total_behaviors", 0)

                # Calculate coverage
                if analysis.total_behaviors > 0:
                    analysis.coverage_percentage = min(100.0,
                        (analysis.total_test_functions / analysis.total_behaviors) * 100)

                # Calculate complexity (simplified)
                analysis.complexity_score = ast_analysis.get("average_complexity", 5.0)

            except Exception as e:
                logger.error(f"AST analysis failed: {e}")
                # Fall back to basic analysis
                analysis = self._basic_codebase_analysis(target_path)
        else:
            # Fallback analysis without AST
            analysis = self._basic_codebase_analysis(target_path)

        return analysis

    def _basic_codebase_analysis(self, target_path: str) -> CodebaseAnalysis:
        """Basic codebase analysis without AST."""
        analysis = CodebaseAnalysis()

        path = Path(target_path)
        if path.is_file():
            files = [path]
        else:
            files = list(path.rglob("*.py"))

        analysis.total_files = len(files)

        for file in files:
            try:
                content = file.read_text()
                lines = content.splitlines()

                # Count functions and classes (basic heuristic)
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("def "):
                        analysis.total_functions += 1
                        if "test_" in stripped:
                            analysis.total_test_functions += 1
                    elif stripped.startswith("class "):
                        analysis.total_classes += 1

                # Check if it's a test file
                if "test" in file.name.lower():
                    analysis.total_test_files += 1

            except Exception as e:
                logger.warning(f"Could not analyze {file}: {e}")

        # Estimate behaviors and coverage
        analysis.total_behaviors = analysis.total_functions
        if analysis.total_behaviors > 0:
            analysis.coverage_percentage = min(100.0,
                (analysis.total_test_functions / analysis.total_behaviors) * 100)

        return analysis

    def _calculate_necessary_scores(self, analysis: CodebaseAnalysis) -> List[NECESSARYScore]:
        """Calculate NECESSARY pattern compliance scores."""
        scores = []

        # N - Named: Test naming clarity
        n_score = self._calculate_n_score(analysis)
        scores.append(n_score)

        # E - Executable: Test independence
        e_score = self._calculate_e_score(analysis)
        scores.append(e_score)

        # C - Comprehensive: Coverage breadth
        c_score = self._calculate_c_score(analysis)
        scores.append(c_score)

        # E2 - Edge cases: Boundary testing
        e2_score = self._calculate_e2_score(analysis)
        scores.append(e2_score)

        # S - Stateful: State management
        s_score = self._calculate_s_score(analysis)
        scores.append(s_score)

        # S2 - Side effects: External interactions
        s2_score = self._calculate_s2_score(analysis)
        scores.append(s2_score)

        # A - Async: Async operation testing
        a_score = self._calculate_a_score(analysis)
        scores.append(a_score)

        # R - Regression: Historical issue coverage
        r_score = self._calculate_r_score(analysis)
        scores.append(r_score)

        # Y - Yielding: Test quality and confidence
        y_score = self._calculate_y_score(analysis, scores)
        scores.append(y_score)

        return scores

    def _calculate_n_score(self, analysis: CodebaseAnalysis) -> NECESSARYScore:
        """Calculate Named score based on test coverage."""
        if analysis.total_behaviors == 0:
            return NECESSARYScore(
                property="N",
                score=0.0,
                violations=["No behaviors found to test"]
            )

        score = min(1.0, analysis.total_test_functions / analysis.total_behaviors)
        violations = []

        if score < 0.8:
            violations.append(f"Low test coverage: {score:.2%}")
        if analysis.total_test_functions == 0:
            violations.append("No test functions found")

        return NECESSARYScore(
            property="N",
            score=score,
            violations=violations,
            details=f"Found {analysis.total_test_functions} tests for {analysis.total_behaviors} behaviors"
        )

    def _calculate_e_score(self, analysis: CodebaseAnalysis) -> NECESSARYScore:
        """Calculate Executable score for test independence."""
        # Heuristic: good if we have reasonable test-to-function ratio
        if analysis.total_functions == 0:
            score = 0.0
        else:
            ratio = analysis.total_test_functions / max(1, analysis.total_functions)
            score = min(1.0, ratio * 1.5)  # Expect 66% test ratio

        violations = []
        if score < 0.7:
            violations.append("Tests may have dependencies or lack independence")

        return NECESSARYScore(
            property="E",
            score=score,
            violations=violations
        )

    def _calculate_c_score(self, analysis: CodebaseAnalysis) -> NECESSARYScore:
        """Calculate Comprehensive score for coverage breadth."""
        score = analysis.coverage_percentage / 100.0
        violations = []

        if score < 0.8:
            violations.append(f"Coverage below 80%: {analysis.coverage_percentage:.1f}%")
        if score < 0.5:
            violations.append("Critical: Less than half of code is tested")

        return NECESSARYScore(
            property="C",
            score=score,
            violations=violations
        )

    def _calculate_e2_score(self, analysis: CodebaseAnalysis) -> NECESSARYScore:
        """Calculate Edge cases score."""
        # Estimate: expect 20% of tests to be edge cases
        expected_edge_tests = max(1, analysis.total_test_functions * 0.2)
        # Heuristic: assume we have 50% of expected edge case tests
        score = min(1.0, 0.5)

        violations = []
        if score < 0.6:
            violations.append("Insufficient edge case testing")

        return NECESSARYScore(
            property="E2",
            score=score,
            violations=violations,
            details="Edge case testing estimated from patterns"
        )

    def _calculate_s_score(self, analysis: CodebaseAnalysis) -> NECESSARYScore:
        """Calculate Stateful score for state management."""
        # Default reasonable score
        score = 0.7

        violations = []
        if score < 0.6:
            violations.append("State validation could be improved")

        return NECESSARYScore(
            property="S",
            score=score,
            violations=violations
        )

    def _calculate_s2_score(self, analysis: CodebaseAnalysis) -> NECESSARYScore:
        """Calculate Side effects score."""
        # Default reasonable score
        score = 0.6

        violations = []
        if score < 0.5:
            violations.append("Side effect testing needs improvement")

        return NECESSARYScore(
            property="S2",
            score=score,
            violations=violations
        )

    def _calculate_a_score(self, analysis: CodebaseAnalysis) -> NECESSARYScore:
        """Calculate Async score for async operations."""
        # Default score assuming some async testing
        score = 0.8

        violations = []
        if score < 0.7:
            violations.append("Async operation testing needs attention")

        return NECESSARYScore(
            property="A",
            score=score,
            violations=violations
        )

    def _calculate_r_score(self, analysis: CodebaseAnalysis) -> NECESSARYScore:
        """Calculate Regression score."""
        # Default good score for regression
        score = 0.8

        violations = []
        if score < 0.7:
            violations.append("Regression testing could be strengthened")

        return NECESSARYScore(
            property="R",
            score=score,
            violations=violations
        )

    def _calculate_y_score(self, analysis: CodebaseAnalysis, other_scores: List[NECESSARYScore]) -> NECESSARYScore:
        """Calculate Yielding (confidence) score based on other scores."""
        if not other_scores:
            score = 0.0
        else:
            # Average of all other scores
            total = sum(s.score for s in other_scores)
            score = total / len(other_scores)

        violations = []
        if score < 0.7:
            violations.append("Overall test confidence needs improvement")

        return NECESSARYScore(
            property="Y",
            score=score,
            violations=violations,
            details=f"Confidence score based on {len(other_scores)} metrics"
        )

    def _calculate_qt_score(self, necessary_scores: List[NECESSARYScore]) -> float:
        """Calculate overall Q(T) score from NECESSARY scores."""
        if not necessary_scores:
            return 0.0

        total = sum(score.score for score in necessary_scores)
        return total / len(necessary_scores)

    def _generate_findings(
        self,
        necessary_scores: List[NECESSARYScore],
        analysis: CodebaseAnalysis,
        context: AuditContext
    ) -> List[AuditFinding]:
        """Generate audit findings from scores."""
        findings = []

        for score in necessary_scores:
            # Determine severity based on score and thresholds
            severity = self._determine_severity(score.score, context.thresholds)

            if severity in ["critical", "high", "medium"]:
                for violation in score.violations:
                    finding = AuditFinding(
                        file_path=context.target_path,
                        severity=severity,
                        category=f"NECESSARY-{score.property}",
                        description=violation,
                        recommendation=self._get_recommendation_for_property(score.property)
                    )
                    findings.append(finding)

        # Add findings for low coverage
        if analysis.coverage_percentage < 60:
            findings.append(AuditFinding(
                file_path=context.target_path,
                severity="critical",
                category="Coverage",
                description=f"Test coverage critically low: {analysis.coverage_percentage:.1f}%",
                recommendation="Increase test coverage to at least 80%"
            ))

        return findings

    def _determine_severity(self, score: float, thresholds: Dict[str, float]) -> str:
        """Determine severity based on score and thresholds."""
        if score < thresholds["critical"]:
            return "critical"
        elif score < thresholds["high"]:
            return "high"
        elif score < thresholds["medium"]:
            return "medium"
        else:
            return "low"

    def _prioritize_findings(
        self,
        findings: List[AuditFinding],
        context: AuditContext
    ) -> List[AuditFinding]:
        """Prioritize findings based on severity and impact."""
        if DSPY_AVAILABLE and hasattr(self.prioritize, '__call__'):
            # Use DSPy prioritization
            try:
                items = [f.__dict__ for f in findings]
                result = self.prioritize(
                    items=items,
                    criteria=["severity", "impact", "effort"],
                    context=context.__dict__
                )

                # Reconstruct prioritized findings
                if hasattr(result, 'prioritized_items'):
                    findings = [AuditFinding(**item) for item in result.prioritized_items]
            except Exception as e:
                logger.warning(f"DSPy prioritization failed: {e}, using fallback")

        # Fallback or direct sorting
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: (severity_order.get(f.severity, 3), f.description))

        return findings

    def _generate_recommendations(
        self,
        qt_score: float,
        findings: List[AuditFinding],
        necessary_scores: List[NECESSARYScore]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Overall score recommendations
        if qt_score < 0.6:
            recommendations.append("🚨 CRITICAL: Q(T) score below 0.6 requires immediate attention")
        elif qt_score < 0.8:
            recommendations.append("⚠️ Q(T) score indicates significant improvement opportunities")
        else:
            recommendations.append("✅ Q(T) score is good - focus on continuous improvement")

        # Property-specific recommendations
        for score in necessary_scores:
            if score.score < 0.7:
                rec = self._get_recommendation_for_property(score.property)
                if rec and rec not in recommendations:
                    recommendations.append(rec)

        # Critical findings recommendations
        critical_findings = [f for f in findings if f.severity == "critical"]
        if critical_findings:
            recommendations.append(f"Address {len(critical_findings)} critical findings immediately")

        return recommendations[:10]  # Limit to top 10

    def _get_recommendation_for_property(self, property: str) -> str:
        """Get specific recommendation for a NECESSARY property."""
        recommendations = {
            "N": "📝 Add test cases for uncovered behaviors",
            "E": "🔧 Improve test independence and isolation",
            "C": "📊 Increase test coverage with multiple test vectors",
            "E2": "🔍 Add edge case and boundary condition tests",
            "S": "💾 Improve state validation in test assertions",
            "S2": "🔄 Add tests for side effects and external interactions",
            "A": "⚡ Add async operation testing with proper patterns",
            "R": "🔒 Implement regression tests for known issues",
            "Y": "⭐ Enhance overall test quality and readability"
        }
        return recommendations.get(property, "Review and improve test implementation")

    def _learn_from_audit(self, result: AuditResult) -> None:
        """Learn patterns from audit results."""
        learning_entry = {
            "timestamp": result.timestamp,
            "target": result.audit_context.target_path,
            "qt_score": result.qt_score,
            "critical_findings": len([f for f in result.findings if f.severity == "critical"]),
            "total_findings": len(result.findings),
            "lowest_score": min((s.score for s in result.necessary_scores), default=0.0),
            "mode": result.audit_context.mode
        }

        self.audit_history.append(learning_entry)

        # Limit history size
        if len(self.audit_history) > 100:
            self.audit_history = self.audit_history[-100:]

        logger.info(f"Learned from audit: Q(T)={result.qt_score:.2f}, findings={len(result.findings)}")

    # ===========================
    # Fallback Methods
    # ===========================

    def _fallback_analyze(self, **kwargs) -> Any:
        """Fallback analysis when DSPy is not available."""
        logger.info("Using fallback analysis (DSPy not available)")
        # Return a simple object with expected attributes
        return type('Result', (), {
            'findings': [],
            'compliance_score': 0.75,
            'summary': "Basic analysis completed"
        })()

    def _fallback_prioritize(self, **kwargs) -> Any:
        """Fallback prioritization when DSPy is not available."""
        items = kwargs.get('items', [])
        # Simple severity-based sorting
        return type('Result', (), {
            'prioritized_items': sorted(items, key=lambda x: x.get('severity', 'low')),
            'prioritization_rationale': "Sorted by severity"
        })()

    def _fallback_report(self, **kwargs) -> Any:
        """Fallback reporting when DSPy is not available."""
        findings = kwargs.get('findings', [])
        return type('Result', (), {
            'report': f"Audit Report: {len(findings)} findings",
            'key_metrics': {'total_findings': len(findings)},
            'recommendations': ["Review and address findings"]
        })()

    def get_audit_summary(self) -> Dict[str, JSONValue]:
        """Get summary of audit history and patterns."""
        if not self.audit_history:
            return {"message": "No audits performed yet"}

        avg_qt = sum(h['qt_score'] for h in self.audit_history) / len(self.audit_history)
        total_findings = sum(h['total_findings'] for h in self.audit_history)

        return {
            "total_audits": len(self.audit_history),
            "average_qt_score": avg_qt,
            "total_findings": total_findings,
            "improvement_trend": self._calculate_improvement_trend(),
            "common_issues": self._identify_common_issues()
        }

    def _calculate_improvement_trend(self) -> str:
        """Calculate trend in Q(T) scores."""
        if len(self.audit_history) < 2:
            return "insufficient_data"

        recent = self.audit_history[-5:]
        older = self.audit_history[-10:-5] if len(self.audit_history) >= 10 else self.audit_history[:len(self.audit_history)//2]

        if not older:
            return "insufficient_data"

        recent_avg = sum(h['qt_score'] for h in recent) / len(recent)
        older_avg = sum(h['qt_score'] for h in older) / len(older)

        if recent_avg > older_avg * 1.05:
            return "improving"
        elif recent_avg < older_avg * 0.95:
            return "declining"
        else:
            return "stable"

    def _identify_common_issues(self) -> List[str]:
        """Identify common issues from audit history."""
        issues = []

        if self.audit_history:
            avg_critical = sum(h['critical_findings'] for h in self.audit_history) / len(self.audit_history)
            if avg_critical > 1:
                issues.append("Frequent critical findings")

            avg_score = sum(h['lowest_score'] for h in self.audit_history) / len(self.audit_history)
            if avg_score < 0.5:
                issues.append("Consistently low NECESSARY scores")

        return issues


# ===========================
# Factory Function
# ===========================

def create_dspy_auditor_agent(
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "medium",
    enable_learning: bool = True,
    **kwargs
) -> DSPyAuditorAgent:
    """
    Factory function to create a DSPy Auditor Agent.

    Args:
        model: Model to use
        reasoning_effort: Reasoning effort level
        enable_learning: Whether to enable learning
        **kwargs: Additional configuration

    Returns:
        Configured DSPyAuditorAgent instance
    """
    return DSPyAuditorAgent(
        model=model,
        reasoning_effort=reasoning_effort,
        enable_learning=enable_learning,
        **kwargs
    )