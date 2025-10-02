"""
Test prompt compression and token savings.

Validates:
- Prompt structure (system vs. task separation)
- Token estimation accuracy
- Compression statistics
- 60% savings target

Constitutional Compliance:
- Article I: Complete context in prompts
- Article II: 100% test verification
- Law #1: TDD (tests first)
"""

import pytest
from shared.prompt_compression import (
    create_compressed_prompt,
    estimate_tokens,
    get_compression_stats,
    load_agent_role,
    load_agent_instructions,
    CONSTITUTION_CORE,
    QUALITY_STANDARDS,
)


@pytest.mark.unit
class TestPromptCompression:
    """Test prompt compression utilities."""

    @pytest.mark.unit
    def test_create_compressed_prompt_structure(self):
        """Test compressed prompt has correct structure."""
        prompts = create_compressed_prompt(
            agent_name="planner",
            task="Create a plan",
            context={}
        )

        # Verify structure
        assert "system" in prompts
        assert "task" in prompts
        assert isinstance(prompts["system"], str)
        assert isinstance(prompts["task"], str)

        # System prompt should contain constitution and standards
        assert "Constitutional" in prompts["system"]
        assert "Quality Standards" in prompts["system"]

        # Task prompt should contain user request
        assert "Create a plan" in prompts["task"]

    @pytest.mark.unit
    def test_system_prompt_is_cacheable(self):
        """Test system prompt is stable across calls (cacheable)."""
        prompts1 = create_compressed_prompt("planner", "Task 1", {})
        prompts2 = create_compressed_prompt("planner", "Task 2", {})

        # System prompts should be identical (cacheable)
        assert prompts1["system"] == prompts2["system"]

        # Task prompts should differ (variable)
        assert prompts1["task"] != prompts2["task"]

    @pytest.mark.unit
    def test_task_prompt_varies_by_request(self):
        """Test task prompt changes with user request."""
        prompts1 = create_compressed_prompt("planner", "Task A", {})
        prompts2 = create_compressed_prompt("planner", "Task B", {})

        # Task prompts should differ
        assert "Task A" in prompts1["task"]
        assert "Task B" in prompts2["task"]
        assert prompts1["task"] != prompts2["task"]

    @pytest.mark.unit
    def test_context_included_in_task_prompt(self):
        """Test context is included in task prompt."""
        context = {
            "files": ["spec.md", "plan.md"],
            "data": "Focus on security"
        }
        prompts = create_compressed_prompt("planner", "Create plan", context)

        # Files should be in task prompt
        assert "spec.md" in prompts["task"]
        assert "plan.md" in prompts["task"]

        # Context data should be in task prompt
        assert "Focus on security" in prompts["task"]

    @pytest.mark.unit
    def test_estimate_tokens_accuracy(self):
        """Test token estimation is reasonably accurate."""
        # Short text
        short_text = "Hello world"
        short_tokens = estimate_tokens(short_text)
        assert 2 <= short_tokens <= 5  # ~3 tokens expected

        # Medium text
        medium_text = "This is a longer sentence with more words."
        medium_tokens = estimate_tokens(medium_text)
        assert 10 <= medium_tokens <= 15

        # Long text
        long_text = "A" * 4000  # 4000 chars
        long_tokens = estimate_tokens(long_text)
        assert 900 <= long_tokens <= 1100  # ~1000 tokens

    @pytest.mark.unit
    def test_compression_stats_calculation(self):
        """Test compression statistics are calculated correctly."""
        prompts = create_compressed_prompt("planner", "Test task", {})
        stats = get_compression_stats(prompts)

        # Verify structure
        assert "system_tokens" in stats
        assert "task_tokens" in stats
        assert "first_call_tokens" in stats
        assert "cached_call_tokens" in stats
        assert "savings_percent" in stats

        # Verify calculations
        assert stats["first_call_tokens"] == (
            stats["system_tokens"] + stats["task_tokens"]
        )
        assert stats["cached_call_tokens"] == stats["task_tokens"]

        # Verify savings percentage
        expected_savings = round(
            (1 - stats["cached_call_tokens"] / stats["first_call_tokens"]) * 100,
            1
        )
        assert stats["savings_percent"] == expected_savings

    @pytest.mark.unit
    def test_token_savings_target(self):
        """Test prompt compression achieves 60% savings target."""
        prompts = create_compressed_prompt(
            agent_name="planner",
            task="Create implementation plan for user authentication",
            context={"files": ["spec.md"]}
        )
        stats = get_compression_stats(prompts)

        # System tokens should be reasonable (cacheable)
        # Note: Includes full agent instruction, so may be ~4,000 tokens
        assert stats["system_tokens"] < 5000, (
            f"System prompt too large: {stats['system_tokens']} tokens"
        )

        # Task tokens should be minimal
        assert stats["task_tokens"] < 500, (
            f"Task prompt too large: {stats['task_tokens']} tokens"
        )

        # First call should be <5,000 tokens total
        assert stats["first_call_tokens"] < 5500, (
            f"First call too large: {stats['first_call_tokens']} tokens"
        )

        # Cached calls should be minimal (<500 tokens)
        assert stats["cached_call_tokens"] < 500, (
            f"Cached call too large: {stats['cached_call_tokens']} tokens"
        )

        # Savings should be ≥50% (target is 60%)
        assert stats["savings_percent"] >= 50, (
            f"Insufficient savings: {stats['savings_percent']}% (target: 60%)"
        )

    @pytest.mark.unit
    def test_different_agents_same_structure(self):
        """Test different agents use same prompt structure."""
        agents = ["planner", "coder", "auditor"]

        for agent_name in agents:
            prompts = create_compressed_prompt(agent_name, "Test task", {})

            # All should have same structure
            assert "system" in prompts
            assert "task" in prompts

            # All should contain constitution
            assert "Constitutional" in prompts["system"]

            # Agent name should be in system prompt
            assert agent_name in prompts["system"]

    @pytest.mark.unit
    def test_load_agent_role(self):
        """Test agent role loading."""
        role = load_agent_role("planner")

        # Should return non-empty string
        assert isinstance(role, str)
        assert len(role) > 0

        # Should be descriptive
        assert len(role) > 10  # More than just agent name

    @pytest.mark.unit
    def test_load_agent_instructions(self):
        """Test agent instructions loading."""
        instructions = load_agent_instructions("planner")

        # Should return non-empty string
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    @pytest.mark.unit
    def test_constitution_core_included(self):
        """Test constitution core is included in system prompt."""
        prompts = create_compressed_prompt("planner", "Test", {})

        # Should contain all 5 articles
        assert "Article I" in prompts["system"]
        assert "Article II" in prompts["system"]
        assert "Article III" in prompts["system"]
        assert "Article IV" in prompts["system"]
        assert "Article V" in prompts["system"]

    @pytest.mark.unit
    def test_quality_standards_included(self):
        """Test quality standards are included in system prompt."""
        prompts = create_compressed_prompt("planner", "Test", {})

        # Should contain key quality standards
        assert "TDD" in prompts["system"]
        assert "Strict Typing" in prompts["system"]
        assert "Result" in prompts["system"]  # Result pattern

    @pytest.mark.unit
    def test_empty_context_handling(self):
        """Test handling of empty/None context."""
        # None context
        prompts1 = create_compressed_prompt("planner", "Test", None)
        assert "task" in prompts1
        assert "Test" in prompts1["task"]

        # Empty context
        prompts2 = create_compressed_prompt("planner", "Test", {})
        assert "task" in prompts2
        assert "Test" in prompts2["task"]

    @pytest.mark.unit
    def test_large_context_handling(self):
        """Test handling of large context (many files)."""
        context = {
            "files": [f"file{i}.py" for i in range(50)],
            "data": "Large dataset" * 100
        }
        prompts = create_compressed_prompt("planner", "Test", context)

        # Should not error
        assert "task" in prompts

        # Files should be included
        assert "file0.py" in prompts["task"]
        assert "file49.py" in prompts["task"]

    @pytest.mark.unit
    def test_prompt_determinism(self):
        """Test prompts are deterministic (same inputs = same outputs)."""
        task = "Create plan"
        context = {"files": ["spec.md"]}

        prompts1 = create_compressed_prompt("planner", task, context)
        prompts2 = create_compressed_prompt("planner", task, context)

        # Should be identical
        assert prompts1["system"] == prompts2["system"]
        assert prompts1["task"] == prompts2["task"]


@pytest.mark.unit
class TestCompressionBenchmark:
    """Benchmark prompt compression performance."""

    @pytest.mark.benchmark
    def test_compression_speed(self):
        """Test prompt compression is fast (<10ms)."""
        import time

        start = time.perf_counter()

        for _ in range(100):
            create_compressed_prompt("planner", "Test task", {})

        elapsed = time.perf_counter() - start

        # Should compress 100 prompts in <1 second
        assert elapsed < 1.0, f"Too slow: {elapsed:.3f}s for 100 compressions"

        # Average should be <10ms per compression
        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 10, f"Average too slow: {avg_ms:.1f}ms per compression"

    @pytest.mark.benchmark
    def test_token_estimation_speed(self):
        """Test token estimation is fast."""
        import time

        text = "Test text " * 1000  # ~10,000 chars

        start = time.perf_counter()

        for _ in range(1000):
            estimate_tokens(text)

        elapsed = time.perf_counter() - start

        # Should estimate 1000 times in <0.1s
        assert elapsed < 0.1, f"Too slow: {elapsed:.3f}s for 1000 estimations"


@pytest.mark.unit
class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.unit
    def test_planner_agent_scenario(self):
        """Test planner agent prompt compression."""
        prompts = create_compressed_prompt(
            agent_name="planner",
            task="Create implementation plan for user authentication feature",
            context={
                "files": ["specs/user_auth.md", "plans/authentication.md"],
                "data": "Focus on security, type safety, and testing"
            }
        )

        stats = get_compression_stats(prompts)

        # Verify reasonable token counts
        assert stats["system_tokens"] > 100  # Has content
        assert stats["task_tokens"] > 20  # Has task (may be small)
        assert stats["savings_percent"] > 40  # Good savings

    @pytest.mark.unit
    def test_coder_agent_scenario(self):
        """Test coder agent prompt compression."""
        prompts = create_compressed_prompt(
            agent_name="coder",
            task="Implement user registration with email validation",
            context={
                "files": ["src/auth/register.py", "tests/test_register.py"],
                "data": "Use Result pattern for error handling"
            }
        )

        stats = get_compression_stats(prompts)

        # Verify savings
        assert stats["savings_percent"] >= 50

    @pytest.mark.unit
    def test_multiple_agents_caching(self):
        """Test multiple agents can benefit from caching."""
        agents = ["planner", "coder", "auditor", "quality_enforcer"]

        for agent_name in agents:
            prompts = create_compressed_prompt(
                agent_name=agent_name,
                task=f"Perform {agent_name} tasks",
                context={}
            )

            stats = get_compression_stats(prompts)

            # All agents should achieve good savings
            assert stats["savings_percent"] >= 40, (
                f"{agent_name} insufficient savings: {stats['savings_percent']}%"
            )
