"""
Adapter layer for bridging legacy and DSPy audit systems.

Provides seamless transition and fallback mechanisms.
"""

import traceback
from typing import Any
from .type_definitions import AuditResultDict

from .config import get_config, get_flags, should_use_dspy
from .modules import AuditRefactorModule
from .optimize import load_optimized_module


class AuditAdapter:
    """
    Adapter for seamlessly switching between legacy and DSPy audit systems.
    """

    def __init__(self):
        """Initialize the adapter with both systems."""
        self.config = get_config()
        self.flags = get_flags()

        # Load DSPy module if enabled
        self.dspy_module = None
        if self.flags["use_dspy_audit"]:
            self._initialize_dspy()

        # Initialize legacy auditor
        self.legacy_auditor = None
        self._initialize_legacy()

    def _initialize_dspy(self) -> None:
        """Initialize DSPy audit module."""
        try:
            # Try to load optimized module first
            self.dspy_module = load_optimized_module()

            if self.dspy_module is None:
                # Create new module if no saved version
                self.dspy_module = AuditRefactorModule(
                    use_learning=self.flags["enable_vectorstore_learning"],
                    parallel_execution=self.flags["parallel_audit_execution"],
                )
                print("Created new DSPy audit module")
            else:
                print("Loaded optimized DSPy audit module")

        except Exception as e:
            print(f"Failed to initialize DSPy module: {e}")
            self.dspy_module = None

    def _initialize_legacy(self) -> None:
        """Initialize legacy auditor agent."""
        try:
            from auditor_agent.auditor_agent import create_auditor_agent

            self.legacy_auditor = create_auditor_agent()
            print("Initialized legacy auditor")
        except Exception as e:
            print(f"Failed to initialize legacy auditor: {e}")
            self.legacy_auditor = None

    def run_audit(
        self,
        code_path: str,
        max_fixes: int = 3,
        force_legacy: bool = False,
        force_dspy: bool = False,
    ) -> AuditResultDict:
        """
        Run audit using appropriate system.

        Args:
            code_path: Path to code to audit
            max_fixes: Maximum fixes to attempt
            force_legacy: Force use of legacy system
            force_dspy: Force use of DSPy system

        Returns:
            Audit results in standardized format
        """
        # Determine which system to use
        use_dspy = self._should_use_dspy(force_legacy, force_dspy)

        if use_dspy and self.dspy_module:
            return self._run_dspy_audit(code_path, max_fixes)
        elif self.legacy_auditor:
            return self._run_legacy_audit(code_path, max_fixes)
        else:
            return {
                "error": "No audit system available",
                "dspy_available": self.dspy_module is not None,
                "legacy_available": self.legacy_auditor is not None,
            }

    def _should_use_dspy(self, force_legacy: bool, force_dspy: bool) -> bool:
        """Determine which system to use."""
        if force_legacy:
            return False
        if force_dspy:
            return True
        return should_use_dspy()

    def _run_dspy_audit(self, code_path: str, max_fixes: int) -> dict[str, Any]:
        """Run audit using DSPy system."""
        try:
            print(f"Running DSPy audit on {code_path}")

            # Run DSPy module
            result = self.dspy_module.forward(
                code_path=code_path,
                max_fixes=max_fixes,
                available_time=self.config["prioritization"]["max_time_per_fix"]
                * max_fixes,
                auto_rollback=self.flags["auto_rollback_on_failure"],
            )

            # Convert to standardized format
            return self._dspy_to_standard_format(result)

        except Exception as e:
            print(f"DSPy audit failed: {e}")
            if self.flags["debug_mode"]:
                traceback.print_exc()

            # Fallback to legacy if available
            if self.legacy_auditor and not self.flags["block_on_violation"]:
                print("Falling back to legacy auditor")
                return self._run_legacy_audit(code_path, max_fixes)

            return {"error": str(e), "system": "dspy"}

    def _run_legacy_audit(self, code_path: str, max_fixes: int) -> dict[str, Any]:
        """Run audit using legacy system."""
        try:
            print(f"Running legacy audit on {code_path}")

            # Run legacy auditor
            from auditor_agent.ast_analyzer import ASTAnalyzer

            analyzer = ASTAnalyzer()
            analysis = analyzer.analyze_directory(code_path)

            # Calculate NECESSARY scores
            necessary_scores = self._calculate_necessary_scores(analysis)

            # Generate report
            return {
                "system": "legacy",
                "target": code_path,
                "qt_score": self._calculate_qt_score(necessary_scores),
                "necessary_scores": necessary_scores,
                "issues": self._extract_issues_from_analysis(analysis),
                "recommendations": self._generate_recommendations(analysis),
                "max_fixes": max_fixes,
            }

        except Exception as e:
            print(f"Legacy audit failed: {e}")
            return {"error": str(e), "system": "legacy"}

    def _dspy_to_standard_format(self, dspy_result: dict) -> dict[str, Any]:
        """Convert DSPy result to standard format."""
        standard_result = {
            "system": "dspy",
            "target": dspy_result.get("audit", {}).get("code_path", ""),
        }

        # Extract audit information
        if "audit" in dspy_result:
            audit = dspy_result["audit"]

            # Handle different attribute access methods
            if hasattr(audit, "qt_score"):
                standard_result["qt_score"] = audit.qt_score
                standard_result["necessary_scores"] = audit.necessary_scores
                standard_result["issues"] = self._convert_issues(audit.issues)
                standard_result["recommendations"] = audit.recommendations
            else:
                standard_result["qt_score"] = audit.get("qt_score", 0.5)
                standard_result["necessary_scores"] = audit.get("necessary_scores", {})
                standard_result["issues"] = audit.get("issues", [])
                standard_result["recommendations"] = audit.get("recommendations", [])

        # Extract fix information
        if "applied_fixes" in dspy_result:
            standard_result["applied_fixes"] = len(dspy_result["applied_fixes"])
            standard_result["fixes"] = dspy_result["applied_fixes"]

        if "failed_fixes" in dspy_result:
            standard_result["failed_fixes"] = len(dspy_result["failed_fixes"])

        # Extract verification
        if "verification" in dspy_result:
            verification = dspy_result["verification"]
            if hasattr(verification, "success"):
                standard_result["verification_success"] = verification.success
                standard_result["final_qt_score"] = verification.final_qt_score
            else:
                standard_result["verification_success"] = verification.get(
                    "success", False
                )
                standard_result["final_qt_score"] = verification.get(
                    "final_qt_score", 0.5
                )

        # Extract learning
        if "learning" in dspy_result and dspy_result["learning"]:
            standard_result["patterns_learned"] = len(
                getattr(dspy_result["learning"], "success_patterns", [])
            )

        return standard_result

    def _convert_issues(self, issues: list) -> list[dict]:
        """Convert Issue objects to dictionaries."""
        converted = []
        for issue in issues:
            if hasattr(issue, "file_path"):
                converted.append(
                    {
                        "file": issue.file_path,
                        "line": issue.line_number,
                        "severity": issue.severity.value,
                        "category": issue.category,
                        "description": issue.description,
                        "suggested_fix": issue.suggested_fix,
                    }
                )
            else:
                converted.append(issue)
        return converted

    def _calculate_necessary_scores(self, analysis: dict) -> dict[str, float]:
        """Calculate NECESSARY scores from analysis."""
        total_behaviors = analysis.get("total_behaviors", 0)
        total_tests = analysis.get("total_test_functions", 0)

        if total_behaviors == 0:
            return dict.fromkeys("NECESSARY", 0.0)

        coverage = min(1.0, total_tests / total_behaviors)

        return {
            "N": coverage,
            "E": 0.5,  # Estimated
            "C": min(1.0, (total_tests / max(1, total_behaviors)) / 2),
            "E2": 0.6,  # Estimated
            "S1": 0.7,  # Estimated
            "S2": 0.7,  # Estimated
            "A": 0.3,  # Estimated
            "R": 0.8,  # Estimated
            "Y": 0.5,  # Estimated
        }

    def _calculate_qt_score(self, necessary_scores: dict[str, float]) -> float:
        """Calculate Q(T) score from NECESSARY scores."""
        return sum(necessary_scores.values()) / len(necessary_scores)

    def _extract_issues_from_analysis(self, analysis: dict) -> list[dict]:
        """Extract issues from analysis."""
        issues = []

        # Check for missing tests
        if analysis.get("total_test_functions", 0) == 0:
            issues.append(
                {
                    "file": analysis.get("target", ""),
                    "line": 0,
                    "severity": "constitutional",
                    "category": "missing_tests",
                    "description": "No test coverage found",
                    "constitutional_article": 2,
                }
            )

        # Check for complexity violations
        for func in analysis.get("functions", []):
            if func.get("complexity", 0) > 10:
                issues.append(
                    {
                        "file": func.get("file", ""),
                        "line": func.get("line", 0),
                        "severity": "complexity",
                        "category": "high_complexity",
                        "description": f"Function complexity {func.get('complexity')} exceeds threshold",
                    }
                )

        return issues

    def _generate_recommendations(self, analysis: dict) -> list[str]:
        """Generate recommendations from analysis."""
        recommendations = []

        if analysis.get("total_test_functions", 0) == 0:
            recommendations.append("Add comprehensive test coverage")

        if analysis.get("total_behaviors", 0) > analysis.get("total_test_functions", 0):
            recommendations.append("Increase test coverage for all behaviors")

        return recommendations

    def compare_systems(self, code_path: str) -> dict[str, Any]:
        """
        Run both systems and compare results.

        Useful for A/B testing and validation.

        Args:
            code_path: Path to audit

        Returns:
            Comparison results
        """
        results = {}

        # Run legacy
        results["legacy"] = self._run_legacy_audit(code_path, max_fixes=3)

        # Run DSPy
        if self.dspy_module:
            results["dspy"] = self._run_dspy_audit(code_path, max_fixes=3)

        # Calculate differences
        if "legacy" in results and "dspy" in results:
            results["comparison"] = {
                "qt_score_delta": (
                    results["dspy"].get("qt_score", 0)
                    - results["legacy"].get("qt_score", 0)
                ),
                "issues_delta": (
                    len(results["dspy"].get("issues", []))
                    - len(results["legacy"].get("issues", []))
                ),
                "dspy_found_unique": [
                    i
                    for i in results["dspy"].get("issues", [])
                    if i not in results["legacy"].get("issues", [])
                ],
                "legacy_found_unique": [
                    i
                    for i in results["legacy"].get("issues", [])
                    if i not in results["dspy"].get("issues", [])
                ],
            }

        return results
