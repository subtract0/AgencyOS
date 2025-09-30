"""
Comprehensive tests for Enhanced Model Policy (Trinity Protocol).

Tests complexity assessment, classification, tier selection, model routing,
environment overrides, and backward compatibility using NECESSARY pattern.

NECESSARY Pattern Compliance:
- Named: Descriptive test names explain what is being tested
- Executable: All tests are deterministic and fast (<1s total)
- Comprehensive: Covers normal, edge, error, and boundary cases
- Error-validated: Tests error conditions and edge cases
- State-verified: Asserts verify correct state changes
- Side-effects controlled: No external dependencies, uses mocks
- Assertions meaningful: Clear, specific assertions
- Repeatable: Deterministic, no flaky behavior
- Yield fast: All tests complete in <1s total
"""

import os
import pytest
from unittest.mock import patch
from typing import Optional

from shared.model_policy_enhanced import (
    ModelTier,
    ComplexityLevel,
    assess_complexity,
    classify_complexity,
    select_model_tier,
    get_model_for_agent,
    should_use_local,
    agent_model,
    TIER_MODELS,
    TRINITY_AGENT_TIERS,
    AGENCY_AGENT_MODELS,
)


class TestComplexityAssessment:
    """Test complexity assessment with different parameters."""

    def test_assess_complexity_normal_priority_single_file(self):
        """Test complexity assessment for normal priority single-file task."""
        score = assess_complexity(
            task_description="Fix typo in function docstring",
            scope="single-file",
            priority="NORMAL"
        )
        assert 0.0 <= score <= 1.0
        assert score == 0.1  # Only scope contributes

    def test_assess_complexity_high_priority_multi_file(self):
        """Test complexity assessment for high priority multi-file task."""
        score = assess_complexity(
            task_description="Refactor authentication module",
            scope="multi-file",
            priority="HIGH"
        )
        assert score == 0.6  # 0.3 (HIGH) + 0.3 (multi-file)

    def test_assess_complexity_critical_priority_system_wide(self):
        """Test complexity assessment for critical priority system-wide task."""
        score = assess_complexity(
            task_description="Fix security vulnerability in auth system",
            scope="system-wide",
            priority="CRITICAL"
        )
        assert score == 1.0  # 0.5 (CRITICAL) + 0.7 (system-wide), capped at 1.0

    def test_assess_complexity_with_architecture_keyword(self):
        """Test complexity assessment with architecture keyword."""
        score = assess_complexity(
            task_description="Implement new architecture pattern",
            keywords=["architecture"],
            scope="single-file",
            priority="NORMAL"
        )
        assert abs(score - 0.3) < 0.001  # 0.1 (single-file) + 0.2 (architecture keyword)

    def test_assess_complexity_with_security_keyword(self):
        """Test complexity assessment with security keyword."""
        score = assess_complexity(
            task_description="Fix critical security issue",
            keywords=["security", "critical"],
            scope="multi-file",
            priority="CRITICAL"
        )
        # 0.5 (CRITICAL) + 0.3 (multi-file) + 0.2 (security) + 0.2 (critical) = 1.2, capped at 1.0
        assert score == 1.0

    def test_assess_complexity_with_refactor_keyword(self):
        """Test complexity assessment with refactor keyword."""
        score = assess_complexity(
            task_description="Refactor legacy code module",
            keywords=["refactor"],
            scope="multi-file",
            priority="NORMAL"
        )
        assert abs(score - 0.45) < 0.001  # 0.3 (multi-file) + 0.15 (refactor keyword)

    def test_assess_complexity_with_performance_keyword(self):
        """Test complexity assessment with performance keyword."""
        score = assess_complexity(
            task_description="Optimize database query performance",
            keywords=["performance"],
            scope="single-file",
            priority="NORMAL"
        )
        assert score == 0.2  # 0.1 (single-file) + 0.1 (performance keyword)

    def test_assess_complexity_with_constitutional_violation_keyword(self):
        """Test complexity assessment with constitutional violation keyword."""
        score = assess_complexity(
            task_description="Fix constitutional_violation in type checking",
            keywords=["constitutional_violation"],
            scope="architecture",
            priority="HIGH"
        )
        # 0.3 (HIGH) + 0.5 (architecture) + 0.15 (constitutional_violation) = 0.95
        assert abs(score - 0.95) < 0.001

    def test_assess_complexity_with_multi_agent_keyword(self):
        """Test complexity assessment with multi-agent keyword."""
        score = assess_complexity(
            task_description="Coordinate multi-agent workflow",
            keywords=["multi-agent"],
            scope="system-wide",
            priority="NORMAL"
        )
        assert score == 0.85  # 0.7 (system-wide) + 0.15 (multi-agent keyword)

    def test_assess_complexity_with_unknown_keyword(self):
        """Test complexity assessment with unknown keyword gets default weight."""
        score = assess_complexity(
            task_description="Update configuration file",
            keywords=["config"],
            scope="single-file",
            priority="NORMAL"
        )
        assert abs(score - 0.15) < 0.001  # 0.1 (single-file) + 0.05 (unknown keyword default)

    def test_assess_complexity_with_high_evidence_count(self):
        """Test complexity assessment with high evidence count increases score."""
        score = assess_complexity(
            task_description="Fix common pattern error",
            scope="single-file",
            priority="NORMAL",
            evidence_count=5
        )
        assert abs(score - 0.15) < 0.001  # 0.1 (single-file) + 0.05 (evidence bonus)

    def test_assess_complexity_with_low_evidence_count(self):
        """Test complexity assessment with low evidence count has no bonus."""
        score = assess_complexity(
            task_description="Fix rare error",
            scope="single-file",
            priority="NORMAL",
            evidence_count=2
        )
        assert score == 0.1  # 0.1 (single-file), no evidence bonus

    def test_assess_complexity_capped_at_one(self):
        """Test complexity score is capped at 1.0."""
        score = assess_complexity(
            task_description="Critical security refactor across system architecture",
            keywords=["security", "critical", "architecture", "system-wide", "refactor"],
            scope="system-wide",
            priority="CRITICAL",
            evidence_count=10
        )
        assert score == 1.0

    def test_assess_complexity_minimum_zero(self):
        """Test complexity score has minimum of 0.0."""
        score = assess_complexity(
            task_description="Simple change",
            scope="single-file",
            priority="NORMAL"
        )
        assert score >= 0.0

    def test_assess_complexity_case_insensitive_keywords(self):
        """Test keyword matching is case-insensitive."""
        score1 = assess_complexity(
            task_description="ARCHITECTURE changes needed",
            keywords=["architecture"],
            scope="single-file",
            priority="NORMAL"
        )
        score2 = assess_complexity(
            task_description="architecture changes needed",
            keywords=["ARCHITECTURE"],
            scope="single-file",
            priority="NORMAL"
        )
        assert abs(score1 - score2) < 0.001
        assert abs(score1 - 0.3) < 0.001  # Both match keyword


class TestComplexityClassification:
    """Test complexity score classification into levels."""

    def test_classify_complexity_trivial_lower_bound(self):
        """Test classification of trivial complexity at lower bound."""
        level = classify_complexity(0.0)
        assert level == ComplexityLevel.TRIVIAL

    def test_classify_complexity_trivial_upper_bound(self):
        """Test classification of trivial complexity at upper bound."""
        level = classify_complexity(0.29)
        assert level == ComplexityLevel.TRIVIAL

    def test_classify_complexity_simple_lower_bound(self):
        """Test classification of simple complexity at lower bound."""
        level = classify_complexity(0.3)
        assert level == ComplexityLevel.SIMPLE

    def test_classify_complexity_simple_upper_bound(self):
        """Test classification of simple complexity at upper bound."""
        level = classify_complexity(0.49)
        assert level == ComplexityLevel.SIMPLE

    def test_classify_complexity_moderate_lower_bound(self):
        """Test classification of moderate complexity at lower bound."""
        level = classify_complexity(0.5)
        assert level == ComplexityLevel.MODERATE

    def test_classify_complexity_moderate_upper_bound(self):
        """Test classification of moderate complexity at upper bound."""
        level = classify_complexity(0.69)
        assert level == ComplexityLevel.MODERATE

    def test_classify_complexity_complex_lower_bound(self):
        """Test classification of complex complexity at lower bound."""
        level = classify_complexity(0.7)
        assert level == ComplexityLevel.COMPLEX

    def test_classify_complexity_complex_upper_bound(self):
        """Test classification of complex complexity at upper bound."""
        level = classify_complexity(0.89)
        assert level == ComplexityLevel.COMPLEX

    def test_classify_complexity_critical_lower_bound(self):
        """Test classification of critical complexity at lower bound."""
        level = classify_complexity(0.9)
        assert level == ComplexityLevel.CRITICAL

    def test_classify_complexity_critical_upper_bound(self):
        """Test classification of critical complexity at upper bound."""
        level = classify_complexity(1.0)
        assert level == ComplexityLevel.CRITICAL

    def test_classify_complexity_boundary_values(self):
        """Test classification at exact boundary values."""
        assert classify_complexity(0.299) == ComplexityLevel.TRIVIAL
        assert classify_complexity(0.3) == ComplexityLevel.SIMPLE
        assert classify_complexity(0.499) == ComplexityLevel.SIMPLE
        assert classify_complexity(0.5) == ComplexityLevel.MODERATE
        assert classify_complexity(0.699) == ComplexityLevel.MODERATE
        assert classify_complexity(0.7) == ComplexityLevel.COMPLEX
        assert classify_complexity(0.899) == ComplexityLevel.COMPLEX
        assert classify_complexity(0.9) == ComplexityLevel.CRITICAL


class TestModelTierSelection:
    """Test model tier selection for different agents and complexity."""

    def test_select_model_tier_witness_default(self):
        """Test default tier selection for witness agent."""
        tier = select_model_tier("witness")
        assert tier == ModelTier.LOCAL_FAST

    def test_select_model_tier_architect_default(self):
        """Test default tier selection for architect agent."""
        tier = select_model_tier("architect")
        assert tier == ModelTier.LOCAL_ADVANCED

    def test_select_model_tier_executor_default(self):
        """Test default tier selection for executor agent."""
        tier = select_model_tier("executor")
        assert tier == ModelTier.CLOUD_STANDARD

    def test_select_model_tier_unknown_agent_default(self):
        """Test default tier for unknown agent falls back to cloud standard."""
        tier = select_model_tier("unknown_agent")
        assert tier == ModelTier.CLOUD_STANDARD

    def test_select_model_tier_critical_complexity_escalates_to_premium(self):
        """Test critical complexity escalates to cloud premium."""
        tier = select_model_tier("witness", complexity=0.95)
        assert tier == ModelTier.CLOUD_PREMIUM

    def test_select_model_tier_complex_complexity_escalates_to_standard(self):
        """Test complex complexity escalates to cloud standard."""
        tier = select_model_tier("witness", complexity=0.75)
        assert tier == ModelTier.CLOUD_STANDARD

    def test_select_model_tier_moderate_complexity_escalates_local_agent(self):
        """Test moderate complexity escalates local agent to local advanced."""
        tier = select_model_tier("witness", complexity=0.6)
        assert tier == ModelTier.LOCAL_ADVANCED

    def test_select_model_tier_moderate_complexity_keeps_cloud_agent(self):
        """Test moderate complexity keeps cloud agent at default tier."""
        tier = select_model_tier("executor", complexity=0.6)
        assert tier == ModelTier.CLOUD_STANDARD

    def test_select_model_tier_simple_complexity_keeps_default(self):
        """Test simple complexity keeps default tier."""
        witness_tier = select_model_tier("witness", complexity=0.4)
        executor_tier = select_model_tier("executor", complexity=0.4)
        assert witness_tier == ModelTier.LOCAL_FAST
        assert executor_tier == ModelTier.CLOUD_STANDARD

    def test_select_model_tier_trivial_complexity_keeps_default(self):
        """Test trivial complexity keeps default tier."""
        tier = select_model_tier("witness", complexity=0.1)
        assert tier == ModelTier.LOCAL_FAST

    def test_select_model_tier_force_cloud_overrides_default(self):
        """Test force_cloud overrides default tier selection."""
        tier = select_model_tier("witness", force_cloud=True)
        assert tier == ModelTier.CLOUD_STANDARD

    def test_select_model_tier_force_cloud_overrides_complexity(self):
        """Test force_cloud overrides complexity-based escalation."""
        tier = select_model_tier("witness", complexity=0.1, force_cloud=True)
        assert tier == ModelTier.CLOUD_STANDARD

    def test_select_model_tier_force_local_keeps_local_agent(self):
        """Test force_local keeps local agent at its tier."""
        tier = select_model_tier("witness", force_local=True)
        assert tier == ModelTier.LOCAL_FAST

    def test_select_model_tier_force_local_downgrades_cloud_agent(self):
        """Test force_local downgrades cloud agent to local advanced."""
        tier = select_model_tier("executor", force_local=True)
        assert tier == ModelTier.LOCAL_ADVANCED

    def test_select_model_tier_force_cloud_takes_precedence_over_local(self):
        """Test force_cloud takes precedence over force_local."""
        tier = select_model_tier("witness", force_local=True, force_cloud=True)
        assert tier == ModelTier.CLOUD_STANDARD

    def test_select_model_tier_no_complexity_uses_default(self):
        """Test None complexity uses default tier without escalation."""
        tier = select_model_tier("witness", complexity=None)
        assert tier == ModelTier.LOCAL_FAST


class TestGetModelForAgent:
    """Test model name retrieval for agents."""

    def test_get_model_for_agent_witness_returns_local_fast(self):
        """Test witness agent returns local fast model."""
        model = get_model_for_agent("witness")
        assert model == "qwen2.5-coder:1.5b"

    def test_get_model_for_agent_architect_returns_local_advanced(self):
        """Test architect agent returns local advanced model."""
        model = get_model_for_agent("architect")
        assert model == "codestral-22b"

    def test_get_model_for_agent_executor_returns_cloud_standard(self):
        """Test executor agent returns cloud standard model."""
        model = get_model_for_agent("executor")
        assert model == "gpt-5"

    def test_get_model_for_agent_with_critical_complexity(self):
        """Test agent with critical complexity returns cloud premium model."""
        model = get_model_for_agent("witness", complexity=0.95)
        assert model == "claude-sonnet-4.5"

    def test_get_model_for_agent_with_complex_complexity(self):
        """Test agent with complex complexity returns cloud standard model."""
        model = get_model_for_agent("witness", complexity=0.75)
        assert model == "gpt-5"

    def test_get_model_for_agent_force_cloud(self):
        """Test force_cloud returns cloud standard model."""
        model = get_model_for_agent("witness", force_cloud=True)
        assert model == "gpt-5"

    def test_get_model_for_agent_force_local(self):
        """Test force_local returns local model."""
        model = get_model_for_agent("executor", force_local=True)
        assert model == "codestral-22b"

    def test_get_model_for_agent_legacy_agency_agent_planner(self):
        """Test legacy agency agent (planner) returns correct model."""
        model = get_model_for_agent("planner")
        # Should use AGENCY_AGENT_MODELS, which checks PLANNER_MODEL env or defaults to gpt-5
        assert model == os.getenv("PLANNER_MODEL", "gpt-5")

    def test_get_model_for_agent_legacy_agency_agent_coder(self):
        """Test legacy agency agent (coder) returns correct model."""
        model = get_model_for_agent("coder")
        assert model == os.getenv("CODER_MODEL", "gpt-5")

    def test_get_model_for_agent_legacy_agency_agent_summary(self):
        """Test legacy agency agent (summary) returns correct model."""
        model = get_model_for_agent("summary")
        assert model == os.getenv("SUMMARY_MODEL", "gpt-5-mini")

    @patch.dict(os.environ, {"WITNESS_MODEL": "custom-model"})
    def test_get_model_for_agent_env_override(self):
        """Test environment variable override for Trinity agent."""
        model = get_model_for_agent("witness")
        assert model == "custom-model"

    @patch.dict(os.environ, {"WITNESS_MODEL": "custom-model"})
    def test_get_model_for_agent_env_override_disabled(self):
        """Test environment variable override can be disabled."""
        model = get_model_for_agent("witness", use_env_override=False)
        assert model == "qwen2.5-coder:1.5b"

    @patch.dict(os.environ, {"ARCHITECT_MODEL": "gpt-5"})
    def test_get_model_for_agent_env_override_with_complexity(self):
        """Test environment variable override takes precedence over complexity."""
        model = get_model_for_agent("architect", complexity=0.95)
        assert model == "gpt-5"  # Env override, not claude-sonnet-4.5

    def test_get_model_for_agent_trinity_plan_alias(self):
        """Test 'plan' alias for architect agent."""
        model = get_model_for_agent("plan")
        assert model == "codestral-22b"

    def test_get_model_for_agent_trinity_execute_alias(self):
        """Test 'execute' alias for executor agent."""
        model = get_model_for_agent("execute")
        assert model == "gpt-5"

    def test_get_model_for_agent_trinity_auditlearn(self):
        """Test auditlearn agent returns local fast model."""
        model = get_model_for_agent("auditlearn")
        assert model == "qwen2.5-coder:1.5b"


class TestShouldUseLocal:
    """Test local model determination."""

    def test_should_use_local_witness_agent(self):
        """Test witness agent should use local model."""
        assert should_use_local("witness") is True

    def test_should_use_local_architect_agent(self):
        """Test architect agent should use local model."""
        assert should_use_local("architect") is True

    def test_should_use_local_executor_agent(self):
        """Test executor agent should not use local model."""
        assert should_use_local("executor") is False

    def test_should_use_local_witness_with_critical_complexity(self):
        """Test witness with critical complexity should not use local model."""
        assert should_use_local("witness", complexity=0.95) is False

    def test_should_use_local_witness_with_complex_complexity(self):
        """Test witness with complex complexity should not use local model."""
        assert should_use_local("witness", complexity=0.75) is False

    def test_should_use_local_witness_with_moderate_complexity(self):
        """Test witness with moderate complexity escalates to local advanced."""
        assert should_use_local("witness", complexity=0.6) is True

    def test_should_use_local_witness_with_simple_complexity(self):
        """Test witness with simple complexity uses local model."""
        assert should_use_local("witness", complexity=0.4) is True

    def test_should_use_local_executor_with_simple_complexity(self):
        """Test executor with simple complexity still uses cloud model."""
        assert should_use_local("executor", complexity=0.4) is False

    def test_should_use_local_unknown_agent_defaults_to_cloud(self):
        """Test unknown agent defaults to cloud model."""
        assert should_use_local("unknown_agent") is False


class TestBackwardCompatibility:
    """Test backward compatibility with original model_policy.py."""

    def test_agent_model_planner(self):
        """Test agent_model function for planner agent."""
        model = agent_model("planner")
        assert model == os.getenv("PLANNER_MODEL", "gpt-5")

    def test_agent_model_chief_architect(self):
        """Test agent_model function for chief_architect agent."""
        model = agent_model("chief_architect")
        assert model == os.getenv("CHIEF_ARCHITECT_MODEL", "gpt-5")

    def test_agent_model_coder(self):
        """Test agent_model function for coder agent."""
        model = agent_model("coder")
        assert model == os.getenv("CODER_MODEL", "gpt-5")

    def test_agent_model_auditor(self):
        """Test agent_model function for auditor agent."""
        model = agent_model("auditor")
        assert model == os.getenv("AUDITOR_MODEL", "gpt-5")

    def test_agent_model_quality_enforcer(self):
        """Test agent_model function for quality_enforcer agent."""
        model = agent_model("quality_enforcer")
        assert model == os.getenv("QUALITY_ENFORCER_MODEL", "gpt-5")

    def test_agent_model_merger(self):
        """Test agent_model function for merger agent."""
        model = agent_model("merger")
        assert model == os.getenv("MERGER_MODEL", "gpt-5")

    def test_agent_model_learning(self):
        """Test agent_model function for learning agent."""
        model = agent_model("learning")
        assert model == os.getenv("LEARNING_MODEL", "gpt-5")

    def test_agent_model_test_generator(self):
        """Test agent_model function for test_generator agent."""
        model = agent_model("test_generator")
        assert model == os.getenv("TEST_GENERATOR_MODEL", "gpt-5")

    def test_agent_model_summary(self):
        """Test agent_model function for summary agent."""
        model = agent_model("summary")
        assert model == os.getenv("SUMMARY_MODEL", "gpt-5-mini")

    def test_agent_model_toolsmith(self):
        """Test agent_model function for toolsmith agent."""
        model = agent_model("toolsmith")
        assert model == os.getenv("TOOLSMITH_MODEL", "gpt-5")

    def test_agent_model_unknown_agent_uses_global_default(self):
        """Test agent_model function for unknown agent uses global default."""
        model = agent_model("unknown_agent")
        assert model == os.getenv("AGENCY_MODEL", "gpt-5")

    @patch.dict(os.environ, {"AGENCY_MODEL": "custom-global-model"})
    def test_agent_model_unknown_agent_uses_custom_global_default(self):
        """Test agent_model function respects AGENCY_MODEL env variable."""
        model = agent_model("unknown_agent")
        assert model == "custom-global-model"

    def test_agent_model_respects_agent_specific_env_override(self):
        """Test agent_model function respects agent-specific env variable."""
        # Note: AGENCY_AGENT_MODELS is evaluated at module import time,
        # so this test verifies the structure rather than runtime override
        with patch.dict(os.environ, {"CODER_MODEL": "custom-coder-model"}, clear=False):
            # Re-import to pick up env var at module load time
            import importlib
            import shared.model_policy_enhanced
            importlib.reload(shared.model_policy_enhanced)
            from shared.model_policy_enhanced import agent_model as reloaded_agent_model
            model = reloaded_agent_model("coder")
            assert model == "custom-coder-model"
            # Reload again to restore original state
            importlib.reload(shared.model_policy_enhanced)


class TestConstants:
    """Test module constants are properly defined."""

    def test_tier_models_contains_all_tiers(self):
        """Test TIER_MODELS contains all ModelTier values."""
        expected_tiers = {
            ModelTier.LOCAL_FAST,
            ModelTier.LOCAL_STANDARD,
            ModelTier.LOCAL_ADVANCED,
            ModelTier.CLOUD_STANDARD,
            ModelTier.CLOUD_PREMIUM,
        }
        assert set(TIER_MODELS.keys()) == expected_tiers

    def test_tier_models_has_correct_values(self):
        """Test TIER_MODELS maps to correct model names."""
        assert TIER_MODELS[ModelTier.LOCAL_FAST] == "qwen2.5-coder:1.5b"
        assert TIER_MODELS[ModelTier.LOCAL_STANDARD] == "qwen2.5-coder:7b"
        assert TIER_MODELS[ModelTier.LOCAL_ADVANCED] == "codestral-22b"
        assert TIER_MODELS[ModelTier.CLOUD_STANDARD] == "gpt-5"
        assert TIER_MODELS[ModelTier.CLOUD_PREMIUM] == "claude-sonnet-4.5"

    def test_trinity_agent_tiers_contains_all_agents(self):
        """Test TRINITY_AGENT_TIERS contains all Trinity agents."""
        expected_agents = {"witness", "auditlearn", "architect", "plan", "executor", "execute"}
        assert set(TRINITY_AGENT_TIERS.keys()) == expected_agents

    def test_trinity_agent_tiers_has_correct_defaults(self):
        """Test TRINITY_AGENT_TIERS maps to correct default tiers."""
        assert TRINITY_AGENT_TIERS["witness"] == ModelTier.LOCAL_FAST
        assert TRINITY_AGENT_TIERS["auditlearn"] == ModelTier.LOCAL_FAST
        assert TRINITY_AGENT_TIERS["architect"] == ModelTier.LOCAL_ADVANCED
        assert TRINITY_AGENT_TIERS["plan"] == ModelTier.LOCAL_ADVANCED
        assert TRINITY_AGENT_TIERS["executor"] == ModelTier.CLOUD_STANDARD
        assert TRINITY_AGENT_TIERS["execute"] == ModelTier.CLOUD_STANDARD

    def test_agency_agent_models_contains_all_agents(self):
        """Test AGENCY_AGENT_MODELS contains all legacy agents."""
        expected_agents = {
            "planner", "chief_architect", "coder", "auditor", "quality_enforcer",
            "merger", "learning", "test_generator", "summary", "toolsmith"
        }
        assert set(AGENCY_AGENT_MODELS.keys()) == expected_agents

    def test_agency_agent_models_respects_env_variables(self):
        """Test AGENCY_AGENT_MODELS reads from environment variables."""
        # This test verifies the structure, actual env vars are tested elsewhere
        for agent_key in AGENCY_AGENT_MODELS.keys():
            model = AGENCY_AGENT_MODELS[agent_key]
            assert isinstance(model, str)
            assert len(model) > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_assess_complexity_with_empty_keywords_list(self):
        """Test complexity assessment with empty keywords list."""
        score = assess_complexity(
            task_description="Simple task",
            keywords=[],
            scope="single-file",
            priority="NORMAL"
        )
        assert score == 0.1

    def test_assess_complexity_with_none_keywords(self):
        """Test complexity assessment with None keywords."""
        score = assess_complexity(
            task_description="Simple task",
            keywords=None,
            scope="single-file",
            priority="NORMAL"
        )
        assert score == 0.1

    def test_assess_complexity_with_empty_task_description(self):
        """Test complexity assessment with empty task description."""
        score = assess_complexity(
            task_description="",
            keywords=["architecture"],
            scope="single-file",
            priority="NORMAL"
        )
        # Keywords won't match empty description
        assert score == 0.1

    def test_assess_complexity_with_very_long_task_description(self):
        """Test complexity assessment with very long task description."""
        long_description = "architecture " * 1000
        score = assess_complexity(
            task_description=long_description,
            keywords=["architecture"],
            scope="single-file",
            priority="NORMAL"
        )
        # Should match keyword once and add weight once
        assert abs(score - 0.3) < 0.001

    def test_select_model_tier_with_zero_complexity(self):
        """Test tier selection with exactly zero complexity."""
        tier = select_model_tier("witness", complexity=0.0)
        assert tier == ModelTier.LOCAL_FAST

    def test_select_model_tier_with_max_complexity(self):
        """Test tier selection with maximum complexity."""
        tier = select_model_tier("witness", complexity=1.0)
        assert tier == ModelTier.CLOUD_PREMIUM

    def test_get_model_for_agent_with_both_force_flags_true(self):
        """Test get_model_for_agent with both force flags (cloud wins)."""
        model = get_model_for_agent("witness", force_local=True, force_cloud=True)
        assert model == "gpt-5"  # force_cloud takes precedence

    @patch.dict(os.environ, {}, clear=True)
    def test_get_model_for_agent_with_no_env_variables(self):
        """Test get_model_for_agent works without any env variables."""
        model = get_model_for_agent("witness")
        assert model == "qwen2.5-coder:1.5b"

    @patch.dict(os.environ, {"NONEXISTENT_AGENT_MODEL": "some-model"})
    def test_get_model_for_agent_ignores_unrelated_env_variables(self):
        """Test get_model_for_agent ignores unrelated env variables."""
        model = get_model_for_agent("witness")
        assert model == "qwen2.5-coder:1.5b"


class TestComplexityLevels:
    """Test ComplexityLevel enum values."""

    def test_complexity_level_trivial_value(self):
        """Test TRIVIAL complexity level has correct value."""
        assert ComplexityLevel.TRIVIAL.value == "trivial"

    def test_complexity_level_simple_value(self):
        """Test SIMPLE complexity level has correct value."""
        assert ComplexityLevel.SIMPLE.value == "simple"

    def test_complexity_level_moderate_value(self):
        """Test MODERATE complexity level has correct value."""
        assert ComplexityLevel.MODERATE.value == "moderate"

    def test_complexity_level_complex_value(self):
        """Test COMPLEX complexity level has correct value."""
        assert ComplexityLevel.COMPLEX.value == "complex"

    def test_complexity_level_critical_value(self):
        """Test CRITICAL complexity level has correct value."""
        assert ComplexityLevel.CRITICAL.value == "critical"

    def test_complexity_level_is_string_enum(self):
        """Test ComplexityLevel is a string enum."""
        assert isinstance(ComplexityLevel.TRIVIAL, str)
        assert isinstance(ComplexityLevel.CRITICAL, str)


class TestModelTiers:
    """Test ModelTier enum values."""

    def test_model_tier_local_fast_value(self):
        """Test LOCAL_FAST tier has correct value."""
        assert ModelTier.LOCAL_FAST.value == "local_fast"

    def test_model_tier_local_standard_value(self):
        """Test LOCAL_STANDARD tier has correct value."""
        assert ModelTier.LOCAL_STANDARD.value == "local_standard"

    def test_model_tier_local_advanced_value(self):
        """Test LOCAL_ADVANCED tier has correct value."""
        assert ModelTier.LOCAL_ADVANCED.value == "local_advanced"

    def test_model_tier_cloud_standard_value(self):
        """Test CLOUD_STANDARD tier has correct value."""
        assert ModelTier.CLOUD_STANDARD.value == "cloud_standard"

    def test_model_tier_cloud_premium_value(self):
        """Test CLOUD_PREMIUM tier has correct value."""
        assert ModelTier.CLOUD_PREMIUM.value == "cloud_premium"

    def test_model_tier_is_string_enum(self):
        """Test ModelTier is a string enum."""
        assert isinstance(ModelTier.LOCAL_FAST, str)
        assert isinstance(ModelTier.CLOUD_PREMIUM, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
