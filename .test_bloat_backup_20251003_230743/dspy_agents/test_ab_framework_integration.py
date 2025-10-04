"""
Integration tests for A/B testing framework with DSPy agents.

Tests the A/B testing controller with multiple agent variants.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dspy_agents.ab_testing import (
    ABTestController,
    get_ab_controller,
)
from dspy_agents.modules.code_agent import DSPyCodeAgent
from dspy_agents.registry import AgentRegistry, get_global_registry


class TestABFrameworkIntegration:
    """Test A/B testing framework with real agents."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def controller(self, temp_dir):
        """Create test controller with temp paths."""
        config_path = temp_dir / "ab_tests.json"
        metrics_path = temp_dir / "metrics.jsonl"
        return ABTestController(config_path=str(config_path), metrics_path=str(metrics_path))

    @pytest.fixture
    def registry(self):
        """Get initialized agent registry."""
        registry = AgentRegistry()
        registry.initialize()
        return registry

    def test_registry_has_both_dspy_and_legacy_agents(self, registry):
        """Test that registry contains both agent types."""
        agents = registry.list_agents()

        # Check we have both DSPy and legacy agents
        dspy_agents = [a for a in agents if a["type"] == "dspy"]
        legacy_agents = [a for a in agents if a["type"] == "legacy"]

        assert len(dspy_agents) >= 2  # Code, Auditor, Planner, Learning
        assert (
            len(legacy_agents) >= 4
        )  # Remaining legacy agents (chief_architect, merger, test_generator, work_completion)

        # Verify specific agents
        agent_names = [a["name"] for a in agents]
        assert "code" in agent_names
        assert "auditor" in agent_names

    def test_create_experiment_for_code_agent(self, controller):
        """Test creating an A/B experiment for CodeAgent."""
        experiment = controller.create_experiment(
            name="code_agent_dspy_migration",
            agent_name="code",
            rollout_percentage=0.2,
            duration_days=7,
        )

        assert experiment.name == "code_agent_dspy_migration"
        assert experiment.agent_name == "code"
        assert experiment.rollout_percentage == 0.2
        assert experiment.enabled is True

    def test_create_experiment_for_auditor_agent(self, controller):
        """Test creating an A/B experiment for AuditorAgent."""
        experiment = controller.create_experiment(
            name="auditor_agent_dspy_migration",
            agent_name="auditor",
            rollout_percentage=0.15,
            duration_days=5,
            min_samples=50,
        )

        assert experiment.name == "auditor_agent_dspy_migration"
        assert experiment.agent_name == "auditor"
        assert experiment.rollout_percentage == 0.15
        assert experiment.min_samples == 50

    def test_traffic_splitting_logic(self, controller):
        """Test that traffic splitting works correctly."""
        # Create experiment with 30% rollout
        controller.create_experiment(name="test_split", agent_name="code", rollout_percentage=0.3)

        # Test multiple decisions
        dspy_count = 0
        legacy_count = 0

        for i in range(100):
            use_dspy, exp_name = controller.should_use_dspy("code", user_id=f"user_{i}")
            if use_dspy:
                dspy_count += 1
            else:
                legacy_count += 1

        # Should be roughly 30/70 split (with some variance)
        assert 20 <= dspy_count <= 40  # Allow for variance
        assert 60 <= legacy_count <= 80
        assert dspy_count + legacy_count == 100

    def test_consistent_user_assignment(self, controller):
        """Test that same user gets consistent variant assignment."""
        controller.create_experiment(
            name="test_consistent", agent_name="code", rollout_percentage=0.5
        )

        # Same user should always get same variant
        user_id = "test_user_123"
        first_decision, _ = controller.should_use_dspy("code", user_id=user_id)

        for _ in range(10):
            decision, _ = controller.should_use_dspy("code", user_id=user_id)
            assert decision == first_decision

    def test_metric_recording(self, controller, temp_dir):
        """Test recording metrics for experiments."""
        controller.create_experiment(name="test_metrics", agent_name="auditor")

        # Record some metrics
        controller.record_metric(
            experiment_name="test_metrics", variant="legacy", metric_name="qt_score", value=0.75
        )

        controller.record_metric(
            experiment_name="test_metrics", variant="dspy", metric_name="qt_score", value=0.82
        )

        # Check metrics were recorded
        metrics_file = temp_dir / "metrics.jsonl"
        assert metrics_file.exists()

        lines = metrics_file.read_text().strip().split("\n")
        assert len(lines) >= 2  # At least our 2 metrics

        # Parse and verify metrics
        for line in lines:
            if line:
                metric = json.loads(line)
                if metric.get("metric") == "qt_score":
                    assert metric["value"] in [0.75, 0.82]

    def test_experiment_analysis_insufficient_data(self, controller):
        """Test analysis with insufficient data."""
        controller.create_experiment(name="test_analysis", agent_name="code", min_samples=10)

        # Add only a few metrics
        for i in range(3):
            controller.record_metric(
                experiment_name="test_analysis",
                variant="legacy",
                metric_name="success_rate",
                value=0.8,
            )

        # Analysis should return None due to insufficient data
        result = controller.analyze_experiment("test_analysis")
        assert result is None

    def test_experiment_analysis_with_sufficient_data(self, controller):
        """Test analysis with sufficient data."""
        controller.create_experiment(name="test_full_analysis", agent_name="auditor", min_samples=5)

        # Add sufficient metrics for both variants
        for i in range(6):
            controller.record_metric(
                experiment_name="test_full_analysis",
                variant="legacy",
                metric_name="success_rate",
                value=0.7 + (i * 0.01),
            )
            controller.record_metric(
                experiment_name="test_full_analysis",
                variant="dspy",
                metric_name="success_rate",
                value=0.8 + (i * 0.01),
            )

        # Analysis should work
        result = controller.analyze_experiment("test_full_analysis")
        assert result is not None
        assert result.control_samples >= 5
        assert result.treatment_samples >= 5
        assert result.treatment_metrics["success_rate"] > result.control_metrics["success_rate"]

    def test_agent_selection_with_ab_testing(self, registry, controller):
        """Test agent selection respects A/B testing decisions."""
        # Create experiment favoring DSPy
        controller.create_experiment(
            name="test_selection",
            agent_name="code",
            rollout_percentage=1.0,  # 100% DSPy
        )

        # Mock the controller in registry
        with patch("dspy_agents.ab_testing.get_ab_controller", return_value=controller):
            # When we request code agent, should get DSPy version
            use_dspy, _ = controller.should_use_dspy("code")
            assert use_dspy is True

            agent = registry.get_agent("code", prefer_dspy=True)
            assert isinstance(agent, DSPyCodeAgent)

    def test_pause_resume_experiment(self, controller):
        """Test pausing and resuming experiments."""
        controller.create_experiment(name="test_pause", agent_name="auditor")

        # Initially should be active
        use_dspy1, exp1 = controller.should_use_dspy("auditor")
        assert exp1 == "test_pause"

        # Pause experiment
        controller.pause_experiment("test_pause")

        # Should not use experiment when paused
        use_dspy2, exp2 = controller.should_use_dspy("auditor")
        assert exp2 == "no_experiment"

        # Resume experiment
        controller.resume_experiment("test_pause")

        # Should use experiment again
        use_dspy3, exp3 = controller.should_use_dspy("auditor")
        assert exp3 == "test_pause"

    def test_force_variant_override(self, controller):
        """Test forcing specific variant in experiment."""
        controller.create_experiment(
            name="test_force",
            agent_name="code",
            rollout_percentage=0.0,  # Would normally be all legacy
        )

        # Update to force DSPy
        controller.experiments["test_force"].force_variant = "dspy"
        controller._save_experiments()

        # Should always get DSPy
        for i in range(10):
            use_dspy, _ = controller.should_use_dspy("code", user_id=f"user_{i}")
            assert use_dspy is True

    def test_environment_override(self, controller, monkeypatch):
        """Test environment variable override."""
        controller.create_experiment(
            name="test_env",
            agent_name="auditor",
            rollout_percentage=0.0,  # Would normally be all legacy
        )

        # Set environment override
        monkeypatch.setenv("FORCE_DSPY_AUDITOR", "1")

        # Should use DSPy despite 0% rollout
        use_dspy, exp_name = controller.should_use_dspy("auditor")
        assert use_dspy is True
        assert exp_name == "forced_env"

    def test_experiment_status_tracking(self, controller):
        """Test getting experiment status."""
        controller.create_experiment(name="test_status", agent_name="code", min_samples=10)

        # Add some metrics
        for i in range(3):
            controller.record_metric(
                experiment_name="test_status",
                variant="legacy" if i % 2 == 0 else "dspy",
                metric_name="latency",
                value=100 + i,
            )

        # Get status
        status = controller.get_experiment_status("test_status")
        assert status is not None
        assert status["name"] == "test_status"
        assert status["agent"] == "code"
        assert status["control_samples"] >= 0
        assert status["treatment_samples"] >= 0
        assert 0 <= status["progress"] <= 100

    def test_list_all_experiments(self, controller):
        """Test listing all experiments."""
        # Create multiple experiments
        controller.create_experiment("exp1", "code")
        controller.create_experiment("exp2", "auditor")
        controller.create_experiment("exp3", "code")

        experiments = controller.list_experiments()
        assert len(experiments) == 3

        names = [exp["name"] for exp in experiments]
        assert "exp1" in names
        assert "exp2" in names
        assert "exp3" in names

    def test_recommendation_generation(self, controller):
        """Test recommendation generation based on results."""
        controller.create_experiment(name="test_recommend", agent_name="auditor", min_samples=3)

        # Add metrics showing DSPy improvement
        for i in range(5):
            controller.record_metric(
                experiment_name="test_recommend",
                variant="legacy",
                metric_name="quality_score",
                value=0.6,
            )
            controller.record_metric(
                experiment_name="test_recommend",
                variant="dspy",
                metric_name="quality_score",
                value=0.85,
            )

        result = controller.analyze_experiment("test_recommend")
        assert result is not None

        # Should recommend rollout due to improvement
        assert "ROLLOUT" in result.recommendation or "EXPAND" in result.recommendation

    def test_global_controller_singleton(self):
        """Test global controller is singleton."""
        controller1 = get_ab_controller()
        controller2 = get_ab_controller()
        assert controller1 is controller2

    def test_global_registry_singleton(self):
        """Test global registry is singleton."""
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        assert registry1 is registry2
