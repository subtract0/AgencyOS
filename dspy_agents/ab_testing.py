"""
A/B Testing Framework for DSPy Migration

Enables gradual rollout and performance comparison between
DSPy and legacy agent implementations.
"""

import hashlib
import json
import logging
import os
import random
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from shared.type_definitions.json import JSONValue

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Status of an A/B test experiment."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AgentVariant(Enum):
    """Agent implementation variant."""

    LEGACY = "legacy"
    DSPY = "dspy"
    CONTROL = "control"  # Usually legacy
    TREATMENT = "treatment"  # Usually DSPy


class ExperimentConfig(BaseModel):
    """Configuration for an A/B test experiment."""

    name: str = Field(..., description="Experiment name")
    agent_name: str = Field(..., description="Agent being tested")
    rollout_percentage: float = Field(0.1, description="Percentage of traffic for DSPy (0.0-1.0)")
    start_date: datetime | None = Field(None, description="Experiment start date")
    end_date: datetime | None = Field(None, description="Experiment end date")
    min_samples: int = Field(100, description="Minimum samples needed per variant")
    confidence_level: float = Field(0.95, description="Statistical confidence level")
    metrics_to_track: list[str] = Field(
        default_factory=lambda: ["success_rate", "latency", "quality_score"],
        description="Metrics to track",
    )
    enabled: bool = Field(True, description="Whether experiment is enabled")
    force_variant: str | None = Field(None, description="Force a specific variant for testing")


class ExperimentResult(BaseModel):
    """Results from an A/B test experiment."""

    experiment_name: str
    agent_name: str
    control_samples: int
    treatment_samples: int
    control_metrics: dict[str, float]
    treatment_metrics: dict[str, float]
    improvement: dict[str, float]
    statistical_significance: dict[str, bool]
    recommendation: str
    confidence: float


class ABTestController:
    """
    Controls A/B testing for agent implementations.

    Manages traffic splitting, metric collection, and statistical analysis
    for comparing DSPy and legacy agent implementations.
    """

    def __init__(self, config_path: str | None = None, metrics_path: str | None = None):
        """
        Initialize the A/B test controller.

        Args:
            config_path: Path to experiments configuration file
            metrics_path: Path to store metrics data
        """
        self.config_path = Path(config_path or "experiments/ab_tests.json")
        self.metrics_path = Path(metrics_path or "logs/ab_testing/metrics.jsonl")

        # Ensure directories exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)

        self.experiments: dict[str, ExperimentConfig] = {}
        self.metrics: list[dict[str, JSONValue]] = []

        self._load_experiments()

    def _load_experiments(self) -> None:
        """Load experiment configurations from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    for exp_data in data.get("experiments", []):
                        config = ExperimentConfig(**exp_data)
                        self.experiments[config.name] = config
                logger.info(f"Loaded {len(self.experiments)} experiments")
            except Exception as e:
                logger.error(f"Failed to load experiments: {e}")

    def _save_experiments(self) -> None:
        """Save experiment configurations to file."""
        try:
            data = {
                "experiments": [config.model_dump() for config in self.experiments.values()],
                "last_updated": datetime.utcnow().isoformat(),
            }
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save experiments: {e}")

    def should_use_dspy(
        self, agent_name: str, user_id: str | None = None, session_id: str | None = None
    ) -> tuple[bool, str]:
        """
        Determine whether to use DSPy variant for a request.

        Args:
            agent_name: Name of the agent
            user_id: Optional user identifier for consistent assignment
            session_id: Optional session identifier

        Returns:
            Tuple of (use_dspy, experiment_name)
        """
        # Check for environment override
        env_key = f"FORCE_DSPY_{agent_name.upper()}"
        if os.getenv(env_key):
            logger.info(f"Forcing DSPy for {agent_name} due to {env_key}")
            return True, "forced_env"

        # Find active experiment for this agent
        active_experiment = None
        for exp_name, config in self.experiments.items():
            if (
                config.agent_name == agent_name
                and config.enabled
                and self._is_experiment_active(config)
            ):
                active_experiment = config
                break

        if not active_experiment:
            # No active experiment, use default behavior
            return False, "no_experiment"

        # Check for forced variant in config
        if active_experiment.force_variant:
            use_dspy = active_experiment.force_variant.lower() in ["dspy", "treatment"]
            return use_dspy, active_experiment.name

        # Deterministic assignment based on user/session
        if user_id or session_id:
            identifier = user_id or session_id
            hash_value = int(hashlib.md5(identifier.encode()).hexdigest(), 16)
            assignment = (hash_value % 100) / 100.0
        else:
            # Random assignment
            assignment = random.random()

        use_dspy = assignment < active_experiment.rollout_percentage

        # Log the decision
        self._log_assignment(
            experiment_name=active_experiment.name,
            agent_name=agent_name,
            variant="dspy" if use_dspy else "legacy",
            user_id=user_id,
            session_id=session_id,
        )

        return use_dspy, active_experiment.name

    def _is_experiment_active(self, config: ExperimentConfig) -> bool:
        """Check if an experiment is currently active."""
        now = datetime.utcnow()

        if config.start_date and now < config.start_date:
            return False

        if config.end_date and now > config.end_date:
            return False

        return True

    def _log_assignment(
        self,
        experiment_name: str,
        agent_name: str,
        variant: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Log variant assignment for analysis."""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "experiment": experiment_name,
                "agent": agent_name,
                "variant": variant,
                "user_id": user_id,
                "session_id": session_id,
            }

            with open(self.metrics_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"Failed to log assignment: {e}")

    def record_metric(
        self,
        experiment_name: str,
        variant: str,
        metric_name: str,
        value: float,
        metadata: dict[str, JSONValue] | None = None,
    ) -> None:
        """
        Record a metric for an experiment.

        Args:
            experiment_name: Name of the experiment
            variant: Which variant was used
            metric_name: Name of the metric
            value: Metric value
            metadata: Optional additional metadata
        """
        try:
            metric_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "experiment": experiment_name,
                "variant": variant,
                "metric": metric_name,
                "value": value,
                "metadata": metadata or {},
            }

            with open(self.metrics_path, "a") as f:
                f.write(json.dumps(metric_entry) + "\n")

            self.metrics.append(metric_entry)

        except Exception as e:
            logger.error(f"Failed to record metric: {e}")

    def create_experiment(
        self,
        name: str,
        agent_name: str,
        rollout_percentage: float = 0.1,
        duration_days: int = 7,
        **kwargs,
    ) -> ExperimentConfig:
        """
        Create a new A/B test experiment.

        Args:
            name: Experiment name
            agent_name: Agent to test
            rollout_percentage: Percentage for DSPy variant
            duration_days: How long to run the experiment
            **kwargs: Additional configuration

        Returns:
            Created experiment configuration
        """
        config = ExperimentConfig(
            name=name,
            agent_name=agent_name,
            rollout_percentage=rollout_percentage,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration_days),
            **kwargs,
        )

        self.experiments[name] = config
        self._save_experiments()

        logger.info(f"Created experiment: {name} for agent: {agent_name}")
        return config

    def pause_experiment(self, name: str) -> None:
        """Pause an experiment."""
        if name in self.experiments:
            self.experiments[name].enabled = False
            self._save_experiments()
            logger.info(f"Paused experiment: {name}")

    def resume_experiment(self, name: str) -> None:
        """Resume a paused experiment."""
        if name in self.experiments:
            self.experiments[name].enabled = True
            self._save_experiments()
            logger.info(f"Resumed experiment: {name}")

    def analyze_experiment(self, name: str) -> ExperimentResult | None:
        """
        Analyze results from an experiment.

        Args:
            name: Experiment name

        Returns:
            Analysis results or None if insufficient data
        """
        if name not in self.experiments:
            logger.error(f"Experiment not found: {name}")
            return None

        config = self.experiments[name]

        # Load metrics for this experiment
        experiment_metrics = self._load_experiment_metrics(name)

        if not experiment_metrics:
            logger.warning(f"No metrics found for experiment: {name}")
            return None

        # Separate by variant
        control_metrics = [m for m in experiment_metrics if m["variant"] == "legacy"]
        treatment_metrics = [m for m in experiment_metrics if m["variant"] == "dspy"]

        # Check minimum samples
        if len(control_metrics) < config.min_samples or len(treatment_metrics) < config.min_samples:
            logger.warning(f"Insufficient samples for experiment: {name}")
            return None

        # Calculate aggregated metrics
        control_agg = self._aggregate_metrics(control_metrics)
        treatment_agg = self._aggregate_metrics(treatment_metrics)

        # Calculate improvement
        improvement = {}
        for metric in control_agg:
            if metric in treatment_agg and control_agg[metric] > 0:
                improvement[metric] = (
                    (treatment_agg[metric] - control_agg[metric]) / control_agg[metric]
                ) * 100

        # Statistical significance (simplified)
        significance = self._calculate_significance(control_metrics, treatment_metrics)

        # Generate recommendation
        recommendation = self._generate_recommendation(improvement, significance)

        return ExperimentResult(
            experiment_name=name,
            agent_name=config.agent_name,
            control_samples=len(control_metrics),
            treatment_samples=len(treatment_metrics),
            control_metrics=control_agg,
            treatment_metrics=treatment_agg,
            improvement=improvement,
            statistical_significance=significance,
            recommendation=recommendation,
            confidence=config.confidence_level,
        )

    def _load_experiment_metrics(self, experiment_name: str) -> list[dict[str, JSONValue]]:
        """Load metrics for a specific experiment."""
        metrics = []

        if self.metrics_path.exists():
            try:
                with open(self.metrics_path) as f:
                    for line in f:
                        entry = json.loads(line)
                        if entry.get("experiment") == experiment_name:
                            metrics.append(entry)
            except Exception as e:
                logger.error(f"Failed to load metrics: {e}")

        return metrics

    def _aggregate_metrics(self, metrics: list[dict[str, JSONValue]]) -> dict[str, float]:
        """Aggregate metrics by type."""
        aggregated = {}
        metric_values: dict[str, list[float]] = {}

        for entry in metrics:
            if "metric" in entry and "value" in entry:
                metric_name = entry["metric"]
                if metric_name not in metric_values:
                    metric_values[metric_name] = []
                metric_values[metric_name].append(entry["value"])

        # Calculate averages
        for metric_name, values in metric_values.items():
            if values:
                aggregated[metric_name] = sum(values) / len(values)

        return aggregated

    def _calculate_significance(
        self, control: list[dict[str, JSONValue]], treatment: list[dict[str, JSONValue]]
    ) -> dict[str, bool]:
        """
        Calculate statistical significance (simplified).

        In production, use proper statistical tests like t-test or chi-square.
        """
        significance = {}

        # Group by metric type
        control_by_metric = {}
        treatment_by_metric = {}

        for entry in control:
            if "metric" in entry:
                metric = entry["metric"]
                if metric not in control_by_metric:
                    control_by_metric[metric] = []
                control_by_metric[metric].append(entry.get("value", 0))

        for entry in treatment:
            if "metric" in entry:
                metric = entry["metric"]
                if metric not in treatment_by_metric:
                    treatment_by_metric[metric] = []
                treatment_by_metric[metric].append(entry.get("value", 0))

        # Simple significance check (in production, use scipy.stats)
        for metric in set(control_by_metric.keys()) | set(treatment_by_metric.keys()):
            c_values = control_by_metric.get(metric, [0])
            t_values = treatment_by_metric.get(metric, [0])

            # For small samples (< 30), use more lenient significance check
            if len(c_values) >= 3 and len(t_values) >= 3:
                # Simplified: check if means are >5% different
                c_mean = sum(c_values) / len(c_values)
                t_mean = sum(t_values) / len(t_values)

                if c_mean > 0:
                    diff = abs(t_mean - c_mean) / c_mean
                    # More lenient threshold for small samples
                    threshold = 0.05 if len(c_values) >= 30 else 0.15
                    significance[metric] = diff > threshold
                else:
                    significance[metric] = t_mean > 0
            else:
                significance[metric] = False

        return significance

    def _generate_recommendation(
        self, improvement: dict[str, float], significance: dict[str, bool]
    ) -> str:
        """Generate recommendation based on results."""
        # Check for significant positive improvements
        significant_improvements = 0
        significant_regressions = 0

        for metric, imp in improvement.items():
            if significance.get(metric, False):
                if imp > 5:  # >5% improvement
                    significant_improvements += 1
                elif imp < -5:  # >5% regression
                    significant_regressions += 1

        if significant_regressions > 0:
            return "ROLLBACK: DSPy variant shows significant regressions"
        elif significant_improvements >= 2:
            return "ROLLOUT: DSPy variant shows significant improvements"
        elif significant_improvements == 1:
            return "EXPAND: Increase rollout percentage to gather more data"
        else:
            return "CONTINUE: Continue monitoring, no clear winner yet"

    def get_experiment_status(self, name: str) -> dict[str, JSONValue] | None:
        """Get current status of an experiment."""
        if name not in self.experiments:
            return None

        config = self.experiments[name]
        metrics = self._load_experiment_metrics(name)

        control_count = sum(1 for m in metrics if m.get("variant") == "legacy")
        treatment_count = sum(1 for m in metrics if m.get("variant") == "dspy")

        return {
            "name": name,
            "agent": config.agent_name,
            "status": "active" if self._is_experiment_active(config) else "inactive",
            "rollout_percentage": config.rollout_percentage,
            "control_samples": control_count,
            "treatment_samples": treatment_count,
            "progress": min((control_count + treatment_count) / (config.min_samples * 2), 1.0)
            * 100,
        }

    def list_experiments(self) -> list[dict[str, JSONValue]]:
        """List all experiments with their status."""
        experiments = []

        for name in self.experiments:
            status = self.get_experiment_status(name)
            if status:
                experiments.append(status)

        return experiments


# Global controller instance
_global_controller: ABTestController | None = None


def get_ab_controller() -> ABTestController:
    """Get the global A/B test controller instance."""
    global _global_controller
    if _global_controller is None:
        _global_controller = ABTestController()
    return _global_controller
