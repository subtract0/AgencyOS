"""
LLM Cost Tracking Wrapper

Monkey-patches OpenAI client to automatically track token usage and costs.
Works transparently with Agency Swarm agents.

Usage:
    from shared.llm_cost_wrapper import wrap_openai_client
    from trinity_protocol.cost_tracker import CostTracker

    tracker = CostTracker()
    wrap_openai_client(tracker, agent_name="AgencyOSAgent")
"""

import functools
import time
from typing import Any

from shared.cost_tracker import CostTracker, ModelTier


def determine_model_tier(model: str) -> ModelTier:
    """
    Determine pricing tier from model name.

    Args:
        model: Model identifier (e.g., "gpt-5", "gpt-4o-mini")

    Returns:
        ModelTier enum value
    """
    model_lower = model.lower()

    # Local models
    if "ollama" in model_lower or "local" in model_lower:
        return ModelTier.LOCAL

    # Premium models (GPT-5, Claude Opus)
    if "gpt-5" in model_lower or "opus" in model_lower:
        return ModelTier.CLOUD_PREMIUM

    # Mini models
    if "mini" in model_lower or "haiku" in model_lower:
        return ModelTier.CLOUD_MINI

    # Standard models (GPT-4, Claude Sonnet)
    return ModelTier.CLOUD_STANDARD


def wrap_openai_client(
    cost_tracker: CostTracker,
    agent_name: str,
    task_id: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """
    Monkey-patch OpenAI client to track costs automatically.

    This wraps the chat.completions.create method to extract token counts
    from API responses and log them to the CostTracker.

    Args:
        cost_tracker: CostTracker instance to use
        agent_name: Name of the agent making calls
        task_id: Optional task identifier
        correlation_id: Optional correlation identifier

    Example:
        >>> tracker = CostTracker()
        >>> wrap_openai_client(tracker, "AgencyOSAgent")
        >>> # All subsequent OpenAI calls will be tracked
    """
    from openai.resources.chat import Completions

    # Get the original method from the Completions class
    original_create = Completions.create

    @functools.wraps(original_create)
    def wrapped_create(self: Any, *args: Any, **kwargs: Any) -> Any:
        """Wrapped completion method with cost tracking."""
        start_time = time.time()
        error_msg: str | None = None
        success = True

        try:
            # Make the original API call
            response = original_create(self, *args, **kwargs)

            # Extract token counts from response
            usage = getattr(response, "usage", None)
            model = getattr(response, "model", "unknown")

            if usage:
                input_tokens = getattr(usage, "prompt_tokens", 0)
                output_tokens = getattr(usage, "completion_tokens", 0)

                # Determine pricing tier
                tier = determine_model_tier(model)

                # Track the call
                duration = time.time() - start_time
                metadata: dict[str, str] = {}
                if task_id:
                    metadata["task_id"] = task_id
                if correlation_id:
                    metadata["correlation_id"] = correlation_id

                cost_tracker.track(
                    operation=agent_name,
                    model=model,
                    model_tier=tier,
                    tokens_in=input_tokens,
                    tokens_out=output_tokens,
                    duration_seconds=duration,
                    success=True,
                    metadata=metadata if metadata else None,
                )

            return response

        except Exception as e:
            success = False
            error_msg = str(e)

            # Track failed call
            duration = time.time() - start_time
            model = kwargs.get("model", "unknown")
            tier = determine_model_tier(model)

            metadata: dict[str, str] = {}
            if task_id:
                metadata["task_id"] = task_id
            if correlation_id:
                metadata["correlation_id"] = correlation_id

            cost_tracker.track(
                operation=agent_name,
                model=model,
                model_tier=tier,
                tokens_in=0,
                tokens_out=0,
                duration_seconds=duration,
                success=False,
                metadata=metadata if metadata else None,
                error=error_msg,
            )

            raise

    # Replace the method on the Completions class
    Completions.create = wrapped_create  # type: ignore


def wrap_agent_with_cost_tracking(
    agent: Any,
    cost_tracker: CostTracker,
    task_id: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """
    Wrap an Agency Swarm agent to track all LLM costs.

    Args:
        agent: Agent instance to wrap
        cost_tracker: CostTracker instance
        task_id: Optional task ID
        correlation_id: Optional correlation ID

    Example:
        >>> from agencyos_agent import create_agencyos_agent
        >>> from shared.cost_tracker import CostTracker
        >>>
        >>> tracker = CostTracker()
        >>> agent = create_agencyos_agent()
        >>> wrap_agent_with_cost_tracking(agent, tracker)
    """
    agent_name = getattr(agent, "name", agent.__class__.__name__)
    wrap_openai_client(cost_tracker, agent_name, task_id, correlation_id)


def create_cost_tracking_context(
    cost_tracker: CostTracker,
    agent_name: str,
    task_id: str | None = None,
    correlation_id: str | None = None,
):
    """
    Context manager for temporary cost tracking.

    Enables cost tracking within a specific code block, then restores
    the original OpenAI client behavior.

    Args:
        cost_tracker: CostTracker instance
        agent_name: Agent name
        task_id: Optional task ID
        correlation_id: Optional correlation ID

    Example:
        >>> tracker = CostTracker()
        >>> with create_cost_tracking_context(tracker, "TestAgent"):
        ...     # Make LLM calls here
        ...     client = OpenAI()
        ...     response = client.chat.completions.create(...)
    """
    import contextlib

    from openai.resources.chat import Completions

    @contextlib.contextmanager
    def _context():
        # Save original method
        original_create = Completions.create

        try:
            # Enable tracking
            wrap_openai_client(cost_tracker, agent_name, task_id, correlation_id)
            yield
        finally:
            # Restore original
            Completions.create = original_create

    return _context()
