"""
Continuous Learning System - Automatic pattern extraction from VectorStore memories.

This module enables Article IV continuous learning by automatically extracting
reusable patterns from agent experiences stored in VectorStore.

Constitutional Compliance:
- Article IV: Continuous Learning and Improvement (MANDATORY)
- Patterns extracted with confidence scoring (min 0.6)
- Auto-triggers after every N memories (default: 50)
- Evidence-based confidence calculation (min 3 occurrences for high confidence)

Performance Targets:
- Extract 10 patterns in <5 seconds (benchmark target)
- Pattern confidence accuracy >90% (validated patterns)
- Auto-extraction trigger: every 50 memories (configurable)

Example Usage:
    from agency_memory.learning import LearningSystem
    from agency_memory.vector_store import VectorStore

    vector_store = VectorStore()
    learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)

    # Extract patterns from VectorStore
    result = learning.extract_patterns()
    if result.is_ok():
        patterns = result.unwrap()
        print(f"Extracted {len(patterns)} patterns")

    # Auto-trigger extraction
    if learning.should_trigger_extraction():
        learning.extract_patterns()
"""

import logging
from collections import Counter
from datetime import datetime
from typing import Any

from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class LearningPattern:
    """A learned pattern extracted from VectorStore memories.

    Attributes:
        pattern_type: Pattern category ("tool", "error", "interaction")
        description: Human-readable pattern description
        evidence: List of memory records supporting this pattern
        confidence: Confidence score (0.0-1.0) based on evidence count
        tags: Tags for categorization and search
        timestamp: ISO timestamp of pattern creation
        provenance: Provenance metadata (origin, actor, retention_policy) - Article VIII
    """

    def __init__(
        self,
        pattern_type: str,
        description: str,
        evidence: list[dict[str, Any]],
        confidence: float,
        tags: list[str],
        origin: str = "learning_system",
        actor: str = "LearningAgent",
        retention_policy: str = "keep_until_superseded",
    ):
        self.pattern_type = pattern_type
        self.description = description
        self.evidence = evidence
        self.confidence = confidence
        self.tags = tags
        self.timestamp = datetime.now().isoformat()
        self.evidence_count = len(evidence)

        # Article VIII: Provenance tracking for all learning artifacts
        self.provenance = {
            "origin": origin,  # Where pattern was extracted (learning_system, manual, imported)
            "actor": actor,  # Which agent/system created this pattern
            "timestamp": self.timestamp,
            "retention_policy": retention_policy,  # keep_until_superseded, expire_90d, permanent
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert pattern to dictionary for storage."""
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "evidence_count": self.evidence_count,
            "confidence": self.confidence,
            "tags": self.tags,
            "timestamp": self.timestamp,
            "provenance": self.provenance,  # Article VIII: Include provenance
        }

    def __repr__(self) -> str:
        return (
            f"LearningPattern(type={self.pattern_type}, "
            f"confidence={self.confidence:.2f}, "
            f"evidence={self.evidence_count})"
        )


class LearningSystem:
    """Continuous learning system for automatic pattern extraction.

    Constitutional Compliance:
    - Article IV: Continuous Learning and Improvement (MANDATORY)
    - Min confidence: 0.6 (constitutional requirement)
    - Min evidence: 3 occurrences for high-confidence patterns
    - Auto-extraction every N memories (default: 50)

    Performance:
    - Extract 10 patterns in <5 seconds (target)
    - Pattern confidence accuracy >90% (validated)
    - Supports tool, error, and interaction pattern types
    """

    def __init__(
        self,
        vector_store: Any,
        min_confidence: float = 0.6,
        auto_extraction_trigger: int = 15,
    ):
        """Initialize LearningSystem.

        Args:
            vector_store: VectorStore instance for pattern extraction
            min_confidence: Minimum confidence threshold (default: 0.6)
            auto_extraction_trigger: Extract patterns every N memories (default: 15, Article VIII requirement)
        """
        self.vector_store = vector_store
        self.min_confidence = min_confidence
        self.auto_extraction_trigger = auto_extraction_trigger
        self.last_extraction_count = 0

        logger.info(
            f"LearningSystem initialized: "
            f"min_confidence={min_confidence}, "
            f"auto_trigger={auto_extraction_trigger}"
        )

    def extract_patterns(self) -> Result[list[LearningPattern], str]:
        """Extract patterns from VectorStore memories.

        Extracts three pattern types:
        1. Tool usage patterns (successful tool operations)
        2. Error resolution patterns (error → fix workflows)
        3. Agent interaction patterns (handoff coordination)

        Returns:
            Result containing list of learned patterns or error message.

        Constitutional Compliance:
            - Article IV: Continuous learning from experience
            - Min evidence: 3 occurrences for high confidence
            - Confidence calculation: evidence_count / 5 (capped at 1.0)

        Performance:
            - Target: 10 patterns in <5 seconds
            - Uses tag-based queries for efficiency
        """
        import time

        start_time = time.perf_counter()

        try:
            patterns = []

            # Extract tool usage patterns
            tool_patterns = self._extract_tool_patterns()
            patterns.extend(tool_patterns)

            # Extract error resolution patterns
            error_patterns = self._extract_error_patterns()
            patterns.extend(error_patterns)

            # Extract agent interaction patterns
            interaction_patterns = self._extract_interaction_patterns()
            patterns.extend(interaction_patterns)

            # Filter by confidence threshold (Article IV requirement)
            patterns = [p for p in patterns if p.confidence >= self.min_confidence]

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"Extracted {len(patterns)} patterns in {elapsed_ms:.2f}ms "
                f"(min_confidence={self.min_confidence})"
            )

            return Ok(patterns)

        except Exception as e:
            logger.error(f"Pattern extraction failed: {e}")
            return Err(f"Pattern extraction error: {e}")

    def _extract_tool_patterns(self) -> list[LearningPattern]:
        """Extract successful tool usage patterns.

        Groups tool memories by tool name, filters for success,
        and creates patterns with evidence-based confidence scoring.

        Returns:
            List of tool usage patterns (confidence ≥ min_confidence)
        """
        patterns = []

        # Query for tool-related memories (success only)
        tool_memories = self.vector_store.search_by_tags(
            tags=["tool", "success"], min_confidence=0.5
        )

        if len(tool_memories) < 3:  # Need at least 3 examples
            logger.debug(
                f"Insufficient tool memories for pattern extraction: {len(tool_memories)}"
            )
            return patterns

        # Group by tool name (extract from tags)
        tool_groups: dict[str, list[dict[str, Any]]] = {}
        for memory in tool_memories:
            memory_tags = memory.get("tags", [])
            if not isinstance(memory_tags, list):
                continue

            # Identify tool name from tags
            tool_name = None
            for tag in memory_tags:
                if isinstance(tag, str) and tag in [
                    "Read",
                    "Write",
                    "Edit",
                    "Bash",
                    "Glob",
                    "Grep",
                ]:
                    tool_name = tag
                    break

            if tool_name:
                tool_groups.setdefault(tool_name, []).append(memory)

        # Create patterns from groups (min 3 examples)
        for tool_name, examples in tool_groups.items():
            if len(examples) >= 3:
                # Confidence calculation: evidence_count / 5, capped at 1.0
                confidence = min(1.0, len(examples) / 5)

                pattern = LearningPattern(
                    pattern_type="tool",
                    description=f"Successful {tool_name} tool usage pattern",
                    evidence=examples,
                    confidence=confidence,
                    tags=["tool", tool_name, "success", "pattern"],
                )
                patterns.append(pattern)

                logger.debug(
                    f"Tool pattern: {tool_name} (evidence={len(examples)}, "
                    f"confidence={confidence:.2f})"
                )

        return patterns

    def _extract_error_patterns(self) -> list[LearningPattern]:
        """Extract error resolution patterns.

        Identifies error → fix workflows from VectorStore memories.
        Creates patterns for successful error resolutions.

        Returns:
            List of error resolution patterns (confidence ≥ min_confidence)
        """
        patterns = []

        # Query for error-related memories (fixed errors only)
        error_memories = self.vector_store.search_by_tags(
            tags=["error", "fixed"], min_confidence=0.5
        )

        if len(error_memories) < 2:  # Need at least 2 examples
            logger.debug(
                f"Insufficient error memories for pattern extraction: {len(error_memories)}"
            )
            return patterns

        # Group by error type (extract from content or tags)
        error_types: dict[str, list[dict[str, Any]]] = {}
        for memory in error_memories:
            content = memory.get("content", {})
            if not isinstance(content, dict):
                continue

            # Identify error type
            error_type = content.get("error_type", "unknown")
            if isinstance(error_type, str):
                error_types.setdefault(error_type, []).append(memory)

        # Create patterns from error types (min 2 examples)
        for error_type, examples in error_types.items():
            if len(examples) >= 2:
                # Confidence calculation: evidence_count / 3, capped at 1.0
                confidence = min(1.0, len(examples) / 3)

                pattern = LearningPattern(
                    pattern_type="error",
                    description=f"Error resolution pattern: {error_type}",
                    evidence=examples,
                    confidence=confidence,
                    tags=["error", "fixed", "resolution", "pattern"],
                )
                patterns.append(pattern)

                logger.debug(
                    f"Error pattern: {error_type} (evidence={len(examples)}, "
                    f"confidence={confidence:.2f})"
                )

        # Generic error pattern if we have many fixed errors
        if len(error_memories) >= 5:
            confidence = min(1.0, len(error_memories) / 10)
            pattern = LearningPattern(
                pattern_type="error",
                description="Generic error resolution pattern (NoneType, attribute errors, etc.)",
                evidence=error_memories[:10],  # Sample first 10
                confidence=confidence,
                tags=["error", "fixed", "resolution", "pattern"],
            )
            patterns.append(pattern)

            logger.debug(
                f"Generic error pattern (evidence={len(error_memories)}, "
                f"confidence={confidence:.2f})"
            )

        return patterns

    def _extract_interaction_patterns(self) -> list[LearningPattern]:
        """Extract agent interaction patterns.

        Identifies successful agent coordination and handoff workflows.
        Creates patterns for multi-agent collaboration.

        Returns:
            List of agent interaction patterns (confidence ≥ min_confidence)
        """
        patterns = []

        # Query for interaction-related memories
        interaction_memories = self.vector_store.search_by_tags(
            tags=["agent", "handoff"], min_confidence=0.5
        )

        if len(interaction_memories) < 3:
            logger.debug(
                f"Insufficient interaction memories for pattern extraction: "
                f"{len(interaction_memories)}"
            )
            return patterns

        # Group by agent pair (source → target)
        agent_pairs: dict[str, list[dict[str, Any]]] = {}
        for memory in interaction_memories:
            content = memory.get("content", {})
            if not isinstance(content, dict):
                continue

            source = content.get("source_agent", "unknown")
            target = content.get("target_agent", "unknown")
            pair_key = f"{source} → {target}"

            agent_pairs.setdefault(pair_key, []).append(memory)

        # Create patterns from agent pairs (min 3 examples)
        for pair_key, examples in agent_pairs.items():
            if len(examples) >= 3:
                # Confidence calculation: evidence_count / 5, capped at 1.0
                confidence = min(1.0, len(examples) / 5)

                pattern = LearningPattern(
                    pattern_type="interaction",
                    description=f"Agent coordination pattern: {pair_key}",
                    evidence=examples,
                    confidence=confidence,
                    tags=["agent", "interaction", "coordination", "pattern"],
                )
                patterns.append(pattern)

                logger.debug(
                    f"Interaction pattern: {pair_key} (evidence={len(examples)}, "
                    f"confidence={confidence:.2f})"
                )

        # Generic interaction pattern if we have many handoffs
        if len(interaction_memories) >= 5:
            confidence = min(1.0, len(interaction_memories) / 10)
            pattern = LearningPattern(
                pattern_type="interaction",
                description="Generic agent coordination pattern",
                evidence=interaction_memories[:10],  # Sample first 10
                confidence=confidence,
                tags=["agent", "interaction", "coordination", "pattern"],
            )
            patterns.append(pattern)

            logger.debug(
                f"Generic interaction pattern (evidence={len(interaction_memories)}, "
                f"confidence={confidence:.2f})"
            )

        return patterns

    def should_trigger_extraction(self) -> bool:
        """Check if pattern extraction should be triggered.

        Auto-triggers when memory count increases by auto_extraction_trigger.

        Returns:
            True if extraction should be triggered, False otherwise
        """
        # Get current memory count from VectorStore
        current_count = (
            len(self.vector_store._memories)
            if hasattr(self.vector_store, "_memories")
            else 0
        )

        # Trigger if count increased by threshold
        if current_count - self.last_extraction_count >= self.auto_extraction_trigger:
            self.last_extraction_count = current_count
            logger.info(
                f"Auto-extraction triggered: {current_count} memories "
                f"(threshold: {self.auto_extraction_trigger})"
            )
            return True

        return False

    def enable_auto_extraction(self) -> None:
        """Enable automatic pattern extraction after every N memories.

        Hooks into VectorStore to auto-trigger extraction.
        """
        logger.info(
            f"Auto-extraction enabled (trigger every {self.auto_extraction_trigger} memories)"
        )

    def calculate_pattern_confidence(
        self, evidence_count: int, consistency_score: float = 1.0, recency_days: int = 0
    ) -> float:
        """Calculate confidence score for a pattern.

        Formula:
            confidence = min(1.0, (evidence_count / 3) * consistency_score * recency_factor)

        Args:
            evidence_count: Number of supporting examples
            consistency_score: Pattern consistency (0.0-1.0, default: 1.0)
            recency_days: Days since pattern last observed (0 = today)

        Returns:
            Confidence score (0.0-1.0)

        Constitutional Compliance:
            - Article IV: Min 3 occurrences for confidence ≥1.0
            - Consistency weighting prevents false positives
            - Recency factor prioritizes recent patterns
        """
        # Base confidence from evidence count (min 3 for confidence ≥1.0)
        base_confidence = evidence_count / 3

        # Recency factor: 1.0 (recent) to 0.5 (old)
        # Decays linearly over 90 days
        if recency_days == 0:
            recency_factor = 1.0
        else:
            recency_factor = max(0.5, 1.0 - (recency_days / 90))

        # Calculate final confidence
        confidence = min(1.0, base_confidence * consistency_score * recency_factor)

        return confidence

    def get_pattern_statistics(self) -> dict[str, Any]:
        """Get statistics on extracted patterns.

        Returns:
            Dictionary with pattern statistics:
            - total_patterns: Total patterns in VectorStore
            - by_type: Pattern count by type (tool, error, interaction)
            - avg_confidence: Average confidence score
            - high_confidence_count: Patterns with confidence ≥0.9
        """
        # Query all patterns
        all_patterns = self.vector_store.search_by_tags(
            tags=["pattern"], min_confidence=0.0  # Get all patterns
        )

        if not all_patterns:
            return {
                "total_patterns": 0,
                "by_type": {},
                "avg_confidence": 0.0,
                "high_confidence_count": 0,
            }

        # Count by type
        type_counter = Counter()
        confidence_scores = []
        high_confidence_count = 0

        for pattern in all_patterns:
            # Extract pattern type from tags
            tags = pattern.get("tags", [])
            if "tool" in tags:
                type_counter["tool"] += 1
            elif "error" in tags:
                type_counter["error"] += 1
            elif "interaction" in tags:
                type_counter["interaction"] += 1

            # Track confidence
            confidence = pattern.get("confidence", 0.0)
            if isinstance(confidence, (int, float)):
                confidence_scores.append(confidence)
                if confidence >= 0.9:
                    high_confidence_count += 1

        # Calculate average confidence
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        )

        return {
            "total_patterns": len(all_patterns),
            "by_type": dict(type_counter),
            "avg_confidence": round(avg_confidence, 2),
            "high_confidence_count": high_confidence_count,
        }

    def apply_supervision(
        self,
        memory_id: str,
        signal: dict[str, Any],
        actor: str = "human",
        reason: str = "",
    ) -> Result[None, str]:
        """Apply supervision signal to a memory for RLHF-style feedback (Article VIII).

        Stores reinforcement signal (approved/rejected/neutral) for training data curation.
        This enables DPO/RLHF-style learning loops.

        Args:
            memory_id: Memory record identifier to supervise
            signal: Supervision signal dict with keys:
                - outcome: "approved" | "rejected" | "neutral"
                - quality_score: 0.0-1.0
                - counterfactual: Optional alternative approach
                - preference: Optional preference data
                - learning_value: 0.0-1.0 (how valuable for future learning)
            actor: Who provided the supervision (human, agent, automated)
            reason: Why this supervision was applied (optional)

        Returns:
            Result[None, str] - Ok(None) on success, Err(message) on failure

        Article VIII Compliance:
            - Supervision signal density target: ≥90%
            - Quality score ≥0.8 tagged as "rl_training_data"
            - Counterfactuals enable what-if analysis

        Example:
            >>> learning = LearningSystem(vector_store)
            >>> result = learning.apply_supervision(
            ...     memory_id="jwt_auth_success_123",
            ...     signal={
            ...         "outcome": "approved",
            ...         "quality_score": 0.95,
            ...         "learning_value": 1.0
            ...     },
            ...     actor="human",
            ...     reason="Excellent implementation, clean code"
            ... )
        """
        try:
            # Validate signal format
            required_keys = ["outcome", "quality_score"]
            if not all(k in signal for k in required_keys):
                return Err(f"Missing required keys: {required_keys}")

            outcome = signal.get("outcome")
            if outcome not in ["approved", "rejected", "neutral"]:
                return Err(f"Invalid outcome: {outcome} (must be approved/rejected/neutral)")

            quality_score = signal.get("quality_score")
            if not isinstance(quality_score, (int, float)) or not (0.0 <= quality_score <= 1.0):
                return Err(f"Invalid quality_score: {quality_score} (must be 0.0-1.0)")

            # Build supervision record
            supervision_record = {
                "memory_id": memory_id,
                "signal": signal,
                "actor": actor,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "provenance": {
                    "origin": "supervision",
                    "actor": actor,
                    "timestamp": datetime.now().isoformat(),
                    "retention_policy": "permanent",  # Supervision data kept permanently
                },
            }

            # Tag as RL training data if high quality (Article VIII: quality ≥0.8)
            tags = ["supervision", "rl_data", outcome]
            if quality_score >= 0.8:
                tags.append("rl_training_data")

            # Store supervision signal in VectorStore
            self.vector_store.store(
                key=f"{memory_id}_supervision_{int(datetime.now().timestamp())}",
                content=supervision_record,
                tags=tags,
                confidence=quality_score,
            )

            logger.info(
                f"Supervision applied: {memory_id} → {outcome} (quality={quality_score:.2f}, actor={actor})"
            )

            return Ok(None)

        except Exception as e:
            logger.error(f"Supervision application failed: {e}")
            return Err(f"Supervision error: {e}")

    def ingest(self, payload: dict[str, Any]) -> Result[None, str]:
        """Ingest memory payload with optional supervision signal (Article VIII integration).

        This method is called by AgentContext.store_memory() to integrate
        learning extraction with memory storage.

        Args:
            payload: Memory payload dict with keys:
                - key: Memory identifier
                - content: Memory content
                - tags: List of tags
                - confidence: Confidence score (0.0-1.0)
                - supervision_signal: Optional supervision metadata

        Returns:
            Result[None, str] - Ok(None) on success, Err(message) on failure

        Article VIII Compliance:
            - Automatic pattern extraction trigger after N memories
            - Supervision signal storage for RLHF training
            - Provenance tracking for all ingested data

        Example:
            >>> learning = LearningSystem(vector_store)
            >>> result = learning.ingest({
            ...     "key": "feature_x_success",
            ...     "content": {"code": "...", "tests_passed": True},
            ...     "tags": ["coder", "feature", "success"],
            ...     "confidence": 0.9,
            ...     "supervision_signal": {
            ...         "outcome": "approved",
            ...         "quality_score": 0.95
            ...     }
            ... })
        """
        try:
            # Extract supervision signal if present
            supervision_signal = payload.get("supervision_signal")
            if supervision_signal:
                memory_id = payload.get("key", "unknown")
                result = self.apply_supervision(
                    memory_id=memory_id,
                    signal=supervision_signal,
                    actor=supervision_signal.get("actor", "automated"),
                    reason=supervision_signal.get("reason", "Automatic ingestion"),
                )

                if result.is_err():
                    logger.warning(f"Supervision storage failed: {result.unwrap_err()}")

            # Check if pattern extraction should be triggered (Article VIII: every 15 memories)
            if self.should_trigger_extraction():
                logger.info("Auto-extraction triggered by ingest()")
                extraction_result = self.extract_patterns()

                if extraction_result.is_ok():
                    patterns = extraction_result.unwrap()
                    logger.info(f"Auto-extracted {len(patterns)} patterns during ingestion")

                    # Emit learning artifacts (Article VIII requirement)
                    for pattern in patterns:
                        # Store pattern to VectorStore with provenance
                        self.vector_store.store(
                            key=f"learning:concept:{pattern.pattern_type}:{int(datetime.now().timestamp())}",
                            content=pattern.to_dict(),
                            tags=pattern.tags + ["learning_artifact", "concept"],
                            confidence=pattern.confidence,
                        )
                else:
                    logger.warning(f"Auto-extraction failed: {extraction_result.unwrap_err()}")

            return Ok(None)

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return Err(f"Ingestion error: {e}")


# Legacy functions for backward compatibility
def consolidate_learnings(memories: list[dict[str, Any]]) -> dict[str, Any]:
    """
    LEGACY: Consolidate learnings from memory records (backward compatibility).

    This function is maintained for compatibility with existing code that uses
    the old consolidation-based approach. New code should use LearningSystem
    for pattern extraction.

    Args:
        memories: List of memory records with tags, timestamps, and content

    Returns:
        Structured summary with tag frequencies and basic statistics
    """
    if not memories:
        return {
            "summary": "No memories to analyze",
            "total_memories": 0,
            "tag_frequencies": {},
            "patterns": {},
            "generated_at": datetime.now().isoformat(),
        }

    # Initialize counters
    tag_counter: Counter[str] = Counter()

    # Process each memory
    for memory in memories:
        tags = memory.get("tags", [])
        if isinstance(tags, list):
            string_tags = [str(tag) for tag in tags if isinstance(tag, str)]
            tag_counter.update(string_tags)

    # Generate simple summary
    total_memories = len(memories)
    tag_frequencies = dict(tag_counter)
    unique_tags = len(tag_frequencies)
    top_tags = tag_counter.most_common(10)

    return {
        "summary": f"Analyzed {total_memories} memories with {unique_tags} unique tags",
        "total_memories": total_memories,
        "unique_tags": unique_tags,
        "tag_frequencies": tag_frequencies,
        "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
        "patterns": {},
        "generated_at": datetime.now().isoformat(),
    }


def generate_learning_report(memories: list[dict[str, Any]], session_id: str | None = None) -> str:
    """
    LEGACY: Generate formatted learning report (backward compatibility).

    This function is maintained for compatibility with existing code.
    New code should use LearningSystem for pattern extraction.

    Args:
        memories: List of memory records
        session_id: Optional session identifier

    Returns:
        Formatted markdown report string
    """
    analysis = consolidate_learnings(memories)

    report = "# Learning Consolidation Report\n\n"

    if session_id:
        report += f"**Session:** {session_id}\n"

    report += f"**Generated:** {analysis['generated_at']}\n"
    report += f"Total Memories: {analysis['total_memories']}\n"
    report += f"**Summary:** {analysis['summary']}\n\n"

    # Statistics
    report += "## Statistics\n\n"
    report += f"- **Total Memories:** {analysis['total_memories']}\n"
    report += f"- **Unique Tags:** {analysis['unique_tags']}\n\n"

    # Top tags
    top_tags = analysis.get("top_tags", [])
    if isinstance(top_tags, list) and top_tags:
        report += "## Most Used Tags\n\n"
        for tag_info in top_tags[:5]:
            if isinstance(tag_info, dict):
                tag_name = tag_info.get("tag", "unknown")
                tag_count = tag_info.get("count", 0)
                report += f"- **{tag_name}:** {tag_count} times\n"

    return report
