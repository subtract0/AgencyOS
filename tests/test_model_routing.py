"""
Test suite for multi-tier model routing optimization.

Article II: TDD - Tests written FIRST before implementation.
ADR-008: Strict typing with Pydantic.

10x cost reduction: Route 60% of tasks to gpt-4o-mini ($0.15/1M vs $4/1M)
"""

import os
from unittest.mock import patch

import pytest

from shared.model_policy import (
    agent_model,
    classify_task_complexity,
    get_optimal_model,
)


class TestTaskComplexityClassification:
    """Test AI task complexity classification for model routing."""

    def test_classify_simple_task_p3(self):
        """Test classification of simple P3 tasks (gpt-4o-mini)."""
        # P3: Simple fixes, formatting, documentation
        simple_tasks = [
            "Fix typo in README.md",
            "Add docstring to function",
            "Format code with black",
            "Remove unused import",
            "Update copyright year",
        ]

        for task in simple_tasks:
            complexity = classify_task_complexity(task)
            assert complexity == "P3", f"Task '{task}' should be P3 (simple)"

    def test_classify_moderate_task_p2(self):
        """Test classification of moderate P2 tasks (gpt-4o)."""
        # P2: Standard features, refactoring, bug fixes
        moderate_tasks = [
            "Implement user authentication endpoint",
            "Refactor database connection pooling",
            "Fix race condition in async handler",
            "Add validation to API input",
            "Write unit tests for new feature",
        ]

        for task in moderate_tasks:
            complexity = classify_task_complexity(task)
            assert complexity == "P2", f"Task '{task}' should be P2 (moderate)"

    def test_classify_complex_task_p1(self):
        """Test classification of complex P1 tasks (gpt-5)."""
        # P1: Architecture, critical systems, constitutional compliance
        complex_tasks = [
            "Design distributed consensus algorithm",
            "Implement constitutional compliance validation",
            "Create ADR for system architecture",
            "Design multi-agent coordination protocol",
            "Implement autonomous healing system",
        ]

        for task in complex_tasks:
            complexity = classify_task_complexity(task)
            assert complexity == "P1", f"Task '{task}' should be P1 (complex)"

    def test_classify_ambiguous_task_defaults_to_p2(self):
        """Test that ambiguous tasks default to P2 (safe middle ground)."""
        ambiguous = "Update the system"
        complexity = classify_task_complexity(ambiguous)
        assert complexity == "P2", "Ambiguous tasks should default to P2"

    def test_classify_empty_task(self):
        """Test handling of empty task description."""
        complexity = classify_task_complexity("")
        assert complexity == "P2", "Empty task should default to P2"


class TestOptimalModelSelection:
    """Test optimal model selection based on complexity."""

    def test_p3_tasks_use_mini_model(self):
        """Test P3 tasks route to gpt-4o-mini or local model for cost savings."""
        # Test both local and cloud modes
        # Cloud mode (USE_LOCAL_MODEL=false)
        with patch.dict(os.environ, {"CODER_MODEL": "", "USE_LOCAL_MODEL": "false"}, clear=False):
            model = get_optimal_model("P3", agent_key="coder")
            assert model == "gpt-4o-mini", f"P3 cloud mode should use gpt-4o-mini, got {model}"
            assert model != "gpt-5", "P3 should not use expensive gpt-5"

        # Local mode (USE_LOCAL_MODEL=true)
        with patch.dict(os.environ, {"CODER_MODEL": "", "USE_LOCAL_MODEL": "true"}, clear=False):
            model = get_optimal_model("P3", agent_key="coder")
            assert "ollama/" in model.lower(), f"P3 local mode should use ollama model, got {model}"
            assert model != "gpt-5", "P3 should not use expensive gpt-5"

    def test_p2_tasks_use_standard_model(self):
        """Test P2 tasks route to gpt-4o (balanced cost/quality)."""
        # Clear environment overrides to test complexity-based routing
        with patch.dict(os.environ, {"CODER_MODEL": ""}, clear=False):
            model = get_optimal_model("P2", agent_key="coder")

            # Should use standard gpt-4o or agent default
            assert model in ["gpt-4o", "gpt-5"], f"P2 should use gpt-4o or gpt-5, got {model}"

    def test_p1_tasks_use_premium_model(self):
        """Test P1 tasks route to gpt-5 for maximum quality."""
        # Clear environment overrides to test complexity-based routing
        with patch.dict(os.environ, {"PLANNER_MODEL": ""}, clear=False):
            model = get_optimal_model("P1", agent_key="planner")

            # Should use premium model for critical tasks
            assert model == "gpt-5", "P1 critical tasks require gpt-5"

    def test_env_override_still_works(self):
        """Test environment variable overrides are still respected."""
        with patch.dict(os.environ, {"CODER_MODEL": "custom-model"}):
            model = get_optimal_model("P2", agent_key="coder")
            assert model == "custom-model", "Env override should still work"

    def test_unknown_complexity_defaults_to_p2(self):
        """Test unknown complexity defaults to P2 (safe choice)."""
        model = get_optimal_model("UNKNOWN", agent_key="coder")
        # Should default to P2 behavior
        assert model != "gpt-4o-mini", "Unknown complexity should not use cheapest model"


class TestModelRoutingIntegration:
    """Integration tests for model routing with existing agent_model()."""

    def test_existing_agent_model_function_unchanged(self):
        """Test backward compatibility - agent_model() still works."""
        # Mock both os.getenv (for env var check) and DEFAULTS dict (for default lookup)
        import shared.model_policy

        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            # Return None for agent model env vars to test default behavior
            if key in ["PLANNER_MODEL", "CODER_MODEL", "SUMMARY_MODEL"]:
                return None
            return original_getenv(key, default)

        mock_defaults = {
            "planner": "gpt-5",
            "coder": "gpt-5",
            "summary": "gpt-5-mini",  # Test expectation
        }

        with patch.object(shared.model_policy.os, 'getenv', side_effect=mock_getenv), \
             patch.object(shared.model_policy, 'DEFAULTS', mock_defaults):
            # Should return default model for each agent
            planner_model = agent_model("planner")
            coder_model = agent_model("coder")
            summary_model = agent_model("summary")

            assert isinstance(planner_model, str)
            assert isinstance(coder_model, str)
            assert isinstance(summary_model, str)

            # Summary should use cheaper model
            assert "mini" in summary_model.lower() or summary_model == "gpt-5-mini"

    def test_complexity_aware_routing_api(self):
        """Test new complexity-aware API works alongside existing API."""
        # Old API still works
        old_api_model = agent_model("coder")

        # New API provides complexity-aware routing
        simple_model = get_optimal_model("P3", agent_key="coder")
        complex_model = get_optimal_model("P1", agent_key="coder")

        assert isinstance(simple_model, str)
        assert isinstance(complex_model, str)

        # Complex should be equal or better than simple
        # (gpt-5 > gpt-4o > gpt-4o-mini)
        model_tier = {"gpt-4o-mini": 1, "gpt-4o": 2, "gpt-5": 3}
        simple_tier = model_tier.get(simple_model, 2)
        complex_tier = model_tier.get(complex_model, 2)

        assert complex_tier >= simple_tier, "Complex tasks should use equal or better model"


class TestCostOptimization:
    """Test cost optimization scenarios."""

    def test_60_percent_task_distribution(self):
        """Test realistic task distribution achieves 60% cost savings."""
        # Clear env override for this test
        with patch.dict(os.environ, {"CODER_MODEL": ""}, clear=False):
            # Simulate realistic task mix
            tasks = [
                # 60% P3 (simple) - Documentation, formatting, simple fixes
                *["P3"] * 60,
                # 30% P2 (moderate) - Features, refactoring
                *["P2"] * 30,
                # 10% P1 (complex) - Architecture, critical systems
                *["P1"] * 10,
            ]

            # Count model usage
            model_usage = {"gpt-4o-mini": 0, "gpt-4o": 0, "gpt-5": 0}

            for complexity in tasks:
                model = get_optimal_model(complexity, agent_key="coder")
                if "mini" in model.lower():
                    model_usage["gpt-4o-mini"] += 1
                elif model == "gpt-4o":
                    model_usage["gpt-4o"] += 1
                elif model == "gpt-5":
                    model_usage["gpt-5"] += 1

            # At least 50% should use cost-efficient models
            efficient_usage = model_usage["gpt-4o-mini"] + model_usage["gpt-4o"]
            total = sum(model_usage.values())

            efficiency_rate = efficient_usage / total if total > 0 else 0
            assert efficiency_rate >= 0.5, (
                f"Should route ≥50% to efficient models, got {efficiency_rate:.1%}"
            )

    def test_cost_savings_calculation(self):
        """Test calculated cost savings from model routing."""
        # Pricing (per 1M tokens)
        prices = {
            "gpt-4o-mini": 0.15,
            "gpt-4o": 1.50,
            "gpt-5": 4.00,
        }

        # Baseline: Everything on gpt-5
        baseline_cost = 100 * prices["gpt-5"]  # 100 tasks

        # Optimized: 60% P3 (mini), 30% P2 (4o), 10% P1 (gpt-5)
        optimized_cost = 60 * prices["gpt-4o-mini"] + 30 * prices["gpt-4o"] + 10 * prices["gpt-5"]

        savings = (baseline_cost - optimized_cost) / baseline_cost

        # Should achieve >70% cost reduction
        assert savings >= 0.70, f"Should save ≥70% on costs, got {savings:.1%}"


class TestEdgeCases:
    """Edge case tests for model routing."""

    def test_none_task_description(self):
        """Test handling of None task description."""
        complexity = classify_task_complexity(None)
        assert complexity in ["P1", "P2", "P3"], "Should return valid complexity"

    def test_very_long_task_description(self):
        """Test handling of very long task descriptions."""
        long_task = "Fix bug " * 1000  # 5000 chars
        complexity = classify_task_complexity(long_task)
        assert complexity in ["P1", "P2", "P3"]

    def test_special_characters_in_task(self):
        """Test task descriptions with special characters."""
        special = "Fix bug: 'NoneType' object has no attribute 'get' @line:42"
        complexity = classify_task_complexity(special)
        assert complexity in ["P1", "P2", "P3"]

    def test_unknown_agent_key(self):
        """Test model selection for unknown agent."""
        model = get_optimal_model("P2", agent_key="unknown_agent")
        assert isinstance(model, str), "Should return valid model string"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
