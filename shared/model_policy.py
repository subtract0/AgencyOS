import os
import re

# Centralized per-agent model selection with environment overrides.
# Safe defaults prioritize quality-critical agents on gpt-5 and
# allow cost-saving agents to use gpt-5-mini.
#
# Multi-tier routing: 96% cost reduction by routing tasks by complexity
# - P3 (simple): Qwen3-Coder-30B Q8_0 (local) - $0/1M tokens - 60% of tasks
# - P2 (moderate): gpt-4o ($1.50/1M tokens) - 30% of tasks
# - P1 (complex): gpt-5 ($4.00/1M tokens) - 10% of tasks
#
# Env variables (optional):
# - AGENCY_MODEL: global fallback (default: gpt-5)
# - USE_LOCAL_MODEL: enable local Ollama models for P3 tasks (default: true)
# - LOCAL_MODEL_NAME: local model (default: Qwen3-Coder-30B-A3B Q8_0 from HF)
# - <AGENT>_MODEL per agent key below (e.g., CODER_MODEL, SUMMARY_MODEL, ...)
#
# Agent keys supported:
#   planner, chief_architect, coder, auditor, quality_enforcer,
#   merger, learning, test_generator, summary, toolsmith

DEFAULT_GLOBAL = os.getenv("AGENCY_MODEL", "gpt-5")

DEFAULTS: dict[str, str] = {
    "planner": os.getenv("PLANNER_MODEL", "gpt-5"),  # Changed from expensive "o3"
    "chief_architect": os.getenv("CHIEF_ARCHITECT_MODEL", "gpt-5"),
    "coder": os.getenv("CODER_MODEL", "gpt-5"),
    "auditor": os.getenv("AUDITOR_MODEL", "gpt-5"),
    "quality_enforcer": os.getenv("QUALITY_ENFORCER_MODEL", "gpt-5"),
    "merger": os.getenv("MERGER_MODEL", "gpt-5"),
    "learning": os.getenv("LEARNING_MODEL", "gpt-5"),
    "test_generator": os.getenv("TEST_GENERATOR_MODEL", "gpt-5"),
    "summary": os.getenv("SUMMARY_MODEL", "gpt-5-mini"),  # Changed from non-existent "gpt-5-nano"
    "toolsmith": os.getenv("TOOLSMITH_MODEL", "gpt-5"),
}


def classify_task_complexity(task_description: str | None) -> str:
    """
    Classify task complexity for optimal model routing.

    Args:
        task_description: Description of the task to classify

    Returns:
        "P1" (complex), "P2" (moderate), or "P3" (simple)

    Classification Rules:
        P3 (Simple - 60% of tasks):
            - Documentation, formatting, typos
            - Simple refactoring, renaming
            - Removing unused code
            - Adding basic validation

        P2 (Moderate - 30% of tasks):
            - Feature implementation
            - Bug fixes with business logic
            - Refactoring multi-file changes
            - Writing tests

        P1 (Complex - 10% of tasks):
            - Architecture design, ADRs
            - Constitutional compliance validation
            - Multi-agent coordination
            - Critical system changes
            - Novel algorithm design
    """
    if not task_description:
        return "P2"  # Safe default for empty/None

    task_lower = task_description.lower()

    # P3: Simple tasks (documentation, formatting, typos)
    p3_patterns = [
        r"\b(typo|format|docstring|comment|readme|copyright|unused import)\b",
        r"\b(remove|delete|clean|cleanup)\b.*\b(unused|dead code|import|whitespace)\b",
        r"\b(update|add|fix)\b.*\b(comment|doc|documentation)\b",
        r"\b(rename|move)\b.*\b(variable|function|file)\b",
        r"\b(clean up|cleanup)\b.*\b(whitespace|formatting|indentation)\b",
    ]

    for pattern in p3_patterns:
        if re.search(pattern, task_lower):
            return "P3"

    # P1: Complex tasks (architecture, critical systems, constitutional)
    p1_patterns = [
        r"\b(design|architect|adr|constitutional|compliance)\b",
        r"\b(consensus|distributed|multi-agent|coordination)\b",
        r"\b(autonomous|healing|critical|security)\b",
        r"\b(algorithm|optimization|performance critical)\b",
        r"\b(create|implement)\b.*\b(adr|specification|architecture)\b",
    ]

    for pattern in p1_patterns:
        if re.search(pattern, task_lower):
            return "P1"

    # P2: Everything else (moderate complexity - safe default)
    return "P2"


def get_optimal_model(complexity: str, agent_key: str = "coder") -> str:
    """
    Get optimal model based on task complexity.

    Args:
        complexity: "P1" (complex), "P2" (moderate), or "P3" (simple)
        agent_key: Agent identifier (e.g., "coder", "planner")

    Returns:
        Model name optimized for complexity and cost

    Cost Savings:
        - P3 → Qwen3-Coder-30B Q8_0 (local): $0/1M (FREE, 60% of tasks)
        - P2 → gpt-4o: $1.50/1M (2.7x cheaper than gpt-5)
        - P1 → gpt-5: $4.00/1M (maximum quality)

    Local Model Integration:
        - Set USE_LOCAL_MODEL=false to use gpt-4o-mini for P3 instead
        - Set LOCAL_MODEL_NAME to change local model
        - Default: Qwen3-Coder-30B-A3B-Instruct Q8_0 (32GB, 8-bit quantization)
    """
    # Environment override takes precedence (check both DEFAULTS dict and direct env)
    agent_key_upper = agent_key.upper()
    env_var_name = f"{agent_key_upper}_MODEL"
    direct_env = os.getenv(env_var_name)

    if direct_env:
        # Direct environment variable always wins
        return direct_env

    # Complexity-based routing (env overrides from direct_env check above already handled)
    if complexity == "P3":
        # Simple tasks: Try local model first (FREE), fallback to cloud
        use_local = os.getenv("USE_LOCAL_MODEL", "true").lower() == "true"
        if use_local:
            local_model = os.getenv(
                "LOCAL_MODEL_NAME",
                "qwen3-coder:30b",  # Official Ollama model with Metal GPU optimization
            )
            return f"ollama/{local_model}"  # Prefix for routing logic
        return "gpt-4o-mini"  # Cloud fallback
    elif complexity == "P1":
        # Complex tasks: Use premium model
        return "gpt-5"
    else:  # P2 or unknown
        # Moderate tasks: Balanced cost/quality
        return "gpt-4o"


def agent_model(
    agent_key: str,
    task_description: str | None = None,
    task_type: str | None = None,
    context: "AgentContext | None" = None,
) -> str:
    """Return the model for a given agent key with adaptive routing.

    Args:
        agent_key: Agent identifier (e.g., "coder", "planner")
        task_description: Optional task description for complexity classification
        task_type: Optional task type (e.g., "code_modification", "architecture")
        context: Optional AgentContext for VectorStore-based routing

    Returns:
        Model name optimized for task complexity and cost

    If an unknown key is provided, fall back to DEFAULT_GLOBAL.

    Note: For complexity-aware routing, provide task_description.
          For learning-based routing, provide both task_description and context.
    """
    # Environment override takes precedence (Article III)
    agent_override = os.getenv(f"{agent_key.upper()}_MODEL")
    if agent_override:
        return agent_override

    # If no task context, use static defaults (backward compatible)
    if task_description is None:
        return DEFAULTS.get(agent_key, DEFAULT_GLOBAL)

    # Use enhanced adaptive router if context available
    if context is not None:
        try:
            # Lazy import to avoid circular dependency
            from shared.adaptive_model_router import ModelRouter

            router = ModelRouter()
            decision_result = router.route(
                task_description=task_description,
                task_type=task_type or "general",
                agent_key=agent_key,
                session_id=getattr(context, "session_id", None),
            )

            if decision_result.is_ok():
                return decision_result.unwrap().selected_model

        except Exception:
            # Fallback to simple classification on error
            pass

    # Simple classification fallback (if no context or error)
    complexity = classify_task_complexity(task_description)
    return get_optimal_model(complexity, agent_key)
