# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Article IV Compliance Decorator

Enforces Constitutional Article IV (Continuous Learning and Improvement) by:
1. Querying VectorStore patterns BEFORE agent action
2. Storing successful outcomes AFTER agent action

Usage:
    @with_article_iv_compliance(query_tags=["planner", "spec"])
    def generate_plan(self, spec: str) -> Result[Plan, Error]:
        # Agent implementation here
        pass

Constitutional Requirements:
    - Article IV (ADR-004): Mandatory VectorStore integration
    - Query search_memories() before action
    - Store successful patterns after completion
    - Min confidence: 0.6 for queries, 0.85 for storage
"""

import logging
import time
from functools import wraps
from typing import Any, Callable

from shared.agent_context import AgentContext
from shared.type_definitions.json_value import JSONValue

logger = logging.getLogger(__name__)


def with_article_iv_compliance(
    query_tags: list[str] | Callable[..., list[str]] | None = None,
    store_on_success: bool = True,
    min_confidence: float = 0.6,
    storage_confidence: float = 0.85,
):
    """
    Decorator that enforces Article IV compliance (query before, store after).

    Args:
        query_tags: Tags for VectorStore query OR callable to generate tags dynamically
                   If callable: (self, *args, **kwargs) -> list[str]
        store_on_success: Store result in VectorStore on success (default: True)
        min_confidence: Minimum confidence for query results (default: 0.6)
        storage_confidence: Confidence score for stored patterns (default: 0.85)

    Returns:
        Decorated function with Article IV compliance

    Constitutional Compliance:
        - Article IV: Query learnings BEFORE action (mandatory)
        - Article IV: Store successful patterns AFTER action (mandatory)
        - ADR-004: VectorStore integration is constitutionally required

    Example:
        >>> @with_article_iv_compliance(query_tags=["planner", "spec"])
        >>> def generate_plan(self, spec: str) -> Result[Plan, Error]:
        >>>     # Agent implementation
        >>>     pass

        >>> # Dynamic tags based on task type
        >>> def get_tags(self, task_type: str, **kwargs):
        >>>     return ["coder", task_type, "implementation"]
        >>>
        >>> @with_article_iv_compliance(query_tags=get_tags)
        >>> def implement_task(self, task_type: str) -> Result[Code, Error]:
        >>>     # Agent implementation
        >>>     pass
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Get context from agent instance
            context = getattr(self, "context", None)

            # If no context, skip compliance (defensive)
            if not isinstance(context, AgentContext):
                logger.warning(
                    f"{func.__name__}: No AgentContext found, skipping Article IV compliance"
                )
                return func(self, *args, **kwargs)

            # STEP 1: QUERY BEFORE ACTION (Article IV)
            tags = _resolve_query_tags(query_tags, self, *args, **kwargs)

            if tags:
                try:
                    patterns = context.search_memories(
                        tags=tags, include_session=True, min_confidence=min_confidence
                    )

                    if patterns:
                        logger.info(
                            f"{func.__name__}: Found {len(patterns)} patterns "
                            f"from VectorStore (tags: {tags})"
                        )
                        # Inject patterns into kwargs for agent to use
                        kwargs["_vectorstore_patterns"] = patterns
                    else:
                        logger.debug(
                            f"{func.__name__}: No VectorStore patterns found " f"(tags: {tags})"
                        )

                except Exception as e:
                    logger.error(f"{func.__name__}: VectorStore query failed: {e}")
                    # Continue without patterns (degraded mode)

            # STEP 2: EXECUTE AGENT ACTION
            result = func(self, *args, **kwargs)

            # STEP 3: STORE AFTER SUCCESS (Article IV)
            if store_on_success:
                try:
                    # Check if result is Result<T,E> pattern
                    if hasattr(result, "is_ok"):
                        # Only store if Result is Ok, skip if Err
                        if result.is_ok():
                            _store_success_pattern(
                                context=context,
                                func_name=func.__name__,
                                result=result.unwrap(),
                                tags=tags,
                                confidence=storage_confidence,
                            )
                        # else: Skip storage for Err results
                    # Check if result is a dict with success indicator
                    elif isinstance(result, dict) and result.get("success"):
                        _store_success_pattern(
                            context=context,
                            func_name=func.__name__,
                            result=result,
                            tags=tags,
                            confidence=storage_confidence,
                        )
                    # Check if result is truthy (simple success check)
                    # BUT: Exclude Result objects (already handled above)
                    elif result and not isinstance(result, bool) and not hasattr(result, "is_ok"):
                        _store_success_pattern(
                            context=context,
                            func_name=func.__name__,
                            result=result,
                            tags=tags,
                            confidence=storage_confidence,
                        )

                except Exception as e:
                    logger.error(f"{func.__name__}: VectorStore storage failed: {e}")
                    # Continue despite storage failure (non-blocking)

            return result

        return wrapper

    return decorator


def _resolve_query_tags(
    query_tags: list[str] | Callable[..., list[str]] | None,
    self: Any,
    *args: Any,
    **kwargs: Any,
) -> list[str]:
    """
    Resolve query tags from static list or dynamic callable.

    Args:
        query_tags: Static tags OR callable to generate tags
        self: Agent instance
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        List of tags for VectorStore query
    """
    if query_tags is None:
        return []

    if callable(query_tags):
        try:
            tags = query_tags(self, *args, **kwargs)
            if not isinstance(tags, list):
                logger.warning(
                    f"query_tags callable returned non-list: {type(tags)}, " f"using empty list"
                )
                return []
            return tags
        except Exception as e:
            logger.error(f"query_tags callable failed: {e}, using empty list")
            return []

    if isinstance(query_tags, list):
        return query_tags

    logger.warning(f"Invalid query_tags type: {type(query_tags)}, using empty list")
    return []


def _store_success_pattern(
    context: AgentContext,
    func_name: str,
    result: Any,
    tags: list[str],
    confidence: float,
) -> None:
    """
    Store successful pattern in VectorStore.

    Args:
        context: AgentContext instance
        func_name: Function name (for key generation)
        result: Successful result to store
        tags: Tags for categorization
        confidence: Confidence score
    """
    key = f"{func_name}_success_{int(time.time())}"

    # Build content for VectorStore
    content: dict[str, JSONValue] = {
        "function": func_name,
        "timestamp": int(time.time()),
        "success": True,
    }

    # Add result data (handle various types)
    if isinstance(result, dict):
        content["result"] = result
    elif isinstance(result, str):
        content["result"] = {"output": result}
    elif hasattr(result, "__dict__"):
        # Convert object to dict (for Pydantic models, etc.)
        try:
            content["result"] = result.__dict__
        except Exception:
            content["result"] = {"type": type(result).__name__}
    else:
        content["result"] = {"type": type(result).__name__}

    # Store in VectorStore with success tag
    all_tags = tags + ["success", func_name]

    context.store_memory(key=key, content=content, tags=all_tags, confidence=confidence)

    logger.info(f"{func_name}: Stored success pattern in VectorStore (tags: {all_tags})")
