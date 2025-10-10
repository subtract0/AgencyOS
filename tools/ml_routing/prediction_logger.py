"""
Prediction Logger: Query and retrieve prediction logs from VectorStore.

Provides VectorStore integration for prediction retrieval (Article IV).

Constitutional Compliance:
- Article IV: VectorStore integration (predictions retrieved for learning)
- Law #2: Strict typing (typed inputs/outputs)
- Law #5: Result pattern for fallible operations

Author: QualityEnforcer
Date: 2025-10-10
"""

from datetime import datetime

from shared.agent_context import AgentContext
from shared.models.prediction_log import PredictionLog
from shared.type_definitions.result import Err, Ok, Result


def get_predictions(
    context: AgentContext,
    since: datetime,
    tier_filter: str | None = None,
) -> Result[list[PredictionLog], str]:
    """
    Retrieve predictions from VectorStore since given timestamp.

    Queries VectorStore for all prediction logs matching criteria.
    Used for retraining, drift detection, and A/B rollout validation.

    Args:
        context: AgentContext with VectorStore access
        since: Retrieve predictions after this timestamp
        tier_filter: Optional tier filter (P1, P2, P3)

    Returns:
        Result with list of PredictionLog or error message

    Example:
        >>> context = create_agent_context("session")
        >>> result = get_predictions(context, datetime.now() - timedelta(days=7))
        >>> if result.is_ok():
        ...     predictions = result.unwrap()
    """
    try:
        # Query VectorStore for predictions (Article IV)
        tags = ["prediction", "ml_classification"]
        if tier_filter:
            tags.append(tier_filter.lower())

        memories = context.search_memories(tags=tags, include_session=True)

        # Parse memories into PredictionLog objects
        predictions: list[PredictionLog] = []
        for memory in memories:
            # VectorStore may wrap content in dict
            if "content" in memory and isinstance(memory["content"], dict):
                pred_data = memory["content"]
            else:
                pred_data = memory

            # Parse timestamp
            if "timestamp" in pred_data:
                timestamp = pred_data["timestamp"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)

                # Filter by timestamp
                if timestamp >= since:
                    predictions.append(PredictionLog(**pred_data))

        return Ok(predictions)

    except Exception as e:
        return Err(f"Failed to retrieve predictions: {e}")
