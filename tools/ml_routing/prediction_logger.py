"""
Prediction logging utility for VectorStore integration.

Provides functions to log ML predictions and retrieve them for analysis:
- log_prediction(): Store prediction in VectorStore (async/non-blocking)
- get_predictions(): Retrieve predictions with filtering (timestamp, tier)

Constitutional Compliance:
- Article I: Complete context (all prediction metadata logged)
- Article II: Result pattern for error handling (no exceptions)
- Article IV: MANDATORY VectorStore logging (all predictions tracked)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for all fallible operations
- Law #8: Functions <50 lines each

Reference: specs/spec-007-phase3-ml-inference.md Section 5.5
Author: CodingAgent
Date: 2025-10-10
"""

import logging
from datetime import UTC, datetime
from typing import Any

from shared.agent_context import AgentContext
from shared.models.prediction_log import PredictionLog
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


def log_prediction(
    context: AgentContext,
    prediction_log: PredictionLog,
) -> Result[None, str]:
    """
    Log prediction to VectorStore for online learning and monitoring.

    Stores prediction with tags ['prediction', tier, method] for searchability.
    Non-blocking operation (returns immediately).

    Args:
        context: AgentContext with VectorStore access
        prediction_log: PredictionLog to store

    Returns:
        Result[None, str] - Ok(None) on success, Err(message) on failure

    Constitutional Compliance:
        - Article I: Complete context (all prediction metadata)
        - Article IV: MANDATORY VectorStore logging (all predictions)
        - Law #5: Result pattern for error handling
        - Law #8: Function <50 lines

    Example:
        >>> context = create_agent_context(session_id="session_001")
        >>> prediction = PredictionLog(
        ...     task_id="task_abc",
        ...     tier="moderate",
        ...     confidence=0.85,
        ...     method="ml_model",
        ...     model_version="2025-10-10T12:00:00Z",
        ...     session_id="session_001"
        ... )
        >>> result = log_prediction(context, prediction)
        >>> assert result.is_ok()
    """
    try:
        # Generate unique key for prediction
        timestamp_str = prediction_log.timestamp  # Already an ISO string
        key = f"prediction_{prediction_log.task_id}_{timestamp_str}"

        # Convert to dict for storage
        content = prediction_log.to_dict()

        # Tags for searchability: ['prediction', tier, method]
        tags = [
            "prediction",
            prediction_log.tier,
            prediction_log.method,
        ]

        # Store in VectorStore (Article IV mandate)
        context.store_memory(key=key, content=content, tags=tags)

        logger.debug(
            f"Logged prediction: task_id={prediction_log.task_id}, "
            f"tier={prediction_log.tier}, "
            f"confidence={prediction_log.confidence:.2f}"
        )

        return Ok(None)

    except Exception as e:
        error_msg = f"Failed to log prediction for task {prediction_log.task_id}: {e}"
        logger.error(error_msg)
        return Err(error_msg)


def get_predictions(
    context: AgentContext,
    since: datetime | None = None,
    tier_filter: str | None = None,
) -> Result[list[PredictionLog], str]:
    """
    Retrieve predictions from VectorStore with optional filtering.

    Filters:
    - since: Only return predictions after this timestamp (UTC)
    - tier_filter: Only return predictions with this tier (simple/moderate/complex)

    Args:
        context: AgentContext with VectorStore access
        since: Optional timestamp filter (UTC)
        tier_filter: Optional tier filter (simple/moderate/complex)

    Returns:
        Result[list[PredictionLog], str] - Ok(predictions) or Err(message)

    Constitutional Compliance:
        - Article I: Complete context retrieval
        - Article II: 100% verification (skip invalid entries)
        - Law #5: Result pattern for error handling
        - Law #8: Function <50 lines

    Example:
        >>> context = create_agent_context(session_id="session_001")
        >>> # Get all predictions
        >>> result = get_predictions(context)
        >>> predictions = result.unwrap()
        >>>
        >>> # Get complex predictions from last hour
        >>> cutoff = datetime.now(UTC) - timedelta(hours=1)
        >>> result = get_predictions(context, since=cutoff, tier_filter="complex")
    """
    try:
        # Build search tags (conjunctive search)
        search_tags = ["prediction"]

        # Add tier filter if specified
        if tier_filter is not None:
            search_tags.append(tier_filter)

        # Retrieve predictions from VectorStore (session-scoped for test isolation)
        raw_predictions = context.search_memories(search_tags, include_session=False)

        # Filter and reconstruct PredictionLog objects
        predictions: list[PredictionLog] = []

        for raw in raw_predictions:
            # Apply timestamp filter (since)
            if since is not None:
                try:
                    timestamp_str = raw["content"]["timestamp"]
                    stored_timestamp = datetime.fromisoformat(timestamp_str)

                    # Ensure both timestamps are timezone-aware for comparison
                    if stored_timestamp.tzinfo is None:
                        stored_timestamp = stored_timestamp.replace(tzinfo=UTC)
                    if since.tzinfo is None:
                        since_aware = since.replace(tzinfo=UTC)
                    else:
                        since_aware = since

                    if stored_timestamp < since_aware:
                        continue  # Skip old predictions
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid timestamp in prediction {raw.get('key')}: {e}")
                    continue

            # Reconstruct PredictionLog from stored content
            try:
                prediction = PredictionLog.from_dict(raw["content"])
                predictions.append(prediction)
            except Exception as e:
                # Skip invalid entries (Article II: verification)
                logger.warning(f"Skipping invalid prediction {raw.get('key')}: {e}")
                continue

        logger.debug(
            f"Retrieved {len(predictions)} predictions (filters: since={since}, tier={tier_filter})"
        )

        return Ok(predictions)

    except Exception as e:
        error_msg = f"Failed to retrieve predictions: {e}"
        logger.error(error_msg)
        return Err(error_msg)
