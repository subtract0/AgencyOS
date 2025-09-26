"""
Intelligence Measurement Framework

Provides concrete, measurable benchmarks for AI intelligence amplification.
Implements the AIQ (AI Intelligence Quotient) and growth tracking systems.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from shared.types.json import JSONValue
from datetime import datetime, timedelta
import json
import math

logger = logging.getLogger(__name__)


class IntelligenceMetrics:
    """
    Concrete metrics for measuring AI intelligence amplification.

    Provides quantifiable, testable benchmarks for "smart" using TDD principles.
    """

    def __init__(self):
        """Initialize intelligence metrics tracker."""
        self.measurement_history: List[Dict[str, JSONValue]] = []
        self.baseline_metrics: Optional[Dict[str, float]] = None

    def calculate_aiq(
        self,
        pattern_effectiveness: float,
        application_success_rate: float,
        learning_velocity: float,
        context_accuracy: float = 1.0
    ) -> float:
        """
        Calculate AI Intelligence Quotient (AIQ).

        AIQ = (Pattern Effectiveness × Application Success × Learning Velocity × Context Accuracy) × 100

        Args:
            pattern_effectiveness: Average effectiveness of patterns (0.0-1.0)
            application_success_rate: Success rate of pattern applications (0.0-1.0)
            learning_velocity: Learning speed relative to baseline (0.0-2.0+)
            context_accuracy: Accuracy of context matching (0.0-1.0)

        Returns:
            AIQ score (0-100+)
        """
        try:
            # Validate inputs
            metrics = [pattern_effectiveness, application_success_rate, learning_velocity, context_accuracy]
            for metric in metrics:
                if not isinstance(metric, (int, float)) or metric < 0:
                    raise ValueError(f"Invalid metric value: {metric}")

            # Calculate composite intelligence score
            aiq = pattern_effectiveness * application_success_rate * learning_velocity * context_accuracy * 100

            logger.info(f"AIQ calculated: {aiq:.1f} (PE:{pattern_effectiveness:.2f}, "
                       f"AS:{application_success_rate:.2f}, LV:{learning_velocity:.2f}, "
                       f"CA:{context_accuracy:.2f})")

            return round(aiq, 1)

        except Exception as e:
            logger.error(f"AIQ calculation failed: {e}")
            return 0.0

    def measure_intelligence_growth_rate(
        self,
        current_aiq: float,
        previous_aiq: float
    ) -> float:
        """
        Calculate intelligence growth rate.

        Growth Rate = (Current AIQ - Previous AIQ) / Previous AIQ × 100%

        Args:
            current_aiq: Current AIQ measurement
            previous_aiq: Previous AIQ measurement

        Returns:
            Growth rate percentage
        """
        try:
            if previous_aiq <= 0:
                return 0.0

            growth_rate = ((current_aiq - previous_aiq) / previous_aiq) * 100
            return round(growth_rate, 1)

        except Exception as e:
            logger.error(f"Growth rate calculation failed: {e}")
            return 0.0

    def detect_exponential_amplification(
        self,
        aiq_history: List[float],
        min_periods: int = 4
    ) -> Dict[str, JSONValue]:
        """
        Detect exponential intelligence amplification patterns.

        Args:
            aiq_history: List of AIQ measurements over time
            min_periods: Minimum periods needed for detection

        Returns:
            Amplification analysis results
        """
        try:
            if len(aiq_history) < min_periods:
                return {
                    "exponential_detected": False,
                    "reason": f"Insufficient data points: {len(aiq_history)} < {min_periods}"
                }

            # Calculate growth rates
            growth_rates = []
            for i in range(1, len(aiq_history)):
                if aiq_history[i-1] > 0:
                    growth_rate = ((aiq_history[i] - aiq_history[i-1]) / aiq_history[i-1]) * 100
                    growth_rates.append(growth_rate)

            if len(growth_rates) < 3:
                return {"exponential_detected": False, "reason": "Insufficient growth rate data"}

            # Detect increasing growth rates (exponential pattern)
            increasing_periods = 0
            for i in range(1, len(growth_rates)):
                if growth_rates[i] > growth_rates[i-1]:
                    increasing_periods += 1

            exponential_ratio = increasing_periods / (len(growth_rates) - 1)

            # Calculate acceleration coefficient
            acceleration = sum(growth_rates[i] - growth_rates[i-1]
                             for i in range(1, len(growth_rates))) / (len(growth_rates) - 1)

            exponential_detected = exponential_ratio >= 0.6 and acceleration > 2.0

            return {
                "exponential_detected": exponential_detected,
                "exponential_ratio": exponential_ratio,
                "acceleration": acceleration,
                "growth_rates": growth_rates,
                "confidence": min(1.0, exponential_ratio * (acceleration / 10))
            }

        except Exception as e:
            logger.error(f"Exponential amplification detection failed: {e}")
            return {"exponential_detected": False, "error": str(e)}

    def benchmark_intelligence_capabilities(
        self,
        pattern_store,
        pattern_applicator,
        meta_learning_engine
    ) -> Dict[str, JSONValue]:
        """
        Run comprehensive intelligence benchmarks.

        Returns:
            Complete benchmark results with pass/fail status
        """
        benchmarks = {}

        try:
            # Benchmark 1: Pattern Quality
            store_stats = pattern_store.get_stats()
            pattern_effectiveness = store_stats.get("average_effectiveness", 0)
            benchmarks["pattern_effectiveness"] = {
                "value": pattern_effectiveness,
                "threshold": 0.70,
                "passed": pattern_effectiveness >= 0.70,
                "unit": "effectiveness_ratio"
            }

            # Benchmark 2: Application Success
            app_stats = pattern_applicator.get_application_stats()
            app_success_rate = app_stats.get("success_rate", 0)
            benchmarks["application_success_rate"] = {
                "value": app_success_rate,
                "threshold": 0.75,
                "passed": app_success_rate >= 0.75,
                "unit": "success_ratio"
            }

            # Benchmark 3: Learning Velocity
            learning_analysis = meta_learning_engine.analyze_learning_effectiveness()
            learning_velocity = learning_analysis.get("learning_trends", {}).get("learning_velocity", 0)
            # Normalize to 0-2 scale (1.0 = baseline)
            normalized_velocity = min(2.0, learning_velocity / 5.0) if learning_velocity > 0 else 0.0
            benchmarks["learning_velocity"] = {
                "value": normalized_velocity,
                "threshold": 0.8,
                "passed": normalized_velocity >= 0.8,
                "unit": "velocity_ratio"
            }

            # Benchmark 4: Context Accuracy (simulated based on domain coverage)
            unique_domains = store_stats.get("unique_domains", 0)
            max_expected_domains = 15  # Expected domain coverage
            context_accuracy = min(1.0, unique_domains / max_expected_domains)
            benchmarks["context_accuracy"] = {
                "value": context_accuracy,
                "threshold": 0.6,
                "passed": context_accuracy >= 0.6,
                "unit": "accuracy_ratio"
            }

            # Calculate overall AIQ
            aiq = self.calculate_aiq(
                pattern_effectiveness,
                app_success_rate,
                normalized_velocity,
                context_accuracy
            )

            benchmarks["overall_aiq"] = {
                "value": aiq,
                "threshold": 50.0,
                "passed": aiq >= 50.0,
                "unit": "aiq_score"
            }

            # Summary
            total_benchmarks = len(benchmarks)
            passed_benchmarks = sum(1 for b in benchmarks.values() if b["passed"])
            overall_pass_rate = passed_benchmarks / total_benchmarks

            benchmarks["summary"] = {
                "total_benchmarks": total_benchmarks,
                "passed_benchmarks": passed_benchmarks,
                "overall_pass_rate": overall_pass_rate,
                "intelligence_grade": self._calculate_intelligence_grade(overall_pass_rate),
                "timestamp": datetime.now().isoformat()
            }

            return benchmarks

        except Exception as e:
            logger.error(f"Intelligence benchmarking failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def record_measurement(
        self,
        aiq: float,
        component_metrics: Dict[str, float],
        context: Dict[str, JSONValue] = None
    ) -> None:
        """Record intelligence measurement for historical tracking."""
        measurement = {
            "timestamp": datetime.now().isoformat(),
            "aiq": aiq,
            "metrics": component_metrics,
            "context": context or {}
        }

        self.measurement_history.append(measurement)

        # Keep only last 100 measurements
        if len(self.measurement_history) > 100:
            self.measurement_history = self.measurement_history[-100:]

        # Update baseline if this is first measurement
        if self.baseline_metrics is None:
            self.baseline_metrics = component_metrics.copy()

    def get_intelligence_trajectory(self) -> Dict[str, JSONValue]:
        """Get intelligence development trajectory over time."""
        try:
            if len(self.measurement_history) < 2:
                return {"trajectory": "insufficient_data", "measurements": len(self.measurement_history)}

            # Extract AIQ history
            aiq_history = [m["aiq"] for m in self.measurement_history]

            # Calculate overall trend
            if len(aiq_history) >= 2:
                initial_aiq = aiq_history[0]
                current_aiq = aiq_history[-1]
                overall_growth = self.measure_intelligence_growth_rate(current_aiq, initial_aiq)
            else:
                overall_growth = 0.0

            # Detect exponential amplification
            amplification_analysis = self.detect_exponential_amplification(aiq_history)

            # Calculate velocity (AIQ change per measurement)
            if len(aiq_history) >= 2:
                recent_measurements = aiq_history[-5:]  # Last 5 measurements
                if len(recent_measurements) >= 2:
                    velocity = (recent_measurements[-1] - recent_measurements[0]) / (len(recent_measurements) - 1)
                else:
                    velocity = 0.0
            else:
                velocity = 0.0

            return {
                "trajectory": "improving" if overall_growth > 0 else "stable" if overall_growth == 0 else "declining",
                "overall_growth_rate": overall_growth,
                "current_aiq": aiq_history[-1],
                "baseline_aiq": aiq_history[0],
                "measurement_count": len(aiq_history),
                "recent_velocity": velocity,
                "exponential_amplification": amplification_analysis,
                "intelligence_status": self._assess_intelligence_status(aiq_history[-1], overall_growth)
            }

        except Exception as e:
            logger.error(f"Trajectory analysis failed: {e}")
            return {"error": str(e)}

    def _calculate_intelligence_grade(self, pass_rate: float) -> str:
        """Calculate intelligence grade based on benchmark pass rate."""
        if pass_rate >= 0.9:
            return "A+ (Exceptional)"
        elif pass_rate >= 0.8:
            return "A (Excellent)"
        elif pass_rate >= 0.7:
            return "B (Good)"
        elif pass_rate >= 0.6:
            return "C (Satisfactory)"
        elif pass_rate >= 0.5:
            return "D (Minimal)"
        else:
            return "F (Insufficient)"

    def _assess_intelligence_status(self, current_aiq: float, growth_rate: float) -> str:
        """Assess overall intelligence status."""
        if current_aiq >= 80 and growth_rate >= 20:
            return "Superintelligent Growth"
        elif current_aiq >= 70 and growth_rate >= 15:
            return "Rapid Intelligence Amplification"
        elif current_aiq >= 60 and growth_rate >= 10:
            return "Steady Intelligence Development"
        elif current_aiq >= 50 and growth_rate >= 5:
            return "Basic Intelligence Learning"
        elif current_aiq >= 40:
            return "Functional Intelligence"
        else:
            return "Developing Intelligence"

    def export_intelligence_report(self) -> str:
        """Export comprehensive intelligence analysis report."""
        try:
            if not self.measurement_history:
                return json.dumps({"error": "No measurements recorded"}, indent=2)

            trajectory = self.get_intelligence_trajectory()
            latest_measurement = self.measurement_history[-1]

            report = {
                "intelligence_report": {
                    "generated_timestamp": datetime.now().isoformat(),
                    "measurement_period": {
                        "start": self.measurement_history[0]["timestamp"],
                        "end": self.measurement_history[-1]["timestamp"],
                        "total_measurements": len(self.measurement_history)
                    },
                    "current_intelligence": {
                        "aiq": latest_measurement["aiq"],
                        "status": trajectory.get("intelligence_status", "Unknown"),
                        "grade": self._calculate_intelligence_grade(
                            latest_measurement["aiq"] / 100
                        )
                    },
                    "growth_analysis": {
                        "overall_growth_rate": trajectory.get("overall_growth_rate", 0),
                        "trajectory": trajectory.get("trajectory", "unknown"),
                        "recent_velocity": trajectory.get("recent_velocity", 0),
                        "exponential_amplification": trajectory.get("exponential_amplification", {})
                    },
                    "benchmark_history": [
                        {
                            "timestamp": m["timestamp"],
                            "aiq": m["aiq"],
                            "metrics": m["metrics"]
                        }
                        for m in self.measurement_history[-10:]  # Last 10 measurements
                    ],
                    "intelligence_classification": self._classify_intelligence_level(latest_measurement["aiq"]),
                    "recommendations": self._generate_intelligence_recommendations(trajectory)
                }
            }

            return json.dumps(report, indent=2)

        except Exception as e:
            logger.error(f"Intelligence report export failed: {e}")
            return json.dumps({"error": str(e)}, indent=2)

    def _classify_intelligence_level(self, aiq: float) -> Dict[str, JSONValue]:
        """Classify intelligence level based on AIQ score."""
        if aiq >= 100:
            return {
                "level": "Superintelligent",
                "description": "Exceeds human-level performance across all domains",
                "capabilities": ["Self-improvement", "Novel pattern creation", "Meta-learning mastery"]
            }
        elif aiq >= 80:
            return {
                "level": "Highly Intelligent",
                "description": "Advanced pattern recognition and application",
                "capabilities": ["Complex problem solving", "Pattern synthesis", "Rapid learning"]
            }
        elif aiq >= 60:
            return {
                "level": "Intelligent",
                "description": "Good pattern matching and moderate learning ability",
                "capabilities": ["Pattern recognition", "Context understanding", "Basic learning"]
            }
        elif aiq >= 40:
            return {
                "level": "Functional",
                "description": "Basic pattern storage and retrieval",
                "capabilities": ["Simple pattern matching", "Limited context awareness"]
            }
        else:
            return {
                "level": "Developing",
                "description": "Early stage intelligence development",
                "capabilities": ["Basic pattern storage", "Simple operations"]
            }

    def _generate_intelligence_recommendations(self, trajectory: Dict[str, JSONValue]) -> List[str]:
        """Generate recommendations for intelligence improvement."""
        recommendations = []

        current_aiq = trajectory.get("current_aiq", 0)
        growth_rate = trajectory.get("overall_growth_rate", 0)
        exponential = trajectory.get("exponential_amplification", {})

        if current_aiq < 50:
            recommendations.append("Focus on pattern quality improvement and extraction efficiency")

        if growth_rate < 5:
            recommendations.append("Enhance learning velocity through meta-learning optimization")

        if not exponential.get("exponential_detected", False):
            recommendations.append("Implement recursive self-improvement mechanisms")

        if current_aiq >= 80:
            recommendations.append("Consider expanding to new domains and pattern synthesis")

        return recommendations or ["Continue current intelligence development trajectory"]