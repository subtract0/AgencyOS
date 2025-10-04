"""
Enhanced Model Policy for Trinity Protocol

Provides complexity-based routing between local and cloud models.
Extends existing model_policy.py with hybrid intelligence support.

Routing Logic:
- Simple/routine tasks: Local models (qwen, codestral)
- Complex/critical tasks: Cloud models (gpt-5, claude-4.1)
- Automatic escalation based on complexity score

Constitutional Compliance:
- Article I: Complete context - retry on failures
- Hybrid Doctrine: Cost-efficient local default, quality escalation
"""

import os
from enum import Enum
from typing import Literal


class ModelTier(str, Enum):
    """Model tier for routing decisions."""

    LOCAL_FAST = "local_fast"  # qwen2.5-coder:1.5b (detection)
    LOCAL_STANDARD = "local_standard"  # qwen2.5-coder:7b (execution)
    LOCAL_ADVANCED = "local_advanced"  # codestral-22b (planning)
    CLOUD_STANDARD = "cloud_standard"  # gpt-5
    CLOUD_PREMIUM = "cloud_premium"  # claude-4.1, o3


class ComplexityLevel(str, Enum):
    """Task complexity classification."""

    TRIVIAL = "trivial"  # 0.0-0.3: Pattern detection, simple classification
    SIMPLE = "simple"  # 0.3-0.5: Single-file changes, bug fixes
    MODERATE = "moderate"  # 0.5-0.7: Multi-file refactors, feature additions
    COMPLEX = "complex"  # 0.7-0.9: Architectural changes, system-wide refactors
    CRITICAL = "critical"  # 0.9-1.0: Critical failures, security issues


# Model mapping per tier
TIER_MODELS: dict[ModelTier, str] = {
    ModelTier.LOCAL_FAST: "qwen2.5-coder:1.5b",
    ModelTier.LOCAL_STANDARD: "qwen2.5-coder:7b",
    ModelTier.LOCAL_ADVANCED: "codestral-22b",
    ModelTier.CLOUD_STANDARD: "gpt-5",
    ModelTier.CLOUD_PREMIUM: "claude-sonnet-4.5",
}


# Trinity agent to default tier mapping
TRINITY_AGENT_TIERS: dict[str, ModelTier] = {
    "witness": ModelTier.LOCAL_FAST,  # High-frequency detection
    "auditlearn": ModelTier.LOCAL_FAST,  # Pattern classification
    "architect": ModelTier.LOCAL_ADVANCED,  # Strategic planning (escalates on complexity)
    "plan": ModelTier.LOCAL_ADVANCED,  # Same as architect
    "executor": ModelTier.CLOUD_STANDARD,  # Meta-orchestration (Claude Sonnet preferred)
    "execute": ModelTier.CLOUD_STANDARD,  # Same as executor
}


# Existing Agency agents (from original model_policy.py)
AGENCY_AGENT_MODELS: dict[str, str] = {
    "planner": os.getenv("PLANNER_MODEL", "gpt-5"),
    "chief_architect": os.getenv("CHIEF_ARCHITECT_MODEL", "gpt-5"),
    "coder": os.getenv("CODER_MODEL", "gpt-5"),
    "auditor": os.getenv("AUDITOR_MODEL", "gpt-5"),
    "quality_enforcer": os.getenv("QUALITY_ENFORCER_MODEL", "gpt-5"),
    "merger": os.getenv("MERGER_MODEL", "gpt-5"),
    "learning": os.getenv("LEARNING_MODEL", "gpt-5"),
    "test_generator": os.getenv("TEST_GENERATOR_MODEL", "gpt-5"),
    "summary": os.getenv("SUMMARY_MODEL", "gpt-5-mini"),
    "toolsmith": os.getenv("TOOLSMITH_MODEL", "gpt-5"),
}


def assess_complexity(
    task_description: str,
    keywords: list[str] | None = None,
    scope: Literal["single-file", "multi-file", "architecture", "system-wide"] = "single-file",
    priority: Literal["NORMAL", "HIGH", "CRITICAL"] = "NORMAL",
    evidence_count: int = 1,
) -> float:
    """
    Assess task complexity for routing decisions.

    Args:
        task_description: Description of the task
        keywords: Optional keywords from task
        scope: Scope of changes required
        priority: Task priority
        evidence_count: Number of supporting evidence samples

    Returns:
        Complexity score 0.0-1.0
    """
    score = 0.0

    # Priority contributes significantly
    if priority == "CRITICAL":
        score += 0.5
    elif priority == "HIGH":
        score += 0.3

    # Scope determines base complexity
    scope_scores = {"single-file": 0.1, "multi-file": 0.3, "architecture": 0.5, "system-wide": 0.7}
    score += scope_scores.get(scope, 0.1)

    # Keywords indicate specific complexity types
    if keywords:
        keyword_weights = {
            "architecture": 0.2,
            "refactor": 0.15,
            "security": 0.2,
            "constitutional_violation": 0.15,
            "system-wide": 0.2,
            "critical": 0.2,
            "performance": 0.1,
            "multi-agent": 0.15,
        }

        task_lower = task_description.lower()
        for keyword in keywords:
            kw_lower = keyword.lower()
            if kw_lower in task_lower:
                score += keyword_weights.get(kw_lower, 0.05)

    # Evidence count can reduce uncertainty
    if evidence_count >= 5:
        score += 0.05

    return min(1.0, score)


def classify_complexity(score: float) -> ComplexityLevel:
    """
    Classify complexity score into level.

    Args:
        score: Complexity score 0.0-1.0

    Returns:
        ComplexityLevel enum
    """
    if score >= 0.9:
        return ComplexityLevel.CRITICAL
    elif score >= 0.7:
        return ComplexityLevel.COMPLEX
    elif score >= 0.5:
        return ComplexityLevel.MODERATE
    elif score >= 0.3:
        return ComplexityLevel.SIMPLE
    else:
        return ComplexityLevel.TRIVIAL


def select_model_tier(
    agent_key: str,
    complexity: float | None = None,
    force_local: bool = False,
    force_cloud: bool = False,
) -> ModelTier:
    """
    Select appropriate model tier for agent and task.

    Args:
        agent_key: Agent identifier (witness, architect, executor, etc.)
        complexity: Optional complexity score for escalation
        force_local: Force local model selection
        force_cloud: Force cloud model selection

    Returns:
        ModelTier to use
    """
    # Handle forced selection
    if force_cloud:
        return ModelTier.CLOUD_STANDARD

    if force_local:
        default_tier = TRINITY_AGENT_TIERS.get(agent_key, ModelTier.LOCAL_STANDARD)
        if default_tier in [ModelTier.CLOUD_STANDARD, ModelTier.CLOUD_PREMIUM]:
            return ModelTier.LOCAL_ADVANCED
        return default_tier

    # Get agent's default tier
    default_tier = TRINITY_AGENT_TIERS.get(agent_key, ModelTier.CLOUD_STANDARD)

    # No complexity assessment - use default
    if complexity is None:
        return default_tier

    # Complexity-based escalation
    complexity_level = classify_complexity(complexity)

    if complexity_level == ComplexityLevel.CRITICAL:
        return ModelTier.CLOUD_PREMIUM
    elif complexity_level == ComplexityLevel.COMPLEX:
        return ModelTier.CLOUD_STANDARD
    elif complexity_level == ComplexityLevel.MODERATE:
        # Escalate from local if agent defaults to local
        if default_tier in [ModelTier.LOCAL_FAST, ModelTier.LOCAL_STANDARD]:
            return ModelTier.LOCAL_ADVANCED
        return default_tier
    else:
        # Simple/trivial - keep local if possible
        return default_tier


def get_model_for_agent(
    agent_key: str,
    complexity: float | None = None,
    force_local: bool = False,
    force_cloud: bool = False,
    use_env_override: bool = True,
) -> str:
    """
    Get model name for agent with complexity-based routing.

    Args:
        agent_key: Agent identifier
        complexity: Optional complexity score
        force_local: Force local model
        force_cloud: Force cloud model
        use_env_override: Check environment variables for overrides

    Returns:
        Model name string
    """
    # Check for legacy Agency agent first
    if agent_key in AGENCY_AGENT_MODELS:
        return AGENCY_AGENT_MODELS[agent_key]

    # Check for direct env override
    if use_env_override:
        env_var = f"{agent_key.upper()}_MODEL"
        override = os.getenv(env_var)
        if override:
            return override

    # Select tier based on complexity
    tier = select_model_tier(
        agent_key=agent_key, complexity=complexity, force_local=force_local, force_cloud=force_cloud
    )

    return TIER_MODELS[tier]


def should_use_local(agent_key: str, complexity: float | None = None) -> bool:
    """
    Determine if local model should be used.

    Args:
        agent_key: Agent identifier
        complexity: Optional complexity score

    Returns:
        True if local model is appropriate
    """
    tier = select_model_tier(agent_key, complexity)
    return tier in [ModelTier.LOCAL_FAST, ModelTier.LOCAL_STANDARD, ModelTier.LOCAL_ADVANCED]


# Backward compatibility with original model_policy.py
def agent_model(agent_key: str) -> str:
    """
    Legacy function for backward compatibility.

    Returns model name for agent using original policy.
    """
    return AGENCY_AGENT_MODELS.get(agent_key, os.getenv("AGENCY_MODEL", "gpt-5"))
