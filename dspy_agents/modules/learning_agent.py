"""
DSPy-powered Learning Agent Implementation

This module implements a DSPy Module that replaces the static markdown-based
LearningAgent with adaptive, learning-based pattern extraction and knowledge consolidation.

Key Features:
- Pattern extraction from session data
- Insight consolidation across sessions
- Knowledge storage in VectorStore
- Continuous learning and improvement
- Compatible with existing Agency memory systems
"""

import os
import logging
import traceback
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
from ..type_definitions import (
    DSPyContext, LearningContext, SessionData, Insight,
    LearningSummary, PatternDict
)

from pydantic import BaseModel, Field, ValidationError

# Conditional DSPy import for gradual migration
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    # Fallback for when DSPy is not yet installed
    class dspy:
        class Module:
            def __init__(self):
                pass
            def forward(self, *args, **kwargs):
                raise NotImplementedError("DSPy not available")

        class ChainOfThought:
            def __init__(self, signature):
                self.signature = signature
            def __call__(self, *args, **kwargs):
                raise NotImplementedError("DSPy not available")

        class Predict:
            def __init__(self, signature):
                self.signature = signature
            def __call__(self, *args, **kwargs):
                raise NotImplementedError("DSPy not available")

    DSPY_AVAILABLE = False

from ..signatures.base import (
    PatternExtractionSignature,
    ConsolidationSignature,
    StorageSignature,
)

# Configure logging
logger = logging.getLogger(__name__)


class LearningContext(BaseModel):
    """Context for learning operations with Agency-specific information."""

    session_id: str = Field(..., description="Session to analyze")
    logs_directory: str = Field(default="logs/sessions", description="Directory containing session logs")
    memory_store: Optional[str] = Field(default="vectorstore", description="Where to store learnings")
    pattern_types: List[str] = Field(default_factory=lambda: [
        "tool_usage",
        "error_resolution",
        "task_completion",
        "workflow_optimization",
        "agent_coordination"
    ])
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for patterns")
    historical_limit: int = Field(default=10, description="Number of historical sessions to consider")


class ExtractedPattern(BaseModel):
    """A pattern extracted from session data."""

    pattern_type: str = Field(..., description="Type of pattern")
    description: str = Field(..., description="Description of the pattern")
    confidence: float = Field(..., description="Confidence score (0-1)")
    occurrences: int = Field(..., description="Number of occurrences")
    context: DSPyContext = Field(default_factory=dict, description="Additional context")
    keywords: List[str] = Field(default_factory=list, description="Keywords for retrieval")


class ConsolidatedLearning(BaseModel):
    """A consolidated learning from multiple patterns."""

    title: str = Field(..., description="Title of the learning")
    summary: str = Field(..., description="Summary description")
    patterns: List[ExtractedPattern] = Field(..., description="Supporting patterns")
    actionable_insights: List[str] = Field(..., description="Actionable insights")
    confidence: float = Field(..., description="Overall confidence")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class LearningResult(BaseModel):
    """Result from a learning operation."""

    success: bool = Field(..., description="Whether the operation succeeded")
    patterns_extracted: int = Field(default=0, description="Number of patterns extracted")
    learnings_consolidated: int = Field(default=0, description="Number of learnings consolidated")
    knowledge_stored: bool = Field(default=False, description="Whether knowledge was stored")
    message: str = Field(..., description="Summary message")
    details: Optional[dict] = Field(None, description="Additional details")


class DSPyLearningAgent(dspy.Module if DSPY_AVAILABLE else object):
    """
    DSPy-powered Learning Agent that extracts patterns and consolidates knowledge.

    This agent replaces the static LearningAgent with adaptive reasoning
    capabilities, learning from successful patterns and building institutional memory.

    Falls back to a basic implementation when DSPy is not available.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        reasoning_effort: str = "high",
        enable_learning: bool = True,
        min_confidence: float = 0.7
    ):
        """
        Initialize the DSPy Learning Agent.

        Args:
            model: Language model to use
            reasoning_effort: Level of reasoning effort (low, medium, high)
            enable_learning: Whether to enable continuous learning
            min_confidence: Minimum confidence threshold for patterns
        """
        if DSPY_AVAILABLE:
            super().__init__()

        self.model = model
        self.reasoning_effort = reasoning_effort
        self.enable_learning = enable_learning
        self.min_confidence = min_confidence
        self.dspy_available = DSPY_AVAILABLE

        # Initialize DSPy modules for different tasks if available
        if DSPY_AVAILABLE:
            self.pattern_extractor = dspy.ChainOfThought(PatternExtractionSignature)
            self.consolidator = dspy.ChainOfThought(ConsolidationSignature)
            self.storage = dspy.Predict(StorageSignature)
        else:
            # Fallback to None when DSPy is not available
            self.pattern_extractor = None
            self.consolidator = None
            self.storage = None

        # Initialize knowledge base
        self.knowledge_base: Dict[str, List[ConsolidatedLearning]] = {}
        self.pattern_history: List[ExtractedPattern] = []

        status = "with DSPy" if DSPY_AVAILABLE else "in fallback mode (DSPy not available)"
        logger.info(f"DSPyLearningAgent initialized {status} - model={model}, reasoning={reasoning_effort}")

    def forward(
        self,
        session_id: Optional[str] = None,
        session_data: Optional[SessionData] = None,
        pattern_types: Optional[List[str]] = None,
        context: Optional[DSPyContext] = None,
        **kwargs
    ) -> LearningResult:
        """
        Main forward method for learning operations.

        Args:
            session_id: ID of session to analyze
            session_data: Pre-loaded session data (optional)
            pattern_types: Types of patterns to extract
            context: Optional context dictionary
            **kwargs: Additional keyword arguments

        Returns:
            LearningResult: Result of the learning operation
        """
        try:
            # Validate and prepare context
            learning_context = self._prepare_context(session_id, pattern_types, context or {})

            if not DSPY_AVAILABLE:
                # Fallback implementation when DSPy is not available
                return self._fallback_execution(learning_context, session_data)

            # Load session data if not provided
            if session_data is None:
                session_data = self._load_session_data(learning_context)

            # Extract patterns using DSPy
            extraction_result = self.pattern_extractor(
                session_data=session_data,
                pattern_types=learning_context.pattern_types,
                minimum_confidence=learning_context.confidence_threshold
            )

            patterns = self._process_patterns(extraction_result)

            # Get existing knowledge for consolidation
            existing_knowledge = self._get_existing_knowledge(learning_context)

            # Consolidate learnings using DSPy
            consolidation_result = self.consolidator(
                patterns=patterns,
                existing_knowledge=existing_knowledge,
                validation_criteria=[
                    f"Confidence >= {learning_context.confidence_threshold}",
                    "At least 2 supporting patterns",
                    "Actionable insights present"
                ]
            )

            learnings = self._process_learnings(consolidation_result)

            # Store knowledge using DSPy
            storage_result = self.storage(
                learnings=learnings,
                storage_location=learning_context.memory_store,
                metadata={
                    "session_id": learning_context.session_id,
                    "timestamp": datetime.now().isoformat(),
                    "agent": "DSPyLearningAgent"
                }
            )

            # Update internal knowledge base if learning enabled
            if self.enable_learning:
                self._update_knowledge_base(learnings, learning_context)

            return LearningResult(
                success=True,
                patterns_extracted=len(patterns),
                learnings_consolidated=len(learnings),
                knowledge_stored=storage_result.storage_confirmation,
                message=f"Extracted {len(patterns)} patterns and consolidated {len(learnings)} learnings",
                details={
                    "pattern_types": [p["pattern_type"] for p in patterns],
                    "learning_titles": [l["title"] for l in learnings],
                    "storage_ids": storage_result.storage_ids
                }
            )

        except Exception as e:
            logger.error(f"Error in DSPyLearningAgent.forward: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            return LearningResult(
                success=False,
                message=f"Learning operation failed: {str(e)}"
            )

    def _fallback_execution(
        self,
        context: LearningContext,
        session_data: Optional[SessionData]
    ) -> LearningResult:
        """
        Fallback execution when DSPy is not available.

        Provides basic functionality for pattern extraction.
        """
        logger.warning("Using fallback execution - DSPy not available")

        # Basic pattern extraction
        patterns = []
        if session_data:
            # Extract basic patterns without DSPy
            if "tool_calls" in session_data:
                patterns.append({
                    "pattern_type": "tool_usage",
                    "description": f"Session used {len(session_data['tool_calls'])} tools",
                    "confidence": 0.5
                })

            if "errors" in session_data and session_data["errors"]:
                patterns.append({
                    "pattern_type": "error_resolution",
                    "description": f"Session encountered {len(session_data['errors'])} errors",
                    "confidence": 0.5
                })

        return LearningResult(
            success=False,
            patterns_extracted=len(patterns),
            learnings_consolidated=0,
            knowledge_stored=False,
            message="DSPy not available. Basic pattern extraction only.",
            details={"patterns": patterns}
        )

    def analyze_session(
        self,
        session_path: str,
        focus_areas: Optional[List[str]] = None
    ) -> dict:
        """
        Analyze a specific session for patterns.

        Args:
            session_path: Path to session transcript
            focus_areas: Specific areas to focus on

        Returns:
            Analysis results
        """
        try:
            # Load session data
            with open(session_path, 'r') as f:
                session_data = json.load(f) if session_path.endswith('.json') else {"content": f.read()}

            # Use forward method for analysis
            result = self.forward(
                session_data=session_data,
                pattern_types=focus_areas or ["all"]
            )

            return {
                "success": result.success,
                "patterns": result.patterns_extracted,
                "learnings": result.learnings_consolidated,
                "message": result.message
            }

        except Exception as e:
            logger.error(f"Error analyzing session: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def extract_insights(
        self,
        patterns: List[ExtractedPattern],
        min_occurrences: int = 2
    ) -> List[Insight]:
        """
        Extract actionable insights from patterns.

        Args:
            patterns: List of patterns
            min_occurrences: Minimum occurrences for significance

        Returns:
            List of insights
        """
        insights = []

        # Group patterns by type
        pattern_groups = {}
        for pattern in patterns:
            pattern_type = pattern.pattern_type
            if pattern_type not in pattern_groups:
                pattern_groups[pattern_type] = []
            pattern_groups[pattern_type].append(pattern)

        # Extract insights from each group
        for pattern_type, group in pattern_groups.items():
            if len(group) >= min_occurrences:
                insight = {
                    "type": pattern_type,
                    "frequency": len(group),
                    "avg_confidence": sum(p.confidence for p in group) / len(group),
                    "description": f"Recurring {pattern_type} pattern detected",
                    "patterns": [p.model_dump() for p in group]
                }
                insights.append(insight)

        return insights

    def consolidate_learning(
        self,
        insights: List[Insight],
        existing_learnings: Optional[List[ConsolidatedLearning]] = None
    ) -> List[ConsolidatedLearning]:
        """
        Consolidate insights into learnings.

        Args:
            insights: List of insights to consolidate
            existing_learnings: Existing learnings to build on

        Returns:
            List of consolidated learnings
        """
        learnings = []
        existing_learnings = existing_learnings or []

        # Keep track of which existing learnings were updated
        updated_existing_learnings = []

        for insight in insights:
            # Check if this updates existing learning
            updated_existing = False
            for existing in existing_learnings:
                if self._is_related_learning(insight, existing):
                    # Update existing learning
                    patterns_to_add = []
                    for p in insight.get("patterns", []):
                        if isinstance(p, dict):
                            try:
                                patterns_to_add.append(ExtractedPattern(**p))
                            except:
                                pass
                    existing.patterns.extend(patterns_to_add)
                    existing.confidence = (existing.confidence + insight.get("avg_confidence", 0.5)) / 2
                    updated_existing = True
                    if existing not in updated_existing_learnings:
                        updated_existing_learnings.append(existing)
                    break

            if not updated_existing:
                # Create new learning
                patterns_list = []
                for p in insight.get("patterns", []):
                    if isinstance(p, dict):
                        try:
                            patterns_list.append(ExtractedPattern(**p))
                        except:
                            pass

                learning = ConsolidatedLearning(
                    title=f"{insight.get('type', 'Unknown').replace('_', ' ').title()} Pattern",
                    summary=insight.get("description", "Automatically extracted pattern"),
                    patterns=patterns_list,
                    actionable_insights=[
                        f"This pattern occurs with {insight.get('frequency', 'unknown')} frequency",
                        f"Average confidence: {insight.get('avg_confidence', 0.0):.2f}"
                    ],
                    confidence=insight.get("avg_confidence", 0.5),
                    tags=[insight.get("type", "unknown"), "auto_extracted"]
                )
                learnings.append(learning)

        # Return both new learnings and updated existing ones
        return learnings + updated_existing_learnings

    def store_knowledge(
        self,
        learnings: List[ConsolidatedLearning],
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Store consolidated learnings in knowledge base.

        Args:
            learnings: Learnings to store
            metadata: Additional metadata

        Returns:
            Success status
        """
        try:
            for learning in learnings:
                # Store in internal knowledge base
                category = learning.tags[0] if learning.tags else "general"
                if category not in self.knowledge_base:
                    self.knowledge_base[category] = []
                self.knowledge_base[category].append(learning)

                # Log storage
                logger.info(f"Stored learning: {learning.title} (confidence: {learning.confidence:.2f})")

            return True

        except Exception as e:
            logger.error(f"Error storing knowledge: {str(e)}")
            return False

    def query_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[ConsolidatedLearning]:
        """
        Query the knowledge base for relevant learnings.

        Args:
            query: Query string
            category: Optional category filter
            min_confidence: Minimum confidence threshold

        Returns:
            List of relevant learnings
        """
        min_confidence = min_confidence or self.min_confidence
        results = []

        # Search categories
        categories_to_search = [category] if category else self.knowledge_base.keys()

        for cat in categories_to_search:
            if cat in self.knowledge_base:
                for learning in self.knowledge_base[cat]:
                    # Check confidence
                    if learning.confidence < min_confidence:
                        continue

                    # Simple keyword matching (could be enhanced with semantic search)
                    query_lower = query.lower()
                    if any(keyword.lower() in query_lower for keyword in learning.tags):
                        results.append(learning)
                    elif query_lower in learning.title.lower() or query_lower in learning.summary.lower():
                        results.append(learning)

        return results

    def _prepare_context(
        self,
        session_id: Optional[str],
        pattern_types: Optional[List[str]],
        context: DSPyContext
    ) -> LearningContext:
        """Prepare and validate the learning context."""
        try:
            # Set defaults
            if session_id:
                context["session_id"] = session_id
            elif "session_id" not in context:
                context["session_id"] = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if pattern_types:
                context["pattern_types"] = pattern_types

            return LearningContext(**context)

        except ValidationError as e:
            logger.error(f"Context validation error: {str(e)}")
            # Return minimal valid context
            return LearningContext(
                session_id=context.get("session_id", f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            )

    def _load_session_data(self, context: LearningContext) -> SessionData:
        """Load session data from logs."""
        session_path = Path(context.logs_directory) / f"{context.session_id}.json"

        if session_path.exists():
            with open(session_path, 'r') as f:
                return json.load(f)
        else:
            # Return empty session data
            logger.warning(f"Session file not found: {session_path}")
            return {
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat(),
                "events": []
            }

    def _get_existing_knowledge(self, context: LearningContext) -> dict:
        """Get existing knowledge from the knowledge base."""
        knowledge = {
            "categories": list(self.knowledge_base.keys()),
            "total_learnings": sum(len(learnings) for learnings in self.knowledge_base.values()),
            "learnings": []
        }

        # Include recent learnings
        for category, learnings in self.knowledge_base.items():
            for learning in learnings[-context.historical_limit:]:
                knowledge["learnings"].append(learning.model_dump())

        return knowledge

    def _process_patterns(self, extraction_result: Any) -> List[PatternDict]:
        """Process raw DSPy extraction result into patterns."""
        patterns = []

        try:
            raw_patterns = getattr(extraction_result, 'patterns', [])
            confidence_scores = getattr(extraction_result, 'confidence_scores', {})

            for pattern in raw_patterns:
                if isinstance(pattern, dict):
                    # Add confidence if available
                    if pattern.get("pattern_type") in confidence_scores:
                        pattern["confidence"] = confidence_scores[pattern["pattern_type"]]
                    patterns.append(pattern)
                elif hasattr(pattern, 'model_dump'):
                    patterns.append(pattern.model_dump())

        except Exception as e:
            logger.error(f"Error processing patterns: {str(e)}")

        return patterns

    def _process_learnings(self, consolidation_result: Any) -> List[PatternDict]:
        """Process raw DSPy consolidation result into learnings."""
        learnings = []

        try:
            consolidated = getattr(consolidation_result, 'consolidated_learnings', [])

            for learning in consolidated:
                if isinstance(learning, dict):
                    learnings.append(learning)
                elif hasattr(learning, 'model_dump'):
                    learnings.append(learning.model_dump())

        except Exception as e:
            logger.error(f"Error processing learnings: {str(e)}")

        return learnings

    def _update_knowledge_base(self, learnings: List[PatternDict], context: LearningContext):
        """Update internal knowledge base with new learnings."""
        for learning in learnings:
            try:
                consolidated = ConsolidatedLearning(**learning)
                category = consolidated.tags[0] if consolidated.tags else "general"

                if category not in self.knowledge_base:
                    self.knowledge_base[category] = []

                self.knowledge_base[category].append(consolidated)

                # Limit size to prevent memory issues
                if len(self.knowledge_base[category]) > 100:
                    self.knowledge_base[category] = self.knowledge_base[category][-100:]

            except Exception as e:
                logger.error(f"Error updating knowledge base: {str(e)}")

    def _is_related_learning(self, insight: Insight, learning: ConsolidatedLearning) -> bool:
        """Check if an insight is related to an existing learning."""
        # Simple type matching - could be enhanced with semantic similarity
        return insight.get("type") in learning.tags

    def get_learning_summary(self) -> LearningSummary:
        """Get a summary of the knowledge base."""
        return {
            "total_categories": len(self.knowledge_base),
            "total_learnings": sum(len(learnings) for learnings in self.knowledge_base.values()),
            "categories": {
                category: len(learnings)
                for category, learnings in self.knowledge_base.items()
            },
            "pattern_history_size": len(self.pattern_history),
            "avg_confidence": sum(l.confidence for learnings in self.knowledge_base.values() for l in learnings) / max(1, sum(len(learnings) for learnings in self.knowledge_base.values()))
        }

    def reset_knowledge(self) -> None:
        """Reset the knowledge base (useful for testing)."""
        self.knowledge_base = {}
        self.pattern_history = []
        logger.info("Knowledge base reset")


# Factory function for backwards compatibility
def create_dspy_learning_agent(
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "high",
    enable_learning: bool = True,
    min_confidence: float = 0.7,
    **kwargs
) -> DSPyLearningAgent:
    """
    Factory function to create a DSPyLearningAgent instance.

    This provides backwards compatibility with the existing Agency infrastructure
    while enabling the new DSPy-powered capabilities.

    Args:
        model: Language model to use
        reasoning_effort: Level of reasoning effort
        enable_learning: Whether to enable continuous learning
        min_confidence: Minimum confidence threshold
        **kwargs: Additional arguments passed to the agent

    Returns:
        DSPyLearningAgent: Configured agent instance
    """
    return DSPyLearningAgent(
        model=model,
        reasoning_effort=reasoning_effort,
        enable_learning=enable_learning,
        min_confidence=min_confidence
    )


# Export the main class and factory function
__all__ = [
    "DSPyLearningAgent",
    "create_dspy_learning_agent",
    "LearningContext",
    "ExtractedPattern",
    "ConsolidatedLearning",
    "LearningResult",
]