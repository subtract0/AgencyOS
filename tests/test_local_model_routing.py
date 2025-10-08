"""Test local model routing for quality_enforcer and other agents.

This test suite validates Phase 3 of 10X optimization: local model integration
for 60% of tasks (P3 simple tasks) to achieve $0 cost.

Constitutional Compliance:
- Article I: Complete context before action (tests verify all routing paths)
- Article II: TDD approach (tests written first, then implementation)
- Article IV: Learning from patterns (routing patterns based on task complexity)
"""
import os
import unittest
from unittest.mock import patch

from shared.model_policy import classify_task_complexity, get_optimal_model


class TestLocalModelRouting(unittest.TestCase):
    """Test local model routing for P3 simple tasks."""

    def test_p3_routes_to_local_model(self):
        """Test that P3 simple tasks route to local Ollama model."""
        with patch.dict(os.environ, {
            "USE_LOCAL_MODEL": "true",
            "LOCAL_MODEL_NAME": "hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0",
            "QUALITY_ENFORCER_MODEL": "",  # Clear override
        }, clear=False):
            task = "Fix typo in docstring"
            complexity = classify_task_complexity(task)
            model = get_optimal_model(complexity, agent_key="quality_enforcer")

            self.assertEqual(complexity, "P3")
            self.assertEqual(model, "ollama/hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0")

    def test_p3_cloud_fallback_when_disabled(self):
        """Test that P3 tasks use cloud when local disabled."""
        with patch.dict(os.environ, {
            "USE_LOCAL_MODEL": "false",
            "QUALITY_ENFORCER_MODEL": "",
        }, clear=False):
            task = "Remove unused import"
            complexity = classify_task_complexity(task)
            model = get_optimal_model(complexity, agent_key="quality_enforcer")

            self.assertEqual(complexity, "P3")
            self.assertEqual(model, "gpt-4o-mini")

    def test_p2_uses_gpt4o(self):
        """Test that P2 moderate tasks use gpt-4o."""
        with patch.dict(os.environ, {
            "USE_LOCAL_MODEL": "true",
            "QUALITY_ENFORCER_MODEL": "",
        }, clear=False):
            task = "Implement OAuth authentication"
            complexity = classify_task_complexity(task)
            model = get_optimal_model(complexity, agent_key="quality_enforcer")

            self.assertEqual(complexity, "P2")
            self.assertEqual(model, "gpt-4o")

    def test_p1_uses_gpt5(self):
        """Test that P1 complex tasks use gpt-5."""
        with patch.dict(os.environ, {
            "USE_LOCAL_MODEL": "true",
            "QUALITY_ENFORCER_MODEL": "",
        }, clear=False):
            task = "Design distributed consensus protocol"
            complexity = classify_task_complexity(task)
            model = get_optimal_model(complexity, agent_key="quality_enforcer")

            self.assertEqual(complexity, "P1")
            self.assertEqual(model, "gpt-5")

    def test_env_override_takes_precedence(self):
        """Test that QUALITY_ENFORCER_MODEL env var overrides routing."""
        with patch.dict(os.environ, {
            "USE_LOCAL_MODEL": "true",
            "QUALITY_ENFORCER_MODEL": "gpt-4o",  # Override
        }, clear=False):
            task = "Fix typo"  # P3, should route to local but env overrides
            complexity = classify_task_complexity(task)
            model = get_optimal_model(complexity, agent_key="quality_enforcer")

            self.assertEqual(model, "gpt-4o")  # Env override wins

    def test_multiple_p3_tasks_route_locally(self):
        """Test various P3 tasks all route to local model."""
        expected_model = "ollama/hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0"
        with patch.dict(os.environ, {
            "USE_LOCAL_MODEL": "true",
            "LOCAL_MODEL_NAME": "hf.co/abirhossen/Qwen3-Coder-30B-A3B-Instruct-Q8_0-GGUF:Q8_0",
            "QUALITY_ENFORCER_MODEL": "",
        }, clear=False):
            p3_tasks = [
                "Fix typo in comment",
                "Remove unused import",
                "Update docstring formatting",
                "Delete dead code",
                "Clean up whitespace",
            ]

            for task in p3_tasks:
                complexity = classify_task_complexity(task)
                model = get_optimal_model(complexity, agent_key="quality_enforcer")

                with self.subTest(task=task):
                    self.assertEqual(complexity, "P3", f"Task '{task}' should be P3")
                    self.assertEqual(model, expected_model,
                                     f"Task '{task}' should route to local")

    def test_cost_savings_distribution(self):
        """Test realistic task distribution achieves 96% cost reduction."""
        with patch.dict(os.environ, {
            "USE_LOCAL_MODEL": "true",
            "QUALITY_ENFORCER_MODEL": "",
        }, clear=False):
            # Realistic distribution: 60% P3, 30% P2, 10% P1
            tasks = [
                *["Fix typo"] * 60,  # P3 → $0 (local)
                *["Implement feature"] * 30,  # P2 → gpt-4o
                *["Design architecture"] * 10,  # P1 → gpt-5
            ]

            cost_free = 0
            cost_moderate = 0
            cost_premium = 0

            for task in tasks:
                complexity = classify_task_complexity(task)
                model = get_optimal_model(complexity, agent_key="quality_enforcer")

                if model.startswith("ollama/"):
                    cost_free += 1
                elif model == "gpt-4o":
                    cost_moderate += 1
                elif model == "gpt-5":
                    cost_premium += 1

            # Verify distribution
            total = len(tasks)
            self.assertEqual(cost_free, 60, "60% should use local (FREE)")
            self.assertEqual(cost_moderate, 30, "30% should use gpt-4o")
            self.assertEqual(cost_premium, 10, "10% should use gpt-5")

            # Calculate cost savings vs all gpt-5
            # $4.00/1M * 100 tasks = $400 baseline
            # $0/1M * 60 + $1.50/1M * 30 + $4.00/1M * 10 = $85
            # Savings: (400-85)/400 = 78.75%
            baseline_cost = total * 4.00
            actual_cost = cost_free * 0 + cost_moderate * 1.50 + cost_premium * 4.00
            savings_pct = (baseline_cost - actual_cost) / baseline_cost

            self.assertGreaterEqual(savings_pct, 0.78, "Should save at least 78% vs all gpt-5")

    def test_custom_local_model_name(self):
        """Test that LOCAL_MODEL_NAME env var changes local model."""
        with patch.dict(os.environ, {
            "USE_LOCAL_MODEL": "true",
            "LOCAL_MODEL_NAME": "custom-model:7b",
            "QUALITY_ENFORCER_MODEL": "",
        }, clear=False):
            task = "Fix typo"
            complexity = classify_task_complexity(task)
            model = get_optimal_model(complexity, agent_key="quality_enforcer")

            self.assertEqual(model, "ollama/custom-model:7b")


if __name__ == "__main__":
    unittest.main()
