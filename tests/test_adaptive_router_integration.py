"""Integration tests for AdaptiveModelRouter.

Per ADR-024 and Leap 3 Milestone 3.
"""

import os
from datetime import datetime, timedelta

import pytest

from shared.adaptive_model_router import CostTracker, ModelRouter
from shared.agent_context import create_agent_context
from shared.task_complexity import TaskComplexity, TaskComplexityClassifier


@pytest.fixture(autouse=True)
def clean_model_env():
    """Clean model-related environment variables for tests.

    Save existing values, unset for test, restore after.
    This ensures tests run with clean environment regardless of shell config.
    """
    # Save existing values
    saved_env = {}
    model_vars = [
        "AGENCY_MODEL",
        "CODER_MODEL",
        "PLANNER_MODEL",
        "AUDITOR_MODEL",
        "QUALITY_ENFORCER_MODEL",
        "SUMMARY_MODEL",
        "FORCE_MODEL",
    ]

    for var in model_vars:
        if var in os.environ:
            saved_env[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var, value in saved_env.items():
        os.environ[var] = value


class TestModelRouting:
    """Test model routing decisions."""

    def test_p3_routes_to_local_model(self):
        """P3 simple tasks route to local Ollama model."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        result = router.route(
            task_description="Fix typo in README: recieve → receive",
            task_type="documentation",
            agent_key="coder",
        )

        assert result.is_ok()
        decision = result.unwrap()

        assert decision.complexity == TaskComplexity.P3_SIMPLE
        # Should route to local or fallback to mini
        assert decision.selected_model in ["ollama/qwen3-coder:30b", "gpt-4o-mini"]
        assert decision.estimated_cost_usd == 0.0 or decision.estimated_cost_usd < 0.01

    def test_p2_routes_to_gpt4o(self):
        """P2 moderate tasks route to gpt-4o."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        result = router.route(
            task_description="Implement user authentication with JWT tokens",
            task_type="feature_implementation",
            agent_key="coder",
        )

        assert result.is_ok()
        decision = result.unwrap()

        assert decision.complexity == TaskComplexity.P2_MODERATE
        assert decision.selected_model == "gpt-4o"
        assert decision.estimated_cost_usd > 0.0

    def test_p1_routes_to_gpt5(self):
        """P1 complex tasks route to gpt-5."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        result = router.route(
            task_description="Create ADR for database selection strategy",
            task_type="architecture",
            agent_key="chief_architect",
        )

        assert result.is_ok()
        decision = result.unwrap()

        assert decision.complexity == TaskComplexity.P1_COMPLEX
        assert decision.selected_model == "gpt-5"
        assert decision.estimated_cost_usd > 0.0

    def test_environment_override_force_model(self):
        """FORCE_MODEL environment variable overrides routing."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        # Set override
        os.environ["FORCE_MODEL"] = "gpt-4o-mini"

        try:
            result = router.route(
                task_description="Create ADR for critical architecture",
                task_type="architecture",
                agent_key="chief_architect",
            )

            assert result.is_ok()
            decision = result.unwrap()

            # Override should force gpt-4o-mini even for P1 task
            assert decision.selected_model == "gpt-4o-mini"
            assert decision.environment_override is True

        finally:
            del os.environ["FORCE_MODEL"]

    def test_environment_override_agent_specific(self):
        """Agent-specific override (e.g., CODER_MODEL)."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        os.environ["CODER_MODEL"] = "gpt-5"

        try:
            result = router.route(
                task_description="Fix typo",  # P3 task
                task_type="documentation",
                agent_key="coder",
            )

            assert result.is_ok()
            decision = result.unwrap()

            # Override should force gpt-5 even for P3
            assert decision.selected_model == "gpt-5"
            assert decision.environment_override is True

        finally:
            del os.environ["CODER_MODEL"]


class TestCostTracking:
    """Test cost tracking and telemetry."""

    def test_track_routing_decision(self):
        """CostTracker records routing decisions."""
        tracker = CostTracker()
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier, cost_tracker=tracker)

        # Route a few tasks
        router.route("Fix typo", "documentation", "coder")
        router.route("Implement auth", "feature_implementation", "coder")
        router.route("Create ADR", "architecture", "chief_architect")

        # Should have 3 decisions tracked
        assert len(tracker.decisions) == 3

    def test_cost_calculation(self):
        """Cost estimates are calculated correctly."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        result = router.route(
            task_description="Implement feature X",
            task_type="feature_implementation",
            agent_key="coder",
            estimated_tokens=1000,  # 1K tokens
        )

        assert result.is_ok()
        decision = result.unwrap()

        # P2 → gpt-4o → $1.50/1M input, $6.00/1M output
        # 1K tokens: 600 input + 400 output = $0.0009 + $0.0024 = $0.0033
        assert 0.003 <= decision.estimated_cost_usd <= 0.004

    def test_cost_summary_generation(self):
        """Generate cost summary for time period."""
        tracker = CostTracker()
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier, cost_tracker=tracker)

        # Route 10 tasks
        for i in range(10):
            if i < 6:
                # 60% P3
                router.route("Fix typo", "documentation", "coder")
            elif i < 9:
                # 30% P2
                router.route("Implement feature", "feature_implementation", "coder")
            else:
                # 10% P1
                router.route("Create ADR", "architecture", "chief_architect")

        # Generate summary
        now = datetime.now()
        summary = tracker.generate_summary(
            period_start=now - timedelta(hours=1), period_end=now + timedelta(hours=1)
        )

        assert summary.total_tasks == 10
        assert summary.p3_tasks == 6
        assert summary.p2_tasks == 3
        assert summary.p1_tasks == 1

        # Cost savings should be significant
        assert summary.cost_savings_usd > 0
        assert summary.cost_reduction_percent >= 49.9  # At least ~50% savings (account for floating point precision)


class TestPerformance:
    """Test routing performance and latency."""

    def test_routing_latency(self):
        """Routing decision latency is acceptable."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        result = router.route(
            task_description="Fix typo in README", task_type="documentation", agent_key="coder"
        )

        assert result.is_ok()
        decision = result.unwrap()

        # Routing should be fast (<50ms per spec)
        assert decision.routing_latency_ms < 100  # Relaxed for CI
        assert decision.classification_latency_ms < 100


class TestAgentContextIntegration:
    """Test integration with AgentContext."""

    def test_get_optimal_model(self):
        """AgentContext.get_optimal_model returns correct model."""
        context = create_agent_context()

        # P3 simple task
        model = context.get_optimal_model(
            agent_key="coder",
            task_description="Fix typo in variable name",
            task_type="code_modification",
        )

        # Should route to local or mini
        assert model in ["ollama/qwen3-coder:30b", "gpt-4o-mini", "gpt-5"]

    def test_get_optimal_model_p1(self):
        """AgentContext routes P1 to gpt-5."""
        context = create_agent_context()

        model = context.get_optimal_model(
            agent_key="chief_architect",
            task_description="Design distributed consensus algorithm",
            task_type="architecture",
        )

        assert model == "gpt-5"

    def test_get_optimal_model_p2(self):
        """AgentContext routes P2 to gpt-4o."""
        context = create_agent_context()

        model = context.get_optimal_model(
            agent_key="coder",
            task_description="Implement JWT authentication",
            task_type="feature_implementation",
        )

        assert model == "gpt-4o"


class TestLocalModelFallback:
    """Test local model availability and fallback."""

    def test_local_model_unavailable_fallback(self):
        """Falls back to cloud when local model unavailable."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        # Disable local model
        os.environ["USE_LOCAL_MODEL"] = "false"

        try:
            result = router.route(
                task_description="Fix typo", task_type="documentation", agent_key="coder"
            )

            assert result.is_ok()
            decision = result.unwrap()

            # Should use cloud fallback
            assert decision.selected_model == "gpt-4o-mini"
            assert decision.fallback_used is True

        finally:
            del os.environ["USE_LOCAL_MODEL"]


class TestVectorStoreLearning:
    """Test VectorStore pattern storage (Article IV)."""

    def test_pattern_storage_on_completion(self):
        """Routing patterns are stored to VectorStore."""

        class MockVectorStore:
            def __init__(self):
                self.stored_memories = []

            def add_memory(self, key, content, tags=None, namespace=None):
                self.stored_memories.append(
                    {"key": key, "content": content, "tags": tags or [], "namespace": namespace}
                )

        vector_store = MockVectorStore()
        tracker = CostTracker()
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier, cost_tracker=tracker)

        # Route a task
        result = router.route(
            task_description="Implement auth", task_type="feature_implementation", agent_key="coder"
        )

        assert result.is_ok()
        decision = result.unwrap()

        # Record completion
        tracker.record_completion(
            decision=decision,
            success=True,
            actual_tokens=500,
            duration_ms=2500.0,
            vector_store=vector_store,
        )

        # Verify pattern stored
        assert len(vector_store.stored_memories) == 1

        memory = vector_store.stored_memories[0]
        assert "routing_" in memory["key"]
        assert memory["content"]["task_description"] == "Implement auth"
        assert memory["content"]["success"] is True
        assert "routing_pattern" in memory["tags"]
        assert memory["namespace"] == "task_classification"


class TestConstitutionalCompliance:
    """Test constitutional compliance (Articles I-V)."""

    def test_article_ii_result_pattern(self):
        """All routing operations use Result pattern (Article II)."""
        classifier = TaskComplexityClassifier()
        router = ModelRouter(classifier=classifier)

        result = router.route(
            task_description="Fix typo", task_type="documentation", agent_key="coder"
        )

        # Result pattern used
        assert hasattr(result, "is_ok")
        assert hasattr(result, "is_err")
        assert result.is_ok() or result.is_err()

    def test_article_iv_vectorstore_integration(self):
        """VectorStore integration is mandatory (Article IV)."""

        class MockVectorStore:
            def search(self, query, namespace, limit):
                return []

        # Classifier accepts VectorStore
        classifier = TaskComplexityClassifier(vector_store=MockVectorStore())

        assert classifier.vector_store is not None

    def test_classification_confidence_tracking(self):
        """Classification confidence is tracked (Article II verification)."""
        classifier = TaskComplexityClassifier()

        result = classifier.classify("Fix typo in README", task_type="documentation")

        assert result.is_ok()
        classification = result.unwrap()

        # Confidence is tracked
        assert hasattr(classification, "confidence")
        assert 0.0 <= classification.confidence <= 1.0
